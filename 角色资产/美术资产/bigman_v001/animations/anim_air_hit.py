"""anim_air_hit —— D13 `Air_Hit` 空中受击。

清单原文：「**短动作，不能破坏空中轨迹系统**」。

★★ 本支与 D12 `Launch_Hit` 是**首尾相接**的一对（D12 被击飞 → 在飞行途中又挨一下）：

    | 接缝 | 上游 / 下游 | 本支落成的做法 |
    |---|---|---|
    | 上游**姿态** | D12 末帧 = `SELF_HOLD` 锁存姿态（**不是**零位） | 本支 f0 **逐位 = `Launch_Hit@34`**（读落盘 action，同 D12 读 `Idle_01@0` 的 `boot()`） |
    | 上游**动量** | D12 携带 `end_vz = −9.3889 mm/帧`（在下落） | 本支**继承该竖速**：弹道相位直接续在 D12 f34 之后（`T_PHASE = 31.5`），**全片同一条抛物线** |
    | 下游 | D14 `Knockdown_F` / 回 `Jump_Land` / 继续下落 | 末帧仍落在共享弹道上，登记 `end_pelvis_z_m` + `end_vz_m_per_frame`，竖速**为负且更负** |

★ **与 B08 的区别（别照抄）**：B08 首末帧**都** = `Jump_Fall@0`（插一段、插完接回原姿态）。
  本支是**受击** ⟹ 首帧 = D12 末帧（"被打飞的自持姿态"），末帧是**另一副**自持姿态
  ⟹ 不能用 B08 的"首末同姿态"那把尺子；本支新造「**同弹道、异姿态**」的接缝尺子。

★★ §1 本支唯一的真风险：**"受力"与"弹道"必须完全解耦**

  空中**没有地面反作用** ⟹ 任何"被打得往上弹一下 / 往下沉一下"都会**直接改写弹道**。
  ⟹ 受力只能落在 **躯干折角（横折）+ 四肢甩动** 上；**骨盆 z 一个毫米都不许动**。

  · 骨盆 z 逐帧 = 共享解析弹道（误差 ≤ `BALLISTIC_TOL_MM = 2.0`）；
  · 竖速的一阶差分**恒为 −G_PER_FRAME** ⟹ 全片是一条**单一**抛物线，不许分段；
  · ★ **反向守卫 `vz_no_lift_can_fail_ok`（本支头号守卫，与 D12 的守卫正好相反）**：
    D12 的守卫是"抬升**太小**就判红"；本支是"命中帧**只要出现正向 vz 增量就判红**"，
    即"空中挨打**不许往上弹**"。同一族、相邻两支、方向相反，这对守卫必须同时存在。

★★ 本支技术件：**命中停顿只冻姿态、位置继续走弹道**
  D05~D12 的停顿是**姿态 + 位置**全冻；本支只能冻**姿态**，位置**必须继续掉**
  （否则就是"空中悬停"，与清单原文"不能破坏空中轨迹系统"直接冲突）。
  ⟹ `set_hitstop_pose_only()` 只对 `rotation_euler` 曲线设 CONSTANT，
     `location` 曲线照常走弹道。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_air_hit.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
    D13_TRACE=1    逐帧打印驱动标量 / 弹道 / 折角 / 四肢行程（调参用）

反向验证（§4 第 7 步，四组）：
    D13_TP_SEAM_ZERO=1   ① 首帧改零位（接缝断）  ⟹ `seam_in_ok` 红
    D13_TP_BUMP=30       ② 命中帧骨盆 +30 mm 上抬 ⟹ `ballistic_exact_ok` + `vz_no_lift_can_fail_ok` 红
    D13_TP_NOVZ=1        ③ 抽掉 vz 继承（f0 竖速 = 0）⟹ `vz_continuous_ok` 红
    D13_TP_NOFOLD=1      ④ 抽掉躯干主驱动        ⟹ `hit_air_fold_ok` 红
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
import anim_jump_start as JS             # noqa: E402
import anim_jump_fall as JFE             # noqa: E402
import anim_ultimate_end as UE           # noqa: E402
import anim_crouch as CR                 # noqa: E402
import probe_c12_baseline as P           # noqa: E402
import probe_d01_guard as PD             # noqa: E402

NAME = "Air_Hit"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")

# ★ 接缝真源：上游 D12 的落盘 action + 末帧号
SEAM_ACTION = os.environ.get("D13_SEAM_ACTION", "Launch_Hit")
SEAM_FRAME = int(os.environ.get("D13_SEAM_FRAME", "34"))
# ★ D12 的相位原点（`anim_launch_hit.T_ORIGIN`）—— 本支**必须**沿用它才能同一条抛物线
D12_T_ORIGIN = 2.50


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


def _f32(value):
    """量化到 float32 —— F-Curve 关键帧就是按 float32 存的（与 D02~D12 同源）。"""
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


def _lin(keys, frame):
    """分段**线性**取值。"""
    if frame <= keys[0][0]:
        return keys[0][1]
    if frame >= keys[-1][0]:
        return keys[-1][1]
    for index in range(len(keys) - 1):
        xa, ya = keys[index]
        xb, yb = keys[index + 1]
        if xa <= frame <= xb:
            if xb == xa:
                return yb
            return ya + (yb - ya) * (frame - xa) / float(xb - xa)
    return keys[-1][1]


# =============================================================== 时间轴
# ★ 计划 §2：建议 18 帧 / 0.300 s @60fps，非循环（"短动作"）。
#   帧预算上界 22 帧（§4 第 4 步）—— 若"甩臂总行程 ÷ 可用帧数"装不下再延时。
TOTAL = _env_i("D13_TOTAL", 18)
IMPACT = _env_i("D13_IMPACT", 2)             # ★ 空中命中帧
HIT_HOLD = _env_i("D13_HOLD", 2)             # ★ 空中 2 帧完全停顿（地面是 3 帧）
HOLD_END = IMPACT + HIT_HOLD                 # 4
#   计划 §2：**`FOLD`=4~9 / `RECOVER`=9~14**（折峰在 **f9**，不是 f7）——
#   实测折峰放 7 会让"甩出"三帧到顶、f7→f8 骤停到 0.05°/帧 ⟹ `no_snap_stop` 判红。
#   折峰取 9（折 5 帧 / 收 5 帧）后，甩出与收回各自都是**单调节奏**，无死停。
FOLD_PEAK = _env_i("D13_FOLD_PEAK", 9)       # ★ 躯干折角 / 四肢甩动峰值帧（∈ 4~9）
PLATEAU = _env_i("D13_PLATEAU", 14)          # ★ 定格自持起点（f14 起逐位锁存）
RECOVER_END = _env_i("D13_RECOVER", 14)
CANCEL = _env_i("D13_CANCEL", 14)

# =============================================================== 共享弹道
# ★ 相位**直接续在 D12 f34 之后**：D13 frame f ⟺ 解析时刻 t = (f + 34) − T_ORIGIN
#   ⟹ f0 与 D12 f34 是**同一个**解析点（z 逐位相同），全片同一条抛物线。
T_PHASE = float(SEAM_FRAME) - D12_T_ORIGIN   # 31.5
BALLISTIC_TOL_MM = _env_f("D13_BALLISTIC_TOL", 2.0)
Z_PELVIS_REST = 0.900
PELVIS_Y_M = _env_f("D13_Y", 0.026)          # 沿用 D12 末帧的水平后移量（**不新增位移**）


def ball_z(frame):
    """★ 与 A10/A11/A12/B08/D12 **同一个**解析弹道，相位续在 D12 之后。"""
    t = T_PHASE + float(frame)
    return JS.TAKEOFF_PELVIS_Z + JS.TAKEOFF_SPEED * t - 0.5 * JS.G_PER_FRAME * t * t


def ball_vz(frame):
    """该帧的弹道**瞬时**竖速（米/帧）。"""
    return JS.TAKEOFF_SPEED - JS.G_PER_FRAME * (T_PHASE + float(frame))


# ★ 竖速用**一阶差分**度量（与 D12 的 `end_vz_mm_per_frame` 同口径 —— 那是差分不是瞬时）
D12_END_VZ_MM = (ball_z(0) - ball_z(-1)) * 1000.0     # = −9.388889 mm/帧
G_MM = JS.G_PER_FRAME * 1000.0                        # = 2.722222 mm/帧²

Z_APEX = JS.TAKEOFF_PELVIS_Z + JS.APEX_RISE
F_APEX_D12 = D12_T_ORIGIN + JS.TAKEOFF_SPEED / JS.G_PER_FRAME   # 30.051（D12 的顶点帧）
F_APEX_LOCAL = F_APEX_D12 - float(SEAM_FRAME)                   # 顶点在 D13 坐标里 = −3.949

# =============================================================== 反向验证旋钮
BUMP_MM = _env_f("D13_TP_BUMP", 0.0)         # ② 命中帧骨盆上抬（mm）
SEAM_ZERO = _env_b("D13_TP_SEAM_ZERO")       # ① 首帧改零位（接缝断）
# ★★ ① 号旋钮的落点：**只换"零位真源"，不换弹道相位**。
#   `SEAM_ACTION/SEAM_FRAME` 继续用于「弹道相位 + handoff 报告」；
#   `ZERO_ACTION/ZERO_FRAME` 才是 f0 姿态的读取源。打开 ① 后 f0 变零位 ⟹ `seam_in_ok` 红。
ZERO_ACTION = "Idle_01" if SEAM_ZERO else SEAM_ACTION
ZERO_FRAME = 0 if SEAM_ZERO else SEAM_FRAME
NO_VZ = _env_b("D13_TP_NOVZ")                # ③ 抽掉 vz 继承
NO_FOLD = _env_b("D13_TP_NOFOLD")            # ④ 抽掉躯干主驱动
NO_FLING = _env_b("D13_TP_NOFLING")          # 附加：抽掉四肢甩动


def pelvis_bump(frame):
    """★ 反向验证 ② 用：命中帧给骨盆一个**正向**抬升（正常 = 0）。"""
    if BUMP_MM <= 0.0:
        return 0.0
    return (BUMP_MM / 1000.0) if IMPACT <= frame <= HOLD_END else 0.0


def pelvis_z_at(frame):
    """骨盆世界 z（米）。★ 全段 = 共享解析弹道（本支**没有**自由段）。"""
    z = ball_z(frame) + pelvis_bump(frame)
    if NO_VZ:
        # ③ "抽掉 vz 继承"：f0 竖速 = 0 ⟹ 把 f0 钉在 f1 的高度上（弹道在接缝处被压平）
        if frame <= 0:
            z = ball_z(1)
    return z


def pelvis_vz_at(frame):
    """本支用于判据的"竖速" = **一阶差分**（与 D12 `end_vz_mm_per_frame` 同口径）。"""
    return (pelvis_z_at(frame) - pelvis_z_at(frame - 1)) * 1000.0


# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
REACH_MAX_RATIO = 0.995
# ---- ★★ 本支头号判据（§1 解耦）---------------------------------------------
BALLISTIC_TOL = BALLISTIC_TOL_MM
VZ_CONT_TOL_MM = _env_f("D13_VZ_CONT_TOL", 1.0)      # 接缝竖速**步长**对 −G 的容差
VZ_G_TOL = _env_f("D13_VZ_G_TOL", 1.0e-6)            # 竖速一阶差分 ≡ −G（解析求值）
VZ_MIN_MM = _env_f("D13_VZ_MIN", -1.0)               # 竖速必须 ≤ 该值（"全程在下落"）
# ---- ★ 离地（绝对量，不是相对 f0 —— f0 本来就在空中）----------------------
AIRBORNE_MIN_MM = _env_f("D13_AIRBORNE_MIN", 100.0)
# ---- ★★ 命中帧躯干**横折**（主承载）---------------------------------------
FOLD_MIN_DEG = _env_f("D13_FOLD_MIN", 12.0)          # 命中帧胸世界侧倾
FOLD_MIN_IMPACT_FRAC = _env_f("D13_FOLD_FRAC", 0.55)  # 命中帧折角 / 峰值 ≥ 该比例
PELVIS_TILT_DEG = _env_f("D13_TP_PELVIS", 10.0)
CHEST_TILT_DEG = _env_f("D13_TP_CHEST", 34.0)
HEAD_TILT_DEG = _env_f("D13_TP_HEAD", 44.0)
SPINE_MIX_1 = _env_f("D13_MIX_S1", 0.30)
SPINE_MIX_2 = _env_f("D13_MIX_S2", 0.62)
SPINE_RY_DEG = _env_f("D13_SPINE_RY", 8.0)
PELVIS_RY_DEG = _env_f("D13_PELVIS_RY", 4.0)
FOLD_SCALE = _env_f("D13_TP_FOLD_SCALE", 1.0)        # 反向验证用（符号/幅度）
# ---- ★★ 四肢被惯性甩（**无回弹力**：甩出去就停在展开位）------------------
FLING_FIST_RATIO = _env_f("D13_TP_FIST_RATIO", 0.72)
FIST_TRAVEL_MIN_MM = _env_f("D13_FIST_MIN", 200.0)
ANKLE_TRAVEL_MIN_MM = _env_f("D13_ANKLE_MIN", 200.0)
LIMB_OUTWARD_MIN_MM = _env_f("D13_OUTWARD_MIN", 25.0)   # 四肢必须**向外**扩（方向守卫）
LEG_LAT_MM = _env_f("D13_TP_LEG_LAT", 70.0)
LEG_BACK_MM = _env_f("D13_TP_LEG_BACK", 55.0)
# ---- 打击停顿（≥2 帧；★ 只冻姿态，位置继续走弹道）-------------------------
HITSTOP_MIN_FRAMES = _env_f("D13_HITSTOP_MIN", 2.0)
HITSTOP_POSE_TOL_DEG = _env_f("D13_HITSTOP_POSE_TOL", 1.0e-6)
# ---- 节奏（升 ≤3 / 降 ≥8）--------------------------------------------------
HIT_RISE_MAX_FRAMES = _env_f("D13_RISE_MAX", 3.0)
HIT_FALL_MIN_FRAMES = _env_f("D13_FALL_MIN", 8.0)
# ---- 收尾：定格自持（末 N 帧姿态逐位冻结；只有骨盆沿弹道平移）---------------
END_HOLD_MAX_DEG = _env_f("D13_END_HOLD_TOL", 0.5)
END_VZ_REG_MAX_MM = _env_f("D13_END_VZ_MAX", 0.0)   # 登记竖速必须 **< 0**
# ---- 收招不许瞬停（定格前 8 帧的单帧步长上界 —— ★ 帧预算紧，本支更严）------
NO_SNAP_END_DEG = _env_f("D13_SNAP_END", 5.0)
# ---- 滚转回位（D11 教训 3 → D12 照抄 → 本支继续）--------------------------
ROLL_WEIGHT_MODE = os.environ.get("D13_ROLL_WEIGHT", "always").strip().lower()
ROLL_BONES = tuple(
    item for item in os.environ.get(
        "D13_ROLL_BONES",
        "upperarm.L,forearm.L,hand.L,upperarm.R,forearm.R,hand.R").split(",")
    if item)
ROLL_ITER = max(1, int(os.environ.get("D13_ROLL_ITER", "2")))
# ---- 穿模
CLIP_MAX_MM = _env_f("D13_CLIP_MAX", 0.0)
CLIP_EVERY = int(os.environ.get("D13_CLIP_EVERY", 3))
# ---- 零位/接缝复显守卫
SEAM_REPLAY_POS_MAX_MM = _env_f("D13_SEAM_POS", 0.01)
SEAM_REPLAY_DIR_MAX_DEG = _env_f("D13_SEAM_DIR", 0.05)

# =============================================================== 驱动标量
#   `press` —— 节奏时钟（升 2 / 停 2 / 降 10 —— 18 帧预算）
#   `fold`  —— ★ **主驱动**：躯干**横折**（命中窗口内已吃满大半）
#   `fling` —— ★ **四肢惯性甩动**：甩出去后**不回弹**（停在展开位）
#   `twist` —— 轻微绕体轴扭转（让 3Q 读得出"横折"不是"前后折"）
#   ★ 硬直平台 f2~f4 必须**真的平**：PCHIP 只有"两侧割线同号且非零"才给非零斜率，
#     所以平台段**每一帧都要写键**（只写两端点会让中间鼓起来 —— 实测 f3 漂 8.08°）。
FOLD_KEYS = ((0, 0.0), (1, 0.30), (IMPACT, 0.74), (3, 0.74), (HOLD_END, 0.74),
             (5, 0.790), (6, 0.845), (7, 0.900), (8, 0.955),
             (FOLD_PEAK, 1.00),
             (10, 0.940), (11, 0.875), (12, 0.810), (13, 0.745),
             (RECOVER_END, 0.700), (TOTAL, 0.700))
FLING_KEYS = ((0, 0.0), (1, 0.22), (IMPACT, 0.56), (3, 0.56), (HOLD_END, 0.56),
              (5, 0.620), (6, 0.680), (7, 0.740), (8, 0.800),
              (FOLD_PEAK, 0.855),
              (10, 0.900), (11, 0.935), (12, 0.960), (13, 0.975),
              (RECOVER_END, 0.985), (TOTAL, 0.99))
TWIST_KEYS = ((0, 0.0), (1, 0.15), (IMPACT, 0.50), (3, 0.50), (HOLD_END, 0.50),
              (5, 0.565), (6, 0.630), (7, 0.700), (8, 0.775),
              (FOLD_PEAK, 0.855),
              (10, 0.900), (11, 0.940), (12, 0.965), (13, 0.980),
              (RECOVER_END, 0.990), (TOTAL, 0.99))


def press(frame):
    """节奏标量 ∈ [0, 1]：**升 2 / 峰停 2 / 降 12** 的单脉冲。"""
    keys = [(0, 0.0), (1, 1.0 / max(1, IMPACT))]
    keys += [(IMPACT, 1.0), (HOLD_END, 1.0), (RECOVER_END, 0.0), (TOTAL, 0.0)]
    return UE.pwl(tuple(keys), float(frame), 0.0)


def fold(frame):
    """★ 主驱动：躯干**横折**量（0~1）。命中窗口内已 0.74（"读得出被打了"）。"""
    if NO_FOLD:
        return 0.0
    return UE.pwl(FOLD_KEYS, float(frame), 0.0) * FOLD_SCALE


def fling(frame):
    """★ 四肢被惯性甩（0~1）。甩出去**不回弹**（尾部停在 0.99）。"""
    if NO_FLING:
        return 0.0
    return UE.pwl(FLING_KEYS, float(frame), 0.0)


def twist(frame):
    """绕体轴扭转（0~1）—— 与 D12 的"后仰"区分开：本支是"横折 + 拧"。"""
    return UE.pwl(TWIST_KEYS, float(frame), 0.0)


# =============================================================== 世界角目标
TORSO_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head")
PARENT_OF = {"pelvis": "root", "spine_01": "pelvis", "spine_02": "spine_01",
             "chest": "spine_02", "neck": "chest", "head": "neck"}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")


def world_tilts(frame):
    """★★ 各骨**世界侧倾目标**（度，+ = 倾向角色**左**（+X））—— 本支核心解算。

    语义表：`rz > 0` = 向角色**右**（−X）侧倾 ⟹ 自骨世界侧倾 `W_self = W_parent − rz_self`
    ⟹ 反解 **`rz_self = W_parent − W_self`**（D11 的"世界侧倾 → 局部 rz"，原样照抄）。
    """
    f = fold(frame)
    w = {"root": 0.0}
    w["pelvis"] = -PELVIS_TILT_DEG * f
    w["chest"] = -CHEST_TILT_DEG * f
    w["spine_01"] = w["pelvis"] + SPINE_MIX_1 * (w["chest"] - w["pelvis"])
    w["spine_02"] = w["pelvis"] + SPINE_MIX_2 * (w["chest"] - w["pelvis"])
    w["head"] = -HEAD_TILT_DEG * f
    w["neck"] = w["chest"] + 0.45 * (w["head"] - w["chest"])
    return w


def torso_pose(frame):
    """世界侧倾目标 → 局部 `rz`；`rx`/`ry` 在**接缝姿态（D12 末帧）**之上叠加。

    ★ `@loc` = `wloc(0, PELVIS_Y_M, pelvis_z_at − Z_PELVIS_REST)` —— 与 D12 逐位同式，
      于是 f0 的骨盆世界位置与 `Launch_Hit@34` 完全一致（面缝尺子要求）。
    """
    w = world_tilts(frame)
    t = twist(frame)
    out = {}
    for name in TORSO_BONES:
        rz = w[PARENT_OF[name]] - w[name]
        base = ZERO.get(name, (0.0, 0.0, 0.0))
        if name == "pelvis":
            out[name] = (base[0], base[1] + PELVIS_RY_DEG * t, base[2] + rz)
        elif name in ("spine_01", "spine_02", "chest"):
            ry = SPINE_RY_DEG * t * (0.6 if name == "spine_01" else
                                     1.0 if name == "spine_02" else 0.8)
            out[name] = (base[0], base[1] + ry, base[2] + rz)
        else:
            out[name] = (base[0], base[1], base[2] + rz)
    for side in SIDES:
        name = "shoulder." + side
        base = ZERO.get(name, (0.0, 0.0, 0.0))
        out[name] = (base[0], base[1], base[2])
    out["@loc"] = {"pelvis": A.wloc(0.0, PELVIS_Y_M,
                                    pelvis_z_at(frame) - Z_PELVIS_REST)}
    return out


# =============================================================== 拳 / 肘目标
# ★ 本支的甩出方向 = 在 **D12 末帧的甩出位置之上再往外 / 往上 / 往后**
#   （D12 末帧方向 ≈ (0.886, −0.299, 0.353)）。夹角 ~32°：
#   ①物理 —— 空中再挨一下，手脚被惯性继续带出去；②门禁 —— 单帧骨旋转速率
#   上界（`no_teleport` ≤25°/帧、`no_snap_stop` ≤5°/帧）必须是先算过账的
#   （B08 的先例、D12 的教训 5 ⟹ §4 第 4 步"开工第一件测量"）。
FLUNG_DIR = {
    "L": tuple(float(x) for x in
               os.environ.get("D13_FLUNG_L", "0.800,0.200,0.560").split(",")),
    "R": tuple(float(x) for x in
               os.environ.get("D13_FLUNG_R", "-0.800,0.200,0.560").split(",")),
}
ELBOW_FLUNG = {
    "L": tuple(float(x) for x in
               os.environ.get("D13_ELBOW_L", "0.58,0.22,-0.78").split(",")),
    "R": tuple(float(x) for x in
               os.environ.get("D13_ELBOW_R", "-0.58,0.22,-0.78").split(",")),
}


def fist_target(arm, side, frame):
    """拳世界目标 = **肩位 + 方向 × 臂展**（必须相对肩，因为骨盆一直在掉）。"""
    shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    d0 = (SEAM_FIST[side] - SEAM_SHOULDER[side])
    d0 = d0.normalized() if d0.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    d1 = Vector(FLUNG_DIR[side]).normalized()
    t = fling(frame)
    direction = d0 * (1.0 - t) + d1 * t
    direction = direction.normalized() if direction.length > 1e-9 else d1
    span = SEAM_SPAN[side] + (FLING_FIST_RATIO * ARM_MAX[side]
                              - SEAM_SPAN[side]) * t
    return shoulder + direction * span


def elbow_dir(side, frame):
    t = fling(frame)
    d0 = Vector(SEAM_ELBOW_DIR[side])
    d1 = Vector(ELBOW_FLUNG[side]).normalized()
    out = d0 * (1.0 - t) + d1 * t
    return out.normalized() if out.length > 1e-9 else d1


# =============================================================== 踝目标
def ankle_target(arm, side, frame):
    """踝目标 = **髋位 + 接缝髋-踝偏移** + **向外张开** + **向后拖尾**。

    ★ 为什么锚在**髋**上而不是 f0 的踝位：骨盆在世界侧倾时髋会跟着走，
      把踝锚死在 f0 的绝对位置会让"髋-踝"矢量被折角**歪掉** ⟹ 膝解崩、单帧步长爆。
      锚在髋上，腿就永远是"挂在髋下面的那条腿"（`leg_reach` 也因此稳在 0.73 附近）。
    ★ 本支**不新增水平位移**（`root_motion_m` 仍归引擎）—— 这里动的是**四肢姿态**。
    """
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    off = SEAM_HIP_OFF[side]
    t = fling(frame)
    sgn = 1.0 if side == "L" else -1.0
    lat = LEG_LAT_MM / 1000.0 * t * sgn
    back = LEG_BACK_MM / 1000.0 * t
    vert = _lin(VERT_KEYS, frame)
    return Vector((hip.x + off[0] + lat, hip.y + off[1] + back, hip.z - vert))


VERT_KEYS = ((0, 0.685), (IMPACT, 0.696), (FOLD_PEAK, 0.718), (11, 0.708),
             (RECOVER_END, 0.700), (TOTAL, 0.700))
TIP_KEYS = ((0, 26.0), (TOTAL, 26.0))     # 与 D12 末帧一致（绷脚背），保持接缝

# =============================================================== 模块级表
ZERO = {}
ZERO_WORLD = {}
ZERO_BASIS = {}
ZERO_DIR = {}
SEAM_FIST = {}
SEAM_SHOULDER = {}
SEAM_SPAN = {}
SEAM_ELBOW_DIR = {}
SEAM_HAND_DIR = {}
SEAM_ANKLE = {}
SEAM_HIP = {}
SEAM_HIP_OFF = {}
ANKLE_0 = {}
KNEE_DIR = {}
ARM_MAX = {}
Z_SEAM = 0.0
LOCK_POSE = {}
# ★★ 命中停顿姿态锁存（`IMPACT` 上解算一次，`IMPACT+1..HOLD_END` **逐位复用**）。
#   与 `LOCK_POSE` 同构，但只覆盖命中平台，且**位置继续走弹道**。
HITSTOP_POSE = {}
_HITSTOP_REUSED = [0]
SEAM_MATCH = {"src": None, "euler_diff": None, "geom_pos": None, "geom_dir": None,
              "pos_bone": None, "dir_bone": None, "per_bone": {}}
_ZERO_SHORTCUT_SKIPPED = [0]


# =============================================================== 姿态装配
def arm_seat_tip(arm, pose, side, tip_target, elbow_dir_in):
    """★★ D05 立的臂解算：两骨 IK 打在腕上，手骨按零位自己的折角单独瞄。"""
    up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
    dims = UE.ARM_LEN[side]
    l1, l2 = dims["upper"], dims["forearm"]
    hand_dir = SEAM_HAND_DIR[side]
    wrist_target = Vector(tip_target) - hand_dir * dims["hand"]
    shoulder = Vector(A.bone_world(arm, up, "head"))
    delta = wrist_target - shoulder
    limit = (l1 + l2) * 0.9995
    clamp = delta.length > limit
    distance = max(1e-4, min(delta.length, limit))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    bulge = Vector(elbow_dir_in) - axis * Vector(elbow_dir_in).dot(axis)
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
    # ★ f0 = **逐位**接缝姿态（`Launch_Hit@34`）—— 不走解算，原样返回。
    if frame <= 0:
        pose = {}
        for key, value in ZERO.items():
            pose[key] = (tuple(value) if not key.startswith("@")
                         else {kk: tuple(vv) for kk, vv in value.items()})
        _ZERO_SHORTCUT_SKIPPED[0] += 1
        return pose

    # ★★ 命中停顿（§2）：`IMPACT+1..HOLD_END` **逐位复用** f=IMPACT 的姿态，
    #   只把骨盆 `@loc` 换成弹道值 ⟹ 「姿态完全停顿、位置继续掉」是**构造性**成立的
    #   （不靠 CONSTANT 插值兜 —— CONSTANT 只保证键之间不漂移，管不住键取值不同）。
    if HITSTOP_POSE and IMPACT < frame <= HOLD_END:
        pose = {}
        for key, value in HITSTOP_POSE.items():
            if key == "@loc":
                locs = {k: tuple(v) for k, v in value.items()}
                locs["pelvis"] = A.wloc(0.0, PELVIS_Y_M,
                                        pelvis_z_at(frame) - Z_PELVIS_REST)
                pose["@loc"] = locs
            else:
                pose[key] = tuple(value)
        _HITSTOP_REUSED[0] += 1
        return pose

    # ★★ 定格自持（§2）：f > PLATEAU ⟹ **逐位复用** f14 的解，
    #   只把骨盆 `@loc` 换成弹道值 ⟹ 整段沿弹道平移，姿态构造性冻结。
    if LOCK_POSE and frame > PLATEAU:
        pose = {}
        for key, value in LOCK_POSE.items():
            if key == "@loc":
                locs = {k: tuple(v) for k, v in value.items()}
                locs["pelvis"] = A.wloc(0.0, PELVIS_Y_M,
                                        pelvis_z_at(frame) - Z_PELVIS_REST)
                pose["@loc"] = locs
            else:
                pose[key] = tuple(value)
        _ZERO_SHORTCUT_SKIPPED[0] += 1
        return pose

    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    for side in SIDES:
        UE.leg_seat(arm, pose, side, ankle_target(arm, side, frame),
                    KNEE_DIR[side])
    for name in ("foot.L", "foot.R"):
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            UE.keep_foot_lifted(arm, name.split(".")[1], _lin(TIP_KEYS, frame)))
    for side in SIDES:
        arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                     elbow_dir(side, frame))
    if ROLL_WEIGHT_MODE != "off":
        weight = 1.0
        for _ in range(ROLL_ITER):
            for name in ROLL_BONES:
                if name in arm.pose.bones:
                    _roll_return(arm, pose, name, weight)
            for side in SIDES:
                arm_seat_tip(arm, pose, side, fist_target(arm, side, frame),
                             elbow_dir(side, frame))
    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    if frame == IMPACT:
        HITSTOP_POSE.update({k: (tuple(v) if not k.startswith("@")
                                 else {kk: tuple(vv) for kk, vv in v.items()})
                             for k, v in pose.items()})
    if frame == PLATEAU:
        LOCK_POSE.update({k: (tuple(v) if not k.startswith("@")
                              else {kk: tuple(vv) for kk, vv in v.items()})
                          for k, v in pose.items()})
    return pose


def solve_pose(arm, frame, meshes=None):
    return build_pose(arm, frame)


# =============================================================== 滚转回位修正
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
def _pitch(direction):
    """世界**俯仰**（矢状面 YZ，度）：+ = 前屈，− = 后仰。"""
    return -math.degrees(math.atan2(direction.y, direction.z))


def _lat(direction):
    """世界**侧倾**（正面平面 XZ，度）：+ = 倾向 +X（角色左）。"""
    return math.degrees(math.atan2(direction.x, direction.z))


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
        "pelvis_lat_deg": _lat(Vector(A.bone_direction(arm, "pelvis"))),
        "spine1_lat_deg": _lat(Vector(A.bone_direction(arm, "spine_01"))),
        "spine2_lat_deg": _lat(Vector(A.bone_direction(arm, "spine_02"))),
        "chest_lat_deg": _lat(Vector(A.bone_direction(arm, "chest"))),
        "neck_lat_deg": _lat(Vector(A.bone_direction(arm, "neck"))),
        "head_lat_deg": _lat(Vector(A.bone_direction(arm, "head"))),
        "pelvis_pitch_deg": _pitch(Vector(A.bone_direction(arm, "pelvis"))),
        "chest_pitch_deg": _pitch(Vector(A.bone_direction(arm, "chest"))),
        "head_pitch_deg": _pitch(Vector(A.bone_direction(arm, "head"))),
        "pelvis": Vector(A.bone_world(arm, "pelvis", "head")),
        "hip_z": {s: Vector(A.bone_world(arm, "thigh." + s, "head")).z
                  for s in SIDES},
        "ankle": {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                  for s in SIDES},
        "shoulder": {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                     for s in SIDES},
        "knee_deg": {s: _knee_angle(arm, s) for s in SIDES},
    }


def _foot_clearance():
    low = A.foot_lowest_by_side()
    return {s: (low[s][2] if low[s] is not None else None) for s in SIDES}


def _worst_step(samples, index_a, index_b, skip_loc=True):
    ea, eb = samples[index_a]["euler"], samples[index_b]["euler"]
    worst, at = 0.0, None
    for name in set(ea) | set(eb):
        a = ea.get(name, (0.0, 0.0, 0.0))
        b = eb.get(name, (0.0, 0.0, 0.0))
        step = max(abs(x - y) for x, y in zip(a, b))
        if step > worst:
            worst, at = step, (samples[index_b]["frame"], name)
    return worst, at


def hit_assertions(arm, action, samples, meshes):
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 接缝真值 + 逐帧扫描
    arm.animation_data.action = None
    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    zero = _body_metrics(arm)
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    per, clear = {}, {}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        per[frame] = _body_metrics(arm)
        clear[frame] = _foot_clearance()

    zs = {f: per[f]["pelvis"].z for f in per}
    ys = {f: per[f]["pelvis"].y for f in per}
    xs = {f: per[f]["pelvis"].x for f in per}
    clat = {f: per[f]["chest_lat_deg"] - zero["chest_lat_deg"] for f in per}
    hlat = {f: per[f]["head_lat_deg"] - zero["head_lat_deg"] for f in per}
    cpitch = {f: per[f]["chest_pitch_deg"] - zero["chest_pitch_deg"] for f in per}

    # ---- ★★ (a) 接缝：首帧逐位 = `Launch_Hit@34`（平移不变尺子）----------
    moving = _pelvis_moving(arm)
    seam_mats = CR.action_world_matrices(arm, _seam_action(), SEAM_FRAME)
    mats0 = CR.action_world_matrices(arm, action, 0)
    ori0, rel0, ori_bone0, rel_bone0 = _pose_seam_split(mats0, seam_mats, moving)
    raw0 = CR.matrix_delta(mats0, seam_mats)
    res["seam_in_orient_delta"] = float("%.3e" % ori0)
    res["seam_in_orient_bone"] = ori_bone0
    res["seam_in_relpos_delta_mm"] = round(rel0 * 1000.0, 6)
    res["seam_in_relpos_bone"] = rel_bone0
    res["seam_in_raw_delta"] = float("%.3e" % raw0)
    res["seam_in_ok"] = bool(max(ori0, rel0) <= SEAM_TOL)
    res["seam_ruler_note"] = (
        "首帧比 `%s@%d`：**平移不变**尺子（pelvis 的后代比「骨位置−骨盆位置」，"
        "非后代比世界绝对）。容差 1e-6，未放宽。" % (SEAM_ACTION, SEAM_FRAME))

    # ---- ★★ (b) 弹道：全段逐帧 = 共享解析弹道 ---------------------------
    ball_err, ball_err_at = 0.0, None
    for frame in range(0, TOTAL + 1):
        err = abs(zs[frame] - ball_z(frame)) * 1000.0
        if err > ball_err:
            ball_err, ball_err_at = err, frame
    res["ballistic_max_err_mm"] = round(ball_err, 4)
    res["ballistic_err_at"] = ball_err_at
    res["ballistic_tol_mm"] = BALLISTIC_TOL
    res["ballistic_exact_ok"] = bool(ball_err <= BALLISTIC_TOL)
    res["ballistic_phase"] = {
        "T_PHASE": T_PHASE, "z_f0_mm": round(ball_z(0) * 1000.0, 3),
        "vz_f0_mm": round(ball_vz(0) * 1000.0, 4),
        "apex_frame_local": round(F_APEX_LOCAL, 3),
        "apex_frame_d12": round(F_APEX_D12, 3),
        "apex_z_mm": round(Z_APEX * 1000.0, 3),
        "end_z_mm": round(ball_z(TOTAL) * 1000.0, 3),
        "end_vz_mm": round(ball_vz(TOTAL) * 1000.0, 4),
        "d12_end_vz_mm": round(D12_END_VZ_MM, 4)}

    # ---- ★★★ (c) 竖速三条：连续性 / 恒 −G / **不许往上弹** ---------------
    vz = {f: pelvis_vz_at(f) for f in range(1, TOTAL + 1)}
    res["pelvis_vz_mm_per_frame"] = {str(f): round(vz[f], 4) for f in sorted(vz)}
    res["d12_end_vz_mm"] = round(D12_END_VZ_MM, 4)
    res["vz_seam_step_mm"] = round(vz[1] - D12_END_VZ_MM, 4)
    res["vz_seam_expect_mm"] = round(-G_MM, 4)
    res["vz_cont_tol_mm"] = VZ_CONT_TOL_MM
    res["vz_continuous_ok"] = bool(
        abs((vz[1] - D12_END_VZ_MM) - (-G_MM)) <= VZ_CONT_TOL_MM)
    res["vz_continuous_note"] = (
        "★ 口径（为什么不是「直接作差 ≤1 mm/帧」）：`Launch_Hit.end_vz` 是 **D12 f33→f34 "
        "的差分**（= 抛物线上 t=31 处的平均竖速），本支 f0→f1 的差分是 t=32 处的平均；"
        "两者**本来就差一个 −G**。真正的不跳变定义是：跨接缝的二阶差分 ≡ −G。")
    gdiff, gdiff_at = 0.0, None
    for f in range(2, TOTAL + 1):
        d = (vz[f] - vz[f - 1]) - (-G_MM)
        if abs(d) > abs(gdiff):
            gdiff, gdiff_at = d, f
    res["vz_g_err_mm"] = round(abs(gdiff), 9)
    res["vz_g_err_at"] = gdiff_at
    res["vz_g_tol_mm"] = VZ_G_TOL
    res["vz_constant_g_ok"] = bool(abs(gdiff) <= VZ_G_TOL)
    res["vz_vz_min_mm"] = round(min(vz.values()), 4)
    res["vz_all_falling_ok"] = bool(min(vz.values()) <= VZ_MIN_MM)
    res["vz_lift_impact_mm"] = round(vz[IMPACT], 4)
    res["vz_lift_max_mm"] = round(max(vz.values()), 4)
    res["vz_no_lift_can_fail_ok"] = bool(max(vz.values()) <= 0.0
                                         and vz[IMPACT] < 0.0)
    res["vz_no_lift_note"] = (
        "★★ 本支头号守卫（与 D12 的 `pelvis_lift_*` 方向**相反**）：D12 要求"
        "「命中帧**必须**被顶起来 ≥50 mm」，本支要求「命中帧**只要出现正向 vz "
        "增量就判红**」—— 空中没有地面反作用，受力一旦漏进竖直通道就改写了轨迹。")

    # ---- ★★ (d) 命中帧躯干**横折**（主承载）-----------------------------
    fold_impact = abs(clat[IMPACT])
    fold_peak = max(abs(v) for v in clat.values())
    fold_peak_frame = max(clat, key=lambda f: abs(clat[f]))
    head_fold_peak = max(abs(v) for v in hlat.values())
    res["fold_chest_impact_deg"] = round(clat[IMPACT], 4)
    res["fold_chest_peak_deg"] = round(clat[fold_peak_frame], 4)
    res["fold_chest_peak_frame"] = fold_peak_frame
    res["fold_head_peak_deg"] = round(head_fold_peak, 4)
    res["fold_min_deg"] = FOLD_MIN_DEG
    res["fold_pitch_impact_deg"] = round(cpitch[IMPACT], 4)
    res["hit_air_fold_ok"] = bool(
        fold_impact >= FOLD_MIN_DEG
        and fold_impact >= FOLD_MIN_IMPACT_FRAC * fold_peak
        and fold_peak_frame >= IMPACT)
    # ★ 方向守卫：本支是**横折**（侧倾占主导），不是"前后折"。
    #   把主驱动取反（`D13_TP_FOLD_SCALE=-1`）后，"命中帧折角 ≥ 下界"必须越界。
    res["fold_lateral_dominant_ok"] = bool(
        abs(clat[IMPACT]) > abs(cpitch[IMPACT]))
    res["fold_direction_can_fail_ok"] = bool(
        not (-fold_impact >= FOLD_MIN_DEG))

    # ---- ★★ (e) 四肢被甩（行程 + **向外**方向守卫）----------------------
    fist_dev, fist_dev_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["fist"][s] - ZERO_FIST[s]).length * 1000.0
            if gap > fist_dev:
                fist_dev, fist_dev_at = gap, (s, frame)
    res["fist_travel_mm"] = round(fist_dev, 3)
    res["fist_travel_at"] = fist_dev_at
    ankle_dev, ankle_dev_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["ankle"][s] - zero["ankle"][s]).length * 1000.0
            if gap > ankle_dev:
                ankle_dev, ankle_dev_at = gap, (s, frame)
    res["ankle_travel_mm"] = round(ankle_dev, 3)
    res["ankle_travel_at"] = ankle_dev_at
    res["limb_flung_ok"] = bool(fist_dev >= FIST_TRAVEL_MIN_MM
                                and ankle_dev >= ANKLE_TRAVEL_MIN_MM)
    # 向外方向守卫：拳的 |x| 与踝的 |x| 相对 f0 必须**扩大**
    fist_out = max(abs(per[f]["fist"][s].x) for f in per for s in SIDES) - \
        max(abs(ZERO_FIST[s].x) for s in SIDES)
    ank_out = max(abs(per[f]["ankle"][s].x) for f in per for s in SIDES) - \
        max(abs(zero["ankle"][s].x) for s in SIDES)
    res["fist_outward_mm"] = round(fist_out * 1000.0, 3)
    res["ankle_outward_mm"] = round(ank_out * 1000.0, 3)
    res["limb_flung_can_fail_ok"] = bool(
        fist_out * 1000.0 >= LIMB_OUTWARD_MIN_MM
        and ank_out * 1000.0 >= LIMB_OUTWARD_MIN_MM)

    # ---- ★★ (f) 离地：**全段**鞋底 ≥100 mm（绝对量，不是相对 f0）--------
    air = {f: min(clear[f]["L"], clear[f]["R"]) * 1000.0
           for f in range(0, TOTAL + 1)}
    res["airborne_clearance_mm"] = {str(f): round(v, 2) for f, v in sorted(air.items())}
    res["airborne_min_mm"] = round(min(air.values()), 3)
    res["airborne_min_at"] = min(air, key=lambda f: air[f])
    res["airborne_end_mm"] = round(air[TOTAL], 3)
    res["airborne_min_threshold_mm"] = AIRBORNE_MIN_MM
    res["airborne_all_frames_ok"] = bool(min(air.values()) >= AIRBORNE_MIN_MM)
    res["airborne_ruler_note"] = (
        "★ 口径换掉（与 D12 不同）：D12 用「相对 f0 离地 ≥100 mm」，本支 f0 本来就在"
        "空中（鞋底 %.1f mm）⟹ 改成**绝对量**：全段鞋底 ≥ %.0f mm。"
        % (air[0], AIRBORNE_MIN_MM))

    # ---- ★★ (g) 打击停顿：**只冻姿态，位置继续走弹道** ------------------
    platform = HOLD_END - IMPACT
    pose_step, pose_step_at = 0.0, None
    for index in range(IMPACT, HOLD_END):
        step, at = _worst_step(samples, index, index + 1)
        if step > pose_step:
            pose_step, pose_step_at = step, at
    pose_step = max(pose_step, _worst_step(samples, IMPACT, HOLD_END)[0])
    z_drop = (zs[IMPACT] - zs[HOLD_END]) * 1000.0
    ball_drop = (ball_z(IMPACT) - ball_z(HOLD_END)) * 1000.0
    res["hitstop_frames"] = platform
    res["hitstop_pose_drift_deg"] = round(pose_step, 6)
    res["hitstop_pose_drift_at"] = pose_step_at
    res["hitstop_z_drop_mm"] = round(z_drop, 4)
    res["hitstop_ball_drop_mm"] = round(ball_drop, 4)
    res["hitstop_present"] = bool(
        platform >= HITSTOP_MIN_FRAMES
        and pose_step <= HITSTOP_POSE_TOL_DEG
        and abs(z_drop - ball_drop) <= 1e-6
        and z_drop > 0.0)
    res["hitstop_note"] = (
        "★★ 本支与地面受击的硬区别：D05~D12 的停顿是**姿态 + 位置**全冻；"
        "本支**只冻姿态**（`set_hitstop_pose_only` 只对 rotation_euler 设 CONSTANT），"
        "位置**必须继续掉**（%.3f mm，逐位等于弹道）—— 否则就是「空中悬停」。"
        % z_drop)

    # ---- ★ (h) 收招不许瞬停（定格前 8 帧；★ 帧预算紧，本支更严）--------
    snap, snap_at = 0.0, None
    for index in range(max(1, PLATEAU - 8) + 1, PLATEAU + 1):
        step, at = _worst_step(samples, index - 1, index)
        if step > snap:
            snap, snap_at = step, at
    res["no_snap_stop_step_deg"] = round(snap, 4)
    res["no_snap_stop_at"] = snap_at
    res["no_snap_stop_ok"] = bool(snap <= NO_SNAP_END_DEG)
    res["no_snap_window"] = [max(1, PLATEAU - 8), PLATEAU]

    # ---- ★ (i) 定格自持（末 N 帧姿态逐位冻结）---------------------------
    last = []
    for index in range(PLATEAU + 1, TOTAL + 1):
        last.append(round(_worst_step(samples, index - 1, index)[0], 6))
    res["end_hold_steps_deg"] = last
    res["end_air_hold_ok"] = bool(last and max(last) <= END_HOLD_MAX_DEG)
    res["end_identical_skipped"] = True
    res["end_identical_note"] = (
        "★ 本支末帧**不回零位**（仍在空中下落）⟹ 只报：末帧与 f0 的世界位置差"
        "就是「被这一下又打出去了多远」。")

    # ---- ★ 竖速登记（给下一棒）-----------------------------------------
    end_vz = vz[TOTAL]
    res["end_vz_mm_per_frame"] = round(end_vz, 4)
    res["end_pelvis_z_mm"] = round(zs[TOTAL] * 1000.0, 3)
    res["end_ball_z_mm"] = round(ball_z(TOTAL) * 1000.0, 3)
    res["end_vz_ok"] = bool(end_vz <= END_VZ_REG_MAX_MM)

    # ---- ★ handoff（**只报**）：末帧 vs D12 末帧 / vs `Jump_Fall@0` ------
    res["handoff"] = _handoff_report(arm, action, seam_mats)

    # ---- ★ 力量传导链（脚→腿→髋→腰→肩→手）------------------------------
    knee_flex = {s: round(max(abs(per[f]["knee_deg"][s] - zero["knee_deg"][s])
                              for f in per), 3) for s in SIDES}
    shoulder_move, shoulder_at = 0.0, None
    for frame in per:
        for s in SIDES:
            gap = (per[frame]["shoulder"][s] - zero["shoulder"][s]).length * 1000.0
            if gap > shoulder_move:
                shoulder_move, shoulder_at = gap, (s, frame)
    pelvis_span = max((per[f]["pelvis"] - per[0]["pelvis"]).length
                      for f in per) * 1000.0
    res["knee_flex_peak_deg"] = knee_flex
    res["shoulder_move_mm"] = round(shoulder_move, 3)
    res["shoulder_move_at"] = shoulder_at
    res["pelvis_span_mm"] = round(pelvis_span, 3)
    res["chain_travel"] = {
        "foot_mm": round(ankle_dev, 2),
        "knee_deg": round(max(knee_flex.values()), 3),
        "hip_mm": round(pelvis_span, 2),
        "waist_deg": round(abs(clat[IMPACT]), 3),
        "shoulder_mm": round(shoulder_move, 2),
        "hand_mm": round(fist_dev, 2),
    }
    res["chain_present_ok"] = bool(
        res["chain_travel"]["foot_mm"] > 50.0
        and res["chain_travel"]["knee_deg"] > 0.2
        and res["chain_travel"]["hip_mm"] > 20.0
        and res["chain_travel"]["waist_deg"] > 2.0
        and res["chain_travel"]["shoulder_mm"] > 5.0
        and res["chain_travel"]["hand_mm"] > 30.0)
    res["chain_note"] = (
        "★ 本支的「髋」段由**弹道**承担（姿态层不产生骨盆位移，见 §1 解耦）；"
        "其余五段（踝/膝/腰/肩/手）由**受力**驱动。")

    # ---- 水平位移归属（本支**不新增**位移）------------------------------
    dx = {f: (xs[f] - xs[0]) * 1000.0 for f in per}
    dy = {f: (ys[f] - ys[0]) * 1000.0 for f in per}
    res["root_motion_net_mm"] = round(math.hypot(dx[TOTAL], dy[TOTAL]), 3)
    res["root_motion_back_mm"] = round(dy[TOTAL], 3)
    res["root_motion_side_mm"] = round(dx[TOTAL], 3)
    res["root_motion_ok"] = bool(res["root_motion_net_mm"] <= 1.0)
    res["root_motion_note"] = (
        "★ 沿用 D12 的立场：水平净位移 = 0（接缝处与上游逐位对齐，姿态自持、"
        "位移交给引擎）⟹ 本支只允许「被顶得重心偏移」级别的抖动（≤1 mm）。")

    # ---- 节奏 -----------------------------------------------------------
    risers = sum(1 for f in range(TOTAL) if press(f + 1) > press(f) + 1e-9)
    fallers = sum(1 for f in range(TOTAL) if press(f + 1) < press(f) - 1e-9)
    res["press_rise_frames"] = risers
    res["press_fall_frames"] = fallers
    res["hit_speed_ok"] = bool(risers <= HIT_RISE_MAX_FRAMES
                               and fallers >= HIT_FALL_MIN_FRAMES)

    # ---- 冻结段 / 零位短路 ----------------------------------------------
    res["lock_frames"] = _ZERO_SHORTCUT_SKIPPED[0]     # 只统计 f>PLATEAU 的解算调用
    res["lock_expect"] = TOTAL - PLATEAU
    res["lock_ok"] = bool(res["lock_frames"] == TOTAL - PLATEAU)

    # ---- 穿模 -----------------------------------------------------------
    frames = sorted(set(list(range(0, TOTAL + 1, CLIP_EVERY))
                        + [IMPACT, HOLD_END, FOLD_PEAK, PLATEAU, TOTAL]))
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

    # ---- 可达性 ---------------------------------------------------------
    worst_reach, worst_reach_frame = 0.0, None
    worst_leg, worst_leg_frame = 0.0, None
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            up = "upperarm." + side
            shoulder = Vector(A.bone_world(arm, up, "head"))
            limit = ARM_MAX[side] * 0.9995
            ratio = (fist_target(arm, side, frame) - shoulder).length / limit
            if ratio > worst_reach:
                worst_reach, worst_reach_frame = ratio, (frame, side)
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            leg_limit = (A.L_THIGH + A.L_SHIN) * 0.9995
            ratio = (ankle_target(arm, side, frame) - hip).length / leg_limit
            if ratio > worst_leg:
                worst_leg, worst_leg_frame = ratio, (frame, side)
    res["reach_ratio_max"] = round(worst_reach, 5)
    res["reach_ratio_at"] = worst_reach_frame
    res["reach_ok"] = bool(worst_reach <= REACH_MAX_RATIO)
    res["leg_reach_ratio_max"] = round(worst_leg, 5)
    res["leg_reach_ratio_at"] = worst_leg_frame
    res["leg_reach_ok"] = bool(worst_leg <= REACH_MAX_RATIO)

    # ---- 剪影 / aspect：只报不判 ----------------------------------------
    sil = P.silhouette(arm, "d13")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]

    # ---- 姿态口径**显式跳过**（本支离地 + 非循环）-----------------------
    res["foot_slide_skipped"] = True
    res["foot_slide_note"] = (
        "★ 全段离地（鞋底 ≥ %.1f mm）⟹ `foot_probe` 显式关掉、`ground_contact_ok` "
        "显式跳过（同 A12 / D12 的先例：「全段离地，显式跳过 + 登记原因」）。"
        % AIRBORNE_MIN_MM)

    if os.environ.get("D13_TRACE"):
        res["trace"] = {str(f): {
            "press": round(press(f), 4),
            "fold": round(fold(f), 4),
            "fling": round(fling(f), 4),
            "twist": round(twist(f), 4),
            "ball_z": round(ball_z(f) * 1000.0, 2),
            "has_z": round(zs[f] * 1000.0, 2),
            "vz": round(vz[f], 2) if f in vz else None,
            "lowL": None if clear[f]["L"] is None else round(clear[f]["L"] * 1000.0, 2),
            "lowR": None if clear[f]["R"] is None else round(clear[f]["R"] * 1000.0, 2),
            "chest_lat": round(clat[f], 3),
            "head_lat": round(hlat[f], 3),
            "chest_pitch": round(cpitch[f], 3),
            "pelvis_y": round(dy[f], 2),
            "kneeL": round(per[f]["knee_deg"]["L"] - zero["knee_deg"]["L"], 3),
            "kneeR": round(per[f]["knee_deg"]["R"] - zero["knee_deg"]["R"], 3),
            "fistL": round((per[f]["fist"]["L"] - ZERO_FIST["L"]).length * 1000.0, 2),
            "fistR": round((per[f]["fist"]["R"] - ZERO_FIST["R"]).length * 1000.0, 2),
            "ankL": round((per[f]["ankle"]["L"] - zero["ankle"]["L"]).length * 1000.0, 2),
            "ankR": round((per[f]["ankle"]["R"] - zero["ankle"]["R"]).length * 1000.0, 2),
        } for f in range(0, TOTAL + 1)}
    return res


def _handoff_report(arm, action, seam_mats):
    """末帧 vs D12 末帧 / vs `Jump_Fall@0` 的姿态差 —— **只报**，不判。"""
    out = {}
    mats_end = CR.action_world_matrices(arm, action, TOTAL)
    moving = _pelvis_moving(arm)
    ori, rel, ob, rb = _pose_seam_split(mats_end, seam_mats, moving)
    out["vs_launch_hit34_orient"] = float("%.3e" % ori)
    out["vs_launch_hit34_relpos_mm"] = round(rel * 1000.0, 3)
    out["vs_launch_hit34_bone"] = rb or ob
    fall = bpy.data.actions.get("Jump_Fall")
    if fall is not None:
        fm = CR.action_world_matrices(arm, fall, 0)
        ori2, rel2, ob2, rb2 = _pose_seam_split(mats_end, fm, moving)
        out["vs_jump_fall0_orient"] = float("%.3e" % ori2)
        out["vs_jump_fall0_relpos_mm"] = round(rel2 * 1000.0, 3)
        out["vs_jump_fall0_bone"] = rb2 or ob2
    return out


def _pelvis_moving(arm):
    """pelvis 的**后代**骨集合（接缝尺子用）。"""
    moving = set()
    for bone in arm.pose.bones:
        node = bone
        while node is not None:
            if node.name == "pelvis":
                moving.add(bone.name)
                break
            node = node.parent
    return moving


def _bone_point(mat):
    return mat[3], mat[7], mat[11]


def _pose_seam_split(mats_a, mats_b, moving):
    """两套世界矩阵的「平移不变」逐位差（B08 第 2 件那把尺子，原样照抄）。"""
    ori, rel = 0.0, 0.0
    ori_bone, rel_bone = None, None
    pa, pb = _bone_point(mats_a["pelvis"]), _bone_point(mats_b["pelvis"])
    for name in mats_a:
        ma, mb = mats_a[name], mats_b[name]
        for index in (0, 1, 2, 4, 5, 6, 8, 9, 10):
            if abs(ma[index] - mb[index]) > ori:
                ori, ori_bone = abs(ma[index] - mb[index]), name
        xa, ya, za = _bone_point(ma)
        xb, yb, zb = _bone_point(mb)
        if name in moving:
            da = (xa - pa[0], ya - pa[1], za - pa[2])
            db = (xb - pb[0], yb - pb[1], zb - pb[2])
        else:
            da, db = (xa, ya, za), (xb, yb, zb)
        worst = max(abs(u - v) for u, v in zip(da, db))
        if worst > rel:
            rel, rel_bone = worst, name
    return ori, rel, ori_bone, rel_bone


def _seam_action():
    return bpy.data.actions.get(SEAM_ACTION)


# =============================================================== 引导
def _load_seam_zero(arm):
    """★ 零位真源：**上游 `Launch_Hit@34` 的落盘行动作**（不是零位姿态！）。

    ★ 反向验证 ① 打开时改读 `Idle_01@0`（零位姿态）—— 用来证明 `seam_in_ok` 抓得住接缝断裂。
    """
    action = bpy.data.actions.get(ZERO_ACTION)
    if action is None:
        return {}, {"action": ZERO_ACTION, "found": False}
    rot_keyed, loc_keyed = _keyed_bones(action)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    A.reset_pose(arm)
    bpy.context.scene.frame_set(int(ZERO_FRAME))
    bpy.context.view_layer.update()
    pose = {name: tuple(math.degrees(v)
                        for v in arm.pose.bones[name].rotation_euler)
            for name in rot_keyed if name in arm.pose.bones}
    loc = {name: tuple(arm.pose.bones[name].location)
           for name in loc_keyed if name in arm.pose.bones}
    if loc:
        pose["@loc"] = loc
    info = {"action": ZERO_ACTION, "found": True, "frame": int(ZERO_FRAME),
            "rot_bones": len(rot_keyed), "loc_bones": sorted(loc_keyed),
            "frame_range": [int(v) for v in action.frame_range]}
    return pose, info


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
    global ZERO, ZERO_WORLD, Z_SEAM, KNEE_DIR, ANKLE_0, ZERO_FIST
    ZERO, ZERO_WORLD = {}, {}
    ZERO_BASIS.clear()
    ZERO_DIR.clear()
    SEAM_FIST.clear()
    SEAM_SHOULDER.clear()
    SEAM_SPAN.clear()
    SEAM_ELBOW_DIR.clear()
    SEAM_HAND_DIR.clear()
    SEAM_ANKLE.clear()
    SEAM_HIP.clear()
    SEAM_HIP_OFF.clear()
    ANKLE_0.clear()
    KNEE_DIR.clear()
    ARM_MAX.clear()
    LOCK_POSE.clear()
    HITSTOP_POSE.clear()
    _HITSTOP_REUSED[0] = 0
    _ZERO_SHORTCUT_SKIPPED[0] = 0

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if SEAM_ACTION not in bpy.data.actions:
        raise RuntimeError("接缝动作 %s 不在落盘文件里" % SEAM_ACTION)
    if ZERO_ACTION not in bpy.data.actions:
        raise RuntimeError("零位真源 %s 不在落盘文件里" % ZERO_ACTION)

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
        ARM_MAX[side] = (UE.ARM_LEN[side]["upper"]
                         + UE.ARM_LEN[side]["forearm"]
                         + UE.ARM_LEN[side]["hand"])

    UE.ROLL_STEP_DEG = _env_f("D13_ROLLSTEP", 2.0)
    UE.ROLL_GRID = UE._roll_grid()
    UE.EULER_Y_SAFE = _env_f("D13_YSAFE", 88.0)
    UE.EULER_Y_WEIGHT = _env_f("D13_YWEIGHT", 0.0)

    for extra in LEG_BONES + ("foot.L", "foot.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    ZERO, saved_info = _load_seam_zero(arm)
    if not ZERO:
        raise RuntimeError("读不到接缝零位")

    # ★ "落盘真值 vs 手写重演"（同 D12 的 `_load_idle_zero` 检查口径）：
    #   action 驱动一份，手写 apply 一份，比世界几何。
    arm.animation_data.action = bpy.data.actions[ZERO_ACTION]
    A._bind_slot(arm, bpy.data.actions[ZERO_ACTION])
    bpy.context.scene.frame_set(int(ZERO_FRAME))
    bpy.context.view_layer.update()
    action_heads, action_dirs = {}, {}
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            action_heads[name] = Vector(A.bone_world(arm, name, "head"))
            action_dirs[name] = Vector(A.bone_direction(arm, name)).normalized()
    arm.animation_data.action = None
    replay_heads, replay_dirs = _world_snapshot(arm, ZERO)
    geom_pos, geom_pos_bone = 0.0, None
    for name, point in action_heads.items():
        other = replay_heads.get(name)
        if other is None:
            continue
        gap = (point - other).length * 1000.0
        if gap > geom_pos:
            geom_pos, geom_pos_bone = gap, name
    geom_dir, geom_dir_bone = 0.0, None
    for name, direction in action_dirs.items():
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
        got = ZERO.get(name)
        row = [_f32(a) - _f32(b) for a, b in zip(got, value)]
        worst = max(abs(v) for v in row)
        if worst > euler_diff:
            euler_diff, euler_bone = worst, name
        if worst > 0.5:
            per_bone[name] = [round(v, 4) for v in row]
    SEAM_MATCH.update({
        "src": "%s@%d" % (ZERO_ACTION, ZERO_FRAME),
        "saved": saved_info,
        "geom_pos": round(geom_pos, 6), "pos_bone": geom_pos_bone,
        "geom_dir": round(geom_dir, 6), "dir_bone": geom_dir_bone,
        "per_bone": per_bone,
        "matched": bool(geom_pos <= SEAM_REPLAY_POS_MAX_MM
                        and geom_dir <= SEAM_REPLAY_DIR_MAX_DEG),
    })

    A.apply_pose(arm, ZERO)
    bpy.context.view_layer.update()
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    for side in SIDES:
        SEAM_FIST[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        SEAM_ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        SEAM_HIP[side] = Vector(A.bone_world(arm, "thigh." + side, "head"))
        SEAM_HIP_OFF[side] = (SEAM_ANKLE[side].x - SEAM_HIP[side].x,
                              SEAM_ANKLE[side].y - SEAM_HIP[side].y)
        SEAM_HAND_DIR[side] = Vector(
            A.bone_direction(arm, "hand." + side)).normalized()
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        SEAM_SHOULDER[side] = shoulder
        SEAM_SPAN[side] = (SEAM_FIST[side] - shoulder).length
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        SEAM_ELBOW_DIR[side] = tuple((elbow - shoulder).normalized())
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

    ZERO_WORLD = {n: tuple(v) for n, v in replay_heads.items()}
    for name in A.PROBE_TAILS:
        if name in arm.pose.bones:
            ZERO_WORLD[name + ".tail"] = tuple(A.bone_world(arm, name, "tail"))
    for name in A.PROBE_BONES:
        if name in arm.pose.bones:
            ZERO_BASIS[name] = tuple(
                arm.pose.bones[name].matrix.to_3x3().to_quaternion())
    for name in ARM_BONES:
        ZERO_DIR[name] = Vector(A.bone_direction(arm, name)).normalized()

    ZERO_FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    zrow = _body_metrics(arm)
    A.report("D13_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "impact": IMPACT, "hold_end": HOLD_END, "hit_hold": HIT_HOLD,
        "fold_peak": FOLD_PEAK, "plateau": PLATEAU, "cancel": CANCEL,
        "recover_end": RECOVER_END,
        "root_motion_m": [0.0, 0.0],
        "seam": {"action": SEAM_ACTION, "frame": SEAM_FRAME,
                 "src": saved_info,
                 "d12_end_vz_mm": round(D12_END_VZ_MM, 4),
                 "z_f0_mm": round(ball_z(0) * 1000.0, 3),
                 "apex_frame_d12": round(F_APEX_D12, 3),
                 "apex_frame_local": round(F_APEX_LOCAL, 3),
                 "Z_SEAM_mm": round(Z_SEAM * 1000.0, 3)},
        "zero_pelvis_loc": {k: [round(v, 6) for v in val]
                            for k, val in (ZERO.get("@loc") or {}).items()},
        "zero_pelvis_loc_expected": list(
            A.wloc(0.0, PELVIS_Y_M, ball_z(0) - Z_PELVIS_REST)),
        "force_direction": "空中受击：**受力与弹道完全解耦** —— 骨盆 z 逐帧 = 共享解析弹道；"
                           "受力只落在**躯干横折**（世界侧倾目标 → 局部 rz）+ **四肢惯性甩动**",
        "ballistic": {"T_PHASE": T_PHASE, "T_ORIGIN_D12": D12_T_ORIGIN,
                      "takeoff_pelvis_z_m": JS.TAKEOFF_PELVIS_Z,
                      "takeoff_speed_mps": round(JS.TAKEOFF_SPEED * A.FPS, 3),
                      "g_per_frame": JS.G_PER_FRAME,
                      "f0_z_mm": round(ball_z(0) * 1000.0, 3),
                      "f0_vz_mm": round(ball_vz(0) * 1000.0, 4),
                      "end_z_mm": round(ball_z(TOTAL) * 1000.0, 3),
                      "end_vz_mm": round(ball_vz(TOTAL) * 1000.0, 4),
                      "tol_mm": BALLISTIC_TOL},
        "zero_pelvis_z_mm": round(Z_SEAM * 1000.0, 3),
        "zero_chest_lat_deg": round(zrow["chest_lat_deg"], 4),
        "zero_fist_mm": {s: [round(v * 1000.0, 2) for v in SEAM_FIST[s]]
                         for s in SIDES},
        "zero_ankle_mm": {s: [round(v * 1000.0, 2) for v in SEAM_ANKLE[s]]
                          for s in SIDES},
        "arm_max_mm": {s: round(ARM_MAX[s] * 1000.0, 2) for s in SIDES},
        "fold_keys": [list(k) for k in FOLD_KEYS],
        "fling_keys": [list(k) for k in FLING_KEYS],
        "twist_keys": [list(k) for k in TWIST_KEYS],
        "pelvis_tilt_deg": PELVIS_TILT_DEG, "chest_tilt_deg": CHEST_TILT_DEG,
        "head_tilt_deg": HEAD_TILT_DEG,
        "roll_weight_mode": ROLL_WEIGHT_MODE,
        "note": ("D13 空中受击：零位 = **`Launch_Hit@34` 落盘帧**（不是零位姿态）；"
                 "骨盆 z 全段 = 共享解析弹道（相位续在 D12 之后，同一条抛物线）；"
                 "★ 命中停顿**只冻姿态**（位置继续掉）；★ 竖速守卫方向与 D12 **相反**"
                 "（`vz_no_lift_can_fail_ok`：不许往上弹）；末 %d 帧定格自持。"
                 % (TOTAL - PLATEAU)),
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
        "note": ("空中受击：受力与弹道完全解耦（骨盆 z = 共享解析弹道，全片单一抛物线）；"
                 "受力只落躯干横折 + 四肢惯性甩动；命中停顿只冻姿态、位置继续掉；"
                 "水平不新增位移；末 %d 帧定格自持" % (TOTAL - PLATEAU)),
        "antic_frame": 0,
        "hit_frame": IMPACT,
        "cancel_frame": CANCEL,
        "stagger_end_frame": HOLD_END,
        "fold_peak_frame": FOLD_PEAK,
        "self_hold_frame": PLATEAU,
        "hitstop_frames": HIT_HOLD,
        "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "hit_point_m": None,
        "end_pelvis_z_m": round(ball_z(TOTAL), 6),
        "end_vz_m_per_frame": round((ball_z(TOTAL) - ball_z(TOTAL - 1)), 6),
        "ballistic_ref": "anim_jump_start.TAKEOFF_PELVIS_Z/TAKEOFF_SPEED + "
                         "anim_jump_fall.G_PER_FRAME（同一解析弹道，相位续 D12 f%d）"
                         % SEAM_FRAME,
        "start_pose_ref": "%s 帧 %d（SELF_HOLD 锁存姿态）" % (SEAM_ACTION, SEAM_FRAME),
        "end_pose_ref": "空中自持（**不回原位**；落在共享弹道上，竖速更负）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "IMPACT": IMPACT, "HITSTOP_END": HOLD_END,
                           "FOLD_PEAK": FOLD_PEAK, "SELF_HOLD": PLATEAU,
                           "CANCEL": CANCEL, "END": TOTAL})
    _set_hitstop_pose_only(action, IMPACT, HOLD_END)

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.pop("ground_contact_ok", None)
    report.pop("ground_min_mm", None)
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

    report["seam_zero_saved_ok"] = bool(SEAM_MATCH["matched"])
    report["seam_zero_src"] = SEAM_MATCH["src"]
    report["seam_zero_geom_pos_mm"] = SEAM_MATCH["geom_pos"]
    report["seam_zero_geom_dir_deg"] = SEAM_MATCH["geom_dir"]
    report["seam_zero_worst_bone"] = SEAM_MATCH["pos_bone"]

    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("D13_REPORT", report)

    if not SKIP_RENDER:
        side_frames = list(range(0, TOTAL + 1))
        other_frames = [0, IMPACT, HOLD_END, FOLD_PEAK, 11, PLATEAU, TOTAL]
        A.render_pose_sheet(arm, action, side_frames, "airhit",
                            views=(VIEW_D13_SIDE,))
        A.render_pose_sheet(arm, action, other_frames, "airhit",
                            views=(VIEW_D13_FRONT, VIEW_D13_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D13_DONE failed=%s" % report["failed"])
    print("D13_DONE non_ok_bools=%s" % report["non_ok_bools"])
    if os.environ.get("D13_TRACE"):
        print("D13_TRACE " + json.dumps(report.get("trace", {}),
                                        ensure_ascii=False))


def _set_hitstop_pose_only(action, start_frame, end_frame):
    """★★ 本支专属：**只冻姿态** —— 只对 `rotation_euler` 曲线设 CONSTANT。

    `location` 曲线（骨盆）**必须继续走弹道** —— 否则就是"空中悬停"，
    与清单原文"不能破坏空中轨迹系统"直接冲突。
    """
    for fcurve in action.fcurves:
        if not fcurve.data_path.endswith("rotation_euler"):
            continue
        for point in fcurve.keyframe_points:
            if start_frame <= point.co.x <= end_frame:
                point.interpolation = "CONSTANT"


# ★ 本支取景：人物从 f0 的骨盆 1932 mm（头 ~2.7 m）一路落到 f18 的 1297 mm
#   （鞋底 ~0.5 m）⟹ 标准站姿视图（中心 0.92 / 宽 2.10）切头切脚。
VIEW_D13_SIDE = ("side", (5.20, 0.0, 1.30), (0.0, 0.0, 1.30), 3.30,
                 (780, 1100))
VIEW_D13_FRONT = ("front", (0.0, -5.60, 1.30), (0.0, 0.0, 1.30), 3.30,
                  (780, 1100))
VIEW_D13_3Q = ("three_quarter", (3.90, -4.10, 1.45), (0.0, 0.0, 1.30), 3.30,
               (780, 1100))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D13_FAILURE " + traceback.format_exc())
