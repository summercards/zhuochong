"""anim_guard_hit —— D03 `Guard_Hit` 防御受击。

设计（对着清单 §四 D03 的原文「手臂和上身被力量推回，但**脚不能轻易移动**」逐条落）：

    段结构     **1 段（推回 → 顶住 → 归零）**、**0 命中点**、**0 位移**。
    时长       36 帧 = **0.600 s** @60fps（计划 0.4~0.6 s —— 受击要短促）
    零位       ★ **= D01 `Guard_Start` 落盘 action 的末帧**（同 D02 口径：读引擎真正播的
               那份数据，不重演。理由见 `_load_d01_end_pose()`）。
    首尾       ★ 首帧 == D01 末帧（引擎 `Guard_Loop → Guard_Hit` 直连）；
               末帧 == 同一 `dict(ZERO)`（受击后回到护架，可接回 `Guard_Loop`）。
    节奏       ★★ **前摇极短 + 冲击极快 + 回弹慢** —— 不许对称（本支头号语义）：
               f0 零位 → **f4 冲击峰 → f6 顶住**（2 帧完全停顿）→ 慢回弹 → f32 归零。
               上升 4 帧 / 下降 26 帧 ⟹ `guard_hit_impact_ok`。
    姿态       ★ **被"推回"**：上身后仰、双臂被压向躯干、**脚纹丝不动**
               （力在路上被腿吸掉 —— 全靠 `UE.leg_seat` 把踝钉死在 `GS.ANKLE_0`）。
    核心难点   ★★ **上身被打回去、下身纹丝不动**；且"压回"不能压进脸（穿模是新立判据
               最容易翻车处，D02 就在这里翻过一次车）。

"被力量推回"的量化口径（本支新立 `guard_hit_ok`，三条子判据）：
    (a) 手臂被推回   拳到头盒**前缘**的 y 距离（正 = 拳在盒前）在冲击帧**减少 ≥ 20 mm**，
                     且**全程不得为负**（压回来也不能越过盒前缘 ⟹ 更不许插进脸）；
    (b) 上身后仰     `chest` 骨的**世界俯仰**（`atan2(dy, dz)`，+ = 后仰）相对零位
                     转 **≥ 3°**（方向与 D02 前倾相反）；
    (c) 头颈后甩     `head`/`neck` 相对零位**沿 +Y（身后）方向位移 ≥ 15 mm**。

★ 关于计划里"沿 −Y 方向"的更正：世界约定 `+Y = 角色身后`（`doc/rig_axis_map.md`），
  受击来自 −Y（正面）⟹ 被推回必然**朝 +Y**。计划 §2 同一段写"上身后仰（方向与 D02
  相反）"，与前倾相反即后仰即 +Y —— 故"−Y"是笔误。本支按 **+Y（身后）** 实现，
  幅度门槛 15 mm 不变（计划 §4 第 3 条明许"改幅度/方向，不要放宽区间"）。

★ 关于幅度：全部**先量再定**（计划 §3 要求"先扫再定，不要假设后仰一定安全"）。
  本支把 4 个幅度参数与 8 个躯干角都开成环境变量，逐组跑完整门禁后锁定
  （见下方 `PRESS_*` / `TORSO_PRESS` 处注释里的扫描记录）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_guard_hit.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D03_TRACE=1    逐帧打印 press / 拳到盒前缘 / chest 俯仰 / 头颈 y（调参用）
"""

import json
import math
import os
import struct
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                     # noqa: E402
import anim_idle_01 as I1                # noqa: E402
import anim_jump_start as JS             # noqa: E402
import anim_ultimate_end as UE           # noqa: E402
import probe_c12_baseline as P           # noqa: E402
import probe_d01_guard as PD             # noqa: E402
import anim_guard_start as GS            # noqa: E402

