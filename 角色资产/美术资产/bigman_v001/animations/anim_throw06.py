"""anim_throw06 —— C06 `Throw` 投掷（C 族第六支，**一次性 + 大幅度位移**）。

=============================================================================
清单原文
=============================================================================
「抱起 / 过肩摔 / 抛投。强调**髋部发力**和敌人重量」。

本支是 C04 → C05 → C06 抓投链的**收口**：抓住（C04）→ 控住（C05）→
**把敌人扔出去**（C06）。

=============================================================================
第 0 件 —— 这支的形态选择（先认清再动手）
=============================================================================
「抛投」的读法：**沉髋蓄力 → 髋部爆发前送 → 双手把敌人从胸前向前抛出去
→ 跟随姿（双臂前伸、身体前压）**。
不是过肩摔（那要两角色同步、属 C10 `抱摔` 的活），本支只做**单角色**的抛投。

与 C05 的四条根本差异：

| | C05 | C06 |
|---|---|---|
| 类型 | 循环 | **一次性**（`loop=false`） |
| 接管 | 首帧 = `Grab_Start@54` | 首帧 = **`Grab_Hold@120`**（逐位） |
| 双手 | 钉死在世界抓取点 | **钉死到释放帧，之后交给手臂摆动** |
| 躯干 | 恒定 14°、只做呼吸 | **髋部大幅旋转（ry −20° → +26°，发力主通道）** |
| 位移 | 0 | **Root Motion 前冲 300 mm** |

=============================================================================
第 1 件 —— ★★ 收招门禁决定形态：不许过冲 ⟹ 末帧是"跟随姿"而不是 Idle
=============================================================================
`decel_smooth_ok`（C03 第 2 件、C04 第 2 件）取的是**全骨逐帧步长的最大值**，
要求 `[RETURN_START, TOTAL]` 上**单调不增** —— 本质是"收招段不许有任何过冲"。
C02 / C03 / C04 三支全是"从命中姿**单向**、逐帧减速走到末姿"，没有例外。

而"抛出去"这个动作天然要**外抛再回收**（先向前伸展、再收回来）。这两件事在
同一个 `RETURN_START` 起点上是**互斥**的：先外抛到极值则速度为 0，随后回收
必然重新加速 ⟹ 步长回升 ⟹ 门禁红。

⟹ 本支的形态学结论：**整段收招 = 从冻结的命中姿单向减速走到"跟随姿"
（双臂前伸、略低于肩、上身前压、两脚前后开立）**。
- 好处一：`throw_arc_ok`（释放后单调外抛、无反向帧）**构造性成立** ——
  手从抓取点（身前 835 mm、屈肘）一路伸展到身前 1100+ mm，全程向外、不回头。
- 好处二：收招是**单段减速**，`decel_smooth_ok` 结构性成立（所有通道都是
  同一个 `q(frame)` 的仿射函数 ⟹ 步长 = |Δ|·Δq，Δq 单调不增 ⟹ 步长单调不增）。
- 代价：**末帧不是 `Idle_01@0`**，而是"投掷跟随姿"。这是**有意的设计决定**
  （同 C02/C03 的"不许过冲"约定），不是遗漏；引擎侧从跟随姿混回 Idle 即可。
  ⟹ 本支**不设**下游接缝门禁，改为把末帧姿态登记进 Action 自定义属性。

=============================================================================
第 2 件 —— 释放帧与"钉死 → 释放"的接口
=============================================================================
`RELEASE = HOLD_END + 1 = 31`：第 31 帧起手离开抓取点。
`release_frame_ok` 的口径是「存在且**唯一**」：取逐帧 `hand.tail` 到登记抓取点的
最大漂移，第一条 > 3 mm 的帧必须**恰好**是 `RELEASE`，且此前每一帧都 ≤ 3 mm。
命停窗（f28~f30）内手逐位冻结（`_HIT_FROZEN`），漂移恒为 0 ⟹ 构造性成立。

=============================================================================
第 3 件 —— ★ 可达域：释放前手臂必须"收"，因为骨盆在往前压
=============================================================================
`probe_c06_baseline.py` 实测 C05 末帧（= 本支首帧）：

    肩→抓取点   L 629.20 mm / R 631.19 mm      臂长上限 649.675 mm
    **余量      L 20.47 mm / R 18.49 mm**（与 C05 完全一致）
    腿余量      L 123.40 mm / R 130.60 mm（很松，沉髋随便沉）

本支**不向上、向外够**，而是反过来：骨盆前冲 300 mm，把肩**送到**敌人的方向
⟹ 肩→抓取点距离**从 629 mm 一路缩到 ~330 mm**（肘深屈）。这正是"拉起—抛出去"
的力学形态：先把身体压进敌人，再用髋把敌人甩出去。
`arm_seat` 的截断标志（`arm_seat_ok`）是本支**最紧**的一条 —— 全程不许 True。

=============================================================================
第 4 件 —— 髋部发力必须变成两个会失败的数字
=============================================================================
清单点名「髋部发力」，形容词不算交付。两条判据：

    hip_drive_ok   髋部旋转峰值 ÷ 躯干链（spine_01/spine_02/chest）峰值 > 1.0
    hip_then_arm_ok  髋角速度峰值帧 早于 手世界速度峰值帧 ≥ 4 帧

物理根据：手在 f0~f30 被**钉死**在世界抓取点 ⟹ 手速 ≈ 0；髋在 f20~f28 爆发
（ry −20° → +26°，峰值 ≈ 7.3°/帧）。手的峰值必然出现在释放之后 ⟹ 两条同时成立。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_throw06.py
    SKIP_RENDER=1 只跑门禁（迭代用）；C06_TRACE=1 打逐帧轨迹。
"""

import json
import math
import os
import sys

import bpy
from mathutils import Euler, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402
import anim_run_stop as RS      # noqa: E402
import anim_jump_start as JS    # noqa: E402
import anim_grab04 as G4        # noqa: E402
import anim_grab05 as G5        # noqa: E402

NAME = "Throw"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SRC_ACTION = G5.NAME                    # 上游 = Grab_Hold
SRC_FRAME = 120                         # Grab_Hold 末帧
SIDES = ("L", "R")


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


# ---------------------------------------------------------------- 帧预算
TOTAL = _env_i("C06_TOTAL", 60)                 # 1.000 s @60fps
ANTIC = _env_i("C06_ANTIC", 20)                 # 前摇结束（§0.1 重攻击 12~20）
HIT = _env_i("C06_HIT", 28)                     # 命中帧（髋部爆发到位）
HOLD = _env_i("C06_HOLD", 3)                    # 命停 3 帧（§0.1 2~4）
HOLD_END = HIT + HOLD - 1                       # 30
RELEASE = HOLD_END + 1                          # 31（手离开抓取点）
RETURN_START = RELEASE                          # 收招起点（单段减速，见文件头第 1 件）
SETTLE = _env_i("C06_SETTLE", 50)               # 收招落定帧（此后逐位静止）
CANCEL = _env_i("C06_CANCEL", 52)               # 可取消帧
POST_POW = _env_f("C06_POSTPOW", 1.5)           # 收招缓动 q = 1 − (1−u)^p

