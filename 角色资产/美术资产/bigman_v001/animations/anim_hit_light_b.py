"""anim_hit_light_b —— D06 `Hit_Light_B` 背面轻受击。

设计（对着清单 §四 D06 的原文「幅度小，快速恢复」逐条落）：

    ★★ 本支是 **D05 的镜像支**，但"镜像"只发生在**受力方向**。
       头号风险**不是幅度，是符号** —— 符号一错就会做出"正面受击"
       （见清单「下一支详细制作计划 —— D06」§1/§2）。

    段结构     **单脉冲 + 快速恢复，无硬直平台**、**0 命中点**、**0 位移**。
    时长       24 帧 = **0.400 s** @60fps（与 D05 同）
    零位       ★★ **= `Idle_01@0` 的落盘 action 帧 0**（与 D05 同源，`_load_idle_zero()`）。
    首尾       首帧 == `Idle_01@0`；末帧 == 同一份零位（受击结束回战斗待机）。
    节奏       升 3 帧 / 峰停 2 帧 / 降 19 帧（`press` 单脉冲，与 D05 同）。
    姿态       ★★ 与 D05 **逐条反号**：
               头/胸**小幅前折**（chest 世界俯仰 **Δ ∈ [−5.0, −1.5]**，D05 是 +2.30°）
               + 头颈**前甩** 15~60 mm（`head_fwd_mm`，D05 是 `head_back_mm`）
               + 骨盆被往**前**推（`HIT_BACK_MM` 取负）
               + **拳往前/外被带走、不应后收**（`HIT_BACKF_MM` 取负 ——
                 后收会读成"被正面打"，方向读反）
               + 双臂仍保持防御形状 + 脚纹丝不动、膝几乎不弯（≤2°）。
    受力链     ★ 背后来力是 **头/肩先往前甩**（颈被推着走），**不是骨盆先走**：
               D05 是"被甩"，D06 是"被推" ⟹ 头/颈/肩用 `lead_scale()`
               （比躯干**更早到位**，`LEAD_GAMMA < 1`），躯干其余骨仍用 `press`。

★★ 本支门禁的**头号重点**：`hit_light_pitch_ok` 的**两个界都取负**
   （`−5.0 ≤ Δ ≤ −1.5`）—— **绝对不要用 `abs()`**。
   `abs()` 会让"方向做反了"（正面受击）也判绿。另立
   `hit_light_direction_can_fail_ok`：把 Δ 取反后必须**失败**，
   即"这条判据能抓住方向做反"由数据当场证明（SOUL：判据必须能失败）。

三条 D05 修正**必须一并继承**（缺任何一条，末帧就回不到 `Idle_01@0`）：
    1. `arm_seat_tip()`（腕驱动两骨 IK + 手骨单独瞄）—— 否则腕位差 ~30 mm。
    2. `elbow_hit()`：`p <= 1e-9 → return 零位肘向`，且偏移**乘 `p`**。
    3. `KNEE_DIR[side]` **逐侧**（不要共用一根）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_hit_light_b.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D06_TRACE=1    逐帧打印 press / 前折 / 头前甩 / 拳位移（调参用）
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

NAME = "Hit_Light_B"
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
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（D02~D05 的 `_f32` 同源）。

    零位 `ZERO` 是 float64，`sample_animation` 读回的是 float32 ⟹ 直接比会假红。
    两边都过 float32，"逐位相同" 才是真的逐位相同（差值 = 0.0）。
    """
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


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


# =============================================================== 时间轴
TOTAL = _env_i("D06_TOTAL", 24)          # 0.400 s @60fps（计划 0.35~0.5 s）
IMPACT = _env_i("D06_IMPACT", 3)         # 峰值帧（上升沿 3 帧 —— 计划"升 2~3 帧"）
HIT_HOLD = _env_i("D06_HOLD", 2)         # 峰值微停顿帧数（f3..f5 逐位冻结）
HOLD_END = IMPACT + HIT_HOLD             # 5
RECOVER_END = _env_i("D06_RECOVER", TOTAL)   # 回零帧（下降段 f6..f24 = 19 帧 ≥18）
CANCEL = _env_i("D06_CANCEL", 18)

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
PLANT_MAX_MM = _env_f("D06_PLANT", 1.0)      # 与 D03/D04/D05 同：站姿零位移
SLIDE_MAX_MM = _env_f("D06_SLIDE", 1.0)
GROUND_MIN_MM, GROUND_MAX_MM = -2.0, 6.0
REACH_MAX_RATIO = 0.995
# ★ 膝几乎不弯（计划 §1："膝几乎不弯 ≤2°"）—— 与 D05 同。
KNEE_DELTA_MAX_DEG = _env_f("D06_KNEE", 2.0)

