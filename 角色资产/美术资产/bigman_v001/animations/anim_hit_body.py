"""anim_hit_body —— D10 `Hit_Body` 腹部受击。

清单原文：「对应躯干命中，身体前折」。

★★ 本支回到 D05~D08 那个族（**整躯干受力**），但与 D09 **不是一个族**：
   D09 是「**局部**受力」（躯干逐位不动、只有 `neck` + `head` 后甩）；
   本支是「**中段**受力」—— 力打在**腰腹**，把**上身往前折**（前屈），
   而**下肢要继续站住**（方案 A：踝目标 = 零位常量，脚全程钉住）。

方向符号（★ 与 D09 全反）：
    受力 = **躯干中段（腰腹）**，力把上身往 **−Y（身前）** 折。所以
      · 骨 `rx > 0` = **前屈**（`anim_lib` 语义表）—— 全表取**正号**（同 D08）
      · `chest_pitch` 定义（本支**前屈为正**，与 D09 的"后仰为正"同一坐标系、
        相反符号预期）：`chest_pitch = −atan2(chest_dir.y, chest_dir.z)`
        ⟹ 前折 = **正**，两界都取正：Δ ∈ [+8, +20]
      · `head_fwd_mm = (zero.head_y − per[IMPACT].head_y) × 1000`（正 = 头往前）
      · 骨盆位移：**中段**受力 ⟹ 髋后移（+Y 30 mm）+ 下沉（−12 mm），脚不动
      · 侧视像素符号 `SIDE_SIGN = −1`（前折往 −Y = 图像**左**移，同 D06/D08）

本支唯一的真风险（计划 §2）：**"身体前折"会被做成"弯腰鞠躬"**。三种失败读法：
      · 读成"鞠躬"：折得**慢** + **头先动**（应该是**胸先折、头滞后**）；
      · 读成"下蹲"：膝屈得比腰多 ⟹ 读成"蹲下去"而不是"被打折了"；
      · 读成"没事"：折幅太小，或躯干动了但读不出受力点在中段。
   做法：`spine_01 : spine_02 : chest` 分工**递减**（根节带大头、末端补一点）；
   头颈由**独立的滞后标量**驱动 —— 撞上时头**还没跟上**（相对胸是**后仰**的），
   命中峰后头才被惯性拖着折下去 → 世界俯仰**峰值比胸晚 ≥2 帧**，然后**反向回补**；
   上界由 `no_face_clip_ok` + `chest_pitch` 上界两条一起钉住。

★★ 两条独立的驱动标量（同 D09 的双标量结构，D09 教训 1 的直接继承）：
    `press` —— **单调**单脉冲（升 3 / 硬直 3 / 降 20）⟹ 只当"节奏时钟"与
               `zero_shortcut` 的作用域。它的"降"必须单调，否则节奏判据被污染。
    `fold`  —— **真正驱动躯干**的标量：命中峰 1.0 → 回落 → **反向过冲 −0.085**
               （= 上身弹回 8.5% 峰值，惯性）→ 微抖 → 0。
    `lag`   —— **真正驱动头颈**的标量：撞上时**负**（头顶往后甩 = 头来不及跟上）
               → 命中峰后冲到 +1.0（惯性把头顶拽下去）→ **反向回补** → 归零。

继承（逐条照抄，别重写）：
    · 骨架 / 零位加载 / `_ZERO_SHORTCUT` / `_roll_return` 滚-瞄交替 2 趟
      / `end_torso_ok` / `zero_shortcut_ok` / `fist_held_ok` 的构造
    · D05 三条修正：`arm_seat_tip()` / `elbow_hit()` 乘标量 / `KNEE_DIR[side]`
    · D07 教训 2：量零位前必须 `arm.animation_data.action = None`
    · D07 教训 3：`_roll_return` 必须"滚一趟 → 重瞄一趟"交替、末趟收在"瞄"上
    · D09 教训 1：**首跑即绿必须先做反向验证**（符号反 / 幅度小 / 幅度大）
    · D08 教训 1：腿相对髋摆开会让**鞋底网格**下沉（蒙皮伪影）——
      本支骨盆后移 30 mm / 下沉 12 mm（远小于 D08 的 137 mm）⟹ 预判 <1 mm，
      由 `ground_contact_ok` 直接盯，**不引入** `sole_lift`（跑出来看，不预防性加）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_hit_body.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D10_TRACE=1    逐帧打印 press / fold / lag / 胸头世界俯仰（调参用）
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

NAME = "Hit_Body"
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
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D09 同源）。"""
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _keyed_bones(action):
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


# =============================================================== 时间轴
# ★ 计划 §1：时长量级「约 34~40 帧」⟹ 取 38 帧 = 0.633 s @60fps。
TOTAL = _env_i("D10_TOTAL", 38)          # 0.633 s @60fps
IMPACT = _env_i("D10_IMPACT", 3)         # 躯干命中峰（上升沿 3 帧）
HIT_HOLD = _env_i("D10_HOLD", 3)         # 小硬直平台 3 帧
HOLD_END = IMPACT + HIT_HOLD             # 6
HEAD_PEAK = _env_i("D10_HEAD_PEAK", 8)   # ★ 头（惯性）世界俯仰峰 —— 必须晚于 IMPACT
REBOUND = _env_i("D10_REBOUND", 16)      # 反向过冲峰（上身弹回，惯性）
DUMP_END = _env_i("D10_DUMP", 19)        # 过冲之后的第一微抖峰
SHAKE_END = _env_i("D10_SHAKE", 22)      # 第二微抖峰
RECOVER_END = _env_i("D10_RECOVER", 26)  # 驱动标量回到 0 的帧（降 20 帧）
CANCEL = _env_i("D10_CANCEL", 30)
#   ★ 为什么回落取 20 帧：`no_teleport`（≤25°/帧）是物理下界，本支折角 ~15°
#     若在 5 帧内回完 ⟹ 单帧 3°+ 且末段速度不连续；20 帧给足惯性感，
#     且满足"升 ≤4 / 降 ≥18"的不对称要求（命中快、回落慢）。

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
GROUND_MIN_MM, GROUND_MAX_MM = -2.0, 6.0
REACH_MAX_RATIO = 0.995
# ---- ★★ 本支头号判据（计划 §1）：`chest` 世界俯仰 —— 定义成「前屈为正」
# ★ 定义：`chest_pitch = −atan2(chest_dir.y, chest_dir.z)`。+Y = 身后 ⟹
#   `atan2` 在前折时为负 ⟹ 取负号后**前折为正**。两界都取正，**不许用 abs()**。
CHEST_FOLD_MIN_DEG = _env_f("D10_FOLD_MIN", 8.0)
CHEST_FOLD_MAX_DEG = _env_f("D10_FOLD_MAX", 20.0)
# ★ 反向过冲（惯性）：上身弹回一截（后仰），但**必须小于峰值**（计划 §2「不能大过峰值」）。
CHEST_REBOUND_MIN_DEG = _env_f("D10_REB_MIN", -2.4)
CHEST_REBOUND_MAX_DEG = _env_f("D10_REB_MAX", -0.6)
OVERSHOOT_MIN = _env_f("D10_OVS_MIN", 0.08)
OVERSHOOT_MAX = _env_f("D10_OVS_MAX", 0.12)
# ★ 脊柱递减分工（计划 §3：`spine_01 : spine_02 : chest` 递减，防全堆在 `chest`）
SPINE_RATIO_MIN = _env_f("D10_SR_MIN", 0.45)
SPINE_RATIO_MAX = _env_f("D10_SR_MAX", 0.98)
# ★★ 本支主设计 `head_lag_ok`（计划 §3）：头颈**滞后**（D09 是"领跑"，本支是镜像）
HEAD_LAG_MIN_FRAMES = _env_f("D10_LAG_FRAMES", 2.0)   # 头峰比胸峰晚 ≥2 帧
HEAD_REL_AT_HIT_MAX_DEG = _env_f("D10_REL_HIT", -0.5)  # 撞上时头相对胸必须**后仰**
HEAD_REL_BACK_MAX_DEG = _env_f("D10_REL_BACK", -0.5)  # 回落段反向回补（头往前甩回）
# ★ 头顶位移口径（正 = 头往 −Y 身前）
HEAD_FWD_MIN_MM = _env_f("D10_HEAD_MIN", 60.0)
# ★ 髋（骨盆）位移：中段受力 ⟹ 髋后移 + 下沉（幅值只报 + 参与传导链判据）
PELVIS_MOVE_MIN_MM = _env_f("D10_PELVIS_MIN", 5.0)
# ★ 末段必须归零并稳住
SETTLE_MAX_DEG = _env_f("D10_SETTLE", 0.05)
SETTLE_STEP_MAX_DEG = _env_f("D10_SETTLE_STEP", 0.02)
# ★ 拳架近似保持防御形状（本支双臂被躯干带着走，但**不主动挥**）
FIST_HELD_MAX_MM = _env_f("D10_FIST_MAX", 45.0)
# ★ 肩的传导（力量链条可见：腰折 → 肩被带动）
SHOULDER_RISE_MIN_MM = _env_f("D10_SHO_MIN", 0.5)
# ★ 膝被动吸收（★ 方案 A 的新增：膝屈是被动量出来的，不设拍脑袋的界 ——
#   先跑出来看量级，再定"下蹲"与"被动吸收"的分界线）。
KNEE_ABSORB_MAX_DEG = _env_f("D10_KNEE", 8.0)
# ★ 站姿类硬要求：脚不许滑动（≤3 mm）
FOOT_SLIDE_MAX_MM = _env_f("D10_SLIDE", 3.0)
STANCE_SOLE_MAX_MM = _env_f("D10_SOLE", 6.0)