# 脚步：R（后脚）先上步，L（前脚）随后上步，两次都在前摇/爆发段内完成
T_R_OFF = _env_i("C06_R_OFF", 5)
T_R_ON = _env_i("C06_R_ON", 15)
T_L_OFF = _env_i("C06_L_OFF", 15)
T_L_ON = _env_i("C06_L_ON", 26)
WINDOWS = {"L": ((0, T_L_OFF), (T_L_ON, TOTAL)),
           "R": ((0, T_R_OFF), (T_R_ON, TOTAL))}
R_LIFT = _env_f("C06_R_LIFT", 0.090)
L_LIFT = _env_f("C06_L_LIFT", 0.085)
SWING_POW = _env_f("C06_SWING_POW", 1.45)
SIDES = ("L", "R")

# ---------------------------------------------------------------- 位移
D_TOTAL_MM = _env_f("C06_D_TOTAL", 270.0)       # Root Motion 前冲
# ★ 第 1 轮实测：`world_step_max_deg=27.96`（上限 25）@f25，根因是 f20→f24
#   手臂可及长 527→392 mm（34~46 mm/帧的收拢率）把肘部推进高敏区，
#   与髋速峰值同窗。这里把驱动率从 ~17 mm/帧压到 ~10 mm/帧、总量 300→270 mm，
#   并给命停窗留 14 mm 爬行（`hitstop_momentum_mm` 只要求 >10）。
D_DRIVE = ((0, 0.0), (6, 18.0), (12, 56.0), (18, 100.0), (22, 140.0),
           (25, 168.0), (28, 196.0), (HOLD_END, 210.0))

# ---------------------------------------------------------------- 躯干轨道
# 每支都是 (帧, 值)。frame 0 由上游接缝真值回填（见 main），故写占位 0。
#
# ★ 第 3 轮实测（血的教训）：**躯干 rx 不能为了"读感"而降**。
#   我把蓄力段 pelvis rx 从 21.5 降到 14、spine/chest 同步降了 ~4°，
#   想着"立起来更像蓄力" —— 结果 f14 右手到抓取点的距离从 631 mm
#   暴涨到 709.026 mm（上限 649.675，超 59.351 mm），`arm_seat` 截断，
#   手被甩离 59.33 mm，一次带崩 4 项门禁（`arm_seat_ok`/`grab_reach_ok`/
#   `hold_drift_ok`/`release_frame_ok`）。
#   物理原因：抓取点在 y = −1374 mm、z = 1135 mm 的**前方远处**，
#   而躯干链前倾正是把肩往前送、够到它的**唯一手段**（≈6.5 mm 距离/度）。
#   ⟹ 躯干 rx 是**可达域硬约束**，不是美术参数，这里回到第 2 轮的可用值。
#   读感改由**颈/头抬起来**承担（见下，颈/头完全不参与肩位姿，零可达风险）。
PELVIS_RX = ((0, 0.0), (8, 17.5), (14, 20.0), (20, 21.5), (23, 19.5),
             (26, 16.5), (28, 16.0), (HOLD_END, 16.0))
# ★ 髋部旋转是**发力主通道**（清单点名的"髋部发力"）。f23 取 −2：
#   实测 f23 = −10 会把髋角速峰拖到 f27，与手峰 f31 只差 4 帧（门槛值本身）
#   ⟹ 太脆；−4（第 1 轮）峰在 f25。取 −2 让峰落在 f24~f25，与手峰差 6~7 帧。
PELVIS_RY = ((0, 0.0), (6, -8.0), (14, -18.0), (20, -20.0), (23, -2.0),
             (26, 10.0), (28, 20.0), (HOLD_END, 22.0))
SPINE01_RX = ((0, 0.0), (10, 7.5), (20, 9.5), (28, 8.0), (HOLD_END, 8.0))
SPINE01_RY = ((0, 0.0), (10, -4.0), (20, -8.0), (28, 5.0), (HOLD_END, 6.0))
SPINE02_RX = ((0, 0.0), (10, 7.5), (20, 9.5), (28, 8.0), (HOLD_END, 8.0))
SPINE02_RY = ((0, 0.0), (10, -4.0), (20, -8.0), (28, 5.0), (HOLD_END, 6.0))
CHEST_RX = ((0, 0.0), (10, 9.0), (20, 11.5), (28, 12.0), (HOLD_END, 12.0))
CHEST_RY = ((0, 0.0), (10, -6.0), (20, -10.0), (28, 7.0), (HOLD_END, 8.0))
# ★ 读感修正落在**颈/头**上（第 1 轮目检 f0020 读成"抱头下蹲"）。
#   原版颈 −13 / 头 +9 ⟹ 相对躯干净 −4°，而躯干前倾 52° ⟹ 净朝下 48°，
#   看起来像低头认输。改成颈 −22 / 头 −6 ⟹ 相对躯干净 −28°，
#   蓄力段净朝向 ≈ 24° 下俯（弓腰但眼睛盯住对手，这才是摔投蓄力）。
NECK_RX = ((0, 0.0), (12, -18.0), (20, -22.0), (28, -12.0), (HOLD_END, -11.0))
NECK_RY = ((0, 0.0), (10, 3.0), (20, 5.0), (28, -3.0), (HOLD_END, -4.0))
HEAD_RX = ((0, 0.0), (12, -6.0), (20, -6.0), (28, -2.0), (HOLD_END, -2.0))
HEAD_RY = ((0, 0.0), (10, 2.0), (20, 3.0), (28, -2.0), (HOLD_END, -2.0))
SHOULDER_L_RX = ((0, 0.0), (10, -5.0), (20, -7.0), (28, -3.0), (HOLD_END, -2.0))
SHOULDER_R_RX = ((0, 0.0), (10, -5.0), (20, -7.0), (28, -3.0), (HOLD_END, -2.0))
SHOULDER_L_RZ = ((0, 0.0), (10, -24.0), (20, -27.0), (28, -20.0), (HOLD_END, -19.0))
SHOULDER_R_RZ = ((0, 0.0), (10, 25.0), (20, 28.0), (28, 21.0), (HOLD_END, 20.0))

