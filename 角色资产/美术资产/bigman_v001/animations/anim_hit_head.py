"""anim_hit_head —— D09 `Hit_Head` 头部受击。

清单原文：「对应头部命中，头颈后甩」。

★★ 本支与 D05~D08 **不是一个族**（计划 §1）：
   那四支是「**整躯干**受力」（骨盆被推、躯干折、迈步），
   本支是「**局部**受力」—— 躯干基本不动，只有 `neck` + `head` 动。
   ⟹ `body_shift` / `step_y` / `step_lift` / `sole_lift` / 迈步时间表
      **全部不适用**，本支一律删掉（腿只做"钉在零位踝"的常量 IK）。

方向符号（★ 与 D08 全反）：
    受力 = **头部**（力把头顶往 +Y 身后甩）。所以
      · `head_pitch` Δ = **正**（后仰），两界都取正：Δ ∈ [+14.0, +28.0]
      · `head_back_mm = (per[IMPACT].head_y − zero.head_y) × 1000` ∈ [+50, +180]
      · 骨盆位移 = **0**（`root_motion_m = [0, 0]`）
      · 侧视像素符号 `SIDE_SIGN = +1`（头往 +Y 身后 = 图像**右**移）
    ★ 世界俯仰口径（D08 立、本支沿用）：`pitch = atan2(dir.y, dir.z)`，
      +Y = 身后 ⟹ **后仰为正、前屈为负**。

本支唯一的真风险（计划 §2）：**"头颈后甩"不能被读成"抬头看天"或"点头"**。
    后甩（whiplash）= 快、有惯性、带过冲、末端抖一下就稳。三种失败读法：
      · 读成"抬头看天"：甩角太小 + 回落太慢 ⟹ 头只是朝天看了一眼；
      · 读成"点头"：符号反了（本支 `rx < 0` = 后仰，写成 `rx > 0` 就成点头）；
      · 读成"脖子断了"：甩角过大 + 颈椎穿模。
    做法：`neck` 承担大头（1.0）、`head` 只补 `0.35`（分工比 1 : 0.35）；
    甩到峰值后**反向过冲 8~12%**（惯性）再回落，末尾 3~4 帧微抖后归零；
    上界由 `no_face_clip_ok` + `head_pitch` 上界**两条一起**钉住。

继承（逐条照抄，别重写）：
    · 骨架 / 零位加载 / `_ZERO_SHORTCUT` / `press`（升 3 / 硬直 3 / 降 20）
      / `_roll_return` 滚-瞄交替 2 趟 / `end_torso_ok` / `zero_shortcut_ok`
    · D05 三条修正：`arm_seat_tip()` / `elbow_hit()` 乘标量 / `KNEE_DIR[side]`
    · D07 教训 2：量零位前必须 `arm.animation_data.action = None`
    · D07 教训 3：`_roll_return` 必须"滚一趟 → 重瞄一趟"交替、末趟收在"瞄"上

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_hit_head.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D09_TRACE=1    逐帧打印 press / whip / 头俯仰 / 头顶位移（调参用）
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

NAME = "Hit_Head"
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
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D08 同源）。"""
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
# ★ 计划 §3：`press` 照抄 D08 的机器，参数改为 **升 3 / 硬直 3 / 降 20**。
TOTAL = _env_i("D09_TOTAL", 34)          # 0.567 s @60fps
IMPACT = _env_i("D09_IMPACT", 3)         # 命中峰（上升沿 3 帧）
HIT_HOLD = _env_i("D09_HOLD", 3)         # 小硬直平台 3 帧
HOLD_END = IMPACT + HIT_HOLD             # 6
REBOUND = _env_i("D09_REBOUND", 18)      # 反向过冲峰（惯性）
DUMP_END = _env_i("D09_DUMP", 22)        # 过冲之后的第一回落峰
SHAKE_END = _env_i("D09_SHAKE", 25)      # 微抖峰
RECOVER_END = _env_i("D09_RECOVER", 26)  # 驱动标量回到 0 的帧（降 20 帧）
CANCEL = _env_i("D09_CANCEL", 30)
#   ★ 为什么回落取 20 帧：`no_teleport`（≤25°/帧）是**物理下界**，本支甩角 ~20°
#     若在 5 帧内回完 ⟹ 单帧 4°+ 且末段速度不连续；20 帧给足惯性感，
#     且满足"升 ≤4 / 降 ≥18"的不对称要求（"启动略慢、收招不能瞬停"的受击版：
#     命中快、回落慢）。

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
GROUND_MIN_MM, GROUND_MAX_MM = -2.0, 6.0
REACH_MAX_RATIO = 0.995
# ---- ★★ 本支头号判据（计划 §1）：`head` 骨的世界俯仰，**两个界都取正**
# ★ 世界俯仰 `head_pitch = atan2(head_dir.y, head_dir.z)`，+Y = 身后 ⟹ **后仰为正**。
#   本支是**头部受击 ⟹ 后甩** ⟹ Δ 必须为**正**。两界都取正，**不许用 abs()**。
HEAD_PITCH_MIN_DEG = _env_f("D09_PITCH_MIN", 14.0)
HEAD_PITCH_MAX_DEG = _env_f("D09_PITCH_MAX", 28.0)
# ★ 反向过冲（惯性）：头往前弹回一截，但**必须小于峰值**（计划 §2「不能大过峰值」）。
HEAD_REBOUND_MIN_DEG = _env_f("D09_REB_MIN", -6.0)
HEAD_REBOUND_MAX_DEG = _env_f("D09_REB_MAX", -0.5)
OVERSHOOT_MIN = _env_f("D09_OVS_MIN", 0.08)
OVERSHOOT_MAX = _env_f("D09_OVS_MAX", 0.12)
# ★ 头顶位移口径（照 D08 的 `head_fwd_mm`，符号取正 = 往身后）
HEAD_BACK_MIN_MM = _env_f("D09_HEAD_MIN", 50.0)
HEAD_BACK_MAX_MM = _env_f("D09_HEAD_MAX", 180.0)
# ★ 颈 / 头 分工比（计划 §2：neck 承担大头、head 只补一点）
NECK_HEAD_RATIO = _env_f("D09_RATIO", 0.35)
NECK_HEAD_RATIO_TOL = _env_f("D09_RATIO_TOL", 0.06)
# ★ 躯干必须"基本不动"（计划 §1：躯干清 0）
TORSO_STILL_MAX_DEG = _env_f("D09_TORSO_STILL", 0.05)
TORSO_PITCH_MAX_DEG = _env_f("D09_TORSO_PITCH", 0.5)
# ★ 末段必须归零并稳住
SETTLE_MAX_DEG = _env_f("D09_SETTLE", 0.05)
SETTLE_STEP_MAX_DEG = _env_f("D09_SETTLE_STEP", 0.02)
# ★ 头颈领跑（D06/D07/D08 连续三支的遗留，本支终于成为主设计）
LEAD_F1_RATIO_MIN = _env_f("D09_LEAD_MIN", 0.20)
LEAD_F1_RATIO_MAX = _env_f("D09_LEAD_MAX", 0.45)
# ★ 拳架不许动（本支双臂保持防御形状，靠肩的轻微耸起表达传导）
FIST_HELD_MAX_MM = _env_f("D09_FIST_MAX", 3.0)
# ★ 站姿类硬要求：脚不许滑动（≤3 mm）
FOOT_SLIDE_MAX_MM = _env_f("D09_SLIDE", 3.0)
STANCE_SOLE_MAX_MM = _env_f("D09_SOLE", 6.0)

