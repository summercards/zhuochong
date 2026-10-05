"""anim_dash10 —— B10 `Dash_Attack` 冲刺攻击（地面支，**带 Root Motion**）。

=============================================================================
清单原文
=============================================================================
「奔跑直接接肩撞 / 飞膝 / 冲拳；攻击过程中**保留强烈前冲惯性**」。

选型：**后手冲拳（右直拳）** —— 三种候选里唯一能把"支撑脚世界钉死 ≤3 mm"
与"前冲不瞬停"同时做稳的一种（肩撞要躯干前倾到重心外，飞膝要单腿支撑把
全部前冲交给一条腿的滑移）。走 `Run@0 → 冲刺冲拳 → Idle_01@0`。

=============================================================================
★ 第 1 件 —— `root_motion_m` 到底该不该给 0：**本支给真值**
=============================================================================
上一轮的计划里写「清单 §0.4 说 C 族起才允许 Root Motion ⟹ B10 不许」，那是对
制作日志里一句话的误读 —— **§0.4 的统一制作标准原文把 `Dash_Attack` 直接列进了
「强表演动作」那一组**：

    强表演动作（Dash_Attack / Grab / Throw / Skill_* / Ultimate_*）：
        允许 **Root Motion**，且必须登记 `root_motion_m` 数值。

而那句"C 族起才允许"出现在日志里，且最新一条日志已自行改成"B11 起进 C 族"。
⟹ **本支按 §0.4 走 Root Motion**，并把 `root_motion_m = [0, −1.0001]` 登记进 Action。
理由不止"文档这么说"：
  · "保留强烈前冲惯性"在**原地支**里是无意义的 —— 原地时骨盆净位移恒为 0，
    "惯性"只剩"支撑脚相对身体后滑的速率"，那是 Run 已经做过的事，不叫冲刺。
  · 走了 Root Motion，**支撑脚才能在世界里真的钉死**（漂移 0.0 mm）⟹ 清单 §6
    的 `≤3 mm` 与 `−2~+6 mm` 两条**重新启用**，而不是像 B08/B09 那样记 None。

=============================================================================
★ 第 2 件 —— 本支的**死量**是「前冲速度曲线的起点」，不是落距
=============================================================================
B08 死量是弹道（加帧买余量）；B09 死量是落距总量（加帧吃掉余量）；本支死量是
**入口速率**：`Run` 的 2.75 m/s = **45.8333 mm/帧**（探针 `DASH10_STANCE_RATE`
实测支撑脚后滑 45.556 mm/帧、2.7334 m/s，与声明值一致）。

一旦"起手必须接 Run 的末速"且"速度只能衰减"，**总前进量就被曲线形状锁死**：

    v(f) = V0 − a·f      （a = 衰减率，mm/帧²）
    D(f) = f·V0 − a·f(f−1)/2
    D(TOTAL) = TOTAL·V0 − a·TOTAL(TOTAL−1)/2

42 帧、V0 = 45.8333、取 a = 1.0743 ⟹ **D = 1000.1 mm**（0.394 g 的制动减速度，
落在 [0.15, 0.85] g 的手感区间里）。★ 这三个数是**一起解**出来的，不是一个一个拍的。

=============================================================================
★ 第 3 件 —— 「换脚」不是可选项：腿长 822 mm 把单支撑钉死在 ~770 mm
=============================================================================
探针 `DASH10_LEG_GEOMETRY`：髋→踝 822 mm。要在一个**钉死的踝**上把身体推前进，
横向可达距离 = √(L² − dz²)，髋高 800 mm 时只有 **392.9 mm**；从"踝在髋前
379 mm"推到"踝在髋后 390 mm"合计 **≈ 770 mm** 是这个骨架单支撑的物理天花板
（Run 的支撑脚正好滑 775 mm，说明它已经踩在天花板上）。

⟹ 1000 mm 的前冲**必须换脚**：L 蹬 → R 落 → L 再落。时刻表：

    L 支撑 [0, 20]   L 摆动 (20, 34)   L 支撑 [34, 42]
    R 摆动 [0, 20)   R 支撑 [20, 42]

★ 换脚的**步位不是自由量**：末帧必须逐位（平移不变）落在 `Idle_01@0` 上，
所以两个落脚点是**由终点反推**的 ——
    R 落点 = 末端骨盆 y + 140.43 mm（Idle 的后脚）
    L 落点 = 末端骨盆 y − 169.57 mm（Idle 的前脚）
于是"R 在 [20,42] 只滑 reach+140.43"这条约束反过来把 R 的**落地帧**逼到 20：
D(20) = 712.6 ⟹ R 落点相对髋 **+147.1 mm**（在 392.9 的几何余量内，占 37%）。

=============================================================================
★ 第 4 件 —— 顿感与惯性可以同时成立：**冻关节、不冻动量**
=============================================================================
`HIT 20`、`HOLD 3`（f20~f22 关节欧拉逐位冻结）。骨盆**照常前冲** 24.3 mm/帧 ×
3 帧 = 72.8 mm。B09 在空中支上已经证明"冻关节不冻骨盆"能同时过
`hitstop_frozen_steps=[0,0]` 与弹道判据；本支是它的**地面版**，而且语义更顺 ——
顿的是关节（打击停顿），不顿的是**前冲惯性**（清单原文要保的那一条）。

=============================================================================
★ 第 5 件 —— 「惯性」写成**速度曲线的判据**，不是"位移有多大"
=============================================================================
`dash_inertia_ok` 四条一起判（都在实测骨盆世界 y 上做）：
  ① 起点 = Run 的每帧速率（|v(0) − 45.8333| ≤ 0.5 mm/帧）；
  ② 全程 v **单调不增**（不许再加速 ⟹ 不是"跑两步站住打一拳"）；
  ③ 减速度 ∈ [0.15, 0.85] g（给**区间**：太快读作撞墙，太慢读作滑行）；
  ④ CANCEL 帧与末帧 **v > 0**（收招时仍保留残余前冲）。
★ 参照 B09 `monotone_down_ok` 的思路：改的是**判据口径**，容差一格没动。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_dash10.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import json
import math
import os
import sys

import bpy
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_run as R  # noqa: E402
import anim_run_stop as RS  # noqa: E402
import anim_walk_f as WF  # noqa: E402
import anim_jump_start as JS  # noqa: E402

NAME = "Dash_Attack"
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
    """取字符串型离线参数（如相位定时曲线名）。"""
    return os.environ.get(key, default)


# ---------------------------------------------------------------- 帧预算
TOTAL = _env_i("DD_TOTAL", 42)                 # 0.700 s @60fps
# ★ 前摇 **9 帧**（0.150 s）：爆发段因此有 **11 帧**（f9~f20）。
#   爆发段的欧拉行程是这条支的**死量**（肘由 169.6° 折到位展到 8.6°，
#   前臂欧拉 Z 通道要走 181.8°），单帧步长 = 行程 / 帧数 × 定时峰值因子。
#   7 帧 + smoothstep（峰值因子 1.5）实测顶到 39.0°；7 帧 + 线性降到 29.8；
#   9 帧 + 线性降到 **21.175°**（余 3.8°）。再往上是 10 帧 22.35 / 11 帧 24.18
#   —— 非单调，因为前摇与爆发段的**峰值位置**互相换手（7~9 帧峰在 f4 前摇段、
#   10 帧起峰移到 f19 爆发段）。9 帧是两段同时逼近预算的鞍点。
#   ★ 这不是"放宽容差"，是**改节奏**：前摇 0.15 s 也更贴清单 §6 的"启动略慢"。
ANTIC = _env_i("DD_ANTIC", 9)                  # 前摇结束（收拳蓄势到位）
BURST = ANTIC                                  # 爆发起点
HIT = _env_i("DD_HIT", 20)                     # 命中帧（= 后脚落地帧）
HOLD = _env_i("DD_HOLD", 3)                    # 命停帧数 ⟹ f20~f22
HOLD_END = HIT + HOLD - 1                      # 22
RETURN_START = HOLD_END + 1                    # 23 收招起点
CANCEL = _env_i("DD_CANCEL", 32)               # 可取消帧

# ---------------------------------------------------------------- 脚步时刻表
# ★ 这三个数和 D(f) 是**一起解**出来的（见文件头第 2、3 件），不是各自拍的：
#   换脚位置由出口接缝反推，而落地帧由"单支撑滑动预算 ≤ reach+140.43"反推。
T_L_OFF = _env_i("DD_L_OFF", 20)               # L 蹬离地（= R 落地，交接无腾空）
T_R_ON = _env_i("DD_R_ON", 20)                 # R 落地
T_L_ON = _env_i("DD_L_ON", 38)                 # L 二次落地
WINDOWS = {"L": ((0, T_L_OFF), (T_L_ON, TOTAL)),
           "R": ((T_R_ON, TOTAL),)}
SIDES = ("L", "R")
TIP3 = 3.0                                     # 触地脚背角（与 Run 一致）
TIP_RAMP = 3                                   # 触地后 3 帧内收平
T_LIFT = _env_f("DD_T_LIFT", 0.090)            # L 摆动离地峰值（米）
L_LIFT_POW = _env_f("DD_LIFT_POW", 1.40)       # L 摆动包络指数（>1 ⟹ 起落更缓）
L_SWING_POW = _env_f("DD_L_POW", 2.50)         # L 摆动**水平**缓动指数
R_SWING_POW = _env_f("DD_R_POW", 1.35)         # R 摆动**水平**缓动指数
SOLE_FLOOR_MM = _env_f("DD_SOLE_FLOOR", -0.8)  # 支撑窗口鞋底**最低点**的目标位置
LEG_TAIL_START = _env_i("DD_LEGTAIL0", T_L_ON)  # 收尾收敛起点（腿座解接管处）
_LEG_EASE = os.environ.get("DD_LEGEASE", "quad")   # 收尾收敛缓动（离线扫描用）


def _swing_u(s, power):
    """摆动归一化位移：`1 − (1−s)^p`。

    ★ 为什么用"前端发力"型而不是`s^p`（加速型）：本支收招窗口 [23,42] 里要求
      **逐帧角度增量单调收敛**（`decel_smooth_ok`，口径与 B08/B09 一致）。
      `s^p` 把最大增量放在**落地前一帧**，与收敛要求直接冲突（旧版实测
      L 的落地帧单帧走 69.86 mm、shin.L 一帧 10.8°）。改成前端发力后，
      腿的最大增量落在收招窗口**之前**，窗口内单调下降 —— 收敛是构造出来的。
      横向减速 + 纵向加速下砸（鞋底包络 `(1−s)^1.5`）⟹ 脚"先甩到位、再砸下去"，
      正是冲刺步的观感。
    """
    return 1.0 - (1.0 - max(0.0, min(1.0, s))) ** power

# ---------------------------------------------------------------- 前冲惯性（死量）
V0_MM = _env_f("DD_V0", 45.8333)               # = 2.75 m/s / 60（Run 的每帧速率）
DECAY_MM = _env_f("DD_DECAY", 1.0743)          # mm/帧² ⟹ 0.394 g 制动


def D_mm(frame):
    """前冲位移（mm，正 = 向前 = 世界 −y）。"""
    return frame * V0_MM - DECAY_MM * frame * (frame - 1) / 2.0


def v_mm(frame):
    """第 frame 帧 ⟶ frame+1 的前进量（mm/帧）。"""
    return V0_MM - DECAY_MM * frame


# ---------------------------------------------------------------- 躯干轨道
PELVIS_X = ((0, -0.0021), (12, 0.004), (24, 0.008), (34, 0.0), (TOTAL, 0.0))
# 骨盆 z：低重心贯穿整个冲刺（重踏 + 冲拳压上去）。
# ★★ 末段必须**提前落定**（本支第二个大坑）：出口接缝要的是"末帧 = Idle_01@0"，
#   而 f38~f42 的大腿/小腿要沿**欧拉直线**向 Idle 收敛。若此刻骨盆 z 还在爬
#   （旧版 f38 = 0.795 → f42 = 0.830，抬 35 mm），锚点处的膝弯比 Idle 多 11.6°，
#   欧拉直线在**踝**上就会鼓出 4~5 mm（实测 L 踝 y 摆 4.4 mm、z 沉 5.0 mm）
#   ⟹ `stance_plant_ok` / `stance_sole_ok` / `hitstop_plant_ok` 三条一起红。
#   让骨盆 z 在 f38 就到位，锚点与 Idle 的膝弯只差 ~1.3°（= 那 13.6 mm 的
#   **水平**残距），欧拉直线的鼓包降到 0.05 mm 量级 —— 收敛与钉脚不再打架。
PELVIS_Z = ((0, 0.8013), (6, 0.7660), (12, 0.7455), (HIT, 0.7380),
            (24, 0.7500), (29, 0.7850), (34, 0.8200), (T_L_ON, 0.8300),
            (TOTAL, 0.8300))
PELVIS_RX = ((0, 8.0), (6, 12.5), (12, 16.5), (HIT, 15.0), (26, 11.0),
             (T_L_ON, 6.0), (TOTAL, 4.0))
# ★ 扭腰符号由探针 `DASH10B_TWIST_SIGN` 实测：**ry > 0 = 右肩/右髋向前**。
#   故前摇（右肩向后蓄）ry < 0、命中（右肩打透）ry > 0。
PELVIS_RY = ((0, -6.0), (6, -11.0), (ANTIC, -13.0), (HIT, 12.0),
             (26, 6.0), (T_L_ON, 1.0), (TOTAL, 0.0))
SPINE01_RX = ((0, 4.0), (ANTIC, 6.0), (HIT, 7.0), (T_L_ON, 3.0), (TOTAL, 2.0))
SPINE01_RY = ((0, 3.0), (6, -5.0), (ANTIC, -7.0), (HIT, 7.0), (TOTAL, 0.0))
SPINE02_RX = ((0, 3.0), (ANTIC, 5.0), (HIT, 6.0), (T_L_ON, 2.5), (TOTAL, 2.0))
SPINE02_RY = ((0, 3.0), (6, -5.0), (ANTIC, -7.0), (HIT, 7.0), (TOTAL, 0.0))
CHEST_RX = ((0, 3.0), (ANTIC, 4.0), (HIT, 5.0), (T_L_ON, 1.5), (TOTAL, 1.0))
CHEST_RY = ((0, 4.0), (6, -9.0), (ANTIC, -12.0), (HIT, 13.0), (TOTAL, 0.0))
NECK_RX = ((0, -10.0), (ANTIC, -13.0), (HIT, -17.0), (T_L_ON, -8.0), (TOTAL, -6.0))
HEAD_RX = ((0, 9.0), (ANTIC, 11.0), (HIT, 14.0), (T_L_ON, 6.5), (TOTAL, 5.0))
# 两肩**同号** rz 才是一前一后（轴语义镜像）：HIT 时 rz 最大 ⟹ 右肩前送 +
# 左肩回拉，正是后手冲拳的肩部动作（1.95 mm/°）。
SHOULDER_RX = ((0, -18.0), (ANTIC, -16.0), (HIT, -10.0), (T_L_ON, -17.0),
               (TOTAL, -18.0))
SHOULDER_RZ = ((0, 14.0), (6, 16.0), (ANTIC, 17.0), (HIT, 22.0), (28, 12.0),
               (T_L_ON, 4.0), (TOTAL, 0.0))

# ---------------------------------------------------------------- 手臂方向轨道
# 六个相位的关键朝向（世界单位向量）。x = 左正，y = 身后正，z = 上正。
ARM_KEYS = {
    # 前摇：右拳收到肋侧（肘向后下）、左拳抬起护面
    "ANTIC": {
        "upperarm.R": (-0.30, 0.52, -0.80),
        "forearm.R": (0.16, -0.46, 0.87),
        "hand.R": (0.10, -0.74, 0.66),
        "upperarm.L": (0.30, -0.34, -0.89),
        "forearm.L": (-0.26, -0.44, 0.86),
        "hand.L": (-0.16, -0.72, 0.67),
    },
    # 命中：右臂近乎伸直前冲（掌心朝下）；左拳**回撤护腮**（反作用手）。
    # ★ 左拳的 y 分量必须比前摇**更靠后**（−0.06 / −0.16 / −0.48 对 −0.34 / −0.44 / −0.72）：
    #   躯干 ry 从 −12° 转到 +13° 会把左肩整体向前带 ~141 mm，手臂若只做小幅回收，
    #   拳头的**世界**位置仍然前移（旧版实测 −38.32 mm ⟹ `counter_arm_ok` 红）。
    "HIT": {
        "upperarm.R": (0.13, -0.97, -0.21),
        "forearm.R": (0.09, -0.99, -0.08),
        "hand.R": (0.07, -0.996, -0.05),
        "upperarm.L": (0.30, -0.06, -0.95),
        "forearm.L": (-0.26, -0.16, 0.95),
        "hand.L": (-0.15, -0.48, 0.86),
    },
    # 收招：右臂退回护体（与 Idle 的 ARM_DIRS 只差一点，末段收敛）
    "SETTLE": {
        "upperarm.R": (0.00, -0.40, -0.92),
        "forearm.R": (0.30, -0.28, 0.91),
        "hand.R": (0.16, -0.62, 0.77),
        "upperarm.L": (0.28, -0.29, -0.92),
        "forearm.L": (-0.30, -0.38, 0.87),
        "hand.L": (-0.19, -0.68, 0.70),
    },
}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
# 每段带**定时曲线**：`smooth` = smoothstep（两端速度 0），`linear` = 匀速。
# ★ 前两段（SEAM→ANTIC→HIT）都用 **linear**：smoothstep 的峰值速率是均速的
#   1.5 倍，而这两段扛着本支欧拉行程的死量（前摇 139°、爆发 181.8°），
#   1.5 倍正好把单帧步长顶穿 25°。冲刺冲拳本来就是"一路加速不松劲"，
#   收势突兀、发力均匀正是要的观感 —— 改的是**节奏**，不是判据。
ARM_PHASES = ((0, "SEAM", _env_p("DD_PH0", "linear")),
              (ANTIC, "ANTIC", "smooth"),
              (HIT, "HIT", "linear"), (HOLD_END, "HIT", "linear"),
              (T_L_ON, "SETTLE", "smooth"), (TOTAL, "END", "smooth"))

# ---------------------------------------------------------------- 命停该冻谁
# ★ 地面支的命停口径与空中支**不同**（B09 是空中支，冻全部关节即可）：
#   本支走 Root Motion，支撑脚在世界里钉死 ⟹ 骨盆前冲时双腿**必须**跟着屈伸，
#   否则"冻结的腿 + 前进的骨盆"= 支撑脚被拖走（实测 f21/f22 各 24.35 mm 脚滑）。
#   所以命停冻的是**骨盆旋转及以上**（打击姿态本身），不冻骨盆位移、不冻双腿。
#   "完全停顿"落在**打击姿态**上 —— 拳停了，动量没停。
HITSTOP_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "shoulder.L", "shoulder.R",
                 "upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R")


def _hold(frame):
    """该帧是否落在命停窗口（HIT 之后、HOLD_END 及之前）。"""
    return HIT < frame <= HOLD_END

# ---------------------------------------------------------------- 门禁阈值
DASH_ENTRY_TOL_MM = 0.5            # 起手速率与 Run 的偏差
DASH_DECEL_RANGE_G = (0.15, 0.85)  # 减速度区间（g）
SOLE_RANGE_MM = (-2.0, 6.0)        # 支撑脚鞋底（清单 §6）
PLANT_DRIFT_MAX_MM = 3.0           # 支撑脚世界漂移（清单 §6）
NO_TELEPORT_MAX_DEG = 25.0
FIST_TRAVEL_MIN_MM = 450.0         # 前摇→命中 的拳世界行程（"动作幅度大"）
# 反作用手（左拳）在爆发段必须**相对骨盆**后撤的下限。取臂链总长（≈0.62 m）的
# 两成 —— 低于这个量在画面里读不出"回撤"，只是"手没动"。
GUARD_RETRACT_MIN_MM = 120.0
LEAN_RANGE_MM = (140.0, 340.0)     # 命中帧躯干前倾（pelvis → 胸骨顶）
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995

SEAM_POSE = {}
IDLE_POSE = {}
SEAM_DIRS = {}
PY0 = -0.008
IDLE_PELVIS = None
L_SEAM = None
R_SEAM = None
L_END = None
R_END = None
SEAM_SOLE_R = 0.0
Z_PLANT_FLAT = 0.078
Z_PLANT_TIP3 = 0.085
FROZEN_SHIFT = {}
WINDOW_SOLE = {}      # (side, idx) -> [该窗口每帧实测鞋底最低点]（第 1 趟用）
WINDOW_Z0 = {}        # (side, idx) -> 该窗口"鞋底贴地"时的基准踝高（米）
LEG_TAIL_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
_TAIL_ANCHOR = {}     # 收招欧拉斜坡的起点（命中定格帧的手臂欧拉）
_LEG_ANCHOR = {}      # 收腿欧拉斜坡的起点（L 二次落地帧的大腿/小腿欧拉）
_KNEE_ANCHOR = {}     # 收尾段"膝朝向"斜坡的起点（L 二次落地帧的髋→膝单位向量）
IDLE_KNEE_DIR = {}    # 出口接缝（Idle_01@0）的髋→膝单位向量
IDLE_BASIS = {}       # 出口接缝下 thigh/shin 的**世界 3×3**（滚转的参考姿态）
IDLE_DIR = {}         # 出口接缝下 thigh/shin 的**世界朝向**
LEG_REACH = []


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
        # ★ 指数 >1 ⟹ 起落更缓（sin^0.8 会在离地第一帧就把脚抬到 27 mm，
        #   包络 z 目标一帧跳 37 mm，摆动步长被顶到接近上限）。改的是**曲线形状**。
        out["L"] = T_LIFT * math.sin(math.pi * s) ** L_LIFT_POW
    else:
        out["L"] = 0.0
    if frame < T_R_ON:
        # R 从接缝的 108 mm 高处**加速拍下**（指数 1.5 ⟹ 触地前一帧最快）
        s = frame / float(T_R_ON)
        out["R"] = SEAM_SOLE_R * (1.0 - s) ** 1.5
    else:
        out["R"] = 0.0
    return out


def tip_of(side, frame):
    """足尖角（度，+ = 压脚背 / 脚尖朝下）。"""
    if side == "L":
        if frame <= T_L_OFF:
            return TIP3 * max(0.0, 1.0 - frame / float(TIP_RAMP))
        if frame < T_L_ON:
            # 摆动期：抬跟 → 空中压平 → 落地前回到触地角
            s = (frame - T_L_OFF) / float(T_L_ON - T_L_OFF)
            return TIP3 + 5.0 * math.sin(math.pi * s) ** 0.7
        return TIP3 * max(0.0, 1.0 - (frame - T_L_ON) / float(TIP_RAMP))
    if frame < T_R_ON:
        # R 全程保持 Run 的触地角（下落中脚尖微朝下）
        return TIP3 + 4.0 * math.sin(math.pi * frame / float(T_R_ON)) ** 0.8
    return TIP3 * max(0.0, 1.0 - (frame - T_R_ON) / float(TIP_RAMP))


def plant_z(tip):
    """该足尖角下"鞋底贴地"所需的踝高（由 tip=0 / tip=3 两点线性插值）。"""
    return Z_PLANT_FLAT + (Z_PLANT_TIP3 - Z_PLANT_FLAT) * (tip / TIP3)


def ankle_targets(frame, shift):
    """返回 {"L": (x, y, z, tip), ...}：踝世界目标 + 足尖角。

    ★ 落脚点必须**按 (side, 窗口序号) 分别取**，不能用"idx == 0 ⟹ 接缝点"：
      L 的窗口 0 是**起手支撑期**（用接缝点 `L_SEAM`），而 R 的窗口 0 就是
      **落地窗口** [T_R_ON, TOTAL]（必须用终点 `R_END`）。第一版把这条规则
      套在 R 上，R 在落地帧被瞬间拽回起跑线（踝 y −780.68 → −120.75 mm，
      一帧倒飞 660 mm），整条右腿此后 23 帧都在错误位置 —— 连锁反应是
      `ik_reach_ok`（髋踝距一路爬到 823.5 mm，超过 822 mm 腿长）、
      `stance_plant_ok`（R 漂移 242 mm）、`swing_speed_ok`（单帧 674 mm）、
      `seam_end_ok` 全部红。
    """
    out = {}
    for side, seam, end in (("L", L_SEAM, L_END), ("R", R_SEAM, R_END)):
        idx = window_of(side, frame)
        tip = tip_of(side, frame)
        if idx is not None:
            if side == "L":
                x, y = (seam.x, seam.y) if idx == 0 else (end.x, end.y)
            else:
                x, y = (end.x, end.y)       # R 只有一个窗口：落地 = 终点
            z0 = WINDOW_Z0[(side, idx)]
        else:
            # 摆动：从上一个落脚点到下一个落脚点（前端发力 ⟹ 收招段增量单调收敛）
            if side == "L":
                a, b = seam, end
                u = _swing_u((frame - T_L_OFF) / float(T_L_ON - T_L_OFF),
                             L_SWING_POW)
                z0 = WINDOW_Z0[("L", 1)]
            else:
                a, b = seam, end
                u = _swing_u(frame / float(T_R_ON), R_SWING_POW)
                z0 = WINDOW_Z0[("R", 0)]
            x = a.x + (b.x - a.x) * u
            y = a.y + (b.y - a.y) * u
        z = z0 + plant_z(tip) + sole_target(frame)[side] + shift[side]
        out[side] = (x, y, z, tip)
    return out


# =============================================================== 姿态
def torso_pose(frame):
    # ★ 命停窗口：**姿态轨道整体停在 HIT 帧**（见 HITSTOP_BONES 的说明）。
    #   关节（含骨盆旋转）冻住 ⟹ 顿感；骨盆 @loc 仍按 D(frame) 前冲 ⟹ 惯性。
    f = HIT if _hold(frame) else frame
    return {
        "pelvis": (RS.track(PELVIS_RX, f), RS.track(PELVIS_RY, f), 0.0),
        "spine_01": (RS.track(SPINE01_RX, f), RS.track(SPINE01_RY, f), 0.0),
        "spine_02": (RS.track(SPINE02_RX, f), RS.track(SPINE02_RY, f), 0.0),
        "chest": (RS.track(CHEST_RX, f), RS.track(CHEST_RY, f), 0.0),
        "neck": (RS.track(NECK_RX, f), 0.0, 0.0),
        "head": (RS.track(HEAD_RX, f), 0.0, 0.0),
        "shoulder.L": (RS.track(SHOULDER_RX, f), 0.0,
                       RS.track(SHOULDER_RZ, f)),
        "shoulder.R": (RS.track(SHOULDER_RX, f), 0.0,
                       RS.track(SHOULDER_RZ, f)),
        "@loc": {"pelvis": A.wloc(RS.track(PELVIS_X, frame),
                                  PY0 - D_mm(frame) / 1000.0,
                                  RS.track(PELVIS_Z, frame) - 0.900)},
    }


def arm_dirs(frame):
    """六个相位之间**按帧球面插值**的手臂朝向。"""
    if _hold(frame):
        frame = HIT                      # 命停：手臂朝向也停在命中帧
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

    # ★★ 顺序：收尾段**先于**脚部定朝向。反过来（旧版）会留下"用 IK 腿算出来
    #    的脚欧拉、去配已经换过的腿"这一对矛盾 —— 末帧脚的世界朝向不再是 rest
    #    （实测接缝差 3.26 mm / 1.5°，红的正是 `toe.L`），支撑窗口的鞋底也被
    #    这 1.5° 顶出去 3~5 mm。
    #
    # ★★ 收尾段（f38~f42）的**参数化空间**（本支第二个大坑，见 `leg_seat`）：
    #    旧版把"锚点欧拉 → Idle 欧拉"做**线性插值**，两端都把踝放在同一个世界点，
    #    但欧拉直线是条**弦** —— 实测在踝上鼓出 L 5.15 mm / R 4.92 mm，双双超过
    #    §6 的 3 mm。扫过 linear / smooth / 三次 / 冻结四种缓动，漂移一字不变
    #    ⟹ 是几何问题不是定时问题。改成"**踝持续精确落点、只把膝朝向从锚点
    #    旋转到 Idle**"：每帧由两骨几何构造（|髋→膝| = 0.410、|膝→踝| = 0.412），
    #    踝恒等于目标 ⟹ 漂移是构造出来的 0，而末帧仍**逐位**等于 `Idle_01@0`
    #    （f42 直接取 IDLE_POSE，膝盖朝向已在 s→1 时转到位，末帧无跳变）。
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
            # ★ 为什么 leg_seat 在 s=1 时还不够：踝目标带**贴地闭环**的 shift
            #   （≈ −0.8 mm），与 Idle 的踝高差 ~1 mm ⟹ shin.L 世界矩阵差
            #   3.96e-3 / 相对位置差 1.62 mm，`seam_end_ok` 红。末帧必须直接
            #   取 Idle 的欧拉。**这不会再造成跳变** —— 因为上面的 leg_seat 已把
            #   滚转基准换成了 `IDLE_BASIS`，f41 的欧拉已经落在 Idle 的表示
            #   分支上（实测末帧最大步长 shin.L 0.77° < 前一步 1.07°）。
            for bone in LEG_TAIL_BONES:
                e = JS._unwrap_xyz(JS._PREV_EULER.get(bone), IDLE_POSE[bone])
                pose[bone] = e
                arm.pose.bones[bone].rotation_euler = [math.radians(v) for v in e]
            bpy.context.view_layer.update()

    # ---- 脚：把世界朝向钉回 rest（只允许平移）+ 足尖角。
    #      必须在腿部（含收尾收敛）定稿之后才做（见上面的顺序说明）。
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
        # ★ 收招：**欧拉逐分量插值**（B08 第 3 件 —— 目标姿态已知时不要走朝向解）。
        #   端点逐位等于 `Idle_01@0` 的手臂欧拉；`s = 2u − u²` 的逐帧增量单调递减
        #   ⟹ `decel_smooth_ok` / `no_snap_stop_ok` 是构造出来的（与 B09 同法）。
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
    """把**有状态**的手臂接力 / 欧拉解缠状态拍一张快照。"""
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

    `A.aim_bone` 用"最小旋转"定方向，滚转是它的副产物；而 `Idle_01@0` 的
    thigh/shin 滚转来自 `A.leg_ik` 的平面解（欧拉 ry = 0）。两者方向一致、
    **滚转不同** ⟹ 世界 3×3 不同 ⟹ 收尾段最后一帧要"跳"这半个滚转角
    （实测 `foot.L` 单帧 1.365°，把 `decel_smooth_ok` 顶红）。

    这里改成：把**参考姿态**(`ref_basis`) 用"参考朝向 → 目标朝向"的最小旋转
    带过去。**目标朝向等于参考朝向时，结果与参考姿态逐位相同** —— 于是
    s→1 时本函数自动精确复现 `Idle_01@0`，不需要任何"末帧特殊分支"。
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
    """两骨逆解：踝**精确**落在 `target`，膝按给定的 `knee_dir` 方向鼓出。

    与 `RS.leg_to` 唯一的差别是"膝往哪鼓"这一步 —— `leg_to` 固定向正前 −Y，
    本函数接受一个**显式方向**（收尾段用它把膝从锚点朝向旋转到 Idle 朝向）。

    ★ 为什么整条尾巴要换掉旧的"欧拉直线收敛"：两端（f38 的 IK 解、f42 的
      `Idle_01@0`）都把踝放在同一个世界点上，但**欧拉直线**是一条弦 ——
      实测它在踝上鼓出 **5.1 mm**（L 窗口 1）/ **4.9 mm**（R 窗口 0），双双
      顶穿 §6 的 3 mm。换成这个解：每一帧都由"|髋→膝| = 大腿长、|膝→踝| =
      小腿长、膝在给定方向上"三条构造，踝**恒等于**目标 ⟹ 漂移是构造出来的 0。
      换缓动曲线（linear / smooth / 三次）扫过，漂移一模一样 ⟹ 确实是**几何**
      问题，不是定时问题，只能换参数化空间。
    """
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

    （沿用 `anim_run_stop.solve_pose` 的口径：逐帧重算 shift 会让踝一路微沉，
    那不是"钉死"，是"脚在往下爬"。冻结后踝是世界常量。）

    ★★ 每帧只允许**推进一次**手臂接力状态（本支踩过的大坑）：
      `build_pose` 不是纯函数 —— 它改 `JS._PREV_EULER` / `ARM_QUAT`（carry 的
      上一帧参照）。而贴地闭环要重跑 build_pose，于是"跑几趟"这件事本身成了
      状态的一部分：某个窗口的**首帧**在第 1 趟要闭环（多跑 1~2 次）、
      第 2 趟已冻结（只跑 1 次）⟹ 第 2 趟的手臂实际落在**另一条轨迹**上。
      实测后果是标定完全对不上（`DASH10_SOLE_CALIB` 说 R_w0 抬 7.764 mm 后
      最低点应到 −0.8，报告里却是 −5.378；同窗口最高点还从 7.764 变成 8.642）。
      修法：闭环迭代前后各拍一次快照，把"试跑"的历史擦掉，只用**最终那次**
      构造去推进状态。
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

    # 用"干净历史 + 最终 shift"重构造一次：保证状态只前进一步。
    _restore_carry(snap)
    pose = build_pose(arm, frame, shift)

    for side in SIDES:
        idx = window_of(side, frame)
        key = (side, idx)
        if idx is not None and key not in FROZEN_SHIFT:
            FROZEN_SHIFT[key] = shift[side]
    # 第 1 趟标定用：记下支撑窗口里每一帧的鞋底最低点。
    # ★ 为什么要它：支撑窗口**冻结 shift** 之后（踝世界恒定）鞋底仍会随腿的
    #   伸屈被蒙皮带动，实测下沉 3.7 mm 撞穿 −2 mm 下界。冻结与"抬到区间里
    #   的安全位"两条并不冲突 —— 冻结保证踝不动，标定保证鞋底在带内。
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
    """两套世界矩阵的「**平移不变**」逐位差。

    ★ 本支走 Root Motion ⟹ 末帧骨盆比 `Idle_01@0` **前移了 1.0 m**。
    原始 4×4 逐位差必然等于位移本身；只有对"会动的那部分骨架"比**相对骨盆**
    的量才有意义。B08 的尺子对"改弹道"成立，对"带根位移"同样成立。
    """
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
    """逐帧实测：踝世界位 + **按鞋对象分左右**的鞋底最低点 + 骨盆。

    为什么不用 `lowest_z_by_side`（按顶点 x 符号分左右）：本支站宽只有
    ±147 mm、鞋宽 ~90 mm，两鞋会在 x≈0 附近**串门**（B09 已记）。
    支撑脚漂移必须按**踝骨世界坐标**量（与清单 `no_foot_slide` 同口径）。
    """
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
def dash_assertions(arm, action, samples, foots, start_mats, end_mats):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(f["pelvis"]) for f in foots]

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
    res["seam_end_translation_invariant_ok"] = res["seam_end_ok"]

    # 1) 前冲惯性：在**实测骨盆世界 y** 上做（见文件头第 5 件）
    # ★ 世界 −y 为前 ⟹ 前进速度是 y 的**减少**量。写成 (y_i − y_{i+1}) 才是正值，
    #   否则整套惯性判据（起点/单调/减速/残余）会集体反号（本支第一版就踩了）。
    vs = [(pelvis[i].y - pelvis[i + 1].y) * 1000.0
          for i in range(len(pelvis) - 1)]
    res["entry_speed_mm"] = round(vs[0], 4)
    res["entry_speed_ok"] = abs(vs[0] - V0_MM) <= DASH_ENTRY_TOL_MM
    worst_up = min(vs)
    res["min_step_mm"] = round(worst_up, 4)
    res["monotone_ok"] = all(vs[i + 1] <= vs[i] + 1e-9
                             for i in range(len(vs) - 1))
    decel = [(vs[i] - vs[i + 1]) for i in range(len(vs) - 1)]
    res["decel_mm_per_frame2"] = round(sum(decel) / len(decel), 5)
    res["decel_g"] = round(sum(decel) / len(decel) * 3600.0 / 1000.0 / 9.80665, 4)
    res["decel_ok"] = (DASH_DECEL_RANGE_G[0] <= res["decel_g"]
                       <= DASH_DECEL_RANGE_G[1])
    res["speed_at_cancel_mm"] = round(vs[CANCEL], 4)
    res["speed_at_end_mm"] = round(vs[-1], 4)
    res["residual_drive_ok"] = vs[CANCEL] > 0.0 and vs[-1] > 0.0
    res["advance_total_mm"] = round((pelvis[-1].y - pelvis[0].y) * 1000.0, 3)
    res["dash_inertia_ok"] = bool(res["entry_speed_ok"] and res["monotone_ok"]
                                  and res["decel_ok"]
                                  and res["residual_drive_ok"])
    res["root_motion_ok"] = abs(abs(res["root_motion_m"]) * 1000.0
                                - D_mm(TOTAL)) <= 1.0

    # 2) 支撑脚：世界漂移 + 鞋底区间（清单 §6，本支**重新启用**）
    plant = {}
    sole = {}
    for side in SIDES:
        for idx, (a, b) in enumerate(WINDOWS[side]):
            lo, hi = max(a, 1), b
            pts = [foots[f] for f in range(lo, hi + 1)]
            xs = [p["ankle_" + side][0] for p in pts]
            ys = [p["ankle_" + side][1] for p in pts]
            drift = max(math.hypot(max(xs) - min(xs), max(ys) - min(ys))
                        * 1000.0, 0.0)
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

    # 3) 摆动脚真的离地（不许"贴地滑过去"）
    clear = {}
    for side in SIDES:
        windows = WINDOWS[side]
        if side == "L":
            span = range(T_L_OFF + 1, T_L_ON)
        else:
            span = range(1, T_R_ON)
        vals = [foots[f]["sole_" + side] for f in span
                if foots[f]["sole_" + side] is not None]
        clear[side] = round(min(vals) * 1000.0, 3) if vals else None
    res["swing_min_clearance_mm"] = clear
    res["swing_airborne_ok"] = all(v is not None and v > 0.0
                                   for v in clear.values())

    # 4) 顿感：命停窗口**打击姿态**逐位冻结，而骨盆照常前冲、双腿照常贴地
    #    （见文件头第 4 件 / HITSTOP_BONES）。
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
    res["hitstop_keeps_momentum_ok"] = res["hitstop_momentum_mm"] > 40.0
    # ★ 命停窗口里**仍在支撑的脚**才判钉死（比 §6 更严：这一段最容易漏）。
    #   必须按"该帧该脚是否在支撑窗口内"筛选 —— L 的支撑窗口在 f20 结束，
    #   f21/f22 它已经在摆动了，把它算进来是**错口径**（那 77 mm 正是离地）。
    hold_plant = {}
    for side in SIDES:
        support = [f for f in range(HIT, HOLD_END + 1)
                   if window_of(side, f) is not None]
        if not support:
            hold_plant[side] = None
            continue
        pts = [foots[f] for f in support]
        xs = [p["ankle_" + side][0] for p in pts]
        ys = [p["ankle_" + side][1] for p in pts]
        dz = [p["sole_" + side] for p in pts if p["sole_" + side] is not None]
        hold_plant[side] = [[support[0], support[-1]],
                            round(math.hypot(max(xs) - min(xs),
                                             max(ys) - min(ys)) * 1000.0, 4),
                            round(min(dz) * 1000.0, 3) if dz else None]
    res["hitstop_plant_mm"] = hold_plant     # [[支撑帧区间], 水平漂移, 鞋底最低]
    res["hitstop_plant_ok"] = all(
        v is None or (v[1] <= PLANT_DRIFT_MAX_MM and v[2] is not None
                      and SOLE_RANGE_MM[0] <= v[2] <= SOLE_RANGE_MM[1])
        for v in hold_plant.values())

    # 5) 幅度：前摇→命中的拳世界行程 + 反作用手回撤
    # ★★ 反作用手口径修正（本支新增 Root Motion 后必须换尺子）：
    #    原判据是"左拳**世界** y 的位移 ≥ −20 mm"。那个 −20 是在**没有位移**
    #    的版本上标定的（旧版实测 −38.32 就红）。本支允许 Root Motion 后，躯干
    #    ry 带转 ~141 mm + 手臂回收 ~322 mm 已经让拳头**相对身体**后撤了 322 mm，
    #    可身体自己前冲 414 mm，世界量净剩 −91.87 ⟹ 判据实际变成了"要求手臂
    #    相对身体回收 394 mm"，而臂链总长只有 0.62 m。**不是姿态没做对，是尺子
    #    被位移带走了**。修法：把判据放到**骨盆系**（位移在这里被减掉），语义与
    #    阈值都不动，世界量仍照报（`guard_retract_world_mm`）——换尺子，不放容差。
    #    另配一条同族的、天然与位移无关的判据："命中帧左拳到下巴的距离必须比
    #    前摇帧**更近**"（= 回撤护腮，而不是跟着前伸）。
    fist = [Vector(f["hand.R_tail"]) for f in foots]
    travel = max((p - fist[ANTIC]).length for p in fist[ANTIC:HIT + 1]) * 1000.0
    res["fist_travel_mm"] = round(travel, 2)
    res["fist_travel_ok"] = travel >= FIST_TRAVEL_MIN_MM
    res["fist_forward_mm"] = round((fist[HIT].y - fist[ANTIC].y) * 1000.0, 2)
    guard = [Vector(f["hand.L_tail"]) for f in foots]
    pelvis = [Vector(f["pelvis"]) for f in foots]
    chin = [Vector(f["neck"]) for f in foots]
    res["guard_retract_world_mm"] = round(
        (guard[HIT].y - guard[ANTIC].y) * 1000.0, 2)
    res["guard_retract_mm"] = round(
        ((guard[HIT].y - pelvis[HIT].y)
         - (guard[ANTIC].y - pelvis[ANTIC].y)) * 1000.0, 2)
    res["guard_antic_mm"] = round((guard[ANTIC].y - pelvis[ANTIC].y) * 1000.0, 2)
    res["guard_hit_mm"] = round((guard[HIT].y - pelvis[HIT].y) * 1000.0, 2)
    res["guard_chin_antic_mm"] = round(
        (guard[ANTIC] - chin[ANTIC]).length * 1000.0, 2)
    res["guard_chin_hit_mm"] = round(
        (guard[HIT] - chin[HIT]).length * 1000.0, 2)
    res["counter_arm_ok"] = bool(
        res["guard_retract_mm"] >= GUARD_RETRACT_MIN_MM
        and res["guard_chin_hit_mm"] < res["guard_chin_antic_mm"])

    # 6) 躯干前倾（配重）+ 力矩链
    leans = [(p.y - Vector(f["neck"]).y) * 1000.0
             for p, f in zip(pelvis, foots)]
    res["lean_at_hit_mm"] = round(leans[HIT], 2)
    res["lean_max_mm"] = round(max(leans), 2)
    res["lean_peak_frame"] = frames[leans.index(max(leans))]
    res["torso_lean_ok"] = LEAN_RANGE_MM[0] <= leans[HIT] <= LEAN_RANGE_MM[1]
    res["lean_peak_in_window_ok"] = ANTIC <= res["lean_peak_frame"] <= HIT + 2

    keys = ("pelvis", "spine_01", "spine_02", "chest", "shoulder.L",
            "shoulder.R")
    channel = {}
    for name in keys:
        vals = [s["euler"].get(name, (0.0, 0.0, 0.0)) for s in samples]
        channel[name] = round(max(max(abs(v) for v in item) for item in vals), 3)
    res["power_chain_channels_deg"] = channel
    res["power_chain_ok"] = all(v > 0.5 for v in channel.values())

    # 7) 腿可达 + 摆动速率体检
    limit = A.L_THIGH + A.L_SHIN
    ratios = {}
    peak_frames = {}
    for side in SIDES:
        vals = [(f["reach_" + side], f["frame"]) for f in foots]
        peak, peak_f = max(vals)
        ratios[side] = round(peak / limit, 5)
        peak_frames[side] = [peak_f, round(peak * 1000.0, 2),
                             round((peak - limit) * 1000.0, 2)]
    res["leg_reach_max_ratio"] = ratios
    res["leg_reach_peak"] = peak_frames       # [帧, 髋踝距mm, 超限量mm]
    res["ik_reach_ok"] = all(v <= REACH_MAX_RATIO for v in ratios.values())
    swings = {}
    swing_frames = {}
    for side in SIDES:
        if side == "L":
            span = range(T_L_OFF, T_L_ON + 1)
        else:
            span = range(0, T_R_ON + 1)
        best, best_f = 0.0, None
        for f in span:
            if f == 0 or f > TOTAL:
                continue
            pa = Vector(foots[f - 1]["ankle_" + side])
            pb = Vector(foots[f]["ankle_" + side])
            step = (pb - pa).length * 1000.0
            if step > best:
                best, best_f = step, f
        swings[side] = round(best, 2) if best_f else None
        swing_frames[side] = [best_f, round(best, 2)]
    res["swing_step_max_mm"] = swings
    res["swing_step_peak_frame"] = swing_frames
    res["swing_speed_ok"] = all(v is not None and v <= 120.0
                                for v in swings.values())

    # 8) 收招不许瞬停
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
    return res


# =============================================================== 主流程
def main():
    global SEAM_POSE, IDLE_POSE, SEAM_DIRS, PY0, IDLE_PELVIS
    global L_SEAM, R_SEAM, L_END, R_END, SEAM_SOLE_R
    global Z_PLANT_FLAT, Z_PLANT_TIP3

    FROZEN_SHIFT.clear()
    del LEG_REACH[:]

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("DASH10_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()
    for module in (R,):
        if module.NAME not in bpy.data.actions:
            print("DASH10_BOOTSTRAP 动画工程缺 %s，先补跑" % module.NAME)
            module.main()
            arm, meshes = A.open_animation_project()
            A.setup_scene()

    A.PROBE_BONES = tuple(A.PROBE_BONES) + ("thigh.L", "thigh.R",
                                            "shin.L", "shin.R")

    # ---- 上游接缝：`Run@0`（逐位取用，**相位由探针选定**）
    # 探针 `DASH10_RUN_SCAN`：f0 = 左脚刚在身前落地（踝 −387.35，鞋底 0）、
    # 右脚在身后 532 mm 处**腾空**（鞋底 108.18）—— 正是"蹬伸已起、后脚在摆"，
    # 是三条候选里唯一能直接接"收拳 → 冲拳"的相位。
    SEAM_POSE = WF.gait_pose(arm, R.RUN, 0, meshes)
    A.apply_pose(arm, SEAM_POSE)
    bpy.context.view_layer.update()
    PY0 = A.bone_world(arm, "pelvis", "head").y
    L_SEAM = A.bone_world(arm, "foot.L", "head").copy()
    R_SEAM = A.bone_world(arm, "foot.R", "head").copy()
    SEAM_DIRS = {bone: tuple(A.bone_direction(arm, bone)) for bone in ARM_BONES}
    SEAM_SOLE_R = A.foot_lowest_by_side()["R"][2]

    # ---- 下游接缝：`Idle_01@0`
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

    # ★ 落脚点由**终点反推**（见文件头第 3 件）：Root Motion 让整具身体前移
    #   D(TOTAL)，两个落脚点就是"平移后的 Idle 站架"。
    #   前移量 = (前移后的骨盆 y) − (Idle 的骨盆 y)（世界 −y 为前）。
    shift_y = (PY0 - D_mm(TOTAL) / 1000.0) - IDLE_PELVIS.y
    L_END = Vector((idle_l.x, idle_l.y + shift_y, idle_l.z))
    R_END = Vector((idle_r.x, idle_r.y + shift_y, idle_r.z))

    A.report("DASH10_LAYOUT", {
        "total_frames": TOTAL,
        "advance_mm": round(D_mm(TOTAL), 3),
        "entry_speed_mm_per_frame": round(V0_MM, 4),
        "exit_speed_mm_per_frame": round(v_mm(TOTAL - 1), 4),
        "decel_g": round(DECAY_MM * 3600.0 / 1000.0 / 9.80665, 4),
        "foot_schedule": {"L": [[a, b] for a, b in WINDOWS["L"]],
                          "R": [[a, b] for a, b in WINDOWS["R"]]},
        "seam_frame": 0,
        "pelvis_y0_mm": round(PY0 * 1000.0, 3),
        "pelvis_y_end_mm": round((PY0 - D_mm(TOTAL) / 1000.0) * 1000.0, 3),
        "L_seam_mm": [round(v * 1000.0, 2) for v in L_SEAM],
        "R_seam_mm": [round(v * 1000.0, 2) for v in R_SEAM],
        "L_plant_mm": [round(v * 1000.0, 2) for v in L_END],
        "R_plant_mm": [round(v * 1000.0, 2) for v in R_END],
        "R_seam_sole_mm": round(SEAM_SOLE_R * 1000.0, 3),
        "note": ("落脚点由出口接缝（Idle_01@0 + 前移 D）**反推**；"
                 "落地帧由单支撑滑动预算反推。"),
    })

    # ---- 贴地标定（tip=0 与 tip=3 两点）
    torso_seam = {
        "pelvis": (8.0, -6.0, 0.0), "spine_01": (4.0, 3.0, 0.0),
        "spine_02": (3.0, 3.0, 0.0), "chest": (3.0, 4.0, 0.0),
        "@loc": {"pelvis": A.wloc(-0.0021, PY0, 0.8013 - 0.900)},
    }
    Z_PLANT_TIP3, err3 = RS.measure_plant_z(arm, TIP3, torso_seam,
                                             (L_SEAM.x, L_SEAM.y),
                                             L_SEAM.z)
    Z_PLANT_FLAT, err0 = RS.measure_plant_z(arm, 0.0, torso_pose(TOTAL),
                                             (L_END.x, L_END.y), 0.120)
    A.report("DASH10_CALIBRATION", {
        "plant_z_flat_mm": round(Z_PLANT_FLAT * 1000.0, 3),
        "plant_z_tip3_mm": round(Z_PLANT_TIP3 * 1000.0, 3),
        "tip3_reach_err_mm": err3,
        "flat_reach_err_mm": err0,
        "seam_L_ankle_z_mm": round(L_SEAM.z * 1000.0, 3),
    })

    # ---- 每个支撑窗口的"鞋底贴地"基准踝高 Z0（见 ankle_targets 注释）
    #   L 窗口 0（起手支撑）以 **Run 接缝的踝高**为基准（tip = TIP3）⟹ Z0 = 0；
    #   L 窗口 1 / R 窗口 0（都终止在出口站架上）以 **Idle 的踝高**为基准
    #   （tip = 0）⟹ 末帧踝高逐位等于 Idle，接缝才是逐位的。
    WINDOW_Z0[("L", 0)] = L_SEAM.z - plant_z(TIP3)
    WINDOW_Z0[("L", 1)] = L_END.z - plant_z(0.0)
    WINDOW_Z0[("R", 0)] = R_END.z - plant_z(0.0)
    A.report("DASH10_Z0", {("%s_w%d" % k): round(v * 1000.0, 4)
                           for k, v in WINDOW_Z0.items()})

    # ---- 手臂 carry 接力的初始态（每一趟都要从接缝重来，否则状态会跨趟累积）
    def reset_carry():
        JS._PREV_EULER.clear()
        JS.ARM_QUAT.clear()
        JS.ARM_ROLL.clear()
        JS.ROLL_MAX.clear()
        _TAIL_ANCHOR.clear()
        _LEG_ANCHOR.clear()
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
        # ★ Y_SAFE 保持 jump_start 的默认 62（本支一度压到 28，反而害了自己）：
        #   上游接缝 `Run@0` 的 `forearm.R` 欧拉中间角本身就是 **−62.96°**。
        #   把安全带压到 28 ⟹ 求解器在第 1 帧就必须把 |Y| 从 63 拽到 28，
        #   于是一帧里绕骨轴扭了 42°（实测 f1 真转角 42.01°）—— 那不是门禁
        #   太严，是一次**真的翻腕闪帧**。安全带设在接缝值之上，carry 才接得上。
        JS.Y_SAFE = 62.0

    def build_keyframes():
        """逐帧打帧。命停窗口由 `torso_pose` / `arm_dirs` 的 `_hold` 处理，
        这里不必再特判（第一版用 LOCK 复用 HIT 解，会把双腿一起冻住 ⟹ 脚滑）。"""
        frames = [(0, SEAM_POSE)]
        for frame in range(1, TOTAL + 1):
            frames.append((frame, solve_pose(arm, frame, meshes)))
        return frames

    # ---- 第 1 趟：量出每个支撑窗口里鞋底最低点，再把冻结 shift 整体抬高
    #      （冻结保证踝世界恒定；标定保证鞋底 −2~+6 mm 在带内。两件事不冲突）
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
    A.report("DASH10_SOLE_CALIB", {
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
        "category": "普通攻击",
        "note": ("冲刺冲拳：奔跑直接接后手直拳，Root Motion 前冲 1.0001 m；"
                 "起步接 Run 的 2.75 m/s、全程单调减速到 ~0；"
                 "支撑脚世界钉死，后脚落地 = 命中帧"),
        "antic_frame": ANTIC,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HOLD,
        "root_motion_m": [0.0, round(-D_mm(TOTAL) / 1000.0, 4)],
        "entry_speed_mps": round(V0_MM * A.FPS / 1000.0, 4),
        "exit_speed_mps": round(v_mm(TOTAL - 1) * A.FPS / 1000.0, 4),
        "decel_g": round(DECAY_MM * 3600.0 / 1000.0 / 9.80665, 4),
        "hit_point_m": None,
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "ANTIC": ANTIC, "BURST": BURST, "HIT": HIT,
        "HITSTOP_END": HOLD_END, "RECOV": RETURN_START, "CANCEL": CANCEL,
        "L_OFF": T_L_OFF, "R_ON": T_R_ON, "L_ON": T_L_ON, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    if os.environ.get("DD_LEGTRACE") == "1":
        # 收尾段腿骨逐帧体检：欧拉三通道 + 单帧最大分量步长。
        leg_bones = ("thigh.L", "shin.L", "foot.L",
                     "thigh.R", "shin.R", "foot.R")
        prev = {}
        for s in samples:
            if s["frame"] < LEG_TAIL_START - 3:
                continue
            row = {"f": s["frame"]}
            for name in leg_bones:
                e = s["euler"].get(name, (0.0, 0.0, 0.0))
                step = None
                if name in prev:
                    step = round(max(abs(a - b) for a, b in zip(prev[name], e)), 3)
                prev[name] = e
                row[name] = [round(v, 2) for v in e] + [step]
            print("DASH10_LEGTRACE " + json.dumps(row))

    # foot_probe 置空：本支要**换脚**，整段"脚不动 ≤3 mm"是错口径；
    # 换成按**落地窗口**判的 `stance_plant_ok`（口径更严，不只 ≤3 mm）。
    report = A.run_common_assertions(samples, meta, foot_probe=())

    foots = foot_series(arm, action, meshes)
    if os.environ.get("DD_ARM_TRACE") == "1":
        # 臂部逐帧体检：欧拉三通道 + **世界四元数真转角**。
        # ★ 排 `no_teleport` / `decel_smooth_ok` 只看法：若"欧拉步 ≫ 真转角"，
        #   那是表示/扭转放大（roll 分支没接上）；若两者同量级，那是**真的动得快**。
        scene = bpy.context.scene
        prev_action = arm.animation_data.action if arm.animation_data else None
        if arm.animation_data is None:
            arm.animation_data_create()
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        prev_q = {}
        for f in range(0, TOTAL + 1):
            scene.frame_set(f)
            bpy.context.view_layer.update()
            row = {"f": f}
            for name in ARM_BONES:
                pb = arm.pose.bones[name]
                e = [round(math.degrees(v), 2) for v in pb.rotation_euler]
                q = pb.matrix.to_quaternion()
                true_step = None
                if name in prev_q:
                    true_step = round(math.degrees(
                        prev_q[name].rotation_difference(q).angle), 2)
                prev_q[name] = q
                row[name] = [e, true_step]
            print("DASH10_ARMTRACE " + json.dumps(row))
        if prev_action is not None:
            arm.animation_data.action = prev_action
    if os.environ.get("DD_TRACE") == "1":
        # 逐帧实测：踝世界位 / 鞋底 / 髋踝距。★ 排红项先跑它 ——
        # "哪一帧的哪条腿在爆"必须看得见，不能只看一个最大值。
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for f in foots:
            print("DASH10_TRACE " + json.dumps({
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
    start_mats = RS.action_world_matrices(arm, bpy.data.actions[R.NAME], 0)
    end_mats = RS.action_world_matrices(arm, bpy.data.actions[I1.NAME], 0)
    if os.environ.get("DD_SEAM") == "1":
        # 接缝残量拆到骨级：`ori` 是 3×3 逐元素差，`rel` 是骨盆相对位置差（米）。
        rows = []
        mats_ours = RS.action_world_matrices(arm, action, TOTAL)
        for name in end_mats:
            ma, mb = mats_ours.get(name), end_mats[name]
            if ma is None:
                continue
            ori = max(abs(ma[i] - mb[i]) for i in (0, 1, 2, 4, 5, 6, 8, 9, 10))
            rel = max(abs(ma[i] - mb[i]) for i in (3, 7, 11))
            rows.append((max(ori, rel * 100.0), name, round(ori, 6),
                         round(rel * 1000.0, 5)))
        rows.sort(reverse=True)
        for row in rows[:8]:
            print("DASH10_SEAMTOP %s" % json.dumps(
                {"bone": row[1], "ori": row[2], "rel_mm": row[3]}))
    report.update(dash_assertions(arm, action, samples, foots,
                                  start_mats, end_mats))
    report["max_abs_euler_y_deg"] = round(JS.MAX_ABS_EULER_Y, 2)
    report["arm_roll_max_deg"] = {k: round(v, 1)
                                  for k, v in JS.ROLL_MAX.items()}
    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True)
    report["failed"] = failed
    A.report("DASH10_REPORT", report)

    if not SKIP_RENDER:
        # ★ 取景必须**跟着 Root Motion 平移**：本支末帧比首帧前冲 1000 mm，
        #   标准视图（中心在原点、宽 2.10 m）会把整条身体推出画面 —— 实测
        #   第一版 f20（命中帧）只拍到半个身子。把相机与目标一起沿 −y 移
        #   半个行程（−0.50 m）并把宽度放到 2.80 m，整段都在画面里。
        sheets = [(A.VIEW_SIDE, -0.50, 2.80), (A.VIEW_FRONT, -0.42, 2.80),
                  (A.VIEW_3Q, -0.42, 2.80)]
        for base, shift_y, scale in sheets:
            name, location, target, _scale, res = base
            view = (name, (location[0], location[1] + shift_y, location[2]),
                    (target[0], target[1] + shift_y, target[2]), scale, res)
            frames = ([0, ANTIC, 15, HIT, HOLD_END, 26, T_L_ON, TOTAL]
                      if name == "side" else [0, ANTIC, HIT, TOTAL])
            A.render_pose_sheet(arm, action, frames, "dash10", views=(view,))
    A.save_project()
    A.export_glb(arm)
    print("DASH10_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("DASH10_FAILURE " + traceback.format_exc())