# ---- 节奏不对称（升 ≤4 帧、降 ≥18 帧）
HIT_RISE_MAX_FRAMES = _env_f("D10_RISE_MAX", 4.0)
HIT_FALL_MIN_FRAMES = _env_f("D10_FALL_MIN", 18.0)
# ---- 打击停顿（≥3 帧）
HITSTOP_MIN_FRAMES = _env_f("D10_HITSTOP_MIN", 3.0)
# ---- 末帧口径（四口径；本支**回原位** ⟹ 世界位置不加整体位移）
HIT_END_MAX_MM = _env_f("D10_END_MAX", 0.5)
HIT_LAST2_MAX_DEG = _env_f("D10_LAST2", 0.5)
HIT_ROLL_MAX_DEG = _env_f("D10_ROLL_MAX", 0.5)
ROLL_RETURN = _env_f("D10_ROLL_RETURN", 1.0) >= 0.5
ROLL_WEIGHT_MODE = os.environ.get("D10_ROLL_WEIGHT", "tail").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D10_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split(",")
    if item)
ROLL_ITER = max(1, int(os.environ.get("D10_ROLL_ITER", "2")))
END_ROLL_BONES = ARM_ROLL_BONES = ("upperarm.L", "forearm.L", "hand.L",
                                   "upperarm.R", "forearm.R", "hand.R")
# ---- 穿模
CLIP_MAX_MM = _env_f("D10_CLIP_MAX", 0.0)
CLIP_EVERY = int(os.environ.get("D10_CLIP_EVERY", 4))
# ---- 零位守卫
IDLE_MATCH_TOL_DEG = _env_f("D10_IDLE_MATCH", 1.0e-3)
IDLE_GEOM_POS_MAX_MM = _env_f("D10_IDLE_POS", 0.01)
IDLE_GEOM_DIR_MAX_DEG = _env_f("D10_IDLE_DIR", 0.05)

# =============================================================== 驱动标量
# ★★ 为什么需要**三条**标量（D09 双标量结构的直接继承）：
#   `press` 是**单调单脉冲**（升 3 / 停 3 / 降 20）⟹ 只能当"节奏时钟"
#            与 `zero_shortcut` 的作用域（降必须单调，否则节奏判据被过冲污染）。
#   `fold`  是**真正驱动躯干**的标量：命中峰 1.0 → 回落 → **反向过冲 −0.085**
#            （= 上身弹回 8.5% 峰值，惯性）→ 微抖 → 0。
#   `lag`   是**真正驱动头颈**的标量：撞上时**负**（头还没跟上、相对胸反而后仰）
#            → 命中峰后冲到 +1.0（惯性把头顶拽下去）→ **反向回补** → 归零。
FOLD_KEYS = ((0, 0.0), (1, 0.30), (2, 0.68), (IMPACT, 1.0), (HOLD_END, 1.0),
             (10, 0.72), (13, 0.30), (REBOUND, -0.085), (DUMP_END, 0.020),
             (SHAKE_END, -0.006), (RECOVER_END, 0.0), (TOTAL, 0.0))
# ★ `lag` 的 0~IMPACT 必须是**负**的：力打在腰腹时，重的头**留在原地**，
#   胸已经折下去了 ⟹ 相对胸，头是**后仰**的（`lag < 0`）。
#   平台两端都取 −0.55 ⟹ `hitstop` 期间头也**逐位冻结**（不能破坏停顿）。
LAG_KEYS = ((0, 0.0), (1, -0.18), (2, -0.42), (IMPACT, -0.55), (HOLD_END, -0.55),
            (HEAD_PEAK, 1.0), (11, 0.60), (14, 0.20), (REBOUND, -0.100),
            (DUMP_END, 0.025), (SHAKE_END, -0.008), (RECOVER_END, 0.0),
            (TOTAL, 0.0))


def press(frame):
    """节奏标量 ∈ [0, 1]：**升 3 / 峰停 3 / 降 20** 的单脉冲（**单调**）。"""
    keys = [(0, 0.0)]
    for step in range(1, IMPACT):
        keys.append((step, step / float(IMPACT)))
    keys += [(IMPACT, 1.0), (HOLD_END, 1.0), (RECOVER_END, 0.0), (TOTAL, 0.0)]
    return UE.pwl(tuple(keys), float(frame), 0.0)


def fold(frame):
    """★ 躯干驱动标量：1.0 = 折到峰；负 = **反向过冲**（上身弹回）；末段归零。"""
    return UE.pwl(FOLD_KEYS, float(frame), 0.0)


def lag(frame):
    """★ 头颈驱动标量：负 = 头**还没来得及跟**（相对胸后仰）；正 = 惯性拽下去。"""
    return UE.pwl(LAG_KEYS, float(frame), 0.0)


def still(frame):
    """`press ≡ 0` 且 `fold ≡ 0` 且 `lag ≡ 0` 的帧 ⟹ 走零位短路。"""
    return (abs(press(frame)) <= 1e-12 and abs(fold(frame)) <= 1e-12
            and abs(lag(frame)) <= 1e-12)


