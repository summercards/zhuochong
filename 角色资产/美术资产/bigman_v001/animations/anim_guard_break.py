"""anim_guard_break —— D04 `Guard_Break` 破防。

设计（对着清单 §四 D04 的原文「双臂被震开，身体后仰，产生明显**硬直**」逐条落）：

    段结构     **1 段 = 震开 → 硬直平台 → 慢收**、**0 命中点**、**0 位移**。
    时长       60 帧 = **1.000 s** @60fps（计划 0.9~1.2 s —— 硬直要占时间）
    零位       ★ **= D01 `Guard_Start` 落盘 action 的末帧**（与 D02/D03 同口径：
                读引擎真正播的那份数据，不重演。理由见 `_load_d01_end_pose()`）。
    首尾       ★ 首帧 == D01 末帧（引擎 `Guard_Loop → Guard_Break` 直连）；
                末帧 == 同一 `dict(ZERO)`（破防恢复后回到护架，可接回 `Guard_Loop`）。
    节奏       ★★ **升 4 帧 / 平台 10 帧 / 降 40 帧** —— 平台就是"硬直"本身：
               f0 零位 → **f4 震开峰** → **f4..f14 完全僵住**（平台 10 帧）→
               慢回弹 → f54 归零 → f54..f60 逐位冻结。
    姿态       ★★ **护架被打破**（这是本支与 D03 的本质区别）：
               双臂**横向外张**（双拳净距变大）+ 沿 +Y **后收**（明显大于 D03 的 44 mm）
               + **上身后仰明显大于 D03**（chest 世界俯仰 ≥8°，D03 是 4.3°）
               + 肘也被震开（肘尖由内收转为外张）；**脚仍然纹丝不动**。
    核心难点   ★★ **"护不住"要读得出来** —— 判据全绿但看不出"护架被打破" = 失败。

本支与 D03 的门禁差异（计划 §2 原案，逐条落实）：
    ★★★ **撤下 `guard_cover_ok`** 与 **`guard_elbow_ok`**：
         D04 的语义就是"护架被打破"，留着"拳相对胸身前 ≥150 mm、横向 130~200 mm、
         肘尖不得比肩外"是**构造性冲突**（震开 = 横向必然超上界；后仰 8°+ = 身前必然缩短；
         肘被震开 = 肘尖必然比肩外）。
    ★ **新立** `guard_break_ok` / `guard_break_torso_ok` / `guard_break_stagger_ok` /
         `guard_break_recover_ok`（见下）。
    ★ **保留** `guard_no_face_clip_ok`（震开方向是"远离脸"，但要实测 —— 拳头往侧面甩时
         小臂可能扫过下巴/颈侧，这正是 D03 计划 §3 预警过的翻车点）。
    ★ **保留** `ground_contact_ok` / `plant_ok`（≤1.0，与 D03 同） / `no_teleport`（≤25°） /
         `ua_start_ok` / `reach_ok` / `guard_symmetry_hold_ok`（左右**对称** ——
         震开应是左右同时，不是单侧）/ `knee_passive_ok`（≤6°，D03 新立；本支下沉
         更大，**已重扫这个上限**，见下方幅度扫描记录）。
    ★ **显式** `hitstop_present` —— 本支硬直 ≥8 帧，窗口与 D03 的 2 帧停顿分开定义。

★ 关于幅度：全部**先量再定**（计划 §3「先扫再定，不要假设后仰一定安全」）。
  本支把 4 个臂偏移参数与 8 个躯干角全开成环境变量（`D04_*`），逐组跑完整门禁后锁定
  （扫描记录见下方 `受击幅度` 段注释与 `_d04_sw*.log`）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_guard_break.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D04_TRACE=1    逐帧打印 press / 震开量 / chest 俯仰（调参用）
"""

import json
import math
import os
import struct
import sys

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                     # noqa: E402
import anim_idle_01 as I1                # noqa: E402
import anim_jump_start as JS             # noqa: E402
import anim_ultimate_end as UE           # noqa: E402
import probe_c12_baseline as P           # noqa: E402
import probe_d01_guard as PD             # noqa: E402
import anim_guard_start as GS            # noqa: E402

NAME = "Guard_Break"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")


