"""anim_jump_land —— A13 `Jump_Land` 落地。

设计（对着清单「下一支计划 —— A13」逐条落）：
    定位      双腿屈膝吸收冲击，上身下沉后恢复；重落地可增加地面震动（清单原文 A13）。
              **本族唯一有真实地面反力的一支**（A10 蹬地、A11/A12 全在空中）。
    接 A12    首帧**逐位**等于 `Jump_Fall@24`（世界矩阵 max_delta = 0）。
    时长      30 帧 / 0.500 s @60fps，**非循环**（`loop=False`）。
    末帧      逐位等于 `Idle_01@0`（同 A06/A07/A08/A10 的口径）—— Jump 族收尾。

---------------------------------------------------------------------------
★ 本支第 0 件事：清单把「触地 / 屈膝到最深 / 命中停顿」三件事全塞进 4 帧，
  这三件事在时间上**互相排斥** —— 现按物理重排，并说明为什么。

计划原文写：「`IMPACT` 4~8：触地；膝快速屈到最深（骨盆下沉 200~240 mm）；
命中停顿 2~4 帧（姿态完全冻结在触地帧）」。同时专属门禁要求
`hitstop_present`（2~4 帧角度增量恒 0）与 `absorb_depth_ok`（从触地帧起再沉 ≥180 mm）。

矛盾：4 帧窗口里既要做完 200 mm 的屈膝行程，又要冻结 2~4 帧，二者不共存 ——
若先冻结再压缩，压缩只剩 0~2 帧（≈100 mm/帧），膝单帧要转 25° 以上，
`no_teleport`（≤25°）必红；若先压缩再冻结，`IMPACT` 就不是 4 帧能装下的。

**重排（按物理，不按表格）**：命中停顿是**时间冻结**，它必须冻结一切连续量，
所以把整支动画的驱动量改到一根「动作时钟」上：

    clock(f) = f                      (f ≤ 触地帧 4)
    clock(f) = f − 2                  (f > 4)          ← 命中停顿吃掉 2 帧
    帧 4/5/6 三帧共用**同一份姿态对象** ⟹ 角度增量**恒等于 0**（不是"约等于"）

于是每段仍各自成形，而命中停顿不制造任何追赶（冻结后手臂不会"一帧补 3 帧"，
这正是 A11 `no_teleport` 的教学：roll 搜索自己把扭转变造出来过一次）。

| 段 | 帧（动作时钟） | 内容 |
|---|---|---|
| `FALL_IN` | 0~4 (0~4) | 承接 A12 弹道（同一解析弹道 `t = 52 + clock`）；双腿保持伸展、双脚从"略前伸 30 mm"**收回站姿**（触地必须落在 A01 站距上，否则末帧无法逐位等于 Idle_01@0）；脚掌由勾 −6° 转平；**帧 4 鞋底到 0（触地）** |
| `HITSTOP` | 4~6 | **命中停顿 3 帧**：帧 4/5/6 姿态完全冻结（共用同一姿态对象 + `set_hitstop` 设 CONSTANT 插值）—— 地面撞上双脚的顿感 |
| `ABSORB` | 6~12 | 屈膝吸收（动作时钟 4→12，8 步）：骨盆 851.6 → 626.0 mm（**再沉 225.6 mm**），膝弯 ~35° → ~91°；上身被惯性压折（胸链累计前倾 9° → 31°）；**脚钉死** |
| `RISE` | 12~20 | 骨盆单调回升到 715 mm；膝盖伸展；上身抬起 |
| `RECOVER` | 20~30 | 收进 `Idle_01@0`；末 6 帧角度增量单调收敛（`TURN.track` 末段切线置 0） |

---------------------------------------------------------------------------
本支的关键做法（每条都有上游实测依据）

1. **触地帧必须落在 A01 站距上，而 A12 末帧的踝是"略前伸 30 mm"的。**
   清单计划给的交接真值：A12 末帧踝 L (143.2, −199.6, 357.5) / R (−141.6, 110.4, 371.5) mm
   —— y 比 A01 站姿（L −170 / R +140）**各前伸 30 mm**（`JF.FORWARD_REACH`）。
   而 `end_matches_idle_ok` 要求末帧**逐位**等于 `Idle_01@0`、`feet_pinned_ok` 要求
   触地后踝行程 ≤3 mm。两条一起 ⟹ **脚不可能既钉在"前伸 30 mm"处、又回到站姿**。
   → 唯一自洽解：那 30 mm 的回收放在**空中那 4 帧**（`FALL_IN` 还在飞，踝本来就在动），
     触地瞬间就落在站姿踝位上，此后全程钉死。视觉上反而更对：下落时脚在身前探地，
     落地瞬间收进身体正下方承重。

2. **"腿长可达性"是交接段的硬约束（沿用 A12 的 `reach_series`）。**
   A12 末帧 |髋−踝| = L 808.8 mm、上限 822 mm，只剩 13.2 mm。触地段若还想"再伸"就
   静默截断。本支让竖距 782 → 773.6 mm（**收短** 8.4 mm，因为踝降到站姿高度时可用的
   竖距更少），|髋−踝| 反降到 ~794 mm ⟹ 余量 28 mm。这就是清单里
   「触地那 4 帧**必须先屈膝腾空间**，不能再伸」的量化版本。

3. **末帧不重算，直接取 `I1.idle_pose(arm, 0.0)` 的成品姿态。**
   A06/A07/A08/A10 都是这么做的 —— 姿态由同一函数、同一组参数生成 ⟹ 世界矩阵逐位相同。
   只有当末帧欧拉**表示**离前一帧太远（>8°）时才做等价族折算（`_unwrap_xyz`）：
   折算只改表示、不改世界朝向，`end_matches_idle_ok` 仍逐位成立。

4. **贴地常数重扫，但本支与 A08/A10 不同：末帧锚在站姿踝 ⟹ 常数只能"扫完再回零"。**
   A08/A10 的冻结常数全程恒定（它们的末帧不要求等于某支动画的某一帧）。
   本支若全程恒定 +c，末帧踝就偏 c ⟹ `end_matches_idle_ok` 红。
   → 扫 `ABSORB` 段解 c（`-1 mm − 段内鞋底最低`，±3 mm 截断，理由同 A08/A09），
     在 `RISE` 段把 c **线性回零**（12 步摊完，踝行程 = |c| ≤ 3 mm，
     仍在 `feet_pinned_ok` 的 3 mm 内）。最深点承受全部修正，站立姿态不需要修正。

5. **力量传导链换回 A10 的蹬地尺子**（清单明确要求）。
   A11/A12 在空中、没有地面反力，用的是"可见"下限（3°/5 mm）；落地吸收是真蹬地量级，
   `thigh` 摆幅实测 ~40°、`shin` ~56°，A10 的 ≥15° 尺子正好。
   本支的"脚段"按**吸收前的下落行程**判（触地后踝钉死，脚段的行程全在 `FALL_IN`）——
   这正是"脚先着地"的物理。

6. **★ 手臂收势：世界空间的"最短旋转"在这里是错的路 —— 四跑定案。**
   完整证据链与结论写在 `arm_blend` 上方（那是代码里唯一需要读注释的地方）。
   一句话版：
   - ① `aim_carry`（只钉方向、扭转自由）⟹ 末帧手臂真世界旋转跳 51~174°；
   - ② 世界空间朝向 slerp（端点逐位对）⟹ `no_teleport` 29.893° @ f18：
     `upperarm.R` 是 swing 30.7° + **twist 173.9°**，测地线把欧拉中间角 |Y| 顶到
     74.1°，`1/cos(Y)=3.6×` 把 8.2°/帧放大成 29.9°/帧；
   - ③ 只动 roll 把 |Y| 软饱和 ⟹ 逐帧反馈在欧拉分支上不稳（|Y| 只降到 60、步长 126°），**弃**；
   - ④ **逐分量插欧拉**（端点先折到同一等价族）⟹ 峰值步长有解析上界
     （≤ 各分量最大差 × 1.136 / 帧数 = 8.2°），实测 `no_teleport` 22.58°。

   同时把**躯干八骨的末键**也从 `Idle_01@0` 读（`IDLE_RX`）、骨盆站姿高 `Z_IDLE`
   也从成品量 —— 凡有成品可读的终值，一律不手抄。手抄一个"接近"的数，
   就是给末帧留一次几度的跳变。

   附带一条**诊断本身的教训**：`real_world_step_deg` 一度报 61~178° 的假跳变，
   原因是手臂欧拉只写进了 pose 字典、没回写骨骼，快照读到的是"手臂归零"的活状态
   （关键帧用字典 ⟹ 门禁全绿）。现在手臂是 `clock` 的**纯函数**、并入 `apply_pose`
   一次写入；另加 `last_step_move_mm`（**从动画本身量**拳的世界位移，5.8 mm）——
   诊断读数可以错，门禁不行，所以关键量必须有一条**不经过中间态**的判据。

7. **回升段必须是一条 C¹ 曲线，不能用几个分段键拼。**
   第一次跑 `decel_smooth_ok` 红：末 6 帧角度增量 `2.576 → 2.012 → 2.328` 非单调。
   病根是旧写法把回升写成 `(24,0.808) (26,0.820) (28,0.830)` 三个键、末键切线置 0 ——
   Hermite 在 c=26 处的切线由左右邻点定出 ~5.5 mm/帧，于是**速率在 c=25→27 先升后降**。
   收招的"减速"必须是**整条曲线**的性质。改用单条 Hermite：起点斜率接住吸收段末速
   （C¹，不产生速度台阶）、终点斜率 0（站定），末 6 帧速率单调递减是构造保证。

8. **`decel_smooth_ok` 本支**适用**（与 A11/A12 相反）。**
   A11/A12 是弹道段，末段在加速/减速，该判据与"匀加速"互斥 ⟹ 显式跳过。
   本支末段是"从蹲起到站直"的收招 —— 正是 A06 踩坑 4 写这条判据的场景 ⟹ 必须真做。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_jump_land.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_walk_f as WF      # noqa: E402
import anim_turn as TURN      # noqa: E402
import anim_crouch as CR      # noqa: E402
import anim_jump_start as JS  # noqa: E402
import anim_jump_up as JU     # noqa: E402
import anim_jump_fall as JF   # noqa: E402

NAME = "Jump_Land"
TOTAL = 30                    # 0.500 s @ 60 fps
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

ARM_BONES = JS.ARM_BONES

# ---------------------------------------------------------------- 阶段划分（帧域）
T_TOUCH = 4                   # 触地帧（鞋底到 0）
T_HOLD_END = 6                # 命中停顿末帧（帧 4/5/6 共用同一姿态）
HOLD = T_HOLD_END - T_TOUCH   # = 2：命中停顿"吃掉"的动作时间
CLOCK_END = TOTAL - HOLD      # = 28：动作时钟的总跨度
T_DEEP_C = 12                 # 吸收最深（动作时钟）
T_RAMP_END_C = 24             # 贴地常数回零完成（动作时钟）
ARM_RAMP_C = 24               # 手臂收到护体架势（动作时钟）

# ---------------------------------------------------------------- 弹道继承
# 从离地（A10 的 TAKEOFF）算起的帧数。**不许硬编码 28 / 24**：上游改长度自动跟随。
BASE_T = JF.BASE_T + JF.TOTAL            # 28 + 24 = 52（= A12 末帧）
G_PER_FRAME = JS.G_PER_FRAME


def ballistic(c):
    """骨盆世界 z（米）—— A10/A11/A12 同一解析弹道在 A13 动作时钟上的续写。"""
    t = BASE_T + c
    return (JS.TAKEOFF_PELVIS_Z + JS.TAKEOFF_SPEED * t
            - 0.5 * G_PER_FRAME * t * t)


def clock(frame):
    """动作时钟：命中停顿期间**时间冻结**，之后所有连续量按冻结后的时间推进。

    这样"冻结 3 帧"不会让任何曲线产生追赶（手臂不会在 f7 一帧补掉 f5/f6 两帧的行程）。
    """
    return frame if frame <= T_TOUCH else frame - HOLD


Z_TOUCH = ballistic(T_TOUCH)             # 0.851556 m
Z_DEEP = 0.626                           # 最深（下沉 225.6 mm）
Z_IDLE = 0.830                           # A01 战斗站姿（末帧）

# 骨盆 z 轨（动作时钟域）。0~4 段直接走解析弹道（见 `pelvis_z`）。
# 4→12：吸收（60/50/40/30/20/12/8/5.6 mm 八步，逐帧**递减** ⟹ "被腿顶住"的读感）。
PZ_KEYS = ((T_TOUCH, 0.851556), (5, 0.791556), (6, 0.741556), (7, 0.701556),
           (8, 0.671556), (9, 0.651556), (10, 0.639556), (11, 0.631556),
           (T_DEEP_C, 0.626000))

# ★ 12→28 的回升段**不能再用分段 Hermite 键**（本支第一次跑就栽在这）：
#   旧写法 (24,0.808) (26,0.820) (28,0.830) 三点，末键切线置 0，
#   于是 c=26 处的切线由左右邻点定出 ~5.5 mm/帧 ⟹ **速率在 c=25→27 处先升后降**，
#   `decel_smooth_ok`（末 6 帧角度增量单调收敛）实测 2.576 → 2.012 → 2.328 直接红。
#   收招段的"减速"必须是**整条曲线**的性质，不是几个孤立的键值。
#   改用单条 Hermite：起点斜率**接住吸收段的末速**（C¹，不产生速度台阶），
#   终点斜率为 0（站定），中段自然加速再收 —— 末 6 帧速率单调递减是构造保证。
RISE_C0 = T_DEEP_C
RISE_C1 = CLOCK_END
Z_RISE0 = PZ_KEYS[-1][1]
# 吸收段末速（米/帧）—— 从最后两个键解，不硬编码。
RISE_V0 = (PZ_KEYS[-1][1] - PZ_KEYS[-2][1]) / float(PZ_KEYS[-1][0] - PZ_KEYS[-2][0])


def pelvis_z(c):
    """骨盆世界 z（米）。0~4 帧是 A12 弹道的直接续写（`fall_ballistic_ok` 的回比对象）。"""
    if c <= T_TOUCH:
        return ballistic(c)
    if c <= RISE_C0:
        return TURN.track(PZ_KEYS, c)
    span = float(RISE_C1 - RISE_C0)
    u = (c - RISE_C0) / span
    # 归一化到 h 的斜率：h'(0) = v0·span / Δz，h'(1) = 0。
    slope0 = RISE_V0 * span / (Z_IDLE - Z_RISE0)
    h = slope0 * (u ** 3 - 2.0 * u ** 2 + u) + (-2.0 * u ** 3 + 3.0 * u ** 2)
    return Z_RISE0 + (Z_IDLE - Z_RISE0) * h


# ---------------------------------------------------------------- 躯干（度）
# f0 取值 = A12 末键（`JF.XXX[-1][1]` 式取法，不硬编码 → 上游改了自动跟随）。
# ★ 末键**不写在这张表里**：bootstrap 时从 `Idle_01@0` 成品姿态**读出来**（`IDLE_RX`）。
#   理由同"首帧读 A12 末键"：手写一个"接近 idle"的数字，看着对、实测差几度，
#   末帧就是一次可见的跳变。本支第一次跑 `upperarm.R` 末帧真旋转跳 173.9°，
#   同一条教训（见文件头第 6 条）——能读的绝不手抄。
TRUNK_KEYS = {
    "pelvis": ((0, JF.PELVIS_RX[-1][1]), (T_TOUCH, 3.2), (T_DEEP_C, 16.0),
               (20, 12.0)),
    "spine_01": ((0, JF.SPINE01_RX[-1][1]), (T_TOUCH, 2.2), (T_DEEP_C, 5.8),
                 (20, 4.4)),
    "spine_02": ((0, JF.SPINE02_RX[-1][1]), (T_TOUCH, 2.2), (T_DEEP_C, 5.6),
                 (20, 4.2)),
    "chest": ((0, JF.CHEST_RX[-1][1]), (T_TOUCH, 3.0), (T_DEEP_C, 3.8),
              (20, 3.0)),
    # 头：落地瞬间被惯性往前压（rx>0 = 前屈/低头），此后抬回战斗视线。
    "neck": ((0, JF.NECK_RX[-1][1]), (T_TOUCH, -3.4), (T_DEEP_C, -7.0),
             (20, -6.6)),
    "head": ((0, JF.HEAD_RX[-1][1]), (T_TOUCH, 8.6), (T_DEEP_C, 13.0),
             (20, 10.0)),
    # 肩：落地时缩起来（−10 → −20.5），复原到 A01 的护体。
    "shoulder.L": ((0, JF.SHOULDER_RX[-1][1]), (T_TOUCH, -10.0),
                   (T_DEEP_C, -20.5), (20, -19.0)),
    "shoulder.R": ((0, JF.SHOULDER_RX[-1][1]), (T_TOUCH, -10.0),
                   (T_DEEP_C, -20.5), (20, -19.0)),
}
IDLE_RX = {}                     # bone -> Idle_01@0 的 rx（度）；bootstrap 时填


def trunk_rx(bone, c):
    """躯干 rx（度）：分段键 + **末键 = Idle_01@0 的实测值**。"""
    return TURN.track(TRUNK_KEYS[bone] + ((CLOCK_END, IDLE_RX[bone]),), c)


# 骨盆水平：原地（清单 §0.4）。y 只做 8 mm 的后坐（重心压在脚上），末帧回 0。
PELVIS_Y_KEYS = ((0, JF.PELVIS_Y_KEYS[-1][1]), (T_DEEP_C, 0.008),
                 (CLOCK_END, 0.0))

# ---------------------------------------------------------------- 足尖（度）
# `world_tip_deg`：**正 = 脚尖朝下（压脚背）**，**负 = 脚尖朝上（勾脚）**。
# A12 末帧 −6°（勾脚准备接触）⟹ 触地前转平（0°），此后全程 0（与 Idle_01@0 一致）。
TIP_KEYS = ((0, JF.TIP_KEYS[-1][1]), (T_TOUCH, 0.0), (CLOCK_END, 0.0))

# ---------------------------------------------------------------- 踝
ANKLE_REST = {}                  # side -> Vector：A01@0 的踝位（触地后的钉死点）
A12_END_ANKLE = {}               # side -> Vector：A12@24 的踝位（交接真值）
PIN_ANKLE = {}                   # side -> Vector：触地后的钉死目标（= ANKLE_REST + zoff）
Z_OFF = {"L": 0.0, "R": 0.0}     # 贴地冻结常数偏移（米），RISE 段回零
TARGETS = []
TRACE = []
IDLE_QUAT = {}                   # bone -> Quaternion：Idle_01@0 的手臂世界**朝向**（收势终点）
START_ARM_QUAT = {}              # bone -> Quaternion：A12@24 的手臂世界**朝向**（收势起点）


def ankle_target(arm, c, side):
    """该侧踝的世界目标位置。

    0~4（空中）：从 A12 末帧的踝位**线性收回到站姿踝位** —— 那 30 mm 的前伸只能
                在空中收，触地后脚就钉死了（见文件头第 1 条）。
    触地后：钉死在 `PIN_ANKLE`；`RISE` 段把贴地常数线性回零（末帧恰好 = 站姿踝位）。
    """
    if c <= T_TOUCH:
        s = JS._ease_ramp(c / float(T_TOUCH))
        a = A12_END_ANKLE[side]
        b = PIN_ANKLE[side]
        return Vector(a) + (Vector(b) - Vector(a)) * s
    if c <= T_RAMP_END_C:
        k = 1.0 - (c - T_DEEP_C) / float(T_RAMP_END_C - T_DEEP_C)
        k = max(0.0, min(1.0, k))
    else:
        k = 0.0
    rest = ANKLE_REST[side]
    return Vector((rest.x, rest.y, rest.z + Z_OFF[side] * k))


def arm_blend(c):
    """手臂收势的插值因子 s：0 = A12 末的**外张**（找平衡），1 = A01 的**护体架势**。

    定时用 `JS._ease_ramp`（梯形速度剖面，两端速度为 0、中段匀速）。两端速度为 0
    是关键：A12 的末段手臂已**定格**，若本支起点带速度，接缝上会出现速度跳变。
    """
    return JS._ease_ramp(min(1.0, c / float(ARM_RAMP_C)))


# ---------------------------------------------------------------- 手臂收势：逐分量插欧拉
# 本支最贵的一课（四跑定案）——**世界空间的"最短旋转"不是这里该走的路**。
#
# 证据链：
#   ① 用 A10/A11/A12 的 `aim_carry`（只钉骨轴方向、扭转自由）：末帧手臂的**真世界旋转**
#      跳 51~174°（`JUMPLAND_LAST_FRAME.real_world_step_deg`）。因为终点
#      `Idle_01@0` 是 **一个确定朝向**，carry 的扭转落在了完全不同的那一支。
#   ② 改用**世界空间朝向 slerp**（端点逐位对上）：`no_teleport` 报
#      **29.893° @ [f18, upperarm.R]**。摇摆/扭转分解显示 `upperarm.R` 是
#      swing 30.7° + **twist 173.9°** —— 方向几乎不动，是一记纯自转 174°。
#      测地线途中把欧拉中间角 |Y| 顶到 **74.1°**，而 XYZ 欧拉在中间角的放大是
#      **1/cos(Y) = 3.6×**：中段 8.2°/帧 的真旋转被放大成 29.9°/帧 的欧拉步。
#      试过"只动绕骨轴的 roll、把 |Y| 软饱和"—— |Y| 只降到 60、步长反而 126°
#      （逐帧反馈在欧拉分支上不稳）。**放弃**。
#
# 结论：**欧拉 XYZ 通道装不下一记 174° 的大扭转**（任何最大化 C¹ 的世界空间路径
# 都会把它挤成一次中间角穿越）。而 f-curve **本来就是逐分量插值的** ——
# 既然被判据量的就是这三个通道，就**直接在这三个通道上插**：
#
#     e(t) = e_A12 + (e_idle − e_A12) · s(t)        # 逐分量
#     e_idle = `_unwrap_xyz(e_A12, idle_raw)`       # 先折到离 e_A12 最近的等价族
#
# 好处直白：**每帧欧拉增量 = 各分量总差 × 剖面速率**，上界可算
# （总差被 `_unwrap_xyz` 压到每分量 ≤180°，速率峰值 = 均值×1.136 ⟹ ≤8.5°/帧）。
# 且端点逐位落在两支成品上 —— `first_frame_matches_a12_ok` / `end_matches_idle_ok`
# 都不是"约等于"。代价是路径不是世界空间测地线，而是**这台骨骼自己的通道路径**；
# 那正是引擎将来回放时走的那条路径，所以"门禁绿"与"看起来对"在这里是同一件事
# （已渲染关键姿态目视核过，见清单制作日志）。
ARM_E0 = {}                      # bone -> A12@24 的手臂欧拉（收势起点，逐位）
ARM_E1 = {}                      # bone -> Idle_01@0 的手臂欧拉（收势终点，已折族）


# =============================================================== 姿态生成
def build_pose(arm, frame, record=False):
    """按帧构造完整姿态（内部一律用 `clock(frame)` 驱动）。"""
    c = clock(frame)
    pose = {
        "pelvis": (trunk_rx("pelvis", c), 0.0, 0.0),
        "spine_01": (trunk_rx("spine_01", c), 0.0, 0.0),
        "spine_02": (trunk_rx("spine_02", c), 0.0, 0.0),
        "chest": (trunk_rx("chest", c), 0.0, 0.0),
        "neck": (trunk_rx("neck", c), 0.0, 0.0),
        "head": (trunk_rx("head", c), 0.0, 0.0),
        "shoulder.L": (trunk_rx("shoulder.L", c), 0.0, 0.0),
        "shoulder.R": (trunk_rx("shoulder.R", c), 0.0, 0.0),
        "toe.L": (0.0, 0.0, 0.0),
        "toe.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, TURN.track(PELVIS_Y_KEYS, c),
                                  pelvis_z(c) - 0.900)},
    }
    # ★ 手臂收势 = **逐分量插欧拉**（起点 A12@24、终点 Idle_01@0，都已折到同一等价族）。
    #   为什么不用世界空间 slerp / carry —— 见紧邻 `arm_blend` 上方的证据链。
    #   注意它现在是 `clock` 的**纯函数**（不读骨骼、不依赖上一帧），所以放在
    #   `apply_pose` **之前**一次写入；这也是它比 carry/aim 优越的一点：
    #   构造上不可能累积反馈误差。（曾经的坑：只写 pose 字典不回写骨骼，快照读到的
    #   是"手臂归零"的活状态；关键帧用字典所以门禁全绿，诊断却报 61~178° 假跳变。）
    s = arm_blend(c)
    for bone in ARM_BONES:
        e0, e1 = ARM_E0[bone], ARM_E1[bone]
        pose[bone] = tuple(e0[i] + (e1[i] - e0[i]) * s for i in range(3))
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    # 腿：真双骨 IK（A06/A07/A10/A11/A12 的 `leg_to`）。膝弯方向固定世界 −Y（不转身）。
    for side in ("L", "R"):
        target = ankle_target(arm, c, side)
        if record:
            TARGETS.append((frame, side, tuple(target)))
        TURN.leg_to(arm, pose, side, target, (0.0, -1.0))
    JU._unwrap_legs(arm, pose)

    # 足：先钉平到世界水平（rest 朝向），再绕世界 X 叠 tip 角（A10/A11/A12 同路径）。
    tip = TURN.track(TIP_KEYS, c)
    for side in ("L", "R"):
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        WF.add_world_rx(arm, name, tip)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    _record_trace(arm, frame, pose)
    return pose


def _angle_between(qa, qb):
    """两个世界朝向之间的**真旋转角**（度，取最短支）。"""
    ang = math.degrees(qa.rotation_difference(qb).angle)
    return min(ang, 360.0 - ang)


def _record_trace(arm, frame, pose):
    """登记一帧（供 `JUMPLAND_TRACE_DETAIL` 区分"表示跳"与"真扭转变"）。

    ★ 末帧也必须进 TRACE —— 本支第一次跑就栽在这：`no_teleport` 报 f30
    `upperarm.R` 175.03°，而 TRACE 只到 f29，看不出那 175° 是"换了个等价欧拉支"
    还是"手臂真的翻了一下"。诊断表缺最后一帧 = 缺最后一格证据。
    """
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    TRACE.append({
        "frame": frame,
        "euler": {b: tuple(round(v, 2) for v in pose[b]) for b in ARM_BONES},
        "quat": {b: arm.pose.bones[b].matrix.to_quaternion() for b in ARM_BONES},
        "roll": dict(JS.ARM_ROLL),
    })


# =============================================================== 末帧（逐位 = Idle_01@0）
def final_idle_pose(arm, prev_euler, threshold=8.0):
    """末帧姿态：直接取 `Idle_01@0` 成品，必要时把欧拉折到离上一帧最近的一支。

    折算只改**表示**（同一旋转的 ±360 / 翻转分支），世界朝向不变 ⟹
    `end_matches_idle_ok`（世界矩阵逐位）仍然成立，而 `no_teleport`（欧拉逐分量）
    不会被"换了支表示"误伤。阈值 8° 之下不动 —— 能不动就不动，减少浮点差。
    """
    raw = I1.idle_pose(arm, 0.0)
    out = dict(raw)
    adjusted = {}
    for name, value in raw.items():
        if name.startswith("@"):
            continue
        previous = prev_euler.get(name)
        if previous is None or len(previous) != 3:
            continue
        before = max(abs(a - b) for a, b in zip(previous, value))
        if before > threshold:
            fixed = JS._unwrap_xyz(previous, value)
            out[name] = fixed
            adjusted[name] = [round(before, 2),
                              round(max(abs(a - b)
                                        for a, b in zip(previous, fixed)), 2)]
    return out, adjusted


# =============================================================== 贴地常数扫描
def calibrate(arm):
    """扫 `ABSORB`/`RISE` 段（触地后的全段）量鞋底 z，解**一个**冻结常数偏移。

    与 A08 同一条思路（整支冻结一个常数），但本支多一步：末帧必须逐位等于
    `Idle_01@0` ⟹ 站在站姿踝高度上，常数**必须回零**（见文件头第 4 条）。
    截断阈值 ±3 mm：本支蹲得比 A08 深（225.6 vs 202 mm），蒙皮形状漂移更大；
    实际用到的偏移会登记在 `z_off_mm`，回零摊在 12 步上（0.25 mm/帧）。
    """
    order = [_clock_order(c) for c in range(T_DEEP_C, CLOCK_END + 1)]
    lows = {"L": [], "R": []}
    for frame in order:
        build_pose(arm, frame)
        low = A.foot_lowest_by_side()
        for side in ("L", "R"):
            lows[side].append(low[side][2])
    out = {}
    for side in ("L", "R"):
        out[side] = max(-0.003, min(0.003, -0.0010 - min(lows[side])))
    return out, lows


def _clock_order(c):
    """动作时钟值 → 一个真实帧号（取该时钟第一次出现的帧）。"""
    return c if c <= T_TOUCH else c + HOLD


# =============================================================== 专属门禁
def land_assertions(arm, action, samples, start_mats, sole, target_err, reach,
                    idle_mats):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(s["pelvis"]) for s in samples]
    zs = [p.z for p in pelvis]
    rates = [(zs[i + 1] - zs[i]) * 1000.0 for i in range(len(zs) - 1)]

    # 0) 首帧必须**逐位**等于 `Jump_Fall@24`（世界矩阵，不是 euler）。
    mats = CR.action_world_matrices(arm, action, 0)
    delta = CR.matrix_delta(mats, start_mats)
    res["first_frame_delta"] = float("%.3e" % delta)
    res["first_frame_matches_a12_ok"] = delta <= 1e-6

    # 1) 末帧必须**逐位**等于 `Idle_01@0`（同 A06/A07/A08/A10）。
    end_mats = CR.action_world_matrices(arm, action, TOTAL)
    end_delta = CR.matrix_delta(end_mats, idle_mats)
    res["last_frame_delta"] = float("%.3e" % end_delta)
    res["end_matches_idle_ok"] = end_delta <= 1e-6

    # 2) **承接段不许自己乱编**：0~4 帧骨盆 z 逐帧与同一解析弹道比对。
    err = max(abs(zs[i] - ballistic(frames[i])) * 1000.0
              for i in range(len(frames)) if frames[i] <= T_TOUCH)
    res["fall_ballistic_max_err_mm"] = round(err, 4)
    res["fall_ballistic_ok"] = err <= 2.0
    res["fall_mm"] = round((zs[0] - zs[T_TOUCH]) * 1000.0, 1)
    res["start_pelvis_z_mm"] = round(zs[0] * 1000.0, 1)
    res["touch_pelvis_z_mm"] = round(zs[T_TOUCH] * 1000.0, 1)

    # 3) **真的"重落地"**：触地帧竖速 ≤ −60 mm/帧（A12 末帧 −65.2 继续加速到 ~−76）。
    touch_rate = rates[T_TOUCH - 1]
    res["impact_rate_mm_per_frame"] = round(touch_rate, 2)
    res["impact_rate_mps"] = round(touch_rate * A.FPS / 1000.0, 3)
    res["impact_speed_ok"] = touch_rate <= -60.0
    # 落地冲击 = 2 × 落速（A05 同口径：触地前脚相对地面 −v、触地后 0 ⟹ 跳变 2v），
    # 写成可复用版，供日后 D 族（受击 / 击倒）直接调用。
    res["landing_impact_mps"] = round(-touch_rate * 2.0 * A.FPS / 1000.0, 3)
    res["landing_impact_ok"] = res["landing_impact_mps"] >= 7.0
    res["landing_impact_formula"] = "impact = 2 × |触地帧竖速|（A05 口径）"

    # 4) **命中停顿**：触地后连续若干帧角度增量恒 0（帧 4/5/6 共用同一姿态对象）。
    steps = 0
    cursor = T_TOUCH
    while cursor + 1 <= T_HOLD_END:
        before, after = samples[cursor]["euler"], samples[cursor + 1]["euler"]
        worst = 0.0
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
        if worst > 1e-9:
            break
        steps += 1
        cursor += 1
    res["hitstop_zero_steps"] = steps
    res["hitstop_frames"] = steps + 1
    res["hitstop_frozen_delta_deg"] = 0.0
    res["hitstop_present"] = 2 <= (steps + 1) <= 4
    res["hitstop_window"] = [T_TOUCH, T_HOLD_END]

    # 5) **屈膝吸收要肉眼可见**：从触地帧起骨盆再下沉 ≥180 mm，且单调。
    deep_index = min(range(len(zs)), key=lambda i: zs[i])
    depth = (zs[T_TOUCH] - zs[deep_index]) * 1000.0
    segment = zs[T_TOUCH:deep_index + 1]
    res["absorb_depth_mm"] = round(depth, 1)
    res["absorb_deep_frame"] = frames[deep_index]
    res["absorb_deep_pelvis_z_mm"] = round(zs[deep_index] * 1000.0, 1)
    res["absorb_depth_ok"] = depth >= 180.0
    res["absorb_monotone_ok"] = all(segment[i + 1] <= segment[i] + 1e-9
                                    for i in range(len(segment) - 1))
    # 回升段单调不降（清单 ABSORB 原文"吸收到底 → 开始回升"）。
    rise = zs[deep_index:]
    res["rise_monotone_ok"] = all(rise[i + 1] >= rise[i] - 1e-9
                                  for i in range(len(rise) - 1))
    res["rise_mm"] = round((zs[-1] - zs[deep_index]) * 1000.0, 1)

    # 6) **膝弯增幅 ≥45°**（A12 刻意没做的那件事），且换回 A10 的 15° 蹬地尺子。
    bend = CR.knee_series(arm, action, frames)
    gain = {s: max(b[s] for b in bend) - bend[T_TOUCH][s] for s in ("L", "R")}
    res["knee_bend_touch_deg"] = {s: round(bend[T_TOUCH][s], 2) for s in ("L", "R")}
    res["knee_bend_peak_deg"] = {s: round(max(b[s] for b in bend), 2)
                                 for s in ("L", "R")}
    res["knee_bend_end_deg"] = {s: round(bend[-1][s], 2) for s in ("L", "R")}
    res["knee_bend_gain_deg"] = {k: round(v, 2) for k, v in gain.items()}
    res["knee_bend_gain_ok"] = all(v >= 45.0 for v in gain.values())

    # 7) **脚钉死**（触地后全段踝世界行程 ≤3 mm）——本支的核心接地判据。
    base = {s: Vector(samples[T_TOUCH]["foot." + s]) for s in ("L", "R")}
    travel = {}
    for side in ("L", "R"):
        pts = [Vector(samples[i]["foot." + side])
               for i in range(T_TOUCH, len(samples))]
        travel[side] = max((p - base[side]).length for p in pts) * 1000.0
    res["feet_pinned_mm"] = {k: round(v, 3) for k, v in travel.items()}
    res["feet_pinned_ok"] = all(v <= 3.0 for v in travel.values())
    res["z_off_mm"] = {k: round(v * 1000.0, 3) for k, v in Z_OFF.items()}
    res["planted_ankle_span_mm"] = {
        s: [round(min(Vector(samples[i]["foot." + s])[k]
                      for i in range(T_TOUCH, len(samples))) * 1000.0, 3)
            for k in range(3)] for s in ("L", "R")}

    # 8) **贴地窗口**：触地后鞋底最低 ∈ [−2, +6]。落地前的 4 帧在空中，不适用。
    parked = [min(sole[i]["L"], sole[i]["R"]) for i in range(T_TOUCH, len(sole))]
    res["sole_min_after_touch_mm"] = round(min(parked) * 1000.0, 2)
    res["sole_max_after_touch_mm"] = round(max(parked) * 1000.0, 2)
    res["ground_contact_ok"] = -2.0 <= min(parked) * 1000.0 <= 6.0
    air = [min(sole[i]["L"], sole[i]["R"]) for i in range(0, T_TOUCH)]
    res["sole_min_before_touch_mm"] = round(min(air) * 1000.0, 1)
    res["airborne_before_touch_ok"] = min(air) * 1000.0 >= 20.0

    # 9) IK 是否到位（腿最长 0.822 m，够不到会静默截断）。
    res["ankle_target_error_mm"] = round(target_err * 1000.0, 3)
    res["ik_reach_ok"] = target_err * 1000.0 <= 5.0
    limit = A.L_THIGH + A.L_SHIN
    res["leg_reach_limit_mm"] = round(limit * 1000.0, 1)
    res["leg_reach_max_mm"] = {s: round(max(r[s] for r in reach) * 1000.0, 1)
                               for s in ("L", "R")}
    res["leg_reach_min_headroom_mm"] = {
        s: round((limit - max(r[s] for r in reach)) * 1000.0, 1)
        for s in ("L", "R")}
    res["leg_reach_ok"] = all(limit - max(r[s] for r in reach) >= 0.0
                              for s in ("L", "R"))

    # 10) 原地：骨盆水平行程（清单 §0.4「防自带位移」）。
    hspan = max(math.hypot(p.x - pelvis[0].x, p.y - pelvis[0].y)
                for p in pelvis) * 1000.0
    hnet = math.hypot(pelvis[-1].x - pelvis[0].x,
                      pelvis[-1].y - pelvis[0].y) * 1000.0
    res["pelvis_span_mm"] = round(hspan, 2)
    res["pelvis_net_mm"] = round(hnet, 3)
    res["pelvis_in_place_ok"] = hspan <= 60.0

    # 11) 收招不许瞬停：末 6 帧角度增量绝对值单调收敛（A06 踩坑 4 的口径）。
    #     ★ A11/A12 是弹道段、这条不适用（显式跳过）；本支末段正是"从蹲起到站直"
    #     的收招 ⟹ 必须真做。
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
    res["decel_smooth_ok"] = all(deltas[i + 1] <= deltas[i] + 1e-9
                                 for i in range(len(deltas) - 1))

    # 12) 力量传导链（脚→腿→髋→腰→肩→手，六段全非零）。
    #     ★ 尺子换回 **A10 的蹬地量级**（thigh / shin ≥15°）—— 清单明确要求；
    #       A11/A12 的"可见"下限（3°/5 mm）是空中没有地面反力时才用的。
    #       本支"脚段"量的是**触地前那 4 帧的下落行程**（触地后踝钉死）⟹ 见下。
    moved, swing, nonzero = {}, {}, {}
    foot_span = {}
    for side in ("L", "R"):
        pts = [Vector(s["foot." + side]) for s in samples]
        foot_span[side] = max((p - pts[0]).length for p in pts) * 1000.0
    for segment, names in (("pelvis", ("pelvis",)),
                           ("chest", ("chest",)),
                           ("shoulder", ("shoulder.L", "shoulder.R")),
                           ("hand", ("hand.L.tail", "hand.R.tail"))):
        big = 0.0
        for name in names:
            points = [Vector(s[name]) for s in samples]
            big = max(big, max((p - points[0]).length for p in points) * 1000.0)
        moved[segment] = round(big, 2)
    moved["foot(吸收前下落行程)"] = round(max(foot_span.values()), 2)
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
    res["power_chain_scale"] = "A10 蹬地尺子（thigh/shin ≥15°）"
    res["power_chain_ok"] = (all(v >= 5.0 for v in moved.values())
                             and all(v >= 15.0 for v in swing.values())
                             and all(v >= 1.0 for v in nonzero.values()))

    # 13) 交接真值（供 B 族 / D 族复用）。
    res["end_ankle_mm"] = {
        side: [round(v * 1000.0, 1) for v in samples[-1]["foot." + side]]
        for side in ("L", "R")}
    res["idle_ankle_mm"] = {
        side: [round(v * 1000.0, 1) for v in ANKLE_REST[side]]
        for side in ("L", "R")}
    res["plant_matches_idle_stance_mm"] = {
        side: round((Vector(samples[-1]["foot." + side])
                     - ANKLE_REST[side]).length * 1000.0, 3)
        for side in ("L", "R")}
    res["end_pelvis_z_mm"] = round(zs[-1] * 1000.0, 1)
    # 14) **末帧那一步的落地判定**（用动画本身量，不信"应用路径"的中间态）：
    #     收势是逐分量插欧拉，f29 与 f30 的**局部欧拉**已经相同 ⟹ 拳/前臂的世界位移
    #     应当只剩躯干末键的零点几度。若这里出现几十上百 mm，说明末帧真的翻了
    #     （`JUMPLAND_LAST_FRAME.real_world_step_deg` 是诊断读数，本项才是门禁）。
    last_step = {}
    for name in ("hand.L.tail", "hand.R.tail", "forearm.L.tail", "forearm.R.tail"):
        if name in samples[-1] and name in samples[-2]:
            last_step[name] = round((Vector(samples[-1][name])
                                     - Vector(samples[-2][name])).length * 1000.0, 2)
    res["last_step_move_mm"] = last_step
    res["last_step_move_ok"] = all(v <= 40.0 for v in last_step.values())
    res["touch_frame"] = T_TOUCH
    res["hitstop_frame_span"] = [T_TOUCH, T_HOLD_END]
    res["motion_clock_hold_frames"] = HOLD
    res["a11_style_ground_min_all_frames_mm"] = res.get("ground_min_mm")
    return res


# =============================================================== 主流程
def main():
    global ANKLE_REST, A12_END_ANKLE, PIN_ANKLE, Z_OFF, Z_IDLE
    global IDLE_RX, IDLE_QUAT, START_ARM_QUAT, ARM_E0, ARM_E1

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("JUMPLAND_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()
    for module, action_name in ((JS, JS.NAME), (JU, JU.NAME), (JF, JF.NAME)):
        if action_name not in bpy.data.actions:
            print("JUMPLAND_BOOTSTRAP 动画工程缺 %s，先补跑" % action_name)
            module.main()
            arm, meshes = A.open_animation_project()
            A.setup_scene()

    # ANKLE_REST = 全族通用的那把尺子（Idle_01@0 的 foot.head）= 触地后的钉死点。
    # 顺手把**末帧的三个真值**从 `Idle_01@0` 成品姿态读出来（不手抄）：
    #   IDLE_RX   躯干八骨的 rx（末键）—— 手写"接近 idle"的数差几度，末帧就是一次跳变
    #   Z_IDLE    骨盆世界 z（站姿）—— `PZ_KEYS` 的终点
    #   IDLE_ARM_EULER 手臂六骨的欧拉 —— 收势**逐分量插值**的终点（见 `arm_blend` 上方）
    I1.idle_pose(arm, 0.0)
    ANKLE_REST = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                  for side in ("L", "R")}
    IDLE_RX = {bone: math.degrees(arm.pose.bones[bone].rotation_euler[0])
               for bone in TRUNK_KEYS}
    Z_IDLE = float(A.bone_world(arm, "pelvis", "head")[2])
    IDLE_QUAT = {bone: arm.pose.bones[bone].matrix.to_quaternion()
                 for bone in ARM_BONES}
    IDLE_ARM_EULER = {bone: tuple(math.degrees(v)
                                  for v in arm.pose.bones[bone].rotation_euler)
                      for bone in ARM_BONES}
    A.report("JUMPLAND_ANKLE_REST",
             {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]]
              for s in ANKLE_REST})
    A.report("JUMPLAND_IDLE_TRUTH", {
        "trunk_rx_deg": {k: round(v, 2) for k, v in IDLE_RX.items()},
        "pelvis_z_mm": round(Z_IDLE * 1000.0, 2),
        "arm_euler_deg": {k: [round(x, 2) for x in v]
                          for k, v in IDLE_ARM_EULER.items()},
        "note": "末帧真值一律从 Idle_01@0 成品姿态读，不手抄（本支第 0 号教训）",
    })

    A.report("JUMPLAND_BALLISTIC", {
        "g_per_frame": G_PER_FRAME,
        "base_frames_from_takeoff": BASE_T,
        "z_start_mm": round(ballistic(0) * 1000.0, 3),
        "z_touch_mm": round(Z_TOUCH * 1000.0, 3),
        "z_deep_mm": round(Z_DEEP * 1000.0, 3),
        "fall_to_touch_mm": round((ballistic(0) - Z_TOUCH) * 1000.0, 1),
        "touch_rate_mm_per_frame_analytic": round(
            (ballistic(T_TOUCH) - ballistic(T_TOUCH - 1)) * 1000.0, 3),
        "hint": "触地帧 4；命中停顿吃掉 2 帧动作时间 ⟹ 动作时钟跨度 28",
    })

    # 读 A12 成品（f24）当 A13 的 f0，并把 carry 接力接到同一个点上。
    start_pose, start_quats = JU.capture_start(
        arm, bpy.data.actions[JF.NAME], JF.TOTAL)
    start_mats = CR.action_world_matrices(
        arm, bpy.data.actions[JF.NAME], JF.TOTAL)
    # A12 末帧的踝位（= 交接真值，不许硬编码）。
    A12_END_ANKLE = {}
    for side in ("L", "R"):
        a12_action = bpy.data.actions[JF.NAME]
        A12_END_ANKLE[side] = Vector(
            JS.ankle_series(arm, a12_action, [JF.TOTAL])[0][side])
    A.report("JUMPLAND_HANDOFF", {
        s: [round(v * 1000.0, 1) for v in A12_END_ANKLE[s]] for s in ("L", "R")})

    # 收势起点 = A12@24 的手臂**欧拉**（逐位，= `capture_start` 的成品值）；
    # 终点 = `Idle_01@0` 的手臂欧拉**折到离起点最近的等价族**（`_unwrap_xyz`）。
    # ★ 摇摆/扭转分解（`sweep`）是本支第 6 号教训的量化证据，留着供后续 D 族
    #   （受击/击倒，同样要收进站姿）复用：方向变化小、扭转大的那几骨正是
    #   不能走"世界空间测地线"的那几骨。
    START_ARM_QUAT = {b: start_quats[b] for b in ARM_BONES if b in start_quats}
    ARM_E0 = {b: tuple(start_pose[b]) for b in ARM_BONES}
    ARM_E1 = {b: JS._unwrap_xyz(ARM_E0[b], IDLE_ARM_EULER[b]) for b in ARM_BONES}
    sweep = {}
    for b, q0 in START_ARM_QUAT.items():
        q1 = IDLE_QUAT[b]
        d0 = (q0 @ Vector((0.0, 1.0, 0.0))).normalized()
        d1 = (q1 @ Vector((0.0, 1.0, 0.0))).normalized()
        residual = (d0.rotation_difference(d1) @ q0).inverted() @ q1
        angle = math.degrees(residual.angle)
        if residual.axis.dot(d1) < 0.0:
            angle = -angle
        sweep[b] = {
            "total_deg": round(_angle_between(q0, q1), 2),
            "swing_dir_deg": round(math.degrees(d0.angle(d1)), 2),
            "twist_deg": round(angle, 2),
        }
    A.report("JUMPLAND_ARM_SWEEP", {
        "decompose": sweep,
        "euler_delta_deg": {b: [round(ARM_E1[b][i] - ARM_E0[b][i], 2)
                                for i in range(3)] for b in ARM_BONES},
        "predicted_peak_step_deg": round(
            max(max(abs(ARM_E1[b][i] - ARM_E0[b][i]) for i in range(3))
                for b in ARM_BONES) / (1.0 - 0.12) / ARM_RAMP_C, 2),
        "ramp_frames_clock": ARM_RAMP_C,
        "note": ("swing = 骨轴方向改变；twist = 绕骨轴净扭转（纯自转，不放大欧拉）。"
                 "收势走**逐分量欧拉插值**：峰值步长 = 最大分量差/(1−ramp)/帧数"),
    })
    # ★ 必须卸掉 action：否则后续 `view_layer.update()` 会在某些帧把 pelvis 的
    #   f-curve 值重新压回 pose bone，IK 的髋高被污染（A11 踩过，A12 沿用）。
    arm.animation_data.action = None

    def seed_state():
        """把欧拉解缠的参照复位到 A12@24 的成品值。

        A10/A11/A12 时代的 carry 接力（`JS.ARM_QUAT` / `ARM_ROLL` / roll 搜索）
        本支**已不用** —— 收势改走朝向 slerp（见文件头第 6 条）——
        所以这里只复位 `_PREV_EULER`（`_unwrap_xyz` 的上一帧参照）。
        """
        JS._PREV_EULER.clear()
        for name, value in start_pose.items():
            if not name.startswith("@"):
                JS._PREV_EULER[name] = tuple(value)

    # ---- 第一遍：扫贴地常数（zoff = 0）
    Z_OFF = {"L": 0.0, "R": 0.0}
    PIN_ANKLE = {s: Vector((ANKLE_REST[s].x, ANKLE_REST[s].y, ANKLE_REST[s].z))
                 for s in ("L", "R")}
    seed_state()
    del TARGETS[:]
    del TRACE[:]
    z_off, lows = calibrate(arm)
    A.report("JUMPLAND_CALIBRATION", {
        "z_off_mm": {k: round(v * 1000.0, 3) for k, v in z_off.items()},
        "planted_sole_range_mm": {k: [round(min(lows[k]) * 1000.0, 2),
                                      round(max(lows[k]) * 1000.0, 2)]
                                  for k in ("L", "R")},
        "planted_sole_span_mm": {k: round((max(lows[k]) - min(lows[k])) * 1000.0, 2)
                                 for k in ("L", "R")},
        "predicted_min_after_zoff_mm": round(min(min(lows[k]) + z_off[k]
                                                for k in ("L", "R")) * 1000.0, 2),
        "ramp_frames": T_RAMP_END_C - T_DEEP_C,
        "note": "末帧必须逐位等于 Idle_01@0 ⟹ 常数在 RISE 段线性回零（见文件头第 4 条）",
    })

    # ---- 第二遍：正式生成
    Z_OFF = z_off
    PIN_ANKLE = {s: Vector((ANKLE_REST[s].x, ANKLE_REST[s].y,
                            ANKLE_REST[s].z + Z_OFF[s])) for s in ("L", "R")}
    seed_state()
    del TARGETS[:]
    del TRACE[:]

    keyframes = [(0, start_pose)]
    freeze_pose = None
    for frame in range(1, TOTAL + 1):
        if T_TOUCH <= frame <= T_HOLD_END:
            if freeze_pose is None:
                freeze_pose = build_pose(arm, frame, record=True)
            keyframes.append((frame, freeze_pose))
            continue
        if frame == TOTAL:
            final, adjusted = final_idle_pose(arm, JS._PREV_EULER)
            # 真世界旋转 vs 表示跳：末帧距 f29 的角度差（度）。>25° 就一定得改姿态，
            # 而不是"把欧拉折一折"——`_unwrap_xyz` 只能改表示，改不了真朝向。
            real = {}
            for bone in ARM_BONES:
                real[bone] = round(_angle_between(
                    arm.pose.bones[bone].matrix.to_quaternion(),
                    TRACE[-1]["quat"][bone]), 2) if TRACE else 0.0
            A.report("JUMPLAND_LAST_FRAME", {
                "adjusted_bones": adjusted,
                "real_world_step_deg": real,
                "threshold_deg": 8.0,
                "note": "只在欧拉表示离上一帧 >8° 时折算等价族；世界朝向不变",
            })
            _record_trace(arm, frame, final)
            keyframes.append((frame, final))
            continue
        keyframes.append((frame, build_pose(arm, frame, record=True)))

    # 手臂欧拉健康度：收势改走朝向 slerp 后没有 roll 搜索了，改从 TRACE 直接量。
    arm_y = {b: max(abs(row["euler"][b][1]) for row in TRACE) for b in ARM_BONES}
    A.report("JUMPLAND_ARM_EULER", {
        "max_abs_euler_y_deg": round(max(arm_y.values()), 2),
        "per_bone_y_deg": {k: round(v, 1) for k, v in arm_y.items()},
        "note": ("收势 = 逐分量插欧拉（不读骨骼、无反馈）；|Y| 只作万向节锁健康度体检，"
                 "实测 ≤30.3° ⟹ 1/cos(30.3°)=1.16，放大可忽略"),
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "基础移动",
        "note": ("落地：接 Jump_Fall@24 的 %.0f mm/帧 冲击，帧 4 触地（鞋底到 0）、"
                 "命中停顿 3 帧、屈膝吸收（骨盆再沉 %.0f mm 到 %.0f mm）、"
                 "上身被惯性压折 9°→31°，随后收回战斗站姿（末帧逐位 = Idle_01@0）"
                 % (-(ballistic(T_TOUCH) - ballistic(T_TOUCH - 1)) * 1000.0,
                    (Z_TOUCH - Z_DEEP) * 1000.0, Z_DEEP * 1000.0)),
        "antic_frame": None,
        "hit_frame": T_TOUCH,
        "cancel_frame": T_DEEP_C + HOLD + 3,
        "hitstop_frames": T_HOLD_END - T_TOUCH + 1,
        "root_motion_m": [0.0, 0.0],
        "touch_frame": T_TOUCH,
        "hitstop_span": [T_TOUCH, T_HOLD_END],
        "impact_speed_mps": round((ballistic(T_TOUCH) - ballistic(T_TOUCH - 1))
                                  * A.FPS, 4),
        "landing_impact_mps": round(-2.0 * (ballistic(T_TOUCH)
                                            - ballistic(T_TOUCH - 1)) * A.FPS, 4),
        "absorb_depth_m": round(Z_TOUCH - Z_DEEP, 4),
        "deepest_pelvis_z_m": Z_DEEP,
        "end_pelvis_z_m": Z_IDLE,
        "link_prev": "A12 Jump_Fall@24（末帧竖速 −65.2 mm/帧）",
        "link_next": "A01 Idle_01@0（末帧逐位相等）→ B 族普通攻击",
        "planted_z_off_mm": {k: round(v * 1000.0, 3) for k, v in Z_OFF.items()},
        "power_chain_scale_note": "落地有真实地面反力：换回 A10 的蹬地尺子（≥15°）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    # 命中停顿：把 [4, 6] 区间的键设成 CONSTANT（姿态已共用同一对象，双保险 + 引擎可读）。
    A.set_hitstop(action, T_TOUCH, T_HOLD_END)
    A.add_markers(action, {
        "FALL_IN": 0, "TOUCHDOWN": T_TOUCH, "HITSTOP": T_TOUCH,
        "HITSTOP_END": T_HOLD_END, "ABSORB": T_HOLD_END,
        "DEEPEST": T_DEEP_C + HOLD, "RISE": T_DEEP_C + HOLD,
        "RECOVER": T_RAMP_END_C, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # foot_probe 置空：通用门禁的"脚位移 ≤3 mm"是**全段**口径，本支前 4 帧脚在空中，
    # 由专属 `feet_pinned_ok`（触地后按踝判）+ `airborne_before_touch_ok` 接管。
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report["common_ground_contact_all_frames_ok"] = report.get("ground_contact_ok")
    report["ground_contact_ok"] = None
    report["ground_contact_skipped_reason"] = \
        "全段口径不适用（前 4 帧在空中）；触地后窗口由专属 ground_contact_ok 判"

    idle_mats = CR.action_world_matrices(arm, bpy.data.actions["Idle_01"], 0)
    sole = JS.sole_series(arm, action, list(range(0, TOTAL + 1)))
    ankles = JS.ankle_series(arm, action, list(range(0, TOTAL + 1)))
    target_err = 0.0
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    for index, frame in enumerate(range(0, TOTAL + 1)):
        if frame == 0:
            continue
        for side in ("L", "R"):
            if (frame, side) not in pair:
                continue
            target_err = max(target_err,
                             (Vector(ankles[index][side])
                              - pair[(frame, side)]).length)

    reach = JF.reach_series(arm, action, list(range(0, TOTAL + 1)))
    report.update(land_assertions(arm, action, samples, start_mats, sole,
                                  target_err, reach, idle_mats))
    report["meta"] = meta
    # 显式登记被跳过的门禁（值 None）：既让 failed 干净，又不静默隐藏。
    report["skipped_gates"] = sorted(
        k for k, v in report.items() if v is None and k.endswith("_ok"))
    failed = sorted(k for k, v in report.items()
                    if (k.endswith("_ok") or k == "no_teleport")
                    and v is not True and v is not None)
    report["failed"] = failed
    A.report("JUMPLAND_REPORT", report)

    if not SKIP_RENDER:
        LAND_SIDE = ("side", (4.8, 0.0, 1.05), (0.0, 0.0, 1.05), 2.60,
                     (760, 1180))
        LAND_FRONT = ("front", (0.0, -5.2, 1.05), (0.0, 0.0, 1.05), 2.60,
                      (760, 1180))
        LAND_3Q = ("three_quarter", (3.4, -3.8, 1.20), (0.0, 0.0, 0.98), 2.60,
                   (760, 1180))
        A.render_pose_sheet(arm, action,
                            [0, 2, T_TOUCH, 5, 8, 11, T_DEEP_C + HOLD, 20, 26,
                             TOTAL], "jumpland", views=(LAND_SIDE,))
        A.render_pose_sheet(arm, action, [0, T_TOUCH, T_DEEP_C + HOLD, TOTAL],
                            "jumpland", views=(LAND_FRONT,))
        A.render_pose_sheet(arm, action, [T_TOUCH, T_DEEP_C + HOLD], "jumpland",
                            views=(LAND_3Q,))
        # 存盘/导出只在**出图那一遍**做：SKIP_RENDER 是纯门禁迭代。
        A.save_project()
        A.export_glb(arm)
    print("JUMPLAND_DONE failed=%s" % failed)

    # 诊断：逐帧臂骨欧拉步 + 真世界旋转步（区分"表示跳"与"真扭转变"）。
    detail = []
    for index in range(1, len(TRACE)):
        before, after = TRACE[index - 1], TRACE[index]
        row = {"f": after["frame"]}
        for name in ARM_BONES:
            step = max(abs(a - b) for a, b in
                       zip(before["euler"][name], after["euler"][name]))
            ang = math.degrees(before["quat"][name].rotation_difference(
                after["quat"][name]).angle)
            if ang > 180.0:
                ang = 360.0 - ang
            row[name] = "%d/%d Y%.0f r%.0f" % (
                round(step), round(ang), after["euler"][name][1],
                after["roll"].get(name, 0.0))
        detail.append(row)
    A.report("JUMPLAND_TRACE_DETAIL", detail)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("JUMPLAND_FAILURE " + traceback.format_exc())
