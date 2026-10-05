"""anim_grab04 —— C04 `Grab_Start` 抓取（C 族第四支，**带 Root Motion**）。

=============================================================================
清单原文
=============================================================================
「快速伸手抓住敌人，**必须明确双手最终抓取位置**，便于双角色对位」。

选型：**跨步突进的双手擒抱起手（lunging two-handed clinch entry）** ——
重心后坐蓄势 + 双手回收张开 → 后脚先跨、前脚跟进 → 双手自**身侧外后**沿
大圆弧抡到**身前抓取点**、手指合拢 → 命中 4 帧抓取停顿（髋继续前压 12 mm）
→ 抓握保持（双手钉死在世界抓取点、身体只做呼吸级微沉）。

=============================================================================
第 0 件 —— 这支与 C01/C02/C03 的**根本区别**（先认清再动手）
=============================================================================
前三支都是**单角色表演**，判据全是"自己身上的量"（位移、支点、接缝）。
C04 是**第一支"对接"动画** —— 核心交付物不是姿态好不好看，
而是**一个可被另一个角色引用的、明确的手部落点**。所以：

  · 主角是"**双手最终抓取位置**"。本支把它登记成 `grabbed_points_m`
    （世界坐标，米）+ `grabbed_point_L_m` / `grabbed_point_R_m`（Action 元数据，
    平铺是为了绕开 Blender 自定义属性对嵌套容器的限制，见 `build_action`）。
  · **幅度基线没有先例可比**：C01/C02/C03 都是打击，C04 是**伸够**。
    ⟹ 不照抄 `/1.5`、`×1.10~1.20` 那套。本支新量的量是：
    ① 双手**最终**世界位置（抓到没抓到）；② 抓的那一帧之后**不许再滑**。
  · **力学要害换手**：C01~C03 的"沉髋 / 踮脚"在 C04 不是重点，
    重点是**上步距离**（够不够得到）与**躯干扭转**（双手抓必须把躯干转正）。

=============================================================================
第 1 件 —— 接缝：上游 `Heavy_01@CANCEL(36)`，下游 = **抓握保持姿**（C05 的输入）
=============================================================================
★ 与 C01/C02/C03 的**关键差别**：本支的出口**不是** `Idle_01@0`。
C05 `Grab_Hold`（抓住循环）是 C04 的必然下游，所以末帧必须尽量就是 C05 的
**持握姿态**（双手不动、身体只做呼吸级微动），否则 C05 一开局就要大跳变。
C05 还没做 ⟹ 本支把该姿态的**双手世界坐标 + 骨盆位置 + 支点**全部登记下来，
C05 直接引用即可。

★ 上游仍取 `Heavy_01@CANCEL(36)`（与 C01/C02/C03 同源，连接成本最低）。
`probe_c04_baseline.py` 实测该帧：骨盆 (3.34, −89.39, 806.68)、站宽 470.02 mm、
右臂**已经前伸**（hand.R.tail y = −926.64）、左臂在身后低位
（hand.L.tail y = −177.26）⟹ 天然的"刚打完一记重击、右手还伸着"的起手。

★ 出口**不再逐位对齐 Idle** ⟹ 末帧的两脚位置**不必**等于 Idle 平移后的位置。
但为了让 C05 拿到一个"站得住"的基座，仍取 **Idle 站架整体平移 shift_y**
（L 前 R 后、站宽 310 mm），并用 `end_anchor_ok` 保证末帧姿态**可逐位复现**
（这是"下游未生产"时接缝判据唯一诚实的替代口径 —— 见第 5 件）。

    D_TOTAL = 0.450 m  ⟹  shift_y = (PY0 − 0.450) − IDLE_PELVIS.y = −0.53939 m
       L: −329.58 → **−708.96**（上步 **379.38 mm**）
       R:  140.44 → **−398.96**（跨步 **539.40 mm**）

=============================================================================
第 2 件 —— 脚步表：**两次落脚全部压在"前摇段"内**（C03 第 2 件教训的直接应用）
=============================================================================
C03 用血换来的结论：`decel_smooth_ok` 取的是**全骨最大值**，所以
**收招段里只要还有落步，腿的步长就会冲破手臂的衰减包络**。C03 的包络是
`f36 10.88 / f37 14.44 / f38 10.27 …`，它被迫把 L 的落地帧焊死在 f37。

本支的处置**比 C03 更彻底**：两次落脚都排在 `ANTIC(20)` **之前**，
`RETURN_START(32)` 之后的 22 帧**没有任何落步**，腿的步长在收招段恒为 ~0
⟹ 单调门禁**构造性成立**，不需要再去找"包络的哪一段还容得下"。

    R: 支撑 [0, 4] ∪ [12, 54]   摆动 (4, 12)   跨步 539.40 mm
    L: 支撑 [0, 12] ∪ [20, 54]  摆动 (12, 20)  上步 379.38 mm
    ⟹ f5~f11 靠 L、f13~f19 靠 R，**任何一帧至少一只脚在支撑**。

★ 为什么敢把根位移在落脚前就跑掉大半：落脚点 = **终点位置**，
  落地那一刻脚距髋 = (D_TOTAL + 偏移) − D(落地帧)。D 走得太慢就会让脚
  落在髋前很远的地方，髋踝距顶穿腿长被截断 ⟹ 落地滑移（C03 第 6 轮）。
  本支 D 在 f12 已到 150、f20 到 330 ⟹ 落地时 L 脚只在髋前 ≈290 mm，
  实测 `ik_reach_ok` 全程 ≤ 0.885，**这一支最松的就是腿**（与 C03 相反）。

=============================================================================
第 3 件 —— "抓住后手不许再滑"用**位置逆解**实现，不是靠"冻结"
=============================================================================
计划要求 `grab_hold_steady_ok`：抓住后到末帧，**手的世界位置漂移 ≤ 3 mm**。
若只是把姿态冻结，`hitstop_keeps_momentum_ok`（命停期髋必须继续动）就会
把冻结打破 —— 身体一动，冻结的手就跟着动 12 mm ⟹ 直接红。
两个判据**结构性冲突**。

解法是把"手的位置"从"姿态"里**解耦**：新增 `arm_seat()`（与 `leg_seat` 同构的
三骨链逆解：上臂 / 前臂 / 手 = L1 / L2+L3），抓住之后每一帧都**按世界抓取点
重新解一次手臂**。于是：

  · 身体怎么动（命停期髋继续前压、收招段微沉）都行，手**构造性地**钉在抓取点；
  · `aim_bone_ref` 的滚转基准取 **抓取帧自己的骨基座** ⟹ 解出来的姿态与
    抓取帧**逐位同源**（方向相同 ⟹ 最小旋转 = 单位旋转 ⟹ 滚转逐位复现），
    f31→f32 的接缝台阶 ≈ 0，不需要额外配平。

★ 抓取点的**定义**（本支的设计决定，必须写清否则不可复现）：
  抓取点 = **`HOLD_END` 帧双手 hand.tail 的世界坐标**（不是预先拍脑袋定的数）。
  理由：抓取点应当由"手臂够得到"的几何决定；先解出命中帧姿态、
  再从中读取落点，`grab_reach_ok` 就自动是"实际达到的距离 / 臂长"，
  而不是"我希望达到的距离"。

★ 两个帧位的分工（都在 `build_pose` 里）：
    HIT(28)       = **抓取帧**：双手触及敌人、手指合拢、命停开始
    HOLD_END(31)  = **抓握成立帧**：登记抓取点；此帧之后手的世界位置不许动
  `grab_hold_steady_ok` 从 `HOLD_END` 量到 `TOTAL`（"抓住**后**"的字面含义）。

=============================================================================
第 4 件 —— 手指开合：本支唯一"读得出是抓不是打"的通道
=============================================================================
C01/C02/C03 全程 `A.FIST`（握拳），因为那是打击。抓取的辨识度不在手臂位置
（伸拳与伸手在剪影上很像），而在**手指**：本支 f0 握拳（= 上游接缝）、
f20 完全张开、f28 合拢抓住，之后保持。幅度 88° / 8 帧 = 11°/帧（< 25° 门禁）。

=============================================================================
第 5 件 —— `end_anchor_ok`：下游未生产时"接缝判据"的诚实替代
=============================================================================
C03 的 `seam_end_ok` 是拿末帧去比 `Idle_01@0`。C04 的下游 C05 **还不存在**
⟹ 没有可比对象。**不编一个假的比对**，改成比"末帧姿态能不能逐位复现"：
把末帧姿态重新 `apply_pose` 一遍，与 Action 重放的世界矩阵逐位比（≤1e-6）。
它盯的是 C03 第 5 件那个真问题（构造姿态 ≠ Action 重放值），并且正是
C05 的**硬前提**：C05 要能从这个锚点起手，这个锚点就必须是确定且可复现的。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_grab04.py
    SKIP_RENDER=1 只跑门禁（迭代用）；C04_TRACE=1 打逐帧轨迹。
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

NAME = "Grab_Start"
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
TOTAL = _env_i("C04_TOTAL", 54)                 # 0.900 s @60fps
ANTIC = _env_i("C04_ANTIC", 20)                 # 前摇结束（§0.1 重攻击 12~20 帧）
MIDF = _env_i("C04_MIDF", 24)                   # 抓取弧中段（把 100° 大弧劈成两段）
HIT = _env_i("C04_HIT", 28)                     # 抓取帧（双手触及 + 手指合拢）
HOLD = _env_i("C04_HOLD", 4)                    # 抓取停顿 4 帧（§0.1 上限）
HOLD_END = HIT + HOLD - 1                       # 31 = 抓握成立帧（登记抓取点）
RETURN_START = HOLD_END + 1                     # 32
CANCEL = _env_i("C04_CANCEL", 44)

# ---------------------------------------------------------------- 脚步时刻表
# ★ 两次落脚**全部在前摇段内**（文件头第 2 件）。
T_R_OFF = _env_i("C04_R_OFF", 4)                # R（后脚）离地
T_R_ON = _env_i("C04_R_ON", 12)                 # R 落地
T_L_OFF = _env_i("C04_L_OFF", 12)               # L（前脚）离地
T_L_ON = _env_i("C04_L_ON", 20)                 # L 落地 = ANTIC
WINDOWS = {"L": ((0, T_L_OFF), (T_L_ON, TOTAL)),
           "R": ((0, T_R_OFF), (T_R_ON, TOTAL))}
SIDES = ("L", "R")

# 本支**不踮脚**（tip 恒 0），三点支点模型只为"下一支复用"保留：
#   tip = 0 ⟹ `_pivot_ankle` 退化成恒等 ⟹ 踝目标完全由 FLAT_ANK 决定。
SWING_TIP = _env_f("C04_SWING_TIP", 4.0)        # 摆动期足尖角峰值（很小）
TIP_R_OFF = _env_f("C04_TIP_R_OFF", 4.0)
TIP_R_DECAY = _env_i("C04_TIP_R_DECAY", 24)
L_LIFT = _env_f("C04_L_LIFT", 0.085)            # L 上步离地峰值（米）
R_LIFT = _env_f("C04_R_LIFT", 0.095)            # R 跨步离地峰值（米）
R_FALL_POW = _env_f("C04_R_FALLPOW", 1.6)
L_SWING_POW = _env_f("C04_L_SWING_POW", 1.50)
L_SWING_MODE = os.environ.get("C04_L_SWING_MODE", "pow")
R_SWING_POW = _env_f("C04_R_SWING_POW", 2.20)
SOLE_FLOOR_MM = _env_f("C04_SOLE_FLOOR", -0.8)
LEG_TAIL_START = _env_i("C04_LEGTAIL0", T_L_ON)  # 最后一次落地帧 = 换解算器的那帧
_ARM_EASE_P = _env_f("C04_ARMEASE", 1.5)
# ★ 收招"落定"帧：**逐帧取值时把 f ≥ SETTLE 钳到 SETTLE**（见 `_settle`）。
# ★★ 为什么 SETTLE 必须贴着 HOLD_END（= 32）而不是放到 38：
#   第 3 轮的实测给出了一个必须记住的**几何放大**事实 ——
#     收招段若让躯干继续前倾（14.0° → 16.5°），肩前移 42 mm，肩→世界抓取点
#     距离从 635.1 mm 缩到 583 mm。而手被 `arm_seat` **钉死**在抓取点，
#     这条接近伸直的臂链里肩关节内角对距离**极敏感**（sin_sh 从 0.21 涨到
#     0.44）⟹ 肘部沿 bulge 外摆 74 mm ⟹ 前臂欧拉角速度被**放大**。
#     实测：肩位移在**递减**（26.2 → 5.5 → 4.6 → 3.9 → 3.2 → 2.5 → 2.0 mm），
#     前臂步长却在**递增**（3.04 → 2.75 → 3.09 → 4.25 → 6.58 → **10.96**），
#     `decel_smooth_ok` 因此必红。
#   ⟹ 结论：**抓取动作的"收招"不是"拉长行程减速"，而是"抓稳定住"**。
#     把惯性表达在①命停期位移继续前压 12 mm、②f31→f32 的小幅落定（~1.2°，
#     远小于前后段峰值 24°，不是"瞬停"）、③此后逐帧静止 —— 这才是"抓住敌人
#     后定住"该有的样子，也正好把末帧交给 C05 `Grab_Hold` 当静止起点。
SETTLE = _env_i("C04_SETTLE", HOLD_END + 1)

# ---------------------------------------------------------------- Root Motion
# 骨盆前冲量 D（mm，正 = 向前 = 世界 −y）。
# ★ 命停窗内必须**还在爬**（`hitstop_keeps_momentum_ok`）：
#   D(28) = 433 → D(31) = 445 ⟹ `hitstop_momentum_mm` = **12 mm** > 10。
#   ★ 12 而不是 C03 的 30：本支命停期手臂是**位置钉死**的（文件头第 3 件），
#     髋每多压 1 mm，手就多"陷进"敌人 1 mm。12 mm 是"读出压迫感"与
#     "手不许乱动"之间的取中值。
# ★ 落地前先跑掉大半（文件头第 2 件）：f12 已到 150、f20 到 330。
D_TOTAL_MM = _env_f("C04_D_TOTAL", 450.0)
D_KEYS = ((0, 0.0), (6, _env_f("C04_D06", -50.0)),
          (12, _env_f("C04_D12", 150.0)),
          (ANTIC, _env_f("C04_D20", 330.0)),
          (MIDF, _env_f("C04_D24", 395.0)),
          (HIT, _env_f("C04_D28", 433.0)),
          (HOLD_END, _env_f("C04_D31", 445.0)),
          (SETTLE, D_TOTAL_MM), (TOTAL, D_TOTAL_MM))


def D_mm(frame):
    """Root Motion 位移（mm）。**硬上限 = D_TOTAL_MM**，禁止 Hermite 过冲。"""
    return min(RS.track(D_KEYS, frame), D_TOTAL_MM)


def _swing_u(s, power, mode="pow"):
    """摆动归一化位移（C03 的 `_swing_u`，含 `smooth` 与 `pow` 两族及其边界）。"""
    s = max(0.0, min(1.0, s))
    if mode == "smooth":
        return s * s * (3.0 - 2.0 * s)
    if mode == "cub":
        return 1.0 - (1.0 - s) ** 3
    return 1.0 - (1.0 - s) ** power


# ---------------------------------------------------------------- 躯干轨道
# 每条轨道 **frame 0 的值由上游接缝（Heavy_01@36）在 main() 里回填**。
# rx > 0 = 前屈 / 前倾；ry > 0 = 绕纵轴扭转（接缝带 19.16° 的转体）。
# ★ 全程的主线是"**把躯干转正**"：接缝处骨盆/胸腔 ry = 19.16°（右臂前伸的
#   收招姿），到抓取帧必须回到 0 —— 双手抓要求正面朝敌。
# ★★ 第 1 轮门禁的三条红项同根：收招段我把躯干**回正**（15°→13°），肩因此
#   后退 42 mm，肩→抓取点距从 635.1 涨到 659.9 mm，**越过臂长上限 649.675**
#   ⟹ `arm_seat` 截断 10.26 mm ⟹ 手被甩离抓取点同样的量（`grab_hold_drift`
#   实测 10.2542，与截断量逐位吻合）。修法**不是放宽容差**，而是纠正动作
#   设计：抓住敌人之后身体不该回正，而应**继续前压**（重量下沉）—— 这既让
#   肩留在可达域内（前倾 2.5° ⟹ 肩前送 52 mm ⟹ 距离降到 ~583 mm），又是
#   抓取动作物理上该有的样子。
# ★★ 收招段的形状是**门禁的构造量**（C03 第 2 件：`decel_smooth_ok` 取全骨
#   最大值，要求逐帧步长单调不增）。第 2~3 轮把这一条钉死了两次：
#     · 第 1 轮在 f32 放了个"冲出键"（14.0 → 16.2 → 16.5）。`RS.track` 的段
#       起点切线 = 0.55/帧 远大于终点切线 0.0136/帧 ⟹ **段中过冲**（峰值
#       16.75 再回落）⟹ 导数变号 ⟹ 步长 0.4954 → 0.7178 回升。
#     · 第 2 轮删掉冲出键、让 `[HIT, SETTLE]` 成为单段 ⟹ 无过冲，但**几何
#       放大**接管了（见 `SETTLE` 的定义处）⟹ 前臂步长 3.04 → 10.96 递增。
#   ⟹ 最终形状：**命停（f28~f31 逐位冻结）→ f32 一帧小幅落定 → 此后逐帧
#     静止**。步长序列 = [峰值, 0, 0, …] 单调不增，构造性成立。
PELVIS_RX = ((0, 0.0), (8, 5.0), (14, 4.0), (ANTIC, 6.5), (MIDF, 11.0),
             (HIT, 14.0), (SETTLE, 14.0), (TOTAL, 14.0))
PELVIS_RY = ((0, 0.0), (8, 13.0), (14, 9.0), (ANTIC, 4.0), (MIDF, 1.5),
             (HIT, 0.0), (TOTAL, 0.0))
SPINE01_RX = ((0, 0.0), (10, 2.0), (ANTIC, 3.0), (HIT, 6.0),
              (SETTLE, 6.0), (TOTAL, 6.0))
SPINE01_RY = ((0, 0.0), (10, 5.0), (ANTIC, 2.0), (HIT, 0.0), (TOTAL, 0.0))
SPINE02_RX = ((0, 0.0), (10, 2.0), (ANTIC, 3.0), (HIT, 6.0),
              (SETTLE, 6.0), (TOTAL, 6.0))
SPINE02_RY = ((0, 0.0), (10, 5.0), (ANTIC, 2.0), (HIT, 0.0), (TOTAL, 0.0))
CHEST_RX = ((0, 0.0), (10, 2.0), (ANTIC, 3.5), (HIT, 7.0),
            (SETTLE, 7.0), (TOTAL, 7.0))
CHEST_RY = ((0, 0.0), (8, 12.0), (14, 7.0), (ANTIC, 2.5), (MIDF, 1.0),
            (HIT, 0.0), (TOTAL, 0.0))
# 颈/头：接缝处头被转体带偏，本支把视线**转正盯住敌人**（ry → 0）。
NECK_RX = ((0, 0.0), (12, -8.0), (ANTIC, -9.0), (HIT, -6.0),
           (SETTLE, -6.0), (TOTAL, -6.0))
NECK_RY = ((0, 0.0), (10, -5.0), (ANTIC, -2.0), (HIT, 0.0), (TOTAL, 0.0))
HEAD_RX = ((0, 0.0), (12, 6.0), (ANTIC, 6.5), (HIT, 5.0),
           (SETTLE, 5.0), (TOTAL, 5.0))
HEAD_RY = ((0, 0.0), (10, -4.0), (ANTIC, -1.5), (HIT, 0.0), (TOTAL, 0.0))
# 肩带：伸手必须由**肩胛带前送**发起（§0.6 力量链：肩→手）。
#   rz 语义两侧镜像：L rz>0 = 向后、R rz>0 = 向前 ⟹ 前送 = L 负 / R 正。
SHOULDER_R_RX = ((0, 0.0), (10, -10.0), (ANTIC, -4.0), (HIT, -2.0),
                 (SETTLE, -2.0), (TOTAL, -2.0))
SHOULDER_L_RX = ((0, 0.0), (10, -14.0), (ANTIC, -6.0), (HIT, -2.0),
                 (SETTLE, -2.0), (TOTAL, -2.0))
SHOULDER_R_RZ = ((0, 0.0), (10, 10.0), (ANTIC, 16.0), (HIT, 20.0),
                 (SETTLE, 20.0), (TOTAL, 20.0))
SHOULDER_L_RZ = ((0, 0.0), (10, -8.0), (ANTIC, -14.0), (HIT, -19.0),
                 (SETTLE, -19.0), (TOTAL, -19.0))

# 骨盆世界位移。★ 屈膝**压住重心**（806.68 → 750），全程不上抬 ——
#   上抬会把髋踝距顶到腿长上限（C03 第 1 轮就栽在这），而本支是**上步**，
#   重心必须低、腿才有余量够得到前脚。
PELVIS_X = ((0, 0.0), (10, -0.015), (ANTIC, 0.006), (HIT, 0.010),
            (SETTLE, 0.010), (TOTAL, 0.010))
# ★ 收招段微沉（0.7560 → 0.7545）：位移轨道经 `_settle()` 钳位后末段恒定。
PELVIS_Z = ((0, 0.80668), (6, 0.7850), (12, 0.7620), (ANTIC, 0.7500),
            (MIDF, 0.7520), (HIT, 0.7560),
            (SETTLE, 0.7560), (TOTAL, 0.7560))
Z_SEAM = PELVIS_Z[0][1]

# ---------------------------------------------------------------- 手臂方向轨道
# 世界单位向量（x = 左正，y = 身后正，z = 上正）。★ C03 第 1 件血教训：
# 这**不是**躯干系，写"随躯干前倾"必须自己换算。
# ★★ 第 8 轮返工（目检否决第 7 轮的"合格"）：三条实测判据 + 三张渲染图一起
#   认定 HIT 姿是「耸肩/投降」而不是「抓取」——
#     · 双手在骨盆上方 **599 mm**（≈下巴高，抓敌人应该抓胸 40~50% 身高）
#     · 双手间距 **598.6 mm**（≈2 倍肩宽 288；抓一个人应该是肩宽量级）
#     · 前视图：双前臂**沿肋侧向上张开**，手在肩两侧外侧
#     · 侧视图：手在**正前方**、与肩同高 ⟹ 真实方向是"前 + 上"而不是"前"
#   根因：`HIT` 把 z 写到 +0.32（我按"手臂从身侧抡上来、自然带一点上"写的），
#   而世界系 z 对 328 mm 的上臂就是 +105 mm 的肩外抬 ⟹ 整个手臂被抬到胸线以上。
#   ⟹ 修法：抓取帧改为**双手在身前中低位、略低于肩、间距约一个肩宽**：
#        上臂「前 + 下 + 极少外」（z 必须 **负**），前臂「纯前 + 微下」，
#        两段近似同向 ⟹ 内角小 ⟹ `grab_reach_ok` 闭式解 R 大、比值低。
#        期望抓取点：骨盆上方 ≈ 280 mm（敌人胸口高度）、间距 ≈ 334 mm。
#   ★ 中段一并改：第 7 轮的 MID 是「双臂侧平举」（x 到 ±0.84）——前视图剪影
#     横向张开，把动作读成"张开双臂"而不是"伸手去抓"。改为从前下方走**窄弧**
#     收向身前，x 全程不超过 ±0.52，让整条轨迹读成"双手猛伸向前"。
ARM_KEYS = {
    # 前摇：双臂**回收下垂、肘深屈（内角 ≈132°）、双手张在身侧外后** ——
    # 这是"抡"而不是"戳"的起手式。★ 接缝本身左臂就在这个位置（实测 seam
    # upperarm.L = (0.6455, 0.2726, −0.7134)），所以这一段的**主要动作是右臂
    # 从前伸位收回**（right 从 (−0.0135, −0.8374, −0.5464) 拉回来）。
    #   ★ 第 8 轮把双手从"外后"收到"身前外"，内角从 ≈132° 收到 ≈102°
    #     —— 前摇剪影更像"双手收在身前等机会"，且这段更短，整条弧线才读得通。
    "ANTIC": {
        "upperarm.L": (0.30, -0.30, -0.90),
        "forearm.L": (0.40, -0.88, -0.26),
        "hand.L": (0.40, -0.88, -0.26),
        "upperarm.R": (-0.30, -0.30, -0.90),
        "forearm.R": (-0.40, -0.88, -0.26),
        "hand.R": (-0.40, -0.88, -0.26),
    },
    # 中段：ANTIC→HIT 的大圆中点、**微向外偏一点**（x 到 ±0.48 为止）——
    # 保留"横摆"的剪影，但剪影宽度压在肩宽量级以内，读成"双手猛伸"而不是
    # "张开双臂"。这一段也把单段大弧劈成两段，
    # 防"单段大弧 + 万向节锁"把欧拉通道顶爆（C02 第 2 件）。
    "MID": {
        "upperarm.L": (0.4813, -0.6818, -0.5514),
        "forearm.L": (0.3209, -0.9426, -0.0902),
        "hand.L": (0.3209, -0.9426, -0.0902),
        "upperarm.R": (-0.4813, -0.6818, -0.5514),
        "forearm.R": (-0.3209, -0.9426, -0.0902),
        "hand.R": (-0.3209, -0.9426, -0.0902),
    },
    # 抓取帧：**双臂斜前伸、略低于肩、间距约 1.3 个肩宽**（内角 24.7° ⟹ 0.977）。
    # hand 与 forearm 同向 ⟹ 腕是直的 ⟹ 手链退化成"上臂 + (前臂+手)"两段，
    # `grab_reach_ok` 才有闭式解：
    #     R = √(L1² + (L2+L3)² + 2·L1·(L2+L3)·cosθ)   L1=328、L2+L3=322
    #     θ = 24.7° ⟹ R = 635.0 mm ⟹ 比值 0.977（阈值 0.995）
    # ★ z 必须为**负**（手臂低于肩）—— 这是第 8 轮的教训本身。
    # ★ x 不能大：第 8 轮 x=0.395 把双手推到 678.9 mm 间距（2.36 倍肩宽），
    #   读成"双臂张开"。上臂走"斜前"（x=0.400 + 深度 −0.879）而非"斜外"，
    #   前臂再内收到 x=0.150 ⟹ 间距降到 ≈366 mm（1.27 倍肩宽），才是"抓人"。
    "HIT": {
        "upperarm.L": (0.400, -0.879, -0.260),
        "forearm.L": (0.150, -0.986, 0.070),
        "hand.L": (0.150, -0.986, 0.070),
        "upperarm.R": (-0.400, -0.879, -0.260),
        "forearm.R": (-0.150, -0.986, 0.070),
        "hand.R": (-0.150, -0.986, 0.070),
    },
}
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_PHASES = ((0, "SEAM", _env_p("C04_PH0", "smooth")),
              (ANTIC, "ANTIC", _env_p("C04_PH1", "linear")),
              (MIDF, "MID", _env_p("C04_PH2", "linear")),
              (HIT, "HIT", "linear"),
              (HOLD_END, "HIT", "linear"))

# ---------------------------------------------------------------- 命停该冻谁
# ★ 腿**不冻**（C02/C03 先例）：命停期髋继续前压 12 mm，腿必须跟着撑住，
#   否则支撑脚相对地面会滑 12 mm，`stance_pivot_ok` 立红。
HITSTOP_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "shoulder.L", "shoulder.R",
                 "upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R")


def _settle(frame):
    """收招"落定"：f ≥ SETTLE 一律折回 SETTLE 取值。

    ★ C04 第 2~3 轮结论：把"末段静止"交给插值器（"末段切线强制为 0"）是**不
      可靠**的 —— `RS.track` 的段起点切线取中心差分（= 前一段的弦斜率），与终点
      切线 0 不同号时会在段中**过冲**，导数变号，`decel_smooth_ok`（逐帧步长
      单调不增）必红。钳位取值把这件事变成**结构性**的：`SETTLE` 之后每一条
      旋转/位移轨道都取同一个数 ⟹ 逐帧步长精确为 0，与插值器形状完全解耦。
    """
    return SETTLE if frame > SETTLE else frame


def _hold(frame):
    """命停窗（HIT ~ HOLD_END）：旋转**逐位冻结**，位移继续前压。"""
    return HIT < frame <= HOLD_END


# ---------------------------------------------------------------- 门禁阈值
SOLE_RANGE_MM = (-2.0, 6.0)
PIVOT_DRIFT_MAX_MM = 3.0
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
# ---- 抓取专属
GRAB_HOLD_DRIFT_MAX_MM = 3.0     # 同 `stance_pivot_ok`，对象换成手
GRAB_REACH_MAX_RATIO = 0.995     # 同 IK 口径
END_ANCHOR_TOL = 1e-6
# 本支**不设**幅度倍数门禁：C04 是伸够不是打击，没有同向先例可比
#   （文件头第 0 件）。取而代之的是"抓取点存在 + 可达 + 抓住后不滑"三条。

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
PIVOT_VERT = {}
FLAT_ANK = {}
PIVOT_AXIS = {}
PIVOT_SCALE = {}
_PIVOT_K_DEFAULT = 1.0
FROZEN_SHIFT = {}
WINDOW_SOLE = {}
AIR_SOLE = {}
ALL_SOLE = {}
LEG_TAIL_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
_TAIL_ANCHOR = {}
_LEG_ANCHOR = {}
_KNEE_ANCHOR = {}
_HIT_FROZEN = {}       # HIT 帧的 HITSTOP_BONES 欧拉，命停帧逐位复制（"完全冻结"）
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
R_OFF_ANK = None
SEAM_ANK = {}
ARM_LEN = {}           # side -> {"upper","forearm","hand"}（米，实测骨长）
# ---- 抓取点（在 HOLD_END 帧由 build_pose 就地捕获）
GRAB_POINT = {}        # side -> Vector（世界）
GRAB_SHOULDER = {}     # side -> Vector（抓取帧的 upperarm.head 世界位）
GRAB_ELBOW = {}        # side -> Vector（抓取帧 shoulder→elbow 的单位方向）
ARM_REF = {}           # bone -> (基准 3×3, 基准方向)，抓握保持段的滚转基准
ARM_SEAT_CLAMP = {}    # side -> {any, worst_frame, worst_over_mm, ...}（诊断，必须 any=False）
END_POSE = {}          # TOTAL 帧的姿态（end_anchor_ok 用它复现）


# =============================================================== 脚步与踝目标
def window_of(side, frame):
    for index, (a, b) in enumerate(WINDOWS[side]):
        if a <= frame <= b:
            return index
    return None


def tip_of(side, frame):
    """足尖角（度，+ = 压脚背 / 踮脚）。本支**不踮脚**，只在两次摆动里给几度。"""
    if side == "L":
        if frame <= T_L_OFF or frame >= T_L_ON:
            return 0.0
        s = (frame - T_L_OFF) / float(T_L_ON - T_L_OFF)
        return SWING_TIP * math.sin(math.pi * s) ** 0.7
    if frame <= 0:
        return 0.0
    if frame < T_R_OFF:
        s = frame / float(T_R_OFF)
        return TIP_R_OFF * (s ** 1.60)
    if frame >= TIP_R_DECAY:
        return 0.0
    s = (frame - T_R_OFF) / float(TIP_R_DECAY - T_R_OFF)
    return TIP_R_OFF * (1.0 - s) ** 1.30


def _pivot_ankle(key, tip):
    """绕**实测**滚动支点解出该足尖角下的踝世界目标（C02 第 1 件的三点支点模型）。

    ★ 本支 `tip ≡ 0`（除摆动期的几度）⟹ `rot` ≈ 恒等 ⟹ 结果 ≈ `FLAT_ANK`。
      三分量照抄，不因为"这次用不上"就退化成两分量（C03 同款理由）。
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


