"""anim_hit_leg —— D11 `Hit_Leg` 腿部受击。

清单原文：「对应腿部命中，下盘晃动」。

★★ 本支是受击族里**唯一**受力点在下盘的 ── 力量从腿上打进来 ⟹
   骨盆/腿**先**动，上身**被动**跟着晃（滞后），最后一起归零。

与 D09 / D10 的根本区别（计划 §0）：

| 支 | 受力点 | 主设计 | 上身行为 |
|---|---|---|---|
| D09 `Hit_Head` | 头颈（**末端**） | 头颈**领跑** | 躯干不动 |
| D10 `Hit_Body` | 躯干**中段** | 躯干前折 | 头颈**滞后** |
| **D11 `Hit_Leg`** | **腿部（下盘）** | **下盘先动** | **上身滞后补平衡** |

方向（计划 §0）：取**侧向**受力（一记扫腿/低踢打在外侧）。
   受力侧取**角色左腿** `L`（+X 侧）。力把下盘往 **+X（角色左 = 受力侧）** 推 ⟹
      · 骨盆**侧移** +X（`HIT_SIDE_MM > 0`）
      · 骨盆**侧倾**往受力侧（`rz < 0`；语义表：`rz > 0` = 向角色**右**侧倾）
      · 受力侧（L）**髋下沉** ⟹ 踝被钉住 ⟹ **L 膝被动屈曲 > R 膝**（`knee_asym`）
      · 侧视相机在 +X，读不出左右 ⟹ **主检前视 + 3Q**，侧视只报
   本支定义 `pelvis_tilt = atan2(pelvis_dir.x, pelvis_dir.z)` ⟹ **往受力侧（+X）倾为正**。

★★ 上身滞后的实现（本支唯一的技术难点）：
   `pelvis.rz` 会**整条链一起带走**（thigh / spine 都是它的子骨）。若上身只写局部 rz，
   骨盆转 9° 上身就跟着转 9° —— 那不是"滞后"，是"整体刚体倾倒"。
   ⟹ 本支改为**直接给每节骨的 WORLD 侧倾目标**，再换算局部 rz：
        `rz_self = W_parent − W_self`
      · 下盘：`W_pelvis = PELVIS_TILT_DEG · thud(f)`（命中帧吃满）
      · 上身：`W_upper  = UPPER_TILT_DEG  · sway(f)`（命中帧**负**、峰值晚 ≥2 帧）
      · 命中帧 W_pelvis = 9°、W_upper ≈ −0.9° ⟹ 脊柱链用**正 rz 反向抵消**
        骨盆带来的倾斜 ⟹ 上身**留在原地**（这才是"没跟上"）。
      · 峰值帧 W_upper 追到 +6° ⟹ 上身**被带着晃过去**（幅度小于下盘）。

★★ 三根驱动标量（D09/D10 结构的直接继承）：
    `press` —— **单调**单脉冲（升 3 / 硬直 3 / 降 20）⟹ 只当"节奏时钟"与
               `zero_shortcut` 的作用域。
    `thud`  —— **下盘主驱动**：命中峰 1.0 → 回弹 −9%（惯性）→ 微抖 → 0。
    `sway`  —— **上身滞后驱动**：命中帧**负**（还没跟上）→ 峰 +1.0（f8，晚于骨盆 5 帧）
               → **反向回补** → 0。
    `sway_head` —— 头颈比胸再晚 1 帧、幅度略大（把"甩"做出来）。

继承（逐条照抄，别重写）：
    · 骨架 / 零位加载 / `_ZERO_SHORTCUT` / `_roll_return` 滚-瞄交替 2 趟
      / `end_torso_ok` / `zero_shortcut_ok` / `fist_held_ok` 的构造
    · D05 三条修正：`arm_seat_tip()` / `elbow_hit()` 乘标量 / `KNEE_DIR[side]`
    · D07 教训 2：量零位前必须 `arm.animation_data.action = None`
    · D07 教训 3：`_roll_return` 必须"滚一趟 → 重瞄一趟"交替、末趟收在"瞄"上
    · D09/D10 教训 1：**首跑即绿必须先做反向验证**（符号反 / 幅度小 / 幅度大 / 抽主驱动）
    · D08 教训 1：腿相对髋摆开会让**鞋底网格**下沉（蒙皮伪影）——
      本支骨盆侧移 30 mm / 下沉 9 mm（远小于 D08 的 137 mm）⟹ 预判 <1 mm，
      由 `ground_contact_ok` 直接盯，**不引入** `sole_lift`。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_hit_leg.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D11_TRACE=1    逐帧打印 press / thud / sway / 骨盆·胸·头世界侧倾（调参用）
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

NAME = "Hit_Leg"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
# ★ 受力侧 = 角色左腿（+X 侧）；支撑侧 = 右腿。
HIT_SIDE = os.environ.get("D11_HITSIDE", "L").strip().upper()
SUPPORT_SIDE = "R" if HIT_SIDE == "L" else "L"


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
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D10 同源）。"""
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
# ★ 计划 §2：时长量级「约 34~40 帧」⟹ 取 38 帧 = 0.633 s @60fps（同 D10）。
TOTAL = _env_i("D11_TOTAL", 38)             # 0.633 s @60fps
IMPACT = _env_i("D11_IMPACT", 3)            # 下盘命中峰（上升沿 3 帧）
HIT_HOLD = _env_i("D11_HOLD", 3)            # 小硬直平台 3 帧
HOLD_END = IMPACT + HIT_HOLD                # 6
UPPER_PEAK = _env_i("D11_UPPER_PEAK", 8)    # ★ 上身侧倾峰 —— 必须晚于 IMPACT ≥2 帧
HEAD_PEAK = _env_i("D11_HEAD_PEAK", 9)      # ★ 头颈再晚 1 帧（把"甩"做出来）
REBOUND = _env_i("D11_REBOUND", 16)         # 反向过冲峰（上身弹回，惯性）
DUMP_END = _env_i("D11_DUMP", 19)           # 过冲之后的第一微抖峰
SHAKE_END = _env_i("D11_SHAKE", 22)         # 第二微抖峰
RECOVER_END = _env_i("D11_RECOVER", 26)     # 驱动标量回到 0 的帧（降 20 帧）
CANCEL = _env_i("D11_CANCEL", 30)
#   ★ 为什么回落取 20 帧：`no_teleport`（≤25°/帧）是物理下界；本支侧倾峰值 ~9°、
#     脊柱反向分量 ~4°，若 5 帧回完 ⟹ 单帧 2.6°+ 且末段速度不连续；20 帧给足惯性感，
#     且满足"升 ≤4 / 降 ≥18"的不对称要求（命中快、回落慢）。

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
GROUND_MIN_MM, GROUND_MAX_MM = -2.0, 6.0
REACH_MAX_RATIO = 0.995
# ---- ★★ 本支头号判据（计划 §2）：骨盆**世界侧倾**（往受力侧为正）------------
PELVIS_TILT_MIN_DEG = _env_f("D11_TILT_MIN", 5.0)
PELVIS_TILT_MAX_DEG = _env_f("D11_TILT_MAX", 14.0)
PELVIS_REB_MIN_DEG = _env_f("D11_REB_MIN", -2.4)
PELVIS_REB_MAX_DEG = _env_f("D11_REB_MAX", -0.5)
OVERSHOOT_MIN = _env_f("D11_OVS_MIN", 0.08)
OVERSHOOT_MAX = _env_f("D11_OVS_MAX", 0.12)
# ---- ★★★ 本支主设计 `lower_body_leads_ok`（计划 §2）-----------------------
LEAD_MIN_FRAMES = _env_f("D11_LEAD_FRAMES", 2.0)     # 骨盆峰必须早于胸/头峰 ≥2 帧
LOWER_PROGRESS_MIN = _env_f("D11_LOWPROG", 0.90)     # 命中帧下身进度 ≈ 1.0
UPPER_PROGRESS_MAX = _env_f("D11_UPPROG", 0.25)      # 命中帧上身进度 ≤ 0.25
# ---- ★ 下盘晃动是**不对称**的（"被扫腿"与"自己下蹲"的分界，计划 §2）--------
KNEE_ASYM_MIN_DEG = _env_f("D11_KNEE_ASYM", 0.5)     # 受力侧膝屈 > 支撑侧 + 余量
KNEE_MAX_DEG = _env_f("D11_KNEE_MAX", 12.0)          # 两膝都应是**被动**吸收
# ---- ★ 上身只能"跟着晃"、不得**独立大幅主动**（计划 §2）------------------
UPPER_FOLD_MAX_DEG = _env_f("D11_UPPER_FOLD", 6.0)   # chest 前后折增量上界
UPPER_TILT_RATIO_MAX = _env_f("D11_UPPER_RATIO", 1.0)  # 上身侧倾 ≤ 下身侧倾
# ---- ★ 骨盆**侧向位移**（下盘晃动的主动量，计划 §2）------------------------
PELVIS_SIDE_MIN_MM = _env_f("D11_SIDE_MIN", 10.0)
PELVIS_SIDE_MAX_MM = _env_f("D11_SIDE_MAX", 60.0)
PELVIS_MOVE_MIN_MM = _env_f("D11_PELVIS_MIN", 5.0)
# ---- 肩的传导（力量链"下盘动 → 肩被带"可见）--------------------------------
SHOULDER_MOVE_MIN_MM = _env_f("D11_SHO_MIN", 5.0)
# ---- 末段必须归零并稳住
SETTLE_MAX_DEG = _env_f("D11_SETTLE", 0.05)
SETTLE_STEP_MAX_DEG = _env_f("D11_SETTLE_STEP", 0.02)
# ---- 拳架近似保持防御形状（本支双臂被上身带着走，但**不主动挥**）
FIST_HELD_MAX_MM = _env_f("D11_FIST_MAX", 45.0)
# ---- 站姿类硬要求：脚不许滑动（≤3 mm）
FOOT_SLIDE_MAX_MM = _env_f("D11_SLIDE", 3.0)
STANCE_SOLE_MAX_MM = _env_f("D11_SOLE", 6.0)
# ---- 节奏不对称（升 ≤4 帧、降 ≥18 帧）
HIT_RISE_MAX_FRAMES = _env_f("D11_RISE_MAX", 4.0)
HIT_FALL_MIN_FRAMES = _env_f("D11_FALL_MIN", 18.0)
# ---- 打击停顿（≥3 帧）
HITSTOP_MIN_FRAMES = _env_f("D11_HITSTOP_MIN", 3.0)
# ---- 末帧口径（本支**回原位** ⟹ 世界位置不加整体位移）
HIT_END_MAX_MM = _env_f("D11_END_MAX", 0.5)
HIT_LAST2_MAX_DEG = _env_f("D11_LAST2", 0.5)
HIT_ROLL_MAX_DEG = _env_f("D11_ROLL_MAX", 0.5)
ROLL_RETURN = _env_f("D11_ROLL_RETURN", 1.0) >= 0.5
# ★ D11 教训：滚转修正的权重取 **`always`（全程 1.0）**，不是 D10 的 `tail`。
#   原因（实测三组）：臂 IK 有**绕轴滚转的自由度**，标量已回到 0 的 f25，
#   `forearm.R` 的局部 euler 仍与零位差 21~28°；f26 起走零位短路 ⟹ 接缝处跳变。
#   实测 `max_frame_step_deg`：
#     · `D11_ROLL_RETURN=0`        → 22.50°（`no_teleport` 擦线通过）
#     · `tail`（收到 RECOVER_END）  → 21.27°
#     · `tail`（收到 RECOVER_END−4）→ **28.27° 判红**
#     · `always`                   → **11.73°**（本支采用，余量 2.1×）
#   本支双臂全程只是**被动跟晃**（`fist_dev` 仅 27.5 mm），不存在"要保留自然
#   滚转"的主动挥臂 ⟹ 把滚转锁死在零位滚转上**没有副作用**，只换来接缝干净。
ROLL_WEIGHT_MODE = os.environ.get("D11_ROLL_WEIGHT", "always").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D11_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split(",")
    if item)