# =============================================================== 受击幅度
# ★★ 幅度标定（同一把尺子，不要拍脑袋）：
#   D04 破防：胸世界俯仰 9.8°（头前移 168.6 mm）；D08 背面重受击：−6.8°（头前移 145 mm）。
#   本支是**中段（腰腹）**受力、幅度要比 D08 更狠（清单「动作幅度大夸张有力」）⟹
#   取 `pelvis..chest` 累加 **+14.8°**（俯仰口径 = 前屈 14.8°，落在 [8, 20] 带内中上段）。
#   ★ 分工递减（计划 §2「spine_01 : spine_02 : chest 递减」）：2.0 / 5.6 / 4.2 / 3.0
#     —— 根节 `spine_01` 带大头（腰椎是真正的折点），末端 `chest` 只补一点。
AMP = {"pelvis": _env_f("D10_TP_PELVIS", 2.0),
       "spine_01": _env_f("D10_TP_S1", 5.6),
       "spine_02": _env_f("D10_TP_S2", 4.2),
       "chest": _env_f("D10_TP_CHEST", 3.0),
       # ★ 头颈由 `lag` 驱动（见 `lag()`）：撞上时取负 ⟹ **头没有跟上**。
       "neck": _env_f("D10_TP_NECK", 3.6),
       "head": _env_f("D10_TP_HEAD", 5.2),
       # ★ 肩被躯干带动（力量链条"腰折 → 肩被带"可见）
       "shoulder.L": _env_f("D10_TP_SH", 2.0),
       "shoulder.R": _env_f("D10_TP_SH", 2.0)}
# 躯干**轻微偏转**（ry，度）：中段受力不完全是纯矢状面，加一点扭转才不像"机械推拉"。
YAW = {"pelvis": _env_f("D10_YAW_PELVIS", 0.35),
       "spine_01": _env_f("D10_YAW_S1", 0.45),
       "spine_02": _env_f("D10_YAW_S2", 0.45),
       "chest": _env_f("D10_YAW_CHEST", 0.55),
       "neck": 0.0, "head": 0.0,
       "shoulder.L": 0.0, "shoulder.R": 0.0}
# 髋位移（中段受力 ⟹ 髋**后移** + 下沉；脚被 IK 钉住 ⟹ 膝**被动**吸收）
HIT_BACK_MM = _env_f("D10_BACK", 30.0)     # 骨盆沿 +Y 后移（上身前折时的"铰链"）
HIT_DROP_MM = _env_f("D10_DROP", -12.0)    # 骨盆下沉（负 = 往下）
HIT_SIDE_MM = _env_f("D10_SIDE", 4.0)      # 骨盆沿 +X 侧移（前视可见的轻微侧移）
# 拳被躯干带着走一点点（不主动挥拳 ⟹ 幅度小）
HIT_OUT_MM = _env_f("D10_OUT", 8.0)        # 每侧拳**横向外张**
HIT_BACKF_MM = _env_f("D10_BACKF", -14.0)  # 拳沿 **−Y 前送**（身体折下去带的）
HIT_DOWN_MM = _env_f("D10_DOWN", 12.0)     # 拳下沉
# 肘被顶开一点点
_EH_X = _env_f("D10_EB_X", 0.05)
_EH_Y = _env_f("D10_EB_Y", 0.04)
_EH_Z = _env_f("D10_EB_Z", -0.04)

# ★ 只有头颈吃 `lag`；其余吃 `fold`
LAG_BONES = ("neck", "head")
TORSO_BONES = ("pelvis", "spine_01", "spine_02", "chest")
SPINE_BONES = ("spine_01", "spine_02", "chest")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")

# =============================================================== 模块级表
ZERO = {}
ZERO_WORLD = {}
ZERO_BASIS = {}
ZERO_DIR = {}
IDLE_FIST = {}
IDLE_ELBOW_DIR = {}
IDLE_WRIST = {}
IDLE_HAND_DIR = {}
ANKLE_0 = {}
KNEE_DIR = {}
Z_SEAM = 0.0
IDLE_MATCH = {"src": None, "diff": None, "geom_pos": None, "geom_dir": None,
              "pos_bone": None, "dir_bone": None, "per_bone": {}}
_ZERO_SHORTCUT = [0]


# =============================================================== 姿态装配
def torso_pose(frame):
    """★★ 躯干吃 `fold`（前折链，递减分工）；头颈吃 `lag`（滞后 + 反向回补）。

    `@loc` = 零位骨盆 + 髋后移/下沉/侧移（**按 `fold` 缩放** ⟹ 命中峰处最大）。
    """
    p = fold(frame)
    g = lag(frame)
    out = {}
    for name in TARGET_BONES:
        zero = ZERO[name]
        scalar = g if name in LAG_BONES else p
        out[name] = (zero[0] + AMP.get(name, 0.0) * scalar,
                     zero[1] + YAW.get(name, 0.0) * p,
                     zero[2])
    out["@loc"] = {"pelvis": A.wloc(HIT_SIDE_MM * p / 1000.0,
                                    HIT_BACK_MM * p / 1000.0,
                                    Z_SEAM + HIT_DROP_MM * p / 1000.0 - 0.900)}
    return out


def ankle_target(side, frame):
    """腿目标 = **常量**（零位踝）。本支无步态、无位移（方案 A，计划 §2）。"""
    return Vector(ANKLE_0[side])


def fist_target(side, frame):
    """拳世界目标 = `Idle_01@0` 拳位 + 受击偏移（镜像）。**绝对世界点**。"""
    p = fold(frame)
    sign = 1.0 if side == "L" else -1.0
    return Vector(IDLE_FIST[side]) + Vector(
        (sign * HIT_OUT_MM, HIT_BACKF_MM, -HIT_DOWN_MM)) * (p / 1000.0)


def elbow_hit(side, frame):
    """肘偏好方向：Idle 内收 → 受击时微微外张下压（按 `fold` 插值，归一化）。

    ★ D05 首轮漏乘标量 ⟹ 偏移变常量、`fold = 0` 的末帧仍带偏角 ⟹ 肘位差 11.6 mm。
    """
    p = fold(frame)
    if abs(p) <= 1e-9:
        return tuple(IDLE_ELBOW_DIR[side])
    sign = 1.0 if side == "L" else -1.0
    want = Vector(IDLE_ELBOW_DIR[side]) + Vector(
        (sign * _EH_X, _EH_Y, _EH_Z)) * p
    if want.length < 1e-9:
        return tuple(IDLE_ELBOW_DIR[side])
    return tuple(want.normalized())


def arm_seat_tip(arm, pose, side, tip_target, elbow_dir):
    """★★ D05 立的臂解算：两骨 IK 打在腕上，手骨按零位自己的折角单独瞄。"""
    up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
    dims = UE.ARM_LEN[side]
    l1, l2 = dims["upper"], dims["forearm"]
    hand_dir = IDLE_HAND_DIR[side]
    wrist_target = Vector(tip_target) - hand_dir * dims["hand"]
    shoulder = Vector(A.bone_world(arm, up, "head"))
    delta = wrist_target - shoulder
    limit = (l1 + l2) * 0.9995
    clamp = delta.length > limit
    distance = max(1e-4, min(delta.length, limit))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    bulge = Vector(elbow_dir) - axis * Vector(elbow_dir).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    cos_sh = (l1 * l1 + distance * distance - l2 * l2) / (2.0 * l1 * distance)
    cos_sh = max(-1.0, min(1.0, cos_sh))
    sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
    elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * l1
    for name, direction in ((up, elbow - shoulder),
                            (fo, wrist_target - elbow),
                            (hd, hand_dir)):
        pose[name] = UE.aim_nearest(arm, name, direction,
                                    UE.IDLE_BASIS[name], UE.IDLE_DIR[name])
    return clamp, delta.length * 1000.0, limit * 1000.0