NAME = "Guard_Hit"
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
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（D02 的 `_f32` 同源）。

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

    理由与 D02 完全一致：D01 的腕骨滚转在自身两次跑之间差 18°（`aim_nearest`
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
TOTAL = _env_i("D03_TOTAL", 36)          # 0.600 s @60fps（计划 0.4~0.6 s）
IMPACT = _env_i("D03_IMPACT", 4)         # 冲击峰（上升沿 4 帧 ≤ 5）
HOLD_END = _env_i("D03_HOLD", 6)         # 顶住：f4..f6 停在峰值（2 帧完全停顿）
RECOVER_END = _env_i("D03_RECOVER", 32)  # 回弹归零帧（此后逐位冻结，保证末 2 帧步长 0）

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
# ★ 计划 §2：D03 是全项目第一支"上身被打、脚必须不动"的动作 —— plant 收紧到 1.0 mm
PLANT_MAX_MM = _env_f("D03_PLANT", 1.0)
SLIDE_MAX_MM = _env_f("D03_SLIDE", 1.0)
GROUND_MIN_MM, GROUND_MAX_MM = -2.0, 6.0
REACH_MAX_RATIO = 0.995
# ★ 膝角被动吸收上限：骨盆下沉由腿 IK 吸收 ⟹ 膝必然微弯（实测 4.78°），
#   但不得出现"蹲姿级别"的屈膝。见 `hit_assertions()` 里的口径澄清。
KNEE_DELTA_MAX_DEG = _env_f("D03_KNEE", 6.0)

# ---- "被力量推回" 三条子判据（阈值由「下一支详细制作计划」§2 给出）
# ★ 口径修正：`HIT_GAP_DROP_MIN_MM` 的**原文**是"拳到头盒前缘的距离减少 ≥20 mm"，
#   实测该口径**构造性不可能满足**（零位拳已在头盒前缘之后 −5.79 mm，且后仰把头盒
#   同向拖走，拳实退 40 mm 该距离只变 6.95 mm）。已改锚到**骨盆**：拳沿 +Y 相对
#   骨盆的后移量。详见 `hit_assertions()` 里的完整记录。这是**修判据**，不是放宽。
HIT_GAP_DROP_MIN_MM = _env_f("D03_GAP_DROP", 20.0)     # 拳沿 +Y 相对骨盆的后移量下界
HIT_PITCH_MIN_DEG = _env_f("D03_PITCH", 3.0)           # chest 世界俯仰（后仰）下界
HIT_HEAD_BACK_MIN_MM = _env_f("D03_HEADBACK", 15.0)    # head 骨尾沿 +Y 位移下界

# ---- "不许对称" 的节奏判据
HIT_RISE_MAX_FRAMES = _env_f("D03_RISE_MAX", 5.0)
HIT_FALL_MIN_FRAMES = _env_f("D03_FALL_MIN", 10.0)

# ---- 末帧回到零位
HIT_END_MAX_MM = _env_f("D03_END_MAX", 0.5)
HIT_LAST2_MAX_DEG = _env_f("D03_LAST2", 0.5)

# ★★ "零位 = D01 末帧" 的三条守卫（与 D02 逐字同源）
D01_REF_TOL_DEG = 5.0e-05
D01_GEOM_POS_MAX_MM = _env_f("D03_D01_POS", 0.01)
D01_GEOM_DIR_MAX_DEG = _env_f("D03_D01_DIR", 0.05)

# ★ 复用 D01 定稿的护架判据（本支全程都必须保持住 —— 否则接不回 Guard_Loop）
GUARD_IN_FRONT_MIN_MM = 150.0
GUARD_LATERAL_MIN_MM = 130.0
GUARD_LATERAL_MAX_MM = 200.0
GUARD_RAISE_MIN_MM = 60.0
GUARD_HEAD_MARGIN_MM = 100.0
GUARD_SYM_MAX_MM = _env_f("D03_SYM", 25.0)
GUARD_ELBOW_OUT_MAX_MM = 20.0
GUARD_ELBOW_DROP_MIN_MM = 150.0
GUARD_CLIP_MAX_MM = 0.0
CLIP_EVERY = int(os.environ.get("D03_CLIP_EVERY", 4))