ROLL_ITER = max(1, int(os.environ.get("D11_ROLL_ITER", "2")))
END_ROLL_BONES = ARM_ROLL_BONES = ("upperarm.L", "forearm.L", "hand.L",
                                   "upperarm.R", "forearm.R", "hand.R")
# ---- 穿模
CLIP_MAX_MM = _env_f("D11_CLIP_MAX", 0.0)
CLIP_EVERY = int(os.environ.get("D11_CLIP_EVERY", 4))
# ---- 零位守卫
IDLE_MATCH_TOL_DEG = _env_f("D11_IDLE_MATCH", 1.0e-3)
IDLE_GEOM_POS_MAX_MM = _env_f("D11_IDLE_POS", 0.01)
IDLE_GEOM_DIR_MAX_DEG = _env_f("D11_IDLE_DIR", 0.05)

# =============================================================== 驱动标量
#   `press` 是**单调单脉冲**（升 3 / 停 3 / 降 20）⟹ 只能当"节奏时钟"。
#   `thud`  是**真下盘驱动**：命中峰 1.0 → 回弹 −9%（惯性）→ 微抖 → 0。
#   `sway`  是**上身滞后驱动**：撞上时**负**（上身留在原地）→ 峰 +1.0（f8）
#           → **反向回补** → 归零。
THUD_KEYS = ((0, 0.0), (1, 0.30), (2, 0.68), (IMPACT, 1.0), (HOLD_END, 1.0),
             (10, 0.72), (13, 0.30), (REBOUND, -0.090), (DUMP_END, 0.020),
             (SHAKE_END, -0.006), (RECOVER_END, 0.0), (TOTAL, 0.0))
