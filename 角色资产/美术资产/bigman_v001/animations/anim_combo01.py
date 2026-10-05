"""anim_combo01 —— C01 `Combo_Finish` 连招终结（C 族第一支，**带 Root Motion**）。

=============================================================================
清单原文
=============================================================================
「大幅度重拳、踢飞或双拳砸击，动作幅度 ≥ 普通攻击的 **1.5 倍**」。

选型：**双拳过顶劈砸**（step-in overhead double-fist smash）——
清单给出的三种里唯一能把"幅度 ≥ 1.5×"与"末帧逐位回 Idle"同时做稳的一种。
（单臂摆拳的臂链只有 0.65 m，相对骨盆的行程天花板 ~1.1 m，
够不到 1.5 × B 族最大 1218 mm；双拳过顶的弧线才够。）
与 C07 `Ground_Smash`（双拳高举后**砸地**、配裂纹震屏）的区别：C01 是**连招收尾**，
劈砸的落点在**身前中段高度**（砸人不是砸地），且带跨步前冲与命中停顿。

=============================================================================
第 0 件 —— "≥1.5 倍"必须先在**可判定量**上落地（`probe_combo01*.py` 实测）
=============================================================================
1.5 倍是清单的硬要求，但"幅度"不是量。本支把 B 族（普通攻击 B01~B10）**全族**
逐帧实测，取**同维度的全族最大值**做基准。第一轮探针（`probe_combo01.py`）
给出的事实：

    拳世界两点极差   max = Air_Heavy 1729.39 mm（含 813 mm 自由落体 ⟹ 被位移污染）
    拳世界路径长     max = Air_Heavy 2705.31 mm（同上）
    ⟹ 世界口径在有 Root Motion / 空中支上**不可比**（B10 的教训 11：
      "先问这个量是相对谁的"）。**全部改用骨盆系口径**（把整具身体的平移减掉）。

★ 第 0 件 A —— **两个候选维度在 1.5 倍上物理不可达，如实登记、换维度**：

  (a)「躯干前倾极差」1.5 × Heavy_02 (501.0) = **751.5 mm**。
      脊柱（pelvis.head → neck.head）长 L ≈ 0.52 m。把一条长 L 的链弯成圆弧，
      末端相对根的最大矢高 = R(1−cos θ)，R = L/θ；对 θ 求极值（θ sinθ = 1−cos θ）
      得 θ* ≈ 135°、矢高上界 **0.377 m** ⟹ 极差上限 **0.754 m**。
      0.7515 / 0.754 = **99.7%** —— 要求脊柱**前后各折 135°**，那是杂技不是重拳。
      ⟹ 本维度**不进门禁**，只作诊断上报（阈值 1.2× = 601 mm，落在可行区间）。
  (b)「拳相对骨盆的两点极差」本身也被臂链锁死：肩到骨盆 0.565 m + 臂链 0.65 m
      ⟹ 拳离骨盆 ≤ ~1.05 m，两点极差 ≤ ~2.0 m。1.5 × Heavy_02 (1218.22) = 1827.33，
      落在可达区间的**上沿**（本支实测 1.90 m 量级）。
      ⟹ 保留，但它是**本支最紧的一条**，必须真做出来。

★ 第 0 件 B —— 最终门禁（三条，全部**骨盆系**，阈值 = 1.5 × B 族同维度最大）：

    ① `fist_rel_range_mm`  ≥ 1.5 × 1218.22 (Heavy_02) = **1827.33**
       打击手相对骨盆的**最大两点距离**（= 动作幅度本身）
    ② `fist_rel_path_mm`   ≥ 1.5 × 2401.37 (Heavy_02) = **3602.05**
       打击手相对骨盆的**路径长度**（弧长；无几何天花板，量的是"甩了多大一圈"）
    ③ `swing_step_rel_mm`  ≥ 1.5 × 95.10   (Air_Light) = **142.65**
       摆动脚**单帧相对位移**（步幅速率）
    + 诊断（不判）：`torso_pitch_range_mm`（阈值 1.2× = 601 mm，见 0.A(a)）

=============================================================================
第 1 件 —— 上游接缝 = `Heavy_01@36`（B04 的**可取消帧**）
=============================================================================
清单 §0.3 把 `CANCEL` 定义为"从这一帧起可接下一段连招" —— 连招终结接在普通攻击
之后，接的**就是**那一帧。实测 `Heavy_01@36`（探针 `COMBO01B_SEAM`）：

    pelvis 世界 = (3.34, −89.39, 806.68) mm
    L 踝 = (152.18, −329.58, 79.74)  相对骨盆 **+240.2 mm（前）**  髋踝距 777.99
    R 踝 = (−141.58, 140.44, 79.80)  相对骨盆 **−229.8 mm（后）**  髋踝距 774.08
    腿长 822.00 ⟹ 余量 44.0 / 47.9 mm（已踩到 Heavy_01 自己的收招站架）

出口接缝 = `Idle_01@0`（平移不变尺子；Idle 相对骨盆 L +169.57 / R −140.43）。

=============================================================================
第 2 件 —— **单支撑的天花板逼出"两步 + 1 帧小跳"的脚步表**
=============================================================================
髋→踝水平可达距离 = √(822² − dz²)。本支命中帧骨盆 z = 718 mm ⟹ dz = 640
⟹ 水平 515.8 mm；接缝站架骨盆 z = 806.68 ⟹ dz = 728.7 ⟹ 水平 **379.6 mm**。
于是"脚在世界里钉死"的前提下，身体相对任何一只脚最多前后各走 ~380~515 mm。

Root Motion 900 mm ⟹ **必须两只脚都换**。由"落脚点 = 出口接缝反推"（同 B10）：

    R 落点相对髋 = (D_TOTAL − 140.43) − D(T_R_ON)
    L 落点相对髋 = (D_TOTAL + 169.57) − D(T_L_ON)

取 D_TOTAL = 900 mm、R 落点 ≈ +290（前）、L 落点 ≈ +290（前）：

    R 支撑 [0, 16] ∪ [25, 48]     R 摆动 (16, 25) = **9 帧**，世界步 989.4 mm
    L 支撑 [0, 24] ∪ [33, 48]     L 摆动 (24, 33) = **9 帧**，世界步 829.4 mm

★ **任何一帧都至少有一只脚在支撑**（f17~24 靠 L、f25~32 靠 R）—— 不做腾空，
  于是 `ground_contact` 全程有定义，不必像 B09 那样记 None。

=============================================================================
第 3 件 —— 摆动脚单帧步长（门禁③）是**双边界**鞍点，不是"越快越好"
=============================================================================
`_swing_u(s) = 1 − (1−s)^p`：p > 1 ⟹ 最大增量落在摆动**开始**的几帧。

本支的摆动单帧步长被**两条方向相反的边界**夹住：

    · 下界 `swing_step_rel_mm ≥ 142.65`（门禁③ = 1.5 × B 族最大 95.10）
    · 上界 `no_teleport ≤ 25°`（§6 通用门禁，量的是 thigh 的**局部欧拉**通道）

前端发力（大 p）把整段行程压在首帧 ⟹ 越过上界；改线性（小 p）又把峰值压到
142 以下 ⟹ 越过下界。实测地形（`C01_R_POW` / `C01_L_POW` 离线扫参）：

    R_POW  L_POW | 单帧最大步长（位置）        | rel 步长 R / L  | 结论
    ------------ | --------------------------- | --------------- | ----
    2.40   2.60  | **25.873 @f17 thigh.R**     | 204.69 / 166.38 | ❌ 越上界
    1.30   2.60  | 25.499 @f25 thigh.L         | ≤166.38 / 166.38| ❌ 峰换手到 L
    1.90   2.30  | **24.385 @f10 forearm.R**   | 160.11 / 145.03 | ✅ 两侧同时进窗口
    1.90   2.40  | 24.385 @f10 forearm.R       | 160.11 / 152.21 | ✅

★ B10 第 4 条在此处**第二次应验**：峰会在"摆动腿"与"前摇臂"之间换手。
  把腿的 p 压下去之后，天花板立刻变成 `forearm.R` 的前摇段（f10）——
  那不是腿的参数能动的。**剩下 0.615° 就是本支的真实余量，如实登记，不凑。**
★ 手与腿的欧拉是**各自的局部空间**，只能同框比"度数"，不能互相换算；
  **单看一个量会被"加帧"骗过去**（见第 0 件 B 的三维度设计）。

=============================================================================
第 4 件 —— 命停只冻**打击姿态**，不冻位移（同 B10 的地面版口径）
=============================================================================
`HIT 30`、`HOLD 4`（f30~f33 关节欧拉逐位冻结）。骨盆照常前冲
D(33) − D(30) = 60 mm ⟹ `hitstop_momentum_mm` > 0。
腿照常工作（L 就在 f33 落地）—— 冻腿会让"前进的骨盆 + 冻住的腿"把支撑脚拖走。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_combo01.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_heavy_01 as H  # noqa: E402
import anim_run_stop as RS  # noqa: E402
import anim_walk_f as WF  # noqa: E402
import anim_jump_start as JS  # noqa: E402

NAME = "Combo_Finish"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"


# ---------------------------------------------------------------- 离线调参入口
def _env_f(key, default):
    try:
        return float(os.environ[key])
    except (KeyError, ValueError):
        return default


def _env_i(key, default):
    try:
        return int(os.environ[key])
    except (KeyError, ValueError):
        return default


def _env_p(key, default):
    return os.environ.get(key, default)


# ---------------------------------------------------------------- 帧预算
TOTAL = _env_i("C01_TOTAL", 48)                 # 0.800 s @60fps
ANTIC = _env_i("C01_ANTIC", 15)                 # 前摇结束（§0.1 重攻击 12~20 帧）
BURST = ANTIC
HIT = _env_i("C01_HIT", 30)                     # 命中帧
HOLD = _env_i("C01_HOLD", 4)                    # 命停 4 帧 ⟹ f30~f33（§0.1 上限）
HOLD_END = HIT + HOLD - 1                       # 33
RETURN_START = HOLD_END + 1                     # 34
CANCEL = _env_i("C01_CANCEL", 40)

# ---------------------------------------------------------------- 脚步时刻表
T_R_OFF = _env_i("C01_R_OFF", 16)               # R（后脚）蹬离地
T_R_ON = _env_i("C01_R_ON", 25)                 # R 落地
T_L_OFF = _env_i("C01_L_OFF", 24)               # L（前脚）蹬离地
T_L_ON = _env_i("C01_L_ON", 33)                 # L 落地（与命停末帧同帧）
WINDOWS = {"L": ((0, T_L_OFF), (T_L_ON, TOTAL)),
           "R": ((0, T_R_OFF), (T_R_ON, TOTAL))}
SIDES = ("L", "R")

TIP3 = 3.0
TIP_RAMP = 3
R_LIFT = _env_f("C01_R_LIFT", 0.135)            # R 摆动离地峰值（米）
L_LIFT = _env_f("C01_L_LIFT", 0.115)
R_SWING_POW = _env_f("C01_R_POW", 1.90)         # R 摆动前端发力指数（见文件头第 3 件）
L_SWING_POW = _env_f("C01_L_POW", 2.30)
SOLE_FLOOR_MM = _env_f("C01_SOLE_FLOOR", -0.8)
LEG_TAIL_START = _env_i("C01_LEGTAIL0", T_L_ON)
_LEG_EASE = os.environ.get("C01_LEGEASE", "quad")

# ---------------------------------------------------------------- Root Motion
# 骨盆前冲量 D（mm，正 = 向前 = 世界 −y）。**Hermite 轨道**，不是解析式：
# 本支的起手是"站架蓄力"（速度 ~0），不是 B10 的"接 Run 的 2.75 m/s"，
# 所以速度剖面是**先向后坐、再爆发前冲、再收**的鼓包，而不是单调减速。
D_KEYS = ((0, 0.0), (10, _env_f("C01_D10", -60.0)),
          (15, _env_f("C01_D15", -45.0)), (20, _env_f("C01_D20", 180.0)),
          (25, _env_f("C01_D25", 470.0)), (30, _env_f("C01_D30", 720.0)),
          (35, _env_f("C01_D35", 820.0)), (40, _env_f("C01_D40", 870.0)),
          (TOTAL, _env_f("C01_D48", 900.0)))
D_TOTAL_MM = D_KEYS[-1][1]


def D_mm(frame):
    return RS.track(D_KEYS, frame)


def v_mm(frame):
    return D_mm(frame + 1) - D_mm(frame)


def _swing_u(s, power):
    """摆动归一化位移：`1 − (1−s)^p`（前端发力，见文件头第 3 件）。"""
    return 1.0 - (1.0 - max(0.0, min(1.0, s))) ** power


# ---------------------------------------------------------------- 躯干轨道
# 每条轨道 **frame 0 的值由上游接缝（Heavy_01@36）在 main() 里回填**。
PELVIS_RX = ((0, 0.0), (10, -12.0), (15, -16.0), (22, -4.0), (30, 32.0),
             (36, 24.0), (42, 10.0), (TOTAL, 4.0))
PELVIS_RY = ((0, 0.0), (15, 8.0), (30, 0.0), (TOTAL, 0.0))
SPINE01_RX = ((0, 0.0), (10, -10.0), (15, -14.0), (22, -3.0), (30, 28.0),
              (36, 20.0), (42, 8.0), (TOTAL, 2.0))
SPINE01_RY = ((0, 0.0), (15, 5.0), (30, 0.0), (TOTAL, 0.0))
SPINE02_RX = ((0, 0.0), (10, -10.0), (15, -14.0), (22, -3.0), (30, 28.0),
              (36, 20.0), (42, 8.0), (TOTAL, 2.0))
SPINE02_RY = ((0, 0.0), (15, 5.0), (30, 0.0), (TOTAL, 0.0))
CHEST_RX = ((0, 0.0), (10, -11.0), (15, -16.0), (22, -3.0), (30, 32.0),
            (36, 22.0), (42, 9.0), (TOTAL, 1.0))
CHEST_RY = ((0, 0.0), (15, 6.0), (30, 0.0), (TOTAL, 0.0))
# 颈/头**反向**：拱背时收下巴（rx>0），折身时抬头（rx<0）—— 别让头埋进胸口。
NECK_RX = ((0, 0.0), (15, 10.0), (30, -14.0), (42, -7.0), (TOTAL, -6.0))
NECK_RY = ((0, 0.0), (15, -4.0), (30, 0.0), (TOTAL, 0.0))
HEAD_RX = ((0, 0.0), (15, 6.0), (30, -10.0), (42, 1.0), (TOTAL, 5.0))
HEAD_RY = ((0, 0.0), (15, -3.0), (30, 0.0), (TOTAL, 0.0))
# 肩带：举拳时**上抬**（rx → −4），劈下时**下沉**（rx → −28）。
#   rz 两侧镜像：L rz>0 = 向后、R rz>0 = 向前（rig_axis_map 实测）。
SHOULDER_RX = ((0, -18.0), (15, -4.0), (30, -28.0), (40, -22.0), (TOTAL, -18.0))
SHOULDER_L_RZ = ((0, 0.0), (15, 10.0), (30, -22.0), (40, -6.0), (TOTAL, 0.0))
SHOULDER_R_RZ = ((0, 0.0), (15, -10.0), (30, 22.0), (40, 6.0), (TOTAL, 0.0))

# 骨盆位移（世界系）：蓄力**后坐 + 下沉**，劈砸时**再下沉**，收招回到 Idle 的 0.830。
PELVIS_X = ((0, 0.0), (15, 0.006), (30, 0.002), (TOTAL, 0.0))
PELVIS_Z = ((0, 0.8067), (10, 0.7560), (15, 0.7420), (22, 0.7620), (30, 0.7180),
            (36, 0.7620), (42, 0.8240), (TOTAL, 0.8300))
Z_SEAM = PELVIS_Z[0][1]

# ---------------------------------------------------------------- 手臂方向轨道
# 八个相位（世界单位向量）。x = 左正，y = 身后正，z = 上正。
ARM_KEYS = {
    # 前摇：双拳**并举过顶、略偏后**（|拳−骨盆| 要走满，见文件头 0.B）
    "ANTIC": {
        "upperarm.L": (0.26, 0.32, 0.91),
        "forearm.L": (0.20, 0.28, 0.94),
        "hand.L": (0.14, 0.26, 0.96),
        "upperarm.R": (-0.26, 0.32, 0.91),
        "forearm.R": (-0.20, 0.28, 0.94),
        "hand.R": (-0.14, 0.26, 0.96),
    },
    # 命中：双拳劈到**身前下方**（拳背朝前，砸向对手身上）
    "HIT": {
        "upperarm.L": (0.16, -0.66, -0.73),
        "forearm.L": (0.12, -0.78, -0.61),
        "hand.L": (0.08, -0.82, -0.56),
        "upperarm.R": (-0.16, -0.66, -0.73),
        "forearm.R": (-0.12, -0.78, -0.61),
        "hand.R": (-0.08, -0.82, -0.56),
    },
    # 收招：双拳收回护体（≈ Idle 的 ARM_DIRS，末段沿欧拉斜坡逐位收敛）
    "SETTLE": {
        "upperarm.L": (0.28, -0.30, -0.91),
        "forearm.L": (-0.30, -0.36, 0.88),
        "hand.L": (-0.20, -0.68, 0.70),
        "upperarm.R": (-0.24, -0.34, -0.91),
        "forearm.R": (0.32, -0.24, 0.92),
        "hand.R": (0.18, -0.60, 0.78),
    },
}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_PHASES = ((0, "SEAM", _env_p("C01_PH0", "smooth")),
              (ANTIC, "ANTIC", _env_p("C01_PH1", "smooth")),
              (HIT, "HIT", _env_p("C01_PH2", "linear")),
              (HOLD_END, "HIT", "linear"),
              (T_L_ON, "SETTLE", "smooth"), (TOTAL, "END", "smooth"))

# ---------------------------------------------------------------- 命停该冻谁
HITSTOP_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "shoulder.L", "shoulder.R",
                 "upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R")


def _hold(frame):
    return HIT < frame <= HOLD_END


# ---------------------------------------------------------------- 门禁阈值
SOLE_RANGE_MM = (-2.0, 6.0)
PLANT_DRIFT_MAX_MM = 3.0
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
# ---- 「幅度 ≥ 1.5 × 普通攻击」：基准来自 probe_combo01b（B 族全族最大，骨盆系）
BMAX = {"fist_rel_range_mm": 1218.22, "fist_rel_path_mm": 2401.37,
        "swing_step_rel_mm": 95.10, "torso_pitch_range_mm": 501.00}
RATIO = 1.5
FIST_RANGE_MIN_MM = _env_f("C01_FR_MIN", BMAX["fist_rel_range_mm"] * RATIO)
FIST_PATH_MIN_MM = _env_f("C01_FP_MIN", BMAX["fist_rel_path_mm"] * RATIO)
SWING_STEP_MIN_MM = _env_f("C01_SS_MIN", BMAX["swing_step_rel_mm"] * RATIO)
# 躯干前倾极差：1.5×(751.5) 超过脊柱几何上限 754 的 99.7% ⟹ 只作诊断，
# 阈值取 1.2×（= 601.2 mm，落在可行区间）。见文件头第 0 件 A(a)。
TORSO_PITCH_DIAG_MIN_MM = _env_f("C01_TP_MIN", BMAX["torso_pitch_range_mm"] * 1.2)

SEAM_POSE = {}
IDLE_POSE = {}
SEAM_DIRS = {}
PY0 = 0.0
IDLE_PELVIS = None
L_SEAM = None
R_SEAM = None
L_END = None
R_END = None
SEAM_SOLE = {}
Z_PLANT_FLAT = 0.078
Z_PLANT_TIP3 = 0.085
FROZEN_SHIFT = {}
WINDOW_SOLE = {}
WINDOW_Z0 = {}
LEG_TAIL_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
_TAIL_ANCHOR = {}
_LEG_ANCHOR = {}
_KNEE_ANCHOR = {}
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
SEAM_EULER = {}
SEAM_SOURCE = {}


# =============================================================== 脚步与踝目标
def window_of(side, frame):
    for index, (a, b) in enumerate(WINDOWS[side]):
        if a <= frame <= b:
            return index
    return None


def sole_target(frame):
    """该帧每只脚**期望的鞋底离地量**（米）—— 支撑 0，摆动按包络。"""
    out = {}
    if T_L_OFF < frame < T_L_ON:
        s = (frame - T_L_OFF) / float(T_L_ON - T_L_OFF)
        out["L"] = L_LIFT * math.sin(math.pi * s) ** 1.35
    else:
        out["L"] = 0.0
    if T_R_OFF < frame < T_R_ON:
        s = (frame - T_R_OFF) / float(T_R_ON - T_R_OFF)
        out["R"] = R_LIFT * math.sin(math.pi * s) ** 1.35
    else:
        out["R"] = 0.0
    return out


def tip_of(side, frame):
    """足尖角（度，+ = 压脚背 / 脚尖朝下）。接缝两脚都平放 ⟹ 支撑期 0。"""
    if side == "L":
        if frame <= T_L_OFF:
            return 0.0
        if frame < T_L_ON:
            s = (frame - T_L_OFF) / float(T_L_ON - T_L_OFF)
            return 5.0 * math.sin(math.pi * s) ** 0.7
        return TIP3 * max(0.0, 1.0 - (frame - T_L_ON) / float(TIP_RAMP))
    if frame <= T_R_OFF:
        return 0.0
    if frame < T_R_ON:
        s = (frame - T_R_OFF) / float(T_R_ON - T_R_OFF)
        return 5.0 * math.sin(math.pi * s) ** 0.7
    return TIP3 * max(0.0, 1.0 - (frame - T_R_ON) / float(TIP_RAMP))


def plant_z(tip):
    return Z_PLANT_FLAT + (Z_PLANT_TIP3 - Z_PLANT_FLAT) * (tip / TIP3)


def ankle_targets(frame, shift):
    """返回 {"L": (x, y, z, tip), ...}：踝世界目标 + 足尖角。

    ★ 落脚点**按 (side, 窗口序号) 分别取**（B10 的坑：不能用"idx == 0 ⟹ 接缝点"）
      —— L 的窗口 0 是起手支撑期（接缝点），窗口 1 是二次落地（终点）；
      R 的窗口 0 是起手支撑期（接缝点），窗口 1 是落地窗口（终点）。
    """
    out = {}
    for side in SIDES:
        seam = L_SEAM if side == "L" else R_SEAM
        end = L_END if side == "L" else R_END
        idx = window_of(side, frame)
        tip = tip_of(side, frame)
        if idx is not None:
            x, y = (seam.x, seam.y) if idx == 0 else (end.x, end.y)
            z0 = WINDOW_Z0[(side, idx)]
        else:
            if side == "L":
                a, b = seam, end
                u = _swing_u((frame - T_L_OFF) / float(T_L_ON - T_L_OFF),
                             L_SWING_POW)
                z0 = WINDOW_Z0[("L", 1)]
            else:
                a, b = seam, end
                u = _swing_u((frame - T_R_OFF) / float(T_R_ON - T_R_OFF),
                             R_SWING_POW)
                z0 = WINDOW_Z0[("R", 1)]
            x = a.x + (b.x - a.x) * u
            y = a.y + (b.y - a.y) * u
        z = z0 + plant_z(tip) + sole_target(frame)[side] + shift[side]
        out[side] = (x, y, z, tip)
    return out


# =============================================================== 姿态
def torso_pose(frame):
    f = HIT if _hold(frame) else frame
    return {
        "pelvis": (RS.track(PELVIS_RX, f), RS.track(PELVIS_RY, f), 0.0),
        "spine_01": (RS.track(SPINE01_RX, f), RS.track(SPINE01_RY, f), 0.0),
        "spine_02": (RS.track(SPINE02_RX, f), RS.track(SPINE02_RY, f), 0.0),
        "chest": (RS.track(CHEST_RX, f), RS.track(CHEST_RY, f), 0.0),
        "neck": (RS.track(NECK_RX, f), RS.track(NECK_RY, f), 0.0),
        "head": (RS.track(HEAD_RX, f), RS.track(HEAD_RY, f), 0.0),
        "shoulder.L": (RS.track(SHOULDER_RX, f), 0.0,
                       RS.track(SHOULDER_L_RZ, f)),
        "shoulder.R": (RS.track(SHOULDER_RX, f), 0.0,
                       RS.track(SHOULDER_R_RZ, f)),
        "@loc": {"pelvis": A.wloc(RS.track(PELVIS_X, frame),
                                  PY0 - D_mm(frame) / 1000.0,
                                  RS.track(PELVIS_Z, frame) - 0.900)},
    }


def arm_dirs(frame):
    if _hold(frame):
        frame = HIT
    frames = [item[0] for item in ARM_PHASES]
    if frame <= frames[0]:
        return dict(SEAM_DIRS)
    if frame >= frames[-1]:
        return dict(I1.ARM_DIRS)
    for index in range(len(ARM_PHASES) - 1):
        fa, na, mode = ARM_PHASES[index]
        fb, nb, _mode_b = ARM_PHASES[index + 1]
        if not (fa <= frame <= fb):
            continue
        if fa == fb:
            continue
        source = SEAM_DIRS if na == "SEAM" else ARM_KEYS.get(na)
        target = (I1.ARM_DIRS if nb == "END" else ARM_KEYS.get(nb))
        u = (frame - fa) / float(fb - fa)
        t = u if mode == "linear" else RS.smooth(u)
        return {bone: RS.slerp_dir(source[bone], target[bone], t)
                for bone in ARM_BONES}
    return dict(I1.ARM_DIRS)


def build_pose(arm, frame, shift):
    """构造并写入第 frame 帧姿态（一次姿态，不含贴地闭环）。"""
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)

    targets = ankle_targets(frame, shift)
    for side in SIDES:
        x, y, z, _tip = targets[side]
        RS.leg_to(arm, pose, side, (x, y, z))

    # ★ 顺序：收尾段的腿座解**先于**脚部定朝向（B10 的坑：反过来会留下
    #   "用 IK 腿算出来的脚欧拉、去配已经换过的腿"这一对矛盾，接缝差 1.5°）。
    if frame == LEG_TAIL_START:
        _LEG_ANCHOR.update({b: pose[b] for b in LEG_TAIL_BONES})
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
            _KNEE_ANCHOR[side] = (knee - hip).normalized()
    elif frame > LEG_TAIL_START and _LEG_ANCHOR:
        u = (frame - LEG_TAIL_START) / float(TOTAL - LEG_TAIL_START)
        mode = _LEG_EASE
        if mode == "linear":
            s = u
        elif mode == "smooth":
            s = u * u * (3.0 - 2.0 * u)
        elif mode == "cub":
            s = 1.0 - (1.0 - u) ** 3
        else:
            s = 2.0 * u - u * u
        for side in SIDES:
            x, y, z, _tip = targets[side]
            hint = RS.slerp_dir(_KNEE_ANCHOR[side], IDLE_KNEE_DIR[side], s)
            leg_seat(arm, pose, side, (x, y, z), hint)
        if frame >= TOTAL:
            # 末帧：**逐位**取出口接缝 `Idle_01@0`（SEAM_TOL = 1e-6）。
            #   leg_seat 在 s=1 时踝已到位，但踝目标带贴地闭环的 shift
            #   （≈ −0.8 mm）⟹ 世界矩阵还差一点点；末帧必须直接取 Idle 的欧拉。
            #   这不会再造成跳变 —— leg_seat 的滚转基准已经是 `IDLE_BASIS`。
            for bone in LEG_TAIL_BONES:
                e = JS._unwrap_xyz(JS._PREV_EULER.get(bone), IDLE_POSE[bone])
                pose[bone] = e
                arm.pose.bones[bone].rotation_euler = [math.radians(v) for v in e]
            bpy.context.view_layer.update()

    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        WF.add_world_rx(arm, name, targets[side][3])
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    pose.update(A.FIST)
    if frame > HOLD_END and _TAIL_ANCHOR:
        # 收招：**欧拉逐分量插值**（端点逐位 = Idle_01@0 的手臂欧拉）。
        #   `s = 2u − u²` 的逐帧增量单调递减 ⟹ `decel_smooth_ok` 是构造出来的。
        u = (frame - HOLD_END) / float(TOTAL - HOLD_END)
        s = 2.0 * u - u * u
        for bone in ARM_BONES:
            goal = JS._unwrap_xyz(_TAIL_ANCHOR[bone], IDLE_POSE[bone])
            raw = tuple(a + (b - a) * s
                        for a, b in zip(_TAIL_ANCHOR[bone], goal))
            e = JS._unwrap_xyz(JS._PREV_EULER.get(bone), raw)
            pose[bone] = e
            arm.pose.bones[bone].rotation_euler = [math.radians(v) for v in e]
        bpy.context.view_layer.update()
    else:
        dirs = arm_dirs(frame)
        for bone in ARM_BONES:
            pose[bone] = JS.aim_carry(arm, bone, dirs[bone])
        if frame == HOLD_END:
            _TAIL_ANCHOR.update({b: pose[b] for b in ARM_BONES})

    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


def _snapshot_carry():
    return (dict(JS._PREV_EULER), dict(JS.ARM_QUAT), dict(JS.ARM_ROLL),
            dict(JS.ROLL_MAX), JS.MAX_ABS_EULER_Y,
            dict(_TAIL_ANCHOR), dict(_LEG_ANCHOR), dict(_KNEE_ANCHOR))


def _restore_carry(snap):
    JS._PREV_EULER.clear()
    JS._PREV_EULER.update(snap[0])
    JS.ARM_QUAT.clear()
    JS.ARM_QUAT.update(snap[1])
    JS.ARM_ROLL.clear()
    JS.ARM_ROLL.update(snap[2])
    JS.ROLL_MAX.clear()
    JS.ROLL_MAX.update(snap[3])
    JS.MAX_ABS_EULER_Y = snap[4]
    _TAIL_ANCHOR.clear()
    _TAIL_ANCHOR.update(snap[5])
    _LEG_ANCHOR.clear()
    _LEG_ANCHOR.update(snap[6])
    _KNEE_ANCHOR.clear()
    _KNEE_ANCHOR.update(snap[7])


def aim_bone_ref(arm, name, direction, ref_basis, ref_dir):
    """把骨指向 `direction`，**滚转沿用参考姿态**（而不是最小旋转）。

    `A.aim_bone` 用最小旋转定方向，滚转是副产物；`Idle_01@0` 的 thigh/shin
    滚转来自 `A.leg_ik` 的平面解。两者方向一致、滚转不同 ⟹ 世界 3×3 不同
    ⟹ 收尾段最后一帧要"跳"半个滚转角。这里改成把参考姿态用"参考朝向 →
    目标朝向"的最小旋转带过去：**目标朝向等于参考朝向时逐位复现参考姿态**。
    """
    pose_bone = arm.pose.bones[name]
    pose_bone.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()

    quaternion = (Vector(ref_dir).normalized()
                  .rotation_difference(Vector(direction).normalized()))
    target = (quaternion.to_matrix() @ ref_basis).to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def leg_seat(arm, pose, side, target, knee_dir):
    """两骨逆解：踝**精确**落在 `target`，膝按给定的 `knee_dir` 方向鼓出。"""
    thigh_len, shin_len = A.L_THIGH, A.L_SHIN
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    target = Vector(target)
    delta = target - hip
    distance = max(1e-4, min(delta.length, (thigh_len + shin_len) * 0.9995))
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, 0.0, -1.0))
    bulge = Vector(knee_dir) - axis * Vector(knee_dir).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, -1.0, 0.0)) - axis * Vector((0.0, -1.0, 0.0)).dot(axis)
        if bulge.length < 1e-6:
            bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    cos_hip = (thigh_len ** 2 + distance ** 2 - shin_len ** 2) \
        / (2.0 * thigh_len * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    knee = hip + (axis * cos_hip + bulge * sin_hip) * thigh_len
    for name, direction in (("thigh." + side, knee - hip),
                            ("shin." + side, target - knee)):
        pose[name] = aim_bone_ref(arm, name, direction,
                                  IDLE_BASIS[name], IDLE_DIR[name])


def solve_pose(arm, frame, meshes=None):
    """两遍**实测贴地闭环**；支撑期一旦落地，该窗口的 shift **冻结**。

    ★ 每帧只允许**推进一次**手臂接力状态（B10 的坑）：`build_pose` 不是纯函数，
      它改 `JS._PREV_EULER` / `ARM_QUAT`。闭环要重跑它 ⟹ "跑几趟"成了状态的一部分。
      修法：闭环迭代前后各拍一次快照，只用**最终那次**构造去推进状态。
    """
    shift = {}
    locked = set()
    for side in SIDES:
        idx = window_of(side, frame)
        key = (side, idx)
        if idx is not None and key in FROZEN_SHIFT:
            shift[side] = FROZEN_SHIFT[key]
            locked.add(side)
        else:
            shift[side] = 0.0

    snap = _snapshot_carry()
    pose = build_pose(arm, frame, shift)
    if meshes is None:
        return pose
    for _ in range(3):
        want = sole_target(frame)
        low = A.foot_lowest_by_side()
        error = {side: want[side] - low[side][2]
                 for side in SIDES if side not in locked}
        if not error or max(abs(v) for v in error.values()) < 5e-5:
            break
        for side, value in error.items():
            shift[side] += value
        _restore_carry(snap)
        pose = build_pose(arm, frame, shift)

    _restore_carry(snap)
    pose = build_pose(arm, frame, shift)

    for side in SIDES:
        idx = window_of(side, frame)
        key = (side, idx)
        if idx is not None and key not in FROZEN_SHIFT:
            FROZEN_SHIFT[key] = shift[side]
    if meshes is not None:
        low = A.foot_lowest_by_side()
        for side in SIDES:
            idx = window_of(side, frame)
            if idx is not None and low[side] is not None:
                WINDOW_SOLE.setdefault((side, idx), []).append(low[side][2])
    return pose


# =============================================================== 接缝尺子
def _bone_point(mat):
    return (mat[3], mat[7], mat[11])


def pelvis_moving(arm):
    moving = set()
    for bone in arm.pose.bones:
        node = bone
        while node is not None:
            if node.name == "pelvis":
                moving.add(bone.name)
                break
            node = node.parent
    return moving


def pose_seam_split(mats_a, mats_b, moving):
    """两套世界矩阵的「**平移不变**」逐位差（带 Root Motion 的支必须用它）。"""
    ori = 0.0
    rel = 0.0
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


# =============================================================== 逐帧实测
def foot_series(arm, action, meshes):
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    rows = []
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {"frame": frame,
               "pelvis": tuple(A.bone_world(arm, "pelvis", "head")),
               "neck": tuple(A.bone_world(arm, "neck", "head"))}
        low = A.foot_lowest_by_side()
        for side in SIDES:
            row["ankle_" + side] = tuple(A.bone_world(arm, "foot." + side,
                                                      "head"))
            row["sole_" + side] = (None if low[side] is None
                                   else low[side][2])
            row["reach_" + side] = ((Vector(row["ankle_" + side])
                                     - Vector(row["pelvis"])).length)
        for key in ("hand.R", "hand.L"):
            row[key + "_tail"] = tuple(A.bone_world(arm, key, "tail"))
        rows.append(row)

    if previous is not None:
        arm.animation_data.action = previous
    return rows


# =============================================================== 专属门禁
def combo_assertions(arm, action, samples, foots, start_mats, end_mats):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(f["pelvis"]) for f in foots]
    necks = [Vector(f["neck"]) for f in foots]

    # 0) 接缝
    mats0 = RS.action_world_matrices(arm, action, 0)
    mats1 = RS.action_world_matrices(arm, action, TOTAL)
    delta0 = RS.matrix_delta(mats0, start_mats)
    moving = pelvis_moving(arm)
    ori1, rel1, ori_bone, rel_bone = pose_seam_split(mats1, end_mats, moving)
    raw1 = RS.matrix_delta(mats1, end_mats)
    res["seam_start_delta"] = float("%.3e" % delta0)
    res["seam_start_ok"] = delta0 <= SEAM_TOL
    res["seam_end_pose_delta"] = float("%.3e" % max(ori1, rel1))
    res["seam_end_orient_delta"] = float("%.3e" % ori1)
    res["seam_end_relative_delta"] = float("%.3e" % rel1)
    res["seam_end_raw_delta"] = float("%.3e" % raw1)
    res["seam_end_orient_bone"] = ori_bone
    res["seam_end_relative_bone"] = rel_bone
    res["root_motion_m"] = round((pelvis[-1].y - pelvis[0].y), 6)
    res["seam_end_ok"] = max(ori1, rel1) <= SEAM_TOL
    res["root_motion_ok"] = abs(abs(res["root_motion_m"]) * 1000.0
                                - D_TOTAL_MM) <= 1.0
    res["advance_total_mm"] = round((pelvis[-1].y - pelvis[0].y) * 1000.0, 3)

    # 1) 支撑脚：世界漂移 + 鞋底区间
    plant = {}
    sole = {}
    for side in SIDES:
        for idx, (a, b) in enumerate(WINDOWS[side]):
            lo, hi = max(a, 0), b
            pts = [foots[f] for f in range(lo, hi + 1)]
            xs = [p["ankle_" + side][0] for p in pts]
            ys = [p["ankle_" + side][1] for p in pts]
            drift = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) * 1000.0
            zs = [p["sole_" + side] for p in pts if p["sole_" + side] is not None]
            plant["%s_w%d_mm" % (side, idx)] = round(drift, 4)
            sole["%s_w%d" % (side, idx)] = [round(min(zs) * 1000.0, 3),
                                            round(max(zs) * 1000.0, 3)]
    res["plant_drift_mm"] = plant
    res["stance_plant_ok"] = all(v <= PLANT_DRIFT_MAX_MM
                                 for v in plant.values())
    res["plant_sole_mm"] = sole
    res["stance_sole_ok"] = all(SOLE_RANGE_MM[0] <= v[0]
                                and v[1] <= SOLE_RANGE_MM[1]
                                for v in sole.values())
    # 全程至少一只脚在支撑（本支**不做腾空**，见文件头第 2 件）
    unsupported = [f for f in range(0, TOTAL + 1)
                   if window_of("L", f) is None and window_of("R", f) is None]
    res["unsupported_frames"] = unsupported
    res["always_supported_ok"] = not unsupported

    # 2) 摆动脚真的离地
    clear = {}
    for side in SIDES:
        if side == "L":
            span, lo, hi = range(T_L_OFF + 1, T_L_ON), T_L_OFF, T_L_ON
        else:
            span, lo, hi = range(T_R_OFF + 1, T_R_ON), T_R_OFF, T_R_ON
        vals = [foots[f]["sole_" + side] for f in span
                if foots[f]["sole_" + side] is not None]
        clear[side] = round(min(vals) * 1000.0, 3) if vals else None
    res["swing_min_clearance_mm"] = clear
    res["swing_airborne_ok"] = all(v is not None and v > 0.0
                                   for v in clear.values())

    # 3) 顿感：命停窗口**打击姿态**逐位冻结，而骨盆照常前冲
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
            frozen.append(round(step, 4))
    res["hitstop_frozen_steps"] = frozen
    res["hitstop_present_ok"] = bool(frozen) and max(frozen) <= 1e-6
    res["hitstop_momentum_mm"] = round(
        (pelvis[HIT].y - pelvis[HOLD_END].y) * 1000.0, 3)
    res["hitstop_keeps_momentum_ok"] = res["hitstop_momentum_mm"] > 10.0

    # 4) ★ 幅度三连（本支核心："≥ 1.5 × 普通攻击"）
    #    全部在**骨盆系**里量（把 Root Motion 减掉）—— 见文件头第 0 件。
    fists = {"L": [Vector(f["hand.L_tail"]) for f in foots],
             "R": [Vector(f["hand.R_tail"]) for f in foots]}
    rel = {s: [v - p for v, p in zip(fists[s], pelvis)] for s in SIDES}

    def span(series):
        best = 0.0
        for i in range(len(series)):
            for j in range(i + 1, len(series)):
                best = max(best, (series[i] - series[j]).length)
        return best * 1000.0

    def path(series):
        return sum((series[i + 1] - series[i]).length
                   for i in range(len(series) - 1)) * 1000.0

    ranges = {s: round(span(rel[s]), 2) for s in SIDES}
    paths = {s: round(path(rel[s]), 2) for s in SIDES}
    res["fist_rel_range_by_side_mm"] = ranges
    res["fist_rel_path_by_side_mm"] = paths
    res["fist_rel_range_mm"] = max(ranges.values())
    res["fist_rel_path_mm"] = max(paths.values())
    res["amplitude_baseline"] = dict(BMAX)
    res["amplitude_ratio"] = {
        "fist_rel_range": round(max(ranges.values()) / BMAX["fist_rel_range_mm"], 3),
        "fist_rel_path": round(max(paths.values()) / BMAX["fist_rel_path_mm"], 3),
    }
    res["fist_rel_range_ok"] = res["fist_rel_range_mm"] >= FIST_RANGE_MIN_MM
    res["fist_rel_path_ok"] = res["fist_rel_path_mm"] >= FIST_PATH_MIN_MM

    # 摆动脚**单帧相对位移**（步幅速率）
    steps = {}
    frames_at = {}
    for side in SIDES:
        if side == "L":
            spanf = range(T_L_OFF, T_L_ON + 1)
        else:
            spanf = range(T_R_OFF, T_R_ON + 1)
        arr = [Vector(foots[f]["ankle_" + side]) - pelvis[f] for f in spanf]
        best, best_f = 0.0, None
        for i in range(1, len(arr)):
            step = (arr[i] - arr[i - 1]).length * 1000.0
            if step > best:
                best, best_f = step, spanf[i]
        steps[side] = round(best, 2)
        frames_at[side] = best_f
    res["swing_step_rel_by_side_mm"] = steps
    res["swing_step_rel_peak_frame"] = frames_at
    res["swing_step_rel_mm"] = max(steps.values())
    res["swing_step_rel_ratio"] = round(
        res["swing_step_rel_mm"] / BMAX["swing_step_rel_mm"], 3)
    res["swing_step_rel_ok"] = res["swing_step_rel_mm"] >= SWING_STEP_MIN_MM

    # 躯干前倾极差（**只作诊断**，见文件头 0.A(a)）
    pitch = [(p.y - n.y) * 1000.0 for p, n in zip(pelvis, necks)]
    res["torso_pitch_range_mm"] = round(max(pitch) - min(pitch), 2)
    res["torso_pitch_peak_mm"] = round(max(pitch), 2)
    res["torso_pitch_min_mm"] = round(min(pitch), 2)
    res["torso_pitch_diag_ok"] = res["torso_pitch_range_mm"] >= \
        TORSO_PITCH_DIAG_MIN_MM
    res["combo_amplitude_ok"] = bool(
        res["fist_rel_range_ok"] and res["fist_rel_path_ok"]
        and res["swing_step_rel_ok"])

    # 5) 力矩链（脚→腿→髋→腰→肩→手 逐级都要有非零关键帧）
    keys = ("pelvis", "spine_01", "spine_02", "chest", "shoulder.L",
            "shoulder.R", "thigh.L", "shin.L", "thigh.R", "shin.R")
    channel = {}
    for name in keys:
        vals = [s["euler"].get(name, (0.0, 0.0, 0.0)) for s in samples]
        channel[name] = round(max(max(abs(v) for v in item) for item in vals), 3)
    res["power_chain_channels_deg"] = channel
    res["power_chain_ok"] = all(v > 0.5 for v in channel.values())

    # 6) 腿可达
    limit = A.L_THIGH + A.L_SHIN
    ratios = {}
    peak_frames = {}
    for side in SIDES:
        vals = [(f["reach_" + side], f["frame"]) for f in foots]
        peak, peak_f = max(vals)
        ratios[side] = round(peak / limit, 5)
        peak_frames[side] = [peak_f, round(peak * 1000.0, 2)]
    res["leg_reach_max_ratio"] = ratios
    res["leg_reach_peak"] = peak_frames
    res["ik_reach_ok"] = all(v <= REACH_MAX_RATIO for v in ratios.values())

    # 7) 收招不许瞬停
    tails = []
    tail_bones = []
    for index in range(1, len(samples)):
        frame = samples[index]["frame"]
        if frame >= RETURN_START:
            ea = samples[index - 1]["euler"]
            eb = samples[index]["euler"]
            step = 0.0
            owner = None
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
    res["return_tail_zero_frames"] = sum(1 for t in tails if t <= 1e-9)

    # 8) 帧预算（重攻击前摇 12~20、命停 2~4）—— 清单 §0.1
    res["antic_frames"] = ANTIC
    res["antic_frames_ok"] = 12 <= ANTIC <= 20
    res["hitstop_frames"] = HOLD
    res["hitstop_frames_ok"] = 2 <= HOLD <= 4
    return res


# =============================================================== 主流程
def main():
    global SEAM_POSE, IDLE_POSE, SEAM_DIRS, PY0, IDLE_PELVIS
    global L_SEAM, R_SEAM, L_END, R_END, SEAM_SOLE, SEAM_EULER, SEAM_SOURCE
    global Z_PLANT_FLAT, Z_PLANT_TIP3, PELVIS_RX, PELVIS_RY, SPINE01_RX
    global SPINE01_RY, SPINE02_RX, SPINE02_RY, CHEST_RX, CHEST_RY
    global NECK_RX, NECK_RY, HEAD_RX, HEAD_RY
    global SHOULDER_RX, SHOULDER_L_RZ, SHOULDER_R_RZ
    # ★ `torso_pose()` 读的是**模块级**轨道 ⟹ 这里的回填必须走 global，
    #   否则 main 里的赋值只是局部变量，torso_pose 仍用未回填的版本。
    global PELVIS_X, PELVIS_Z, Z_SEAM

    FROZEN_SHIFT.clear()
    WINDOW_SOLE.clear()
    WINDOW_Z0.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    for module, label in ((I1, "Idle_01"), (H, "Heavy_01")):
        if module.NAME not in bpy.data.actions:
            print("C01_BOOTSTRAP 动画工程缺 %s，先补跑" % label)
            module.main()
            arm, meshes = A.open_animation_project()
            A.setup_scene()

    A.PROBE_BONES = tuple(A.PROBE_BONES) + ("thigh.L", "thigh.R",
                                            "shin.L", "shin.R")

    # ---- 上游接缝：`Heavy_01@36`（可取消帧）—— **直接读 Action**，不重跑姿态构造器
    #      （Heavy_01 的 build_pose 有状态：pole 接力 / _BULGE_PREV，
    #       单独调它复现不出帧值；读 Action 才是权威。）
    scene = bpy.context.scene
    heavy = bpy.data.actions[H.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = heavy
    A._bind_slot(arm, heavy)
    scene.frame_set(H.CANCEL)
    bpy.context.view_layer.update()
    SEAM_SOURCE["action"] = H.NAME
    SEAM_SOURCE["frame"] = H.CANCEL
    SEAM_EULER = {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
                  for b in arm.pose.bones}
    SEAM_POSE = {name: value for name, value in SEAM_EULER.items()}
    SEAM_POSE["@loc"] = {"pelvis": tuple(arm.pose.bones["pelvis"].location)}
    SEAM_POSE.update(A.FIST)
    PY0 = A.bone_world(arm, "pelvis", "head").y
    L_SEAM = A.bone_world(arm, "foot.L", "head").copy()
    R_SEAM = A.bone_world(arm, "foot.R", "head").copy()
    SEAM_DIRS = {bone: tuple(A.bone_direction(arm, bone)) for bone in ARM_BONES}
    SEAM_SOLE = {s: A.foot_lowest_by_side()[s][2] for s in SIDES}
    seam_extra = sorted(
        name for name, value in SEAM_EULER.items()
        if max(abs(v) for v in value) > 1e-9
        and name not in set(SEAM_POSE) | set(A.FIST) | {"pelvis"})

    # ---- 下游接缝：`Idle_01@0`
    SEAM_POSE = {name: value for name, value in SEAM_EULER.items()}
    SEAM_POSE["@loc"] = {"pelvis": tuple(arm.pose.bones["pelvis"].location)}
    SEAM_POSE.update(A.FIST)
    arm.animation_data.action = bpy.data.actions[I1.NAME]
    A._bind_slot(arm, bpy.data.actions[I1.NAME])
    scene.frame_set(0)
    bpy.context.view_layer.update()
    IDLE_POSE = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, IDLE_POSE)
    bpy.context.view_layer.update()
    IDLE_PELVIS = A.bone_world(arm, "pelvis", "head").copy()
    idle_l = A.bone_world(arm, "foot.L", "head").copy()
    idle_r = A.bone_world(arm, "foot.R", "head").copy()
    IDLE_KNEE_DIR.clear()
    IDLE_BASIS.clear()
    IDLE_DIR.clear()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        IDLE_KNEE_DIR[side] = (knee - hip).normalized()
        for name in ("thigh." + side, "shin." + side):
            IDLE_BASIS[name] = arm.pose.bones[name].matrix.to_3x3().copy()
            IDLE_DIR[name] = A.bone_direction(arm, name)

    # ---- 躯干轨道：**frame 0 回填上游接缝的真值**（否则 Hermite 的首段切线是错的）
    def patch(track, bone, channel=None):
        value = SEAM_EULER[bone]
        if channel is not None:
            value = value[channel]
        else:
            value = value[0]
        return ((0, value),) + tuple(k for k in track if k[0] != 0)

    PELVIS_RX = patch(PELVIS_RX, "pelvis", 0)
    PELVIS_RY = patch(PELVIS_RY, "pelvis", 1)
    SPINE01_RX = patch(SPINE01_RX, "spine_01", 0)
    SPINE01_RY = patch(SPINE01_RY, "spine_01", 1)
    SPINE02_RX = patch(SPINE02_RX, "spine_02", 0)
    SPINE02_RY = patch(SPINE02_RY, "spine_02", 1)
    CHEST_RX = patch(CHEST_RX, "chest", 0)
    CHEST_RY = patch(CHEST_RY, "chest", 1)
    NECK_RX = patch(NECK_RX, "neck", 0)
    NECK_RY = patch(NECK_RY, "neck", 1)
    HEAD_RX = patch(HEAD_RX, "head", 0)
    HEAD_RY = patch(HEAD_RY, "head", 1)
    SHOULDER_RX = patch(SHOULDER_RX, "shoulder.L", 0)
    SHOULDER_L_RZ = patch(SHOULDER_L_RZ, "shoulder.L", 2)
    SHOULDER_R_RZ = patch(SHOULDER_R_RZ, "shoulder.R", 2)
    PELVIS_XE = SEAM_POSE["@loc"]["pelvis"][0]
    PELVIS_ZE = SEAM_POSE["@loc"]["pelvis"][1]
    Z_SEAM = PELVIS_ZE + 0.900
    PELVIS_X = ((0, PELVIS_XE),) + tuple(k for k in PELVIS_X if k[0] != 0)
    PELVIS_Z = ((0, Z_SEAM),) + tuple(k for k in PELVIS_Z if k[0] != 0)

    # ★ 落脚点由**终点反推**（Root Motion 让整具身体前移 D_TOTAL）
    shift_y = (PY0 - D_TOTAL_MM / 1000.0) - IDLE_PELVIS.y
    L_END = Vector((idle_l.x, idle_l.y + shift_y, idle_l.z))
    R_END = Vector((idle_r.x, idle_r.y + shift_y, idle_r.z))

    A.report("C01_LAYOUT", {
        "total_frames": TOTAL,
        "antic": ANTIC, "hit": HIT, "hold": HOLD, "cancel": CANCEL,
        "advance_mm": round(D_TOTAL_MM, 3),
        "foot_schedule": {"L": [[a, b] for a, b in WINDOWS["L"]],
                          "R": [[a, b] for a, b in WINDOWS["R"]]},
        "seam_source": [H.NAME, H.CANCEL],
        "pelvis_y0_mm": round(PY0 * 1000.0, 3),
        "L_seam_mm": [round(v * 1000.0, 2) for v in L_SEAM],
        "R_seam_mm": [round(v * 1000.0, 2) for v in R_SEAM],
        "L_end_mm": [round(v * 1000.0, 2) for v in L_END],
        "R_end_mm": [round(v * 1000.0, 2) for v in R_END],
        "L_step_mm": round((L_SEAM.y - L_END.y) * 1000.0, 2),
        "R_step_mm": round((R_SEAM.y - R_END.y) * 1000.0, 2),
        "seam_sole_mm": {s: round(v * 1000.0, 3) for s, v in SEAM_SOLE.items()},
        "seam_extra_bones": seam_extra,
        "note": ("上游接缝 = Heavy_01 的 CANCEL 帧（§0.3：从这一帧起可接连招）；"
                 "落脚点由出口接缝反推；两脚都换，全程至少一只脚支撑。"),
    })

    # ---- 贴地标定（tip=0 与 tip=3 两点）
    Z_PLANT_TIP3, err3 = RS.measure_plant_z(
        arm, TIP3, torso_pose(0), (L_SEAM.x, L_SEAM.y), L_SEAM.z)
    Z_PLANT_FLAT, err0 = RS.measure_plant_z(
        arm, 0.0, torso_pose(TOTAL), (L_END.x, L_END.y), 0.140)
    A.report("C01_CALIBRATION", {
        "plant_z_flat_mm": round(Z_PLANT_FLAT * 1000.0, 3),
        "plant_z_tip3_mm": round(Z_PLANT_TIP3 * 1000.0, 3),
        "tip3_reach_err_mm": err3,
        "flat_reach_err_mm": err0,
    })

    # ---- 每个支撑窗口的"鞋底贴地"基准踝高 Z0
    WINDOW_Z0[("L", 0)] = L_SEAM.z - plant_z(tip_of("L", 0))
    WINDOW_Z0[("L", 1)] = L_END.z - plant_z(0.0)
    WINDOW_Z0[("R", 0)] = R_SEAM.z - plant_z(tip_of("R", 0))
    WINDOW_Z0[("R", 1)] = R_END.z - plant_z(0.0)
    A.report("C01_Z0", {("%s_w%d" % k): round(v * 1000.0, 4)
                        for k, v in WINDOW_Z0.items()})

    def reset_carry():
        JS._PREV_EULER.clear()
        JS.ARM_QUAT.clear()
        JS.ARM_ROLL.clear()
        JS.ROLL_MAX.clear()
        _TAIL_ANCHOR.clear()
        _LEG_ANCHOR.clear()
        _KNEE_ANCHOR.clear()
        A.apply_pose(arm, SEAM_POSE)
        bpy.context.view_layer.update()
        for name, value in SEAM_POSE.items():
            if not name.startswith("@"):
                JS._PREV_EULER[name] = tuple(value)
        for name in ARM_BONES + ("thigh.L", "shin.L", "foot.L",
                                 "thigh.R", "shin.R", "foot.R"):
            JS.ARM_QUAT[name] = arm.pose.bones[name].matrix.to_quaternion()
        JS.MAX_ABS_EULER_Y = 0.0
        JS.ROLL_RANGE = 150.0
        JS.Y_SAFE = 62.0

    def build_keyframes():
        out = [(0, SEAM_POSE)]
        for frame in range(1, TOTAL + 1):
            out.append((frame, solve_pose(arm, frame, meshes)))
        return out

    # ---- 第 1 趟：量出每个支撑窗口里鞋底最低点，再把冻结 shift 整体抬高
    WINDOW_SOLE.clear()
    FROZEN_SHIFT.clear()
    reset_carry()
    build_keyframes()
    adjust = {}
    for key in sorted(WINDOW_SOLE):
        vals = WINDOW_SOLE[key]
        if not vals:
            continue
        delta = SOLE_FLOOR_MM / 1000.0 - min(vals)
        FROZEN_SHIFT[key] = FROZEN_SHIFT.get(key, 0.0) + delta
        adjust["%s_w%d" % key] = [round(min(vals) * 1000.0, 3),
                                 round(delta * 1000.0, 3)]
    A.report("C01_SOLE_CALIB", {
        "window_floor_before_and_lift_mm": adjust,
        "frozen_shift_mm": {("%s_w%d" % k): round(v * 1000.0, 4)
                            for k, v in FROZEN_SHIFT.items()},
        "target_floor_mm": SOLE_FLOOR_MM,
    })

    # ---- 第 2 趟：用校正后的冻结 shift 正式打帧
    WINDOW_SOLE.clear()
    reset_carry()
    keyframes = build_keyframes()

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "连招与特殊技",
        "note": ("连招终结：接 Heavy_01 可取消帧，跨步双拳过顶劈砸，"
                 "Root Motion 前冲 0.900 m；幅度 ≥ 普通攻击 1.5 倍（骨盆系口径）"),
        "antic_frame": ANTIC,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HOLD,
        "root_motion_m": [0.0, round(-D_TOTAL_MM / 1000.0, 4)],
        "amplitude_baseline": dict(BMAX),
        "hit_point_m": None,
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "ANTIC": ANTIC, "BURST": BURST, "HIT": HIT,
        "HITSTOP_END": HOLD_END, "RECOV": RETURN_START, "CANCEL": CANCEL,
        "R_OFF": T_R_OFF, "R_ON": T_R_ON, "L_OFF": T_L_OFF, "L_ON": T_L_ON,
        "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    if os.environ.get("C01_ARMTRACE") == "1":
        prev_q = {}
        for s in samples:
            row = {"f": s["frame"]}
            for name in ARM_BONES:
                q = arm.pose.bones[name].matrix.to_quaternion()
                step = None
                if name in prev_q:
                    step = round(math.degrees(
                        prev_q[name].rotation_difference(q).angle), 2)
                prev_q[name] = q
                row[name] = [round(v, 2) for v in
                             s["euler"].get(name, (0.0, 0.0, 0.0))] + [step]
            print("C01_ARMTRACE " + json.dumps(row))
    if os.environ.get("C01_LEGTRACE") == "1":
        _prev = {}
        for s in samples:
            row = {"f": s["frame"]}
            for name in ("thigh.L", "thigh.R", "shin.L", "shin.R",
                         "foot.L", "foot.R"):
                e = tuple(round(v, 2) for v in
                          s["euler"].get(name, (0.0, 0.0, 0.0)))
                d = [None, None, None]
                if name in _prev:
                    d = [round(a - b, 2) for a, b in zip(e, _prev[name])]
                _prev[name] = e
                row[name] = list(e) + [d]
            row["L_ank"] = [round(v * 1000.0, 1)
                            for v in s.get("foot.L", (0, 0, 0))]
            row["R_ank"] = [round(v * 1000.0, 1)
                            for v in s.get("foot.R", (0, 0, 0))]
            row["pel"] = [round(v * 1000.0, 1) for v in s.get("pelvis", (0, 0, 0))]
            print("C01_LEGTRACE " + json.dumps(row))
    if os.environ.get("C01_TRACE") == "1":
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for f in foot_series(arm, action, meshes):
            print("C01_TRACE " + json.dumps({
                "f": f["frame"],
                "pelvis_y": round(f["pelvis"][1] * 1000.0, 2),
                "pelvis_z": round(f["pelvis"][2] * 1000.0, 2),
                "L_ank": [round(v * 1000.0, 2) for v in f["ankle_L"]],
                "R_ank": [round(v * 1000.0, 2) for v in f["ankle_R"]],
                "L_sole": (None if f["sole_L"] is None
                           else round(f["sole_L"] * 1000.0, 3)),
                "R_sole": (None if f["sole_R"] is None
                           else round(f["sole_R"] * 1000.0, 3)),
                "L_reach": round(f["reach_L"] * 1000.0, 2),
                "R_reach": round(f["reach_R"] * 1000.0, 2),
                "over": round(max(f["reach_L"], f["reach_R"]) * 1000.0
                              - limit_mm, 2),
            }))

    report = A.run_common_assertions(samples, meta, foot_probe=())
    foots = foot_series(arm, action, meshes)
    start_mats = RS.action_world_matrices(arm, bpy.data.actions[H.NAME],
                                          H.CANCEL)
    end_mats = RS.action_world_matrices(arm, bpy.data.actions[I1.NAME], 0)
    report.update(combo_assertions(arm, action, samples, foots,
                                   start_mats, end_mats))
    report["max_abs_euler_y_deg"] = round(JS.MAX_ABS_EULER_Y, 2)
    report["arm_roll_max_deg"] = {k: round(v, 1)
                                  for k, v in JS.ROLL_MAX.items()}
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    # ★ `no_teleport` 的键名**不以 `_ok` 结尾**，永远不进 `failed` ——
    #   B10 留下的教训 12：每支收尾必须**单独 grep 一次非 `_ok` 的布尔项**。
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C01_REPORT", report)

    if not SKIP_RENDER:
        # 取景跟着 Root Motion 平移（末帧比首帧前冲 900 mm）。
        sheets = [(A.VIEW_SIDE, -0.45, 2.80), (A.VIEW_FRONT, -0.45, 2.80),
                  (A.VIEW_3Q, -0.45, 2.80)]
        for base, shift_y, scale in sheets:
            name, location, target, _scale, res = base
            view = (name, (location[0], location[1] + shift_y, location[2]),
                    (target[0], target[1] + shift_y, target[2]), scale, res)
            frames = ([0, ANTIC, HIT, HOLD_END, TOTAL]
                      if name == "side" else [0, ANTIC, HIT, TOTAL])
            A.render_pose_sheet(arm, action, frames, "combo01", views=(view,))
    A.save_project()
    A.export_glb(arm)
    print("C01_DONE failed=%s" % report["failed"])
    print("C01_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C01_FAILURE " + traceback.format_exc())
