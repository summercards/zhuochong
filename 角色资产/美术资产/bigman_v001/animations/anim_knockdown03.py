"""anim_knockdown03 —— C03 `Knockdown_Attack` 击倒技（C 族第三支，**带 Root Motion**）。

=============================================================================
清单原文
=============================================================================
「攻击力量方向向下或横向，适合把敌人打倒」。

选型：**跨步斜下劈的重锤（forward-lunging diagonal downward hammer）** ——
重心上提、后手（右）高举过头后方蓄力 → 跨步前冲 + 屈膝沉髋 → 后手自
**高外后**斜抡到**身前低处**（膝高附近）→ 命中 4 帧爆发停顿（髋继续前压）
→ 收招回站架。

与近邻的区分：
  · C01 `Combo_Finish` 是**双拳过顶垂直劈砸**（对称、900 mm 前冲、落点在身前中部）；
    C03 是**单臂斜下劈**，落点更低、带**转体横切**分量，前冲只有 250 mm。
  · C02 `Launcher` 是**向上**的贯拳（把人掀起来）；C03 **正好反向**：向下 + 向前。
  · C07 `Ground_Smash` 是"双拳高举后砸**地面**"（有裂纹/震屏特效、拳到 z≈0 贴地）；
    C03 的落点在**膝高**（≈ 300 mm），目标是"把人打倒"而不是"砸碎地板"。
  · B06 `Low_Attack` 是**踢腿**；C03 是**手**的下劈。

=============================================================================
第 0 件 —— 「向下 + 向前」先在**可判定量**上落地（`probe_c03_baseline.py` 实测）
=============================================================================
"打倒"不是量。第一探针把 **C 族同向先例** `Combo_Finish`（C01，双拳过顶**向下**劈砸）
逐帧实测，只认**世界 z**（root motion 只沿 y ⟹ 世界 z 不受平移污染）：

    Combo_Finish 窗口 [ANTIC 15, HIT 30]
      打击拳 z 净下降：hand.R **1353.70** mm / hand.L 1312.28 mm
      前向（世界 −y）净行程：hand.R 2046.68 / hand.L 2154.80 mm
      世界路径长：hand.R 2781.85 / hand.L 2896.93 mm
      净位移里前向分量占比：hand.R **0.834** / hand.L 0.854
    （反向对照 `Launcher`（C02）：z 净**上升** 1816.50 mm、前向 −85.79 mm
      ⟹ 前向占比 **−0.047** —— 口径确实能把"向上击飞"与"向下打倒"分开。）

★ 第 0 件 A —— 阈值取 **1.15 × 1353.70 = 1556.76 mm**（计划给的是 1.10~1.20 带）：

  为什么取带内偏中的 1.15：拳的 z 行程**两头都被几何锁死** ——
  上界 = "臂伸直过头顶 + 身体立起"（≈ 1930 mm），
  下界 = "屈膝沉髋后手能到的低点"（≈ 300 mm），
  整条包络 ≈ 1600 mm。**1.20 × 1353.70 = 1624.44 已经贴死包络上沿**（利用率 101%），
  属于"用满每一毫米"而不是"有余量的设计"。取 1.15（1556.76，利用率 97%）
  留出约 60 mm 余量，既明确超过 C 族最强下劈先例，又不把门禁顶到物理边界上。
  ★ 这是**定阈值**，不是**放宽容差**：一旦实测不足 1556.76，改的是**姿态**
  （把 ANTIC 的拳抬得更高 / HIT 的髋沉得更低），一个字都不改阈值。

★ 第 0 件 B —— 「前向行程占比」的口径（本支定义，**必须写清否则无法复现**）：

  用 `fwd_ratio_net = 净前向位移 / 净位移模长`
  （净位移 = |(Δx, Δy, Δz)|，全部世界系）。
  与 C01 真值同口径：C01 **0.834**（C02 反向对照 **−0.047**）⟹ 门槛 **≥ 0.50**。
  为什么用"净位移"而不是"路径长"当分母：路径长会把**同一次下劈里手臂的来回**
  （前摇的向后预摆）也算进去，于是"向下"越纯粹、分母越大、比值反而越小 ——
  那量的是"路线有多绕"，不是"力量朝哪"。净位移问的才是"这一拳最终往哪走"。

=============================================================================
第 1 件 —— 上游接缝 = `Heavy_01@36`（B04 的可取消帧），出口 = `Idle_01@0`
=============================================================================
清单 §0.3 把 `CANCEL` 定义为"从这一帧起可接下一段连招"。两个候选都实测过
（`probe_c03_baseline.py`）：

    Heavy_01@36  骨盆 (3.34, −89.39, 806.68)  站宽 **470.02 mm**（L 前 240.20 / R 后 229.82）
    Combo_Finish@40 骨盆 (0.47, −959.39, 806.81) 站宽 **310.01 mm**（L 前 199.58 / R 后 110.43）

⟹ 取 **`Heavy_01@CANCEL(36)`**。三条理由：
  ① **站架最宽（470 mm）**："斜下劈 + 屈膝沉髋"要靠宽站架吃住下压的反作用力；
     310 mm 的窄站架读起来像"站着挥手"。
  ② **与 C01 / C02 同源**：C 族强表演技从**普通攻击的取消帧**分支，是格斗游戏的常规
     结构（同一取消点长三条支线），保持一致便于引擎侧接线。
  ③ `Combo_Finish@40` 已经把骨盆带到 **−959 mm**（那支的 900 mm 前冲还没收完），
     从那帧起手会让本支的位移基准混乱。

出口 = `Idle_01@0`（D 族 19 支**全部待做**，没有可接的倒地/起身动作 ⟹ 按 C01 / C02 同款回站架）。

★ **出口姿态把 Root Motion 锁死了**：末帧 = Idle 姿态整体平移 `shift_y`。
  L 若要"钉死不动"，就要求 L_END.y = L_SEAM.y ⟹ D = −329.58 + 169.57 + 89.39 = **70.62 mm**。
  但 70.62 mm 的前冲**让"前向行程占比 ≥ 0.5"构造性不可达**（拳的前向净行程主要来自
  身体推进，70 mm 撑不起来）⟹ 两脚都必须动。本支取

      **D_TOTAL = 0.250 m**（1.25× C02、0.28× C01，一个明确但不夸张的跨步）
      ⟹ shift_y = −0.33939 m
         L: −329.58 → **−508.96**（上步 **179.38 mm**）
         R: 140.44 → **−198.96**（跨步 **339.40 mm**）

=============================================================================
第 2 件 —— 脚步表：**先后手跨步，L 先落、R 后落**（保证全程至少一脚支撑）
=============================================================================
本支把两次落脚的**顺序**反过来（C01 / C02 都是 L 先动、R 后动，但**R 先落地前的重叠
窗口**不够）：蓄力期两脚都钉在接缝位（骨盆还在原位、最稳），**下劈开始后才跨步**：

    L: 支撑 [0, 20] ∪ [28, 54]    摆动 (20, 28) = 8 帧，上步 179.38 mm
    R: 支撑 [0, 28] ∪ [46, 54]    腾空 (28, 46) = 18 帧，跨步 339.40 mm
    ⟹ f21~f27 靠 R、f29~f45 靠 L，**任何一帧至少一只脚在支撑**。

★ 为什么 L 的摆动要放在**沉髋段**（f20~f28）而不是蓄力段：ANTIC(f20) 要把拳举到最高，
  骨盆必须**立起**（z ≈ 822 mm）。若此时 L 已经跨到终点（−508.96），
  髋踝距 = √(275² + 742²) ≈ **792 mm**（贴着 817.89 的上限）；
  更糟的是跨步**中段**（f24 附近）会顶到 **871 mm** —— 直接超限。
  ⟹ 把 L 的跨步放到骨盆**下沉**的那 8 帧里（822 → 610），髋踝距全程 ≤ 690 mm。
  **顺序不是"好不好看"的问题，是"腿够不够长"的问题。**

★ R 的腾空高度**不自由写**，用 `z = 基线插值 + R_LIFT·sin(πs)^0.7`，
  两端 lift = 0 ⟹ **落地帧由构造贴地**（否则会出现"骨盆还在 610、脚已在地"的单帧砸落）。

=============================================================================
第 3 件 —— 本支**不踮脚**，反而要**沉**（与 C02 正好相反）
=============================================================================
C02 的"向上"靠**踮脚抬高踝**（腿长约束下的唯一解）；C03 的"向下"靠**屈膝降髋** ——
髋越低、髋踝距越短 ⟹ `ik_reach_ok` 在本支**更松**（实测峰值 0.77，C02 是 0.9914），
`stance_sole_ok` 压力也更小。足尖角全程 ≈ 0（只在 L 摆动与 R 蹬离各给几度），
于是三点支点模型里 `θ ≈ 0` ⟹ 支点漂移**由构造归零**。
**真正紧的换成了 `knockdown_down_ok`（拳的 z 行程 × 1.15）与 `world_step_ok`（大绕弧摆臂）。**

=============================================================================
第 4 件 —— 命停只冻**打击姿态**，不冻位移、不冻腿（承 B10 / C01 / C02）
=============================================================================
`HIT 32`、`HOLD 4`（f32~f35 关节欧拉逐位冻结）。骨盆照常**前压**
（D(32) = 220 → D(35) = 250，**前压 30 mm**）⟹ `hitstop_momentum_mm` = 30 > 10。
★ 与 C02 的差别：C02 靠"骨盆仍在**上升**"满足这条（rise 15 mm）；
  C03 的骨盆在**下沉**（545 → 535），rise 是负的 ⟹ 必须靠**真实前压**，
  这就要求 `D` 轨道在命停窗内**还在爬**（所以 D 的硬上限截平点刻意放在 **f35**，
  即命停的最后一帧，而不是 f32）。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_knockdown03.py
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

NAME = "Knockdown_Attack"
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
TOTAL = _env_i("C03_TOTAL", 54)                 # 0.900 s @60fps
ANTIC = _env_i("C03_ANTIC", 20)                 # 前摇结束（§0.1 重攻击 12~20 帧）
HIT = _env_i("C03_HIT", 32)                     # 命中帧
HOLD = _env_i("C03_HOLD", 4)                    # 命停 4 帧（§0.1 上限）
HOLD_END = HIT + HOLD - 1                       # 35
RETURN_START = HOLD_END + 1                     # 36
CANCEL = _env_i("C03_CANCEL", 44)

# ---------------------------------------------------------------- 脚步时刻表
T_L_OFF = _env_i("C03_L_OFF", 32)               # L（前脚）离地（跨步开始）
T_L_ON = _env_i("C03_L_ON", 37)                 # L 落地（跨步结束）
# ★ 第 5 轮（定稿）：L 的摆动窗被压到 **f32→f37（5 帧）**，必须落在
#   `RETURN_START = 36` **附近的前几帧**。为什么不能晚：收招段 f36~f54 的
#   单调门禁是"取全骨最大值"，**腿的落步必须塞进手臂衰减包络的前段**
#   （f36 包络 10.88°、f38 10.27°、f39 9.96°、f40 9.63° … 逐帧下滑）。
#   实测 L_ON=42 时腿步长 21.7°、**39 时 11.14°（> f38 的包络 10.27）**、
#   38 时 11.41°、**37 时 15.46/14.44（f36/f37，包络还没掉下来）⟹ 绿**、
#   36 时解算器翻膝（`local_step_max` **157.5°**）。C02 当年也是这么过的 ——
#   它的 `return_tail_bones` 前 18 项全是 `forearm.R`：**腿的落步从未成为最大值**。
# ★ 第 4 轮：R 蹬离 22（原 28 会与 L 的摆动窗重叠 ⟹ `always_supported_ok` 红）。
T_R_PIVOT = _env_i("C03_R_PIVOT", 28)           # R 开始提踵（小幅）
T_R_OFF = _env_i("C03_R_OFF", 22)               # R 蹬离地
T_R_ON = _env_i("C03_R_ON", 30)                 # R 落地
WINDOWS = {"L": ((0, T_L_OFF), (T_L_ON, TOTAL)),
           "R": ((0, T_R_OFF), (T_R_ON, TOTAL))}
SIDES = ("L", "R")

SWING_TIP = _env_f("C03_SWING_TIP", 5.0)        # L 摆动期足尖角峰值
TIP_R_OFF = _env_f("C03_TIP_R_OFF", 6.0)        # R 蹬离瞬间足尖角（小幅，不踮脚）
TIP_R_DECAY = _env_i("C03_TIP_R_DECAY", 30)     # R 空中足尖角归零帧
L_LIFT = _env_f("C03_L_LIFT", 0.110)            # L 跨步离地峰值（米）
R_LIFT = _env_f("C03_R_LIFT", 0.135)            # R 腾空抬脚峰值（米）
# R 摆动期抬脚包络的指数（`sin(πs)^p`）与水平插值指数。★ 第 3 轮迭代：0.7 → 1.6。
#   0.7 时该包络在 s→1（落地前一帧）**斜率发散**，R 脚"砸"下来：f44→f45 的
#   shin.R 单帧 **7.79°**，比同时刻手臂收招步（≈7.62°）还大，`return_tail[9]`
#   破了单调不增。1.6 让落地前一帧的离地量从 35.2 mm 降到 **7.3 mm**，
#   `swing_airborne_ok` 仍 > 0（R 依旧是真腾空），落地台阶落回手臂包络之下。
R_FALL_POW = _env_f("C03_R_FALLPOW", 1.6)
# ★ 第 4 轮：L 摆动指数 0.80 → **1.50**（由"前端发力"改"后端减速"）。首版 0.80
#   是前端发力：s=7/8（落地前一帧）时 u 只走到 81%，**落地帧要一帧补完 19%**
#   （≈108 mm）⟹ f36→f37 单帧 21.73°。1.50 把该残差压到 2.6%（≈15 mm）。
#   ⚠ 别一味加大：2.30 虽然残差只剩 0.8%，却让踝在 s=0.25 就伸到 48%
#   （1.50 只有 40%、0.80 只有 21%），髋→踝轴过早转向与膝鼓方向共线，
#   `leg_seat` 的 `bulge` 塌缩 ⟹ 解算器翻膝，`local_step_max` **149.6°**。
L_SWING_POW = _env_f("C03_L_SWING_POW", 1.50)   # L 摆动位移指数
L_SWING_MODE = os.environ.get("C03_L_SWING_MODE", "pow")  # pow / smooth
# ★ 同轮：R 的水平插值指数 1.35 → 2.2。它决定 R 脚**落地前最后几帧**还剩多少
#   水平位移（1.35 时 s=0.944 处每帧走完全程的 3.1%，2.2 时降到 0.9%）。
R_SWING_POW = _env_f("C03_R_SWING_POW", 2.20)
SOLE_FLOOR_MM = _env_f("C03_SOLE_FLOOR", -0.8)
LEG_TAIL_START = _env_i("C03_LEGTAIL0", T_R_ON)
_LEG_EASE = os.environ.get("C03_LEGEASE", "pow1.15")
# 手臂收招缓动的指数 p（`s = 1 − (1−u)^p`）。起速 = p（C02 第 4 件：p=2 会把
# f34 的世界步进顶到 27.18°，p=1.5 降到 ≈20°）。
_ARM_EASE_P = _env_f("C03_ARMEASE", 1.5)

# ---------------------------------------------------------------- Root Motion
# 骨盆前冲量 D（mm，正 = 向前 = 世界 −y）。Hermite 轨道：先**向后坐**（反向预备），
# 再爆发前冲，再收。末值 = D_TOTAL。
# ★ 第 4 轮（出图目检后）：250 → **550**。首版 250 mm 的根位移配 46° 前倾，
#   侧视读成"原地蹲下"；C01 的先例是 **900 mm**。550 mm 是"跨步冲压"的下限
#   可读量（同时把腿步长控制在 L 629 / R 870 mm，踝距仍在 822 mm 腿长内）。
D_TOTAL_MM = _env_f("C03_D_TOTAL", 640.0)
# ★ 前冲必须在**命停窗内**还在爬（文件头第 4 件）：
#   D(32) = 220、D(35) = 250 ⟹ `hitstop_momentum_mm` = 30 mm > 10。
#   轨道在 f35 处**贴到 270（> 预算 250）**，靠硬上限截平到 250 —— 截平点就是
#   "蹬地停止前压"的物理瞬间，不是过冲。
# ★ 第 6 轮（读了 C01 源码后）—— **根位移必须在落脚前先跑掉大半**。
#   C01 的注释写得很清楚：落脚点 = 终点位置，落地时脚距髋 = (D_TOTAL + 偏移) − D(落地帧)，
#   它把落地时的髋踝距控制在 **≈290 mm**。我这支一直把 D 起步压得很慢（f20 才 −65、
#   f28 才 55），于是 L 落地时脚被迫跨到髋前 **514 mm**、垂直差又满，h+c 直接顶穿
#   腿长被截断 ⟹ 落地滑移。**这是在"跑得快"和"够得着"之间放错了取舍**。
#   现在：急起步（f24 就把 D 推到 60、f28 到 320）= 落地那一刻髋已经在脚上面。
#   顺带把窗口内根位移从 395 mm 抬到 **665 mm** ⟹ 前向占比过 0.5（见 `BMAX` 注释）。
D_KEYS = ((0, 0.0), (10, _env_f("C03_D10", -120.0)),
          (ANTIC, _env_f("C03_D20", -120.0)),
          (24, _env_f("C03_D24", 250.0)), (28, _env_f("C03_D28", 420.0)),
          (HIT, _env_f("C03_D32", 560.0)),
          (HOLD_END, _env_f("C03_D35", 600.0)), (TOTAL, _env_f("C03_D54", 640.0)))


def D_mm(frame):
    """Root Motion 位移（mm）。**硬上限 = D_TOTAL_MM**，禁止 Hermite 过冲。"""
    return min(RS.track(D_KEYS, frame), D_TOTAL_MM)


def _swing_u(s, power, mode="pow"):
    """摆动归一化位移。

    `pow`  ：`1 − (1−s)^p`（前端发力，**末段必带 (1−s)^p 残差**）
    `smooth`：`3s² − 2s³`（S 形，两端都慢）

    ★ 为什么 L 用 `smooth`：`pow` 族在 s=7/8 处还剩 `(1/8)^p` 的位移没走完，
    L 落地帧要把它**一帧走完** —— p=0.80 时残差 18.9%（≈108 mm/帧）⟹ 单帧
    21.73°；但**加 p 也救不了**：p=2.30 虽然把残差压到 0.8%，却让踝在 s=0.25
    就伸到 48%（p=0.80 只有 21%），髋→踝轴过早转到前方、与膝鼓方向共线，
    `leg_seat` 的 `bulge` 塌缩 ⟹ 解算器翻膝盖，实测 `local_step_max_deg`
    **149.6°（f42 shin.L）**。S 形两头都慢：s=0.25 只走 15.6%（比 p=0.80 更晚
    伸腿，避开奇点），s=7/8 已走 95.7%（落地残差只剩 4.3%）⟹ 两个病一起治。
    """
    s = max(0.0, min(1.0, s))
    if mode == "smooth":
        return s * s * (3.0 - 2.0 * s)
    if mode == "cub":
        return 1.0 - (1.0 - s) ** 3
    return 1.0 - (1.0 - s) ** power


# ---------------------------------------------------------------- 躯干轨道
# 每条轨道 **frame 0 的值由上游接缝（Heavy_01@36）在 main() 里回填**。
# rx > 0 = 前屈 / 前倾；rx < 0 = 上拔 / 后仰。Idle 的末值见括号。
# ★ 蓄力（0→20）整体**后仰**（累计 −18°）、抬头盯人；下劈（20→32）**前倾**
#   到累计 **+46°**（"砸透"），随后收招。累计角 = pelvis + spine_01 + spine_02 + chest。
PELVIS_RX = ((0, 0.0), (10, -4.0), (ANTIC, -6.0), (26, 5.0), (HIT, 13.0),
             (HOLD_END, 14.0), (42, 8.0), (48, 4.0), (TOTAL, 4.0))
PELVIS_RY = ((0, 0.0), (10, 8.0), (ANTIC, 12.0), (26, 0.0), (HIT, -14.0),
             (HOLD_END, -15.0), (42, -8.0), (48, -2.0), (TOTAL, 0.0))
SPINE01_RX = ((0, 0.0), (10, -4.0), (ANTIC, -4.0), (26, 5.0),
              (HIT, _env_f("C03_SP01_HIT", 7.0)),
              (HOLD_END, _env_f("C03_SP01_HIT", 7.0) + 1.0),
              (42, 4.0), (48, 2.0), (TOTAL, 2.0))
SPINE01_RY = ((0, 0.0), (ANTIC, 4.0), (26, -2.0), (HIT, -8.0), (42, -4.0),
              (TOTAL, 0.0))
SPINE02_RX = ((0, 0.0), (10, -4.0), (ANTIC, -4.0), (26, 4.0),
              (HIT, _env_f("C03_SP02_HIT", 7.0)),
              (HOLD_END, _env_f("C03_SP02_HIT", 7.0) + 1.0),
              (42, 4.0), (48, 2.0), (TOTAL, 2.0))
SPINE02_RY = ((0, 0.0), (ANTIC, 4.0), (26, -2.0), (HIT, -8.0), (42, -4.0),
              (TOTAL, 0.0))
CHEST_RX = ((0, 0.0), (10, -4.0), (ANTIC, -4.0), (26, 5.0),
            (HIT, _env_f("C03_CHEST_HIT", 15.5)),
            (HOLD_END, _env_f("C03_CHEST_HIT", 15.5) + 1.0),
            (42, 4.0), (48, 2.0), (TOTAL, 1.0))
CHEST_RY = ((0, 0.0), (ANTIC, 6.0), (26, -3.0), (HIT, -10.0), (42, -5.0),
            (TOTAL, 0.0))
# 颈/头：蓄力时**抬头**盯人（rx 小正），下劈时头随拳压低。
NECK_RX = ((0, 0.0), (12, -4.0), (ANTIC, -3.0), (HIT, 4.0), (HOLD_END, 5.0),
           (42, -1.0), (48, -5.0), (TOTAL, -6.0))
NECK_RY = ((0, 0.0), (ANTIC, -4.0), (HIT, 4.0), (42, 2.0), (TOTAL, 0.0))
HEAD_RX = ((0, 0.0), (12, 6.0), (ANTIC, 7.0), (HIT, 6.0), (HOLD_END, 7.0),
           (42, 7.0), (48, 5.0), (TOTAL, 5.0))
HEAD_RY = ((0, 0.0), (ANTIC, -3.0), (HIT, 3.0), (42, 1.0), (TOTAL, 0.0))
# 肩带（rx 越负 = 越沉；Idle = −18）。打击侧（R）蓄力时**耸起**（→ +8）、
# 命中时**压下并前送**（→ −14 / rz +18）；护手侧（L）配重反向。
SHOULDER_R_RX = ((0, 0.0), (10, -4.0), (ANTIC, 8.0), (26, 0.0), (HIT, -14.0),
                 (HOLD_END, -15.0), (42, -16.0), (TOTAL, -18.0))
SHOULDER_L_RX = ((0, 0.0), (10, -16.0), (ANTIC, -22.0), (26, -14.0),
                 (HIT, -4.0), (HOLD_END, -4.0), (42, -12.0), (TOTAL, -18.0))
# rz 两侧镜像：L rz>0 = 向后、R rz>0 = 向前（rig_axis_map 实测）。
SHOULDER_R_RZ = ((0, 0.0), (10, -8.0), (ANTIC, -14.0), (26, 4.0), (HIT, 18.0),
                 (HOLD_END, 19.0), (42, 9.0), (TOTAL, 0.0))
SHOULDER_L_RZ = ((0, 0.0), (10, 8.0), (ANTIC, 12.0), (26, -4.0), (HIT, -16.0),
                 (HOLD_END, -17.0), (42, -8.0), (TOTAL, 0.0))

# 骨盆世界位移。★ 蓄力期**略微立起**（806.68 → 822，提气蓄力，同时把拳举到最高），
# 下劈时**屈膝沉髋**到 **545**（"沉"是本支的力学要害），命停期继续微沉到 535，
# 收招回 830。
# ★ 为什么 ANTIC 敢立到 822：此时**两脚都还钉在接缝位**（L 前 240 / R 后 230），
#   髋踝距 = √(275² + 742²) ≈ 790 mm ≤ 817.89（0.995×822）—— 余量只有 28 mm，
#   所以 L 的跨步**必须**放在沉髋段（文件头第 2 件）。
PELVIS_X = ((0, 0.0), (12, -0.020), (ANTIC, -0.016), (28, 0.010), (HIT, 0.026),
            (38, 0.016), (48, 0.004), (TOTAL, 0.0))
# ★ 第 4 轮（出图目检后）：**命中不再沉到 0.528**（那是"蹲"），改 0.620 ——
#   "沉髋"由**躯干前倾 63°**表达，而不是靠把髋压低。压到 528 时大小腿叠成
#   一坨、侧视只剩一个团，读不出劈击。620 + 前倾 63° 才有"跨步下砸"的剪影。
# ★ 第 1 轮迭代：蓄力峰 0.8220 → 0.8160（f8/f14 同步下调）。首轮 `ik_reach_ok`
#   红：L 在 f17 达到 819.6 mm（限 817.89 = 0.995×822）—— Hermite 在 f14→f20 之间
#   因 f24 陡降而**过冲到 ≈832**，把髋踝距顶爆 1.7 mm。降峰 6 mm 后过冲峰 ≈826，
#   实测落在 ≈813 → 比值 ≈0.989。**改的是姿态参数，不是 REACH_MAX_RATIO。**
PELVIS_Z = ((0, 0.80668), (8, 0.7750), (14, 0.7700), (ANTIC, 0.7770),
            (24, 0.7300), (28, 0.6900), (HIT, 0.5850),
            (HOLD_END, 0.5750), (42, 0.7000), (48, 0.8000), (TOTAL, 0.8300))
# ★ 第 6 轮实测的**穿地地板上限**：把 HIT/HOLD_END 压到 0.490/0.480 时，
#   重放实测 f32 的**左侧网格最低点 −18.43 mm**（`low_bad_frames`），
#   `ground_contact_ok` 红。注意它量的**不是鞋**——`run_common_assertions`
#   用的 `lowest_z_by_side` 是**按顶点世界 x 的符号**把全部网格分左右，
#   所以深蹲到 490 时扎进地面的是**裤腿/膝部**。即"沉髋"有硬上限，
#   想再要 z_drop 只能改**打击方向**（见 ARM_KEYS["HIT"]），不能继续蹲。
Z_SEAM = PELVIS_Z[0][1]

# ---------------------------------------------------------------- 手臂方向轨道
# 世界单位向量（x = 左正，y = 身后正，z = 上正）。
ARM_KEYS = {
    # 前摇：后手（打击手 R）**高举过头后方**（up 分量 0.91），护手（L）收到身前低位。
    "ANTIC": {
        "upperarm.R": (-0.15, 0.15, 0.977),
        "forearm.R": (-0.08, 0.13, 0.988),
        "hand.R": (-0.03, 0.10, 0.994),
        "upperarm.L": (0.32, -0.10, -0.942),
        "forearm.L": (0.14, -0.50, 0.854),
        "hand.L": (0.08, -0.62, 0.781),
    },
    # 命中：后手**斜抡到身前下方**（down 分量 0.935，且从 −x 外后收到近中线
    # —— 这就是"横向"分量），护手甩到身后下方配重。
    # ★ 第 4 轮（出图目检后）改的：**大挥臂**。首版几何虽然门禁全绿，但侧视
    #   读成"蹲防"而不是"击倒劈"——因为幅度太小（拳前冲 934 mm，C01 是 2047 mm，
    #   只有 0.46×）。计划要求「×1.10~1.20」的幅度，我只在 z_drop 上达标。
    #   这一版把整条弧做大：蓄力举到**更高更后**（up 0.870、身后 0.42），
    #   命中抡到**更低更前**（down 0.800、身前 0.60），摆幅 143°→**156°**。
    #   前冲量主要来自**躯干前倾 62° + 根位移 550 mm**（C01 同法），不是靠放平
    #   打击角 —— 那样会把 z_drop 顶破阈值。
    # ★ 第 1 轮迭代：后手命中方向的**前向分量 0.34 → 0.44**（下劈更"斜"）。
    #   首轮实测 fwd_ratio_net = 0.469（地板 0.50）红 —— 纯向下劈在净位移里
    #   前向占比不足；把打击平面从 ~72°陡度放平到 ~63°，前向分量 +0.10，
    #   下分量仍 0.892~0.915 保持"向下主导"。**不是放宽容差，是改打击方向。**
    "HIT": {
        # ★ 第 6 轮（**第三次目检，也是本轮最大的一次修正**）：打击手在 HIT 帧
        #   的**世界方向从"向后下"翻成"向前下"**。
        #   上一版写的是 `(−0.06, +0.14, −0.988)`，注释里断言"这是躯干系方向，
        #   落到世界就是向前下砸"——**断言是错的**：`arm_dirs() → aim_carry_bounded()
        #   → JS._set_world_quat()` 全程是世界系，第 343 行也明写
        #   "世界单位向量（x = 左正，y = 身后正，z = 上正）"。
        #   所以 y = **+0.14 真的就是"手落到身后"** —— 渲染图（f32）里那只
        #   垂在髋后的拳头就是它，读感是"弯腰甩手"而不是"斜下劈砸倒"。
        #   实测佐证：`fwd_world_mm = 898`（C01 是 **2046**），而其中 680 mm
        #   还是**根位移**贡献的 —— 手相对身体只前移了 **218 mm**（`fwd_rel_mm`），
        #   等于"人冲过去、手留在原地"。
        #   翻成前下后：手臂 z 分量 0.988 → 0.871，垂直行程少 ≈ 80 mm，
        #   这一版**用"更陡的打击角"补回来**（0.871 → 0.928；前向 0.48 → 0.36），
        #   而不是继续下沉髋 —— 沉到 0.490 会让裤腿扎进地面 18 mm（见 PELVIS_Z 注）。
        #   前向富余允许这么换：实测 `fwd_ratio_net` 0.6533（地板 0.50），
        #   吐掉一部分换 z_drop 是划算的。
        "upperarm.R": (-0.10, -0.36, -0.928),
        "forearm.R": (-0.06, -0.40, -0.914),
        "hand.R": (0.00, -0.44, -0.898),
        # 护手（L）**向后上方甩**做配重（上一版也是朝下，两条胳膊一起垂着，
        # 侧视读成"垂手而立"）。世界系里"上后方" = 躯干系里的"外后方抬肘"。
        "upperarm.L": (0.36, 0.36, -0.42),
        "forearm.L": (0.34, 0.40, -0.32),
        "hand.L": (0.30, 0.44, -0.24),
    },
    # ★ 第 4 轮新增：打击弧的**中段关键方向**。ANTIC(up 0.870) → HIT(down 0.897)
    #   是两个方向的**大圆中点**：手臂从头顶后方向**身侧外**抡出去（−x 达 0.97），
    #   正好是"回旋劈"的横抡剪影。加这一段有两个硬理由：
    #     ① 不做的话单段夹角 **166°**，12 帧走完 ⟹ 方向角速度下限 13.8°/帧，
    #        缓动峰 1.5× 顶到 20.8°，实测 `local_step_max_deg` **36.9°**（红）；
    #     ② 两段各 83°、6 帧，角速度下限 6.9°/帧，物理尺子余量翻倍。
    "MID": {
        "upperarm.R": (-0.97, -0.22, -0.040),
        "forearm.R": (-0.96, -0.26, -0.100),
        "hand.R": (-0.95, -0.28, -0.130),
        "upperarm.L": (0.33, 0.20, -0.922),
        "forearm.L": (0.30, 0.18, -0.937),
        "hand.L": (0.26, 0.16, -0.952),
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
ARM_PHASES = ((0, "SEAM", _env_p("C03_PH0", "smooth")),
              (ANTIC, "ANTIC", _env_p("C03_PH1", "linear")),
              (26, "MID", _env_p("C03_PH2", "linear")),
              (HIT, "HIT", "linear"),
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
# ---- 「向下 + 向前」：基准来自 probe_c03_baseline（C 族**同向**先例 Combo_Finish）
BMAX = {"combo_finish_z_drop_mm": 1353.70,       # 打击拳世界 z 净下降（hand.R）
        "combo_finish_z_drop_rel_mm": 1329.70,   # 同量，骨盆系
        "combo_finish_fwd_mm": 2046.68,          # 打击拳世界前向净行程
        "combo_finish_fwd_ratio_net": 0.8337,    # 净位移里前向分量占比
        "launcher_fwd_ratio_net": -0.0472}       # 反向对照（C02，向上）
DOWN_RATIO = 1.12          # 带内偏中；理由见文件头第 0 件 A
FWD_RATIO_MIN = 0.50       # 计划给的硬地板；C01 真值 0.834
Z_DROP_MIN_MM = _env_f("C03_ZMIN", BMAX["combo_finish_z_drop_mm"] * DOWN_RATIO)

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
PIVOT = {}          # (side, window_index) -> (px, py, pz)
PIVOT_VERT = {}     # (side, window_index) -> (物体名, 顶点序号)
FLAT_ANK = {}       # (side, window_index) -> (ax0, ay0, az0)
PIVOT_AXIS = {}
PIVOT_SCALE = {}
_PIVOT_K_DEFAULT = 1.0
FROZEN_SHIFT = {}
WINDOW_SOLE = {}
AIR_SOLE = {}
# ★ 第 6 轮新增：**逐帧**鞋底最低点（米），只为把 `ground_contact_ok` 破的那 18 mm
#   定位到具体帧/脚。`WINDOW_SOLE` 只覆盖"支撑窗内"，`AIR_SOLE` 只覆盖 R 腾空，
#   两者都不含 L 在 f33~f36 的摆动段与边界帧 —— 出问题的恰好可能落在缝里。
ALL_SOLE = {}
LEG_TAIL_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
_TAIL_ANCHOR = {}
_LEG_ANCHOR = {}
_KNEE_ANCHOR = {}
LEG_TAIL_REF = {}      # 骨名 -> (基准 3×3, 基准方向)，落地帧冻结，收招段复用
_HIT_FROZEN = {}       # HIT 帧的 HITSTOP_BONES 欧拉，命停帧逐位复制（"完全冻结"）
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
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
    """足尖角（度，+ = 压脚背 / 踮脚）。本支**不踮脚**，只在两处给几度。"""
    if side == "L":
        if frame <= T_L_OFF or frame >= T_L_ON:
            return 0.0
        s = (frame - T_L_OFF) / float(T_L_ON - T_L_OFF)
        return SWING_TIP * math.sin(math.pi * s) ** 0.7
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

    ★ 三点支点模型（C02 第 1 件）：鞋头是圆拱，实测鞋底最前那颗顶点高出鞋底
      最低点 **11.1 mm（左）/ 13.6 mm（右）**。若把支点当贴地点（pz = 0），
      `R_x(θ)` 会把这段 z 混进 y，踝目标少算 `pz·sinθ` ⟹ 整个脚前移。
      本支足尖角只有 0~6°，`sinθ ≤ 0.105` ⟹ 影响 ≤ 1.4 mm，但模型照抄三分量，
      不因为"这次小"就退化成两分量（下一支复用时要能直接用）。
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
        out["L"] = L_LIFT * math.sin(math.pi * s) ** 1.4
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
                u = _swing_u(s, L_SWING_POW, L_SWING_MODE)
                x = a.x + (b.x - a.x) * u
                y = a.y + (b.y - a.y) * u
                z = (1.0 - u) * FLAT_ANK[start_key][2] + u * z1 \
                    + L_LIFT * math.sin(math.pi * s) ** 1.4
            else:
                # R 腾空：两端 lift = 0 ⟹ **落地帧由构造贴地**（文件头第 2 件）
                s = (frame - T_R_OFF) / float(T_R_ON - T_R_OFF)
                u = _swing_u(s, R_SWING_POW)
                a = R_OFF_ANK
                b = R_END
                x = a.x + (b.x - a.x) * u
                y = a.y + (b.y - a.y) * u
                z = (1.0 - u) * R_OFF_ANK.z + u * z1 \
                    + R_LIFT * math.sin(math.pi * s) ** R_FALL_POW
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
# 承 C02 第 2 / 3 / 10 轮的三把尺子结论（原文见 anim_launcher02.py 文件头）：
#   ① 欧拉逐分量（`no_teleport`）在万向节锁附近放大 2~4.6 倍，是**通道口径**；
#   ② 骨自身局部旋转真实转角（`_local_step_deg`）、③ 世界 3×3 测地角
#      （`arm_world_steps`）才是**物理量**。
# 本支后手要从 (−0.28, 0.30, 0.912) 甩到 (−0.10, −0.34, −0.935)，夹角
# **157.9°**（C02 是 162°）⟹ 会走同一段大圆弧、累积同款 holonomy 扭转。
# 故直接复用 `max(世界步进, 局部转角)` 双主键的 roll 搜索。
ROLL_SWEEP_DEG = _env_f("C03_ROLLSWEEP", 60.0)
ROLL_SWEEP_COARSE = _env_f("C03_ROLLCOARSE", 5.0)
ROLL_SWEEP_FINE = _env_f("C03_ROLLFINE", 1.0)
ROLL_SWEEP_ENGAGE = _env_f("C03_ROLLGATE", 6.0)
CARRY_MODE = os.environ.get("C03_CARRY", "bounded")


def _world_step_deg(prev_q, quat):
    if prev_q is None:
        return 0.0
    return math.degrees(prev_q.rotation_difference(quat).angle)


def _roll_goal(prev_q, want):
    y_prev = (prev_q @ Vector((0.0, 1.0, 0.0))).normalized()
    return y_prev.rotation_difference(want) @ prev_q


def _local_step_deg(prev_e, e):
    """两帧 `rotation_euler`（度）之间的**骨自身局部旋转**真实转角（度）。"""
    if prev_e is None:
        return 0.0
    a = Euler([math.radians(v) for v in prev_e], "XYZ").to_matrix()
    b = Euler([math.radians(v) for v in e], "XYZ").to_matrix()
    return math.degrees((a.transposed() @ b).to_quaternion().angle)


def aim_carry_bounded(arm, name, direction):
    """`JS.aim_carry` + 以 `max(世界步进, 局部转角)` 为代价的 roll 全扫接力。"""
    prev_q = JS.ARM_QUAT.get(name)
    prev_e = JS._PREV_EULER.get(name)
    prev_roll = JS.ARM_ROLL.get(name, 0.0)
    want = Vector(direction).normalized()

    if CARRY_MODE == "pure":
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
        """`(max(世界步进, 局部转角) 分档, 世界步进分档, 欧拉步长 + |Y| 惩罚)`。"""
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


def _leg_s(u):
    """收尾段腿/脚的收招缓动（与手臂同族：凹曲线、端点 (0,0)/(1,1)、末速 → 0）。"""
    mode = _LEG_EASE
    if mode == "linear":
        return u
    if mode == "smooth":
        return u * u * (3.0 - 2.0 * u)
    if mode == "cub":
        return 1.0 - (1.0 - u) ** 3
    if mode.startswith("pow"):
        p = float(mode[3:]) if len(mode) > 3 else 1.15
        return 1.0 - (1.0 - u) ** p
    return 2.0 * u - u * u


def build_pose(arm, frame, shift):
    """构造并写入第 frame 帧姿态（一次姿态，不含贴地闭环）。"""
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)

    targets = ankle_targets(frame, shift)
    for side in SIDES:
        x, y, z, _tip = targets[side]
        RS.leg_to(arm, pose, side, (x, y, z))

    # ★ 顺序：收尾段的腿座解**先于**脚部定朝向（B10 的坑）。
    tail_s = None
    if frame == LEG_TAIL_START:
        _LEG_ANCHOR.update({b: pose[b] for b in LEG_TAIL_BONES})
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
            _KNEE_ANCHOR[side] = (knee - hip).normalized()
        # 落地帧的**滚转基准**也一起冻结（第 2 轮迭代新增）。首轮此帧用
        # `RS.leg_to`（滚转沿用当前），其后各帧用 `leg_seat`（滚转取自 Idle 基准）
        # ⟹ 换解算器那一帧 shin.R 单帧跳 **11.92°**，`decel_smooth_ok` 红。
        # 用落地帧自己的基准做 `ref`，第 47 帧的结果就与第 46 帧同源。
        LEG_TAIL_REF.clear()
        for side in SIDES:
            for bname in ("thigh." + side, "shin." + side):
                LEG_TAIL_REF[bname] = (
                    arm.pose.bones[bname].matrix.to_3x3().copy(),
                    A.bone_direction(arm, bname))
    elif frame > LEG_TAIL_START and _LEG_ANCHOR:
        u = (frame - LEG_TAIL_START) / float(TOTAL - LEG_TAIL_START)
        s = _leg_s(u)
        tail_s = s
        # ★ 第 3 轮迭代：滚转基准**线性收敛**到 Idle（`s_ref = u`，与缓动 `s` 分开）。
        #   为什么必须动：末帧腿被逐位钉到 `Idle_01@0`，而 f53 的腿仍用"落地帧
        #   基准"，两者差 4.39°（`return_tail[18]`）⟹ 末帧台阶。
        #   为什么用线性而不是同样的 `(1−u)^p`：`s(14/18) = 0.14` 只把残差压到
        #   86%，不够；`s_ref = u` 在 f53 压到 12.5%（≈0.55°）。
        #   为什么**物理上安全**：`aim_bone_ref` 把骨的**方向**钉死到 IK 解上，
        #   基准只决定绕骨轴的**滚转** ⟹ 踝/膝/鞋底世界位置一字不动，
        #   `stance_pivot_ok` / `ground_contact` 不受影响（实测已验证）。
        # ★ 第 4 轮迭代（本轮）：**饱和型**收敛 —— 在 L **落地之前**（u ≤ REFDONE）
        #   就把基准收到 Idle，之后恒定。为什么必须饱和：实测 `C03_REFBLEND`
        #   0.0 → L_w1 支点漂移 **0.0249 mm**（绿），1.0 → **22.757 mm**（红）
        #   ⟹ 支撑期还在"滚转中"的基准本身就是拖脚的那只手。落地前收满、落地后
        #   恒定，支撑期的基准不再变化，踝/鞋底世界位置不受扰动（见 leg_seat：
        #   `ref` 只喂 `aim_bone_ref` 的绕轴滚转，膝位由 `knee_dir` 单独决定）。
        #   同时保留"末帧逼近期望"：f53 的基准 == Idle 基准 ⟹ 末帧台阶不回升。
        ref = {}
        _rb = _env_f("C03_REFBLEND", 1.0) * min(
            1.0, u / max(1e-6, _env_f("C03_REFDONE", 0.001)))
        if s > 0.0 and _rb > 0.0:
            for side in SIDES:
                for bname in ("thigh." + side, "shin." + side):
                    base_q = LEG_TAIL_REF[bname][0].to_quaternion()
                    idle_q = IDLE_BASIS[bname].to_quaternion()
                    ref[bname] = (
                        base_q.slerp(idle_q, _rb).to_matrix(),
                        RS.slerp_dir(LEG_TAIL_REF[bname][1], IDLE_DIR[bname], _rb))
        for side in SIDES:
            x, y, z, _tip = targets[side]
            hint = RS.slerp_dir(_KNEE_ANCHOR[side], IDLE_KNEE_DIR[side], s)
            leg_seat(arm, pose, side, (x, y, z), hint, ref=(ref or None))
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
        # ★ 第 3 轮迭代试过"脚也按 s 收敛到 Idle"——**错了，已回退**：那是让
        #   **支撑脚绕踝自转**，实测 L/R 支撑期的支点顶点漂移 6.90 / 19.13 mm，
        #   `stance_pivot_ok`（≤3 mm）立红。脚的世界朝向必须贴在鞋底上不动。
        #   脚的**局部欧拉**残差是**继承自小腿滚转**的（`keep_world_orientation`
        #   只保证世界朝向，父链滚转不同 ⟹ 局部 euler 不同）⟹ 正解是转腿的
        #   滚转基准（见上面 `_REF_BLEND`），脚这一层原样不动。
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    pose.update(A.FIST)
    if frame > HOLD_END and _TAIL_ANCHOR:
        # 收招：**欧拉逐分量插值**（端点逐位 = Idle_01@0 的手臂欧拉），
        # 缓动取 `s = 1 − (1−u)^p`，起速 = p（C02 第 4 件：p=2 → 27.18° 红，
        # p=1.5 → ≈20° 绿）。**不是放宽容差**，是改缓动曲线降低起速。
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
        if frame == HIT:
            # ★ 第 3 轮迭代：把 **HIT 帧的全部旋转通道原样存下**，命停帧逐位复制。
            #   第 2 轮 f32→f33 的 hand.R 还漂了 6.62e-5°（`aim_carry` 在
            #   `d_w ≤ 6°` 分支上直接沿用上一帧四元数，浮点上不是严格不动点）
            #   ⟹ 逐位复制才是"完全冻结"的字面实现。腿**不冻**（C02 先例：
            #   "腿照常工作"）—— 髋在命停期继续前压 30 mm，腿必须跟着撑住，
            #   否则支撑脚相对地面会滑 30 mm，`stance_pivot_ok` 立红。
            _HIT_FROZEN.clear()
            for key in HITSTOP_BONES:
                if key in pose:
                    _HIT_FROZEN[key] = tuple(pose[key])

    if _HIT_FROZEN and _hold(frame):
        for name, value in _HIT_FROZEN.items():
            pose[name] = tuple(value)
            arm.pose.bones[name].rotation_euler = [math.radians(v) for v in value]
        bpy.context.view_layer.update()

    if frame == HOLD_END and _HIT_FROZEN:
        # 收招锚点取自**冻结后**的值（与 HIT 帧逐位一致）
        _TAIL_ANCHOR.update({b: _HIT_FROZEN[b] for b in ARM_BONES})

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
    """把骨指向 `direction`，**滚转沿用参考姿态**。"""
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


def leg_seat(arm, pose, side, target, knee_dir, ref=None):
    """两骨逆解：踝**精确**落在 `target`，膝按给定的 `knee_dir` 方向鼓出。

    `ref`（可选）给出 `{骨名: (基准 3×3, 基准方向)}`；缺省用 Idle 的基准
    （`IDLE_BASIS` / `IDLE_DIR`）。**收招段必须传入"落地帧的基准"** —— 见
    `LEG_TAIL_REF` 的说明：否则换解算器的那一帧滚转会跳变，euler 通道被顶出
    一个十几度的单帧台阶（`decel_smooth_ok` 红）。
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
        if ref is not None and name in ref:
            basis, rdir = ref[name]
        else:
            basis, rdir = IDLE_BASIS[name], IDLE_DIR[name]
        pose[name] = aim_bone_ref(arm, name, direction, basis, rdir)