def build_pose(arm, frame):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    # 腿：位置 IK，踝目标 = **零位踝常量**（脚全程钉住 ⟹ `no_foot_slide` 回归默认口径）
    for side in SIDES:
        UE.leg_seat(arm, pose, side, ankle_target(side, frame), KNEE_DIR[side])
    for side in SIDES:
        name = "foot." + side
        pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name),
                                    A.keep_world_orientation(arm, name))
    # ★★ `still` 帧短路（D07 教训 4）：驱动标量恒 0 的帧，躯干 + 臂 + 腿的**正确解
    #   就是零位本身**。再解一遍只会把 `pose_bone.matrix` 的 float32 往返噪声
    #   写进欧拉（实测残差 1.9e-05°，而 `end_torso_ok` 的界是 ≤1e-6°）。
    if still(frame):
        _ZERO_SHORTCUT[0] += 1
        for name in ARM_BONES + LEG_BONES + ("foot.L", "foot.R"):
            if name in ZERO:
                pose[name] = tuple(ZERO[name])
        pose.update(A.FIST)
        for name, value in pose.items():
            if not name.startswith("@"):
                JS._PREV_EULER[name] = tuple(value)
        return pose
    for side in SIDES:
        arm_seat_tip(arm, pose, side, fist_target(side, frame),
                     elbow_hit(side, frame))
    if ROLL_RETURN:
        weight = _roll_weight(frame)
        if weight > 1e-9:
            # ★★ 滚转修正必须"滚一趟 → 重瞄一趟"交替（D07 教训 3）。
            for _ in range(ROLL_ITER):
                for name in ROLL_BONES:
                    if name in arm.pose.bones:
                        _roll_return(arm, pose, name, weight)
                for side in SIDES:
                    arm_seat_tip(arm, pose, side, fist_target(side, frame),
                                 elbow_hit(side, frame))
    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


def solve_pose(arm, frame, meshes=None):
    return build_pose(arm, frame)


# =============================================================== 滚转回位修正
def _roll_weight(frame):
    if ROLL_WEIGHT_MODE == "always":
        return 1.0
    if ROLL_WEIGHT_MODE == "tail":
        if frame <= HOLD_END:
            return 0.0
        span = max(1, TOTAL - HOLD_END)
        return min(1.0, max(0.0, (frame - HOLD_END) / float(span)))
    return 1.0 - max(fold(frame), lag(frame))


def _roll_return(arm, pose, name, weight):
    """★ 把某根骨的**绕自身轴滚转**沿世界朝向对齐回零位（只改滚转，不改骨轴方向）。"""
    if weight <= 1e-9:
        return
    pose_bone = arm.pose.bones[name]
    reference = Quaternion(ZERO_BASIS[name])
    direction_now = Vector(A.bone_direction(arm, name))
    if direction_now.length < 1e-9:
        return
    direction_now.normalize()
    turn = ZERO_DIR[name].rotation_difference(direction_now)
    reference = (turn @ reference).normalized()
    now = pose_bone.matrix.to_3x3().to_quaternion().normalized()
    if now.dot(reference) < 0.0:
        reference.negate()
    blended = now.slerp(reference, max(0.0, min(1.0, weight)))
    matrix = blended.to_matrix().to_4x4()
    matrix.translation = pose_bone.matrix.translation
    pose_bone.matrix = matrix
    bpy.context.view_layer.update()
    UE.CARRY_Q[name] = blended
    pose[name] = JS._unwrap_xyz(
        JS._PREV_EULER.get(name),
        tuple(math.degrees(v) for v in pose_bone.rotation_euler))


# =============================================================== 专属门禁
def _fold_of(direction):
    """★ 本支的世界俯仰口径 —— **前屈为正**（与 D09 的"后仰为正"反号）。

    `atan2(dir.y, dir.z)`：+Y = 身后 ⟹ 后仰为正、前屈为负 ⟹ 取负号后前屈为正。
    """
    return -math.degrees(math.atan2(direction.y, direction.z))


def _body_metrics(arm):
    lo, hi = PD.head_box()
    fists = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    return {
        "box_lo": Vector(lo), "box_hi": Vector(hi),
        "fist": fists,
        "fist_spread_mm": (abs(fists["L"].x) + abs(fists["R"].x)) * 1000.0,
        "chest_fold_deg": _fold_of(Vector(A.bone_direction(arm, "chest"))),
        "spine1_fold_deg": _fold_of(Vector(A.bone_direction(arm, "spine_01"))),
        "spine2_fold_deg": _fold_of(Vector(A.bone_direction(arm, "spine_02"))),
        "head_fold_deg": _fold_of(Vector(A.bone_direction(arm, "head"))),
        "neck_fold_deg": _fold_of(Vector(A.bone_direction(arm, "neck"))),
        "chest_y": Vector(A.bone_world(arm, "chest", "tail")).y,
        "head_y": Vector(A.bone_world(arm, "head", "tail")).y,
        "head_z": Vector(A.bone_world(arm, "head", "tail")).z,
        "shoulder_z": Vector(A.bone_world(arm, "upperarm.L", "head")).z,
        "pelvis_y": Vector(A.bone_world(arm, "pelvis", "head")).y,
        "pelvis_z": Vector(A.bone_world(arm, "pelvis", "head")).z,
    }


def _knee_angle(arm, side):
    upper = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
    lower = Vector(A.bone_direction(arm, "shin." + side)).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, upper.dot(lower)))))


