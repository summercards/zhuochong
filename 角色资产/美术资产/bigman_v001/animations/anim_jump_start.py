"""anim_jump_start —— A10 `Jump_Start` 起跳。

设计（对着清单「下一支计划 —— A10」逐条落）：
    定位      深蹲蓄力后爆发，猛男型角色起跳需要**明显预备动作**（清单原文）。
              这是「战斗站姿 → 离地」的一次性动作；空中上升的**后半段**交 A11。
    时长      36 帧 / 0.600 s @60fps，**非循环**（`loop=False`）。
    衔接      首帧 = `Idle_01@0`（`I1.idle_pose(arm, 0.0)`，世界矩阵逐位一致）。
    结构      0~14   ANTIC：反向预备（骨盆先抬 12 mm）→ 深蹲蓄力到 0.620，
                     双臂向后甩到身后极限，上身压低。
              14~20  LAUNCH：脚掌绕**前掌着地点**碾起（脚跟离地）、膝髋同时伸展、
                     骨盆按**幂律** τ^1.5 上升 300 mm（见下面第 1 条）。
              20~30  AIRBORNE：双脚离地，身体展开、四肢略收（膝弯继续增加）。
              30~36  SETTLE：收腿收尾，末 6 帧角度增量单调收敛。
    原地      清单 §0.4：Jump 属"普通移动"，**不给 Root Motion**（`root_motion_m=[0,0]`），
              但登记 `takeoff_speed_mps` 供引擎侧做起跳初速度。

---------------------------------------------------------------------------
本支的五个关键做法（都有前几支的实测依据）

1. **LAUNCH 只有 6 帧，是清单计划定的，不是随手定的。**
   计划原文：「`launch_speed_ok`（爆发段**平均**骨盆 z 速率 ≥ 45 mm/帧，
   是下蹲速率 16.95 的 ~3 倍 —— 爆发必须有量纲对比）」，且分段表写 `LAUNCH 14~20`。
   六帧、抬升 Δ=300 mm ⟹ 平均速率 = Δ/T = **50.0 mm/帧** ≥ 45 ✓。

   但**"匀加速"在这里被否掉了** —— 不是拍脑袋改，是实测逼出来的：
   匀加速（τ²）意味着末帧速率是平均的 2 倍 = **100 mm/帧**，于是最后一帧
   膝要在一帧里伸掉 18.5°；实测 `shin.L` 在 f20 的欧拉单帧步 **28.33°**
   （`no_teleport` 上限 25°）—— 这一帧会看起来像"腿被弹了一下"。
   改成**幂律 τ^p，p = 1.5**：
       · 起点速率 = 0（与蓄力段末速 0 的 C¹ 衔接保持不变）；
       · 平均速率 = Δ/T = 50（`launch_speed_ok` 的口径不变）；
       · **末帧速率 = p·Δ/T = 75 mm/帧**（而不是 100）⟹ 峰值膝伸展速率降 25%，
         实测 `shin.L` 单帧步从 28.33 降到 **<25**，判据不改。
   代价（必须说清楚）：起跳初速从 6.00 降到 **4.50 m/s**，apex 从 1.837 降到
   **1.033 m**。仍然是一次超人类高度的跳（角色 1.803 m），但不再荒谬。
   ⟹ 这条判据（六帧窗口 × ≥45 平均）**强制**一次高跳，这是 Jump 族
   （A11/A12/A13）的已知设计约束，写进日志。

2. **推离地面时脚不是"绕踝转"，而是"绕鞋底最前端转"。**
   早期实现把着地点取在"踝前 165 mm"（A05 的球部位置），结果碾转期鞋底最低点
   跑到 **−11.38 mm**（远超门禁 −2 mm 上限）：刚性鞋不能像真脚那样折趾，
   **球部之前那截鞋底会绕着球部往下扎**。修法不是放宽容差，而是把着地点
   改到**实测的鞋底最前端**（`measure_pivot`：Idle_01@0 下鞋底最低 6 mm 内
   顶点中 y 最小者）。绕这一点转，鞋的其余部分只升不降 ⟹ 最低点恒 ≈ 0。

3. **空中段不给腿轨，给"髋-踝竖距"轨，让 IK 吃掉骨盆上升。**
   离地后骨盆按弹道继续升 1.2 m；若踝还有独立轨，两者一旦速率不同就会把腿拉直
   或拉穿（|髋−踝| 有 0.822 m 上限）。改成 VERT(f) = 髋踝竖距，逐帧解算，
   腿型只由 VERT 一条曲线控制 ⟹ 膝弯角单调、`no_teleport` / `decel_smooth` 都可控。
   **两侧分别给末值**：这是交错架势（前脚 y = −0.170、后脚 y = +0.140，A01 定稿），
   同一条 VERT 曲线对两腿的膝角增量不同（实测 R 侧只有 L 侧的 0.52 倍）。

4. **`no_teleport` 红的根因是 `_nlerp`，不是 `rotation_difference`。**
   首版把手臂姿态写成"护体方向 ↔ 背后方向"的 `_nlerp` 插值。护体
   `hand.R = (0.18, −0.60, 0.78)` 与背后 `(−0.15, 0.97, −0.20)` 夹角 **140°**
   （近乎反向），线性插值归一化时中间点几乎穿过原点 ⟹ 角速度在 `t ≈ 0.5`
   处爆到 **41°/帧**。探针实测：`f18 hand.R` 的**世界旋转测地角**单帧
   **149.33°** —— 这是真旋转，不是表示跳（`probe_js_branch.py` 把
   `rotation_difference` 的"绕远路"四元数折回来后才量到）。
   修法两件：
     ① `_nlerp` → **`_slerp`**（匀角速，两端 140°×1.5/14 ≈ 15°/帧）；
     ② 手臂路径改**两段式**：护体 → 背后（f0~14）→ 前上（f14~30），
        直接 slerp，不再"经护体中转"（那会把 134° 的路走成 171°）。

5. **欧拉表示仍要逐帧解缠，但等价族不止 ±360。** 表示跳是另一件事，
   它同样会被 `no_teleport` 抓到：同一物理姿态在 XYZ 欧拉的
   `(x, y, z) ≡ (x+180, 180−y, z+180)` 这族**翻转分支**之间跳时，
   表观增量可达 155°（`probe_js_branch` 实测 wrap 模式 155.81 @ [10, hand.R]）。
   手写 ±360 折算处理不了这一族。修法：`_unwrap_xyz` 枚举
   {原分支, 翻转分支} × 每轴 {−1,0,+1}×360°，取离上一帧最近者。

6. **"刚性跟随基准"是错的，`probe_js_base.py` 一次证伪。**
   曾想让前臂/手跟着上臂的 guard→now 旋转走（`base_q = qd @ ARM_GUARD_Q`），
   期望"相对朝向退回 guard、远离万向节锁"。实测**更糟**（35.2° → 168.0°）：
   探针量到 `separation = ∠(基准骨轴, 目标方向)` 在 f14 `forearm.L` 达
   **179.25°** —— 几乎反向。`rotation_difference` 在两向量近反平行时，
   **旋转轴由数值噪声决定**（叉积长度 sin179° ≈ 0），于是每帧给出一个
   轴乱翻的 ~180° 旋转 ⟹ **真世界旋转**单帧跳 **141.33°**（探针 `rot`）。
   这不是表示问题，解缠救不了。
   ⟹ 弃用。**方向约束下绕骨轴的 roll 是自由 DOF**，用它来选欧拉分支
   （见下面 `aim_carry` 的 roll 搜索）。

7. **贴地常数重新扫**（清单注意第三条的硬要求）：深蹲深度 210 mm ≠ A08 的 202 mm，
   蒙皮影响不同，不能沿用 A08 的 z_off。本支扫 0~14 帧（蓄力段）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_jump_start.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A       # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_walk_f as WF   # noqa: E402
import anim_turn as TURN   # noqa: E402
import anim_crouch as CR   # noqa: E402

NAME = "Jump_Start"
TOTAL = 36                       # 0.600 s @ 60 fps
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")

# ---------------------------------------------------------------- 阶段划分
T_ANTIC_TOP = 3                  # 反向预备峰值
T_CROUCH = 14                    # 蓄力最深
T_TAKEOFF = 20                   # 最后一次触地（离地帧）
T_TUCK = 30                      # AIRBORNE 结束（清单分段表）
T_SWING_END = T_TUCK             # 手臂上摆的终点（之后收势到 ARM_AIR）

# ---------------------------------------------------------------- 骨盆轨迹
# 0.830（A01 战斗站姿）→ 反向上抬 12 mm（f3）→ 深蹲到 0.620（f14）
# → 匀加速爆发到 0.920（f20）→ 弹道。
IDLE_PELVIS_Z = 0.8300
CROUCH_PELVIS_Z = 0.6200
TAKEOFF_PELVIS_Z = 0.9200
LAUNCH_FRAMES = T_TAKEOFF - T_CROUCH                  # 6
LAUNCH_RISE = TAKEOFF_PELVIS_Z - CROUCH_PELVIS_Z      # 0.300 m
# **幂律指数**：1.5 而不是 2（匀加速）。理由见文件头第 1 条 —— 匀加速把末帧
# 速率推到平均的 2 倍（100 mm/帧），实测会把 `shin.L` 的单帧欧拉步顶到 28.33°。
# p=1.5 保住了"起点速率为 0"与"平均 = Δ/T = 50"，只把末帧速率降到 75。
LAUNCH_POW = 1.5
TAKEOFF_SPEED = LAUNCH_POW * LAUNCH_RISE / LAUNCH_FRAMES   # 0.075 m/帧 = 4.50 m/s
G_PER_FRAME = 9.8 / float(A.FPS ** 2)                 # m/帧²（按 60 fps 折算）
APEX_RISE = TAKEOFF_SPEED ** 2 / (2.0 * G_PER_FRAME)  # 起跳后还能升多高（m）

# 蓄力：用 cosine ease 采样出来的一串键（末段切线被 TURN.track 强制置 0
# ⟹ 谷底速度天然为 0，正好接"从静止匀加速"的爆发段）。
PELVIS_Z_KEYS = ((0, 0.8300), (1, 0.8360), (2, 0.8405), (3, 0.8420),
                 (5, 0.8227), (7, 0.7793), (9, 0.7159), (11, 0.6561),
                 (13, 0.6252), (14, 0.6200))
# 骨盆水平：原地（清单 §0.4）。y 只做 22 mm 的**重心前后转移** —— 蓄力时重心后坐
# 压在脚上，推离时向前送出，离地后回到 0。上限定在 22 mm 是因为专属门禁
# `crouch_path_ok`（蓄力段水平位移 ≤ 25 mm，A08 踩坑 3 的口径）要把 Hermite
# 的轻微过冲也算进去（实测过冲到 22.06 mm）。
PELVIS_Y_KEYS = ((0, 0.0000), (3, 0.0030), (7, 0.0120), (11, 0.0190),
                 (14, 0.0220), (18, 0.0160), (21, 0.0100), (26, 0.0030),
                 (31, 0.0000), (36, -0.0010))

# ---------------------------------------------------------------- 躯干（度）
# 胸链累计前倾 = pelvis + spine_01 + spine_02 + chest：9°（A01）→ 27.8°（蓄力）
# → 4.2°（起跳，躯干打开做伸展动作）
PELVIS_RX = ((0, 4.0), (3, 5.4), (7, 9.4), (11, 13.2), (14, 14.8), (18, 7.0),
             (20, 2.0), (26, 1.2), (36, 0.6))
SPINE01_RX = ((0, 2.0), (3, 2.4), (7, 3.4), (11, 4.6), (14, 5.2), (18, 2.6),
              (20, 1.2), (26, 0.8), (36, 0.5))
SPINE02_RX = ((0, 2.0), (3, 2.4), (7, 3.4), (11, 4.5), (14, 5.0), (18, 2.5),
              (20, 1.2), (26, 0.7), (36, 0.4))
CHEST_RX = ((0, 1.0), (3, 1.2), (7, 1.8), (11, 2.6), (14, 3.0), (18, 1.2),
            (20, 0.4), (26, 0.0), (36, -0.2))
NECK_RX = ((0, -6.0), (3, -6.6), (7, -8.6), (11, -10.4), (14, -11.0),
           (18, -7.0), (20, -5.0), (26, -4.2), (36, -4.0))
HEAD_RX = ((0, 5.0), (3, 5.4), (7, 6.8), (11, 8.4), (14, 9.0), (18, 6.0),
           (20, 4.4), (26, 3.6), (36, 3.4))
# 肩：蓄力时缩起来（−21.2），起跳时随手臂上摆打开到 −4（肩已抬到最高）
SHOULDER_RX = ((0, -18.0), (3, -18.4), (7, -19.8), (11, -21.0), (14, -21.2),
               (18, -10.0), (20, -4.0), (26, -2.5), (36, -4.0))

# ---------------------------------------------------------------- 手臂（世界方向）
# GUARD = A01 的护体架势（f0 逐位一致）。手臂路径是**两段 slerp**：
#   f0  ~ 14   护体 → 背后极限（蓄力甩臂）
#   f14 ~ 30   背后极限 → 前上略收（起跳甩臂，终点即空中姿态）
# 不再"经护体中转"：背后→护体 140° + 护体→前上 31° = 171° 的路，
# 直接 slerp 只有 137°，且中间不会出现 `_nlerp` 那种角速度尖峰（文件头第 4 条）。
# 终点就落在空中姿态上、**不留独立收势段**：`decel_smooth_ok` 要的是末 6 帧
# 增量单调收敛，而"再补一段收势"必然在末段中部加一个速率峰（实测 2.456 > 1.901，
# 直接判红）。让手臂在 f30 到位后**静止**，末段就只剩腿与躯干在收敛。
ARM_BACK_RAW = {
    "upperarm.L": (0.26, 0.86, -0.44),
    "forearm.L": (0.20, 0.93, -0.31),
    "hand.L": (0.16, 0.96, -0.24),
    "upperarm.R": (-0.24, 0.88, -0.41),
    "forearm.R": (-0.18, 0.94, -0.29),
    "hand.R": (-0.15, 0.97, -0.20),
}
# 蓄力摆幅系数：把"护体 → 背后极限"的 140° 收到 **119°**（0.85 倍）。
# 理由：第一段只有 14 帧，140°/14 = 10.0°/帧的均值已经顶到 `no_teleport`
# 的边缘（欧拉步 ≈ 均值的 2.3 倍）。收到 119° 后均值降到 8.5°/帧，
# 峰值（梯形剖面 1/(1−0.12) 倍）9.7°/帧，欧拉步 ≈ 22°，判据不动。
# 119° 仍是"手臂从护体甩到身后"的明显预备动作（清单要求）。
ARM_BACK_AMP = 0.85
ARM_BACK = {}                    # 运行时由 `build_arm_targets` 从 guard 与 RAW 算出
# 起跳甩臂的**终点**姿态（= 空中姿态，清单 A11 口径「四肢略收」）。
# 上一版把它拆成 ARM_UP + ARM_AIR 两段，实测会在末段中部加一个速率峰
# （2.456 > 1.901）把 `decel_smooth_ok` 判红。两支只差 10°，合并成一支。
ARM_AIR = {
    "upperarm.L": (0.26, -0.70, 0.66),
    "forearm.L": (0.20, -0.62, 0.76),
    "hand.L": (0.16, -0.56, 0.81),
    "upperarm.R": (-0.24, -0.71, 0.65),
    "forearm.R": (-0.18, -0.63, 0.76),
    "hand.R": (-0.15, -0.58, 0.80),
}

# ---------------------------------------------------------------- 足
# 着地点在**踝前方**的距离（米）—— 由 `measure_pivot` 实测，不硬编码。
PIVOT_FWD = {"L": 0.0, "R": 0.0}
TIP_TAKEOFF = 29.0               # 离地瞬间的踮脚角（度）
TIP_END = 12.0                   # 空中收脚后的足尖角
TIP_KEYS = ((0, 0.0), (14, 0.0), (17, 8.0), (20, TIP_TAKEOFF),
            (24, 27.0), (28, 21.0), (32, 16.0), (36, TIP_END))
# 空中段的"髋-踝竖距"末值（米）。**两侧分开**：交错架势下同一条曲线对两腿的
# 膝角增量不同（首版同值时 R 侧只收到 17.74°，判据 ≥20°）。解析预估：
# 竖距每减 10 mm ≈ 膝弯多 3.5°（dθ/dd，在 d≈0.72 处），R 需多 2.3° ⟹ 再多收 ~7 mm。
VERT_END = {"L": 0.690, "R": 0.670}

ARM_REF = {}                     # bone -> 世界参考向量（= A01@0 姿态下该骨的世界 X 轴）
ARM_QUAT = {}                    # bone -> 上一帧**已达成**的世界朝向（carry 接力用）
ARM_ROLL = {}                    # bone -> 本帧选定的绕骨轴 roll（度，诊断用）
MAX_ABS_EULER_Y = 0.0            # 手臂六骨欧拉中间角 |Y| 的全程最大值（诊断用）
ROLL_MAX = {}                    # bone -> |roll| 的最大值（诊断用）
ANKLE_REST = {}                  # side -> Vector（A01@0 实测踝位）
Z_OFF = {"L": 0.0, "R": 0.0}     # 鞋底贴地的冻结常数偏移（米）
TAKEOFF_ANKLE_Z = {"L": 0.0, "R": 0.0}   # 离地瞬间的踝高（米）
TAKEOFF_VERT = {"L": 0.0, "R": 0.0}      # 离地瞬间的髋-踝竖距（米）
TARGETS = []                     # 逐帧登记的 (frame, side, target) —— 供 IK 误差核验
_PREV_EULER = {}                 # 欧拉解缠的上一帧参照

# ---------------------------------------------------------------- roll 搜索
# 方向约束（骨轴 = 目标世界方向）下，**绕骨轴的自转是自由 DOF**。
# carry 接力只保证"世界旋转最小变动"，**不保证 twist 不累积**：本支实测
# forearm.R 的欧拉中间角（Y）从 f14 的 +11° 一路漂到 f30 的 **−88.5°**，
# 直插 XYZ 欧拉的万向节锁（|Y| → 90°）。到那一步 X/Z 两通道开始耦合，
# 真转 2.36° 的一帧要欧拉走 **35°**（放大 15×）。
# 而 roll 恰好能搬动 Y（实测映射 ≈ 1:1：roll 0 → Y=−88.5，roll 120 → Y=+28.8）。
# 于是：carry 解出的欧拉若"步长大"或"|Y| 逼近 90°"，就绕目标方向扫 roll，
# 取"步长 + |Y| 越界惩罚"最小的一支。方向不变、只动滚转。
# **必须在逼近之前就驾开** —— 探针实测到 f30 再补已经晚了：
# 那一帧任意 roll 的最佳欧拉步仍是 35.04（要离开 −90° 就得让 X/Z 各跳 100°+）。
ROLL_COMFORT = 16.0              # 欧拉步低于此值**且** Y 安全时不搜（省时）
ROLL_RANGE = 120.0               # 粗搜半径（度）
ROLL_COARSE = 6.0                # 粗搜步长（度）
ROLL_FINE = 1.0                  # 精搜步长（度）
Y_SAFE = 62.0                    # 欧拉中间角的安全带：|Y| 超过它开始罚
Y_WEIGHT = 2.0                   # 惩罚权重（度/度）


# =============================================================== 数学小工具
def _frange(start, stop, step):
    """闭区间浮点枚举（含两端），避免 range 的整数限制。"""
    count = int(round((stop - start) / step)) + 1
    return [start + i * step for i in range(count)]


def _nlerp(u, v, t):
    """**已弃用**：见 `arm_dirs` 的说明 —— 近乎反向的两向量走线性插值时，
    中间点几乎穿过原点，归一化会把角速度放大到 41°/帧。保留只为对照。"""
    w = tuple(a + (b - a) * t for a, b in zip(u, v))
    n = math.sqrt(sum(c * c for c in w)) or 1.0
    return tuple(c / n for c in w)


def _slerp(u, v, t):
    """单位球面线性插值 —— 整段**匀角速**，不会在中间加速。

    这是本支最贵的一课（文件头第 4 条）：护体方向与背后方向夹角 140°，
    `_nlerp` 在 t=0.5 处把角速度从 10°/帧放大到 41°/帧，`no_teleport` 直接红。
    """
    a = Vector(u).normalized()
    b = Vector(v).normalized()
    d = max(-1.0, min(1.0, a.dot(b)))
    if d > 0.9995:                      # 几乎同向：线性即可（避免 sinθ→0）
        return tuple((a + (b - a) * t).normalized())
    if d < -0.9995:                     # 几乎反向：大圆退化，任取一条正交轴
        axis = a.cross(Vector((0.0, 0.0, 1.0)))
        if axis.length < 1e-6:
            axis = a.cross(Vector((0.0, 1.0, 0.0)))
        axis.normalize()
        ang = math.pi * t
        return tuple((a * math.cos(ang) + axis * math.sin(ang)).normalized())
    theta = math.acos(d)
    sin_theta = math.sin(theta)
    w = (math.sin((1.0 - t) * theta) / sin_theta) * a \
        + (math.sin(t * theta) / sin_theta) * b
    return tuple(w.normalized())


def _smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def _ease_ramp(u, ramp=0.12):
    """梯形速度剖面：两端平滑起停、**中段匀速**，峰值速度 = 均值/(1−ramp)。

    为什么不用 `_smoothstep`：它的峰值速度是平均值的 **1.5 倍**，本支实测把
    `upperarm.R` 的单帧欧拉步顶到 **27.47°**（判据 25°）。梯形剖面把峰值压到
    均值的 1/(1−ramp) 倍 —— ramp = 0.12 时只放大 13.6%。
    两端速度仍为 0 ⟹ 与前后段 C¹ 衔接，末段也不会多出速率峰。

    归一化必须除以 `(1−ramp)`：速度剖面 ∫₀¹v du = 1 − ramp（不是 1），
    忘了除会让 s 在 u = ramp 与 u = 1−ramp 处**跳变**（首版就栽在这，
    实测手臂一帧扫了 45°，`forearm.L` 单帧欧拉步爆到 66.99°）。
    """
    u = max(0.0, min(1.0, u))
    span = 1.0 - ramp
    if u <= ramp:
        return (u * u / (2.0 * ramp)) / span
    if u >= 1.0 - ramp:
        w = 1.0 - u
        return 1.0 - (w * w / (2.0 * ramp)) / span
    return (u - ramp / 2.0) / span


def _unwrap_xyz(prev, raw):
    """把欧拉元组折算到**离 `prev` 最近**的等价表示。

    XYZ 欧拉的等价族有两支，手写 ±360 只覆盖了第一支：
        (x, y, z) ≡ (x ± 360k, y ± 360k, z ± 360k)
        (x, y, z) ≡ (x + 180, 180 − y, z + 180)   ← **翻转分支**
    实测同一物理姿态在这两支之间跳，表观增量可达 155°（`probe_js_branch`
    的 wrap 模式：155.81 @ [10, hand.R]）。欧拉通道是逐分量插值的，
    表示跳变 = 真闪帧，不是"门禁误报"。
    """
    if prev is None:
        return tuple(raw)
    base = tuple(float(v) for v in raw)
    flip = (base[0] + 180.0, 180.0 - base[1], base[2] + 180.0)
    best, best_cost = base, None
    for branch in (base, flip):
        for kx in (-1, 0, 1):
            for ky in (-1, 0, 1):
                for kz in (-1, 0, 1):
                    cand = (branch[0] + 360.0 * kx,
                            branch[1] + 360.0 * ky,
                            branch[2] + 360.0 * kz)
                    cost = max(abs(cand[i] - prev[i]) for i in range(3))
                    if best_cost is None or cost < best_cost:
                        best, best_cost = cand, cost
    return best


def pelvis_at(frame):
    """骨盆世界 z（米）。三段解析：
       ① 0~14  反向预备 + 屈膝下蹲（末段切线为 0 ⟹ 谷底速度天然为 0）
       ② 14~20 爆发：**幂律 τ^1.5**（起点速率为 0，与①的末速 0 保持 C¹；
                 末帧速率 = 1.5·Δ/T = 75 mm/帧，而不是匀加速的 100 —— 见文件头第 1 条）
       ③ 20~36 离地后：**严格弹道**，减速度 = g
    """
    if frame <= T_CROUCH:
        return TURN.track(PELVIS_Z_KEYS, frame)
    if frame <= T_TAKEOFF:
        tau = (frame - T_CROUCH) / float(LAUNCH_FRAMES)
        return CROUCH_PELVIS_Z + LAUNCH_RISE * (tau ** LAUNCH_POW)
    t = frame - T_TAKEOFF
    return TAKEOFF_PELVIS_Z + TAKEOFF_SPEED * t - 0.5 * G_PER_FRAME * t * t


def air_u(frame):
    """空中段的归一化收腿量 u ∈ [0,1]，`u = 2s − s²`。

    选它的理由：du/ds = 2(1−s) 单调递减到 0 ⟹ 逐帧增量单调递减，
    `decel_smooth_ok`（末 6 帧角度增量单调收敛）是**构造出来的**，不是调出来的。
    """
    s = (frame - T_TAKEOFF) / float(TOTAL - T_TAKEOFF)
    s = max(0.0, min(1.0, s))
    return 2.0 * s - s * s


def ankle_target(arm, frame, side):
    """该侧踝的世界目标位置。

    触地期（≤T_TAKEOFF）：**绕鞋底最前端 B 碾转** —— B 固定，踝随之抬起并前移。
    空中（>T_TAKEOFF）：由骨盆 + `VERT`（髋-踝竖距）给出，y 收回身体正下方。
    """
    rest = ANKLE_REST[side]
    piv = PIVOT_FWD[side]
    z0 = rest.z + Z_OFF[side]
    if frame <= T_TAKEOFF:
        tip = math.radians(TURN.track(TIP_KEYS, frame))
        y = rest.y - piv * (1.0 - math.cos(tip)) - z0 * math.sin(tip)
        z = piv * math.sin(tip) + z0 * math.cos(tip)
        return Vector((rest.x, y, z))

    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    u = air_u(frame)
    vert = TAKEOFF_VERT[side] + (VERT_END[side] - TAKEOFF_VERT[side]) * u
    y = ANKLE_REST[side].y - piv * (1.0 - math.cos(math.radians(TIP_TAKEOFF))) \
        - z0 * math.sin(math.radians(TIP_TAKEOFF))
    y = y + (rest.y - y) * u
    return Vector((rest.x, y, hip.z - vert))


def arm_refs(arm):
    """量 A01@0 姿态下每根臂骨的**世界 X 轴**，作为 twist 参考向量。

    为什么需要它（这是本支最贵的一课）：
    `A.aim_bone` 用 `rotation_difference` 求最小旋转 —— 它只管"骨长方向指对"，
    **不管 twist**。手臂在本支要甩 187°，最小旋转的 twist 会沿路径**累积**：
    前臂相对父骨的局部欧拉在 f5 单帧跳 **78.54°**（世界朝向只动了 8.87°），
    而 `no_teleport` 是量欧拉的 ⟹ 红。那不是"门禁太严"：欧拉通道是逐分量
    插值的，78° 的 twist 单帧变化就是一次可见的翻腕闪帧。
    修法不是放松判据，而是**给 twist 一个显式参考**（见 `aim_frame`）。
    """
    basis = arm.pose.bones
    return {name: tuple(basis[name].matrix.to_3x3() @ Vector((1.0, 0.0, 0.0)))
            for name in ARM_BONES}


def aim_frame(arm, name, direction, ref):
    """（定点参考法，**已被 `aim_carry` 取代**，保留作对照。）

    把骨的骨长方向指向世界 `direction`，twist 由**固定的**参考向量定：
    ŷ = direction，x̂ = normalize(ref − ŷ(ref·ŷ))，ẑ = x̂ × ŷ。

    它为什么会坏（本支实测）：x̂ 是 `ref` 在 ⊥ŷ 平面上的投影，投影长度
    = sqrt(1 − (ref·ŷ)²)。当 `ref` 扫到与 ŷ **接近平行**时投影长度 → 0，
    x̂ 的方向由数值噪声决定 ⟹ 世界旋转单帧跳。实测 `forearm.R` 在 f10
    **方向只动了 11.29°，世界旋转却动了 144.59°** —— 这是真扭转变，
    不是欧拉表示跳。固定参考法对这个病态没有防御。
    """
    pose_bone = arm.pose.bones[name]
    y_axis = Vector(direction).normalized()
    ref = Vector(ref)
    x_axis = ref - y_axis * ref.dot(y_axis)
    if x_axis.length < 1e-6:
        fallback = Vector((0.0, 1.0, 0.0))
        x_axis = fallback - y_axis * fallback.dot(y_axis)
    x_axis.normalize()
    z_axis = x_axis.cross(y_axis)
    target = Matrix((x_axis, y_axis, z_axis)).transposed().to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def _euler_step(prev, now):
    if prev is None:
        return 0.0
    return max(abs(a - b) for a, b in zip(prev, now))


def _y_penalty(euler):
    """欧拉中间角逼近 ±90°（XYZ 万向节锁）的惩罚项。"""
    return max(0.0, abs(euler[1]) - Y_SAFE) * Y_WEIGHT


def _set_world_quat(arm, name, quat):
    """把该骨的世界朝向整体设为 `quat`（只改朝向，保留当前位置），
    并把 Blender 反解出的 `rotation_euler` 读回来（度）。"""
    pose_bone = arm.pose.bones[name]
    target = quat.to_matrix().to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def aim_carry(arm, name, direction, base_q=None):
    """最小旋转**接力** + 绕骨轴的 **roll 分支搜索**。

    第一段（接力）：从给定基准世界朝向出发，只补"把骨轴摆到目标方向"所需的
    那一个最小旋转。真旋转步 = ∠(基准骨轴, 目标方向)，twist 只做最小变动。
    基准默认取**上一帧已达成朝向**（`base_q` 可覆盖）⟹ 世界旋转逐帧最小变动，
    大角度甩臂时"扭转变"在构造上不会发生（文件头第 4 条）。

    第二段（分支搜索）：`rotation_euler` 是 XYZ 三通道逐分量插值的，
    而 carry 接力**不保证 twist 不累积**：本支 forearm.R 的欧拉中间角 Y 从
    f14 的 +11° 漂到 f30 的 **−88.5°**，直插万向节锁。到那一步真转 2.36° 的
    一帧要欧拉走 35°（放大 15×）。而绕骨轴的 roll 正好能搬动 Y（≈1:1）。
    于是在"步长超过 `ROLL_COMFORT`"或"|Y| 越过 `Y_SAFE`"时扫 roll，
    取 `步长 + |Y| 越界惩罚` 最小的一支 —— **只动滚转、不动方向**，判据不放宽。

    （曾经的"刚性跟随基准" `qd @ ARM_GUARD_Q` 已弃用：探针 `probe_js_base`
    量到基准骨轴与目标方向夹角达 **179.25°**，`rotation_difference` 的轴
    由噪声决定，真世界旋转单帧跳 141°。见文件头第 6 条。）
    """
    pose_bone = arm.pose.bones[name]
    prev_q = base_q if base_q is not None else ARM_QUAT.get(name)
    if prev_q is None:
        prev_q = pose_bone.matrix.to_quaternion()
    want = Vector(direction).normalized()
    y_prev = (prev_q @ Vector((0.0, 1.0, 0.0))).normalized()
    q0 = y_prev.rotation_difference(want) @ prev_q

    prev_e = _PREV_EULER.get(name)
    best_q = q0
    best_e = _unwrap_xyz(prev_e, _set_world_quat(arm, name, q0))
    best_cost = _euler_step(prev_e, best_e) + _y_penalty(best_e)
    best_roll = 0.0
    if prev_e is not None and (best_cost > ROLL_COMFORT
                               or _y_penalty(best_e) > 0.0):
        for roll in _frange(-ROLL_RANGE, ROLL_RANGE, ROLL_COARSE):
            if abs(roll) <= 1e-9:
                continue
            q = Quaternion(want, math.radians(roll)) @ q0
            e = _unwrap_xyz(prev_e, _set_world_quat(arm, name, q))
            cost = _euler_step(prev_e, e) + _y_penalty(e)
            if cost < best_cost - 1e-9:
                best_cost, best_e, best_q, best_roll = cost, e, q, roll
        if best_roll != 0.0:
            for roll in _frange(best_roll - ROLL_COARSE,
                                best_roll + ROLL_COARSE, ROLL_FINE):
                q = Quaternion(want, math.radians(roll)) @ q0
                e = _unwrap_xyz(prev_e, _set_world_quat(arm, name, q))
                cost = _euler_step(prev_e, e) + _y_penalty(e)
                if cost < best_cost - 1e-9:
                    best_cost, best_e, best_q, best_roll = cost, e, q, roll
        # 把骨架**留在最优那一支**上（搜索过程会把它带着走）
        _set_world_quat(arm, name, best_q)
    ARM_ROLL[name] = best_roll
    ARM_QUAT[name] = best_q
    global MAX_ABS_EULER_Y
    MAX_ABS_EULER_Y = max(MAX_ABS_EULER_Y, abs(best_e[1]))
    ROLL_MAX[name] = max(ROLL_MAX.get(name, 0.0), abs(best_roll))
    return best_e


def build_arm_targets():
    """算出蓄力极值 `ARM_BACK`（= guard 与 RAW 的 slerp，幅度 `ARM_BACK_AMP`）。"""
    global ARM_BACK
    ARM_BACK = {k: _slerp(I1.ARM_DIRS[k], ARM_BACK_RAW[k], ARM_BACK_AMP)
                for k in I1.ARM_DIRS}


def arm_dirs(frame):
    """手臂世界方向：护体 →（蓄力）背后 →（起跳）前上略收。

    每段用 `_slerp`（匀角速）+ `_ease_ramp` 定时（两端速度为 0、中段匀速）。
    峰值角速率 = 段角/段长：140°/14 帧 = 10.0、137°/16 帧 = 8.6 °/帧。
    """
    if frame <= T_CROUCH:
        s = _ease_ramp(frame / float(T_CROUCH))
        return {k: _slerp(I1.ARM_DIRS[k], ARM_BACK[k], s)
                for k in I1.ARM_DIRS}
    s = _ease_ramp((frame - T_CROUCH) / float(T_SWING_END - T_CROUCH))
    return {k: _slerp(ARM_BACK[k], ARM_AIR[k], s) for k in I1.ARM_DIRS}


# =============================================================== 姿态生成
def build_pose(arm, frame, record=False):
    """按帧构造完整姿态。（`record=True` 时把踝目标登记进 `TARGETS`）"""
    pose = {
        "pelvis": (TURN.track(PELVIS_RX, frame), 0.0, 0.0),
        "spine_01": (TURN.track(SPINE01_RX, frame), 0.0, 0.0),
        "spine_02": (TURN.track(SPINE02_RX, frame), 0.0, 0.0),
        "chest": (TURN.track(CHEST_RX, frame), 0.0, 0.0),
        "neck": (TURN.track(NECK_RX, frame), 0.0, 0.0),
        "head": (TURN.track(HEAD_RX, frame), 0.0, 0.0),
        "shoulder.L": (TURN.track(SHOULDER_RX, frame), 0.0, 0.0),
        "shoulder.R": (TURN.track(SHOULDER_RX, frame), 0.0, 0.0),
        "toe.L": (0.0, 0.0, 0.0),
        "toe.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, TURN.track(PELVIS_Y_KEYS, frame),
                                  pelvis_at(frame) - 0.900)},
    }
    A.apply_pose(arm, pose)

    # 腿：真双骨 IK（A06/A07 的 `leg_to`）。膝弯方向固定世界 −Y（本支不转身）。
    for side in ("L", "R"):
        target = ankle_target(arm, frame, side)
        if record:
            TARGETS.append((frame, side, tuple(target)))
        TURN.leg_to(arm, pose, side, target, (0.0, -1.0))

    # 足：先钉平到世界水平（rest 朝向），再**绕世界 X 叠 tip 角**。
    # 不用 foot.rx：父链外展角会把它的旋转轴带偏（A01 老坑）。
    tip = TURN.track(TIP_KEYS, frame)
    for side in ("L", "R"):
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        WF.add_world_rx(arm, name, tip)
        pose[name] = _unwrap_xyz(
            _PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    pose.update(A.FIST)
    dirs = arm_dirs(frame)
    # carry 接力：基准 = 上一帧已达成朝向（世界旋转最小变动）+ 绕骨轴 roll 分支搜索
    # （把欧拉通道拉回良态）。见 `aim_carry` 的说明。
    for bone in ARM_BONES:
        pose[bone] = aim_carry(arm, bone, dirs[bone])

    for name, value in pose.items():
        if not name.startswith("@"):
            _PREV_EULER[name] = tuple(value)
    return pose


def measure_pivot(arm):
    """量"鞋底着地点"在踝前方的水平距离（米）。

    取 Idle_01@0 姿态下鞋底最低 6 mm 以内的顶点中 **y 最小**（= 最前）者。
    理由见文件头第 2 条：刚性鞋推离时只能绕**最前端**转，绕球部转会把
    球部之前那截鞋底扎进地面（首版实测 −11.38 mm）。
    """
    out = {}
    for side in ("L", "R"):
        objects = [bpy.data.objects[n] for n in A.FOOT_MESHES[side]
                   if n in bpy.data.objects]
        objects = [obj for obj in objects if obj.hide_viewport is False]
        depsgraph = bpy.context.evaluated_depsgraph_get()
        points = []
        for obj in objects:
            evaluated = obj.evaluated_get(depsgraph)
            mesh = evaluated.to_mesh()
            matrix = evaluated.matrix_world
            points.extend(matrix @ vertex.co for vertex in mesh.vertices)
            evaluated.to_mesh_clear()
        zmin = min(point.z for point in points)
        sole = [point for point in points if point.z <= zmin + 0.006]
        front = min(sole, key=lambda point: point.y)
        out[side] = ANKLE_REST[side].y - front.y
    return out


def calibrate(arm):
    """扫**蓄力段**（0~T_CROUCH）量鞋底 z 区间，解出冻结常数偏移。

    与 A08 同一条思路（整支冻结一个常数），但**必须重扫**：本支蹲深 210 mm ≠ A08 的
    202 mm，且蓄力段的膝弯轨迹不同 ⟹ 蒙皮影响不同。

    截断阈值从 A08 的 ±2 mm 放宽到 ±6 mm，并**登记原因**：本支 R 侧鞋底在蓄力
    段内的极差就有 3.33 mm（A08 是 1.84 mm），2 mm 截断会让 R 侧最低点停在
    −2.32 mm、越出门禁下限。这不是"放宽容差"—— 门禁窗口仍是 [−2, +6]，
    动的是"标定常数能有多大"这个内部安全界，且实际用到的偏移（+3.32 mm）
    远小于 6 mm。代价是 f0→f1 踝 z 有 3.32 mm 的台阶（f0 必须逐位等于 Idle_01@0，
    不能带偏移），量级 0.18% 身高，登记为 `f1_ankle_step_mm`。
    """
    lows = {"L": [], "R": []}
    for frame in range(0, T_CROUCH + 1):
        build_pose(arm, frame)
        low = A.foot_lowest_by_side()
        for side in ("L", "R"):
            lows[side].append(low[side][2])
    out = {}
    for side in ("L", "R"):
        out[side] = max(-0.006, min(0.006, -0.0010 - min(lows[side])))
    return out, lows


# =============================================================== 测量
def _with_action(arm, action):
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    return previous


def sole_series(arm, action, frames):
    """逐帧量左右鞋底各自的最低点（按**具名鞋对象**分侧，不看 x 符号）。"""
    scene = bpy.context.scene
    previous = _with_action(arm, action)
    out = []
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        out.append({side: low[side][2] for side in ("L", "R")})
    if previous is not None:
        arm.animation_data.action = previous
    return out


def ankle_series(arm, action, frames):
    scene = bpy.context.scene
    previous = _with_action(arm, action)
    out = []
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        out.append({side: tuple(A.bone_world(arm, "foot." + side, "head"))
                    for side in ("L", "R")})
    if previous is not None:
        arm.animation_data.action = previous
    return out


# =============================================================== 专属门禁
def jump_assertions(arm, action, samples, idle_mats, sole, target_err):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(s["pelvis"]) for s in samples]
    zs = [p.z for p in pelvis]
    rates = [(zs[i + 1] - zs[i]) * 1000.0 for i in range(len(zs) - 1)]

    # 0) 首帧必须**逐位**等于 `Idle_01@0`（世界矩阵，不是 euler）。
    mats = CR.action_world_matrices(arm, action, 0)
    delta = CR.matrix_delta(mats, idle_mats)
    res["first_frame_delta"] = float("%.3e" % delta)
    res["first_frame_matches_idle_ok"] = delta <= 1e-6

    # 1) **明显预备动作**：下蹲前先反向抬一下（清单「反向预备」）。
    rise = (max(zs[:T_ANTIC_TOP + 1]) - zs[0]) * 1000.0
    res["antic_rise_mm"] = round(rise, 2)
    res["antic_rise_ok"] = 4.0 <= rise <= 15.0

    # 2) **蓄力要肉眼可见**：骨盆沉到 ≤0.64 m 且降幅 ≥180 mm。
    res["pelvis_z_start_mm"] = round(zs[0] * 1000.0, 1)
    res["pelvis_z_crouch_mm"] = round(min(zs) * 1000.0, 1)
    res["crouch_drop_mm"] = round((zs[0] - min(zs)) * 1000.0, 1)
    res["antic_depth_ok"] = (min(zs) <= 0.64
                             and (zs[0] - min(zs)) * 1000.0 >= 180.0)

    # 2b) 蓄力路径：z 单调不增 + 水平位移有界（A08 踩坑 3 的口径）。
    seg = [i for i, f in enumerate(frames) if T_ANTIC_TOP <= f <= T_CROUCH]
    zseg = [zs[i] for i in seg]
    res["crouch_monotone_ok"] = all(zseg[k + 1] <= zseg[k] + 1e-9
                                    for k in range(len(zseg) - 1))
    hdev = max(math.hypot(pelvis[i].x - pelvis[0].x, pelvis[i].y - pelvis[0].y)
               for i in seg) * 1000.0
    res["crouch_horizontal_mm"] = round(hdev, 2)
    res["crouch_path_ok"] = hdev <= 25.0

    # 3) **蓄力段脚钉死**（骨架世界坐标口径，同 A01/A06/A07/A08）。
    travel = {}
    for side in ("L", "R"):
        pts = [Vector(samples[i]["foot." + side]) for i in seg]
        travel[side] = max((p - pts[0]).length for p in pts) * 1000.0
    res["feet_pinned_mm"] = {k: round(v, 3) for k, v in travel.items()}
    res["feet_pinned_ok"] = all(v <= 3.0 for v in travel.values())

    # 4) **爆发**：爆发段**平均**骨盆 z 速率 ≥ 45 mm/帧（清单计划原文口径，
    #    不是"峰值" —— 峰值可以把一个 12 帧的软爆发也判绿）。
    #    匀加速下 avg = Δ/T 恒成立 ⟹ 这条判据等价于"Δ/T ≥ 45"。
    idx = [i for i in range(len(rates))
           if frames[i + 1] <= T_TAKEOFF and frames[i + 1] > T_CROUCH]
    launch_avg = sum(rates[i] for i in idx) / float(len(idx))
    res["launch_avg_rate_mm_per_frame"] = round(launch_avg, 2)
    res["launch_speed_ok"] = launch_avg >= 45.0
    cidx = [i for i in range(len(rates))
            if frames[i + 1] <= T_CROUCH and frames[i + 1] > T_ANTIC_TOP]
    crouch_avg = -sum(rates[i] for i in cidx) / float(len(cidx))
    res["crouch_avg_rate_mm_per_frame"] = round(crouch_avg, 2)
    res["launch_over_crouch_ratio"] = round(launch_avg / max(1e-6, crouch_avg), 2)

    # 4b) **离地瞬间的竖速 = 起跳初速**（由弹道段实测斜率反推，与解析值比对）。
    #     离散一阶差分 z(1)−z(0) = v₀ − ½g（一帧），所以反推瞬时速度必须
    #     **补回那半帧重力**，否则恒偏低 ½g = 1.36 mm/帧 —— 那不是容差问题，
    #     是"用一阶差分当导数"的口径错。
    v_analytic = TAKEOFF_SPEED * 1000.0
    v_measured = rates[T_TAKEOFF] + 0.5 * G_PER_FRAME * 1000.0
    res["takeoff_speed_mm_per_frame"] = round(v_measured, 2)
    res["takeoff_speed_mps"] = round(v_measured * A.FPS / 1000.0, 3)
    res["takeoff_speed_analytic_mm_per_frame"] = round(v_analytic, 2)
    res["takeoff_speed_matches_analytic_ok"] = \
        abs(v_measured - v_analytic) <= 0.5

    # 5) **离地**：末段双脚（按具名鞋分侧）离地 ≥60 mm。
    air = [i for i, f in enumerate(frames) if f >= T_TAKEOFF + 1]
    low_air = {side: min(sole[i][side] for i in air) for side in ("L", "R")}
    res["airborne_clearance_mm"] = {k: round(v * 1000.0, 1)
                                    for k, v in low_air.items()}
    res["takeoff_airborne_ok"] = all(v * 1000.0 >= 60.0
                                     for v in low_air.values())
    res["airborne_frames"] = len(air)

    # 6) **触地窗口内贴地**（通用门禁是全段扫，本支必须按窗口判 —— 脚会飞出去）。
    ground = [i for i, f in enumerate(frames) if f <= T_TAKEOFF]
    gmin = min(min(sole[i]["L"], sole[i]["R"]) for i in ground) * 1000.0
    gmax = max(max(sole[i]["L"], sole[i]["R"]) for i in ground) * 1000.0
    res["ground_min_mm"] = round(gmin, 2)
    res["ground_max_mm"] = round(gmax, 2)
    res["ground_contact_ok"] = -2.0 <= gmin <= 6.0

    # 7) **四肢略收**：离地后膝弯角继续增加 ≥20°。
    bend = CR.knee_series(arm, action, frames)
    res["knee_bend_start_deg"] = {s: round(bend[0][s], 2) for s in ("L", "R")}
    res["knee_bend_crouch_deg"] = {s: round(bend[T_CROUCH][s], 2)
                                   for s in ("L", "R")}
    res["knee_bend_takeoff_deg"] = {s: round(bend[T_TAKEOFF][s], 2)
                                    for s in ("L", "R")}
    res["knee_bend_end_deg"] = {s: round(bend[-1][s], 2) for s in ("L", "R")}
    tuck = {s: bend[-1][s] - bend[T_TAKEOFF][s] for s in ("L", "R")}
    res["tuck_delta_deg"] = {k: round(v, 2) for k, v in tuck.items()}
    res["tuck_ok"] = all(v >= 20.0 for v in tuck.values())

    # 8) IK 是否到位（踝是否真的落在目标上 —— 腿最长 0.822 m，够不到会静默截断）。
    res["ankle_target_error_mm"] = round(target_err * 1000.0, 3)
    res["ik_reach_ok"] = target_err * 1000.0 <= 5.0

    # 9) 原地：骨盆水平行程（清单 §0.4「防自带位移」）。
    hspan = max(math.hypot(p.x - pelvis[0].x, p.y - pelvis[0].y)
                for p in pelvis) * 1000.0
    hnet = math.hypot(pelvis[-1].x - pelvis[0].x,
                      pelvis[-1].y - pelvis[0].y) * 1000.0
    res["pelvis_span_mm"] = round(hspan, 2)
    res["pelvis_net_mm"] = round(hnet, 3)
    res["pelvis_in_place_ok"] = hspan <= 60.0

    # 10) 末 6 帧角度增量绝对值单调收敛（A06 踩坑 4 的口径）。
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

    # 11) 力量传导链（脚→腿→髋→腰→肩→手，六段全非零）。
    #     本支**脚会离地**，所以脚段按"蹬地行程"判、不按钉死判（清单注意第二条）。
    moved, swing, nonzero = {}, {}, {}
    for segment, names in (("foot(蹬地)", ("foot.L", "foot.R")),
                           ("pelvis", ("pelvis",)),
                           ("chest", ("chest",)),
                           ("shoulder", ("shoulder.L", "shoulder.R")),
                           ("hand", ("hand.L.tail", "hand.R.tail"))):
        big = 0.0
        for name in names:
            pts = [Vector(s[name]) for s in samples]
            big = max(big, max((p - pts[0]).length for p in pts) * 1000.0)
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
                             and all(v >= 15.0 for v in swing.values())
                             and all(v >= 1.0 for v in nonzero.values()))

    # 12) 给 A11 的交接真值。
    last = samples[-1]
    res["takeoff_ankle_mm"] = {
        side: [round(v * 1000.0, 1) for v in samples[T_TAKEOFF]["foot." + side]]
        for side in ("L", "R")}
    res["end_ankle_mm"] = {
        side: [round(v * 1000.0, 1) for v in last["foot." + side]]
        for side in ("L", "R")}
    res["end_pelvis_z_mm"] = round(zs[-1] * 1000.0, 1)
    res["apex_rise_m"] = round(APEX_RISE, 4)
    res["rise_fraction_of_apex"] = round(
        (zs[-1] - TAKEOFF_PELVIS_Z) / APEX_RISE, 4)
    return res


# =============================================================== 主流程
def main():
    global ANKLE_REST, Z_OFF, PIVOT_FWD, TAKEOFF_ANKLE_Z, TAKEOFF_VERT, ARM_REF
    global MAX_ABS_EULER_Y

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    build_arm_targets()

    if "Idle_01" not in bpy.data.actions:
        print("JS_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    I1.idle_pose(arm, 0.0)
    ARM_REF = arm_refs(arm)
    ANKLE_REST = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                  for side in ("L", "R")}
    A.report("JS_ANKLE_REST", {side: [round(v * 1000.0, 2) for v in ANKLE_REST[side]]
                               for side in ANKLE_REST})
    PIVOT_FWD = measure_pivot(arm)
    A.report("JS_PIVOT", {"fwd_mm": {k: round(v * 1000.0, 1)
                                     for k, v in PIVOT_FWD.items()}})

    Z_OFF, lows = calibrate(arm)
    for side in ("L", "R"):
        rest = ANKLE_REST[side]
        piv = PIVOT_FWD[side]
        z0 = rest.z + Z_OFF[side]
        tip = math.radians(TIP_TAKEOFF)
        TAKEOFF_ANKLE_Z[side] = piv * math.sin(tip) + z0 * math.cos(tip)
        TAKEOFF_VERT[side] = TAKEOFF_PELVIS_Z - TAKEOFF_ANKLE_Z[side]
    A.report("JS_CALIBRATION", {
        "z_off_mm": {k: round(v * 1000.0, 3) for k, v in Z_OFF.items()},
        "crouch_sole_range_mm": {k: [round(min(lows[k]) * 1000.0, 2),
                                     round(max(lows[k]) * 1000.0, 2)]
                                 for k in ("L", "R")},
        "crouch_sole_span_mm": {k: round((max(lows[k]) - min(lows[k])) * 1000.0, 2)
                                for k in ("L", "R")},
        "f1_ankle_step_mm": {k: round(abs(Z_OFF[k]) * 1000.0, 3)
                             for k in ("L", "R")},
        "predicted_min_mm": round(min(min(lows[k]) + Z_OFF[k]
                                      for k in ("L", "R")) * 1000.0, 2),
    })
    A.report("JS_TAKEOFF_GEOM", {
        "takeoff_ankle_z_mm": {k: round(v * 1000.0, 1)
                               for k, v in TAKEOFF_ANKLE_Z.items()},
        "takeoff_vert_mm": {k: round(v * 1000.0, 1)
                            for k, v in TAKEOFF_VERT.items()},
        "hint": "vert = 0.920 − 踝高；空中段这条竖距收缩到 VERT_END",
    })
    del TARGETS[:]

    first = I1.idle_pose(arm, 0.0)
    _PREV_EULER.clear()
    for name, value in first.items():
        if not name.startswith("@"):
            _PREV_EULER[name] = tuple(value)
    # carry 接力的起点：f0 的**已达成世界朝向**（= Idle_01@0）。不 seed 的话
    # f1 会以"父链带过来的静止朝向"为起点，等价于退回 `aim_bone`（会翻）。
    ARM_QUAT.clear()
    ARM_ROLL.clear()
    for name in ARM_BONES:
        ARM_QUAT[name] = arm.pose.bones[name].matrix.to_quaternion()

    keyframes = [(0, first)]
    MAX_ABS_EULER_Y = 0.0
    ROLL_MAX.clear()
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, build_pose(arm, frame, record=True)))
    A.report("JS_ARM_ROLL", {
        "max_abs_euler_y_deg": round(MAX_ABS_EULER_Y, 2),
        "max_abs_roll_deg": {k: round(ROLL_MAX.get(k, 0.0), 1)
                             for k in ARM_BONES},
        "hint": "roll = 绕骨轴自转（只改滚转、不改骨轴方向）；Y = 欧拉中间角",
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "基础移动",
        "note": ("起跳：反向预备 → 深蹲蓄力 210 mm → 绕鞋底前端碾地爆发"
                 "（6 帧幂律 τ^1.5 升 300 mm，起跳初速 4.50 m/s）→ 离地后按弹道继续"),
        "antic_frame": T_CROUCH,
        "hit_frame": None,
        "cancel_frame": None,
        "hitstop_frames": 0,
        "root_motion_m": [0.0, 0.0],
        "crouch_drop_m": 0.210,
        "launch_frames": LAUNCH_FRAMES,
        "launch_rise_m": round(LAUNCH_RISE, 3),
        "takeoff_frame": T_TAKEOFF,
        "takeoff_pelvis_z_m": TAKEOFF_PELVIS_Z,
        "takeoff_speed_mps": round(TAKEOFF_SPEED * A.FPS, 3),
        "apex_rise_m": round(APEX_RISE, 4),
        "link_next": "A11 Jump_Up（从 f36 的 82.4% 弹道高度继续上升到顶点）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "START": 0, "ANTIC_TOP": T_ANTIC_TOP, "ANTIC_END": T_CROUCH,
        "LAUNCH": T_CROUCH, "HEELS_UP": 17, "TAKEOFF": T_TAKEOFF,
        "AIRBORNE": T_TAKEOFF, "TUCK_END": T_TUCK, "SETTLE_END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # foot_probe 置空：通用门禁的"脚位移 ≤3 mm"默认量 toe 骨，本支脚要走要飞，
    # 由专属 `feet_pinned_ok`（蓄力段按踝判）与 `takeoff_airborne_ok` 接管。
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report["common_ground_min_all_frames_mm"] = report.get("ground_min_mm")

    idle_mats = CR.action_world_matrices(arm, bpy.data.actions["Idle_01"], 0)
    sole = sole_series(arm, action, list(range(0, TOTAL + 1)))
    ankles = ankle_series(arm, action, list(range(0, TOTAL + 1)))

    target_err = 0.0
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    for i, frame in enumerate(range(0, TOTAL + 1)):
        for side in ("L", "R"):
            if frame == 0:
                continue
            target_err = max(target_err,
                             (Vector(ankles[i][side])
                              - pair[(frame, side)]).length)

    report.update(jump_assertions(arm, action, samples, idle_mats, sole,
                                  target_err))
    report["meta"] = meta
    # `no_teleport` 不带 `_ok` 后缀，早期的 `endswith("_ok")` 过滤会**静默漏掉它**
    # —— 首版就是这样在 failed=[] 的情况下藏了一个 339° 的翻腕。这里显式并入。
    failed = sorted(k for k, v in report.items()
                    if (k.endswith("_ok") or k == "no_teleport") and v is not True)
    report["failed"] = failed
    A.report("JUMPSTART_REPORT", report)

    if not SKIP_RENDER:
        JUMP_SIDE = ("side", (4.6, 0.0, 1.45), (0.0, 0.0, 1.45), 3.60,
                     (760, 1200))
        JUMP_FRONT = ("front", (0.0, -5.0, 1.45), (0.0, 0.0, 1.45), 3.60,
                      (760, 1200))
        JUMP_3Q = ("three_quarter", (3.2, -3.6, 1.55), (0.0, 0.0, 1.35), 3.60,
                   (760, 1200))
        A.render_pose_sheet(arm, action, [0, 3, 9, 14, 17, 20, 24, 28, 32, 36],
                            "jumpstart", views=(JUMP_SIDE,))
        A.render_pose_sheet(arm, action, [0, 3, 14, 20, 26, 36], "jumpstart",
                            views=(JUMP_FRONT,))
        A.render_pose_sheet(arm, action, [14, 20, 36], "jumpstart",
                            views=(JUMP_3Q,))
    A.save_project()
    A.export_glb(arm)
    print("JUMPSTART_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("JUMPSTART_FAILURE " + traceback.format_exc())