# =============================================================== 姿态
def torso_pose(frame):
    # ★ 旋转：命停窗折回 HIT（逐位冻结），收招落定后折回 SETTLE（逐位静止）。
    f = HIT if _hold(frame) else _settle(frame)
    loc_f = _settle(frame)
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
        # ★ 命停期位移轨道**不冻**（`@loc` 用原 frame）—— 只有旋转被冻；
        #   收招段用钳位后的 `loc_f`（同 `_settle`）保证末段位移逐位恒定。
        "@loc": {"pelvis": A.wloc(RS.track(PELVIS_X, loc_f),
                                  PY0 - D_mm(frame) / 1000.0,
                                  RS.track(PELVIS_Z, loc_f) - 0.900)},
    }


def arm_dirs(frame):
    if _hold(frame):
        frame = HIT
    frames = [item[0] for item in ARM_PHASES]
    if frame <= frames[0]:
        return dict(SEAM_DIRS)
    if frame >= frames[-1]:
        return dict(ARM_KEYS["HIT"])
    for index in range(len(ARM_PHASES) - 1):
        fa, na, mode = ARM_PHASES[index]
        fb, nb, _mode_b = ARM_PHASES[index + 1]
        if not (fa <= frame <= fb):
            continue
        if fa == fb:
            continue
        source = SEAM_DIRS if na == "SEAM" else ARM_KEYS.get(na)
        target = (ARM_KEYS["HIT"] if nb == "HIT" else ARM_KEYS.get(nb))
        u = (frame - fa) / float(fb - fa)
        t = u if mode == "linear" else RS.smooth(u)
        return {bone: RS.slerp_dir(source[bone], target[bone], t)
                for bone in ARM_BONES}
    return dict(ARM_KEYS["HIT"])