# ---- 节奏不对称（升 ≤4 帧、降 ≥18 帧）
HIT_RISE_MAX_FRAMES = _env_f("D09_RISE_MAX", 4.0)
HIT_FALL_MIN_FRAMES = _env_f("D09_FALL_MIN", 18.0)
RISE_GAMMA = _env_f("D09_RISE_GAMMA", 1.0)
# ---- 打击停顿（≥3 帧）
HITSTOP_MIN_FRAMES = _env_f("D09_HITSTOP_MIN", 3.0)
# ---- 末帧口径（四口径；本支**回原位** ⟹ 世界位置不加整体位移）
HIT_END_MAX_MM = _env_f("D09_END_MAX", 0.5)
HIT_LAST2_MAX_DEG = _env_f("D09_LAST2", 0.5)
HIT_ROLL_MAX_DEG = _env_f("D09_ROLL_MAX", 0.5)
ROLL_RETURN = _env_f("D09_ROLL_RETURN", 1.0) >= 0.5
ROLL_WEIGHT_MODE = os.environ.get("D09_ROLL_WEIGHT", "tail").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D09_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split(",")
    if item)
ROLL_ITER = max(1, int(os.environ.get("D09_ROLL_ITER", "2")))
END_ROLL_BONES = ARM_ROLL_BONES = ("upperarm.L", "forearm.L", "hand.L",
                                   "upperarm.R", "forearm.R", "hand.R")
