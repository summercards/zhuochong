"""anim_death —— E10 `Death` 死亡（E 族第 10 支 / 全项目第 66 支）。

清单原文：「与普通击倒区分，最终必须进入**稳定尸体 Pose**」。

★★★ 本支与 E09 `Defeat` 的**结构性差别**（开工前想清楚，逐条落地）
    E09 = 「战败但**活着**」：跪落 → 前扑伏地（**俯卧**）→ 之后**必须有呼吸证据**。
    E10 = 「**死亡**」：直接后倒（**无跪姿段**）→ 背/臀触地一次 → **仰卧**尸僵姿，
          末段 60→120 **零微动**（尸体不呼吸）。
    ⟹ 两者的可分性**必须被量出来**，不能靠"看起来不一样"：
       `dth_distinct_from_e09_ok`（57 骨世界矩阵，最大朝向差 ≥ 15°；实测 **175.9°**）。

★★★ 本支唯一的新判据族：`dth_zero_motion_ok`
    「零微动」必须是**可失败的断言**，否则"尸体"与"躺着不动"无法区分。
    载体 = **与 E09 呼吸同一根探针**（胸骨顶 = `neck` = chest.tail 的世界 z），
    窗口 = `[SETTLE_TAIL, END]` = [60, 120]（尸僵窗口）。
    判据 = 幅值 ≤ **1.0 mm** 且 过零 ≤ **1**。
    ★ 为什么是同一根探针：E09 用它在同窗口量出 **5~34 mm 的呼吸**；
      E10 用同一根探针量出 **0 mm** ——**同一把尺子**才是可分性的证明。
    守卫 = `E10_TP_MICROMOTION=1`（在尸僵窗口注入残余微动）⟹ 必须见红。

★★★ 开工第一件测量（`probe_e10_baseline.py` / `_probe_e10_legblend.py` /
    `_probe_e10_solver.py`，三份都是实测，不是公式推的）
    ① 起点 = `Idle_01@0` **逐位**（不是 E09 的伏地终姿）。
    ② ★ 纯欧拉混合在「站立 → 仰卧」之间**不是合法的链插值**：
       `_e10_legblend.log` 实测 t=0.1 鞋底就掉到 **−92.81 mm**、踝自身入地 −13 mm，
       t=0.5 最深 **−239.43 mm**。⟹ 直接 `A.blend` 过来必红。
    ③ ★ 解法 = **世界空间两骨解 + 世界极点**（`leg_solve`）：
       极点取「**骨盆局部 −Y 的世界方向**」= 绕世界 X 转 `pelvis.rx` 后的 (0,−1,0)。
       站架时极点 ≈ (0,−1,0)（膝朝前）；仰卧时 ≈ (0,0,+1)（膝朝**上**）。
       这正是 `leg_ik` 的语义，但**没有小角假设**（`leg_ik` 的 `tilt_deg` 在 rx=−86 时失效）。
       `_e10_solver.log` 实测：站架下解算器复现 `Idle_01@0` 的膝位 **误差 0.19 mm**
       （方向差 1.45°，是**纯绕骨轴滚转** —— 膝位误差 0.19 mm 就是证据）；
       仰卧下踝位误差 **0.13 mm**。
    ④ ★ 仰卧的 `neck_rx / head_rx` 必须**取负**（后仰）：`+rx` 是把下巴往胸口收，
       `−rx` 才是后脑勺落地。（E09 俯卧是 +24/+14，两者符号相反。）
    ⑤ ★ 脚的外翻（绕**世界 Y** 的滚转）在仰卧时才有意义 —— E09 文件里明说
       「脚的自然翻倒留给 E10 `Death`」，本支把它落地：`foot_roll → 45°`。

★★★ 时间轴（120 帧 / 2.0 s，沿用 E01 登记的 E 族上界）
    f0  ──10──▶ 前摇（失去支撑、重心后倒；**无跪姿段** —— `dth_no_kneel_ok` 盯着）
    f10 ──26──▶ **重摔**（16 帧线性下落，背/臀触地）⟹ `[26, 30]` **4 帧完全冻结**
    f30 ──40──▶ **回弹**（头/四肢二次落地、惯性、不许瞬停 —— `dth_rebound_ok`）
    f40 ──60──▶ 沉降（速度衰减到 0，`dth_settle_ok`）
    f60 ──120─▶ **尸僵稳定**（`dth_zero_motion_ok` 的判据窗口）
    ★ 本支是**单段重摔** ⟹ 只有**一个** hitstop 窗口（E09 有两个）。
    ★ 清单原文写「前摇 0→14、命中帧 = 20」，本支改成「0→10 / 命中帧 26」——
      理由在下面 `ANTIC_END / LAND` 的注释里（**继承容差 `dft_limb_step_ok`
      60 mm/帧**把坠落段的加速度上限封死了），**不是**为了好看放宽容差。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_death.py
    SKIP_RENDER=1     只跑门禁不渲图（迭代用）
    E10_TRACE=1       逐帧打印包络 / 最低件 / 膝踝脚 / 头高

反向验证（`_rv_e10.sh`，十组，每组都必须**真的见红**）：
    E10_TP_SEAM_ZERO=1   ① 首帧改零位          ⟹ `dth_seam_in_ok`
    E10_TP_NOFALL=1      ② 抽掉后倒主驱动      ⟹ `dth_supine_ok`
    E10_TP_MICROMOTION=1 ③ 尸僵窗注入残余微动   ⟹ `dth_zero_motion_ok`（本支新判据）
    E10_TP_NOHITSTOP=1   ④ 冻结窗内姿态漂移    ⟹ `dth_hitstop_ok`
    E10_TP_SINK=1        ⑤ 尸体整体下沉 60 mm  ⟹ `dth_body_ground_ok`/`dth_no_penetration_ok`
    E10_TP_KNEEPLUNGE=1  ⑥ 膝极点翻向下       ⟹ `dth_knee_path_ok`
    E10_TP_LIMBJUMP=1    ⑦ 踝目标注入 50 mm 尖峰 ⟹ `dth_limb_step_ok`
    E10_TP_KNEEL=1       ⑧ 前摇段注入跪姿      ⟹ `dth_no_kneel_ok`
    E10_TP_SNAP=1        ⑨ 沉降段改成瞬停      ⟹ `dth_settle_ok`
    E10_TP_PRONE=1       ⑩ 尸体翻成**俯卧**    ⟹ `dth_supine_ok`
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A              # noqa: E402
import anim_idle_01 as IDLE       # noqa: E402
import probe_d01_guard as PD      # noqa: E402
import probe_e10_baseline as PB   # noqa: E402

NAME = "Death"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_SET = set(ARM_BONES)
ARM_LEN_UP = 0.328
ARM_LEN_LO = 0.224 + 0.098
REACH_MAX_RATIO = 0.9995

# =============================================================== 时间轴
TOTAL = 120
START = 0
END = 120
# ★★★ 与清单 §2 的两处**实测修正**（清单原文写「前摇 0→14、命中帧 = 20」）：
#   ① **命中帧 20 → 26、坠落段 6 帧 → 16 帧**。理由不是观感，是**继承来的容差**
#      算出来的：清单 §1 ④ 要求「复用 `dft_limb_step_ok`（60 mm/帧）**不改容差**」。
#      骨盆从 f10 的 (y 0.075, z 0.808) 落到 LAND 的 (0.470, 0.152)，
#      位移 |Δ| = **0.7657 m**。逐帧下界 = 0.7657 / 0.060 = **12.8 帧**。
#      6 帧 ⟹ 128 mm/帧（首跑实测膝单帧 **146.88 mm**，直接红）；
#      14 帧 ⟹ 54.7 mm/帧（第三~五跑实测膝峰值 **58.60 mm @ f23**，只剩 2.3% 余量
#      —— 因为**刚性平移本身就占掉 54.7/60 = 91%**，腿形变化再吃掉 3.9 mm）；
#      16 帧 ⟹ **47.9 mm/帧**，实测膝峰值降到 **52.0 mm**（余量 13%）。
#      ⟹ 「加速下落」的**加速度上限是被这条容差封死的**，不是没做，是做了就红：
#        从 0.69 m 高自由落体的末速 = √(2·9.8·0.69) = **3.68 m/s** = 61.4 mm/帧，
#        本身就**超出** E09 容差（60 mm/帧 = 3.6 m/s）。所以坠落段只能取**线性**，
#        代价是读起来接近匀速；补偿 = 4 帧完全冻结 + 头/四肢**二次落地**
#        （`dth_rebound_ok`）把「重」做在**命中的那一下**，而不是下落过程。
#   ② 窗宽不变：`LAND_HOLD − LAND = 4`（清单 §6：2~4 帧完全冻结）。
ANTIC_END = 10        # 前摇末（失去支撑、重心后倒；无跪姿）
LAND = 26             # **命中帧**：背/臀触地
LAND_HOLD = 30        # 触地定格末（4 帧完全冻结）—— [LAND, LAND_HOLD]
REBOUND_TAIL = 40     # 回弹末（头/四肢二次落地）—— 清单 §2 的 40
SETTLE_TAIL = 60      # 沉降末 = 尸僵窗口起点 —— 清单 §2 的 60
LEG_TAIL = 46         # 腿的包络到顶（踝最后才滑到位 ⟹ 腿在回弹段被**拉直**）
LEG_FALL_SHARE = 0.42  # 坠落段（`ANTIC_END`→`LAND`）先走完的水平滑移比例（见 leg_env）
FOOT_TAIL = 46        # 脚的俯仰/外翻包络：**离地之后**才开始（落地前脚仍踩平）
ARM_LIFT_TAIL = LAND  # 臂被惯性甩到最高（= 命中帧 ⟹ 触地时双臂在**头顶上方**）
ARM_TAIL = 48         # 臂落回地面
# 头**滞后**：主落体到 `REBOUND_TAIL` 走完 `HEAD_MAIN`，余量 `1−HEAD_MAIN`
# 在沉降段以 **(1−x)²** 收尾（速度线性衰减到 0）。
# ★ 为什么不是 1.0：若头在 `REBOUND_TAIL` 就完全到位，沉降窗内「在动的帧数」= 0
#   （`dth_settle_ok` 要求 ≥12）；若余量太大（如 0.10），`(1−x)²` 的末帧步长
#   = 0.10×1340×(1/20²)×... 会顶破 `SETTLE_TAIL_MAX_MM`（0.5 mm）与
#   `SETTLE_PEAK_MAX_MM`（12 mm）。0.04 是**两头都过**的解（实测末帧 ≈0.13 mm，
#   峰值 ≈5.2 mm，在动帧数 19）。
HEAD_MAIN = 0.96
TORSO_POW = 1.35      # 躯干欧拉混合的加速指数（骨盆**单独**走线性，见 pelvis_curve）

# =============================================================== 尸体姿（实测）
# `probe_e10_baseline.py` 四段定标（颈头 → 骨盆 z×腿 → 脚 → 臂）扫出的终值。
# 逐件最低 z（`E10_FINAL_LOW20`）：Hair_Mass −4.8 / Shoe_Sole −0.18 /
# Jacket_Vent 4.2 / Hand_Palm 5.13 / Suit_Torso 7.88 / Head 11.68
# ⟹ 全部落在 `dth_body_ground_ok` 带 [−6, +8] 内或紧邻。
TERM_KW = dict(pz=0.141, leg_dz=-0.06, foot_pitch=-15.0, foot_roll=45.0,
               arm_out=0.50, arm_fwd=0.10, wrist_z=0.055,
               neck_rx=-14.0, head_rx=-11.0, prx=-86.0)

# 尸体末姿的臂**世界方向**（`E10_TERM_DIRS` 实测；左肩为基准，右侧镜像 x）。
TERM_DIRS = {
    "upperarm.L": (0.98002, -0.19600, 0.03375),
    "forearm.L": (0.79711, -0.15942, -0.58241),
    "hand.L": (0.98058, -0.19612, 0.0),
    "upperarm.R": (-0.98002, -0.19600, 0.03375),
    "forearm.R": (-0.79711, -0.15942, -0.58241),
    "hand.R": (-0.98058, -0.19612, 0.0),
}
BASE_DIRS = dict(IDLE.ARM_DIRS)

# ★★★ 臂的**中间态**：被惯性甩到最高（触地那一刻双臂还在**头顶上方**）
# 为什么必须有这一个中间方向：清单 §1 要求「起步慢、命中重、有惯性」。
# 后倒时肩先降到 ~0.25 m 才触地，如果臂此时还在朝「地面平铺」（= `TERM_DIRS`）
# 插值，肩已贴地而臂指下方 ⟹ 袖子**从地面穿过去**（首跑实测 f20 `Sleeve_R`
# 低到 **−90.3 mm**，`dth_no_penetration_ok` 红）。
# 物理上也对：向背后倒的人，双臂是被**甩起来**的，落地后才摊到两侧。
#  阶段 1 `[ANTIC_END, LAND]`：BASE_DIRS → LIFT_DIRS（甩起）
#  阶段 2 `[LAND, ARM_TAIL]` ：LIFT_DIRS → TERM_DIRS（摊到地面）
# ★ 阶段 1 跨 14 帧转 ~128° ⟹ 峰值 ≈ 1.5×9.1 = 13.7°/帧 < `no_teleport` 25°/帧。
LIFT_DIRS = {
    "upperarm.L": (0.42, -0.26, 0.87),
    "forearm.L": (-0.05, -0.32, 0.946),
    "hand.L": (-0.10, -0.42, 0.90),
    "upperarm.R": (-0.42, -0.26, 0.87),
    "forearm.R": (0.05, -0.32, 0.946),
    "hand.R": (0.10, -0.42, 0.90),
}

# =============================================================== 骨盆轨迹（实测/设计）
# ★ 为什么骨盆不跟着 `A.blend` 走直线：站立 → 仰卧 是**绕脚踝的圆弧**，
#   直线会让重心在 f10 前后穿地。(y, z, rx) 逐段给定，ease 标在**段首**。
# ★ 坠落段 `[ANTIC_END, LAND]` 必须**整体线性**，而且键位要**等分**（不是只把每段
#   标 `lin`）。第二跑的实测教训：段内虽 `lin`，但**段与段斜率不同**
#   （f10→14 = 23 mm/帧、f14→19 = 47 mm/帧、f19→24 = 65.6 mm/帧）⟹ 末段单帧
#   骨盆 z 掉 **66 mm**，髋随之下 72.5 mm，`dth_limb_step_ok`（60 mm/帧）在
#   f24 报 **74.60 mm @ knee.R**。
#   改**等分**（4 帧一档，共 16 帧）后骨盆单帧位移 = |Δ(0.0247, −0.041)| = **47.9 mm**
#   ⟹ 膝峰值实测 **52 mm**（余量 13%）；上一版 14 帧等分则是 54.7 mm ⟹ 膝峰值
#   实测 **58.60 mm**，只剩 2.3% 余量，因为**刚性平移本身就吃掉 91% 的容差**。
#   落体的"重"由冻结窗与二次落地给，不再靠下落的加速度。
PELVIS_KEYS = (
    # frame, (world_y, world_z, rx_deg), ease_of_this_segment
    (0, (0.000, 0.830, 4.0), "lin"),
    (6, (0.025, 0.826, 0.5), "lin"),
    (10, (0.075, 0.808, -7.0), "lin"),        # = ANTIC_END ⟹ 刚失去支撑
    (14, (0.17375, 0.644, -24.75), "lin"),
    (18, (0.2725, 0.480, -42.5), "lin"),
    (22, (0.37125, 0.316, -60.25), "lin"),
    (26, (0.470, 0.152, -78.0), "lin"),       # = **命中帧**（背/臀触地）
    (30, (0.470, 0.152, -78.0), "lin"),       # = 冻结窗末（逐位相同 ⟹ 见 death_pose）
    (34, (0.545, 0.143, -83.5), "smooth"),
    (40, (0.605, 0.140, -85.2), "smooth"),    # = REBOUND_TAIL
    (60, (0.640, 0.141, -86.0), "smooth"),    # = SETTLE_TAIL（尸僵起点）
    (120, (0.640, 0.141, -86.0), "smooth"),   # = 尸僵 ⟹ 逐位冻结
)

KNEEL_POW = 1.7

# =============================================================== 阈值
BODY_BAND = (-6.0, 8.0)           # 尸体触地带（**沿用 E09 口径与容差**）
PENETRATION_MIN_MM = -8.0         # 全程任一帧不许低于（沿用 E09）
KNEE_RADIUS_MM = 104.7            # 膝网格半径（沿用 E09 `KNEE_Z_FALL` 实测值）
KNEE_PATH_TOL_MM = 4.0            # 膝关节 z 允许低于目标 4 mm（沿用 E09）
LIMB_STEP_MAX_MM = 60.0           # 膝/踝单帧世界位移上限（沿用 E09）
HITSTOP_MAX_DEG = 0.01
FINAL_ELEM_MAX = 1e-6
SEAM_POS_MAX_MM = 0.01
SEAM_DIR_MAX_DEG = 0.05
NO_TELEPORT_DEG = 25.0
NO_SNAP_END_DEG = 6.0
CLIP_MAX_MM = 0.0
LEG_THIGH_R = 0.105
LEG_SHIN_R = 0.095
PHASE_MATRIX_STEP_DEG = 25.0
# ⑬ 可达性：踝**真的到了设计目标**（不是"髋踝距离"——那个被解算器截断封死）
LEG_REACH_RESID_MAX_MM = 2.0
FULL_EXT_RATIO_MAX = 1.0
# ① ★ 本支新判据：零微动（尸体不呼吸）
ZERO_MOTION_MAX_MM = 1.0
ZERO_MOTION_MAX_CROSS = 1
# ② 前摇无跪姿段：膝关节世界 z 的下限（跪姿实测膝 z ≈ 104.7；站架 ≈ 487）
NO_KNEEL_MIN_KNEE_MM = 300.0
# ③ 仰卧判定
SUPINE_AXIS_MIN = 0.90            # 躯干长轴 |y| 分量（仰卧实测 0.99756）
SUPINE_HEAD_GAP_MM = 8.0          # 后脑勺（Hair_Mass）须**低于**头（Head）
SUPINE_PELVIS_MAX_MM = 200.0      # 骨盆贴地（实测 141）
# ④ 与 E09 的可分性
DISTINCT_MIN_DEG = 15.0
# ⑤ 回弹 / 沉降
REBOUND_HEAD_MIN_MM = 40.0        # 躯干触地后头还要再落这么多（二次落地）
SETTLE_PEAK_MAX_MM = 12.0         # 沉降段单帧头部位移上限（不许瞬停）
SETTLE_TAIL_MAX_MM = 0.5          # 到 `SETTLE_TAIL` 时头必须已经停住
SETTLE_MIN_MOVING_FRAMES = 12     # 沉降段「在动」的帧数下限（动作是铺开的）

# =============================================================== 取景
VIEW_DTH_SIDE = ("side", (4.6, 0.30, 0.62), (0.0, 0.30, 0.62), 2.60, (1000, 700))
VIEW_DTH_FRONT = ("front", (0.0, -5.2, 0.62), (0.0, 0.30, 0.62), 2.60,
                  (1000, 700))
VIEW_DTH_3Q = ("three_quarter", (3.4, -3.2, 1.40), (0.0, 0.30, 0.45), 2.60,
               (1000, 700))


# =============================================================== 反向验证旋钮
def _b(key):
    return os.environ.get(key, "0").strip() not in ("", "0", "false", "False")


SEAM_ZERO = _b("E10_TP_SEAM_ZERO")
NO_FALL = _b("E10_TP_NOFALL")
MICROMOTION = _b("E10_TP_MICROMOTION")
MICROMOTION_MM = 3.0
NO_HITSTOP = _b("E10_TP_NOHITSTOP")
SINK = _b("E10_TP_SINK")
SINK_MM = 60.0
KNEE_PLUNGE = _b("E10_TP_KNEEPLUNGE")
LIMB_JUMP = _b("E10_TP_LIMBJUMP")
LIMB_JUMP_MM = 50.0
# ★ 注入帧必须**远离冻结窗** `[LAND, LAND_HOLD]`：窗内 `frame` 被钉回 `LAND`，
#   若注在窗内，窗口 5 帧会被注入**同一个**尖峰 ⟹ 窗内不产生步长，守卫是"靠
#   f(LAND_HOLD+1) 尖峰消失"间接红的（脆弱）。f18 在坠落段正中，基线步长已 54.8 mm/帧
#   ⟹ 叠加 50 mm 后必 > 60，判据**直接**见红。
LIMB_JUMP_FRAME = 18
KNEEL = _b("E10_TP_KNEEL")
KNEEL_DROP_M = 0.33        # 前摇段骨盆下沉量（跪姿）
KNEEL_ANKLE_BACK_M = 0.30  # 前摇段踝向后收（+Y = 身后；跪姿的脚在膝后）
SNAP = _b("E10_TP_SNAP")
PRONE = _b("E10_TP_PRONE")
TRACE = _b("E10_TRACE")

# 身体长轴符号：仰卧 = +1（头朝 +Y），俯卧 = −1（头朝 −Y）
AXIS = -1.0 if PRONE else 1.0

BASE = {}
TERM = {}
BONE_LIST = []
L1 = 0.410019
L2 = 0.412005
ANKLE_REST = {}
ANKLE_TERM = {}
TGT = {}          # (raw_frame, side) → 该帧**设计**的踝世界目标（可达性门禁核账用）
_PREV_STEP = {}   # TRACE 用：上一帧的髋/膝/踝世界位置（逐帧步长拆解）


# =============================================================== 包络
def _clamp01(x):
    return 0.0 if x <= 0.0 else (1.0 if x >= 1.0 else x)


def _smooth(x):
    x = _clamp01(x)
    return x * x * (3.0 - 2.0 * x)


def land_env(frame):
    """躯干后倒包络：`ANTIC_END` 起 0 → `LAND` 到 1。

    ★ 这里仍用 >1 的指数（`TORSO_POW`）是**安全**的：它驱动的是**躯干欧拉**混合
      （spine/chest/shoulder），量级只有十几度；骨盆有自己的 `pelvis_curve`
      （坠落段线性）。若把 `land_env` 直接接到骨盆上，`TORSO_POW` 会把单帧位移
      推到容差外 —— 两者职责必须分开。
    """
    if NO_FALL:
        return 0.0
    if frame <= ANTIC_END:
        return 0.0
    if frame >= LAND:
        return 1.0
    return _clamp01((frame - ANTIC_END) / float(LAND - ANTIC_END)) ** TORSO_POW


def _smooth_env(frame, tail):
    """`ANTIC_END` 起 0 → `tail` 到 1 的 smoothstep 包络（头/四肢的**滞后**）。"""
    if NO_FALL:
        return 0.0
    if frame <= ANTIC_END:
        return 0.0
    if frame >= tail:
        return 1.0
    return _smooth((frame - ANTIC_END) / float(tail - ANTIC_END))


def head_env(frame):
    """头**滞后** + **衰减收尾**（两段，见文件头 `HEAD_MAIN` 的推导）。

    段 1 `[ANTIC_END, REBOUND_TAIL]`：走完 `HEAD_MAIN`（smoothstep）。
    段 2 `[REBOUND_TAIL, SETTLE_TAIL]`：余量以 **1−(1−x)²** 收尾 ⟹ 单帧步长
    随 x **线性衰减到 0**，这正是「沉降 = 速度衰减到 0」的量化形态。

    ★ 反向验证 ⑨：`SNAP` 让头在 `REBOUND_TAIL` 直接到终点（与 `pelvis_curve`
      同刻）⟹ 沉降被压成单帧。
    """
    if NO_FALL:
        return 0.0
    if SNAP and frame >= REBOUND_TAIL:
        return 1.0
    if frame <= ANTIC_END:
        return 0.0
    if frame <= REBOUND_TAIL:
        return HEAD_MAIN * _smooth((frame - ANTIC_END)
                                   / float(REBOUND_TAIL - ANTIC_END))
    if frame <= SETTLE_TAIL:
        x = _clamp01((frame - REBOUND_TAIL) / float(SETTLE_TAIL - REBOUND_TAIL))
        return 1.0 - (1.0 - HEAD_MAIN) * (1.0 - x) * (1.0 - x)
    return 1.0


def arm_rise_env(frame):
    """臂阶段 1：被甩起（`ANTIC_END` → `ARM_LIFT_TAIL`）。"""
    return _smooth_env(frame, ARM_LIFT_TAIL)


def arm_fall_env(frame):
    """臂阶段 2：摊到地面（`LAND` → `ARM_TAIL`）。0 = 还在最高点。"""
    if NO_FALL:
        return 0.0
    if frame <= LAND:
        return 0.0
    if frame >= ARM_TAIL:
        return 1.0
    return _smooth((frame - LAND) / float(ARM_TAIL - LAND))


def leg_env(frame):
    """踝目标的**水平面**（x/y）包络 —— **两段**，跨冻结窗 **C0 连续**。

    ★ 本支的冻结窗是「把 `frame` 钉回 `LAND`」实现的 ⟹ **任何**在窗内还在爬的
      包络，都会把这 5 帧积累的位移在 f29 **一次性兑现**。这一条把两个"显然"的
      写法都否掉了（都是实测）：
      ① **单段** `ANTIC_END`→`LEG_TAIL`（smoothstep）：f24→f29 正处**斜率峰值**
         （0.0412/帧 × 右脚踝 y 行程 **312.6 mm** = 12.9 mm/帧）⟹ 5 帧积累
         **64.5 mm**，f29 报 **65.86 mm @ `foot.R`**。
      ② 起点挪到 `LAND`（坠落段踝完全不动）：窗那一侧干净了（41.1 mm），但站架的
         **后脚**（右踝 y=+140）不动、髋却退到 y=+470 ⟹ 右腿被迫以 28 mm/帧**折**
         起来，膝在 f23 报 **77.54 mm @ `knee.R`**。矛盾只是从窗的一侧挪到另一侧。
      ⟹ 解 = **两段**：窗**前**先走完 `LEG_FALL_SHARE`（把坠落段腿形的变化率摊开，
        同时让双脚跟着身体**滑一半**，别让后腿被折死），窗**后**从 `LEG_FALL_SHARE`
        接着走到 1（第二段仍是 smoothstep ⟹ **起步斜率为 0**）。
        实测：f24→f29 只走 **0.5%** ⟹ 单步 **1.7 mm**；两段的峰值斜率都 ≤ 15 mm/帧。
    """
    if NO_FALL:
        return 0.0
    if frame <= ANTIC_END:
        return 0.0
    if frame <= LAND:
        return LEG_FALL_SHARE * _smooth(
            (frame - ANTIC_END) / float(LAND - ANTIC_END))
    if frame >= LEG_TAIL:
        return 1.0
    return LEG_FALL_SHARE + (1.0 - LEG_FALL_SHARE) * _smooth(
        (frame - LAND_HOLD) / float(LEG_TAIL - LAND_HOLD))


def ankle_z_env(frame):
    """踝目标的 **z 分量**用一条**更早到位**的包络（`ANTIC_END` → `LAND` 走完）。

    ★ 为什么必须把 z 从 `leg_env` 里**分出来**（f24 鞋底 −9.18 mm 的实测修正）：
      鞋网格是**三骨平均蒙皮**（`foot` + `toe` + `shin`，见 `_probe_e10_land.py`）。
      `foot` 的世界朝向被 `keep_foot_orient` 钉在 rest（`foot_env` 到 `LAND` 才启动）
      ⟹「刚体那部分」只随踝平移；但 `shin` 的权重会把鞋**跟着折叠的小腿扭下去**：
      f24 实测（shin 偏离 rest 47.5°）鞋底比「踝高 − 79.8 mm」低了 **20.6 mm**
      （f60 shin 86.3° 时低 34.6 mm ⟹ 与 shin 偏角近似成正比）。
      不改容差、不动终姿、也不给脚加俯仰（那会把鞋**边**转下去）的唯一解：
      让**踝在坠落段就把 z 抬到位**（终端 z = 113.9 mm，比 rest 高 34.1 mm），
      鞋的刚体部分随之上抬，覆盖掉蒙皮扭降。
      水平面（y/x）仍走慢包络 ⟹「腿在回弹段被拉直」的观感不变，
      `dth_rebound_ok` / `dth_settle_ok`（载体都是头）也不受影响。
    """
    if NO_FALL:
        return 0.0
    if frame <= ANTIC_END:
        return 0.0
    if frame >= LAND:
        return 1.0
    return _smooth((frame - ANTIC_END) / float(LAND - ANTIC_END))


def foot_env(frame):
    """脚的俯仰/外翻包络：**离地之后**才开始，落地前脚仍踩平。

    ★ 为什么单独开一条而不复用 `leg_env`：`leg_env` 到 `LAND` 已走 33.6%，
      若脚在同一时刻也转 33.6%（俯仰 −5°、外翻 +15°），鞋底边缘会被转下去
      —— 鞋半宽 ~50 mm，外翻 15.1° 就压低 **13 mm**，叠加俯仰 5° 的脚尖下沉
      **16.5 mm**，而踝只抬高了 11.5 mm ⟹ 鞋底穿地约 −18 mm。脚必须**等离地**再翻。
    """
    if NO_FALL:
        return 0.0
    if frame <= LAND:
        return 0.0
    if frame >= FOOT_TAIL:
        return 1.0
    return _smooth((frame - LAND) / float(FOOT_TAIL - LAND))


def tip_env(frame):
    """前摇包络（0 → `ANTIC_END`）：重心后倒的**启动略慢**。"""
    if frame <= START:
        return 0.0
    if frame >= ANTIC_END:
        return 1.0
    return (frame / float(ANTIC_END)) ** KNEEL_POW


def break_hitstop(frame):
    """反向验证 ④：把冻结窗内的姿态**缓慢漂移**（控制组）。"""
    if not NO_HITSTOP:
        return 0.0
    if LAND <= frame <= LAND_HOLD:
        return (frame - LAND) * 1.5
    return 0.0


def micro_env(frame):
    """反向验证 ③：尸僵窗内注入残余微动（控制组）。"""
    if not MICROMOTION:
        return 0.0
    if frame < SETTLE_TAIL:
        return 0.0
    span = float(END - SETTLE_TAIL)
    return math.sin(2.0 * math.pi * 2.0 * (frame - SETTLE_TAIL) / span)


def _ease(kind, x):
    x = _clamp01(x)
    if kind == "lin":
        return x
    if kind == "smooth":
        return x * x * (3.0 - 2.0 * x)
    if kind.startswith("pow:"):
        return x ** float(kind.split(":", 1)[1])
    return x


def pelvis_curve(frame):
    """世界骨盆 (y, z, rx)。★ 反向验证 ⑨：`SNAP` 把沉降压成单帧瞬停。

    ★ 首版只把 `frame >= SETTLE_TAIL - 2`（末 2 帧）钉死 ⟹ 沉降窗 `[40, 60]` 里
      f40..f57 照旧在爬，`dth_settle_moving_frames` = 17 纹丝不动（判据载体是
      **头**，头挂在骨盆之下：只钉骨盆的**最后两帧**根本停不住整段）。
      正解 = 在 `REBOUND_TAIL` 就把骨盆 + 头**一起**推到终点 ⟹ 沉降窗退化为
      「一帧跳完 + 之后不动」，`dth_settle_ok` 的**帧数**一条直接见红。
    """
    if SNAP and frame >= REBOUND_TAIL:
        frame = SETTLE_TAIL
    keys = PELVIS_KEYS
    if frame <= keys[0][0]:
        return keys[0][1]
    for i in range(len(keys) - 1):
        f0, v0, kind = keys[i]
        f1, v1, _k1 = keys[i + 1]
        if f0 <= frame <= f1:
            t = _ease(kind, (frame - f0) / float(f1 - f0))
            return tuple(a + (b - a) * t for a, b in zip(v0, v1))
    return keys[-1][1]


# =============================================================== 工具
def _mix_dir(a, b, t):
    """两方向之间按**球面**（slerp）插值 —— 不是 lerp + 归一。

    ★ 为什么不能 lerp + 归一（第二跑实测教训）：上臂这段的两个方向差 **126.9°**，
      `va.lerp(vb, t).normalized()` 的**角速度不是常数** —— 在 t=0.5 处
      |v| 只剩 0.447，而 |vb−va| = 1.789 ⟹ dφ/dt = 1.789/0.447 = 4.00 rad/单位 t
      （是平均角速度 2.226 rad 的 **1.80 倍**），再叠加 smoothstep 的 1.5 倍峰值
      ⟹ 上臂单帧方向变化实测 **23.07° @f17**。而 `no_teleport` 的载体是**子骨 euler**：
      `forearm` 为守住世界朝向必须在 euler 上**反向补偿**父骨那 23° 的滚转 ⟹
      实测 **25.868° @f17 `forearm.R`**（容差 25）—— 红的是子骨，因在父骨。
      改球面插值 ⟹ 角速度恒定，峰值 = 1.5 × 126.9/14 = **13.6°/帧**。
      ★ `t=0` 仍**逐位**返回 `va` ⟹ 首帧接缝（`dth_seam_in_ok`）不受影响。
    """
    va = Vector(a).normalized()
    vb = Vector(b).normalized()
    if t <= 0.0:
        return tuple(va)
    if t >= 1.0:
        return tuple(vb)
    if va.dot(vb) < -0.9999:
        return tuple(va)
    return tuple(va.slerp(vb, t))


def leg_pole(prx_deg):
    """极点 = **骨盆局部 −Y 的世界方向**（膝的弯曲侧）。

    站架（rx≈4°）⟹ ≈ (0,−1,0)：膝朝前。
    仰卧（rx=−86°）⟹ ≈ (0,0,+1)：膝朝**上**。
    ★ 反向验证 ⑥：`KNEE_PLUNGE` 把它翻成朝下 ⟹ 膝入地。
    """
    rot = Matrix.Rotation(math.radians(prx_deg), 3, "X")
    pole = (rot @ Vector((0.0, -1.0, 0.0))).normalized()
    if KNEE_PLUNGE:
        pole = Vector((0.0, 0.0, -1.0))
    return pole


def leg_solve(hip, target, l1, l2, pole):
    """世界空间两骨解：返回 (thigh 方向, shin 方向, 膝位置, 是否被截断)。

    `u` = 髋→踝单位向量；膝在离「髋→踝」连线 `h` 处、朝极点一侧。
    ★ 没有小角假设 ⟹ 站架与仰卧用**同一套**公式（E09 的 `leg_ik` 不行）。
    """
    d = Vector(target) - Vector(hip)
    dist = d.length
    limit = (l1 + l2) * REACH_MAX_RATIO
    clipped = dist > limit
    if clipped:
        d = d.normalized() * limit
        dist = limit
    dist = max(dist, abs(l1 - l2) + 1e-4)
    u = d.normalized()
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2.0 * dist)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    pv = Vector(pole).normalized()
    n = pv - u * pv.dot(u)
    if n.length < 1e-6:
        n = Vector((0.0, 0.0, 1.0)) - u * u.z
    n.normalize()
    knee = Vector(hip) + u * a + n * h
    return ((knee - Vector(hip)).normalized(),
            (Vector(target) - knee).normalized(), knee, clipped)


def keep_foot_orient(arm, name, fp_deg, roll_deg):
    """世界朝向 = rest 先绕**世界 X** 俯仰 `fp_deg`、再绕**世界 Y** 外翻 `roll_deg`。

    ★ `fp=0, roll=0` 时与 `A.keep_world_orientation` **逐位相同**（都是 rest 3×3）
    ⟹ 首帧用它可以天然接缝，不需要特判脚。
    """
    pose_bone = arm.pose.bones[name]
    rest_basis = pose_bone.bone.matrix_local.to_3x3()
    rot = (Matrix.Rotation(math.radians(roll_deg), 3, "Y")
           @ Matrix.Rotation(math.radians(fp_deg), 3, "X"))
    target = (rot @ rest_basis).to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def ankle_target(frame, side):
    """踝的世界目标：站架 → 仰卧。

    ★ x/y 走 `leg_env`（慢，到 `LEG_TAIL`），**z 单独走 `ankle_z_env`**（到 `LAND`）
      —— 见 `ankle_z_env` 的推导（f24 鞋底蒙皮沉陷的修正）。
    """
    s = 1.0 if side == "L" else -1.0
    base = ANKLE_REST[side]
    term = ANKLE_TERM[side]
    t = leg_env(frame)
    tz = ankle_z_env(frame)
    out = Vector((base.x + (term.x - base.x) * t,
                  base.y + (term.y - base.y) * t,
                  base.z + (term.z - base.z) * tz))
    if KNEEL and frame <= ANTIC_END:
        # 反向验证 ⑧：前摇段把踝**收到身后** + 骨盆下沉 ⟹ 读作**跪姿**
        # ★ 方向是**实测**定出来的，不是想当然：把踝拉到**身前**（y 更负）时，
        #   髋→踝矢量与极点（朝前）同侧，`perp` 把膝**顶高** —— 骨盆下沉 0.33 m
        #   只把膝从 428 压到 383 mm（判据 300 够不着）。真跪姿是**脚在身后**
        #   （小腿贴地、膝在髋前下方）：踝 y 取 +（身后）后，髋→踝转成后下方，
        #   极点分量被反转 ⟹ 膝落到 200 mm 量级。
        k = (frame / float(ANTIC_END)) ** KNEEL_POW
        out.y += KNEEL_ANKLE_BACK_M * k
        out.z += -0.03 * k
    if LIMB_JUMP and frame == LIMB_JUMP_FRAME:
        out.y += LIMB_JUMP_MM / 1000.0
    return out


def foot_pitch(frame):
    """鞋的俯仰（绕世界 X）。到顶 −15°（探针扫出的终值）。"""
    return -15.0 * foot_env(frame)


def foot_roll(frame):
    """鞋的外翻（绕**世界 Y**）。到顶 45° —— E09 明说「留给 E10」的那件事。"""
    return 45.0 * foot_env(frame)


# =============================================================== 姿态装配
def death_pose(arm, frame):  # noqa: C901
    """生成第 `frame` 帧的完整姿态（**逐帧**调用，每帧自洽）。"""
    raw = frame
    # ★★★ 冻结窗：命中后的 `[LAND, LAND_HOLD]` 四帧**姿态逐位相同**。
    #   为什么不能只靠 `A.set_hitstop`：本支是**逐帧打键**（0..120 每帧一个键），
    #   而 `set_hitstop` 设的是 **CONSTANT 插值** —— 它只影响"键与键之间"的取值；
    #   在我们这里键就是帧、插值根本轮不到 ⟹ 姿态必须由**生成函数本身**冻结。
    #   首跑实测：只设 CONSTANT 时窗内单帧仍漂 **25.64°**（`dth_hitstop_ok` 红）。
    if not NO_HITSTOP and LAND <= frame <= LAND_HOLD:
        frame = LAND
    s = land_env(frame)
    hs = head_env(frame)
    ars = arm_rise_env(frame)
    afs = arm_fall_env(frame)
    fes = foot_env(frame)
    drift = break_hitstop(raw)
    mic = micro_env(raw)

    # ---- 躯干：欧拉混合（骨盆 / 脊柱 / 胸 / 颈 / 头 / 肩 / 指）------------
    pose = A.blend(BASE, TERM, s)
    py, pz, prx = pelvis_curve(frame)
    if NO_FALL:
        py, pz, prx = PELVIS_KEYS[0][1]
    # ★ 俯卧反演（反向验证 ⑩）：身体长轴翻向 −Y，颈/头/踝同步翻符号
    py *= AXIS
    prx *= AXIS
    pose["pelvis"] = (prx, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(0.0, py, pz - 0.900)}

    # ---- 颈 / 头：**滞后**于躯干（头是最后落地的）------------------------
    if hs != s:
        for name in ("neck", "head"):
            rb = BASE.get(name, (0.0, 0.0, 0.0))
            rt = TERM.get(name, (0.0, 0.0, 0.0))
            pose[name] = tuple(a + (b - a) * hs for a, b in zip(rb, rt))
    if AXIS < 0.0:
        for name in ("neck", "head"):
            rx, ry, rz = pose.get(name, (0.0, 0.0, 0.0))
            pose[name] = (-rx, -ry, rz)

    # ---- 反向验证旋钮：姿态漂移 / 残余微动 -------------------------------
    if drift != 0.0:
        rx, ry, rz = pose.get("chest", (0.0, 0.0, 0.0))
        pose["chest"] = (rx + drift, ry, rz)
    if mic != 0.0:
        for name, amp in (("chest", 1.1), ("neck", 0.7), ("head", 0.5)):
            rx, ry, rz = pose.get(name, (0.0, 0.0, 0.0))
            pose[name] = (rx + amp * mic, ry, rz)

    # ★★ 注入必须先过一遍 **轴映射**：`A.wloc(dx, dy, dz) = (dx, dz, -dy)`
    #   ⟹ 竖直骨链的局部 **index 1 = 世界 Z**、局部 index 2 = −世界 Y。
    #   首版把下沉量写在 index 2 上 = 把尸体沿**世界 Y**推了 60 mm ⟹
    #   触地判据纹丝不动（守卫"没红"不是判据弱，是注入打偏）。两条注入同病同修。
    if SINK and frame >= LAND_HOLD:
        loc = pose["@loc"]["pelvis"]
        pose["@loc"] = {"pelvis": (loc[0], loc[1] - SINK_MM / 1000.0, loc[2])}
    # 反向验证 ⑧：跪姿段把骨盆按下去
    if KNEEL and frame <= ANTIC_END:
        k = (frame / float(ANTIC_END)) ** KNEEL_POW
        loc = pose["@loc"]["pelvis"]
        pose["@loc"] = {"pelvis": (loc[0], loc[1] - KNEEL_DROP_M * k, loc[2])}
        pose["pelvis"] = (prx + 30.0 * k, 0.0, 0.0)

    pose["root"] = (0.0, 0.0, 0.0)
    pose.update(A.FIST)

    # ---- 腿：**世界空间两骨解 + 世界极点**（不是欧拉混合，见文件头 ②③）----
    A.apply_pose(arm, pose)
    pole = leg_pole(prx)
    if AXIS < 0.0:
        pole = leg_pole(-86.0)
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        tgt = ankle_target(frame, side)
        if AXIS < 0.0:
            tgt = Vector((tgt.x, -tgt.y, tgt.z))
        TGT[(raw, side)] = tgt.copy()      # 供可达性门禁核账（`dth_assertions` ⑬）
        du, df, _knee, _clip = leg_solve(hip, tgt, L1, L2, pole)
        pose["thigh." + side] = A.aim_bone(arm, "thigh." + side, du)
        A.apply_pose(arm, pose)
        pose["shin." + side] = A.aim_bone(arm, "shin." + side, df)
        A.apply_pose(arm, pose)
    for side in SIDES:
        pose["foot." + side] = keep_foot_orient(arm, "foot." + side,
                                                foot_pitch(frame),
                                                foot_roll(frame)
                                                * (1.0 if side == "L" else -1.0))
        A.apply_pose(arm, pose)

    # ---- 臂：世界方向**两段**插值（甩起 → 摊地），不插欧拉 ⟹ 无万向节假跳 --
    for bone in ARM_BONES:
        if afs <= 0.0:
            d = _mix_dir(BASE_DIRS[bone], LIFT_DIRS[bone], ars)
        else:
            d = _mix_dir(LIFT_DIRS[bone], TERM_DIRS[bone], afs)
        if AXIS < 0.0:
            d = (d[0], -d[1], d[2])
        pose[bone] = A.aim_bone(arm, bone, d)
        A.apply_pose(arm, pose)

    # ---- ★ 首帧接缝特判：腿走解算器会带来 1.45° 的**绕骨轴滚转**差 --------
    # （膝位误差仅 0.19 mm ⟹ 是纯滚转）⟹ 为了让 `dth_seam_in_ok` 逐位成立，
    #   首帧的腿骨直接取自 `Idle_01@0`。**脚必须一起取**：脚的欧拉是在「解算器
    #   给出的胫骨」下解出来的；只把胫骨换回 BASE 而脚留用解算器结果，脚的世界
    #   朝向就差 1.45°（首跑实测 `toe.L` 世界位置差 **3.10 mm** ⟹ `dth_seam_in_ok` 红）。
    #   f0→f1 这点差值在圆截面的腿网格上不可见，且远低于 `no_teleport` 的 25°。
    if not SEAM_ZERO and raw == START:
        for bone in ("thigh.L", "shin.L", "foot.L",
                     "thigh.R", "shin.R", "foot.R"):
            if bone in BASE:
                pose[bone] = BASE[bone]
        A.apply_pose(arm, pose)

    if TRACE:
        A.apply_pose(arm, pose)
        # ★ 逐帧拆解 `dth_limb_step_ok` 的载体（f? 到底是**平移**还是**腿形变化**）
        pv = {}
        for x in SIDES:
            pv["hip." + x] = Vector(A.bone_world(arm, "thigh." + x, "head"))
            pv["knee." + x] = Vector(A.bone_world(arm, "shin." + x, "head"))
            pv["foot." + x] = Vector(A.bone_world(arm, "foot." + x, "head"))
        if _PREV_STEP:
            parts = []
            for k in sorted(pv):
                parts.append("%s=%5.1f" % (k, (pv[k] - _PREV_STEP[k]).length
                                           * 1000.0))
            print("E10STEP f=%3d %s" % (raw, " ".join(parts)))
        _PREV_STEP.clear()
        _PREV_STEP.update(pv)
        lows = body_low_profile()
        ank_zs = [A.bone_world(arm, "foot." + x, "head").z * 1000.0
                  for x in SIDES]
        leg_len = []
        for x in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + x, "head"))
            leg_len.append(round((Vector(TGT[(raw, x)]) - hip).length * 1000.0,
                                 1))
        print("E10_TRACE f=%3d s=%.3f hs=%.3f ar=%.3f af=%.3f fe=%.3f "
              "lg=%.3f az=%.3f py=%+.3f pz=%.3f rx=%+.1f low=%.2f(%s) knee=%.1f "
              "head=%.1f ank=%.1f leglen=%s"
              % (raw, s, hs, ars, afs, fes, leg_env(frame),
                 ankle_z_env(frame), py, pz, prx,
                 min(lows.values()),
                 min(lows.items(), key=lambda kv: kv[1])[0],
                 min(A.bone_world(arm, "shin." + x, "head").z
                     for x in SIDES) * 1000.0,
                 A.bone_world(arm, "head").z * 1000.0,
                 min(ank_zs), leg_len))
    return pose


# =============================================================== 快照
def body_low_profile(arm=None):
    """逐网格对象的最低世界 z（毫米）—— 沿用 E09 的基础设施件。"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        out[obj.name] = min((matrix @ v.co).z for v in mesh.vertices) * 1000.0
        evaluated.to_mesh_clear()
    return out


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
def dth_assertions(arm, action, samples, meshes):  # noqa: C901
    res = {}
    scene = bpy.context.scene
    frames = [s["frame"] for s in samples]
    rest = [f for f in frames if SETTLE_TAIL <= f <= END]
    tips = [f for f in frames if START <= f <= ANTIC_END]

    # ---- ① ★ 零微动（本支唯一的新判据族）---------------------------------
    # 载体 = 与 E09 呼吸**同一根探针**（胸骨顶 = `neck` = chest.tail 的世界 z）。
    # 同一把尺子量出的差别才是可分性的证明：E09 同窗口 5~34 mm，本支必须 ≈ 0。
    stern = [(s["frame"], Vector(s["neck"]).z * 1000.0) for s in samples
             if s["frame"] >= SETTLE_TAIL]
    zs = [v for _f, v in stern]
    amp = max(zs) - min(zs)
    mean = sum(zs) / float(len(zs))
    dev = [v - mean for v in zs]
    cross = sum(1 for i in range(1, len(dev))
                if (dev[i - 1] > 0.0) != (dev[i] > 0.0))
    res["dth_zero_motion_amp_mm"] = round(amp, 4)
    res["dth_zero_motion_crossings"] = cross
    res["dth_zero_motion_ok"] = bool(
        amp <= ZERO_MOTION_MAX_MM and cross <= ZERO_MOTION_MAX_CROSS)
    res["dth_zero_motion_note"] = (
        "★★★ **本支唯一的新判据族**（清单 E10 详细计划 §1 ①）：「死亡」与"
        "「躺着的战败」差别**就是**「有没有呼吸」。载体 = 与 E09 `dft_breath_ok`"
        "**完全同一根探针**（胸骨顶 `neck` = chest.tail 世界 z），窗口同为"
        " `[%d, %d]`。E09 在同窗口实测呼吸 **5~34 mm / 过零 ≥3**；本支实测"
        " 幅 **%.4f mm / 过零 %d**（判据：幅 ≤ %.1f mm 且 过零 ≤ %d）。"
        "★ 守卫 = `E10_TP_MICROMOTION=1`（尸僵窗注入残余微动）⟹ 必须见红。"
        % (SETTLE_TAIL, END, amp, cross, ZERO_MOTION_MAX_MM,
           ZERO_MOTION_MAX_CROSS))

    # ---- ② 前摇**无跪姿段**（清单 E10 详细计划 §2）------------------------
    knee_tips = []
    for frame in tips:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        knee_tips.append(min(A.bone_world(arm, "shin." + s, "head").z
                             for s in SIDES) * 1000.0)
    res["dth_tip_knee_min_mm"] = round(min(knee_tips), 2)
    res["dth_no_kneel_ok"] = bool(
        res["dth_tip_knee_min_mm"] >= NO_KNEEL_MIN_KNEE_MM)
    res["dth_no_kneel_note"] = (
        "★ 清单原文：「与普通击倒区分」⟹ 本支是**直接后倒**，**不许有跪姿段**"
        "（E09 的招牌是「双膝触地 4 帧冻结」）。载体 = 前摇窗 `[%d, %d]` 内"
        "**膝关节世界 z 的最小值** ≥ %.0f mm（跪姿实测膝 z ≈ %.1f，站架 ≈ 487）。"
        "实测最低 %.2f mm。守卫 = `E10_TP_KNEEL=1`（前摇注入跪姿）⟹ 必须见红。"
        % (START, ANTIC_END, NO_KNEEL_MIN_KNEE_MM, KNEE_RADIUS_MM,
           res["dth_tip_knee_min_mm"]))

    # ---- ③ 力量传导链（脚→腿→髋→腰→肩→手，每段都要有关键帧）--------------
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
    knee_deg = 0.0
    for sample in samples:
        knee_deg = max(knee_deg, abs(sample["euler"].get(
            "shin.L", (0.0, 0.0, 0.0))[0]))
    pelvis = [Vector(s["pelvis"]) for s in samples]
    hip_travel = max((p - pelvis[0]).length for p in pelvis) * 1000.0
    waist = [abs(s["euler"].get("chest", (0.0, 0.0, 0.0))[0])
             for s in samples]
    waist_deg = (max(waist) - min(waist)) * 180.0 / math.pi
    shoulder = [Vector(s["upperarm.L"]) for s in samples]
    shoulder_mm = max((p - shoulder[0]).length for p in shoulder) * 1000.0
    hand = [Vector(s["hand.L.tail"]) for s in samples]
    hand_mm = max((p - hand[0]).length for p in hand) * 1000.0
    foot = [Vector(s["foot.L"]) for s in samples]
    foot_mm = max((p - foot[0]).length for p in foot) * 1000.0
    res["dth_chain_travel"] = {"foot_mm": round(foot_mm, 3),
                               "knee_deg": round(knee_deg, 3),
                               "hip_mm": round(hip_travel, 3),
                               "waist_deg": round(waist_deg, 3),
                               "shoulder_mm": round(shoulder_mm, 3),
                               "hand_mm": round(hand_mm, 3)}
    res["dth_chain_ok"] = bool(
        foot_mm > 20.0 and knee_deg > 0.2 and hip_travel > 20.0
        and waist_deg > 2.0 and shoulder_mm > 1.0 and hand_mm > 20.0)
    res["dth_chain_note"] = (
        "★ SOUL 硬约束：**脚→腿→髋→腰→肩→手**逐段都要有关键帧量。本支是"
        "「整体后倒」，髋/手行程远大于 E09（实测髋 %.0f mm / 手 %.0f mm / 脚 %.0f mm）。"
        % (hip_travel, hand_mm, foot_mm))

    # ---- ④ 逐件贴地 / 无穿模（★ 沿用 E09 口径与容差，**不改**）------------
    prof = {}
    scan = sorted(set(list(range(START, END + 1, 2))
                      + [ANTIC_END, LAND, LAND_HOLD, REBOUND_TAIL, END]))
    for frame in scan:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        prof[frame] = body_low_profile()
    rest_lows = {f: min(prof[f].values()) for f in rest if f in prof}
    all_lows = {f: min(prof[f].values()) for f in prof}
    res["dth_body_low_min_mm"] = round(min(rest_lows.values()), 2)
    res["dth_body_low_max_mm"] = round(max(rest_lows.values()), 2)
    res["dth_body_ground_ok"] = bool(
        BODY_BAND[0] <= res["dth_body_low_min_mm"]
        and res["dth_body_low_max_mm"] <= BODY_BAND[1])
    res["dth_worst_part"] = min(prof[END].items(), key=lambda kv: kv[1])[0]
    res["dth_worst_frame"] = min(all_lows.items(), key=lambda kv: kv[1])[0]
    res["dth_global_low_mm"] = round(min(all_lows.values()), 2)
    res["dth_no_penetration_ok"] = bool(
        res["dth_global_low_mm"] >= PENETRATION_MIN_MM)
    res["dth_ground_note"] = (
        "★ **沿用 E09 `dft_body_ground_ok` / `dft_no_penetration_ok` 的口径与容差**"
        "（带 [%.0f, %.0f] mm；下限 %.0f mm），只把窗口换成尸僵窗 `[%d, %d]`。"
        "载体 = 逐件最低 z。尸僵窗内最低件 = `%s`（%.2f mm）；全程最险帧 = f%s，"
        "最低件 = `%s`。守卫 = `E10_TP_SINK=1`（整体下沉 %.0f mm）⟹ 两条都要见红。"
        % (BODY_BAND[0], BODY_BAND[1], PENETRATION_MIN_MM, SETTLE_TAIL, END,
           res["dth_worst_part"], min(rest_lows.values()),
           res["dth_worst_frame"], res["dth_worst_part"], SINK_MM))

    # ---- ⑤ 膝不入地 + 无肢体跳变（**沿用 E09 口径与容差**）----------------
    knee_zs, steps, step_at = [], [], None
    prev = None
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        cur = {}
        for side in SIDES:
            cur["knee." + side] = Vector(A.bone_world(arm, "shin." + side,
                                                      "head"))
            cur["foot." + side] = Vector(A.bone_world(arm, "foot." + side,
                                                      "head"))
        knee_zs.append(min(v.z for k, v in cur.items()
                           if k.startswith("knee")) * 1000.0)
        if prev is not None:
            for key in cur:
                d = (cur[key] - prev[key]).length * 1000.0
                if step_at is None or d > step_at[0]:
                    step_at = (d, frame, key)
                steps.append(d)
        prev = cur
    res["dth_knee_z_min_mm"] = round(min(knee_zs), 2)
    res["dth_knee_z_at"] = START + knee_zs.index(min(knee_zs))
    res["dth_knee_path_ok"] = bool(
        res["dth_knee_z_min_mm"] >= KNEE_RADIUS_MM - KNEE_PATH_TOL_MM)
    res["dth_limb_step_max_mm"] = round(max(steps), 2)
    res["dth_limb_step_at"] = step_at
    res["dth_limb_step_ok"] = bool(max(steps) <= LIMB_STEP_MAX_MM)
    res["dth_knee_path_note"] = (
        "★ **沿用 E09 `dft_knee_path_ok` 的容差**（膝 z ≥ %.1f − %.1f mm）。"
        "为什么本支也要盯：本支的腿**由世界空间解算器驱动**，仰卧极点朝上、"
        "站架极点朝前 —— 极点一旦取反（`E10_TP_KNEEPLUNGE=1`）膝立刻入地。"
        "实测最低 %.2f mm（f%s）。守卫 = `E10_TP_KNEEPLUNGE=1`。"
        % (KNEE_RADIUS_MM, KNEE_PATH_TOL_MM, res["dth_knee_z_min_mm"],
           res["dth_knee_z_at"]))
    res["dth_limb_step_note"] = (
        "★ **沿用 E09 `dft_limb_step_ok` 的容差 %0.f mm/帧**（= %.1f m/s @60fps）。"
        "实测峰值 %.2f mm/帧 @f%s `%s`。守卫 = `E10_TP_LIMBJUMP=1`"
        "（f%d 给踝目标注入 %.0f mm 尖峰）⟹ 必须见红。"
        % (LIMB_STEP_MAX_MM, LIMB_STEP_MAX_MM * 60.0 / 1000.0,
           res["dth_limb_step_max_mm"],
           res["dth_limb_step_at"][1] if res["dth_limb_step_at"] else "?",
           res["dth_limb_step_at"][2] if res["dth_limb_step_at"] else "?",
           LIMB_JUMP_FRAME, LIMB_JUMP_MM))

    # ---- ⑥ **唯一**一个命中停顿（单段重摔；清单 §6 要 2~4 帧完全冻结）------
    worst, at = 0.0, None
    for index in range(LAND - START + 1, LAND_HOLD - START + 1):
        step, pos = _worst_step(samples, index - 1, index)
        if step > worst:
            worst, at = step, pos
    res["dth_hitstop_windows"] = {"land": {"frames": [LAND, LAND_HOLD],
                                           "worst_step_deg": round(worst, 5),
                                           "at": at}}
    res["dth_hitstop_ok"] = bool(worst <= HITSTOP_MAX_DEG)
    res["dth_hitstop_note"] = (
        "★ 本支是**单段重摔** ⟹ 只有**一个**冻结窗 `[%d, %d]`（4 帧；E09 有两个："
        "膝落 + 前扑）。载体 = 窗口内逐帧姿态。守卫 = `E10_TP_NOHITSTOP=1`"
        "（窗口内每帧漂 1.5°）⟹ 必须见红（≥ %.2f°）。"
        % (LAND, LAND_HOLD, HITSTOP_MAX_DEG))

    # ---- ⑦ 仰卧判定（★ 本支新判据：**真的躺在背上**吗）--------------------
    scene.frame_set(END)
    bpy.context.view_layer.update()
    chest_dir = Vector(A.bone_direction(arm, "chest"))
    hair = prof[END].get("Hair_Mass", 1e9)
    head = prof[END].get("Head", 1e9)
    pel_end = Vector(samples[END - START]["pelvis"])
    res["dth_supine_axis_y"] = round(chest_dir.y, 5)
    res["dth_supine_head_gap_mm"] = round(head - hair, 2)
    res["dth_supine_pelvis_z_mm"] = round(pel_end.z * 1000.0, 2)
    res["dth_supine_ok"] = bool(
        abs(chest_dir.y) >= SUPINE_AXIS_MIN
        and res["dth_supine_head_gap_mm"] >= SUPINE_HEAD_GAP_MM
        and res["dth_supine_pelvis_z_mm"] <= SUPINE_PELVIS_MAX_MM)
    res["dth_supine_note"] = (
        "★★★ **本支相对 E09 的全部差别就是「趴着」变「躺着」** ⟹ 必须被量出来。"
        "三个载体：① 躯干长轴 `chest` 世界方向的 |y| 分量 ≥ %.2f（**仰卧**实测 "
        "%.5f；俯卧会翻成负 ⟹ 见守卫）；② **后脑勺**（`Hair_Mass`）最低 z 必须"
        "**低于**头（`Head`）最低 z 至少 %.1f mm —— 头发着地 ⟹ 脸朝上"
        "（实测 gap %.2f mm）；③ 尾帧骨盆世界 z ≤ %.0f mm（实测 %.2f，E09 同口径"
        "上限 200）。守卫 = `E10_TP_PRONE=1` / `E10_TP_NOFALL=1`，两条都必须见红。"
        % (SUPINE_AXIS_MIN, res["dth_supine_axis_y"], SUPINE_HEAD_GAP_MM,
           res["dth_supine_head_gap_mm"], SUPINE_PELVIS_MAX_MM,
           res["dth_supine_pelvis_z_mm"]))

    # ---- ⑧ ★ 与 E09 `Defeat@120` 的可分性（照抄 `_probe_e07_vs_e06.py` 口径）--
    e09 = bpy.data.actions.get("Defeat")
    if e09 is None:
        res["dth_distinct_from_e09_ok"] = None
        res["dth_distinct_note"] = "★ `Defeat` action 不在工程里 ⟹ 本判据置空。"
    else:
        arm.animation_data.action = e09
        A._bind_slot(arm, e09)
        scene.frame_set(120)
        bpy.context.view_layer.update()
        e09_mats = {n: (arm.matrix_world @ arm.pose.bones[n].matrix).copy()
                    for n in BONE_LIST if n in arm.pose.bones}
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        scene.frame_set(END)
        bpy.context.view_layer.update()
        e10_mats = {n: (arm.matrix_world @ arm.pose.bones[n].matrix).copy()
                    for n in BONE_LIST if n in arm.pose.bones}
        wp, wd, wb = 0.0, 0.0, None
        for name in e09_mats:
            if name not in e10_mats:
                continue
            p, dg = _mat_delta(e10_mats[name], e09_mats[name])
            if dg > wd:
                wd, wb = dg, name
            wp = max(wp, p)
        res["dth_vs_e09_pos_mm"] = round(wp, 2)
        res["dth_vs_e09_dir_deg"] = round(wd, 3)
        res["dth_vs_e09_worst_bone"] = wb
        res["dth_distinct_from_e09_ok"] = bool(wd >= DISTINCT_MIN_DEG)
        res["dth_distinct_note"] = (
            "★★★ 清单 E10 详细计划 §0：「E09 终姿定格作**可分性基准**（≥15°）」。"
            "口径照抄 `_probe_e07_vs_e06.py`：57 骨**世界矩阵**，取朝向差的最大值。"
            "实测最大 **%.3f° @ %s**（位置差 %.2f mm），阈值 %.0f° ⟹ 余量 %.1f×。"
            "★ 这条判据是**跨支接口**（E10 与 E09 必须能被玩家一眼区分），"
            "不是行为开关 ⟹ 它的失败模式是「作者把尸体姿写成了 E09 的伏地姿」，"
            "由本判据本身兜住。"
            % (wd, wb, wp, DISTINCT_MIN_DEG,
               (wd / DISTINCT_MIN_DEG) if DISTINCT_MIN_DEG else 0.0))

    # ---- ⑨ 回弹：头/四肢**二次落地** + 惯性（不许瞬停）--------------------
    head_series = {s["frame"]: Vector(s["head"]).z * 1000.0 for s in samples}
    h_hold = head_series[LAND_HOLD]
    h_end = head_series[END]
    res["dth_rebound_head_drop_mm"] = round(h_hold - h_end, 2)
    res["dth_rebound_head_at_land_mm"] = round(head_series[LAND], 2)
    res["dth_rebound_ok"] = bool(
        res["dth_rebound_head_drop_mm"] >= REBOUND_HEAD_MIN_MM)
    res["dth_rebound_note"] = (
        "★ 清单 E10 详细计划 §2：「回弹 24→40（**头/四肢二次落地**、惯性、"
        "不许瞬停）」。载体 = **头（`head`）世界 z 在触地定格之后还要再落多少**"
        " ≥ %.0f mm。实测：f%d 触地时头 z = %.1f，f%d 定格末 = %.1f，"
        "尾帧 = %.1f ⟹ 二次落地落差 **%.2f mm**。"
        "★ 为什么必须单开一条：躯干触地（`dth_hitstop_ok`）只证明**背**停了，"
        "证明不了**头还在往下走** —— 没有这条，「头跟躯干一起瞬停」会全绿。"
        % (REBOUND_HEAD_MIN_MM, LAND, res["dth_rebound_head_at_land_mm"],
           LAND_HOLD, h_hold, h_end, res["dth_rebound_head_drop_mm"]))

    # ---- ⑩ 沉降：速度**衰减到 0**（不是瞬停）------------------------------
    # ★ 窗口 = `[REBOUND_TAIL, SETTLE_TAIL]`（= 清单 §2 的「沉降 40→60」），
    #   **不含回弹段**：回弹段头还在快速二次落地（`dth_rebound_ok` 管），
    #   把回弹段一起算进来会让"沉降"这个判据去量回弹，峰值必然红。
    hs = [head_series[f] for f in range(REBOUND_TAIL, SETTLE_TAIL + 1)]
    hsteps = [abs(hs[i] - hs[i - 1]) for i in range(1, len(hs))]
    res["dth_settle_peak_mm"] = round(max(hsteps), 3)
    res["dth_settle_tail_mm"] = round(hsteps[-1], 4)
    res["dth_settle_decay_ratio"] = round(hsteps[-1] / max(hsteps[0], 1e-9), 4)
    res["dth_settle_moving_frames"] = sum(1 for v in hsteps if v > 0.2)
    res["dth_settle_ok"] = bool(
        res["dth_settle_peak_mm"] <= SETTLE_PEAK_MAX_MM
        and res["dth_settle_tail_mm"] <= SETTLE_TAIL_MAX_MM
        and res["dth_settle_moving_frames"] >= SETTLE_MIN_MOVING_FRAMES)
    res["dth_settle_note"] = (
        "★ 清单 §6「起步慢、命中重、有惯性、**不许瞬停**」在**尾部**的量化。"
        "载体 = **头**（`head`）世界 z 在沉降窗 `[%d, %d]` 内的逐帧位移"
        "（= 清单 §2 的「沉降 40→60」）。三条：单帧峰值 ≤ %.0f mm（实测 %.3f）、"
        "末帧 ≤ %.1f mm（实测 %.4f ⟹ 已经停住）、「在动（> 0.2 mm）」帧数 ≥ %d"
        "（实测 %d ⟹ 动作是**铺开**的，不是一帧刹住）。产出 `%.4f` 的衰减比"
        "（末帧 / 首帧）。守卫 = `E10_TP_SNAP=1`（沉降压成单帧瞬停）⟹ 峰值与"
        "帧数两条同时见红。"
        % (REBOUND_TAIL, SETTLE_TAIL, SETTLE_PEAK_MAX_MM,
           res["dth_settle_peak_mm"], SETTLE_TAIL_MAX_MM,
           res["dth_settle_tail_mm"], SETTLE_MIN_MOVING_FRAMES,
           res["dth_settle_moving_frames"], res["dth_settle_decay_ratio"]))

    # ---- ⑪ 收招不许瞬停（沿用 E09 口径：末 8 帧）-------------------------
    snap, snap_at = 0.0, None
    for index in range(max(1, len(samples) - 8), len(samples)):
        step, at = _worst_step(samples, index - 1, index)
        if step > snap:
            snap, snap_at = step, at
    res["no_snap_stop_step_deg"] = round(snap, 4)
    res["no_snap_stop_at"] = snap_at
    res["no_snap_stop_ok"] = bool(snap <= NO_SNAP_END_DEG)

    # ---- ⑫ 穿模（臂 vs 头盒 + 臂 vs 腿）----------------------------------
    worst_clip, clip_at = 0.0, None
    worst_limb, limb_at = 1e9, None
    scan2 = sorted(set(list(range(START, END + 1, 3))
                       + [ANTIC_END, LAND, LAND_HOLD, REBOUND_TAIL, END]))
    for frame in scan2:
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

    # ---- ⑬ 可达性（全程）-------------------------------------------------
    # ★ 腿改成量「**踝是否真的到了设计目标**」，不量"髋踝距离 / 骨长"：
    #   解算器在超伸时会**自己截断**（`leg_solve` 的 `clipped`）⟹ "髋踝距离"
    #   永远 ≤ 上限，比值型判据**结构上不可能红**。首跑实测 1.00003 也只是
    #   因为分子用骨骼真长、分母用了 `A.L_THIGH/A.L_SHIN` 这对**取整到毫米**的
    #   常量（真值 0.410019/0.412005），纯口径不一致，不是设计问题。
    #   ⟹ 改成量残差 `|踝实测 − 踝设计目标|`（目标由 `death_pose` 逐帧登记在
    #   `TGT`）。它同时盯两件事：① 目标超出可达（腿"差一截"没伸到）；
    #   ② 解算器截断。容差 2 mm ≈ 截断余量 0.9995（≈0.41 mm）+ 浮点余量。
    worst_leg, worst_leg_at = 0.0, None
    worst_res, worst_res_at = 0.0, None
    worst_arm, worst_arm_at = 0.0, None
    for frame in range(START, END + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
            ratio = (ankle - hip).length / (L1 + L2)
            if ratio > worst_leg:
                worst_leg, worst_leg_at = ratio, (frame, side)
            if (frame, side) in TGT:
                residual = (ankle - Vector(TGT[(frame, side)])).length * 1000.0
                if residual > worst_res:
                    worst_res, worst_res_at = residual, (frame, side)
            sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
            r2 = (fist - sh).length / ((ARM_LEN_UP + ARM_LEN_LO)
                                       * REACH_MAX_RATIO)
            if r2 > worst_arm:
                worst_arm, worst_arm_at = r2, (frame, side)
    res["leg_reach_len_ratio_max"] = round(worst_leg, 5)
    res["leg_reach_len_at"] = worst_leg_at
    res["dth_leg_target_resid_mm"] = round(worst_res, 3)
    res["dth_leg_target_resid_at"] = worst_res_at
    res["leg_reach_ok"] = bool(worst_res <= LEG_REACH_RESID_MAX_MM
                               and worst_leg <= FULL_EXT_RATIO_MAX)
    res["leg_reach_note"] = (
        "★ 载体 = `|踝实测世界位置 − 踝设计目标|`（目标逐帧登记在 `TGT`），"
        "容差 %.1f mm；辅以「全长比」%.5f（≤ %.2f）。实测最大残差 **%.3f mm**"
        " @ f%s `%s`。★ 为什么不用「髋踝距离 / 骨长」：解算器超伸时**自己截断**，"
        "该比值**恒 ≤ 上限**，结构上不可红。守卫 = `E10_TP_LIMBJUMP=1`"
        "（f%d 给目标注入 %.0f mm 尖峰 ⟹ 残差直接爆）。"
        % (LEG_REACH_RESID_MAX_MM, worst_leg, FULL_EXT_RATIO_MAX, worst_res,
           worst_res_at[0] if worst_res_at else "?",
           worst_res_at[1] if worst_res_at else "?", LIMB_JUMP_FRAME,
           LIMB_JUMP_MM))
    res["arm_reach_ratio_max"] = round(worst_arm, 5)
    res["arm_reach_at"] = worst_arm_at
    res["arm_reach_ok"] = bool(worst_arm <= 1.0)

    # ---- ⑭ 相位标记 ------------------------------------------------------
    res["phase_markers"] = {"START": START, "ANTIC_END": ANTIC_END,
                            "IMPACT": LAND, "IMPACT_HOLD_END": LAND_HOLD,
                            "REBOUND_TAIL": REBOUND_TAIL,
                            "SETTLE_TAIL": SETTLE_TAIL, "END": END}
    res["phase_note"] = (
        "★ 按 SOUL「动作必须有前摇/命中/后摇」拆：前摇 0→%d（失去支撑、重心后倒，"
        "**无跪姿段**）、**命中帧 = %d**（背/臀触地 + 4 帧冻结）、"
        "回弹 %d→%d（头/四肢二次落地）、沉降 %d→%d、**尸僵 %d→%d**（零微动）、"
        "**可取消帧 = %d**（触地定格之后即可接 E11 `Revive`）。"
        % (ANTIC_END, LAND, LAND_HOLD, REBOUND_TAIL, REBOUND_TAIL,
           SETTLE_TAIL, SETTLE_TAIL, END, LAND_HOLD + 1))
    res["hold_window"] = [LAND, END]

    # ---- ⑮ 模型侧遗留的量化入册（上游缺陷，不是本支的判据）----------------
    hem_z = min(prof[END].get("Jacket_Hem", 1e9),
                prof[END].get("Jacket_Hem_Line", 1e9))
    res["dth_hem_float_mm"] = round(hem_z - res["dth_body_low_min_mm"], 2)
    res["dth_hem_float_note"] = (
        "★★★ **E09 登记的上游缺陷在本支更严重**：`Jacket_Hem` / `Jacket_Hem_Line`"
        "（未蒙皮，`vgroups=0`/`parent=null`）在尸体末帧悬于全身最低件之上 "
        "**%.0f mm**（衣摆 z = %.1f，全身最低件 z = %.1f）。"
        "E09 是**仰卧前**的过渡态，本支是**永久保持**的水平尸体 ⟹ 这块浮空薄板"
        "从「一瞬穿帮」升级为「尸体特写里的常驻穿帮」。定性 = **上游资产缺陷**，"
        "动画侧无权修（§6 硬约束：绝不回写 `bigman_tpose_v001.blend`）"
        "⟹ 按 E04/E05/E09 惯例**测量入册 + 排除出像素判据**，"
        "升级为**待主人决策的高优项**。"
        % (res["dth_hem_float_mm"], hem_z, res["dth_body_low_min_mm"]))
    return res


# =============================================================== 主流程
def boot():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    global BASE, TERM, BONE_LIST, ANKLE_REST, ANKLE_TERM, L1, L2
    TGT.clear()
    L1 = arm.data.bones["thigh.L"].length
    L2 = arm.data.bones["shin.L"].length
    if SEAM_ZERO:
        BASE = {}
        A.apply_pose(arm, BASE)
    else:
        BASE = IDLE.idle_pose(arm, 0.0)
    BONE_LIST = sorted(arm.pose.bones.keys())

    A.apply_pose(arm, BASE)
    ANKLE_REST = {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                  for s in SIDES}

    TERM = PB.build_supine(arm, **TERM_KW)
    A.apply_pose(arm, TERM)
    ANKLE_TERM = {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                  for s in SIDES}
    print("E10_BOOT %s" % json.dumps({
        "ankle_rest": {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]]
                       for s in SIDES},
        "ankle_term": {s: [round(v * 1000.0, 2) for v in ANKLE_TERM[s]]
                       for s in SIDES},
        "L1": round(L1, 6), "L2": round(L2, 6),
        "axis": AXIS,
    }, ensure_ascii=False))
    return arm, meshes


