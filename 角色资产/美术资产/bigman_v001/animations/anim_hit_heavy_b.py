"""anim_hit_heavy_b —— D08 `Hit_Heavy_B` 背面重受击。

清单原文：「明显重心移动，可退 1~2 步」。

★★ 本支是 D07 `Hit_Heavy_F` 的**镜像支**（清单「下一支详细制作计划 —— D08」）：
    "镜像"只在 **受力方向** 与 **重心去向**；腿的时间表、门禁口径、末帧语义
    **逐条照抄 D07**（D07 已把这一族全趟通）。

  D07「正面重受击」：力把上身往 **+Y（身后）** 推 ⟹ 后仰 + 后脚后撤。
  D08「背面重受击」：力把上身往 **−Y（身前）** 折 ⟹ 前折 + 前脚**前提步**。
  ★ 同一个量（胸世界俯仰 / 头位移 / 侧视像素重心）**符号全反**。

★★ §2 唯一的真风险：不能照 D07 硬编码"后脚 = R"。D08 里迈步的那只脚是
   **L**（零位的前脚，受力同向侧）—— 见 §2 **方案 A**。沿用 R 会让"被推方向"
   与"迈步方向"打架（侧视读成"自己往前走了一步"）。

方向符号（★ 与 D07 全反）：
    受力 = **背面**（力把上身往前 −Y 折）。所以
      · `chest` 世界俯仰 Δ = **负**（前折），两界都取负：Δ ∈ [−10.0, −5.0]
      · `head_fwd_mm = (zero.head_y − per[IMPACT].head_y) × 1000` ∈ [+100, +175]
      · 骨盆被往 **−Y** 推（`BODY_SIGN = −1`）—— 与 D07 反号
      · 拳被往**前/外**带开（`HIT_BACKF_MM` 取 **负**）—— 与 D06 同号、与 D07 反号
      · 侧视像素符号 `SIDE_SIGN = −1`（重心左移）—— 与 D06 同号、与 D07 反号
      · `root_motion_m = [0, −0.250]`（负 = 前移）
    横向量（`HIT_SIDE_MM` / `HIT_OUT_MM` / `TORSO_YAW` / 肘提示 `_EH_*`）**不翻**：
    它们与受力方向无关（D05/D06 的肘提示逐字相同即为证据）。

D07 四条教训**一并继承**：
    ① 大位移先算 `1.5×位移/N ≤ 30 mm`（本支 0.387 m / 21 帧，同 D07）；
    ② ★ 量零位前必须 `arm.animation_data.action = None`（末帧不回原位，
       否则每个 Δ 都偏一个整体位移、且**静默地把方向读反**）；
    ③ `_roll_return` 「滚一趟 → 重瞄一趟」交替、**末趟必须收在"瞄"上**（定点 2 趟）；
    ④ `press ≡ 0` 的帧必须**短路**回零位（float32 往返噪声顶红 `end_torso_ok`）。
三条 D05 修正**一并继承**：`arm_seat_tip()` / `elbow_hit()` 乘 `p` / `KNEE_DIR[side]`。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_hit_heavy_b.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D08_TRACE=1    逐帧打印 press / 躯干俯仰 / 迈步脚位移 / 离地量（调参用）
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

NAME = "Hit_Heavy_B"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")

# ★★ 运动方向：背面受击 ⟹ 身体被往 **−Y（身前）** 推。D07 是 +1（身后）。
BODY_SIGN = -1.0
# ★★ §2 方案 A：迈步脚 = 零位的**前脚 L**（受力同向侧那个脚），R 只被**蹭**着走。
#    ★ 绝不能沿用 D07 的"后脚 = R"硬编码 —— 那会让"被推方向"与"迈步方向"打架。
STEP_FOOT = "L"      # 迈步脚（D07 的 `BACK_FOOT` 槽位）
SKID_FOOT = "R"      # 蹭地脚（D07 的 `FRONT_FOOT` 槽位）


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
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D07 的 `_f32` 同源）。"""
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
# ★ 逐条照抄 D07（时间表是这一族已验证的成品，本支不重新设计）。
TOTAL = _env_i("D08_TOTAL", 42)          # 0.700 s @60fps（计划 0.6~0.9 s）
IMPACT = _env_i("D08_IMPACT", 4)         # 命中峰（上升沿 4 帧）
HIT_HOLD = _env_i("D08_HOLD", 4)         # 小硬直平台 4 帧
HOLD_END = IMPACT + HIT_HOLD             # 8
STEP_OFF = HOLD_END                      # 8  —— 迈步脚离地（= 硬直结束）
STEP_PLANT = _env_i("D08_PLANT", 29)     # 迈步脚落地（迈步段 8→29 = 21 帧）
#   ★ 为什么是 21 帧而不是 18（D07 教训 1）：`no_foot_teleport_ok`（≤30 mm/帧）是
#   **物理下界**。0.387 m / N 帧，pwl 平滑段峰值 = 1.5×均值 ⟹ 1.5×387/N ≤ 30
#   ⟹ N ≥ 19.4 ⟹ N = 21（D07 实测峰值 29.353 mm/帧，余量 1.6）。改**动画**，不改判据。
SKID_END = _env_i("D08_SKID_END", 20)    # 蹭地脚蹭完（比迈步脚落地**早** ⟹ 有先后）
RECOVER_END = _env_i("D08_RECOVER", 32)  # 躯干偏转回到 0 的帧（降 24 帧 ≥18）
CANCEL = _env_i("D08_CANCEL", 34)

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
GROUND_MIN_MM, GROUND_MAX_MM = -2.0, 6.0
REACH_MAX_RATIO = 0.995
# ★ 膝：本支允许更大（迈步必然屈膝），计划建议 ≤12°
KNEE_DELTA_MAX_DEG = _env_f("D08_KNEE", 12.0)
STANCE_SOLE_MAX_MM = _env_f("D08_SOLE", 6.0)