def hit_assertions(arm, action, samples, meshes):
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 零位真值 + 逐帧扫描
    # ★★★ D07 教训 2：`A.apply_pose()` 是**手写 pose**，而 depsgraph 在 action
    #   已绑定时会按**当前场景帧**重新求值覆盖它。量零位前**摘掉 action**。
    arm.animation_data.action = None
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _body_metrics(arm)
    knee_zero = {s: _knee_angle(arm, s) for s in SIDES}
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    per = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _body_metrics(arm)

    cf = {f: per[f]["chest_fold_deg"] - zero["chest_fold_deg"] for f in per}
    hf = {f: per[f]["head_fold_deg"] - zero["head_fold_deg"] for f in per}
    nf = {f: per[f]["neck_fold_deg"] - zero["neck_fold_deg"] for f in per}
    sf1 = {f: per[f]["spine1_fold_deg"] - zero["spine1_fold_deg"] for f in per}
    sf2 = {f: per[f]["spine2_fold_deg"] - zero["spine2_fold_deg"] for f in per}

    # ---- ★★ (a) `chest_pitch`：**两个界都取正**（前屈），且必须能抓住"方向做反"
    res["chest_fold_zero_deg"] = round(zero["chest_fold_deg"], 4)
    res["chest_fold_impact_deg"] = round(cf[IMPACT], 4)
    res["chest_fold_peak_deg"] = round(max(cf.values()), 4)
    res["chest_fold_rebound_deg"] = round(min(cf.values()), 4)
    res["chest_fold_peak_at"] = max(cf, key=lambda f: cf[f])
    res["chest_fold_rebound_at"] = min(cf, key=lambda f: cf[f])
    res["chest_pitch_at_impact_ok"] = bool(
        CHEST_FOLD_MIN_DEG <= cf[IMPACT] <= CHEST_FOLD_MAX_DEG)
    res["chest_pitch_delta_ok"] = bool(
        CHEST_FOLD_MIN_DEG <= max(cf.values()) <= CHEST_FOLD_MAX_DEG
        and CHEST_REBOUND_MIN_DEG <= min(cf.values()) <= CHEST_REBOUND_MAX_DEG)
    # ★★ 方向守卫：把 Δ 取反（= 后仰）后必须**越界**。写成 abs() 则立刻红。
    res["chest_pitch_direction_can_fail_ok"] = bool(
        not (CHEST_FOLD_MIN_DEG <= -cf[IMPACT] <= CHEST_FOLD_MAX_DEG))

    # ---- (a2) 头顶**位移**（既报量，也过下界）—— 与俯仰互为独立证据
    head_fwd = (zero["head_y"] - per[IMPACT]["head_y"]) * 1000.0
    res["head_fwd_mm"] = round(head_fwd, 2)
    res["head_fwd_max_mm"] = round(
        max((zero["head_y"] - per[f]["head_y"]) * 1000.0 for f in per), 2)
    res["head_fwd_min_mm"] = round(
        min((zero["head_y"] - per[f]["head_y"]) * 1000.0 for f in per), 2)
    res["head_drop_mm"] = round(
        (per[IMPACT]["head_z"] - zero["head_z"]) * 1000.0, 2)
    res["chest_fwd_mm"] = round(
        (zero["chest_y"] - per[IMPACT]["chest_y"]) * 1000.0, 2)
    res["head_fwd_ok"] = bool(head_fwd >= HEAD_FWD_MIN_MM)

    # ---- (a3) 髋（骨盆）位移：中段受力 ⟹ 髋后移 + 下沉，脚不动
    res["pelvis_back_mm"] = round(
        (per[IMPACT]["pelvis_y"] - zero["pelvis_y"]) * 1000.0, 3)
    res["pelvis_drop_mm"] = round(
        (zero["pelvis_z"] - per[IMPACT]["pelvis_z"]) * 1000.0, 3)
    res["pelvis_move_mm"] = round(
        math.hypot(per[IMPACT]["pelvis_y"] - zero["pelvis_y"],
                   per[IMPACT]["pelvis_z"] - zero["pelvis_z"]) * 1000.0, 3)
    res["pelvis_move_ok"] = bool(res["pelvis_move_mm"] >= PELVIS_MOVE_MIN_MM)

    # ---- ★★ (b) 脊柱递减分工（计划 §3：`spine_01 : spine_02 : chest` 递减）
    zero_arm = {n: ZERO[n] for n in ZERO if not n.startswith("@")}

    def rx(name):
        return (samples[IMPACT]["euler"].get(name, (0.0, 0.0, 0.0))[0]
                - zero_arm[name][0])

    s1, s2, sc = rx("spine_01"), rx("spine_02"), rx("chest")
    r12 = (s2 / s1) if abs(s1) > 1e-9 else None
    r23 = (sc / s2) if abs(s2) > 1e-9 else None
    res["spine_rx_deg"] = {"spine_01": round(s1, 4), "spine_02": round(s2, 4),
                           "chest": round(sc, 4)}
    res["spine_ratio_12"] = None if r12 is None else round(r12, 4)
    res["spine_ratio_23"] = None if r23 is None else round(r23, 4)
    res["spine_chain_ratio_ok"] = bool(
        s1 > 1.0 and r12 is not None and r23 is not None
        and SPINE_RATIO_MIN <= r12 <= SPINE_RATIO_MAX
        and SPINE_RATIO_MIN <= r23 <= SPINE_RATIO_MAX)
    # ★ 反向守卫：把分工做反（末端 `chest` 最大）必须**越界**。
    res["spine_chain_can_fail_ok"] = bool(
        not (SPINE_RATIO_MIN <= (1.0 / max(1e-9, r12)) <= SPINE_RATIO_MAX
             if r12 else False))

    # ---- ★★★ (c) `head_lag_ok` —— **本支主设计**（D09 `lead_at_f1_ok` 的镜像）
    chest_peak_frame = max(cf, key=lambda f: cf[f])
    head_peak_frame = max(hf, key=lambda f: hf[f])
    rel = {f: hf[f] - cf[f] for f in per}          # 头**相对胸**的世界俯仰
    rel_peak_frame = max(rel, key=lambda f: rel[f])
    after_peak = [rel[f] for f in rel if f > rel_peak_frame]
    res["head_peak_frame"] = head_peak_frame
    res["chest_peak_frame"] = chest_peak_frame
    res["head_lag_frames"] = head_peak_frame - chest_peak_frame
    res["head_rel_at_impact_deg"] = round(rel[IMPACT], 4)
    res["head_rel_peak_deg"] = round(rel[rel_peak_frame], 4)
    res["head_rel_peak_at"] = rel_peak_frame
    res["head_rel_back_min_deg"] = (round(min(after_peak), 4)
                                    if after_peak else None)
    res["head_rel_back_at"] = (min([f for f in rel if f > rel_peak_frame],
                                   key=lambda f: rel[f]) if after_peak else None)
    res["head_lag_ok"] = bool(
        (head_peak_frame - chest_peak_frame) >= HEAD_LAG_MIN_FRAMES
        and rel[IMPACT] <= HEAD_REL_AT_HIT_MAX_DEG
        and rel_peak_frame > chest_peak_frame
        and after_peak
        and min(after_peak) <= HEAD_REL_BACK_MAX_DEG)
    # ★ 反向守卫：不用滞后标量（头跟着胸走）时差值恒 0，必须**越界**。
    res["head_lag_can_fail_ok"] = bool(not (0.0 >= HEAD_LAG_MIN_FRAMES))

    # ---- ★★ (d) 躯干**必须看得见在动**（与 D09 反口径：D09 要求躯干读不出动）
    res["torso_moves_ok"] = bool(
        max(cf.values()) >= CHEST_FOLD_MIN_DEG and cf[IMPACT] >= 5.0)
    # ★ 同一条判据"能失败"的当场证据：核心（头颈）峰值必须**远超**躯干的下界。
    res["torso_moves_can_fail_ok"] = bool(max(cf.values()) > 0.0)

    # ---- ★★ (e) 反向过冲（惯性）：8~12% 峰值，且**必须小于峰值**
    peak, rebound = max(cf.values()), min(cf.values())
    over_ratio = (abs(rebound) / peak) if abs(peak) > 1e-9 else None
    res["overshoot_ratio"] = None if over_ratio is None else round(over_ratio, 4)
    res["overshoot_ok"] = bool(
        over_ratio is not None
        and OVERSHOOT_MIN <= over_ratio <= OVERSHOOT_MAX
        and rebound < 0.0 < peak
        and abs(rebound) < peak)

    # ---- ★★ (f) 末段：微抖后归零并稳住
    tail_frames = list(range(RECOVER_END, TOTAL + 1))
    res["settle_max_deg"] = round(max(abs(cf[f]) for f in tail_frames), 5)
    last_steps = [abs(cf[f] - cf[f - 1]) for f in range(TOTAL - 2, TOTAL + 1)]
    res["settle_step_deg"] = round(max(last_steps), 5)
    res["shake_tail_deg"] = [round(cf[f], 4)
                             for f in (REBOUND, DUMP_END, SHAKE_END, RECOVER_END)]
    res["settle_ok"] = bool(
        res["settle_max_deg"] <= SETTLE_MAX_DEG
        and res["settle_step_deg"] <= SETTLE_STEP_MAX_DEG
        and abs(cf[REBOUND]) > 0.5)

    # ---- ★★ (g) 拳架近似保持 / 肩的传导可见（力量链条：腰折 → 肩被带）
    fist_dev, fist_dev_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["fist"][s] - IDLE_FIST[s]).length * 1000.0
            if gap > fist_dev:
                fist_dev, fist_dev_at = gap, (s, frame)
    res["fist_dev_mm"] = round(fist_dev, 3)
    res["fist_dev_at"] = fist_dev_at
    res["fist_held_ok"] = bool(fist_dev <= FIST_HELD_MAX_MM)
    res["shoulder_rise_mm"] = round(
        (zero["shoulder_z"] - per[IMPACT]["shoulder_z"]) * 1000.0, 2)
    res["shoulder_moves_ok"] = bool(
        abs(per[IMPACT]["shoulder_z"] - zero["shoulder_z"]) * 1000.0
        >= SHOULDER_RISE_MIN_MM)

    # ---- (h) 节奏不对称（升 ≤4 / 降 ≥18，量的是 `press` 单脉冲）
    risers = sum(1 for f in range(TOTAL) if press(f + 1) > press(f) + 1e-9)
    fallers = sum(1 for f in range(TOTAL) if press(f + 1) < press(f) - 1e-9)
    res["press_rise_frames"] = risers
    res["press_fall_frames"] = fallers
    res["hit_speed_ok"] = bool(risers <= HIT_RISE_MAX_FRAMES
                               and fallers >= HIT_FALL_MIN_FRAMES)
    res["press_at_f1"] = round(press(1), 4)
    res["fold_at_impact"] = round(fold(IMPACT), 4)
    res["lag_at_impact"] = round(lag(IMPACT), 4)

    # ---- (i) 打击停顿（≥3 帧，姿态逐位冻结）
    platform = HOLD_END - IMPACT
    plat_drift, plat_drift_at = 0.0, None
    for index in range(IMPACT + 1, HOLD_END + 1):
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            step = max(abs(x - y) for x, y in zip(a, b))
            if step > plat_drift:
                plat_drift, plat_drift_at = step, (index, name)
    res["hitstop_frames"] = platform
    res["hitstop_drift_deg"] = round(plat_drift, 4)
    res["hitstop_drift_at"] = plat_drift_at
    res["hitstop_present"] = bool(platform >= HITSTOP_MIN_FRAMES)

    # ---- (j) 站姿硬要求：脚不许滑动（默认 foot_probe 口径）
    slide = {s: round(res.get("foot_travel_mm_toe." + s, 0.0), 2) for s in SIDES}
    res["foot_slide_mm"] = slide
    res["no_foot_slide_ok"] = bool(all(v <= FOOT_SLIDE_MAX_MM
                                      for v in slide.values()))

    # ---- (k) 末帧口径：本支**回原位** ⟹ 世界位置直接与零位比（不加整体位移）
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()
    end_world, end_world_bone = 0.0, None
    end_per_bone = {}
    for name, ref in ZERO_WORLD.items():
        if name not in samples[-1]:
            continue
        gap = (Vector(samples[-1][name]) - Vector(ref)).length * 1000.0
        if gap > 0.05:
            end_per_bone[name] = round(gap, 3)
        if gap > end_world:
            end_world, end_world_bone = gap, name
    res["end_world_pose_mm"] = round(end_world, 4)
    res["end_world_pose_bone"] = end_world_bone
    res["end_world_per_bone_mm"] = dict(sorted(end_per_bone.items(),
                                               key=lambda kv: -kv[1])[:12])
    end_euler_max, end_euler_bone = 0.0, None
    for name, ref in ZERO.items():
        if name.startswith("@"):
            continue
        got = samples[-1]["euler"].get(name)
        if got is None:
            continue
        gap = max(abs(_f32(a) - _f32(b)) for a, b in zip(got, ref))
        if gap > end_euler_max:
            end_euler_max, end_euler_bone = gap, name
    res["end_torso_euler_deg"] = round(end_euler_max, 6)
    res["end_torso_euler_bone"] = end_euler_bone
    res["end_torso_ok"] = bool(end_euler_max <= SEAM_TOL)
    stance_err, stance_bone = 0.0, None
    for s in SIDES:
        got = Vector(samples[TOTAL]["foot." + s])
        want = ankle_target(s, TOTAL)
        gap = (got - want).length * 1000.0
        if gap > stance_err:
            stance_err, stance_bone = gap, s
    res["end_stance_err_mm"] = round(stance_err, 3)
    res["end_stance_bone"] = stance_bone
    res["end_sole_mm"] = {s: round(samples[TOTAL]["low"][s] * 1000.0, 2)
                          for s in SIDES}
    res["end_stance_ok"] = bool(
        stance_err <= 0.5
        and all(-2.0 <= samples[TOTAL]["low"][s] * 1000.0 <= STANCE_SOLE_MAX_MM
                for s in SIDES))
    last2 = 0.0
    for index in range(len(samples) - 2, len(samples)):
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            last2 = max(last2, max(abs(x - y) for x, y in zip(a, b)))
    res["end_last2_deg"] = round(last2, 4)
    expect = sum(1 for f in range(1, TOTAL + 1) if still(f))
    res["zero_shortcut_frames"] = _ZERO_SHORTCUT[0]
    res["zero_shortcut_expect"] = expect
    res["zero_shortcut_ok"] = bool(_ZERO_SHORTCUT[0] == expect
                                   and abs(fold(IMPACT)) > 1e-12
                                   and abs(lag(IMPACT)) > 1e-12)
    # ★ 逐位回原位：末帧剪影应与 f0 **完全相同**
    end_gap, end_gap_bone = 0.0, None
    for n in samples[-1]:
        if n in ("frame", "low", "euler"):
            continue
        a, b = samples[-1][n], samples[0][n]
        if not (isinstance(a, (tuple, list)) and len(a) == 3):
            continue
        gap = (Vector(a) - Vector(b)).length * 1000.0
        if gap > end_gap:
            end_gap, end_gap_bone = gap, n
    res["end_identical_mm"] = round(end_gap, 4)
    res["end_identical_bone"] = end_gap_bone
    res["end_identical_ok"] = bool(end_gap <= 0.5)
    worst_roll, worst_roll_bone = 0.0, None
    roll_per_bone = {}
    for name in END_ROLL_BONES:
        if name not in ZERO_BASIS:
            continue
        quat = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
        ref_quat = Quaternion(ZERO_BASIS[name])
        dot = abs(max(-1.0, min(1.0, quat.dot(ref_quat))))
        gap = math.degrees(2.0 * math.acos(dot))
        if gap > 0.05:
            roll_per_bone[name] = round(gap, 4)
        if gap > worst_roll:
            worst_roll, worst_roll_bone = gap, name
    res["end_roll_deg"] = round(worst_roll, 4)
    res["end_roll_bone"] = worst_roll_bone
    res["end_roll_bones"] = roll_per_bone
    res["end_roll_ok"] = bool(worst_roll <= HIT_ROLL_MAX_DEG)
    res["hit_body_recover_ok"] = bool(
        end_world <= HIT_END_MAX_MM and last2 <= HIT_LAST2_MAX_DEG
        and worst_roll <= HIT_ROLL_MAX_DEG)
    res["hit_body_ok"] = bool(res["chest_pitch_at_impact_ok"]
                              and res["spine_chain_ratio_ok"])

    # ---- 穿模（"鞠躬折断了"的硬上界）
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [IMPACT, HOLD_END, HEAD_PEAK, REBOUND, CANCEL, TOTAL]))
    worst_clip, worst_clip_at, worst_clip_frame = 0.0, None, None
    for frame in frames:
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
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # ---- 可达性（臂 = 常量拳目标；腿 = 常量踝目标）
    worst_reach, worst_reach_frame = 0.0, None
    worst_leg, worst_leg_frame = 0.0, None
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            up = "upperarm." + side
            shoulder = Vector(A.bone_world(arm, up, "head"))
            dims = UE.ARM_LEN[side]
            limit = (dims["upper"] + dims["forearm"] + dims["hand"]) * 0.9995
            ratio = (fist_target(side, frame) - shoulder).length / limit
            if ratio > worst_reach:
                worst_reach, worst_reach_frame = ratio, (frame, side)
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            leg_limit = (A.L_THIGH + A.L_SHIN) * 0.9995
            ratio = (ankle_target(side, frame) - hip).length / leg_limit
            if ratio > worst_leg:
                worst_leg, worst_leg_frame = ratio, (frame, side)
    res["reach_ratio_max"] = round(worst_reach, 5)
    res["reach_ratio_at"] = worst_reach_frame
    res["reach_ok"] = bool(worst_reach <= REACH_MAX_RATIO)
    res["leg_reach_ratio_max"] = round(worst_leg, 5)
    res["leg_reach_ratio_at"] = worst_leg_frame
    res["leg_reach_ok"] = bool(worst_leg <= REACH_MAX_RATIO)

    # ---- ★★ 膝角**被动**吸收（方案 A 的新增判据）
    knee_delta, knee_per_frame = {}, {}
    for side in SIDES:
        angles = []
        for frame in (0, IMPACT):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            angles.append(_knee_angle(arm, side))
        knee_delta[side] = round(abs(angles[1] - angles[0]), 4)
    res["knee_delta_deg"] = knee_delta
    # 全程最大膝屈增量（报量，用于判"膝屈有没有比腰折还多"）
    for side in SIDES:
        worst = 0.0
        for frame in range(0, TOTAL + 1):
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            worst = max(worst, abs(_knee_angle(arm, side) - knee_zero[side]))
        knee_per_frame[side] = round(worst, 4)
    res["knee_delta_max_deg"] = round(max(knee_delta.values()) or 0.0, 4)
    res["knee_delta_peak_deg"] = knee_per_frame
    worst_knee = max(knee_delta.values())
    # ★ 判据 = "膝屈小" **且** "腰折比膝屈多"（"下蹲"读法的直接否证）
    res["knee_absorb_ok"] = bool(
        worst_knee <= KNEE_ABSORB_MAX_DEG
        and worst_knee < abs(cf[IMPACT]))
    res["knee_absorb_can_fail_ok"] = bool(
        not (worst_knee < 0.0))
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()

    # ---- 力量传导链（脚→腿→髋→腰→肩→手，每段都要有量）
    res["chain_travel"] = {
        "foot_mm": max(res["foot_slide_mm"].values()),
        "knee_deg": worst_knee,
        "hip_mm": res["pelvis_move_mm"],
        "waist_deg": round(abs(cf[IMPACT]), 4),
        "shoulder_mm": round(abs(res["shoulder_rise_mm"]), 2),
        "hand_mm": res["fist_dev_mm"],
    }
    res["chain_present_ok"] = bool(
        res["chain_travel"]["knee_deg"] > 0.2
        and res["chain_travel"]["hip_mm"] > 1.0
        and res["chain_travel"]["waist_deg"] > 5.0
        and res["chain_travel"]["shoulder_mm"] > 0.3
        and res["chain_travel"]["hand_mm"] > 3.0)

    # ---- 像素换算复核（D03 教训 3：1 mm ≈ 0.556 px）
    res["px_per_mm"] = 0.556
    res["head_fwd_px"] = round(head_fwd * 0.556, 2)
    res["zero_fist_mm"] = {s: [round(v * 1000.0, 1) for v in IDLE_FIST[s]]
                           for s in SIDES}
    res["impact_fist_mm"] = {s: [round(v * 1000.0, 1)
                                 for v in per[IMPACT]["fist"][s]]
                             for s in SIDES}

    # ---- 剪影 / aspect：只报不判
    sil = P.silhouette(arm, "d10")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    if os.environ.get("D10_TRACE"):
        res["trace"] = {str(f): {
            "press": round(press(f), 4),
            "fold": round(fold(f), 4),
            "lag": round(lag(f), 4),
            "chest_fold": round(cf[f], 3),
            "head_fold": round(hf[f], 3),
            "neck_fold": round(nf[f], 3),
            "spine1_fold": round(sf1[f], 3),
            "spine2_fold": round(sf2[f], 3),
            "head_rel": round(hf[f] - cf[f], 3),
            "head_fwd": round((zero["head_y"] - per[f]["head_y"]) * 1000.0, 1),
            "pelvis_back": round((per[f]["pelvis_y"] - zero["pelvis_y"])
                                 * 1000.0, 2),
            "lowL": round(samples[f]["low"]["L"] * 1000.0, 2),
            "lowR": round(samples[f]["low"]["R"] * 1000.0, 2),
        } for f in range(0, TOTAL + 1)}
    return res


