"""anim_stun —— E01 `Stun` 眩晕（E 族第一支 / 第 57 支）。

清单原文：「身体摇晃但**脚尽量保持原位**，方便判定」。

★★★ E01 与 D 族的根本差别（开工前想清楚，写在最上面）：
    D 族 19 支全是**被动挨打**，起点承接上游的击飞 / 倒地姿态；
    E01 是**主动状态** —— 角色**站着**被打出眩晕，摇晃但**脚不动**。
    ⟹ 接缝族完全变了：不再有弹道、不再有墙、不再有命中帧。

★★★ 本支的真风险：**「摇晃但脚不动」是一组互相拉扯的约束**
    · 摇晃的自然写法是"整个身体（含 root）左右晃" ⟹ **脚跟着晃**，直接违反清单原文；
    · 正确做法：摇晃全部放在**骨盆以上的骨链**上，`root` 不参与位移，
      双 `thigh/shin/foot` **闭环数值修正**（不是简单 IK —— 见下）把踝钉在首帧锚点上。
    · ★ 本项目铁律：**没有任何判据盯着的约束等于不存在** ⟹ 必须新建
      `stun_foot_lock_ok`（骨架级）+ `px_stun_foot_lock_ok`（像素级），
      且反向验证 ②（`E01_TP_FOOTSWAY=1`）**必须见红**，否则本支不算完成。

★★★ 本支的工程件 ①：**脚锁 = 闭环数值修正，不是解析 IK**
    实测（`probe_e01_baseline.py`）：躯干总倾角每 1° 会让踝世界坐标漂 **2.13 mm**
    —— 其中**绝大部分来自骨盆 rz**（骨盆转 θ ⟹ 整条腿被带着转，踝走
    `0.75 m × sin θ`），`A.leg_ik` 的 `tilt_deg` 只处理**绕世界 X 的前倾**，
    **处理不了 rz**。⟹ 本支的解法：
      · y / z 两通道：锚在接缝踝上，误差反馈进 IK 目标（同一平面内 1 步收敛）；
      · **x 通道**：误差反馈成 `thigh.rz` 的**反向配平**（实测灵敏度
        `d(ankle.x)/d(thigh.rz) ≈ −0.0131 m/°`，两侧同号）；
      · 反复迭代 6 轮，把残余压到亚毫米（实测见日志）。

★★★ 本支的工程件 ②：**「消失于接缝」的周期函数**
    循环动画首末帧必须**逐位一致**，且首帧还必须**逐位 = 上游**
    （`Idle_01@0`）。两个约束同时满足的构造：每个通道都用
        v(φ) = A · w · [ sin(φ + ψ − δ) − sin(ψ − δ) ]
    —— `φ = 2πk·f/N`，`δ` 是**滞后相位**（越靠上越滞后 = 惯性），
    `ψ` 是通道相位（左右倾 ψ=0、前后倾 ψ=−π/2 ⟹ 合成椭圆晃动）。
    ★ 关键性质：`f=0` 与 `f=N` 时 `v ≡ 0`（**不是"看起来一样"，是恒等于 0**）
    ⟹ 首帧逐位 = 接缝、末帧逐位 = 首帧，两个约束**同时**成立。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_stun.py
    SKIP_RENDER=1    只跑门禁不渲图（迭代用）
    E01_TRACE=1      逐帧打印摇晃量 / 踝误差 / 骨盆高度

反向验证（§4 第 7 步，七组）：
    E01_TP_SEAM_ZERO=1   ① 首帧改零位            ⟹ `seam_in_ok`
    E01_TP_FOOTSWAY=1    ② ★★★ 让脚跟着晃        ⟹ `stun_foot_lock_ok` / `px_stun_foot_lock_ok`
    E01_TP_NOSWAY=1      ③ 摇晃退化成不动        ⟹ `stun_sway_amp_ok` / `px_stun_sway_ok`
    E01_TP_ONESHOT=1     ④ 只晃一次不回来        ⟹ `stun_sway_period_ok`
    E01_TP_LOOPBREAK=1   ⑤ 末帧不闭合            ⟹ `loop_seamless` / `end_matches_start_ok`
    E01_TP_SINK=1        ⑥ 骨盆高度崩掉          ⟹ `stun_height_hold_ok`
    E01_TP_LIFT=1        ⑦ 脚离地                ⟹ `sole_ground_ok`
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

NAME = "Stun"
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


def _env_b(key):
    return os.environ.get(key, "0").strip() not in ("", "0", "false", "False")


# =============================================================== 接缝
# ★ 上游 = `Idle_01@0`。★ 实测（`probe_e01_baseline.py`）：
#   `Hit_Head@0`、`Hit_Head@34`、`Idle_01@0`、`Idle_01@180` **四者逐位同一姿态**
#   （head.tail 实测皆为 (0.0, −104.06, 1713.26) mm），⟹ 「逐骨相对位置差 = 0.000 mm」，
#   两个候选**代价完全相等**。选 `Idle_01@0` 的理由：① 它是**战斗站架**的定义帧，
#   眩晕是"站着被打出状态"，站架是最自然的入口；② 它可由 `IDLE.idle_pose(arm, 0.0)`
#   **同参数复现** ⟹ 首帧逐位由构造保证；③ `Hit_Head@末帧` 实测与它同一姿态，
#   ⟹ 选它同时也保住了 `Hit_Head → Stun` 这条链的无缝性。**两边都不欠。**
SEAM_ACTION = os.environ.get("E01_SEAM_ACTION", "Idle_01")
SEAM_FRAME = _env_i("E01_SEAM_FRAME", 0)

# =============================================================== 时间轴
# ★ 帧预算（计划 §1 风险 4「必须显式申请放宽上界」）：
#   D19 计划 §2 的硬上界是 40 帧 / 0.667 s —— 那是**单次受击**的上界。
#   本支是**循环**状态：时长由「看起来像不像眩晕」决定，不由通用上界决定
#   （A01 `Idle_01` 已登记 180 帧 / 3.0 s 是同一逻辑的先例）。
#   ★ **新上界登记 = 120 帧 / 2.0 s**（本支实测用时 2.0 s，2 个摇晃周期）。
TOTAL = _env_i("E01_TOTAL", 120)
START = 0
END = TOTAL
CYCLES = _env_f("E01_CYCLES", 2.0)      # 摇晃周期数（整数倍 ⟹ 循环闭合）

# =============================================================== 摇晃量
A_LAT = _env_f("E01_LAT", 13.0)         # 左右倾总幅（度，全链累计）
A_FWD = _env_f("E01_FWD", 7.0)          # 前后倾总幅（度）
A_ROLL = _env_f("E01_ROLL", 3.0)        # 头颈自转（度）
A_BOB = _env_f("E01_BOB", 0.0035)       # 骨盆升降（米，0..−3.5 mm）
A_SHIFT = _env_f("E01_SHIFT", 0.007)    # 骨盆左右平移（米，重心转移）
LEG_ITER = _env_i("E01_LEG_ITER", 6)
LEG_DAMP = _env_f("E01_LEG_DAMP", 0.85)
# 实测灵敏度：踝 x 对 thigh.rz 的响应 = −0.75 m × sin(1°) = −13.09 mm/°
THIGH_RZ_GAIN = _env_f("E01_RZ_GAIN", 1.0 / 0.01309)   # ° 每米（误差）

# ★ 摇晃权重表：(rz 权重, rx 权重, ry 权重, 滞后帧)
#   合计归一（rz 与 rx 各自合计 1.0）。★ 骨盆只拿 0.08/0.10 —— 骨盆每转 1°，
#   整条腿被带着转、踝走 13.1 mm（实测），把大头放在它身上等于自找麻烦；
#   而骨盆以上的骨**完全不影响腿**，可以放心给大权重。
SWAY = (
    ("pelvis",   0.08, 0.10, 0.00, 0.0),
    ("spine_01", 0.20, 0.18, 0.00, 1.0),
    ("spine_02", 0.22, 0.20, 0.00, 2.0),
    ("chest",    0.22, 0.20, 0.00, 2.5),
    ("neck",     0.15, 0.16, 0.50, 4.0),
    ("head",     0.13, 0.16, 0.50, 5.0),
)
TORSO = tuple(row[0] for row in SWAY)

# 手臂：跟着身体甩 + 明显滞后（眩晕时手是"被甩"的，不是主动动的）
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_RZ = {"upperarm.L": 3.0, "forearm.L": 2.0, "hand.L": 1.0,
          "upperarm.R": -3.0, "forearm.R": -2.0, "hand.R": -1.0}
ARM_RX = {"upperarm.L": 3.0, "forearm.L": 2.0, "hand.L": 1.0,
          "upperarm.R": 3.0, "forearm.R": 2.0, "hand.R": 1.0}
ARM_LAG = {"upperarm.L": 4.0, "forearm.L": 5.0, "hand.L": 6.0,
           "upperarm.R": 4.0, "forearm.R": 5.0, "hand.R": 6.0}

# =============================================================== 阈值
FOOT_LOCK_MM = _env_f("E01_FOOT_LOCK", 0.5)      # 「原位」上界（实测 0.0035 mm）
HEIGHT_HOLD_MM = _env_f("E01_HEIGHT_HOLD", 12.0)  # 骨盆 z 波动上界
SWAY_AMP_MIN_MM = _env_f("E01_SWAY_AMP_MIN", 100.0)
SWAY_AMP_MAX_MM = _env_f("E01_SWAY_AMP_MAX", 320.0)
SWAY_SIDE_MIN_MM = _env_f("E01_SWAY_SIDE_MIN", 30.0)   # 前后向行程（侧视像素尺子的骨架对应量）
SWAY_MIN_CROSS = _env_i("E01_SWAY_CROSS", 3)
SWAY_PERIOD_RANGE = (_env_f("E01_PERIOD_LO", 40.0), _env_f("E01_PERIOD_HI", 90.0))
SOLE_BAND = (-2.0, 6.0)
SOLE_RANGE_MM = _env_f("E01_SOLE_RANGE", 4.0)
NO_SNAP_END_DEG = _env_f("E01_SNAP_END", 6.0)
SNAP_WINDOW = _env_i("E01_SNAP_WIN", 8)
SEAM_POS_MAX_MM = _env_f("E01_SEAM_POS", 0.01)
SEAM_DIR_MAX_DEG = _env_f("E01_SEAM_DIR", 0.05)
LOOP_VEL_TOL = _env_f("E01_LOOP_VEL", 0.25)      # 过缝速度连续性（相对）
CLIP_MAX_MM = _env_f("E01_CLIP_MAX", 0.0)
REACH_MAX_RATIO = 0.995

# =============================================================== 取景
# ★★ 本支**必须自己立一套基准**（项目惯例：不许照抄上一支）——
#    D17 = −300 mm、D18 = +250 mm、D19 = +200 mm，**全是「人被打飞后的落点中心」**。
#    本支 0..120 帧 `root` 恒为 `(0,0,0)`、骨盆几乎不动（z 波动 7 mm、x 平移 ≤ 7 mm）
#    ⟹ 取景中心就是**世界原点**：横 0.0 / 高 0.90。
#    ★★★ 机位选**正面**（相机沿 +Y 看）：正面横轴 = 世界 **X**
#      ⟹ **本支的左右摇晃只有正面看得见**（侧视沿 −X 看，X 向摇摆正好落在视轴上，
#      完全不可见；侧视只看得见前后摇 + 高度）。所以本支**主检正面**，
#      侧视只作「前后摇 + 脚不动」的辅助目检。
#    竖直：ortho 2.10 作用在**长边**（res 780x1100 ⟹ 长边是高）⟹ 覆盖
#      z ∈ [0.90 − 1.05, 0.90 + 1.05] = [−0.15, 1.95]，身高 1.803 全收。
#    水平：2.10 × 780/1100 = **1.489 m** ⟹ x ∈ [−0.745, +0.745]（躯干 ±0.24、摇晃 ±0.12）。
VIEW_E01_FRONT_WIDE = ("front", (0.0, -5.80, 0.90), (0.0, 0.0, 0.90), 2.10,
                       (780, 1100))

# =============================================================== 反向验证旋钮
SEAM_ZERO = _env_b("E01_TP_SEAM_ZERO")      # ① 首帧改零位
FOOT_SWAY = _env_b("E01_TP_FOOTSWAY")       # ② 让脚跟着晃（★ 最关键）
FOOT_SWAY_MM = _env_f("E01_TP_FOOTSWAY_MM", 60.0)
NO_SWAY = _env_b("E01_TP_NOSWAY")           # ③ 摇晃退化成不动
ONE_SHOT = _env_b("E01_TP_ONESHOT")         # ④ 只晃一次不回来
LOOP_BREAK = _env_b("E01_TP_LOOPBREAK")     # ⑤ 末帧不闭合
SINK = _env_b("E01_TP_SINK")                # ⑥ 骨盆高度崩掉
SINK_MM = _env_f("E01_TP_SINK_MM", 80.0)
LIFT = _env_b("E01_TP_LIFT")                # ⑦ 脚离地
LIFT_MM = _env_f("E01_TP_LIFT_MM", 30.0)
TRACE = _env_b("E01_TRACE")

# =============================================================== 模块级表
BASE = {}
ANCHOR = {}
BONE_LIST = []


# =============================================================== 周期函数
def _phase(frame, lag):
    """`φ + ψ − δ` 里的滞后项。★ 滞后的**帧数**换算成**相位**。"""
    return 2.0 * math.pi * CYCLES * (frame - lag) / float(TOTAL)


def _wave(frame, lag, psi):
    """v = sin(φ + ψ − δ) − sin(ψ − δ) —— ★ 在 f=0 与 f=N 上**恒等于 0**。"""
    base = psi - 2.0 * math.pi * CYCLES * lag / float(TOTAL)
    return math.sin(_phase(frame, lag) + psi) - math.sin(base)


def sway_values(frame):
    """返回 {骨: (drx, dry, drz)}；★ 每项在 f=0 / f=N 上恒等于 0。"""
    out = {}
    if NO_SWAY:
        return {name: (0.0, 0.0, 0.0) for name in TORSO + ARM_BONES + ("shoulder.L", "shoulder.R")}
    if ONE_SHOT:
        # ④ 只晃一次不回来：半正弦包络（只在两端过零 ⟹ 过零点不足、周期超出区间）
        half = math.sin(math.pi * frame / float(TOTAL))
        for name, wz, wx, wy, _lag in SWAY:
            out[name] = (A_FWD * wx * half, 0.0, A_LAT * wz * half)
        return out
    for name, wz, wx, wy, lag in SWAY:
        out[name] = (A_FWD * wx * _wave(frame, lag, -math.pi / 2.0),
                     0.0,
                     A_LAT * wz * _wave(frame, lag, 0.0))
    return out


def arm_values(frame):
    out = {}
    for name in ARM_BONES:
        lag = ARM_LAG[name]
        out[name] = (ARM_RX[name] * _wave(frame, lag, -math.pi / 2.0),
                     0.0,
                     ARM_RZ[name] * _wave(frame, lag, 0.0))
    for side in SIDES:
        out["shoulder." + side] = (2.5 * _wave(frame, 2.0, -math.pi / 2.0), 0.0, 0.0)
    return out


def pelvis_shift(frame):
    """骨盆的世界位移增量（米）：(dx 左右, dy 前后, dz 上下)。"""
    if NO_SWAY:
        return (0.0, 0.0, 0.0)
    if ONE_SHOT:
        half = math.sin(math.pi * frame / float(TOTAL))
        return (A_SHIFT * half, 0.0, -A_BOB * half)
    dx = A_SHIFT * _wave(frame, 0.0, 0.0)
    dy = 0.0
    dz = -A_BOB * (1.0 - math.cos(2.0 * math.pi * CYCLES * frame / float(TOTAL)))
    if SINK:
        dz -= (SINK_MM / 1000.0) * (1.0 - math.cos(
            2.0 * math.pi * CYCLES * frame / float(TOTAL))) / 2.0
    return (dx, dy, dz)


# =============================================================== 脚锁
def lock_feet(arm, pose, want):
    """把双踝**闭环**钉在 `want`（世界坐标）上，就地改 `pose`。

    ★ 为什么不是单纯 IK：`A.leg_ik` 是**平面（YZ）解**，`tilt_deg` 只补偿
      **绕世界 X 的前倾**。本支的摇晃有骨盆 rz（左右倾）—— 它把整条腿一起转，
      踝横向漂 `0.75 m × sin(rz)`（实测每 1° 总倾角漂 2.13 mm），平面 IK 里
      **没有任何通道管这件事**。所以 x 通道必须另配一条：误差反馈成 `thigh.rz`。
    """
    if FOOT_SWAY:
        return 0.0, {s: 0.0 for s in SIDES}
    tgt = {s: Vector(want[s]) for s in SIDES}
    # ★ `E01_TP_SEAM_ZERO=1` 时 `BASE = {}` ⟹ `pose` 里可能**没有** `thigh.*`
    #   （第一版直接取下标 ⟹ `KeyError: 'thigh.L'`，整支抛异常而非见红）。
    rz = {s: pose.get("thigh." + s, (0.0, 0.0, 0.0))[2] for s in SIDES}
    pelvis_rx_world = pose.get("pelvis", (0.0, 0.0, 0.0))[0]
    worst = 0.0
    errs = {s: 0.0 for s in SIDES}
    for _ in range(LEG_ITER):
        A.apply_pose(arm, pose)
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            thigh_rx, shin_rx = A.leg_ik(hip.y, hip.z, tgt[side].y, tgt[side].z,
                                         tilt_deg=pelvis_rx_world)
            pose["thigh." + side] = (thigh_rx, 0.0, rz[side])
            pose["shin." + side] = (shin_rx, 0.0, 0.0)
        A.apply_pose(arm, pose)
        for side in SIDES:
            pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
        A.apply_pose(arm, pose)
        for side in SIDES:
            err = Vector(A.bone_world(arm, "foot." + side, "head")) - Vector(want[side])
            tgt[side] = tgt[side] - err * LEG_DAMP
            rz[side] = rz[side] + THIGH_RZ_GAIN * err.x * LEG_DAMP
            errs[side] = err.length * 1000.0
            worst = max(worst, errs[side])
    return worst, errs


# =============================================================== 姿态装配
def stun_pose(arm, frame):
    pose = {}
    for key, value in BASE.items():
        pose[key] = (tuple(value) if not key.startswith("@")
                     else {kk: tuple(vv) for kk, vv in value.items()})
    pose.setdefault("@loc", {})
    pose["@loc"].setdefault("pelvis", (0.0, 0.0, 0.0))
    delta = sway_values(frame)
    for name in TORSO:
        rx, ry, rz = pose.get(name, (0.0, 0.0, 0.0))
        drx, dry, drz = delta[name]
        pose[name] = (rx + drx, ry + dry, rz + drz)
    for name, (drx, dry, drz) in arm_values(frame).items():
        rx, ry, rz = pose.get(name, (0.0, 0.0, 0.0))
        pose[name] = (rx + drx, ry + dry, rz + drz)
    pose["root"] = (0.0, 0.0, 0.0)

    dx, dy, dz = pelvis_shift(frame)
    base_loc = pose["@loc"]["pelvis"]
    if FOOT_SWAY:
        # ② 让整个身体（含脚）跟着左右平移 —— 脚不再锁死
        dx = (FOOT_SWAY_MM / 1000.0) * math.sin(
            2.0 * math.pi * CYCLES * frame / float(TOTAL))
    pose["@loc"]["pelvis"] = (base_loc[0] + dx, base_loc[1] + dz, base_loc[2] - dy)

    if LOOP_BREAK and frame == TOTAL:
        rx, ry, rz = pose["chest"]
        pose["chest"] = (rx + 4.0, ry, rz + 4.0)
        loc = pose["@loc"]["pelvis"]
        pose["@loc"]["pelvis"] = (loc[0] + 0.012, loc[1], loc[2])

    want = {s: Vector(ANCHOR[s]) for s in SIDES}
    if LIFT:
        for s in SIDES:
            want[s].z += LIFT_MM / 1000.0
    worst, errs = lock_feet(arm, pose, want)
    if TRACE:
        print("E01_TRACE f=%3d lock_err_max=%8.4f mm errs=%s pelvis_z=%.3f lat=%.3f"
              % (frame, worst, {k: round(v, 4) for k, v in errs.items()},
                 (arm.matrix_world @ arm.pose.bones["pelvis"].matrix.translation).z * 1000.0,
                 delta["chest"][2]))
    return pose


# =============================================================== 快照工具
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


def _worst_step(samples, index_a, index_b):
    worst, at = 0.0, None
    ea = samples[index_a]["euler"]
    eb = samples[index_b]["euler"]
    for name in set(ea) | set(eb):
        va = ea.get(name, (0.0, 0.0, 0.0))
        vb = eb.get(name, (0.0, 0.0, 0.0))
        step = max(abs(x - y) for x, y in zip(va, vb))
        if step > worst:
            worst, at = step, (samples[index_b]["frame"], name)
    return worst, at


def _crossings(series):
    """去均值后的**符号反转**次数 + 估算周期（帧）。"""
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
    period = 2.0 * span / float(len(cross) - 1)
    return len(cross), period


# =============================================================== 专属门禁
def stun_assertions(arm, action, samples, meshes):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    frames = [s["frame"] for s in samples]

    res["foot_lock_tol_mm"] = FOOT_LOCK_MM
    # ★ 基准必须取**每个量自己的首帧值**（第一版把 toe 也拿去和踝锚点比，
    #   于是"toe 漂移 128.86 mm"—— 那 128 mm 其实是**脚掌本身的长度**。
    #   这个错法会同时污染 `chain_present_ok`（它的脚段读的正是这个量）。
    ref = {"foot": {}, "toe": {}}
    for side in SIDES:
        for tag, key in (("foot", "foot." + side), ("toe", "toe." + side)):
            if key in samples[0]:
                ref[tag][side] = Vector(samples[0][key])
    drift = {s: 0.0 for s in SIDES}
    toe_drift = {s: 0.0 for s in SIDES}
    drift_at = {s: None for s in SIDES}
    for sample in samples:
        for side in SIDES:
            for tag, key, store in (("foot", "foot." + side, drift),
                                    ("toe", "toe." + side, toe_drift)):
                if key not in sample or side not in ref[tag]:
                    continue
                dist = (Vector(sample[key]) - ref[tag][side]).length * 1000.0
                if store[side] < dist:
                    store[side] = dist
                    if tag == "foot":
                        drift_at[side] = sample["frame"]
    res["stun_ankle_drift_mm"] = {k: round(v, 4) for k, v in drift.items()}
    res["stun_toe_drift_mm"] = {k: round(v, 4) for k, v in toe_drift.items()}
    res["stun_ankle_drift_frame"] = drift_at
    res["stun_foot_lock_ok"] = bool(max(max(drift.values()),
                                        max(toe_drift.values())) <= FOOT_LOCK_MM)

    pelvis = [Vector(s["pelvis"]) for s in samples]
    zs = [p.z for p in pelvis]
    res["stun_pelvis_z_range_mm"] = round((max(zs) - min(zs)) * 1000.0, 4)
    res["stun_height_hold_ok"] = bool(res["stun_pelvis_z_range_mm"] <= HEIGHT_HOLD_MM)

    head = [Vector(s["head.tail"]) for s in samples]
    lat = [p.x for p in head]
    side = [p.y for p in head]
    res["stun_head_lat_travel_mm"] = round((max(lat) - min(lat)) * 1000.0, 3)
    res["stun_head_side_travel_mm"] = round((max(side) - min(side)) * 1000.0, 3)
    res["stun_sway_amp_ok"] = bool(
        SWAY_AMP_MIN_MM <= res["stun_head_lat_travel_mm"] <= SWAY_AMP_MAX_MM)
    res["stun_sway_side_amp_ok"] = bool(
        res["stun_head_side_travel_mm"] >= SWAY_SIDE_MIN_MM)
    cross, period = _crossings(lat)
    res["stun_sway_crossings"] = cross
    res["stun_sway_period_frames"] = None if period is None else round(period, 3)
    res["stun_sway_period_ok"] = bool(
        cross >= SWAY_MIN_CROSS and period is not None
        and SWAY_PERIOD_RANGE[0] <= period <= SWAY_PERIOD_RANGE[1])

    # 贴地：分左右按**顶点的世界 x 符号**分不了左右（两鞋在 x≈0 附近重叠），
    # 所以用 `foot_lowest_by_side`（按**鞋对象**分左右）。逐帧实测。
    sole = {s: [] for s in SIDES}
    probe_frames = frames[::2] + [TOTAL]
    for frame in sorted(set(probe_frames)):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        for side in SIDES:
            if low[side] is not None:
                sole[side].append(low[side][2] * 1000.0)
    all_low = sole["L"] + sole["R"]
    res["stun_sole_min_mm"] = round(min(all_low), 3)
    res["stun_sole_max_mm"] = round(max(all_low), 3)
    res["stun_sole_range_mm"] = {s: round(max(sole[s]) - min(sole[s]), 3)
                                 for s in SIDES}
    res["sole_ground_ok"] = bool(SOLE_BAND[0] <= min(all_low)
                                 and max(all_low) <= SOLE_BAND[1])
    res["ground_hold_ok"] = bool(max(res["stun_sole_range_mm"].values())
                                 <= SOLE_RANGE_MM)

    # 收招 / 过缝：末 8 帧没有一帧大跳 + 过缝速度连续
    snap, snap_at = 0.0, None
    lo = max(1, TOTAL - SNAP_WINDOW)
    for index in range(lo, len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > snap:
            snap, snap_at = step, at
    res["no_snap_stop_step_deg"] = round(snap, 4)
    res["no_snap_stop_at"] = snap_at
    res["no_snap_stop_ok"] = bool(snap <= NO_SNAP_END_DEG)
    res["no_snap_window"] = [lo, TOTAL]

    first_step, _ = _worst_step(samples, 0, 1)
    last_step, _ = _worst_step(samples, len(samples) - 2, len(samples) - 1)
    res["loop_seam_step_first_deg"] = round(first_step, 4)
    res["loop_seam_step_last_deg"] = round(last_step, 4)
    res["loop_velocity_ok"] = bool(
        abs(first_step - last_step) <= LOOP_VEL_TOL * max(first_step, last_step, 0.05))
    res["loop_velocity_note"] = (
        "★ 循环动画的「过缝速度连续」：`no_snap_stop`（§0.6 的「收招不许瞬停」）"
        "是给**单次攻击**定的，对循环不适用 ⟹ 本支改判据为"
        "**首帧步长 ≈ 末帧步长**（正弦过缝天然连续）。")

    # 力量传导链（六段；★ 脚段与 D19 **反号**：本支要求 ≤ 3 mm，因为清单原文要求脚不动）
    foot_travel = max(max(drift.values()), max(toe_drift.values()))
    hip_travel = max((p - pelvis[0]).length for p in pelvis) * 1000.0
    knee = []
    for frame in frames[::2]:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            knee.append(arm.pose.bones["shin." + side].rotation_euler.x)
    knee_deg = (max(knee) - min(knee)) * 180.0 / math.pi
    waist = [abs(s["euler"].get("chest", (0.0, 0.0, 0.0))[2]) for s in samples]
    waist_deg = max(waist) - min(waist)
    shoulder = [Vector(s["upperarm.L"]) for s in samples]
    shoulder_mm = max((p - shoulder[0]).length for p in shoulder) * 1000.0
    hand = [Vector(s["hand.L.tail"]) for s in samples]
    hand_mm = max((p - hand[0]).length for p in hand) * 1000.0
    res["chain_travel"] = {"foot_mm": round(foot_travel, 4),
                           "knee_deg": round(knee_deg, 4),
                           "hip_mm": round(hip_travel, 4),
                           "waist_deg": round(waist_deg, 4),
                           "shoulder_mm": round(shoulder_mm, 4),
                           "hand_mm": round(hand_mm, 4)}
    res["chain_present_ok"] = bool(
        foot_travel <= FOOT_LOCK_MM and knee_deg > 0.2 and hip_travel > 2.0
        and waist_deg > 2.0 and shoulder_mm > 1.0 and hand_mm > 20.0)
    res["chain_note"] = (
        "★ 六段 = 脚→腿→髋→腰→肩→手。**脚段与 D19 反号**：D19 要 `foot_mm > 50`"
        "（撞墙时机体整体位移），本支要 `foot_mm ≤ 3` —— 清单原文「脚尽量保持原位」。"
        "其余五段全部要求**有非零关键帧 + 可测位移**。")

    # 穿模（照抄 D19）
    worst_clip, clip_at = 0.0, None
    for frame in sorted(set(list(range(0, TOTAL + 1, 6)) + [TOTAL])):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        clip = PD.clip_metrics(arm)
        if clip["clip_max_mm"] > worst_clip:
            worst_clip, clip_at = clip["clip_max_mm"], (frame, clip["clip_at"])
    res["clip_max_mm"] = round(worst_clip, 2)
    res["clip_at"] = clip_at
    res["no_face_clip_ok"] = bool(worst_clip <= CLIP_MAX_MM)

    # 可达性（照抄 D19）
    worst_leg, worst_leg_at = 0.0, None
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            limit = (A.L_THIGH + A.L_SHIN) * REACH_MAX_RATIO
            ratio = (Vector(ANCHOR[side]) - hip).length / limit
            if ratio > worst_leg:
                worst_leg, worst_leg_at = ratio, (frame, side)
    res["leg_reach_ratio_max"] = round(worst_leg, 5)
    res["leg_reach_ratio_at"] = worst_leg_at
    res["leg_reach_ok"] = bool(worst_leg <= 1.0)

    # 秒表（供像素探针）
    res["sway_markers"] = {
        "LAT_MAX_R": int(round(TOTAL / (4.0 * CYCLES))),
        "LAT_ZERO_1": int(round(TOTAL / (2.0 * CYCLES))),
        "LAT_MAX_L": int(round(3.0 * TOTAL / (4.0 * CYCLES)))}
    return res


# =============================================================== 主流程
def boot():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    global BASE, ANCHOR, BONE_LIST
    if SEAM_ZERO:
        BASE = {}
        A.apply_pose(arm, BASE)
        BONE_LIST = sorted(arm.pose.bones.keys())
    else:
        BASE = IDLE.idle_pose(arm, 0.0)
        BONE_LIST = sorted(arm.pose.bones.keys())
    ANCHOR = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    return arm, meshes


def main():
    arm, meshes = boot()
    scene = bpy.context.scene

    keyframes = [(frame, stun_pose(arm, frame)) for frame in range(START, END + 1)]
    meta = {
        "anim_id": NAME,
        "loop": True,
        "category": "状态与流程",
        "note": ("眩晕：站姿下身体持续摇晃（左右为主 + 前后为辅），"
                 "双脚**钉在首帧原位**（≤%.1f mm），拳架随晃松散" % FOOT_LOCK_MM),
        "loop_frames": [START, END],
        "root_motion_m": [0.0, 0.0],
        "hitstop_frames": 0,
        "sway_cycles": CYCLES,
        "sway_lat_deg": A_LAT,
        "sway_fwd_deg": A_FWD,
        "foot_lock_mm": FOOT_LOCK_MM,
        "seam": "%s@%d" % (SEAM_ACTION, SEAM_FRAME),
        "frame_bound_note": "★ 本支登记**新上界 120 帧 / 2.0 s**（循环状态，见文件头）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "LOOP_START": 0,
        "SWAY_R_MAX": int(round(TOTAL / (4.0 * CYCLES))),
        "SWAY_CENTER_1": int(round(TOTAL / (2.0 * CYCLES))),
        "SWAY_L_MAX": int(round(3.0 * TOTAL / (4.0 * CYCLES))),
        "LOOP_END": TOTAL,
    })

    samples = A.sample_animation(arm, action, START, END, meshes)
    report = A.run_common_assertions(samples, meta,
                                     foot_probe=("toe.L", "toe.R"),
                                     slide_tolerance_mm=FOOT_LOCK_MM)
    report.update(stun_assertions(arm, action, samples, meshes))

    # 接缝入：首帧 vs 上游（逐骨 4x4）
    upstream = bpy.data.actions[SEAM_ACTION]
    seam_mats = world_mats(arm, upstream, SEAM_FRAME)
    mine = world_mats(arm, action, 0)
    worst_pos, worst_dir, worst_at = 0.0, 0.0, None
    for name in BONE_LIST:
        if name not in seam_mats or name not in mine:
            continue
        pos, deg = _mat_delta(mine[name], seam_mats[name])
        if pos > worst_pos or deg > worst_dir:
            worst_at = name if (pos > worst_pos or deg > worst_dir) else worst_at
        worst_pos = max(worst_pos, pos)
        worst_dir = max(worst_dir, deg)
    report["seam_in_pos_max_mm"] = round(worst_pos, 6)
    report["seam_in_dir_max_deg"] = round(worst_dir, 6)
    report["seam_in_at"] = worst_at
    report["seam_in_ok"] = bool(worst_pos <= SEAM_POS_MAX_MM
                                and worst_dir <= SEAM_DIR_MAX_DEG)
    report["seam_in_src"] = "%s@%d" % (SEAM_ACTION, SEAM_FRAME)

    # 首末闭合：逐骨 4x4 世界矩阵**逐元素**比对（A01/A09 的口径）。
    # ★ 第一版用「矩阵列夹角」当方向差，实测噪声底 = **0.0312°**
    #   （= acos(1 − 1.5e-7)，float32 的机器精度被 acos 放大成 sqrt(2ε)）
    #   ⟹ 用 1e-3° 当阈值必然假红。改用逐元素 1e-6（位移列单位是米，1e-6 m = 0.001 mm）。
    first = world_mats(arm, action, START)
    last = world_mats(arm, action, END)
    end_pos, end_dir = 0.0, 0.0
    end_elem, end_elem_at = 0.0, None
    for name in BONE_LIST:
        if name in first and name in last:
            pos, deg = _mat_delta(first[name], last[name])
            end_pos = max(end_pos, pos)
            end_dir = max(end_dir, deg)
            for row in range(4):
                for col in range(4):
                    delta = abs(first[name][row][col] - last[name][row][col])
                    if delta > end_elem:
                        end_elem, end_elem_at = delta, (name, row, col)
    report["end_matches_start_pos_mm"] = round(end_pos, 9)
    report["end_matches_start_dir_deg"] = round(end_dir, 9)
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
    A.report("E01_REPORT", report)

    # ★★ 基线图 + 存盘 / 导出**必须被 `SKIP_RENDER` 拦住**（D19 的教训）：
    #   反向验证全部用 `SKIP_RENDER=1` 跑 ⟹ 坏姿态**绝不落盘**，正式资产不被污染。
    #   （第一版把 `save_project` / `export_glb` 写在守卫外面，跑一组 TP 就会把
    #    畸形动画写进 `bigman_anim_v001.blend` 与 `bigman_anim_v001.glb`。）
    #   ★ `E01_STEM_ONLY=1` 也一并拦住基线图 —— 它是**改过旋钮**的重渲，
    #     绝不能拿它去覆盖基线那 121 张（否则像素探针的「基线」就变成畸形数据了）。
    stem_only = os.environ.get("E01_STEM_ONLY") == "1"
    if not SKIP_RENDER and not stem_only:
        # ★★ **探针用图与目检用图必须分开**（D19 踩过的坑）：
        #   `stunwide_front_*` = **像素探针唯一读的机位**，0..120 **逐帧**（121 张）；
        #   `stunkey_*` / `stun_*` 只服务「三重目检」，不参与任何断言。
        A.render_pose_sheet(arm, action, list(range(START, END + 1)),
                            "stunwide", views=(VIEW_E01_FRONT_WIDE,))
        side_frames = list(range(START, END + 1, 2)) + [END]
        A.render_pose_sheet(arm, action, sorted(set(side_frames)), "stun",
                            views=(A.VIEW_SIDE,))
        key_frames = [0, 15, 30, 45, 60, 90, 120]
        A.render_pose_sheet(arm, action, key_frames, "stunkey",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))

    # ★ `E01_STEM_ONLY=1`：**只为像素探针的反面对照服务** —— 在 `E01_TP_FOOTSWAY=1`
    #   （或 `E01_TP_NOSWAY=1`）下重渲**与基线判据同一台相机、同一批帧**的正面宽视图
    #   （★ 帧集合必须逐帧相同，否则就是 D19 记下的「反面对照换了尺子」）。
    #   **不存盘、不导出、不覆盖基线图。**
    if stem_only:
        A.render_pose_sheet(arm, action, list(range(START, END + 1)),
                            os.environ.get("E01_STEM", "stunfootsway"),
                            views=(VIEW_E01_FRONT_WIDE,))
        print("E01_DONE failed=%s non_ok=%s" % (failed, non_ok))
        return

    if not SKIP_RENDER:
        A.save_project()
        A.export_glb(arm)
    print("E01_DONE failed=%s non_ok=%s" % (failed, non_ok))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E01_FAILURE " + traceback.format_exc())