# ---- ★★ 本支头号判据 `hit_heavy_ok`：**两个界都取负**（与 D07 相反，与 D06 同口径）--
# ★ 世界俯仰 `pitch = atan2(chest_dir.y, chest_dir.z)`，+Y = 身后 ⟹ **后仰为正**。
#   本支是**背面受击** ⟹ Δ 必须为**负**。两界都取负，**不许用 abs()**。
HIT_PITCH_MIN_DEG = _env_f("D08_PITCH_MIN", -10.0)
HIT_PITCH_MAX_DEG = _env_f("D08_PITCH_MAX", -5.0)
# ★ 头部口径（照 D06 的表）：`head_fwd_mm = (zero.head_y − per[IMPACT].head_y) × 1000`
#   （正 = 头往前）。D04 对照：胸 9.8° / 头 168.6 mm；本支要求接近 D04 的量级。
HIT_HEAD_FWD_MIN_MM = _env_f("D08_HEAD_MIN", 100.0)
HIT_HEAD_FWD_MAX_MM = _env_f("D08_HEAD_MAX", 175.0)

# ---- 节奏不对称（升 ≤4 帧、降 ≥18 帧）
HIT_RISE_MAX_FRAMES = _env_f("D08_RISE_MAX", 4.0)
HIT_FALL_MIN_FRAMES = _env_f("D08_FALL_MIN", 18.0)
RISE_EVEN = _env_f("D08_RISE_EVEN", 1.0) >= 0.5
RISE_GAMMA = _env_f("D08_RISE_GAMMA", 1.0)
# ★ lead 机器照抄 D07，本支同样**默认恒等**（LEAD_GAMMA = 1）：
#   重击的"折"由 neck/head 的更大 rx 承担，不引入"头颈领跑"这个额外自由度。
LEAD_GAMMA = _env_f("D08_LEAD_GAMMA", 1.0)
LEAD_BONES = ("neck", "head", "shoulder.L", "shoulder.R")

# ---- 打击停顿
HITSTOP_MIN_FRAMES = _env_f("D08_HITSTOP_MIN", 4.0)

# ---- 末帧口径（四口径；世界位置要**加整体位移**，腿不比世界位置）
HIT_END_MAX_MM = _env_f("D08_END_MAX", 0.5)
HIT_LAST2_MAX_DEG = _env_f("D08_LAST2", 0.5)
HIT_ROLL_MAX_DEG = _env_f("D08_ROLL_MAX", 0.5)
# ★ 滚转修正：D07 实测需要（2 趟 ⟹ 0.0396°）；本支臂摆幅同量级 ⟹ 默认打开。
ROLL_RETURN = _env_f("D08_ROLL_RETURN", 1.0) >= 0.5
ROLL_WEIGHT_MODE = os.environ.get("D08_ROLL_WEIGHT", "tail").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D08_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split(",")
    if item)
# ★ 滚转修正的迭代趟数（见 build_pose 的 ★★ 说明）：
#   1 趟 = D05/D06 的老行为（会留下方向残差）；2 趟 = 滚→瞄→滚→瞄（D07 的定点）；
#   3 趟以上反而**过冲**（末趟是"滚"、没人接"瞄" ⟹ 每多一趟 +2.0°）。
ROLL_ITER = max(1, int(os.environ.get("D08_ROLL_ITER", "2")))
# ★ 滚转口径只对**臂骨**成立：腿在本支末帧处于**新站位**，其世界基"本就不同"。
END_ROLL_BONES = ARM_ROLL_BONES = ("upperarm.L", "forearm.L", "hand.L",
                                   "upperarm.R", "forearm.R", "hand.R")

# ---- 穿模
CLIP_MAX_MM = _env_f("D08_CLIP_MAX", 0.0)
CLIP_EVERY = int(os.environ.get("D08_CLIP_EVERY", 4))

# ---- 零位守卫
IDLE_MATCH_TOL_DEG = _env_f("D08_IDLE_MATCH", 1.0e-3)
IDLE_GEOM_POS_MAX_MM = _env_f("D08_IDLE_POS", 0.01)
IDLE_GEOM_DIR_MAX_DEG = _env_f("D08_IDLE_DIR", 0.05)

# =============================================================== 位移几何
# ★★ 步幅**从 A03 `Walk_F` 的实测取**（计划 §2 硬要求：「不要拍脑袋」）：
#   `Walk_F` 落盘门禁 `stride_m` ＝ **0.3871 m**。故 **1 步 = 0.387 m**，本支迈 **1 步**。
STEP_BACK_M = _env_f("D08_STEP", 0.387)     # 步幅**幅值**（下面再乘方向符号）
# ★ 身体净位移**幅值**：迈步脚要在髋**前** `0.170 + STEP − BODY = 0.307` 处落地。
#   脚相对髋的前向可达上限 = √(0.814² − 0.737²) = **0.345 m**（髋高 0.815 / 腿长 0.822）。
#   取 BODY = 0.250 ⟹ 相对前移 0.307（余量 0.038 m）⟹ 前膝仍有明显屈曲。
BODY_BACK_M = _env_f("D08_BODY", 0.250)
OVERSHOOT = _env_f("D08_OVERSHOOT", 1.072)  # 骨盆先被推过一点，再由腿"找回"
# 蹭地脚只**蹭**（skid）：位移必须 ≤ 迈步脚的一半（计划 §2）
SKID_M = _env_f("D08_SKID_M", 0.140)
LIFT_PEAK = _env_f("D08_LIFT", 0.11)        # 迈步脚离地峰值（米）
STEP_MIN_M = _env_f("D08_STEP_MIN", 0.20)
STEP_MAX_M = _env_f("D08_STEP_MAX", 0.60)
STEP_ORDER_FRAC = _env_f("D08_STEP_ORDER", 0.5)
LIFT_MIN_MM = _env_f("D08_LIFT_MIN", 25.0)
# ★★ 带符号的位移（★ 本支全部指向 **−Y 身前**）
PUSH_M = BODY_SIGN * _env_f("D08_PUSH", 0.055)     # 命中瞬间（f0→f4）被推走的量
BODY_MOVE_M = BODY_SIGN * BODY_BACK_M              # −0.250
STEP_MOVE_M = BODY_SIGN * STEP_BACK_M              # −0.387
SKID_MOVE_M = BODY_SIGN * SKID_M                   # −0.140
# ★★ 蒙皮补偿（D08 实测根因，见 sole_lift 注释）：
#   `Shoe_Sole_*` / `Shoe_Heel_*` / `Shoe_Upper_*` 的**顶点权重**里有 `shin.*`（实测
#   `Shoe_Sole_L` = foot.L 1.0 / toe.L 1.0 / **shin.L 0.5**）。腿一旦相对骨盆摆开，
#   小腿的旋转会把**鞋底**一起带下去 —— 脚骨世界朝向逐位钉在 rest（实测 0.0000°）、
#   脚骨 head z 全程恒定（79.74 mm），鞋底却仍会下沉。实测本支：L 脚相对骨盆前伸
#   +137 mm（小腿摆角变 ~21°）⟹ 鞋底相对脚骨漂 **Δy +85.8 / Δz −5.6 mm**；
#   蹭地脚 R 摆角只变 ~1.8° ⟹ 只漂 0.15 mm。**这不是脚朝向问题，是蒙皮伪影。**
#   ⟹ 按"相对骨盆的前伸变化"线性抬踝补偿，让**看得见的鞋底**贴地（门禁量的就是网格）。
SOLE_LIFT_MM = _env_f("D08_SOLE_LIFT", 5.6)   # t = 1 时的踝抬升（mm）
REL_END_M = abs(BODY_MOVE_M - STEP_MOVE_M)    # 0.137 —— 迈步脚相对骨盆的净前伸

