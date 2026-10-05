"""anim_smash07 —— C07 `Ground_Smash` 地面砸击（C 族第七支，**一次性 + 原地**）。

=============================================================================
清单原文
=============================================================================
「双拳高举后砸地，攻击前蓄力明显，可配裂纹、震屏。」

=============================================================================
第 0 件 —— 形态选择
=============================================================================
读法：**站桩 → 双拳从护胸举起过顶（躯干后弓）→ 躯干猛烈前折 70°、
双拳砸到身前地面 → 4 帧完全硬停 → 单向减速收到「半蹲起势」**。

与 C06 的差异（清单 C07 计划 §1 原表）：

| 维度 | C06 `Throw`        | C07 `Ground_Smash`            |
|------|--------------------|-------------------------------|
| 接缝 | `Grab_Hold@120` 逐位 | **无上游** = `Idle_01@0` 逐位 |
| 位移 | 前冲 270 mm         | **0**（原地；骨盆只做 ±5 cm 的重心移动） |
| 难点 | 末端钉死 + 髋部发力   | **躯干开合 70°**（C06 的 ~3 倍） |
| 手部 | 位置逆解钉死抓取点    | **方向链**（高举→砸下）        |
| 顿感 | 躯干 8 骨冻结        | **14 骨全冻**（含 6 根手臂骨，见第 3 件） |

=============================================================================
第 1 件 —— ★ 收招门禁决定形态：收招是"单段减速"，末帧不回 Idle
=============================================================================
`decel_smooth_ok` 要求 `[RETURN_START, TOTAL]` 上**全骨逐帧步长最大值单调不增**
⟹ 收招段不许有任何过冲。因此收招 = 从冻结的命中姿，用**同一个 `q(frame)`
作仿射插值**，单向减速走到「半蹲起势」（双拳在膝前）。

结构保证：躯干/骨盆/手臂全部是 `X(frame) = base + (end − base) · q(frame)` 且
`q = 1 − (1−u)^POST_POW`（增量递减）⟹ 每帧步长 = |Δ| · Δq，而"全骨最大步长"
= maxᵢ|Δᵢ| · Δq = **常数 × Δq** ⟹ 单调不增，门禁**构造性成立**（C06 沉淀）。

代价：**末帧不是 `Idle_01@0`**，是"半蹲起势"。引擎侧混回 Idle 即可；
末帧姿态登记进 Action 自定义属性 `end_pose_deg`。

=============================================================================
第 2 件 —— 首帧 = `Idle_01@0`，逐位（`SEAM_TOL = 1e-6`）
=============================================================================
无上游接缝 ⟹ 首帧直接读 `Idle_01` Action 在 f0 的**真值**（全部 57 骨的
`rotation_euler` + `pelvis.location`），不做任何解算。`patch()` 把躯干/骨盆
轨道的 f0 回填成同一批值 ⟹ f1 起管线接管时不会跳变。

★ 为什么不用"跑一遍 `idle_pose()` 复现"：`Idle_01` 的腿是 `leg_ik`（平面解析）
解的，而本支的腿是 `leg_seat`（三维 IK）解的；两者**世界方向一致但欧拉滚转
不一定逐位一致**，逐位门禁会红。所以 f0 走真值、f1 起走管线。

=============================================================================
第 3 件 —— ★ 命停冻 14 骨（含 6 根手臂骨），这是 C06 教训的反向适用
=============================================================================
C06 教训 1：位置逆解（`arm_seat`）的抓握保持段**不能**把手冻进命停集，
否则骨盆在命停窗爬行时手会被"焊"在旧位置。

C07 **没有位置逆解** —— 手臂是**方向链**（`aim_bone_ref`，世界方向给死）。
方向链驱动下，冻结欧拉 = 冻结视觉，不存在"焊住"问题 ⟹ 恢复 C04 的
**14 骨全冻**（躯干 8 + 手臂 6）。这正是 C04 的适用条件。

=============================================================================
第 4 件 —— ★ 命停期"力量还在往前灌"（`hitstop_keeps_momentum_ok`）
=============================================================================
本支**无 Root Motion**，若命停窗内骨盆完全不动则 `hitstop_momentum_mm = 0`
（门禁要 > 10）。设计：命停窗 [HIT, HOLD_END] 内**旋转 14 骨逐位冻结**，
但骨盆**继续往前爬 14 mm**（`PELVIS_Y` 0.040 → 0.054 前移）——读作
"砸下去的力还在往地里压"。爬行量由清单 C06 教训 4 的同类机制给出。

=============================================================================
第 5 件 —— 开工前实测（`probe_c07_baseline.py` / `probe_c07_smash.py`）
=============================================================================
| 量 | 实测 | 门禁 | 余量 |
|---|---|---|---|
| 高举顶拳中点 z（pz 0.83） | 1998.8 mm | ≥ 1850 | +148.8 |
| 高举顶腿可达比（后弓 −8°） | 0.938 / 0.931 | < 0.995 | 松 |
| 砸下拳中点 z（pz 0.56, α=0°） | 297.5 mm | ≤ 320 | −22.5 |
| 砸下腿可达比 | 0.623 / 0.612 | < 0.995 | 很松 |
| 拳间距（spread 3°） | 355.4 mm | — | 两拳并列砸，不是"拍地" |

结论：**原地砸击在几何上完全可行**；举高靠手臂方向（不靠抬骨盆，
因为后弓时腿已达 0.94 可达比，骨盆再抬会截断 ⟹ 脚会滑）。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_smash07.py
    SKIP_RENDER=1 只跑门禁（迭代用）；C07_TRACE=1 打逐帧轨迹。
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402
import anim_run_stop as RS      # noqa: E402
import anim_jump_start as JS    # noqa: E402
import anim_grab04 as G4        # noqa: E402

NAME = "Ground_Smash"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")


def _env_f(key, default):
    return float(os.environ[key]) if os.environ.get(key) else float(default)


def _env_i(key, default):
    return int(os.environ[key]) if os.environ.get(key) else int(default)


# ---------------------------------------------------------------- 帧预算
TOTAL = _env_i("C07_TOTAL", 60)                 # 1.000 s @60fps
ANTIC = _env_i("C07_ANTIC", 20)                 # 前摇结束（§0.1 重攻击 12~20）
HIT = _env_i("C07_HIT", 36)                     # 命中帧（双拳到最低点）
HOLD = _env_i("C07_HOLD", 4)                    # 命停 4 帧（§0.1 上限）
HOLD_END = HIT + HOLD - 1                       # 39
RETURN_START = HOLD_END + 1                     # 40（收招起点）
SETTLE = _env_i("C07_SETTLE", 54)               # 收招落定（此后逐位静止）
CANCEL = _env_i("C07_CANCEL", 56)               # 可取消帧
POST_POW = _env_f("C07_POSTPOW", 1.6)           # 收招缓动 q = 1 − (1−u)^p
MID = (ANTIC + HIT) // 2                        # 躯干/臂的中段键（前倾转折）
SWING_F = (ANTIC + HIT) // 2                    # 双臂前平举的必经点
# ★ 第 2 轮实测（`world_step_ok` 红）：ANTIC→SWING 只有 6 帧却要走 ~110°，
#   峰值 27.1°/帧（上限 25）。把前摇拉到 ANTIC=20、命中推到 HIT=36
#   （前摇 12~20 的上界内），挥砸段由 12 帧扩到 16 帧，并把加速指数
#   从 1.5 降到 1.35（仍"越来越快砸向地面"，但峰值砍掉 10%）。
ACCEL_POW = _env_f("C07_ACCELPOW", 1.35)

# 命停窗内骨盆继续前爬的量（`hitstop_keeps_momentum_ok` 要 > 10 mm）
MOMENTUM_MM = _env_f("C07_MOMENTUM", 14.0)

# ---------------------------------------------------------------- 躯干轨道
# 帧 0 由 `patch()` 回填成 `Idle_01@0` 真值（禁手写）。
PELVIS_RX = ((6, 0.0), (12, -4.0), (ANTIC, -8.0), (MID, 6.0), (HIT, 22.0),
             (HOLD_END, 22.0))
SPINE01_RX = ((6, 0.0), (12, -1.5), (ANTIC, -3.0), (MID, 4.0), (HIT, 11.0),
              (HOLD_END, 11.0))
SPINE02_RX = ((6, 0.0), (12, -1.0), (ANTIC, -2.0), (MID, 4.0), (HIT, 11.0),
              (HOLD_END, 11.0))
CHEST_RX = ((6, 0.0), (12, -1.0), (ANTIC, -2.0), (MID, 4.0), (HIT, 11.0),
            (HOLD_END, 11.0))
NECK_RX = ((6, 0.0), (12, 6.0), (ANTIC, 14.0), (MID, -6.0), (HIT, -14.0),
           (HOLD_END, -14.0))
HEAD_RX = ((6, 0.0), (12, 3.0), (ANTIC, 6.0), (MID, -2.0), (HIT, -4.0),
           (HOLD_END, -4.0))
SHOULDER_RX = ((6, 0.0), (12, 8.0), (ANTIC, 16.0), (MID, 2.0), (HIT, -6.0),
               (HOLD_END, -6.0))

# 骨盆位移：x 恒 0（对称，`spread_ok` 要拳砸在正中）；y 后坐 → 前压；
# z 微升（举高）→ 深蹲（砸下）。见文件头第 4 件。
PELVIS_X = ((0, 0.0), (TOTAL, 0.0))
PELVIS_Y = ((0, 0.0), (6, 0.006), (ANTIC, 0.030), (MID, -0.010),
            (HIT, -0.040), (HOLD_END, -0.040 - MOMENTUM_MM / 1000.0))
PELVIS_Z = ((6, -0.004), (12, 0.003), (ANTIC, 0.010), (MID, -0.170),
            (HIT, -0.285), (HOLD_END, -0.285))       # 相对 Z_SEAM 的偏移

# ---------------------------------------------------------------- 手臂方向轨道
# 世界单位向量：x = 左正，y = 身后正，z = 上正，角色正面朝 −y。
ARM_KEYS = {
    # 半举：双拳在身前抬起（上臂已过水平、前臂竖起来）
    "RISE": {
        "upperarm.L": (0.30, -0.52, 0.80),
        "forearm.L": (0.24, -0.34, 0.91),
        "hand.L": (0.20, -0.26, 0.945),
        "upperarm.R": (-0.30, -0.52, 0.80),
        "forearm.R": (-0.24, -0.34, 0.91),
        "hand.R": (-0.20, -0.26, 0.945),
    },
    # 高举顶：双臂几乎竖直向上、略偏后（探针实测拳中点 z ≈ 2000 mm）
    "ANTIC": {
        "upperarm.L": (0.16, 0.06, 0.985),
        "forearm.L": (0.14, 0.05, 0.988),
        "hand.L": (0.12, 0.04, 0.992),
        "upperarm.R": (-0.16, 0.06, 0.985),
        "forearm.R": (-0.14, 0.05, 0.988),
        "hand.R": (-0.12, 0.04, 0.992),
    },
    # 中段：双臂前平举略下（砸击弧的必经点，保证拳 z 单调下降）
    "SWING": {
        "upperarm.L": (0.13, -0.955, -0.27),
        "forearm.L": (0.11, -0.975, -0.19),
        "hand.L": (0.09, -0.985, -0.14),
        "upperarm.R": (-0.13, -0.955, -0.27),
        "forearm.R": (-0.11, -0.975, -0.19),
        "hand.R": (-0.09, -0.985, -0.14),
    },
    # 砸下：双臂指向身前下方（α ≈ 6° 偏前，探针实测拳中点 z ≈ 300 mm）
    "HIT": {
        "upperarm.L": (0.09, -0.105, -0.990),
        "forearm.L": (0.06, -0.200, -0.978),
        "hand.L": (0.04, -0.280, -0.959),
        "upperarm.R": (-0.09, -0.105, -0.990),
        "forearm.R": (-0.06, -0.200, -0.978),
        "hand.R": (-0.04, -0.280, -0.959),
    },
}
ARM_PHASES = ((0, "SEAM", "smooth"), (9, "RISE", "smooth"),
              (ANTIC, "ANTIC", "smooth"), (SWING_F, "SWING", "accel"),
              (HIT, "HIT", "accel"), (HOLD_END, "HIT", "linear"))

# 收招末姿（半蹲起势）：躯干前倾 34°、双拳在膝前下方
END_ROT = {
    "pelvis": (12.0, 0.0, 0.0), "spine_01": (7.0, 0.0, 0.0),
    "spine_02": (7.0, 0.0, 0.0), "chest": (8.0, 0.0, 0.0),
    "neck": (-10.0, 0.0, 0.0), "head": (-4.0, 0.0, 0.0),
    "shoulder.L": (-8.0, 0.0, -8.0), "shoulder.R": (-8.0, 0.0, 8.0),
}
END_DIRS = {
    "upperarm.L": (0.20, -0.42, -0.885),
    "forearm.L": (0.17, -0.50, -0.850),
    "hand.L": (0.14, -0.56, -0.816),
    "upperarm.R": (-0.20, -0.42, -0.885),
    "forearm.R": (-0.17, -0.50, -0.850),
    "hand.R": (-0.14, -0.56, -0.816),
}
END_PX = _env_f("C07_END_PX", 0.0)
END_PY = _env_f("C07_END_PY", -0.010)           # 世界 y 偏移（略前）
END_PZ = _env_f("C07_END_PZ", 0.700)            # 世界 z（半蹲）

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
# ★ 14 骨全冻（C04 那套；见文件头第 3 件）
HITSTOP_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "shoulder.L", "shoulder.R",
                 "upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R")


# ---------------------------------------------------------------- 门禁阈值
SOLE_RANGE_MM = (-2.0, 6.0)
PLANT_DRIFT_MAX_MM = 3.0
PIVOT_DRIFT_MAX_MM = 3.0
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
# C07 新增门禁
SMASH_HEIGHT_MIN_MM = _env_f("C07_H_MIN", 1850.0)    # 高举顶双拳中点 z
SMASH_DEPTH_MAX_MM = _env_f("C07_D_MAX", 320.0)      # 砸击帧双拳中点 z
SMASH_SWING_MIN_DEG = _env_f("C07_S_MIN", 60.0)      # 躯干链 rx 行程
SQUAT_DEPTH_MAX_MM = _env_f("C07_Q_MAX", 640.0)      # 砸击帧骨盆 z
SPREAD_MAX_MM = _env_f("C07_SPR_MAX", 60.0)          # 拳中点 |x| 偏差

# ---------------------------------------------------------------- 观测量
SEAM_POSE = {}
SEAM_EULER = {}
SEAM_DIRS = {}
PY0 = 0.0
Z_SEAM = 0.0
ANKLE_0 = {}
IDLE_POSE = {}
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
IDLE_ARMDIR = {}
ARM_LEN = {}
ARM_BASIS = {}
HIT_POINT = {}          # ★ 砸击帧的骨世界坐标（下游/VFX 用）
E0 = {}                 # 收招起点（HOLD_END 的臂欧拉）
E_END = {}              # 收招终点（半蹲起势的臂欧拉）
_HIT_FROZEN = {}
SRC_MATS = {}
LOG = {}


def _hold(frame):
    return HIT < frame <= HOLD_END


def _lerp3(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def q_of(frame):
    """收招进度：0 = 命中（冻结值），1 = 半蹲起势。增量单调递减 ⟹ 步长单调不增。"""
    if frame <= HOLD_END:
        return 0.0
    if frame >= SETTLE:
        return 1.0
    u = (frame - HOLD_END) / float(SETTLE - HOLD_END)
    return 1.0 - (1.0 - u) ** POST_POW


# =============================================================== 姿态
def torso_pose(frame):
    """躯干 + 骨盆位移。命停窗内 `f = HIT`（旋转冻结，位移照走）。"""
    f = HIT if _hold(frame) else frame
    rot = {
        "pelvis": (RS.track(PELVIS_RX, f), 0.0, 0.0),
        "spine_01": (RS.track(SPINE01_RX, f), 0.0, 0.0),
        "spine_02": (RS.track(SPINE02_RX, f), 0.0, 0.0),
        "chest": (RS.track(CHEST_RX, f), 0.0, 0.0),
        "neck": (RS.track(NECK_RX, f), 0.0, 0.0),
        "head": (RS.track(HEAD_RX, f), 0.0, 0.0),
        "shoulder.L": (RS.track(SHOULDER_RX, f), 0.0, 0.0),
        "shoulder.R": (RS.track(SHOULDER_RX, f), 0.0, 0.0),
    }
    if frame <= HOLD_END:
        px = RS.track(PELVIS_X, frame)
        py = RS.track(PELVIS_Y, frame)
        pz = Z_SEAM + RS.track(PELVIS_Z, frame)
    else:
        q = q_of(frame)
        pz0 = Z_SEAM + RS.track(PELVIS_Z, HOLD_END)
        px0 = RS.track(PELVIS_X, HOLD_END)
        py0 = RS.track(PELVIS_Y, HOLD_END)
        px = px0 + (END_PX - px0) * q
        py = py0 + (END_PY - py0) * q
        pz = pz0 + (END_PZ - pz0) * q
    rot["@loc"] = {"pelvis": A.wloc(px, py, pz - 0.900)}
    return rot


def arm_phase(frame):
    """相位插值参数 `(键a, 键b, t)`；相位表与旧版逐字一致。"""
    if _hold(frame):
        frame = HIT
    bounds = [item[0] for item in ARM_PHASES]
    if frame <= bounds[0]:
        return ("SEAM", "SEAM", 0.0)
    if frame >= bounds[-1]:
        return ("HIT", "HIT", 1.0)
    for index in range(len(ARM_PHASES) - 1):
        fa, na, mode = ARM_PHASES[index]
        fb, nb, _mb = ARM_PHASES[index + 1]
        if not (fa <= frame <= fb) or fa == fb:
            continue
        u = (frame - fa) / float(fb - fa)
        if mode == "linear":
            t = u
        elif mode == "accel":
            t = u ** ACCEL_POW
        else:
            t = RS.smooth(u)
        return (na, nb, t)
    return ("HIT", "HIT", 1.0)


def key_basis(dirs):
    """把一组世界方向解成各骨的**世界基准 3×3**（= 从 Idle 基准做最小旋转）。"""
    out = {}
    for bone in ARM_BONES:
        quat = (Vector(IDLE_DIR[bone]).normalized()
                .rotation_difference(Vector(dirs[bone]).normalized()))
        out[bone] = quat.to_matrix() @ IDLE_BASIS[bone]
    return out


def build_arm_basis():
    table = {"SEAM": SEAM_DIRS}
    table.update(ARM_KEYS)
    return {name: key_basis(dirs) for name, dirs in table.items()}


def arm_basis(frame):
    """本帧各臂骨的**目标世界基准**：相位两端做四元数 slerp。

    ★ 为什么不逐帧 `aim_bone_ref` 反解（第 1 轮 7 项红门的最后一项）：
    反解 = 从 Idle 方向做**最小旋转**。本支要求"双拳过顶"，手臂方向必然
    接近 Idle 方向的**反向**（砸击类是唯一天天走到反向点的动作），而最小
    旋转的**滚转**分量在反向点附近病态。实测：ANTIC 之后第 2 帧单帧世界
    转动 **34.3°**（上限 25），而同一帧**方向**只变了 **8.0°** ——
    多出来的 26° 全是滚转在"补课"，读起来是手臂**拧了一下**。
    把前摇拉长到 20 帧只把它压到 25.6°，峰位仍钉在"ANTIC+2"，
    证明病根是滚转不是速度。

    改为对两个**朝向**做 slerp：路径 = 测地线，无病态点；且**相位端点**
    的朝向与反解结果逐位相同 ⟹ 六项 C07 专属门禁（举高 2019.5 / 砸深
    292.3 / 弧线单调 / 拳心居中 …）全部不受影响。
    """
    na, nb, t = arm_phase(frame)
    out = {}
    for bone in ARM_BONES:
        qa = ARM_BASIS[na][bone].to_quaternion()
        qb = ARM_BASIS[nb][bone].to_quaternion()
        if qa.dot(qb) < 0.0:
            qb = Quaternion((-qb.w, -qb.x, -qb.y, -qb.z))
        out[bone] = qa.slerp(qb, t).to_matrix()
    return out


def aim_world_basis(arm, name, basis):
    """把骨的世界基准钉到 `basis`（只改朝向，位置不变），返回解出的 euler。"""
    pose_bone = arm.pose.bones[name]
    pose_bone.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    target = basis.to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


# =============================================================== 姿态装配
def build_pose(arm, frame, shift):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)

    for side in SIDES:
        target = (ANKLE_0[side].x, ANKLE_0[side].y,
                  ANKLE_0[side].z + shift[side])
        G4.leg_seat(arm, pose, side, target, IDLE_KNEE_DIR[side])

    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    if frame <= HOLD_END:
        basis = arm_basis(frame)
        for bone in ARM_BONES:
            pose[bone] = JS._unwrap_xyz(
                JS._PREV_EULER.get(bone),
                aim_world_basis(arm, bone, basis[bone]))
    else:
        q = q_of(frame)
        for bone in ARM_BONES:
            goal = JS._unwrap_xyz(E0.get(bone), E_END[bone])
            pose[bone] = JS._unwrap_xyz(
                JS._PREV_EULER.get(bone), _lerp3(E0[bone], goal, q))

    if frame == HIT:
        _HIT_FROZEN.clear()
        for key in HITSTOP_BONES:
            if key in pose:
                _HIT_FROZEN[key] = tuple(pose[key])
        # ★ 登记砸击帧（HIT）的**双拳与骨盆世界坐标** —— 清单 C07 计划第 1 节
        #   点名要给下游 D 族"格挡/受击"与 VFX（裂纹、震屏）定位用。
        fist_l = Vector(A.bone_world(arm, "hand.L", "tail"))
        fist_r = Vector(A.bone_world(arm, "hand.R", "tail"))
        HIT_POINT.clear()
        HIT_POINT.update({
            "frame": HIT,
            "fist_L_m": [round(v, 4) for v in fist_l],
            "fist_R_m": [round(v, 4) for v in fist_r],
            "fist_mid_m": [round(v, 4) for v in (fist_l + fist_r) * 0.5],
            "fist_span_mm": round((fist_l - fist_r).length * 1000.0, 2),
            "pelvis_m": [round(v, 4)
                         for v in A.bone_world(arm, "pelvis", "head")],
        })
    if _HIT_FROZEN and _hold(frame):
        for name, value in _HIT_FROZEN.items():
            pose[name] = tuple(value)
            arm.pose.bones[name].rotation_euler = [math.radians(v)
                                                   for v in value]
        bpy.context.view_layer.update()

    if frame == HOLD_END:
        E0.clear()
        for bone in ARM_BONES:
            E0[bone] = tuple(pose[bone])

    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


def _snapshot_carry():
    return (dict(JS._PREV_EULER),)


def _restore_carry(snap):
    JS._PREV_EULER.clear()
    JS._PREV_EULER.update(snap[0])


def solve_pose(arm, frame, meshes=None):
    """逐帧贴地闭环：两只脚全程支撑，鞋底钉到 0 mm。"""
    shift = {side: 0.0 for side in SIDES}
    snap = _snapshot_carry()
    pose = build_pose(arm, frame, shift)
    if meshes is None:
        return pose
    for _ in range(4):
        low = A.foot_lowest_by_side()
        error = {s: 0.0 - low[s][2] for s in SIDES if low[s] is not None}
        if not error or max(abs(v) for v in error.values()) < 5e-5:
            break
        for side, value in error.items():
            shift[side] += value
        _restore_carry(snap)
        pose = build_pose(arm, frame, shift)
    _restore_carry(snap)
    pose = build_pose(arm, frame, shift)
    return pose


def solve_end_arm(arm):
    """一次性解出「半蹲起势」的手臂欧拉（收招插值终点）。"""
    torso = {
        "pelvis": (END_ROT["pelvis"][0], 0.0, 0.0),
        "spine_01": (END_ROT["spine_01"][0], 0.0, 0.0),
        "spine_02": (END_ROT["spine_02"][0], 0.0, 0.0),
        "chest": (END_ROT["chest"][0], 0.0, 0.0),
        "neck": (END_ROT["neck"][0], 0.0, 0.0),
        "head": (END_ROT["head"][0], 0.0, 0.0),
        "shoulder.L": END_ROT["shoulder.L"],
        "shoulder.R": END_ROT["shoulder.R"],
        "@loc": {"pelvis": A.wloc(END_PX, END_PY, END_PZ - 0.900)},
    }
    A.apply_pose(arm, torso)
    for side in SIDES:
        G4.leg_seat(arm, torso, side,
                    (ANKLE_0[side].x, ANKLE_0[side].y, ANKLE_0[side].z),
                    IDLE_KNEE_DIR[side])
    for side in SIDES:
        A.keep_world_orientation(arm, "foot." + side)
    out = {}
    for bone in ARM_BONES:
        out[bone] = JS._unwrap_xyz(
            None, G4.aim_bone_ref(arm, bone, END_DIRS[bone],
                                  IDLE_BASIS[bone], IDLE_DIR[bone]))
    return out


# =============================================================== 逐帧实测
def _sole_anchor(side):
    """找该侧鞋底「最前的最低点」顶点的 **(对象名, 顶点号)** —— 枢轴基准。

    ★ 为什么不用"每帧取最低顶点"：脚底前后两个顶点 z 常只差零点几毫米，
    姿态微动就让"最低"在两者之间跳，跳动量 = 两顶点的 xy 距离。
    C07 第 1 轮实测 `stance_pivot_ok` = 红，L 侧 57.5 mm —— 而同一轮
    `plant_drift_mm` 只有 0.015 mm（踝是钉死的）。57 mm 全是**量法伪影**，
    脚根本没滑。钉死一个顶点才量得到"脚有没有在原地转"。
    这与 C06 `measure_pivot` 同法（取最低点上方 2 mm 带内最前那个顶点）。
    """
    deps = bpy.context.evaluated_depsgraph_get()
    points = []
    for name in A.FOOT_MESHES[side]:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            point = matrix @ vertex.co
            points.append((point.x, point.y, point.z, name, vertex.index))
        evaluated.to_mesh_clear()
    if not points:
        return None
    zmin = min(p[2] for p in points)
    band = [p for p in points if p[2] <= zmin + 2.0]
    front = min(band, key=lambda p: p[1])
    return (front[3], front[4])


def _vertex_world(key):
    deps = bpy.context.evaluated_depsgraph_get()
    obj = bpy.data.objects.get(key[0])
    if obj is None:
        return None
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    point = evaluated.matrix_world @ mesh.vertices[key[1]].co
    evaluated.to_mesh_clear()
    return (point.x, point.y, point.z)


def foot_series(arm, action, meshes):
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    rows = []
    anchor = {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        if frame == 0:
            for side in SIDES:
                anchor[side] = _sole_anchor(side)
        row = {"frame": frame,
               "pelvis": tuple(A.bone_world(arm, "pelvis", "head")),
               "neck": tuple(A.bone_world(arm, "neck", "head"))}
        low = A.foot_lowest_by_side()
        for side in SIDES:
            row["ankle_" + side] = tuple(A.bone_world(arm, "foot." + side,
                                                      "head"))
            row["contact_" + side] = low[side]
            row["sole_" + side] = None if low[side] is None else low[side][2]
            row["reach_" + side] = (
                Vector(row["ankle_" + side]) - Vector(row["pelvis"])).length
            row["hand_" + side + "_tail"] = tuple(
                A.bone_world(arm, "hand." + side, "tail"))
            # ★ 枢轴 = **同一个顶点**逐帧的世界坐标（见 `_sole_anchor`）
            row["pivot_" + side] = (None if anchor.get(side) is None
                                    else _vertex_world(anchor[side]))
        rows.append(row)
    if previous is not None:
        arm.animation_data.action = previous
    return rows


def arm_world_steps(arm, action):
    mats = {}
    for frame in range(0, TOTAL + 1):
        raw = RS.action_world_matrices(arm, action, frame)
        mats[frame] = {
            name: Matrix([raw[name][i * 4:i * 4 + 3] for i in range(3)])
            for name in ARM_BONES + ("pelvis", "spine_01", "spine_02", "chest",
                                     "neck", "head") if name in raw}
    worst, worst_at = 0.0, None
    for frame in range(1, TOTAL + 1):
        for name in mats[frame]:
            if name not in mats[frame - 1]:
                continue
            q = (mats[frame - 1][name].transposed()
                 @ mats[frame][name]).to_quaternion()
            angle = math.degrees(q.angle)
            if angle > worst:
                worst, worst_at = angle, (frame, name)
    return worst, worst_at


# =============================================================== 专属门禁
def smash_assertions(arm, action, samples, foots):
    res = {}
    pelvis = [Vector(f["pelvis"]) for f in foots]
    pz = [p.z * 1000.0 for p in pelvis]
    fist_mid = [Vector(f["hand_L_tail"]).lerp(Vector(f["hand_R_tail"]), 0.5)
                for f in foots]
    mid_z = [v.z * 1000.0 for v in fist_mid]
    mid_x = [v.x * 1000.0 for v in fist_mid]

    # ---- 0) 首帧接缝：C07@0 必须逐位等于 `Idle_01@0`
    mats0 = RS.action_world_matrices(arm, action, 0)
    delta0 = RS.matrix_delta(mats0, SRC_MATS)
    res["seam_source"] = [I1.NAME, 0]
    res["smash_start_delta"] = float("%.3e" % delta0)
    res["smash_start_ok"] = delta0 <= SEAM_TOL
    res["root_motion_m"] = [0.0, round(pelvis[-1].y - pelvis[0].y, 6)]
    res["root_motion_ok"] = abs(res["root_motion_m"][1]) * 1000.0 <= 30.0

    # ---- 1) 支撑脚：踝 XY 漂移 + 鞋底区间 + 全部有支撑
    plant, sole, pivot = {}, {}, {}
    for side in SIDES:
        pts = list(range(0, TOTAL + 1))
        xs = [foots[f]["ankle_" + side][0] for f in pts]
        ys = [foots[f]["ankle_" + side][1] for f in pts]
        plant[side + "_mm"] = round(
            math.hypot(max(xs) - min(xs), max(ys) - min(ys)) * 1000.0, 4)
        zs = [foots[f]["sole_" + side] for f in pts
              if foots[f]["sole_" + side] is not None]
        sole[side] = [round(min(zs) * 1000.0, 3), round(max(zs) * 1000.0, 3)]
        # 枢轴 = 钉死顶点（`_sole_anchor`）的 xy 行程；见 `_sole_anchor` 的注释
        prow = [foots[f]["pivot_" + side] for f in pts]
        prow = [p for p in prow if p is not None]
        if prow:
            cx = [p[0] for p in prow]
            cy = [p[1] for p in prow]
            pivot[side + "_mm"] = round(
                math.hypot(max(cx) - min(cx), max(cy) - min(cy)) * 1000.0, 4)
        else:
            pivot[side + "_mm"] = None
    res["plant_drift_mm"] = plant
    res["stance_plant_ok"] = all(v <= PLANT_DRIFT_MAX_MM for v in plant.values())
    res["pivot_drift_mm"] = pivot
    res["stance_pivot_ok"] = all(
        v is not None and v <= PIVOT_DRIFT_MAX_MM for v in pivot.values())
    res["plant_sole_mm"] = sole
    res["stance_sole_ok"] = all(SOLE_RANGE_MM[0] <= v[0]
                                and v[1] <= SOLE_RANGE_MM[1]
                                for v in sole.values())
    # 本支两脚全程支撑 ⟹ `always_supported_ok` 构造性成立（无腾空帧）
    res["unsupported_frames"] = []
    res["always_supported_ok"] = True
    # 无摆动脚 ⟹ "摆动脚必须真的离地"**空集**，条件性成立（已在日志登记）
    res["swing_windows"] = None
    res["swing_airborne_ok"] = True

    # ---- 2) 顿感：命停窗 14 骨逐位冻结，而骨盆继续前压
    frozen = []
    for index in range(1, len(samples)):
        frame = samples[index]["frame"]
        if HIT < frame <= HOLD_END:
            ea = samples[index - 1]["euler"]
            eb = samples[index]["euler"]
            step = 0.0
            for name in HITSTOP_BONES:
                va = ea.get(name, (0.0, 0.0, 0.0))
                vb = eb.get(name, (0.0, 0.0, 0.0))
                step = max(step, max(abs(a - b) for a, b in zip(va, vb)))
            frozen.append(round(step, 6))
    res["hitstop_frozen_steps"] = frozen
    res["hitstop_present_ok"] = bool(frozen) and max(frozen) <= 1e-6
    res["hitstop_momentum_mm"] = round((pelvis[HIT].y
                                        - pelvis[HOLD_END].y) * 1000.0, 3)
    res["hitstop_keeps_momentum_ok"] = res["hitstop_momentum_mm"] > 10.0
    res["hitstop_frames"] = HOLD
    res["hitstop_frames_ok"] = 2 <= HOLD <= 4
    res["antic_frames"] = ANTIC
    res["antic_frames_ok"] = 12 <= ANTIC <= 20

    # ---- 3) ★ C07 六个新门禁
    raise_fist = fist_mid[ANTIC]
    res["raise_fist_mid_mm"] = [round(v * 1000.0, 1) for v in raise_fist]
    res["smash_height_ok"] = raise_fist.z * 1000.0 >= SMASH_HEIGHT_MIN_MM

    hit_fist = fist_mid[HIT]
    res["hit_fist_mid_mm"] = [round(v * 1000.0, 1) for v in hit_fist]
    res["hit_fist_span_mm"] = round(
        (Vector(foots[HIT]["hand_L_tail"])
         - Vector(foots[HIT]["hand_R_tail"])).length * 1000.0, 2)
    res["smash_depth_ok"] = hit_fist.z * 1000.0 <= SMASH_DEPTH_MAX_MM
    res["smash_depth_headroom_mm"] = round(
        SMASH_DEPTH_MAX_MM - hit_fist.z * 1000.0, 2)

    chain = []
    for s in samples:
        chain.append(sum(s["euler"].get(n, (0.0, 0.0, 0.0))[0]
                         for n in ("pelvis", "spine_01", "spine_02", "chest")))
    swing = chain[ANTIC] - chain[HIT]
    res["torso_sum_rx_antic_deg"] = round(chain[ANTIC], 3)
    res["torso_sum_rx_hit_deg"] = round(chain[HIT], 3)
    res["smash_swing_deg"] = round(abs(swing), 3)
    res["smash_swing_ok"] = abs(swing) >= SMASH_SWING_MIN_DEG

    seg = mid_z[ANTIC:HIT + 1]
    steps = [seg[i + 1] - seg[i] for i in range(len(seg) - 1)]
    res["smash_arc_steps_mm"] = [round(v, 2) for v in steps]
    res["smash_arc_rise_frames"] = sum(1 for v in steps if v > 1.0)
    res["smash_arc_ok"] = all(v <= 1.0 for v in steps)

    res["hit_pelvis_z_mm"] = round(pz[HIT], 2)
    res["squat_depth_ok"] = pz[HIT] <= SQUAT_DEPTH_MAX_MM

    res["hit_fist_mid_x_mm"] = round(mid_x[HIT], 2)
    res["spread_ok"] = abs(mid_x[HIT]) <= SPREAD_MAX_MM

    # ---- 4) 力矩链：脚→腿→髋→腰→肩→手 逐级非零
    keys = ("pelvis", "spine_01", "spine_02", "chest", "shoulder.L",
            "shoulder.R", "thigh.L", "shin.L", "thigh.R", "shin.R")
    channel = {}
    for name in keys:
        vals = [s["euler"].get(name, (0.0, 0.0, 0.0)) for s in samples]
        channel[name] = round(max(max(abs(v) for v in item) for item in vals), 3)
    res["power_chain_channels_deg"] = channel
    res["power_chain_ok"] = all(v > 0.5 for v in channel.values())

    # ---- 5) 腿可达（不做截断）
    limit = A.L_THIGH + A.L_SHIN
    ratios, peak = {}, {}
    for side in SIDES:
        vals = [(f["reach_" + side], f["frame"]) for f in foots]
        best, best_f = max(vals)
        ratios[side] = round(best / limit, 5)
        peak[side] = [best_f, round(best * 1000.0, 2)]
    res["leg_reach_max_ratio"] = ratios
    res["leg_reach_peak"] = peak
    res["ik_reach_ok"] = all(v <= REACH_MAX_RATIO for v in ratios.values())

    # ---- 6) 收招：不许瞬停、不许过冲
    tails, tail_bones = [], []
    for index in range(1, len(samples)):
        frame = samples[index]["frame"]
        if frame >= RETURN_START:
            ea = samples[index - 1]["euler"]
            eb = samples[index]["euler"]
            step, owner = 0.0, None
            for name in set(ea) | set(eb):
                va = ea.get(name, (0.0, 0.0, 0.0))
                vb = eb.get(name, (0.0, 0.0, 0.0))
                here = max(abs(a - b) for a, b in zip(va, vb))
                if here > step:
                    step, owner = here, name
            tails.append(round(step, 4))
            tail_bones.append(owner)
    res["return_tail"] = tails
    res["return_tail_bones"] = tail_bones
    res["decel_smooth_ok"] = bool(
        tails and all(tails[i + 1] <= tails[i] + 1e-9
                      for i in range(len(tails) - 1)))
    res["no_snap_stop_ok"] = bool(tails and tails[-1] <= 5.0
                                  and tails[-1] <= tails[0])
    res["local_step_max_deg"] = round(max(tails) if tails else 0.0, 3)
    return res


# =============================================================== 主流程
def main():
    global SEAM_POSE, SEAM_EULER, SEAM_DIRS, PY0, Z_SEAM, ANKLE_0, IDLE_POSE
    global IDLE_KNEE_DIR, IDLE_BASIS, IDLE_DIR, IDLE_ARMDIR, ARM_LEN
    global ARM_BASIS
    global E0, E_END, SRC_MATS
    global PELVIS_X, PELVIS_RX, PELVIS_Y, PELVIS_Z
    global SPINE01_RX, SPINE02_RX, CHEST_RX
    global NECK_RX, HEAD_RX, SHOULDER_RX

    for store in (SEAM_POSE, SEAM_EULER, SEAM_DIRS, ANKLE_0, IDLE_POSE,
                  IDLE_KNEE_DIR, IDLE_BASIS, IDLE_DIR, IDLE_ARMDIR, ARM_LEN,
                  ARM_BASIS, E0, E_END, _HIT_FROZEN, LOG, HIT_POINT):
        store.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("C07_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}

    if "thigh.L" not in A.PROBE_BONES:
        A.PROBE_BONES = tuple(A.PROBE_BONES) + ("thigh.L", "thigh.R",
                                                "shin.L", "shin.R")
        A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail"
                                             for n in A.PROBE_TAILS)

    # ---- 首帧真值：`Idle_01@0`
    scene = bpy.context.scene
    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    scene.frame_set(0)
    bpy.context.view_layer.update()
    SEAM_EULER = {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
                  for b in arm.pose.bones}
    SEAM_POSE = dict(SEAM_EULER)
    SEAM_POSE["@loc"] = {"pelvis": tuple(arm.pose.bones["pelvis"].location)}
    SEAM_POSE.update(A.FIST)
    SEAM_DIRS = {bone: tuple(A.bone_direction(arm, bone)) for bone in ARM_BONES}
    SRC_MATS = RS.action_world_matrices(arm, src, 0)
    PY0 = A.bone_world(arm, "pelvis", "head").y
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    IDLE_ARMDIR = dict(SEAM_DIRS)

    # ---- Idle 骨基座（`leg_seat` / `aim_bone_ref` 的缺省滚转基准）
    IDLE_POSE = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, IDLE_POSE)
    bpy.context.view_layer.update()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        IDLE_KNEE_DIR[side] = (knee - hip).normalized()
        for name in ("thigh." + side, "shin." + side):
            IDLE_BASIS[name] = arm.pose.bones[name].matrix.to_3x3().copy()
            IDLE_DIR[name] = A.bone_direction(arm, name)
    for name in ARM_BONES:
        IDLE_BASIS[name] = arm.pose.bones[name].matrix.to_3x3().copy()
        IDLE_DIR[name] = A.bone_direction(arm, name)
    G4.IDLE_BASIS.clear()
    G4.IDLE_BASIS.update(IDLE_BASIS)
    G4.IDLE_DIR.clear()
    G4.IDLE_DIR.update(IDLE_DIR)
    G4.IDLE_KNEE_DIR.clear()
    G4.IDLE_KNEE_DIR.update(IDLE_KNEE_DIR)
    G4.ARM_LEN.clear()
    for side in SIDES:
        G4.ARM_LEN[side] = dict(ARM_LEN[side])

    # ---- 躯干/骨盆轨道：f0 回填 Idle 真值（★ 必须 global，见 C01 教训）
    def patch(track, bone, channel=0):
        return ((0, SEAM_EULER[bone][channel]),) + tuple(
            k for k in track if k[0] != 0)

    PELVIS_RX = patch(PELVIS_RX, "pelvis")
    SPINE01_RX = patch(SPINE01_RX, "spine_01")
    SPINE02_RX = patch(SPINE02_RX, "spine_02")
    CHEST_RX = patch(CHEST_RX, "chest")
    NECK_RX = patch(NECK_RX, "neck")
    HEAD_RX = patch(HEAD_RX, "head")
    SHOULDER_RX = patch(SHOULDER_RX, "shoulder.L")
    # ★ PELVIS_X 是**位移**轨道（米），绝不能走 `patch()` —— `patch()` 取的是
    # `SEAM_EULER[bone][0]`，那是**旋转**角（度）。误用会把 Idle 的骨盆 rx
    # （≈3.93°）当成 3.93 **米**的横向位移灌进去 ⟹ 全身横飞 3.9 m、
    # 腿被拉爆（可达比 1.09）、脚飞起 285 mm、拳心偏 1500 mm。
    # 位移轨道统一用 `(0, 0.0)` 起手（骨盆位移本身就以偏移量表达）。
    PELVIS_X = ((0, 0.0),) + tuple(k for k in PELVIS_X if k[0] != 0)
    PELVIS_Y = ((0, 0.0),) + tuple(k for k in PELVIS_Y if k[0] != 0)
    PELVIS_Z = ((0, 0.0),) + tuple(k for k in PELVIS_Z if k[0] != 0)

    A.report("C07_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "antic": ANTIC, "hit": HIT, "hold": HOLD, "hold_end": HOLD_END,
        "return_start": RETURN_START, "settle": SETTLE, "cancel": CANCEL,
        "seam_source": [I1.NAME, 0],
        "pelvis_y0_mm": round(PY0 * 1000.0, 3),
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                      for s in SIDES},
        "end_pelvis_m": [END_PX, END_PY, END_PZ],
        "hitstop_bones": list(HITSTOP_BONES),
        "momentum_mm": MOMENTUM_MM,
        "note": ("地面砸击：首帧 = `Idle_01@0`（逐位）；双拳由方向链高举过顶"
                 "（ANTIC）再砸到身前地面（HIT）；命停 4 帧 14 骨全冻、骨盆"
                 "继续前爬；收招单向减速到「半蹲起势」。原地，无 Root Motion。"),
    })

    # ---- 相位基准（升高/砸下两端的**朝向**，供四元数 slerp）
    ARM_BASIS.clear()
    ARM_BASIS.update(build_arm_basis())
    A.report("C07_ARM_BASIS", {
        "phases": sorted(ARM_BASIS),
        "dirs": {name: {b: [round(c, 4) for c in (SEAM_DIRS if name == "SEAM" else ARM_KEYS[name])[b]]
                        for b in ARM_BONES}
                 for name in sorted(ARM_BASIS)},
    })

    # ---- 收招终点的臂欧拉（一次性）
    E_END = solve_end_arm(arm)
    A.report("C07_END_ARM", {
        "end_dirs": END_DIRS,
        "end_euler_deg": {k: [round(v, 4) for v in E_END[k]]
                          for k in ARM_BONES},
    })

    # ---- 建帧
    JS._PREV_EULER.clear()
    A.apply_pose(arm, SEAM_POSE)
    bpy.context.view_layer.update()
    for name, value in SEAM_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    keyframes = [(0, SEAM_POSE)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "连招与特殊技",
        "note": ("地面砸击：首帧 = `Idle_01@0`（逐位）；双拳高举过顶再砸到身前"
                 "地面；命停 %d 帧 14 骨全冻；收招单向减速到「半蹲起势」。"
                 "原地动作，无 Root Motion。" % HOLD),
        "antic_frame": ANTIC,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HOLD,
        "root_motion_m": [0.0, 0.0],
        "inherit_from": None,
        "hit_point_m": dict(HIT_POINT),
        "end_pose_deg": {k: [round(v, 4) for v in val]
                         for k, val in sorted(END_ROT.items())},
        "end_arm_dirs": {k: [round(v, 6) for v in val]
                         for k, val in sorted(END_DIRS.items())},
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "RISE": 9, "ANTIC": ANTIC, "SWING": SWING_F, "HIT": HIT,
        "HOLD_END": HOLD_END, "RECOV": RETURN_START, "SETTLE": SETTLE,
        "CANCEL": CANCEL, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    foots = foot_series(arm, action, meshes)
    if os.environ.get("C07_TRACE") == "1":
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for f in foots:
            fm = (Vector(f["hand_L_tail"]) + Vector(f["hand_R_tail"])) * 0.5
            print("C07_TRACE " + json.dumps({
                "f": f["frame"], "q": round(q_of(f["frame"]), 5),
                "pelvis": [round(v * 1000.0, 2) for v in f["pelvis"]],
                "fist_mid": [round(v * 1000.0, 2) for v in fm],
                "L_sole": (None if f["sole_L"] is None
                           else round(f["sole_L"] * 1000.0, 3)),
                "R_sole": (None if f["sole_R"] is None
                           else round(f["sole_R"] * 1000.0, 3)),
                "L_reach": round(f["reach_L"] * 1000.0 / limit_mm, 4),
                "R_reach": round(f["reach_R"] * 1000.0 / limit_mm, 4),
            }))
        # 逐帧世界步长（定位 `world_step_ok` 的峰落在哪个相位）
        prev_mats = None
        for frame in range(0, TOTAL + 1):
            raw = RS.action_world_matrices(arm, action, frame)
            cur = {name: Matrix([raw[name][i * 4:i * 4 + 3] for i in range(3)])
                   for name in ARM_BONES
                   + ("pelvis", "spine_01", "spine_02", "chest", "neck", "head")
                   if name in raw}
            if prev_mats is not None:
                worst, at, dstep = 0.0, None, 0.0
                for name in cur:
                    if name not in prev_mats:
                        continue
                    angle = math.degrees(
                        (prev_mats[name].transposed()
                         @ cur[name]).to_quaternion().angle)
                    if angle > worst:
                        worst, at = angle, name
                        da = (prev_mats[name] @ Vector((0.0, 1.0, 0.0)))
                        db = (cur[name] @ Vector((0.0, 1.0, 0.0)))
                        dstep = math.degrees(da.normalized().angle(
                            db.normalized()))
                print("C07_WSTEP " + json.dumps(
                    {"f": frame, "deg": round(worst, 3), "bone": at,
                     "dir_deg": round(dstep, 3)}))
            prev_mats = cur

    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.update(smash_assertions(arm, action, samples, foots))

    report["low_bad_frames"] = {
        str(s["frame"]): [round(s["low"]["L"] * 1000.0, 2),
                          round(s["low"]["R"] * 1000.0, 2)]
        for s in samples
        if min(s["low"]["L"], s["low"]["R"]) * 1000.0 < -2.0}
    world_step, world_at = arm_world_steps(arm, action)
    report["world_step_max_deg"] = round(world_step, 3)
    report["world_step_max_at"] = (None if world_at is None
                                   else [world_at[0], world_at[1]])
    report["world_step_ok"] = world_step <= NO_TELEPORT_MAX_DEG
    report["hit_point_m"] = dict(HIT_POINT)
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C07_REPORT", report)

    if not SKIP_RENDER:
        # ★ 取景由**实测包围盒**算（C06 教训 2 的通则）。
        #   C07 的坑不在水平位移（原地、无 Root Motion），而在**竖直跨度**：
        #   `ortho_scale` 量的是**长边**，本视图分辨率 780×1100 ⟹ 2.10 m 是
        #   **竖直**跨度、机位中心 z=0.92 ⟹ 上边界只到 **1.97 m**；而高举顶
        #   双拳到 **2.02~2.11 m**。第 1 轮出图把双拳**整段切掉**，而门禁
        #   当时全绿（取景不进判据）—— 与 C06 第 1 轮 18 张图出画同款事故。
        frames = [0, 9, ANTIC, SWING_F, HIT, HOLD_END, SETTLE, TOTAL]
        ratio = 780.0 / 1100.0
        keys = [k for k in samples[0]
                if k != "frame" and isinstance(samples[0][k], tuple)]
        pts = [Vector(s[k]) for s in samples for k in keys if k in s]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        center = (0.5 * (min(xs) + max(xs)),
                  0.5 * (min(ys) + max(ys)),
                  0.5 * (min(zs) + max(zs)))
        scale = max(2.10,
                    (max(zs) - min(zs)) * 1.15,
                    (max(xs) - min(xs)) * 1.15 / ratio,
                    (max(ys) - min(ys)) * 1.15 / ratio)

        def reframe(view):
            """保留原视图的**方向**，只按实测包围盒重定中心与跨度。"""
            _name, location, target, _scale, res = view
            direction = (Vector(location) - Vector(target)).normalized()
            new_target = Vector(center)
            new_location = new_target + direction * 4.6
            return (_name, tuple(new_location), tuple(new_target), scale, res)

        A.report("C07_CAMERA", {
            "bbox_min": [round(min(xs), 4), round(min(ys), 4), round(min(zs), 4)],
            "bbox_max": [round(max(xs), 4), round(max(ys), 4), round(max(zs), 4)],
            "center": [round(v, 4) for v in center],
            "ortho_scale": round(scale, 4),
            "z_top_of_frame_m": round(center[2] + scale / 2.0, 4),
            "note": ("标准视图上边界 1.97 m 会把高举顶双拳（2.02~2.11 m）切掉，"
                     "故按实测包围盒重定；三视角沿用各自原方向。"),
        })
        for base in (A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q):
            A.render_pose_sheet(arm, action, frames, "smash07",
                                views=(reframe(base),))
    A.save_project()
    A.export_glb(arm)
    print("C07_DONE failed=%s" % report["failed"])
    print("C07_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C07_FAILURE " + traceback.format_exc())