# ---- ★★ 本支头号判据 `hit_light_ok`：**两个界都取负**（计划 §2）-----------------
# ★ 世界俯仰 `pitch = atan2(chest_dir.y, chest_dir.z)`，+Y = 身后 ⟹ **后仰为正**。
#   D06 是**前折** ⟹ Δ 必须为**负**。两界都取负，**不许用 abs()**
#   （abs() 会让"方向做反了"也判绿）。
HIT_PITCH_MIN_DEG = _env_f("D06_PITCH_MIN", -5.0)
HIT_PITCH_MAX_DEG = _env_f("D06_PITCH_MAX", -1.5)
# ★ 头部口径：`head_fwd_mm = (zero.head_y − per[IMPACT].head_y) × 1000`（正 = 头往前）。
#   头在侧视图里对应"重心**左**移"（D05 是右移）。
HIT_HEAD_FWD_MIN_MM = _env_f("D06_HEAD_MIN", 15.0)
HIT_HEAD_FWD_MAX_MM = _env_f("D06_HEAD_MAX", 60.0)

# ---- 节奏不对称（升 ≤3 帧、降 ≥18 帧）
HIT_RISE_MAX_FRAMES = _env_f("D06_RISE_MAX", 3.0)
HIT_FALL_MIN_FRAMES = _env_f("D06_FALL_MIN", 18.0)
# ★ 上升沿逐帧等量（D04 教训：PCHIP 在单段上首点斜率 > 弦斜率，位移全砸第 1 帧）。
RISE_EVEN = _env_f("D06_RISE_EVEN", 1.0) >= 0.5
RISE_GAMMA = _env_f("D06_RISE_GAMMA", 1.0)
# ★★ 头/颈/肩的**领跑指数**（计划 §2：「头颈的上升沿要比 D05 更快」）：
#   `lead = press ** LEAD_GAMMA`，`LEAD_GAMMA < 1` ⟹ 0<p<1 时 lead > p ⟹ 头颈先到位。
#   p ∈ {0, 1} 时 lead ≡ p（首尾逐位不变），故**不影响任何幅度门禁**，只改轨迹形状。
LEAD_GAMMA = _env_f("D06_LEAD_GAMMA", 0.75)
LEAD_BONES = ("neck", "head", "shoulder.L", "shoulder.R")

# ---- 打击停顿（§0.6 通用门禁 `hitstop_present`）
HITSTOP_MIN_FRAMES = _env_f("D06_HITSTOP_MIN", 2.0)

# ---- 末帧回到零位（四口径，与 D03/D04/D05 同源）
HIT_END_MAX_MM = _env_f("D06_END_MAX", 0.5)
HIT_LAST2_MAX_DEG = _env_f("D06_LAST2", 0.5)
# ★ 第四口径：末帧**绕骨轴滚转**漂移上限（位置口径发现不了的量，D04 立）
HIT_ROLL_MAX_DEG = _env_f("D06_ROLL_MAX", 0.5)
# ★ 滚转回位修正开关 + 权重时间形状（见 `_roll_return()`）。
#   ★★ **本支默认打开**（与 D05 相反）：D05 那支臂摆幅小、该修正是**可证明的空操作**，
#   故默认关；本支实测 `end_roll_deg` = **2.0003°**（> 0.5° 判据，红）—— 这正是
#   D05「遗留问题」里写的那条触发条件：「幅度做大 / end_roll_ok 变红 → 打开开关」。
#   打开后 `end_roll_deg = 0.0`（见 `_d06_sw*.log` 扫描）。**限值一个没动。**
ROLL_RETURN = _env_f("D06_ROLL_RETURN", 1.0) >= 0.5
ROLL_WEIGHT_MODE = os.environ.get("D06_ROLL_WEIGHT", "tail").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D06_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split(",")
    if item)

# ---- 穿模
CLIP_MAX_MM = _env_f("D06_CLIP_MAX", 0.0)
CLIP_EVERY = int(os.environ.get("D06_CLIP_EVERY", 4))

# ---- 零位守卫：落盘 action@0 与 `I1.idle_pose(arm, 0.0)` 必须同解（绝对零位）
IDLE_MATCH_TOL_DEG = _env_f("D06_IDLE_MATCH", 1.0e-3)
IDLE_GEOM_POS_MAX_MM = _env_f("D06_IDLE_POS", 0.01)
IDLE_GEOM_DIR_MAX_DEG = _env_f("D06_IDLE_DIR", 0.05)