# =============================================================== 受击幅度
# ★ 符号规则（与 D07 逐条反号，横向量不翻）：
#     - 骨盆沿 −Y 是"身前" ⟹ 被从背后推 ⟹ **body_shift 取负（往 −Y 前冲）**。
#     - 拳沿 −Y 是"前送" ⟹ **HIT_BACKF_MM 取负**（后收会读成"被正面打"）。
#     - 骨盆侧移 / 拳外张 / 拳下沉 / 肘提示：侧向量，符号不随受力方向翻转。
HIT_SIDE_MM = _env_f("D08_SIDE", 6.0)      # 骨盆侧移（前视可见）
HIT_OUT_MM = _env_f("D08_OUT", 14.0)       # 每侧拳**横向外张**
HIT_BACKF_MM = _env_f("D08_BACKF", -28.0)  # ★ 拳沿 **−Y 前送**
HIT_DOWN_MM = _env_f("D08_DOWN", 8.0)      # 拳下沉
# 躯干**前折**链：`chest` 世界俯仰 = pelvis..chest 的 rx 之和（D04~D07 实测线性）。
# ★★ 符号铁律（D05 实测标定）：`rx > 0` = **前屈** ⟹ `pitch = atan2(chest_dir.y,
#   chest_dir.z)` 随 `+rx` **下降**。故本支要"前折"，全表必须取 **正号**
#   （照 D06 的表重定标；D07 是全部负号）。
# 幅度标定（同一把尺子）：D06 累加 2.30° ⟹ pitch −2.30°；D07 累加 −6.80° ⟹ +6.7983°。
#   本支取累加 **+6.80°** ⟹ pitch −6.80°（∈[−10,−5]），头位旋转分量 ≈ 90 mm，
#   加 `body_shift(f4) = −55 mm` ⟹ `head_fwd ≈ 145 mm`（∈[100,175]）。
TORSO_HIT = {"pelvis": _env_f("D08_TP_PELVIS", 1.10),
             "spine_01": _env_f("D08_TP_S1", 1.35),
             "spine_02": _env_f("D08_TP_S2", 1.60),
             "chest": _env_f("D08_TP_CHEST", 2.75),
             "neck": _env_f("D08_TP_NECK", 0.95),
             "head": _env_f("D08_TP_HEAD", 1.45),
             # ★ 照 D06 的表：两侧**同号同值**（D07 的 ±3 是它的侧滚，本支镜像回对称）
             "shoulder.L": _env_f("D08_TP_SH", 3.00),
             "shoulder.R": _env_f("D08_TP_SH", 3.00)}
TORSO_YAW = {"pelvis": _env_f("D08_YAW_PELVIS", 0.60),
             "spine_01": _env_f("D08_YAW_S1", 0.70),
             "spine_02": _env_f("D08_YAW_S2", 0.70),
             "chest": _env_f("D08_YAW_CHEST", 0.90),
             "neck": _env_f("D08_YAW_NECK", 0.80),
             "head": _env_f("D08_YAW_HEAD", 1.10)}
# 肘被顶开（比 D06 大，同 D07 幅值；★ 与受力方向无关，符号沿用 D05/D06/D07）
_EH_X = _env_f("D08_EB_X", 0.10)
_EH_Y = _env_f("D08_EB_Y", 0.08)
_EH_Z = _env_f("D08_EB_Z", -0.06)
# 骨盆沉降（mm，负 = 下沉）。★ 末帧**必须回到 0**（否则 `end_torso_ok` 等三口径全红）。
PZ_KEYS_MM = ((0, 0.0), (IMPACT, _env_f("D08_PZ_HIT", -12.0)),
              (HOLD_END, _env_f("D08_PZ_HIT", -12.0)),
              (18, _env_f("D08_PZ_BRACE", -26.0)),
              (STEP_PLANT, _env_f("D08_PZ_PLANT", -14.0)),
              # ★ 必须**在 CANCEL 之前**回到 0 并保持（否则末 2 帧 `end_last2_deg` 红）。
              (CANCEL, _env_f("D08_PZ_SETTLE", 0.0)),
              (TOTAL, _env_f("D08_PZ_END", 0.0)))

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")

# =============================================================== 模块级表
ZERO = {}                 # `Idle_01@0` 定格真值（本支零位）
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
# `press ≡ 0` 短路的命中帧数（见 build_pose 的 ★★）。只报，用于证明短路的作用域。
_ZERO_SHORTCUT = [0]


# =============================================================== 驱动标量
def press(frame):
    """躯干受力标量 ∈ [0, 1]：**升 4 / 峰停 4 / 降 24** 的单脉冲。

    峰值帧（press ≡ 1）由同一组参数解出 ⟹ 姿态逐位相同（硬直是真的"僵住"）。
    """
    keys = [(0, 0.0)]
    if RISE_EVEN:
        for step in range(1, IMPACT):
            keys.append((step, (step / float(IMPACT)) ** RISE_GAMMA))
    keys += [(IMPACT, 1.0), (HOLD_END, 1.0), (RECOVER_END, 0.0), (TOTAL, 0.0)]
    return UE.pwl(tuple(keys), float(frame), 0.0)


def lead_scale(frame):
    """★ 头/颈/肩的驱动标量（D07 的机器照抄）。本支默认 `LEAD_GAMMA = 1` ⟹ 恒等。"""
    p = press(frame)
    if LEAD_GAMMA >= 1.0:
        return p
    return p ** LEAD_GAMMA