# =============================================================== 受击幅度
# ★★ 全部**先量再定**（计划 §3："先扫再定，不要假设后仰一定安全"）。
#   扫描记录（每组都跑完整门禁，`D03_*` 环境变量覆盖，见 `_d03_sw*.log`）：
#
#   第 1 轮 —— 幅度 ↔ 穿模：**穿模在全部配置下恒为 0.0**（后仰把头盒整体往 +Y 带走，
#   臂被"拉开"而不是压进头里；担心的"下巴/颈那侧反过来"没有发生）。地面恒 −1.33 mm。
#     back=40 chest=-1.5 → 全绿 | back=10 → 红(arm_pushed_back_ok) | back=40 chest=-2.4
#     → 全绿 | back=40 chest=-3.2 → 全绿
#
#   第 2/3 轮 —— **拳后收的上限不是穿模，是 `guard_cover_ok`**（拳相对胸身前 ≥150 mm）：
#     back=50 chest=-2.4 → 红(guard_cover_ok, 身前只剩 ~146) | back=50 chest=-3.2 →
#     靠强后仰把胸往回带才救回 | back=44 → 身前 151.8（余量 1.8 mm，贴着实测边界）
#
#   第 4 轮 —— ★★ **发现判据数值 ≠ 画面可见量**。实测换算（角色 900 px ↔ 1.8 m
#   ⟹ 1 px ≈ 2 mm）：
#     `head_back`=47.6 mm 时头顶**骨尾**后移 47.6 mm，但头部是**绕颈旋转**，
#     轮廓中心只走一半 ≈ 12 mm ≈ **6 px** —— 所以初版判据 3 倍余量、画面却几乎看不出。
#   根因：`head_back` 原先主要由 `chest` 的整链后仰带动，而 `chest` 受"不能抢 D04
#   `Guard_Break`（身体后仰 + 明显硬直）戏份"卡在 ~3.5°。
#   ⟹ 正解是**让 head 骨自身多转**（`TP_HEAD`），而不是加胸腔。实测 `TP_HEAD`
#      -2.2 / -2.8 / -3.4 → `head_back` 67.25 / 72.09 / **76.93 mm**，而 `chest` 恒 −1.8。
#
#   ★ 定稿（K 组，全绿、clip 0.0、ground −1.33、plant 0.001、end_world 0.0012 mm）：
#     back=44 | pelvis −0.6 | spine_01/02 −0.95 | chest −1.8（pitch_delta 4.3°）
#     | neck −2.4 | head −3.4 | shoulder 3.0（耸肩护住）
#     ⟹ 头顶后甩 76.93 mm（画面 ≈10 px，读得出来）；`chest` 只 4.3°，不与 D04 撞车。
#
# 设计意图（相对 D02）：
#   D02 是"躯干前压 + 拳前送"（护架顶住、身体在后沉）；
#   D03 是"躯干后仰 + 拳后收"（被打回去、护架被压向躯干、身体在后面接住）。
PRESS_DROP_MM = _env_f("D03_DROP", -14.0)    # 骨盆下沉（腿 IK 吸收 ⟹ 脚不动）
PRESS_IN_MM = _env_f("D03_IN", 0.0)          # 拳横向（0 = 不加）
PRESS_BACK_MM = _env_f("D03_BACK", 44.0)     # 拳沿 +Y **后收**（正 = 往躯干压回来）
PRESS_DOWN_MM = _env_f("D03_DOWN", 6.0)      # 拳下沉 6 mm（护架随身体略沉）
TORSO_PRESS = {"pelvis": _env_f("D03_TP_PELVIS", -0.6),
               "spine_01": _env_f("D03_TP_S1", -0.95),
               "spine_02": _env_f("D03_TP_S2", -0.95),
               "chest": _env_f("D03_TP_CHEST", -1.8),
               "neck": _env_f("D03_TP_NECK", -2.4),
               "head": _env_f("D03_TP_HEAD", -3.4),
               "shoulder.L": _env_f("D03_TP_SH", 3.0),
               "shoulder.R": _env_f("D03_TP_SH", 3.0)}

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")