# ★ `sway` 的 0~IMPACT 必须是**负**的：力打在下盘时，上身因惯性**留在原地**，
#   骨盆已经往受力侧走了 ⟹ 相对骨盆，上身是**反方向**的（`sway < 0`）。
#   平台两端都取 −0.15 ⟹ `hitstop` 期间上身也**逐位冻结**（不能破坏停顿）。
SWAY_KEYS = ((0, 0.0), (1, -0.05), (2, -0.12), (IMPACT, -0.15), (HOLD_END, -0.15),
             (UPPER_PEAK, 1.0), (11, 0.58), (14, 0.18), (REBOUND, -0.095),
             (DUMP_END, 0.024), (SHAKE_END, -0.008), (RECOVER_END, 0.0),
             (TOTAL, 0.0))
# ★ 头颈比胸再晚 1 帧、幅度略大（"甩"）。
SWAY_HEAD_KEYS = ((0, 0.0), (1, -0.04), (2, -0.10), (IMPACT, -0.13), (HOLD_END, -0.13),
                  (HEAD_PEAK, 1.0), (12, 0.55), (15, 0.16), (REBOUND, -0.100),
                  (DUMP_END, 0.026), (SHAKE_END, -0.009), (RECOVER_END, 0.0),
                  (TOTAL, 0.0))


def press(frame):
    """节奏标量 ∈ [0, 1]：**升 3 / 峰停 3 / 降 20** 的单脉冲（**单调**）。"""
    keys = [(0, 0.0)]
    for step in range(1, IMPACT):
        keys.append((step, step / float(IMPACT)))
    keys += [(IMPACT, 1.0), (HOLD_END, 1.0), (RECOVER_END, 0.0), (TOTAL, 0.0)]
    return UE.pwl(tuple(keys), float(frame), 0.0)


def thud(frame):
    """★ 下盘主驱动标量：1.0 = 骨盆吃到峰；负 = **反向回弹**（惯性）；末段归零。"""
    return UE.pwl(THUD_KEYS, float(frame), 0.0)


def sway(frame):
    """★ 上身滞后驱动：负 = 上身**留在原地**（相对骨盆反向）；正 = 被带着晃过去。"""
    return UE.pwl(SWAY_KEYS, float(frame), 0.0)


def sway_head(frame):
    """头颈的滞后标量（比胸再晚 1 帧、幅度略大）。"""
    return UE.pwl(SWAY_HEAD_KEYS, float(frame), 0.0)


def still(frame):
    """`press ≡ 0` 且 `thud ≡ 0` 且 `sway ≡ 0` 且 `sway_head ≡ 0` 的帧 ⟹ 走零位短路。"""
    return (abs(press(frame)) <= 1e-12 and abs(thud(frame)) <= 1e-12
            and abs(sway(frame)) <= 1e-12 and abs(sway_head(frame)) <= 1e-12)


# =============================================================== 幅度
# ★★ 幅度标定（同一把尺子，不拍脑袋）：
#   参考 D04 破防：胸世界俯仰 9.8°；D10 腹部受击：胸世界前折 14.8°。
#   本支受力在**下盘**、要"震撼"⟹ 骨盆世界侧倾 9.0°（落在 [5, 14] 带内中段），
#   上身峰值 **6.0°**（小于下盘 ⟹ 读作"被带着晃"，而不是"上身自己在动"）。
PELVIS_TILT_DEG = _env_f("D11_TP_PELVIS", 9.0)
UPPER_TILT_DEG = _env_f("D11_TP_UPPER", 6.0)
HEAD_TILT_GAIN = _env_f("D11_TP_HEADGAIN", 1.10)
# 脊柱链的**空间分布**（把"骨盆倾斜 ↔ 上身倾斜"的差摊到三节上，递减分工）
SPINE_MIX_1 = _env_f("D11_MIX_S1", 0.30)
SPINE_MIX_2 = _env_f("D11_MIX_S2", 0.62)
# 骨盆自身的前后 / 扭转小幅（让"晃"不像机械推拉；保持 <2°）
PELVIS_RX_DEG = _env_f("D11_PELVIS_RX", 1.2)
PELVIS_RY_DEG = _env_f("D11_PELVIS_RY", 1.5)
SPINE_RY_DEG = _env_f("D11_SPINE_RY", 1.0)
# 骨盆位移：**侧移**是"下盘晃动"的主动量；下沉让受力侧膝被动屈曲；后移取小量
HIT_SIDE_MM = _env_f("D11_SIDE", 30.0)      # 沿 +X（受力侧）侧移
HIT_DROP_MM = _env_f("D11_DROP", -9.0)      # 下沉（负 = 往下）
HIT_BACK_MM = _env_f("D11_BACK", 9.0)       # 沿 +Y 后移（前侧向受力的分量）
# 拳随上身漂移（**不主动挥** ⟹ 幅度小、且由 `sway` 驱动）
FIST_LAT_MM = _env_f("D11_FIST_LAT", 20.0)  # 世界横向（同为 +X）
FIST_OUT_MM = _env_f("D11_FIST_OUT", 6.0)   # 额外外张（镜像）
FIST_DOWN_MM = _env_f("D11_FIST_DOWN", 9.0)  # 下沉
# 肘被顶开一点点
_EH_X = _env_f("D11_EB_X", 0.05)
_EH_Y = _env_f("D11_EB_Y", 0.04)
_EH_Z = _env_f("D11_EB_Z", -0.04)