def body_shift(frame):
    """★ 身体（骨盆）世界 y 净位移（**带符号**，米）。**本支的"迈步"主时间轴。**

    D08 为 **负**（往 −Y 身前冲）。形状 = 命中瞬间被推走 `PUSH_M` → 硬直冻结
    → 迈步段继续被推（略过头 `OVERSHOOT`）→ 迈步脚落地时**收回一点**（"靠腿找回"）。
    末帧停在 `BODY_MOVE_M`。
    """
    keys = ((0, 0.0), (IMPACT, PUSH_M), (HOLD_END, PUSH_M),
            (18, BODY_MOVE_M * OVERSHOOT), (STEP_PLANT, BODY_MOVE_M),
            (TOTAL, BODY_MOVE_M))
    return UE.pwl(keys, float(frame), 0.0)


def step_y(side, frame):
    """该脚的世界 y 位移（**带符号**，米；本支负 = 往 −Y 身前）。

    · 迈步脚（L）：硬直结束才离地起步，`STEP_PLANT` 落地 ⟹ 0 → `STEP_MOVE_M`。
    · 蹭地脚（R）：落地前它一直撑着，被身体**蹭**着走 ⟹ 0 → `SKID_MOVE_M`，
      且**更早**走完。
    """
    if side == STEP_FOOT:
        return UE.pwl(((0, 0.0), (STEP_OFF, 0.0), (STEP_PLANT, STEP_MOVE_M),
                       (TOTAL, STEP_MOVE_M)), float(frame), 0.0)
    return UE.pwl(((0, 0.0), (STEP_OFF, 0.0), (SKID_END, SKID_MOVE_M),
                   (TOTAL, SKID_MOVE_M)), float(frame), 0.0)


def step_lift(side, frame):
    """该脚的世界 z 抬升（米）。只有迈步脚会离地；蹭地脚全程贴地（蹭，不是抬）。"""
    if side != STEP_FOOT:
        return 0.0
    peak = STEP_OFF + (STEP_PLANT - STEP_OFF) * 0.5      # 17（步中）
    return UE.pwl(((0, 0.0), (STEP_OFF, 0.0),
                   (peak - 5, LIFT_PEAK * 0.5), (peak, LIFT_PEAK),
                   (peak + 5, LIFT_PEAK * 0.55), (STEP_PLANT, 0.0),
                   (TOTAL, 0.0)), float(frame), 0.0)


def pelvis_drop_mm(frame):
    return UE.pwl(PZ_KEYS_MM, float(frame), 0.0)


def sole_lift(side, frame):
    """★★ **蒙皮补偿**：腿相对骨盆前伸时，鞋底被 `shin.*` 权重带下去的抬踝补偿（米）。

    量：`delta = step_y − body_shift`（该踝相对骨盆的前伸变化，负 = 更前伸）。
    `delta >= 0` 时**不补**（零位、以及"身体先走、脚还没迈"的那一段）。
    线性映射 `t = clamp(−delta / REL_END_M, 0, 1)`，末端 `t = 1` ⟹ 抬 `SOLE_LIFT_MM`。

    ★ 为什么是"踝"而不是"改判据"：门禁量的是**鞋底网格最低点**，主人看到的也是鞋底，
      脚骨本身高 5.6 mm 看不见。抬踝让**可见鞋底**回到地面，是把动画改对，不是放宽容差。
    """
    delta = step_y(side, frame) - body_shift(frame)
    if delta >= 0.0:
        return 0.0
    t = min(1.0, -delta / REL_END_M)
    return SOLE_LIFT_MM * t / 1000.0


def ankle_target(side, frame):
    """★★ 本支的腿目标：**不再是常量**，而是按帧的时间表（+ 蒙皮补偿抬升）。"""
    base = ANKLE_0[side]
    return Vector((base.x, base.y + step_y(side, frame),
                   base.z + step_lift(side, frame) + sole_lift(side, frame)))


def fist_target(side, frame):
    """拳世界目标 = `Idle_01@0` 拳位 **+ 整体位移** + 受击偏移。

    ★★ 必须加 `body_shift`：身形前移 0.25 m，拳若钉在绝对世界点上，
       手臂要凭空伸长 0.25 m —— `reach_ok` 会当场红。
    """
    p = press(frame)
    sign = 1.0 if side == "L" else -1.0
    return Vector(IDLE_FIST[side]) + Vector((0.0, body_shift(frame), 0.0)) + Vector(
        (sign * HIT_OUT_MM, HIT_BACKF_MM, -HIT_DOWN_MM)) * (p / 1000.0)


def elbow_hit(side, frame):
    """肘偏好方向：Idle 内收 → 受击时外张下压（按 `press` 插值）。

    ★★ 必须**乘 `p`**（D05 教训 2）：`p = 0` 的末帧要逐位等于零位肘向。
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
    """★★ D05 立的臂解算：**两骨 IK 打在腕上，手骨按零位自己的折角单独瞄**。

    做法：拳尖目标 → 腕目标 `tip − |hand| · 零位手骨朝向`；两骨 IK 只解
    `upperarm + forearm`；手骨用 `aim_nearest` 单独瞄回零位朝向。
    `press = 0` 时腕目标 ≡ 零位腕、肘提示 ≡ 零位肘、手向 ≡ 零位手向 ⟹ 自洽。
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
        scalar = lead if name in LEAD_BONES else p
        out[name] = (zero[0] + TORSO_HIT.get(name, 0.0) * scalar,
                     zero[1] + TORSO_YAW.get(name, 0.0) * scalar,
                     zero[2])
    out["@loc"] = {"pelvis": A.wloc(HIT_SIDE_MM * p / 1000.0,
                                    body_shift(frame),
                                    Z_SEAM + pelvis_drop_mm(frame) / 1000.0
                                    - 0.900)}
    return out