# ---------------------------------------------------------------- 手臂：世界步进封套
# 承 C02 第 2/3/10 轮的结论：`no_teleport`（欧拉逐分量）在大绕弧 +
# 万向节锁附近放大 2~4.6 倍，是**通道口径**；`max(世界步进, 局部转角)`
# 才是物理量。本支上臂走 100.6° 的两段大圆（每段 50.3°），仍会累积
# holonomy 扭转，故沿用同一套双主键 roll 搜索。
ROLL_SWEEP_DEG = _env_f("C04_ROLLSWEEP", 60.0)
ROLL_SWEEP_COARSE = _env_f("C04_ROLLCOARSE", 5.0)
ROLL_SWEEP_FINE = _env_f("C04_ROLLFINE", 1.0)
ROLL_SWEEP_ENGAGE = _env_f("C04_ROLLGATE", 6.0)
CARRY_MODE = os.environ.get("C04_CARRY", "bounded")


def _world_step_deg(prev_q, quat):
    if prev_q is None:
        return 0.0
    return math.degrees(prev_q.rotation_difference(quat).angle)


def _roll_goal(prev_q, want):
    y_prev = (prev_q @ Vector((0.0, 1.0, 0.0))).normalized()
    return y_prev.rotation_difference(want) @ prev_q