# =============================================================== 受击幅度
# ★★ 全部**先量再定**（计划 §3：「先扫再定」）。所有量都是"相对 `Idle_01@0`"。
#   ★ 符号规则（本支最容易翻车处，逐条对着计划 §1 表）：
#     - 骨盆沿 +Y 是"身后" ⟹ 被从背后推 ⟹ **HIT_BACK_MM 取负（往 −Y = 前）**。
#     - 拳沿 +Y 是"后收" ⟹ 背后来力时拳被往**前/外**带走 ⟹ **HIT_BACKF_MM 取负**。
#     - 骨盆下沉 / 侧移 / 拳外张 / 拳下沉：侧向量，符号不随受力方向翻转。
#   ★ `HIT_BACK_MM` 的**幅值**沿用 D05 的 6 mm（干净的镜像）；但 `HIT_DROP_MM` 从
#     D05 的 −4.0 收到 **−2.0** —— 原因不是"放宽"，是**腿的几何不对称**：
#     骨盆**前**移压的是前腿（L，踝 y = −0.170），压得比 D05 的**后**移多。
#     扫描（`_d06_sw*`）：BACK −6 / DROP −4 ⟹ 膝弯 L **2.07°**（> 2.0 判据，红）；
#     DROP −2 ⟹ **1.32°**（绿，留 0.68° 余量）。见 `_d06_sweep_knee.sh`。
HIT_DROP_MM = _env_f("D06_DROP", -2.0)     # 骨盆下沉（腿 IK 吸收 ⟹ 脚不动）
HIT_BACK_MM = _env_f("D06_BACK", -6.0)     # ★ 骨盆沿 **−Y 前移**（被从背后推）
HIT_SIDE_MM = _env_f("D06_SIDE", 3.0)      # 骨盆沿 +X 侧移（前视可见的轻微侧移）
HIT_OUT_MM = _env_f("D06_OUT", 9.0)        # 每侧拳**横向外张**
HIT_BACKF_MM = _env_f("D06_BACKF", -16.0)  # ★ 拳沿 **−Y 前送**（不是后收！）
HIT_DOWN_MM = _env_f("D06_DOWN", 4.0)      # 拳下沉
# 躯干**前折**链：★ `chest` 世界俯仰 = **pelvis..chest 的 rx 之和**（D04/D05 实测线性）。
#   D05 那一组是负值（后仰，得 +2.30°）；本支**整体翻正号**（前折，得 −2.30°）。
#   pelvis+spine_01+spine_02+chest = 0.35+0.45+0.55+0.95 = 2.30 ⟹ 俯仰 −2.30°。
TORSO_HIT = {"pelvis": _env_f("D06_TP_PELVIS", 0.35),
             "spine_01": _env_f("D06_TP_S1", 0.45),
             "spine_02": _env_f("D06_TP_S2", 0.55),
             "chest": _env_f("D06_TP_CHEST", 0.95),
             "neck": _env_f("D06_TP_NECK", 1.30),
             "head": _env_f("D06_TP_HEAD", 2.10),
             "shoulder.L": _env_f("D06_TP_SH", 1.40),
             "shoulder.R": _env_f("D06_TP_SH", 1.40)}
# 躯干**轻微偏转**（ry，度）：侧向量，符号沿用 D05（只报不判，不影响俯仰口径）。
TORSO_YAW = {"pelvis": _env_f("D06_YAW_PELVIS", 0.30),
             "spine_01": _env_f("D06_YAW_S1", 0.35),
             "spine_02": _env_f("D06_YAW_S2", 0.35),
             "chest": _env_f("D06_YAW_CHEST", 0.45),
             "neck": _env_f("D06_YAW_NECK", 0.40),
             "head": _env_f("D06_YAW_HEAD", 0.55)}
# 肘被顶开一点点：由 Idle 的"内收护胸"微微转向"外张下压"。幅度远小于 D04。
_EH_X = _env_f("D06_EB_X", 0.06)
_EH_Y = _env_f("D06_EB_Y", 0.05)
_EH_Z = _env_f("D06_EB_Z", -0.04)

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")

# =============================================================== 模块级表
ZERO = {}                 # `Idle_01@0` 定格真值（本支零位）
ZERO_WORLD = {}
ZERO_BASIS = {}           # 零位的世界旋转基（盯"绕骨轴滚转"）
ZERO_DIR = {}
IDLE_FIST = {}
IDLE_ELBOW_DIR = {}
IDLE_WRIST = {}
IDLE_HAND_DIR = {}
ANKLE_0 = {}
KNEE_DIR = {}   # ★ 逐侧（L/R 的零位膝鼓出方向**不同**，不可共用一根常量）
Z_SEAM = 0.0
IDLE_MATCH = {"src": None, "diff": None, "geom_pos": None, "geom_dir": None,
              "pos_bone": None, "dir_bone": None, "per_bone": {}}


def press(frame):
    """受击标量 ∈ [0, 1]：**升 3 / 峰停 2 / 降 19** 的单脉冲（无平台）。

    峰值帧（press ≡ 1）由**同一组参数**解出 ⟹ 姿态逐位相同（停顿是真的"僵住"）。
    """
    keys = [(0, 0.0)]
    if RISE_EVEN:
        for step in range(1, IMPACT):
            keys.append((step, (step / float(IMPACT)) ** RISE_GAMMA))
    keys += [(IMPACT, 1.0), (HOLD_END, 1.0), (RECOVER_END, 0.0), (TOTAL, 0.0)]
    return UE.pwl(tuple(keys), float(frame), 0.0)


def lead_scale(frame):
    """★ 头/颈/肩的驱动标量 —— 比躯干**更早到位**（背后来力时头颈先被推着走）。

    `LEAD_GAMMA < 1` ⟹ `press ** LEAD_GAMMA >= press`（0 ≤ press ≤ 1）
    ⟹ 上升沿被**前加载**（头先走、骨盆后跟）。p ∈ {0, 1} 时恒等于 `press`，
    所以**首尾帧与所有峰值帧逐位不变**，本函数只改"位移怎么分布到帧上"。
    """
    p = press(frame)
    if LEAD_GAMMA >= 1.0:
        return p
    return p ** LEAD_GAMMA


