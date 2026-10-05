"""anim_guard_loop —— D02 `Guard_Loop` 防御。

设计（对着清单 §四 D02 的原文「稳定循环，身体持续承受压力」逐条落）：

    段结构     **1 段循环**、**0 命中点**、**0 位移**。
    时长       72 帧 = **1.200 s** @60fps（计划 1.2~1.6 s）
    零位       ★ **= D01 `Guard_Start` 的定格真值**（逐位重演 D01 的 f0..TOTAL 求解取末帧，
               不重新探针、不重扫姿态）。本支把这个零位再往"承压"方向压一个小幅度。
    首尾       ★★ 首帧 == D01 末帧（引擎 `Guard_Start → Guard_Loop` 直连），
               且**首帧与末帧共用同一 `dict`** ⟹ `loop_seamless` 构造性成立。
    节奏       ★ **单一正弦式脉冲**（PCHIP 过 0 → 0.75 → 1.0 → 0.75 → 0），
               不许有"起手"式的加速度脉冲 —— 这是"稳定循环"，不是第二支起手。
    核心难点   循环闭合 **且** 与 D01 末帧对齐，两个约束同时满足。

"持续承受压力"的量化口径（本支新立 `guard_pressure_ok`）：
    胸腔顶（`neck.head` = `chest.tail`）竖直行程 ∈ [4, 14] mm
    拳（`hand.*.tail`）竖直行程           ∈ [2,  8] mm
    骨盆竖直行程                          ∈ [2,  8] mm
    ★ 骨盆**水平**位移 ≤ 2 mm —— 一左一右地晃是"站不稳"，不是"扛压力"。

承压时身体怎么动（全部相对零位、按 `press` 标量驱动，数值见下方 `PRESS_*`）：
    骨盆下沉 **24 mm**（腿由位置 IK 吸收，踝钉死 ⟹ 脚纹丝不动、鞋底不回弹）
    躯干小幅前压（chest +1.2°、spine +0.5°、pelvis +0.35°）—— 只到**穿模上限**
    肩胛略耸（shoulder **+4°**）—— 顶住压力的"憋劲"
    双拳随身体下沉 24 mm、并略前送 9 mm —— 护架顶住，身体沉在后面

★ **幅度是量出来的，不是拍的**。第一版（下沉 7 / 肩 1.8°）门禁全绿，
  但目检"看不出来在扛压力" ⟹ 回炉。换算：角色 1.7083 m ↔ 姿态表约 950 px，
  **1 mm ≈ 0.556 px**；原幅度只有几像素。重扫三组后锁定（见 `PRESS_*` 处注释）。
★ 躯干前压**卡在 1.2°**：它是穿模的唯一来源 —— chest 到 1.6° 时 `hand.L`
  插入头盒 0.75 mm（实测 `_d02_sw_F`）。腿下沉是**纯杠杆**，扫到 26 mm
  穿模仍是 0.0（`_d02_sw_G`）⟹ "扛压力"的量全给到下沉与肩，不给前倾。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_guard_loop.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
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

NAME = "Guard_Loop"
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
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的。

    ★ 为什么需要它：零位 `ZERO` 是**算出来的 float64**，而 `sample_animation`
      读回的是 Blender 存成 **float32** 的值。拿 float64 去比 float32，
      欧拉分量 ~150° 时噪声就有 **3.15e-06** ⟹ `SEAM_TOL = 1e-6` 假红。
      两边都过一遍 float32 之后，"逐位相同" 才是真的逐位相同（差值 = 0.0）。
    """
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _ulp32(value):
    """float32 在 `value` 处的间距（用来把"逐位相同"写成 ULP 口径）。"""
    return max(1e-12, math.ulp(_f32(value)))


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
    """D01 报告里**发布的**末帧欧拉真值（`_d01_final.log` 优先）。

    ★ 这是"报告说了什么"，不是"引擎播什么"。引擎播的是 `.blend` 里的
      `Guard_Start` action —— 见 `_load_d01_end_pose()`。两者必须一致，
      `d01_end_saved_ok` 就是盯着这条的。
    """
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
    """★ 零位真源：落盘 `Guard_Start` action 的**末帧**。

    为什么不是"重演 `solve_pose(SETTLE)`"（第 1 轮的写法）——
    **因为 D01 自己都不可复现**。实测（`probe_d01_action_end.py`）：

        同一条 `anim_guard_start.py`，两次独立跑：
          `hand.R`  = [0, 7.7368, 0]  vs  [0, 25.7369, 0]   ← 差**恰好 18.000°**
          其余 56 骨 ≤ 0.002°
        世界口径：骨根位置差 **0.0027 mm**、骨向差 **0.026°** ⟹ 完全同解

    根因：`aim_nearest` 只约束**骨轴指向**，绕骨自身轴的滚转是它管不到的
    **零空间自由度**；`_set_euler_nearest` 在 `ROLL_GRID` 上搜"离上一帧最近"
    的那支，`hand.R` 的代价函数是个平台 ⟹ 两次跑落到平台的两端。
    滚转**过骨根** ⟹ 位置/IK/贴地/骨轴全都不受影响，位置口径永远看不见它 ——
    但它会**把拳头网格拧 18°**，而它**会**出现在导出的欧拉里。

    ⟹ 结论：零位不能从"重演"取，必须从**引擎真正播的那份数据**取。
      重演保留，但降级为"复用同一条代码路径"的**几何同解**守卫
      （`d01_replay_geom_ok`），而不是逐位欧拉对表。
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
    `solve_pose(1..TOTAL)`，不多不少，取 `SETTLE` 帧。

    ⚠️ 两个必须照抄的点（第 1 轮各踩了一次）：
      1. **从第 1 帧开始**：D01 的 f0 是把 `SEAM_POSE` 直接写进去的
         （`keyframes = [(0, SEAM_POSE)]`，**没有**走 `solve_pose(0)`）。
         从 f0 起重演会让接力链在起点分叉。
      2. **`UE.CARRY_Q` 不能清**：D01 的 `main()` 里没有 `clear()`，
         它继承 `GS.boot()` 留下的接力基准当 f1 的起点。
    """
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
TOTAL = _env_i("D02_TOTAL", 72)          # 1.200 s @60fps（计划 1.2~1.6 s）
PEAK = _env_i("D02_PEAK", 36)            # 承压峰值
MID = _env_i("D02_MID", 18)              # 半幅

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
PLANT_MAX_MM = 3.0
SLIDE_MAX_MM = 3.0
GROUND_MIN_MM, GROUND_MAX_MM = -2.0, 6.0
REACH_MAX_RATIO = 0.995