def _local_step_deg(prev_e, e):
    """两帧 `rotation_euler`（度）之间的**骨自身局部旋转**真实转角（度）。

    `no_teleport` 逐分量口径的正确版本（C02 第 2 件，已逐位复核）。
    """
    if prev_e is None or e is None:
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
        q = prev_q
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


def aim_bone_ref(arm, name, direction, ref_basis, ref_dir):
    """把骨指向 `direction`，**滚转沿用参考姿态**（= `JS.aim_frame` 的定点版）。

    与"最小旋转"版的差别：这里基准是**给死的一整套 3×3**，不是靠当前姿态
    反推 ⟹ 方向相同时结果**逐位等于基准**，这是抓握保持段 f31→f32
    台阶为 0 的构造性来源（文件头第 3 件）。
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


def arm_seat(arm, pose, side, target, elbow_dir, ref=None):
    """**三骨链逆解**：把 `hand.tail` 精确落到世界 `target`（文件头第 3 件）。

    与 `leg_seat` 同构，只是链变成 上臂(L1) / [前臂+手](L2+L3) —— 后者成立
    是因为抓取帧的 hand 方向与前臂同向（腕直），见 `ARM_KEYS["HIT"]`。

    为什么不是"冻结姿态"：冻结会让 `hitstop_keeps_momentum_ok`（命停期髋
    必须继续前压）与 `grab_hold_steady_ok`（手不许动）**结构性互斥**。
    位置逆解把"手在哪"从"姿态"里解耦，两个判据同时成立。

    返回 (clamp, distance_mm, limit_mm)；clamp 为 True 表示目标超出臂长被截断
    （此时手会离开抓取点 —— 收招段任何一帧 clamp 都算失败）。
    """
    up = "upperarm." + side
    fo = "forearm." + side
    hd = "hand." + side
    dims = ARM_LEN[side]
    l1 = dims["upper"]
    l23 = dims["forearm"] + dims["hand"]

    shoulder = Vector(A.bone_world(arm, up, "head"))
    target = Vector(target)
    delta = target - shoulder
    limit = (l1 + l23) * 0.9995
    clamp = delta.length > limit
    distance = max(1e-4, min(delta.length, limit))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    bulge = Vector(elbow_dir) - axis * Vector(elbow_dir).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    cos_sh = (l1 * l1 + distance * distance - l23 * l23) / (2.0 * l1 * distance)
    cos_sh = max(-1.0, min(1.0, cos_sh))
    sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
    elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * l1

    for name, direction in ((up, elbow - shoulder),
                            (fo, target - elbow),
                            (hd, target - elbow)):
        if ref is not None and name in ref:
            basis, rdir = ref[name]
        else:
            basis, rdir = IDLE_BASIS[name], IDLE_DIR[name]
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            aim_bone_ref(arm, name, direction, basis, rdir))
    return clamp, delta.length * 1000.0, limit * 1000.0


def leg_seat(arm, pose, side, target, knee_dir, ref=None):
    """两骨逆解：踝**精确**落在 `target`，膝按给定的 `knee_dir` 方向鼓出。

    `ref`（可选）给出 `{骨名: (基准 3×3, 基准方向)}`；缺省用 Idle 的基准。
    ★ C03 第 4 件的实测结论：**「落地前把基准收满到 Idle、落地后恒定」是
      支点漂移最小的配置（0.0249 mm）**，而"沿用落地帧基准"会漂到 22.757 mm。
      本支因此**恒定用 Idle 基准**（`ref=None`），不做收敛混合。
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
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            aim_bone_ref(arm, name, direction, basis, rdir))