def fist_target(side, frame):
    """拳世界目标 = `Idle_01@0` 定格 + 受击偏移（镜像）。**绝对世界点**（同 D02~D05 口径）。"""
    p = press(frame)
    sign = 1.0 if side == "L" else -1.0
    return Vector(IDLE_FIST[side]) + Vector(
        (sign * HIT_OUT_MM, HIT_BACKF_MM, -HIT_DOWN_MM)) * (p / 1000.0)


def elbow_hit(side, frame):
    """肘偏好方向：Idle 内收 → 受击时微微外张下压（按 `press` 插值，归一化）。

    ★★ 必须**乘 `p`**！D05 首轮漏了这一步 ⟹ 偏移变成常量、`press = 0` 的末帧
    仍带着约 2° 的肘提示偏角 ⟹ 肘位差 `328 mm × 2° ≈ 11.6 mm`。
    """
    p = press(frame)
    if p <= 1e-9:
        return tuple(IDLE_ELBOW_DIR[side])
    sign = 1.0 if side == "L" else -1.0
    want = Vector(IDLE_ELBOW_DIR[side]) + Vector(
        (sign * _EH_X, _EH_Y, _EH_Z)) * p
    if want.length < 1e-9:
        return tuple(IDLE_ELBOW_DIR[side])
    return tuple(want.normalized())


def arm_seat_tip(arm, pose, side, tip_target, elbow_dir):
    """★★ D05 立的臂解算：**两骨 IK 打在腕上，手骨按零位自己的握拳角单独瞄**。

    ══════════════════════════════════════════════════════════════════════════
    `UE.arm_seat` 把 `forearm + hand` 当成一根**共线刚性连杆**（给 `fo` 与 `hd`
    的是**同一个**方向）⟹ 解出来的手骨必然与前臂共线。D01/D03/D04 没事，因为
    那几支零位（护架）本身就是 `arm_seat` 解出来的、自洽。本支零位是 A01
    **授权**的战斗待机（`aim_bone` 直瞄，不走两骨 IK），小臂→拳有**自己的折角**
    （实测 L 21.34° / R 26.16°）⟹ 腕位差 ~30 mm（拳尖却精确）—— 这个
    "**拳尖 0.0 mm、腕 30.4 mm**"的矛盾组合就是共线假设的铁证。

    做法：拳尖目标 → 腕目标 `tip − |hand| · 零位手骨朝向`；两骨 IK 只解
    `upperarm + forearm`；手骨用 `aim_nearest` 单独瞄回零位朝向。
    `press = 0` 时腕目标 ≡ 零位腕、肘提示 ≡ 零位肘、手向 ≡ 零位手向 ⟹ 自洽。
    ══════════════════════════════════════════════════════════════════════════
    """
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


def torso_pose(frame):
    p = press(frame)
    lead = lead_scale(frame)
    out = {}
    for name in TARGET_BONES:
        zero = ZERO[name]
        # ★ 头/颈/肩用领跑标量（先到位），躯干其余骨用主标量。
        scalar = lead if name in LEAD_BONES else p
        out[name] = (zero[0] + TORSO_HIT.get(name, 0.0) * scalar,
                     zero[1] + TORSO_YAW.get(name, 0.0) * scalar,
                     zero[2])
    drop = HIT_DROP_MM * p
    out["@loc"] = {"pelvis": A.wloc(HIT_SIDE_MM * p / 1000.0,
                                    HIT_BACK_MM * p / 1000.0,
                                    Z_SEAM + drop / 1000.0 - 0.900)}
    return out


def build_pose(arm, frame):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    # 腿：位置 IK（`UE.leg_seat`），踝目标钉死在 **`Idle_01@0` 的踝位**。
    for side in SIDES:
        UE.leg_seat(arm, pose, side, ANKLE_0[side], KNEE_DIR[side])
    for side in SIDES:
        name = "foot." + side
        pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name),
                                    A.keep_world_orientation(arm, name))
    for side in SIDES:
        # ★ 拳目标必须在 `apply_pose` 之后按**当前**肩位现取（肩随躯干走）
        arm_seat_tip(arm, pose, side, fist_target(side, frame),
                     elbow_hit(side, frame))
    if ROLL_RETURN:
        weight = _roll_weight(frame)
        if weight > 1e-9:
            for name in ROLL_BONES:
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, weight)
    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


def solve_pose(arm, frame, meshes=None):
    """单帧装配（无贴地闭环；踝由位置 IK 钉死，脚纹丝不动）。"""
    return build_pose(arm, frame)