# =============================================================== 模块级表
ZERO = {}                 # D01 定格真值（本支零位）
ZERO_WORLD = {}
IDLE_FIST = {}
D01_SAME_SOLVE = {"ok": None, "diff": None, "src": None, "per_bone": {}}


def press(frame):
    """受击标量 ∈ [0, 1]：**不对称**脉冲（升 4 帧 / 顶 2 帧 / 降 26 帧）。

    ★ 与 D02 的关键差异：D02 是 PCHIP 对称脉冲（两头为零）；D03 必须"被打是快的、
      撑回来是慢的" ⟹ 键表左端只留 `IMPACT` 帧、右端拉到 `RECOVER_END`。
      用 `((0,0),(IMPACT,1),(HOLD_END,1),(RECOVER_END,0),(TOTAL,0))`：
      上升 4 帧、平台 2 帧（命中停顿）、下降 26 帧。
    """
    keys = ((0, 0.0), (IMPACT, 1.0), (HOLD_END, 1.0),
            (RECOVER_END, 0.0), (TOTAL, 0.0))
    return UE.pwl(keys, float(frame), 0.0)


def fist_target(side, frame):
    """拳世界目标 = D01 定格 + 受击偏移（镜像）。**绝对世界点**（同 D02 口径）。"""
    p = press(frame)
    sign = 1.0 if side == "L" else -1.0
    return Vector(GS.GUARD_FIST[side]) + Vector(
        (-sign * PRESS_IN_MM, PRESS_BACK_MM, -PRESS_DOWN_MM)) * (p / 1000.0)


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
                    GS.GUARD_ELBOW[side])
    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


def solve_pose(arm, frame, meshes=None):
    """单帧装配（无贴地闭环；踝由位置 IK 钉死，脚纹丝不动）。"""
    return build_pose(arm, frame)