# ---- 穿模
CLIP_MAX_MM = _env_f("D09_CLIP_MAX", 0.0)
CLIP_EVERY = int(os.environ.get("D09_CLIP_EVERY", 4))
# ---- 零位守卫
IDLE_MATCH_TOL_DEG = _env_f("D09_IDLE_MATCH", 1.0e-3)
IDLE_GEOM_POS_MAX_MM = _env_f("D09_IDLE_POS", 0.01)
IDLE_GEOM_DIR_MAX_DEG = _env_f("D09_IDLE_DIR", 0.05)

# =============================================================== 驱动标量
# ★★ 为什么需要**两条**标量：
#   `press`  是**单调单脉冲**（升 3 / 停 3 / 降 20）⟹ 只能当"节奏时钟"
#            与 `zero_shortcut` 的作用域。它的"降"必须是单调的，
#            否则 `press_rise/fall` 的节奏判据会被过冲段污染。
#   `whip`   是**真正驱动头颈**的标量：命中峰 1.0 → 回落 → **反向过冲 −0.10**
#            （= 头往前弹回 10% 峰值，惯性）→ 微抖 +0.014 / −0.005 → 0。
WHIP_KEYS = ((0, 0.0), (1, 0.30), (2, 0.68), (IMPACT, 1.0), (HOLD_END, 1.0),
             (12, 0.22), (16, -0.070), (REBOUND, -0.100), (DUMP_END, 0.014),
             (SHAKE_END, -0.005), (RECOVER_END, 0.0), (TOTAL, 0.0))


def press(frame):
    """节奏标量 ∈ [0, 1]：**升 3 / 峰停 3 / 降 20** 的单脉冲。

    峰值帧（press ≡ 1）由同一组参数解出 ⟹ 姿态逐位相同（硬直是真的"僵住"）。
    """
    keys = [(0, 0.0)]
    for step in range(1, IMPACT):
        keys.append((step, (step / float(IMPACT)) ** RISE_GAMMA))
    keys += [(IMPACT, 1.0), (HOLD_END, 1.0), (RECOVER_END, 0.0), (TOTAL, 0.0)]
    return UE.pwl(tuple(keys), float(frame), 0.0)


def whip(frame):
    """★ 头颈驱动标量：1.0 = 甩到峰；负 = **反向过冲**（惯性）；末段微抖后归零。"""
    return UE.pwl(WHIP_KEYS, float(frame), 0.0)


def still(frame):
    """`press ≡ 0` **且** `whip ≡ 0` 的帧（末端静止段）⟹ 走零位短路。"""
    return press(frame) <= 1e-12 and whip(frame) <= 1e-12


# =============================================================== 受击幅度
# ★★ 幅度标定（同一把尺子，不要拍脑袋）：
#   `neck` 长 120 mm（`probe_axes`：neck 绕 X 转 15° 使 tail 走 31.33 mm ⟹ R=120.0），
#   `head` 长 230 mm（同表：60.04 mm ⟹ R=230.0），两者 rest 朝向都是 **+Z**。
#   ⟹ 头顶（head.tail）相对颈根的后移 ≈ 120·sin|neck| + 230·sin|neck+head|。
#   取 neck −19° / head −6.65°（比 1 : 0.35）⟹
#     Δhead_pitch ≈ −(−19 −6.65) = **+25.64°**（后仰）；
#     头顶后移 ≈ 120·sin19 + 230·sin25.64 = 39.06 + 99.48 = **138.5 mm**（实测 141.06）。
#   ★ 为什么取 −19（而不是先试的 −15 = 20.25°）：
#     清单「动作幅度大夸张有力」 ⟹ 往带内**上半段**靠，让"被打头"读得更狠。
#     `D09_NECK=-19 D09_HEAD=-6.65` 实测：`clip_max_mm = 0.0`（穿模守住，正是
#     计划 §2「上界由 `no_face_clip_ok` + `head_pitch_max` 两条一起钉住」的验证）、
#     `head_pitch = 25.64°`（< 28 上界）、`head_back = 141.06 mm`（< 180 上界）。
#   ⟹ 两者都落在判据带内（俯仰 [14,28]、位移 [50,180]），且像素下界 8 px 有 3× 余量。
NECK_WHIP = _env_f("D09_NECK", -19.0)      # 颈根带动（主承载）
HEAD_WHIP = _env_f("D09_HEAD", -6.65)      # 头相对颈再仰（= 0.35 × 颈，计划 §2 分工比）
SHOULDER_WHIP = _env_f("D09_SHOULDER", 2.0)   # 保护性耸肩（力量传导可见，量级 2°）
# ★ 打脸常带一点偏头（计划 §2「只报到量，不设无依据的界」）
NECK_YAW = _env_f("D09_YAW_NECK", 1.2)
HEAD_YAW = _env_f("D09_YAW_HEAD", 1.8)