# 收招末值（= 跟随姿）：累计前倾 45°（不是 65°），头抬起看投掷方向。
# ★ 第 1 轮目检：原版 pelvis 25 + spine 12+12 + chest 16 = 65° 前倾，
#   双臂又是**水平**前伸（FLY_DIR 的 z 只有 −0.15），渲出来是"前扑/超人飞"。
#   真实投掷的跟随姿是"躯干前压 ~45°、双臂甩过并垂向前下、眼睛看着落点"。
END_ROT = {
    "pelvis": (15.0, 6.0, 0.0),
    "spine_01": (7.0, 3.0, 0.0),
    "spine_02": (7.0, 3.0, 0.0),
    "chest": (9.0, 4.0, 0.0),
    "neck": (-12.0, 0.0, 0.0),
    "head": (-8.0, 0.0, 0.0),
    "shoulder.L": (-2.0, 0.0, -10.0),
    "shoulder.R": (-2.0, 0.0, 11.0),
}
END_PX = _env_f("C06_END_PX", 0.010)
END_PZ = _env_f("C06_END_PZ", 0.7260)

PELVIS_X = ((0, 0.0), (10, -0.010), (20, 0.006), (HOLD_END, 0.012))
PELVIS_Z = ((0, 0.0), (8, 0.7280), (14, 0.7080), (20, 0.7000), (23, 0.7120),
            (26, 0.7400), (28, 0.7520), (HOLD_END, 0.7560))

# ---------------------------------------------------------------- 手臂方向（收招终点）
# ★ C03 第 1 件的血教训：这是**世界系**（x = 左正，y = 身后正，z = 上正），
#   不是躯干系。跟随姿 = 双臂向**前（−y）+ 微下（−z）**伸展 ——
# ★ 第 1、4 轮目检：z 只给 −0.15 时双臂读起来是"水平前伸"（僵尸手）；
#   改成 −0.41/−0.34 后仍偏"前扑"，因为**上臂与前臂几乎共线（肘弯 ≈ 0）**，
#   整条手臂是一根僵直长棍，在正交视图里显得又长又假。
#   真实投掷甩出后是"**上臂垂、前臂平**（肘弯 ~25°）+ 手略内旋"。
#   这里上臂下垂 34.4°、前臂下垂 10.4° ⟹ 肘弯 24°，手仍伸向前方：
FLY_DIR = {
    "upperarm.L": (0.260, -0.500, -0.830),
    "forearm.L": (0.140, -0.860, -0.490),
    "hand.L": (0.140, -0.860, -0.490),
    "upperarm.R": (-0.260, -0.500, -0.830),
    "forearm.R": (-0.140, -0.860, -0.490),
    "hand.R": (-0.140, -0.860, -0.490),
}

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
HITSTOP_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "shoulder.L", "shoulder.R")
# ★ 与 C04 的关键差异（第 1 轮实测逼出来的）：**手臂不进命停冻结集**。
#   理由不是"放松"，而是机制不同 —— C04 抓握保持段的手臂是**方向链**
#   (`aim_carry_bounded`) 驱动的，冻结欧拉 = 冻结视觉，手不动。C06 的抓握
#   保持段手臂是**位置逆解** (`arm_seat`) 钉死在世界抓取点上的：骨盆在命停
#   窗仍爬 14 mm（`hitstop_momentum_mm` 要 >10），此时若把手臂欧拉冻住，
#   手就被"焊"在旧位置 ⟹ 第 1 轮实测 f29/f30 漂 11.59 / 4.91 mm，
#   `hold_drift_ok`(≤3 mm) 与 `release_frame_ok`(唯一=f31) 同时红。
#   去掉手臂后：躯干链逐位冻结（"顿"仍在），手臂继续位置逆解 ⟹ 手**始终
#   贴在对手身上**（漂移 0），这才是抓投动画在命停期该有的样子。
_ARM_FROZEN_NAMED = "命中冻结 = 躯干链（手臂由位置逆解保持，见上）"

# ---------------------------------------------------------------- 门禁阈值
SEAM_TOL = 1e-6
SOLE_RANGE_MM = (-2.0, 6.0)
PIVOT_DRIFT_MAX_MM = 3.0
NO_TELEPORT_MAX_DEG = 25.0
REACH_MAX_RATIO = 0.995
GRAB_REACH_MAX_RATIO = 0.995
GRAB_HOLD_DRIFT_MAX_MM = 3.0
RELEASE_EPS_MM = 3.0
HIP_DRIVE_MIN = 1.0
HIP_LEAD_MIN_FRAMES = 4
THROW_FWD_MIN_MM = 100.0
WEIGHT_SETTLE_MIN_MM = 20.0
LIN_TOL_MM = 1.0

# ---------------------------------------------------------------- 模块级状态
SEAM_POSE = {}
SEAM_EULER = {}
PY0 = 0.0
Z_SEAM = 0.9
IDLE_POSE = {}
IDLE_PELVIS = None
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
ANKLE_0 = {}
ANKLE_1 = {}
FLAT_ANK = {}
PIVOT = {}
PIVOT_VERT = {}
PIVOT_AXIS = {}
PIVOT_SCALE = 1.0
GRAB_POINT = {}
GRAB_SHOULDER = {}
GRAB_ELBOW = {}
ARM_REF = {}
ARM_LEN = {}
ARM_SEAT_CLAMP = {}
E0 = {}                 # 命中帧冻结的手臂欧拉（收招插值起点）
E_FLY = {}              # 跟随姿的手臂欧拉（收招插值终点）
E_FLY_DIR_ACH = {}
_HIT_FROZEN = {}
WINDOW_SOLE = {}
AIR_SOLE = {}
ALL_SOLE = {}
SRC_MATS = {}
SRC_META = {}
LOG = {}


def _unit(v):
    v = Vector(v)
    n = v.length or 1.0
    return v / n


def _ang(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0,
                                                 sum(x * y for x, y in zip(a, b))))))


def _slerp_dir(a, b, t):
    a, b = _unit(a), _unit(b)
    dot = max(-1.0, min(1.0, a.dot(b)))
    theta = math.acos(dot)
    if theta < 1e-9:
        return tuple(b)
    s = math.sin(theta)
    return tuple((math.sin((1.0 - t) * theta) / s) * ai
                 + (math.sin(t * theta) / s) * bi
                 for ai, bi in zip(a, b))