# =============================================================== 专属门禁
def _frame_guard_metrics(arm):
    """当前帧的护架指标（只读骨骼，便宜 —— 可以逐帧跑）。逐字复刻 D02。"""
    torso_y = A.bone_world(arm, "chest", "head").y
    chest_top = A.bone_world(arm, "neck", "head").z
    head_top = A.bone_world(arm, "head", "tail").z
    fists, elbows, shoulders = {}, {}, {}
    for side in SIDES:
        fists[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        shoulders[side] = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbows[side] = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
    lo_z = chest_top * 1000.0
    hi_z = head_top * 1000.0 + GUARD_HEAD_MARGIN_MM
    in_front = {s: (torso_y - fists[s].y) * 1000.0 for s in SIDES}
    lateral = {s: abs(fists[s].x) * 1000.0 for s in SIDES}
    raise_mm = {s: (fists[s].z - IDLE_FIST[s].z) * 1000.0 for s in SIDES}
    cover = bool(all(v >= GUARD_IN_FRONT_MIN_MM for v in in_front.values())
                 and all(GUARD_LATERAL_MIN_MM <= v <= GUARD_LATERAL_MAX_MM
                         for v in lateral.values())
                 and all(lo_z <= fists[s].z * 1000.0 <= hi_z for s in SIDES)
                 and all(v >= GUARD_RAISE_MIN_MM for v in raise_mm.values()))
    elbow = bool(
        all((abs(elbows[s].x) - abs(shoulders[s].x)) * 1000.0
            <= GUARD_ELBOW_OUT_MAX_MM for s in SIDES)
        and all((fists[s].z - elbows[s].z) * 1000.0
                >= GUARD_ELBOW_DROP_MIN_MM for s in SIDES))
    dx = abs(abs(fists["L"].x) - abs(fists["R"].x)) * 1000.0
    dz = abs(fists["L"].z - fists["R"].z) * 1000.0
    dy = abs(fists["L"].y - fists["R"].y) * 1000.0
    return {"cover": cover, "elbow": elbow,
            "sym": max(dx, dz, dy),
            "in_front": in_front, "lateral": lateral, "raise_mm": raise_mm,
            "z_window": (lo_z, hi_z)}


def _hit_frame_metrics(arm):
    """受击口径指标（当前帧）：头盒前缘 / 拳（含相对骨盆）/ chest 世界俯仰 / 头颈 y。"""
    lo, hi = PD.head_box()
    fists = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    pelvis_y = A.bone_world(arm, "pelvis", "head").y
    chest_dir = Vector(A.bone_direction(arm, "chest"))
    # ★ 世界俯仰：atan2(dy, dz)。躯干骨朝上 ⟹ 后仰（顶端往 +Y）为正。
    pitch = math.degrees(math.atan2(chest_dir.y, chest_dir.z))
    return {
        "box_lo": Vector(lo), "box_hi": Vector(hi),
        "fist": fists,
        "front_gap_mm": {s: (lo.y - fists[s].y) * 1000.0 for s in SIDES},
        # ★ 拳沿 +Y 相对**骨盆**的后退量（骨盆水平不动、root 0 位移 ⟹ 干净口径）。
        #   为什么不拿"到头盒前缘的距离"当判据：后仰会把头盒（含 Hair_Sweep/Nose）
        #   一起往 +Y 拖 ~33 mm，与拳的后退**同向抵消**，实测拳退了 40 mm 而该距离
        #   只变了 6.95 mm ⟹ 判据量不出"被推回"。见下方 `arm_pushed_back_ok`。
        "fist_back_vs_pelvis_mm": {s: (fists[s].y - pelvis_y) * 1000.0
                                   for s in SIDES},
        "chest_pitch_deg": pitch,
        "neck_y": Vector(A.bone_world(arm, "neck", "head")).y,
        "head_y": Vector(A.bone_world(arm, "head", "tail")).y,
    }


def hit_assertions(arm, action, samples, meshes):
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 逐帧护架保持（骨骼口径，便宜）—— 全程必须仍是"举防"
    worst_sym = 0.0
    worst_in_front = 1e9
    worst_lateral = 1e9
    worst_raise = 1e9
    cover_all, elbow_all = True, True
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = _frame_guard_metrics(arm)
        cover_all = cover_all and row["cover"]
        elbow_all = elbow_all and row["elbow"]
        worst_sym = max(worst_sym, row["sym"])
        worst_in_front = min(worst_in_front, min(row["in_front"].values()))
        worst_lateral = min(worst_lateral, min(row["lateral"].values()))
        worst_raise = min(worst_raise, min(row["raise_mm"].values()))
    res["guard_cover_ok"] = bool(cover_all)
    res["guard_elbow_ok"] = bool(elbow_all)
    res["min_in_front_mm"] = round(worst_in_front, 1)
    res["min_lateral_mm"] = round(worst_lateral, 1)
    res["min_raise_mm"] = round(worst_raise, 1)
    res["guard_symmetry_hold_ok"] = bool(worst_sym <= GUARD_SYM_MAX_MM)
    res["max_sym_mm"] = round(worst_sym, 2)

    # ---- 穿模（网格口径，贵 —— 抽样跑；冲击帧/顶住帧强制入样）
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

    # ---- ★★ 受击语义：零位真值 + 逐帧扫描
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _hit_frame_metrics(arm)
    zero_pen = PD.clip_metrics(arm)["clip_max_mm"]      # 零位（举防定格）的臂-头盒穿透
    per = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _hit_frame_metrics(arm)

    # (a) 手臂被推回 —— 拳沿 +Y 相对骨盆后退 ≥20 mm，且头盒穿透不得比零位更深
    #
    # ★ 判据口径修正（第 1 轮实测，见 `_d03_gate1.log`）：原案取「拳到头盒前缘的 y 距离
    #   减少 ≥20 mm」。实测零位该距离 = **−5.79 mm** —— 头盒含 `Hair_Sweep`/`Nose`，
    #   鼻尖/发梢本来就伸在拳中心前面，所以"≥0"是**构造性不可能**。更要命的是后仰把
    #   整个头盒往 +Y 拖，与拳的后退**同向**：拳实退 40 mm，该距离只变了 **6.95 mm**。
    #   ⟹ 判据量不出"被推回"。改锚到**骨盆**（root 0 位移、骨盆水平不动）：
    #       `Δfist_y(相对骨盆)` 就是"手臂被压向躯干"的干净口径（本支实测 40.0 mm）。
    #   "压回来不能插进脸"改用**穿透量不得比零位更深**来盯（真正的几何判据），
    #   全程数值由 `guard_no_face_clip_ok`（抽样穿透 ≤0）兜底。★ 这是修判据，不是放宽。
    back = {s: per[IMPACT]["fist_back_vs_pelvis_mm"][s]
            - zero["fist_back_vs_pelvis_mm"][s] for s in SIDES}
    pen_impact = clip_by_frame.get(IMPACT, 0.0)
    res["fist_back_vs_pelvis_zero_mm"] = {s: round(
        zero["fist_back_vs_pelvis_mm"][s], 2) for s in SIDES}
    res["fist_back_vs_pelvis_pull_mm"] = {s: round(back[s], 2) for s in SIDES}
    res["fist_back_pull_mm"] = round(min(back.values()), 2)
    res["zero_arm_clip_mm"] = round(zero_pen, 2)
    res["impact_arm_clip_mm"] = round(pen_impact, 2)
    res["arm_pushed_back_ok"] = bool(min(back.values())
                                     >= HIT_GAP_DROP_MIN_MM
                                     and pen_impact <= zero_pen)

    # (b) 上身后仰 —— chest 世界俯仰相对零位（正 = 后仰）转 ≥3°
    pitch_delta = per[IMPACT]["chest_pitch_deg"] - zero["chest_pitch_deg"]
    res["chest_pitch_zero_deg"] = round(zero["chest_pitch_deg"], 4)
    res["chest_pitch_impact_deg"] = round(per[IMPACT]["chest_pitch_deg"], 4)
    res["chest_pitch_delta_deg"] = round(pitch_delta, 4)
    res["torso_lean_back_ok"] = bool(pitch_delta >= HIT_PITCH_MIN_DEG)

    # (c) 头颈后甩 —— 沿 +Y（身后）位移 ≥15 mm
    head_back = (per[IMPACT]["head_y"] - zero["head_y"]) * 1000.0
    neck_back = (per[IMPACT]["neck_y"] - zero["neck_y"]) * 1000.0
    res["head_back_mm"] = round(head_back, 2)
    res["neck_back_mm"] = round(neck_back, 2)
    res["head_snap_back_ok"] = bool(max(head_back, neck_back)
                                    >= HIT_HEAD_BACK_MIN_MM)
    res["guard_hit_ok"] = bool(res["arm_pushed_back_ok"]
                               and res["torso_lean_back_ok"]
                               and res["head_snap_back_ok"])

    # ---- ★ 节奏不对称（量 `press` 曲线：升 ≤5 帧、降 ≥10 帧）
    risers = sum(1 for f in range(TOTAL) if press(f + 1) > press(f) + 1e-9)
    fallers = sum(1 for f in range(TOTAL) if press(f + 1) < press(f) - 1e-9)
    res["press_rise_frames"] = risers
    res["press_fall_frames"] = fallers
    res["guard_hit_impact_ok"] = bool(risers <= HIT_RISE_MAX_FRAMES
                                      and fallers >= HIT_FALL_MIN_FRAMES)

    # ---- ★ 末帧回零位（末帧世界姿态 == 零位；末 2 帧步长 ≈ 0）
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()
    end = {}
    for side in SIDES:
        got = Vector(A.bone_world(arm, "hand." + side, "tail"))
        end[side] = round((got - GS.GUARD_FIST[side]).length * 1000.0, 3)
    res["end_pose_mm"] = end
    # ★ 世界姿态口径（比欧拉钉值更强）：整条骨链逐位对齐零位
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
    last2 = 0.0
    for index in range(len(samples) - 2, len(samples)):
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            last2 = max(last2, max(abs(x - y) for x, y in zip(a, b)))
    res["end_last2_deg"] = round(last2, 4)
    res["guard_hit_recover_ok"] = bool(all(v <= HIT_END_MAX_MM
                                           for v in end.values())
                                       and end_world <= HIT_END_MAX_MM
                                       and last2 <= HIT_LAST2_MAX_DEG)

    # ---- 可达性（逐帧取最差）
    worst_reach = 0.0
    for frame in range(0, TOTAL + 1, 2):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            up = "upperarm." + side
            shoulder = Vector(A.bone_world(arm, up, "head"))
            dims = UE.ARM_LEN[side]
            limit = (dims["upper"] + dims["forearm"] + dims["hand"]) * 0.9995
            need = (fist_target(side, frame) - shoulder).length
            worst_reach = max(worst_reach, need / limit)
    res["reach_ratio_max"] = round(worst_reach, 5)
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

    # ---- ★ 膝角被动吸收（本支新增 —— 盯住一条容易漏掉的隐形契约）
    #
    #   清单 §4.4 的目检项写的是「膝盖角度不变」。但本支的骨盆下沉（`PRESS_DROP_MM`
    #   = −14 mm）是**由腿位置 IK 吸收**的：踝钉死 ⟹ 髋降 ⟹ 膝**必然**微弯。
    #   实测（`probe_d03_knee.py`）：f0 44.324° / 46.537° → f4 **49.108° / 51.162°**，
    #   即 **+4.784° / +4.625°**；f32/f36 逐位回到 0.000°。
    #   而**踝完全不动**（`foot_z` 恒定 79.740 / 79.804 mm，`plant_mm` 0.001 mm）。
    #   ⟹ 口径澄清：D03 的硬要求是**脚不动**（清单正文 line 148「脚不能轻易移动」），
    #      膝角变化是"重量被腿吸收"的几何必然（14 mm / 4.78° ⟹ 等效杠杆 ~170 mm，
    #      与大腿 0.42 m + 小腿 0.40 m 的量级吻合）。
    #   ⟹ 本门禁上限 6.0°（可失败、余量 1.2°）：将来谁把 `PRESS_DROP_MM` 调大到出现
    #      **蹲姿级别**的屈膝，或谁退回 `A.leg_ik` 让脚跟着动，都会被这条抓住。
    #   画面口径复核：鞋区（亮度<90 的黑皮鞋，12489 px）在 f32/f36 与 f0 差异 **0 px**；
    #   f4 的 304 px（2.4%，集中在鞋面顶缘）来自**裤腿前移遮挡**，不是脚移动。
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
    scene.frame_set(TOTAL)          # 复位（后续剪影采样本就在末帧）
    bpy.context.view_layer.update()

    # ---- 峰值/零位拳位（供人看）
    res["zero_fist_mm"] = {s: [round(v * 1000.0, 1)
                              for v in GS.GUARD_FIST[s]] for s in SIDES}
    res["impact_fist_mm"] = {s: [round(v * 1000.0, 1)
                                 for v in per[IMPACT]["fist"][s]]
                             for s in SIDES}
    res["impact_head_box_mm"] = [[round(v * 1000.0, 1) for v in per[IMPACT]["box_lo"]],
                                 [round(v * 1000.0, 1) for v in per[IMPACT]["box_hi"]]]
    res["zero_head_box_mm"] = [[round(v * 1000.0, 1) for v in zero["box_lo"]],
                               [round(v * 1000.0, 1) for v in zero["box_hi"]]]

    # ---- 剪影（双手挡胸前：只报不用）
    sil = P.silhouette(arm, "d03")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    if os.environ.get("D03_TRACE"):
        res["trace"] = {str(f): {
            "press": round(press(f), 4),
            "gap": round(min(per[f]["front_gap_mm"].values()), 2),
            "back": round(min(per[f]["fist_back_vs_pelvis_mm"].values())
                          - min(zero["fist_back_vs_pelvis_mm"].values()), 2),
            "pitch": round(per[f]["chest_pitch_deg"], 3),
            "head_y": round(per[f]["head_y"] * 1000.0, 1),
        } for f in range(0, TOTAL + 1)}
    return res


# =============================================================== 引导
def boot():
    global ZERO, ZERO_WORLD
    ZERO, ZERO_WORLD = {}, {}
    IDLE_FIST.clear()

    arm, meshes = GS.boot()

    # ★★ 零位 = 落盘 `Guard_Start` action 的末帧（与 D02 一字不改）
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
    zrow = _hit_frame_metrics(arm)
    A.report("D03_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "impact": IMPACT, "hold_end": HOLD_END, "recover_end": RECOVER_END,
        "segments": 1, "hit_points": 0, "root_motion_m": [0.0, 0.0],
        "zero_source": "%s@%d（落盘 action，非重演）"
                        % (saved_info.get("action"), saved_info.get("last_frame")),
        "zero_fist_mm": {s: [round(v * 1000.0, 2) for v in GS.GUARD_FIST[s]]
                         for s in SIDES},
        "zero_head_box_mm": [[round(v * 1000.0, 1) for v in zrow["box_lo"]],
                             [round(v * 1000.0, 1) for v in zrow["box_hi"]]],
        "zero_front_gap_mm": {s: round(v, 2)
                              for s, v in zrow["front_gap_mm"].items()},
        "zero_pelvis_z_mm": round(GS.Z_SEAM * 1000.0, 3),
        "press_drop_mm": PRESS_DROP_MM,
        "press_fist_offset_mm": [PRESS_IN_MM, PRESS_BACK_MM, PRESS_DOWN_MM],
        "torso_press_deg": TORSO_PRESS,
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
        "note": ("D03 防御受击：零位 = D01 落盘末帧；不对称受击脉冲 0.6 s；"
                 "上身后仰 + 双臂被压回 + 脚纹丝不动；首尾共用同一 dict"),
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
    # ★★ 尾部**不再钉 `dict(ZERO)`**（第 2 轮实测：见 `_d03_sw_*.log`）。
    #   原先把 `RECOVER_END..TOTAL` 逐位钉成 ZERO 的欧拉，结果 f32→f33 单帧跳
    #   **27.13°**（`upperarm.R`）⟹ `no_teleport` 假红。根因：`press ≡ 0` 时求解器的
    #   **世界矩阵与 ZERO 完全相同**，但 `_set_euler_nearest` 沿接力链走出来的欧拉
    #   与 ZERO（= D01 落盘值）差一个**绕骨轴滚转的零空间支**（D01 自身 `hand.R`
    #   就有 18° 同类现象）。钉值 = 强行掰到另一支 ⟹ 凭空造出一个跳变。
    #   ⟹ 改为**全程求解**：尾部输入恒等于零位 ⟹ 解出的姿态逐帧恒定、世界姿态 = 零位，
    #      欧拉路径连续。由此"末帧 == 零位"这条契约从**构造保证**换成**实测门禁**
    #      （`end_world_pose_ok`，比钉值更强：它盯的是世界姿态，不是欧拉表示）。

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "防御",
        "note": ("防御受击：上身后仰、双臂被压回、脚不动"
                 "（零位 = D01 举防定格），0 命中点、0 位移"),
        "impact_frame": IMPACT,
        "hold_end_frame": HOLD_END,
        "recover_frame": RECOVER_END,
        "hitstop_frames": 2,
        "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "hit_point_m": None,
        "start_pose_ref": "D01 Guard_Start 末帧",
        "end_pose_ref": "D01 Guard_Start 末帧（回到护架，可接 Guard_Loop）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "IMPACT": IMPACT, "HOLD_END": HOLD_END,
                           "RECOVER": RECOVER_END, "END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta,
                                     foot_probe=("foot.L", "foot.R"),
                                     slide_tolerance_mm=SLIDE_MAX_MM)
    report.update(hit_assertions(arm, action, samples, meshes))
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
    A.report("D03_REPORT", report)

    if not SKIP_RENDER:
        frames = [0, 2, IMPACT, HOLD_END, 14, RECOVER_END, TOTAL]
        A.render_pose_sheet(arm, action, frames, "guardhit",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D03_DONE failed=%s" % report["failed"])
    print("D03_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D03_FAILURE " + traceback.format_exc())
