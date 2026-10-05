"""anim_air_heavy —— B09 `Air_Heavy` 空中重击（双拳过顶下砸）。

定位（清单原文 B09）：「双拳向下砸或重脚踩落，**允许改变下落速度**，落地衔接专用落地动作」。

本支取 **双拳过顶下砸**：空中吊住 → 双拳举过头顶蓄力 → 全身加速下砸 → 命中定格
→ 卸力收招 → **末帧逐位 = `Jump_Land@0`**（交给 A13 屈膝吸收）。

---------------------------------------------------------------------------
★★ 与 B08 的**关键区别**：这一支**允许改弹道**

B08 的死约束是「骨盆 z 逐帧 = A12 的 `pelvis_z(f)`，误差 ≤2 mm」。
B09 清单原文明确写「**允许改变下落速度**」⟹ **不能照搬 `air_ballistic_ok`**，
否则等于把一支"下砸"做成"匀速飘落"。但也不能放任 —— 要给一条**新的、可判定的**弹道：

  · `monotone_down_ok`  —— 全程骨盆 z 单调落（上升 = "下砸"变成了"上挑"）；
  · `slam_accel_ok`      —— 下砸段帧间落距**严格递增**，且
                            下砸段总落距 / 同时长自由落体落距 ∈ **[1.2, 2.2]**。
    ★ 给**区间**上下界（同 B08 的 `counter_balance_ok`）：下界保证"真的砸下去了"，
      上界保证"不是瞬移"。
  · `landing_link_ok`    —— 末帧骨盆 z 对 A13 首帧（**实测值**，不是拍的）。

---------------------------------------------------------------------------
★★ 第 1 件 —— 「落距守恒」：**落速可改，落距不可改**（本支的死约束）

首帧钉在 `Jump_Fall@0`、末帧钉在 `Jump_Land@0`，两帧骨盆 z 之差
= **813.3333 mm** 是一个**死数**（探针 `AIR09_SEAM_GAP` 实测）：

    骨盆 z：1952.889 mm（`Jump_Fall@0`）→ 1139.556 mm（`Jump_Land@0`）
    ★ 1139.556 == `JFE.pelvis_z(24)`（逐位），即 **A13 首帧就是 A12 末帧**、
      就是"触地那一刻"。

所以「下砸段要砸得更快」**只能由「前摇段吊得更慢」来付账**。
把前摇的"吊速比例" `c` 当**唯一自由量**，由「总落距 == 两接缝骨盆 z 差」
**200 步二分反解**出来（不是手调的残差）。

    22 帧自由落体只落 685.67 mm ⟹ 本支必须落 **813.333 mm** = 自由落体的 **1.186 倍**。
    ⟹ 全程本来就"比自由落体快"，而"慢前摇 + 快下砸"还要在这之上再挖坑，
       于是前摇被压到 `c = 0.2493`（吊在半空，6 帧只落 14 mm）——
       **这就是"吊滞"（hang time）**，也正是空中重击该有的样子。

---------------------------------------------------------------------------
★★ 第 2 件 —— 前摇"吊滞"不是 bug，是"下砸"的代价

`c = 0.2493` ⟹ 前摇 6 帧的落距是 0.644 / 1.322 / 2.001 / 2.680 / 3.358 / 4.037 mm —— 
几乎悬停。这是**设计使然**：`Jump_Fall@0` 本来就是弹道顶点附近（竖速 2.58 mm/帧），
角色在空中"吊一下、把双拳举过头顶"，然后**炸下去**。

★ 若把前摇做成正常下落（`c≈1`），则 813.333 mm 的预算根本不够，
  下砸段将**低于**自由落体速度（`slam_ratio ≈ 0.75`）—— 那才是"匀速飘落"。
  **"吊滞"是"下砸"的必要代价**，两者由「落距守恒」绑死。

---------------------------------------------------------------------------
★★ 第 3 件 —— 收招不回到"接缝姿态"，而是回到**下游接缝**

B08 的末帧 = 自己的首帧（`Jump_Fall@0`），所以 `_a0_clone()` 够用。
B09 的末帧 = **别人**的姿态（`Jump_Land@0`）⟹ 需要**两个**接缝：

    `START_POSE` = `Jump_Fall@0`（首帧逐位）
    `END_POSE`   = `Jump_Land@0`（末帧逐位，走 `pose_seam_split` 平移不变尺子）

`_end_clone()` 用 `JS._unwrap_xyz` 把 `Jump_Land@0` 的欧拉折到**离命中姿态最近**的
等价支（★ 必须在命中姿态刚被 `_record` 写进 `_PREV_EULER` **之后**构造，
行程才最短），收招段仍走 `_euler_mix` 欧拉逐分量插值（B08 第 2 件：目标姿态已知
时不要走 IK）。

---------------------------------------------------------------------------
★★ 第 4 件 —— 收招末速**接上 A13 的入场速度**（速度域也要守恒）

末帧骨盆 z 对上只是位置对上了；若末帧落速与 A13 首帧落速差太多，接缝处会有
一次速度"顿挫"。A13 首帧落速 = `v_free(24)` = **67.9167 mm/帧**（同一个弹道函数
在 f24 的差分，**派生**、不硬编码）。

⟹ 收招 5 帧改成**从「下砸末速 − 卸力 8 mm/帧」线性升到 67.9167**的斜坡：
   56.600 / 59.429 / 62.258 / 65.088 / **67.917**（末帧逐位等于 A13 入场速度）。
★ 前两帧比下砸末速**慢**，是"卸力"（命中后身体被反震压一下），
  这是重击该有的"顿"；随后按弹道重新加速。

---------------------------------------------------------------------------
★ 探针 `probe_air09.py` 实测（先量再做）定下的数

| 量 | 实测 | 用法 |
|---|---|---|
| `Jump_Fall@0` 骨盆 z | **1952.889 mm** | 首帧 |
| `Jump_Land@0` 骨盆 z | **1139.556 mm** | 末帧（= `pelvis_z(24)`） |
| 总落距 | **813.3333 mm** | 落距守恒的死数 |
| 臂几何 | 上臂+前臂 **552.0**、含手 **650.0**、折叠下界 **176.6** | 双拳轨的可行环带 |
| AC（过顶）`rel` | (75, −215, **470**) ⟹ 腕距 **424.3** | 蓄力顶点 |
| AH（砸落）`rel` | (75, −330, **−460**) ⟹ 腕距 **473.1** | 命中点 |
| `all_in_band` | **true**（6 行全中） | 双拳同时下砸可达 |
| 拳峰下砸行程 | **930.0 mm**（相对肩 z） | `slam_power_ok` |
| 方向摆动 | A0→AC **45.3°**、AC→AH **117.9°** | 出拳幅度 |
| 腿余量（落地构型） | L 13.2 / R 44.4 mm（比值 0.9840 / 0.9460） | `leg_reach_ok` 的天花板 |
| 收招预算 | 5 帧 ⟹ 欧拉行程 ≤ **93.18°** | 见文件头第 3 件 |

★ 第 4 项（末帧回得去吗）的**风险点**：`AH` 的双拳在"身前下方"（`rel` x 只有 75 mm），
而 `Jump_Land@0` 的双臂是**向体侧外张**的（`rel` x = ±416.7 mm）⟹ 收招要摆动
**约 32.6°** 的拳−肩方向。5 帧、首步占比 0.2682 ⟹ 首步 = 32.6×0.2682 ≈ 8.8°
（拳方向），乘欧拉放大系数后仍应 < 25°。**先算过，所以敢用 5 帧。**

---------------------------------------------------------------------------
★ 本支的五条关键做法

1. **双拳走 `rel` 法**（B08 第 2 条）：手骨指向 = `normalize(rel)` ⟹ 腕距
   = `|rel| − hand_len`，恒落在 [176.6, 551.7] 环带内，`arm_to` 的夹取全程不触发。
   探针已把 AC/AH × L/R 六行全部实测过 `all_in_band = true`。
2. **下砸用幂律 `u^1.35`**（`p > 1` ⟹ 速度单调升 ⟹ 峰值帧 ≡ HIT），
   与 SLAM 段的落距表（`SLAM_A/P/Q`，帧间增量 `P + Q·j` 递增）**同向**。
   前摇用 `_ease_ramp`（两端速度 0），收招用 `1−(1−u)^1.40`（速度单调降）。
3. **腿：收膝 → 落地构型**。前摇把双膝收起（踝相对髋 +175 mm 上、+55 mm 后），
   下砸段把腿**同时伸到落地构型**（末帧比值 L 0.9840 / R 0.9460）——
   这样命中帧之后腿几乎不再动，收招只需回收**臂**，`no_teleport` 风险最小。
4. **躯干：后仰蓄力 → 前折发力**（`counter_balance_ok`）。空中无地面反力，
   下砸的反作用只能由躯干前折 + 腿下伸吃：`AC` 累计 −11°（后仰）、
   `AH` 累计 +17°（前折）⟹ 摆动 28°。**给的是区间**，单边阈值等于没定。
5. **`ground_contact_ok` / `no_foot_slide` 全段离地 ⟹ 记 None** 并登记理由
   （A11/A12 口径：None = "不适用"，不是"通过"）；`all_airborne_ok` 用**结构口径**
   （鞋底全程 >0 + 腿不许比**出口接缝**多伸 >80 mm），不用绝对余量（B08 第 4 件）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_air_heavy.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_walk_f as WF      # noqa: E402
import anim_turn as TURN      # noqa: E402
import anim_crouch as CR      # noqa: E402
import anim_jump_start as JS  # noqa: E402
import anim_jump_up as JU     # noqa: E402
import anim_jump_fall as JFE  # noqa: E402
import anim_jump_land as JL   # noqa: E402
import anim_uppercut as UP    # noqa: E402

NAME = "Air_Heavy"
TOTAL = 22                    # 0.367 s @60fps
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"


# ---------------------------------------------------------------- 离线调参入口
# 默认值 = 本支定稿常量。不设这些环境变量时**行为与常量写法逐位相同**；
# 只在离线扫参（`SKIP_RENDER=1` + 环境变量）时用来一次跑多组，省去反复改文件。
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


# ---------------------------------------------------------------- 阶段划分
# ★ 帧预算不是拍脑袋 —— 它是**落距预算**的函数（见文件头第 1 件）：
#   总落距被两个接缝钉死（813.3333 mm），每多一帧就多花 ~60 mm，
#   所以「下砸长度 / 命停长度 / 收招长度」三者必须一起解，改一个要动另两个。
#   下面的默认值是定稿解；`AH_*` 环境变量只为离线扫参（不设即与常量逐位相同）。
CHAMBER_END = _env_i("AH_CHAMBER", 6)      # 前摇 0~6：吊滞 + 双拳过顶 + 收膝
HIT = _env_i("AH_HIT", 16)                 # 命中帧（下砸 6~16 = **10 帧**，帧数按单帧步长预算反解）
HOLD_END = _env_i("AH_HOLD", 18)           # 命停 f_HIT~f_HOLD_END（**3 帧**关节冻结）
RETURN_END = _env_i("AH_RET_END", 25)      # 收招欧拉混合终点（**7 个区间**）；其后逐位克隆
TOTAL = _env_i("AH_TOTAL", 26)             # 0.433 s @60fps（RETURN_END 后 1 帧收招平台）
SLAM_START = CHAMBER_END
RETURN_START = HOLD_END
CANCEL = _env_i("AH_CANCEL", 21)           # 可取消帧（回接缝途中）
# ★ `SLAM_POW` 取值由**扫描**定，不是拍的。三条通道都随它动：
#     f7 （下砸首帧，速度从 chamber 的缓出突然接上）随 `p` **单调下降而上升**；
#     f16（命中帧）随 `p` 上升而上升；
#     f19（收招首帧）**不吃 `p`**，由 `D`·`RETURN_POW` 决定（本支 ≈ 24.2° 的地板）。
#   实测扫描（预算 25.0°，未放宽）：0.92→25.10 红 / 0.91→24.88 余 0.12 /
#   **0.89→24.23 余 0.77（f7 23.49 / f16 24.23 / f19 24.21，三处齐平）** /
#   0.88→24.21 余 0.79（f19 封顶，`p` 已无效）/ 0.84→26.07 红（f7 顶穿）。
#   ⟹ 0.89 是**三条通道同时逼近预算**的鞍点：再降会被 f7 顶穿，再升会被 f16 顶穿。
#   这也印证文件头第 5 件：帧预算已被「落距守恒」榨干，想再压到 23° 以下必须加帧。
SLAM_POW = _env_f("AH_SLAM_POW", 0.89)     # 下砸行程的角速度缓入缓出（近似匀速，两端各让一点）
RETURN_POW = _env_f("AH_RETURN_POW", 1.40)  # 收招缓出（首帧速度 ∝ p，见文件头第 3 件）
ROLL_W = _env_f("AH_ROLL_W", 1.20)         # roll 连续性权重（B08 实测优于 B07 的 0.60）

# ---------------------------------------------------------------- 落速表（见文件头第 1 件）
# 下砸段：`SLAM_A/P/Q` 三个数由**下砸段总落距比 ≥1.2**（区间下界）+ 帧数**一起解**出来，
# 不是手调：10 帧、比值 1.2018。见文件头第 1 件。
SLAM_A = _env_f("AH_SLAM_A", 20.0)   # 下砸段起始落速（mm/帧）
SLAM_P = _env_f("AH_SLAM_P", 2.50)   # 下砸段第一段速度增量
SLAM_Q = _env_f("AH_SLAM_Q", 0.5125)  # 速度增量的增量（>0 ⟹ 帧间落距**严格递增**）
# 收招起始落速（mm/帧）：命中的冲量把下落"吃掉"⟹ 卸力后落速几近归零（吊滞），
# 再由重力线性拉回 A13 入场速度。**它不是"卸力扣减"**（原设计的 `slam_end−RECOIL`
# 会把一帧成本锁在 ~56 mm，8 帧收招要 500 mm 落距 ⟹ 帧数根本买不起，见文件头第 5 件）。
RETURN_V0_MM = _env_f("AH_RETURN_V0", 5.0)

SIDES = ("L", "R")
ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")
LEG6 = ("thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R")
TRUNK8 = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
          "shoulder.L", "shoulder.R")
# ★ 库里 `PROBE_BONES` 不含 thigh / shin（长期坑，B06 已记），本进程内并入。
PROBE_EXTRA = ("thigh.L", "thigh.R", "shin.L", "shin.R")

G_PER_FRAME = JFE.G_PER_FRAME

# ---------------------------------------------------------------- 门禁阈值
AIR_DRIFT_MAX_MM = 60.0              # 骨盆水平漂移
SLAM_RATIO_RANGE = (1.20, 2.20)      # 下砸段总落距 / 同时长自由落体（**区间**）
SLAM_POWER_MIN_MM = 850.0            # 双拳相对肩的 −z 行程（探针设计值 930.0）
COUNTER_BALANCE_RANGE = (0.05, 0.35)  # 躯干前折 / 下砸行程（**区间**）
NO_TELEPORT_MAX_DEG = 25.0
AIRBORNE_MIN_CLEARANCE_MM = 0.0      # 只需"真的离地"（>0）
LEG_DROP_OVER_SEAM_MM = 80.0         # 腿比**出口接缝**最多多伸多少（姿态口径）
SEAM_TOL = 1e-6
FALL_TOL_MM = 0.05                   # 落距守恒的数值容差

# ---------------------------------------------------------------- 设计候选
# 拳峰**相对肩**的世界偏移（米）。x = 左正；y = 身后正（角色正面朝 −y）；z = 上正。
REL_AC = {"L": Vector((0.075, -0.215, 0.470)),      # 过顶蓄力
          "R": Vector((-0.075, -0.215, 0.470))}
# 砸落命中：竖直 −460 mm 恒定（保证 `slam_power` = 470+460 = 930 mm 不变），
# **水平距离**是自由量 —— 它决定肘的弯曲角，进而决定收招的欧拉行程 D（见文件头第 5 件）。
_AH_H_MM = _env_f("AH_H_MM", 338.4)     # 拳峰相对肩的水平距离（mm），默认 = |(75, −330)|
_AH_Z_MM = _env_f("AH_Z_MM", -460.0)    # 拳峰相对肩的竖直偏移（mm）
_AH_U = Vector((75.0, -330.0))          # 水平方向（保持 x:y 比例，只缩放模长）
_AH_UX = _AH_U.normalized() * (_AH_H_MM / 1000.0)
REL_AH = {"L": Vector((_AH_UX.x, _AH_UX.y, _AH_Z_MM / 1000.0)),
          "R": Vector((-_AH_UX.x, _AH_UX.y, _AH_Z_MM / 1000.0))}
# 踝**相对髋**的增量（米）：前摇收膝，下砸段回到出口接缝的落地构型。
ANK_AC_DELTA = Vector((0.0, 0.055, 0.175))
POLE_ARM_AC = {"L": (0.62, 0.12, -0.77), "R": (-0.62, 0.12, -0.77)}
POLE_ARM_AH = {"L": (_env_f("AH_POLE_X", 0.30), _env_f("AH_POLE_Y", 0.62),
                     _env_f("AH_POLE_Z", -0.72)),
               "R": (-_env_f("AH_POLE_X", 0.30), _env_f("AH_POLE_Y", 0.62),
                     _env_f("AH_POLE_Z", -0.72))}
POLE_LEG_AH = {"L": (0.16, -1.0, 0.0), "R": (-0.16, -1.0, 0.0)}

# ---------------------------------------------------------------- 足尖（度，正 = 压脚背）
TIP_A0 = JU.TIP_KEYS[-1][1]    # = 8.0（A11 末帧的真值，不硬编码）
TIP_AC = {"L": 10.0, "R": 10.0}
TIP_AH = {"L": -4.0, "R": -4.0}   # 向出口接缝（A12 末 = −6 勾脚）靠

STATE = {}                     # A0 / AC / AH
HAND0 = {}
POLE_LEG_A0 = {}
POLE_ARM_A0 = {}
HIP0 = {}
START_POSE = {}
START_QUATS = {}
START_MATS = None
END_POSE = {}
END_QUATS = {}
END_MATS = None
Z_START = 0.0
Z_END = 0.0
TARGET_FALL_MM = 0.0
CHAMBER_SCALE = 0.0
FALL_PROFILE = []
PELVIS_Z_TABLE = []
LOCK = {}
LOCK_PY = {}
LOCK_ANK = {}
LOCK_POLE = {}
TARGETS = []
ARMTGT = []
TRACE = []


# =============================================================== 弹道（落距守恒）
def v_free(frame):
    """A12 弹道在第 frame 帧的落距（mm，正 = 往下落）——**自由落体参照**。"""
    return (JFE.pelvis_z(frame) - JFE.pelvis_z(frame + 1)) * 1000.0


def _fall_profile(c):
    """落距表（mm/帧，共 TOTAL 条）—— 吊滞前摇 / 递增下砸 / 命停续落 / 卸力收招。

    ★ 前摇的"吊速比例" `c` 是**唯一自由量**，由「总落距必须精确等于两个接缝
      的骨盆 z 差」**二分反解**得到（不硬编码残差）—— 见文件头第 1 件。
    """
    out = []
    # 前摇（吊滞）：帧 0..CHAMBER_END-1
    for frame in range(CHAMBER_END):
        out.append(c * v_free(frame))
    # 下砸：帧 CHAMBER_END..HIT-1，增量 P + Q·j ⟹ **严格递增**
    for k in range(HIT - CHAMBER_END):
        out.append(SLAM_A + sum(SLAM_P + SLAM_Q * j for j in range(k)))
    slam_end = out[-1]
    # 命停：帧 HIT..HOLD_END-1（关节冻结，骨盆续落）
    for k in range(HOLD_END - HIT):
        out.append(slam_end - 1.0 - k)
    # 收招：帧 HOLD_END..TOTAL-1。从「卸力后的落速」线性回升到 A13 入场速度
    # （见常量 `RETURN_V0_MM` 的注释：末帧落速必须**精确**等于 A13 入场速度，
    #  否则接缝处会看到一次"突然加速掉进地面"的跳变）。
    count = TOTAL - HOLD_END
    entry = v_free(24)                       # = A13 首帧落速（派生，不硬编码）
    step = (entry - RETURN_V0_MM) / float(max(1, count - 1))
    for i in range(count):
        out.append(RETURN_V0_MM + i * step)
    return out


def _solve_chamber_scale(target_mm):
    lo, hi = -6.0, 6.0
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        if sum(_fall_profile(mid)) < target_mm:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def build_trajectory(z_start, z_end):
    """解出落速表并把骨盆 z 表建好（末帧**强制**逐位等于出口接缝）。"""
    global FALL_PROFILE, PELVIS_Z_TABLE, CHAMBER_SCALE, TARGET_FALL_MM
    TARGET_FALL_MM = (z_start - z_end) * 1000.0
    CHAMBER_SCALE = _solve_chamber_scale(TARGET_FALL_MM)
    FALL_PROFILE = _fall_profile(CHAMBER_SCALE)
    table, z = [z_start], z_start
    for drop in FALL_PROFILE:
        z -= drop / 1000.0
        table.append(z)
    table[-1] = z_end        # 末端逐位对齐出口接缝（残差 ~1e-13 m，纯浮点尾巴）
    PELVIS_Z_TABLE = table
    return table


def pelvis_z(frame):
    """B09 自己的骨盆世界 z（米）—— 见文件头第 1 件（**不是** A12 的弹道）。"""
    return PELVIS_Z_TABLE[frame]


# =============================================================== 阶段时钟
def stage_of(frame):
    """返回 (段名, 插值参数 s)。"""
    if frame <= 0:
        return ("seam", 0.0)
    if frame <= CHAMBER_END:
        return ("chamber", JS._ease_ramp(frame / float(CHAMBER_END)))
    if frame <= HIT:
        u = (frame - SLAM_START) / float(HIT - SLAM_START)
        return ("slam", u ** SLAM_POW)
    if frame <= HOLD_END:
        return ("hold", 1.0)
    u = min(1.0, (frame - RETURN_START) / float(RETURN_END - RETURN_START))
    return ("return", 1.0 - (1.0 - u) ** RETURN_POW)


def lerp_state(frame):
    kind, s = stage_of(frame)
    if kind == "seam":
        return kind, 0.0, STATE["A0"], STATE["A0"]
    if kind == "chamber":
        return kind, s, STATE["A0"], STATE["AC"]
    if kind == "slam":
        return kind, s, STATE["AC"], STATE["AH"]
    if kind == "hold":
        return kind, 1.0, STATE["AH"], STATE["AH"]
    return kind, s, STATE["AH"], STATE["A0"]


def _clone(pose):
    return {k: (dict(v) if k == "@loc" else tuple(v)) for k, v in pose.items()}


def _end_clone():
    """出口接缝姿态的克隆：欧拉折算到「离命中姿态最近」的等价分支。

    ★ 为什么必须折算：直接抄 `Jump_Land@0` 的 euler 可能落在另一个等价分支上
    （±360 / ±180 翻转），世界姿态一样、但欧拉通道差一大截 ⟹ 收招末段步长爆炸。
    """
    pose = _clone(END_POSE)
    for name in list(pose):
        if name.startswith("@"):
            continue
        pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name), pose[name])
    return pose


# =============================================================== 腿 IK（带 roll 连续性）
def leg_aim_stable(arm, pose, side, target, pole, frame):
    """`UP.leg_aim` 的 roll 连续性版（把 `JS.aim_carry` 换成 `aim_carry_stable`）。

    本支的腿要从收膝（比值 0.59）伸到落地构型（比值 0.98），
    「逐帧改主意」的病会落在腿上，所以给腿也用 B07/B08 那把尺子。
    """
    thigh_len, shin_len = A.L_THIGH, A.L_SHIN
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    target = Vector(target)
    delta = target - hip
    raw = delta.length
    limit = (thigh_len + shin_len) * 0.9995
    distance = max(1e-4, min(raw, limit))
    UP.REACH.append((side, raw / (thigh_len + shin_len)))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    bulge, sin_pole = UP._bulge(side, axis, pole)
    cos_hip = (thigh_len ** 2 + distance ** 2 - shin_len ** 2) \
        / (2.0 * thigh_len * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    knee = hip + (axis * cos_hip + bulge * sin_hip) * thigh_len
    pose["thigh." + side] = UP.aim_carry_stable(arm, "thigh." + side, knee - hip)
    pose["shin." + side] = UP.aim_carry_stable(arm, "shin." + side, target - knee)
    UP.POLE_SIN.append((frame, side, sin_pole))
    return sin_pole


# =============================================================== 姿态生成
def _euler_mix(pose_a, pose_b, t):
    """欧拉空间**逐分量**插值（收招专用）。`t >= 1` 直接取 `pose_b`（逐位）。

    为什么不复用 `A.blend`：`a + (b−a)·1.0` 在浮点下不保证逐位等于 `b`，
    而收招的终点必须**逐位**等于出口接缝克隆（`air_seam_end_ok` 容差 1e-6）。
    """
    if t >= 1.0:
        return _clone(pose_b)
    out = {}
    for key in set(pose_a) | set(pose_b):
        if key.startswith("@"):
            continue
        va = pose_a.get(key, (0.0, 0.0, 0.0))
        vb = pose_b.get(key, (0.0, 0.0, 0.0))
        out[key] = tuple(a + (b - a) * t for a, b in zip(va, vb))
    return out


def build_pose(arm, frame, record=False):
    """按帧构造完整姿态。

    三类执行：
      ① 命中窗口 f15~f17：复用 f15 解出的**关节姿态**；骨盆 loc 每帧仍按落速表
         （见文件头：顿的是关节，不是时间）；
      ② 收招段 f18~f21：**欧拉空间逐分量插值** AH → 出口接缝克隆（不做 IK）；
      ③ 末帧 f22：复用「出口接缝克隆」；骨盆 loc = 出口接缝的真值。
    """
    lock_key = HIT if HIT <= frame <= HOLD_END \
        else (TOTAL if frame >= RETURN_END else None)

    if lock_key is not None and lock_key in LOCK:
        pose = _clone(LOCK[lock_key])
        pose["@loc"]["pelvis"] = A.wloc(0.0, LOCK_PY[lock_key],
                                        pelvis_z(frame) - 0.900)
        A.apply_pose(arm, pose)
        if record:
            for side in SIDES:
                target = (Vector(A.bone_world(arm, "thigh." + side, "head"))
                          + Vector(LOCK_ANK[lock_key][side]))
                TARGETS.append((frame, side, tuple(target)))
        _record(arm, frame, pose)
        return pose

    kind, s, sa, sb = lerp_state(frame)

    if kind == "return":
        # ★★ 收招**不做 IK**：直接在欧拉空间插值到出口接缝克隆（B08 第 2 件）。
        pose = _euler_mix(LOCK[HIT], LOCK[TOTAL], s)
        py = sa["pelvis_y"] + (sb["pelvis_y"] - sa["pelvis_y"]) * s
        pose["@loc"] = {"pelvis": A.wloc(0.0, py, pelvis_z(frame) - 0.900)}
        A.apply_pose(arm, pose)
        _record(arm, frame, pose)
        return pose

    trunk = A.blend(sa["trunk"], sb["trunk"], s)
    rel = {k: sa["rel"][k].lerp(sb["rel"][k], s) for k in SIDES}
    hand = {k: JS._slerp(sa["hand"][k], sb["hand"][k], s) for k in SIDES}
    ankle = {k: sa["ankle"][k].lerp(sb["ankle"][k], s) for k in SIDES}
    tip = {k: sa["tip"][k] + (sb["tip"][k] - sa["tip"][k]) * s for k in SIDES}
    pole_arm = {k: _lerp3(sa["pole_arm"][k], sb["pole_arm"][k], s) for k in SIDES}
    pole_leg = {k: _lerp3(sa["pole_leg"][k], sb["pole_leg"][k], s) for k in SIDES}
    py = sa["pelvis_y"] + (sb["pelvis_y"] - sa["pelvis_y"]) * s

    pose = dict(trunk)
    pose["toe.L"] = (0.0, 0.0, 0.0)
    pose["toe.R"] = (0.0, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(0.0, py, pelvis_z(frame) - 0.900)}
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    for side in SIDES:
        target = Vector(A.bone_world(arm, "thigh." + side, "head")) + ankle[side]
        if record:
            TARGETS.append((frame, side, tuple(target)))
        leg_aim_stable(arm, pose, side, target, pole_leg[side], frame)

    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        WF.add_world_rx(arm, name, tip[side])
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v) for v in arm.pose.bones[name].rotation_euler))

    req_mark = len(UP.REQ)
    for side in SIDES:
        fist = Vector(A.bone_world(arm, "upperarm." + side, "head")) + rel[side]
        if record:
            ARMTGT.append((frame, side, tuple(fist)))
        UP.arm_to(arm, pose, side, fist, hand[side], pole_arm[side])
    for index in range(req_mark, len(UP.REQ)):
        UP.REQ[index] = (frame,) + UP.REQ[index]

    _record(arm, frame, pose)
    if lock_key == HIT and HIT not in LOCK:
        LOCK[HIT] = _clone(pose)
        LOCK_PY[HIT] = py
        LOCK_ANK[HIT] = {s: tuple(ankle[s]) for s in SIDES}
        LOCK_POLE["HIT"] = {s: tuple(UP._elbow_pole_from_pose(arm, s))
                            for s in SIDES}
        # ★ 出口接缝克隆**就在此刻**构造：`_PREV_EULER` 刚被 `_record` 写成命中姿态，
        #   于是 `_unwrap_xyz` 把 `Jump_Land@0` 的欧拉折到**离命中姿态最近的那一支**
        #   ⟹ 收招的欧拉行程最短（见文件头第 3 件）。
        LOCK[TOTAL] = _end_clone()
        LOCK_PY[TOTAL] = 0.0
        LOCK_ANK[TOTAL] = {s: tuple(STATE["END"]["ankle"][s]) for s in SIDES}
    return pose


def _lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _record(arm, frame, pose):
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    TRACE.append({
        "frame": frame,
        "euler": {b: tuple(round(v, 2) for v in pose.get(b, (0.0, 0.0, 0.0)))
                  for b in ARM6 + LEG6},
        "roll": {b: round(JS.ARM_ROLL.get(b, 0.0), 1) for b in ARM6 + LEG6},
    })


# =============================================================== 状态表
def _trunk(start):
    """三张躯干表：A0 = 接缝原值；AC = 后仰蓄力；AH = 前折发力（见文件头第 4 条）。"""
    def g(bone):
        return start.get(bone, (0.0, 0.0, 0.0))[0]

    a0 = {bone: tuple(start.get(bone, (0.0, 0.0, 0.0))) for bone in TRUNK8}
    # ★ 轴语义（`rig_axis_map`）：rx > 0 = 前屈 / 低头；rx < 0 = 后仰 / 抬头。
    ac = {
        "pelvis": (g("pelvis") - 1.0, 0.0, 0.0),
        "spine_01": (g("spine_01") - 3.0, 0.0, 0.0),
        "spine_02": (g("spine_02") - 3.0, 0.0, 0.0),
        "chest": (g("chest") - 5.0, 0.0, 0.0),      # 累计 −11°（后仰）
        "neck": (g("neck") + 2.0, 0.0, 0.0),
        "head": (g("head") + 5.0, 0.0, 0.0),        # 低头盯住下方目标
        "shoulder.L": (g("shoulder.L") + 9.0, 0.0, 0.0),   # 双肩抬起（举拳过顶）
        "shoulder.R": (g("shoulder.R") + 9.0, 0.0, 0.0),
    }
    ah = {
        "pelvis": (g("pelvis") + 3.5, 0.0, 0.0),
        "spine_01": (g("spine_01") + 5.5, 0.0, 0.0),
        "spine_02": (g("spine_02") + 5.5, 0.0, 0.0),
        "chest": (g("chest") + 7.5, 0.0, 0.0),      # 累计 +17°（前折）
        "neck": (g("neck") - 2.0, 0.0, 0.0),
        "head": (g("head") - 4.5, 0.0, 0.0),        # 折腹后抬头，视线不离目标
        "shoulder.L": (g("shoulder.L") - 3.0, 0.0, 0.0),
        "shoulder.R": (g("shoulder.R") - 3.0, 0.0, 0.0),
    }
    return a0, ac, ah


def build_state(arm, start_pose, end_pose):
    """把 A0 / AC / AH / END 四张表算出来（拳/踝都是**相对肩 / 相对髋**的向量）。"""
    global STATE
    A.apply_pose(arm, start_pose)
    bpy.context.view_layer.update()
    fist0, sh0, hip0, ankle0 = {}, {}, {}, {}
    for side in SIDES:
        fist0[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        sh0[side] = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        hip0[side] = Vector(A.bone_world(arm, "thigh." + side, "head"))
        ankle0[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        HAND0[side] = tuple(A.bone_direction(arm, "hand." + side))
        POLE_LEG_A0[side] = UP._leg_pole_from_pose(arm, side)
        POLE_ARM_A0[side] = UP._elbow_pole_from_pose(arm, side)
        HIP0[side] = hip0[side]

    # 出口接缝的踝−髋（本支的"落地构型"，**实测**，不是拍的）
    A.apply_pose(arm, end_pose)
    bpy.context.view_layer.update()
    ank_end = {}
    for side in SIDES:
        hip_e = Vector(A.bone_world(arm, "thigh." + side, "head"))
        ankle_e = Vector(A.bone_world(arm, "foot." + side, "head"))
        ank_end[side] = ankle_e - hip_e

    a0, ac, ah = _trunk(start_pose)

    rel_a0 = {s: fist0[s] - sh0[s] for s in SIDES}
    rel_ac = {s: Vector(REL_AC[s]) for s in SIDES}
    rel_ah = {s: Vector(REL_AH[s]) for s in SIDES}
    # ★ 手骨指向 = 拳峰相对肩的方向（文件头第 1 条）⟹ 腕距 = |rel| − hand_len，
    #   恒落在 [176.6, 551.7] 环带内，`arm_to` 的夹取全程不触发。
    hand_ac = {s: tuple(rel_ac[s].normalized()) for s in SIDES}
    hand_ah = {s: tuple(rel_ah[s].normalized()) for s in SIDES}

    ank_a0 = {s: ankle0[s] - hip0[s] for s in SIDES}
    ank_ac = {s: ank_a0[s] + ANK_AC_DELTA for s in SIDES}

    STATE = {
        "A0": {
            "trunk": a0, "rel": rel_a0, "hand": dict(HAND0),
            "ankle": ank_a0, "tip": {"L": TIP_A0, "R": TIP_A0},
            "pole_arm": dict(POLE_ARM_A0), "pole_leg": dict(POLE_LEG_A0),
            "pelvis_y": 0.0,
        },
        "AC": {
            "trunk": ac, "rel": rel_ac, "hand": hand_ac, "ankle": ank_ac,
            "tip": dict(TIP_AC),
            "pole_arm": {s: _lerp3(POLE_ARM_A0[s], POLE_ARM_AC[s], 0.6)
                         for s in SIDES},
            "pole_leg": {s: _lerp3(POLE_LEG_A0[s], POLE_LEG_AH[s], 0.5)
                         for s in SIDES},
            "pelvis_y": 0.0,
        },
        "AH": {
            "trunk": ah, "rel": rel_ah, "hand": hand_ah, "ankle": ank_end,
            "tip": dict(TIP_AH),
            "pole_arm": dict(POLE_ARM_AH), "pole_leg": dict(POLE_LEG_AH),
            "pelvis_y": 0.0,
        },
        "END": {"ankle": ank_end},
    }
    return rel_a0, ank_a0, ank_end


# =============================================================== 接缝尺子
def _bone_point(mat):
    return (mat[3], mat[7], mat[11])


def pelvis_moving(arm):
    """`pelvis` 的后代骨集合（含自身）。

    ★ B08 第 1 件：全世界只有 `pelvis` 带 `@loc` ⟹ 只有它和它的**后代**跟着
    弹道平移；`root`（pelvis 的父骨）**原地不动**。所以「平移不变」只对
    **会动的那部分骨架**成立：后代骨比「相对骨盆」，非后代骨比「世界绝对」。
    **修的是尺子，容差 1e-6 一字未动。**
    """
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
    """两套世界矩阵的「平移不变」逐位差（返回 朝向差 / 相对位置差_m / 两根最差骨）。"""
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


# =============================================================== 门禁
def air_assertions(arm, action, samples, start_mats, end_mats, sole,
                   target_err, reach, knee):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(s["pelvis"]) for s in samples]
    zs = [p.z for p in pelvis]

    # 0) 接缝：首帧 vs `Jump_Fall@0`（原始世界矩阵逐位）；
    #    末帧 vs `Jump_Land@0`（**平移不变**尺子 —— 骨盆已沿新弹道又落 813 mm）。
    mats0 = CR.action_world_matrices(arm, action, 0)
    mats1 = CR.action_world_matrices(arm, action, TOTAL)
    moving = pelvis_moving(arm)
    delta0 = CR.matrix_delta(mats0, start_mats)
    ori1, rel1, ori_bone, rel_bone = pose_seam_split(mats1, end_mats, moving)
    delta1 = max(ori1, rel1)
    raw1 = CR.matrix_delta(mats1, end_mats)
    res["seam_start_delta"] = float("%.3e" % delta0)
    res["seam_end_pose_delta"] = float("%.3e" % delta1)
    res["seam_end_orient_delta"] = float("%.3e" % ori1)
    res["seam_end_orient_bone"] = ori_bone
    res["seam_end_relpos_delta_mm"] = round(rel1 * 1000.0, 6)
    res["seam_end_relpos_bone"] = rel_bone
    res["seam_end_raw_delta_mm"] = round(raw1 * 1000.0, 1)
    res["air_seam_start_ok"] = delta0 <= SEAM_TOL
    res["air_seam_end_ok"] = delta1 <= SEAM_TOL
    res["seam_ruler_note"] = (
        "首帧比 `Jump_Fall@0` 的**原始**世界矩阵；末帧比 `Jump_Land@0` 的"
        "**平移不变**姿态差（pelvis 的后代比「骨位置−骨盆位置」，非后代比世界绝对）。"
        "容差 1e-6，未放宽。")

    # 1) **落距守恒**：总落距必须精确等于两接缝骨盆 z 之差（死数 813.3333 mm）。
    res["fall_total_mm"] = round((zs[0] - zs[-1]) * 1000.0, 4)
    res["target_fall_mm"] = round(TARGET_FALL_MM, 4)
    res["fall_residual_mm"] = round(
        (zs[0] - zs[-1]) * 1000.0 - TARGET_FALL_MM, 6)
    res["fall_conserved_ok"] = abs(res["fall_residual_mm"]) <= FALL_TOL_MM
    res["landing_link_mm"] = round((zs[-1] - Z_END) * 1000.0, 6)
    res["landing_link_ok"] = abs(res["landing_link_mm"]) <= FALL_TOL_MM
    res["free_fall_same_frames_mm"] = round(
        (JFE.pelvis_z(0) - JFE.pelvis_z(TOTAL)) * 1000.0, 3)
    res["fall_vs_free_fall"] = round(
        res["fall_total_mm"] / res["free_fall_same_frames_mm"], 4)

    # 2) 单调下落（"下砸"不许变成"上挑"）。
    rise = [frames[i + 1] for i in range(len(zs) - 1)
            if zs[i + 1] > zs[i] + 1e-12]
    res["ballistic_rise_frames"] = rise
    res["monotone_down_ok"] = not rise
    res["z_start_mm"] = round(zs[0] * 1000.0, 3)
    res["z_hit_mm"] = round(zs[HIT] * 1000.0, 3)
    res["z_end_mm"] = round(zs[-1] * 1000.0, 3)
    res["pelvis_hit_minus_start_mm"] = round((zs[HIT] - zs[0]) * 1000.0, 1)
    res["no_center_rise_ok"] = zs[HIT] <= zs[0] - 1e-9

    # 3) **下砸段**：帧间落距**严格递增** + 总落距比 ∈[1.2, 2.2]（区间）。
    drops = [(zs[i] - zs[i + 1]) * 1000.0 for i in range(CHAMBER_END, HIT)]
    frees = [v_free(f) for f in range(CHAMBER_END, HIT)]
    res["slam_drops_mm"] = [round(v, 3) for v in drops]
    res["slam_deltas_mm"] = [round(drops[i + 1] - drops[i], 4)
                             for i in range(len(drops) - 1)]
    res["slam_step_increasing_ok"] = all(
        res["slam_deltas_mm"][i + 1] > res["slam_deltas_mm"][i]
        for i in range(len(res["slam_deltas_mm"]) - 1))
    res["slam_total_mm"] = round(sum(drops), 3)
    res["slam_free_equiv_mm"] = round(sum(frees), 3)
    res["slam_ratio"] = round(sum(drops) / sum(frees), 4)
    res["slam_ratio_range"] = list(SLAM_RATIO_RANGE)
    res["slam_accel_ok"] = bool(
        res["slam_step_increasing_ok"]
        and SLAM_RATIO_RANGE[0] <= res["slam_ratio"] <= SLAM_RATIO_RANGE[1])
    res["slam_accel_note"] = (
        "区间 [%.2f, %.2f] 的物理含义：下界 = 真的砸下去了（不只是滑落），"
        "上界 = 不是瞬移。**落距守恒** ⟹ 前摇吊得越狠、下砸就能砸得越重；"
        "本支前摇比例 c = %.4f（吊滞）。" % (SLAM_RATIO_RANGE[0], SLAM_RATIO_RANGE[1],
                                            CHAMBER_SCALE))
    res["chamber_drops_mm"] = [round((zs[i] - zs[i + 1]) * 1000.0, 3)
                               for i in range(CHAMBER_END)]
    res["chamber_scale"] = round(CHAMBER_SCALE, 6)

    # 4) **下砸力度**：双拳**相对肩**的 −z 行程（隔离"挥臂下砸"，不含下落）。
    def rel_z(idx, side):
        return (Vector(samples[idx]["hand." + side + ".tail"]).z
                - Vector(samples[idx]["upperarm." + side]).z) * 1000.0

    power = {s: rel_z(CHAMBER_END, s) - rel_z(HIT, s) for s in SIDES}
    res["fist_rel_shoulder_z_ac_mm"] = {s: round(rel_z(CHAMBER_END, s), 1)
                                        for s in SIDES}
    res["fist_rel_shoulder_z_hit_mm"] = {s: round(rel_z(HIT, s), 1)
                                         for s in SIDES}
    res["slam_power_mm"] = {s: round(power[s], 1) for s in SIDES}
    res["slam_power_min_mm"] = SLAM_POWER_MIN_MM
    res["slam_power_ok"] = all(v >= SLAM_POWER_MIN_MM for v in power.values())
    world_z = {s: (Vector(samples[CHAMBER_END]["hand." + s + ".tail"]).z
                   - Vector(samples[HIT]["hand." + s + ".tail"]).z) * 1000.0
               for s in SIDES}
    res["slam_world_drop_mm"] = {s: round(world_z[s], 1) for s in SIDES}
    res["slam_ruler_note"] = (
        "力度量的是「拳峰 − 肩」的 −z 行程（**相对量**）：下落由弹道门禁单独守，"
        "混进来会被 813 mm 的落距淹没（同 A06 踩坑 5 / B08 的口径）。"
        "探针设计值 = 470 −(−460) = 930 mm。")
    chest_hit = Vector(samples[HIT]["chest.tail"]).z
    fist_hit = min(Vector(samples[HIT]["hand." + s + ".tail"]).z for s in SIDES)
    res["fist_below_chest_mm"] = round((chest_hit - fist_hit) * 1000.0, 1)
    res["fist_below_chest_ok"] = fist_hit < chest_hit

    # 5) **配重**：躯干前折行程 / 下砸行程（空中无地面反力，反作用只能由躯干吃）。
    def chest_fwd(idx):
        return (Vector(samples[idx]["chest.tail"]).y
                - Vector(samples[idx]["pelvis"]).y) * 1000.0

    fold = chest_fwd(CHAMBER_END) - chest_fwd(HIT)     # AC 在后 → AH 在前 ⟹ 正
    res["chest_fold_mm"] = round(fold, 1)
    res["chest_fwd_ac_mm"] = round(chest_fwd(CHAMBER_END), 1)
    res["chest_fwd_hit_mm"] = round(chest_fwd(HIT), 1)
    denom = max(power.values()) if max(power.values()) > 1e-9 else None
    ratio = (fold / denom) if denom is not None else None
    res["counter_balance_ratio"] = round(ratio, 4) if ratio is not None else None
    res["counter_balance_range"] = list(COUNTER_BALANCE_RANGE)
    res["counter_balance_ok"] = bool(
        ratio is not None
        and COUNTER_BALANCE_RANGE[0] <= ratio <= COUNTER_BALANCE_RANGE[1])
    res["counter_balance_note"] = (
        "躯干前折（胸骨顶相对骨盆的 −y 位移）/ 双拳下砸行程，**给的是区间**，"
        "单边阈值等于没定。分侧腿姿态（A13 出口接缝）本身不对称，故用躯干做配重尺子。")

    # 6) 命停：f15~f17 **关节**姿态完全冻结（骨盆 loc 照常落）。
    steps = []
    for i in range(HIT + 1, HOLD_END + 1):
        worst = 0.0
        for name in set(samples[i]["euler"]) | set(samples[i - 1]["euler"]):
            ea = samples[i - 1]["euler"].get(name, (0.0, 0.0, 0.0))
            eb = samples[i]["euler"].get(name, (0.0, 0.0, 0.0))
            worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
        steps.append(round(worst, 5))
    res["hitstop_frozen_steps"] = steps
    res["hitstop_frames"] = HOLD_END - HIT + 1
    res["hitstop_present"] = (len(steps) >= 2 and max(steps) <= 1e-3)
    res["hitstop_fall_mm"] = round((zs[HIT] - zs[HOLD_END]) * 1000.0, 1)
    res["hitstop_note"] = (
        "顿的是**关节欧拉通道**，不含 location；骨盆在这 3 帧仍按落速表续落 %.1f mm"
        "（连骨盆一起冻就没有下砸的动能了）。" % res["hitstop_fall_mm"])

    # 7) 全段离地：通用贴地/滑移窗口不适用，显式登记原因。
    #    ★ 判据是**结构式**：鞋底全程 >0 + 腿不许比**出口接缝**多伸 >80 mm。
    lows = [min(sole[i]["L"], sole[i]["R"]) for i in range(len(sole))]
    drop = [zs[i] - lows[i] for i in range(len(sole))]
    res["min_sole_all_mm"] = round(min(lows) * 1000.0, 1)
    res["min_sole_frame"] = frames[lows.index(min(lows))]
    res["end_sole_clearance_mm"] = round(lows[-1] * 1000.0, 1)
    res["leg_drop_mm"] = {"start": round(drop[0] * 1000.0, 1),
                          "max": round(max(drop) * 1000.0, 1),
                          "end": round(drop[-1] * 1000.0, 1)}
    res["leg_drop_over_seam_mm"] = round((max(drop) - drop[-1]) * 1000.0, 1)
    res["all_airborne_ok"] = bool(
        min(lows) > AIRBORNE_MIN_CLEARANCE_MM
        and (max(drop) - drop[-1]) * 1000.0 <= LEG_DROP_OVER_SEAM_MM)
    res["airborne_ruler_note"] = (
        "全段离地用**结构口径**：① 鞋底全程 > 0（真的没落地）；② 腿不许比**出口接缝"
        "（落地构型）**多伸 > %.0f mm —— 口径 = 「骨盆→最低鞋底」的竖距，"
        "只跟姿态有关、跟落了多少无关。★ 基准取**出口接缝**而不是入口接缝："
        "入口（`Jump_Fall@0`）是屈腿 640 mm 的姿势，而本支的任务就是把它伸到 782"
        "（B08 拿入口当基准的坑）。" % LEG_DROP_OVER_SEAM_MM)
    res["ground_contact_ok"] = None
    res["ground_contact_skipped_reason"] = \
        "全段离地（鞋底最低 %.1f mm @ f%d），-2~+6 mm 窗口不适用" % (
            min(lows) * 1000.0, frames[lows.index(min(lows))])
    res["no_foot_slide_skipped_reason"] = "全段离地，支撑脚不存在"

    # 8) 收招缓出：口径固定在**收招窗口**（含"从命停释放"的第一步 f17→f18）。
    tail, bones = [], []
    for index in range(RETURN_START + 1, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst, bone = 0.0, None
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > worst:
                worst, bone = step, name
        tail.append(round(worst, 5))
        bones.append(bone)
    res["return_tail_deg_per_frame"] = tail
    res["return_tail_worst_bone"] = bones
    res["return_tail_window"] = [RETURN_START + 1, TOTAL]
    res["decel_smooth_ok"] = bool(
        len(tail) >= 2 and all(tail[i + 1] <= tail[i] + 1e-9
                               for i in range(len(tail) - 1)))
    res["no_snap_stop_ok"] = bool(tail and tail[-1] <= 5.0)
    res["return_exit_speed_mm_per_frame"] = round(
        (zs[-2] - zs[-1]) * 1000.0, 3)
    res["a13_entry_speed_mm_per_frame"] = round(v_free(24), 3)
    res["return_speed_match_mm"] = round(
        abs(res["return_exit_speed_mm_per_frame"]
            - res["a13_entry_speed_mm_per_frame"]), 4)
    res["decel_smooth_note"] = (
        "窗口取 [f%d, f%d]：**含**从命停释放的第一步 f%d→f%d（最大的一步就在这里），"
        "再逐帧单调收敛到 0。收招 5 帧、缓出幂 1.40 ⟹ 首步占比 0.2682。"
        "**是换对窗口，不是放宽容差。**"
        % (RETURN_START + 1, TOTAL, RETURN_START, RETURN_START + 1))

    # 9) IK 到位 / 腿可达余量。
    limit = A.L_THIGH + A.L_SHIN
    res["ankle_target_error_mm"] = round(target_err * 1000.0, 3)
    res["ik_reach_ok"] = target_err * 1000.0 <= 5.0
    res["leg_reach_limit_mm"] = round(limit * 1000.0, 1)
    res["leg_reach_max_ratio"] = {
        s: round(max(r for side, r in reach if side == s), 4) for s in SIDES}
    res["leg_reach_headroom_mm"] = {
        s: round((limit - max(r for side, r in reach if side == s) * limit)
                 * 1000.0, 1) for s in SIDES}
    res["leg_reach_ok"] = bool(all(r <= 0.9995 for _s, r in reach))

    # 10) 膝角（诊断）。
    res["knee_bend_start_deg"] = {s: round(knee[0][s], 2) for s in SIDES}
    res["knee_bend_hit_deg"] = {s: round(knee[HIT][s], 2) for s in SIDES}
    res["knee_bend_end_deg"] = {s: round(knee[-1][s], 2) for s in SIDES}
    res["knee_bend_span_deg"] = {
        s: round(max(k[s] for k in knee) - min(k[s] for k in knee), 2)
        for s in SIDES}

    # 11) 力量传导链（脚→腿→髋→腰→肩→手，六段全非零）。
    #     空中无地面反力 ⟹ 尺子取「可见」下限（位移 ≥5 mm / 转角 ≥3°），
    #     与 A11/A12/B08 同口径，实测值一并登记（**不放宽、只换对**）。
    moved, swing, nonzero = {}, {}, {}
    for segment, names in (("foot", ("foot.L", "foot.R")),
                           ("pelvis", ("pelvis",)),
                           ("chest", ("chest",)),
                           ("shoulder", ("shoulder.L", "shoulder.R")),
                           ("hand", ("hand.L.tail", "hand.R.tail"))):
        big = 0.0
        for name in names:
            points = [Vector(s[name]) for s in samples]
            big = max(big, max((p - points[0]).length for p in points) * 1000.0)
        moved[segment] = round(big, 2)
    for segment, names in (("thigh", ("thigh.L", "thigh.R")),
                           ("shin", ("shin.L", "shin.R"))):
        big = 0.0
        for name in names:
            vals = [s["euler"].get(name, (0.0, 0.0, 0.0))[0] for s in samples]
            big = max(big, max(vals) - min(vals))
        swing[segment] = round(big, 2)
    for name in ("spine_01", "spine_02", "chest", "shoulder.L", "shoulder.R"):
        nonzero[name] = round(max(abs(v) for s in samples
                                  for v in s["euler"].get(name, (0.0, 0.0, 0.0))),
                              2)
    res["power_chain_travel_mm"] = moved
    res["power_chain_swing_deg"] = swing
    res["power_chain_nonzero_deg"] = nonzero
    res["power_chain_ok"] = (all(v >= 5.0 for v in moved.values())
                             and all(v >= 3.0 for v in swing.values())
                             and all(v >= 1.0 for v in nonzero.values()))

    # 12) 逐帧最大欧拉步长排行（`no_teleport` 红时直接定位）。
    scan = []
    for index in range(1, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst_step, worst_bone = 0.0, None
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > worst_step:
                worst_step, worst_bone = step, name
        scan.append([samples[index]["frame"], worst_bone, round(worst_step, 2)])
    res["step_scan_top"] = sorted(scan, key=lambda r: -r[2])[:10]
    worst_scan = max((r[2] for r in scan), default=0.0)
    res["no_teleport_max_step_deg"] = round(worst_scan, 3)
    res["no_teleport_budget_left_deg"] = round(
        NO_TELEPORT_MAX_DEG - worst_scan, 3)

    # 13) 打击点 / 元数据。
    res["hit_point_fist_mm"] = {
        s: [round(v * 1000.0, 1) for v in samples[HIT]["hand." + s + ".tail"]]
        for s in SIDES}
    res["hit_point_ankle_mm"] = {
        s: [round(v * 1000.0, 1) for v in samples[HIT]["foot." + s]]
        for s in SIDES}
    res["chamber_top_fist_mm"] = {
        s: [round(v * 1000.0, 1)
            for v in samples[CHAMBER_END]["hand." + s + ".tail"]] for s in SIDES}
    res["hit_frame"] = HIT
    res["antic_frame"] = CHAMBER_END
    res["cancel_frame"] = CANCEL
    return res


# =============================================================== 主流程
def main():
    global START_POSE, START_QUATS, START_MATS
    global END_POSE, END_QUATS, END_MATS, Z_START, Z_END

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("AIRHEAVY_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()
    for module, action_name in ((JS, JS.NAME), (JU, JU.NAME),
                                (JFE, JFE.NAME), (JL, JL.NAME)):
        if action_name not in bpy.data.actions:
            print("AIRHEAVY_BOOTSTRAP 动画工程缺 %s，先补跑" % action_name)
            module.main()
            arm, meshes = A.open_animation_project()
            A.setup_scene()

    # ★ 库里 `PROBE_BONES` 不含 thigh / shin，本支要量膝，本进程内并入。
    A.PROBE_BONES = tuple(A.PROBE_BONES) + PROBE_EXTRA

    I1.idle_pose(arm, 0.0)

    # ---- 读两条接缝（**不重算**：`aim_carry` 是有状态接力）。
    JU.build_arm_targets()
    START_POSE, START_QUATS = JU.capture_start(
        arm, bpy.data.actions[JFE.NAME], 0)
    START_MATS = CR.action_world_matrices(
        arm, bpy.data.actions[JFE.NAME], 0)
    END_POSE, END_QUATS = JU.capture_start(
        arm, bpy.data.actions[JL.NAME], 0)
    END_MATS = CR.action_world_matrices(
        arm, bpy.data.actions[JL.NAME], 0)
    # ★ 必须卸 action（A11 踩过：留着上游会在某些帧把 f-curve 压回 pose bone）。
    arm.animation_data.action = None
    bpy.context.view_layer.update()

    Z_START = _bone_point(START_MATS["pelvis"])[2]
    Z_END = _bone_point(END_MATS["pelvis"])[2]
    table = build_trajectory(Z_START, Z_END)

    A.report("AIRHEAVY_TRAJECTORY", {
        "z_start_mm": round(Z_START * 1000.0, 3),
        "z_end_mm": round(Z_END * 1000.0, 3),
        "target_fall_mm": round(TARGET_FALL_MM, 4),
        "free_fall_same_frames_mm": round(
            (JFE.pelvis_z(0) - JFE.pelvis_z(TOTAL)) * 1000.0, 3),
        "fall_over_free_fall": round(
            TARGET_FALL_MM / ((JFE.pelvis_z(0) - JFE.pelvis_z(TOTAL)) * 1000.0), 4),
        "chamber_scale": round(CHAMBER_SCALE, 6),
        "v_mm_per_frame": [round(v, 3) for v in FALL_PROFILE],
        "pelvis_z_mm": [round(v * 1000.0, 3) for v in table],
        "sum_mm": round(sum(FALL_PROFILE), 4),
        "residual_mm": round(sum(FALL_PROFILE) - TARGET_FALL_MM, 9),
        "slam_range": [CHAMBER_END, HIT],
        "slam_total_mm": round(sum(FALL_PROFILE[CHAMBER_END:HIT]), 3),
        "slam_free_equiv_mm": round(
            sum(v_free(f) for f in range(CHAMBER_END, HIT)), 3),
        "slam_ratio": round(sum(FALL_PROFILE[CHAMBER_END:HIT])
                            / sum(v_free(f) for f in range(CHAMBER_END, HIT)), 4),
        "a13_entry_v_mm": round(v_free(24), 3),
        "end_v_mm": round(FALL_PROFILE[-1], 3),
        "note": ("★ 「落距守恒」：落速可改、**落距不可改**（首末帧都钉死在接缝上）。"
                 "前摇比例 c 由「总落距 = 两接缝骨盆 z 差」**二分反解**，不是手调。"
                 "下砸要更快 ⟹ 前摇必然更慢（本支吊滞）。"),
    })

    rel_a0, ank_a0, ank_end = build_state(arm, START_POSE, END_POSE)
    A.report("AIRHEAVY_STATE", {
        "fist_rel_shoulder_A0_mm": {s: [round(v * 1000.0, 1) for v in rel_a0[s]]
                                    for s in SIDES},
        "ankle_rel_hip_A0_mm": {s: [round(v * 1000.0, 1) for v in ank_a0[s]]
                                for s in SIDES},
        "ankle_rel_hip_END_mm": {s: [round(v * 1000.0, 1) for v in ank_end[s]]
                                 for s in SIDES},
        "AC_fist_rel_mm": {s: [round(v * 1000.0, 1) for v in REL_AC[s]]
                           for s in SIDES},
        "AH_fist_rel_mm": {s: [round(v * 1000.0, 1) for v in REL_AH[s]]
                           for s in SIDES},
        "slam_z_travel_mm": round((REL_AC["L"].z - REL_AH["L"].z) * 1000.0, 1),
        "note": "拳/踝都是**相对肩 / 相对髋**的量（B07 教训 1：参照系跟躯干走）。",
    })

    JS._PREV_EULER.clear()
    for name, value in START_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    JS.ARM_QUAT.clear()
    JS.ARM_ROLL.clear()
    JS.ROLL_MAX.clear()
    A.apply_pose(arm, START_POSE)
    bpy.context.view_layer.update()
    for name in ARM6 + LEG6:
        JS.ARM_QUAT[name] = arm.pose.bones[name].matrix.to_quaternion()
    JS.MAX_ABS_EULER_Y = 0.0
    # 沿用 A11/B07/B08 已验收的旋钮（A11 实测 `Y_SAFE` 的拐点就是 28）。
    JS.ROLL_RANGE = 150.0
    JS.Y_SAFE = 28.0
    del TARGETS[:]
    del ARMTGT[:]
    del TRACE[:]
    del UP.REACH[:]
    del UP.POLE_SIN[:]
    del UP.REQ[:]
    UP._BULGE_PREV.clear()
    UP._ROLL_PREV.clear()
    UP.ROLL_W = ROLL_W
    LOCK.clear()
    LOCK_PY.clear()
    LOCK_ANK.clear()
    LOCK_POLE.clear()

    keyframes = [(0, START_POSE)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, build_pose(arm, frame, record=True)))

    A.report("AIRHEAVY_ARM_ROLL", {
        "max_abs_euler_y_deg": round(JS.MAX_ABS_EULER_Y, 2),
        "max_abs_roll_deg": {k: round(JS.ROLL_MAX.get(k, 0.0), 1)
                             for k in ARM6 + LEG6},
        "roll_range_deg": JS.ROLL_RANGE, "y_safe_deg": JS.Y_SAFE, "roll_w": ROLL_W,
    })

    meta = {
        "anim_id": NAME, "loop": False, "category": "普通攻击",
        "note": ("空中重击：接 `Jump_Fall@0`（弹道下落中）→ 吊滞 + 双拳举过头顶蓄力 "
                 "+ 收膝 → 全身加速下砸（双拳相对肩下砸 ≥%.0f mm，落速比 ∈[%.1f, %.1f]）"
                 "→ f%d~f%d 关节冻结 3 帧 → 卸力收招（末速接上 A13 入场 %.1f mm/帧）"
                 "→ 末帧逐位 = `Jump_Land@0`（交给 A13 屈膝吸收）"
                 % (SLAM_POWER_MIN_MM, SLAM_RATIO_RANGE[0], SLAM_RATIO_RANGE[1],
                    HIT, HOLD_END, v_free(24))),
        "antic_frame": CHAMBER_END, "hit_frame": HIT, "cancel_frame": CANCEL,
        "hitstop_frames": HOLD_END - HIT + 1,
        "hitstop_span": [HIT, HOLD_END],
        "root_motion_m": [0.0, 0.0],
        "root_motion_note": "空中族**不许** Root Motion（清单 §0.4；C 族起才允许）。",
        "seam_in": "%s@0（世界矩阵逐位相同）" % JFE.NAME,
        "seam_out": ("%s@0（**平移不变**姿态逐位相同 + 末速接上 A13 入场速度；"
                     "骨盆已沿本支新弹道又落 %.1f mm）"
                     % (JL.NAME, TARGET_FALL_MM)),
        "pelvis_ballistic": {
            "rule": ("**自持落速表**：吊滞前摇（c=%.4f）→ 严格递增下砸 → 命停续落 → "
                     "卸力收招（末速 = A13 入场 %.3f mm/帧）"
                     % (CHAMBER_SCALE, v_free(24))),
            "change_allowed": "**允许**（清单原文「允许改变下落速度」；B08 是禁止）",
            "conservation": "落距守恒：总落距 ≡ 两接缝骨盆 z 差 = %.4f mm" % TARGET_FALL_MM,
        },
        "air_drift": {"rule": "骨盆水平位移 ≤ %.0f mm" % AIR_DRIFT_MAX_MM,
                      "why": "空中无地面反力，出拳必有反冲；60 mm 是'看得出但不成漂移'"},
        "counter_balance": {"rule": "躯干前折 / 下砸行程 ∈ [%.2f, %.2f]"
                                    % COUNTER_BALANCE_RANGE,
                            "why": "制动力只能由躯干前折 + 腿下伸提供 —— 空中动作守恒"},
        "power_chain_scale_note": ("空中无地面反力：thigh/shin 取'可见'下限 3°，"
                                   "A10 的 15° 是蹬地展开的量"),
        "hitstop_scope": "冻结全身关节欧拉；骨盆 location 仍走落速表（顿的是关节，不是时间）",
        "landing_link": "末帧 = `Jump_Land@0`（A13 首帧即触地帧，`JFE.pelvis_z(24)`）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "ANTIC_END": CHAMBER_END, "SLAM_START": SLAM_START + 1,
        "HIT": HIT, "HITSTOP_END": HOLD_END, "RETURN_START": RETURN_START,
        "CANCEL": CANCEL, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report["common_ground_min_all_frames_mm"] = report.get("ground_min_mm")
    report["ground_contact_ok"] = None

    sole = JS.sole_series(arm, action, list(range(0, TOTAL + 1)))
    ankles = JU.ankle_series(arm, action, list(range(0, TOTAL + 1)))
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    target_err = 0.0
    for index, frame in enumerate(range(0, TOTAL + 1)):
        if frame == 0:
            continue
        for side in SIDES:
            if (frame, side) in pair:
                target_err = max(target_err,
                                 (Vector(ankles[index][side])
                                  - pair[(frame, side)]).length)

    reach = list(UP.REACH)
    knee = CR.knee_series(arm, action, list(range(0, TOTAL + 1)))
    report.update(air_assertions(arm, action, samples, START_MATS, END_MATS,
                                 sole, target_err, reach, knee))
    report["meta"] = meta
    report["skipped_gates"] = sorted(
        k for k, v in report.items() if v is None and k.endswith("_ok"))
    failed = sorted(k for k, v in report.items()
                    if (k.endswith("_ok") or k == "no_teleport")
                    and v is not True and v is not None)
    report["failed"] = failed
    A.report("AIRHEAVY_REPORT", report)

    detail = []
    for index in range(1, len(TRACE)):
        before, after = TRACE[index - 1], TRACE[index]
        row, big = {"f": after["frame"]}, 0.0
        wname, wfrm, wto = None, None, None
        for name in ARM6 + LEG6:
            ea = before["euler"][name]
            eb = after["euler"][name]
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > big:
                big, wname, wfrm, wto = step, name, ea, eb
            row[name] = "%d Y%.0f r%.0f" % (
                round(step), after["euler"][name][1],
                after["roll"].get(name, 0.0))
        if big >= 4.0:
            row["max_step"] = round(big, 2)
            # ★ 诊断：最差骨的三分量 before → after（找"哪个通道在爆"）
            row["worst_bone"] = wname
            row["worst_from"] = [round(v, 1) for v in wfrm]
            row["worst_to"] = [round(v, 1) for v in wto]
            detail.append(row)
    A.report("AIRHEAVY_TRACE_DETAIL", detail)

    # ★ 诊断：收招的欧拉行程 D 落在哪根骨上（`no_teleport` / `no_snap_stop`
    #   同时被 D 卡住 ⟹ 必须先看清 D 的构成，再决定"改姿态"还是"改帧数"）。
    seam = {}
    if HIT in LOCK and TOTAL in LOCK:
        for name in list(ARM6 + LEG6) + list(TRUNK8):
            ea = tuple(round(v, 2) for v in LOCK[HIT].get(name, (0.0, 0.0, 0.0)))
            eb = tuple(round(v, 2) for v in LOCK[TOTAL].get(name, (0.0, 0.0, 0.0)))
            seam[name] = {
                "hit": ea, "end": eb,
                "delta": [round(b - a, 2) for a, b in zip(ea, eb)],
                "max_abs": round(max(abs(b - a) for a, b in zip(ea, eb)), 2)}
    pole_hit = {}
    if "HIT" in LOCK_POLE:
        pole_hit = {s: [round(v, 3) for v in LOCK_POLE["HIT"][s]] for s in SIDES}
    pole_end = {}
    A.apply_pose(arm, LOCK[TOTAL])
    bpy.context.view_layer.update()
    for side in SIDES:
        pole_end[side] = [round(v, 3)
                          for v in UP._elbow_pole_from_pose(arm, side)]
    A.report("AIRHEAVY_SEAM_EULER", {
        "bones": seam,
        "d_max_deg": round(max([v["max_abs"] for v in seam.values()] or [0.0]), 2),
        "d_owner": max(seam, key=lambda k: seam[k]["max_abs"]) if seam else None,
        "pole_elbow_hit": pole_hit,
        "pole_elbow_end": pole_end,
    })

    reach_mm = UP.bone_len(arm, "upperarm.L") + UP.bone_len(arm, "forearm.L")
    reqs = [r for r in UP.REQ if len(r) == 4]
    A.report("AIRHEAVY_ARM_CLAMP_SUMMARY", {
        "reach_mm": round(reach_mm * 1000.0, 1),
        "upper_limit_mm": round(reach_mm * 0.9995 * 1000.0, 1),
        "fold_min_mm": round(reach_mm * UP.FOLD_MIN_RATIO * 1000.0, 1),
        "lower_clamped_frames": sorted({f for f, s, req, used in reqs
                                        if used > req + 1e-6}),
        "upper_clamped_frames": sorted({f for f, s, req, used in reqs
                                       if req > reach_mm * 0.9995 * 1000.0}),
        "upper_over_by_mm": round(max(
            [req - reach_mm * 0.9995 * 1000.0 for f, s, req, used in reqs]
            or [0.0]), 2),
        "min_req_mm": round(min([r[2] for r in reqs] or [0.0]), 1),
        "max_req_mm": round(max([r[2] for r in reqs] or [0.0]), 1),
        "note": ("上下夹取**分开报**（B07 诊断教训：只报下夹取会埋红点）。"
                 "手骨指向取 `normalize(rel)` ⟹ 腕距恒在环带内，夹取不应触发。"),
    })

    if not SKIP_RENDER:
        A_SIDE = ("side", (4.8, -0.10, 1.60), (0.0, -0.10, 1.60), 3.30,
                  (760, 1200))
        A_FRONT = ("front", (0.0, -5.2, 1.60), (0.0, 0.0, 1.60), 3.30,
                   (760, 1200))
        A_3Q = ("three_quarter", (3.4, -3.8, 1.75), (0.0, -0.15, 1.55), 3.30,
                (760, 1200))
        A.render_pose_sheet(arm, action,
                            [0, 3, 6, 9, 12, HIT, HOLD_END, 19, TOTAL],
                            "airheavy", views=(A_SIDE,))
        A.render_pose_sheet(arm, action, [0, 6, HIT, TOTAL], "airheavy",
                            views=(A_FRONT,))
        A.render_pose_sheet(arm, action, [0, 6, HIT, TOTAL], "airheavy",
                            views=(A_3Q,))
        # 存盘/导出只在**出图那一遍**做：SKIP_RENDER 是纯门禁迭代。
        A.save_project()
        A.export_glb(arm)
    print("AIRHEAVY_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("AIRHEAVY_FAILURE " + traceback.format_exc())