TORSO_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head")
LOWER_BONES = ("pelvis",)
UPPER_BONES = ("spine_01", "spine_02", "chest", "neck", "head")
PARENT_OF = {"pelvis": "root", "spine_01": "pelvis", "spine_02": "spine_01",
             "chest": "spine_02", "neck": "chest", "head": "neck"}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
TARGET_BONES = TORSO_BONES + ("shoulder.L", "shoulder.R")

# =============================================================== 模块级表
ZERO = {}
ZERO_WORLD = {}
ZERO_BASIS = {}
ZERO_DIR = {}
IDLE_FIST = {}
IDLE_ELBOW_DIR = {}
IDLE_WRIST = {}
IDLE_HAND_DIR = {}
IDLE_ANKLE = {}
ANKLE_0 = {}
KNEE_DIR = {}
Z_SEAM = 0.0
IDLE_MATCH = {"src": None, "diff": None, "geom_pos": None, "geom_dir": None,
              "pos_bone": None, "dir_bone": None, "per_bone": {}}
_ZERO_SHORTCUT = [0]


# =============================================================== 姿态装配
def world_tilts(frame):
    """★ 各骨**世界侧倾目标**（度，往受力侧 +X 为正）—— 本支的核心解算。"""
    p = thud(frame)
    u = sway(frame)
    h = sway_head(frame)
    w = {"root": 0.0}
    w["pelvis"] = PELVIS_TILT_DEG * p
    w["chest"] = UPPER_TILT_DEG * u
    w["spine_01"] = w["pelvis"] + SPINE_MIX_1 * (w["chest"] - w["pelvis"])
    w["spine_02"] = w["pelvis"] + SPINE_MIX_2 * (w["chest"] - w["pelvis"])
    w["neck"] = UPPER_TILT_DEG * u
    w["head"] = UPPER_TILT_DEG * HEAD_TILT_GAIN * h
    return w


def torso_pose(frame):
    """★★ 世界侧倾目标 → 局部 `rz`：`rz_self = W_parent − W_self`。

    推导：语义表 `rz > 0` = 向角色**右**（−X）侧倾 ⟹ 正的局部 rz 会**减小**
    世界侧倾。所以自骨的世界侧倾 `W_self = W_parent − rz_self`，
    反解得 `rz_self = W_parent − W_self`。

    `@loc` = 零位骨盆 local + 侧移/后移/下沉（**按 `thud` 缩放** ⟹ 命中峰处最大）。
    ★ 为什么写成 `Z_SEAM + dz − 0.900`：零位站架本身把骨盆压在 830 mm
      （rest 是 900 mm，站架 local Y = −0.070）—— 这个式子把**站架基准**保住，
      只叠加增量（实测 `_d11_zseam_probe.py`：wloc(0,0,Z_SEAM−0.012−0.900)
      ⟹ 世界 −12.0 mm）。
    """
    w = world_tilts(frame)
    p = thud(frame)
    out = {}
    for name in TORSO_BONES:
        rz = w[PARENT_OF[name]] - w[name]
        if name == "pelvis":
            out[name] = (ZERO[name][0] + PELVIS_RX_DEG * p,
                         ZERO[name][1] + PELVIS_RY_DEG * p,
                         ZERO[name][2] + rz)
        elif name in ("spine_01", "spine_02", "chest"):
            ry = SPINE_RY_DEG * sway(frame) * (0.6 if name == "spine_01" else
                                               1.0 if name == "spine_02" else 0.8)
            out[name] = (ZERO[name][0], ZERO[name][1] + ry, ZERO[name][2] + rz)
        else:
            out[name] = (ZERO[name][0], ZERO[name][1], ZERO[name][2] + rz)
    for side in SIDES:
        name = "shoulder." + side
        out[name] = (ZERO[name][0], ZERO[name][1], ZERO[name][2])
    out["@loc"] = {"pelvis": A.wloc(HIT_SIDE_MM * p / 1000.0,
                                    HIT_BACK_MM * p / 1000.0,
                                    Z_SEAM + HIT_DROP_MM * p / 1000.0 - 0.900)}
    return out


def ankle_target(side, frame):
    """腿目标 = **常量**（零位踝）。本支无步态、无位移（方案 A，计划 §1）。"""
    return Vector(ANKLE_0[side])


def fist_target(side, frame):
    """拳世界目标 = `Idle_01@0` 拳位 + 随上身的漂移（**由 `sway` 驱动**，不主动挥）。"""
    u = sway(frame)
    sign = 1.0 if side == "L" else -1.0
    return Vector(IDLE_FIST[side]) + Vector(
        (FIST_LAT_MM + sign * FIST_OUT_MM, 0.0, -FIST_DOWN_MM)) * (u / 1000.0)


def elbow_hit(side, frame):
    """肘偏好方向：Idle 内收 → 受击时微微外张下压（按 `sway` 插值，归一化）。"""
    u = sway(frame)
    if abs(u) <= 1e-9:
        return tuple(IDLE_ELBOW_DIR[side])
    sign = 1.0 if side == "L" else -1.0
    want = Vector(IDLE_ELBOW_DIR[side]) + Vector(
        (sign * _EH_X, _EH_Y, _EH_Z)) * u
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
        if "@loc" in ZERO:
            pose["@loc"] = {k: tuple(v) for k, v in ZERO["@loc"].items()}
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
        # ★ D11 修正：D07 教训 3 的"滚-瞄交替"本支沿用，但**收敛点提前到
        #   `RECOVER_END`**（D10 收到 `TOTAL`）。原因：臂 IK 有**绕轴滚转的自
        #   由度** —— 标量已回到 0 的 f25，`forearm.R` 的 euler 仍与零位差 **22.5°**
        #   （实测：f25 `ry = +13.60` vs 零位 `ry = −8.90`）。若滚转权重到 f38 才到 1，
        #   f26 起走零位短路 ⟹ **f25→f26 单帧跳 29.17°**，`no_teleport`（≤25°）判红。
        #   收到 `RECOVER_END − 4` 帧前**收满 1.0**（最后 4 帧臂滚转逐位对齐零位
        #   ⟹ 零位短路接缝处**构造性零跳变**；实测 `max_frame_step` 由 29.17° 降到 11.73°）。
        span = max(1, RECOVER_END - HOLD_END - 4)
        return min(1.0, max(0.0, (frame - HOLD_END) / float(span)))
    return 1.0 - max(thud(frame), sway(frame))


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