# =============================================================== 滚转回位修正（D04 立）
def _roll_weight(frame):
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
    逐行沿用 D04/D05 的实作（根因：`UE.aim_nearest` 的世界朝向是沿接力链
    累积的，骨轴在方向球上划闭合回路时滚转吃到一份 holonomy）。
    做法 = 只在**世界朝向**里做 `q_ref = Δmin(零位骨轴 → 当前骨轴) ∘ q_zero`，
    再 `slerp(q_now, q_ref, w)` —— 骨轴一动不动 ⟹ IK / 指尖 / 贴地全不受影响。
    陷阱 = `upperarm` 零位欧拉可能骑在 XYZ 万向节锁上 ⟹ 必须配合
    `ROLL_WEIGHT_MODE="tail"`，把修正摊在恢复段上。★ 本支**默认不打开**。
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
    turn = ZERO_DIR[name].rotation_difference(direction_now)
    reference = (turn @ reference).normalized()
    now = pose_bone.matrix.to_3x3().to_quaternion().normalized()
    # ★ 四元数双覆盖：`q` 与 `−q` 是同一个旋转，不同半球会让 `slerp` 走长弧。
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
def _hit_frame_metrics(arm):
    """受击口径指标（当前帧）。"""
    lo, hi = PD.head_box()
    fists = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    pelvis_y = A.bone_world(arm, "pelvis", "head").y
    chest_dir = Vector(A.bone_direction(arm, "chest"))
    head_dir = Vector(A.bone_direction(arm, "head"))
    # ★ 世界俯仰：atan2(dy, dz)。躯干骨朝上 ⟹ 后仰（顶端往 +Y）为正，
    #   前折（顶端往 −Y）为**负**（D06 要的就是负）。
    pitch = math.degrees(math.atan2(chest_dir.y, chest_dir.z))
    head_pitch = math.degrees(math.atan2(head_dir.y, head_dir.z))
    return {
        "box_lo": Vector(lo), "box_hi": Vector(hi),
        "fist": fists,
        "fist_spread_mm": (abs(fists["L"].x) + abs(fists["R"].x)) * 1000.0,
        "fist_back_vs_pelvis_mm": {s: (fists[s].y - pelvis_y) * 1000.0
                                   for s in SIDES},
        "fist_z_mm": {s: fists[s].z * 1000.0 for s in SIDES},
        "chest_pitch_deg": pitch,
        "head_pitch_deg": head_pitch,
        "neck_y": Vector(A.bone_world(arm, "neck", "head")).y,
        "head_y": Vector(A.bone_world(arm, "head", "tail")).y,
        "chest_y": Vector(A.bone_world(arm, "chest", "head")).y,
        "pelvis_x": Vector(A.bone_world(arm, "pelvis", "head")).x,
    }