def _lerp3(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def q_of(frame):
    """收招进度：0 = 命中（冻结值），1 = 跟随姿。结构性保证步长单调不增。"""
    if frame <= HOLD_END:
        return 0.0
    if frame >= SETTLE:
        return 1.0
    u = (frame - HOLD_END) / float(SETTLE - HOLD_END)
    return 1.0 - (1.0 - u) ** POST_POW


def _hold(frame):
    return HIT < frame <= HOLD_END


# =============================================================== 姿态
def torso_pose(frame):
    if frame <= HOLD_END:
        f = HIT if _hold(frame) else frame
        rot = {
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
        }
        px = RS.track(PELVIS_X, frame)
        pz = RS.track(PELVIS_Z, frame)
        dy = PY0 - RS.track(D_DRIVE, frame) / 1000.0
        rot["@loc"] = {"pelvis": A.wloc(px, dy, pz - 0.900)}
        return rot

    q = q_of(frame)
    f = HIT                       # HOLD_END 上的旋转值 = HIT 的冻结值
    base = {
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
    }
    rot = {name: _lerp3(base[name], END_ROT[name], q) for name in base}
    px = RS.track(PELVIS_X, HOLD_END) + (END_PX - RS.track(PELVIS_X, HOLD_END)) * q
    pz = RS.track(PELVIS_Z, HOLD_END) + (END_PZ - RS.track(PELVIS_Z, HOLD_END)) * q
    d0 = RS.track(D_DRIVE, HOLD_END)
    d = d0 + (D_TOTAL_MM - d0) * q
    rot["@loc"] = {"pelvis": A.wloc(px, PY0 - d / 1000.0, pz - 0.900)}
    return rot


# =============================================================== 脚步
def window_of(side, frame):
    for index, (a, b) in enumerate(WINDOWS[side]):
        if a <= frame <= b:
            return index
    return None


def _swing_u(s):
    s = max(0.0, min(1.0, s))
    return 1.0 - (1.0 - s) ** SWING_POW


def ankle_targets(frame, shift):
    """返回 {"L": (x, y, z), ...}（世界，米）。支撑期钉死，摆动期抬脚。"""
    out = {}
    for side in SIDES:
        idx = window_of(side, frame)
        if idx is not None:
            base = FLAT_ANK[(side, idx)]
            out[side] = (base[0], base[1], base[2] + shift[side])
            continue
        if side == "L":
            off, on, t0, t1 = FLAT_ANK[("L", 0)], FLAT_ANK[("L", 1)], T_L_OFF, T_L_ON
            lift = L_LIFT
        else:
            off, on, t0, t1 = FLAT_ANK[("R", 0)], FLAT_ANK[("R", 1)], T_R_OFF, T_R_ON
            lift = R_LIFT
        s = (frame - t0) / float(t1 - t0)
        u = _swing_u(s)
        base_off = ANKLE_0[side]
        x = base_off[0] + (on[0] - off[0]) + (off[0] - base_off[0])
        # 用 FLAT_ANK 的两端插值（x 不变，y/z 走抬脚曲线）
        x = off[0] + (on[0] - off[0]) * u
        y = off[1] + (on[1] - off[1]) * u
        z = off[2] + (on[2] - off[2]) * u + lift * math.sin(math.pi * s) ** 1.35
        out[side] = (x, y, z)
        del x
    return out


def sole_target(frame):
    """该帧每只脚**期望的鞋底离地量**（米）。None = 不闭环（摆动脚自己管）。"""
    out = {}
    for side in SIDES:
        out[side] = 0.0 if window_of(side, frame) is not None else None
    return out


# =============================================================== 姿态装配
def _arm_section(arm, pose, frame):
    if frame <= HOLD_END:
        for side in SIDES:
            info = ARM_SEAT_CLAMP.setdefault(
                side, {"any": False, "worst_frame": None, "worst_over_mm": 0.0,
                       "worst_dist_mm": 0.0, "limit_mm": 0.0, "n_frames": 0})
            clamp, dist_mm, limit_mm = G4.arm_seat(
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

    # ★ 释放后：**单段减速**欧拉插值（文件头第 1 件）——
    #   所有通道共用同一个 q(frame) ⟹ 步长 = |Δ|·Δq，Δq 单调不增。
    q = q_of(frame)
    for bone in ARM_BONES:
        target = JS._unwrap_xyz(E0.get(bone), E_FLY[bone])
        pose[bone] = _lerp3(E0[bone], target, q)


def build_pose(arm, frame, shift):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)

    targets = ankle_targets(frame, shift)
    for side in SIDES:
        x, y, z = targets[side]
        G4.leg_seat(arm, pose, side, (x, y, z), IDLE_KNEE_DIR[side])

    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    _arm_section(arm, pose, frame)

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
        # E0 = 释放前一帧的**真值**（手臂已由 arm_seat 解到抓取点）。
        # 手臂不在 _HIT_FROZEN 里，故这里必须从 pose 取，不能从冻结表取。
        E0.clear()
        for bone in ARM_BONES:
            E0[bone] = tuple(pose[bone])

    # 手指：自命中帧起**握力逐渐松开**（q 通道，随收招单调变化）
    k = 1.0 - 0.45 * q_of(frame)
    for name, value in A.FIST.items():
        pose[name] = (value[0] * k, 0.0, 0.0)

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
    """逐帧实测贴地闭环（对**支撑脚**闭环）。"""
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
        ALL_SOLE[frame] = {
            side: (None if low[side] is None
                   else round(low[side][2] * 1000.0, 2))
            for side in SIDES}
    return pose


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
               "neck": tuple(A.bone_world(arm, "neck", "head")),
               "head": tuple(A.bone_world(arm, "head", "head")),
               "head_tail": tuple(A.bone_world(arm, "head", "tail"))}
        low = A.foot_lowest_by_side()
        for side in SIDES:
            row["ankle_" + side] = tuple(A.bone_world(arm, "foot." + side,
                                                     "head"))
            row["sole_" + side] = (None if low[side] is None
                                   else low[side][2])
            row["reach_" + side] = ((Vector(row["ankle_" + side])
                                     - Vector(row["pelvis"])).length)
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


def pivot_series(arm, action, tracked):
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


def arm_world_steps(arm, action):
    mats = {}
    for frame in range(0, TOTAL + 1):
        raw = RS.action_world_matrices(arm, action, frame)
        mats[frame] = {
            name: __import__("mathutils").Matrix(
                [raw[name][i * 4:i * 4 + 3] for i in range(3)])
            for name in ARM_BONES + ("pelvis", "spine_01", "spine_02", "chest",
                                     "neck", "head") if name in raw}
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