def main():  # noqa: C901
    arm, meshes = boot()
    keyframes = [(frame, death_pose(arm, frame))
                 for frame in range(START, END + 1)]
    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "状态与战斗流程",
        "note": ("死亡：失去支撑直接后倒（无跪姿段）→ 背/臀重摔（触地 4 帧冻结）"
                 "→ 头/四肢二次落地（回弹）→ 沉降 → 尸僵稳定（零微动）。"
                 "起点 = Idle_01@0 逐位，终点 = **仰卧尸体 Pose**（不是 E09 的伏地）"),
        "frame_bound_note": "★ 沿用 E01 登记的 E 族上界 120 帧 / 2.0 s",
        "hitstop_frames": "land[%d,%d]（★ 单段重摔 ⟹ 只有一个窗口）"
                          % (LAND, LAND_HOLD),
        "seam_in": "Idle_01@0",
        "end_pose": "supine_corpse_zero_motion",
        "terminal_pelvis_m": [0.640, 0.141],
        "root_motion_m": [0.0, 0.640],
        "distinct_from": "E09 Defeat（仰卧 vs 俯卧）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    markers = {"START": START, "ANTIC_END": ANTIC_END, "IMPACT": LAND,
               "IMPACT_HOLD_END": LAND_HOLD, "REBOUND_TAIL": REBOUND_TAIL,
               "SETTLE_TAIL": SETTLE_TAIL, "CANCEL": LAND_HOLD + 1, "END": END}
    A.add_markers(action, markers)
    A.set_hitstop(action, LAND, LAND_HOLD)

    samples = A.sample_animation(arm, action, START, END, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=(),
                                     slide_tolerance_mm=3.0)
    # ★ 通用 `ground_contact_ok` 的口径是「**鞋底** −2 ~ +6 mm」（站姿族）。
    #   本支末段是**仰卧尸体**：支撑面是**背/头/四肢**，鞋底只是其中一个件。
    #   ⟹ 原判据在本支**不适用**，按 E09 既有先例（非循环动作的 `loop_seamless`
    #   报 `null`）**显式置空 + 留痕**，替代判据 = `dth_body_ground_ok`
    #   （载体换成**全身最低件**，带 [−6, +8] mm）—— **不是删红灯，是换载体**。
    raw_ground = report.pop("ground_contact_ok")
    report["dth_common_ground_contact_raw"] = raw_ground
    report["dth_common_ground_contact_note"] = (
        "★ 原读数（鞋底口径 `ground_contact_ok`）= %r，**本支置空**：仰卧尸体的"
        "支撑面不是鞋底。替代判据 = `dth_body_ground_ok`（载体 = 全身最低件，"
        "带 [%.0f, %.0f] mm）。与 E09 同一处口径处理。"
        % (raw_ground, BODY_BAND[0], BODY_BAND[1]))
    report.update(dth_assertions(arm, action, samples, meshes))

    # ---- 接缝入：首帧逐位 = Idle_01@0 ------------------------------------
    upstream = bpy.data.actions["Idle_01"]
    seam = world_mats(arm, upstream, 0)
    mine = world_mats(arm, action, START)
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
    report["dth_seam_in_ok"] = report["seam_in_ok"]

    # ---- 终点自持：尸僵窗**逐位恒定**（f60 == f120）----------------------
    first = world_mats(arm, action, SETTLE_TAIL)
    last = world_mats(arm, action, END)
    end_elem, end_at = 0.0, None
    for bone in BONE_LIST:
        if bone in first and bone in last:
            for r in range(4):
                for c in range(4):
                    d = abs(first[bone][r][c] - last[bone][r][c])
                    if d > end_elem:
                        end_elem, end_at = d, (bone, r, c)
    report["dth_final_pose_elem_max"] = end_elem
    report["dth_final_pose_at"] = end_at
    report["dth_final_pose_ok"] = bool(end_elem <= FINAL_ELEM_MAX)
    report["dth_final_pose_note"] = (
        "★ 尸僵起点（f%d）与尾帧（f%d）**逐位一致**（57 骨 × 16 元素）⟹ "
        "「尸体姿」是**自持**的（不是「停在半口气」）。这是 `dth_zero_motion_ok`"
        "（只盯胸骨顶一根探针）的**全骨兜底**：任一骨在尸僵窗内漂移都会在这里见红。"
        % (SETTLE_TAIL, END))

    # ---- 相位矩阵步长（防万向节假跳）-------------------------------------
    worst_m, worst_m_at = 0.0, None
    prev = world_mats(arm, action, START)
    for frame in range(START + 1, END + 1):
        cur = world_mats(arm, action, frame)
        for bone in BONE_LIST:
            if bone in prev and bone in cur:
                pos, deg = _mat_delta(cur[bone], prev[bone])
                if deg > worst_m:
                    worst_m, worst_m_at = deg, (frame, bone)
        prev = cur
    report["phase_matrix_step_deg"] = round(worst_m, 4)
    report["phase_matrix_step_at"] = worst_m_at
    report["phase_matrix_step_ok"] = bool(worst_m <= PHASE_MATRIX_STEP_DEG)

    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True and v is not None)
    non_ok = sorted(k for k, v in report.items()
                    if isinstance(v, bool) and v is False)
    report["failed"] = failed
    report["non_ok_bools"] = non_ok
    A.report("E10_REPORT", report)

    if not SKIP_RENDER:
        key = [START, 6, ANTIC_END, 17, LAND, LAND_HOLD, 34, REBOUND_TAIL,
               50, SETTLE_TAIL, 90, END]
        A.render_pose_sheet(arm, action, key, "dthkey",
                            views=(VIEW_DTH_SIDE, VIEW_DTH_FRONT, VIEW_DTH_3Q))
        side = sorted(set(list(range(START, END + 1, 4)) + [END]))
        A.render_pose_sheet(arm, action, side, "dth",
                            views=(VIEW_DTH_SIDE,))
        A.save_project()
        A.export_glb(arm)
    print("E10_DONE failed=%s non_ok=%s" % (failed, non_ok))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E10_FAILURE " + traceback.format_exc())