def build_pose(arm, frame):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    # 腿：位置 IK（`UE.leg_seat`），踝目标 = 零位踝 + 逐帧步态时间表
    for side in SIDES:
        UE.leg_seat(arm, pose, side, ankle_target(side, frame), KNEE_DIR[side])
    for side in SIDES:
        name = "foot." + side
        pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name),
                                    A.keep_world_orientation(arm, name))
    # ★★ `press ≡ 0` 短路（D07 教训 4）：受击标量恒 0 的帧，躯干 + 臂的**正确解
    #   就是零位本身**（整体平移已由 `@loc` 表达完）。再解一遍只会把
    #   `pose_bone.matrix` 的 float32 往返噪声写进欧拉（D07 实测 hand.L 残差
    #   1.9e-05°，而 `end_torso_ok` 的界是 ≤1e-6°，差 19 倍）—— 这不是动画不达标，
    #   是**表示噪声**。判据不放宽，改成让解算器在恒零帧上精确。
    #   ★ 腿**不短路**：它站**新站位**，本来就不是零位。
    if press(frame) <= 1e-12:
        _ZERO_SHORTCUT[0] += 1
        for name in ARM_BONES:
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
            # ★★ 滚转修正必须"滚一趟 → 重瞄一趟"交替（D07 教训 3）：
            #   `_roll_return` 是**绕骨自身轴**滚转 ⟹ 它把该骨的**所有子骨**在世界里
            #   一起带偏。每趟滚完**重瞄**（`aim_nearest` + 同步过的 `CARRY_Q` = 只补
            #   方向、保留滚转），交替到收敛。判据一个没动。
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
    return 1.0 - press(frame)


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
    # ★★ 必须同步 `CARRY_Q`：后面重瞄时 `aim_nearest` 从 `CARRY_Q` 接力、只补
    #    "把骨轴摆到目标"的最小旋转 ⟹ 同步后重瞄**保留滚转**。
    UE.CARRY_Q[name] = blended
    pose[name] = JS._unwrap_xyz(
        JS._PREV_EULER.get(name),
        tuple(math.degrees(v) for v in pose_bone.rotation_euler))


# =============================================================== 专属门禁
def _hit_frame_metrics(arm):
    lo, hi = PD.head_box()
    fists = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    pelvis_y = A.bone_world(arm, "pelvis", "head").y
    chest_dir = Vector(A.bone_direction(arm, "chest"))
    head_dir = Vector(A.bone_direction(arm, "head"))
    # ★ 世界俯仰：atan2(dy, dz)。躯干骨朝上 ⟹ 后仰（顶端往 +Y）为**正**。
    pitch = math.degrees(math.atan2(chest_dir.y, chest_dir.z))
    head_pitch = math.degrees(math.atan2(head_dir.y, head_dir.z))
    return {
        "box_lo": Vector(lo), "box_hi": Vector(hi),
        "fist": fists,
        "fist_spread_mm": (abs(fists["L"].x) + abs(fists["R"].x)) * 1000.0,
        "chest_pitch_deg": pitch, "head_pitch_deg": head_pitch,
        "neck_y": Vector(A.bone_world(arm, "neck", "head")).y,
        "head_y": Vector(A.bone_world(arm, "head", "tail")).y,
        "pelvis_x": Vector(A.bone_world(arm, "pelvis", "head")).x,
        "pelvis_y": pelvis_y,
    }