def hit_assertions(arm, action, samples, meshes):
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 零位真值 + 逐帧扫描
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _hit_frame_metrics(arm)
    per = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _hit_frame_metrics(arm)

    # ---- ★★ (a) `hit_light_ok`：**两个界都取负**，且必须能抓住"方向做反"
    pitch_delta = per[IMPACT]["chest_pitch_deg"] - zero["chest_pitch_deg"]
    head_fwd = (zero["head_y"] - per[IMPACT]["head_y"]) * 1000.0
    neck_fwd = (zero["neck_y"] - per[IMPACT]["neck_y"]) * 1000.0
    res["chest_pitch_zero_deg"] = round(zero["chest_pitch_deg"], 4)
    res["chest_pitch_impact_deg"] = round(per[IMPACT]["chest_pitch_deg"], 4)
    res["chest_pitch_delta_deg"] = round(pitch_delta, 4)
    res["head_fwd_mm"] = round(head_fwd, 2)
    res["neck_fwd_mm"] = round(neck_fwd, 2)
    # 与 D05 口径对照（D05 的 `head_back_mm = head_y - zero_y` ⟹ 本支 = −head_fwd）
    res["head_back_mm"] = round(-head_fwd, 2)
    # 全程极值（只报，用于抓"峰不在 IMPACT"这种设置错误）
    res["chest_pitch_delta_max_deg"] = round(
        max(abs(per[f]["chest_pitch_deg"] - zero["chest_pitch_deg"])
            for f in per), 4)
    res["head_fwd_max_mm"] = round(
        max((zero["head_y"] - per[f]["head_y"]) * 1000.0 for f in per), 2)
    res["hit_light_pitch_ok"] = bool(HIT_PITCH_MIN_DEG <= pitch_delta
                                     <= HIT_PITCH_MAX_DEG)
    res["hit_light_head_ok"] = bool(HIT_HEAD_FWD_MIN_MM <= head_fwd
                                    <= HIT_HEAD_FWD_MAX_MM)
    # ★★ 方向守卫（本支头号风险的"能失败"证明）：把 Δ 取反（= 正面受击）后
    #    必须**越界**。若有人写成 `abs()`，这条会立刻变红。
    res["hit_light_direction_can_fail_ok"] = bool(
        not (HIT_PITCH_MIN_DEG <= -pitch_delta <= HIT_PITCH_MAX_DEG))
    res["hit_light_ok"] = bool(res["hit_light_pitch_ok"]
                               and res["hit_light_head_ok"])

    # ---- (a2) 躯干偏转 / 侧移（前视可读的"被撞了一下"）—— 只报不判
    res["pelvis_side_shift_mm"] = round(
        (per[IMPACT]["pelvis_x"] - zero["pelvis_x"]) * 1000.0, 2)
    fists_delta = {}
    for s in SIDES:
        fists_delta[s] = [
            round((per[IMPACT]["fist"][s].x - zero["fist"][s].x) * 1000.0, 2),
            round((per[IMPACT]["fist"][s].y - zero["fist"][s].y) * 1000.0, 2),
            round((per[IMPACT]["fist"][s].z - zero["fist"][s].z) * 1000.0, 2)]
    res["fist_delta_mm"] = fists_delta
    res["fist_spread_zero_mm"] = round(zero["fist_spread_mm"], 2)
    res["fist_spread_impact_mm"] = round(per[IMPACT]["fist_spread_mm"], 2)
    res["fist_spread_delta_mm"] = round(
        per[IMPACT]["fist_spread_mm"] - zero["fist_spread_mm"], 2)
    # ★ "双臂仍保持防御形状"（计划 §1：**拳不应后收**）：
    #   `fist_back_delta_mm = impact_y − zero_y`，**负 = 拳往前**。
    #   D05（正面受击）是 +16 mm 后收；本支若**后收 >10 mm** 就说明符号翻漏了
    #   （方向读成"被正面打"）⟹ 上界 10 mm；前送允许到 40 mm。
    res["fist_back_delta_mm"] = round(
        min(per[IMPACT]["fist"][s].y - zero["fist"][s].y
            for s in SIDES) * 1000.0, 2)
    res["fist_fwd_delta_mm"] = round(-res["fist_back_delta_mm"], 2)
    res["arms_kept_shape_ok"] = bool(-40.0 <= res["fist_back_delta_mm"] <= 10.0)

    # ---- ★ (b) `hit_light_speed_ok`：节奏不对称（升 ≤3 帧、降 ≥18 帧）
    risers = sum(1 for f in range(TOTAL) if press(f + 1) > press(f) + 1e-9)
    fallers = sum(1 for f in range(TOTAL) if press(f + 1) < press(f) - 1e-9)
    res["press_rise_frames"] = risers
    res["press_fall_frames"] = fallers
    res["hit_light_speed_ok"] = bool(risers <= HIT_RISE_MAX_FRAMES
                                     and fallers >= HIT_FALL_MIN_FRAMES)
    # ★ 领跑指数的"确实领跑"自检（只报不判，用于抓 LEAD_GAMMA 是否生效）
    res["lead_scale_at_f1"] = round(lead_scale(1), 4)
    res["press_at_f1"] = round(press(1), 4)

    # ---- ★ (c) 打击停顿（§0.6：≥2 帧）
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

    # ---- ★ (d) `hit_light_recover_ok`：末帧回零位（四口径，D04 的第 4 条不许漏）
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()
    end = {}
    for side in SIDES:
        got = Vector(A.bone_world(arm, "hand." + side, "tail"))
        end[side] = round((got - IDLE_FIST[side]).length * 1000.0, 3)
    res["end_pose_mm"] = end
    end_world, end_world_bone = 0.0, None
    for name, ref in ZERO_WORLD.items():
        got = samples[-1].get(name)
        if got is None:
            continue
        gap = (Vector(got) - Vector(ref)).length * 1000.0
        if gap > end_world:
            end_world, end_world_bone = gap, name
    res["end_world_pose_mm"] = round(end_world, 4)
    res["end_world_pose_bone"] = end_world_bone
    # ★ 逐骨诊断（定位"哪根骨没回到零位"）
    end_per_bone = {}
    for name, ref in ZERO_WORLD.items():
        if name not in samples[-1]:
            continue
        gap = (Vector(samples[-1][name]) - Vector(ref)).length * 1000.0
        if gap > 0.05:
            end_per_bone[name] = round(gap, 3)
    res["end_world_per_bone_mm"] = dict(sorted(end_per_bone.items(),
                                               key=lambda kv: -kv[1])[:12])
    # ★ 手骨头/尖分开报（区分"整根骨位移"与"绕骨轴滚转"）
    hand_rows = {}
    for side in SIDES:
        head_now = Vector(A.bone_world(arm, "hand." + side, "head"))
        tail_now = Vector(A.bone_world(arm, "hand." + side, "tail"))
        hand_rows[side] = {
            "head_mm": round((head_now - Vector(
                ZERO_WORLD.get("hand." + side, head_now))).length * 1000.0, 3)
            if ("hand." + side) in ZERO_WORLD else None,
            "tail_mm": round((tail_now - IDLE_FIST[side]).length * 1000.0, 3),
            "dir_deg": round(math.degrees(math.acos(max(-1.0, min(1.0,
                Vector(A.bone_direction(arm, "hand." + side)).normalized().dot(
                    ZERO_DIR.get("hand." + side,
                                 Vector(A.bone_direction(
                                     arm, "hand." + side)).normalized())))))), 4),
        }
    res["end_hand_rows"] = hand_rows
    # ★★ 位置口径**发现不了绕骨轴滚转**：一根骨整体绕自身轴转 30°，骨根与骨尖
    #    一动都不动，但蒙皮（袖子 / 拳套截面）会转 ⟹ 画面里轮廓变。
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
    res["end_roll_ok"] = bool(worst_roll <= HIT_ROLL_MAX_DEG)
    last2 = 0.0
    for index in range(len(samples) - 2, len(samples)):
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            last2 = max(last2, max(abs(x - y) for x, y in zip(a, b)))
    res["end_last2_deg"] = round(last2, 4)
    res["hit_light_recover_ok"] = bool(
        all(v <= HIT_END_MAX_MM for v in end.values())
        and end_world <= HIT_END_MAX_MM
        and last2 <= HIT_LAST2_MAX_DEG
        and worst_roll <= HIT_ROLL_MAX_DEG)

    # ---- 穿模（`guard_no_face_clip_ok` → `no_face_clip_ok` 改名保留）
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [IMPACT, HOLD_END, RECOVER_END, TOTAL]))
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

    # ---- 可达性（逐帧取最差）
    worst_reach, worst_reach_frame = 0.0, None
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

    # ---- ★ 膝角被动吸收（D03 新立；本支上限**收到 2.0°** —— "膝几乎不弯"）
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
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()

    # ---- 峰值/零位拳位 + 像素换算复核（D03 教训 3：1 mm ≈ 0.556 px）
    res["zero_fist_mm"] = {s: [round(v * 1000.0, 1) for v in IDLE_FIST[s]]
                           for s in SIDES}
    res["impact_fist_mm"] = {s: [round(v * 1000.0, 1)
                                 for v in per[IMPACT]["fist"][s]]
                             for s in SIDES}
    res["zero_head_box_mm"] = [[round(v * 1000.0, 1) for v in zero["box_lo"]],
                               [round(v * 1000.0, 1) for v in zero["box_hi"]]]
    res["px_per_mm"] = 0.556
    res["head_fwd_px"] = round(head_fwd * 0.556, 2)

    # ---- 剪影 / aspect / 高度：**只报不判**（计划 §2 原文）
    sil = P.silhouette(arm, "d06")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    if os.environ.get("D06_TRACE"):
        res["trace"] = {str(f): {
            "press": round(press(f), 4),
            "lead": round(lead_scale(f), 4),
            "pitch": round(per[f]["chest_pitch_deg"], 3),
            "head_y": round(per[f]["head_y"] * 1000.0, 1),
            "fist_back": round(min(per[f]["fist"][s].y - zero["fist"][s].y
                                   for s in SIDES) * 1000.0, 2),
        } for f in range(0, TOTAL + 1)}
        step_trace = {}
        for index in range(1, len(samples)):
            row = {}
            for name in ARM_BONES:
                ea = samples[index - 1]["euler"].get(name, (0.0, 0.0, 0.0))
                eb = samples[index]["euler"].get(name, (0.0, 0.0, 0.0))
                row[name] = round(max(abs(x - y) for x, y in zip(ea, eb)), 2)
            step_trace[str(samples[index]["frame"])] = row
        res["arm_step_trace"] = step_trace
    return res