def _fingers(frame):
    """手指开合（文件头第 4 件）：f0 握拳 → ANTIC 张开 → HIT 合拢 → 保持。"""
    if frame <= ANTIC:
        k = 1.0 - frame / float(ANTIC)
    elif frame <= HIT:
        k = (frame - ANTIC) / float(HIT - ANTIC)
    else:
        k = 1.0
    k = max(0.0, min(1.0, k))
    return {name: (value[0] * k, 0.0, 0.0)
            for name, value in A.FIST.items()}


def _arm_section(arm, pose, frame):
    """手臂段：抓握保持用位置逆解，其余用方向链。"""
    if frame > HOLD_END and GRAB_POINT:
        for side in SIDES:
            info = ARM_SEAT_CLAMP.setdefault(
                side, {"any": False, "worst_frame": None,
                       "worst_over_mm": 0.0, "worst_dist_mm": 0.0,
                       "limit_mm": 0.0, "n_frames": 0})
            clamp, dist_mm, limit_mm = arm_seat(
                arm, pose, side, GRAB_POINT[side], GRAB_ELBOW[side],
                ref=ARM_REF)
            info["limit_mm"] = round(limit_mm, 3)
            info["n_frames"] += 1
            if clamp:
                info["any"] = True
                over = dist_mm - limit_mm
                if over > info["worst_over_mm"]:
                    info["worst_frame"] = frame
                    info["worst_over_mm"] = round(over, 3)
                    info["worst_dist_mm"] = round(dist_mm, 3)
        return
    dirs = arm_dirs(frame)
    for bone in ARM_BONES:
        pose[bone] = aim_carry_bounded(arm, bone, dirs[bone])
    if frame == HIT:
        # 把 HIT 帧全部旋转通道原样存下，命停帧**逐位复制**（"完全冻结"的
        # 字面实现；`aim_carry` 在 d_w ≤ 6° 分支上沿用上一帧四元数，
        # 浮点上不是严格不动点 —— C03 第 3 轮实测 f32→f33 还漂 6.62e-5°）。
        _HIT_FROZEN.clear()
        for key in HITSTOP_BONES:
            if key in pose:
                _HIT_FROZEN[key] = tuple(pose[key])