# =============================================================== 测量
def _lat_tilt(direction):
    """世界**侧倾**（正面平面 XZ，度）：+ = 骨末端朝角色**左**（+X = 受力侧）倾。"""
    return math.degrees(math.atan2(direction.x, direction.z))


def _fore_aft(direction):
    """世界**俯仰**（矢状面 YZ，度）：+ = 前屈（同 D10 口径，只用于 `upper_fold` 上界）。"""
    return -math.degrees(math.atan2(direction.y, direction.z))


def _knee_angle(arm, side):
    upper = Vector(A.bone_direction(arm, "thigh." + side)).normalized()
    lower = Vector(A.bone_direction(arm, "shin." + side)).normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, upper.dot(lower)))))


def _body_metrics(arm):
    lo, hi = PD.head_box()
    fists = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    return {
        "box_lo": Vector(lo), "box_hi": Vector(hi),
        "fist": fists,
        "fist_spread_mm": (abs(fists["L"].x) + abs(fists["R"].x)) * 1000.0,
        "pelvis_tilt_deg": _lat_tilt(Vector(A.bone_direction(arm, "pelvis"))),
        "spine1_tilt_deg": _lat_tilt(Vector(A.bone_direction(arm, "spine_01"))),
        "spine2_tilt_deg": _lat_tilt(Vector(A.bone_direction(arm, "spine_02"))),
        "chest_tilt_deg": _lat_tilt(Vector(A.bone_direction(arm, "chest"))),
        "neck_tilt_deg": _lat_tilt(Vector(A.bone_direction(arm, "neck"))),
        "head_tilt_deg": _lat_tilt(Vector(A.bone_direction(arm, "head"))),
        "chest_fold_deg": _fore_aft(Vector(A.bone_direction(arm, "chest"))),
        "pelvis_x": Vector(A.bone_world(arm, "pelvis", "head")).x,
        "pelvis_y": Vector(A.bone_world(arm, "pelvis", "head")).y,
        "pelvis_z": Vector(A.bone_world(arm, "pelvis", "head")).z,
        "chest_x": Vector(A.bone_world(arm, "chest", "tail")).x,
        "head_x": Vector(A.bone_world(arm, "head", "tail")).x,
        "shoulder_x": {
            s: Vector(A.bone_world(arm, "upperarm." + s, "head")).x
            for s in SIDES},
        "hip_z": {s: Vector(A.bone_world(arm, "thigh." + s, "head")).z
                  for s in SIDES},
        "knee_deg": {s: _knee_angle(arm, s) for s in SIDES},
    }