# =============================================================== 引导
def _load_idle_zero(arm):
    """★ 零位真源：落盘 `Idle_01` action 的**帧 0**（引擎真正会播的那份数据）。

    `Idle_01 → Hit_Light_B` 直连要求起手帧 = **战斗待机的某一帧**；
    A01 是**循环**动画、`Idle_01@0 ≡ Idle_01@180` ⟹ 取帧 0。
    读**落盘 action**（引擎真正播的那份），重演只用来交叉核对（`IDLE_MATCH`）。
    """
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
    """重演 `I1.idle_pose(arm, 0.0)`（确定性，不走接力链）—— 交叉核对用。"""
    return I1.idle_pose(arm, 0.0)


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
        print("D06_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ---- 臂长（`arm_seat_tip` 用）
    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}

    # ---- 欧拉支搜索调参（照抄 D05 的定稿）
    UE.ROLL_STEP_DEG = _env_f("D06_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D06_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D06_YWEIGHT", 0.0)

    # ---- 探针骨表扩容（腿 + 脚）—— 与 D01/D04/D05 同
    for extra in LEG_BONES + ("foot.L", "foot.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    # ---- ★★ 零位 = 落盘 `Idle_01` action 帧 0
    ZERO, saved_info = _load_idle_zero(arm)

    # ---- 交叉核对：落盘 vs 重演 `I1.idle_pose(arm, 0.0)`
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

    # ---- 零位几何（IK 基准 + 判据锚点）
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
    # ★ 膝鼓出方向**逐侧、从零位现取**（D05 教训 3：两侧共用一根会让
    #   `thigh.R` 方向差 0.887° ⟹ 膝位偏 6.36 mm）。
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
    # ★ 零位世界旋转基（含绕骨轴滚转）—— 位置口径看不见它
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            ZERO_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES:
        ZERO_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()

    zrow = _hit_frame_metrics(arm)
    A.report("D06_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "impact": IMPACT, "hold_end": HOLD_END, "hit_hold": HIT_HOLD,
        "recover_end": RECOVER_END, "cancel": CANCEL,
        "segments": 1, "hit_points": 0, "root_motion_m": [0.0, 0.0],
        "force_direction": "背面（力把上身往 +Y→−Y 前折）",
        "zero_source": "Idle_01@%d（落盘 action，非重演）" % saved_info.get(
            "frame"),
        "zero_pose_src": saved_info,
        "zero_vs_idle_pose_euler_max_diff_deg": round(euler_diff, 6),
        "zero_vs_idle_pose_worst_bone": euler_bone,
        "zero_vs_idle_pose_geom_pos_mm": round(geom_pos, 6),
        "zero_vs_idle_pose_geom_dir_deg": round(geom_dir, 6),
        "zero_pelvis_z_mm": round(Z_SEAM * 1000.0, 3),
        "zero_fist_mm": {s: [round(v * 1000.0, 2) for v in IDLE_FIST[s]]
                         for s in SIDES},
        "zero_fist_spread_mm": round(zrow["fist_spread_mm"], 2),
        "zero_ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                          for s in SIDES},
        "zero_knee_dir": {s: [round(v, 4) for v in KNEE_DIR[s]] for s in SIDES},
        "zero_wrist_mm": {s: [round(v * 1000.0, 2) for v in IDLE_WRIST[s]]
                          for s in SIDES},
        "zero_hand_dir": {s: [round(v, 4) for v in IDLE_HAND_DIR[s]]
                          for s in SIDES},
        "zero_hand_bend_deg": {
            s: round(math.degrees(math.acos(max(-1.0, min(1.0, IDLE_HAND_DIR[s].dot(
                Vector(A.bone_direction(arm, "forearm." + s)).normalized()))))), 4)
            for s in SIDES},
        "zero_euler_y_deg": {n: round(ZERO[n][1], 4) for n in ARM_BONES
                             if n in ZERO},
        "zero_euler_y_lock_risk": {n: round(abs(abs(ZERO[n][1]) - 90.0), 3)
                                   for n in ARM_BONES if n in ZERO},
        "hit_drop_mm": HIT_DROP_MM,
        "hit_pelvis_offset_mm": [HIT_SIDE_MM, HIT_BACK_MM, HIT_DROP_MM],
        "hit_fist_offset_mm": [HIT_OUT_MM, HIT_BACKF_MM, HIT_DOWN_MM],
        "torso_hit_deg": TORSO_HIT,
        "torso_yaw_deg": TORSO_YAW,
        "elbow_hit_delta": [_EH_X, _EH_Y, _EH_Z],
        "pitch_gate_deg": [HIT_PITCH_MIN_DEG, HIT_PITCH_MAX_DEG],
        "head_fwd_gate_mm": [HIT_HEAD_FWD_MIN_MM, HIT_HEAD_FWD_MAX_MM],
        "lead_gamma": LEAD_GAMMA, "lead_bones": list(LEAD_BONES),
        "roll_return": ROLL_RETURN, "roll_weight_mode": ROLL_WEIGHT_MODE,
        "note": ("D06 背面轻受击：零位 = Idle_01 落盘帧 0；升 3 / 峰停 2 / 降 19；"
                 "小幅**前折**（chest 俯仰 −1.5~−5.0°）+ 头前甩 15~60 mm + "
                 "骨盆前移 + 躯干轻微偏转侧移；拳往前/外带走、**不应后收**；"
                 "头/颈/肩领跑（更早到位）；脚不动、膝几乎不弯；0 命中点、0 位移"),
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

    # ★ 首键 = 零位（= `Idle_01@0`，含绕骨轴滚转的逐位相同）
    keyframes = [(0, ZERO)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))
    # ★★ 尾部**不钉 `dict(ZERO)`**（D03 教训 2：钉值会凭空造出零空间滚转跳变）。
    #   尾部输入恒等于零位 ⟹ 解出的姿态逐帧恒定、世界姿态 = 零位，欧拉路径连续。

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "防御与受击",
        "note": ("背面轻受击：头/胸小幅前折 + 躯干轻微偏转侧移，快速恢复；"
                 "拳被往前/外带走（不后收）、双臂保持防御形状、脚不动、膝几乎不弯；"
                 "0 命中点、0 位移"),
        "antic_frame": 0,
        "hit_frame": IMPACT,
        "cancel_frame": CANCEL,
        "stagger_end_frame": HOLD_END,
        "hitstop_frames": HIT_HOLD,
        "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "hit_point_m": None,
        "start_pose_ref": "Idle_01 帧 0（战斗待机）",
        "end_pose_ref": "Idle_01 帧 0（受击结束回到战斗待机，可接 Idle_01 / Idle_02）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "IMPACT": IMPACT, "HOLD_END": HOLD_END,
                           "CANCEL": CANCEL, "END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta,
                                     foot_probe=("foot.L", "foot.R"),
                                     slide_tolerance_mm=SLIDE_MAX_MM)
    report.update(hit_assertions(arm, action, samples, meshes))
    report["meta"] = meta

    # 起手接合：f0 必须与 `Idle_01@0` **逐位相同**（两边都过 float32）
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

    # 零位守卫：落盘 `Idle_01@0` 与 `I1.idle_pose(arm, 0.0)` 必须几何同解
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
    A.report("D06_REPORT", report)

    if not SKIP_RENDER:
        # ★ 计划 §4 要 f0/f2/f3/f5/f12/f24（**f5 不可省**：停顿平台的像素级证据）。
        frames = [0, 2, IMPACT, HOLD_END, 12, TOTAL]
        A.render_pose_sheet(arm, action, frames, "hitlightb",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D06_DONE failed=%s" % report["failed"])
    print("D06_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D06_FAILURE " + traceback.format_exc())