# =============================================================== 专属门禁
def throw_assertions(arm, action, samples, foots, tracks):
    from mathutils import Matrix
    res = {}
    pelvis = [Vector(f["pelvis"]) for f in foots]
    py = [p.y * 1000.0 for p in pelvis]
    pz = [p.z * 1000.0 for p in pelvis]
    hand_mid = [Vector(f["hand_L_tail"]).lerp(Vector(f["hand_R_tail"]), 0.5)
                for f in foots]

    # ---- 0) 上游接缝：C06@0 必须逐位等于 Grab_Hold@120
    mats0 = RS.action_world_matrices(arm, action, 0)
    delta0 = RS.matrix_delta(mats0, SRC_MATS)
    res["seam_source"] = [SRC_ACTION, SRC_FRAME]
    res["throw_start_delta"] = float("%.3e" % delta0)
    res["throw_start_ok"] = delta0 <= SEAM_TOL
    res["root_motion_m"] = [0.0, round((pelvis[-1].y - pelvis[0].y), 6)]
    res["root_motion_ok"] = abs(abs(res["root_motion_m"][1]) * 1000.0
                                - D_TOTAL_MM) <= 1.0
    res["advance_total_mm"] = round((pelvis[0].y - pelvis[-1].y) * 1000.0, 3)

    # ---- 1) 抓取点（沿用 C04/C05 登记值，释放前不许动）
    res["grabbed_points_m"] = {s: [round(v, 6) for v in GRAB_POINT[s]]
                               for s in SIDES}
    res["grab_gap_mm"] = round(
        (Vector(GRAB_POINT["L"]) - Vector(GRAB_POINT["R"])).length * 1000.0, 2)
    res["grab_z_mm"] = round(
        (GRAB_POINT["L"].z + GRAB_POINT["R"].z) * 0.5 * 1000.0, 2)
    res["grab_depth_mm"] = round(
        ((GRAB_POINT["L"].y + GRAB_POINT["R"].y) * 0.5 - pelvis[0].y) * 1000.0,
        2)

    # ---- 2) 释放帧：存在且**唯一**
    drift = {}
    for side in SIDES:
        ref = Vector(GRAB_POINT[side])
        drift[side] = [round((Vector(foots[f]["hand_" + side + "_tail"])
                              - ref).length * 1000.0, 5)
                       for f in range(0, TOTAL + 1)]
    dmax = [max(drift["L"][f], drift["R"][f]) for f in range(0, TOTAL + 1)]
    released = [f for f in range(0, TOTAL + 1) if dmax[f] > RELEASE_EPS_MM]
    res["hold_drift_max_mm"] = round(max(dmax[0:HOLD_END + 1]), 5)
    res["hold_drift_ok"] = max(dmax[0:HOLD_END + 1]) <= GRAB_HOLD_DRIFT_MAX_MM
    res["release_frame_found"] = (None if not released else min(released))
    res["release_frame_want"] = RELEASE
    res["release_frame_ok"] = bool(released) and min(released) == RELEASE
    res["release_drift_after_mm"] = (None if not released
                                     else round(dmax[min(released)], 4))
    res["release_hand_L_m"] = [round(v, 6) for v in foots[HOLD_END]["hand_L_tail"]]
    res["release_hand_R_m"] = [round(v, 6) for v in foots[HOLD_END]["hand_R_tail"]]
    res["release_pelvis_m"] = [round(v, 6) for v in foots[HOLD_END]["pelvis"]]

    # ---- 3) 可达比 & 逆解不许截断
    arm_len = {}
    ratio = {}
    for side in SIDES:
        total = (ARM_LEN[side]["upper"] + ARM_LEN[side]["forearm"]
                 + ARM_LEN[side]["hand"])
        arm_len[side] = round(total * 1000.0, 3)
        ratio[side] = round(max(float(f["armreach_" + side])
                                for f in foots[0:HOLD_END + 1]) / total, 5)
    res["arm_total_len_mm"] = arm_len
    res["grab_reach_ratio"] = ratio
    res["grab_reach_ok"] = all(v <= GRAB_REACH_MAX_RATIO
                               for v in ratio.values())
    res["arm_seat_clamped"] = {s: bool(v.get("any"))
                               for s, v in ARM_SEAT_CLAMP.items()}
    res["arm_seat_detail"] = {s: dict(v) for s, v in ARM_SEAT_CLAMP.items()}
    res["arm_seat_ok"] = not any(v.get("any")
                                 for v in ARM_SEAT_CLAMP.values())
    res["hand_reach_min_mm"] = {
        s: round(min(float(f["armreach_" + s]) for f in foots
                     if f["frame"] <= HOLD_END) * 1000.0, 2) for s in SIDES}

    # ---- 4) ★ 髋部发力（本支核心判据 1）
    pel_e = [s["euler"].get("pelvis", (0.0, 0.0, 0.0)) for s in samples]
    hip_norm = [math.sqrt(sum(v * v for v in e)) for e in pel_e]
    torso_norm = []
    for s in samples:
        vals = [math.sqrt(sum(v * v for v in s["euler"].get(n, (0.0, 0.0, 0.0))))
                for n in ("spine_01", "spine_02", "chest")]
        torso_norm.append(max(vals))
    hip_peak = max(hip_norm)
    torso_peak = max(torso_norm)
    res["hip_peak_deg"] = round(hip_peak, 3)
    res["hip_peak_frame"] = int(hip_norm.index(hip_peak))
    res["torso_peak_deg"] = round(torso_peak, 3)
    res["hip_drive_ratio"] = round(hip_peak / torso_peak, 4)
    res["hip_drive_ok"] = res["hip_drive_ratio"] > HIP_DRIVE_MIN

    hip_step = [0.0] + [
        G4._local_step_deg(pel_e[i - 1], pel_e[i])
        for i in range(1, len(pel_e))]
    hand_step = [0.0] + [
        (hand_mid[i] - hand_mid[i - 1]).length * 1000.0
        for i in range(1, len(hand_mid))]
    hip_spd = max(hip_step)
    hand_spd = max(hand_step)
    res["hip_spd_peak_deg"] = round(hip_spd, 3)
    res["hip_spd_peak_frame"] = int(hip_step.index(hip_spd))
    res["hand_spd_peak_mm"] = round(hand_spd, 3)
    res["hand_spd_peak_frame"] = int(hand_step.index(hand_spd))
    res["hip_lead_frames"] = (res["hand_spd_peak_frame"]
                              - res["hip_spd_peak_frame"])
    res["hip_then_arm_ok"] = res["hip_lead_frames"] >= HIP_LEAD_MIN_FRAMES

    # ---- 5) ★ 抛出弧：释放后单调外抛（向前 + 向上），无反向帧
    fwd = [-p.y * 1000.0 for p in hand_mid]
    apex = RELEASE + max(range(0, TOTAL - RELEASE + 1),
                         key=lambda k: fwd[RELEASE + k])
    res["throw_apex_frame"] = apex
    seg = fwd[RELEASE:apex + 1]
    steps = [seg[i + 1] - seg[i] for i in range(len(seg) - 1)]
    res["throw_arc_steps_mm"] = [round(v, 3) for v in steps]
    res["throw_arc_forward_mm"] = round(seg[-1] - seg[0], 3)
    res["throw_arc_back_frames"] = sum(1 for v in steps if v < -LIN_TOL_MM)
    res["throw_apex_span"] = apex - RELEASE
    res["throw_arc_ok"] = bool(
        res["throw_apex_span"] >= 3
        and res["throw_arc_forward_mm"] >= THROW_FWD_MIN_MM
        and res["throw_arc_back_frames"] == 0)

    # ---- 6) ★ 重量沉降：抛出后骨盆继续前冲 ≥20 mm，且前冲步长单调不增
    tail_y = py[RETURN_START:TOTAL + 1]
    res["pelvis_after_release_mm"] = round(py[RELEASE] - min(tail_y), 3)
    fwd_steps = [py[i - 1] - py[i] for i in range(RETURN_START, TOTAL + 1)]
    res["settle_steps_mm"] = [round(v, 4) for v in fwd_steps]
    mono = all(fwd_steps[i + 1] <= fwd_steps[i] + 1e-9
               for i in range(len(fwd_steps) - 1))
    res["settle_steps_monotone"] = mono
    res["weight_settle_ok"] = bool(
        res["pelvis_after_release_mm"] >= WEIGHT_SETTLE_MIN_MM and mono)

    # ---- 7) 支撑脚 / 鞋底 / 支撑覆盖
    pivot = {}
    sole = {}
    for side in SIDES:
        for idx, (a, b) in enumerate(WINDOWS[side]):
            pts = [tracks[(side, idx)][f] for f in range(max(a, 0), b + 1)
                   if tracks[(side, idx)][f] is not None]
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            pivot["%s_w%d_mm" % (side, idx)] = round(
                math.hypot(max(xs) - min(xs), max(ys) - min(ys)) * 1000.0, 4)
            zs = [foots[f]["sole_" + side] for f in range(max(a, 0), b + 1)
                  if foots[f]["sole_" + side] is not None]
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
    air = {}
    for side in SIDES:
        vals = AIR_SOLE.get(side, [])
        air[side] = None if not vals else round(min(vals) * 1000.0, 3)
    res["air_sole_min_mm"] = air
    res["swing_airborne_ok"] = all(v is not None and v > 0.0
                                   for v in air.values())

    # ---- 8) 顿感
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
    res["hitstop_present_ok"] = bool(frozen) and max(frozen) <= 1e-6
    res["hitstop_momentum_mm"] = round(
        (pelvis[HIT].y - pelvis[HOLD_END].y) * 1000.0, 3)
    res["hitstop_keeps_momentum_ok"] = res["hitstop_momentum_mm"] > 10.0
    res["hitstop_frames"] = HOLD
    res["hitstop_frames_ok"] = 2 <= HOLD <= 4
    res["antic_frames"] = ANTIC
    res["antic_frames_ok"] = 12 <= ANTIC <= 20

    # ---- 9) 躯干/髋的沉与升（"髋部发力"的可见形态）
    res["pelvis_z_min_mm"] = round(min(pz), 2)
    res["pelvis_z_max_mm"] = round(max(pz), 2)
    res["pelvis_sink_mm"] = round(pz[0] - pz[ANTIC], 2)
    res["pelvis_sink_ok"] = pz[ANTIC] < pz[0]
    res["pelvis_rise_mm"] = round(pz[HIT] - pz[ANTIC], 2)
    res["pelvis_rise_ok"] = pz[HIT] > pz[ANTIC]

    # ---- 10) 力矩链（脚→腿→髋→腰→肩→手 五通道都有非零关键帧）
    keys = ("pelvis", "spine_01", "spine_02", "chest", "shoulder.L",
            "shoulder.R", "thigh.L", "shin.L", "thigh.R", "shin.R")
    channel = {}
    for name in keys:
        vals = [s["euler"].get(name, (0.0, 0.0, 0.0)) for s in samples]
        channel[name] = round(max(max(abs(v) for v in item) for item in vals), 3)
    res["power_chain_channels_deg"] = channel
    res["power_chain_ok"] = all(v > 0.5 for v in channel.values())

    # ---- 11) 腿可达
    limit = A.L_THIGH + A.L_SHIN
    ratios = {}
    for side in SIDES:
        ratios[side] = round(max(f["reach_" + side] for f in foots) / limit, 5)
    res["leg_reach_max_ratio"] = ratios
    res["ik_reach_ok"] = all(v <= REACH_MAX_RATIO for v in ratios.values())

    # ---- 12) 收招：单一减速段（不许任何过冲）
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
    res["return_tail_head"] = tails[:8]
    res["decel_smooth_ok"] = bool(
        tails and all(tails[i + 1] <= tails[i] + 1e-9
                      for i in range(len(tails) - 1)))
    res["no_snap_stop_ok"] = bool(tails and tails[-1] <= 5.0
                                  and tails[-1] <= tails[0])
    res["return_tail_zero_frames"] = sum(1 for t in tails if t <= 1e-9)

    # ---- 13) 物理口径的"瞬移"（登记项）
    worst_local = 0.0
    worst_local_at = None
    for index in range(1, len(samples)):
        ea = samples[index - 1]["euler"]
        eb = samples[index]["euler"]
        for name in set(ea) | set(eb):
            here = G4._local_step_deg(ea.get(name, (0.0, 0.0, 0.0)),
                                      eb.get(name, (0.0, 0.0, 0.0)))
            if here > worst_local:
                worst_local, worst_local_at = here, (samples[index]["frame"],
                                                     name)
    res["local_step_max_deg"] = round(worst_local, 3)
    res["local_step_max_at"] = (None if worst_local_at is None
                                else [worst_local_at[0], worst_local_at[1]])

    # ---- 14) 末帧跟随姿登记（本支**不设**下游接缝门禁，见文件头第 1 件）
    res["end_pose_note"] = ("收招 = 单向减速到「投掷跟随姿」（不许过冲 ⟹ 不回 Idle）；"
                            "末帧姿态登记在 Action 自定义属性 end_pose_deg 里。")
    res["end_hand_mid_m"] = [round(v, 6) for v in hand_mid[-1]]
    res["end_pelvis_m"] = [round(v, 6) for v in pelvis[-1]]
    res["end_vs_idle_orient_delta"] = float("%.3e" % LOG.get("end_vs_idle", 0.0))
    return res