def build_pose(arm, frame, shift):
    """构造并写入第 frame 帧姿态（一次姿态，不含贴地闭环）。"""
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)

    targets = ankle_targets(frame, shift)
    if frame == LEG_TAIL_START:
        _LEG_ANCHOR.update({b: pose[b] for b in LEG_TAIL_BONES if b in pose})
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
            _KNEE_ANCHOR[side] = (knee - hip).normalized()
        for side in SIDES:
            x, y, z, _tip = targets[side]
            RS.leg_to(arm, pose, side, (x, y, z))
    elif frame > LEG_TAIL_START:
        for side in SIDES:
            x, y, z, _tip = targets[side]
            leg_seat(arm, pose, side, (x, y, z), IDLE_KNEE_DIR[side])
    else:
        for side in SIDES:
            x, y, z, _tip = targets[side]
            RS.leg_to(arm, pose, side, (x, y, z))

    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        WF.add_world_rx(arm, name, targets[side][3])
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    _arm_section(arm, pose, frame)

    if _HIT_FROZEN and _hold(frame):
        for name, value in _HIT_FROZEN.items():
            pose[name] = tuple(value)
            arm.pose.bones[name].rotation_euler = [math.radians(v) for v in value]
        bpy.context.view_layer.update()

    if frame == HOLD_END:
        # ★ 抓握成立帧：就地登记**抓取点**（文件头第 3 件）与滚转基准 ——
        #   必须在这里（而不是预先标定），因为抓取点 = "手臂真的够到哪"，
        #   而基准必须取自**本段真实走出来的那一支滚转**，否则 f31→f32 跳。
        for side in SIDES:
            GRAB_POINT[side] = A.bone_world(arm, "hand." + side, "tail").copy()
            GRAB_SHOULDER[side] = A.bone_world(
                arm, "upperarm." + side, "head").copy()
            sh = Vector(GRAB_SHOULDER[side])
            el = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
            GRAB_ELBOW[side] = (el - sh).normalized()
        ARM_REF.clear()
        for bone in ARM_BONES:
            ARM_REF[bone] = (arm.pose.bones[bone].matrix.to_3x3().copy(),
                             A.bone_direction(arm, bone))

    pose.update(_fingers(frame))

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