# 骨 -> 幅度（躯干**清 0**：骨盆 / 脊柱全为 0，计划 §1 硬要求）
AMP = {"pelvis": 0.0, "spine_01": 0.0, "spine_02": 0.0, "chest": 0.0,
       "neck": NECK_WHIP, "head": HEAD_WHIP,
       "shoulder.L": SHOULDER_WHIP, "shoulder.R": SHOULDER_WHIP}
YAW = {"pelvis": 0.0, "spine_01": 0.0, "spine_02": 0.0, "chest": 0.0,
       "neck": NECK_YAW, "head": HEAD_YAW,
       "shoulder.L": 0.0, "shoulder.R": 0.0}
# ★ 只有头颈（+ 肩）吃 `whip`；其余吃 `press`（但幅度为 0 ⟹ 恒等于零位）
WHIP_BONES = ("neck", "head", "shoulder.L", "shoulder.R")
TORSO_BONES = ("pelvis", "spine_01", "spine_02", "chest")

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
    """★★ 躯干**逐位不动**：只有 `neck` / `head` / `shoulder.*` 吃 `whip`。

    `@loc` 恒为 `Z_SEAM − 0.900`（= 零位骨盆局部 y）⟹ 骨盆世界位置逐位等于零位。
    """
    w = whip(frame)
    p = press(frame)
    out = {}
    for name in TARGET_BONES:
        zero = ZERO[name]
        scalar = w if name in WHIP_BONES else p
        out[name] = (zero[0] + AMP.get(name, 0.0) * scalar,
                     zero[1] + YAW.get(name, 0.0) * scalar,
                     zero[2])
    out["@loc"] = {"pelvis": A.wloc(0.0, 0.0, Z_SEAM - 0.900)}
    return out


def ankle_target(side, frame):
    """腿目标 = **常量**（零位踝）。本支无步态、无位移、无蒙皮补偿（计划 §1）。"""
    return Vector(ANKLE_0[side])


def fist_target(side, frame):
    """拳世界目标 = `Idle_01@0` 拳位（**不加任何偏移**）：本支双臂保持防御形状。

    ★ D08 的 `body_shift` 项在本支恒为 0（骨盆位移 = 0），故直接取零位拳位。
    """
    return Vector(IDLE_FIST[side])