# =============================================================== 标定
def measure_pivot(arm, side, ankle_xy, z_probe, torso):
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


def solve_fly_arm(arm):
    """在**跟随姿的躯干 + 腿**上把手臂摆到 `FLY_DIR`，解出该上下文下的欧拉角。

    为什么必须这样解而不是手写角度：`pose_bone.matrix` 是**父链相关**的，
    同一个世界方向在不同躯干姿态下对应不同欧拉角。跟随姿的躯干是固定的
    （`END_ROT`），所以在这一上下文里解一次即可，末帧逐位复现。
    """
    pose = torso_pose(TOTAL)
    A.apply_pose(arm, pose)
    for side in SIDES:
        base = FLAT_ANK[(side, 1)]
        G4.leg_seat(arm, pose, side, base, IDLE_KNEE_DIR[side])
    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
    for bone in ARM_BONES:
        pose[bone] = JS._unwrap_xyz(
            None, G4.aim_bone_ref(arm, bone, FLY_DIR[bone],
                                  IDLE_BASIS[bone], IDLE_DIR[bone]))
    E_FLY.clear()
    for bone in ARM_BONES:
        E_FLY[bone] = tuple(pose[bone])
        E_FLY_DIR_ACH[bone] = tuple(A.bone_direction(arm, bone))


