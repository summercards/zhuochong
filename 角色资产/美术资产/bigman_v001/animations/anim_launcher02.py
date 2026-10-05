"""anim_launcher02 —— C02 `Launcher` 击飞技（C 族第二支，**带 Root Motion**）。

=============================================================================
清单原文
=============================================================================
「攻击轨迹明确向上，命中瞬间身体必须有**爆发停顿**」。

选型：**后手上挑贯拳（rising rear-fist launcher）** —— 深蹲蓄力 → 双踮脚蹬伸 →
后手拳自裆前一路贯到头顶前上方 → 命中后 4 帧爆发停顿 → 收招回站架。

与近邻的区分：
  · B07 `Uppercut` 是**普通攻击**（单手上勾、前摇 14、幅度以"打得疼"为准）；
    C02 是 **C 族强表演技**：前摇 18 帧（更深更长）、拳的纵向行程 ≥1.2×Uppercut、
    双踮脚、命中停顿 4 帧、带 0.200 m Root Motion。
  · C01 `Combo_Finish` 是**向下**的双拳过顶劈砸（轨迹向下）；C02 是**向上**的贯拳。
  · C07 `Ground_Smash` 是"双拳高举后砸地"（有地面特效），落点在地面；
    C02 的落点在**头顶上前方**（把人掀起来，不是砸地）。

=============================================================================
第 0 件 —— "明确向上"必须先在**可判定量**上落地（`probe_launch02.py` 实测）
=============================================================================
"向上"不是量。第一探针（`probe_launch02.py`）把 B 族十支 + C01 全族逐帧实测，
只认**世界 z**（骨盆系里"向上"会被身体自转吃掉 —— C01 第 0 件已证明世界口径在
无位移时可比、有位移时要减掉平移；但"升起来没有"这件事**必须看世界 z**）：

    B 族(地面支) 髋 z 全程极差 max = Uppercut  357.0 mm  (615 → 972)
    B 族(地面支) 拳 z 全程极差 max = Uppercut 1235.0 mm  (695 → 1930)
    B 族(地面支) 拳 z 峰值     max = Uppercut 1929.98 mm
    （Air_Light / Air_Heavy 被排除：它们自带 813~1025 mm 抛物线，世界口径被
      位移污染、不可比 —— C01 第 0 件同款理由。Crouch / Jump_Start 是 A 族参考。）

★ 第 0 件 A —— **髋的上升率被腿长死死卡住，两个量必须分开定阈值**：

  "髋能抬多高"的物理上限 = `踝高 + sqrt((0.995·L)² − dy²)`，L = 822 mm（实测
  `probe_launch02` 的 LAUNCH02_REACH）。**踝不抬（平放，踝高 89 mm）时**，
  在接缝站架下髋最多到 858 mm —— 比 B07 的 972 mm 还低 **114 mm**。
  ⟹ 要"比最强的普通攻击还向上"，唯一出路是**把踝也抬起来**：实测踝高随足尖角
     89(0°) → 165(30°) → 187(40°) → 196(45°) mm。**踮脚是腿长约束下的唯一解**
     （不是"好看才加的装饰"）。
  但即便踮到 40°，髋的上限也只有 ≈ 987 mm ⟹ **髋的极差上界 ≈ 987 − 560 = 427 mm**，
  1.5×Uppercut = 535.5 mm 是**物理不可达**的（同 C01 第 0 件 A 的诚实登记）。
  ⟹ 髋阈值取 **1.10 × 357.0 = 392.70 mm**（C 族必须明确超过最强普通攻击，
     10% 是腿长预算里还剩得起的量级），并**同时登记实际利用率**。

★ 第 0 件 B —— 拳的纵向行程**没有几何天花板**，所以它承担更大的比率：

  臂链（肩→拳）0.65 m、躯干 0.52 m，都不接近极限 ⟹ 拳 z 极差可以做到
  ≈ 1.25×Uppercut。本期两条专属阈值：

    ① `launch_up_ok`      髋 z 极差      ≥ **1.10 × 357.0  = 392.70 mm**
    ② `fist_rise_up_ok`   打击拳 z 极差  ≥ **1.20 × 1235.0 = 1482.00 mm**

  两条都是"**C 族必须明确超过最强的地面普通攻击**"这同一条规则，比率不同是因为
  一个被腿长卡住、一个没有 —— 拍脑袋统一取一个比率才是负债。

=============================================================================
第 1 件 —— 上游接缝 = `Heavy_01@36`（B04 的可取消帧），出口 = `Idle_01@0`
=============================================================================
清单 §0.3 把 `CANCEL` 定义为"从这一帧起可接下一段连招"；C02 是"接在普通攻击之后"
的起手技 ⟹ 接的**就是**那一帧。同一接缝 C01 已用过（两支特殊技从同一个取消点
分支，是格斗游戏的常规结构）。实测 `Heavy_01@36`（LAUNCH02_SEAM）：

    pelvis 世界 = (3.34, −89.39, 806.68) mm   （髋 z ≡ 骨盆 z，实测差 0.00 mm）
    L 踝 = (152.18, −329.58, 79.74)  相对骨盆 **+240.20 mm（前）**  髋踝距 777.99
    R 踝 = (−141.58, 140.44, 79.80)  相对骨盆 **−229.82 mm（后）**  髋踝距 774.08

出口 = `Idle_01@0`（D 族**全部待做**，没有可接的落地动作 ⟹ 按 C01 同款回站架）。
`Idle_01@0`：pelvis (0, 0, 830)，L 踝相对骨盆 +169.57，R 踝 −140.43。

★ **出口姿态把 Root Motion 锁死了**：末帧 = Idle 姿态整体平移 `shift_y`。
  L 若要在整支里"钉死不动"，就要求

      L_END.y = idle_L.y + (PY0 − D) = L_SEAM.y
      ⟹ D = −329.58 + 169.57 + 89.39 = **D = 200.00 mm 时 L 必须上步 129.38 mm**

  ⟹ 本支取 **D_TOTAL = 0.200 m**（落在计划书 200~400 mm 预算的下沿）。
     两脚都要动：L 在蓄力段上步 129.38 mm，R 蹬离地后前落 289.40 mm。
     （若取 D = 70 mm 则 L 可以全程钉死，但那样整支没有任何横向驱动，
      读起来像"原地蹦"而不是"上步击飞"。）

=============================================================================
第 2 件 —— 脚步表：**后脚真正离地**，前脚全程支撑（唯一的合法解）
=============================================================================
命中帧骨盆 z ≈ 966、y ≈ −249。两脚都留在地面的话：

    R 踝在 +140.44 ⟹ dy = 389.8 ⟹ dz ≤ sqrt(817.89² − 389.8²) = 719.0
    ⟹ 髋 ≤ 84 + 719 = 803 mm —— **比接缝还低**，根本举不起来。

⟹ **后脚必须蹬离地**（这也正是"蹬地击飞"的写实形态：前脚是支点，后脚蹬完跟着身体走）。
   本支脚步表：

    L: 支撑 [0, 6] ∪ [16, 52]     摆动 (6, 16) = 10 帧，上步 129.38 mm
    R: 支撑 [0, 20] ∪ [42, 52]    腾空 (20, 42) = 22 帧，前落 289.40 mm
    ⟹ 任何一帧**至少一只脚在支撑**（f7~f15 靠 R、f21~f41 靠 L）。

R 的空中高度**不自由写**，用 `z = 骨盆 z − vert(u)`：`vert` 从蹬离值插值到
"落地帧骨盆 z − 落地踝高"，于是**落地帧由构造贴地**（否则会出现"骨盆还在 886、
脚已在 0"的 56 mm 单帧砸落）。

=============================================================================
第 3 件 —— 踮脚用**鞋底前缘滚动支点**模型（承 B07 第 1 件）
=============================================================================
平放时踝在"鞋底最低点"上方 `az0`；绕**鞋底最前缘那一行最低顶点**绕世界 X 轴刚性
旋转 θ 后：

    ankle_y(θ) = py + (ay0 − py)·cosθ − az0·sinθ
    ankle_z(θ) =        (ay0 − py)·sinθ + az0·cosθ      ← 之后由贴地闭环只调 z

**支点 x/y 由构造不变**（闭环只改 z），所以 `stance_pivot_ok` 量的是**接触点**
（鞋底最前缘最低顶点）的世界 (x,y) 漂移，而**不是踝**——踮脚时踝本来就该前移
（实测前移 ~100 mm），拿踝当尺子会假红（B07 已把支撑脚判据改成接触点口径）。

=============================================================================
第 4 件 —— 命停只冻**打击姿态**，不冻位移、不冻腿（承 B10 / C01）
=============================================================================
`HIT 30`、`HOLD 4`（f30~f33 关节欧拉逐位冻结）。骨盆照常上升 + 前冲
（D(33) − D(30) ≈ 20 mm）⟹ `hitstop_momentum_mm` > 10。腿照常工作 ——
把腿一起冻住，会让"上升 + 前冲的骨盆"把支撑脚从地上拔走。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_launcher02.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import json
import math
import os
import sys

import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_heavy_01 as H  # noqa: E402
import anim_run_stop as RS  # noqa: E402
import anim_walk_f as WF  # noqa: E402
import anim_jump_start as JS  # noqa: E402

NAME = "Launcher"
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
TOTAL = _env_i("C02_TOTAL", 52)                 # 0.867 s @60fps
ANTIC = _env_i("C02_ANTIC", 18)                 # 前摇结束（§0.1 重攻击 12~20 帧）
HIT = _env_i("C02_HIT", 30)                     # 命中帧
HOLD = _env_i("C02_HOLD", 4)                    # 命停 4 帧（§0.1 上限）
HOLD_END = HIT + HOLD - 1                       # 33
RETURN_START = HOLD_END + 1                     # 34
CANCEL = _env_i("C02_CANCEL", 42)

# ---------------------------------------------------------------- 脚步时刻表
T_L_OFF = _env_i("C02_L_OFF", 6)                # L（前脚）离地（上步开始）
T_L_ON = _env_i("C02_L_ON", 16)                 # L 落地（上步结束）
T_R_PIVOT = _env_i("C02_R_PIVOT", 14)           # R 开始提踵
T_R_OFF = _env_i("C02_R_OFF", 20)               # R 蹬离地
T_R_ON = _env_i("C02_R_ON", 42)                 # R 落地
WINDOWS = {"L": ((0, T_L_OFF), (T_L_ON, TOTAL)),
           "R": ((0, T_R_OFF), (T_R_ON, TOTAL))}
SIDES = ("L", "R")

TIP_HIT = _env_f("C02_TIP_HIT", 40.0)           # 命中帧足尖角（踮脚深度）
TIP_L_POW = _env_f("C02_TIP_L_POW", 1.30)       # L 提踵"起缓收快"
TIP_R_OFF = _env_f("C02_TIP_R_OFF", 32.0)       # R 蹬离瞬间足尖角
TIP_R_DECAY = _env_i("C02_TIP_R_DECAY", 38)     # R 空中足尖角归零帧
TIP_TAIL_END = _env_i("C02_TIP_TAIL_END", 46)   # L 提踵归零帧
SWING_TIP = _env_f("C02_SWING_TIP", 6.0)        # L 摆动期足尖角峰值
L_LIFT = _env_f("C02_L_LIFT", 0.090)            # L 上步离地峰值（米）
L_SWING_POW = _env_f("C02_L_SWING_POW", 1.60)   # L 摆动位移前端发力指数
R_SWING_POW = _env_f("C02_R_SWING_POW", 1.35)
SOLE_FLOOR_MM = _env_f("C02_SOLE_FLOOR", -0.8)
LEG_TAIL_START = _env_i("C02_LEGTAIL0", T_R_ON)
_LEG_EASE = os.environ.get("C02_LEGEASE", "quad")
# 手臂收招缓动的指数 p（`s = 1 − (1−u)^p`）。见 build_pose 收招段的推导：
#   quad(2u−u²) ≡ p=2 起速 2.0；p=1.5 起速 1.5。**只有 p 在这里有物理含义**。
_ARM_EASE_P = _env_f("C02_ARMEASE", 1.5)

# ---------------------------------------------------------------- Root Motion
# 骨盆前冲量 D（mm，正 = 向前 = 世界 −y）。Hermite 轨道：先**向后坐**（反向预备），
# 再爆发前冲，再收。末值 = D_TOTAL。
D_TOTAL_MM = _env_f("C02_D_TOTAL", 200.0)
# ★ 前冲必须**在命中帧之前走完**（第 2 轮修的）：髋越靠前，单支撑腿的
#   髋踝距越短。旧的 24→110 / 30→160 / 36→195 让命中时髋还落后 20 mm，
#   两个后手都不够，`ik_reach_ok` 直接红 12.2 mm。
#   这里让轨道在 HIT 处**贴到 208（> 预算 200）**，再靠 `D_mm` 的硬上限截平 ——
#   截平点就是"蹬地、停止前冲"的物理瞬间，不是过冲。
D_KEYS = ((0, 0.0), (8, _env_f("C02_D8", -30.0)),
          (ANTIC, _env_f("C02_D18", -22.0)), (24, _env_f("C02_D24", 120.0)),
          (HIT, _env_f("C02_D30", 208.0)), (TOTAL, 208.0))


def D_mm(frame):
    """Root Motion 位移（mm）。**硬上限 = D_TOTAL_MM**，禁止 Hermite 过冲。"""
    return min(RS.track(D_KEYS, frame), D_TOTAL_MM)


def _swing_u(s, power):
    """摆动归一化位移：`1 − (1−s)^p`（前端发力）。"""
    return 1.0 - (1.0 - max(0.0, min(1.0, s))) ** power


# ---------------------------------------------------------------- 躯干轨道
# 每条轨道 **frame 0 的值由上游接缝（Heavy_01@36）在 main() 里回填**。
# rx > 0 = 前屈 / 前倾；rx < 0 = 上拔 / 后仰。Idle 的末值见括号。
PELVIS_RX = ((0, 0.0), (8, 13.0), (13, 20.0), (18, 22.0), (24, 4.0),
             (30, -10.0), (33, -12.0), (38, -6.0), (44, 0.0), (TOTAL, 4.0))
PELVIS_RY = ((0, 0.0), (12, 6.0), (18, 7.0), (26, -3.0), (HIT, -9.0),
             (38, -5.0), (46, -1.0), (TOTAL, 0.0))
SPINE01_RX = ((0, 0.0), (8, 11.0), (13, 18.0), (18, 20.0), (24, 3.0),
              (30, -8.0), (33, -10.0), (38, -5.0), (44, 0.0), (TOTAL, 2.0))
SPINE01_RY = ((0, 0.0), (18, 5.0), (HIT, -6.0), (38, -3.0), (TOTAL, 0.0))
SPINE02_RX = ((0, 0.0), (8, 11.0), (13, 18.0), (18, 20.0), (24, 3.0),
              (30, -8.0), (33, -10.0), (38, -5.0), (44, 0.0), (TOTAL, 2.0))
SPINE02_RY = ((0, 0.0), (18, 5.0), (HIT, -6.0), (38, -3.0), (TOTAL, 0.0))
CHEST_RX = ((0, 0.0), (8, 10.0), (13, 17.0), (18, 20.0), (24, 1.0),
            (30, -14.0), (33, -16.0), (38, -8.0), (44, -1.0), (TOTAL, 1.0))
CHEST_RY = ((0, 0.0), (18, 6.0), (HIT, -8.0), (38, -4.0), (TOTAL, 0.0))
# 颈/头**反向**：深蹲时抬头盯人（rx<0 = 后仰），贯拳时头随拳上抬再收。
NECK_RX = ((0, 0.0), (10, -8.0), (18, -11.0), (24, -6.0), (HIT, -15.0),
           (33, -15.0), (40, -10.0), (TOTAL, -6.0))
NECK_RY = ((0, 0.0), (18, -3.0), (HIT, 4.0), (38, 2.0), (TOTAL, 0.0))
HEAD_RX = ((0, 0.0), (18, 3.0), (24, -2.0), (HIT, -8.0), (38, 0.0), (TOTAL, 5.0))
HEAD_RY = ((0, 0.0), (18, -2.0), (HIT, 3.0), (38, 1.0), (TOTAL, 0.0))
# 肩带（rx 越负 = 越沉；Idle = −18）：打击侧**上抬**（→ −3），护手侧**下沉**（→ −28）。
SHOULDER_L_RX = ((0, 0.0), (10, -10.0), (18, -16.0), (24, -23.0), (HIT, -28.0),
                 (33, -28.0), (40, -23.0), (TOTAL, -18.0))
SHOULDER_R_RX = ((0, 0.0), (10, -12.0), (18, -18.0), (24, -9.0), (HIT, -3.0),
                 (33, -3.0), (40, -10.0), (TOTAL, -18.0))
# rz 两侧镜像：L rz>0 = 向后、R rz>0 = 向前（rig_axis_map 实测）。
SHOULDER_L_RZ = ((0, 0.0), (18, 6.0), (24, -6.0), (HIT, -14.0), (38, -6.0),
                 (TOTAL, 0.0))
SHOULDER_R_RZ = ((0, 0.0), (18, -6.0), (24, 6.0), (HIT, 14.0), (38, 6.0),
                 (TOTAL, 0.0))

# 骨盆世界位移：蓄力**下沉 259 mm**，蹬伸后**升到 948 mm**，收招回 830。
# ★ 峰值 948 不是拍的，是**解出来的**（第 2 轮）：
#   命中帧 L 是唯一支撑脚，髋踝距 ≥ |髋z − 踝z| 与 |髋y − 踝y| 的合成，
#   实测 L_END 落点下 40° 踮脚的踝是 (−557.7, 192.5)，髋在 (−289.4, z)：
#   z ≤ 956.2 才使 reach ≤ 0.995×822 = 817.89 —— 留 8 mm 余量取 948。
#   少了的抬髋量由**更深的蓄力**补回来（548 而非 570），净上升 400 mm 仍 ≥ 392.7。
#   另：命中后仍在升（933→948 = 15 mm）⟹ 命停期"冻关节不冻位移"成立。
PELVIS_X = ((0, 0.0), (10, 0.010), (18, 0.016), (26, 0.024), (HIT, 0.026),
            (38, 0.014), (46, 0.004), (TOTAL, 0.0))
PELVIS_Z = ((0, 0.80668), (6, 0.7520), (12, 0.6560), (ANTIC, 0.5480),
            (21, 0.6400), (24, 0.7800), (27, 0.8800), (HIT, 0.9330),
            (33, 0.9480), (37, 0.9200), (T_R_ON, 0.8500), (47, 0.8400),
            (TOTAL, 0.8300))
Z_SEAM = PELVIS_Z[0][1]

# ---------------------------------------------------------------- 手臂方向轨道
# 世界单位向量（x = 左正，y = 身后正，z = 上正）。
ARM_KEYS = {
    # 前摇：**后手拳沉到裆前**（拳 z 越低，后半段"向上"的行程越长），护手收紧。
    "ANTIC": {
        "upperarm.R": (-0.10, 0.40, -0.91),
        "forearm.R": (-0.05, 0.22, -0.975),
        "hand.R": (-0.02, 0.14, -0.99),
        "upperarm.L": (0.30, -0.06, -0.952),
        "forearm.L": (0.16, -0.44, 0.883),
        "hand.L": (0.08, -0.66, 0.747),
    },
    # 命中：后手拳**贯到头顶前上方**（方向近乎竖直），护手甩到身后下方配重。
    "HIT": {
        "upperarm.R": (-0.16, -0.24, 0.957),
        "forearm.R": (-0.12, -0.20, 0.972),
        "hand.R": (-0.08, -0.16, 0.984),
        "upperarm.L": (0.34, 0.34, -0.877),
        "forearm.L": (0.26, 0.22, -0.940),
        "hand.L": (0.18, 0.12, -0.976),
    },
    # 收招：回到护体（≈ Idle 的 ARM_DIRS，末段沿欧拉斜坡逐位收敛）。
    "SETTLE": {
        "upperarm.R": (-0.24, -0.30, -0.862),
        "forearm.R": (0.10, -0.42, 0.902),
        "hand.R": (0.06, -0.62, 0.782),
        "upperarm.L": (0.30, -0.22, -0.928),
        "forearm.L": (-0.20, -0.44, 0.874),
        "hand.L": (-0.12, -0.70, 0.704),
    },
}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_PHASES = ((0, "SEAM", _env_p("C02_PH0", "smooth")),
              (ANTIC, "ANTIC", _env_p("C02_PH1", "smooth")),
              (HIT, "HIT", _env_p("C02_PH2", "linear")),
              (HOLD_END, "HIT", "linear"),
              (T_R_ON, "SETTLE", "smooth"), (TOTAL, "END", "smooth"))

# ---------------------------------------------------------------- 命停该冻谁
HITSTOP_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "shoulder.L", "shoulder.R",
                 "upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R")


def _hold(frame):
    return HIT < frame <= HOLD_END


# ---------------------------------------------------------------- 门禁阈值
SOLE_RANGE_MM = (-2.0, 6.0)
PIVOT_DRIFT_MAX_MM = 3.0
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
# ---- 「向上」：基准来自 probe_launch02（B 族**地面支**全族最大 = Uppercut）
BMAX = {"pelvis_z_rise_mm": 357.0, "fist_z_rise_mm": 1235.0,
        "fist_z_peak_mm": 1929.98}
HIP_RATIO = 1.10          # 髋被腿长卡住（文件头第 0 件 A）
FIST_RATIO = 1.20         # 拳没有几何天花板（文件头第 0 件 B）
HIP_RISE_MIN_MM = _env_f("C02_HIP_MIN", BMAX["pelvis_z_rise_mm"] * HIP_RATIO)
FIST_RISE_MIN_MM = _env_f("C02_FIST_MIN", BMAX["fist_z_rise_mm"] * FIST_RATIO)
RISE_MONO_MIN = _env_f("C02_MONO_MIN", 0.90)
UP_DOMINANCE_MIN = _env_f("C02_UPDOM_MIN", 0.70)   # |Δz| / 路径 ≥ 0.70 ⟹ 读作"向上"

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
SEAM_EULER = {}
SEAM_SOURCE = {}
PIVOT = {}          # (side, window_index) -> (px, py, pz)（支点世界 x/y + 高出鞋底最低点）
PIVOT_VERT = {}     # (side, window_index) -> (物体名, 顶点序号)（就是上面那个 px/py 所在的顶点）
FLAT_ANK = {}       # (side, window_index) -> (ax0, ay0, az0)（tip=0 贴地时的踝与踝高）
PIVOT_AXIS = {}     # (side, window_index) -> Vector（实测滚动轴，世界系；= 骨架 X 轴投影）
PIVOT_SCALE = {}    # (side, window_index) -> float（实测角比例 k；θ_eff = k·θ）
_PIVOT_K_DEFAULT = 1.0
FROZEN_SHIFT = {}
WINDOW_SOLE = {}
AIR_SOLE = {}
LEG_TAIL_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
_TAIL_ANCHOR = {}
_LEG_ANCHOR = {}
_KNEE_ANCHOR = {}
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
R_VERT0 = 0.0
R_VERT1 = 0.0
R_OFF_ANK = None
PELVIS_Z0 = 0.0
PELVIS_Z1 = 0.0


# =============================================================== 脚步与踝目标
def window_of(side, frame):
    for index, (a, b) in enumerate(WINDOWS[side]):
        if a <= frame <= b:
            return index
    return None


def tip_of(side, frame):
    """足尖角（度，+ = 压脚背 / 踮脚）。"""
    if side == "L":
        if frame <= T_L_OFF:
            return 0.0
        if frame < T_L_ON:
            s = (frame - T_L_OFF) / float(T_L_ON - T_L_OFF)
            return SWING_TIP * math.sin(math.pi * s) ** 0.7
        if frame <= HIT:
            s = (frame - T_L_ON) / float(HIT - T_L_ON)
            return TIP_HIT * (s ** TIP_L_POW)
        if frame <= HOLD_END:
            return TIP_HIT
        if frame >= TIP_TAIL_END:
            return 0.0
        s = (frame - HOLD_END) / float(TIP_TAIL_END - HOLD_END)
        return TIP_HIT * (1.0 - s) ** 1.40
    # R
    if frame <= T_R_PIVOT:
        return 0.0
    if frame < T_R_OFF:
        s = (frame - T_R_PIVOT) / float(T_R_OFF - T_R_PIVOT)
        return TIP_R_OFF * (s ** 1.60)
    if frame >= TIP_R_DECAY:
        return 0.0
    s = (frame - T_R_OFF) / float(TIP_R_DECAY - T_R_OFF)
    return TIP_R_OFF * (1.0 - s) ** 1.30


def _pivot_ankle(key, tip):
    """绕**实测**滚动支点解出该足尖角下的踝世界目标（Vector）。

    ★ 为什么不用解析式（第 3 轮实测逼出来的）：
      `keep_world_orientation` 把脚钉的是**骨架空间**的 rest 基，`WF.add_world_rx`
      也是对 `pose_bone.matrix` 前置一个骨架空间 R_x —— 理论上是精确的绕世界 X 转，
      实测脚骨 3×3 也确实 = `R_x(θ)·平放基`。所以问题**不在旋转**。

    ★ 真正错的是"支点在上还是在地"（第 4 轮实测逼出来的）：
      鞋头是圆拱的，实测鞋底最前那颗顶点高出鞋底最低点 **11.1 mm（左）/ 13.6 mm（右）**。
      若把支点当贴地点（pz = 0），`R_x(θ)` 会把这段 z 混进 y：
          a_true − a_model = (0, 0, pz) − R_x(θ)·(0, 0, pz)
                           = (0, +pz·sinθ, pz·(1−cosθ))
      踝目标少算 `pz·sinθ` ⟹ 整个脚**前移** `pz·sinθ`。
      实测前移：40° → 7.11 mm（= 11.12·sin40°）；32° → 7.22 mm（= 13.62·sin32°）。
      两条独立数据都把 pz 反解回同一量级，所以这不是拟合，是量出来的几何。
    """
    ax0, ay0, az0 = FLAT_ANK[key]
    px, py, pz = PIVOT[key]
    rel = Vector((px - ax0, py - ay0, pz - az0))
    rot = Matrix.Rotation(
        math.radians(tip * PIVOT_SCALE.get(key, _PIVOT_K_DEFAULT)), 3,
        PIVOT_AXIS.get(key, Vector((1.0, 0.0, 0.0))))
    v = rot @ rel
    return Vector((px - v.x, py - v.y, pz - v.z))


def sole_target(frame):
    """该帧每只脚**期望的鞋底离地量**（米）。None = 不闭环（模型自己管）。"""
    out = {}
    if T_L_OFF < frame < T_L_ON:
        s = (frame - T_L_OFF) / float(T_L_ON - T_L_OFF)
        out["L"] = L_LIFT * math.sin(math.pi * s) ** 2.0
    else:
        out["L"] = 0.0
    out["R"] = None if T_R_OFF < frame < T_R_ON else 0.0
    return out


def ankle_targets(frame, shift):
    """返回 {"L": (x, y, z, tip), ...}：踝世界目标 + 足尖角。"""
    out = {}
    for side in SIDES:
        tip = tip_of(side, frame)
        idx = window_of(side, frame)
        if idx is not None:
            key = (side, idx)
            ank = _pivot_ankle(key, tip)
            x, y = ank.x, ank.y
            z = ank.z + shift[side]
        else:
            key = (side, 1)
            start_key = (side, 0)
            z1 = FLAT_ANK[key][2]
            if side == "L":
                a = L_SEAM
                b = L_END
                s = (frame - T_L_OFF) / float(T_L_ON - T_L_OFF)
                u = _swing_u(s, L_SWING_POW)
                x = a.x + (b.x - a.x) * u
                y = a.y + (b.y - a.y) * u
                z = (1.0 - u) * FLAT_ANK[start_key][2] + u * z1 \
                    + L_LIFT * math.sin(math.pi * s) ** 2.0
            else:
                # R 腾空：z = 骨盆 z − vert(u)，**落地帧由构造贴地**（文件头第 2 件）
                s = (frame - T_R_OFF) / float(T_R_ON - T_R_OFF)
                u = _swing_u(s, R_SWING_POW)
                # ★ 起点必须是**蹬离瞬间的踝**（已带 32° 踮脚的支点位移），
                #   不能拿接缝踝当起点 —— 那会留下 70.7 mm 的单帧跳。
                a = R_OFF_ANK
                b = R_END
                x = a.x + (b.x - a.x) * u
                y = a.y + (b.y - a.y) * u
                # ★ `s^1.10` 在 s→1 处导数为正 ⟹ 落地是在**加速**，
                #   f41→f42 一帧里 shin.R 转 13.33° ⟹ `decel_smooth_ok` 红。
                #   换成 smoothstep：两端导数都为 0 ⟹ 蹬离和着地都是"软端点"，
                #   末帧 vert 增量从 17 mm 掉到 2 mm，落地那一步自然收敛。
                ss = s * s * (3.0 - 2.0 * s)
                vert = R_VERT0 + (R_VERT1 - R_VERT0) * ss
                z = RS.track(PELVIS_Z, frame) - vert
        out[side] = (x, y, z, tip)
    return out


SEAM_ANK = {}


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
        "shoulder.L": (RS.track(SHOULDER_L_RX, f), 0.0,
                       RS.track(SHOULDER_L_RZ, f)),
        "shoulder.R": (RS.track(SHOULDER_R_RX, f), 0.0,
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


# ---------------------------------------------------------------- 手臂：世界步进封套
# `JS.aim_carry` 的 roll 搜索最小化的是**欧拉步长**（+ |Y| 越界惩罚），世界旋转
# 不在代价里。本支实测（第 5 轮）：默认参数下 f24 被选中一支"欧拉步长 39.8°、
# 世界步进 55.5°，其中 **35.4° 是纯绕骨轴扭转**"的解 —— 门禁口径看着像改善，
# 观感上却是小臂拧一下再拧回来。
#
# ★ 为什么扭转会累积（第 6 轮想清楚的）：
#   `aim_carry` 的基准取**上一帧已达成朝向**，再补一个最小旋转把骨轴摆到目标方向。
#   连续做"最小旋转接力"时，方向走大圆弧会带来 **holonomy（和乐）扭转** ——
#   本支后手要从裆前 (−0.10, 0.40, −0.91) 甩到头顶 (−0.16, −0.24, 0.957)，
#   夹角 162°，12 帧走完，扭转就在这段里累积、出弧后释放。
#   实测 twist 余量 (dW − dA)：0 → **35.4** → 15.1 → 7.1 → 1.4 → 0，是一条**连续**
#   曲线，不是单帧跳 —— 所以它不违反 `no_teleport` 的"真旋转"语义，
#   但它把世界步进顶到了 55°。
#
# ★ 判据不动的修法：绕骨轴的 roll **不改变骨轴方向**（dA 一字不变），
#   却能整体搬动扭转。于是在定方向之后，**全扫 roll ∈ [−180, 180]**，
#   取 `(max(欧拉步长, 世界步进), 欧拉步长)` 字典序最小的一支：
#   只要能找到 dW ≈ dA 的解，扭转就被压掉，而方向判据（`trajectory_up_ok`、
#   `fist_z_*`、`power_chain`）全部不受影响。这是"只动滚转、不动方向"，
#   **不是放宽容差**。
# ★ 被判据逼出来的第三件事（第 6 轮）：窗口不能开满。
#   全扫 ±180° 虽然能把扭转压得更干净，却把 `|euler Y|` 顶到 **95.79°**
#   （原实现 66.28°，±60° 窗口 73.4°）—— 那已经越过万向节锁，
#   表示本身变得病态。所以窗口取 ±60°：够压扭转，又不撞锁。
#   收窄后 f24 的欧拉逐分量步长**下限**仍是 39.3°：骨轴每帧转 20.09°，
#   在 |Y|≈66° 处放大 `sec 66° ≈ 2.46` 倍 —— `25° × 2.46 = 61°` 也压不住时，
#   说明这是**表示放大**，不是"真瞬移"。故另立一条更贴语义的判据
#   `world_step_ok`（量**世界 3×3 测地角**，见 `arm_world_step`），
#   欧拉口径的 `no_teleport` 如实报红、进遗留问题，**不放宽**。
#
# =============================================================================
# 第 10 轮 —— 把"瞬移"拆成**三把尺子**，放大系数全部实测
# =============================================================================
# 同一个 f23→f24（upperarm.R），三条口径给出三个数：
#
#   ① 欧拉逐分量（`anim_lib` 的 `no_teleport` 口径）  **58.6°**   ← 通道口径
#   ② 骨自身局部旋转真实转角（`_local_step_deg`）      **26.9°**   ← 关节转角
#   ③ 世界 3×3 测地角（`arm_world_steps`）             **23.0°**   ← 观众看到的
#
# ★ ①的放大系数是**实测**的，不是推的：用 Blender 4.5 的 `Euler(..., 'XYZ')`
#   逐位复核 `forearm.L` f28→f29（该帧父骨 `upperarm.L` 只动 1.28°，②③应当相等）
#       Euler XYZ 合成 → ② 8.41°   vs 探针 ③ 8.81°  ⟹ 公式口径正确
#       而 `no_teleport` 对同一步报 **38.91°**     ⟹ 4.6 倍放大
#   原因是那一帧 |euler Y| 从 −84.29 穿到 −92.58，**正在万向节锁上**。
#   ①在锁附近**没有梯度**（同一帧所有 roll 取值的欧拉下限是同一个病态数），
#   所以它既不能做优化目标、也不能做物理判据 —— 只保留为**通道安全**上报。
#
# ★ ②③ 才是物理量，都 ≤25° 才算"没有真瞬移"。实测：
#     ③ = 22.99°（绿，f24 hand.R）  —— 第 10 轮由 27.18° 压下来的
#     ② = 26.9°（红，f23 upperarm.R，超 7.7%）
#   ② 的 25° 是**从①借来的**，本支没有独立标定过它 ⟹ 登记不判红。
#   要把它压进 25° 只剩"把 12 帧的 162° 摆拳摊到 14 帧以上"一条路，
#   而那会级联改动 HIT / HOLD_END / T_R_ON 整套帧预算 —— 那是**改设计换数字**，
#   不是修门禁，本轮不做（登记进遗留问题）。
ROLL_SWEEP_DEG = _env_f("C02_ROLLSWEEP", 60.0)
ROLL_SWEEP_COARSE = _env_f("C02_ROLLCOARSE", 5.0)
ROLL_SWEEP_FINE = _env_f("C02_ROLLFINE", 1.0)
ROLL_SWEEP_ENGAGE = _env_f("C02_ROLLGATE", 6.0)
# 探调用：`pure` = 只用最小旋转接力（不做任何 roll 搜索）。
CARRY_MODE = os.environ.get("C02_CARRY", "bounded")


def _world_step_deg(prev_q, quat):
    if prev_q is None:
        return 0.0
    return math.degrees(prev_q.rotation_difference(quat).angle)


def _roll_goal(prev_q, want):
    y_prev = (prev_q @ Vector((0.0, 1.0, 0.0))).normalized()
    return y_prev.rotation_difference(want) @ prev_q


def _local_step_deg(prev_e, e):
    """两帧 `rotation_euler`（度）之间的**骨自身局部旋转**真实转角（度）。

    ★ 这是 `no_teleport` 那条"逐分量"尺子的**正确版本**（第 10 轮定稿）：
      把欧拉按 Blender 的 XYZ 合成还原成 3×3，再取测地角。已用 Blender 逐位复核
      `forearm.L@29`：本函数 8.41° vs 探针世界口径 8.81°（该帧父骨只动 1.28°，
      两者应当相等）⟹ 公式口径正确。而 `no_teleport` 对同一步报 **38.91°**
      （|Y| 从 −84.29 穿到 −92.58，正在万向节锁上）—— 4.6 倍放大，纯表示。
    """
    if prev_e is None:
        return 0.0
    a = Euler([math.radians(v) for v in prev_e], "XYZ").to_matrix()
    b = Euler([math.radians(v) for v in e], "XYZ").to_matrix()
    return math.degrees((a.transposed() @ b).to_quaternion().angle)


def aim_carry_bounded(arm, name, direction):
    """`JS.aim_carry` + 以 `max(欧拉步长, 世界步进)` 为代价的 roll 全扫接力。"""
    prev_q = JS.ARM_QUAT.get(name)
    prev_e = JS._PREV_EULER.get(name)
    prev_roll = JS.ARM_ROLL.get(name, 0.0)
    want = Vector(direction).normalized()

    if CARRY_MODE == "pure":
        # 最小旋转接力：世界步进 = 骨轴转角（构造最小），扭转零累积。
        q = (prev_q if prev_q is not None else None)
        if q is None:
            q = arm.pose.bones[name].matrix.to_quaternion()
        q = _roll_goal(q, want)
        JS._set_world_quat(arm, name, q)
        e = JS._unwrap_xyz(prev_e, tuple(
            math.degrees(v) for v in arm.pose.bones[name].rotation_euler))
        JS.ARM_QUAT[name] = q
        JS.ARM_ROLL[name] = 0.0
        JS.MAX_ABS_EULER_Y = max(JS.MAX_ABS_EULER_Y, abs(e[1]))
        return e

    e = JS.aim_carry(arm, name, direction)
    if prev_q is None:
        return e

    d_w = _world_step_deg(prev_q, JS.ARM_QUAT[name])
    if d_w <= ROLL_SWEEP_ENGAGE:
        return e

    q0 = _roll_goal(prev_q, want)

    def cost_of(roll):
        """该 roll 下的 `(max(世界步进, 局部转角) 分档, 世界步进分档, 欧拉步长 + |Y| 惩罚)`。

        ★ 主键用 **max(世界步进, 局部转角)** —— 第 10 轮把次键里那把"欧拉逐分量"
          换成**局部真实转角**（`_local_step_deg`，用 Blender 的 XYZ 合成还原 3×3 后
          取测地角）。理由：欧拉逐分量在 `|Y|→90°` 处没有梯度（所有 roll 的取值都
          是同一个病态数），做次键只会把解推向更差的一支；而局部转角是有梯度的
          物理量。世界步进仍是并列主键，避免"为了压局部而多拧扭转"。
        """
        q = Quaternion(want, math.radians(roll)) @ q0
        step = _world_step_deg(prev_q, q)
        euler = JS._unwrap_xyz(prev_e, JS._set_world_quat(arm, name, q))
        local = _local_step_deg(prev_e, euler)
        penalty = JS._euler_step(prev_e, euler) + JS._y_penalty(euler)
        return (round(max(step, local) / 2.0), round(step / 2.0),
                penalty), roll, euler

    best = None
    for roll in JS._frange(prev_roll - ROLL_SWEEP_DEG,
                           prev_roll + ROLL_SWEEP_DEG, ROLL_SWEEP_COARSE):
        cand = cost_of(roll)
        if best is None or cand[0] < best[0]:
            best = cand
    anchor = best[1]
    for roll in JS._frange(anchor - ROLL_SWEEP_COARSE,
                           anchor + ROLL_SWEEP_COARSE, ROLL_SWEEP_FINE):
        cand = cost_of(roll)
        if cand[0] < best[0]:
            best = cand

    q_best = Quaternion(want, math.radians(best[1])) @ q0
    JS._set_world_quat(arm, name, q_best)
    JS.ARM_QUAT[name] = q_best
    JS.ARM_ROLL[name] = best[1]
    best_e = JS._unwrap_xyz(prev_e, best[2])
    JS.MAX_ABS_EULER_Y = max(JS.MAX_ABS_EULER_Y, abs(best_e[1]))
    JS.ROLL_MAX[name] = max(JS.ROLL_MAX.get(name, 0.0), abs(best[1]))
    return best_e


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
        #   缓动必须**凹**（s' 单调不增）⟹ 逐帧增量单调递减，`decel_smooth_ok` 是构造出来的；
        #   且 `s(1)=1、s'(1)=0` ⟹ 末帧增量 → 0，`no_snap_stop_ok` 也是构造出来的。
        # ★ 第 10 轮改的（f34 世界步进 27.18° 红的真因）：
        #   `s = 1 − (1−u)^p` 与 `s = 2u − u²` 端点同为 (0,0)/(1,1)、同为凹、s'(1)=0，
        #   唯一差别是**起速** `s'(0) = p`：
        #       quad (p=2)   首帧吃掉全段 10.25% ⟹ f34 欧拉步 17.19°、世界步进 27.18°
        #       p=1.5        首帧吃掉 7.60%         ⟹ f34 欧拉步 12.75°、世界步进 ≈20°
        #   逐帧增量：p=2 → 17.19 … 1.394；p=1.5 → 12.75 … 2.03（都单调递减、末项 ≤5°）。
        #   **不是放宽容差**：`no_teleport`/`world_step_ok` 的 25° 一个字没动。
        u = (frame - HOLD_END) / float(TOTAL - HOLD_END)
        s = 1.0 - (1.0 - u) ** _ARM_EASE_P
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
            pose[bone] = aim_carry_bounded(arm, bone, dirs[bone])
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
    """把骨指向 `direction`，**滚转沿用参考姿态**（`A.aim_bone` 只定方向、滚转是副产物）。"""
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
    """**逐帧实测贴地闭环**（本支**不冻结** shift）。

    为什么不冻结：C01 冻结是因为它整个支撑窗口里足尖角恒定；本支的支撑窗口里
    足尖角要从 0° 扫到 40°（踮脚），踝高随之变 98 mm —— 冻结 shift 会让鞋底
    在扫的过程中穿地或悬空。而 shift 只改 **z** ⟹ 支点 x/y 仍由构造不变，
    `stance_pivot_ok` 照样守得住。
    """
    shift = {side: 0.0 for side in SIDES}
    snap = _snapshot_carry()
    pose = build_pose(arm, frame, shift)
    if meshes is None:
        return pose
    want = sole_target(frame)
    active = [s for s in SIDES if want[s] is not None]
    for _ in range(4):
        if not active:
            break
        low = A.foot_lowest_by_side()
        error = {s: want[s] - low[s][2] for s in active if low[s] is not None}
        if not error or max(abs(v) for v in error.values()) < 5e-5:
            break
        for side, value in error.items():
            shift[side] += value
        _restore_carry(snap)
        pose = build_pose(arm, frame, shift)

    _restore_carry(snap)
    pose = build_pose(arm, frame, shift)
    if meshes is not None:
        low = A.foot_lowest_by_side()
        for side in SIDES:
            idx = window_of(side, frame)
            if idx is not None and low[side] is not None:
                WINDOW_SOLE.setdefault((side, idx), []).append(low[side][2])
            elif low[side] is not None:
                AIR_SOLE.setdefault(side, []).append(low[side][2])
        FROZEN_SHIFT[frame] = dict(shift)
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


def arm_world_steps(arm, action):
    """逐帧量**世界 3×3 的测地角**（度）—— 比欧拉逐分量更贴 `no_teleport` 的语义。

    ★ 为什么另立一把尺子（第 6 轮实测逼出来的）：
      `no_teleport` 量的是 `rotation_euler` **逐分量**最大增量。那是"通道口径"，
      在万向节锁附近会被放大 `sec|Y|` 倍：本支 f24 的骨轴只转 20.09°，
      但 |euler Y| ≈ 66°，`sec 66° ≈ 2.46` ⟹ 逐分量要走近 39°。
      探针 `probe_c02_teleport` 实测同一帧：
          欧拉步长 39.83° / 世界测地角 55.49°，其中 **35.4° 是纯绕骨轴扭转**。
      扭转靠 `aim_carry_bounded` 压回 ~20° 之后，**世界旋转已经正常**，
      剩下的 39° 全是表示放大。所以两把尺子必须分开报：
          世界口径（本函数） = 观众看到的旋转，判据 ≤ 25°；
          欧拉口径（`no_teleport`）= 逐分量插值的通道安全，如实报红、不放宽。
    """
    mats = {}
    for frame in range(0, TOTAL + 1):
        raw = RS.action_world_matrices(arm, action, frame)
        mats[frame] = {
            name: Matrix([raw[name][i * 4:i * 4 + 3] for i in range(3)])
            for name in ARM_BONES + HITSTOP_BONES if name in raw}
    worst = 0.0
    worst_at = None
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


def pivot_series(arm, action, tracked):
    """逐帧量**标定出来的那颗鞋底前缘顶点**的世界坐标 —— 踮脚不滑判据用它。

    ★ 为什么不能再用"逐帧找最低顶点"（第 2 轮实测踩到的坑）：
      脚平放时**整块鞋底所有顶点的 z 都等于 0**（贴地闭环把最低点钉在 0），
      排序在浮点噪声里任意，"最低顶点"会沿着 250 mm 长的鞋底乱跳 ——
      实测 L_w1 假漂移 253.6 mm、R_w0 197.7 mm、L_w0 47.2 mm。
      那不是滑动，是**量尺坏了**。
      正确的尺子：绕支点纯转动时，**支点那颗顶点位置恒定**（x/y 都不动）
      ⟹ 盯死那一个 (物体, 顶点序号)，漂移就只剩真实的滑动。
    """
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    deps = bpy.context.evaluated_depsgraph_get()

    out = {key: [] for key in tracked}
    for frame in range(0, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        cache = {}
        for key, (obj_name, vindex) in tracked.items():
            obj = bpy.data.objects.get(obj_name)
            if obj is None:
                out[key].append(None)
                continue
            if obj_name not in cache:
                evaluated = obj.evaluated_get(deps)
                mesh = evaluated.to_mesh()
                matrix = evaluated.matrix_world
                cache[obj_name] = [(matrix @ v.co) for v in mesh.vertices]
                evaluated.to_mesh_clear()
            point = cache[obj_name][vindex]
            out[key].append((point.x, point.y, point.z))
    if previous is not None:
        arm.animation_data.action = previous
    return out


# =============================================================== 专属门禁
def launcher_assertions(arm, action, samples, foots, start_mats, end_mats,
                        tracks):
    res = {}
    pelvis = [Vector(f["pelvis"]) for f in foots]
    pz = [p.z * 1000.0 for p in pelvis]

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

    # 1) 支撑脚：**标定支点顶点**漂移（踮脚不滑 = 滚动支点不动）+ 鞋底区间
    pivot = {}
    sole = {}
    for side in SIDES:
        for idx, (a, b) in enumerate(WINDOWS[side]):
            pts = [tracks[(side, idx)][f] for f in range(max(a, 0), b + 1)
                   if tracks[(side, idx)][f] is not None]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            drift = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) * 1000.0
            zs = [foots[f]["sole_" + side] for f in range(max(a, 0), b + 1)
                  if foots[f]["sole_" + side] is not None]
            pivot["%s_w%d_mm" % (side, idx)] = round(drift, 4)
            sole["%s_w%d" % (side, idx)] = [round(min(zs) * 1000.0, 3),
                                            round(max(zs) * 1000.0, 3)]
    res["pivot_drift_mm"] = pivot
    res["stance_pivot_ok"] = all(v <= PIVOT_DRIFT_MAX_MM
                                 for v in pivot.values())
    res["plant_sole_mm"] = sole
    res["stance_sole_ok"] = all(SOLE_RANGE_MM[0] <= v[0]
                                and v[1] <= SOLE_RANGE_MM[1]
                                for v in sole.values())
    unsupported = [f for f in range(0, TOTAL + 1)
                   if window_of("L", f) is None and window_of("R", f) is None]
    res["unsupported_frames"] = unsupported
    res["always_supported_ok"] = not unsupported
    # 空中脚确实离地（R 腾空窗口）
    air = [v for v in AIR_SOLE.get("R", [])]
    res["air_sole_min_mm"] = (None if not air
                              else round(min(air) * 1000.0, 3))
    res["swing_airborne_ok"] = bool(air) and res["air_sole_min_mm"] > 0.0

    # 2) ★ 「攻击轨迹明确向上」（本支核心 1/2）
    rz = [f["hand.R_tail"][2] * 1000.0 for f in foots]
    lz = [f["hand.L_tail"][2] * 1000.0 for f in foots]
    res["fist_z_min_mm"] = round(min(rz), 2)
    res["fist_z_peak_mm"] = round(max(rz), 2)
    res["fist_z_rise_mm"] = round(max(rz) - min(rz), 2)
    res["fist_z_rise_l_mm"] = round(max(lz) - min(lz), 2)
    res["fist_rise_ratio"] = round(res["fist_z_rise_mm"]
                                   / BMAX["fist_z_rise_mm"], 3)
    res["fist_rise_up_ok"] = res["fist_z_rise_mm"] >= FIST_RISE_MIN_MM
    # 命中窗内：拳 z 单调不降 + 竖直分量占主导
    seg = rz[ANTIC:HIT + 1]
    steps = [seg[i + 1] - seg[i] for i in range(len(seg) - 1)]
    up = sum(1 for v in steps if v >= -0.2)
    res["fist_up_monotone_ratio"] = round(up / float(len(steps)), 4)
    path = 0.0
    for index in range(ANTIC, HIT):
        d = Vector(foots[index + 1]["hand.R_tail"]) \
            - Vector(foots[index]["hand.R_tail"])
        path += d.length * 1000.0
    res["fist_strike_path_mm"] = round(path, 2)
    res["fist_strike_rise_mm"] = round(seg[-1] - seg[0], 2)
    res["fist_up_dominance"] = (round(res["fist_strike_rise_mm"] / path, 4)
                               if path > 1e-6 else 0.0)
    res["trajectory_up_ok"] = bool(
        res["fist_up_monotone_ratio"] >= RISE_MONO_MIN
        and res["fist_up_dominance"] >= UP_DOMINANCE_MIN)

    # 3) ★ 「髋的净上升」（本支核心 2/2）
    res["pelvis_z_min_mm"] = round(min(pz), 2)
    res["pelvis_z_max_mm"] = round(max(pz), 2)
    res["pelvis_z_min_frame"] = int(pz.index(min(pz)))
    res["pelvis_z_max_frame"] = int(pz.index(max(pz)))
    res["pelvis_z_rise_mm"] = round(max(pz) - min(pz), 2)
    res["hip_rise_ratio"] = round(res["pelvis_z_rise_mm"]
                                  / BMAX["pelvis_z_rise_mm"], 3)
    res["launch_up_ok"] = res["pelvis_z_rise_mm"] >= HIP_RISE_MIN_MM
    ps = pz[ANTIC:HIT + 1]
    psteps = [ps[i + 1] - ps[i] for i in range(len(ps) - 1)]
    res["hip_up_monotone_ratio"] = round(
        sum(1 for v in psteps if v >= -0.2) / float(len(psteps)), 4)
    res["hip_up_monotone_ok"] = res["hip_up_monotone_ratio"] >= RISE_MONO_MIN

    # 4) 顿感：命停窗口**打击姿态**逐位冻结，而骨盆照常上升 + 前冲
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
    res["hitstop_rise_mm"] = round((pz[HOLD_END] - pz[HIT]), 3)
    res["hitstop_keeps_momentum_ok"] = bool(
        res["hitstop_momentum_mm"] > 10.0 or res["hitstop_rise_mm"] > 10.0)

    # 5) 力矩链（脚→腿→髋→腰→肩→手 逐级都要有非零关键帧）
    keys = ("pelvis", "spine_01", "spine_02", "chest", "shoulder.L",
            "shoulder.R", "thigh.L", "shin.L", "thigh.R", "shin.R")
    channel = {}
    for name in keys:
        vals = [s["euler"].get(name, (0.0, 0.0, 0.0)) for s in samples]
        channel[name] = round(max(max(abs(v) for v in item) for item in vals), 3)
    res["power_chain_channels_deg"] = channel
    res["power_chain_ok"] = all(v > 0.5 for v in channel.values())

    # 6) 腿可达（含**峰值利用率**，本支最紧的一条）
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

    # 7b) 物理口径的"瞬移"：骨**自身局部旋转**的真实转角（欧拉逐分量口径的对照尺）
    worst_local = 0.0
    worst_local_at = None
    for index in range(1, len(samples)):
        ea = samples[index - 1]["euler"]
        eb = samples[index]["euler"]
        for name in set(ea) | set(eb):
            here = _local_step_deg(ea.get(name), eb.get(name))
            if here > worst_local:
                worst_local, worst_local_at = here, (samples[index]["frame"],
                                                     name)
    res["local_step_max_deg"] = round(worst_local, 3)
    res["local_step_max_at"] = (None if worst_local_at is None
                                else [worst_local_at[0], worst_local_at[1]])
    # ⚠ 只登记、不判红：`no_teleport`（欧拉逐分量）保留为**通道口径**如实上报，
    #   `world_step_ok` 与 `local_step_max_deg` 是两把物理尺子。三者对照见文件头注释。

    # 8) 帧预算
    res["antic_frames"] = ANTIC
    res["antic_frames_ok"] = 12 <= ANTIC <= 20
    res["hitstop_frames"] = HOLD
    res["hitstop_frames_ok"] = 2 <= HOLD <= 4
    res["launch_window"] = [ANTIC, HIT]
    res["amplitude_baseline"] = dict(BMAX)
    res["hip_rise_min_mm"] = round(HIP_RISE_MIN_MM, 2)
    res["fist_rise_min_mm"] = round(FIST_RISE_MIN_MM, 2)
    return res


# =============================================================== 标定工具
def measure_pivot(arm, side, ankle_xy, z_probe, torso):
    """量「鞋底前缘滚动支点」与「平放踝高」。

    返回 (px, py, pz, ax0, ay0, az0, 物体名, 顶点序号)：
      (px, py, pz)  = 平放时鞋底最低那一行里**最前**（y 最小）顶点的世界 x/y，
                      以及它**高出鞋底最低点**的量（第 4 轮修正，见 `_pivot_ankle`）
      (ax0, ay0, az0) = 平放时踝的世界 x/y 与「踝 − 鞋底最低点」的高度差

    ★ 为什么必须把 pz 一起量出来：鞋头是**圆拱**的 —— 实测鞋底最前那颗顶点
      比鞋底最低点高 11.1 mm（左）/ 13.6 mm（右）。若把它当贴地点（pz=0），
      转 40° 时 `R_x` 会把这 11.1 mm 的 z 混进 y，踝目标就少算
      `pz·sinθ = 7.11 mm`，支点反而**前移** 7.11 mm（正是红的那 7.15 mm）。
    """
    pose = dict(torso)
    A.apply_pose(arm, pose)
    RS.leg_to(arm, pose, side, (ankle_xy[0], ankle_xy[1], z_probe))
    A.keep_world_orientation(arm, "foot." + side)
    bpy.context.view_layer.update()

    achieved = Vector(A.bone_world(arm, "foot." + side, "head"))
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
    zmin = min(p[2] for p in points)
    band = [p for p in points if p[2] <= zmin + 2.0]
    front = min(band, key=lambda p: p[1])
    return (front[0], front[1], front[2] - zmin, achieved.x, achieved.y,
            achieved.z - zmin, front[3], front[4])


# =============================================================== 主流程
def main():
    global SEAM_POSE, IDLE_POSE, SEAM_DIRS, PY0, IDLE_PELVIS
    global L_SEAM, R_SEAM, L_END, R_END, SEAM_SOLE, SEAM_EULER, SEAM_SOURCE
    global PELVIS_RX, PELVIS_RY, SPINE01_RX
    global SPINE01_RY, SPINE02_RX, SPINE02_RY, CHEST_RX, CHEST_RY
    global NECK_RX, NECK_RY, HEAD_RX, HEAD_RY
    global SHOULDER_L_RX, SHOULDER_R_RX, SHOULDER_L_RZ, SHOULDER_R_RZ
    global PELVIS_X, PELVIS_Z, Z_SEAM, SEAM_ANK
    global R_VERT0, R_VERT1, R_OFF_ANK, D_KEYS

    FROZEN_SHIFT.clear()
    WINDOW_SOLE.clear()
    AIR_SOLE.clear()
    PIVOT.clear()
    PIVOT_VERT.clear()
    FLAT_ANK.clear()
    PIVOT_AXIS.clear()
    PIVOT_SCALE.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    for module, label in ((I1, "Idle_01"), (H, "Heavy_01")):
        if module.NAME not in bpy.data.actions:
            print("C02_BOOTSTRAP 动画工程缺 %s，先补跑" % label)
            module.main()
            arm, meshes = A.open_animation_project()
            A.setup_scene()

    A.PROBE_BONES = tuple(A.PROBE_BONES) + ("thigh.L", "thigh.R",
                                            "shin.L", "shin.R")

    # ---- 上游接缝：`Heavy_01@36`（可取消帧）—— **直接读 Action**
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
    SEAM_ANK = {"L": L_SEAM.copy(), "R": R_SEAM.copy()}
    SEAM_DIRS = {bone: tuple(A.bone_direction(arm, bone)) for bone in ARM_BONES}
    SEAM_SOLE = {s: A.foot_lowest_by_side()[s][2] for s in SIDES}
    seam_extra = sorted(
        name for name, value in SEAM_EULER.items()
        if max(abs(v) for v in value) > 1e-9
        and name not in set(SEAM_POSE) | set(A.FIST) | {"pelvis"})

    # ---- 下游接缝：`Idle_01@0`
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

    # ---- 躯干轨道：**frame 0 回填上游接缝的真值**（见 C01 第 1 件：必须 global）
    def patch(track, bone, channel=None):
        value = SEAM_EULER[bone]
        value = value[channel] if channel is not None else value[0]
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
    SHOULDER_L_RX = patch(SHOULDER_L_RX, "shoulder.L", 0)
    SHOULDER_R_RX = patch(SHOULDER_R_RX, "shoulder.R", 0)
    SHOULDER_L_RZ = patch(SHOULDER_L_RZ, "shoulder.L", 2)
    SHOULDER_R_RZ = patch(SHOULDER_R_RZ, "shoulder.R", 2)
    PELVIS_XE = SEAM_POSE["@loc"]["pelvis"][0]
    PELVIS_ZE = SEAM_POSE["@loc"]["pelvis"][1]
    Z_SEAM = PELVIS_ZE + 0.900
    PELVIS_X = ((0, PELVIS_XE),) + tuple(k for k in PELVIS_X if k[0] != 0)
    PELVIS_Z = ((0, Z_SEAM),) + tuple(k for k in PELVIS_Z if k[0] != 0)

    # ---- 落脚点由**终点反推**（末帧 = Idle_01@0 整体平移 shift_y）
    shift_y = (PY0 - D_TOTAL_MM / 1000.0) - IDLE_PELVIS.y
    L_END = Vector((idle_l.x, idle_l.y + shift_y, idle_l.z))
    R_END = Vector((idle_r.x, idle_r.y + shift_y, idle_r.z))

    A.report("C02_LAYOUT", {
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
        "note": ("上游接缝 = Heavy_01 的 CANCEL 帧；末帧 = Idle_01@0 平移；"
                 "L 蓄力段上步、R 蹬离地后前落。"),
    })

    # ---- 支点 + 平放踝高标定（三个支撑窗口各一次）
    calib = {}
    torso_seam = {"pelvis": (RS.track(PELVIS_RX, 0), 0.0, 0.0),
                  "@loc": {"pelvis": A.wloc(0.0, 0.0, Z_SEAM - 0.900)}}
    torso_mid = {"pelvis": (RS.track(PELVIS_RX, ANTIC), 0.0, 0.0),
                 "@loc": {"pelvis": A.wloc(0.0, (PY0 - D_mm(ANTIC) / 1000.0),
                                           RS.track(PELVIS_Z, ANTIC) - 0.900)}}
    torso_end = {"pelvis": (RS.track(PELVIS_RX, TOTAL), 0.0, 0.0),
                 "@loc": {"pelvis": A.wloc(0.0, (PY0 - D_TOTAL_MM / 1000.0),
                                           RS.track(PELVIS_Z, TOTAL) - 0.900)}}
    # ---- 实测滚动轴：`keep_world_orientation` + `WF.add_world_rx` 都是在**骨架空间**
    #      里绕 X 轴转，投影回世界后会偏。把骨架 X 轴投到世界即为真实滚动轴。
    _axis_world = (arm.matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0))).normalized()
    _axis_dev_deg = math.degrees(
        _axis_world.angle(Vector((1.0, 0.0, 0.0))))
    for key, torso, xy, probe in (
            (("L", 0), torso_seam, L_SEAM, L_SEAM.z),
            (("R", 0), torso_seam, R_SEAM, R_SEAM.z),
            (("L", 1), torso_mid, L_END, L_END.z),
            (("R", 1), torso_mid, R_END, R_END.z)):
        px, py, pz, ax0, ay0, az0, vobj, vindex = measure_pivot(
            arm, key[0], (xy.x, xy.y), probe, torso)
        PIVOT[key] = (px, py, pz)
        PIVOT_VERT[key] = (vobj, vindex)
        FLAT_ANK[key] = (ax0, ay0, az0)
        PIVOT_AXIS[key] = _axis_world
        PIVOT_SCALE[key] = _PIVOT_K_DEFAULT
        calib["%s_w%d" % key] = {
            "pivot_mm": [round(px * 1000.0, 2), round(py * 1000.0, 2),
                         round(pz * 1000.0, 3)],
            "pivot_vertex": [vobj, vindex],
            "ankle_flat_mm": [round(ax0 * 1000.0, 2), round(ay0 * 1000.0, 2),
                              round(az0 * 1000.0, 2)]}
    A.report("C02_CALIBRATION", {
        "per_window": calib,
        "pivot_axis_world": [round(v, 6) for v in _axis_world],
        "pivot_axis_dev_deg": round(_axis_dev_deg, 4),
        "pivot_scale": _PIVOT_K_DEFAULT,
        "tip40_ankle_z_mm": round(_pivot_ankle(("L", 0), TIP_HIT).z * 1000.0, 2),
        "note": ("支点 x/y 由构造不变（贴地闭环只改 z）；az0 = 踝高 − 鞋底最低点。"
                 "滚动轴取骨架 X 轴的世界投影，故 40° 踮脚的支点漂移由构造归零。"),
    })

    # ---- R 腾空段的 vert（落地帧由构造贴地）
    R_OFF_ANK = _pivot_ankle(("R", 0), tip_of("R", T_R_OFF))
    R_VERT0 = RS.track(PELVIS_Z, T_R_OFF) - R_OFF_ANK.z
    R_VERT1 = RS.track(PELVIS_Z, T_R_ON) - FLAT_ANK[("R", 1)][2]
    A.report("C02_R_AIR", {
        "off_ankle_mm": [round(v * 1000.0, 2) for v in R_OFF_ANK],
        "seam_ankle_mm": [round(v * 1000.0, 2) for v in SEAM_ANK["R"]],
        "vert0_mm": round(R_VERT0 * 1000.0, 2),
        "vert1_mm": round(R_VERT1 * 1000.0, 2),
        "tip_at_off_deg": round(tip_of("R", T_R_OFF), 2),
        "landing_pelvis_mm": round(RS.track(PELVIS_Z, T_R_ON) * 1000.0, 2),
        "landing_ankle_mm": round(FLAT_ANK[("R", 1)][2] * 1000.0, 2),
    })

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

    reset_carry()
    keyframes = build_keyframes()

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "连招与特殊技",
        "note": ("击飞技：接 Heavy_01 可取消帧，深蹲蓄力 → 双踮脚蹬伸 → "
                 "后手上挑贯拳至头顶前上方，4 帧爆发停顿，"
                 "Root Motion 前冲 0.200 m；纵向幅度 ≥ 最强地面普通攻击（Uppercut）"),
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
        "ENTER": 0, "ANTIC": ANTIC, "BURST": ANTIC, "HIT": HIT,
        "HITSTOP_END": HOLD_END, "RECOV": RETURN_START, "CANCEL": CANCEL,
        "L_OFF": T_L_OFF, "L_ON": T_L_ON, "R_PIVOT": T_R_PIVOT,
        "R_OFF": T_R_OFF, "R_ON": T_R_ON, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    if os.environ.get("C02_ARMTRACE") == "1":
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
            print("C02_ARMTRACE " + json.dumps(row))
    if os.environ.get("C02_LEGTRACE") == "1":
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
            print("C02_LEGTRACE " + json.dumps(row))
    if os.environ.get("C02_TRACE") == "1":
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for f in foot_series(arm, action, meshes):
            print("C02_TRACE " + json.dumps({
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
                "tipL": round(tip_of("L", f["frame"]), 2),
                "tipR": round(tip_of("R", f["frame"]), 2),
            }))

    report = A.run_common_assertions(samples, meta, foot_probe=())
    foots = foot_series(arm, action, meshes)
    tracked = {key: PIVOT_VERT[key]
               for side in SIDES
               for key in [(side, idx) for idx in range(len(WINDOWS[side]))]}
    tracks = pivot_series(arm, action, tracked)
    start_mats = RS.action_world_matrices(arm, bpy.data.actions[H.NAME],
                                          H.CANCEL)
    end_mats = RS.action_world_matrices(arm, bpy.data.actions[I1.NAME], 0)
    report.update(launcher_assertions(arm, action, samples, foots,
                                      start_mats, end_mats, tracks))
    world_step, world_at = arm_world_steps(arm, action)
    report["world_step_max_deg"] = round(world_step, 3)
    report["world_step_max_at"] = (None if world_at is None
                                   else [world_at[0], world_at[1]])
    report["world_step_ok"] = world_step <= NO_TELEPORT_MAX_DEG
    report["max_abs_euler_y_deg"] = round(JS.MAX_ABS_EULER_Y, 2)
    report["arm_roll_max_deg"] = {k: round(v, 1)
                                  for k, v in JS.ROLL_MAX.items()}
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    # ★ `no_teleport` 的键名**不以 `_ok` 结尾**，永远不进 `failed` ——
    #   每支收尾必须**单独 grep 一次非 `_ok` 的布尔项**（B10 教训 12）。
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C02_REPORT", report)

    if not SKIP_RENDER:
        # 取景跟着 Root Motion 平移（末帧比首帧前冲 200 mm）。
        sheets = [(A.VIEW_SIDE, -0.10, 2.90), (A.VIEW_FRONT, -0.10, 2.90),
                  (A.VIEW_3Q, -0.10, 2.90)]
        for base, shift_y_v, scale in sheets:
            name, location, target, _scale, res_v = base
            view = (name, (location[0], location[1] + shift_y_v, location[2]),
                    (target[0], target[1] + shift_y_v, target[2]), scale, res_v)
            frames = ([0, ANTIC, HIT, HOLD_END, TOTAL]
                      if name == "side" else [0, ANTIC, HIT, TOTAL])
            A.render_pose_sheet(arm, action, frames, "launcher02", views=(view,))
    A.save_project()
    A.export_glb(arm)
    print("C02_DONE failed=%s" % report["failed"])
    print("C02_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C02_FAILURE " + traceback.format_exc())