def elbow_hit(side, frame):
    """肘偏好方向 = 零位肘向（本支拳头不动 ⟹ 肘提示不参与，恒等返回）。"""
    return tuple(IDLE_ELBOW_DIR[side])


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
    #   写进欧拉（D07 实测残差 1.9e-05°，而 `end_torso_ok` 的界是 ≤1e-6°）。
    #   ★ 本支腿本就钉在零位 ⟹ 腿也一起短路（D08 腿站新站位，故不走短路）。
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
    return 1.0 - whip(frame)


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
def _hit_frame_metrics(arm):
    lo, hi = PD.head_box()
    fists = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    chest_dir = Vector(A.bone_direction(arm, "chest"))
    head_dir = Vector(A.bone_direction(arm, "head"))
    neck_dir = Vector(A.bone_direction(arm, "neck"))
    return {
        "box_lo": Vector(lo), "box_hi": Vector(hi),
        "fist": fists,
        "fist_spread_mm": (abs(fists["L"].x) + abs(fists["R"].x)) * 1000.0,
        "chest_pitch_deg": math.degrees(math.atan2(chest_dir.y, chest_dir.z)),
        "head_pitch_deg": math.degrees(math.atan2(head_dir.y, head_dir.z)),
        "neck_pitch_deg": math.degrees(math.atan2(neck_dir.y, neck_dir.z)),
        "neck_y": Vector(A.bone_world(arm, "neck", "head")).y,
        "head_y": Vector(A.bone_world(arm, "head", "tail")).y,
        "head_z": Vector(A.bone_world(arm, "head", "tail")).z,
        "shoulder_z": Vector(A.bone_world(arm, "upperarm.L", "head")).z,
        "pelvis_y": Vector(A.bone_world(arm, "pelvis", "head")).y,
    }


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
    zero = _hit_frame_metrics(arm)
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    per = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _hit_frame_metrics(arm)

    hp = {f: per[f]["head_pitch_deg"] - zero["head_pitch_deg"] for f in per}

    # ---- ★★ (a) `head_pitch`：**两个界都取正**（后仰），且必须能抓住"方向做反"
    res["head_pitch_zero_deg"] = round(zero["head_pitch_deg"], 4)
    res["head_pitch_impact_deg"] = round(hp[IMPACT], 4)
    res["head_pitch_peak_deg"] = round(max(hp.values()), 4)
    res["head_pitch_rebound_deg"] = round(min(hp.values()), 4)
    res["head_pitch_peak_at"] = max(hp, key=lambda f: hp[f])
    res["head_pitch_rebound_at"] = min(hp, key=lambda f: hp[f])
    res["head_pitch_at_impact_ok"] = bool(
        HEAD_PITCH_MIN_DEG <= hp[IMPACT] <= HEAD_PITCH_MAX_DEG)
    res["head_pitch_delta_ok"] = bool(
        HEAD_PITCH_MIN_DEG <= max(hp.values()) <= HEAD_PITCH_MAX_DEG
        and HEAD_REBOUND_MIN_DEG <= min(hp.values()) <= HEAD_REBOUND_MAX_DEG)
    # ★★ 方向守卫：把 Δ 取反（= 前屈 / 点头）后必须**越界**。写成 abs() 则立刻红。
    res["head_pitch_direction_can_fail_ok"] = bool(
        not (HEAD_PITCH_MIN_DEG <= -hp[IMPACT] <= HEAD_PITCH_MAX_DEG))

    # ---- (a2) 头顶**位移**（既报量，也过双界）—— 与俯仰互为独立证据
    head_back = (per[IMPACT]["head_y"] - zero["head_y"]) * 1000.0
    res["head_back_mm"] = round(head_back, 2)
    res["head_back_max_mm"] = round(
        max((per[f]["head_y"] - zero["head_y"]) * 1000.0 for f in per), 2)
    res["head_back_min_mm"] = round(
        min((per[f]["head_y"] - zero["head_y"]) * 1000.0 for f in per), 2)
    res["neck_back_mm"] = round(
        (per[IMPACT]["neck_y"] - zero["neck_y"]) * 1000.0, 2)
    res["head_rise_mm"] = round(
        (per[IMPACT]["head_z"] - zero["head_z"]) * 1000.0, 2)
    res["head_back_ok"] = bool(HEAD_BACK_MIN_MM <= head_back
                               <= HEAD_BACK_MAX_MM)
    res["head_back_direction_can_fail_ok"] = bool(
        not (HEAD_BACK_MIN_MM <= -head_back <= HEAD_BACK_MAX_MM))
    res["hit_head_ok"] = bool(res["head_pitch_at_impact_ok"]
                              and res["head_back_ok"])

    # ---- ★★ (b) 颈 / 头 分工比（计划 §2：1 : 0.35，防止全堆在一根骨上）
    zero_arm = {n: ZERO[n] for n in ZERO if not n.startswith("@")}
    neck_rx = samples[IMPACT]["euler"].get("neck", (0.0, 0.0, 0.0))[0] \
        - zero_arm["neck"][0]
    head_rx = samples[IMPACT]["euler"].get("head", (0.0, 0.0, 0.0))[0] \
        - zero_arm["head"][0]
    ratio = (head_rx / neck_rx) if abs(neck_rx) > 1e-9 else None
    res["neck_delta_rx_deg"] = round(neck_rx, 4)
    res["head_delta_rx_deg"] = round(head_rx, 4)
    res["neck_head_ratio"] = None if ratio is None else round(ratio, 4)
    res["neck_head_ratio_ok"] = bool(
        ratio is not None and abs(neck_rx) > 1.0
        and abs(neck_head_rx_sign(neck_rx, head_rx)) > 0.5
        and abs(ratio - NECK_HEAD_RATIO) <= NECK_HEAD_RATIO_TOL)

    # ---- ★★ (c) 躯干**必须基本不动**（计划 §1「躯干清 0」）
    torso_delta, torso_delta_bone = 0.0, None
    for name in TORSO_BONES:
        got = samples[IMPACT]["euler"].get(name, (0.0, 0.0, 0.0))
        ref = zero_arm[name]
        gap = max(abs(_f32(a) - _f32(b)) for a, b in zip(got, ref))
        if gap > torso_delta:
            torso_delta, torso_delta_bone = gap, name
    res["torso_delta_deg"] = round(torso_delta, 6)
    res["torso_delta_bone"] = torso_delta_bone
    res["torso_pitch_delta_deg"] = round(
        per[IMPACT]["chest_pitch_deg"] - zero["chest_pitch_deg"], 4)
    res["pelvis_move_mm"] = round(
        abs(per[IMPACT]["pelvis_y"] - zero["pelvis_y"]) * 1000.0, 3)
    res["torso_still_ok"] = bool(
        torso_delta <= TORSO_STILL_MAX_DEG
        and abs(per[IMPACT]["chest_pitch_deg"] - zero["chest_pitch_deg"])
        <= TORSO_PITCH_MAX_DEG)
    # ★ 反向守卫：同一把尺子量"该动的"那一截（头颈），必须**远超**这个界
    #   ⟹ 证明 `torso_still_ok` 不是一个恒真的空判据。
    res["torso_still_can_fail_ok"] = bool(
        abs(hp[IMPACT]) > 10.0 * TORSO_STILL_MAX_DEG)

    # ---- ★★ (d) 反向过冲（惯性）：8~12% 峰值，且**必须小于峰值**
    peak = max(hp.values())
    rebound = min(hp.values())
    over_ratio = (abs(rebound) / peak) if abs(peak) > 1e-9 else None
    res["overshoot_ratio"] = None if over_ratio is None else round(over_ratio, 4)
    res["overshoot_ok"] = bool(
        over_ratio is not None
        and OVERSHOOT_MIN <= over_ratio <= OVERSHOOT_MAX
        and rebound < 0.0 < peak
        and abs(rebound) < peak)

    # ---- ★★ (e) 末段：微抖后归零并稳住
    tail_frames = list(range(RECOVER_END, TOTAL + 1))
    res["settle_max_deg"] = round(max(abs(hp[f]) for f in tail_frames), 5)
    last_steps = [abs(hp[f] - hp[f - 1]) for f in range(TOTAL - 2, TOTAL + 1)]
    res["settle_step_deg"] = round(max(last_steps), 5)
    shake = [round(hp[f], 4) for f in (DUMP_END, SHAKE_END, RECOVER_END)]
    res["shake_tail_deg"] = shake
    res["settle_ok"] = bool(
        res["settle_max_deg"] <= SETTLE_MAX_DEG
        and res["settle_step_deg"] <= SETTLE_STEP_MAX_DEG
        and abs(hp[REBOUND]) > 0.5)

    # ---- ★★ (f) 头颈领跑（D06/D07/D08 三支的遗留）
    torso_prog = abs(per[1]["chest_pitch_deg"] - zero["chest_pitch_deg"])
    ratio_f1 = (hp[1] / peak) if abs(peak) > 1e-9 else None
    res["lead_f1_pitch_deg"] = round(hp[1], 4)
    res["lead_f1_ratio"] = None if ratio_f1 is None else round(ratio_f1, 4)
    res["lead_torso_progress_deg"] = round(torso_prog, 5)
    res["lead_at_f1_ok"] = bool(
        ratio_f1 is not None and LEAD_F1_RATIO_MIN <= ratio_f1
        <= LEAD_F1_RATIO_MAX and torso_prog <= 0.01)
    res["lead_at_f1_can_fail_ok"] = bool(
        not (LEAD_F1_RATIO_MIN <= 0.0 <= LEAD_F1_RATIO_MAX))

    # ---- ★★ (g) 拳架不许动 / 肩的传导可见
    fist_dev, fist_dev_bone = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["fist"][s] - IDLE_FIST[s]).length * 1000.0
            if gap > fist_dev:
                fist_dev, fist_dev_bone = gap, (s, frame)
    res["fist_dev_mm"] = round(fist_dev, 3)
    res["fist_dev_at"] = fist_dev_bone
    res["fist_held_ok"] = bool(fist_dev <= FIST_HELD_MAX_MM)
    res["shoulder_rise_mm"] = round(
        (per[IMPACT]["shoulder_z"] - zero["shoulder_z"]) * 1000.0, 2)
    res["fist_spread_zero_mm"] = round(zero["fist_spread_mm"], 2)
    res["fist_spread_impact_mm"] = round(per[IMPACT]["fist_spread_mm"], 2)

    # ---- (h) 节奏不对称（升 ≤4 / 降 ≥18，量的是 `press` 单脉冲）
    risers = sum(1 for f in range(TOTAL) if press(f + 1) > press(f) + 1e-9)
    fallers = sum(1 for f in range(TOTAL) if press(f + 1) < press(f) - 1e-9)
    res["press_rise_frames"] = risers
    res["press_fall_frames"] = fallers
    res["hit_speed_ok"] = bool(risers <= HIT_RISE_MAX_FRAMES
                               and fallers >= HIT_FALL_MIN_FRAMES)
    res["press_at_f1"] = round(press(1), 4)
    res["whip_at_f1"] = round(whip(1), 4)

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

    # ---- (j) 站姿硬要求：脚不许滑动（恢复默认 foot_probe 口径）
    slide = {s: round(res.get("foot_travel_mm_toe." + s, 0.0), 2)
             for s in SIDES}
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
                                   and press(IMPACT) > 1e-12
                                   and whip(IMPACT) > 1e-12)
    # ★ 逐位回原位：末帧剪影应与 f0 **完全相同**（与 D08 相反：D08 不回原位）
    #   只比世界坐标量（探针骨骼/尾），"euler"/"low"/"frame" 不是向量。
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
    res["hit_head_recover_ok"] = bool(
        end_world <= HIT_END_MAX_MM and last2 <= HIT_LAST2_MAX_DEG
        and worst_roll <= HIT_ROLL_MAX_DEG)

    # ---- 穿模（"脖子断了"的硬上界）
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [IMPACT, HOLD_END, REBOUND, CANCEL, TOTAL]))
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

    # ---- 膝角被动吸收（本支腿钉住 ⟹ 应当几乎为 0）
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
    res["knee_passive_ok"] = bool(worst_knee <= 2.0)
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()

    # ---- 像素换算复核（D03 教训 3：1 mm ≈ 0.556 px）
    res["px_per_mm"] = 0.556
    res["head_back_px"] = round(head_back * 0.556, 2)
    res["head_pitch_px_equiv"] = round(20.0 * 0.556, 2)
    res["zero_fist_mm"] = {s: [round(v * 1000.0, 1) for v in IDLE_FIST[s]]
                           for s in SIDES}
    res["impact_fist_mm"] = {s: [round(v * 1000.0, 1)
                                 for v in per[IMPACT]["fist"][s]]
                             for s in SIDES}

    # ---- 剪影 / aspect：只报不判
    sil = P.silhouette(arm, "d09")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    if os.environ.get("D09_TRACE"):
        res["trace"] = {str(f): {
            "press": round(press(f), 4),
            "whip": round(whip(f), 4),
            "head_pitch": round(hp[f], 3),
            "neck_pitch": round(per[f]["neck_pitch_deg"]
                                - zero["neck_pitch_deg"], 3),
            "head_back": round((per[f]["head_y"] - zero["head_y"]) * 1000.0, 1),
            "shoulder_dz": round((per[f]["shoulder_z"] - zero["shoulder_z"])
                                 * 1000.0, 2),
            "lowL": round(samples[f]["low"]["L"] * 1000.0, 2),
            "lowR": round(samples[f]["low"]["R"] * 1000.0, 2),
        } for f in range(0, TOTAL + 1)}
    return res