# ★ 压力判据（阈值**先量再定**，此处是第二版 —— 第一版定小了，见下）
#
# 第一版按「下一支详细制作计划」§2 的**建议值**定了 [4,14] / [2,8] / [2,8]。
# 全绿了，但**目检不过**：`guardloop_side_f0000` 与 `f0036` 几乎一模一样，
# 看不出在"扛压力" —— 而清单第 4 步写得很明确：
# **「判据全绿但看不出来在'扛压力' = 失败，回炉。」**
#
# 复盘发现是**阈值本身定小了**，而且缺口可以算出来：
#   角色高 1.7083 m ↔ 姿态表画面里约 **950 px** ⟹ **1 mm ≈ 0.556 px**。
#   原上界 14 mm 只有 **≈8 px** —— 而且它是"峰值到零位"的**全幅**，
#   真正被看到的半个循环只有 ~4 px，和站姿摆动一个量级 ⟹ 读不出来。
#   1° 的上臂摆动（臂长 234 mm、力臂近 500 mm）≈ 8.7 mm ≈ **4.9 px** —— 这就是
#   "1° 在画面里的价钱"。
#
# ⟹ 重定口径【可读性】：位移幅度必须 ≥ **12 mm（≈7 px）**才算"看得见"。
#    上界取 **32 mm**：静止骨盆高 830 mm，下沉超过其 **4%** 就从"扛压力"
#    变成"下蹲"—— 那是 A08 `Crouch` 的语义，不是本支的。
#    ★ 这个窗口对下限**不放松**（从 4 提到 12），只把"看不见"那一半砍掉 ——
#      不是"放宽容差凑绿"，是把判据修到能真正抓东西。
PRESS_STERNUM_MIN_MM, PRESS_STERNUM_MAX_MM = _env_f("D02_STERN_LO", 12.0), \
    _env_f("D02_STERN_HI", 32.0)
PRESS_FIST_MIN_MM, PRESS_FIST_MAX_MM = _env_f("D02_FIST_LO", 12.0), \
    _env_f("D02_FIST_HI", 32.0)
