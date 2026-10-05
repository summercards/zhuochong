"""anim_heavy_01 —— B04 `Heavy_01` 重拳（明显后拉蓄力 → 跨步轰拳 → 身体随拳打透）。

设计（对着清单「下一支计划 —— B04」逐条落）：
    定位      单发重击，核心是**蓄力—爆发—回收三段清晰**；**允许末帧不回 idle**。
    时长      48 帧 / 0.800 s @60fps，**非循环**。
    首帧      **逐位 = `Idle_01@0`**（起手不许闪）。
    末帧      **停在自持的「前压姿态」**（跨步 + 前倾 + 拳半收），不回 idle。
    结构      GUARD 0 ／ CHARGE 0~12（后坐 + 拳拉到身后）／
              BURST 14~26（`hit_frame = 26`，跨步 160 mm 在爆发段内完成）／
              打透 26~31（躯干继续前送）／
              HITSTOP f26~f29（**4 帧完全冻结**）／
              SETTLE 31~42（单调衰减）／clock 42~45 姿态**逐位恒定**／CANCEL 36。

---------------------------------------------------------------------------
★ 第 0 件：探针先量（`probe_heavy01.py`，只读）。四个定盘数：

  1. **前脚 = L**（踝世界 y：L −169.6 / R +140.4，与 B01/B02/B03 逐位一致）
     ⟹ 前手 = L、后手 = R。**重拳用后手 R**（B01 前手直拳 / B02 后手横拳 /
     B03 前手摆拳 / B04 后手重拳 —— 与前三支的手位节奏不重复）。
  2. **跨步可达性扫描**（本支最大几何风险）：前脚前移 160 mm 时，
     只要骨盆有 ≥30 mm 下沉，前腿余量 ≥15 mm；后腿余量在所有档位都 ≥72 mm。
     ⟹ 取 **前脚前移 160 mm + 骨盆后坐 28 mm / 下沉 38 mm（蓄力）
     → 前送 90 mm / 下沉 30 mm（命中）**。本支实测余量 ≥40 mm。
  3. `|Y|` 体检：guard 的最大 `|Y|` 是 **15.19°**（远小于 B03 的 61.45°）——
     重拳是"直"的，万向节锁风险低。按 B03 结论：`|Y|` 只作体检，
     判据仍交回 `no_teleport`。
  4. 预算：**本支放弃"guard→strike 单段插值"**（B01/B02/B03 三次都死在
     "STRIKE 段装不下"），改成**四段姿态路径**，每段帧数按
     `峰值 = span×(1−(1−1/n)^p) ≤ 25` 反算：
     蓄力 12 帧 (`p=1.30`) ／ 爆发 **14 帧** (`p=1.00`) ／ 打透 5 帧 (`p=1.25`) ／
     收招 11 帧 (**缓出** `1−(1−u)^p`)。
     爆发段 14 帧（不是计划里的 6 帧）—— "加帧是唯一可靠的余量来源"。
     **首版 12 帧 + `p=1.35` 实测末帧 euler 步 54.233°（判据 25）**，
     见 `burst_s` 注释。

---------------------------------------------------------------------------
★ 第 1 件：**「跨步」怎么写才不撞门禁**（清单 §0.4：普通攻击不许 Root Motion）。
  处置（照计划预案）：
    · **重写两条旧口径**：`feet_pinned_ok` → `cross_step_ok`
      （**前脚**前移 ≥120 mm、**后脚** ≤3 mm、两脚鞋底全程 ∈[−2,+6]、全程鞋底不离地）； `pelvis_small_move_ok` → `pelvis_step_ok`
      （后坐峰值 ≥20 mm、末帧净前移 ∈[50,140] mm、XY 行程 ≤160 mm）。
    · **显式登记 `root_motion_m`**：前移量已烘进姿态，**引擎不得再叠加位移**。
    · ❌ 不沿用旧口径然后把前脚焊死 —— 那会把"跨步"做成假动作。
    · **跨步全部落在 BURST 段内**（clock 14→26）⟹ 命中之后前脚**逐位静止**
      （`cross_step_planted_mm = 0.000`），这正是"落步踩实再发力"的读法。

---------------------------------------------------------------------------
★ 第 2 件：**拳路用「肩相对偏移」+ 双骨 IK，不用绝对世界点/欧拉插值**。
    `fist_target = 肩(upperarm.head) + offset(c)` → `arm_to()` 反解上臂/前臂/手。
  三条理由：
    ① 手臂伸展率可控（`|offset| / 0.650`），不会解到不可达点再被静默截断；
    ② **躯干扭 49° 时拳峰仍朝世界正前**（欧拉插值做不到 —— 它会跟着躯干转）；
    ③ 抬帧/改剖面不需要重算欧拉族。
  护手（L）相反：它的目标定义在**胸骨顶 + 躯干 yaw 旋转**的身体坐标系里，
  这样躯干一扭护手就跟着走，护手手臂的欧拉几乎不动。

  ★ **两个坑（本支踩实了才写下来）**：
  (a) **肘的鼓出方向必须是"从 idle 实测"的，不能拍脑袋**。IK 只确定了肩→腕的
      轴与两段骨长，**肘落在轴的哪一侧由 `pole` 决定**。首版把 `pole` 写死成
      `(0.30, 0.45, -0.84)`，与 idle 的手肘实际鼓出方向差了近 90° ⟹ f0（逐位
      = idle）到 f1（IK 解）**肘翻了**，`hand.L` 单帧欧拉跳 **101.636°**，
      `no_teleport` 红、`power_chain` 的"手"峰值帧被钉在 f1（时序判据连带红）。
      修法：`_pole_from_pose()` 在 idle 姿态上**实测** `(肘−肩)` 去掉沿轴分量后
      的垂足方向 —— 这样才能保证 f1 的 IK 解与 idle 的肘**落在同一侧**。
  (b) **手骨方向必须逐段给，且 guard 段必须 = idle 的 `ARM_DIRS`**。首版护手
      用了恒定 `HAND_CHAMBER`，而 idle 的 `hand.L` 方向是 `(-0.20,-0.70,0.68)`
      ⟹ f0→f1 手骨世界朝向猛转，欧拉表示跟着放大。

---------------------------------------------------------------------------
★ 第 3 件：**躯干轨不能再用 `TURN.track`（分段 Hermite），必须用"相位叠加"**。
  原因（`decel_smooth_ok` 红的真凶）：`TURN.track` 的切线是中心差分，
  **末段的入切线取自它之前那个差异键**。于是即使我给最后两个键相同的值，
  曲线仍会**掠过终点再回来**：

      FRONT_ANKLE_Y = ((0,0),(6,0),(18,−0.16),(42,−0.16),(45,−0.16))
      段 [18,42] 两端值相同，但 m_a = (−0.16−0)/(42−6) = −0.00444 ≠ 0
      ⟹ h10 峰值 0.148 处过冲到 −0.1733，**往返 13.3 mm**，
      `cross_step_planted_mm` 实测 **15.821 mm**（判据 ≤3）红。

  修法：把每条通道写成 **"基准值 + 四段已缓动增量"** 的叠加
  （`chain()`，见下）。每个相位标量都**精确饱和到 1**，所以：

      c=0 → guard ；c=12 → chamber ；c=26 → strike ；c=31 → follow ；c≥42 → end
      **clock 42~45 逐位恒定 ⟹ 末 4 帧步长恒为 0**

  一次性解决 `decel_smooth_ok`（末 3 步恰为 0，单调收敛）、
  `end_pose_hold_ok`、`cross_step_planted_mm`（命中后前脚**逐位不动**）、
  以及 `body_follow_through_ok`（打透段是独立相位，峰值在 clock 31）。

---------------------------------------------------------------------------
★ 第 4 件：**`body_follow_through_ok`（"身体随拳打透"）的时窗陷阱**。
  "命中帧后 2~4 帧继续前送"——但 f26~f29 是 **4 帧完全冻结**（clock 被夹在 26），
  那 4 帧里躯干按定义**一动不动**。所以窗口必须取**冻结之后**：
  `[HIT+HOLD+1, HIT+HOLD+4]` = f30~f34（clock 27~30）。
  ⟹ 躯干 ry 的峰值刻意放在 **clock 31**（打透相位末端），比命中帧再前送 +5~6°。

---------------------------------------------------------------------------
★ 第 5 件：**欧拉解缠用 `JS.aim_carry`（接力 + 绕骨轴 roll 分支搜索）**，
  而不是裸的 `A.aim_bone`。`aim_bone` 用 `rotation_difference` 最小旋转反解，
  只保证"方向对"，**不保证 twist 不累积、也不保证欧拉表示连续**；
  而欧拉通道是逐分量插值的，表示跳 = 真闪帧。`aim_carry` 从**上一帧已达成
  世界朝向**接力（世界旋转逐帧最小变动），并在"步长偏大或 |Y| 逼近万向节锁"
  时绕骨轴扫 roll，取最小代价支（`anim_jump_start` 文件头第 4/6 条的结论）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_heavy_01.py
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

NAME = "Heavy_01"
TOTAL = 48                    # 0.800 s @60fps
HIT = 26                      # 命中帧
HOLD = 3                      # 冻结 f26..f29 = **4 帧**（清单上限）
CLOCK_END = TOTAL - HOLD      # 45：动作时钟跨度

CHARGE_END = 12               # 拳拉到身后（蓄力到位）
ANTIC_END = 14                # 前摇结束（清单「重攻击前摇 12~20 帧」）
FOLLOW_END = 31               # 打透峰值（命中后躯干继续前送，见文件头第 4 件）
RECOVER_END = 42              # 收招到位 ⟹ clock 42~45 姿态逐位恒定
CANCEL = 36                   # 可取消帧（清单）

CHARGE_POW = 1.30
# ★ 爆发 `p`：**保持 1.20**（本支最后一轮的结论 —— 原来卡住的不是它）。
#   爆发段 12→26 = 14 帧，`s(u)=u^1.20`：末帧步长 `Δs=1−(13/14)^1.20` 最大 ⟹
#   拳在**命中帧最快**（`burst_last_step_deg` ≈ 23.2 vs 中段 ≈ 15，比值 1.55），
#   与"蓄力—爆发—收招"的设计意图一致。
#   ★ 曾经以为必须把 p 抬到 1.35~1.45 才能让"手"的发力峰值落在命中帧
#     （`power_chain_timing_ok`）。那是**误判**：当时真正在捣乱的是本文件
#     自己把 `aim_carry` 的 roll 搜索收紧了（见下方 `JS.*` 那段注释）。
#     还原库默认后逐点实测（`H01_BURSTP` 扫描，Y_SAFE/ROLL_COMFORT 用库默认）：
#       p=1.16 → peak 22.33 @f26，budget 2.67；p=1.18 → 23.11，1.89
#       p=1.20 → peak 23.18 @f26，budget 1.82  ★ 取值（手峰对次高 f18=15.47，余 7.7°）
#       p=1.24 → 21.96，3.04；p=1.28 → 24.07，0.93；p=1.32 → `decel_smooth_ok` 抖动
#     全组 `failed=[]`，手峰都在 f26 ⟹ **不需要动 p**，取原值。
BURST_POW = 1.20
FOLLOW_POW = 1.25
SETTLE_POW = 2.00
BURST_START = CHARGE_END     # 爆发起点 = 蓄力饱和点（12）⟹ 爆发段 12→26 = **14 帧**
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

PUNCH = "R"                   # 出拳手 = 后手（探针：前脚 L ⟹ 前手 L、后手 R）
GUARD_HAND = "L"
ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")
ARM_REACH = 0.650             # upperarm 328 + forearm 224 + hand 98 (mm)，探针实测
DROP = I1.DROP                # −0.070：战斗站姿的骨盆下沉量

# B03 的比较基准（"重拳必须比三连终结更重"，基准写死在文件里，不靠记忆）
B03_TRAVEL_MM = 640.9
B03_SWEEP_DEG = 142.78
B03_REACH_MM = 636.5
B03_SEGMENT_RANGES = {"foot": 20.278, "leg": 16.065, "hip": 23.168,
                      "waist": 23.168, "shoulder": 31.218, "hand": 112.885}

# =============================================================== 相位时钟
def clock(frame):
    """动作时钟：命中停顿期间**时间冻结**（f26~f29 读同一个 clock = 26 ⟹ 姿态逐位相同）。"""
    if frame <= HIT:
        return frame
    if frame <= HIT + HOLD:
        return HIT
    return frame - HOLD


def _ramp(c, start, end, power):
    """`start → end` 的幂律上升；两端**精确**取 0 / 1（这是"真平台"的来源）。"""
    if c <= start:
        return 0.0
    if c >= end:
        return 1.0
    return ((c - start) / float(end - start)) ** power


def charge_s(c):
    return _ramp(c, 0.0, CHARGE_END, CHARGE_POW)


def burst_s(c):
    """爆发：`BURST_START(12) → HIT(26)` = **14 帧**（不是计划里的 6 帧），`u**1.20`。

    ★ 为什么把爆发起点从 `ANTIC_END(14)` 提前到 `CHARGE_END(12)`：
      `u**1.35` 在 12 帧上的**末帧步长**是 0.1108 —— 拳臂在这一帧要走完
      最后 11% 的行程（实测 euler 单帧 **54.233°**，判据 25）。
      摊到 14 帧后末帧步长 0.0783~0.0885。**加帧是唯一可靠的余量来源**
      （B01/B02/B03 三次同一死法）。
    ★ 但真正的病根不是帧数，而是 `_elbow_bulge` 的 **pole 退化奇点**：
      查清那个之后 euler 峰值从 54.233 → **23.306**（见 `_elbow_bulge`）。
      所以 `p` 的取值现在就由 `power_chain_timing_ok` 决定（见 `BURST_POW`）。
    """
    return _ramp(c, BURST_START, HIT, BURST_POW)


def follow_s(c):
    return _ramp(c, HIT, FOLLOW_END, FOLLOW_POW)


def settle_s(c):
    """收招：**缓出**（步长随 u→1 单调递减到 0）。

    ★ 为什么不能用 `u**SETTLE_POW`（首版）：`u**p` 的导数随 u **递增**，
      clock 41→42（f44→f45）的单帧步长最大（实测 **8.068°/帧**）⟹ 两条判据同时红：
        · `decel_smooth_ok`（末 6 帧必须单调递减）—— 实测 7.26 / 7.68 / 8.07 递增；
        · `end_pose_hold_ok`（末 4 帧 ≤2°）—— 实测首步 8.0681°。
      读起来也错：末段"越收越快"是急刹，不是滑停。
    ★ 顺带治好 `cancel_marker_ok`（第三条红）：`u**p` 在 clock 33（f36）只到
      **0.033** ⟹ 拳头几乎没回收，"拳峰−肩"伸展 **643.6 mm > 命中帧 640.0**
      （判据要 `hit > cancel`）。缓出在 clock 33 就到 **0.331** ⟹ 伸展回落到
      ~594.7 mm，"可取消帧 = 拳头已在回收"才立得住。
    """
    u = (c - FOLLOW_END) / float(RECOVER_END - FOLLOW_END)
    if u <= 0.0:
        return 0.0
    if u >= 1.0:
        return 1.0
    return 1.0 - (1.0 - u) ** SETTLE_POW


def chain(g, ch, st, fo, en, c):
    """五段姿态路径：guard → chamber → strike → follow → end。

    `= g + (ch−g)·charge + (st−ch)·burst + (fo−st)·follow + (en−fo)·settle`

    每个相位标量都精确饱和，所以 `c=0 / 12 / 26 / 31 / ≥42` 处取到的
    分别是 `g / ch / st / fo / en`，**且 clock ≥42 后逐位恒定**。
    """
    return (g
            + (ch - g) * charge_s(c)
            + (st - ch) * burst_s(c)
            + (fo - st) * follow_s(c)
            + (en - fo) * settle_s(c))


def chain3(g, ch, st, fo, en, c):
    """三个分量各自走 `chain()`（`g/ch/st/fo/en` 都是三元组）。"""
    return tuple(chain(g[i], ch[i], st[i], fo[i], en[i], c) for i in range(3))


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def qbez3(p0, p1, p2, t):
    u = 1.0 - t
    return tuple(u * u * p0[i] + 2.0 * u * t * p1[i] + t * t * p2[i]
                 for i in range(3))


# =============================================================== 躯干轨
# 每行 = (bone, channel, guard, chamber, strike, follow, end)，单位度。
# ★ **c=0 那一列必须逐位等于 `Idle_01@0`**（Idle_01 的手臂/躯干真值）：
#   pelvis 4.0 / spine 2.0 / chest 1.0 / neck −6.0 / head 5.0 / shoulder −18.0，其余 0。
# ★ 镜像：`ry > 0` 把 +X（角色左）侧转向 +Y 身后 ⟹ **右肩向前**。
#   本支出拳手是 **R** ⟹ 命中帧 ry 取**正**（B03 的 L 拳取负）。
TRUNK_CHAIN = (
    ("pelvis", "rx", 4.0, 7.0, 11.0, 12.0, 6.8),
    ("pelvis", "ry", 0.0, -13.0, 17.0, 22.5, 12.4),
    ("spine_01", "rx", 2.0, 3.4, 4.6, 5.0, 2.8),
    ("spine_01", "ry", 0.0, -6.5, 7.5, 9.5, 4.6),
    ("spine_02", "rx", 2.0, 3.4, 4.6, 5.0, 2.8),
    ("spine_02", "ry", 0.0, -6.5, 7.5, 9.5, 4.6),
    ("chest", "rx", 1.0, 2.6, 5.0, 5.4, 2.0),
    ("chest", "ry", 0.0, -13.0, 17.0, 23.0, 11.4),
    # 颈/头反向扭转：胸累计扭 49° ⟹ 颈 −9 + 头 −6.5 收回头部朝向（不跟着甩过去）
    ("neck", "rx", -6.0, -7.6, -11.0, -11.5, -7.2),
    ("neck", "ry", 0.0, 7.0, -9.0, -11.5, -5.6),
    ("head", "rx", 5.0, 5.4, 4.0, 3.8, 5.0),
    ("head", "ry", 0.0, 5.0, -6.5, -8.5, -4.2),
    # 肩带：出拳侧（R）**先向后拉开再前送**（`右臂 rz>0 = 向前`），护手侧相反
    # ★ `shoulder.R rz` 的末端从 7.5 抬到 13.5：不只是"前压姿态里右肩仍偏前"更好看，
    #   更是为了**时序判据**。收招是缓出（首帧步长最大），7.5 时末段摆幅 15.5°
    #   ⟹ 收招首步 **2.69°/帧** > 爆发段峰 2.5 ⟹ `_peak_frame` 把"肩"的发力峰值
    #   判在 **f35（收招段）**，`power_chain_timing_ok` 的"肩 ≤ 手"直接红。
    #   抬到 13.5 后末段摆幅 9.5° ⟹ 收招首步 1.65 < 爆发峰，肩的峰值回到命中帧。
    ("shoulder.R", "rx", -18.0, -13.0, -3.0, -4.0, -15.0),
    ("shoulder.R", "rz", 0.0, -12.0, 20.0, 23.0, 13.5),
    ("shoulder.L", "rx", -18.0, -19.6, -20.5, -20.5, -18.4),
    ("shoulder.L", "rz", 0.0, 3.0, -5.0, -6.0, -1.6),
)

# 骨盆位移（**重写口径**，见文件头第 1 件）：
#   后坐 +28 mm（蓄力） → 前送 −90 mm（命中/跨步） → 收到 −76 mm（前压姿态）。
#   z 随「下沉」走（重心降低把前腿余量从 4.8 mm 抬到 40 mm）。
PELVIS_X = (0.000, 0.008, 0.004, 0.004, 0.002)
PELVIS_Y = (0.000, 0.028, -0.090, -0.096, -0.076)
PELVIS_DZ = (0.000, -0.038, -0.030, -0.022, -0.026)

# 跨步（前脚 L）：**全部落在 BURST 段内**（clock 14→26）⟹ 命中后前脚逐位静止。
STEP_FWD = 0.160
FRONT_ANKLE_X = (0.000, 0.000, 0.009, 0.009, 0.009)
FRONT_ANKLE_Y = (0.000, 0.000, -STEP_FWD, -STEP_FWD, -STEP_FWD)

# ---------------------------------------------------------------- 拳路（肩相对偏移，米）
# `O_*` 都是「拳峰(hand.tail) − 肩(upperarm.head)」的世界向量；`g` 段 = idle 实测。
O_GUARD = (0.0211, -0.2223, -0.0147)      # Idle_01@0 实测
# ★ 蓄力极值：|v| 从 209 mm 抬到 **340 mm**（方向不变）。
#   首版 209 mm ⟹ 腕离肩只有 111 mm，而 upperarm 单骨就 328 mm ⟹ 反解把肘
#   折到 **8.2°**（人手极限约 35~40°，IK 已贴死"自折"奇点），f0→f1 与爆发起
#   两端的欧拉表示都被放大。抬到 340 mm 后肘内角 **47.5°**，是"拳头拉到胯侧
#   身后、肘弯 45°"的正常重拳蓄力，也不再踩奇点。
O_CHAMBER = (-0.1625, 0.1139, -0.2764)    # 340 mm × (−0.478, 0.335, −0.813)
# ★ 命中伸展从 0.985 × 臂长 收到 **0.96 × 臂长**：0.985 时腕目标离肩
#   550 mm / 552 mm ⟹ `cos_hip` 被钳到 1（另一端的"肘拉直"奇点），
#   实测 `max_extension_ratio` = **0.9966**。收到 0.96 后约 0.95，
#   拳仍接近全展（视觉上是直的），而命中帧的欧拉不再坐在奇点上。
#   代价：前伸 −16 mm（738.7 → ~722），仍远大于 B03 的 636.5。
O_STRIKE = (0.0624, -0.6082, -0.1247)     # 0.96 × 0.650 × (0.100,−0.9747,−0.1999)
O_FOLLOW = (0.0632, -0.6160, -0.1263)     # 0.632：命中后再挤出 8 mm
O_END = (0.055, -0.470, -0.160)           # 半收，前压姿态（拳仍朝前）
O_BURST_CTRL = (-0.150, -0.310, -0.130)   # 二次 Bezier 控制点：拳走**外弧**过中线
O_REC_CTRL = (0.070, -0.560, -0.140)

# 手骨世界方向（**逐段给**；g 段必须 = idle 的 `ARM_DIRS`，见文件头第 2(b) 件）。
# ★ 相邻段之间**夹角必须小**：手骨的世界朝向变化会在欧拉通道上被放大
#   （父链同时在转，两者反向时步长相加）。首版 `chamber` 取 (0.05,−0.92,−0.38)，
#   与 guard 差 **147°** ⟹ 蓄力段单帧欧拉步 **44.247°**（f9, hand.R），
#   `no_teleport` 红、`power_chain` 的"手"峰值帧被钉到 f9。改成 ≤46° 一段。
PUNCH_HAND = (I1.ARM_DIRS["hand.R"],        # (0.18, -0.60, 0.78)
              (0.21, -0.90, 0.16),          # 与 guard 夹 45.4°
              (0.10, -0.985, -0.14),        # 与 chamber 夹 27.8°
              (0.09, -0.985, -0.16),        # 与 strike 夹 1.5°
              (0.06, -0.94, -0.34))         # 与 follow 夹 9.7°
LEAD_HAND = (I1.ARM_DIRS["hand.L"],         # (-0.20, -0.70, 0.68)
             (-0.26, -0.62, 0.74),
             (-0.34, -0.52, 0.78),
             (-0.36, -0.50, 0.79),
             (-0.28, -0.58, 0.76))

# 护手（L）目标：定义在「胸骨顶 + 躯干 yaw 旋转」的**身体系**里
L_GUARD = (0.1445, -0.2419, -0.0946)       # Idle_01@0 实测
L_CHAMBER = (0.1500, -0.2700, -0.1000)
L_STRIKE = (0.1700, -0.1200, 0.0100)       # 出拳时护手回收到下巴
L_FOLLOW = (0.1700, -0.1100, 0.0200)
L_END = (0.1600, -0.1900, -0.0600)

# 肘的鼓出方向（pole）—— **一律从 idle 实测**（`_pole_from_pose`），不写死。
POLE_PUNCH = None
POLE_LEAD = None
# ★ pole 退化保护（见 `_elbow_bulge`）：`|pole⊥axis|` 低于 LO 就完全用上一帧的
#   鼓出方向接力，高于 HI 就完全用 pole，中间 **smoothstep 平滑过渡**。
#   ★ 必须是"过渡带"而不是"硬阈值"：首版用单阈值 0.35，实测 sin 在 f15=0.329、
#     f16=0.479 —— 一刀切 ⟹ f16 的鼓出方向从"接力支"**跳**到"pole 支"，
#     肘跟着跳，upperarm.R / hand.R 在 f16 单帧 20°/23.5°（`seg_probe` 的孤立尖峰）。
#     宽带过渡后两支在交界处已经互相收敛，切换点不再存在。
POLE_BLEND_LO = 0.30
POLE_BLEND_HI = 0.90

CHANNEL_INDEX = {"rx": 0, "ry": 1, "rz": 2}

ANKLE_REST = {}               # side -> Vector：`Idle_01@0` 的踝位（后脚钉死点）
IDLE_POSE = {}                # `Idle_01@0` 的完整姿态字典（首帧整帧取用）
FIST_GUARD = {}               # side -> Vector：护体架势拳峰
SHOULDER_GUARD = {}           # side -> Vector：护体架势肩峰（upperarm.head）
L_LOCAL_GUARD = {}            # 护手在「胸骨顶身体系」里的实测偏移
TRACE = []                    # 逐帧手臂欧拉（|Y| 健康度诊断）
TARGETS = []                  # [(frame, side, target)]：腿部 IK 到位核验
EXTEND = []                   # [(frame, side, ratio)]：手臂伸展率体检


def tval(track, c):
    return TURN.track(track, c) if track else 0.0


def trunk_pose(c):
    pose = {}
    for bone, channel, g, ch, st, fo, en in TRUNK_CHAIN:
        row = pose.setdefault(bone, [0.0, 0.0, 0.0])
        row[CHANNEL_INDEX[channel]] = chain(g, ch, st, fo, en, c)
    return {bone: tuple(row) for bone, row in pose.items()}


def trunk_yaw(c):
    """躯干累计绕纵轴扭转（度）—— 护手目标所在的「身体系」就是它定的。"""
    return sum(trunk_pose(c)[b][1]
               for b in ("pelvis", "spine_01", "spine_02", "chest"))


def punch_offset(c):
    """拳峰 − 肩 的世界偏移（米）。四段路径，各段端点精确落在 `O_*`。

    ★ 分段点必须与 `burst_s` 的起点一致（`BURST_START`），否则 clock 12→15
      会从"蓄力饱和支"直接跳到"爆发支"的 0.18，等于白送一跳。
    """
    if c <= BURST_START:
        return lerp3(O_GUARD, O_CHAMBER, charge_s(c))
    if c <= HIT:
        return qbez3(O_CHAMBER, O_BURST_CTRL, O_STRIKE, burst_s(c))
    if c <= FOLLOW_END:
        return lerp3(O_STRIKE, O_FOLLOW, follow_s(c))
    return qbez3(O_FOLLOW, O_REC_CTRL, O_END, settle_s(c))


def punch_hand_dir(c):
    return chain3(PUNCH_HAND[0], PUNCH_HAND[1], PUNCH_HAND[2],
                  PUNCH_HAND[3], PUNCH_HAND[4], c)


def lead_offset(c):
    return chain3(L_GUARD, L_CHAMBER, L_STRIKE, L_FOLLOW, L_END, c)


def lead_hand_dir(c):
    return chain3(LEAD_HAND[0], LEAD_HAND[1], LEAD_HAND[2],
                  LEAD_HAND[3], LEAD_HAND[4], c)


def bone_len(arm, name):
    return (Vector(A.bone_world(arm, name, "tail"))
            - Vector(A.bone_world(arm, name, "head"))).length


def _pole_from_pose(arm, side):
    """实测「肘的鼓出方向」= `(肘−肩)` 去掉沿 `肩→腕` 轴的分量后的单位垂足。

    为什么必须实测：IK 只定肩→腕的轴与两段骨长，**肘落在轴的哪一侧由 pole 决定**。
    pole 与 idle 的手肘实际朝向差 90°，f0（= idle）到 f1（IK 解）就会**翻肘**。
    实测 pole 后，f0 的 IK 解与 idle 的手肘**逐位同侧**，接缝才不闪（文件头第 2(a) 件）。
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

    ★ **本支第 6 件（最贵的一课）：pole 的退化奇点。**
      首版直接用 `pole − axis·(pole·axis)`。问题：蓄力到 chamber 时
      「肩→腕」轴 = (−0.4565, 0.5151, −0.7254)，而从 idle 实测的
      pole = (−0.3575, 0.4487, −0.8191) —— **夹角只有 8.7°**
      ⟹ `|pole⊥| = sin 8.7° = 0.151`，鼓出方向由"轴方向的微小变化"决定。
      轴每转 1°，鼓出方向能转几十度 ⟹ 肘在 f10/f11/f13 单帧甩 **29° / 29° / 32°**
      （判据 25），f13 的真旋转更是 **68°/帧**（`HEAVY01_TRACE_DETAIL`）。
      —— 这是 f13 = 32.094° 的**根因**：剖面怎么调都压不下去
      （实测把爆发段从 12 帧摊到 14 帧、`p` 从 1.35 降到 1.00，
      峰值只从 54.233 降到 32.094，**都卡在同一个几何奇点上**）。

    ★ 处置：把 `pole` 与"上一帧鼓出方向"按 `|pole⊥axis|` **平滑混合**
      （`POLE_BLEND_LO/HI` 之间的 smoothstep 过渡带）。鼓出方向因此**逐帧连续**，
      不再被退化投影翻来翻去。这是"接力"而非"放宽判据" ——
      输出仍是严格垂直于轴的单位向量，只是不再由噪声决定。
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
                w = w * w * (3.0 - 2.0 * w)          # smoothstep 过渡
                bulge = bulge.normalized() * w + alt * (1.0 - w)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    _BULGE_PREV[side] = bulge
    return bulge, sin_pole