def neck_head_rx_sign(neck_rx, head_rx):
    """颈 / 头必须**同号**（都后仰）；异号 = 一个后仰一个前屈 = "点头 + 缩脖子"。"""
    if abs(neck_rx) < 1e-9 or abs(head_rx) < 1e-9:
        return 0.0
    return 1.0 if (neck_rx > 0) == (head_rx > 0) else 0.0


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
        print("D09_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}

    UE.ROLL_STEP_DEG = _env_f("D09_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D09_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D09_YWEIGHT", 0.0)

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
    A.report("D09_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "impact": IMPACT, "hold_end": HOLD_END, "hit_hold": HIT_HOLD,
        "rebound": REBOUND, "dump_end": DUMP_END, "shake_end": SHAKE_END,
        "recover_end": RECOVER_END, "cancel": CANCEL,
        "segments": 3, "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "force_direction": "头部（力把头顶往 +Y 身后甩）",
        "leg_plan": "无步态：踝目标 = 零位常量，脚全程钉住",
        "zero_source": "Idle_01@%d（落盘 action，非重演）" % saved_info.get(
            "frame"),
        "zero_pose_src": saved_info,
        "zero_vs_idle_pose_euler_max_diff_deg": round(euler_diff, 6),
        "zero_vs_idle_pose_worst_bone": euler_bone,
        "zero_vs_idle_pose_geom_pos_mm": round(geom_pos, 6),
        "zero_vs_idle_pose_geom_dir_deg": round(geom_dir, 6),
        "zero_pelvis_z_mm": round(Z_SEAM * 1000.0, 3),
        "zero_head_pitch_deg": round(zrow["head_pitch_deg"], 4),
        "zero_neck_pitch_deg": round(zrow["neck_pitch_deg"], 4),
        "zero_fist_mm": {s: [round(v * 1000.0, 2) for v in IDLE_FIST[s]]
                         for s in SIDES},
        "zero_fist_spread_mm": round(zrow["fist_spread_mm"], 2),
        "zero_ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                          for s in SIDES},
        "zero_knee_dir": {s: [round(v, 4) for v in KNEE_DIR[s]] for s in SIDES},
        "bone_len_mm": {"neck": round(arm.pose.bones["neck"].length * 1000.0, 2),
                        "head": round(arm.pose.bones["head"].length * 1000.0, 2)},
        "neck_whip_deg": NECK_WHIP, "head_whip_deg": HEAD_WHIP,
        "head_whip_ratio": round(abs(HEAD_WHIP / NECK_WHIP), 4),
        "shoulder_whip_deg": SHOULDER_WHIP,
        "neck_yaw_deg": NECK_YAW, "head_yaw_deg": HEAD_YAW,
        "whip_keys": [list(k) for k in WHIP_KEYS],
        "head_pitch_gate_deg": [HEAD_PITCH_MIN_DEG, HEAD_PITCH_MAX_DEG],
        "head_rebound_gate_deg": [HEAD_REBOUND_MIN_DEG, HEAD_REBOUND_MAX_DEG],
        "head_back_gate_mm": [HEAD_BACK_MIN_MM, HEAD_BACK_MAX_MM],
        "overshoot_gate": [OVERSHOOT_MIN, OVERSHOOT_MAX],
        "note": ("D09 头部受击：零位 = Idle_01 落盘帧 0；升 3 / 硬直 3 / 降 20；"
                 "★ **局部受力** —— 躯干清 0（骨盆/脊柱逐位不动）、只 neck + head "
                 "后甩（分工比 1 : 0.35）；峰值后**反向过冲 8~12%**（惯性）再微抖"
                 "归零；腿无步态、脚全程钉住（no_foot_slide 回归默认口径）；"
                 "末帧**逐位回零位**（含位置）"),
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
        "note": ("头部受击：局部受力，躯干清 0、只头颈后甩（neck : head = 1 : 0.35），"
                 "峰值后反向过冲 8~12% 再微抖归零；腿无步态、脚全程钉住；"
                 "末帧逐位回零位（含位置）"),
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
    A.report("D09_REPORT", report)

    if not SKIP_RENDER:
        # ★ 计划 §4：f0 / 命中 / 停顿中 / 过冲峰 / 回落 / CANCEL / 末帧
        #   ★ 多出 f6（停顿平台末端）与 f12（回落中段）—— 像素探针要用。
        frames = [0, IMPACT, 5, HOLD_END, 12, REBOUND, DUMP_END, CANCEL, TOTAL]
        A.render_pose_sheet(arm, action, frames, "hithead",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D09_DONE failed=%s" % report["failed"])
    print("D09_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D09_FAILURE " + traceback.format_exc())