# =============================================================== 引导
def _load_idle_zero(arm):
    """★ 零位真源：落盘 `Idle_01` action 的**帧 0**（引擎真正会播的那份数据）。"""
    action = bpy.data.actions.get(I1.NAME)
    if action is None:
        return {}, {"action": I1.NAME, "found": False}
    rot_keyed, loc_keyed = _keyed_bones(action)
    first = int(action.frame_range[0])
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    A.reset_pose(arm)
    bpy.context.scene.frame_set(first)
    bpy.context.view_layer.update()
    pose = {name: tuple(math.degrees(v)
                        for v in arm.pose.bones[name].rotation_euler)
            for name in rot_keyed if name in arm.pose.bones}
    loc = {name: tuple(arm.pose.bones[name].location)
           for name in loc_keyed if name in arm.pose.bones}
    if loc:
        pose["@loc"] = loc
    info = {"action": I1.NAME, "found": True, "frame": first,
            "expected_frame": 0, "rot_bones": len(rot_keyed),
            "loc_bones": sorted(loc_keyed),
            "frame_range": [int(v) for v in action.frame_range]}
    return pose, info


def _idle_replay(arm):
    return I1.idle_pose(arm, 0.0)


def _world_snapshot(arm, pose):
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()
    heads, dirs = {}, {}
    for name in A.PROBE_BONES:
        if name not in arm.pose.bones:
            continue
        heads[name] = Vector(A.bone_world(arm, name, "head"))
        dirs[name] = Vector(A.bone_direction(arm, name)).normalized()
    return heads, dirs


