"""anim_exhausted —— E02 `Exhausted` 虚弱（E 族第二支 / 第 58 支）。

清单原文：「**弯腰喘气、双手扶膝**」。

★★★ 本支与 E01 `Stun` 的三处根本不同（开工前想清楚）
    · 方向：E01 是**横向**周期摇晃；E02 是**纵向**弯腰 + 呼吸起伏。
    · 高度：E01 骨盆高度恒定；E02 **必然降骨盆**（`stun_height_hold_ok` 已**停用**，
      换成两端都卡的 `exh_bend_depth_ok`）。
    · ★★★ 手：E01 的手是自由的；**E02 的手要钉在膝盖上** —— 而膝盖是**会动的目标**
      （随骨盆升降 / 屈膝变化），比 E01 的**静止踝锚点**更难。

★★★ 本支的工程件 ①：**「步进 + 弯腰」的姿态混合 + 呼吸的重新锚定（两段结构）**
    E01 的「消失于接缝」周期函数是**整体**的（f=0 与 f=N 上恒 0）。
    本支是**两段**：`pose(f) = BLEND(站架 → 弯腰, B(f)) ⊕ 呼吸(φ)·B(f)`。
    · `B(f)` = smoothstep 包络，**f=0 与 f=N 上恒等于 0**（3x²−2x³ 在端点取 0/1）；
    · 呼吸用 `sin(φ) − sin(0)` 形式，φ 在 hold 窗口两端为 0，再乘 `B(f)`
      ⟹ 首帧逐位 = 站架、末帧逐位 = 首帧，**两个约束同时成立**。
    ★ E01 的 `_wave()` **不能直接搬**（会把弯腰在末帧抹掉 / 让首帧带上呼吸）。

★★★ 本支的工程件 ②：**手钉在「动目标」膝盖上（闭环 + 逐帧重解）**
    · 每帧先解**躯干 + 腿**，得到**当前帧的膝盖世界坐标**（不是静态值）；
    · 再对**当前**膝盖做臂链位置 IK（`upperarm` + `forearm`+`hand` 视作两段）；
    · 臂的 euler 与站架臂**按 B(f) 混合** ⟹ f=0 时逐位 = 站架臂（接缝）。
    ★ 本项目铁律：**没有任何判据盯着的约束等于不存在** ⟹ 新建
      `exh_hand_on_knee_ok`（骨架级）+ `px_exh_hand_on_knee_ok`（像素级），
      且反向验证 ②（`E02_TP_HANDFAR=1`）**必须见红**，否则本支不算完成。

★★★ 一处**实测推翻计划**的地方（必须写进日志）
    计划 §0 假设「沿用 E01 的**静止踝锚点**（首帧原位）」。
    `probe_e02_baseline.py` 实测：沿用 `Idle_01@0` 的**弓步站架**时，
    **后脚（R）膝盖到肩的距离 = 757 mm > 臂链 650 mm（ratio 1.164）**，
    深弯腰到 drop −180 mm / 躯干 62° 仍只降到 1.124
    ⟹ **「双手扶膝」在弓步下几何不可达**（不是参数没调好，是姿势族不匹配）。
    `_e02_scan.py` 二次扫描：**对称站架**（双踝 x ±0.150、y −0.180）+ drop −150 mm
    + 躯干 74° + 髋后移 60 mm ⟹ ratio **0.932**（肘部微屈，自然）。
    ⟹ 本支的**过渡段要迈一步**（后脚从 y +0.140 走到 −0.180），
      **hold 段双脚锁死**（`exh_foot_lock_ok` 只在 hold 段判，见下）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_exhausted.py
    SKIP_RENDER=1      只跑门禁不渲图（迭代用）
    E02_TRACE=1        逐帧打印弯腰包络 / 呼吸 / 手到膝距离 / 脚锁误差

反向验证（§4 第 7 步，九组）：
    E02_TP_SEAM_ZERO=1  ① 首帧改零位             ⟹ `seam_in_ok`
    E02_TP_HANDFAR=1    ② ★★★ 手离开膝           ⟹ `exh_hand_on_knee_ok` / 像素
    E02_TP_NOBREATH=1   ③ 不呼吸                 ⟹ `exh_breath_ok` / 像素
    E02_TP_NOBEND=1     ④a 不弯腰                ⟹ `exh_bend_depth_ok`
    E02_TP_TOODEEP=1    ④b 弯过头                ⟹ `exh_bend_depth_ok`（区间另一端）
    E02_TP_HANDCLIP=1   ⑤ ★ 手插进大腿          ⟹ `hand_leg_no_clip_ok`
    E02_TP_FOOTSWAY=1   ⑥ 脚跟着滑（hold 段）    ⟹ `exh_foot_lock_ok` / 像素
    E02_TP_LOOPBREAK=1  ⑦ 末帧不闭合             ⟹ `loop_seamless` / `end_matches_start_ok`
    E02_TP_ONESHOT=1    ⑧ 呼吸退化成「只吸不吐」  ⟹ `exh_breath_period_ok`
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as IDLE   # noqa: E402
import probe_d01_guard as PD  # noqa: E402

NAME = "Exhausted"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_SET = set(ARM_BONES)
ARM_LEN_UP = 0.328
ARM_LEN_LO = 0.224 + 0.098          # forearm + hand 视作一根刚性段


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


def _env_b(key):
    return os.environ.get(key, "0").strip() not in ("", "0", "false", "False")


# =============================================================== 接缝
# ★ 上游 = `Idle_01@0`。★ 实测（`probe_e02_baseline.py`，**复核不是照抄**）：
#   `Idle_01@0` vs `Stun@末帧(120)` 逐骨世界矩阵最差差 = **0.000258123 mm**
#   （elem 4.77e-7）⟹ 两个候选**代价完全相等**，只能按语义选。
#   选 `Idle_01@0` 的理由：**虚弱是「独立的力竭状态」，不是「眩晕的下一步」**；
#   且 `Hit_Head@末帧` 实测与它同一姿态 ⟹ 选它也保住 `Hit_Head → Exhausted` 的无缝性。
SEAM_ACTION = os.environ.get("E02_SEAM_ACTION", "Idle_01")
SEAM_FRAME = _env_i("E02_SEAM_FRAME", 0)

# =============================================================== 时间轴
# ★ 帧预算：**沿用 E01 登记的 120 帧 / 2.0 s 上界**（显式声明，不是悄悄超）。
#   结构：站架 →（22 帧）迈步下沉弯腰 →（72 帧）扶膝喘气 2 周期 →（22 帧）直身收步 → 站架。
TOTAL = _env_i("E02_TOTAL", 120)
START = 0
END = TOTAL
BEND_END = _env_i("E02_BEND_END", 22)      # 弯腰到位
RISE_START = _env_i("E02_RISE_START", 98)  # 开始直身
CYCLES = _env_f("E02_CYCLES", 2.0)         # hold 段呼吸周期数（整数 ⟹ 归零）

# =============================================================== 弯身参数
PELVIS_DROP = _env_f("E02_DROP", -0.145)   # 骨盆下降（米；站架 −0.070 之上再降）
HIP_BACK = _env_f("E02_HIP_BACK", 0.060)   # 髋后移（米）—— 弯腰时屁股后坐
BEND_DEG = _env_f("E02_BEND_DEG", 74.0)    # 躯干总前倾（度）
BEND_DIST = (("pelvis", 0.16), ("spine_01", 0.24), ("spine_02", 0.24),
             ("chest", 0.24), ("neck", 0.06), ("head", 0.06))
ANKLE_X = _env_f("E02_ANKLE_X", 0.150)
ANKLE_Y = _env_f("E02_ANKLE_Y", -0.180)
STEP_LIFT = _env_f("E02_STEP_LIFT", 0.040)  # 迈步时抬脚（米）
ABDUCT_DEG = 4.3

# ★ 拳头目标 = 膝盖 + 本偏移（世界）。做法与依据见 `probe_e02_baseline` / 渲染目检。
# ★★ 实测修正（`_e02_diag.log`）：原值 `(0, +0.020, +0.085)`（膝**上方** 85 mm）
#    会把拳头放进**大腿胶囊里** —— `limb_clearance = −54.69 mm`（拳心到 `thigh.L`
#    轴只有 50.2 mm，胶囊半径 105 mm）。原因：膝是**大腿胶囊的端头**，
#    离膝 85 mm 的点必然在半径 105 mm 的球冠内。
#    ⟹ 手必须放在膝**前方**（世界 −Y，角色正面）：`|offset| ≥ 105 mm` 就出了大腿胶囊，
#      而 `|offset| ≤ 140 mm` 又满足「扶膝」阈值 ⟹ 取 **|offset| = 127.5 mm**。
KNEE_OFFSET = (0.0, _env_f("E02_KNEE_OFF_Y", -0.125),
               _env_f("E02_KNEE_OFF_Z", 0.025))
ELBOW_DIR = {"L": Vector((1.0, 0.55, -0.10)), "R": Vector((-1.0, 0.55, -0.10))}

# =============================================================== 呼吸
BR_CHEST = _env_f("E02_BR_CHEST", 4.5)     # 胸腔 rx 幅（度）
BR_SPINE = _env_f("E02_BR_SPINE", 1.5)
BR_SHOULDER = _env_f("E02_BR_SHOULDER", 6.0)
BR_PELVIS = _env_f("E02_BR_PELVIS", 0.004)  # 骨盆升降（米）
ARM_EASE = _env_f("E02_ARM_EASE", 2.25)    # 手臂混合因子 = 弯腰包络^本值

# =============================================================== 阈值
FOOT_LOCK_MM = _env_f("E02_FOOT_LOCK", 0.5)
HAND_KNEE_MAX_MM = _env_f("E02_HAND_KNEE_MAX", 140.0)
HAND_KNEE_FOLLOW_MM = _env_f("E02_HAND_FOLLOW", 45.0)
HAND_ABOVE_MM = _env_f("E02_HAND_ABOVE", 10.0)
BEND_DROP_RANGE = (_env_f("E02_DROP_LO", 40.0), _env_f("E02_DROP_HI", 145.0))
BEND_LEAN_RANGE = (_env_f("E02_LEAN_LO", 250.0), _env_f("E02_LEAN_HI", 850.0))
BREATH_RANGE = (_env_f("E02_BR_LO", 8.0), _env_f("E02_BR_HI", 70.0))
BREATH_MIN_CROSS = _env_i("E02_BR_CROSS", 3)
BREATH_PERIOD_RANGE = (_env_f("E02_BR_P_LO", 25.0), _env_f("E02_BR_P_HI", 60.0))
SOLE_BAND = (-2.0, 6.0)
NO_SNAP_END_DEG = _env_f("E02_SNAP_END", 6.0)
SEAM_POS_MAX_MM = _env_f("E02_SEAM_POS", 0.01)
SEAM_DIR_MAX_DEG = _env_f("E02_SEAM_DIR", 0.05)
CLIP_MAX_MM = _env_f("E02_CLIP_MAX", 0.0)
ARM_R = 0.042
LEG_THIGH_R = 0.105
LEG_SHIN_R = 0.095
REACH_MAX_RATIO = 0.995

# =============================================================== 取景
# ★★ 本支**自己立基准**（项目惯例：不许照抄上一支）。
#   主运动在 **YZ 平面**（弯腰 + 下沉 + 迈步），与 D13~D19 同族
#   ⟹ **主检用侧视**（正面会把弯腰方向压成视轴，读不出来）。
#   弯腰后身体包络：z ∈ [0, 1.40]、y ∈ [−0.85, +0.40] ⟹ 取景中心 y −0.25 / z 0.72，
#   ortho 1.90 作用在长边（高）⟹ 竖直 [−0.23, 1.67]、水平 1.347 m ⟹ y [−0.92, +0.42]。
VIEW_E02_SIDE = ("side", (4.2, -0.25, 0.72), (0.0, -0.25, 0.72), 1.90,
                 (780, 1100))
VIEW_E02_FRONT = ("front", (0.0, -5.6, 0.72), (0.0, -0.25, 0.72), 1.90,
                  (780, 1100))

# =============================================================== 反向验证旋钮
SEAM_ZERO = _env_b("E02_TP_SEAM_ZERO")
HAND_FAR = _env_b("E02_TP_HANDFAR")
HAND_FAR_V = (_env_f("E02_TP_HANDFAR_Y", -0.22), _env_f("E02_TP_HANDFAR_Z", 0.20))
NO_BREATH = _env_b("E02_TP_NOBREATH")
NO_BEND = _env_b("E02_TP_NOBEND")
TOO_DEEP = _env_b("E02_TP_TOODEEP")
TOO_DEEP_MM = _env_f("E02_TP_TOODEEP_MM", 140.0)
HAND_CLIP = _env_b("E02_TP_HANDCLIP")
HAND_CLIP_MM = _env_f("E02_TP_HANDCLIP_MM", 110.0)
FOOT_SWAY = _env_b("E02_TP_FOOTSWAY")
FOOT_SWAY_MM = _env_f("E02_TP_FOOTSWAY_MM", 55.0)
LOOP_BREAK = _env_b("E02_TP_LOOPBREAK")
ONE_SHOT = _env_b("E02_TP_ONESHOT")
TRACE = _env_b("E02_TRACE")

# =============================================================== 模块级表
BASE = {}
BENT = {}
ANCHOR = {}
TARGET = {}
BONE_LIST = []


# =============================================================== 包络
def _smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def bend_env(frame):
    """弯腰包络 B(f) ∈ [0,1]；★ f=0 与 f=N 上**恒等于 0**。"""
    if NO_BEND:
        return 0.0
    if TOO_DEEP:
        return 1.0
    if frame <= BEND_END:
        return _smoothstep(frame / float(max(1, BEND_END)))
    if frame >= RISE_START:
        return _smoothstep((TOTAL - frame) / float(max(1, TOTAL - RISE_START)))
    return 1.0


def breath_raw(frame):
    """hold 段呼吸（-1..1）：φ 在 hold 两端为 0 ⟹ 端点归零。"""
    if NO_BREATH:
        return 0.0
    span = float(RISE_START - BEND_END)
    if frame <= BEND_END or frame >= RISE_START:
        return 0.0
    phi = 2.0 * math.pi * CYCLES * (frame - BEND_END) / span
    if ONE_SHOT:
        return math.sin(math.pi * (frame - BEND_END) / span)
    return math.sin(phi) - math.sin(0.0)


def breath_env(frame):
    return bend_env(frame) * breath_raw(frame)


def arm_env(frame):
    """手臂的混合因子 = 弯腰包络的幂（★ 与躯干**同一个包络源**，只是换了曲线）。

    为什么手臂要**单独一条曲线**（实测依据，不是审美）：
      手臂到位时要走 **74.8°**（`forearm.R` 的 rz），而末 8 帧的躯干包络只走
      `Δb = 0.3005`。若手臂照抄 `b`，单帧最大步 = **9.24°**（实测 `[112, forearm.R]`）
      ⟹ `no_snap_stop_ok`（≤ 6.0°）红。
      `b^e` 在 `b→0` 处一阶/二阶导都是 0 ⟹ **接缝处手臂角速度归零**
      （实测 `loop_velocity_ok`：首 = 末 = 0.8683°），中段仍然到位。
      指数由实测反推：末 8 帧内 |Δ(b^e)| ≤ 6.0 / 142.2 = **0.0422**；
      实测 `b^1 → 0.0646`（9.24° ✗）、`b^2.25 → 0.0368`（**5.22° ✓**）。
    """
    return bend_env(frame) ** ARM_EASE


def _crossings(series):
    mean = sum(series) / float(len(series))
    dev = [v - mean for v in series]
    cross = []
    for index in range(1, len(dev)):
        if dev[index - 1] == 0.0:
            continue
        if (dev[index - 1] > 0.0) != (dev[index] > 0.0):
            cross.append(index)
    if len(cross) < 2:
        return len(cross), None
    span = cross[-1] - cross[0]
    return len(cross), 2.0 * span / float(len(cross) - 1)


# =============================================================== 脚锁
def lock_feet(arm, pose, want, iters=8, damp=0.85):
    """把双踝**闭环**钉在 `want`（世界坐标 dict）上，就地改 `pose`。

    ★ 照抄 E01 的结构（x 通道反馈进 `thigh.rz`），差别只有一处：
      本支的 `want` 是**逐帧会动**的（过渡段迈步），不是固定锚点。
    """
    tgt = {s: Vector(want[s]) for s in SIDES}
    rz = {s: pose.get("thigh." + s, (0.0, 0.0, 0.0))[2] for s in SIDES}
    pelvis_rx = pose.get("pelvis", (0.0, 0.0, 0.0))[0]
    worst = 0.0
    for _ in range(iters):
        A.apply_pose(arm, pose)
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            th, sh = A.leg_ik(hip.y, hip.z, tgt[side].y, tgt[side].z,
                              tilt_deg=pelvis_rx)
            pose["thigh." + side] = (th, 0.0, rz[side])
            pose["shin." + side] = (sh, 0.0, 0.0)
        A.apply_pose(arm, pose)
        for side in SIDES:
            pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
        A.apply_pose(arm, pose)
        for side in SIDES:
            err = Vector(A.bone_world(arm, "foot." + side, "head")) - want[side]
            tgt[side] = tgt[side] - err * damp
            rz[side] = rz[side] + (1.0 / 0.01309) * err.x * damp
            worst = max(worst, err.length * 1000.0)
    return worst


def ankle_target(frame, side):
    """过渡段迈步：踝目标从站架踝走到对称站架踝（远的那个抬脚）。"""
    b = bend_env(frame)
    start = Vector(ANCHOR[side])
    end = Vector(TARGET[side])
    point = start.lerp(end, b)
    if (end - start).length > 0.05:
        point.z += STEP_LIFT * math.sin(math.pi * min(1.0, max(0.0, b)))
    if FOOT_SWAY and bend_env(frame) >= 0.999:
        # ⑥ hold 段脚跟着滑（反向验证用）
        # ★★ 实测修正（`_e02_px1.log`）：**原按 X（横向）晃，对本支是惰性旋钮**。
        #   本支主检是**侧视**（相机沿 +X 看）⟹ 视轴 = X ⟹ X 向晃动**在画面里
        #   完全不可见**，像素级 `px_exh_foot_lock_can_fail_ok` 因此**判不出**红
        #   （实测控制重渲脚带左右缘漂 0.0 / 1.0 px —— 与基线一模一样）。
        #   ⟹ 改为**按 Y（前后）晃**：前后滑步**同样是「脚没锁住」**，但
        #   **侧视可见**（横轴 = Y）⟹ 骨架级 `exh_foot_lock_ok`（踝漂 3D 距离）
        #   与像素级 `px_exh_foot_lock_ok`（脚带左右缘）**同时见红**。
        #   ★ 这不是放宽容差，是**换了一个本例机位看得见的扰动方向**。
        point.y += (FOOT_SWAY_MM / 1000.0) * math.sin(
            2.0 * math.pi * CYCLES * (frame - BEND_END)
            / float(RISE_START - BEND_END))
    return point


# =============================================================== 臂 IK
def seat_arm(arm, pose, targets):
    """把拳头摆到 `targets`（世界坐标）：上臂 + （前臂+手）两段位置 IK。"""
    A.apply_pose(arm, pose)
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        shoulder = Vector(A.bone_world(arm, up, "head"))
        target = Vector(targets[side])
        delta = target - shoulder
        limit = (ARM_LEN_UP + ARM_LEN_LO) * 0.9995
        distance = max(1e-4, min(delta.length, limit))
        axis = (delta.normalized() if delta.length > 1e-9
                else Vector((0.0, 0.0, -1.0)))
        bulge = ELBOW_DIR[side] - axis * ELBOW_DIR[side].dot(axis)
        if bulge.length < 1e-6:
            bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
        bulge.normalize()
        cos_sh = max(-1.0, min(1.0, (ARM_LEN_UP ** 2 + distance ** 2
                                     - ARM_LEN_LO ** 2)
                               / (2.0 * ARM_LEN_UP * distance)))
        sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
        elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * ARM_LEN_UP
        pose[up] = A.aim_bone(arm, up, elbow - shoulder)
        pose[fo] = A.aim_bone(arm, fo, target - elbow)
        pose[hd] = A.aim_bone(arm, hd, target - elbow)
    return pose


def fist_target(arm, side):
    knee = Vector(A.bone_world(arm, "shin." + side, "head"))
    off = Vector(KNEE_OFFSET)
    if HAND_FAR:
        off = off + Vector((0.0, HAND_FAR_V[0], HAND_FAR_V[1]))
    if HAND_CLIP:
        # ⑤ 手插进大腿：把拳头从「膝前」推回「膝上」⟹ 穿进大腿胶囊
        #   （基底偏移在 −Y，所以往 +Y 推 110 mm 就落到膝上方 ≈ 原缺陷位置）
        off = off + Vector((0.0, HAND_CLIP_MM / 1000.0, 0.0))
    return knee + off


# =============================================================== 姿态装配
def exh_pose(arm, frame):  # noqa: C901
    b = bend_env(frame)
    br = breath_env(frame)

    pose = {}
    for key in set(BASE) | set(BENT):
        if key == "@loc":
            continue
        va = BASE.get(key, (0.0, 0.0, 0.0))
        vb = BENT.get(key, (0.0, 0.0, 0.0))
        if key in ARM_SET:
            # ★★ 实测修正（`_e02_diag2.log`）：`BENT` 里**没有手臂**，
            #   若这里照常按 `(1−b)` 衰减，末尾的「与 IK 混合」会再乘一次
            #   `(1−b)` ⟹ 实际是 `(1−b)²·站架 + b·IK`（**非线性**）。
            #   后果（都是实测出来的）：
            #     ① 手臂在过渡段**过早甩到位** ⟹ 前臂扫过股四头肌 ⟹
            #        f=21 穿模 −56.3 mm；
            #     ② 靠近接缝处手臂角速度是设计值的 ~3 倍 ⟹
            #        f=114 `forearm.R` 12.94°/帧 ⟹ `no_snap_stop_ok` 红。
            #   ⟹ 手臂在这一步**不动**，交给末尾**一次性**线性混合。
            vb = va
        pose[key] = tuple(x + (y - x) * b for x, y in zip(va, vb))
    pose["root"] = (0.0, 0.0, 0.0)
    pose.update(A.FIST)

    # ---- 呼吸（只在躯干；★ 与弯腰同一个包络 ⟹ 端点归零）------------------
    if br != 0.0:
        for name, drx in (("chest", -BR_CHEST), ("spine_02", -BR_SPINE),
                          ("neck", BR_SPINE * 0.5), ("head", -BR_SPINE * 0.5),
                          ("shoulder.L", BR_SHOULDER),
                          ("shoulder.R", BR_SHOULDER)):
            rx, ry, rz = pose.get(name, (0.0, 0.0, 0.0))
            pose[name] = (rx + drx * br, ry, rz)

    # ---- 骨盆位移（弯腰下沉 + 髋后移 + 呼吸升降）-------------------------
    base_loc = BASE.get("@loc", {}).get("pelvis", (0.0, 0.0, 0.0))
    bent_loc = BENT.get("@loc", {}).get("pelvis", (0.0, 0.0, 0.0))
    loc = tuple(x + (y - x) * b for x, y in zip(base_loc, bent_loc))
    # ★ 骨骼局部 location：X→世界+X、**Y→世界+Z**、Z→世界−Y ⟹ 世界升降加在 loc[1]。
    dz = BR_PELVIS * br
    if TOO_DEEP:
        dz -= TOO_DEEP_MM / 1000.0
    pose["@loc"] = {"pelvis": (loc[0], loc[1] + dz, loc[2])}

    # ---- 腿：逐帧闭环锁到（会动的）踝目标 --------------------------------
    want = {s: ankle_target(frame, s) for s in SIDES}
    lock_err = lock_feet(arm, pose, want)

    # ---- 臂：对**当前帧的膝盖**重解，再按 `arm_env` 与站架臂混合（保证接缝）----
    ba = arm_env(frame)
    A.apply_pose(arm, pose)
    ik_pose = dict(pose)
    seat_arm(arm, ik_pose, {s: fist_target(arm, s) for s in SIDES})
    for name in ARM_BONES:
        va = pose.get(name, (0.0, 0.0, 0.0))
        vb = ik_pose.get(name, (0.0, 0.0, 0.0))
        pose[name] = tuple(x + (y - x) * ba for x, y in zip(va, vb))

    if LOOP_BREAK and frame == TOTAL:
        rx, ry, rz = pose["chest"]
        pose["chest"] = (rx + 4.0, ry, rz + 4.0)

    if TRACE:
        A.apply_pose(arm, pose)
        dists = {s: round((Vector(A.bone_world(arm, "hand." + s, "tail"))
                           - Vector(A.bone_world(arm, "shin." + s, "head"))).length
                          * 1000.0, 1) for s in SIDES}
        print("E02_TRACE f=%3d B=%.3f br=%+.3f lock=%.4f hand2knee=%s"
              % (frame, b, br, lock_err, dists))
    return pose


# =============================================================== 快照
def world_mats(arm, action, frame):
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    out = {}
    for name in BONE_LIST:
        if name in arm.pose.bones:
            out[name] = (arm.matrix_world @ arm.pose.bones[name].matrix).copy()
    return out


def _mat_delta(a, b):
    pos = (a.translation - b.translation).length * 1000.0
    dirs = []
    for index in range(3):
        va = a.to_3x3().col[index]
        vb = b.to_3x3().col[index]
        cos = max(-1.0, min(1.0, va.normalized().dot(vb.normalized())))
        dirs.append(math.degrees(math.acos(cos)))
    return pos, max(dirs)


def _worst_step(samples, i0, i1):
    worst, at = 0.0, None
    ea, eb = samples[i0]["euler"], samples[i1]["euler"]
    for name in set(ea) | set(eb):
        va = ea.get(name, (0.0, 0.0, 0.0))
        vb = eb.get(name, (0.0, 0.0, 0.0))
        step = max(abs(x - y) for x, y in zip(va, vb))
        if step > worst:
            worst, at = step, (samples[i1]["frame"], name)
    return worst, at


def limb_clearance(arm):
    """臂骨采样点到**腿胶囊面**的最小外距（正 = 有间隙，负 = 已穿模）。"""
    pts = []
    for side in SIDES:
        for name in ARM_BONES:
            h = Vector(A.bone_world(arm, name, "head"))
            t = Vector(A.bone_world(arm, name, "tail"))
            for i in range(9):
                pts.append(h.lerp(t, i / 8.0))
    worst = 1e9
    for side in SIDES:
        for bone_name, radius in (("thigh." + side, LEG_THIGH_R),
                                  ("shin." + side, LEG_SHIN_R)):
            a = Vector(A.bone_world(arm, bone_name, "head"))
            b = Vector(A.bone_world(arm, bone_name, "tail"))
            ab = b - a
            for p in pts:
                t = 0.0 if ab.length_squared < 1e-12 else max(
                    0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
                worst = min(worst, (p - (a + ab * t)).length - radius)
    return worst * 1000.0


# =============================================================== 专属门禁
def exh_assertions(arm, action, samples, meshes):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    frames = [s["frame"] for s in samples]
    hold = [f for f in frames if BEND_END <= f <= RISE_START]

    # ---- 脚锁（★ 只在 hold 段判：过渡段本支**故意迈了一步**）------------
    ref = {"foot": {}, "toe": {}}
    for side in SIDES:
        for tag, key in (("foot", "foot." + side), ("toe", "toe." + side)):
            ref[tag][side] = Vector(samples[hold[0] - START][key])
    drift = {s: 0.0 for s in SIDES}
    toe_drift = {s: 0.0 for s in SIDES}
    step_travel = {s: 0.0 for s in SIDES}
    for sample in samples:
        for side in SIDES:
            for tag, key, store in (("foot", "foot." + side, drift),
                                    ("toe", "toe." + side, toe_drift)):
                d = (Vector(sample[key]) - ref[tag][side]).length * 1000.0
                if sample["frame"] in hold:
                    store[side] = max(store[side], d)
            step_travel[side] = max(step_travel[side],
                                    (Vector(sample["foot." + side])
                                     - Vector(samples[0]["foot." + side])).length
                                    * 1000.0)
    res["exh_hold_ankle_drift_mm"] = {k: round(v, 4) for k, v in drift.items()}
    res["exh_hold_toe_drift_mm"] = {k: round(v, 4) for k, v in toe_drift.items()}
    res["exh_step_travel_mm"] = {k: round(v, 2) for k, v in step_travel.items()}
    res["exh_foot_lock_ok"] = bool(
        max(max(drift.values()), max(toe_drift.values())) <= FOOT_LOCK_MM)
    res["exh_foot_lock_note"] = (
        "★ 本支的「脚不动」**只在 hold 段 [%d, %d] 判**：过渡段本支**故意迈了一步**"
        "（实测 R 脚行程 %.1f mm）—— 因为 `probe_e02_baseline` 实测出"
        "**弓步站架下后膝不可达**（ratio 1.164 > 1），「双手扶膝」必须换对称站架。"
        "★ 这不是放宽容差，是判据换了适用的时间段，理由由实测给出（见文末日志）。"
        % (BEND_END, RISE_START, res["exh_step_travel_mm"]["R"]))

    # ---- 弯腰深度（★ 两端都卡）-----------------------------------------
    pelvis = [Vector(s["pelvis"]) for s in samples]
    p0 = Vector(samples[0]["pelvis"]).z
    p_hold = min(Vector(s["pelvis"]).z for s in samples if s["frame"] in hold)
    res["exh_pelvis_drop_mm"] = round((p0 - p_hold) * 1000.0, 3)
    res["exh_bend_depth_ok"] = bool(
        BEND_DROP_RANGE[0] <= res["exh_pelvis_drop_mm"] <= BEND_DROP_RANGE[1])
    head = [Vector(s["head.tail"]) for s in samples]
    h0 = Vector(samples[0]["head.tail"]).y
    h_hold = min(Vector(s["head.tail"]).y for s in samples if s["frame"] in hold)
    res["exh_head_lean_mm"] = round((h0 - h_hold) * 1000.0, 3)
    res["exh_bend_lean_ok"] = bool(
        BEND_LEAN_RANGE[0] <= res["exh_head_lean_mm"] <= BEND_LEAN_RANGE[1])
    res["exh_bend_note"] = (
        "★ `exh_bend_depth_ok`（骨盆 z 下降 %s~%s mm）与 `exh_bend_lean_ok`"
        "（头顶前移 %s~%s mm）**两端都卡**：太浅 = 没弯，太深 = 蹲下去了。"
        % (BEND_DROP_RANGE[0], BEND_DROP_RANGE[1],
           BEND_LEAN_RANGE[0], BEND_LEAN_RANGE[1]))

    # ---- 呼吸（★ 纵向；载体 = 胸骨顶 z）---------------------------------
    sternum = [(s["frame"], Vector(s["neck"]).z) for s in samples
               if s["frame"] in hold]
    zs = [v for _f, v in sternum]
    res["exh_breath_mm"] = round((max(zs) - min(zs)) * 1000.0, 3)
    cross, period = _crossings(zs)
    res["exh_breath_crossings"] = cross
    res["exh_breath_period_frames"] = None if period is None else round(period, 3)
    res["exh_breath_ok"] = bool(BREATH_RANGE[0] <= res["exh_breath_mm"]
                                <= BREATH_RANGE[1])
    res["exh_breath_period_ok"] = bool(
        cross >= BREATH_MIN_CROSS and period is not None
        and BREATH_PERIOD_RANGE[0] <= period <= BREATH_PERIOD_RANGE[1])
    res["exh_breath_note"] = (
        "★ 换载体：E01 的横向摇晃量的是**列心**（面积列心 / 头部横行程），"
        "本支是**纵向呼吸**，改量**胸骨顶（`neck` = chest.tail）的世界 z**。"
        "阈值 %.0f~%.0f mm、过零 ≥ %d、周期 %.0f~%.0f 帧。"
        % (BREATH_RANGE[0], BREATH_RANGE[1], BREATH_MIN_CROSS,
           BREATH_PERIOD_RANGE[0], BREATH_PERIOD_RANGE[1]))

    # ---- ★★★ 手扶膝 -----------------------------------------------------
    # ★ 不往 `anim_lib.PROBE_BONES` 里加 `shin.*`（那是全项目共享的口径，
    #   动它会改到已完成的 57 支的读数口径）⟹ 这里现取膝盖世界坐标。
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    dist = {s: [] for s in SIDES}
    above = {s: [] for s in SIDES}
    for frame in hold:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            knee = Vector(A.bone_world(arm, "shin." + side, "head"))
            fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
            dist[side].append((fist - knee).length * 1000.0)
            above[side].append((fist.z - knee.z) * 1000.0)
    all_d = dist["L"] + dist["R"]
    res["exh_hand_knee_mm"] = {s: [round(min(dist[s]), 1), round(max(dist[s]), 1)]
                               for s in SIDES}
    res["exh_hand_knee_follow_mm"] = round(
        max(max(dist[s]) - min(dist[s]) for s in SIDES), 3)
    res["exh_hand_above_knee_mm"] = {s: round(min(above[s]), 1) for s in SIDES}
    res["exh_hand_on_knee_ok"] = bool(
        max(all_d) <= HAND_KNEE_MAX_MM
        and res["exh_hand_knee_follow_mm"] <= HAND_KNEE_FOLLOW_MM)
    res["exh_hand_above_knee_ok"] = bool(
        min(min(above[s]) for s in SIDES) >= HAND_ABOVE_MM)
    res["exh_hand_note"] = (
        "★★★ **本支的命门**：拳头（`hand.*.tail`）到**同侧膝盖**（`shin.*` head）的"
        "世界距离，hold 段全程 ≤ %.0f mm；且**跟得住动目标** —— 膝盖随呼吸升降"
        "（实测 3 mm 骨盆升降让膝走 %.2f mm），拳头-膝距离的**波动** ≤ %.0f mm"
        "（若把手钉在**世界定点**，这个波动会等于膝盖的行程 ⟹ 红）。"
        "`exh_hand_above_knee_ok` = 拳头必须在膝**上方**（≥ %.0f mm）"
        "（读成「手在膝下面」= 扶的不是膝）。"
        % (HAND_KNEE_MAX_MM, KNEE_MOTION_MM, HAND_KNEE_FOLLOW_MM, HAND_ABOVE_MM))

    # ---- 穿模（臂 vs 头盒 沿用 + ★ 新增 臂 vs 腿）------------------------
    worst_clip, clip_at = 0.0, None
    worst_limb, limb_at = 1e9, None
    for frame in sorted(set(list(range(0, TOTAL + 1, 3)) + hold[:1] + hold[-1:])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, clip_at = clip["clip_max_mm"], (frame, clip["clip_at"])
        limb = limb_clearance(arm)
        if limb < worst_limb:
            worst_limb, limb_at = limb, frame
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = clip_at
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)
    res["hand_leg_clearance_mm"] = round(worst_limb, 2)
    res["hand_leg_clearance_frame"] = limb_at
    res["hand_leg_no_clip_ok"] = bool(worst_limb >= 0.0)
    res["clip_note"] = (
        "★ `no_face_clip_ok` 只量**臂 vs 头盒**（D01 起的老口径）——本支还必须量"
        "**臂 vs 腿**（手 / 前臂 / 大腿挤在一个小区域，计划 §1 风险 2）。"
        "`hand_leg_clearance_mm` = 臂骨采样点到腿胶囊面（大腿 r=%.3f / 小腿 r=%.3f）"
        "的最小外距，**负 = 已穿模**。" % (LEG_THIGH_R, LEG_SHIN_R))

    # ---- 贴地（★ 迈步的那只脚只在 hold 段判）----------------------------
    sole = {s: [] for s in SIDES}
    for frame in sorted(set(list(range(0, TOTAL + 1, 2)) + [TOTAL])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        for side in SIDES:
            if low[side] is not None:
                sole[side].append((frame, low[side][2] * 1000.0))
    hold_sole = [z for s in SIDES for f, z in sole[s] if f in hold]
    res["exh_sole_min_mm"] = round(min(hold_sole), 3)
    res["exh_sole_max_mm"] = round(max(hold_sole), 3)
    res["exh_sole_hold_range_mm"] = {
        s: round(max(z for f, z in sole[s] if f in hold)
                 - min(z for f, z in sole[s] if f in hold), 3) for s in SIDES}
    res["sole_ground_ok"] = bool(SOLE_BAND[0] <= res["exh_sole_min_mm"]
                                 and res["exh_sole_max_mm"] <= SOLE_BAND[1])
    res["ground_hold_ok"] = bool(max(res["exh_sole_hold_range_mm"].values())
                                 <= 4.0)
    res["sole_note"] = ("★ 迈步脚的鞋底在过渡段会抬起（实测单脚最高抬 %.0f mm），"
                        "所以贴地判据只取 **hold 段**。" % (STEP_LIFT * 1000.0))

    # ---- 收招 / 过缝 ----------------------------------------------------
    snap, snap_at = 0.0, None
    lo = max(1, TOTAL - 8)
    for index in range(lo, len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > snap:
            snap, snap_at = step, at
    res["no_snap_stop_step_deg"] = round(snap, 4)
    res["no_snap_stop_at"] = snap_at
    res["no_snap_stop_ok"] = bool(snap <= NO_SNAP_END_DEG)
    first_step, _ = _worst_step(samples, 0, 1)
    last_step, _ = _worst_step(samples, len(samples) - 2, len(samples) - 1)
    res["loop_seam_step_first_deg"] = round(first_step, 4)
    res["loop_seam_step_last_deg"] = round(last_step, 4)
    res["loop_velocity_ok"] = bool(
        abs(first_step - last_step) <= 0.25 * max(first_step, last_step, 0.05))

    # ---- 力量传导链（六段；★ 脚段 = 迈步行程，与 E01 反号）--------------
    foot_travel = max(step_travel.values())
    hip_travel = max((p - pelvis[0]).length for p in pelvis) * 1000.0
    knee = []
    for frame in frames[::2]:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            knee.append(arm.pose.bones["shin." + side].rotation_euler.x)
    knee_deg = (max(knee) - min(knee)) * 180.0 / math.pi
    waist = [abs(s["euler"].get("chest", (0.0, 0.0, 0.0))[0]) for s in samples]
    waist_deg = (max(waist) - min(waist)) * 180.0 / math.pi
    shoulder = [Vector(s["upperarm.L"]) for s in samples]
    shoulder_mm = max((p - shoulder[0]).length for p in shoulder) * 1000.0
    hand = [Vector(s["hand.L.tail"]) for s in samples]
    hand_mm = max((p - hand[0]).length for p in hand) * 1000.0
    res["chain_travel"] = {"foot_mm": round(foot_travel, 3),
                           "knee_deg": round(knee_deg, 3),
                           "hip_mm": round(hip_travel, 3),
                           "waist_deg": round(waist_deg, 3),
                           "shoulder_mm": round(shoulder_mm, 3),
                           "hand_mm": round(hand_mm, 3)}
    res["chain_present_ok"] = bool(
        foot_travel > 20.0 and knee_deg > 0.2 and hip_travel > 2.0
        and waist_deg > 2.0 and shoulder_mm > 1.0 and hand_mm > 20.0)

    # ---- 可达性（臂链 & 腿链）-------------------------------------------
    worst_leg, worst_leg_at = 0.0, None
    worst_arm, worst_arm_at = 0.0, None
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            want = Vector(A.bone_world(arm, "foot." + side, "head"))
            ratio = (want - hip).length / ((A.L_THIGH + A.L_SHIN) * REACH_MAX_RATIO)
            if ratio > worst_leg:
                worst_leg, worst_leg_at = ratio, (frame, side)
            sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
            r2 = (fist - sh).length / ((ARM_LEN_UP + ARM_LEN_LO) * REACH_MAX_RATIO)
            if r2 > worst_arm:
                worst_arm, worst_arm_at = r2, (frame, side)
    res["leg_reach_ratio_max"] = round(worst_leg, 5)
    res["leg_reach_ok"] = bool(worst_leg <= 1.0)
    res["arm_reach_ratio_max"] = round(worst_arm, 5)
    res["arm_reach_at"] = worst_arm_at
    res["arm_reach_ok"] = bool(worst_arm <= 1.0)

    res["hold_window"] = [BEND_END, RISE_START]
    res["phase_markers"] = {
        "START": START, "BEND": BEND_END,
        "INHALE_1": BEND_END + (RISE_START - BEND_END) // 4,
        "EXHALE_1": BEND_END + (RISE_START - BEND_END) // 2,
        "INHALE_2": BEND_END + 3 * (RISE_START - BEND_END) // 4,
        "RISE_START": RISE_START, "END": END}
    return res


# =============================================================== 主流程
KNEE_MOTION_MM = 0.0


def boot():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    global BASE, BENT, ANCHOR, TARGET, BONE_LIST, KNEE_MOTION_MM
    if SEAM_ZERO:
        BASE = {}
        A.apply_pose(arm, BASE)
    else:
        BASE = IDLE.idle_pose(arm, 0.0)
    BONE_LIST = sorted(arm.pose.bones.keys())
    # 站架踝（接缝锚）
    ANCHOR = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    # 弯曲姿态：躯干显式给定 + 骨盆位移
    tilt = 4.0 + BEND_DEG * BEND_DIST[0][1]
    BENT = {
        "pelvis": (tilt, 0.0, 0.0),
        "spine_01": (2.0, 0.0, 0.0),
        "spine_02": (2.0, 0.0, 0.0),
        "chest": (0.0, 0.0, 0.0),
        "neck": (-6.0, 0.0, 0.0),
        "head": (5.0, 0.0, 0.0),
        "shoulder.L": (-16.0, 0.0, 0.0),
        "shoulder.R": (-16.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, HIP_BACK, PELVIS_DROP)},
    }
    for name, weight in BEND_DIST[1:]:
        rx, ry, rz = BENT[name]
        BENT[name] = (rx + BEND_DEG * weight, ry, rz)
    # 对称站架踝目标
    TARGET = {s: Vector(((1.0 if s == "L" else -1.0) * ANKLE_X, ANKLE_Y,
                         A.Z_ANKLE_REST)) for s in SIDES}
    # 呼吸让膝盖走多少（供日志；用 ±BR_PELVIS 的骨盆升降实测）
    ks = []
    for dz in (-BR_PELVIS, 0.0, BR_PELVIS):
        pose = {"pelvis": (BENT["pelvis"][0], 0.0, 0.0),
                "@loc": {"pelvis": A.wloc(0.0, HIP_BACK, PELVIS_DROP + dz)}}
        lock_feet(arm, pose, TARGET)
        A.apply_pose(arm, pose)
        ks.append(Vector(A.bone_world(arm, "shin.L", "head")))
    KNEE_MOTION_MM = max((k - ks[1]).length for k in ks) * 1000.0
    return arm, meshes


def knee_screen(arm, action):
    """hold 段逐帧把「拳头目标点」（膝 + 偏移）投影到**侧视**屏幕坐标，供像素探针用。"""
    # side 视图：横轴 = 世界 Y；ortho 作用在长边（高）
    name, loc, tgt, scale, res = VIEW_E02_SIDE
    mm_per_px = scale / float(res[1]) * 1000.0
    floor_row = (scale / 2.0 - loc[2]) / (scale / float(res[1]))
    out = {}
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    for frame in range(START, END + 1):
        if not (BEND_END <= frame <= RISE_START):
            continue
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {}
        for side in SIDES:
            knee = Vector(A.bone_world(arm, "shin." + side, "head"))
            point = knee + Vector(KNEE_OFFSET)
            row[side] = [
                round((point.z * 1000.0) / mm_per_px + floor_row, 3),
                round(res[0] / 2.0 + (point.y * 1000.0 - tgt[1] * 1000.0)
                      / mm_per_px, 3)]
        out[str(frame)] = row
    return {"view": VIEW_E02_SIDE[0], "res": list(VIEW_E02_SIDE[4]),
            "ortho_m": VIEW_E02_SIDE[3], "cam_y": VIEW_E02_SIDE[1][1],
            "cam_z": VIEW_E02_SIDE[1][2], "mm_per_px": round(mm_per_px, 7),
            "floor_row": round(floor_row, 4), "rows": out}


def main():  # noqa: C901
    arm, meshes = boot()
    keyframes = [(frame, exh_pose(arm, frame)) for frame in range(START, END + 1)]
    meta = {
        "anim_id": NAME,
        "loop": True,
        "category": "状态与流程",
        "note": ("虚弱：迈步下沉 → 弯腰 %.0f° 双手扶膝 → 重喘 %g 周期 → 直身站架；"
                 "hold 段双脚锁死（≤%.1f mm）" % (BEND_DEG, CYCLES, FOOT_LOCK_MM)),
        "loop_frames": [START, END],
        "root_motion_m": [0.0, 0.0],
        "hitstop_frames": 0,
        "bend_deg": BEND_DEG,
        "breath_cycles": CYCLES,
        "hand_knee_max_mm": HAND_KNEE_MAX_MM,
        "seam": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
        "frame_bound_note": "★ 沿用 E01 登记的 120 帧 / 2.0 s 上界（循环状态）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    ph = {k: v for k, v in (("START", START), ("BEND", BEND_END),
                            ("INHALE_1", BEND_END + (RISE_START - BEND_END) // 4),
                            ("EXHALE_1", BEND_END + (RISE_START - BEND_END) // 2),
                            ("INHALE_2", BEND_END + 3 * (RISE_START - BEND_END) // 4),
                            ("RISE_START", RISE_START), ("END", END))}
    A.add_markers(action, ph)

    samples = A.sample_animation(arm, action, START, END, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=(),
                                     slide_tolerance_mm=FOOT_LOCK_MM)
    report.update(exh_assertions(arm, action, samples, meshes))

    # 接缝入
    upstream = bpy.data.actions[SEAM_ACTION]
    seam = world_mats(arm, upstream, SEAM_FRAME)
    mine = world_mats(arm, action, 0)
    worst_pos, worst_dir, worst_at = 0.0, 0.0, None
    for bone in BONE_LIST:
        if bone not in seam or bone not in mine:
            continue
        pos, deg = _mat_delta(mine[bone], seam[bone])
        if pos > worst_pos or deg > worst_dir:
            worst_at = bone
        worst_pos = max(worst_pos, pos)
        worst_dir = max(worst_dir, deg)
    report["seam_in_pos_max_mm"] = round(worst_pos, 6)
    report["seam_in_dir_max_deg"] = round(worst_dir, 6)
    report["seam_in_at"] = worst_at
    report["seam_in_ok"] = bool(worst_pos <= SEAM_POS_MAX_MM
                                and worst_dir <= SEAM_DIR_MAX_DEG)
    report["seam_in_src"] = "%s@%d" % (SEAM_ACTION, SEAM_FRAME)

    # 首末闭合：逐元素矩阵比对
    first = world_mats(arm, action, START)
    last = world_mats(arm, action, END)
    end_elem, end_elem_at = 0.0, None
    for bone in BONE_LIST:
        if bone in first and bone in last:
            for r in range(4):
                for c in range(4):
                    d = abs(first[bone][r][c] - last[bone][r][c])
                    if d > end_elem:
                        end_elem, end_elem_at = d, (bone, r, c)
    report["end_matches_start_elem_max"] = end_elem
    report["end_matches_start_elem_at"] = end_elem_at
    report["end_matches_start_ok"] = bool(end_elem <= 1e-6)

    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True and v is not None)
    non_ok = sorted(k for k, v in report.items()
                    if isinstance(v, bool) and v is False)
    report["failed"] = failed
    report["non_ok_bools"] = non_ok
    A.report("E02_REPORT", report)

    stem_only = os.environ.get("E02_STEM_ONLY") == "1"
    if stem_only:
        # 只为像素探针的**反面对照**重渲：同一台相机 + 同一批帧（含手部单件层）。
        # ★ 帧集合 = **hold 段**（`BEND_END..RISE_START`）——与探针三条尺子
        #   （脚锁 / 呼吸 / 手扶膝）的判读窗口**逐帧相同**，且与 `render_hand_layer`
        #   同窗口。★ 这**只是缩小渲染范围**，不碰任何姿态 / 门禁（`E02_DONE`
        #   的 `failed` 在改动前后逐项一致）。
        A.render_pose_sheet(arm, action, list(range(BEND_END, RISE_START + 1)),
                            os.environ.get("E02_STEM", "exhfar"),
                            views=(VIEW_E02_SIDE,))
        render_hand_layer(arm, action, os.environ.get("E02_STEM_HAND", "exhfarhand"))
        print("E02_DONE failed=%s non_ok=%s" % (failed, non_ok))
        return

    if not SKIP_RENDER:
        A.render_pose_sheet(arm, action, list(range(START, END + 1)),
                            "exhwide", views=(VIEW_E02_SIDE,))
        side_frames = sorted(set(list(range(START, END + 1, 3)) + [END]))
        A.render_pose_sheet(arm, action, side_frames, "exh",
                            views=(VIEW_E02_SIDE,))
        key_frames = [0, 11, 22, 40, 60, 80, 98, 109, 120]
        A.render_pose_sheet(arm, action, key_frames, "exhkey",
                            views=(VIEW_E02_SIDE, VIEW_E02_FRONT, A.VIEW_3Q))
        render_hand_layer(arm, action, "exhhand")
        with open(os.path.join(A.PREVIEW_DIR, "_e02_kneescreen.json"), "w",
                  encoding="utf-8") as handle:
            json.dump(knee_screen(arm, action), handle, ensure_ascii=False)
        A.save_project()
        A.export_glb(arm)
    print("E02_DONE failed=%s non_ok=%s" % (failed, non_ok))


def render_hand_layer(arm, action, prefix):
    """只显手部网格渲一层（供 `px_exh_hand_on_knee_ok` 定位手在屏幕上的位置）。"""
    keep = [o for o in bpy.data.objects if o.type == "MESH"
            and (o.name.startswith("Hand_Palm_") or o.name.startswith("Thumb_")
                 or o.name.startswith("Finger_"))]
    hidden = []
    for obj in bpy.data.objects:
        if obj.type == "MESH" and obj not in keep:
            hidden.append((obj, obj.hide_render))
            obj.hide_render = True
    frames = sorted(set(list(range(BEND_END, RISE_START + 1, 6)) + [RISE_START]))
    A.render_pose_sheet(arm, action, frames, prefix, views=(VIEW_E02_SIDE,))
    for obj, was in hidden:
        obj.hide_render = was


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E02_FAILURE " + traceback.format_exc())