# =============================================================== 主流程
def main():
    global SEAM_POSE, SEAM_EULER, PY0, Z_SEAM, IDLE_POSE, IDLE_PELVIS
    global ANKLE_0, ANKLE_1, SRC_MATS, SRC_META, PIVOT_AXIS, PIVOT_SCALE
    global PELVIS_X, PELVIS_Z, PELVIS_RX, PELVIS_RY
    global SPINE01_RX, SPINE01_RY, SPINE02_RX, SPINE02_RY, CHEST_RX, CHEST_RY
    global NECK_RX, NECK_RY, HEAD_RX, HEAD_RY
    global SHOULDER_L_RX, SHOULDER_R_RX, SHOULDER_L_RZ, SHOULDER_R_RZ

    for store in (ARM_SEAT_CLAMP, WINDOW_SOLE, AIR_SOLE, ALL_SOLE,
                  PIVOT, PIVOT_VERT, FLAT_ANK, GRAB_POINT, GRAB_SHOULDER,
                  GRAB_ELBOW, ARM_REF, E0, E_FLY, E_FLY_DIR_ACH,
                  _HIT_FROZEN, LOG):
        store.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    for module, label in ((I1, "Idle_01"), (G4, "Grab_Start"), (G5, "Grab_Hold")):
        if module.NAME not in bpy.data.actions:
            print("C06_BOOTSTRAP 动画工程缺 %s，先补跑" % label)
            module.main()
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

    # ---- 上游接缝：直接读 `Grab_Hold@120` 的**真值**
    scene = bpy.context.scene
    src = bpy.data.actions[SRC_ACTION]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    scene.frame_set(SRC_FRAME)
    bpy.context.view_layer.update()
    SEAM_EULER = {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
                  for b in arm.pose.bones}
    SEAM_POSE = {name: value for name, value in SEAM_EULER.items()}
    SEAM_POSE["@loc"] = {"pelvis": tuple(arm.pose.bones["pelvis"].location)}
    SEAM_POSE.update(A.FIST)
    PY0 = A.bone_world(arm, "pelvis", "head").y
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z + 0.0  # 骨盆世界 z
    ANKLE_0 = {s: A.bone_world(arm, "foot." + s, "head").copy() for s in SIDES}
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
    SRC_MATS = RS.action_world_matrices(arm, src, SRC_FRAME)
    SRC_META = {}
    for key in ("grabbed_point_L_m", "grabbed_point_R_m", "grab_frame",
                "grab_hold_frame"):
        try:
            value = src[key]
            SRC_META[key] = value
        except (KeyError, TypeError):
            SRC_META[key] = None

    # ---- Idle 站架与骨基座（`leg_seat` / `aim_bone_ref` 的缺省基准）
    arm.animation_data.action = bpy.data.actions[I1.NAME]
    A._bind_slot(arm, bpy.data.actions[I1.NAME])
    scene.frame_set(0)
    bpy.context.view_layer.update()
    IDLE_POSE = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, IDLE_POSE)
    bpy.context.view_layer.update()
    IDLE_PELVIS = A.bone_world(arm, "pelvis", "head").copy()
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
    G4.IDLE_BASIS.clear()
    G4.IDLE_BASIS.update(IDLE_BASIS)
    G4.IDLE_DIR.clear()
    G4.IDLE_DIR.update(IDLE_DIR)
    G4.IDLE_KNEE_DIR.clear()
    G4.IDLE_KNEE_DIR.update(IDLE_KNEE_DIR)
    G4.ARM_LEN.clear()
    for side in SIDES:
        G4.ARM_LEN[side] = dict(ARM_LEN[side])

    # ---- 躯干轨道：frame 0 回填上游接缝真值（C01 第 1 件：必须 global）
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
    PELVIS_X = ((0, SEAM_POSE["@loc"]["pelvis"][0]),) + tuple(
        k for k in PELVIS_X if k[0] != 0)
    PELVIS_Z = ((0, Z_SEAM),) + tuple(k for k in PELVIS_Z if k[0] != 0)

    # ---- 落脚点：起点 = 首帧踝；终点 = 起点 + 前冲量（站架宽度不变）
    ANKLE_1 = {s: Vector((ANKLE_0[s].x, ANKLE_0[s].y - D_TOTAL_MM / 1000.0,
                          ANKLE_0[s].z)) for s in SIDES}

    A.report("C06_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "antic": ANTIC, "hit": HIT, "hold": HOLD, "hold_end": HOLD_END,
        "release": RELEASE, "return_start": RETURN_START, "settle": SETTLE,
        "cancel": CANCEL, "advance_mm": round(D_TOTAL_MM, 3),
        "foot_schedule": {"L": [[a, b] for a, b in WINDOWS["L"]],
                          "R": [[a, b] for a, b in WINDOWS["R"]]},
        "seam_source": [SRC_ACTION, SRC_FRAME],
        "pelvis_y0_mm": round(PY0 * 1000.0, 3),
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                      for s in SIDES},
        "ankle1_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_1[s]]
                      for s in SIDES},
        "grabbed_points_m": {s: [round(v, 6) for v in GRAB_POINT[s]]
                             for s in SIDES},
        "end_rot_deg": END_ROT,
        "note": ("投掷：首帧 = `Grab_Hold@120`（逐位）；双手逆解钉死在世界抓取点"
                 "到 f30，f31 释放；髋部 ry −20° → +26° 为发力主通道；"
                 "收招 = 单向减速到「跟随姿」。"),
    })

    # ---- 支点 + 平放踝高标定
    calib = {}
    torso_seam = {"pelvis": (RS.track(PELVIS_RX, 0), 0.0, 0.0),
                  "@loc": {"pelvis": A.wloc(0.0, PY0, Z_SEAM - 0.900)}}
    torso_end = torso_pose(TOTAL)
    _axis_world = (arm.matrix_world.to_3x3()
                   @ Vector((1.0, 0.0, 0.0))).normalized()
    for key, torso, xy, probe in (
            (("L", 0), torso_seam, ANKLE_0["L"], ANKLE_0["L"].z),
            (("R", 0), torso_seam, ANKLE_0["R"], ANKLE_0["R"].z),
            (("L", 1), torso_end, ANKLE_1["L"], ANKLE_1["L"].z),
            (("R", 1), torso_end, ANKLE_1["R"], ANKLE_1["R"].z)):
        px, py, pz, ax0, ay0, az0, vobj, vindex = measure_pivot(
            arm, key[0], (xy.x, xy.y), probe, torso)
        PIVOT[key] = (px, py, pz)
        PIVOT_VERT[key] = (vobj, vindex)
        FLAT_ANK[key] = (ax0, ay0, az0)
        PIVOT_AXIS[key] = _axis_world
        calib["%s_w%d" % key] = {
            "pivot_mm": [round(px * 1000.0, 2), round(py * 1000.0, 2),
                         round(pz * 1000.0, 3)],
            "ankle_flat_mm": [round(ax0 * 1000.0, 2), round(ay0 * 1000.0, 2),
                              round(az0 * 1000.0, 2)]}
    A.report("C06_CALIBRATION", {
        "per_window": calib,
        "arm_len_mm": {s: {k: round(v * 1000.0, 3) for k, v in d.items()}
                       for s, d in ARM_LEN.items()},
        "note": "本支不踮脚（tip ≡ 0）⟹ 踝目标完全由 FLAT_ANK 决定。",
    })

    # ---- 跟随姿手臂欧拉（一次性解算）
    solve_fly_arm(arm)
    A.report("C06_FLY", {
        "fly_dir": FLY_DIR,
        "fly_euler_deg": {k: [round(v, 4) for v in E_FLY[k]]
                          for k in ARM_BONES},
        "achieved_dir": {k: [round(v, 6) for v in E_FLY_DIR_ACH[k]]
                         for k in ARM_BONES},
        "note": "跟随姿 = 双臂向前（−y）+ 微下（−z）伸展；收招终点逐位复现。",
    })

    # ---- 建帧
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
        "note": ("投掷：接 `Grab_Hold@120`（逐位）；双手位置逆解钉死在 C04 登记的"
                 "世界抓取点到释放帧（f31）；髋部 ry −20° → +26° 为发力主通道；"
                 "释放后双臂单向减速伸展到「跟随姿」（不许过冲，故不回 Idle）。"
                 "Root Motion 前冲 %.3f m。" % (D_TOTAL_MM / 1000.0)),
        "antic_frame": ANTIC,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HOLD,
        "release_frame": RELEASE,
        "root_motion_m": [0.0, round(-D_TOTAL_MM / 1000.0, 4)],
        "inherit_from": "Grab_Hold@%d" % SRC_FRAME,
        "grabbed_point_L_m": [round(v, 6) for v in GRAB_POINT["L"]],
        "grabbed_point_R_m": [round(v, 6) for v in GRAB_POINT["R"]],
        "hit_point_m": None,
        "end_pose_deg": {k: [round(v, 4) for v in val]
                         for k, val in sorted(END_ROT.items())},
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "ANTIC": ANTIC, "HIT": HIT, "HOLD_END": HOLD_END,
        "RELEASE": RELEASE, "RECOV": RETURN_START, "SETTLE": SETTLE,
        "CANCEL": CANCEL, "R_OFF": T_R_OFF, "R_ON": T_R_ON,
        "L_OFF": T_L_OFF, "L_ON": T_L_ON, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    if os.environ.get("C06_TRACE") == "1":
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for f in foot_series(arm, action, meshes):
            print("C06_TRACE " + json.dumps({
                "f": f["frame"], "q": round(q_of(f["frame"]), 5),
                "pelvis_y": round(f["pelvis"][1] * 1000.0, 2),
                "pelvis_z": round(f["pelvis"][2] * 1000.0, 2),
                "L_sole": (None if f["sole_L"] is None
                           else round(f["sole_L"] * 1000.0, 3)),
                "R_sole": (None if f["sole_R"] is None
                           else round(f["sole_R"] * 1000.0, 3)),
                "L_reach": round(f["reach_L"] / limit_mm, 4),
                "R_reach": round(f["reach_R"] / limit_mm, 4),
                "handL": [round(v * 1000.0, 2) for v in f["hand_L_tail"]],
                "handR": [round(v * 1000.0, 2) for v in f["hand_R_tail"]],
                "armL_r": round(f["armreach_L"] * 1000.0, 2),
                "armR_r": round(f["armreach_R"] * 1000.0, 2),
            }))

    report = A.run_common_assertions(samples, meta, foot_probe=())
    foots = foot_series(arm, action, meshes)
    tracks = pivot_series(arm, action, dict(PIVOT_VERT))
    report.update(throw_assertions(arm, action, samples, foots, tracks))

    # 末帧 vs Idle（诊断，不判红；本支有意不回 Idle）
    mats_end = RS.action_world_matrices(arm, action, TOTAL)
    moving = set()
    for bone in arm.pose.bones:
        node = bone
        while node is not None:
            if node.name == "pelvis":
                moving.add(bone.name)
                break
            node = node.parent
    ori, rel, _ob, _rb = G4.pose_seam_split(mats_end, SRC_MATS, moving)
    LOG["end_seam_orient"] = ori
    LOG["end_seam_rel"] = rel
    report["end_vs_start_orient_delta"] = float("%.3e" % ori)
    report["end_vs_start_rel_delta"] = float("%.3e" % rel)
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
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C06_REPORT", report)

    if not SKIP_RENDER:
        # ★ 第 1 轮实测教训：**不许照抄 C04 的 `cam_dy = -0.55 × 总位移`**。
        #   那条公式的前提是"起手在原点"（C04 成立），而 C06 起手继承 C05
        #   的持握姿、骨盆已在 y = −539 mm、双手在 −1374 mm。照抄会让机位
        #   中心停在 −148 mm，角色整体落到画幅外 —— 第 1 轮 18 张图全部把
        #   角色切掉半边（清单 §3 里"取景跟随用 C04 的 cam_dy"这条建议
        #   对本支是反例，已在日志里更正）。
        #   正解：机位中心取**本支全部帧的 y 包围盒中心**（骨盆 + 双手尾巴
        #   共同参与），跨度决定 ortho_scale ⟹ 首帧的手、末帧的手、以及
        #   全部骨盆位置一定同框。
        ys = []
        for f in foots:
            ys.append(f["pelvis"][1])
            ys.append(f["hand_L_tail"][1])
            ys.append(f["hand_R_tail"][1])
        cam_cy = 0.5 * (min(ys) + max(ys))
        span = max(ys) - min(ys)
        scale = max(2.60, span * 1.75)
        A.report("C06_CAM", {"cam_center_y_m": round(cam_cy, 4),
                             "y_span_m": round(span, 4),
                             "ortho_scale": round(scale, 3),
                             "y_min_m": round(min(ys), 4),
                             "y_max_m": round(max(ys), 4)})
        for base in (A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q):
            name, location, target, _scale, res_v = base
            view = (name, (location[0], location[1] + cam_cy, 0.92),
                    (target[0], target[1] + cam_cy, 0.92), scale, res_v)
            A.render_pose_sheet(arm, action,
                                [0, ANTIC, HIT, RELEASE, SETTLE, TOTAL],
                                "throw06", views=(view,))
    A.save_project()
    A.export_glb(arm)
    print("C06_DONE failed=%s" % report["failed"])
    print("C06_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C06_FAILURE " + traceback.format_exc())