def hit_assertions(arm, action, samples, meshes):
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 零位真值 + 逐帧扫描
    # ★★★ 本支头号陷阱（D07 教训 2）：`A.apply_pose()` 是**手写 pose**，而 depsgraph
    #   在 action 已绑定时会按**当前场景帧**重新求值覆盖它。采样结束后场景帧停在
    #   `TOTAL` ⟹ 拿到的"零位"其实是**末帧姿态**。本支末帧带 `body_shift(TOTAL)`
    #   = −0.25 m 的整体位移 ⟹ 每个 Δ 都偏 +250 mm，连"方向"都被读反。
    #   修法：量零位前**摘掉 action**，量完再绑回。
    arm.animation_data.action = None
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _hit_frame_metrics(arm)
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    per = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _hit_frame_metrics(arm)

    # ---- ★★ (a) `hit_heavy_ok`：**两个界都取负**，且必须能抓住"方向做反"
    pitch_delta = per[IMPACT]["chest_pitch_deg"] - zero["chest_pitch_deg"]
    head_fwd = (zero["head_y"] - per[IMPACT]["head_y"]) * 1000.0
    neck_fwd = (zero["neck_y"] - per[IMPACT]["neck_y"]) * 1000.0
    res["chest_pitch_zero_deg"] = round(zero["chest_pitch_deg"], 4)
    res["chest_pitch_impact_deg"] = round(per[IMPACT]["chest_pitch_deg"], 4)
    res["chest_pitch_delta_deg"] = round(pitch_delta, 4)
    res["head_fwd_mm"] = round(head_fwd, 2)
    res["neck_fwd_mm"] = round(neck_fwd, 2)
    # 与 D07 口径对照（D07 的 `head_back_mm = head_y - zero_y` ⟹ 本支 = −head_fwd）
    res["head_back_mm"] = round(-head_fwd, 2)
    res["chest_pitch_delta_max_deg"] = round(
        max(abs(per[f]["chest_pitch_deg"] - zero["chest_pitch_deg"])
            for f in per), 4)
    res["head_fwd_max_mm"] = round(
        max((zero["head_y"] - per[f]["head_y"]) * 1000.0 for f in per), 2)
    res["hit_heavy_pitch_ok"] = bool(HIT_PITCH_MIN_DEG <= pitch_delta
                                     <= HIT_PITCH_MAX_DEG)
    res["hit_heavy_head_ok"] = bool(HIT_HEAD_FWD_MIN_MM <= head_fwd
                                    <= HIT_HEAD_FWD_MAX_MM)
    # ★★ 方向守卫：把 Δ 取反（= 正面受击）后必须**越界**。写成 abs() 则立刻红。
    res["hit_heavy_direction_can_fail_ok"] = bool(
        not (HIT_PITCH_MIN_DEG <= -pitch_delta <= HIT_PITCH_MAX_DEG))
    res["hit_heavy_ok"] = bool(res["hit_heavy_pitch_ok"]
                               and res["hit_heavy_head_ok"])

    # ---- (a2) 受击瞬间的骨盆/拳位移（只报，供像素复核）
    res["pelvis_side_shift_mm"] = round(
        (per[IMPACT]["pelvis_x"] - zero["pelvis_x"]) * 1000.0, 2)
    res["pelvis_fwd_hit_mm"] = round(
        (zero["pelvis_y"] - per[IMPACT]["pelvis_y"]) * 1000.0, 2)
    res["pelvis_back_hit_mm"] = round(
        (per[IMPACT]["pelvis_y"] - zero["pelvis_y"]) * 1000.0, 2)
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
    # ★ 拳的**前送**量（相对零位，**去掉整体位移**）—— 背面受击应前送（D06 口径）。
    press_fist_back = min(
        per[IMPACT]["fist"][s].y - zero["fist"][s].y - body_shift(IMPACT)
        for s in SIDES) * 1000.0
    res["fist_back_delta_mm"] = round(press_fist_back, 2)
    res["fist_fwd_delta_mm"] = round(-press_fist_back, 2)
    # ★ 上界口径（与 D07 对称）：拳被震开但**不能读成"破防"**（D04 是 148 mm 张开）。
    res["guard_kept_ok"] = bool(
        10.0 <= res["fist_fwd_delta_mm"] <= 60.0
        and 20.0 <= res["fist_spread_delta_mm"] <= 60.0)

    # ---- ★ (b) 节奏不对称（升 ≤4 帧、降 ≥18 帧）
    risers = sum(1 for f in range(TOTAL) if press(f + 1) > press(f) + 1e-9)
    fallers = sum(1 for f in range(TOTAL) if press(f + 1) < press(f) - 1e-9)
    res["press_rise_frames"] = risers
    res["press_fall_frames"] = fallers
    res["hit_heavy_speed_ok"] = bool(risers <= HIT_RISE_MAX_FRAMES
                                     and fallers >= HIT_FALL_MIN_FRAMES)
    res["lead_scale_at_f1"] = round(lead_scale(1), 4)
    res["press_at_f1"] = round(press(1), 4)

    # ---- ★ (c) 打击停顿（≥4 帧；"小硬直"）
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

    # ---- ★★ (d) 迈步口径（本支的核心，替代 D05/D06 的 plant_ok）
    step_axis = {}
    for s in SIDES:
        start = Vector(samples[0]["foot." + s])
        end = Vector(samples[TOTAL]["foot." + s])
        step_axis[s] = round((end.y - start.y) * 1000.0, 3)
    res["step_axis_mm"] = step_axis
    # ★ 本支的位移是**负向** ⟹ 口径取**幅值**，方向由 `step_back_dir_can_fail_ok` 守。
    res["step_back_m"] = round(abs(step_axis[STEP_FOOT]) / 1000.0, 4)
    res["step_skid_m"] = round(abs(step_axis[SKID_FOOT]) / 1000.0, 4)
    res["step_back_ok"] = bool(
        STEP_MIN_M <= res["step_back_m"] <= STEP_MAX_M)
    # ∵ 位移是**有向**的 ⟹ 必须自带"反向必失败"的证明（D06 教训 3）
    res["step_back_dir_can_fail_ok"] = bool(
        not (STEP_MIN_M <= -res["step_back_m"] <= STEP_MAX_M))
    res["step_order_ok"] = bool(
        res["step_skid_m"] <= STEP_ORDER_FRAC * res["step_back_m"] + 1e-9)
    # 单帧最大脚位移（防"瞬移"；位置口径，`no_teleport` 只管角度）
    max_foot_step_mm, max_foot_step_at = 0.0, None
    for index in range(1, len(samples)):
        for s in SIDES:
            a = Vector(samples[index - 1]["foot." + s])
            b = Vector(samples[index]["foot." + s])
            move = (b - a).length * 1000.0
            if move > max_foot_step_mm:
                max_foot_step_mm, max_foot_step_at = move, (index, s)
    res["max_foot_step_mm"] = round(max_foot_step_mm, 3)
    res["max_foot_step_at"] = max_foot_step_at
    res["no_foot_teleport_ok"] = bool(max_foot_step_mm <= 30.0)
    # 迈步脚确实**离地过**（空中有弧，不是贴地拖过去）
    lift_series = [samples[f]["low"][STEP_FOOT] for f in range(TOTAL + 1)]
    res["step_foot_lift_peak_mm"] = round(max(lift_series) * 1000.0, 2)
    res["step_foot_low_at_off_mm"] = round(
        samples[STEP_OFF]["low"][STEP_FOOT] * 1000.0, 2)
    res["step_foot_low_at_plant_mm"] = round(
        samples[STEP_PLANT]["low"][STEP_FOOT] * 1000.0, 2)
    res["foot_lift_ok"] = bool(
        res["step_foot_lift_peak_mm"] >= LIFT_MIN_MM
        and res["step_foot_low_at_off_mm"] <= STANCE_SOLE_MAX_MM
        and res["step_foot_low_at_plant_mm"] <= STANCE_SOLE_MAX_MM)
    # 蹭地脚全程贴地（它是**蹭**，不是抬）
    skid_low = [samples[f]["low"][SKID_FOOT] for f in range(TOTAL + 1)]
    res["skid_foot_low_min_mm"] = round(min(skid_low) * 1000.0, 2)
    res["skid_foot_low_max_mm"] = round(max(skid_low) * 1000.0, 2)
    res["skid_foot_planted_ok"] = bool(
        -2.0 <= min(skid_low) * 1000.0 and max(skid_low) * 1000.0 <= 8.0)
    # 迈步段里"被推"的读感：骨盆**先走**、迈步脚**后到**
    res["body_shift_at_off_mm"] = round(body_shift(STEP_OFF) * 1000.0, 1)
    res["body_shift_at_plant_mm"] = round(body_shift(STEP_PLANT) * 1000.0, 1)
    res["body_shift_end_mm"] = round(body_shift(TOTAL) * 1000.0, 1)
    res["body_shift_lead_ok"] = bool(
        abs(body_shift(STEP_PLANT)) >= 0.5 * BODY_BACK_M)

    # ---- (e) 末帧口径：躯干/臂**逐位回零位形状** + 世界位置（加整体位移后）达标
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()
    end_world, end_world_bone = 0.0, None
    end_per_bone = {}
    for name, ref in ZERO_WORLD.items():
        if _is_leg(name) or name not in samples[-1]:
            continue                     # 腿在新站位 ⟹ 不与零位比世界位置
        want = Vector(ref) + Vector((0.0, body_shift(TOTAL), 0.0))
        gap = (Vector(samples[-1][name]) - want).length * 1000.0
        if gap > 0.05:
            end_per_bone[name] = round(gap, 3)
        if gap > end_world:
            end_world, end_world_bone = gap, name
    res["end_world_pose_mm"] = round(end_world, 4)
    res["end_world_pose_bone"] = end_world_bone
    res["end_world_per_bone_mm"] = dict(sorted(end_per_bone.items(),
                                               key=lambda kv: -kv[1])[:12])
    # ★ 躯干 + 臂的**欧拉**是否逐位等于零位
    end_euler_max, end_euler_bone = 0.0, None
    for name, ref in ZERO.items():
        if name.startswith("@") or _is_leg(name):
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
    # ★ 末帧站立：两脚都贴地，且严格站在目标站位上
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
        and all(-2.0 <= samples[TOTAL]["low"][s] * 1000.0 <= 6.0
                for s in SIDES))
    # 末 2 帧不许瞬停
    last2 = 0.0
    for index in range(len(samples) - 2, len(samples)):
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            last2 = max(last2, max(abs(x - y) for x, y in zip(a, b)))
    res["end_last2_deg"] = round(last2, 4)
    # ★ `press ≡ 0` 短路的**作用域证明**
    expect = sum(1 for f in range(1, TOTAL + 1) if press(f) <= 1e-12)
    res["zero_shortcut_frames"] = _ZERO_SHORTCUT[0]
    res["zero_shortcut_expect"] = expect
    res["zero_shortcut_ok"] = bool(_ZERO_SHORTCUT[0] == expect
                                   and press(IMPACT) > 1e-12)
    # ★ 滚转口径**只对臂骨**（腿在新站位，其世界基本就不同）
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
    if os.environ.get("D08_DIAG"):
        diag = {}
        for name in END_ROLL_BONES:
            if name not in ZERO_BASIS:
                continue
            now_q = arm.pose.bones[name].matrix.to_3x3().to_quaternion().normalized()
            dir_now = Vector(A.bone_direction(arm, name)).normalized()
            turn = ZERO_DIR[name].rotation_difference(dir_now)
            ref = Quaternion(ZERO_BASIS[name])
            ref2 = (turn @ ref).normalized()
            if now_q.dot(ref2) < 0.0:
                ref2.negate()

            def _ang(a, b):
                return math.degrees(2.0 * math.acos(
                    max(-1.0, min(1.0, abs(a.dot(b))))))
            diag[name] = {
                "now_vs_ref2_deg": round(_ang(now_q, ref2), 5),
                "now_vs_zerobasis_deg": round(_ang(now_q, ref), 5),
                "dir_vs_zerodir_deg": round(math.degrees(math.acos(max(
                    -1.0, min(1.0, dir_now.dot(ZERO_DIR[name]))))), 5),
                "turn_deg": round(math.degrees(turn.angle), 5),
                "weight_TOTAL": round(_roll_weight(TOTAL), 6),
            }
        res["diag"] = diag
    res["hit_heavy_recover_ok"] = bool(
        end_world <= HIT_END_MAX_MM and last2 <= HIT_LAST2_MAX_DEG
        and worst_roll <= HIT_ROLL_MAX_DEG)

    # ---- 穿模
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [IMPACT, HOLD_END, STEP_OFF, STEP_PLANT, TOTAL]))
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

    # ---- 可达性（臂 = 拳目标；腿 = 踝目标 —— 本支腿目标会动，必须单独盯）
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

    # ---- 膝角被动吸收（本支上限 12°：迈步必然屈膝）
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

    # ---- 像素换算复核（D03 教训 3：1 mm ≈ 0.556 px）
    res["zero_fist_mm"] = {s: [round(v * 1000.0, 1) for v in IDLE_FIST[s]]
                           for s in SIDES}
    res["impact_fist_mm"] = {s: [round(v * 1000.0, 1)
                                 for v in per[IMPACT]["fist"][s]]
                             for s in SIDES}
    res["px_per_mm"] = 0.556
    res["head_fwd_px"] = round(head_fwd * 0.556, 2)
    res["body_shift_px"] = round(body_shift(TOTAL) * 1000.0 * 0.556, 2)
    res["step_back_px"] = round(res["step_axis_mm"][STEP_FOOT] * 0.556, 2)

    # ---- 剪影 / aspect：只报不判
    sil = P.silhouette(arm, "d08")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    if os.environ.get("D08_TRACE"):
        res["trace"] = {str(f): {
            "press": round(press(f), 4),
            "body_shift": round(body_shift(f) * 1000.0, 1),
            "stepL": round(step_y("L", f) * 1000.0, 1),
            "stepR": round(step_y("R", f) * 1000.0, 1),
            "liftL": round(step_lift("L", f) * 1000.0, 1),
            "pitch": round(per[f]["chest_pitch_deg"], 3),
            "head_fwd": round((zero["head_y"] - per[f]["head_y"]) * 1000.0, 1),
            "lowL": round(samples[f]["low"]["L"] * 1000.0, 2),
            "lowR": round(samples[f]["low"]["R"] * 1000.0, 2),
        } for f in range(0, TOTAL + 1)}

    # ---- ★ 临时诊断（D08_SOLE）：区分"脚朝向没回 rest"与"鞋底几何本身偏"
    if os.environ.get("D08_SOLE"):
        depsgraph = bpy.context.evaluated_depsgraph_get()

        def _lowest_of(objects):
            best = None
            for obj in objects:
                ev = obj.evaluated_get(depsgraph)
                me = ev.to_mesh()
                mat = ev.matrix_world
                for v in me.vertices:
                    p = mat @ v.co
                    if best is None or p.z < best[2]:
                        best = (p.x, p.y, p.z, obj.name)
                ev.to_mesh_clear()
            return best

        probe = {}
        for frame in [0, 4, 8, 20, 26, 29, 34, 42]:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            item = {}
            for side in SIDES:
                parts = {}
                for nm in A.FOOT_MESHES[side]:
                    if nm in bpy.data.objects:
                        lp = _lowest_of([bpy.data.objects[nm]])
                        parts[nm] = [round(v * 1000.0, 2) for v in lp[:3]] + [lp[3]]
                whole = _lowest_of([bpy.data.objects[nm]
                                    for nm in A.FOOT_MESHES[side]
                                    if nm in bpy.data.objects])
                item[side] = {
                    "foot_z_mm": round(A.bone_world(arm, "foot." + side, "head").z * 1000.0, 2),
                    "knee_y_mm": round(A.bone_world(arm, "shin." + side, "head").y * 1000.0, 2),
                    "knee_z_mm": round(A.bone_world(arm, "shin." + side, "head").z * 1000.0, 2),
                    "low_whole": [round(v * 1000.0, 2) for v in whole[:3]] + [whole[3]],
                    "by_part": parts,
                }
            item["low_split_mm"] = {s: round(samples[frame]["low"][s] * 1000.0, 2)
                                    for s in SIDES}
            probe[str(frame)] = item
        res["sole_probe"] = probe
    return res