def _env_i(key, default):
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_f(key, default):
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _f32(value):
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（D02/D03 的 `_f32` 同源）。

    零位 `ZERO` 是 float64，`sample_animation` 读回的是 float32 ⟹ 直接比会假红。
    两边都过 float32，"逐位相同" 才是真的逐位相同（差值 = 0.0）。
    """
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _extract_report(text, tag):
    """从日志里抠出 `TAG {json}`（花括号配平），返回 dict 或 None。"""
    marker = tag + " "
    index = text.find(marker)
    if index < 0:
        return None
    start = text.find("{", index)
    if start < 0:
        return None
    depth = 0
    for offset in range(start, len(text)):
        char = text[offset]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:offset + 1])
                except ValueError:
                    return None
    return None


def _load_d01_end_ref():
    """D01 报告里**发布的**末帧欧拉真值（`_d01_final.log` 优先）。"""
    base = os.path.join(A.OUT_DIR, "animations")
    for name in ("_d01_final.log", "_d01_rep3.json"):
        path = os.path.join(base, name)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError:
            continue
        payload = _extract_report(text, "D01_REPORT")
        if payload and payload.get("end_euler_ref"):
            return payload["end_euler_ref"], name
    return {}, "MISSING"


def _keyed_bones(action):
    """action 里真有 F-Curve 的骨（分开报旋转 / 位移）。"""
    rot, loc = set(), set()
    for curve in action.fcurves:
        path = curve.data_path
        if not path.startswith('pose.bones["'):
            continue
        name = path.split('"')[1]
        if path.endswith("rotation_euler"):
            rot.add(name)
        elif path.endswith("location"):
            loc.add(name)
    return rot, loc


def _load_d01_end_pose(arm):
    """★ 零位真源：落盘 `Guard_Start` action 的**末帧**（引擎真正会播的那份数据）。

    理由与 D02/D03 完全一致：D01 的腕骨滚转在自身两次跑之间差 18°（`aim_nearest`
    管不到的零空间自由度），**重演不可复现** ⟹ 零位必须从落盘数据取，不能从重演取。
    读回值已过 `deg → rad → f32 → deg` 链，f0 写回去是**构造性逐位相同**。
    """
    action = bpy.data.actions.get(GS.NAME)
    if action is None:
        return {}, {"action": GS.NAME, "found": False}
    rot_keyed, loc_keyed = _keyed_bones(action)
    last = int(action.frame_range[1])
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    A.reset_pose(arm)
    bpy.context.scene.frame_set(last)
    bpy.context.view_layer.update()
    pose = {name: tuple(math.degrees(v)
                        for v in arm.pose.bones[name].rotation_euler)
            for name in rot_keyed if name in arm.pose.bones}
    loc = {name: tuple(arm.pose.bones[name].location)
           for name in loc_keyed if name in arm.pose.bones}
    if loc:
        pose["@loc"] = loc
    info = {"action": GS.NAME, "found": True, "last_frame": last,
            "expected_last_frame": GS.TOTAL,
            "rot_bones": len(rot_keyed), "loc_bones": sorted(loc_keyed),
            "frame_range": [int(v) for v in action.frame_range]}
    return pose, info


def _replay_d01_settle(arm, meshes):
    """逐行照抄 D01 `main()` 的求解：起手帧打底 + `_PREV_EULER` 播种 +
    `solve_pose(1..TOTAL)`，取 `SETTLE` 帧（复用同一条代码路径的**几何同解**守卫）。"""
    JS._PREV_EULER.clear()
    A.apply_pose(arm, GS.SEAM_POSE)
    bpy.context.view_layer.update()
    for name, value in GS.SEAM_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    pose = None
    for frame in range(1, GS.TOTAL + 1):
        got = GS.solve_pose(arm, frame, meshes)
        if frame == GS.SETTLE:
            pose = got
    if pose is None:
        raise RuntimeError("D01 重演没拿到 SETTLE 帧")
    return pose


def _world_snapshot(arm, pose):
    """把姿态打进去，取世界快照（骨根位置 + 骨轴指向）。"""
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()
    heads, dirs = {}, {}
    for name in A.PROBE_BONES:
        if name not in arm.pose.bones:
            continue
        heads[name] = Vector(A.bone_world(arm, name, "head"))
        dirs[name] = Vector(A.bone_direction(arm, name)).normalized()
    return heads, dirs


# =============================================================== 时间轴
# ★ 计划 §4 第 2 条的建议：TOTAL = 60（1.0 s）→ f0 零位 / f4 震开峰 / 硬直 / 慢收。
TOTAL = _env_i("D04_TOTAL", 60)           # 1.000 s @60fps（计划 0.9~1.2 s）
IMPACT = _env_i("D04_IMPACT", 4)          # 震开峰（上升沿 4 帧 —— 计划"升 3~4 帧"）
HOLD_END = _env_i("D04_HOLD", 14)         # 硬直平台末帧 ⟹ 平台 = 10 帧
RECOVER_END = _env_i("D04_RECOVER", 54)   # 慢收归零帧（此段 40 帧 ≥30）

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
# ★ 与 D03 同：本支同样"上身被打、脚必须不动"，plant 收紧到 1.0 mm
PLANT_MAX_MM = _env_f("D04_PLANT", 1.0)
SLIDE_MAX_MM = _env_f("D04_SLIDE", 1.0)
GROUND_MIN_MM, GROUND_MAX_MM = -2.0, 6.0
REACH_MAX_RATIO = 0.995
# ★ `knee_passive_ok`（D03 新立，上限 6.0°）：本支下沉更大 ⟹ **已重扫**。
#   实测关系 ≈ 0.342°/(mm 下沉)（D03：14 mm → 4.784°）。定稿下沉 −16 mm ⟹ 实测
#   5.47°，落在 6.0° 内（余量 0.53°）⟹ **上限不动**（不靠放宽容差凑绿）。
KNEE_DELTA_MAX_DEG = _env_f("D04_KNEE", 6.0)

# ---- "护架被打破" 三条子判据（阈值由「下一支详细制作计划」§2 给出，先扫再定）
BREAK_SPREAD_MIN_MM = _env_f("D04_SPREAD", 60.0)   # 双拳横向净距相对零位的增量下界
BREAK_BACK_MIN_MM = _env_f("D04_BACKMIN", 60.0)    # 拳沿 +Y 相对骨盆后收增量下界
BREAK_PITCH_MIN_DEG = _env_f("D04_PITCH", 8.0)     # chest 世界俯仰（后仰）下界

# ---- "硬直" 判据
BREAK_PLATFORM_MIN = _env_f("D04_PLAT_MIN", 8.0)
BREAK_PLATFORM_MAX = _env_f("D04_PLAT_MAX", 16.0)
BREAK_PLATFORM_DRIFT_DEG = _env_f("D04_PLAT_DRIFT", 0.5)

# ---- 节奏不对称
BREAK_RISE_MAX_FRAMES = _env_f("D04_RISE_MAX", 4.0)
BREAK_FALL_MIN_FRAMES = _env_f("D04_FALL_MIN", 30.0)
# 可选第 1 帧软起（<0 = 不用，纯 4 帧线性升）
EASE_P1 = _env_f("D04_P1", -1.0)
# ★ 上升沿逐帧等量（见 `press()` 的说明：PCHIP 单段天然前重后轻）
RISE_EVEN = _env_f("D04_RISE_EVEN", 1.0) >= 0.5
# ★ 上升沿形状指数：1.0 = 直线；>1 = 前段更慢（把位移更多留给 f3→f4），
#   用来给 `no_teleport` 留余量（限值不是放宽，是**改速度剖面**）。
RISE_GAMMA = _env_f("D04_RISE_GAMMA", 1.3)

# ---- 末帧回到零位（三口径，与 D03 的 `guard_hit_recover_ok` 同源）
BREAK_END_MAX_MM = _env_f("D04_END_MAX", 0.5)
BREAK_LAST2_MAX_DEG = _env_f("D04_LAST2", 0.5)
# ★ 第四口径：末帧**绕骨轴滚转**漂移上限（位置口径发现不了的量，见 `end_roll_deg`）
BREAK_ROLL_MAX_DEG = _env_f("D04_ROLL_MAX", 0.5)
# ★ 滚转回位修正开关与形状（见 `_roll_return()`）
ROLL_RETURN = _env_f("D04_ROLL_RETURN", 1.0) >= 0.5
ROLL_RETURN_GAMMA = _env_f("D04_ROLL_GAMMA", 1.0)
# ★ 修正权重的**时间形状**（三种，供扫描；默认 `press`）：
#   press  —— `1 − press(f)`：震开峰/硬直平台权重 0（设计姿态逐位不变），
#             平台→末帧升到 1。**但上升沿（f1..f3）权重高达 0.84** ⟹ 若该帧
#             的滚转修正量恰好落进 `upperarm.L` 的谐振带（δ≈4.5°，见
#             `probe_d04_gimbal.py`：δ=5° 时欧拉跳 64.8° 而世界只走 5°）就炸。
#   tail   —— 平台结束（f=HOLD_END）前恒 0，之后线性升到 1：彻底躲开上升沿。
#   always —— 恒 1：每帧都钉在"零位滚转沿当前骨轴的延续"上 ⟹ 和乐**不累积**
#             （δ 从 0 出发按步长平方增长，f1 处天然极小）。实测**不行**：
#             f1 欧拉步长 91.075° @ `upperarm.R`，且硬直平台被判据
#             `guard_break_stagger_ok` 抓红（平台帧被修正动到）。
#
# ★ 实测结论（三次扫描 `rr0` / `ral` / `rtl`）：只有 `tail` 能同时满足
#   `failed=[]` + `non_ok_bools=[]` 且 `end_roll_deg` ≤ 0.089°。故 **默认 tail**。
#   理由：本支的和乐总量 30.55°（`rr0` 实测）⟹ 修正量必须从 0 扫到 30°，
#   **必然**穿过 `upperarm.L` 的谐振带（δ≈4.5°）；能做的只是让它**慢慢**穿过去，
#   而"慢"的唯一位置是硬直平台之后的 46 帧（上升沿只有 4 帧，权重又高 0.84）。
ROLL_WEIGHT_MODE = os.environ.get("D04_ROLL_WEIGHT", "tail").strip().lower()
# ★ 修正对象：**全部 6 根臂骨**（默认）。
#   实测依据（`rr0`，把修正关掉直接量和乐分布）：
#       forearm.L / hand.L  30.5479°
#       forearm.R / hand.R   4.5478°
#       upperarm.L          18.1109°
#       upperarm.R          12.1107°
#   近端也吃到 12~18° ⟹ 只修远端会在 `upperarm` 上残留 18.11°（`end_roll_ok` 红，
#   实测第一版白名单就是这个结果）。全修 = 0.0885°。
#   ★ 注意：`upperarm` 的零位欧拉骑在万向节锁上（`ry = −94.4543°`），修它必须
#     配合 `ROLL_WEIGHT_MODE="tail"`，否则会撞进谐振带（见 `_roll_weight` 注释）。
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D04_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split(",")
    if item)

# ★★ "零位 = D01 末帧" 的三条守卫（与 D02/D03 逐字同源）
D01_REF_TOL_DEG = 5.0e-05
D01_GEOM_POS_MAX_MM = _env_f("D04_D01_POS", 0.01)
D01_GEOM_DIR_MAX_DEG = _env_f("D04_D01_DIR", 0.05)

# ★ 保留的护架判据（本支只留"对称"，`guard_cover_ok` / `guard_elbow_ok` 已**撤下**）
GUARD_SYM_MAX_MM = _env_f("D04_SYM", 25.0)
GUARD_CLIP_MAX_MM = 0.0
CLIP_EVERY = int(os.environ.get("D04_CLIP_EVERY", 4))

# =============================================================== 破防幅度
# ★★ 全部**先量再定**（计划 §3："先扫再定，不要假设后仰一定安全"）。
#   扫描记录（每组都跑完整门禁，`D04_*` 环境变量覆盖，见 `_d04_sw*.log`）：
#
#   第 1 轮 —— 基线（计划 §4 建议值）：`guard_break_ok` 红（震开后收 44→不够）、
#     `guard_break_torso_ok` 红（chest 俯仰 4.3° < 8°），其余全绿。
#     ⟹ 按计划"改幅度/方向，不要放宽区间"：加大 `D04_OUT` / `D04_BACKMM` /
#        躯干后仰链（pelvis→chest 的 rx 之和 ≈ −(chest 世界俯仰)）。
#
#   ★★ 关键发现 1：`chest` 世界俯仰 = **pelvis..chest 的 rx 之和取负**（实测线性）。
#     D03 的 −4.3° = −(−0.6−0.95−0.95−1.8)。要 ≥8° 就得把这段和推到 ≥8。
#     但躯干每多后仰 1°，肩就被带走 ~11 mm ⟹ 拳的"后收"里有一部分是躯干送的
#     （与 D03 教训 1 同一现象的镜像）。本支把"后收"锚在**骨盆**上，故躯干后仰
#     不会污染该口径。
#
#   ★★ 关键发现 2（像素换算复核，D03 教训 3 的沿用）：推进器的可见量是"双拳净距"，
#     它在**正视**里直接可读（横向，比例尺 1 mm ≈ 0.556 px）⟹ `spread_delta` 必须
#     ≥ 22 mm 才能进 12 px。定稿 148 mm ⟹ **82 px**，远超复核线。
#
#   ★★ 关键发现 3：`D04_OUT` 有**上限，但不是 clip，是臂长**：每侧外张 ≥ 90 mm 后
#     `reach_ratio_max` 逼近 0.995（肩→拳距离吃满臂长）⟹ 定稿卡在 74 mm/侧。
#     （`clip_max_mm` 全程 0.00 —— 肘外张把前臂推离颈侧，D03 担心的"扫下巴"没发生。）
PRESS_DROP_MM = _env_f("D04_DROP", -16.0)    # 骨盆下沉（腿 IK 吸收 ⟹ 脚不动）
PRESS_OUT_MM = _env_f("D04_OUT", 74.0)       # 每侧拳**横向外张**（震开）
PRESS_BACK_MM = _env_f("D04_BACKMM", 84.0)   # 拳沿 +Y **后收**（明显大于 D03 的 44）
PRESS_DOWN_MM = _env_f("D04_DOWN", 14.0)     # 拳下沉（护架随身体略沉 + 被压开）
TORSO_PRESS = {"pelvis": _env_f("D04_TP_PELVIS", -1.4),
               "spine_01": _env_f("D04_TP_S1", -2.2),
               "spine_02": _env_f("D04_TP_S2", -2.4),
               "chest": _env_f("D04_TP_CHEST", -3.8),
               "neck": _env_f("D04_TP_NECK", -4.6),
               "head": _env_f("D04_TP_HEAD", -7.0),
               "shoulder.L": _env_f("D04_TP_SH", -6.0),
               "shoulder.R": _env_f("D04_TP_SH", -6.0)}
# 肘被震开：肘偏好方向由 D01 的"内收"转为"外张下压"。
# ★ 摆幅（`D04_EB_X`）本身会影响单帧欧拉步长 —— 肘向从 −0.30（内收）翻到 +X（外张）
#   要**穿过 0**，翻得越狠、`press` 上升沿越短，单帧步长越大。见下方扫描记录。
_EB_X = _env_f("D04_EB_X", 0.45)
_EB_Z = _env_f("D04_EB_Z", -0.80)
ELBOW_BREAK = {"L": Vector((_EB_X, -0.05, _EB_Z)).normalized(),
               "R": Vector((-_EB_X, -0.05, _EB_Z)).normalized()}

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")

# =============================================================== 模块级表
ZERO = {}                 # D01 定格真值（本支零位）
ZERO_WORLD = {}
# ★ 零位的**世界旋转基**（不是位置）—— 用来盯"绕骨轴滚转"这种位置口径发现不了的漂移。
#   见 `_roll_return()` 与 `break_assertions()` 里的 `end_roll_deg`（D02 教训 1 的镜像）。
ZERO_BASIS = {}
ZERO_DIR = {}
IDLE_FIST = {}
D01_SAME_SOLVE = {"ok": None, "diff": None, "src": None, "per_bone": {}}


def press(frame):
    """破防标量 ∈ [0, 1]：**升 4 / 平台 10 / 降 40** 的三段表（对称 PCHIP 做不到）。

    ★ 与 D03 的关键差异：D03 是"升 4 / 顶 2 / 降 26"的**尖峰**（被打一下立刻回弹）；
      本支是"升 4 / **平台 10** / 降 40"的**平台**——平台本身就是"硬直"：
      姿态在 f4..f14 完全冻结（PCHIP 在两端等值键之间恒取该值 ⟹ 逐帧输入全等
      ⟹ 解出的姿态逐位相同，平台内漂移恒 0.0°）。

    ★ `D04_RISE_EVEN=1`：把上升沿改成**逐帧等量**（关键键 `(k, k/IMPACT)`）。
      为什么需要它 —— 首次实测 `no_teleport` 红：`max_frame_step_deg` **26.161°/帧**
      落在 `upperarm.L @f1`。逐帧轨迹是 **26.16 / 16.10 / 9.29 / 3.74**（连续**递减**，
      不是孤峰 ⟹ **不是欧拉假跳，是真实的前重后轻**）：
      PCHIP 在 `(0,0)→(IMPACT,1)` 这个**单段**上算出的首点斜率是 0.321/帧
      （> 弦斜率 0.25），于是位移全挤在第 1 帧。
      ⟹ 补上 `f1..f3` 的等分键，PCHIP 退化成直线，4 帧各走 ~14°。
      这不是放宽 `no_teleport`（限值仍是 25°），而是**改速度剖面**。
    """
    keys = [(0, 0.0)]
    if EASE_P1 >= 0.0:
        keys.append((1, EASE_P1))
    elif RISE_EVEN:
        for step in range(1, IMPACT):
            keys.append((step, (step / float(IMPACT)) ** RISE_GAMMA))
    keys += [(IMPACT, 1.0), (HOLD_END, 1.0), (RECOVER_END, 0.0), (TOTAL, 0.0)]
    return UE.pwl(tuple(keys), float(frame), 0.0)


def fist_target(side, frame):
    """拳世界目标 = D01 定格 + 破防偏移（镜像）。**绝对世界点**（同 D02/D03 口径）。

    ★ 与 D03 的符号差异：D03 的 `PRESS_IN_MM` 用于"往中间压"（−sign），本支的
      `PRESS_OUT_MM` 是**往外震**（+sign）⟹ 左拳 x 增大、右拳 x 减小。
    """
    p = press(frame)
    sign = 1.0 if side == "L" else -1.0
    return Vector(GS.GUARD_FIST[side]) + Vector(
        (sign * PRESS_OUT_MM, PRESS_BACK_MM, -PRESS_DOWN_MM)) * (p / 1000.0)


def elbow_break(side, frame):
    """肘偏好方向：D01 内收 → 震开时外张下压（按 `press` 插值，归一化）。"""
    p = press(frame)
    value = Vector(GS.GUARD_ELBOW[side]) * (1.0 - p) + ELBOW_BREAK[side] * p
    if value.length < 1e-9:
        return tuple(ELBOW_BREAK[side])
    return tuple(value.normalized())


def torso_pose(frame):
    p = press(frame)
    out = {}
    for name in TARGET_BONES:
        zero = ZERO[name]
        out[name] = (zero[0] + TORSO_PRESS.get(name, 0.0) * p,
                     zero[1], zero[2])
    drop = GS.GUARD_DROP_MM + PRESS_DROP_MM * p
    out["@loc"] = {"pelvis": A.wloc(0.0, 0.0,
                                    GS.Z_SEAM + drop / 1000.0 - 0.900)}
    return out


def build_pose(arm, frame):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    # 腿：位置 IK（`UE.leg_seat`），踝目标钉死在 D01 的 `ANKLE_0` ⟹ 脚纹丝不动。
    for side in SIDES:
        UE.leg_seat(arm, pose, side, GS.ANKLE_0[side], GS.KNEE_DIR)
    for side in SIDES:
        name = "foot." + side
        pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name),
                                    A.keep_world_orientation(arm, name))
    for side in SIDES:
        # ★ 拳目标必须在 `apply_pose` 之后按**当前**肩位现取（肩随躯干走）
        UE.arm_seat(arm, pose, side, fist_target(side, frame),
                    elbow_break(side, frame))
    # ★ 滚转回位修正（见 `_roll_return()`）：weight = 1 − press ⟹
    #   震开峰与硬直平台（press ≡ 1）权重为 0，设计姿态逐位不变；
    #   平台→末帧平滑升到 1，把 30° 和乐摊在 40 帧里还回去。
    roll_weight = _roll_weight(frame)
    if ROLL_RETURN and roll_weight > 1e-9:
        for name in ROLL_BONES:
            if name not in arm.pose.bones:
                continue
            _roll_return(arm, pose, name, roll_weight ** ROLL_RETURN_GAMMA)
    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


def solve_pose(arm, frame, meshes=None):
    """单帧装配（无贴地闭环；踝由位置 IK 钉死，脚纹丝不动）。"""
    return build_pose(arm, frame)


# =============================================================== 滚转回位修正
def _roll_weight(frame):
    """修正权重 —— 三形状（见 `ROLL_WEIGHT_MODE` 的注释）。"""
    if ROLL_WEIGHT_MODE == "always":
        return 1.0
    if ROLL_WEIGHT_MODE == "tail":
        if frame <= HOLD_END:
            return 0.0
        span = max(1, TOTAL - HOLD_END)
        return min(1.0, max(0.0, (frame - HOLD_END) / float(span)))
    return 1.0 - press(frame)


def _roll_return(arm, pose, name, weight):
    """★ 把某根骨的**绕自身轴滚转**沿世界朝向对齐回零位（只改滚转，不改骨轴方向）。

    ══════════════════════════════════════════════════════════════════════════
    为什么需要它 —— 本支第 1 次收尾实测查出的**真实缺陷**：

        `end_world_pose_mm`  0.0009 mm   （骨根/骨尖逐位对齐零位）
        `end_pose_mm`        0.0 mm
        `end_last2_deg`      0.0         （末 2 帧欧拉步长为 0）
        ───────────────────────────── 三条"回零位"口径**全绿**
        `end_roll_deg`       **30.55°**  （forearm.L / hand.L）

    位置口径全部看不见它 —— 一根骨整体绕自身轴转 30°，骨根与骨尖**一动都不动**，
    但蒙皮（袖子、拳套截面）会转 ⟹ **渲染画面 f60 与 f0 差 3 px**（实测）。
    这就是 D02 教训 1 的镜像："欧拉逐位相同 ≠ 世界姿态相同"，只是这次骗人的
    是**位置**口径而不是欧拉口径。

    不是 D 族共性（`probe_d04_roll.py` 只读实测）：
        Guard_Start  f0↔last 86.47°（那是"抬手"本身，合理）｜last↔zero  0.06°
        Guard_Loop   f0↔last  0.06°                          ｜last↔zero  0.06°
        Guard_Hit    f0↔last  0.06°                          ｜last↔zero  0.06°
        **Guard_Break f0↔last 30.55°**                        ｜last↔zero 30.55°
    ⟹ D02/D03 是干净的（0.06°），**本支独有的缺陷**，必须修 —— 它会让引擎在
      `Guard_Break → Guard_Loop` 直连处把袖子瞬时拧 30°（"直连处会跳"）。

    根因：`UE.aim_nearest` 的世界朝向是沿**接力链**（`CARRY_Q`）累积的
    `q = Δmin(prev_axis → want) ∘ prev_q` —— 只补"骨轴对准"的最小旋转，
    **滚转不参与求解、只被继承**。当骨轴在方向球上划出一个**闭合回路**时，
    滚转就吃到一份 **holonomy（和乐）**，正比于回路张的立体角。D03 的臂几乎只在
    一条直线上"出去再回来"（立体角 ≈ 0），本支的臂从胸前**横向张开 + 肘位面翻转**
    （肘偏好方向 (−0.30,−0.10,−0.95) → (+0.45,−0.05,−0.80)），回路张的立体角大
    ⟹ 30° 和乐。实测分离验证：把滚转网格关掉（`D01_ROLLSTEP=6.3`）后
    `forearm.L` 掉到 0.55° 而 `upperarm.L` 涨到 44.2° —— 滚转网格只是在**搬运**
    这份和乐，不是它的来源。

    做法（为什么不是"把末帧钉成 ZERO"）：
        D03 第 2 号教训已经证明，把尾部欧拉钉成 ZERO 会凭空造出一个 27°/帧的跳变
        （零空间支被强行掰）。所以这里**不碰欧拉**，只在**世界朝向**里做：
            ① `q_ref = Δmin(零位骨轴 → 当前骨轴) ∘ q_zero`
               —— "零位滚转在**当前**骨轴方向上的延续"。它与当前朝向**同轴**
                  （都把 +Y 映到当前轴），故两者之差**纯粹是滚转**。
            ② `q_new = slerp(q_now, q_ref, weight)` —— 只拧滚转、骨轴一动不动
               ⟹ IK / 指尖位置 / 贴地 / `end_world_pose_mm` 全部不受影响。
        `weight` = `_roll_weight(frame)`（默认 `tail`）：**硬直平台结束（f=14）之前
        恒 0** ⟹ 上升沿与整段硬直（press ≡ 1）的姿态**逐位不变**（所有
        `guard_break_*` 判据不受影响）；f14 → f60 线性升到 1 ⟹ 30.55° 的和乐
        摊在 **46 帧**上还回去，每帧 ≈0.66°。

    两条实测陷阱（都是先撞上去才查出来的，记在这里防止下次重犯）：
        ① **`upperarm` 的零位欧拉骑在万向节锁上**：`upperarm.L ry = −94.4543°`
           （D01 定格真值），离 XYZ 锁带 |ry| = 90° 只有 4.45°。
           `probe_d04_gimbal.py`（纯解析探针）实测：在零位上"绕骨轴拧 δ"，
           **δ=5° 时欧拉分量跳 64.81°，而世界朝向只老实走 5°**（放大 13×）；
           δ=1° 只放大 3.2×，δ≥10° 又恢复 1.0× ⟹ 是一条**谐振带**，不是单调病态。
        ② 所以"把修正摊开"还**不够**，必须选对摊开的位置：上升沿只有 4 帧、
           权重却高达 0.84 ⟹ 那一帧的修正量恰好落进谐振带（实测
           `max_frame_step_deg` 76.85° @ f1，而世界只走 12.84°）。改到**平台之后**
           才既没跳变（20.439°，与修正关闭时逐位相同）又回零位（0.0885°）。
        ⟹ 这也回答了"为什么不能一帧到位"：不是数值精度问题，是**表示病态**问题。

    作用骨（`ROLL_BONES`，默认全部 6 根臂骨）：
        `rr0`（修正关闭）实测和乐分布 = `forearm.L/hand.L 30.55°`、
        `forearm.R/hand.R 4.55°`、`upperarm.L 18.11°`、`upperarm.R 12.11°`
        —— **近端也吃到 12~18°**，所以不能只修远端（只修远端时残 18.11° 在
        `upperarm.L` 上，`end_roll_ok` 会红）。全 6 根一起修 = 0.0885°。
    ══════════════════════════════════════════════════════════════════════════
    """
    if weight <= 1e-9:
        return
    pose_bone = arm.pose.bones[name]
    reference = Quaternion(ZERO_BASIS[name])
    direction_now = Vector(A.bone_direction(arm, name))
    if direction_now.length < 1e-9:
        return
    direction_now.normalize()
    # 零位骨轴 → 当前骨轴的**最小**旋转，套在零位朝向上 = 当前方向的"零滚转参考"
    turn = ZERO_DIR[name].rotation_difference(direction_now)
    reference = (turn @ reference).normalized()
    now = pose_bone.matrix.to_3x3().to_quaternion().normalized()
    # ★ 四元数双覆盖：`q` 与 `−q` 是同一个旋转。若两者在**相反半球**，`slerp`
    #   会走**长弧**（>180°）而不是短弧。先统一到同半球，slerp 才是"最小滚转修正"。
    #   （注意：f1 实测那个 76.85°/帧 的跳变**不是**这个原因 —— 它被
    #    `arm_world_step_trace` 证伪为纯表示跳变，根因是 `upperarm` 撞进万向节锁，
    #    已由 `ROLL_BONES` 白名单排除。这里保留双覆盖归一只是为了数学正确。）
    if now.dot(reference) < 0.0:
        reference.negate()
    blended = now.slerp(reference, max(0.0, min(1.0, weight)))
    matrix = blended.to_matrix().to_4x4()
    matrix.translation = pose_bone.matrix.translation
    pose_bone.matrix = matrix
    bpy.context.view_layer.update()
    pose[name] = JS._unwrap_xyz(
        JS._PREV_EULER.get(name),
        tuple(math.degrees(v) for v in pose_bone.rotation_euler))


# =============================================================== 专属门禁
def _sym_metrics(arm):
    """当前帧的左右对称指标（只读骨骼，便宜 —— 可以逐帧跑）。"""
    fists, elbows, shoulders = {}, {}, {}
    for side in SIDES:
        fists[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        shoulders[side] = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbows[side] = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
    dx = abs(abs(fists["L"].x) - abs(fists["R"].x)) * 1000.0
    dz = abs(fists["L"].z - fists["R"].z) * 1000.0
    dy = abs(fists["L"].y - fists["R"].y) * 1000.0
    return {"sym": max(dx, dz, dy),
            "fist": fists, "elbow": elbows, "shoulder": shoulders}


def _break_frame_metrics(arm):
    """破防口径指标（当前帧）：拳横向净距 / 拳（含相对骨盆）/ chest 世界俯仰 / 头颈 y。"""
    lo, hi = PD.head_box()
    fists = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    pelvis_y = A.bone_world(arm, "pelvis", "head").y
    chest_dir = Vector(A.bone_direction(arm, "chest"))
    # ★ 世界俯仰：atan2(dy, dz)。躯干骨朝上 ⟹ 后仰（顶端往 +Y）为正。
    pitch = math.degrees(math.atan2(chest_dir.y, chest_dir.z))
    return {
        "box_lo": Vector(lo), "box_hi": Vector(hi),
        "fist": fists,
        # ★ 双拳横向净距（|x_L| + |x_R|）：**正视里直接可读**的"震开"量。
        "fist_spread_mm": (abs(fists["L"].x) + abs(fists["R"].x)) * 1000.0,
        # ★ 拳沿 +Y 相对**骨盆**的后退量（骨盆水平不动、root 0 位移 ⟹ 干净口径；
        #   躯干后仰不会污染它 —— D03 教训 1 的同一改锚）。
        "fist_back_vs_pelvis_mm": {s: (fists[s].y - pelvis_y) * 1000.0
                                   for s in SIDES},
        "fist_z_mm": {s: fists[s].z * 1000.0 for s in SIDES},
        "chest_pitch_deg": pitch,
        "neck_y": Vector(A.bone_world(arm, "neck", "head")).y,
        "head_y": Vector(A.bone_world(arm, "head", "tail")).y,
    }


def break_assertions(arm, action, samples, meshes):
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 逐帧左右对称（骨骼口径，便宜）—— 震开应是左右同时，不是单侧
    worst_sym = 0.0
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        worst_sym = max(worst_sym, _sym_metrics(arm)["sym"])
    res["max_sym_mm"] = round(worst_sym, 2)
    res["guard_symmetry_hold_ok"] = bool(worst_sym <= GUARD_SYM_MAX_MM)

    # ---- 穿模（网格口径，贵 —— 抽样跑；震开峰 / 平台末 / 归零帧强制入样）
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [IMPACT, HOLD_END, RECOVER_END, TOTAL]))
    worst_clip, worst_clip_at, worst_clip_frame = 0.0, None, None
    clip_by_frame = {}
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        clip_by_frame[frame] = clip["clip_max_mm"]
        if clip["clip_max_mm"] > worst_clip:
            worst_clip = clip["clip_max_mm"]
            worst_clip_at = clip["clip_at"]
            worst_clip_frame = frame
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = worst_clip_at
    res["clip_frame"] = worst_clip_frame
    res["guard_no_face_clip_ok"] = bool(worst_clip <= GUARD_CLIP_MAX_MM)

    # ---- ★★ 破防语义：零位真值 + 逐帧扫描
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _break_frame_metrics(arm)
    per = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _break_frame_metrics(arm)

    # (a) 双臂被震开 —— 双拳横向净距增大 ≥60 mm、拳沿 +Y 相对骨盆后收 ≥60 mm，
    #     且**不允许**任何一侧的拳比零位更靠前（那读成"出拳"不是"被震开"）。
    spread_delta = per[IMPACT]["fist_spread_mm"] - zero["fist_spread_mm"]
    back = {s: per[IMPACT]["fist_back_vs_pelvis_mm"][s]
            - zero["fist_back_vs_pelvis_mm"][s] for s in SIDES}
    res["fist_spread_zero_mm"] = round(zero["fist_spread_mm"], 2)
    res["fist_spread_impact_mm"] = round(per[IMPACT]["fist_spread_mm"], 2)
    res["fist_spread_delta_mm"] = round(spread_delta, 2)
    res["fist_back_vs_pelvis_pull_mm"] = {s: round(back[s], 2) for s in SIDES}
    res["fist_back_pull_mm"] = round(min(back.values()), 2)
    # ★ 正向命名（`_ok` 结尾）—— 门禁收集器把"不以 _ok 结尾的 False bool"也当红项，
    #   所以"不允许出拳"要写成 positive 判据，不能写成 `any_fist_forward`（反向 bool）。
    res["fist_never_forward_ok"] = bool(all(back[s] >= 0.0 for s in SIDES))
    res["guard_break_ok"] = bool(spread_delta >= BREAK_SPREAD_MIN_MM
                                 and min(back.values()) >= BREAK_BACK_MIN_MM
                                 and res["fist_never_forward_ok"])

    # (b) 身体后仰 —— chest 世界俯仰相对零位（正 = 后仰）转 ≥8°（D03 是 4.3°）
    pitch_delta = per[IMPACT]["chest_pitch_deg"] - zero["chest_pitch_deg"]
    res["chest_pitch_zero_deg"] = round(zero["chest_pitch_deg"], 4)
    res["chest_pitch_impact_deg"] = round(per[IMPACT]["chest_pitch_deg"], 4)
    res["chest_pitch_delta_deg"] = round(pitch_delta, 4)
    res["guard_break_torso_ok"] = bool(pitch_delta >= BREAK_PITCH_MIN_DEG)

    # (c) 头颈后甩（附带报告，不做门禁 —— D03 已立口径）
    res["head_back_mm"] = round(
        (per[IMPACT]["head_y"] - zero["head_y"]) * 1000.0, 2)
    res["neck_back_mm"] = round(
        (per[IMPACT]["neck_y"] - zero["neck_y"]) * 1000.0, 2)

    # ---- ★ 硬直（本支头号语义）：平台 8~16 帧 **且** 平台内姿态变化 ≤0.5°
    platform = HOLD_END - IMPACT
    plat_drift = 0.0
    plat_drift_at = None
    for index in range(IMPACT + 1, HOLD_END + 1):
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            step = max(abs(x - y) for x, y in zip(a, b))
            if step > plat_drift:
                plat_drift, plat_drift_at = step, (index, name)
    res["stagger_platform_frames"] = platform
    res["stagger_platform_drift_deg"] = round(plat_drift, 4)
    res["stagger_platform_drift_at"] = plat_drift_at
    res["hitstop_frames"] = platform
    res["hitstop_present"] = bool(platform >= BREAK_PLATFORM_MIN)
    res["guard_break_stagger_ok"] = bool(
        BREAK_PLATFORM_MIN <= platform <= BREAK_PLATFORM_MAX
        and plat_drift <= BREAK_PLATFORM_DRIFT_DEG)

    # ---- ★ 节奏不对称（升 ≤4 帧、降 ≥30 帧）
    risers = sum(1 for f in range(TOTAL) if press(f + 1) > press(f) + 1e-9)
    fallers = sum(1 for f in range(TOTAL) if press(f + 1) < press(f) - 1e-9)
    res["press_rise_frames"] = risers
    res["press_fall_frames"] = fallers
    res["guard_break_impact_ok"] = bool(risers <= BREAK_RISE_MAX_FRAMES
                                       and fallers >= BREAK_FALL_MIN_FRAMES)

    # ---- ★ 末帧回零位（末帧世界姿态 == 零位；末 2 帧步长 ≈ 0）
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()
    end = {}
    for side in SIDES:
        got = Vector(A.bone_world(arm, "hand." + side, "tail"))
        end[side] = round((got - GS.GUARD_FIST[side]).length * 1000.0, 3)
    res["end_pose_mm"] = end
    end_world = 0.0
    end_world_bone = None
    for name, ref in ZERO_WORLD.items():
        got = samples[-1].get(name)
        if got is None:
            continue
        gap = (Vector(got) - Vector(ref)).length * 1000.0
        if gap > end_world:
            end_world, end_world_bone = gap, name
    res["end_world_pose_mm"] = round(end_world, 4)
    res["end_world_pose_bone"] = end_world_bone
    # ★★ 末帧**绕骨轴滚转**是否也回到零位 —— 位置口径**发现不了它**（D02 教训 1 的镜像）：
    #    `end_world_pose_mm` 只比骨根/骨尖坐标；一根骨整体绕自身轴转 18°，
    #    骨根与骨尖**一动都不动**，但蒙皮（袖子/拳套截面）会转 ⟹ 画面里轮廓变。
    #    本支第 1 次渲染实测就撞上了：f60 与 f0 的几何差 0.001 mm，**画面差 3 px**。
    #    ⟹ 补这条世界旋转基口径，把"滚转漂移"从"看不见"变成"量得出"。
    worst_roll, worst_roll_bone = 0.0, None
    roll_per_bone = {}
    for name, ref in ZERO_BASIS.items():
        if name not in arm.pose.bones:
            continue
        quat = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
        ref_quat = Quaternion(ref)
        dot = abs(max(-1.0, min(1.0, quat.dot(ref_quat))))
        gap = math.degrees(2.0 * math.acos(dot))
        if gap > 0.05:
            roll_per_bone[name] = round(gap, 4)
        if gap > worst_roll:
            worst_roll, worst_roll_bone = gap, name
    res["end_roll_deg"] = round(worst_roll, 4)
    res["end_roll_bone"] = worst_roll_bone
    res["end_roll_bones"] = roll_per_bone
    res["end_roll_ok"] = bool(worst_roll <= BREAK_ROLL_MAX_DEG)
    last2 = 0.0
    for index in range(len(samples) - 2, len(samples)):
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            last2 = max(last2, max(abs(x - y) for x, y in zip(a, b)))
    res["end_last2_deg"] = round(last2, 4)
    res["guard_break_recover_ok"] = bool(all(v <= BREAK_END_MAX_MM
                                             for v in end.values())
                                         and end_world <= BREAK_END_MAX_MM
                                         and last2 <= BREAK_LAST2_MAX_DEG)

    # ---- 可达性（逐帧取最差）
    worst_reach = 0.0
    worst_reach_frame = None
    for frame in range(0, TOTAL + 1, 2):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            up = "upperarm." + side
            shoulder = Vector(A.bone_world(arm, up, "head"))
            dims = UE.ARM_LEN[side]
            limit = (dims["upper"] + dims["forearm"] + dims["hand"]) * 0.9995
            need = (fist_target(side, frame) - shoulder).length
            ratio = need / limit
            if ratio > worst_reach:
                worst_reach, worst_reach_frame = ratio, (frame, side)
    res["reach_ratio_max"] = round(worst_reach, 5)
    res["reach_ratio_at"] = worst_reach_frame
    res["reach_ok"] = bool(worst_reach <= REACH_MAX_RATIO)

    # ---- 踝贴死（本支 0 位移）
    plant = {}
    for side in SIDES:
        point = samples[0].get("foot." + side)
        if point is None:
            continue
        travel = max(math.hypot(Vector(s["foot." + side]).x - Vector(point).x,
                                Vector(s["foot." + side]).y - Vector(point).y)
                     for s in samples) * 1000.0
        plant[side] = round(travel, 3)
    res["plant_mm"] = plant
    res["plant_ok"] = bool(all(v <= PLANT_MAX_MM for v in plant.values()))

    # ---- ★ 膝角被动吸收（D03 新立；本支下沉更大 ⟹ **重扫上限**）
    knee_delta = {}
    for side in SIDES:
        angles = []
        for frame in (0, IMPACT):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            upper = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
            lower = Vector(A.bone_direction(arm, "shin." + side)).normalized()
            angles.append(math.degrees(math.acos(
                max(-1.0, min(1.0, upper.dot(lower))))))
        knee_delta[side] = round(abs(angles[1] - angles[0]), 4)
    res["knee_delta_deg"] = knee_delta
    worst_knee = max(knee_delta.values()) if knee_delta else 0.0
    res["knee_delta_max_deg"] = round(worst_knee, 4)
    res["knee_passive_ok"] = bool(worst_knee <= KNEE_DELTA_MAX_DEG)
    scene.frame_set(TOTAL)          # 复位（剪影采样本就在末帧）
    bpy.context.view_layer.update()

    # ---- 峰值/零位拳位（供人看 + 像素换算复核）
    res["zero_fist_mm"] = {s: [round(v * 1000.0, 1)
                              for v in GS.GUARD_FIST[s]] for s in SIDES}
    res["impact_fist_mm"] = {s: [round(v * 1000.0, 1)
                                 for v in per[IMPACT]["fist"][s]]
                             for s in SIDES}
    res["zero_head_box_mm"] = [[round(v * 1000.0, 1) for v in zero["box_lo"]],
                               [round(v * 1000.0, 1) for v in zero["box_hi"]]]
    res["impact_head_box_mm"] = [[round(v * 1000.0, 1)
                                  for v in per[IMPACT]["box_lo"]],
                                 [round(v * 1000.0, 1)
                                  for v in per[IMPACT]["box_hi"]]]
    # ★ 像素复核（D03 教训 3 沿用）：1 mm ≈ 0.556 px（角色 900 px ↔ 1.8 m）
    res["px_per_mm"] = 0.556
    res["spread_delta_px"] = round(spread_delta * 0.556, 2)
    res["fist_back_pull_px"] = round(min(back.values()) * 0.556, 2)

    # ---- 剪影（双手离开胸前：只报不用）
    sil = P.silhouette(arm, "d04")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    if os.environ.get("D04_TRACE"):
        res["trace"] = {str(f): {
            "press": round(press(f), 4),
            "spread": round(per[f]["fist_spread_mm"], 2),
            "back": round(min(per[f]["fist_back_vs_pelvis_mm"].values())
                          - min(zero["fist_back_vs_pelvis_mm"].values()), 2),
            "pitch": round(per[f]["chest_pitch_deg"], 3),
            "head_y": round(per[f]["head_y"] * 1000.0, 1),
        } for f in range(0, TOTAL + 1)}
        # ★ 逐帧欧拉步长（只报不判）：判断 26°/帧 是"真实快速震开"还是欧拉支假跳。
        #   假跳 = 孤峰（前后帧都很小），真快 = 连续几帧都在同一量级。
        step_trace = {}
        for index in range(1, min(len(samples), 12)):
            row = {}
            for name in ARM_BONES + ("shoulder.L", "shoulder.R"):
                ea = samples[index - 1]["euler"].get(name, (0.0, 0.0, 0.0))
                eb = samples[index]["euler"].get(name, (0.0, 0.0, 0.0))
                row[name] = round(max(abs(x - y) for x, y in zip(ea, eb)), 2)
            step_trace[str(samples[index]["frame"])] = row
        res["arm_step_trace"] = step_trace
        # ★ 世界朝向步长（对照 `arm_step_trace`）：用来分辨"欧拉表示跳变"与"真闪帧"。
        #   若欧拉步长很大而世界朝向步长很小 ⟹ 只是换了等价欧拉支（假红）。
        world_trace = {}
        previous = None
        for sample in samples[:12]:
            scene.frame_set(sample["frame"])
            bpy.context.view_layer.update()
            now = {name: arm.pose.bones[name].matrix.to_3x3().to_quaternion()
                   for name in ARM_BONES if name in arm.pose.bones}
            if previous is not None:
                row = {}
                for name in now:
                    dot = abs(max(-1.0, min(1.0, now[name].dot(previous[name]))))
                    row[name] = round(math.degrees(2.0 * math.acos(dot)), 2)
                world_trace[str(sample["frame"])] = row
            previous = now
        res["arm_world_step_trace"] = world_trace
    return res


# =============================================================== 引导
def boot():
    global ZERO, ZERO_WORLD
    ZERO, ZERO_WORLD = {}, {}
    ZERO_BASIS.clear()
    ZERO_DIR.clear()
    IDLE_FIST.clear()

    arm, meshes = GS.boot()

    # ★★ 零位 = 落盘 `Guard_Start` action 的末帧（与 D02/D03 一字不改）
    ZERO, saved_info = _load_d01_end_pose(arm)

    replay = _replay_d01_settle(arm, meshes)
    saved_heads, saved_dirs = _world_snapshot(arm, ZERO)
    replay_heads, replay_dirs = _world_snapshot(arm, replay)
    geom_pos = 0.0
    geom_pos_bone = None
    for name, point in saved_heads.items():
        other = replay_heads.get(name)
        if other is None:
            continue
        gap = (point - other).length * 1000.0
        if gap > geom_pos:
            geom_pos, geom_pos_bone = gap, name
    geom_dir = 0.0
    geom_dir_bone = None
    for name, direction in saved_dirs.items():
        other = replay_dirs.get(name)
        if other is None:
            continue
        dot = max(-1.0, min(1.0, direction.dot(other)))
        gap = math.degrees(math.acos(dot))
        if gap > geom_dir:
            geom_dir, geom_dir_bone = gap, name

    euler_diff = 0.0
    euler_bone = None
    roll_free = {}
    for name, value in ZERO.items():
        if name.startswith("@"):
            continue
        got = replay.get(name)
        if got is None:
            continue
        row = [_f32(a) - _f32(b) for a, b in zip(got, value)]
        worst = max(abs(v) for v in row)
        if worst > euler_diff:
            euler_diff, euler_bone = worst, name
        if worst > 0.5:
            roll_free[name] = [round(v, 4) for v in row]

    d01_ref, ref_src = _load_d01_end_ref()
    ref_diff = 0.0
    for name, value in d01_ref.items():
        got = ZERO.get(name)
        if got is None:
            continue
        ref_diff = max(ref_diff, max(abs(_f32(a) - _f32(b))
                                     for a, b in zip(got, value)))

    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    ZERO_WORLD = {n: tuple(v) for n, v in saved_heads.items()}
    for name in A.PROBE_TAILS:
        if name in arm.pose.bones:
            ZERO_WORLD[name + ".tail"] = tuple(A.bone_world(arm, name, "tail"))
    # ★ 零位世界旋转基（含绕骨轴滚转）—— 位置口径看不见它
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            ZERO_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES:
        ZERO_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()

    for side in SIDES:
        IDLE_FIST[side] = Vector(GS.IDLE_FIST[side])

    D01_SAME_SOLVE.update({
        "saved": saved_info,
        "ref_src": ref_src,
        "ref_diff": round(ref_diff, 8),
        "ref_ok": bool(d01_ref and ref_diff <= D01_REF_TOL_DEG),
        "geom_pos_mm": round(geom_pos, 6), "geom_pos_bone": geom_pos_bone,
        "geom_dir_deg": round(geom_dir, 6), "geom_dir_bone": geom_dir_bone,
        "geom_ok": bool(geom_pos <= D01_GEOM_POS_MAX_MM
                        and geom_dir <= D01_GEOM_DIR_MAX_DEG),
        "euler_diff": round(euler_diff, 6), "euler_bone": euler_bone,
        "roll_free": roll_free,
    })

    # 零位几何（调参用）
    zrow = _break_frame_metrics(arm)
    A.report("D04_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "impact": IMPACT, "hold_end": HOLD_END, "recover_end": RECOVER_END,
        "platform_frames": HOLD_END - IMPACT,
        "segments": 1, "hit_points": 0, "root_motion_m": [0.0, 0.0],
        "zero_source": "%s@%d（落盘 action，非重演）"
                        % (saved_info.get("action"), saved_info.get("last_frame")),
        "zero_fist_mm": {s: [round(v * 1000.0, 2) for v in GS.GUARD_FIST[s]]
                         for s in SIDES},
        "zero_fist_spread_mm": round(zrow["fist_spread_mm"], 2),
        "zero_head_box_mm": [[round(v * 1000.0, 1) for v in zrow["box_lo"]],
                             [round(v * 1000.0, 1) for v in zrow["box_hi"]]],
        "zero_pelvis_z_mm": round(GS.Z_SEAM * 1000.0, 3),
        "press_drop_mm": PRESS_DROP_MM,
        "press_fist_offset_mm": [PRESS_OUT_MM, PRESS_BACK_MM, PRESS_DOWN_MM],
        "torso_press_deg": TORSO_PRESS,
        "elbow_break_dir": {s: [round(v, 4) for v in ELBOW_BREAK[s]]
                            for s in SIDES},
        "d01_saved": saved_info,
        "d01_report_ref_src": ref_src,
        "d01_saved_vs_report_max_diff": round(ref_diff, 8),
        "d01_replay_geom_pos_mm": round(geom_pos, 6),
        "d01_replay_geom_pos_bone": geom_pos_bone,
        "d01_replay_geom_dir_deg": round(geom_dir, 6),
        "d01_replay_geom_dir_bone": geom_dir_bone,
        "d01_replay_euler_max_diff_deg": round(euler_diff, 6),
        "d01_replay_euler_worst_bone": euler_bone,
        "d01_replay_roll_free_bones": roll_free,
        "note": ("D04 破防：零位 = D01 落盘末帧；升 4 / 平台 10 / 降 40；"
                 "双臂被震开（横向外张 + 后收 + 肘外张）+ 身体后仰 ≥8° + 脚纹丝不动；"
                 "首尾共用同一 dict；已撤下 guard_cover_ok / guard_elbow_ok"),
    })
    return arm, meshes


def main():
    arm, meshes = boot()

    JS._PREV_EULER.clear()
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for name in ARM_BONES + LEG_BONES:
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    # ★ 首键 = 零位（= D01 末帧，含绕骨轴滚转的逐位相同）
    keyframes = [(0, ZERO)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))
    # ★★ 尾部**不钉 `dict(ZERO)`**（D03 第 2 号教训）：钉值会凭空造出一个
    #   零空间滚转跳变。改为**全程求解** —— 尾部输入恒等于零位 ⟹ 解出的姿态
    #   逐帧恒定、世界姿态 = 零位，欧拉路径连续。"末帧 == 零位"由此从**构造保证**
    #   换成**实测门禁**（`guard_break_recover_ok` 的三口径，其中世界姿态比欧拉更强）。

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "防御",
        "note": ("破防：双臂被震开（横向外张 + 后收）、身体后仰、明显硬直；"
                 "脚不动（零位 = D01 举防定格），0 命中点、0 位移"),
        "antic_frame": IMPACT,
        "hit_frame": IMPACT,
        "cancel_frame": RECOVER_END,
        "stagger_end_frame": HOLD_END,
        "hitstop_frames": HOLD_END - IMPACT,
        "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "hit_point_m": None,
        "start_pose_ref": "D01 Guard_Start 末帧",
        "end_pose_ref": "D01 Guard_Start 末帧（破防恢复后回到护架，可接 Guard_Loop）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "BREAK": IMPACT,
                           "STAGGER_END": HOLD_END,
                           "RECOVER": RECOVER_END, "END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta,
                                     foot_probe=("foot.L", "foot.R"),
                                     slide_tolerance_mm=SLIDE_MAX_MM)
    report.update(break_assertions(arm, action, samples, meshes))
    report["meta"] = meta

    # 起手接合：f0 必须与 D01 末帧**逐位相同**（两边都过 float32）
    delta0 = 0.0
    for name, ref in ZERO.items():
        if name.startswith("@"):
            continue
        got = samples[0]["euler"].get(name)
        if got is None:
            continue
        delta0 = max(delta0, max(abs(_f32(a) - _f32(b))
                                 for a, b in zip(got, ref)))
    report["ua_start_delta_deg"] = round(delta0, 8)
    report["ua_start_ok"] = bool(delta0 <= SEAM_TOL)

    # 零位 = D01 末帧（三条守卫）
    report["d01_end_saved_ok"] = bool(D01_SAME_SOLVE["saved"].get("found")
                                      and D01_SAME_SOLVE["ref_ok"])
    report["d01_saved_vs_report_max_diff"] = D01_SAME_SOLVE["ref_diff"]
    report["d01_report_ref_src"] = D01_SAME_SOLVE["ref_src"]
    report["d01_replay_geom_ok"] = D01_SAME_SOLVE["geom_ok"]
    report["d01_replay_geom_pos_mm"] = D01_SAME_SOLVE["geom_pos_mm"]
    report["d01_replay_geom_dir_deg"] = D01_SAME_SOLVE["geom_dir_deg"]
    report["d01_replay_euler_max_diff_deg"] = D01_SAME_SOLVE["euler_diff"]
    report["d01_replay_euler_worst_bone"] = D01_SAME_SOLVE["euler_bone"]
    report["d01_replay_roll_free_bones"] = D01_SAME_SOLVE["roll_free"]

    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("D04_REPORT", report)

    if not SKIP_RENDER:
        frames = [0, 2, IMPACT, HOLD_END, 34, RECOVER_END, TOTAL]
        A.render_pose_sheet(arm, action, frames, "guardbreak",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D04_DONE failed=%s" % report["failed"])
    print("D04_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D04_FAILURE " + traceback.format_exc())