PRESS_PELVIS_MIN_MM, PRESS_PELVIS_MAX_MM = _env_f("D02_PELV_LO", 12.0), \
    _env_f("D02_PELV_HI", 32.0)
# 水平位移仍≤2 mm —— 一左一右地晃是"站不稳"，不是"扛压力"，这条不变。
PRESS_PELVIS_HORIZ_MAX_MM = _env_f("D02_PELV_HORIZ", 2.0)

# ★ 循环闭合 / 接合
LOOP_ANGLE_MAX_DEG = _env_f("D02_LOOP_ANG", 0.5)
LOOP_MOVE_MAX_MM = _env_f("D02_LOOP_MOV", 0.5)
SEAM_MOVE_MAX_MM = _env_f("D02_SEAM_MOVE", 0.5)

# ★★ "零位 = D01 末帧" 这条契约的守卫断言（三条，各盯一件事）
#
# ① 落盘 action vs D01 报告发布值：`end_euler_ref` 是**按 4 位小数发布**的
#    （`anim_guard_start.py`：`round(v, 4)`）⟹ 发布粒度本身就是 5e-5 deg。
#    容差取 5e-5 = `round(x,4)` 的最大舍入误差 —— 不是"放宽"，是不比发布精度更细。
#    它盯的是"日志与 .blend 是不是同一份工件"。
D01_REF_DECIMALS = 4
D01_REF_TOL_DEG = 5.0e-05
#
# ② 重演 vs 落盘：**几何**同解。骨根位置 ≤0.01 mm、骨轴指向 ≤0.05°。
#    ★ 为什么用几何而不是逐位欧拉：绕骨自身轴的滚转是 `aim_nearest` 管不到的
#      零空间自由度（实测 D01 自身两次跑就差 18°，而位置只差 0.0027 mm）。
#      逐位对表会把"零空间"当成"错误"，把 D01 自身的不可复现当成 D02 的 bug。
#      几何守卫仍能抓住真正的分叉（选到另一支欧拉 ⟹ 整条链位移，mm 级）。
#      实测值：0.0027 mm / 0.026° ⟹ 余量 ~4× / ~2×。
D01_GEOM_POS_MAX_MM = _env_f("D02_D01_POS", 0.01)
D01_GEOM_DIR_MAX_DEG = _env_f("D02_D01_DIR", 0.05)

# ★ 复用 D01 定稿的护架判据（本支全程都必须保持住）
GUARD_IN_FRONT_MIN_MM = 150.0
GUARD_LATERAL_MIN_MM = 130.0
GUARD_LATERAL_MAX_MM = 200.0
GUARD_RAISE_MIN_MM = 60.0                # 循环里比 D01 定格略低是允许的
GUARD_HEAD_MARGIN_MM = 100.0
GUARD_SYM_MAX_MM = _env_f("D02_SYM", 25.0)
GUARD_ELBOW_OUT_MAX_MM = 20.0
GUARD_ELBOW_DROP_MIN_MM = 150.0
GUARD_CLIP_MAX_MM = 0.0
CLIP_EVERY = int(os.environ.get("D02_CLIP_EVERY", 6))