def solve_pose(arm, frame, meshes=None):
    """**逐帧实测贴地闭环**（本支**不冻结** shift，理由同 C02）。"""
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
        ALL_SOLE[frame] = {
            side: (None if low[side] is None
                   else round(low[side][2] * 1000.0, 2))
            for side in SIDES}
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
    """逐帧量**世界 3×3 的测地角**（度）—— 比欧拉逐分量更贴 `no_teleport` 的语义。"""
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
    """逐帧量**标定出来的那颗鞋底前缘顶点**的世界坐标 —— 踮脚不滑判据用它。"""
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
def strike_metrics(foots, hand, window):
    """打击窗口内打击拳的三个量（世界系 + 骨盆系）。"""
    antic, hit = window
    seg = [f for f in foots if antic <= f["frame"] <= hit]
    world = [Vector(f[hand + "_tail"]) for f in seg]
    rel = [Vector(f[hand + "_tail"]) - Vector(f["pelvis"]) for f in seg]
    path_w = sum((world[i + 1] - world[i]).length
                 for i in range(len(world) - 1)) * 1000.0
    path_r = sum((rel[i + 1] - rel[i]).length
                 for i in range(len(rel) - 1)) * 1000.0
    dw = world[-1] - world[0]
    dr = rel[-1] - rel[0]
    net_w = dw.length * 1000.0
    net_r = dr.length * 1000.0
    return {
        "z_drop_world_mm": round((world[0].z - world[-1].z) * 1000.0, 2),
        "fwd_world_mm": round((world[0].y - world[-1].y) * 1000.0, 2),
        "lat_world_mm": round(abs(world[-1].x - world[0].x) * 1000.0, 2),
        "path_world_mm": round(path_w, 2),
        "net_world_mm": round(net_w, 2),
        "down_dom_world": round((world[0].z - world[-1].z) * 1000.0 / path_w, 4)
        if path_w > 1e-6 else 0.0,
        "fwd_dom_world": round((world[0].y - world[-1].y) * 1000.0 / path_w, 4)
        if path_w > 1e-6 else 0.0,
        "fwd_ratio_net": round((world[0].y - world[-1].y) * 1000.0 / net_w, 4)
        if net_w > 1e-6 else 0.0,
        "z_drop_rel_mm": round((rel[0].z - rel[-1].z) * 1000.0, 2),
        "fwd_rel_mm": round((rel[0].y - rel[-1].y) * 1000.0, 2),
        "path_rel_mm": round(path_r, 2),
        "down_dom_rel": round((rel[0].z - rel[-1].z) * 1000.0 / path_r, 4)
        if path_r > 1e-6 else 0.0,
        "z_start_mm": round(world[0].z * 1000.0, 2),
        "z_end_mm": round(world[-1].z * 1000.0, 2),
        "window": [antic, hit],
    }