def _is_leg(name):
    base = name.split(".tail")[0]
    return base.split(".")[0] in ("thigh", "shin", "foot", "toe")


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
        print("D08_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}

    UE.ROLL_STEP_DEG = _env_f("D08_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D08_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D08_YWEIGHT", 0.0)

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

    zrow = _hit_frame_metrics(arm)
    A.report("D08_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "impact": IMPACT, "hold_end": HOLD_END, "hit_hold": HIT_HOLD,
        "step_off": STEP_OFF, "step_plant": STEP_PLANT, "skid_end": SKID_END,
        "recover_end": RECOVER_END, "cancel": CANCEL,
        "segments": 3, "hit_points": 0,
        "root_motion_m": [0.0, round(BODY_MOVE_M, 4)],
        "force_direction": "背面（力把上身往 −Y 身前折）",
        "step_foot": STEP_FOOT, "skid_foot": SKID_FOOT,
        "step_plan": "§2 方案 A：迈步脚 = 零位前脚 L（受力同向侧）",
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
        "step_back_m": STEP_BACK_M, "step_move_m": STEP_MOVE_M,
        "step_source": "A03 Walk_F 实测 stride_m 0.3871",
        "body_move_m": BODY_MOVE_M, "push_mm": PUSH_M * 1000.0,
        "skid_m": SKID_M, "skid_move_m": SKID_MOVE_M,
        "lift_peak_mm": LIFT_PEAK * 1000.0,
        "rel_step_mm": round((0.170 + STEP_BACK_M - BODY_BACK_M) * 1000.0, 1),
        "rel_skid_mm": round((0.140 + SKID_M - BODY_BACK_M) * 1000.0, 1),
        "hit_side_mm": HIT_SIDE_MM,
        "hit_fist_offset_mm": [HIT_OUT_MM, HIT_BACKF_MM, HIT_DOWN_MM],
        "torso_hit_deg": TORSO_HIT, "torso_yaw_deg": TORSO_YAW,
        "pz_keys_mm": [list(k) for k in PZ_KEYS_MM],
        "elbow_hit_delta": [_EH_X, _EH_Y, _EH_Z],
        "pitch_gate_deg": [HIT_PITCH_MIN_DEG, HIT_PITCH_MAX_DEG],
        "head_fwd_gate_mm": [HIT_HEAD_FWD_MIN_MM, HIT_HEAD_FWD_MAX_MM],
        "lead_gamma": LEAD_GAMMA, "lead_bones": list(LEAD_BONES),
        "roll_return": ROLL_RETURN, "roll_weight_mode": ROLL_WEIGHT_MODE,
        "note": ("D08 背面重受击：零位 = Idle_01 落盘帧 0；升 4 / 硬直 4 / 降 24；"
                 "大幅**前折**（chest 俯仰 −10.0~−5.0°）+ 头前甩 100~175 mm；"
                 "★ **迈 1 步**（迈步脚 L 世界前移 0.387 m = A03 实测步长，带离地弧；"
                 "蹭地脚 R 只前蹭 0.14 m ≤ 迈步脚一半）；骨盆被推走 0.25 m（登记 "
                 "root_motion 为负）；拳被往前/外带开但保持防御形状；末帧躯干+臂逐位"
                 "回零位**形状**、脚站**新站位**"),
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
    # ★ 尾部**不钉 `dict(ZERO)`**（D03 教训 2）：末帧输入恒为"零位形状 + 新站位"，
    #    由同一组解算器逐帧解出 ⟹ 欧拉路径连续。

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "防御与受击",
        "note": ("背面重受击：大幅前折 + 头前甩 + **迈 1 步**（迈步脚 L 世界前移 "
                 "0.387 m 带离地弧、蹭地脚 R 只前蹭）；骨盆被推走 0.25 m（root_motion "
                 "为负）；拳被往前/外带开但双臂保持防御形状；末帧躯干+臂逐位回零位"
                 "形状、脚站新站位"),
        "antic_frame": 0,
        "hit_frame": IMPACT,
        "cancel_frame": CANCEL,
        "stagger_end_frame": HOLD_END,
        "hitstop_frames": HIT_HOLD,
        "hit_points": 0,
        "root_motion_m": [0.0, round(BODY_MOVE_M, 4)],
        "hit_point_m": None,
        "step_back_m": round(STEP_BACK_M, 4),
        "start_pose_ref": "Idle_01 帧 0（战斗待机）",
        "end_pose_ref": "Idle_01 帧 0 的**姿态形状** + 整体前移 0.250 m（新站位）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "IMPACT": IMPACT, "HOLD_END": HOLD_END,
                           "STEP_OFF": STEP_OFF, "STEP_PLANT": STEP_PLANT,
                           "CANCEL": CANCEL, "END": TOTAL})
    A.set_hitstop(action, IMPACT, HOLD_END)

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # ★ foot_probe 置空：`no_foot_slide`（≤3 mm）在本支是**错的口径**（脚本来就要动），
    #   换成 step_back_ok / foot_lift_ok / step_order_ok，见 hit_assertions。
    report = A.run_common_assertions(samples, meta, foot_probe=())
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
    A.report("D08_REPORT", report)

    if not SKIP_RENDER:
        # ★ 计划 §4：f0 / 命中 / 停顿中 / 起蹬 / 迈步中 / 落地 / 末帧
        #   ★ 比计划多出 **f6**（停顿平台中部）与 **f34**（CANCEL，"落定"的像素级证据）。
        frames = [0, IMPACT, 6, 11, 17, STEP_PLANT, CANCEL, TOTAL]
        A.render_pose_sheet(arm, action, frames, "hitheavyb",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D08_DONE failed=%s" % report["failed"])
    print("D08_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D08_FAILURE " + traceback.format_exc())