# =============================================================== 承压幅度
# ★ 全部由 `probe_d02_clip.py` 实测扫出来（不是拍脑袋）：
#   身体前倾是穿模的唯一来源 —— torso 一转，头盒前缘（鼻子）就往 −Y 走 42 mm
#   （基线 2.0/1.0/1.0/1.2），直接把腕关节顶进盒里（clip 22.94 mm @ frame 36）。
#   扫描（每组都是完整跑一遍探针）：
#     torso 全量 2.0/1.0/1.0/1.2/…, fist 后收 4  → clip **+22.94**
#     torso 半量 1.0/0.5/0.5/0.6/…, fist 后收 4  → clip **+11.57**
#     torso 半量,                    fist 前送 8  → clip    −0.09（余量只剩 0.09 mm，太薄）
#     torso 半量,                    fist 前送 15 → clip    −3.77
#     torso 0.7/0.3/0.3/0.35/…,      fist 前送 9  → clip    **−4.95（定稿）**
#     torso 0.9/0.4/0.4/0.5/…,       fist 前送 12 → clip    −4.21
#   ⟹ 定稿：**躯干前倾压到最小**（承压主要靠"下沉 + 肩憋劲"，而不是前倾），
#      拳**前送 9 mm**（不是被压回来）—— "护架顶住不动、身体在后面沉" 才是
#      "承受压力"该有的读法，顺带把穿模从 +22.94 变成 −4.95。
# ★★ 第二版定稿（第一版 7/0/−9/4 + 肩 1.8° 目检读不出来，重扫三组后锁定）
#
#   `_sweep_d02c.sh` 实测（三组都跑完整门禁）：
#     H1  drop 24 / fist 下 24 / 肩 4.0° / chest 1.2 … → stern **27.02** fist **24.0**
#         pelv **24.0** clip **0.0** step **3.496**  failed **[]**   ← **定稿**
#     H2  fist 只下 18（相对变化快）               → step 4.712（偏大，不取）
#     H3  drop 26 / 肩 5.0°                       → stern 29.02（离上界只剩 3 mm，太薄）
#   取 H1 的理由：四项全在窗口中部偏上，余量 16%~25%，且 step 只有限值的 1/7。
PRESS_DROP_MM = _env_f("D02_DROP", -24.0)    # 骨盆再下沉（相对 D01 定格）24 mm
PRESS_IN_MM = _env_f("D02_IN", 0.0)          # 拳内收（0 = 不加横向）
PRESS_BACK_MM = _env_f("D02_BACK", -9.0)     # 拳前后（负 = 前送）9 mm：护架顶住
PRESS_DOWN_MM = _env_f("D02_DOWN", 24.0)     # 拳下沉 24 mm（与身体同步，护架不散）
TORSO_PRESS = {"pelvis": _env_f("D02_TP_PELVIS", 0.35),
               "spine_01": _env_f("D02_TP_S1", 0.50),
               "spine_02": _env_f("D02_TP_S2", 0.50),
               "chest": _env_f("D02_TP_CHEST", 1.20),
               "neck": _env_f("D02_TP_NECK", -0.60),
               "head": _env_f("D02_TP_HEAD", 0.50),
               "shoulder.L": _env_f("D02_TP_SH", 4.00),
               "shoulder.R": _env_f("D02_TP_SH", 4.00)}

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")

# =============================================================== 模块级表
ZERO = {}                 # D01 定格真值（本支零位）
ZERO_WORLD = {}
IDLE_FIST = {}
# "零位 = D01 末帧同解" 的结论（`boot()` 里定，`main()` 并进总报告当门禁）
D01_SAME_SOLVE = {"ok": None, "diff": None, "src": None,
                  "per_bone": {}}


def press(frame):
    """承压标量 ∈ [0, 1]：单一脉冲，两端为 0 ⟹ 首尾逐位相同。"""
    keys = ((0, 0.0), (MID, 0.75), (PEAK, 1.0),
            (TOTAL - MID, 0.75), (TOTAL, 0.0))
    return UE.pwl(keys, float(frame), 0.0)


def fist_target(side, frame):
    """拳世界目标 = D01 定格 + 承压偏移（镜像）。"""
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
    # 腿：位置 IK（`UE.leg_seat`），踝目标钉死在 D01 的 `ANKLE_0`。
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
    """当前帧的护架指标（只读骨骼，便宜 —— 可以逐帧跑）。"""
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