def arm_to(arm, pose, side, fist_target, hand_dir, pole):
    """把上臂/前臂/手解到「拳峰（hand.tail）落在世界 `fist_target`、手骨指向 `hand_dir`」。

    与 `TURN.leg_to` 同一套路数（先定几何、再让 Blender 反解）：
      · 腕目标 = 拳峰目标 − 手骨长 × 手骨方向；
      · 肘由 `pole` 决定鼓出方向（叉积平面内的二骨解，见 `_elbow_bulge`）；
      · 逐级交给 `JS.aim_carry` 反解 —— 它从**上一帧已达成世界朝向**接力，
        并在步长偏大 / |Y| 逼近万向节锁时绕骨轴扫 roll（文件头第 5 件）。
    这样做的意义：**手臂伸展率可控**（`|腕目标−肩| / 0.650`），
    不会像欧拉插值那样解到不可达点再被静默截断。
    返回 `|pole⊥axis|`（体检值）。
    """
    upper, fore, handb = ("upperarm." + side, "forearm." + side, "hand." + side)
    length_up = bone_len(arm, upper)
    length_fore = bone_len(arm, fore)
    length_hand = bone_len(arm, handb)
    direction = Vector(hand_dir).normalized()
    wrist_target = Vector(fist_target) - direction * length_hand

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
    pose[handb] = JS.aim_carry(arm, handb, direction)
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
def build_pose(arm, frame, record=False):
    """按帧构造完整姿态（内部一律用 `clock(frame)` 驱动）。"""
    c = clock(frame)
    pose = trunk_pose(c)
    pose["toe.L"] = (0.0, 0.0, 0.0)
    pose["toe.R"] = (0.0, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(chain(*PELVIS_X, c), chain(*PELVIS_Y, c),
                                     DROP + chain(*PELVIS_DZ, c))}
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    # 出拳臂（R）：拳峰 = 肩 + 偏移（**世界方向**，躯干扭了也照直打）
    pole_mark = len(POLE_SIN)
    shoulder_punch = Vector(A.bone_world(arm, "upperarm." + PUNCH, "head"))
    fist_target = shoulder_punch + Vector(punch_offset(c))
    arm_to(arm, pose, PUNCH, fist_target, punch_hand_dir(c), POLE_PUNCH)

    # 护手臂（L）：目标定义在「胸骨顶 + 躯干 yaw」的身体系里 ⟹ 跟着躯干走
    sternum = Vector(A.bone_world(arm, "neck", "head"))
    lead_world = sternum + Vector(TURN.rot_z3(lead_offset(c), trunk_yaw(c)))
    arm_to(arm, pose, GUARD_HAND, lead_world, lead_hand_dir(c), POLE_LEAD)
    for i in range(pole_mark, len(POLE_SIN)):
        POLE_SIN[i] = (frame,) + POLE_SIN[i]

    # 腿：真双骨 IK（3D 瞄准式）。膝弯方向固定世界 −Y（不转身）。
    for side in ("L", "R"):
        target = ANKLE_REST[side].copy()
        if side == "L":
            target.x += chain(*FRONT_ANKLE_X, c)
            target.y += chain(*FRONT_ANKLE_Y, c)
        if record:
            TARGETS.append((frame, side, tuple(target)))
        TURN.leg_to(arm, pose, side, target, (0.0, -1.0))
    JU._unwrap_legs(arm, pose)

    # 足：钉平到世界水平（rest 朝向）。跨步是**平脚滑步**，鞋底全程不离地面。
    for side in ("L", "R"):
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    _record_trace(arm, frame, pose)
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