def hit_assertions(arm, action, samples, meshes):
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 零位真值 + 逐帧扫描
    # ★★★ D07 教训 2：量零位前**摘掉 action**，否则 depsgraph 会按场景帧覆盖手写 pose。
    arm.animation_data.action = None
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _body_metrics(arm)
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    per = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _body_metrics(arm)

    pt = {f: per[f]["pelvis_tilt_deg"] - zero["pelvis_tilt_deg"] for f in per}
    ct = {f: per[f]["chest_tilt_deg"] - zero["chest_tilt_deg"] for f in per}
    ht = {f: per[f]["head_tilt_deg"] - zero["head_tilt_deg"] for f in per}
    nt = {f: per[f]["neck_tilt_deg"] - zero["neck_tilt_deg"] for f in per}
    st1 = {f: per[f]["spine1_tilt_deg"] - zero["spine1_tilt_deg"] for f in per}
    st2 = {f: per[f]["spine2_tilt_deg"] - zero["spine2_tilt_deg"] for f in per}
    cfold = {f: per[f]["chest_fold_deg"] - zero["chest_fold_deg"] for f in per}
    kd = {s: {f: per[f]["knee_deg"][s] - zero["knee_deg"][s] for f in per}
          for s in SIDES}

    # ---- ★★ (a) `pelvis_tilt`：**往受力侧（+X）为正**，两个界都取正
    res["pelvis_tilt_zero_deg"] = round(zero["pelvis_tilt_deg"], 4)
    res["pelvis_tilt_impact_deg"] = round(pt[IMPACT], 4)
    res["pelvis_tilt_peak_deg"] = round(max(pt.values()), 4)
    res["pelvis_tilt_peak_at"] = max(pt, key=lambda f: pt[f])
    res["pelvis_tilt_rebound_deg"] = round(min(pt.values()), 4)
    res["pelvis_tilt_rebound_at"] = min(pt, key=lambda f: pt[f])
    res["pelvis_tilt_at_impact_ok"] = bool(
        PELVIS_TILT_MIN_DEG <= pt[IMPACT] <= PELVIS_TILT_MAX_DEG)
    res["pelvis_tilt_delta_ok"] = bool(
        PELVIS_TILT_MIN_DEG <= max(pt.values()) <= PELVIS_TILT_MAX_DEG
        and PELVIS_REB_MIN_DEG <= min(pt.values()) <= PELVIS_REB_MAX_DEG)
    # ★★ 方向守卫：把 Δ 取反（= 往支撑侧倾）后必须**越界**。写成 abs() 则立刻红。
    res["pelvis_tilt_direction_can_fail_ok"] = bool(
        not (PELVIS_TILT_MIN_DEG <= -pt[IMPACT] <= PELVIS_TILT_MAX_DEG))

    # ---- ★★ (b) 髋（骨盆）位移：侧移是主动量，后移/下沉是配合
    res["pelvis_side_mm"] = round(
        (per[IMPACT]["pelvis_x"] - zero["pelvis_x"]) * 1000.0, 3)
    res["pelvis_back_mm"] = round(
        (per[IMPACT]["pelvis_y"] - zero["pelvis_y"]) * 1000.0, 3)
    res["pelvis_drop_mm"] = round(
        (zero["pelvis_z"] - per[IMPACT]["pelvis_z"]) * 1000.0, 3)
    res["pelvis_move_mm"] = round(
        math.hypot(per[IMPACT]["pelvis_y"] - zero["pelvis_y"],
                   per[IMPACT]["pelvis_z"] - zero["pelvis_z"]) * 1000.0, 3)
    res["pelvis_side_ok"] = bool(
        PELVIS_SIDE_MIN_MM <= abs(res["pelvis_side_mm"]) <= PELVIS_SIDE_MAX_MM)
    res["pelvis_side_direction_can_fail_ok"] = bool(
        not (PELVIS_SIDE_MIN_MM <= -res["pelvis_side_mm"] <= PELVIS_SIDE_MAX_MM))
    res["pelvis_move_ok"] = bool(res["pelvis_move_mm"] >= PELVIS_MOVE_MIN_MM)

    # ---- ★★★ (c) `lower_body_leads_ok` —— **本支主设计**（D10 `head_lag_ok` 的镜像）
    pelvis_peak_frame = max(pt, key=lambda f: pt[f])
    chest_peak_frame = max(ct, key=lambda f: ct[f])
    head_peak_frame = max(ht, key=lambda f: ht[f])
    lead_chest = chest_peak_frame - pelvis_peak_frame
    lead_head = head_peak_frame - pelvis_peak_frame
    pt_peak = max(pt.values())
    ct_peak = max(ct.values())
    lower_progress = (pt[IMPACT] / pt_peak) if abs(pt_peak) > 1e-9 else None
    upper_progress = (abs(ct[IMPACT]) / abs(ct_peak)) if abs(ct_peak) > 1e-9 else None
    res["pelvis_peak_frame"] = pelvis_peak_frame
    res["chest_peak_frame"] = chest_peak_frame
    res["head_peak_frame"] = head_peak_frame
    res["chest_lag_frames"] = lead_chest
    res["head_lag_frames"] = lead_head
    res["lower_progress_at_impact"] = (None if lower_progress is None
                                       else round(lower_progress, 4))
    res["upper_progress_at_impact"] = (None if upper_progress is None
                                       else round(upper_progress, 4))
    res["lower_body_leads_ok"] = bool(
        lead_chest >= LEAD_MIN_FRAMES and lead_head >= LEAD_MIN_FRAMES
        and lower_progress is not None and lower_progress >= LOWER_PROGRESS_MIN
        and upper_progress is not None and upper_progress <= UPPER_PROGRESS_MAX)
    # ★ 反向守卫：若"滞后"为 0（上身跟着骨盆同时动）本判据必须**变红**。
    res["lower_body_leads_can_fail_ok"] = bool(not (0.0 >= LEAD_MIN_FRAMES))

    # ---- ★★ (d) 膝**不对称**（"被扫腿"与"自己下蹲"的分界）
    knee_hit = kd[HIT_SIDE][IMPACT]
    knee_sup = kd[SUPPORT_SIDE][IMPACT]
    knee_hit_max = max(kd[HIT_SIDE].values())
    knee_sup_max = max(kd[SUPPORT_SIDE].values())
    res["knee_delta_deg"] = {HIT_SIDE: round(knee_hit, 4),
                             SUPPORT_SIDE: round(knee_sup, 4)}
    res["knee_delta_peak_deg"] = {HIT_SIDE: round(knee_hit_max, 4),
                                  SUPPORT_SIDE: round(knee_sup_max, 4)}
    res["knee_asym_deg"] = round(knee_hit - knee_sup, 4)
    res["hip_z_mm"] = {s: round((zero["hip_z"][s] - per[IMPACT]["hip_z"][s])
                                * 1000.0, 3) for s in SIDES}
    res["knee_asym_ok"] = bool(
        knee_hit - knee_sup >= KNEE_ASYM_MIN_DEG
        and abs(knee_hit) <= KNEE_MAX_DEG and abs(knee_sup) <= KNEE_MAX_DEG
        and abs(knee_hit) > thud_waist_min())
    res["knee_asym_can_fail_ok"] = bool(not (0.0 >= KNEE_ASYM_MIN_DEG))

    # ---- ★★ (e) 上身**只跟着晃**、不得独立大幅主动
    res["upper_fold_peak_deg"] = round(max(abs(v) for v in cfold.values()), 4)
    res["upper_tilt_peak_deg"] = round(ct_peak, 4)
    res["upper_tilt_ratio"] = (None if abs(pt_peak) < 1e-9
                               else round(abs(ct_peak) / abs(pt_peak), 4))
    res["upper_follow_only_ok"] = bool(
        res["upper_fold_peak_deg"] <= UPPER_FOLD_MAX_DEG
        and res["upper_tilt_ratio"] is not None
        and res["upper_tilt_ratio"] <= UPPER_TILT_RATIO_MAX)
    # ★ 反向守卫：若上身**领跑**（幅度大于下身）本判据必须**变红**。
    res["upper_follow_only_can_fail_ok"] = bool(not (abs(ct_peak) > abs(pt_peak)))

    # ---- ★★ (f) 反向过冲（惯性）：8~12% 峰值，且**必须小于峰值**
    peak, rebound = max(pt.values()), min(pt.values())
    over_ratio = (abs(rebound) / peak) if abs(peak) > 1e-9 else None
    res["overshoot_ratio"] = None if over_ratio is None else round(over_ratio, 4)
    res["overshoot_ok"] = bool(
        over_ratio is not None
        and OVERSHOOT_MIN <= over_ratio <= OVERSHOOT_MAX
        and rebound < 0.0 < peak
        and abs(rebound) < peak)

    # ---- ★★ (g) 末段：微抖后归零并稳住
    tail_frames = list(range(RECOVER_END, TOTAL + 1))
    res["settle_max_deg"] = round(max(abs(pt[f]) for f in tail_frames), 5)
    last_steps = [abs(pt[f] - pt[f - 1]) for f in range(TOTAL - 2, TOTAL + 1)]
    res["settle_step_deg"] = round(max(last_steps), 5)
    res["shake_tail_deg"] = [round(pt[f], 4)
                             for f in (REBOUND, DUMP_END, SHAKE_END, RECOVER_END)]
    res["settle_ok"] = bool(
        res["settle_max_deg"] <= SETTLE_MAX_DEG
        and res["settle_step_deg"] <= SETTLE_STEP_MAX_DEG
        and abs(pt[REBOUND]) > 0.5)

    # ---- ★★ (h) 拳架近似保持 / 肩的传导可见（力量链：下盘动 → 肩被带）
    fist_dev, fist_dev_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["fist"][s] - IDLE_FIST[s]).length * 1000.0
            if gap > fist_dev:
                fist_dev, fist_dev_at = gap, (s, frame)
    res["fist_dev_mm"] = round(fist_dev, 3)
    res["fist_dev_at"] = fist_dev_at
    res["fist_held_ok"] = bool(fist_dev <= FIST_HELD_MAX_MM)
    shoulder_move, shoulder_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = abs(per[frame]["shoulder_x"][s] - zero["shoulder_x"][s]) * 1000.0
            if gap > shoulder_move:
                shoulder_move, shoulder_at = gap, (s, frame)
    res["shoulder_move_mm"] = round(shoulder_move, 3)
    res["shoulder_move_at"] = shoulder_at
    res["shoulder_moves_ok"] = bool(shoulder_move >= SHOULDER_MOVE_MIN_MM)

    # ---- (i) 节奏不对称（升 ≤4 / 降 ≥18，量的是 `press` 单脉冲）
    risers = sum(1 for f in range(TOTAL) if press(f + 1) > press(f) + 1e-9)
    fallers = sum(1 for f in range(TOTAL) if press(f + 1) < press(f) - 1e-9)
    res["press_rise_frames"] = risers
    res["press_fall_frames"] = fallers
    res["hit_speed_ok"] = bool(risers <= HIT_RISE_MAX_FRAMES
                               and fallers >= HIT_FALL_MIN_FRAMES)
    res["press_at_f1"] = round(press(1), 4)
    res["thud_at_impact"] = round(thud(IMPACT), 4)
    res["sway_at_impact"] = round(sway(IMPACT), 4)

    # ---- (j) 打击停顿（≥3 帧，姿态逐位冻结）
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

    # ---- (k) 站姿硬要求：脚不许滑动（默认 foot_probe 口径）
    slide = {s: round(res.get("foot_travel_mm_toe." + s, 0.0), 2) for s in SIDES}
    res["foot_slide_mm"] = slide
    res["no_foot_slide_ok"] = bool(all(v <= FOOT_SLIDE_MAX_MM
                                      for v in slide.values()))

    # ---- (l) 末帧口径：本支**回原位** ⟹ 世界位置直接与零位比（不加整体位移）
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
                                   and abs(thud(IMPACT)) > 1e-12
                                   and abs(sway(IMPACT)) > 1e-12)
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
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()
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
    res["hit_leg_recover_ok"] = bool(
        end_world <= HIT_END_MAX_MM and last2 <= HIT_LAST2_MAX_DEG
        and worst_roll <= HIT_ROLL_MAX_DEG)
    res["hit_leg_ok"] = bool(res["pelvis_tilt_at_impact_ok"]
                             and res["lower_body_leads_ok"])

    # ---- 穿模（"折断了"的硬上界）
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [IMPACT, HOLD_END, UPPER_PEAK, REBOUND, CANCEL, TOTAL]))
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

    # ---- 力量传导链（脚→腿→髋→腰→肩→手，每段都要有量）
    res["chain_travel"] = {
        "foot_mm": max(res["foot_slide_mm"].values()),
        "knee_deg": round(knee_hit, 4),
        "hip_mm": res["pelvis_side_mm"],
        "waist_deg": round(abs(pt[IMPACT]), 4),
        "shoulder_mm": round(res["shoulder_move_mm"], 2),
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
    res["pelvis_side_px"] = round(res["pelvis_side_mm"] * 0.556, 2)
    res["zero_fist_mm"] = {s: [round(v * 1000.0, 1) for v in IDLE_FIST[s]]
                           for s in SIDES}
    res["impact_fist_mm"] = {s: [round(v * 1000.0, 1)
                                 for v in per[IMPACT]["fist"][s]]
                             for s in SIDES}

    # ---- 剪影 / aspect：只报不判
    sil = P.silhouette(arm, "d11")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    if os.environ.get("D11_TRACE"):
        res["trace"] = {str(f): {
            "press": round(press(f), 4),
            "thud": round(thud(f), 4),
            "sway": round(sway(f), 4),
            "sway_head": round(sway_head(f), 4),
            "pelvis_tilt": round(pt[f], 3),
            "chest_tilt": round(ct[f], 3),
            "head_tilt": round(ht[f], 3),
            "neck_tilt": round(nt[f], 3),
            "spine1_tilt": round(st1[f], 3),
            "spine2_tilt": round(st2[f], 3),
            "chest_fold": round(cfold[f], 3),
            "kneeL": round(kd["L"][f], 3),
            "kneeR": round(kd["R"][f], 3),
            "hip_zL": round((zero["hip_z"]["L"] - per[f]["hip_z"]["L"]) * 1000.0, 2),
            "hip_zR": round((zero["hip_z"]["R"] - per[f]["hip_z"]["R"]) * 1000.0, 2),
            "pelvis_side": round((per[f]["pelvis_x"] - zero["pelvis_x"]) * 1000.0, 2),
            "pelvis_back": round((per[f]["pelvis_y"] - zero["pelvis_y"]) * 1000.0, 2),
            "pelvis_drop": round((zero["pelvis_z"] - per[f]["pelvis_z"]) * 1000.0, 2),
            "lowL": round(samples[f]["low"]["L"] * 1000.0, 2),
            "lowR": round(samples[f]["low"]["R"] * 1000.0, 2),
            "arm_euler": {n: [round(v, 2) for v in
                              samples[f]["euler"].get(n, (0.0, 0.0, 0.0))]
                          for n in ("upperarm.R", "forearm.R", "hand.R")},
        } for f in range(0, TOTAL + 1)}
    return res


def thud_waist_min():
    """`knee_asym_ok` 的伴随条件：腰（骨盆侧倾）必须比膝屈大 —— "晃"不是"蹲"。"""
    return PELVIS_TILT_MIN_DEG * 0.5


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
    global ZERO, ZERO_WORLD, Z_SEAM, KNEE_DIR, ANKLE_0, IDLE_ANKLE
    ZERO, ZERO_WORLD = {}, {}
    ZERO_BASIS.clear()
    ZERO_DIR.clear()
    IDLE_FIST.clear()
    IDLE_ELBOW_DIR.clear()
    IDLE_WRIST.clear()
    IDLE_HAND_DIR.clear()
    ANKLE_0.clear()
    IDLE_ANKLE.clear()
    KNEE_DIR.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("D11_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}

    UE.ROLL_STEP_DEG = _env_f("D11_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D11_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D11_YWEIGHT", 0.0)

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
    A.report("D11_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "impact": IMPACT, "hold_end": HOLD_END, "hit_hold": HIT_HOLD,
        "upper_peak": UPPER_PEAK, "head_peak": HEAD_PEAK, "rebound": REBOUND,
        "dump_end": DUMP_END, "shake_end": SHAKE_END,
        "recover_end": RECOVER_END, "cancel": CANCEL,
        "segments": 3, "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "force_direction": ("腿部（下盘，侧向）：力把下盘往 +X（角色左 = 受力侧）推，"
                            "受力侧取 %s" % HIT_SIDE),
        "leg_plan": "方案 A：踝目标 = 零位常量，脚全程钉住，受力侧膝被动屈曲",
        "zero_source": "Idle_01@%d（落盘 action，非重演）" % saved_info.get(
            "frame"),
        "zero_pose_src": saved_info,
        "zero_vs_idle_pose_euler_max_diff_deg": round(euler_diff, 6),
        "zero_vs_idle_pose_worst_bone": euler_bone,
        "zero_vs_idle_pose_geom_pos_mm": round(geom_pos, 6),
        "zero_vs_idle_pose_geom_dir_deg": round(geom_dir, 6),
        "zero_pelvis_z_mm": round(Z_SEAM * 1000.0, 3),
        "zero_pelvis_tilt_deg": round(zrow["pelvis_tilt_deg"], 4),
        "zero_fist_mm": {s: [round(v * 1000.0, 2) for v in IDLE_FIST[s]]
                         for s in SIDES},
        "zero_fist_spread_mm": round(zrow["fist_spread_mm"], 2),
        "zero_ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                          for s in SIDES},
        "zero_knee_deg": {s: round(zrow["knee_deg"][s], 3) for s in SIDES},
        "zero_hip_z_mm": {s: round(zrow["hip_z"][s] * 1000.0, 2) for s in SIDES},
        "pelvis_tilt_deg": PELVIS_TILT_DEG,
        "upper_tilt_deg": UPPER_TILT_DEG,
        "spine_mix": [SPINE_MIX_1, SPINE_MIX_2],
        "pelvis_rx_deg": PELVIS_RX_DEG, "pelvis_ry_deg": PELVIS_RY_DEG,
        "hip_shift_mm": {"side": HIT_SIDE_MM, "drop": HIT_DROP_MM,
                         "back": HIT_BACK_MM},
        "fist_shift_mm": {"lat": FIST_LAT_MM, "out": FIST_OUT_MM,
                          "down": FIST_DOWN_MM},
        "thud_keys": [list(k) for k in THUD_KEYS],
        "sway_keys": [list(k) for k in SWAY_KEYS],
        "sway_head_keys": [list(k) for k in SWAY_HEAD_KEYS],
        "pelvis_tilt_gate_deg": [PELVIS_TILT_MIN_DEG, PELVIS_TILT_MAX_DEG],
        "pelvis_rebound_gate_deg": [PELVIS_REB_MIN_DEG, PELVIS_REB_MAX_DEG],
        "overshoot_gate": [OVERSHOOT_MIN, OVERSHOOT_MAX],
        "lead_gate_frames": LEAD_MIN_FRAMES,
        "progress_gate": [LOWER_PROGRESS_MIN, UPPER_PROGRESS_MAX],
        "knee_asym_gate_deg": KNEE_ASYM_MIN_DEG,
        "pelvis_side_gate_mm": [PELVIS_SIDE_MIN_MM, PELVIS_SIDE_MAX_MM],
        "note": ("D11 腿部受击：零位 = Idle_01 落盘帧 0；升 3 / 硬直 3 / 降 20；"
                 "★ **下盘先动** —— 骨盆侧移+侧倾（往受力侧）主承载，"
                 "受力侧膝被动屈曲（不对称），上身由 sway **滞后**带动"
                 "（命中帧反向、峰值晚于骨盆 ≥2 帧、回落反向回补）；"
                 "脚全程钉住（方案 A）；末帧**逐位回零位**"),
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
        "note": ("腿部受击：下盘先动（骨盆侧移+侧倾往受力侧、受力侧膝被动屈曲），"
                 "上身由 sway 滞后带动（命中帧反向、峰值晚于骨盆 ≥2 帧、"
                 "回落反向回补）；脚全程钉住；末帧逐位回零位（含位置）"),
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
                           "UPPER_PEAK": UPPER_PEAK, "HEAD_PEAK": HEAD_PEAK,
                           "REBOUND": REBOUND, "RECOVER": RECOVER_END,
                           "CANCEL": CANCEL, "END": TOTAL})
    A.set_hitstop(action, IMPACT, HOLD_END)

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # ★ 本支脚全程钉住 ⟹ `foot_probe` **回归默认**（计划 §1），另加 `no_foot_slide_ok`。
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
    A.report("D11_REPORT", report)

    if not SKIP_RENDER:
        # ★ 计划 §4：f0 / 命中 / 停顿中 / 头峰 / 过冲峰 / 回落 / CANCEL / 末帧
        frames = [0, IMPACT, 5, HOLD_END, UPPER_PEAK, 12, REBOUND, DUMP_END,
                  CANCEL, TOTAL]
        A.render_pose_sheet(arm, action, frames, "hitleg",
                            views=(A.VIEW_FRONT, A.VIEW_SIDE, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D11_DONE failed=%s" % report["failed"])
    print("D11_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D11_FAILURE " + traceback.format_exc())