def solve_pose(arm, frame, meshes=None):
    """**逐帧实测贴地闭环**（本支同样不冻结 shift）。"""
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
        for side in SIDES:
            row["hand_" + side + "_tail"] = tuple(
                A.bone_world(arm, "hand." + side, "tail"))
            row["shoulder_" + side] = tuple(
                A.bone_world(arm, "upperarm." + side, "head"))
            row["armreach_" + side] = (
                Vector(row["hand_" + side + "_tail"])
                - Vector(row["shoulder_" + side])).length
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
def grab_assertions(arm, action, samples, foots, start_mats, tracks):
    res = {}
    pelvis = [Vector(f["pelvis"]) for f in foots]
    pz = [p.z * 1000.0 for p in pelvis]

    # ---- 0) 上游接缝
    mats0 = RS.action_world_matrices(arm, action, 0)
    delta0 = RS.matrix_delta(mats0, start_mats)
    res["seam_source"] = [H.NAME, H.CANCEL]
    res["seam_start_delta"] = float("%.3e" % delta0)
    res["seam_start_ok"] = delta0 <= SEAM_TOL
    res["root_motion_m"] = round(pelvis[-1].y - pelvis[0].y, 6)
    res["root_motion_ok"] = abs(abs(res["root_motion_m"]) * 1000.0
                                - D_TOTAL_MM) <= 1.0
    res["advance_total_mm"] = round((pelvis[-1].y - pelvis[0].y) * 1000.0, 3)

    # ---- 1) ★ 抓取点（本支的核心交付物）
    points = {s: [round(v, 6) for v in GRAB_POINT[s]] for s in SIDES}
    res["grabbed_points_m"] = points
    res["grab_frame"] = HIT
    res["grab_hold_frame"] = HOLD_END
    res["grab_points_ok"] = all(
        len(points[s]) == 3 and any(abs(v) > 1e-9 for v in points[s])
        for s in SIDES)
    pelvis_hold = Vector(foots[HOLD_END]["pelvis"])
    res["grabbed_points_rel_pelvis_mm"] = {
        s: [round((v - pelvis_hold[i]) * 1000.0, 2) for i, v in
            enumerate(GRAB_POINT[s])] for s in SIDES}
    res["grab_gap_mm"] = round(
        (Vector(GRAB_POINT["L"]) - Vector(GRAB_POINT["R"])).length * 1000.0, 2)
    res["grab_z_mm"] = round(
        (GRAB_POINT["L"].z + GRAB_POINT["R"].z) * 0.5 * 1000.0, 2)
    res["grab_depth_mm"] = round(
        ((GRAB_POINT["L"].y + GRAB_POINT["R"].y) * 0.5 - pelvis_hold.y) * 1000.0,
        2)

    # ---- 2) ★ 抓取帧的可达比（= 双手到肩距 / 臂长）
    ratio = {}
    for side in SIDES:
        total = ARM_LEN[side]["upper"] + ARM_LEN[side]["forearm"] \
            + ARM_LEN[side]["hand"]
        ratio[side] = round(float(foots[HOLD_END]["armreach_" + side]) / total, 5)
    res["grab_reach_ratio"] = ratio
    res["grab_reach_ratio_hit"] = {
        side: round(float(foots[HIT]["armreach_" + side])
                    / (ARM_LEN[side]["upper"] + ARM_LEN[side]["forearm"]
                       + ARM_LEN[side]["hand"]), 5) for side in SIDES}
    res["grab_reach_ok"] = all(v <= GRAB_REACH_MAX_RATIO
                               for v in ratio.values())
    res["arm_seat_clamped"] = {s: bool(v.get("any"))
                               for s, v in ARM_SEAT_CLAMP.items()}
    res["arm_seat_detail"] = {s: dict(v) for s, v in ARM_SEAT_CLAMP.items()}
    res["arm_seat_ok"] = not any(v.get("any")
                                for v in ARM_SEAT_CLAMP.values())

    # ---- 3) ★ 抓住之后手不许再滑（本支核心，同 `stance_pivot_ok` 口径）
    drift = {}
    worst_at = {}
    for side in SIDES:
        ref = Vector(GRAB_POINT[side])
        vals = [(Vector(foots[f]["hand_" + side + "_tail"]) - ref).length
                for f in range(HOLD_END, TOTAL + 1)]
        drift[side] = round(max(vals) * 1000.0, 5)
        worst_at[side] = HOLD_END + int(
            vals.index(max(vals)))
    res["grab_hold_drift_mm"] = drift
    res["grab_hold_drift_at"] = worst_at
    res["grab_hold_drift_max_mm"] = round(max(drift.values()), 5)
    res["grab_hold_steady_ok"] = max(drift.values()) <= GRAB_HOLD_DRIFT_MAX_MM

    # ---- 4) ★ 末帧锚点可复现（下游 C05 未生产时的诚实替代，文件头第 5 件）
    mats_r = RS.action_world_matrices(arm, action, TOTAL)
    A.apply_pose(arm, END_POSE)
    bpy.context.view_layer.update()
    mats_a = {b.name: tuple(v for row in b.matrix for v in row)
              for b in arm.pose.bones}
    anchor = RS.matrix_delta(mats_r, mats_a)
    res["end_anchor_delta"] = float("%.3e" % anchor)
    res["end_anchor_ok"] = anchor <= END_ANCHOR_TOL
    res["end_pose_note"] = ("下游 C05 `Grab_Hold` 尚未生产 ⟹ 以"
                            "「末帧姿态可逐位复现」代替 seam_end 比对；"
                            "末帧双手世界坐标见 grabbed_points_m。")

    # ---- 5) 支撑脚：标定支点顶点漂移 + 鞋底区间
    pivot = {}
    sole = {}
    for side in SIDES:
        for idx, (a, b) in enumerate(WINDOWS[side]):
            pts = [tracks[(side, idx)][f] for f in range(max(a, 0), b + 1)
                   if tracks[(side, idx)][f] is not None]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            drift_p = math.hypot(max(xs) - min(xs), max(ys) - min(ys)) * 1000.0
            zs = [foots[f]["sole_" + side] for f in range(max(a, 0), b + 1)
                  if foots[f]["sole_" + side] is not None]
            pivot["%s_w%d_mm" % (side, idx)] = round(drift_p, 4)
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
    res["air_sole_min_mm"] = (None if not air else round(min(air) * 1000.0, 3))
    res["swing_airborne_ok"] = bool(air) and res["air_sole_min_mm"] > 0.0

    # ---- 6) 躯干是否转正（双手抓的力学前提）
    res["pelvis_ry_seam_deg"] = round(SEAM_EULER["pelvis"][1], 3)
    res["pelvis_ry_at_grab_deg"] = round(
        SEAM_POSE.get("pelvis", (0, 0, 0))[0] * 0.0
        + float(samples[HIT]["euler"].get("pelvis", (0, 0, 0))[1]), 3)
    res["torso_square_ok"] = abs(res["pelvis_ry_at_grab_deg"]) <= 1.0

    # ---- 7) 顿感
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
    res["hitstop_rise_mm"] = round(pz[HOLD_END] - pz[HIT], 3)
    res["hitstop_keeps_momentum_ok"] = bool(
        res["hitstop_momentum_mm"] > 10.0 or res["hitstop_rise_mm"] > 10.0)

    # ---- 8) 力矩链（脚→腿→髋→腰→肩→手 逐级都要有非零关键帧）
    keys = ("pelvis", "spine_01", "spine_02", "chest", "shoulder.L",
            "shoulder.R", "thigh.L", "shin.L", "thigh.R", "shin.R")
    channel = {}
    for name in keys:
        vals = [s["euler"].get(name, (0.0, 0.0, 0.0)) for s in samples]
        channel[name] = round(max(max(abs(v) for v in item) for item in vals), 3)
    res["power_chain_channels_deg"] = channel
    res["power_chain_ok"] = all(v > 0.5 for v in channel.values())

    # ---- 9) 腿可达
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

    # ---- 10) 收招不许瞬停 / 不许有死帧
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
    res["return_tail_head"] = tails[:8]

    # ---- 11) 物理口径的"瞬移"（登记项）
    worst_local = 0.0
    worst_local_at = None
    for index in range(1, len(samples)):
        ea = samples[index - 1]["euler"]
        eb = samples[index]["euler"]
        for name in set(ea) | set(eb):
            here = _local_step_deg(ea.get(name, (0.0, 0.0, 0.0)),
                                   eb.get(name, (0.0, 0.0, 0.0)))
            if here > worst_local:
                worst_local, worst_local_at = here, (samples[index]["frame"],
                                                     name)
    res["local_step_max_deg"] = round(worst_local, 3)
    res["local_step_max_at"] = (None if worst_local_at is None
                                else [worst_local_at[0], worst_local_at[1]])

    # ---- 12) 帧预算
    res["antic_frames"] = ANTIC
    res["antic_frames_ok"] = 12 <= ANTIC <= 20
    res["hitstop_frames"] = HOLD
    res["hitstop_frames_ok"] = 2 <= HOLD <= 4
    res["grab_window"] = [ANTIC, HIT]
    return res