def heavy_assertions(arm, action, samples, idle_mats, sole, ankles, reach,
                     target_err):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(s["pelvis"]) for s in samples]
    fist_p = [Vector(s["hand." + PUNCH + ".tail"]) for s in samples]
    fist_g = [Vector(s["hand." + GUARD_HAND + ".tail"]) for s in samples]
    shoulder_p = [Vector(s["upperarm." + PUNCH]) for s in samples]
    sternum = [Vector(s["neck"]) for s in samples]

    # 0) **首帧逐位 = `Idle_01@0`**（世界矩阵，不用像素）；末帧**允许不回 idle**。
    m0 = CR.action_world_matrices(arm, action, 0)
    mN = CR.action_world_matrices(arm, action, TOTAL)
    d0, dN = CR.matrix_delta(m0, idle_mats), CR.matrix_delta(mN, idle_mats)
    res["first_frame_delta"] = float("%.3e" % d0)
    res["last_frame_delta"] = float("%.3e" % dN)
    res["guard_start_ok"] = bool(d0 <= 1e-6)
    res["end_pose_switched_ok"] = bool(dN > 1e-3)
    res["end_pose_note"] = ("B04 是单发重击：首帧仍须逐位 = Idle_01@0（起手不闪），"
                            "末帧**停在自持的前压姿态**（matrix_delta 证明真的换了姿态）")

    # 1) **末帧保持**：末 4 帧姿态变化 ≤2°（收招不是"最后一帧瞬停"）。
    hold = []
    for index in range(len(samples) - 4, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst = 0.0
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
        hold.append(round(worst, 4))
    res["end_hold_steps_deg"] = hold
    res["end_pose_hold_ok"] = bool(max(hold) <= 2.0 and dN > 1e-3)

    # 2) **`charge_window_ok`**：蓄力肉眼可见 —— ANTIC ≥12 帧 **且** 拳峰反向
    #    （+Y，身后）位移 ≥150 mm。
    window = range(0, ANTIC_END + 1)
    back = max((fist_p[i].y - fist_p[0].y) * 1000.0 for i in window)
    coil_i = max(window, key=lambda i: (fist_p[i] - fist_p[0]).length)
    res["charge_window_frames"] = ANTIC_END
    res["charge_pullback_mm"] = round(back, 1)
    res["charge_coil_frame"] = coil_i
    res["charge_coil_draw_mm"] = {
        "x_right": round((fist_p[0].x - fist_p[coil_i].x) * 1000.0, 1),
        "y_back": round((fist_p[coil_i].y - fist_p[0].y) * 1000.0, 1),
        "z": round((fist_p[coil_i].z - fist_p[0].z) * 1000.0, 1),
    }
    res["charge_window_ok"] = bool(ANTIC_END >= 12 and back >= 150.0)

    # 3) **幅度**：拳峰世界行程（相对首帧的最大位移）。
    travel = max((f - fist_p[0]).length for f in fist_p) * 1000.0
    res["fist_travel_mm"] = round(travel, 1)
    res["fist_travel_vs_b03_mm"] = round(travel - B03_TRAVEL_MM, 1)

    # 4) **扫掠角**（沿用 B02/B03 换过的口径：以肩为轴的累计扫掠角，取到命中帧）。
    def _sweep(points, pivots, i0, i1):
        total, prev = 0.0, None
        for i in range(i0, i1 + 1):
            d = points[i] - pivots[i]
            if d.length < 1e-9:
                continue
            d = d.normalized()
            if prev is not None:
                total += math.degrees(prev.angle(d))
            prev = d
        return total

    res["shoulder_sweep_deg"] = round(_sweep(fist_p, shoulder_p, 0, HIT), 2)
    res["shoulder_sweep_b03_deg"] = B03_SWEEP_DEG
    res["amplitude_travel_ok"] = bool(travel > B03_TRAVEL_MM)
    res["amplitude_sweep_ok"] = bool(res["shoulder_sweep_deg"] > B03_SWEEP_DEG)
    res["heavy_amplitude_ok"] = bool(res["amplitude_travel_ok"]
                                     and res["amplitude_sweep_ok"])

    # 5) 命中帧前伸量（重拳必须打得比三连终结更远，报告用）。
    res["hit_reach_mm"] = round((sternum[HIT].y - fist_p[HIT].y) * 1000.0, 1)
    res["hit_reach_b03_mm"] = B03_REACH_MM
    res["hit_point_m"] = [round(v, 4) for v in samples[HIT]["hand." + PUNCH + ".tail"]]

    # 6) **`cross_step_ok`**：前脚前移 ≥120、后脚 ≤3、两脚鞋底 ∈[−2,+6]、
    #    命中后前脚落点稳定（≤3）。**这就是「跨步」的可量化口径**。
    front, back_side = "L", "R"
    step_front = (Vector(ankles[0][front]).y
                  - Vector(ankles[-1][front]).y) * 1000.0
    res["cross_step_front_mm"] = round(step_front, 1)      # −Y 为前 ⟹ 正数 = 前进
    res["cross_step_front_travel_mm"] = round(
        max((Vector(ankles[i][front]) - Vector(ankles[0][front])).length
            for i in range(len(ankles))) * 1000.0, 1)
    res["cross_step_rear_mm"] = round(
        max((Vector(ankles[i][back_side]) - Vector(ankles[0][back_side])).length
            for i in range(len(ankles))) * 1000.0, 3)
    planted = max((Vector(ankles[i][front]) - Vector(ankles[HIT][front])).length
                  for i in range(HIT, len(ankles))) * 1000.0
    res["cross_step_planted_mm"] = round(planted, 3)
    sole_min = min(min(sole[i]["L"], sole[i]["R"]) for i in range(len(sole))) * 1000.0
    sole_max = max(max(sole[i]["L"], sole[i]["R"]) for i in range(len(sole))) * 1000.0
    res["sole_min_mm"] = round(sole_min, 2)
    res["sole_max_mm"] = round(sole_max, 2)
    res["cross_step_sole_ok"] = bool(-2.0 <= sole_min and sole_max <= 6.0)
    res["cross_step_ok"] = bool(step_front >= 120.0
                                and res["cross_step_rear_mm"] <= 3.0
                                and planted <= 3.0
                                and res["cross_step_sole_ok"])
    res["cross_step_note"] = ("清单 §0.4：普通攻击不许 Root Motion ⟹ 跨步用"
                              "「骨盆前移 + 前脚平脚滑步 160 mm」表达，"
                              "且**整步落在 BURST 段内**（clock 14→26）；"
                              "门禁口径已从 feet_pinned（双脚 ≤3）改写为"
                              "「前脚前移 ≥120 + 后脚 ≤3 + 命中后前脚落点稳定」")

    # 7) **`pelvis_step_ok`**（重写 B02/B03 的 `pelvis_small_move_ok ≤60 mm`）：
    #    后坐峰值 ≥20 mm（重心后坐看得见）、末帧净前移 ∈[50,140] mm、XY 行程 ≤160 mm。
    sway = max(math.hypot(p.x - pelvis[0].x, p.y - pelvis[0].y)
               for p in pelvis) * 1000.0
    sit_back = max(p.y for p in pelvis) * 1000.0
    net_fwd = -(pelvis[-1].y - pelvis[0].y) * 1000.0
    res["pelvis_xy_span_mm"] = round(sway, 2)
    res["pelvis_sit_back_mm"] = round(sit_back, 2)
    res["pelvis_net_forward_mm"] = round(net_fwd, 2)
    res["pelvis_step_ok"] = bool(sit_back >= 20.0 and 50.0 <= net_fwd <= 140.0
                                 and sway <= 160.0)

    # 8) **打击停顿 4 帧**：f26~f29 逐位相同。
    #    ★ 冻结判据的**数值地板**：`rotation_euler` 是 float32 存进 F-Curve 的，
    #      同一姿态重复求值会给出 ~1e-05 的差异（`hitstop_probe` 实测 f26 vs
    #      f27 最大 1e-05，其余全 0.0，而相邻真实帧差 **54.233°**）。
    #      首版写 `worst > 1e-9` ⟹ 把"确实冻结"判成"没冻"（`hitstop_frozen_steps=0`）。
    #      这是**采样数值地板**，不是设计容差 —— 1e-3 比噪声高两个数量级、
    #      比真实帧差低 4 个数量级，不存在"放宽凑绿"。
    FROZEN_EPS_DEG = 1e-3
    steps, cursor = 0, HIT
    while cursor + 1 <= HIT + HOLD:
        before, after = samples[cursor]["euler"], samples[cursor + 1]["euler"]
        worst = 0.0
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
        if worst > FROZEN_EPS_DEG:
            break
        steps += 1
        cursor += 1
    res["hitstop_frozen_steps"] = steps
    res["hitstop_frames"] = steps + 1
    res["hitstop_window"] = [HIT, HIT + HOLD]
    res["hitstop_frozen_eps_deg"] = FROZEN_EPS_DEG
    res["hitstop_present"] = bool(steps + 1 == HOLD + 1)

    # 9) **`body_follow_through_ok`**（"身体随拳打透"）：窗口必须取**冻结之后**
    #    [HIT+HOLD+1, HIT+HOLD+4] —— f26~f29 按定义一动不动（见文件头第 4 件）。
    ft = {}
    for bone, channel in (("chest", 1), ("pelvis", 1)):
        series = [s["euler"].get(bone, (0.0, 0.0, 0.0))[channel] for s in samples]
        peak = max(series[HIT + HOLD + 1:HIT + HOLD + 5])
        ft[bone] = [round(series[HIT], 2), round(peak, 2), round(peak - series[HIT], 2)]
    res["follow_through_deg"] = ft
    res["follow_through_window"] = [HIT + HOLD + 1, HIT + HOLD + 4]
    res["body_follow_through_ok"] = bool(
        ft["chest"][2] >= 3.0 and ft["pelvis"][2] >= 3.0)

    # 10) **可取消帧**：f36 有 marker，且该帧拳峰确在**回收路径**上。
    #     ★ 量法必须是**身体系**（拳峰 − 肩）而不是世界距离：本支整个人前移
    #     76 mm 且躯干扭了 33°，用"离 f0 的世界距离"会在拳头**已经收回**时
    #     反而读到更大的数（首版 795.4 > 759.3 判红，是量法错、不是动作错）。
    markers = {m.name: int(m.frame) for m in action.pose_markers}
    res["markers"] = markers
    ext_hit = (fist_p[HIT] - shoulder_p[HIT]).length
    ext_cancel = (fist_p[CANCEL] - shoulder_p[CANCEL]).length
    ext_guard = (fist_p[0] - shoulder_p[0]).length
    res["cancel_ext_mm"] = [round(ext_guard * 1000.0, 1),
                            round(ext_hit * 1000.0, 1),
                            round(ext_cancel * 1000.0, 1)]
    res["cancel_ext_note"] = ("[guard, hit, cancel] 的「拳峰−肩」伸展量；"
                              "判据 = hit > cancel > guard（拳头确实在往回缩）")
    res["cancel_marker_ok"] = bool(markers.get("CANCEL") == CANCEL
                                   and ext_hit > ext_cancel > ext_guard)

    # 11) 手臂 |Y| 健康度（体检项，**不当门禁** —— B03 的结论）。
    max_y = max(max(abs(samples[i]["euler"].get(b, (0., 0., 0.))[1])
                    for b in ARM6) for i in range(len(samples)))
    res["max_abs_euler_y_deg"] = round(max_y, 2)
    res["euler_y_is_health_check_only"] = True
    res["euler_y_note"] = ("B03 已证「|Y|>45° 换族」在大幅度动作上失效（flip 支 y 更大）"
                           "⟹ |Y| 只报数，判据交给 no_teleport")

    # 12) **六段力量传导**：位移全非零 + 时序 t_髋 ≤ t_肩 ≤ t_手（±1 帧）
    #     + **六段幅度必须全部 > B03**（"重拳比三连终结更重"）。
    ranges, peaks = {}, {}
    for segment, bones in SEGMENTS.items():
        ranges[segment] = round(L1._euler_range(samples, bones), 3)
        peaks[segment] = L1._peak_frame(samples, bones)[0]
    res["power_chain_ranges_deg"] = ranges
    res["power_chain_b03_ranges_deg"] = B03_SEGMENT_RANGES
    res["power_chain_peak_frames"] = peaks
    timing = (peaks["hip"] <= peaks["shoulder"] + 1
              and peaks["shoulder"] <= peaks["hand"] + 1)
    heavier = {k: bool(ranges[k] > B03_SEGMENT_RANGES[k]) for k in SEGMENTS}
    res["power_chain_heavier_than_b03"] = heavier
    res["power_chain_timing_ok"] = bool(timing)
    res["power_chain_ok"] = bool(timing
                                 and all(v >= 0.5 for v in ranges.values())
                                 and all(heavier.values()))

    # 13) **收招不许瞬停**：末 6 帧最大欧拉增量单调收敛。
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

    def _step_deg(index):
        before, after = samples[index]["euler"], samples[index + 1]["euler"]
        worst = 0.0
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
        return worst

    peak_frame, peak_val = L1._peak_frame(samples, ARM6)
    res["arm_peak_step_frame"] = peak_frame
    res["arm_peak_step_deg"] = peak_val
    res["recover_first_step_deg"] = round(_step_deg(HIT + HOLD), 3)
    res["strike_peak_leads_recover_deg"] = round(
        peak_val - res["recover_first_step_deg"], 3)
    res["burst_last_step_deg"] = round(_step_deg(HIT - 1), 3)
    res["no_teleport_budget_left_deg"] = round(25.0 - peak_val, 3)

    # 14) IK 到位 / 腿可达余量 / 膝（体检）。
    res["ankle_target_error_mm"] = round(target_err * 1000.0, 3)
    res["ik_reach_ok"] = bool(target_err * 1000.0 <= 5.0)
    limit = A.L_THIGH + A.L_SHIN
    res["leg_reach_limit_mm"] = round(limit * 1000.0, 1)
    res["leg_reach_max_mm"] = {s: round(max(r[s] for r in reach) * 1000.0, 1)
                               for s in ("L", "R")}
    res["leg_reach_headroom_mm"] = {
        s: round((limit - max(r[s] for r in reach)) * 1000.0, 1)
        for s in ("L", "R")}
    res["leg_reach_ok"] = bool(all(limit - max(r[s] for r in reach) >= 0.0
                                   for s in ("L", "R")))
    bend = CR.knee_series(arm, action, frames)
    res["knee_bend_span_deg"] = {s: round(max(b[s] for b in bend)
                                          - min(b[s] for b in bend), 2)
                                 for s in ("L", "R")}

    # 15) 攻击元数据登记。
    res["antic_frame"] = ANTIC_END
    res["hit_frame"] = HIT
    res["cancel_frame"] = CANCEL
    res["hitstop_frame_span"] = [HIT, HIT + HOLD]
    res["punch_hand"] = PUNCH
    return res


# =============================================================== 主流程
def main():
    global ANKLE_REST, IDLE_POSE, FIST_GUARD, SHOULDER_GUARD, L_LOCAL_GUARD
    global POLE_PUNCH, POLE_LEAD

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("HEAVY01_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ---- 定盘数：一律从 `Idle_01@0` 成品姿态读，不手抄。
    #      `I1.idle_pose` 结束时骨架正好停在 idle@0 ⟹ 可以顺手实测 pole。
    IDLE_POSE = I1.idle_pose(arm, 0.0)
    ANKLE_REST = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                  for side in ("L", "R")}
    FIST_GUARD = {side: Vector(A.bone_world(arm, "hand." + side, "tail"))
                  for side in ("L", "R")}
    SHOULDER_GUARD = {side: Vector(A.bone_world(arm, "upperarm." + side, "head"))
                      for side in ("L", "R")}
    sternum0 = Vector(A.bone_world(arm, "neck", "head"))
    L_LOCAL_GUARD = tuple(FIST_GUARD[GUARD_HAND] - sternum0)
    POLE_PUNCH = _pole_from_pose(arm, PUNCH)
    POLE_LEAD = _pole_from_pose(arm, GUARD_HAND)
    A.report("HEAVY01_IDLE_TRUTH", {
        "ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]]
                     for s in ANKLE_REST},
        "front_foot": "L" if ANKLE_REST["L"].y < ANKLE_REST["R"].y else "R",
        "punch_hand": PUNCH,
        "guard_hand": GUARD_HAND,
        "fist_mm": {s: [round(v * 1000.0, 1) for v in FIST_GUARD[s]]
                    for s in FIST_GUARD},
        "shoulder_mm": {s: [round(v * 1000.0, 1) for v in SHOULDER_GUARD[s]]
                        for s in SHOULDER_GUARD},
        "sternum_mm": [round(v * 1000.0, 1) for v in sternum0],
        "punch_offset_from_shoulder_mm": [round(v * 1000.0, 1)
                                          for v in O_GUARD],
        "lead_local_offset_mm": [round(v * 1000.0, 1) for v in L_LOCAL_GUARD],
        "pole_punch": [round(v, 4) for v in POLE_PUNCH],
        "pole_lead": [round(v, 4) for v in POLE_LEAD],
        "arm_reach_mm": round(ARM_REACH * 1000.0, 1),
        "note": ("前脚 L（踝 y −169.6）⟹ 前手 L / 后手 R；**重拳用后手 R**"
                 "（B01 前手直拳 / B02 后手横拳 / B03 前手摆拳 / B04 后手重拳）。"
                 "pole 与手臂方向一律从 idle 实测，保证 f1 的 IK 解与 idle 同侧"),
    })

    # ---- 正式生成：首帧整帧取 `Idle_01@0`，其后逐帧 IK 构造。
    #      `_PREV_EULER` **必须连 ARM6 一起 seed**：漏掉臂骨的话 f1 的
    #      `aim_carry` 没有参照，欧拉表示从 idle 猛跳（首版实测 101.636°）。
    #      ★★ **本支最贵的一课：不要动 `aim_carry` 的搜索旋钮。**
    #        曾经在这里把 roll 搜索"收紧"（`Y_SAFE` 62→52、`ROLL_COMFORT` 16→10），
    #        理由是"越早把欧拉中间角驾驶离万向节锁越好"。**这个推测是错的**，
    #        而且它才是 `power_chain_ok` / `power_chain_timing_ok` 一直红的真凶：
    #          · 收紧后 `ROLL_COMFORT=10` 让搜索在**几乎每一帧**都触发，
    #            `hand.R` 的 roll 序列变成 0,−4,−6,−11,−13,**+6**,0,+9,0…（f19 跳 19°）；
    #          · roll 是**自由参数**（绕骨轴自转，完全不影响骨骼朝向），
    #            它一跳，欧拉表示就得用**大位移**去实现**小旋转**：
    #            f19 `hand.R` 欧拉步 **24.07°** 而真实旋转只有 **6°**
    #            （`HEAVY01_TRACE_DETAIL` 的 `24/6`）⟹ `no_teleport` 与时序判据同时受害；
    #          · 还原库默认（`Y_SAFE=62`、`ROLL_COMFORT=16`）后，f19 的 24.07 直接
    #            掉到 **15.5**，"手"的发力峰值自己回到命中帧 f26（23.18）。
    #        实测对比（同一份骨架、只差这两个数）：
    #          52/10 → hand 峰 **f19**，peak 24.08，`failed=['power_chain_ok','power_chain_timing_ok']`
    #          62/16 → hand 峰 **f26**，peak 23.18，`failed=[]`   ★ 库默认
    #          45/6  → hand 峰 f26，peak 24.79，`failed=[]`（余量更薄）
    #          75/20 → hand 峰 f26，peak 26.82，`failed=['no_teleport']`（|Y| 放任 ⟹ 超 25）
    #        ⟹ **本文件不再覆写 `JS.Y_SAFE` / `JS.ROLL_COMFORT`**，用库默认。
    #          "搜索质量"必须靠实测门禁证明，不能靠推理拍板。
    JS._PREV_EULER.clear()
    for name, value in IDLE_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    # `aim_carry` 的接力起点 = f0 的**已达成世界朝向**（= Idle_01@0）。
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

    keyframes = [(0, IDLE_POSE)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, build_pose(arm, frame, record=True)))

    arm_y = {b: max(abs(row["euler"][b][1]) for row in TRACE) for b in ARM6}
    A.report("HEAVY01_ARM_EULER", {
        "max_abs_euler_y_deg": round(max(arm_y.values()), 2),
        "per_bone_y_deg": {k: round(v, 1) for k, v in arm_y.items()},
        "max_roll_deg": {k: round(JS.ROLL_MAX.get(k, 0.0), 1) for k in ARM6},
        "max_extension_ratio": {
            s: round(max(r for side, r in EXTEND if side == s), 4)
            for s in ("L", "R")},
        "note": ("拳路是肩相对偏移 + 双骨 IK 反解（`aim_carry`：接力 + 绕骨轴 roll "
                 "分支搜索）；|Y| 只作万向节锁健康度体检，判据交给 no_teleport。"
                 "extension_ratio ≥ 1 会被静默截断，必须 < 1"),
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "普通攻击",
        "note": ("重拳（单发）：后手 R 明显后拉蓄力（重心后坐 28 mm、拳拉到身后胯侧"
                 "340 mm / 肘弯 47.5°）→ 跨步 160 mm 轰拳（hit_frame 26，"
                 "拳峰 0.96×臂长 出手）→ 身体随拳打透（命中后躯干 ry 继续前送，"
                 "峰值在 clock 31）→ f26~f29 冻结 4 帧 → 回收停在前压姿态（末帧不回 idle）"),
        "antic_frame": ANTIC_END,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "follow_frame": FOLLOW_END,
        "burst_span_clock": [BURST_START, HIT],
        "hitstop_frames": HOLD + 1,
        "hitstop_span": [HIT, HIT + HOLD],
        "motion_clock_hold_frames": HOLD,
        "punch_hand": PUNCH,
        "root_motion_m": [0.0, -0.076],
        "root_motion_note": ("跨步已烘进姿态：前脚前移 160 mm、骨盆净前移 76 mm"
                             "（世界 −Y 为正面）。**引擎不得再叠加位移**，"
                             "否则跨步会翻倍。清单 §0.4 已登记。"),
        "cross_step": {
            "front_foot": "L",
            "front_step_mm": 160.0,
            "step_window_clock": [ANTIC_END, HIT],
            "rear_foot_move_mm": "≤3（钉死）",
            "why": ("清单要求「跨步轰拳」而 Heavy_01 是普通攻击（不许 Root Motion）"
                    "⟹ 用「骨盆前移 + 前脚平脚滑步」表达，鞋底全程不离地；"
                    "整步落在 BURST 段内，命中后前脚逐位静止"),
        },
        "amplitude_vs_b03": {
            "fist_travel_mm": "> 640.9（B03）",
            "shoulder_sweep_deg": "> 142.78（B03）",
            "power_chain_six_segments": "六段幅度全部 > B03",
        },
        "follow_through": {
            "window": [HIT + HOLD + 1, HIT + HOLD + 4],
            "peak_clock": FOLLOW_END,
            "why": ("f26~f29 是 4 帧完全冻结（clock 被夹在 26），"
                    "「命中后继续前送」只能取冻结之后的窗口；"
                    "打透做成**独立相位**（峰值 clock 31）"),
        },
        "phase_path": {
            "guard": 0, "chamber": CHARGE_END, "strike": HIT,
            "follow": FOLLOW_END, "end": RECOVER_END,
            "burst_start": BURST_START,
            "powers": {"charge": CHARGE_POW, "burst": BURST_POW,
                       "follow": FOLLOW_POW, "settle": SETTLE_POW},
            "why": ("每条通道 = `g + (ch−g)·charge + (st−ch)·burst + "
                    "(fo−st)·follow + (en−fo)·settle`；相位标量精确饱和 ⟹ "
                    "clock 42~45 姿态逐位恒定，末 4 帧零变化（真平台）。"
                    "分段 Hermite 做不到这点（末段入切线非零 ⟹ 掠过终点再回来）。"
                    "★ 四个相位标量里只有 **settle 是缓出** `1−(1−u)^p`"
                    "（其余三个是 `u^p` 加速）：收招必须单调滑停，"
                    "加速曲线会让末帧步长最大 ⟹ `decel_smooth_ok` / "
                    "`end_pose_hold_ok` 双红"),
        },
        "link_prev": "Idle_01@0（**首帧**逐位相等；起手不闪）",
        "link_next": ("末帧 = 自持前压姿态（不回 idle）⟹ 可直接接后摇/硬直；"
                      "B05 起沿用这个范式"),
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
    # ★ 跨步是本支的设计意图 ⟹ 通用脚滑门禁只对**后脚**生效；
    #   前脚由 `cross_step_ok` 用新口径判（前移 ≥120 + 命中后落点稳定）。
    report = A.run_common_assertions(samples, meta, foot_probe=("toe.R",))
    idle_mats = CR.action_world_matrices(arm, bpy.data.actions["Idle_01"], 0)
    sole = JS.sole_series(arm, action, list(range(0, TOTAL + 1)))
    ankles = JS.ankle_series(arm, action, list(range(0, TOTAL + 1)))
    reach = JF.reach_series(arm, action, list(range(0, TOTAL + 1)))
    target_err = 0.0
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    for index, frame in enumerate(range(0, TOTAL + 1)):
        for side in ("L", "R"):
            if (frame, side) not in pair:
                continue
            target_err = max(target_err,
                             (Vector(ankles[index][side])
                              - pair[(frame, side)]).length)
    report.update(heavy_assertions(arm, action, samples, idle_mats, sole,
                                   ankles, reach, target_err))
    report["meta"] = meta
    # ---- 诊断：a) 冻结区间首两帧到底差在哪；b) 末 9 帧的单帧步长落在哪根骨。
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
        "keys_only_in_f%d" % HIT: sorted(set(samples[HIT]["euler"])
                                         - set(samples[HIT + 1]["euler"])),
        "keys_only_in_f%d" % (HIT + 1): sorted(set(samples[HIT + 1]["euler"])
                                               - set(samples[HIT]["euler"])),
    }
    report["tail_probe"] = [
        {"f": samples[i]["frame"], "top": _diff(samples[i - 1]["euler"],
                                                samples[i]["euler"], 3)}
        for i in range(len(samples) - 9, len(samples))]
    # ---- 诊断 c) 爆发段（含命中帧）逐帧原始欧拉 + 施加的 roll：
    #      用于定位"哪条通道在末帧被放大"（euler 步长 vs 真旋转步长）。
    report["burst_probe"] = [
        {"f": row["frame"],
         "euler": {b: list(row["euler"][b]) for b in ARM6},
         "roll": row["roll"]}
        for row in TRACE if 12 <= row["frame"] <= 30]
    # ---- 诊断 d) pole 退化体检：`|pole⊥axis|` 小于阈值就说明肘的鼓出方向
    #      由噪声决定（本支 f10/f11/f12 实测只有 0.09~0.15）。
    report["pole_probe"] = [
        {"f": f, "side": side, "sin": round(s, 4)}
        for f, side, s in POLE_SIN if f <= 28]
    # ---- 诊断 e) 六段"逐帧最大欧拉步"：用于看哪一段在哪一帧发力（时序判据的依据）。
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
    A.report("HEAVY01_REPORT", report)

    if not SKIP_RENDER:
        SIDE = ("side", (4.8, 0.0, 0.98), (0.0, 0.0, 0.98), 2.70, (780, 1100))
        FRONT = ("front", (0.0, -5.2, 0.98), (0.0, 0.0, 0.98), 2.70, (760, 1180))
        TOPQ = ("three_quarter", (3.4, -3.8, 1.15), (0.0, 0.0, 0.98), 2.70,
                (780, 1100))
        A.render_pose_sheet(arm, action,
                            [0, 4, 8, CHARGE_END, ANTIC_END, 18, 22, HIT,
                             HIT + HOLD, HIT + HOLD + 3, CANCEL, RECOVER_END,
                             TOTAL], "heavy01", views=(SIDE,))
        A.render_pose_sheet(arm, action, [0, HIT, TOTAL], "heavy01", views=(FRONT,))
        A.render_pose_sheet(arm, action, [HIT], "heavy01", views=(TOPQ,))
        A.save_project()
        A.export_glb(arm)
    print("HEAVY01_DONE failed=%s" % failed)

    detail = []
    for index in range(1, len(TRACE)):
        before, after = TRACE[index - 1], TRACE[index]
        row = {"f": after["frame"]}
        for name in ARM6:
            step = max(abs(a - b) for a, b in
                       zip(before["euler"][name], after["euler"][name]))
            ang = math.degrees(before["quat"][name].rotation_difference(
                after["quat"][name]).angle)
            if ang > 180.0:
                ang = 360.0 - ang
            row[name] = "%d/%d Y%.0f" % (round(step), round(ang),
                                         after["euler"][name][1])
        detail.append(row)
    A.report("HEAVY01_TRACE_DETAIL", detail)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("HEAVY01_FAILURE " + traceback.format_exc())
