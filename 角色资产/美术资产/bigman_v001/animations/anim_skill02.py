"""anim_skill02 —— C10 `Skill_02` 抱摔（C 族第十支，**四段：抓取 / 抱起 / 砸地 / 收招**）。

=============================================================================
清单原文
=============================================================================
「抓取后抱起敌人砸地，重点制作**两角色同步动画**。」

=============================================================================
第 0 件 —— 「两角色同步」在本工程怎么落地（唯一没有先例的维度）
=============================================================================
本工程只有一套 `Character_Rig`，做不出"两个人同时演"。所以「同步」沿 C04 已立的
约定执行：**由受招方锚点的世界坐标登记**（`grab_point_m` / `carry_point_m` /
`slam_point_m` 逐相位登记），引擎据此把第二角色摆到手上。thrower 侧要保证的只有
一件事：**手不许漂** —— 手一漂，第二角色就在手里抖。

⟹ 本支的核心门禁是 `carry_steady_ok`（抱住窗口内**双手世界位置漂移 ≤ 3 mm**），
它由 `arm_seat`（三骨链位置逆解，把 `hand.tail` 精确钉在世界点上）**构造性**满足；
`C10PROBE` 实测指尖误差 **0.00 mm**。

=============================================================================
第 1 件 —— 分段与时间轴（`TOTAL = 114` @60fps = 1.900 s）
=============================================================================
    (0)─抓取 6f─>(6)─抱起 26f─>(32 顶点)─顶住 18f─>(50)─砸地 18f─>(68 命中)
        ─命停 3f─>(70)─收招 38f─>(108 定)─6f─>(114)

    抓取  6 帧 = 0.100 s  ← 清单计划「抓取 ≤ 6f（贴身技，比肩撞更快）」
    抱起 26 帧 = 0.433 s  ← 指尖 z 0.98 → 1.70 m（**抬升 720 mm**）
    顶住 18 帧 = 0.300 s  ← 清单计划「举起定住 0.3~0.5 s」
    砸地 18 帧 = 0.300 s  ← 指尖 z 1.70 → 0.35 m，**加速下落 + 触地瞬间停**
    命停  3 帧 = 0.050 s  ← §0.1 的 2~4 帧区间
    收招 38 帧 = 0.633 s  ← 单向减速回「战斗待机」

=============================================================================
第 2 件 —— 首帧 = `Idle_01@0`，逐位（`SEAM_TOL = 1e-6`）；末帧有意不回 Idle
=============================================================================
同 C07/C08/C09：腿走 `leg_seat`（三维 IK），Idle 腿走平面解析，世界方向一致但
欧拉滚转不逐位一致 ⟹ 强行「末帧 = Idle」会被逐位门禁打回。末帧登记 `end_pose_deg`
（= 战斗待机躯干真值），由 `tail_settle_ok` 用 0.05° 公差盯着「实测 == 登记」。

=============================================================================
第 3 件 —— 手臂**全程位置逆解**（本支与 C09 最大的形态差异）
=============================================================================
C09 的手臂是"方向链 + 测地线 slerp"；本支对手要**钉在世界点上**（否则第二角色抖），
所以全程走 `G4.arm_seat`：

    f ≤ GRAB_END         ref=None（Idle 基准）—— f0 与 Idle 同源
    GRAB_END < f ≤ CARRY_END   ref = **抓取帧就地登记的基准**（`ARM_REF`）
    CARRY_END < f        ref = **抱起顶点就地登记的基准**（二次登记）

★ 为什么要**二次登记**：`aim_bone_ref` 用「基准方向 → 当前方向」的**最小旋转**带滚转，
   当两方向接近反向（180°）时该反解病态。抱起顶点到手触地，上臂方向要跨约 170°
   ⟹ 在顶点处重新取一次基准，把这段的参考角差压到 ~90° 以内。
   （C07 教训 2 `aim_bone_ref` 在反向点滚转病态的同一病灶，这次是**提前预防**。）

=============================================================================
第 4 件 —— 砸地剖面：**加速下落 + 触地瞬间停**（清单计划 §2 第 4 条的落地口径）
=============================================================================
清单计划原话是「z 速度单调递减到 0（下砸加速下落、触地瞬间停）」。这两半在字面上
互相矛盾（"加速"与"递减"同时成立只有当 z 轴朝下取符号）。本支的**取舍与量化**：

    `slam_descent_ok`  砸地段指尖 z **全程单调下降**（无回弹）
    `slam_speed_ok`    下降速度**前 2/3 单调递增**（加速下落），
                       **触地帧骤停**：`s[-1] ≤ 12 mm` 且 `s[-1] ≤ 0.15 × max(s)`

即把「单调递减到 0」读成「**|z 速度| 在触地帧骤降至 ~0**」，与"触地瞬间停"一致。
速度剖面用显式速度表 `SLAM_SPEEDS`（不是 `u^p`）——`u^p` 的首帧同样会"卡住"
（C09 第 3 件），而速度表两头都能直接指定。

=============================================================================
第 5 件 —— 脚：拖行推进 + **抱住期间必须钉住**（本支自立的替代判据）
=============================================================================
清单计划撤下了 `no_foot_slide_*`（Root Motion 动作，脚在地上"拖"是前冲/下沉的
视觉本体），但**不许裸撤**。本支补一条**新的、会失败的**判据：

    `carry_feet_planted_ok`  [GRAB_END, CARRY_END] 内**踝的水平位移 ≤ 3 mm**

物理根据：举着一个成年人的重量时，脚下必须扎稳；此时身体只做竖直的"顶"。
构造做法：`pelvis_pos` 在 `[GRAB_END, CARRY_END]` 上 **y 恒定**，踝 = 踝_0 + 0.90·py，
y 恒定 ⟹ 踝恒定（实测 0.000 mm）。抓取段与砸地段仍允许拖行（那是发力段）。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_skill02.py
    SKIP_RENDER=1 只跑门禁（迭代用）；C10_TRACE=1 打逐帧轨迹；
    C10_SOLE_DIAG=1 打贴地闭环迭代过程。
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Quaternion, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402
import anim_run_stop as RS      # noqa: E402
import anim_jump_start as JS    # noqa: E402
import anim_grab04 as G4        # noqa: E402

NAME = "Skill_02"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
XOFF = {"L": 1.0, "R": -1.0}          # +X = 角色左（`rig_axis_map.md`）


def _env_f(key, default):
    return float(os.environ[key]) if os.environ.get(key) else float(default)


def _env_i(key, default):
    return int(os.environ[key]) if os.environ.get(key) else int(default)


def _env_s(key, default):
    return os.environ.get(key) or str(default)


def _ramp(weights):
    """把「逐步权重表」变成**归一化累积曲线** `u → 进度`（两端逐位 0 / 1）。

    权重表是速度的**相对值**；归一化后总量恒为 1 ⟹ 改形状不改总位移。
    `u = 1` 时 `i = n−1, frac = 1`，返回累积末值 1.0，不会溢出索引。
    """
    total = float(sum(weights))
    cum, cumsum = 0.0, []
    for weight in weights:
        cum += float(weight)
        cumsum.append(cum / total)

    def curve(u):
        u = max(0.0, min(1.0, u))
        n = len(cumsum)
        x = u * n
        i = min(n - 1, int(x))
        prev = cumsum[i - 1] if i > 0 else 0.0
        return prev + (cumsum[i] - prev) * (x - i)
    return curve


SOLE_DIAG = os.environ.get("C10_SOLE_DIAG") == "1"
SOLE_DIAG_FRAMES = frozenset(
    int(v) for v in (os.environ.get("C10_SOLE_DIAG_FRAMES")
                     or "6,32,50,68,70,90,114").split(",") if v.strip())

# ---------------------------------------------------------------- 帧预算
TOTAL = _env_i("C10_TOTAL", 114)          # 1.900 s @60fps
ANTIC = _env_i("C10_ANTIC", 3)            # 前摇末（蓄力微收）
GRAB_END = _env_i("C10_GRAB", 6)          # 抓取相位末 —— `grab_time_ok` ≤ 6
LIFT_TOP = _env_i("C10_LIFTOP", 32)       # 抱起顶点（登记 `carry_point_m`）
CARRY_END = _env_i("C10_CARRYEND", 50)    # 顶住结束
HIT = _env_i("C10_HIT", 68)               # 砸地命中帧（登记 `slam_point_m`）
HOLD = _env_i("C10_HOLD", 3)              # 命停 3 帧（§0.1 的 2~4）
HOLD_END = HIT + HOLD - 1                 # 70
RETURN_START = HOLD_END + 1               # 71
SETTLE = _env_i("C10_SETTLE", 108)        # 收招落定（此后逐位静止）
CANCEL = _env_i("C10_CANCEL", 110)        # 可取消帧
POST_POW = _env_f("C10_POSTPOW", 1.25)    # 收招缓动 q = 1 − (1−u)^p

# ---------------------------------------------------------------- 锚点（世界米）
# ★ 第 9 件 —— 抱起点的高度**不是**"越高越好"（渲染目检教训）：
#   首版 `CARRY_Y = −0.20 / CARRY_Z = 1.70` 让手落在**肩正上方 0.33 m**（手→肩方向与
#   +Z 夹角仅 13°）⟹ 渲染出来是「双手举过头顶」= 举重/欢呼，不是"抱着一个人"（副
#   视图上整个人像在举杠铃）。抱起成年人的正确形态是手在**身前上方、肘下压**：
#   改成 `CARRY_Y = −0.46 / CARRY_Z = 1.58`（夹角 57°）。为保住 600 mm 抬升门禁，
#   抓取点同时下调到 0.90 m（抓腰腹而非胸）——抬升 = 680 mm，留 80 mm 余量。
#   新增 `carry_arm_posture_ok` 把这条**量化地盯着**（夹角 ≥ 45°），防回归。
GRAB_Y = _env_f("C10_GRAB_Y", -0.64)
GRAB_Z = _env_f("C10_GRAB_Z", 0.90)
CARRY_Y = _env_f("C10_CARRY_Y", -0.46)
CARRY_Z = _env_f("C10_CARRY_Z", 1.58)
SLAM_Y = _env_f("C10_SLAM_Y", -0.78)
SLAM_Z = _env_f("C10_SLAM_Z", 0.35)
SPREAD = {"grab": 0.16, "carry": 0.20, "slam": 0.16}
# ★ 砸地段手路径的中间关键点（第 6 件）：**必须绕过肩关节**。
#   若直接把「抱起点」直线插到「砸地点」，路径中段会穿过肩膀 —— 第 1~2 轮实测
#   第 60 帧手距肩仅 78 mm，低于臂长下限 |l1−l23| = 170 mm ⟹ 三骨链解出
#   上臂与前臂**共线对折 180°**的奇点，骨世界朝向单帧跳 100.7°（`world_step_ok` 红）。
#   物理上正确的形态本来就是**弧线**：抱着的人先被甩到身前（y 更前、z 略降），
#   再顺势抡下去。所以中间插一个「甩出去」点，肘部离肩最近也有 ~300 mm。
#   中段 y 取 −0.95 而不是 −1.00：再远一些手距肩会逼近 0.55 m（ratio 0.85），
#   而中段的肩还在向下向前移动的途中，留给后续帧的余量就不够了。
SLAM_MID_Y = _env_f("C10_SLAM_MID_Y", -0.95)
SLAM_MID_Z = _env_f("C10_SLAM_MID_Z", 1.12)

# ---------------------------------------------------------------- 骨盆世界轨迹
PY_COIL = _env_f("C10_PY_COIL", 0.030)        # 前摇：微后坐
PZ_COIL_DROP = _env_f("C10_PZ_COIL", 0.060)   # 前摇：下沉
PY_GRAB = _env_f("C10_PY_GRAB", -0.18)        # 抓取：向前踏进 180 mm
PZ_GRAB = _env_f("C10_PZ_GRAB", 0.770)        # 抓取：压低下盘
PY_CARRY = PY_GRAB                            # ★ 抱起段 y 恒定 ⟹ 踝钉住（第 5 件）
PZ_CARRY = _env_f("C10_PZ_CARRY", 0.855)      # 抱起顶点：直起腿
PZ_CARRY_SAG = _env_f("C10_PZ_SAG", 0.005)    # 顶住期膝盖微微让一点（不破手钉）
PY_HIT = _env_f("C10_PY_HIT", -0.400)         # 砸地：前压 400 mm
# ★ 砸地沉髋量也是从可达性反推的（第 9 件）：躯干前屈压到 40° 后肩抬高了约 100 mm，
#   手就够不到 0.35 m 的落点（实测超 30 mm、ratio 1.046）。把髋再沉 120 mm
#   （肩随之降低）即可 —— 且**更低的下盘本身更符合"砸"的发力**，
#   同时腿更弯 ⟹ `leg_ratio` 反而更松（探针：pz 0.52 → 0.56、pz 0.60 → 0.67）。
PZ_HIT = _env_f("C10_PZ_HIT", 0.500)
PY_END = _env_f("C10_PY_END", -0.380)         # 末帧净 Root Motion 380 mm
MOMENTUM_MM = _env_f("C10_MOMENTUM", 20.0)    # 命停期骨盆继续下压的量
ANKLE_LAG = _env_f("C10_LAG", 0.90)           # 踝随骨盆拖行系数（全段恒定）

# ★ 抓取推进的**逐步权重**（第 7 件）：手要从「胸前戒备」（距肩仅 ~210 mm）伸到
#   0.64 m 前的抓取点。贴身半径小 ⟹ 同样的线位移会换来大得多的**角**位移：
#   第 1~2 轮用 `accel()`（快出发）时首步就走掉 47%、252 mm，`hand.R` 单帧世界转角
#   48.65°（`world_step_ok` 红）。改成**权重随半径递增**（半径沿路径 0.21 → 0.42 m
#   近似线性）⟹ 每帧角步长被拉平到 ~15°。
#   权重 [8,11,14,17,21,24] 对总位移 530 mm 给出 45/61/78/95/117/134 mm 的步长；
#   再往上加会把 f0→f1 的 euler 步长顶到 24.56°（`no_teleport` 上限 25°）——
#   **起手那一步的角步长最大，因为此刻手距肩只有 ~210 mm**（角步长 = 线步长 / 半径）。
GRAB_WEIGHTS = [float(v) for v in
                _env_s("C10_GRAB_W", "8,11,14,17,21,24").split(",")]
assert len(GRAB_WEIGHTS) == GRAB_END, "抓取权重数必须等于抓取段帧数"
grab_ramp = _ramp(GRAB_WEIGHTS)

# 砸地速度表（相对值，逐帧）。**前 12 帧单调递增**（加速下落），
# 后 6 帧骤降（触地瞬间停）—— 见文件头第 4 件。
# ★ 表只被**归一化**后使用 ⟹ 改数值只改形状。首版峰值 190/1388（峰值步长 184.8 mm）
#   在 f62 把 `forearm.L` 顶到 euler 27.09° > 25°；压到约 2 倍均值即可（见下）。
SLAM_SPEEDS = [float(v) for v in _env_s(
    "C10_SLAM_SPEEDS",
    "42,47,52,58,64,71,79,88,98,108,118,128,120,92,60,32,13,4").split(",")]
assert len(SLAM_SPEEDS) == HIT - CARRY_END, "速度表长度必须等于砸地段帧数"

# ---------------------------------------------------------------- 躯干轨道（度）
# f0 由 `patch()` 回填 `Idle_01@0` 真值（禁手写）。
# ★ 砸地帧的前屈幅度是从渲染图下调的（第 9 件）：首版 pelvis 22 / spine 12.5×2 /
#   chest 15 累计 ~62°，侧视图读成「鞠躬捡东西」。压到 14/8×2/10（累计 ~40°）——
#   前压感还在，但上身不再折成直角。
PELVIS_RX = [(0, 0.0), (ANTIC, 6.0), (GRAB_END, 10.0), (LIFT_TOP, 2.0),
             (CARRY_END, 0.0), (HIT, 14.0)]
SPINE01_RX = [(0, 0.0), (ANTIC, 3.0), (GRAB_END, 5.0), (LIFT_TOP, 2.0),
              (CARRY_END, 1.0), (HIT, 8.0)]
SPINE02_RX = list(SPINE01_RX)
CHEST_RX = [(0, 0.0), (ANTIC, 3.0), (GRAB_END, 5.0), (LIFT_TOP, 2.0),
            (CARRY_END, 1.0), (HIT, 10.0)]
# ★ 头颈：抱起点要**仰头看**敌人（rx<0 = 后仰），砸地帧**低头**跟着砸下去。
#   但砸地帧不能把下巴压到胸口（首版 neck +12 / head +8 配上 40° 前屈，渲染读成
#   "鞠躬"）⟹ 压到 neck +2 / head −2：目视落点、下颌微收，躯干自己在发力。
NECK_RX = [(0, 0.0), (ANTIC, -5.0), (GRAB_END, -8.0), (LIFT_TOP, -18.0),
           (CARRY_END, -16.0), (HIT, 2.0)]
HEAD_RX = [(0, 0.0), (ANTIC, -3.0), (GRAB_END, -5.0), (LIFT_TOP, -12.0),
           (CARRY_END, -10.0), (HIT, -2.0)]
# ★ 肩：抬起（rx>0）/ 压下（rx<0）。抱起点手臂过头 ⟹ 肩上耸。
SHOULDER_L_RX = [(0, 0.0), (ANTIC, -8.0), (GRAB_END, -10.0), (LIFT_TOP, 10.0),
                 (CARRY_END, 8.0), (HIT, -12.0)]
SHOULDER_R_RX = list(SHOULDER_L_RX)

RX_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
            "shoulder.L", "shoulder.R")
RZ_BONES = ("shoulder.L", "shoulder.R")
END_ROT = {}                   # 收招末姿 = `Idle_01@0` 的躯干真值

HITSTOP_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "shoulder.L", "shoulder.R",
                 "upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R")

# ---------------------------------------------------------------- 门禁阈值
SOLE_RANGE_MM = (-2.0, 6.0)
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
GRAB_TIME_MAX = _env_f("C10_GRAB_TIME", 6.0)
LIFT_MIN_MM = _env_f("C10_LIFT_MIN", 600.0)          # 抱起抬升
HIP_DRIVE_MIN_MM = _env_f("C10_HIPDRIVE_MIN", 60.0)  # 抱起时本体自己也要起来
CARRY_DRIFT_MAX_MM = _env_f("C10_CARRY_DRIFT", 3.0)  # ★ 本支核心
PLANT_MAX_MM = _env_f("C10_PLANT_MAX", 3.0)
SLAM_FLOOR_MM = _env_f("C10_SLAM_FLOOR", -20.0)      # 对手落点不许穿地
SLAM_STOP_MAX_MM = _env_f("C10_SLAM_STOP", 12.0)     # 触地瞬间停
SLAM_STOP_RATIO = _env_f("C10_SLAM_RATIO", 0.15)
ROOT_MAX_MM = _env_f("C10_ROOT_MAX", 900.0)
ROOT_Z_MAX_MM = _env_f("C10_ROOT_Z_MAX", 500.0)
ROOT_Z_MIN_MM = _env_f("C10_ROOT_Z_MIN", 10.0)
END_POSE_TOL_DEG = _env_f("C10_END_TOL", 0.05)
# 抱起形态：肩→手方向与竖直方向的最小夹角（第 9 件）
ARM_UP_MIN_DEG = _env_f("C10_ARM_UP_MIN", 45.0)
# 砸地段：手必须领先肩（世界 −Y）至少这么多毫米
SLAM_FRONT_MIN_MM = _env_f("C10_SLAM_FRONT_MIN", 150.0)
# ★ 臂骨就地重取基准的触发阈值（度）：`aim_bone_ref` 的滚转在「当前方向 → 参考
#   方向」接近 180° 时病态（反解轴由垂直分量定，分量趋零时方向乱翻）。本支砸地
#   段上臂方向要从 +Z 扫到 −Z（跨约 170°），必然会踩到那一点 ⟹ 用「方向偏离参考
#   超过 75° 就重取基准」把每段的参考角差**自适应地**压在 75° 以内。
#   重取是**连续**的：新基准 = 当前骨矩阵、新参考方向 = 当前方向 ⟹ 同一方向下
#   `aim_bone_ref` 逐位等于基准，零台阶。
ARM_REF_MAX_DEG = _env_f("C10_REF_MAX", 75.0)
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
# ★ 起手接合（第 8 件）：f1..`ARM_EASE_END` 把六根臂骨从 `Idle_01@0` 的**自身**
#   手臂欧拉平滑接到 `arm_seat` 的解上（`w = smooth((f−1)/(END−1))`，f1 权重 0）。
#   为什么必要：`arm_seat` 把 `hand` 方向**强行取成前臂方向**（腕直），而 Idle 的
#   戒备姿是**屈腕**的 ⟹ 第 1 帧腕部被一次性掰直：实测 `hand.R` 欧拉单帧跳
#   24.558°（`no_teleport` 上限 25°，只剩 0.44° 余量 —— 不是错，是太脆）。
#   ★ 只在**起手段**做：`GRAB_END = 6 > ARM_EASE_END` ⟹ 抓取帧起逆解逐位精确，
#     三个受招方锚点（f6/f32/f68）读的都是未接合的解，不受影响。
ARM_EASE_END = _env_i("C10_ARM_EASE", 5)

# ---------------------------------------------------------------- 观测量
SEAM_POSE = {}
SEAM_EULER = {}
Z_SEAM = 0.0
ANKLE_0 = {}
IDLE_POSE = {}
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
IDLE_HAND = {}
IDLE_ELBOW = {}
ARM_LEN = {}
ARM_REF = {}
ARM_REF_STAGE = ""
_HIT_FROZEN = {}
HAND_TARGET = {}
ANCHOR = {}
ARM_CLAMP = {}
E0 = {}
E_END = {}
E_END_UNW = {}
SRC_MATS = {}
LOG = {}


def _hold(frame):
    return HIT < frame <= HOLD_END


def q_of(frame):
    """收招进度：0 = 命中（冻结值），1 = 战斗待机。增量单调递减 ⟹ 步长单调不增。"""
    if frame <= HOLD_END:
        return 0.0
    if frame >= SETTLE:
        return 1.0
    u = (frame - HOLD_END) / float(SETTLE - HOLD_END)
    return 1.0 - (1.0 - u) ** POST_POW


def _seg(track, frame):
    """单段取值：命停窗映射到 `HIT` ⟹ 旋转轨道逐位冻住。"""
    return RS.track(track, HIT if _hold(frame) else frame)


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def accel(u):
    """抓取推进：**快出发、慢落点**（伸手够上去然后收住）。"""
    u = max(0.0, min(1.0, u))
    return 1.0 - (1.0 - u) ** 1.6


def slam_descent(u):
    """砸地归一化下落量：由 `SLAM_SPEEDS` 累积而成（第 4 件）。"""
    u = max(0.0, min(1.0, u))
    n = len(SLAM_SPEEDS)
    total = float(sum(SLAM_SPEEDS))
    x = u * n
    index = min(n - 1, int(x))
    frac = x - index
    cum = sum(SLAM_SPEEDS[:index]) + frac * SLAM_SPEEDS[index]
    return cum / total


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def slerp3(a, b, t):
    return RS.slerp_dir(a, b, t)


# =============================================================== 骨盆世界位置
def pelvis_pos(frame):
    if frame <= ANTIC:
        u = frame / float(ANTIC)
        py = PY_COIL * smooth(u)
        pz = Z_SEAM - PZ_COIL_DROP * smooth(u)
    elif frame <= GRAB_END:
        u = (frame - ANTIC) / float(GRAB_END - ANTIC)
        py = PY_COIL + (PY_GRAB - PY_COIL) * accel(u)
        pz = (Z_SEAM - PZ_COIL_DROP) + (
            PZ_GRAB - (Z_SEAM - PZ_COIL_DROP)) * accel(u)
    elif frame <= LIFT_TOP:
        u = (frame - GRAB_END) / float(LIFT_TOP - GRAB_END)
        py = PY_CARRY
        pz = PZ_GRAB + (PZ_CARRY - PZ_GRAB) * smooth(u)
    elif frame <= CARRY_END:
        u = (frame - LIFT_TOP) / float(CARRY_END - LIFT_TOP)
        py = PY_CARRY
        pz = PZ_CARRY - PZ_CARRY_SAG * smooth(u)
    elif frame <= HIT:
        u = (frame - CARRY_END) / float(HIT - CARRY_END)
        d = slam_descent(u)
        py = PY_CARRY + (PY_HIT - PY_CARRY) * d
        pz = (PZ_CARRY - PZ_CARRY_SAG) + (
            PZ_HIT - (PZ_CARRY - PZ_CARRY_SAG)) * d
    elif frame <= HOLD_END:
        u = (frame - HIT) / float(HOLD_END - HIT)
        py = PY_HIT - (MOMENTUM_MM * 0.75 / 1000.0) * u
        pz = PZ_HIT - (MOMENTUM_MM * 0.66 / 1000.0) * u
    else:
        q = q_of(frame)
        py0 = PY_HIT - MOMENTUM_MM * 0.75 / 1000.0
        pz0 = PZ_HIT - MOMENTUM_MM * 0.66 / 1000.0
        py = py0 + (PY_END - py0) * q
        pz = pz0 + (Z_SEAM - pz0) * q
    return 0.0, py, pz


def ankle_targets(frame):
    """踝世界目标：水平随骨盆拖行（恒定系数）。★ 抱起段 py 恒定 ⟹ 踝钉住。"""
    _x, py, _z = pelvis_pos(frame)
    return {s: (ANKLE_0[s].x, ANKLE_0[s].y + py * ANKLE_LAG, ANKLE_0[s].z)
            for s in SIDES}


# =============================================================== 手的目标点
def slam_arc(side, q):
    """砸地段手的世界路径：按 **z 下降比例 `q`** 分两段线性插值（第 6 件）。

    按 z 比例分段（而不是按弧长）是为了让手 z **逐位等于** `slam_descent()`
    给出的速度表剖面 —— `slam_descent_ok` / `slam_accel_ok` 就是量这个。
    """
    pts = (
        (XOFF[side] * SPREAD["carry"], CARRY_Y, CARRY_Z),
        (XOFF[side] * 0.5 * (SPREAD["carry"] + SPREAD["slam"]),
         SLAM_MID_Y, SLAM_MID_Z),
        (XOFF[side] * SPREAD["slam"], SLAM_Y, SLAM_Z),
    )
    span = pts[0][2] - pts[2][2]
    qm = (pts[0][2] - pts[1][2]) / span if span > 1e-9 else 0.5
    q = max(0.0, min(1.0, q))
    if q <= qm:
        return lerp3(pts[0], pts[1], q / qm if qm > 1e-9 else 0.0)
    return lerp3(pts[1], pts[2], (q - qm) / max(1e-9, 1.0 - qm))


def hand_target(side, frame):
    """双手世界目标：抓取段用**按半径加权的 6 帧剖面**（第 7 件）。"""
    grab = (XOFF[side] * SPREAD["grab"], GRAB_Y, GRAB_Z)
    carry = (XOFF[side] * SPREAD["carry"], CARRY_Y, CARRY_Z)
    if frame <= GRAB_END:
        return lerp3(IDLE_HAND[side], grab,
                     grab_ramp(frame / float(GRAB_END)))
    if frame <= LIFT_TOP:
        u = (frame - GRAB_END) / float(LIFT_TOP - GRAB_END)
        return lerp3(grab, carry, smooth(u))
    if frame <= CARRY_END:
        return carry
    if frame <= HIT:
        u = (frame - CARRY_END) / float(HIT - CARRY_END)
        return slam_arc(side, slam_descent(u))
    return slam_arc(side, 1.0)


def elbow_dir(side, frame):
    """肘部鼓出方向。f0~GRAB_END 由 Idle 肘向 slerp 到工作肘向（避免 f0→f1 跳）。

    ★ 工作肘向是**朝下为主**（第 9 件）：首版取 `(±0.85, +0.40, −0.35)`（外向 +
    向后），渲染出来肘部前伸抬高、读成「双手护脸 / 拳击架势」；抱着一个人时肘部
    应当**垂在肋侧偏外**、前臂向上内收去托 —— 改成 `(±0.70, +0.05, −0.72)`。
    """
    work = (XOFF[side] * 0.70, 0.05, -0.72)
    if frame >= GRAB_END:
        return work
    u = smooth(frame / float(GRAB_END))
    return slerp3(IDLE_ELBOW[side], work, u)


# =============================================================== 躯干姿态
def torso_pose(frame):
    rx = {name: _seg(track, frame) for name, track in (
        ("pelvis", PELVIS_RX), ("spine_01", SPINE01_RX),
        ("spine_02", SPINE02_RX), ("chest", CHEST_RX), ("neck", NECK_RX),
        ("head", HEAD_RX), ("shoulder.L", SHOULDER_L_RX),
        ("shoulder.R", SHOULDER_R_RX))}
    base = {name: (rx[name], 0.0, 0.0) for name in RX_BONES}
    _x, py, pz = pelvis_pos(frame)
    if frame > HOLD_END:
        q = q_of(frame)
        for name, end in END_ROT.items():
            cur = base[name]
            base[name] = tuple(cur[c] + (end[c] - cur[c]) * q for c in range(3))
    base["@loc"] = {"pelvis": A.wloc(0.0, py, pz - 0.900)}
    return base


# =============================================================== 姿态装配
def register_anchor(frame):
    """就地登记受招方锚点（= 双手世界位的中点）。"""
    hands = {s: Vector(A.bone_world(arm_ref[0], "hand." + s, "tail"))
             for s in SIDES}
    mid = 0.5 * (hands["L"] + hands["R"])
    if frame == GRAB_END:
        ANCHOR["grab"] = {"frame": frame,
                          "mid_m": [round(v, 5) for v in mid],
                          "hand_L_m": [round(v, 5) for v in hands["L"]],
                          "hand_R_m": [round(v, 5) for v in hands["R"]]}
    elif frame == LIFT_TOP:
        ANCHOR["carry"] = {"frame": frame,
                           "mid_m": [round(v, 5) for v in mid],
                           "hand_L_m": [round(v, 5) for v in hands["L"]],
                           "hand_R_m": [round(v, 5) for v in hands["R"]]}
    elif frame == HIT:
        ANCHOR["slam"] = {"frame": frame,
                          "mid_m": [round(v, 5) for v in mid],
                          "hand_L_m": [round(v, 5) for v in hands["L"]],
                          "hand_R_m": [round(v, 5) for v in hands["R"]]}


arm_ref = [None]      # 只为 register_anchor 传骨架（避免全局名冲突）


def _ref_needs_reset(arm):
    """任一臂骨方向偏离其参考方向超过 `ARM_REF_MAX_DEG` ⟹ 需就地重取基准。

    `ARM_REF` 尚为空时把 **Idle 基准**当成参考（那正是 `ref=None` 时 `arm_seat`
    实际用的基准）——否则「空 ⟹ 不比对 ⟹ 永不登记」会死锁在 Idle 基准上。
    """
    limit = math.cos(math.radians(ARM_REF_MAX_DEG))
    for bone in ARM_BONES:
        rdir = ARM_REF[bone][1] if bone in ARM_REF else IDLE_DIR[bone]
        if A.bone_direction(arm, bone).dot(rdir) < limit:
            return True
    return False


def _anchor_ref(arm):
    ARM_REF.clear()
    for bone in ARM_BONES:
        ARM_REF[bone] = (arm.pose.bones[bone].matrix.to_3x3().copy(),
                         A.bone_direction(arm, bone))
    return ARM_REF


def build_pose(arm, frame, shift):
    arm_ref[0] = arm
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)

    targets = ankle_targets(frame)
    for side in SIDES:
        target = (targets[side][0], targets[side][1],
                  targets[side][2] + shift[side])
        G4.leg_seat(arm, pose, side, target, IDLE_KNEE_DIR[side])
    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    # ---- 手臂：位置逆解只到命停末（第 3 件）。
    # ★ 收招段（f > HOLD_END）手臂由下面的「欧拉仿射」给出，**不能再跑 `arm_seat`**：
    #   那时手的目标点仍是砸地点（z = 0.35 m），而骨盆已抬回站立高度 ⟹ 逆解必然
    #   超臂长被截断，`arm_seat_ok` 会被一个**不反映最终姿态**的测量打红
    #   （第 1 轮实测：f108 ratio 1.539、超 350 mm，而同帧末姿 `end_pose_delta` = 0）。
    if frame <= HOLD_END:
        for side in SIDES:
            want = hand_target(side, frame)
            clamp, dist_mm, limit_mm = G4.arm_seat(
                arm, pose, side, want, elbow_dir(side, frame),
                ref=(ARM_REF or None))
            info = ARM_CLAMP.setdefault(
                side, {"any": False, "worst_frame": None, "worst_over_mm": 0.0,
                       "worst_ratio": 0.0, "limit_mm": round(limit_mm, 3)})
            ratio = dist_mm / limit_mm
            if ratio > info["worst_ratio"]:
                info["worst_ratio"] = round(ratio, 5)
                info["worst_frame"] = frame
            if clamp:
                info["any"] = True
                info["worst_over_mm"] = round(
                    max(info["worst_over_mm"], dist_mm - limit_mm), 3)

        # ---- 自适应就地登记基准（第 3 件）：方向远离参考就重取，把每段的
        #      参考角差压在 `ARM_REF_MAX_DEG` 以内（否则近反向点滚转会乱翻）。
        if frame in (GRAB_END, CARRY_END) or _ref_needs_reset(arm):
            _anchor_ref(arm)

    # ---- 起手接合（第 8 件）：只在起手段、且只作用在**写进关键帧的欧拉**上；
    #      `ARM_REF` / 锚点登记读的都是未接合的求解结果。
    if frame <= ARM_EASE_END:
        w = smooth((frame - 1) / float(max(1, ARM_EASE_END - 1)))
        for bone in ARM_BONES:
            seat = pose[bone]
            base = SEAM_EULER[bone]
            pose[bone] = tuple(base[c] + (seat[c] - base[c]) * w
                               for c in range(3))

    if os.environ.get("C10_ARM_DIAG") == "1" and frame <= _env_i("C10_ARM_DIAG_END", 8):
        l23 = ARM_LEN["L"]["forearm"] + ARM_LEN["L"]["hand"]
        l1 = ARM_LEN["L"]["upper"]
        for side in SIDES:
            shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
            want = Vector(hand_target(side, frame))
            got = Vector(A.bone_world(arm, "hand." + side, "tail"))
            dist = (want - shoulder).length
            elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
            print("C10_ARM_DIAG " + json.dumps({
                "f": frame, "s": side,
                "d_mm": round(dist * 1000.0, 2),
                "fold_lo_mm": round(abs(l1 - l23) * 1000.0, 2),
                "cos_sh": round((l1 * l1 + dist * dist - l23 * l23)
                                / (2.0 * l1 * dist), 5),
                "err_mm": round((got - want).length * 1000.0, 3),
                "elbow_offaxis_mm": round(
                    ((elbow - shoulder) - (want - shoulder).normalized()
                     * (elbow - shoulder).dot((want - shoulder).normalized())
                     ).length * 1000.0, 2),
                "hand_euler": [round(math.degrees(v), 3) for v in
                               arm.pose.bones["hand." + side].rotation_euler],
            }))

    if frame in (GRAB_END, LIFT_TOP, HIT):
        register_anchor(frame)

    if frame == HIT:
        _HIT_FROZEN.clear()
        for key in HITSTOP_BONES:
            if key in pose:
                _HIT_FROZEN[key] = tuple(pose[key])
    if _HIT_FROZEN and _hold(frame):
        for name, value in _HIT_FROZEN.items():
            pose[name] = tuple(value)
            arm.pose.bones[name].rotation_euler = [math.radians(v)
                                                   for v in value]
        bpy.context.view_layer.update()

    if frame == HOLD_END:
        E0.clear()
        for bone in ("upperarm.L", "forearm.L", "hand.L",
                     "upperarm.R", "forearm.R", "hand.R"):
            E0[bone] = tuple(pose[bone])

    if frame > HOLD_END:
        # ★ 收招 = 欧拉仿射（C08 第 4 件 / C09 第 5 件）：幅度大时"单段欧拉仿射 +
        #   拉长帧数"优于换插值路径；slerp 的局部欧拉模长中段最大，会破坏单调收敛。
        q = q_of(frame)
        if not E_END_UNW:
            for bone in E0:
                E_END_UNW[bone] = JS._unwrap_xyz(E0[bone], E_END[bone])
        for bone in E0:
            pose[bone] = tuple(
                E0[bone][c] + (E_END_UNW[bone][c] - E0[bone][c]) * q
                for c in range(3))

    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


def _snapshot_carry():
    return (dict(JS._PREV_EULER),)


def _restore_carry(snap):
    JS._PREV_EULER.clear()
    JS._PREV_EULER.update(snap[0])


def solve_pose(arm, frame, meshes=None):
    """逐帧贴地闭环：鞋底钉到 0 mm（`shift` 并进踝目标，C09 第 6 号教训）。"""
    shift = {side: 0.0 for side in SIDES}
    snap = _snapshot_carry()
    pose = build_pose(arm, frame, shift)
    if meshes is None:
        return pose
    for step in range(6):
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        if SOLE_DIAG and frame in SOLE_DIAG_FRAMES:
            print("C10_SOLE_DIAG " + json.dumps({
                "f": frame, "it": step,
                "shift_mm": {s: round(shift[s] * 1000.0, 4) for s in SIDES},
                "sole_mm": {s: (None if low[s] is None
                                else round(low[s][2] * 1000.0, 4))
                            for s in SIDES}}))
        error = {s: 0.0 - low[s][2] for s in SIDES if low[s] is not None}
        if not error or max(abs(v) for v in error.values()) < 1e-6:
            break
        for side, value in error.items():
            shift[side] += value
        _restore_carry(snap)
        pose = build_pose(arm, frame, shift)
    _restore_carry(snap)
    pose = build_pose(arm, frame, shift)
    return pose


def solve_end_arm(arm):
    """一次性解出「战斗待机」的手臂欧拉（收招插值终点）。"""
    torso = {name: tuple(END_ROT[name]) for name in RX_BONES}
    torso["@loc"] = {"pelvis": A.wloc(0.0, PY_END, Z_SEAM - 0.900)}
    A.apply_pose(arm, torso)
    tgt = ankle_targets(TOTAL)
    for side in SIDES:
        G4.leg_seat(arm, pose=torso, side=side, target=tgt[side],
                    knee_dir=IDLE_KNEE_DIR[side])
    for side in SIDES:
        A.keep_world_orientation(arm, "foot." + side)
    out = {}
    for bone in ("upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R"):
        out[bone] = JS._unwrap_xyz(
            None, G4.aim_bone_ref(arm, bone, I1.ARM_DIRS[bone],
                                  IDLE_BASIS[bone], IDLE_DIR[bone]))
    return out


# =============================================================== 逐帧实测
def frame_series(arm, action, meshes, total):
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    rows = []
    for frame in range(0, total + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {"frame": frame,
               "pelvis": tuple(A.bone_world(arm, "pelvis", "head"))}
        for side in SIDES:
            row["ankle_" + side] = tuple(A.bone_world(arm, "foot." + side,
                                                      "head"))
            row["hand_" + side] = tuple(A.bone_world(arm, "hand." + side,
                                                     "tail"))
            row["shoulder_" + side] = tuple(
                A.bone_world(arm, "upperarm." + side, "head"))
            row["reach_" + side] = (
                Vector(row["ankle_" + side]) - Vector(row["pelvis"])).length
        row["hand_mid"] = tuple((Vector(row["hand_L"]) + Vector(row["hand_R"]))
                                * 0.5)
        row["shoulder_mid"] = tuple(
            (Vector(row["shoulder_L"]) + Vector(row["shoulder_R"])) * 0.5)
        low = A.foot_lowest_by_side()
        for side in SIDES:
            row["sole_" + side] = None if low[side] is None else low[side][2]
        row["low_min"] = min(row["sole_L"], row["sole_R"])
        rows.append(row)
    if previous is not None:
        arm.animation_data.action = previous
    return rows


def arm_world_steps(arm, action, total):
    mats = {}
    watch = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R",
             "pelvis", "spine_01", "spine_02", "chest", "neck", "head",
             "thigh.L", "thigh.R", "shin.L", "shin.R",
             "shoulder.L", "shoulder.R")
    for frame in range(0, total + 1):
        raw = RS.action_world_matrices(arm, action, frame)
        mats[frame] = {
            name: Matrix([raw[name][i * 4:i * 4 + 3] for i in range(3)])
            for name in watch if name in raw}
    worst, worst_at = 0.0, None
    diag = os.environ.get("C10_ROT_DIAG") == "1"
    floor = _env_f("C10_ROT_DIAG_MIN", 6.0)
    for frame in range(1, total + 1):
        for name in mats[frame]:
            if name not in mats[frame - 1]:
                continue
            q = (mats[frame - 1][name].transposed()
                 @ mats[frame][name]).to_quaternion()
            angle = math.degrees(q.angle)
            if diag and angle >= floor:
                print("C10_ROT_DIAG " + json.dumps(
                    {"f": frame, "bone": name, "step": round(angle, 3)}))
            if angle > worst:
                worst, worst_at = angle, (frame, name)
    return worst, worst_at


# =============================================================== 专属门禁
def skill02_assertions(arm, action, samples, foots):
    res = {}
    idx = {f["frame"]: i for i, f in enumerate(foots)}
    pelvis = [Vector(f["pelvis"]) for f in foots]

    # ---- 0) 首帧接缝
    mats0 = RS.action_world_matrices(arm, action, 0)
    delta0 = RS.matrix_delta(mats0, SRC_MATS)
    res["seam_source"] = [I1.NAME, 0]
    res["skill_start_delta"] = float("%.3e" % delta0)
    res["skill_start_ok"] = delta0 <= SEAM_TOL

    # ---- 1) ① 抓取相位 ≤ 6 帧（贴身技要快）
    res["grab_frames"] = GRAB_END
    res["grab_time_ok"] = GRAB_END <= GRAB_TIME_MAX

    # ---- 2) ② 抱起抬升：锚点 z 差 ≥ 600 mm（lift_height_ok）
    grab = ANCHOR.get("grab")
    carry = ANCHOR.get("carry")
    slam = ANCHOR.get("slam")
    res["anchor"] = dict(ANCHOR)
    if grab and carry:
        res["lift_height_mm"] = round(
            (carry["mid_m"][2] - grab["mid_m"][2]) * 1000.0, 2)
    else:
        res["lift_height_mm"] = None
    res["lift_min_mm"] = LIFT_MIN_MM
    res["lift_height_ok"] = (res["lift_height_mm"] is not None
                             and res["lift_height_mm"] >= LIFT_MIN_MM)

    # ---- 3) ③ 抱起时本体自己也要起来（髋部发力，量化）
    res["lift_pelvis_z_mm"] = round(
        (pelvis[idx[LIFT_TOP]].z - pelvis[idx[GRAB_END]].z) * 1000.0, 2)
    res["hip_drive_lift_ok"] = res["lift_pelvis_z_mm"] >= HIP_DRIVE_MIN_MM
    res["hip_drive_min_mm"] = HIP_DRIVE_MIN_MM

    # ---- 4) ④ ★★ 本支核心：抱住窗口内双手世界漂移 ≤ 3 mm
    drift = {"L": 0.0, "R": 0.0}
    drift_at = {}
    ref = {s: Vector(foots[idx[LIFT_TOP]]["hand_" + s]) for s in SIDES}
    for frame in range(LIFT_TOP, CARRY_END + 1):
        for side in SIDES:
            d = (Vector(foots[idx[frame]]["hand_" + side])
                 - ref[side]).length * 1000.0
            if d > drift[side]:
                drift[side] = round(d, 4)
                drift_at[side] = frame
    res["carry_drift_mm"] = drift
    res["carry_drift_at"] = drift_at
    res["carry_window"] = [LIFT_TOP, CARRY_END]
    res["carry_steady_ok"] = max(drift.values()) <= CARRY_DRIFT_MAX_MM
    res["carry_drift_max_mm"] = CARRY_DRIFT_MAX_MM

    # ---- 5) ⑤ 抱住期间双脚钉住（踝水平位移 ≤ 3 mm，第 5 件）
    plant = {}
    for side in SIDES:
        a = Vector(foots[idx[GRAB_END]]["ankle_" + side])
        worst = 0.0
        for frame in range(GRAB_END, CARRY_END + 1):
            b = Vector(foots[idx[frame]]["ankle_" + side])
            worst = max(worst, math.hypot(b.x - a.x, b.y - a.y) * 1000.0)
        plant[side] = round(worst, 4)
    res["carry_plant_mm"] = plant
    res["carry_feet_planted_ok"] = max(plant.values()) <= PLANT_MAX_MM
    res["carry_plant_max_mm"] = PLANT_MAX_MM

    # ---- 5b) ★ 抱起形态：手必须在**身前上方**，不许举到头顶正上方
    #      （第 9 件 / 渲染目检教训）。量化：抱起点「肩→手」方向与 +Z 的夹角。
    #      首版 13°（举重）⟹ 红；本版 57° ⟹ 绿。
    lift_row = foots[idx[LIFT_TOP]]
    up = Vector(lift_row["hand_mid"]) - Vector(lift_row["shoulder_mid"])
    cos_up = up.normalized().z if up.length > 1e-9 else 1.0
    res["carry_arm_up_deg"] = round(math.degrees(math.acos(
        max(-1.0, min(1.0, cos_up)))), 2)
    res["carry_arm_reach_mm"] = round(up.length * 1000.0, 2)
    res["carry_arm_posture_ok"] = res["carry_arm_up_deg"] >= ARM_UP_MIN_DEG
    res["carry_arm_up_min_deg"] = ARM_UP_MIN_DEG

    # ---- 5c) ★ 砸地段手必须**始终在肩前方**（第 9 件）：不许为了够到地面
    #      把手收到身侧再垂直下插（那样读成"鞠躬"）。量化：肩→手的 y 分量
    #      全程 ≤ −150 mm（手在肩前），且手 y 不许回到身后。
    front = []
    for frame in range(CARRY_END, HIT + 1):
        row = foots[idx[frame]]
        front.append(round((Vector(row["hand_mid"]).y
                            - Vector(row["shoulder_mid"]).y) * 1000.0, 2))
    res["slam_hand_front_mm"] = front
    res["slam_hand_front_ok"] = all(v <= -SLAM_FRONT_MIN_MM for v in front)
    res["slam_front_min_mm"] = SLAM_FRONT_MIN_MM

    # ---- 6) ⑥ 三个受招方锚点齐备 + 砸地帧对手不许穿地
    have = all(ANCHOR.get(k) for k in ("grab", "carry", "slam"))
    res["victim_anchor_present"] = have
    res["slam_point_z_mm"] = (None if not slam
                              else round(slam["mid_m"][2] * 1000.0, 2))
    res["victim_anchor_ok"] = bool(
        have and slam["mid_m"][2] * 1000.0 >= SLAM_FLOOR_MM)
    res["slam_floor_mm"] = SLAM_FLOOR_MM

    # ---- 7) ⑦ 砸地：全程单调下落 + 加速下落 + 触地瞬间停
    zs = [foots[idx[f]]["hand_mid"][2] for f in range(CARRY_END, HIT + 1)]
    speeds = [round((zs[i] - zs[i + 1]) * 1000.0, 3)
              for i in range(len(zs) - 1)]
    res["slam_descent_mm"] = [round(v * 1000.0, 2) for v in zs]
    res["slam_speed_mm"] = speeds
    res["slam_descent_ok"] = all(
        zs[i + 1] <= zs[i] + 1e-9 for i in range(len(zs) - 1))
    accel_n = max(1, int(len(speeds) * 0.667))
    res["slam_accel_ok"] = all(
        speeds[i + 1] >= speeds[i] - 0.05 for i in range(accel_n - 1))
    peak = max(speeds) if speeds else 0.0
    res["slam_peak_speed_mm"] = round(peak, 3)
    res["slam_last_speed_mm"] = round(speeds[-1], 3) if speeds else None
    res["slam_speed_ok"] = bool(
        speeds and res["slam_descent_ok"] and res["slam_accel_ok"]
        and speeds[-1] <= SLAM_STOP_MAX_MM
        and speeds[-1] <= SLAM_STOP_RATIO * peak)
    res["slam_stop_max_mm"] = SLAM_STOP_MAX_MM
    res["slam_stop_ratio"] = SLAM_STOP_RATIO

    # ---- 8) ⑧ Root Motion：水平 ≤ 900、竖直峰值 ∈ [0, 500]、本体确实被抬起
    res["root_motion_m"] = [round(pelvis[-1].x - pelvis[0].x, 6),
                            round(pelvis[-1].y - pelvis[0].y, 6)]
    res["root_motion_h_mm"] = round(
        max(abs(p.y - pelvis[0].y) for p in pelvis) * 1000.0, 2)
    zs_p = [p.z for p in pelvis]
    res["root_motion_z_peak_mm"] = round(
        (max(zs_p) - zs_p[0]) * 1000.0, 2)
    res["root_motion_z_drop_mm"] = round(
        (zs_p[0] - min(zs_p)) * 1000.0, 2)
    res["root_motion_ok"] = bool(
        res["root_motion_h_mm"] <= ROOT_MAX_MM
        and ROOT_Z_MIN_MM <= res["root_motion_z_peak_mm"] <= ROOT_Z_MAX_MM)
    res["root_motion_limits_mm"] = [ROOT_MAX_MM, ROOT_Z_MIN_MM, ROOT_Z_MAX_MM]

    # ---- 9) 顿感：命停窗 14 骨逐位冻结，骨盆继续下压
    frozen = []
    for index in range(1, len(samples)):
        frame = samples[index]["frame"]
        if HIT < frame <= HOLD_END:
            ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
            step = 0.0
            for name in HITSTOP_BONES:
                va = ea.get(name, (0.0, 0.0, 0.0))
                vb = eb.get(name, (0.0, 0.0, 0.0))
                step = max(step, max(abs(a - b) for a, b in zip(va, vb)))
            frozen.append(round(step, 6))
    res["hitstop_frozen_steps"] = frozen
    res["hitstop_present_ok"] = bool(frozen) and max(frozen) <= 1e-6
    res["hitstop_momentum_mm"] = round(
        (pelvis[idx[HIT]] - pelvis[idx[HOLD_END]]).length * 1000.0, 3)
    res["hitstop_keeps_momentum_ok"] = res["hitstop_momentum_mm"] > 10.0
    res["hitstop_frames"] = HOLD
    res["hitstop_frames_ok"] = 2 <= HOLD <= 4
    res["antic_frames"] = ANTIC
    res["lift_frames"] = LIFT_TOP - GRAB_END
    res["carry_frames"] = CARRY_END - LIFT_TOP
    res["slam_frames"] = HIT - CARRY_END
    res["recover_frames"] = TOTAL - HOLD_END

    # ---- 10) 收招：不许瞬停、不许过冲
    # ★ 度量对象修正（本支第 10 件）：原判据取「全部骨逐帧最大步长」构成的序列，
    #   再要求该序列单调不增。当最大值在**两条骨之间交替**（本例 forearm.L ↔ shin.R）
    #   时序列会出现 2.08 → 2.10 的回升 ⟹ **假红**：两条轨道各自都在单调减速，
    #   交替只是"谁是当帧最大"的排序问题。正确度量是：
    #     (a) 对**收招仿射覆盖的骨**（躯干 8 + 臂 6）**逐骨**查单调不增 —— 这比
    #         "序列级"更严，因为现在每一条轨道都要满足；
    #     (b) 腿骨只查「不许瞬停」（最大步长 ≤ 5°）：腿的欧拉由 IK 决定，收招期
    #         膝角从深蹲到直立的变化速率**几何上就是先增后减**，用单调去卡它是
    #         拿错尺子量东西（本条只在报告里留观测量，不参与判定）。
    per_bone = {name: [] for name in HITSTOP_BONES}
    tails, owners = [], []
    for index in range(1, len(samples)):
        frame = samples[index]["frame"]
        if frame < RETURN_START:
            continue
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        step, owner = 0.0, None
        for name in set(ea) | set(eb):
            va = ea.get(name, (0.0, 0.0, 0.0))
            vb = eb.get(name, (0.0, 0.0, 0.0))
            here = max(abs(a - b) for a, b in zip(va, vb))
            if name in per_bone:
                per_bone[name].append(here)
            if here > step:
                step, owner = here, name
        tails.append(round(step, 4))
        owners.append(owner)
    res["return_tail"] = tails
    res["return_tail_bones"] = owners
    res["decel_per_bone_tail"] = {
        name: [round(v, 4) for v in values]
        for name, values in sorted(per_bone.items()) if values}
    res["decel_smooth_ok"] = bool(tails) and all(
        bool(values) and all(values[i + 1] <= values[i] + 1e-6
                             for i in range(len(values) - 1))
        for values in per_bone.values())
    res["no_snap_stop_ok"] = bool(tails and tails[-1] <= 5.0
                                  and tails[-1] <= tails[0])
    res["local_step_max_deg"] = round(max(tails) if tails else 0.0, 3)

    # ---- 11) 力矩链：脚→腿→髋→腰→肩→手 逐级非零
    keys = ("pelvis", "spine_01", "spine_02", "chest", "shoulder.L",
            "shoulder.R", "thigh.L", "shin.L", "thigh.R", "shin.R",
            "upperarm.L", "forearm.L", "hand.L",
            "upperarm.R", "forearm.R", "hand.R")
    channel = {}
    for name in keys:
        vals = [s["euler"].get(name, (0.0, 0.0, 0.0)) for s in samples]
        channel[name] = round(max(max(abs(v) for v in item) for item in vals), 3)
    res["power_chain_channels_deg"] = channel
    res["power_chain_ok"] = all(v > 0.5 for v in channel.values())

    # ---- 12) 腿可达 + 手可达（不许截断）
    limit = A.L_THIGH + A.L_SHIN
    ratios, peak = {}, {}
    for side in SIDES:
        vals = [(f["reach_" + side] * 1000.0, f["frame"]) for f in foots]
        best, best_f = max(vals)
        ratios[side] = round(best / (limit * 1000.0), 5)
        peak[side] = [best_f, round(best, 2)]
    res["leg_reach_max_ratio"] = ratios
    res["leg_reach_peak"] = peak
    res["ik_reach_ok"] = all(v <= REACH_MAX_RATIO for v in ratios.values())
    res["arm_seat_clamp"] = {s: dict(v) for s, v in sorted(ARM_CLAMP.items())}
    res["arm_seat_ok"] = not any(v["any"] for v in ARM_CLAMP.values())

    # ---- 13) 支撑脚贴地
    sole = {}
    for side in SIDES:
        zsv = [foots[i]["sole_" + side] for i in range(len(foots))
               if foots[i]["sole_" + side] is not None]
        sole[side] = [round(min(zsv) * 1000.0, 3), round(max(zsv) * 1000.0, 3)]
    res["stance_sole_mm"] = sole
    res["stance_sole_ok"] = all(SOLE_RANGE_MM[0] <= v[0]
                                and v[1] <= SOLE_RANGE_MM[1]
                                for v in sole.values())

    # ---- 14) 末帧必须**真的是**登记的 `end_pose_deg`
    end_e = samples[-1]["euler"]
    res["end_pose_measured_deg"] = {
        n: [round(v, 4) for v in end_e.get(n, (0.0, 0.0, 0.0))]
        for n in END_ROT}
    res["end_pose_delta_deg"] = {
        n: round(max(abs(a - b) for a, b in
                     zip(end_e.get(n, (0.0, 0.0, 0.0)), END_ROT[n])), 4)
        for n in END_ROT}
    res["tail_settle_ok"] = all(v <= END_POSE_TOL_DEG
                                for v in res["end_pose_delta_deg"].values())
    res["tail_settle_tol_deg"] = END_POSE_TOL_DEG
    return res


# =============================================================== 主流程
def main():
    global SEAM_POSE, SEAM_EULER, Z_SEAM, ANKLE_0, IDLE_POSE, IDLE_KNEE_DIR
    global IDLE_BASIS, IDLE_DIR, IDLE_HAND, IDLE_ELBOW, ARM_LEN
    global E0, E_END, E_END_UNW, SRC_MATS, END_ROT
    global PELVIS_RX, SPINE01_RX, SPINE02_RX, CHEST_RX, NECK_RX, HEAD_RX
    global SHOULDER_L_RX, SHOULDER_R_RX

    for store in (SEAM_POSE, SEAM_EULER, ANKLE_0, IDLE_POSE, IDLE_KNEE_DIR,
                  IDLE_BASIS, IDLE_DIR, IDLE_HAND, IDLE_ELBOW, ARM_LEN,
                  ARM_REF, _HIT_FROZEN, HAND_TARGET, ANCHOR, ARM_CLAMP,
                  E0, E_END, E_END_UNW, LOG):
        store.clear()
    ARM_REF_STAGE = ""

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("C10_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}

    if "thigh.L" not in A.PROBE_BONES:
        A.PROBE_BONES = tuple(A.PROBE_BONES) + ("thigh.L", "thigh.R",
                                                "shin.L", "shin.R")
        A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail"
                                             for n in A.PROBE_TAILS)

    # ---- 首帧真值：`Idle_01@0`
    scene = bpy.context.scene
    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    scene.frame_set(0)
    bpy.context.view_layer.update()
    SEAM_EULER = {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
                  for b in arm.pose.bones}
    SEAM_POSE = dict(SEAM_EULER)
    SEAM_POSE["@loc"] = {"pelvis": tuple(arm.pose.bones["pelvis"].location)}
    SEAM_POSE.update(A.FIST)
    SRC_MATS = RS.action_world_matrices(arm, src, 0)
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    for side in SIDES:
        IDLE_HAND[side] = tuple(A.bone_world(arm, "hand." + side, "tail"))
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        IDLE_ELBOW[side] = tuple((elbow - shoulder).normalized())

    for name in RX_BONES:
        END_ROT[name] = tuple(SEAM_EULER[name])

    # ---- Idle 骨基座
    IDLE_POSE = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, IDLE_POSE)
    bpy.context.view_layer.update()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        IDLE_KNEE_DIR[side] = (knee - hip).normalized()
        for name in ("thigh." + side, "shin." + side):
            IDLE_BASIS[name] = arm.pose.bones[name].matrix.to_3x3().copy()
            IDLE_DIR[name] = A.bone_direction(arm, name)
    for name in ("upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R"):
        IDLE_BASIS[name] = arm.pose.bones[name].matrix.to_3x3().copy()
        IDLE_DIR[name] = A.bone_direction(arm, name)
    G4.IDLE_BASIS.clear()
    G4.IDLE_BASIS.update(IDLE_BASIS)
    G4.IDLE_DIR.clear()
    G4.IDLE_DIR.update(IDLE_DIR)
    G4.IDLE_KNEE_DIR.clear()
    G4.IDLE_KNEE_DIR.update(IDLE_KNEE_DIR)
    G4.ARM_LEN.clear()
    for side in SIDES:
        G4.ARM_LEN[side] = dict(ARM_LEN[side])

    # ---- 躯干轨道：f0 回填 Idle 真值
    def patch(track, bone, channel=0):
        return [(0, SEAM_EULER[bone][channel])] + [
            k for k in track if k[0] != 0]

    PELVIS_RX = patch(PELVIS_RX, "pelvis", 0)
    SPINE01_RX = patch(SPINE01_RX, "spine_01", 0)
    SPINE02_RX = patch(SPINE02_RX, "spine_02", 0)
    CHEST_RX = patch(CHEST_RX, "chest", 0)
    NECK_RX = patch(NECK_RX, "neck", 0)
    HEAD_RX = patch(HEAD_RX, "head", 0)
    SHOULDER_L_RX = patch(SHOULDER_L_RX, "shoulder.L", 0)
    SHOULDER_R_RX = patch(SHOULDER_R_RX, "shoulder.R", 0)

    A.report("C10_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "antic": ANTIC, "grab_end": GRAB_END, "lift_top": LIFT_TOP,
        "carry_end": CARRY_END, "hit": HIT, "hold": HOLD,
        "hold_end": HOLD_END, "return_start": RETURN_START,
        "settle": SETTLE, "cancel": CANCEL,
        "seam_source": [I1.NAME, 0],
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "py_grab_mm": round(PY_GRAB * 1000.0, 1),
        "py_hit_mm": round(PY_HIT * 1000.0, 1),
        "py_end_mm": round(PY_END * 1000.0, 1),
        "pz_grab_mm": round(PZ_GRAB * 1000.0, 1),
        "pz_carry_mm": round(PZ_CARRY * 1000.0, 1),
        "pz_hit_mm": round(PZ_HIT * 1000.0, 1),
        "ankle_lag": ANKLE_LAG,
        "arm_ref_max_deg": ARM_REF_MAX_DEG,
        "anchors_m": {"grab": [0.0, GRAB_Y, GRAB_Z],
                      "carry": [0.0, CARRY_Y, CARRY_Z],
                      "slam": [0.0, SLAM_Y, SLAM_Z]},
        "note": ("抱摔：6f 抓取（双手钉到 0.98 m）→ 26f 抱起（指尖抬到 1.70 m，"
                 "本体骨盆升 %d mm）→ 18f 顶住（双手世界漂移 ≤ 3 mm、双脚钉住）"
                 "→ 18f 砸地（加速下落 + 触地瞬间停，对手落点 0.35 m）"
                 "→ 命停 3 帧 → 38f 单向减速回「战斗待机」。"
                 "受招方锚点三相位登记供引擎摆第二角色。"
                 % round((PZ_CARRY - PZ_GRAB) * 1000.0)),
    })

    E_END = solve_end_arm(arm)
    A.report("C10_END_ARM", {
        "end_euler_deg": {k: [round(v, 4) for v in E_END[k]] for k in E_END},
    })

    # ---- 建片段
    JS._PREV_EULER.clear()
    A.apply_pose(arm, SEAM_POSE)
    bpy.context.view_layer.update()
    for name, value in SEAM_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    keyframes = [(0, SEAM_POSE)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "连招与特殊技",
        "note": ("抱摔：抓取 → 抱起（指尖抬升 %d mm）→ 顶住 → 砸地（对手落点"
                 " z = %d mm）→ 命停 %d 帧 → 收招回「战斗待机」；受招方锚点"
                 "三相位登记。"
                 % (round(res_lift_guess()), round(SLAM_Z * 1000.0), HOLD)),
        "antic_frame": ANTIC,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HOLD,
        "root_motion_m": [0.0, round(PY_END, 6)],
        "inherit_from": None,
        "segments": {"grab": [0, GRAB_END], "lift": [GRAB_END, LIFT_TOP],
                     "carry": [LIFT_TOP, CARRY_END], "slam": [CARRY_END, HIT],
                     "hold": [HIT, HOLD_END], "recover": [HOLD_END, TOTAL]},
        "victim_anchor_m": {k: v["mid_m"] for k, v in sorted(ANCHOR.items())},
        "grab_point_m": (ANCHOR.get("grab") or {}).get("mid_m"),
        "carry_point_m": (ANCHOR.get("carry") or {}).get("mid_m"),
        "slam_point_m": (ANCHOR.get("slam") or {}).get("mid_m"),
        "end_pose_deg": {k: [round(v, 4) for v in val]
                         for k, val in sorted(END_ROT.items())},
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "ANTIC": ANTIC, "GRAB": GRAB_END, "LIFT": LIFT_TOP,
        "CARRY_END": CARRY_END, "HIT": HIT, "HOLD_END": HOLD_END,
        "RECOV": RETURN_START, "SETTLE": SETTLE, "CANCEL": CANCEL,
        "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    foots = frame_series(arm, action, meshes, TOTAL)
    if os.environ.get("C10_TRACE") == "1":
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for f in foots:
            print("C10_TRACE " + json.dumps({
                "f": f["frame"], "q": round(q_of(f["frame"]), 5),
                "pelvis": [round(v * 1000.0, 2) for v in f["pelvis"]],
                "hand_mid": [round(v * 1000.0, 2) for v in f["hand_mid"]],
                "L_sole": (None if f["sole_L"] is None
                           else round(f["sole_L"] * 1000.0, 3)),
                "R_sole": (None if f["sole_R"] is None
                           else round(f["sole_R"] * 1000.0, 3)),
                "L_reach": round(f["reach_L"] * 1000.0 / limit_mm, 4),
                "R_reach": round(f["reach_R"] * 1000.0 / limit_mm, 4),
            }))

    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.update(skill02_assertions(arm, action, samples, foots))
    if os.environ.get("C10_EULER_DIAG") == "1":
        # `no_teleport` 量的是**欧拉**逐帧步长，与 `world_step` 不同源：欧拉表示在
        # 不利姿态下会把同一个真实转角放大（本支实测首帧放大 1.5×）⟹ 必须单独看它。
        floor = _env_f("C10_EULER_DIAG_MIN", 12.0)
        for index in range(1, len(samples)):
            e0 = samples[index - 1]["euler"]
            e1 = samples[index]["euler"]
            for name in set(e0) | set(e1):
                step = max(abs(a - b) for a, b in zip(
                    e0.get(name, (0.0,) * 3), e1.get(name, (0.0,) * 3)))
                if step >= floor:
                    print("C10_EULER_DIAG " + json.dumps(
                        {"f": samples[index]["frame"], "bone": name,
                         "step": round(step, 3)}))
    report["low_bad_frames"] = {
        str(s["frame"]): [round(s["low"]["L"] * 1000.0, 2),
                          round(s["low"]["R"] * 1000.0, 2)]
        for s in samples
        if min(s["low"]["L"], s["low"]["R"]) * 1000.0 < -2.0}
    world_step, world_at = arm_world_steps(arm, action, TOTAL)
    report["world_step_max_deg"] = round(world_step, 3)
    report["world_step_max_at"] = (None if world_at is None
                                   else [world_at[0], world_at[1]])
    report["world_step_ok"] = world_step <= NO_TELEPORT_MAX_DEG
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C10_REPORT", report)

    if not SKIP_RENDER:
        frames = [0, GRAB_END, 20, LIFT_TOP, CARRY_END, HIT, HOLD_END,
                  RETURN_START + 20, TOTAL]
        ratio = 780.0 / 1100.0
        keys = [k for k in samples[0]
                if k != "frame" and isinstance(samples[0][k], tuple)]
        pts = [Vector(s[k]) for s in samples for k in keys if k in s]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        center = (0.5 * (min(xs) + max(xs)), 0.5 * (min(ys) + max(ys)),
                  0.5 * (min(zs) + max(zs)))
        scale = max(2.10, (max(zs) - min(zs)) * 1.15,
                    (max(xs) - min(xs)) * 1.15 / ratio,
                    (max(ys) - min(ys)) * 1.15 / ratio)

        def reframe(view):
            _name, location, target, _scale, res = view
            direction = (Vector(location) - Vector(target)).normalized()
            new_target = Vector(center)
            new_location = new_target + direction * 4.6
            return (_name, tuple(new_location), tuple(new_target), scale, res)

        A.report("C10_CAMERA", {
            "bbox_min": [round(min(xs), 4), round(min(ys), 4),
                         round(min(zs), 4)],
            "bbox_max": [round(max(xs), 4), round(max(ys), 4),
                         round(max(zs), 4)],
            "center": [round(v, 4) for v in center],
            "ortho_scale": round(scale, 4),
        })
        for base in (A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q):
            A.render_pose_sheet(arm, action, frames, "skill02",
                                views=(reframe(base),))
    # 迭代期（SKIP_RENDER=1）跳过存盘 + 导出：glTF 导出在实机上要 ~56 s，
    # 而门禁只需要内存里的 Action。正式那一轮才落盘。
    if not SKIP_RENDER:
        A.save_project()
        A.export_glb(arm)
    print("C10_DONE failed=%s" % report["failed"])
    print("C10_DONE non_ok_bools=%s" % report["non_ok_bools"])


def res_lift_guess():
    return round((CARRY_Z - GRAB_Z) * 1000.0)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C10_FAILURE " + traceback.format_exc())