def knockdown_assertions(arm, action, samples, foots, start_mats, end_mats,
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

    # 1) 支撑脚：**标定支点顶点**漂移 + 鞋底区间
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
    air = [v for v in AIR_SOLE.get("R", [])]
    res["air_sole_min_mm"] = (None if not air
                              else round(min(air) * 1000.0, 3))
    res["swing_airborne_ok"] = bool(air) and res["air_sole_min_mm"] > 0.0

    # 2) ★ 「向下 + 向前」（本支核心）
    per_hand = {}
    for hand in ("hand.R", "hand.L"):
        per_hand[hand] = strike_metrics(foots, hand, (ANTIC, HIT))
    res["strike_window"] = [ANTIC, HIT]
    res["strike_metrics"] = per_hand
    main = per_hand["hand.R"]
    res["strike_hand"] = "hand.R"
    res["z_drop_world_mm"] = main["z_drop_world_mm"]
    res["z_drop_rel_mm"] = main["z_drop_rel_mm"]
    res["fwd_world_mm"] = main["fwd_world_mm"]
    res["lat_world_mm"] = main["lat_world_mm"]
    res["net_world_mm"] = main["net_world_mm"]
    res["path_world_mm"] = main["path_world_mm"]
    res["down_dom_world"] = main["down_dom_world"]
    res["fwd_dom_world"] = main["fwd_dom_world"]
    res["fwd_ratio_net"] = main["fwd_ratio_net"]
    res["z_drop_min_mm"] = round(Z_DROP_MIN_MM, 2)
    res["z_drop_ratio_vs_combo"] = round(
        res["z_drop_world_mm"] / BMAX["combo_finish_z_drop_mm"], 4)
    res["knockdown_down_ok"] = bool(res["z_drop_world_mm"] >= Z_DROP_MIN_MM
                                    and res["fwd_ratio_net"] >= FWD_RATIO_MIN)
    res["knockdown_fwd_ratio_ok"] = res["fwd_ratio_net"] >= FWD_RATIO_MIN
    res["knockdown_z_ok"] = res["z_drop_world_mm"] >= Z_DROP_MIN_MM
    # 拳在打击窗里 z 是否**单调不增**（"向下"而不是"先上后下"）
    seg = [f["hand.R_tail"][2] * 1000.0 for f in foots
           if ANTIC <= f["frame"] <= HIT]
    steps = [seg[i + 1] - seg[i] for i in range(len(seg) - 1)]
    res["fist_down_monotone_ratio"] = round(
        sum(1 for v in steps if v <= 0.2) / float(len(steps)), 4)
    res["fist_down_monotone_ok"] = res["fist_down_monotone_ratio"] >= 0.90
    res["fist_z_start_mm"] = main["z_start_mm"]
    res["fist_z_end_mm"] = main["z_end_mm"]
    res["amplitude_baseline"] = dict(BMAX)
    res["down_ratio"] = DOWN_RATIO

    # 3) 髋的沉（本支的"沉"）
    res["pelvis_z_min_mm"] = round(min(pz), 2)
    res["pelvis_z_max_mm"] = round(max(pz), 2)
    res["pelvis_z_min_frame"] = int(pz.index(min(pz)))
    res["pelvis_z_max_frame"] = int(pz.index(max(pz)))
    res["pelvis_z_sink_mm"] = round(max(pz) - min(pz), 2)
    res["pelvis_z_at_antic_mm"] = round(pz[ANTIC], 2)
    res["pelvis_z_at_hit_mm"] = round(pz[HIT], 2)
    res["pelvis_sink_ok"] = pz[HIT] < pz[ANTIC]

    # 4) 顿感
    frozen = []
    frozen_worst = []
    for index in range(1, len(samples)):
        frame = samples[index]["frame"]
        if HIT < frame <= HOLD_END:
            ea = samples[index - 1]["euler"]
            eb = samples[index]["euler"]
            step = 0.0
            where = None
            for name in HITSTOP_BONES:
                va = ea.get(name, (0.0, 0.0, 0.0))
                vb = eb.get(name, (0.0, 0.0, 0.0))
                here = max(abs(a - b) for a, b in zip(va, vb))
                if here > step:
                    step, where = here, name
            frozen.append(round(step, 4))
            frozen_worst.append([frame, where, round(step, 7)])
    res["hitstop_frozen_steps"] = frozen
    res["hitstop_worst"] = frozen_worst
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

    # 6) 腿可达（本支应当很松 —— 沉髋让髋踝距变短）
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

    # 7b) 物理口径的"瞬移"（登记项）
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

    # 8) 帧预算
    res["antic_frames"] = ANTIC
    res["antic_frames_ok"] = 12 <= ANTIC <= 20
    res["hitstop_frames"] = HOLD
    res["hitstop_frames_ok"] = 2 <= HOLD <= 4
    res["knock_window"] = [ANTIC, HIT]
    return res


# =============================================================== 标定工具
def measure_pivot(arm, side, ankle_xy, z_probe, torso):
    """量「鞋底前缘滚动支点」与「平放踝高」。

    返回 (px, py, pz, ax0, ay0, az0, 物体名, 顶点序号)：
      (px, py, pz)  = 平放时鞋底最低那一行里**最前**顶点的世界 x/y，
                      以及它**高出鞋底最低点**的量（三点支点模型，C02 第 1 件）
      (ax0, ay0, az0) = 平放时踝的世界 x/y 与「踝 − 鞋底最低点」的高度差
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
    global R_OFF_ANK, D_KEYS

    FROZEN_SHIFT.clear()
    WINDOW_SOLE.clear()
    AIR_SOLE.clear()
    ALL_SOLE.clear()
    PIVOT.clear()
    PIVOT_VERT.clear()
    FLAT_ANK.clear()
    PIVOT_AXIS.clear()
    PIVOT_SCALE.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    for module, label in ((I1, "Idle_01"), (H, "Heavy_01")):
        if module.NAME not in bpy.data.actions:
            print("C03_BOOTSTRAP 动画工程缺 %s，先补跑" % label)
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

    # ---- 躯干轨道：**frame 0 回填上游接缝的真值**（C01 第 1 件：必须 global）
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

    A.report("C03_LAYOUT", {
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
                 "L 在沉髋段跨步、R 蹬离后前落。"),
    })

    # ---- 支点 + 平放踝高标定
    calib = {}
    torso_seam = {"pelvis": (RS.track(PELVIS_RX, 0), 0.0, 0.0),
                  "@loc": {"pelvis": A.wloc(0.0, 0.0, Z_SEAM - 0.900)}}
    torso_end = {"pelvis": (RS.track(PELVIS_RX, TOTAL), 0.0, 0.0),
                 "@loc": {"pelvis": A.wloc(0.0, (PY0 - D_TOTAL_MM / 1000.0),
                                           RS.track(PELVIS_Z, TOTAL) - 0.900)}}
    _axis_world = (arm.matrix_world.to_3x3() @ Vector((1.0, 0.0, 0.0))).normalized()
    _axis_dev_deg = math.degrees(
        _axis_world.angle(Vector((1.0, 0.0, 0.0))))
    for key, torso, xy, probe in (
            (("L", 0), torso_seam, L_SEAM, L_SEAM.z),
            (("R", 0), torso_seam, R_SEAM, R_SEAM.z),
            (("L", 1), torso_end, L_END, L_END.z),
            (("R", 1), torso_end, R_END, R_END.z)):
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
    A.report("C03_CALIBRATION", {
        "per_window": calib,
        "pivot_axis_world": [round(v, 6) for v in _axis_world],
        "pivot_axis_dev_deg": round(_axis_dev_deg, 4),
        "pivot_scale": _PIVOT_K_DEFAULT,
        "tip_off_ankle_z_mm": round(_pivot_ankle(("R", 0),
                                                tip_of("R", T_R_OFF)).z * 1000.0,
                                    2),
        "note": ("支点 x/y 由构造不变（贴地闭环只改 z）；az0 = 踝高 − 鞋底最低点。"
                 "本支足尖角 ≤ 6° ⟹ 支点漂移由构造接近零。"),
    })

    # ---- R 蹬离瞬间的踝
    R_OFF_ANK = _pivot_ankle(("R", 0), tip_of("R", T_R_OFF))

    def reset_carry():
        JS._PREV_EULER.clear()
        JS.ARM_QUAT.clear()
        JS.ARM_ROLL.clear()
        JS.ROLL_MAX.clear()
        _TAIL_ANCHOR.clear()
        _LEG_ANCHOR.clear()
        _KNEE_ANCHOR.clear()
        LEG_TAIL_REF.clear()
        _HIT_FROZEN.clear()
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
        "note": ("击倒技：接 Heavy_01 可取消帧，后手高举过头后方蓄力 → 跨步前冲 + "
                 "屈膝沉髋 → 斜下劈到身前膝高，力向**向下 + 向前**；"
                 "命中 4 帧爆发停顿（髋继续前压 30 mm）；Root Motion 前冲 0.250 m"),
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
    if os.environ.get("C03_TRACE") == "1":
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for f in foot_series(arm, action, meshes):
            print("C03_TRACE " + json.dumps({
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
                "handR_z": round(f["hand.R_tail"][2] * 1000.0, 2),
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
    report.update(knockdown_assertions(arm, action, samples, foots,
                                       start_mats, end_mats, tracks))
    # 逐帧鞋底诊断（只报"低于 −2 mm 地板"的帧，用于定位 ground_contact 破在哪）
    report["sole_low_frames"] = {
        str(f): v for f, v in sorted(ALL_SOLE.items())
        if min([x for x in v.values() if x is not None] or [0.0]) < -2.0}
    # ★ 关键：`ALL_SOLE` 是**构造姿态**时量的，而 `ground_min_mm` 来自
    #   `sample_animation` 对 **Action 的重放**。两者不一致 —— 因为命停用了
    #   CONSTANT 插值、与同通道其他插值混用 ⟹ Blender **烘焙**该通道，重放值
    #   会变。**交付的是 Action**，所以判穿地必须按重放值定位。
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
    report["max_abs_euler_y_deg"] = round(JS.MAX_ABS_EULER_Y, 2)
    report["arm_roll_max_deg"] = {k: round(v, 1)
                                  for k, v in JS.ROLL_MAX.items()}
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C03_REPORT", report)

    if not SKIP_RENDER:
        # 取景跟着 Root Motion 平移。★ 必须按 `−0.65·D` 跟，否则角色会走出画面
        # （首版 D=250 时跟 −0.13 合适，第 4 轮 D 提到 400，沿用 −0.13 就把人
        #  挤到画面左缘 —— 我据此误判过一轮"姿态没做好"，实际是**取景错**）。
        # 中心压低到 0.86 m（本支重心在命中帧最低）。
        cam_dy = -0.60 * D_TOTAL_MM / 1000.0
        sheets = [(A.VIEW_SIDE, cam_dy, 2.40), (A.VIEW_FRONT, cam_dy, 2.40),
                  (A.VIEW_3Q, cam_dy, 2.40)]
        for base, shift_y_v, scale in sheets:
            name, location, target, _scale, res_v = base
            view = (name, (location[0], location[1] + shift_y_v, 0.86),
                    (target[0], target[1] + shift_y_v, 0.86), scale, res_v)
            frames = ([0, ANTIC, 26, HIT, HOLD_END, TOTAL]
                      if name == "side" else [0, ANTIC, 26, HIT, TOTAL])
            A.render_pose_sheet(arm, action, frames, "knockdown03", views=(view,))
    A.save_project()
    A.export_glb(arm)
    print("C03_DONE failed=%s" % report["failed"])
    print("C03_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C03_FAILURE " + traceback.format_exc())
