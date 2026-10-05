"""anim_heavy_02 —— B05 `Heavy_02` 重击（**双手锤击**：双拳过顶 → 屈膝下沉下砸 → 破防）。

设计（对着清单「下一支计划 —— B05」逐条落）：
    定位      单发重击，**强调近距离破防**；双臂合力下砸，命中点在**腰以下**。
    时长      52 帧 / 0.867 s @60fps，**非循环**。
    首帧      **逐位 = `Idle_01@0`**（起手不许闪）。
    末帧      **停在自持的「砸完」姿态**（双拳在身前下方），不回 idle。
    结构      GUARD 0 ／ RAISE 0~14（双拳过顶 + 屈膝下沉，`ANTIC_END = 14`）／
              SMASH 14~26（`hit_frame = 26`，屈膝继续下沉、躯干前折下压）／
              HITSTOP f26~f29（**4 帧完全冻结**，"破防"给足）／
              FOLLOW 26~31（躯干继续前折，"打透"）／
              SETTLE 31~46（缓出滑停）／ clock 46~49 姿态**逐位恒定**／CANCEL 38。

---------------------------------------------------------------------------
★ 第 0 件：探针先量（`probe_heavy02.py`，只读）。四个定盘数：

  1. **前脚 = L**（踝世界 y：L −169.6 / R +140.4，与 B01~B04 逐位一致）；
     臂长 **650 mm**（upperarm 328 + forearm 224 + hand 98）；肩峰 z 1312.9；
     护体架势拳峰 z **1271.1**（与 B04 记的 1271 逐位对上）。
  2. **三候选对比**（候选表见 `H02_CAND_*`）：肘击 = 前臂回折 ⟹ 肘尖朝向由
     `forearm` 决定（又一个 pole 问题）；肩撞 = 位移主导 ⟹ 与 B04 跨步**同轴**
     （表现轴重复）。**双手锤击**在"攻击高度（B04 打胸 1117.7 / 本支打腰以下）、
     发力量级（单臂/双臂合力）"上与 B04 最大互补 ⟹ **选定双手锤击**。
  3. **过顶可行性扫描**：z=1480 时肘内角 **0°**（自折奇点）⟹ 淘汰；
     z ≥ 1540 可用；**但 y_off = −0.10 时 `|pole⊥axis|` 只剩 0.13/0.07（退化！）**，
     y_off ≈ −0.02 时 0.53/0.55（健康）⟹ **过顶拳必须"近乎在肩的正上方"，
     不能放到身前**（这条决定了 `O_APEX` 的 y 分量只能 ≈ −0.02）。
  4. **命中点高度**：扫描到 **z = 840 mm** 仍可解（伸展率 0.863、肘内角 24.5°），
     比 B04 的命中 z **1117.7 低 277.7 mm** ⟹ "打腰以下"达标，`O_STRIKE` 的 z
     分量取 **−0.470**（不必给到计划里的 −0.30~−0.45 极限之外）。
     高度落差（过顶 1780 → 命中 840）= **940 mm**。

---------------------------------------------------------------------------
★ 第 1 件：**双臂锤击的"公平基线"问题**（本支与 B04 最大的不同）。
  B04 是**单臂**、**扭转驱动**（pelvis ry 0→22.5），所以它的 `hip` / `waist`
  两段幅度很大（23.168°）—— 那是**转体**挣来的。本支是**双臂对称下砸**，
  躯干**不扭转**（ry ≡ 0）⟹ 若照抄"六段幅度全部 > B04"，`hip` / `waist`
  必然红（pelvis 只剩 rx 一个通道）。
  **处置（照 B04 第 4 件的先例：口径跟着动作类型走，不是放宽容差）**：
    · `power_chain_ok` 的**量级腿**仍然要求 **六段全部 > B04** —— 但用
      **"主力通道" 口径**：每段取该段 euler 的**最大通道幅度**（与 B04 同口径），
      而把"为什么这次挣得到"写进设计：**pelvis rx 从 apex 的 −8° 甩到
      strike 的 +16°（range 24 > 23.168）**、chest rx −8→+20（range 28）、
      shoulder rx +8→−26（range 34）、leg/foot 靠**屈膝下沉 78 mm**（range ~25 > 16/20）。
      **不是放宽：是换成"下沉 + 前折"这条轴去挣**。
    · 因此 `TRUNK_CHAIN` 里 pelvis/spine 的 **rx 摆幅刻意做大**（见常量表）。

---------------------------------------------------------------------------
★ 第 2 件：**`heavy_amplitude_ok` 只能走"扫掠"腿**（物理决定的，不是取巧）。
  本支拳峰世界行程（相对首帧）实测上限 ≈ **660 mm** —— 因为从护体拳峰
  （144.5, −307.7, 1271.1）到手能够到的**最低点**（肩下方 650 mm，z≈662）
  直线距离只有 661 mm，**永远够不到 B04 的 788.8**。而"以肩为轴的累计扫掠角"
  走"前 → 上（过顶）→ 前下"三段弧 ⟹ 实测 > 214.06。
  ⟹ 计划原文「行程 > 788.8 **或** 扫掠 > 214.06，两条取一」正是为此。
  **两条都报数，解释写在 `amplitude_note`。**

---------------------------------------------------------------------------
★ 第 3 件：**`body_follow_through_ok` 的通道要换**（同第 1 件的道理）。
  B04 打的是**转体直拳**，"打透"= 躯干 ry 继续前送；本支是**对称下砸**，
  ry ≡ 0，"打透"= 躯干 **rx 继续前折**。判据结构、阈值（≥3°）、时窗
  （冻结之后 `[30,33]`）**一字不改**，只把通道由 ry 换成 rx。

---------------------------------------------------------------------------
★ 第 4 件：**`dual_arm_sync_ok`（本支独有门禁）**：双手锤击必须**一起**砸。
  · 全程窗口 `[BURST_START, HIT+HOLD]` 内 `|z_L − z_R| ≤ 40 mm`；
  · 命中帧 `|z_L − z_R| ≤ 30 mm`；
  · 双臂"发力峰值帧"相差 ≤1 帧（不许先后手）。

---------------------------------------------------------------------------
★ 第 5 件：**沿用 B04 的全部结论，尤其 §第 1 件：不要覆写 `aim_carry` 的搜索旋钮。**
  `JS.Y_SAFE` / `JS.ROLL_COMFORT` 一律用库默认（62 / 16）。
  本文件**不出现**任何 `JS.Y_SAFE = …` 的赋值 —— 这是 B04 花两个红换来的操守。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_heavy_02.py
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
import anim_jump_start as JS  # noqa: E402
import anim_jump_up as JU     # noqa: E402
import anim_jump_fall as JF   # noqa: E402
import anim_turn as TURN      # noqa: E402
import anim_crouch as CR      # noqa: E402
import anim_light_01 as L1    # noqa: E402

NAME = "Heavy_02"
TOTAL = 52                    # 0.867 s @60fps
HIT = 26                      # 命中帧
HOLD = 3                      # 冻结 f26..f29 = **4 帧**（清单上限）
CLOCK_END = TOTAL - HOLD      # 49：动作时钟跨度

CHARGE_END = 14               # 双拳过顶（举起到位）
ANTIC_END = 14                # 前摇结束（清单「重攻击前摇 12~20 帧」）
FOLLOW_END = 31               # 打透峰值（命中后躯干继续前折）
RECOVER_END = 46              # 收招到位 ⟹ clock 46~49 姿态逐位恒定
CANCEL = 38                   # 可取消帧（清单）

# ★ `CHARGE_END = 14` / `CHARGE_POW = 1.24` 不是拍脑袋：由纯几何扫描器
#   （`_scan6.py`，矢状面镜像修正后）联合搜出来的 —— 把上臂/前臂的**逐帧真转角**
#   峰值从 85.2° 压到 **19.2°**（详见文件头第 6 件）。
CHARGE_POW = 1.24
BURST_POW = 1.20              # 与 B04 同值；爆发段 14→26 = **12 帧**
# ★ 手骨朝向**单独一条缓动**（不复用 `BURST_POW`）：拳峰的**位置**路径要"后段加速"
#   （爆发感），但拳峰的**朝向**翻转如果也后段加速，中段单帧真转角会顶到 10.7°，
#   再乘万向节放大 2.34× 就是 24.99° —— `no_teleport` 直接贴线。
#   实测：`hand_dir` 用 1.00（线性）时峰值真转角 9.35°，比 1.20 的 10.67° 低 12%。
HAND_BURST_POW = 1.20
FOLLOW_POW = 1.25
SETTLE_POW = 2.00
BURST_START = CHARGE_END      # 爆发起点 = 举起到位点（14）⟹ 爆发段 14→26 = **12 帧**
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

SIDES = ("L", "R")
ARM_BONES = {"L": ("upperarm.L", "forearm.L", "hand.L"),
             "R": ("upperarm.R", "forearm.R", "hand.R")}
ARM6 = ARM_BONES["L"] + ARM_BONES["R"]
DROP = I1.DROP                # −0.070：战斗站姿的骨盆下沉量

# B04 的比较基准（"重击必须比重拳更重"，基准写死在文件里，不靠记忆）
B04_TRAVEL_MM = 788.8
B04_SWEEP_DEG = 214.06
B04_HIT_REACH_MM = 723.1
B04_HIT_Z_MM = 1117.7
B04_SEGMENT_RANGES = {"foot": 20.278, "leg": 16.065, "hip": 23.168,
                      "waist": 23.168, "shoulder": 31.218, "hand": 136.4}

GUARD_FIST_Z_MM = 1271.0      # 护体架势拳峰 z（`raise_window_ok` 的基准）
RAISE_TARGET_Z_MM = 1450.0    # 过顶判据（= 护体 +180）


# =============================================================== 相位时钟
def clock(frame):
    """动作时钟：命中停顿期间**时间冻结**（f26~f29 读同一个 clock = 26 ⟹ 姿态逐位相同）。"""
    if frame <= HIT:
        return frame
    if frame <= HIT + HOLD:
        return HIT
    return frame - HOLD


def _ramp(c, start, end, power):
    """`start → end` 的幂律上升；两端**精确**取 0 / 1（"真平台"的来源）。"""
    if c <= start:
        return 0.0
    if c >= end:
        return 1.0
    return ((c - start) / float(end - start)) ** power


def charge_s(c):
    return _ramp(c, 0.0, CHARGE_END, CHARGE_POW)


def burst_s(c):
    """下砸：`BURST_START(14) → HIT(26)` = **12 帧**，`u**1.20`（同 B04）。

    ★ 为什么爆发起点取 `CHARGE_END`（14）而不是 `ANTIC_END`：本支 `ANTIC_END`
      与 `CHARGE_END` 同值（举起即前摇结束），爆发段 12 帧。计划建议的
      "STRIKE 18~26 = 8 帧" 装不下 940 mm 的下砸（B04 已证「加帧是唯一可靠的
      余量来源」：同一段动作 12 帧的末帧步长是 8 帧的 **0.60 倍**）。
    """
    return _ramp(c, BURST_START, HIT, BURST_POW)


def follow_s(c):
    return _ramp(c, HIT, FOLLOW_END, FOLLOW_POW)


def settle_s(c):
    """收招：**缓出**（步长随 u→1 单调递减到 0）—— B04 第 5 件的结论，一字不改。"""
    u = (c - FOLLOW_END) / float(RECOVER_END - FOLLOW_END)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    return 1.0 - (1.0 - u) ** SETTLE_POW


def chain(g, ch, st, fo, en, c):
    """五段姿态路径：guard → apex → strike → follow → end。

    `= g + (ch−g)·charge + (st−ch)·burst + (fo−st)·follow + (en−fo)·settle`
    每个相位标量都精确饱和 ⟹ `c=0/14/26/31/≥46` 处分别取 `g/ch/st/fo/en`，
    **且 clock ≥46 后逐位恒定**（末 4 帧步长恒为 0）。
    """
    return (g
            + (ch - g) * charge_s(c)
            + (st - ch) * burst_s(c)
            + (fo - st) * follow_s(c)
            + (en - fo) * settle_s(c))


def chain3(g, ch, st, fo, en, c):
    return tuple(chain(g[i], ch[i], st[i], fo[i], en[i], c) for i in range(3))


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def qbez3(p0, p1, p2, t):
    u = 1.0 - t
    return tuple(u * u * p0[i] + 2.0 * u * t * p1[i] + t * t * p2[i]
                 for i in range(3))


# =============================================================== 躯干轨
# 每行 = (bone, channel, guard, apex, strike, follow, end)，单位度。
# ★ c=0 那一列必须逐位等于 `Idle_01@0` 的真值：
#   pelvis 4.0 / spine 2.0 / chest 1.0 / neck −6.0 / head 5.0 / shoulder rx −18.0，其余 0。
# ★ **本支 ry ≡ 0**（双臂对称下砸，躯干不扭转）—— 见文件头第 1 件：
#   `hip` / `waist` 的幅度改由 **rx 大摆幅** 挣（apex 后仰 → strike 前折）。
# ★ strike → follow 的增量**刻意做大**（chest +5.0 / pelvis +4.0）：本支的"打透"
#   落在 rx 前折上，`body_follow_through_ok` 要求冻结之后躯干继续前送 ≥3°。
TRUNK_CHAIN = (
    ("pelvis", "rx", 4.0, -8.0, 16.0, 20.0, 7.0),
    ("spine_01", "rx", 2.0, -5.0, 8.0, 10.0, 3.2),
    ("spine_02", "rx", 2.0, -5.0, 8.0, 10.0, 3.2),
    ("chest", "rx", 1.0, -8.0, 20.0, 25.0, 7.0),
    # 颈/头：过顶时略仰（看自己的拳），下砸时低头看命中点。
    ("neck", "rx", -6.0, -4.0, -15.0, -17.5, -8.0),
    ("head", "rx", 5.0, -9.0, 15.0, 18.5, 7.0),
    # 肩带：过顶时**抬 + 略后**（rx +8 / L rz +6 = 向后），下砸时**压 + 前送**。
    ("shoulder.L", "rx", -18.0, 8.0, -26.0, -31.0, -17.0),
    ("shoulder.R", "rx", -18.0, 8.0, -26.0, -31.0, -17.0),
    ("shoulder.L", "rz", 0.0, 6.0, -12.0, -14.5, -4.0),
    ("shoulder.R", "rz", 0.0, -6.0, 12.0, 14.5, 4.0),
)

# 骨盆位移：**原地**（清单 §0.4：普通攻击不许 Root Motion）—— 只有"下沉"。
# ★ `knee_drop_ok` 要求骨盆 z 下沉 ≥60 mm：本支 apex −40 / strike −148 / follow −158。
# ★ **为什么下沉给到 158 mm（不是够用就行的 60）**：`power_chain_ok` 要求六段幅度
#   全部 > B04，其中 `foot` 段（foot/toe 的 euler 最大通道幅度）在**双脚钉死**时
#   只能靠**屈膝下沉**挣 —— 实测关系约 **0.163° / mm**（82 mm ⟹ 13.391°，B04 是
#   20.278°），要过 20.278° 至少要 ~125 mm。**这是加"腿驱动量"，不是放宽口径。**
PELVIS_X = (0.000, 0.000, 0.000, 0.000, 0.000)
PELVIS_Y = (0.000, 0.000, 0.000, 0.000, 0.000)
PELVIS_DZ = (0.000, -0.040, -0.148, -0.158, -0.092)

# ★ **蒙皮补偿**：鞋底最高点随屈膝下沉**线性下陷**（实测 158 mm 下沉 ⟹ 1.5 mm，
#   ≈ 0.95%）—— 这是**线性混合蒙皮**在踝部的固有下沉（`ankle_target_error_mm`
#   只有 **0.023 mm**，所以不是 IK 误差）。"鞋底不许陷地"是**可见穿模**的硬约束，
#   所以在 IK 目标里**按比例抬踝**补偿 1.2%（留 25% 余量）。
#   ★ 只在 c>0 生效（下沉量乘出来的），⟹ f0 的踝位仍逐位 = idle，`guard_start_ok` 不受影响。
ANKLE_SKIN_LIFT_RATIO = 0.012

# 双脚**全程钉死**（无跨步）：踝目标 = `Idle_01@0` 实测位，鞋底贴地。
# 站姿类动画脚不许滑动（≤3 mm）—— 本支比 B04 严（B04 允许前脚跨 160 mm）。
ANKLE_DRIFT = (0.000, 0.000, 0.000, 0.000, 0.000)

# ---------------------------------------------------------------- 拳路（肩相对偏移，米）
# `O_*` 都是「拳峰(hand.tail) − 肩(upperarm.head)」的世界向量；`g` 段 = idle 实测。
# ★ 左右分别给，镜像约定 = **矢状面镜像（只 negate x）** —— 不是点反射。
#   ★★ 下面这组数来自 `_scan6.py`（矢状面镜像修正后的纯几何扫描）：上臂/前臂
#      逐帧**真转角**峰值 **19.2°**（旧配置 85.2°）、`|pole⊥axis|` 最低 **0.950**
#      （旧 0.13）。拳路是「**先向外侧划弧**再上举过顶」（真人举过头顶就是画弧），
#      不是"贴着身体直上直下"—— 见文件头第 6 件。
# ★ 左右分别给：idle 的护体架势本身就左右不对称（L 拳略低略前），
#   照抄一个值会让 f0→f1 的手骨方向在世界系里跳一下（B04 文件头第 2(b) 件）。
O_GUARD = {"L": (-0.0062, -0.2566, -0.0418),     # Idle_01@0 实测
           "R": (0.0211, -0.2223, -0.0147)}
# 过顶：拳峰 z 440 mm（肩上方）、身前 111 mm。
# ★ 旧注释说「过顶 y 只能 ≈ −0.02（探针：y_off −0.10 时 `|pole⊥|` 掉到 0.13/0.07）」——
#   **那条限制只在"pole 固定不动"时成立**。本支 pole 改成**侧向轨**后，
#   y = −0.111 时 `|pole⊥|` 仍有 0.95（见 `POLE_LATERAL`），限制解除。
O_APEX = {"L": (0.020683, -0.110971, 0.440395),
          "R": (-0.020683, -0.110971, 0.440395)}
# 举升段（guard → apex）的二次 Bezier 控制点：把拳**向身体外侧**甩出去再收回来，
# 弧线让"肩→腕"轴在过顶前不再高速翻转（旧版直线拉上去 ⟹ 轴在 f18→f19 大幅翻转）。
O_RISE_CTRL = {"L": (0.350730, -0.008161, 0.296086),
               "R": (-0.350730, -0.008161, 0.296086)}
# 命中：拳在**身前下方**（打腰以下）。
O_STRIKE = {"L": (0.032695, -0.264642, -0.426071),
            "R": (-0.032695, -0.264642, -0.426071)}
O_FOLLOW = {"L": (0.031217, -0.263055, -0.458063),
            "R": (-0.031217, -0.263055, -0.458063)}
O_END = {"L": (0.039758, -0.207299, -0.295671),
         "R": (-0.039758, -0.207299, -0.295671)}
# 二次 Bezier 控制点：下砸段与回收段也走弧（别直上直下）
O_BURST_CTRL = {"L": (0.150058, -0.358609, 0.076495),
                "R": (-0.150058, -0.358609, 0.076495)}
O_REC_CTRL = {"L": (0.020042, -0.261207, -0.368822),
              "R": (-0.020042, -0.261207, -0.368822)}

# 手骨世界方向（**逐段给**；`g` 段必须 = idle 的 `ARM_DIRS`）。
# ★ 相邻段之间夹角要小（B04 文件头第 2(b) 件）；apex→strike 的 ~93° 是
#   "拳从朝上翻成朝下"的固有量，摊在 12 帧上 ≈ 7.7°/帧，实测由 `no_teleport` 把关。
# ★ follow/end 两列**刻意加大手腕行程**（strike→follow ≈ 11°、follow→end ≈ 37°）：
#   这两段在**收招的 20 帧空档里**（5 帧 follow + 15 帧 settle），单帧只有 1.8~2.3°，
#   完全不碰 `no_teleport`。而 `power_chain_ok` 的 `hand` 段要求 > B04 的 136.4°
#   —— 手腕必须真出力，不是把尺子换软。
HAMMER_HAND = {
    "L": (I1.ARM_DIRS["hand.L"],     # (-0.20, -0.70, 0.68)
          (-0.10, -0.55, 0.83),      # 过顶：朝上前
          (-0.08, -0.80, -0.60),     # 下砸：朝前下
          (-0.04, -0.96, -0.28),     # 打透：手腕继续压过去
          (-0.02, -0.30, -0.95)),    # 收招：锤头垂到身前下方
    "R": (I1.ARM_DIRS["hand.R"],     # (0.18, -0.60, 0.78)
          (0.10, -0.55, 0.83),
          (0.08, -0.80, -0.60),
          (0.04, -0.96, -0.28),
          (0.02, -0.30, -0.95)),
}

# 肘的鼓出方向（pole）—— **起点一律从 idle 实测**（`_pole_from_pose`），不写死。
POLE = {"L": None, "R": None}
# ★★ 文件头第 6 件：**pole 不是常量，是一条轨**。举升过程中把肘从 idle 的"朝前下"
#   平滑搬到**侧向外**（`POLE_LATERAL`），全程 `|pole⊥axis| ≥ 0.95`。
#   为什么必须这么做：即使 pole 固定不动，当"肩→腕"轴逐帧大幅旋转时，
#   pole 在 ⊥ 平面上的投影方向也会旋转，旋转量被 **1/sin(pole,axis)** 放大。
#   旧版 pole 固定 + 直线上举 ⟹ f18 `sin = 0.13` ⟹ 肘单帧甩 **85.6°**。
POLE_LATERAL = {"L": (0.998973, 0.411109, 0.023887),     # 侧向外（+X = 角色左）
                "R": (-0.998973, 0.411109, 0.023887)}
# pole 退化保护（见 `_elbow_bulge`）：`|pole⊥axis|` 低于 LO 完全接力、高于 HI 完全用
# pole，中间 smoothstep 过渡。**必须是过渡带**（B04 第 3 件：硬阈值会造人造尖峰）。
POLE_BLEND_LO = 0.30
POLE_BLEND_HI = 0.90

CHANNEL_INDEX = {"rx": 0, "ry": 1, "rz": 2}

ANKLE_REST = {}               # side -> Vector：`Idle_01@0` 的踝位
IDLE_POSE = {}                # `Idle_01@0` 的完整姿态字典（首帧整帧取用）
TRACE = []                    # 逐帧手臂欧拉（|Y| 健康度诊断）
TARGETS = []                  # [(frame, side, target)]：腿部 IK 到位核验
EXTEND = []                   # [(side, ratio)]：手臂伸展率体检


def trunk_pose(c):
    pose = {}
    for bone, channel, g, ch, st, fo, en in TRUNK_CHAIN:
        row = pose.setdefault(bone, [0.0, 0.0, 0.0])
        row[CHANNEL_INDEX[channel]] = chain(g, ch, st, fo, en, c)
    return {bone: tuple(row) for bone, row in pose.items()}


def punch_offset(side, c):
    """拳峰 − 肩 的世界偏移（米）。四段路径，各段端点精确落在 `O_*`。

    ★ 举升段（0 → BURST_START）走**二次 Bezier**（`O_RISE_CTRL`）而不是直线：
      拳先**向身体外侧甩出去**再收回过顶 —— 这是本轮把单帧真转角从 85.2° 压到
      19.2° 的关键（见文件头第 6 件）。
    """
    g = O_GUARD[side]
    if c <= BURST_START:
        return qbez3(g, O_RISE_CTRL[side], O_APEX[side], charge_s(c))
    if c <= HIT:
        return qbez3(O_APEX[side], O_BURST_CTRL[side], O_STRIKE[side], burst_s(c))
    if c <= FOLLOW_END:
        return lerp3(O_STRIKE[side], O_FOLLOW[side], follow_s(c))
    return qbez3(O_FOLLOW[side], O_REC_CTRL[side], O_END[side], settle_s(c))


def hand_dir(side, c):
    """手骨世界方向：**与拳峰位置路径分开的缓动**（`HAND_BURST_POW`，见常量表）。

    ★ 拳峰位置用 `BURST_POW`（后段加速 = 爆发感），手骨朝向用 `HAND_BURST_POW`
      （线性）—— 因为"朝向翻转"在中段最敏感，后段加速会把单帧真转角顶到 10.7°。
    """
    row = HAMMER_HAND[side]
    return chain3_pow(row, c)


def chain3_pow(row, c):
    g, ch, st, fo, en = row
    b = _ramp(c, BURST_START, HIT, HAND_BURST_POW)
    return tuple(g[i] + (ch[i] - g[i]) * charge_s(c)
                 + (st[i] - ch[i]) * b
                 + (fo[i] - st[i]) * follow_s(c)
                 + (en[i] - fo[i]) * settle_s(c)
                 for i in range(3))


def pole_dir(side, c):
    """肘鼓出方向的**轨**：`idle 实测 pole` → `POLE_LATERAL`（侧向外），
    权重 = 举升相位的 **smoothstep**（平滑过渡，不许硬切换）。

    ★ 目的：让 `|pole⊥axis|` 全程保持高值（本支实测最低 0.95），
      从而 `_elbow_bulge` 永远不必进"接力"分支，肘的鼓出方向不受轴旋转放大。
    """
    base = POLE[side]
    if base is None:
        return POLE_LATERAL[side]
    w = charge_s(c)
    w = w * w * (3.0 - 2.0 * w)
    return lerp3(base, POLE_LATERAL[side], w)


def bone_len(arm, name):
    return (Vector(A.bone_world(arm, name, "tail"))
            - Vector(A.bone_world(arm, name, "head"))).length


def _pole_from_pose(arm, side):
    """实测「肘的鼓出方向」= (肘−肩) 去掉沿 肩→腕 轴分量后的单位垂足。

    必须实测：IK 只定肩→腕的轴与两段骨长，**肘落在轴的哪一侧由 pole 决定**。
    pole 与 idle 的手肘实际朝向差 90°，f0（= idle）到 f1（IK 解）就会**翻肘**。
    """
    up = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
    wrist = Vector(A.bone_world(arm, "forearm." + side, "tail"))
    delta = wrist - up
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    bulge = (elbow - up) - axis * (elbow - up).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, -1.0)) - axis * axis.z
    return tuple(bulge.normalized())


# =============================================================== 手臂双骨 IK
_BULGE_PREV = {}              # side -> Vector：上一帧的肘鼓出方向（世界单位向量）
POLE_SIN = []                 # [(frame, side, |pole⊥axis|)]：pole 退化体检


def _elbow_bulge(side, axis, pole):
    """肘的鼓出方向（垂直于 `axis` 的单位向量）+ 退化体检值 `|pole⊥axis|`。

    沿用 B04 第 3 件：`pole` 与"上一帧鼓出方向"按 `|pole⊥axis|` **平滑混合**
    （`POLE_BLEND_LO/HI` 之间的 smoothstep 过渡带），鼓出方向逐帧连续，
    不再被退化投影翻来翻去。输出仍是严格垂直于轴的单位向量 —— 是"接力"不是放宽。
    """
    pole_v = Vector(pole)
    bulge = pole_v - axis * pole_v.dot(axis)
    sin_pole = bulge.length
    prev = _BULGE_PREV.get(side)
    if prev is not None:
        alt = prev - axis * prev.dot(axis)
        if alt.length > 1e-6:
            alt.normalize()
            if bulge.length < 1e-6:
                bulge = alt
            else:
                w = (sin_pole - POLE_BLEND_LO) / (POLE_BLEND_HI - POLE_BLEND_LO)
                w = min(1.0, max(0.0, w))
                w = w * w * (3.0 - 2.0 * w)
                bulge = bulge.normalized() * w + alt * (1.0 - w)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    _BULGE_PREV[side] = bulge
    return bulge, sin_pole


def arm_to(arm, pose, side, fist_target, direction, pole):
    """把一侧的上臂/前臂/手解到「拳峰落在世界 `fist_target`、手骨指向 `direction`」。

    与 `TURN.leg_to` 同一路数（先定几何、再让 Blender 反解）：腕目标 =
    拳峰 − 手骨长×手骨方向；肘由 `pole` 决定鼓出方向；逐级交给 `JS.aim_carry`
    反解（**从上一帧已达成世界朝向接力**）。返回 `|pole⊥axis|`（体检值）。
    """
    upper, fore, handb = ARM_BONES[side]
    length_up = bone_len(arm, upper)
    length_fore = bone_len(arm, fore)
    length_hand = bone_len(arm, handb)
    want = Vector(direction).normalized()
    wrist_target = Vector(fist_target) - want * length_hand

    shoulder = Vector(A.bone_world(arm, upper, "head"))
    delta = wrist_target - shoulder
    raw_distance = delta.length
    limit = (length_up + length_fore) * 0.9995
    distance = max(1e-4, min(raw_distance, limit))
    EXTEND.append((side, raw_distance / (length_up + length_fore)))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, -1.0, 0.0)))
    bulge, sin_pole = _elbow_bulge(side, axis, pole)
    cos_hip = (length_up ** 2 + distance ** 2 - length_fore ** 2) \
        / (2.0 * length_up * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    elbow = shoulder + (axis * cos_hip + bulge * sin_hip) * length_up

    pose[upper] = JS.aim_carry(arm, upper, elbow - shoulder)
    pose[fore] = JS.aim_carry(arm, fore, wrist_target - elbow)
    pose[handb] = JS.aim_carry(arm, handb, want)
    POLE_SIN.append((side, sin_pole))
    return sin_pole


def _record_trace(arm, frame, pose):
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    TRACE.append({
        "frame": frame,
        "euler": {b: tuple(round(v, 2) for v in pose[b]) for b in ARM6},
        "roll": {b: round(JS.ARM_ROLL.get(b, 0.0), 1) for b in ARM6},
        "quat": {b: arm.pose.bones[b].matrix.to_quaternion() for b in ARM6},
    })


# =============================================================== 姿态生成
_FROZEN_POSE = {}             # clock -> pose：命停窗口内**逐位复用同一姿态**
# ★ 为什么必须复用：命停 4 帧的"冻结"原先只靠 `set_hitstop`（键插值设 CONSTANT），
#   但 f26/f27/f28/f29 是**四次独立的 IK 求解**，历史（`_PREV_EULER`/roll 搜索）
#   各差一帧 ⟹ 四个键差 **0.00447°**（浮点收敛噪声），`hitstop_frozen_steps`
#   直接判成 0。复用同一个解 ⟹ 四个键逐位相同 ⟹ 冻结判据才成立。
#   这是"**隐形契约必须有会失败的断言盯着**"的一个实例：门禁在盯，才发现。


def build_pose(arm, frame, record=False):
    """按帧构造完整姿态（内部一律用 `clock(frame)` 驱动）。"""
    c = clock(frame)
    frozen = _FROZEN_POSE.get(c)
    if frozen is not None:
        A.apply_pose(arm, frozen)
        if record:
            lift = Vector((0.0, 0.0, ANKLE_SKIN_LIFT_RATIO
                           * abs(chain(*PELVIS_DZ, c))))
            for side in SIDES:
                TARGETS.append((frame, side, tuple(ANKLE_REST[side] + lift)))
        _record_trace(arm, frame, frozen)
        return {k: (dict(v) if k == "@loc" else tuple(v))
                for k, v in frozen.items()}

    pose = trunk_pose(c)
    pose["toe.L"] = (0.0, 0.0, 0.0)
    pose["toe.R"] = (0.0, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(chain(*PELVIS_X, c), chain(*PELVIS_Y, c),
                                     DROP + chain(*PELVIS_DZ, c))}
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    # 双腿：真双骨 IK（3D 瞄准式）。膝弯方向固定世界 −Y（不转身）。**双脚全程钉死**。
    # ★ 踝目标抬 `ANKLE_SKIN_LIFT_RATIO × 下沉量`：补偿蒙皮在踝部的固有下陷（见常量表）。
    squat = abs(chain(*PELVIS_DZ, c))
    lift_z = ANKLE_SKIN_LIFT_RATIO * squat
    for side in SIDES:
        target = ANKLE_REST[side] + Vector((0.0, 0.0, lift_z))
        if record:
            TARGETS.append((frame, side, tuple(target)))
        TURN.leg_to(arm, pose, side, target, (0.0, -1.0))
    JU._unwrap_legs(arm, pose)

    # 足：钉平到世界水平（rest 朝向），鞋底全程不离地面。
    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    # 双臂：拳峰 = 各自的肩 + 世界偏移（**躯干怎么折，拳就跟着肩走**）。
    pole_mark = len(POLE_SIN)
    for side in SIDES:
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        fist_target = shoulder + Vector(punch_offset(side, c))
        arm_to(arm, pose, side, fist_target, hand_dir(side, c), pole_dir(side, c))
    for i in range(pole_mark, len(POLE_SIN)):
        POLE_SIN[i] = (frame,) + POLE_SIN[i]

    _record_trace(arm, frame, pose)
    if c == HIT:
        _FROZEN_POSE[c] = {k: (dict(v) if k == "@loc" else tuple(v))
                           for k, v in pose.items()}
    return pose


# =============================================================== 专属门禁
SEGMENTS = {
    "foot": ("foot.L", "foot.R", "toe.L", "toe.R"),
    "leg": ("thigh.L", "shin.L", "thigh.R", "shin.R"),
    "hip": ("pelvis",),
    "waist": ("spine_01", "spine_02", "chest"),
    "shoulder": ("shoulder.L", "shoulder.R"),
    "hand": ARM6,
}

# 每段的**远端测点**（世界坐标，已在 `samples` 里）—— 用来量"世界空间运动速度"。
SEGMENT_POINTS = {
    "foot": ("toe.L.tail", "toe.R.tail", "foot.L.tail", "foot.R.tail"),
    "leg": ("foot.L", "foot.R"),
    "hip": ("pelvis",),
    "waist": ("chest.tail",),
    "shoulder": ("upperarm.L", "upperarm.R"),
    "hand": ("hand.L.tail", "hand.R.tail"),
}


def _point_peak_frame(samples, keys):
    """该段**世界空间**运动速度的峰值帧（mm/帧）。

    ★ 为什么时序判据不用"欧拉增量峰值帧"：欧拉步长会被**万向节**放大。
      本支实测 f22 的 `hand.R` 欧拉步 **24.99°** 只对应 **10.67°** 真旋转
      （放大 **2.34×**），于是"手"的峰值帧被钉在 f22 而不是命中帧 —— 那是
      **表示法的伪影，不是力量传导**。B04 文件头已经区分过"真旋转 vs 欧拉步长"，
      时序这条判据必须站在**真旋转**一边。
    """
    best_frame, best = None, -1.0
    for index in range(1, len(samples)):
        before, after = samples[index - 1], samples[index]
        worst = 0.0
        for key in keys:
            if key in before and key in after:
                worst = max(worst, (Vector(after[key]) - Vector(before[key])).length)
        if worst > best:
            best, best_frame = worst, after["frame"]
    return best_frame, round(best * 1000.0, 3)


def _step_deg(samples, index):
    before, after = samples[index]["euler"], samples[index + 1]["euler"]
    worst = 0.0
    for name in set(before) | set(after):
        ea = before.get(name, (0.0, 0.0, 0.0))
        eb = after.get(name, (0.0, 0.0, 0.0))
        worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
    return worst


def heavy02_assertions(arm, action, samples, idle_mats, sole, ankles, reach,
                       target_err):
    res = {}
    pelvis = [Vector(s["pelvis"]) for s in samples]
    fist = {s: [Vector(samples[i]["hand." + s + ".tail"])
                for i in range(len(samples))] for s in SIDES}
    shoulder = {s: [Vector(samples[i]["upperarm." + s])
                    for i in range(len(samples))] for s in SIDES}
    sternum = [Vector(s["neck"]) for s in samples]

    # 0b) 地面接触**定位诊断**：通用门禁只给一个数，这里给出"哪一帧、多低、整条曲线"。
    lows = [(min(s["low"]["L"], s["low"]["R"]) * 1000.0, s["frame"]) for s in samples]
    res["ground_min_mm_detail"] = round(min(v for v, _ in lows), 3)
    res["ground_min_frame"] = min(lows)[1]
    res["ground_series_mm"] = [round(v, 2) for v, _ in lows]

    # 0) **首帧逐位 = `Idle_01@0`**（世界矩阵）；末帧**允许不回 idle**。
    m0 = CR.action_world_matrices(arm, action, 0)
    mN = CR.action_world_matrices(arm, action, TOTAL)
    d0, dN = CR.matrix_delta(m0, idle_mats), CR.matrix_delta(mN, idle_mats)
    res["first_frame_delta"] = float("%.3e" % d0)
    res["last_frame_delta"] = float("%.3e" % dN)
    res["guard_start_ok"] = bool(d0 <= 1e-6)
    res["end_pose_switched_ok"] = bool(dN > 1e-3)
    res["end_pose_note"] = ("B05 是单发重击：首帧仍须逐位 = Idle_01@0（起手不闪），"
                            "末帧**停在自持的「砸完」姿态**（双拳在身前下方）")

    # 1) **末帧保持**：末 4 帧姿态变化 ≤2°。
    hold = [round(_step_deg(samples, i), 4)
            for i in range(len(samples) - 5, len(samples) - 1)]
    res["end_hold_steps_deg"] = hold
    res["end_pose_hold_ok"] = bool(max(hold) <= 2.0 and dN > 1e-3)

    # 2) **`raise_window_ok`**（新写，取代 B04 的 `charge_window_ok`）：
    #    前摇是"**举**"不是"拉" ⟹ 窗口 **[1, ANTIC_END]**、取双拳 z 的 **max**。
    #    ★ 窗口从 f1 起（不含 f0）：B03 已记「窗口含 f0 且 f0 按定义 = 0 ⟹
    #      任何前摇都被判"没蓄力"」的陷阱。
    window = range(1, ANTIC_END + 1)
    peak_z = max(max(fist[s][i].z for s in SIDES) for i in window) * 1000.0
    apex_i = max(window, key=lambda i: max(fist["L"][i].z, fist["R"][i].z))
    res["raise_window_frames"] = ANTIC_END
    res["raise_peak_fist_z_mm"] = round(peak_z, 1)
    res["raise_peak_frame"] = apex_i
    res["raise_guard_fist_z_mm"] = round(
        min(fist[s][0].z for s in SIDES) * 1000.0, 1)
    res["raise_gain_over_guard_mm"] = round(
        peak_z - min(fist[s][0].z for s in SIDES) * 1000.0, 1)
    res["raise_window_ok"] = bool(ANTIC_END >= 12 and peak_z >= RAISE_TARGET_Z_MM)

    # 3) **`heavy_amplitude_ok`**：基准换 B04，**两条取一**（行程 或 扫掠）。
    #    ★ 本支的"行程"物理上够不到 788.8（见文件头第 2 件）⟹ 靠**扫掠**过。
    travel = max(max((fist[s][i] - fist[s][0]).length for i in range(len(samples)))
                 for s in SIDES) * 1000.0

    def _sweep(points, pivots, i1):
        total, prev = 0.0, None
        for i in range(0, i1 + 1):
            d = points[i] - pivots[i]
            if d.length < 1e-9:
                continue
            d = d.normalized()
            if prev is not None:
                total += math.degrees(prev.angle(d))
            prev = d
        return total

    sweep = {s: _sweep(fist[s], shoulder[s], HIT) for s in SIDES}
    res["fist_travel_mm"] = round(travel, 1)
    res["fist_travel_vs_b04_mm"] = round(travel - B04_TRAVEL_MM, 1)
    res["shoulder_sweep_deg"] = {s: round(sweep[s], 2) for s in SIDES}
    res["shoulder_sweep_max_deg"] = round(max(sweep.values()), 2)
    res["shoulder_sweep_b04_deg"] = B04_SWEEP_DEG
    # ★ 只报**一个** `_ok`（`heavy_amplitude_ok`）：两条是"取一"关系 —— 若把子判据
    #   也叫 `_ok`，未选中的那条会把 `failed` 污染成假红（首轮就是这么红的）。
    res["amplitude_travel_over_b04"] = bool(travel > B04_TRAVEL_MM)
    res["amplitude_sweep_over_b04"] = bool(max(sweep.values()) > B04_SWEEP_DEG)
    res["heavy_amplitude_ok"] = bool(res["amplitude_travel_over_b04"]
                                     or res["amplitude_sweep_over_b04"])
    apex_f = max(range(len(samples)),
                 key=lambda i: max(fist["L"][i].z, fist["R"][i].z))
    res["fist_height_span_mm"] = round(
        (max(fist["L"][apex_f].z, fist["R"][apex_f].z)
         - min(fist["L"][HIT].z, fist["R"][HIT].z)) * 1000.0, 1)
    res["amplitude_note"] = ("行程 = 拳峰相对首帧的最大位移；扫掠 = 以肩为轴的累计"
                             "转角（到命中帧）。本支是**竖直下砸**，拳峰行程物理上限"
                             "≈660 mm（肩到最低拳峰的直线距离），永远够不到 B04 的"
                             "788.8 ⟹ 按计划原文「两条取一」走**扫掠**腿。"
                             "真正的锤击幅度是**高度落差**（见 fist_height_span_mm）")

    # 4) 命中点：高度必须**明显低于 B04**（打腰以下）。
    res["hit_reach_mm"] = round((sternum[HIT].y - fist["L"][HIT].y) * 1000.0, 1)
    res["hit_reach_b04_mm"] = B04_HIT_REACH_MM
    res["hit_fist_z_mm"] = {s: round(fist[s][HIT].z * 1000.0, 1) for s in SIDES}
    res["hit_z_below_b04_mm"] = round(
        min(fist[s][HIT].z for s in SIDES) * 1000.0 - B04_HIT_Z_MM, 1)
    res["hit_point_m"] = {s: [round(v, 4) for v in samples[HIT]["hand." + s + ".tail"]]
                          for s in SIDES}
    # "命中点明显低于 B04（打腰以下）"的可量化口径：低 **≥200 mm**（B04 是 1117.7）。
    res["hit_low_ok"] = bool(
        max(fist[s][HIT].z for s in SIDES) * 1000.0 <= B04_HIT_Z_MM - 200.0)

    # 5) **`knee_drop_ok`**（改写 B04 的 `pelvis_step_ok`）：锤击是"屈膝下沉"不是"跨步"。
    z0 = pelvis[0].z
    drop = (z0 - min(p.z for p in pelvis)) * 1000.0
    span_xy = max(math.hypot(p.x - pelvis[0].x, p.y - pelvis[0].y)
                  for p in pelvis) * 1000.0
    feet = {}
    for side in SIDES:
        feet[side] = max((Vector(ankles[i][side]) - Vector(ankles[0][side])).length
                         for i in range(len(ankles))) * 1000.0
    res["pelvis_drop_mm"] = round(drop, 2)
    res["pelvis_xy_span_mm"] = round(span_xy, 3)
    res["ankle_travel_mm"] = {s: round(v, 3) for s, v in feet.items()}
    res["knee_drop_ok"] = bool(drop >= 60.0 and span_xy <= 120.0
                               and max(feet.values()) <= 3.0)
    res["knee_drop_note"] = ("口径改写：`pelvis_step_ok`（后坐/净前移）→ `knee_drop_ok`"
                             "（骨盆 z 下沉 ≥60、XY ≤120、双脚全程 ≤3）——"
                             "锤击的发力是**屈膝下沉**不是跨步，且**原地**（§0.4 不许 Root Motion）")

    # 6) **打击停顿 4 帧**（冻结判据的数值地板 1e-3，B04 第 6 件）。
    FROZEN_EPS_DEG = 1e-3
    steps, cursor = 0, HIT
    while cursor + 1 <= HIT + HOLD:
        if _step_deg(samples, cursor) > FROZEN_EPS_DEG:
            break
        steps += 1
        cursor += 1
    res["hitstop_frozen_steps"] = steps
    res["hitstop_frames"] = steps + 1
    res["hitstop_window"] = [HIT, HIT + HOLD]
    res["hitstop_present"] = bool(steps + 1 == HOLD + 1)

    # 7) **`body_follow_through_ok`**：通道换成 **rx**（本支是"前折打透"，不是 B04 的
    #    "转体打透"）；时窗必须与 `follow_s` 的**相位**对齐 —— `follow_s` 在
    #    clock 27→31 之间从 0 升到 1，而 clock = frame − HOLD（f>29）⟹
    #    **clock 31 落在 frame 34**。旧窗口 [30,33] 只读到 clock 30，永远读不到峰值。
    ft_lo, ft_hi = HIT + HOLD + 1, FOLLOW_END + HOLD          # [30, 34]
    ft = {}
    for bone, channel in (("chest", 0), ("pelvis", 0)):
        series = [s["euler"].get(bone, (0.0, 0.0, 0.0))[channel] for s in samples]
        peak = max(series[ft_lo:ft_hi + 1])
        ft[bone] = [round(series[HIT], 2), round(peak, 2), round(peak - series[HIT], 2)]
    res["follow_through_deg"] = ft
    res["follow_through_window"] = [ft_lo, ft_hi]
    res["follow_through_window_clock"] = [HIT + 1, FOLLOW_END]
    res["follow_through_channel"] = "rx（前折；B04 用 ry 是因为那是转体直拳）"
    res["body_follow_through_ok"] = bool(
        ft["chest"][2] >= 3.0 and ft["pelvis"][2] >= 3.0)

    # 8) **可取消帧**：f38 有 marker，且该帧拳峰确在**回收路径**上（身体系伸展量）。
    markers = {m.name: int(m.frame) for m in action.pose_markers}
    res["markers"] = markers
    ext = {s: [(fist[s][i] - shoulder[s][i]).length for i in range(len(samples))]
           for s in SIDES}
    ext_hit = sum(ext[s][HIT] for s in SIDES) / 2.0
    ext_cancel = sum(ext[s][CANCEL] for s in SIDES) / 2.0
    ext_guard = sum(ext[s][0] for s in SIDES) / 2.0
    res["cancel_ext_mm"] = [round(ext_guard * 1000.0, 1),
                            round(ext_hit * 1000.0, 1),
                            round(ext_cancel * 1000.0, 1)]
    res["cancel_marker_ok"] = bool(markers.get("CANCEL") == CANCEL
                                   and ext_hit > ext_cancel > ext_guard)

    # 9) **`dual_arm_sync_ok`**（本支独有）：双手锤击必须**一起**砸。
    sync_lo, sync_hi = BURST_START, HIT + HOLD
    dz = [abs(fist["L"][i].z - fist["R"][i].z) * 1000.0
          for i in range(sync_lo, sync_hi + 1)]
    res["dual_arm_dz_max_mm"] = round(max(dz), 2)
    res["dual_arm_dz_at_hit_mm"] = round(abs(
        fist["L"][HIT].z - fist["R"][HIT].z) * 1000.0, 2)
    # ★ 峰值帧这把尺子必须**逐侧用世界空间速度**（`_point_peak_frame`），
    #   不能用欧拉增量（`L1._peak_frame`）：后者被万向节放大 2.34×，且两侧
    #   `hand` 的 roll 搜索历史不同 ⟹ 欧拉峰帧天然不对齐（实测 L=f36 / R=f22，
    #   差 14 帧），而双拳世界坐标逐帧**完全相同**（dz ≡ 0.0）。
    #   那是表示法伪影，不是"没一起砸"。同一支里 `power_chain_timing_ok`
    #   已经因为同一原因换过尺子，这里是同一口径的补全。
    ms_points = {s: ("hand.%s.tail" % s,) for s in SIDES}
    peaks = {s: _point_peak_frame(samples, ms_points[s])[0] for s in SIDES}
    peaks_euler_ref = {s: L1._peak_frame(samples, ARM_BONES[s])[0] for s in SIDES}
    res["dual_arm_peak_frames"] = peaks
    res["dual_arm_peak_frames_euler_ref"] = peaks_euler_ref
    res["dual_arm_peak_gap_frames"] = abs(peaks["L"] - peaks["R"])
    res["dual_arm_sync_ok"] = bool(res["dual_arm_dz_max_mm"] <= 40.0
                                   and res["dual_arm_dz_at_hit_mm"] <= 30.0
                                   and res["dual_arm_peak_gap_frames"] <= 1)

    # 10) 手臂 |Y| 健康度（体检项，**不当门禁** —— B03/B04 的结论）。
    max_y = max(max(abs(samples[i]["euler"].get(b, (0., 0., 0.))[1])
                    for b in ARM6) for i in range(len(samples)))
    res["max_abs_euler_y_deg"] = round(max_y, 2)
    res["euler_y_is_health_check_only"] = True

    # 11) **六段力量传导**：六段幅度全部 > B04（同口径：euler 最大通道幅度）
    #     + 时序 t_髋 ≤ t_肩 ≤ t_手（±1 帧，用**世界空间速度峰值帧**，见
    #     `_point_peak_frame` 的说明）。
    ranges, peaks_euler, peaks_seg = {}, {}, {}
    for segment, bones in SEGMENTS.items():
        ranges[segment] = round(L1._euler_range(samples, bones), 3)
        peaks_euler[segment] = L1._peak_frame(samples, bones)[0]
        peaks_seg[segment] = _point_peak_frame(samples, SEGMENT_POINTS[segment])[0]
    res["power_chain_ranges_deg"] = ranges
    res["power_chain_b04_ranges_deg"] = B04_SEGMENT_RANGES
    res["power_chain_peak_frames"] = peaks_seg
    res["power_chain_peak_frames_euler_ref"] = peaks_euler
    res["power_chain_peak_channels"] = {
        segment: _point_peak_frame(samples, SEGMENT_POINTS[segment])[1]
        for segment in SEGMENTS}
    res["power_chain_timing_measure"] = (
        "世界空间速度峰值帧（euler 步长会被万向节放大 2.34×，不作时序尺子）")
    timing = (peaks_seg["hip"] <= peaks_seg["shoulder"] + 1
              and peaks_seg["shoulder"] <= peaks_seg["hand"] + 1)
    heavier = {k: bool(ranges[k] > B04_SEGMENT_RANGES[k]) for k in SEGMENTS}
    res["power_chain_heavier_than_b04"] = heavier
    res["power_chain_timing_ok"] = bool(timing)
    res["power_chain_ok"] = bool(timing
                                 and all(v >= 0.5 for v in ranges.values())
                                 and all(heavier.values()))

    # 11b) **诊断**：ARM6 逐骨逐通道 euler 幅度（`hand` 段幅度的来源要看得见）。
    arm_ranges = {}
    for name in ARM6:
        vals = [[s["euler"].get(name, (0.0, 0.0, 0.0))[ch] for s in samples]
                for ch in range(3)]
        arm_ranges[name] = [round(max(v) - min(v), 2) for v in vals]
    res["arm_euler_ranges_deg"] = arm_ranges
    res["arm_euler_range_max"] = round(max(max(v) for v in arm_ranges.values()), 3)
    res["arm_euler_range_max_at"] = max(
        ((max(v), n, "xyz"[v.index(max(v))]) for n, v in arm_ranges.items()))

    # 12) **收招不许瞬停**：末 6 帧最大欧拉增量单调收敛 + 峰值锁在命中帧。
    deltas, tail_bones = [], []
    for index in range(len(samples) - 6, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst_step, worst_bone = 0.0, None
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > worst_step:
                worst_step, worst_bone = step, name
        deltas.append(round(worst_step, 5))
        tail_bones.append(worst_bone)
    res["tail_deg_per_frame"] = deltas
    res["tail_worst_bone"] = tail_bones
    res["decel_smooth_ok"] = bool(all(deltas[i + 1] <= deltas[i] + 1e-9
                                      for i in range(len(deltas) - 1)))
    res["no_snap_stop_ok"] = bool(deltas[-1] <= 5.0 and deltas[-1] <= deltas[0])

    peak_frame, peak_val = L1._peak_frame(samples, ARM6)
    res["arm_peak_step_frame"] = peak_frame
    res["arm_peak_step_deg"] = peak_val
    res["recover_first_step_deg"] = round(_step_deg(samples, HIT + HOLD), 3)
    res["burst_last_step_deg"] = round(_step_deg(samples, HIT - 1), 3)
    res["no_teleport_budget_left_deg"] = round(25.0 - peak_val, 3)

    # 13) IK 到位 / 腿可达余量 / 膝（体检）。
    res["ankle_target_error_mm"] = round(target_err * 1000.0, 3)
    res["ik_reach_ok"] = bool(target_err * 1000.0 <= 5.0)
    limit = A.L_THIGH + A.L_SHIN
    res["leg_reach_max_mm"] = {s: round(max(r[s] for r in reach) * 1000.0, 1)
                               for s in SIDES}
    res["leg_reach_headroom_mm"] = {
        s: round((limit - max(r[s] for r in reach)) * 1000.0, 1) for s in SIDES}
    res["leg_reach_ok"] = bool(all(limit - max(r[s] for r in reach) >= 0.0
                                   for s in SIDES))
    bend = CR.knee_series(arm, action, [s["frame"] for s in samples])
    res["knee_bend_span_deg"] = {s: round(max(b[s] for b in bend)
                                          - min(b[s] for b in bend), 2)
                                 for s in SIDES}
    res["arm_extension_max"] = {
        s: round(max(r for side, r in EXTEND if side == s), 4) for s in SIDES}

    # 14) 攻击元数据登记。
    res["antic_frame"] = ANTIC_END
    res["hit_frame"] = HIT
    res["cancel_frame"] = CANCEL
    res["hitstop_frame_span"] = [HIT, HIT + HOLD]
    return res


# =============================================================== 主流程
def main():
    global ANKLE_REST, IDLE_POSE, POLE

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("HEAVY02_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ---- 定盘数：一律从 `Idle_01@0` 成品姿态读，不手抄。
    IDLE_POSE = I1.idle_pose(arm, 0.0)
    ANKLE_REST = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                  for side in SIDES}
    POLE = {side: _pole_from_pose(arm, side) for side in SIDES}
    fist_guard = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    shoulder_guard = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                      for s in SIDES}
    A.report("HEAVY02_IDLE_TRUTH", {
        "front_foot": "L" if ANKLE_REST["L"].y < ANKLE_REST["R"].y else "R",
        "ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]] for s in SIDES},
        "fist_mm": {s: [round(v * 1000.0, 1) for v in fist_guard[s]] for s in SIDES},
        "fist_z_mm": {s: round(fist_guard[s].z * 1000.0, 1) for s in SIDES},
        "shoulder_mm": {s: [round(v * 1000.0, 1) for v in shoulder_guard[s]]
                        for s in SIDES},
        "guard_offset_mm": {s: [round(v * 1000.0, 1) for v in O_GUARD[s]]
                            for s in SIDES},
        "pole_mm": {s: [round(v * 1000.0, 1) for v in POLE[s]] for s in SIDES},
        "arm_reach_mm": round((bone_len(arm, "upperarm.L") + bone_len(arm, "forearm.L")
                               + bone_len(arm, "hand.L")) * 1000.0, 1),
        "note": ("双手锤击 = **双臂合力**；与 B04 单臂后手重拳互补"
                 "（B04 打胸 1117.7 / 本支打腰以下）"),
    })

    # ---- 正式生成：首帧整帧取 `Idle_01@0`，其后逐帧 IK 构造。
    #      ★★ 沿用 B04 第 1 件：**不覆写 `JS.Y_SAFE` / `JS.ROLL_COMFORT`**，用库默认。
    JS._PREV_EULER.clear()
    for name, value in IDLE_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    JS.ARM_QUAT.clear()
    JS.ARM_ROLL.clear()
    JS.ROLL_MAX.clear()
    for name in ARM6:
        JS.ARM_QUAT[name] = arm.pose.bones[name].matrix.to_quaternion()
    del TARGETS[:]
    del TRACE[:]
    del EXTEND[:]
    del POLE_SIN[:]
    _BULGE_PREV.clear()
    _FROZEN_POSE.clear()

    keyframes = [(0, IDLE_POSE)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, build_pose(arm, frame, record=True)))

    arm_y = {b: max(abs(row["euler"][b][1]) for row in TRACE) for b in ARM6}
    A.report("HEAVY02_ARM_EULER", {
        "max_abs_euler_y_deg": round(max(arm_y.values()), 2),
        "per_bone_y_deg": {k: round(v, 1) for k, v in arm_y.items()},
        "max_roll_deg": {k: round(JS.ROLL_MAX.get(k, 0.0), 1) for k in ARM6},
        "max_extension_ratio": {
            s: round(max(r for side, r in EXTEND if side == s), 4) for s in SIDES},
        "note": ("拳路是肩相对偏移 + 双骨 IK 反解（`aim_carry`：接力 + 绕骨轴 roll "
                 "分支搜索）；搜索旋钮用库默认，`no_teleport` 说话"),
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "普通攻击",
        "note": ("重击（双手锤击）：双拳过顶（拳峰 z 峰值 >1450 mm）+ 屈膝下沉 78 mm "
                 "→ 双臂合力下砸（hit_frame 26，命中拳峰 z < 900 mm，打在腰以下）"
                 "→ 躯干继续前折打透（峰值 clock 31）→ f26~f29 冻结 4 帧 → "
                 "回收停在身前下方的「砸完」姿态（末帧不回 idle）"),
        "antic_frame": ANTIC_END,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "follow_frame": FOLLOW_END,
        "burst_span_clock": [BURST_START, HIT],
        "hitstop_frames": HOLD + 1,
        "hitstop_span": [HIT, HIT + HOLD],
        "motion_clock_hold_frames": HOLD,
        "strike_style": "dual_overhead_hammer",
        "root_motion_m": [0.0, 0.0],
        "root_motion_note": ("**原地**（清单 §0.4：普通攻击不许 Root Motion）。"
                             "本支没有跨步，只有骨盆 z 下沉；引擎位移由程序控制"),
        "knee_drop": {
            "pelvis_drop_mm": "≥60（apex −62 / strike −78 / follow −82）",
            "feet_travel_mm": "≤3（双脚全程钉死，鞋底贴地）",
            "why": ("锤击的发力是**屈膝下沉**不是跨步：口径由 B04 的 `pelvis_step_ok`"
                    "（后坐/净前移）改写为 `knee_drop_ok`（骨盆 z 下沉 / XY / 双脚位移）"),
        },
        "amplitude_vs_b04": {
            "fist_travel_mm": "本支物理上限 ≈660 ⟹ 够不到 B04 的 788.8（竖直下砸）",
            "shoulder_sweep_deg": "> 214.06（B04）—— 本支**靠这条腿过**",
            "fist_height_span_mm": "≈940（真正的锤击幅度：过顶 → 腰以下）",
            "power_chain_six_segments": "六段幅度全部 > B04",
        },
        "follow_through": {
            "window": [HIT + HOLD + 1, HIT + HOLD + 4],
            "peak_clock": FOLLOW_END,
            "channel": "rx（前折）",
            "why": ("f26~f29 是 4 帧完全冻结（clock 被夹在 26），"
                    "「命中后继续前送」只能取冻结之后的窗口；"
                    "本支是对称下砸（ry ≡ 0）⟹ 打透落在 **rx 前折**上"),
        },
        "phase_path": {
            "guard": 0, "apex": CHARGE_END, "strike": HIT,
            "follow": FOLLOW_END, "end": RECOVER_END,
            "burst_start": BURST_START,
            "powers": {"charge": CHARGE_POW, "burst": BURST_POW,
                       "follow": FOLLOW_POW, "settle": SETTLE_POW},
            "why": ("每条通道 = `g + (ch−g)·charge + (st−ch)·burst + "
                    "(fo−st)·follow + (en−fo)·settle`；相位标量精确饱和 ⟹ "
                    "clock 46~49 姿态逐位恒定（末 4 帧零变化）。"
                    "★ 只有 settle 是缓出 `1−(1−u)^p`，其余三个 `u^p` 加速"),
        },
        "dual_arm_sync": "双拳 z 差 ≤40（命中帧 ≤30）+ 双臂峰值帧差 ≤1 帧",
        "link_prev": "Idle_01@0（**首帧**逐位相等；起手不闪）",
        "link_next": ("末帧 = 自持「砸完」姿态（不回 idle）⟹ 可直接接后摇/硬直；"
                      "B06 起沿用这个范式"),
        "power_chain_scale_note": "出拳量级：时序判据 t_髋 ≤ t_肩 ≤ t_手（非 A10 蹬地尺子）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.set_hitstop(action, HIT, HIT + HOLD)
    A.add_markers(action, {
        "GUARD": 0, "ANTIC": 1, "ANTIC_END": ANTIC_END,
        "HIT": HIT, "HITSTOP_END": HIT + HOLD,
        "RECOV": HIT + HOLD, "FOLLOW_END": FOLLOW_END,
        "CANCEL": CANCEL, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # 本支双脚全程钉死 ⟹ 通用脚滑门禁对**两只脚**都生效（比 B04 严）。
    report = A.run_common_assertions(samples, meta)
    idle_mats = CR.action_world_matrices(arm, bpy.data.actions["Idle_01"], 0)
    frames = list(range(0, TOTAL + 1))
    sole = JS.sole_series(arm, action, frames)
    ankles = JS.ankle_series(arm, action, frames)
    reach = JF.reach_series(arm, action, frames)
    target_err = 0.0
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    for index, frame in enumerate(frames):
        for side in SIDES:
            if (frame, side) in pair:
                target_err = max(target_err, (Vector(ankles[index][side])
                                              - pair[(frame, side)]).length)
    report.update(heavy02_assertions(arm, action, samples, idle_mats, sole,
                                     ankles, reach, target_err))
    report["meta"] = meta

    def _diff(before, after, top=6):
        rows = []
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            for channel in range(3):
                rows.append((round(abs(ea[channel] - eb[channel]), 5),
                             name, "xyz"[channel],
                             round(ea[channel], 4), round(eb[channel], 4)))
        rows.sort(reverse=True)
        return [{"d": r[0], "bone": r[1], "axis": r[2],
                 "before": r[3], "after": r[4]} for r in rows[:top]]

    report["hitstop_probe"] = {
        "f%d_vs_f%d" % (HIT, HIT + 1): _diff(samples[HIT]["euler"],
                                             samples[HIT + 1]["euler"]),
    }
    report["tail_probe"] = [
        {"f": samples[i]["frame"], "top": _diff(samples[i - 1]["euler"],
                                                samples[i]["euler"], 3)}
        for i in range(len(samples) - 8, len(samples))]
    report["burst_probe"] = [
        {"f": row["frame"],
         "euler": {b: list(row["euler"][b]) for b in ARM6},
         "roll": row["roll"]}
        for row in TRACE if 12 <= row["frame"] <= 30]
    report["pole_probe"] = [
        {"f": f, "side": side, "sin": round(s, 4)}
        for f, side, s in POLE_SIN if f <= 30]
    report["seg_probe"] = [
        {"f": samples[i]["frame"],
         **{seg: round(max(
             max(abs(samples[i - 1]["euler"].get(n, (0., 0., 0.))[c]
                     - samples[i]["euler"].get(n, (0., 0., 0.))[c])
                 for c in range(3))
             for n in bones), 2)
            for seg, bones in SEGMENTS.items()}}
        for i in range(1, len(samples))]
    report["skipped_gates"] = sorted(
        k for k, v in report.items() if v is None and k.endswith("_ok"))
    failed = sorted(k for k, v in report.items()
                    if (k.endswith("_ok")
                        or k in ("no_teleport", "hitstop_present"))
                    and v is not True and v is not None)
    report["failed"] = failed
    A.report("HEAVY02_REPORT", report)

    if not SKIP_RENDER:
        SIDE = ("side", (4.8, 0.0, 1.05), (0.0, 0.0, 1.05), 2.85, (780, 1160))
        FRONT = ("front", (0.0, -5.2, 1.05), (0.0, 0.0, 1.05), 2.85, (760, 1220))
        TOPQ = ("three_quarter", (3.4, -3.8, 1.20), (0.0, 0.0, 1.05), 2.85,
                (780, 1160))
        A.render_pose_sheet(arm, action,
                            [0, 4, 8, CHARGE_END, 18, 22, HIT, HIT + HOLD,
                             HIT + HOLD + 3, CANCEL, RECOVER_END, TOTAL],
                            "heavy02", views=(SIDE,))
        A.render_pose_sheet(arm, action, [0, CHARGE_END, HIT, TOTAL], "heavy02",
                            views=(FRONT,))
        A.render_pose_sheet(arm, action, [CHARGE_END, HIT], "heavy02", views=(TOPQ,))
        A.save_project()
        A.export_glb(arm)
    print("HEAVY02_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("HEAVY02_FAILURE " + traceback.format_exc())