# =============================================================== 标定工具
def measure_pivot(arm, side, ankle_xy, z_probe, torso):
    """量「鞋底前缘滚动支点」与「平放踝高」（C02 第 1 件的三点支点模型）。"""
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
    global R_OFF_ANK, D_KEYS, END_POSE

    FROZEN_SHIFT.clear()
    WINDOW_SOLE.clear()
    AIR_SOLE.clear()
    ALL_SOLE.clear()
    PIVOT.clear()
    PIVOT_VERT.clear()
    FLAT_ANK.clear()
    PIVOT_AXIS.clear()
    PIVOT_SCALE.clear()
    GRAB_POINT.clear()
    GRAB_SHOULDER.clear()
    GRAB_ELBOW.clear()
    ARM_REF.clear()
    ARM_SEAT_CLAMP.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    for module, label in ((I1, "Idle_01"), (H, "Heavy_01")):
        if module.NAME not in bpy.data.actions:
            print("C04_BOOTSTRAP 动画工程缺 %s，先补跑" % label)
            module.main()
            arm, meshes = A.open_animation_project()
            A.setup_scene()

    # 骨长实测（`arm_seat` 的 L1 / L2+L3 用它；不准就等于手落不到抓取点）
    for side in SIDES:
        ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
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

    # ---- 下游：C05 未生产 ⟹ 只取 Idle 的**站架与骨基座**当基座（不是接缝）
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
    for name in ARM_BONES:
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

    # ---- 落脚点由**终点反推**（末帧 = Idle 站架整体平移 shift_y）
    shift_y = (PY0 - D_TOTAL_MM / 1000.0) - IDLE_PELVIS.y
    L_END = Vector((idle_l.x, idle_l.y + shift_y, idle_l.z))
    R_END = Vector((idle_r.x, idle_r.y + shift_y, idle_r.z))

    A.report("C04_LAYOUT", {
        "total_frames": TOTAL,
        "antic": ANTIC, "mid": MIDF, "hit": HIT, "hold": HOLD,
        "hold_end": HOLD_END, "return_start": RETURN_START, "cancel": CANCEL,
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
        "note": ("上游接缝 = Heavy_01 的 CANCEL 帧；末帧 = 抓握保持姿"
                 "（两脚取 Idle 站架整体平移，便于 C05 起手）；"
                 "两次落脚全部压在前摇段内。"),
    })

    # ---- 支点 + 平放踝高标定
    calib = {}
    torso_seam = {"pelvis": (RS.track(PELVIS_RX, 0), 0.0, 0.0),
                  "@loc": {"pelvis": A.wloc(0.0, 0.0, Z_SEAM - 0.900)}}
    torso_end = {"pelvis": (RS.track(PELVIS_RX, TOTAL), 0.0, 0.0),
                 "@loc": {"pelvis": A.wloc(0.0, (PY0 - D_TOTAL_MM / 1000.0),
                                           RS.track(PELVIS_Z, TOTAL) - 0.900)}}
    _axis_world = (arm.matrix_world.to_3x3()
                   @ Vector((1.0, 0.0, 0.0))).normalized()
    _axis_dev_deg = math.degrees(_axis_world.angle(Vector((1.0, 0.0, 0.0))))
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
    A.report("C04_CALIBRATION", {
        "per_window": calib,
        "pivot_axis_world": [round(v, 6) for v in _axis_world],
        "pivot_axis_dev_deg": round(_axis_dev_deg, 4),
        "pivot_scale": _PIVOT_K_DEFAULT,
        "arm_len_mm": {s: {k: round(v * 1000.0, 3) for k, v in d.items()}
                       for s, d in ARM_LEN.items()},
        "note": ("本支 tip ≈ 0 ⟹ `_pivot_ankle` 退化为恒等、踝目标完全由 "
                 "FLAT_ANK 决定；三点支点模型保留以便下一支直接复用。"),
    })

    R_OFF_ANK = _pivot_ankle(("R", 0), tip_of("R", T_R_OFF))

    def reset_carry():
        JS._PREV_EULER.clear()
        JS.ARM_QUAT.clear()
        JS.ARM_ROLL.clear()
        JS.ROLL_MAX.clear()
        _TAIL_ANCHOR.clear()
        _LEG_ANCHOR.clear()
        _KNEE_ANCHOR.clear()
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
    END_POSE = keyframes[-1][1]

    reach_ratio = {}
    for side in SIDES:
        total = (ARM_LEN[side]["upper"] + ARM_LEN[side]["forearm"]
                 + ARM_LEN[side]["hand"])
        reach_ratio[side] = round(
            float((Vector(GRAB_POINT[side]) - Vector(GRAB_SHOULDER[side]))
                  .length) / total, 5)

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "连招与特殊技",
        "note": ("抓取：接 Heavy_01 可取消帧；双手回收张开 → 跨步突进 → 双手自"
                 "身侧外抡到身前抓取点、手指合拢 → 命中 4 帧抓取停顿（髋继续"
                 "前压 12 mm）→ 抓握保持（双手位置逆解钉死在世界抓取点）。"
                 "Root Motion 前冲 0.450 m。下游 C05 `Grab_Hold` 直接引用 "
                 "grabbed_points_m。"),
        "antic_frame": ANTIC,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HOLD,
        "root_motion_m": [0.0, round(-D_TOTAL_MM / 1000.0, 4)],
        "grab_frame": HIT,
        "grab_hold_frame": HOLD_END,
        "grabbed_points_m": {s: [round(v, 6) for v in GRAB_POINT[s]]
                             for s in SIDES},
        "grabbed_point_L_m": [round(v, 6) for v in GRAB_POINT["L"]],
        "grabbed_point_R_m": [round(v, 6) for v in GRAB_POINT["R"]],
        "grab_reach_ratio": reach_ratio,
        "grab_hold_drift_max_mm": GRAB_HOLD_DRIFT_MAX_MM,
        "hit_point_m": None,
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "ANTIC": ANTIC, "BURST": ANTIC, "GRAB": HIT,
        "GRAB_HOLD": HOLD_END, "RECOV": RETURN_START, "CANCEL": CANCEL,
        "R_OFF": T_R_OFF, "R_ON": T_R_ON, "L_OFF": T_L_OFF, "L_ON": T_L_ON,
        "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    if os.environ.get("C04_TRACE") == "1":
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for f in foot_series(arm, action, meshes):
            print("C04_TRACE " + json.dumps({
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
                "handL": [round(v * 1000.0, 2) for v in f["hand_L_tail"]],
                "handR": [round(v * 1000.0, 2) for v in f["hand_R_tail"]],
                "armL_r": round(f["armreach_L"] * 1000.0, 2),
                "armR_r": round(f["armreach_R"] * 1000.0, 2),
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
    report.update(grab_assertions(arm, action, samples, foots,
                                  start_mats, tracks))
    report["sole_low_frames"] = {
        str(f): v for f, v in sorted(ALL_SOLE.items())
        if min([x for x in v.values() if x is not None] or [0.0]) < -2.0}
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
    A.report("C04_REPORT", report)

    if not SKIP_RENDER:
        # 取景跟着 Root Motion 平移（B10 教训：不跟就会把角色走出画面）。
        cam_dy = -0.55 * D_TOTAL_MM / 1000.0
        sheets = [(A.VIEW_SIDE, cam_dy, 2.40), (A.VIEW_FRONT, cam_dy, 2.40),
                  (A.VIEW_3Q, cam_dy, 2.40)]
        for base, shift_y_v, scale in sheets:
            name, location, target, _scale, res_v = base
            view = (name, (location[0], location[1] + shift_y_v, 0.90),
                    (target[0], target[1] + shift_y_v, 0.90), scale, res_v)
            frames = ([0, T_R_ON, ANTIC, MIDF, HIT, HOLD_END, TOTAL]
                      if name == "side"
                      else [0, ANTIC, MIDF, HIT, HOLD_END, TOTAL])
            A.render_pose_sheet(arm, action, frames, "grab04", views=(view,))
    A.save_project()
    A.export_glb(arm)
    print("C04_DONE failed=%s" % report["failed"])
    print("C04_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C04_FAILURE " + traceback.format_exc())