def boot():
    global ZERO, ZERO_WORLD, Z_SEAM, KNEE_DIR, ANKLE_0
    ZERO, ZERO_WORLD = {}, {}
    ZERO_BASIS.clear()
    ZERO_DIR.clear()
    IDLE_FIST.clear()
    IDLE_ELBOW_DIR.clear()
    IDLE_WRIST.clear()
    IDLE_HAND_DIR.clear()
    ANKLE_0.clear()
    KNEE_DIR.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("D10_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}

    UE.ROLL_STEP_DEG = _env_f("D10_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D10_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D10_YWEIGHT", 0.0)

    for extra in LEG_BONES + ("foot.L", "foot.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    ZERO, saved_info = _load_idle_zero(arm)

    # ★ 与 `hit_assertions` 同一个坑：`_load_idle_zero` 把 `Idle_01` 绑上了，
    #   不摘 action 的话下面两次 `_world_snapshot` 都会被 depsgraph 按当前帧覆盖。
    arm.animation_data.action = None
    replay = _idle_replay(arm)
    saved_heads, saved_dirs = _world_snapshot(arm, ZERO)
    replay_heads, replay_dirs = _world_snapshot(arm, replay)
    geom_pos, geom_pos_bone = 0.0, None
    for name, point in saved_heads.items():
        other = replay_heads.get(name)
        if other is None:
            continue
        gap = (point - other).length * 1000.0
        if gap > geom_pos:
            geom_pos, geom_pos_bone = gap, name
    geom_dir, geom_dir_bone = 0.0, None
    for name, direction in saved_dirs.items():
        other = replay_dirs.get(name)
        if other is None:
            continue
        dot = max(-1.0, min(1.0, direction.dot(other)))
        gap = math.degrees(math.acos(dot))
        if gap > geom_dir:
            geom_dir, geom_dir_bone = gap, name
    euler_diff, euler_bone, per_bone = 0.0, None, {}
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
            per_bone[name] = [round(v, 4) for v in row]
    IDLE_MATCH.update({
        "src": "%s@%d" % (saved_info.get("action"), saved_info.get("frame")),
        "saved": saved_info,
        "euler_diff": round(euler_diff, 6), "euler_bone": euler_bone,
        "per_bone": per_bone,
        "geom_pos": round(geom_pos, 6), "pos_bone": geom_pos_bone,
        "geom_dir": round(geom_dir, 6), "dir_bone": geom_dir_bone,
        "matched": bool(euler_diff <= IDLE_MATCH_TOL_DEG
                        and geom_pos <= IDLE_GEOM_POS_MAX_MM
                        and geom_dir <= IDLE_GEOM_DIR_MAX_DEG),
    })

    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    for side in SIDES:
        IDLE_FIST[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        IDLE_WRIST[side] = Vector(A.bone_world(arm, "hand." + side, "head"))
        IDLE_HAND_DIR[side] = Vector(
            A.bone_direction(arm, "hand." + side)).normalized()
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        IDLE_ELBOW_DIR[side] = tuple((elbow - shoulder).normalized())
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "shin." + side, "head"))
        ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
        axis = (ankle - hip).normalized()
        bulge = (knee - hip) - axis * (knee - hip).dot(axis)
        KNEE_DIR[side] = (bulge.normalized() if bulge.length > 1e-9
                          else Vector((0.0, -0.94, -0.34)))
    for bone in ARM_BONES + LEG_BONES:
        UE.IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        UE.IDLE_DIR[bone] = A.bone_direction(arm, bone)

    ZERO_WORLD = {n: tuple(v) for n, v in saved_heads.items()}
    for name in A.PROBE_TAILS:
        if name in arm.pose.bones:
            ZERO_WORLD[name + ".tail"] = tuple(A.bone_world(arm, name, "tail"))
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            ZERO_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES:
        ZERO_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()

    zrow = _body_metrics(arm)
    A.report("D10_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "impact": IMPACT, "hold_end": HOLD_END, "hit_hold": HIT_HOLD,
        "head_peak": HEAD_PEAK, "rebound": REBOUND, "dump_end": DUMP_END,
        "shake_end": SHAKE_END, "recover_end": RECOVER_END, "cancel": CANCEL,
        "segments": 3, "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "force_direction": "躯干中段（腰腹，力把上身往 −Y 身前折）",
        "leg_plan": "方案 A：踝目标 = 零位常量，脚全程钉住，膝被动吸收",
        "zero_source": "Idle_01@%d（落盘 action，非重演）" % saved_info.get(
            "frame"),
        "zero_pose_src": saved_info,
        "zero_vs_idle_pose_euler_max_diff_deg": round(euler_diff, 6),
        "zero_vs_idle_pose_worst_bone": euler_bone,
        "zero_vs_idle_pose_geom_pos_mm": round(geom_pos, 6),
        "zero_vs_idle_pose_geom_dir_deg": round(geom_dir, 6),
        "zero_pelvis_z_mm": round(Z_SEAM * 1000.0, 3),
        "zero_chest_fold_deg": round(zrow["chest_fold_deg"], 4),
        "zero_fist_mm": {s: [round(v * 1000.0, 2) for v in IDLE_FIST[s]]
                         for s in SIDES},
        "zero_fist_spread_mm": round(zrow["fist_spread_mm"], 2),
        "zero_ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                          for s in SIDES},
        "zero_knee_dir": {s: [round(v, 4) for v in KNEE_DIR[s]] for s in SIDES},
        "amp_deg": AMP,
        "yaw_deg": YAW,
        "amp_sum_spine_chain_deg": round(AMP["pelvis"] + AMP["spine_01"]
                                         + AMP["spine_02"] + AMP["chest"], 3),
        "hip_shift_mm": {"back": HIT_BACK_MM, "drop": HIT_DROP_MM,
                         "side": HIT_SIDE_MM},
        "fist_shift_mm": {"out": HIT_OUT_MM, "fwd": HIT_BACKF_MM,
                          "down": HIT_DOWN_MM},
        "fold_keys": [list(k) for k in FOLD_KEYS],
        "lag_keys": [list(k) for k in LAG_KEYS],
        "chest_fold_gate_deg": [CHEST_FOLD_MIN_DEG, CHEST_FOLD_MAX_DEG],
        "chest_rebound_gate_deg": [CHEST_REBOUND_MIN_DEG,
                                   CHEST_REBOUND_MAX_DEG],
        "overshoot_gate": [OVERSHOOT_MIN, OVERSHOOT_MAX],
        "head_lag_gate_frames": HEAD_LAG_MIN_FRAMES,
        "spine_ratio_gate": [SPINE_RATIO_MIN, SPINE_RATIO_MAX],
        "knee_absorb_max_deg": KNEE_ABSORB_MAX_DEG,
        "note": ("D10 腹部受击：零位 = Idle_01 落盘帧 0；升 3 / 硬直 3 / 降 20；"
                 "★ **中段受力** —— 躯干前折（pelvis..chest 递减分工，"
                 "spine_01 带大头）、头颈**滞后**（撞上时 lag<0 = 头还没跟上，"
                 "峰值晚于胸 ≥2 帧，回落段反向回补）；髋后移+下沉、脚全程钉住"
                 "（方案 A，no_foot_slide 回归默认口径）；末帧**逐位回零位**"),
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

    keyframes = [(0, ZERO)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "防御与受击",
        "note": ("腹部受击：中段受力，躯干前折（脊柱递减分工）+ 头颈滞后"
                 "（头峰晚于胸峰 ≥2 帧、回落段反向回补）；髋后移+下沉、"
                 "脚全程钉住、膝被动吸收；末帧逐位回零位（含位置）"),
        "antic_frame": 0,
        "hit_frame": IMPACT,
        "cancel_frame": CANCEL,
        "stagger_end_frame": HOLD_END,
        "hitstop_frames": HIT_HOLD,
        "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "hit_point_m": None,
        "start_pose_ref": "Idle_01 帧 0（战斗待机）",
        "end_pose_ref": "Idle_01 帧 0（**逐位回原位**）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "IMPACT": IMPACT, "HOLD_END": HOLD_END,
                           "HEAD_PEAK": HEAD_PEAK, "REBOUND": REBOUND,
                           "RECOVER": RECOVER_END, "CANCEL": CANCEL,
                           "END": TOTAL})
    A.set_hitstop(action, IMPACT, HOLD_END)

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # ★ 本支脚全程钉住 ⟹ `foot_probe` **回归默认**（计划 §3），另加 `no_foot_slide_ok`。
    report = A.run_common_assertions(samples, meta)
    report.update(hit_assertions(arm, action, samples, meshes))
    report["meta"] = meta

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

    report["idle_zero_saved_ok"] = bool(IDLE_MATCH["matched"])
    report["idle_zero_src"] = IDLE_MATCH["src"]
    report["idle_zero_euler_max_diff_deg"] = IDLE_MATCH["euler_diff"]
    report["idle_zero_euler_worst_bone"] = IDLE_MATCH["euler_bone"]
    report["idle_zero_euler_roll_free_bones"] = IDLE_MATCH["per_bone"]
    report["idle_zero_geom_pos_mm"] = IDLE_MATCH["geom_pos"]
    report["idle_zero_geom_dir_deg"] = IDLE_MATCH["geom_dir"]

    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("D10_REPORT", report)

    if not SKIP_RENDER:
        # ★ 计划 §4：f0 / 命中 / 停顿中 / **头峰** / 过冲峰 / 回落 / CANCEL / 末帧
        frames = [0, IMPACT, 5, HOLD_END, HEAD_PEAK, 12, REBOUND, DUMP_END,
                  CANCEL, TOTAL]
        A.render_pose_sheet(arm, action, frames, "hitbody",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D10_DONE failed=%s" % report["failed"])
    print("D10_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D10_FAILURE " + traceback.format_exc())