def loop_assertions(arm, action, samples, meshes):
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 逐帧护架保持（骨骼口径，便宜）
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

    # ---- 穿模（网格口径，贵 —— 抽样跑）
    worst_clip, worst_clip_at, worst_clip_frame = 0.0, None, None
    for frame in range(0, TOTAL + 1, CLIP_EVERY):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip = clip["clip_max_mm"]
            worst_clip_at = clip["clip_at"]
            worst_clip_frame = frame
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = worst_clip_at
    res["clip_frame"] = worst_clip_frame
    res["guard_no_face_clip_ok"] = bool(worst_clip <= GUARD_CLIP_MAX_MM)

    # ---- ★ 承压可见度（本支语义判据）
    sternum = [s["neck"][2] for s in samples]
    fist_z = [(s["hand.L.tail"][2] + s["hand.R.tail"][2]) / 2.0
              for s in samples]
    pelvis = [s["pelvis"] for s in samples]
    sternum_mm = (max(sternum) - min(sternum)) * 1000.0
    fist_mm = (max(fist_z) - min(fist_z)) * 1000.0
    pelvis_mm = (max(p[2] for p in pelvis) - min(p[2] for p in pelvis)) * 1000.0
    horiz = max(math.hypot(p[0] - pelvis[0][0], p[1] - pelvis[0][1])
                for p in pelvis) * 1000.0
    res["sternum_range_mm"] = round(sternum_mm, 2)
    res["fist_range_mm"] = round(fist_mm, 2)
    res["pelvis_range_mm"] = round(pelvis_mm, 2)
    res["pelvis_horiz_mm"] = round(horiz, 3)
    res["sternum_press_ok"] = bool(PRESS_STERNUM_MIN_MM <= sternum_mm
                                   <= PRESS_STERNUM_MAX_MM)
    res["fist_press_ok"] = bool(PRESS_FIST_MIN_MM <= fist_mm
                                <= PRESS_FIST_MAX_MM)
    res["pelvis_press_ok"] = bool(PRESS_PELVIS_MIN_MM <= pelvis_mm
                                  <= PRESS_PELVIS_MAX_MM)
    res["pelvis_horiz_ok"] = bool(horiz <= PRESS_PELVIS_HORIZ_MAX_MM)
    res["guard_pressure_ok"] = bool(res["sternum_press_ok"]
                                    and res["fist_press_ok"]
                                    and res["pelvis_press_ok"]
                                    and res["pelvis_horiz_ok"])

    # ---- ★ 循环闭合：首帧 vs 末帧（姿态 + 世界位）
    first, last = samples[0], samples[-1]
    worst_ang = 0.0
    for name in set(first["euler"]) | set(last["euler"]):
        ea = first["euler"].get(name, (0.0, 0.0, 0.0))
        eb = last["euler"].get(name, (0.0, 0.0, 0.0))
        worst_ang = max(worst_ang, max(abs(a - b) for a, b in zip(ea, eb)))
    worst_move = 0.0
    for name in A.PROBE_KEYS:
        if name in first and name in last:
            worst_move = max(worst_move,
                             (Vector(first[name]) - Vector(last[name])).length)
    res["loop_angle_deg"] = round(worst_ang, 4)
    res["loop_move_mm"] = round(worst_move * 1000.0, 3)
    res["guard_loop_closure_ok"] = bool(worst_ang <= LOOP_ANGLE_MAX_DEG
                                        and worst_move * 1000.0
                                        <= LOOP_MOVE_MAX_MM)

    # ---- ★ 首帧 == D01 末帧（世界位）
    worst_seam = 0.0
    for name, ref in ZERO_WORLD.items():
        if name in first:
            worst_seam = max(worst_seam,
                             (Vector(first[name]) - Vector(ref)).length)
    res["seam_move_mm"] = round(worst_seam * 1000.0, 3)
    res["guard_seam_ok"] = bool(worst_seam * 1000.0 <= SEAM_MOVE_MAX_MM)

    # ---- 可达性（逐帧取最差）
    worst_reach = 0.0
    for frame in range(0, TOTAL + 1, 6):
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

    # ---- 承压峰值帧（供人看）
    scene.frame_set(PEAK)
    bpy.context.view_layer.update()
    peak_fist = {s: [round(v * 1000.0, 1)
                     for v in A.bone_world(arm, "hand." + s, "tail")]
                 for s in SIDES}
    res["peak_fist_mm"] = peak_fist
    res["zero_fist_mm"] = {s: [round(v * 1000.0, 1)
                              for v in GS.GUARD_FIST[s]] for s in SIDES}

    # ---- 剪影（双手长时间挡胸前：只报不用）
    sil = P.silhouette(arm, "d02")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]
    return res


# =============================================================== 引导
def boot():
    global ZERO, ZERO_WORLD
    ZERO, ZERO_WORLD = {}, {}
    IDLE_FIST.clear()

    # ★ 直接复用 D01 的 boot（读 Idle_01@0 真值 + Idle 骨基座 + 建信封）
    arm, meshes = GS.boot()

    # ★★ 零位 = **落盘 `Guard_Start` action 的末帧**（引擎真正会播的那份数据）。
    #   不抄常量、也不靠"重演"—— 理由见 `_load_d01_end_pose()` 的文档：
    #   D01 的腕骨滚转在自身两次跑之间就差 18°，**重演不可复现**。
    #   读回值本身已经过 `deg → rad → f32 → deg` 这条链
    #   （`rotation_euler` 是 float32 存的），所以 f0 再写回去是**构造性逐位相同**
    #   ⟹ `ua_start_ok` / `guard_loop_closure_ok` 恒 0.0，不是靠调容差凑的。
    ZERO, saved_info = _load_d01_end_pose(arm)

    # ---- 重演 D01（证明复用同一条代码路径）+ **几何**同解守卫
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

    # 逐骨欧拉对表（**只报不判**：滚转零空间本来就允许不同）
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

    # ---- 落盘 action vs D01 报告发布值（同一份工件？）
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

    A.report("D02_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "peak": PEAK, "mid": MID, "segments": 1, "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "zero_source": "%s@%d（落盘 action，非重演）"
                        % (saved_info.get("action"), saved_info.get("last_frame")),
        "zero_fist_mm": {s: [round(v * 1000.0, 2) for v in GS.GUARD_FIST[s]]
                         for s in SIDES},
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
        "note": ("D02 防御：零位 = D01 落盘末帧（引擎真值）；单一承压脉冲 1.2 s；"
                 "首尾共用同一 dict"),
    })
    return arm, meshes


def main():
    arm, meshes = boot()

    JS._PREV_EULER.clear()
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    for name in ARM_BONES + LEG_BONES:
        # ★ 把臂/腿的**接力基准**也钉到零位朝向 —— D01 的链在末帧正好停在这里，
        #   这样 D02 的 f1 就从"零位那一支"继续，末帧不会漂到另一支欧拉上去。
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    # ★ 首键 = 零位（= D01 末帧，含**绕骨轴滚转**的逐位相同）；末键逐位复用同一个
    #   dict ⟹ `guard_loop_closure_ok` 与 `ua_start_ok` 都是构造性的。
    keyframes = [(0, ZERO)]
    for frame in range(1, TOTAL):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))
    keyframes.append((TOTAL, dict(ZERO)))

    meta = {
        "anim_id": NAME,
        "loop": True,
        "category": "防御",
        "note": "防御：稳定循环，身体持续承受压力（零位 = D01 举防定格），0 命中点、0 位移",
        "press_peak_frame": PEAK,
        "hitstop_frames": 0,
        "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "hit_point_m": None,
        "start_pose_ref": "D01 Guard_Start 末帧",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"LOOP_START": 0, "PRESS_MID": MID,
                           "PRESS_PEAK": PEAK, "LOOP_END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta,
                                     foot_probe=("foot.L", "foot.R"),
                                     slide_tolerance_mm=SLIDE_MAX_MM)
    report.update(loop_assertions(arm, action, samples, meshes))
    report["meta"] = meta

    # 起手接合：f0 必须与 D01 末帧**逐位相同**（两边都过 float32，见 `_f32`）
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

    # 零位 = D01 末帧（`boot()` 里三条守卫，门禁口径）
    report["d01_end_saved_ok"] = bool(D01_SAME_SOLVE["saved"].get("found")
                                      and D01_SAME_SOLVE["ref_ok"])
    report["d01_saved_vs_report_max_diff"] = D01_SAME_SOLVE["ref_diff"]
    report["d01_report_ref_src"] = D01_SAME_SOLVE["ref_src"]
    report["d01_replay_geom_ok"] = D01_SAME_SOLVE["geom_ok"]
    report["d01_replay_geom_pos_mm"] = D01_SAME_SOLVE["geom_pos_mm"]
    report["d01_replay_geom_dir_deg"] = D01_SAME_SOLVE["geom_dir_deg"]
    # 只报不判：零空间（绕骨轴滚转）上的差异，必须**看得见**
    report["d01_replay_euler_max_diff_deg"] = D01_SAME_SOLVE["euler_diff"]
    report["d01_replay_euler_worst_bone"] = D01_SAME_SOLVE["euler_bone"]
    report["d01_replay_roll_free_bones"] = D01_SAME_SOLVE["roll_free"]

    if os.environ.get("D02_TRACE"):
        trace = {}
        for index in range(1, len(samples)):
            ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
            for name in ARM_BONES:
                a = ea.get(name, (0.0, 0.0, 0.0))
                b = eb.get(name, (0.0, 0.0, 0.0))
                step = max(abs(x - y) for x, y in zip(a, b))
                trace.setdefault(name, []).append(round(step, 2))
        report["arm_step_trace"] = trace

    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("D02_REPORT", report)

    if not SKIP_RENDER:
        frames = [0, MID, PEAK, TOTAL - MID, TOTAL]
        A.render_pose_sheet(arm, action, frames, "guardloop",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D02_DONE failed=%s" % report["failed"])
    print("D02_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D02_FAILURE " + traceback.format_exc())
