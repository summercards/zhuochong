"""anim_charge08 —— C08 `Charge` 蓄力（C 族第八支，**三段：起手 / 循环 / 释放**）。

=============================================================================
清单原文
=============================================================================
「双腿扎稳、身体下沉、肌肉发力，可分 起手 / 循环 / 释放 三段。」

=============================================================================
第 0 件 —— ★ 分段形态的决定：**两个 Action**，不是"一个 Action 切三段"
=============================================================================
清单 C08 计划 §3 明确要求「先量清楚再决定，不要直接假设 `loop_seamless` 能在一个
三段 Action 上成立」。量完的结论：

* `charge_loop_ok` 的字面要求是 **`loop=true` 且 `loop_seamless` 为 True**。
* 一个装了「起手 + 循环 + 释放」的 Action 在语义上**不是**循环的：它从 `Idle_01@0`
  起、到「半蹲戒备」止。给它挂 `loop=true` 是撒谎，挂 `loop=false` 则 `charge_loop_ok`
  无从成立。

⟹ **两支 Action**：

| Action | 帧 | loop | 作用 |
|---|---|---|---|
| `Charge` | 0 ~ 100（1.667 s） | false | **主片段**：起手 + 循环 + 释放 + 收招，起于 `Idle_01@0`（逐位） |
| `Charge_Loop` | 循环窗 36 帧（0.600 s） | **true** | 引擎按住按键时复核的循环段；**逐帧位相同于主片段的循环窗** |

`Charge_Loop` 不是"另做一遍"——它**逐帧复用**主片段循环窗的姿态字典
（`KEYFRAMES[LOOP_IN:LOOP_OUT+1]` 原样搬进第二个 Action）⟹ 首末帧逐位一致的
构造性来源；不重新解算，就没有"两次解算差一点点"的可能。

帧结构（`@60fps`）：

    f0 ──起手 20f──> f20 ──循环 36f──> f56 ──释放 16f──> f72(命中)
      ──命停 3f──> f74 ──收招 21f──> f96 ──静止 4f──> f100

    起手 20 帧 = 0.333 s（§0.1 重攻击前摇 12~20 的**上界**，蓄力下沉是"慢启动"）
    循环 36 帧 = 0.600 s（3 个 5 Hz 颤振周期，见第 3 件）
    释放 16 帧 = 0.267 s（线性爆发，见第 4 件）
    命停  3 帧 = 0.050 s（§0.1 的 2~4 帧区间内）

=============================================================================
第 1 件 —— 首帧 = `Idle_01@0`，逐位（`SEAM_TOL = 1e-6`）
=============================================================================
读 `Idle_01` Action 在 f0 的**真值**（全 57 骨的 `rotation_euler` + `pelvis.location`），
不做任何解算；`patch()` 把躯干/骨盆轨道的 f0 回填成同一批值。

★ 末帧**有意不回** `Idle_01@0`（同 C07 第 1 件）：末帧是「半蹲戒备」
（骨盆 z 800 mm、双拳护在胸腹前），引擎侧混回 Idle 即可。理由：
本支腿部走 `leg_seat`（三维 IK），而 `Idle_01` 的腿走 `leg_ik`（平面解析），
两者世界方向一致但**欧拉滚转不逐位一致** ⟹ 强行"末帧 = Idle" 会被逐位门禁打回。
末帧姿态登记在 Action 自定义属性 `end_pose_deg`。

=============================================================================
第 2 件 —— ★「身体下沉」与「腿不爆」：实测下来这两个根本**不冲突**
=============================================================================
清单 C08 计划把「'身体下沉'与'腿不爆'的冲突」列为核心难点（抬骨盆举高的反向约束，
C07 教训 4）。`probe_c08_baseline.py` 实测（`C08PROBE_SINK` / `C08PROBE_RISE`）：

| 骨盆 z (mm) | 腿可达比 L / R | 读法 |
|---|---|---|
| 830（Idle） | 0.938 / 0.931 | 站架起点 |
| 730（**下沉 100 mm**） | 0.820 / 0.812 | ★ 下沉**降低**可达比 —— 不冲突 |
| 610（下沉 220 mm） | 0.680 / 0.670 | 还能继续沉 |
| 850 | 0.962 / 0.955 | —— |
| 870 | **0.985** / 0.978 | 上顶的实际上限 |
| 890 | 0.9995（**被截断**） | 踝误差 7.88 mm ⟹ 支撑脚开始滑 ✗ |

**根因**：踝钉死时，骨盆下沉缩短的是"髋→踝"距离 ⟹ 可达比**下降**。
清单里担心的反向约束只对**抬骨盆**成立（C07 举高顶），对**下沉**不成立。
⟹ 本支的真正约束是**释放段上顶的上限**（≤ 875 mm），不是下沉的下限。

本支取值：`PZ_SUNK = 730 mm`（下沉 **100 mm** ≥ 门禁 80 mm）、
`PZ_BURST = 850 mm`、命停期再往上爬 12 mm ⟹ 峰值 **862 mm**，
对应可达比 ≈ 0.976（余量 0.019）—— 留足，不用凑。

=============================================================================
第 3 件 —— ★ 循环段的「肌肉发力」放哪里：**不在骨盆，不在拳头**
=============================================================================
三条门禁把循环段的自由量钉死了：

| 门禁 | 判据 | 反推的振幅上限 |
|---|---|---|
| `charge_sink_pose_ok` | 循环段骨盆 z 的**标准差 ≤ 2 mm** | 骨盆 z 振幅 ≤ 2.83 mm（取 2.0） |
| `charge_arm_hold_ok` | 循环段**双拳**世界漂移 ≤ **8 mm** | 肩→拳 ~0.65 m ⟹ 上游总转角 ≲ 0.35° |
| `charge_stance_ok` | 循环段 `plant_drift ≤ 3 mm`、`sole ∈ [−2, +6]` | 踝基本不许动 |

★ 肩→拳 0.65 m ⟹ **1° 的上游转角对拳头就是 11 mm**，所以"拳头颤动"这种
最直觉的做法**一次就用光 8 mm 预算**。而"骨盆上下颠"又被 2 mm 标准差堵死。

⟹ 设计：把可见的颤振放在**头颈**（离拳最远、且没有门禁），
上身与骨盆只做 0.2~0.25° / 2 mm 的"绷紧微振"：

    pelvis   x ±1.0 mm、z ±2.0 mm     （z 的标准差 1.41 mm ✓）
    chest    rx ±0.25°
    neck     rx ±2.2°、head rx ±1.4°   ← 可见的"咬牙发力"全在这里
    双拳     不额外加扰动（"握死"）

颤振用 `sin(2π·K·u)`（K = 3 ⟹ 5 Hz，36 帧里三个整周期）。`sin(2πK)` 在浮点上
**不精确等于 0**（≈ −7.3e−16）⟹ 两端显式置 `s = 0.0`，让循环首末帧**逐位相同**
（不是"小于容差"，是同一个浮点数）。同时 `sin` 的导数在 u=0 / u=1 相等
⟹ 循环接缝处速度也连续，引擎处不会"顿一下"。

=============================================================================
第 4 件 —— 释放段：线性爆发 + 命停期"力还在往上冲"
=============================================================================
* 手臂走**方向链**（`arm_basis` 四元数 slerp，C07 第 4 件的构造），
  不用逐帧 `aim_bone_ref` 反解（本支手臂摆幅 ~140°，尚未到 C07 的反向病态区，
  但 slerp 路径 = 测地线，没有病态点，白送）。
* 释放段用 **linear** 插值：`accel` 会把峰值单帧步长堆到末帧（C07 教训 4 的鞍点）。
  线性 = 每帧步长恒定 ~8.8°/帧（方向），远离 `no_teleport` 的 25°。
* 命停 [72, 74]：**14 骨旋转逐位冻结**（躯干 8 + 手臂 6，C07 第 3 件同款；
  本支同样无位置逆解 ⟹ 冻结欧拉 = 冻结视觉），而骨盆**继续上爬 12 mm**
  ⟹ `hitstop_keeps_momentum_ok`（要求 > 10 mm）成立，读作"爆发的力还在往上冲"。
* 收招：从冻结的命中姿用同一条 `q(frame) = 1 − (1−u)^POST_POW` 仿射走到
  「半蹲戒备」⟹ 每帧步长 = max|Δᵢ| · Δq，`Δq` 单调递减 ⟹ `decel_smooth_ok` 与
  `no_snap_stop_ok` **构造性成立**（C06/C07 沉淀）。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_charge08.py
    SKIP_RENDER=1 只跑门禁（迭代用）；C08_TRACE=1 打逐帧轨迹。
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

NAME = "Charge"
LOOP_NAME = "Charge_Loop"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")


def _env_f(key, default):
    return float(os.environ[key]) if os.environ.get(key) else float(default)


def _env_i(key, default):
    return int(os.environ[key]) if os.environ.get(key) else int(default)


# ---------------------------------------------------------------- 帧预算
TOTAL = _env_i("C08_TOTAL", 110)          # 1.833 s @60fps
LOOP_IN = _env_i("C08_LOOP_IN", 20)       # 起手结束 / 循环首帧
LOOP_OUT = _env_i("C08_LOOP_OUT", 56)     # 循环末帧 / 释放首帧
HIT = _env_i("C08_HIT", 72)               # 命中帧（爆发最高点）
HOLD = _env_i("C08_HOLD", 3)              # 命停 3 帧（§0.1 的 2~4）
HOLD_END = HIT + HOLD - 1                 # 74
RETURN_START = HOLD_END + 1               # 75
SETTLE = _env_i("C08_SETTLE", 104)        # 收招落定（此后逐位静止）
CANCEL = _env_i("C08_CANCEL", 106)        # 可取消帧
# ★ TOTAL 必须先于 SETTLE/CANCEL 覆盖（第 5 轮修正）：初版写 TOTAL=100 而
#   SETTLE=104 / CANCEL=106 —— 两个标记落在片段区间 [0,100] **之外**，
#   `end_pose_deg` 登记的"半蹲戒备"其实只走到 q=0.919（92%），渲染 f104 与
#   f100 逐像素相同（Action 区间外取到末帧）就是这条漏的现场证据。
#   C07 的约定是 TOTAL=SETTLE+6：落定后留 6 帧静止窗给引擎混合。
#   ⟹ TOTAL=110 / SETTLE=104 / CANCEL=106，全部落在区间内。
POST_POW = _env_f("C08_POSTPOW", 1.25)    # 收招缓动 q = 1 − (1−u)^p
# ★ POST_POW 与收招帧数是被 `world_step_ok` 反推出来的（见文件头第 4 件）：
#   本支收招的臂世界转动 ≈ 137°（爆发位 → 戒备位），远大于 C07 的 ~25°。
#   C07 用 1.6 时首帧步长 = |Δ|·(1−(1−1/N)^p)；N=22 / p=1.6 → 26.0° ❌（实测）。
#   改成 N=30（SETTLE 96→104）/ p=1.25 → 首帧 ≈ 0.0414·137 ≈ 5.7°。

# 命停窗内骨盆继续上爬的量（`hitstop_keeps_momentum_ok` 要 > 10 mm）
MOMENTUM_MM = _env_f("C08_MOMENTUM", 12.0)

# ---------------------------------------------------------------- 循环段颤振
TREMBLE_K = _env_f("C08_TREMBLE_K", 3.0)          # 36 帧里 3 个周期 = 5 Hz
TREMBLE_PX_MM = _env_f("C08_TREMBLE_PX", 1.0)
TREMBLE_PZ_MM = _env_f("C08_TREMBLE_PZ", 2.0)     # std = 1.41 mm ≤ 2 ✓
TREMBLE_CHEST_DEG = _env_f("C08_TREMBLE_CHEST", 0.25)
TREMBLE_NECK_DEG = _env_f("C08_TREMBLE_NECK", 2.2)
TREMBLE_HEAD_DEG = _env_f("C08_TREMBLE_HEAD", 1.4)

# ---------------------------------------------------------------- 姿态常量
# 下沉后的骨盆世界位置（"双腿扎稳、身体下沉"）
PZ_SUNK = _env_f("C08_PZ_SUNK", 0.730)
PY_SUNK = _env_f("C08_PY_SUNK", 0.004)
PX_SUNK = 0.0
# 爆发顶（≤ 875 是实测硬上限，见文件头第 2 件）
PZ_BURST = _env_f("C08_PZ_BURST", 0.850)
PY_BURST = _env_f("C08_PY_BURST", -0.030)
# 收招末姿「半蹲戒备」
END_PX = _env_f("C08_END_PX", 0.0)
END_PY = _env_f("C08_END_PY", -0.008)
END_PZ = _env_f("C08_END_PZ", 0.800)

# 躯干轨道 —— 分**起手（START）/ 释放（REL）两条**，循环窗不用插值（见第 1 件坑）。
# START 的 f0 由 `patch()` 回填 `Idle_01@0` 真值（禁手写）；末键固定在 LOOP_IN。
# REL 的首键由 `main()` 补成 `(LOOP_OUT, START 末值)`，保证循环窗两侧逐位接得上。
START_RX = {
    "pelvis": ((0, 0.0), (8, 9.0), (LOOP_IN, 14.0)),
    "spine_01": ((0, 0.0), (8, 4.5), (LOOP_IN, 7.0)),
    "spine_02": ((0, 0.0), (8, 4.5), (LOOP_IN, 7.0)),
    "chest": ((0, 0.0), (8, 4.5), (LOOP_IN, 7.0)),
    "neck": ((0, 0.0), (8, -10.0), (LOOP_IN, -18.0)),
    "head": ((0, 0.0), (8, -4.0), (LOOP_IN, -8.0)),
    "shoulder.rx": ((0, 0.0), (8, -4.0), (LOOP_IN, -6.0)),
    "shoulder.rz": ((0, 0.0), (8, 3.0), (LOOP_IN, 5.0)),
}
REL_RX = {
    "pelvis": ((HIT, -6.0), (HOLD_END, -6.0)),
    "spine_01": ((HIT, -3.0), (HOLD_END, -3.0)),
    "spine_02": ((HIT, -3.0), (HOLD_END, -3.0)),
    "chest": ((HIT, -3.0), (HOLD_END, -3.0)),
    "neck": ((HIT, -10.0), (HOLD_END, -10.0)),
    "head": ((HIT, -6.0), (HOLD_END, -6.0)),
    "shoulder.rx": ((HIT, -10.0), (HOLD_END, -10.0)),
    "shoulder.rz": ((HIT, 8.0), (HOLD_END, 8.0)),
}
# 骨盆位移（米）：x 恒 0（对称"扎稳"），y 微后坐，z 下沉。
# ★ 位移轨道一律 `(0, 0.0)` 起手，绝不许走 `patch()`（C07 教训 1）。
START_LOC = {
    "x": ((0, 0.0), (LOOP_IN, 0.0)),
    "y": ((0, 0.0), (8, -0.004), (LOOP_IN, 0.0)),      # 占位，main() 里换成 PY_SUNK
    "z": ((0, 0.0), (8, -0.055), (LOOP_IN, 0.0)),      # 占位，main() 里换成相对 Z_SEAM
}
REL_LOC = {
    "x": ((HIT, 0.0), (HOLD_END, 0.0)),
    "y": ((HIT, 0.0), (HOLD_END, 0.0)),                # 占位，main() 里换成 PY_BURST
    "z": ((HIT, 0.0), (HOLD_END, 0.0)),                # 占位，main() 里换成爆发顶 + 命停上爬
}

# ---------------------------------------------------------------- 收招末姿
END_ROT = {
    "pelvis": (8.0, 0.0, 0.0), "spine_01": (4.0, 0.0, 0.0),
    "spine_02": (4.0, 0.0, 0.0), "chest": (4.0, 0.0, 0.0),
    "neck": (-10.0, 0.0, 0.0), "head": (-4.0, 0.0, 0.0),
    "shoulder.L": (-4.0, 0.0, 3.0), "shoulder.R": (-4.0, 0.0, -3.0),
}
# 半蹲戒备：双拳护在胸腹前、肘内收
END_DIRS = {
    "upperarm.L": (0.30, -0.28, -0.912),
    "forearm.L": (-0.22, -0.72, -0.658),
    "hand.L": (-0.20, -0.76, -0.618),
    "upperarm.R": (-0.30, -0.28, -0.912),
    "forearm.R": (0.22, -0.72, -0.658),
    "hand.R": (0.20, -0.76, -0.618),
}

# ---------------------------------------------------------------- 手臂方向轨道
# 世界单位向量：x = 左正，y = 身后正，z = 上正，角色正面朝 −y。
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_KEYS = {
    # 起手中间点：双拳开始下沉外张
    "DRAW": {
        "upperarm.L": (0.46, 0.10, -0.882),
        "forearm.L": (-0.30, -0.42, -0.856),
        "hand.L": (-0.28, -0.46, -0.843),
        "upperarm.R": (-0.46, 0.10, -0.882),
        "forearm.R": (0.30, -0.42, -0.856),
        "hand.R": (0.28, -0.46, -0.843),
    },
    # ★ 蓄力位（循环段基准）：双拳紧握在髋侧、肘向后外引、前臂略前内
    "CHARGE": {
        "upperarm.L": (0.42, 0.40, -0.818),
        "forearm.L": (-0.34, -0.62, -0.708),
        "hand.L": (-0.32, -0.66, -0.680),
        "upperarm.R": (-0.42, 0.40, -0.818),
        "forearm.R": (0.34, -0.62, -0.708),
        "hand.R": (0.32, -0.66, -0.680),
    },
    # ★ 爆发：双臂向两侧上方猛张（"张开爆发"，与 C07 的过顶砸击区分）
    "BURST": {
        "upperarm.L": (0.60, 0.08, 0.796),
        "forearm.L": (0.56, 0.10, 0.822),
        "hand.L": (0.54, 0.10, 0.835),
        "upperarm.R": (-0.60, 0.08, 0.796),
        "forearm.R": (-0.56, 0.10, 0.822),
        "hand.R": (-0.54, 0.10, 0.835),
    },
}
# 相位表：(帧, 键名, 到下一段的插值模式)
ARM_PHASES = ((0, "SEAM", "smooth"), (9, "DRAW", "smooth"),
              (LOOP_IN, "CHARGE", "linear"), (LOOP_OUT, "CHARGE", "linear"),
              (HIT, "BURST", "linear"), (HOLD_END, "BURST", "linear"))

# ★ 14 骨全冻（C04/C07 那套；本支无位置逆解 ⟹ 冻结欧拉 = 冻结视觉）
HITSTOP_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "shoulder.L", "shoulder.R",
                 "upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R")

# ---------------------------------------------------------------- 门禁阈值
SOLE_RANGE_MM = (-2.0, 6.0)
PLANT_DRIFT_MAX_MM = 3.0
PIVOT_DRIFT_MAX_MM = 3.0
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
# C08 新增门禁
SINK_MIN_MM = _env_f("C08_SINK_MIN", 80.0)        # 起手 → 循环的骨盆下沉量
SINK_STD_MAX_MM = _env_f("C08_SINK_STD_MAX", 2.0)  # 循环段骨盆 z 标准差
LOOP_REACH_MAX_RATIO = _env_f("C08_LOOP_REACH_MAX", 0.95)   # 循环段可达比
LOOP_FIST_DRIFT_MAX_MM = _env_f("C08_FIST_DRIFT_MAX", 8.0)  # 循环段双拳漂移
ANTIC_MIN_FRAMES = _env_f("C08_ANTIC_MIN", 12.0)  # 蓄力必须肉眼可见（不设上限）
# 末帧实测必须等于 Action 自定义属性里登记的 `end_pose_deg`。
# 0.05° 是"元数据不许撒谎"的公差 —— 不是姿态公差（姿态好不好看由目检定）。
END_POSE_TOL_DEG = _env_f("C08_END_TOL", 0.05)

# ---------------------------------------------------------------- 观测量
SEAM_POSE = {}
SEAM_EULER = {}
SEAM_DIRS = {}
Z_SEAM = 0.0
ANKLE_0 = {}
IDLE_POSE = {}
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
ARM_LEN = {}
ARM_BASIS = {}
ARM_BASIS_END = {}          # ★ 收招终点的臂世界基准（slerp 的另一端）
E0 = {}
E_END = {}
E_END_UNW = {}
_HIT_FROZEN = {}
HIT_POINT = {}
SRC_MATS = {}
LOG = {}


def _hold(frame):
    return HIT < frame <= HOLD_END


def _lerp3(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def in_loop(frame):
    return LOOP_IN <= frame <= LOOP_OUT


def tremble(frame):
    """循环窗口的颤振相位 s ∈ [−1, 1]。两端**显式置 0**（逐位闭合的构造）。"""
    if not in_loop(frame):
        return 0.0
    if frame == LOOP_IN or frame == LOOP_OUT:
        return 0.0                       # ★ 不依赖 sin(2πK) 的浮点零
    u = (frame - LOOP_IN) / float(LOOP_OUT - LOOP_IN)
    return math.sin(2.0 * math.pi * TREMBLE_K * u)


def q_of(frame):
    """收招进度：0 = 命中（冻结值），1 = 半蹲戒备。增量单调递减 ⟹ 步长单调不增。"""
    if frame <= HOLD_END:
        return 0.0
    if frame >= SETTLE:
        return 1.0
    u = (frame - HOLD_END) / float(SETTLE - HOLD_END)
    return 1.0 - (1.0 - u) ** POST_POW


# =============================================================== 姿态
def _seg(keys_start, keys_release, frame, freeze_hold=True):
    """三段取值：**起手插值 / 循环窗冻结 / 释放插值**。

    `freeze_hold`：
      - 旋转轨道（躯干骨）用 True —— 命停窗内 14 骨逐位冻结，`REL_RX` 在 HIT 与
        HOLD_END 上本来就是同一常量，"冻在 HIT" 与"走到 HOLD_END"等价。
      - **位移轨道用 False** —— 这是第 4 轮踩到的坑：`REL_LOC["z"]` 的 HOLD_END 键
        写的是"爆发顶 + 命停上爬 12 mm"，可 `_hold(74)` 为真 ⟹ 取值被冻回 HIT，
        于是 `pz[HOLD_END] − pz[HIT] = 0.000`，`hitstop_keeps_momentum_ok` 恒红。
        顿感要的是"骨冻住、身体还在往上冲"，位移必须照走。

    ★ 这里踩过一个把六项门禁一次打红的坑（第 1 轮）：
    最初只用**一条** `(0, idle) → (LOOP_IN, 蓄力位) → (HIT, 爆发位)` 的轨道，
    指望"循环窗里轨道自己会停在蓄力位"。**不会** ——

      1. `RS.track` 是 Catmull-Rom，**关键点之间**照走不误：f20→f72 的跨度里，
         f56 已经走完 69%，实测 `pelvis.rx` 在循环末帧掉到 **0.56°**（应为 14°）。
      2. 就算在 LOOP_IN / LOOP_OUT 各插一个 14.0 的键也没用：Hermite 的
         `m_a` / `m_b` 取自**相邻关键点**，中段仍会过冲到 **16.2°**。

    ⟹ 循环窗**不能靠插值实现**，必须显式冻结在起手段末值。这也是清单
    §3「先量清楚再决定，不要直接假设」那句话的实体。
    """
    if frame <= LOOP_IN:
        return RS.track(keys_start, frame)
    if frame <= LOOP_OUT:
        return keys_start[-1][1]                 # ★ 循环窗：冻在起手段末值
    probe = HIT if (freeze_hold and _hold(frame)) else frame
    return RS.track(keys_release, probe)


def torso_pose(frame):
    """躯干 + 骨盆位移。三段各自取值，收招段用 `q()` 仿射到末姿。"""
    s = tremble(frame)
    base = {
        "pelvis": (_seg(START_RX["pelvis"], REL_RX["pelvis"], frame), 0.0, 0.0),
        "spine_01": (_seg(START_RX["spine_01"], REL_RX["spine_01"], frame),
                     0.0, 0.0),
        "spine_02": (_seg(START_RX["spine_02"], REL_RX["spine_02"], frame),
                     0.0, 0.0),
        "chest": (_seg(START_RX["chest"], REL_RX["chest"], frame), 0.0, 0.0),
        "neck": (_seg(START_RX["neck"], REL_RX["neck"], frame), 0.0, 0.0),
        "head": (_seg(START_RX["head"], REL_RX["head"], frame), 0.0, 0.0),
        "shoulder.L": (_seg(START_RX["shoulder.rx"], REL_RX["shoulder.rx"], frame),
                       0.0,
                       _seg(START_RX["shoulder.rz"], REL_RX["shoulder.rz"], frame)),
        "shoulder.R": (_seg(START_RX["shoulder.rx"], REL_RX["shoulder.rx"], frame),
                       0.0,
                       -_seg(START_RX["shoulder.rz"], REL_RX["shoulder.rz"], frame)),
    }
    if s:
        base["chest"] = (base["chest"][0] + TREMBLE_CHEST_DEG * s, 0.0, 0.0)
        base["neck"] = (base["neck"][0] + TREMBLE_NECK_DEG * s, 0.0, 0.0)
        base["head"] = (base["head"][0] + TREMBLE_HEAD_DEG * s, 0.0, 0.0)

    if frame <= HOLD_END:
        # ★ 位移走 freeze_hold=False：命停窗内骨盆继续上爬（顿感的另一半）
        px = _seg(START_LOC["x"], REL_LOC["x"], frame, False) \
            + TREMBLE_PX_MM * s / 1000.0
        py = _seg(START_LOC["y"], REL_LOC["y"], frame, False)
        pz = Z_SEAM + _seg(START_LOC["z"], REL_LOC["z"], frame, False) \
            + TREMBLE_PZ_MM * s / 1000.0
    else:
        q = q_of(frame)
        # ★★ 躯干旋转也必须跟着 `q` 走（第 5 轮修正）。
        #   坑：`REL_RX` 只有 HIT / HOLD_END 两个**同值**键，`RS.track` 在帧号
        #   越过末键后**钳到末键**（不外推）⟹ 收招段躯干永远冻在爆发姿
        #   （pelvis −6° / spine 各 −3°，躯干和 −15°），而 `end_pose_deg` 登记的
        #   是 pelvis +8° / spine 各 +4°（和 +20°）—— **登记值与实测对不上**。
        #   现场指纹：侧视 f110 上身还仰着、只有手臂收了回来。
        #   初版之所以没被门禁抓住，是因为所有门禁都只量**步长**与**脚**，
        #   没有一条量"末帧是否真是登记的那个姿"。已补 `end_pose_ok`。
        for name, end in END_ROT.items():
            cur = base[name]
            base[name] = tuple(cur[c] + (end[c] - cur[c]) * q
                               for c in range(3))
        # ★ 位移这里也必须 freeze_hold=False：否则 pz0 取到 HIT 值，
        #   与 f74 差 12 mm ⟹ 收招首帧跳变
        px0 = _seg(START_LOC["x"], REL_LOC["x"], HOLD_END, False)
        py0 = _seg(START_LOC["y"], REL_LOC["y"], HOLD_END, False)
        pz0 = Z_SEAM + _seg(START_LOC["z"], REL_LOC["z"], HOLD_END, False)
        px = px0 + (END_PX - px0) * q
        py = py0 + (END_PY - py0) * q
        pz = pz0 + (END_PZ - pz0) * q
    rot = dict(base)
    rot["@loc"] = {"pelvis": A.wloc(px, py, pz - 0.900)}
    return rot


def key_basis(dirs):
    """把一组世界方向解成各骨的**世界基准 3×3**（= 从 Idle 基准做最小旋转）。"""
    out = {}
    for bone in ARM_BONES:
        quat = (Vector(IDLE_DIR[bone]).normalized()
                .rotation_difference(Vector(dirs[bone]).normalized()))
        out[bone] = quat.to_matrix() @ IDLE_BASIS[bone]
    return out


def build_arm_basis():
    table = {"SEAM": SEAM_DIRS}
    table.update(ARM_KEYS)
    return {name: key_basis(dirs) for name, dirs in table.items()}


def arm_phase(frame):
    """相位插值参数 `(键a, 键b, t)`。"""
    if _hold(frame):
        frame = HIT
    bounds = [item[0] for item in ARM_PHASES]
    if frame <= bounds[0]:
        return ("SEAM", "SEAM", 0.0)
    if frame >= bounds[-1]:
        return ("BURST", "BURST", 1.0)
    for index in range(len(ARM_PHASES) - 1):
        fa, na, mode = ARM_PHASES[index]
        fb, nb, _mb = ARM_PHASES[index + 1]
        if not (fa <= frame <= fb) or fa == fb:
            continue
        u = (frame - fa) / float(fb - fa)
        if mode == "linear":
            t = u
        elif mode == "accel":
            t = u ** 1.35
        else:
            t = RS.smooth(u)
        return (na, nb, t)
    return ("BURST", "BURST", 1.0)


def arm_basis(frame):
    """本帧各臂骨的**目标世界基准**：相位两端做四元数 slerp（C07 第 4 件的构造）。

    循环窗内两端同为 `CHARGE` ⟹ slerp 结果逐位 = `CHARGE` 基准，
    循环的闭合性由 `tremble()` 保证（见文件头第 3 件）。
    """
    na, nb, t = arm_phase(frame)
    out = {}
    for bone in ARM_BONES:
        qa = ARM_BASIS[na][bone].to_quaternion()
        qb = ARM_BASIS[nb][bone].to_quaternion()
        if qa.dot(qb) < 0.0:
            qb = Quaternion((-qb.w, -qb.x, -qb.y, -qb.z))
        out[bone] = qa.slerp(qb, t).to_matrix()
    return out


def aim_world_basis(arm, name, basis):
    """把骨的世界基准钉到 `basis`（只改朝向，位置不变），返回解出的 euler。"""
    pose_bone = arm.pose.bones[name]
    pose_bone.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    target = basis.to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


# =============================================================== 姿态装配
def build_pose(arm, frame, shift):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)

    for side in SIDES:
        target = (ANKLE_0[side].x, ANKLE_0[side].y,
                  ANKLE_0[side].z + shift[side])
        G4.leg_seat(arm, pose, side, target, IDLE_KNEE_DIR[side])

    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    if frame <= HOLD_END:
        basis = arm_basis(frame)
        for bone in ARM_BONES:
            pose[bone] = JS._unwrap_xyz(
                JS._PREV_EULER.get(bone),
                aim_world_basis(arm, bone, basis[bone]))
    else:
        # ★ 收招的臂 = **欧拉仿射**（C07 第 1 件的构造性保证），不走世界基准 slerp。
        #
        #   第 4 轮实测：slerp 走的是测地线 ⟹ 世界角速度恒定，但**局部位姿欧拉的
        #   模长中间最大**（"欧拉图表"在转 137° 时中段每帧读数变化最快）。
        #   `decel_smooth_decel` 量的正是局部欧拉步长，于是拿到一条**钟形**曲线：
        #   f75 起 7.67° → f86 冲到 16.00° → f92 落回 5.72°，单调不增被破坏。
        #   逐帧 owner 全是 `forearm.L/R`（腿峰值 1.69°、躯干 0.00°），
        #   病根唯一：臂的欧拉读数不随弧长均匀变化。
        #
        #   回到欧拉仿射：`X(f) = E0 + (E_END − E0)·q(f)` ⟹ 每骨步长 = |Δ|·Δq，
        #   "全骨最大步长" = max|Δ|·Δq = **常数 × Δq**，单调不增 ⟹ 门禁构造性成立。
        #
        #   代价（上一轮改 slerp 的原因）是世界单帧步长会因"滚转补课"抬头：
        #   旧参数 N=22 / p=1.6 时 f75 实测 **26.005°**（上限 25）⟹ 当时才改 slerp。
        #   但现在 N=30 / p=1.25，Δq(75) 从 0.0717 降到 0.0429（**0.60×**）
        #   ⟹ 预计首帧世界步长 ≈ 15.6°，硬上限内。这条路径**同时**满足两个门禁。
        q = q_of(frame)
        if not E_END_UNW:
            for bone in ARM_BONES:
                E_END_UNW[bone] = JS._unwrap_xyz(E0[bone], E_END[bone])
        for bone in ARM_BONES:
            pose[bone] = tuple(
                E0[bone][c] + (E_END_UNW[bone][c] - E0[bone][c]) * q
                for c in range(3))

    if frame == HIT:
        _HIT_FROZEN.clear()
        for key in HITSTOP_BONES:
            if key in pose:
                _HIT_FROZEN[key] = tuple(pose[key])
        # ★ 登记命中帧（HIT）的世界坐标 —— 供下游 VFX（气劲、镜头）与
        #   D 族"被击飞"定位用。
        fist_l = Vector(A.bone_world(arm, "hand.L", "tail"))
        fist_r = Vector(A.bone_world(arm, "hand.R", "tail"))
        HIT_POINT.clear()
        HIT_POINT.update({
            "frame": HIT,
            "fist_L_m": [round(v, 4) for v in fist_l],
            "fist_R_m": [round(v, 4) for v in fist_r],
            "fist_mid_m": [round(v, 4) for v in (fist_l + fist_r) * 0.5],
            "fist_span_mm": round((fist_l - fist_r).length * 1000.0, 2),
            "pelvis_m": [round(v, 4)
                         for v in A.bone_world(arm, "pelvis", "head")],
            "head_m": [round(v, 4)
                       for v in A.bone_world(arm, "head", "tail")],
        })
    if _HIT_FROZEN and _hold(frame):
        for name, value in _HIT_FROZEN.items():
            pose[name] = tuple(value)
            arm.pose.bones[name].rotation_euler = [math.radians(v)
                                                   for v in value]
        bpy.context.view_layer.update()

    if frame == HOLD_END:
        E0.clear()
        for bone in ARM_BONES:
            E0[bone] = tuple(pose[bone])

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
    """逐帧贴地闭环：两只脚全程支撑，鞋底钉到 0 mm。

    ★ 为什么非闭环不可：下沉 100 mm 时鞋底本身会往下偏 1~3 mm
    （鞋面顶点带 `shin` 权重，膝弯曲量变了，鞋形微变）——
    `probe_c08_baseline.py` 实测 pelvisZ 730 → 鞋底 [−2.08, −0.22]，
    右脚已经越过 `ground_contact` 的 −2 mm 下限。闭环把它顶回 0。
    """
    shift = {side: 0.0 for side in SIDES}
    snap = _snapshot_carry()
    pose = build_pose(arm, frame, shift)
    if meshes is None:
        return pose
    for _ in range(4):
        low = A.foot_lowest_by_side()
        error = {s: 0.0 - low[s][2] for s in SIDES if low[s] is not None}
        if not error or max(abs(v) for v in error.values()) < 5e-5:
            break
        for side, value in error.items():
            shift[side] += value
        _restore_carry(snap)
        pose = build_pose(arm, frame, shift)
    _restore_carry(snap)
    pose = build_pose(arm, frame, shift)
    return pose


def solve_end_arm(arm):
    """一次性解出「半蹲戒备」的手臂欧拉（收招插值终点）。"""
    torso = {
        "pelvis": (END_ROT["pelvis"][0], 0.0, 0.0),
        "spine_01": (END_ROT["spine_01"][0], 0.0, 0.0),
        "spine_02": (END_ROT["spine_02"][0], 0.0, 0.0),
        "chest": (END_ROT["chest"][0], 0.0, 0.0),
        "neck": (END_ROT["neck"][0], 0.0, 0.0),
        "head": (END_ROT["head"][0], 0.0, 0.0),
        "shoulder.L": END_ROT["shoulder.L"],
        "shoulder.R": END_ROT["shoulder.R"],
        "@loc": {"pelvis": A.wloc(END_PX, END_PY, END_PZ - 0.900)},
    }
    A.apply_pose(arm, torso)
    for side in SIDES:
        G4.leg_seat(arm, torso, side,
                    (ANKLE_0[side].x, ANKLE_0[side].y, ANKLE_0[side].z),
                    IDLE_KNEE_DIR[side])
    for side in SIDES:
        A.keep_world_orientation(arm, "foot." + side)
    out = {}
    for bone in ARM_BONES:
        out[bone] = JS._unwrap_xyz(
            None, G4.aim_bone_ref(arm, bone, END_DIRS[bone],
                                  IDLE_BASIS[bone], IDLE_DIR[bone]))
    return out


# =============================================================== 逐帧实测
def _sole_anchor(side):
    """找该侧鞋底「最前的最低点」顶点的 **(对象名, 顶点号)** —— 枢轴基准。

    照抄 C07 教训 3：脚底前后两个顶点 z 常只差零点几毫米，姿态微动就让
    "最低"在两者之间跳，跳动量 = 两顶点的 xy 距离（C07 第 1 轮量出 57.5 mm
    的**量法伪影**）。钉死一个顶点才量得到"脚有没有在原地转"。
    """
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
    if not points:
        return None
    zmin = min(p[2] for p in points)
    band = [p for p in points if p[2] <= zmin + 2.0]
    front = min(band, key=lambda p: p[1])
    return (front[3], front[4])


def _vertex_world(key):
    deps = bpy.context.evaluated_depsgraph_get()
    obj = bpy.data.objects.get(key[0])
    if obj is None:
        return None
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    point = evaluated.matrix_world @ mesh.vertices[key[1]].co
    evaluated.to_mesh_clear()
    return (point.x, point.y, point.z)


def foot_series(arm, action, meshes, total):
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    rows = []
    anchor = {}
    for frame in range(0, total + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        if frame == 0:
            for side in SIDES:
                anchor[side] = _sole_anchor(side)
        row = {"frame": frame,
               "pelvis": tuple(A.bone_world(arm, "pelvis", "head")),
               "neck": tuple(A.bone_world(arm, "neck", "head"))}
        low = A.foot_lowest_by_side()
        for side in SIDES:
            row["ankle_" + side] = tuple(A.bone_world(arm, "foot." + side,
                                                      "head"))
            row["contact_" + side] = low[side]
            row["sole_" + side] = None if low[side] is None else low[side][2]
            row["reach_" + side] = (
                Vector(row["ankle_" + side]) - Vector(row["pelvis"])).length
            row["hand_" + side + "_tail"] = tuple(
                A.bone_world(arm, "hand." + side, "tail"))
            row["pivot_" + side] = (None if anchor.get(side) is None
                                    else _vertex_world(anchor[side]))
        rows.append(row)
    if previous is not None:
        arm.animation_data.action = previous
    return rows


def arm_world_steps(arm, action, total):
    mats = {}
    watch = ARM_BONES + ("pelvis", "spine_01", "spine_02", "chest",
                         "neck", "head", "thigh.L", "thigh.R",
                         "shin.L", "shin.R")
    for frame in range(0, total + 1):
        raw = RS.action_world_matrices(arm, action, frame)
        mats[frame] = {
            name: Matrix([raw[name][i * 4:i * 4 + 3] for i in range(3)])
            for name in watch if name in raw}
    worst, worst_at = 0.0, None
    for frame in range(1, total + 1):
        for name in mats[frame]:
            if name not in mats[frame - 1]:
                continue
            q = (mats[frame - 1][name].transposed()
                 @ mats[frame][name]).to_quaternion()
            angle = math.degrees(q.angle)
            if angle > worst:
                worst, worst_at = angle, (frame, name)
    return worst, worst_at


def _mean(values):
    return sum(values) / float(len(values)) if values else 0.0


def _std(values):
    if not values:
        return 0.0
    mu = _mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / float(len(values)))


# =============================================================== 专属门禁
def charge_assertions(arm, action, samples, foots):
    res = {}
    pelvis = [Vector(f["pelvis"]) for f in foots]
    pz = [p.z * 1000.0 for p in pelvis]
    fists = {s: [Vector(f["hand_" + s + "_tail"]) for f in foots]
             for s in SIDES}
    mid = [(fists["L"][i] + fists["R"][i]) * 0.5 for i in range(len(foots))]
    mid_z = [v.z * 1000.0 for v in mid]

    idx = {f["frame"]: i for i, f in enumerate(foots)}
    loop_frames = list(range(LOOP_IN, LOOP_OUT + 1))
    loop_idx = [idx[f] for f in loop_frames]

    # ---- 0) 首帧接缝：Charge@0 必须逐位等于 `Idle_01@0`
    mats0 = RS.action_world_matrices(arm, action, 0)
    delta0 = RS.matrix_delta(mats0, SRC_MATS)
    res["seam_source"] = [I1.NAME, 0]
    res["charge_start_delta"] = float("%.3e" % delta0)
    res["charge_start_ok"] = delta0 <= SEAM_TOL
    res["root_motion_m"] = [round(pelvis[-1].x - pelvis[0].x, 6),
                            round(pelvis[-1].y - pelvis[0].y, 6)]
    res["root_motion_ok"] = max(abs(v) for v in res["root_motion_m"]) * 1000.0 \
        <= 30.0

    # ---- 1) 支撑脚：踝 XY 漂移 + 鞋底区间 + 枢轴（全段）
    plant, sole, pivot = {}, {}, {}
    for side in SIDES:
        pts = list(range(0, len(foots)))
        xs = [foots[f]["ankle_" + side][0] for f in pts]
        ys = [foots[f]["ankle_" + side][1] for f in pts]
        plant[side + "_mm"] = round(
            math.hypot(max(xs) - min(xs), max(ys) - min(ys)) * 1000.0, 4)
        zs = [foots[f]["sole_" + side] for f in pts
              if foots[f]["sole_" + side] is not None]
        sole[side] = [round(min(zs) * 1000.0, 3), round(max(zs) * 1000.0, 3)]
        prow = [foots[f]["pivot_" + side] for f in pts]
        prow = [p for p in prow if p is not None]
        if prow:
            cx = [p[0] for p in prow]
            cy = [p[1] for p in prow]
            pivot[side + "_mm"] = round(
                math.hypot(max(cx) - min(cx), max(cy) - min(cy)) * 1000.0, 4)
        else:
            pivot[side + "_mm"] = None
    res["plant_drift_mm"] = plant
    res["stance_plant_ok"] = all(v <= PLANT_DRIFT_MAX_MM for v in plant.values())
    res["pivot_drift_mm"] = pivot
    res["stance_pivot_ok"] = all(
        v is not None and v <= PIVOT_DRIFT_MAX_MM for v in pivot.values())
    res["plant_sole_mm"] = sole
    res["stance_sole_ok"] = all(SOLE_RANGE_MM[0] <= v[0]
                                and v[1] <= SOLE_RANGE_MM[1]
                                for v in sole.values())
    # 本支两脚全程支撑 ⟹ `always_supported_ok` 构造性成立（无腾空帧）
    res["unsupported_frames"] = []
    res["always_supported_ok"] = True
    res["swing_windows"] = None
    res["swing_airborne_ok"] = True

    # ---- 2) 顿感：命停窗 14 骨逐位冻结，而骨盆继续上爬
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
            frozen.append(round(step, 6))
    res["hitstop_frozen_steps"] = frozen
    res["hitstop_present_ok"] = bool(frozen) and max(frozen) <= 1e-6
    res["hitstop_momentum_mm"] = round(pz[idx[HOLD_END]] - pz[idx[HIT]], 3)
    res["hitstop_keeps_momentum_ok"] = res["hitstop_momentum_mm"] > 10.0
    res["hitstop_frames"] = HOLD
    res["hitstop_frames_ok"] = 2 <= HOLD <= 4
    res["antic_frames"] = LOOP_IN
    res["antic_frames_ok"] = LOOP_IN >= ANTIC_MIN_FRAMES
    res["release_frames"] = HIT - LOOP_OUT
    res["loop_frames"] = LOOP_OUT - LOOP_IN

    # ---- 3) ★ C08 六个新门禁
    # ① 下沉量：起手首帧（= Idle@0）到循环段均值的骨盆 z 落差
    loop_pz = [pz[i] for i in loop_idx]
    res["charge_sink_mm"] = round(pz[0] - _mean(loop_pz), 2)
    res["charge_sink_ok"] = res["charge_sink_mm"] >= SINK_MIN_MM
    # ② 下沉后要"稳住"：循环段骨盆 z 的标准差
    res["charge_sink_std_mm"] = round(_std(loop_pz), 4)
    res["charge_sink_span_mm"] = round(max(loop_pz) - min(loop_pz), 4)
    res["charge_sink_pose_ok"] = res["charge_sink_std_mm"] <= SINK_STD_MAX_MM
    # ③ "双腿扎稳"：循环段 踝 XY 漂移 + 鞋底
    l_plant, l_sole = {}, {}
    for side in SIDES:
        xs = [foots[i]["ankle_" + side][0] for i in loop_idx]
        ys = [foots[i]["ankle_" + side][1] for i in loop_idx]
        l_plant[side + "_mm"] = round(
            math.hypot(max(xs) - min(xs), max(ys) - min(ys)) * 1000.0, 4)
        zs = [foots[i]["sole_" + side] * 1000.0 for i in loop_idx
              if foots[i]["sole_" + side] is not None]
        l_sole[side] = [round(min(zs), 3), round(max(zs), 3)]
    res["loop_plant_drift_mm"] = l_plant
    res["loop_sole_mm"] = l_sole
    res["charge_stance_ok"] = (
        all(v <= PLANT_DRIFT_MAX_MM for v in l_plant.values())
        and all(SOLE_RANGE_MM[0] <= v[0] and v[1] <= SOLE_RANGE_MM[1]
                for v in l_sole.values()))
    # ④ 蓄力段腿要有富余（比通用 0.995 更严 ⟹ 不许"膝盖锁死"）
    loop_reach = {}
    for side in SIDES:
        best = max(foots[i]["reach_" + side] for i in loop_idx)
        loop_reach[side] = round(best / (A.L_THIGH + A.L_SHIN), 5)
    res["charge_leg_reach_ratio"] = loop_reach
    res["charge_leg_reach_ok"] = all(v <= LOOP_REACH_MAX_RATIO
                                     for v in loop_reach.values())
    # ⑤ 循环段首末帧逐位闭合 —— 在主片段上量（第二个 Action 同法量一次）
    first_idx, last_idx = loop_idx[0], loop_idx[-1]
    worst_angle, worst_move = 0.0, 0.0
    ea = samples[first_idx]["euler"]
    eb = samples[last_idx]["euler"]
    for name in set(ea) | set(eb):
        va = ea.get(name, (0.0, 0.0, 0.0))
        vb = eb.get(name, (0.0, 0.0, 0.0))
        worst_angle = max(worst_angle, max(abs(a - b) for a, b in zip(va, vb)))
    for name in A.PROBE_KEYS:
        if name in samples[first_idx] and name in samples[last_idx]:
            worst_move = max(worst_move, (
                Vector(samples[first_idx][name])
                - Vector(samples[last_idx][name])).length)
    res["charge_loop_window_angle_deg"] = round(worst_angle, 6)
    res["charge_loop_window_move_mm"] = round(worst_move * 1000.0, 6)
    res["charge_loop_window_ok"] = worst_angle <= 0.5 and worst_move <= 0.0005
    # ⑥ 蓄力时手要"握死"：循环段双拳世界漂移
    hold = {}
    for side in SIDES:
        pts = [fists[side][i] for i in loop_idx]
        c = (sum((p for p in pts), Vector((0.0, 0.0, 0.0))) / float(len(pts)))
        hold[side + "_mm"] = round(max((p - c).length for p in pts)
                                   * 2.0 * 1000.0, 3)
    res["loop_fist_drift_mm"] = hold
    res["charge_arm_hold_ok"] = all(v <= LOOP_FIST_DRIFT_MAX_MM
                                    for v in hold.values())
    # 循环段头颈颤振幅度（可见的"咬呀发力"，无门禁，登记用）
    heads = [Vector(samples[i]["head.tail"]) for i in loop_idx]
    hc = sum(heads, Vector((0.0, 0.0, 0.0))) / float(len(heads))
    res["loop_head_drift_mm"] = round(
        (max(p.z for p in heads) - min(p.z for p in heads)) * 1000.0, 3) \
        if heads else 0.0
    res["loop_head_center_mm"] = [round(v * 1000.0, 2) for v in hc]

    # ---- 4) 爆发幅度（诊断 + 门禁）
    res["burst_pelvis_z_mm"] = round(pz[idx[HIT]], 2)
    res["burst_pelvis_rise_mm"] = round(pz[idx[HIT]] - _mean(loop_pz), 2)
    res["burst_rise_ok"] = res["burst_pelvis_rise_mm"] >= 80.0
    res["burst_fist_mid_mm"] = [round(v * 1000.0, 1) for v in mid[idx[HIT]]]
    res["burst_fist_above_head_mm"] = round(
        (mid[idx[HIT]].z - Vector(samples[idx[HIT]]["head.tail"]).z) * 1000.0, 2)
    res["burst_fist_above_head_ok"] = res["burst_fist_above_head_mm"] >= 100.0
    res["burst_torso_sum_rx_deg"] = round(sum(
        samples[idx[HIT]]["euler"].get(n, (0.0, 0.0, 0.0))[0]
        for n in ("pelvis", "spine_01", "spine_02", "chest")), 3)
    res["charge_torso_sum_rx_deg"] = round(sum(
        samples[first_idx]["euler"].get(n, (0.0, 0.0, 0.0))[0]
        for n in ("pelvis", "spine_01", "spine_02", "chest")), 3)
    res["burst_torso_swing_deg"] = round(abs(
        res["charge_torso_sum_rx_deg"] - res["burst_torso_sum_rx_deg"]), 3)
    res["burst_torso_swing_ok"] = res["burst_torso_swing_deg"] >= 30.0

    # ---- 5) 力矩链：脚→腿→髋→腰→肩→手 逐级非零
    keys = ("pelvis", "spine_01", "spine_02", "chest", "shoulder.L",
            "shoulder.R", "thigh.L", "shin.L", "thigh.R", "shin.R")
    channel = {}
    for name in keys:
        vals = [s["euler"].get(name, (0.0, 0.0, 0.0)) for s in samples]
        channel[name] = round(max(max(abs(v) for v in item) for item in vals), 3)
    res["power_chain_channels_deg"] = channel
    res["power_chain_ok"] = all(v > 0.5 for v in channel.values())

    # ---- 6) 腿可达（全段，不做截断）
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

    # ---- 7) 收招：不许瞬停、不许过冲
    tails, tail_bones = [], []
    for index in range(1, len(samples)):
        frame = samples[index]["frame"]
        if frame >= RETURN_START:
            ea = samples[index - 1]["euler"]
            eb = samples[index]["euler"]
            step, owner = 0.0, None
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
    res["local_step_max_deg"] = round(max(tails) if tails else 0.0, 3)

    # ---- 8) ★ 末帧必须**真的是**登记的 `end_pose_deg`（第 5 轮新增）
    # 起因：收招段只把骨盆**位移**按 `q` 混到末姿，躯干**旋转**被 `RS.track`
    # 钳在末键 ⟹ 元数据登记 pelvis +8° 而实测 −6°。所有步长类门禁都是绿的，
    # 因为没有任何一条量过"末帧 == 登记值"。这条就是补上那个空洞。
    end_e = samples[-1]["euler"]
    res["end_pose_measured_deg"] = {
        n: [round(v, 4) for v in end_e.get(n, (0.0, 0.0, 0.0))]
        for n in END_ROT}
    res["end_pose_delta_deg"] = {
        n: round(max(abs(a - b) for a, b in
                     zip(end_e.get(n, (0.0, 0.0, 0.0)), END_ROT[n])), 4)
        for n in END_ROT}
    res["end_pose_ok"] = all(v <= END_POSE_TOL_DEG
                             for v in res["end_pose_delta_deg"].values())
    return res


def loop_action_assertions(arm, loop_action):
    """对第二个 Action（`Charge_Loop`）跑一遍通用门禁，验证它真的是循环。"""
    meta = {"anim_id": LOOP_NAME, "loop": True}
    samples = A.sample_animation(arm, loop_action, 0, LOOP_OUT - LOOP_IN)
    common = A.run_common_assertions(samples, meta, foot_probe=("toe.L", "toe.R"))
    first, last = samples[0], samples[-1]
    fist = {}
    for side in SIDES:
        pts = [Vector(s["hand." + side + ".tail"]) for s in samples]
        c = sum(pts, Vector((0.0, 0.0, 0.0))) / float(len(pts))
        fist[side + "_mm"] = round(max((p - c).length for p in pts)
                                   * 2.0 * 1000.0, 3)
    pz = [Vector(s["pelvis"]).z * 1000.0 for s in samples]
    return {
        "frames": len(samples),
        "loop_seamless": common.get("loop_seamless"),
        "loop_angle_deg": common.get("loop_angle_deg"),
        "loop_move_mm": common.get("loop_move_mm"),
        "ground_min_mm": common.get("ground_min_mm"),
        "ground_contact_ok": common.get("ground_contact_ok"),
        "max_frame_step_deg": common.get("max_frame_step_deg"),
        "no_teleport": common.get("no_teleport"),
        "fist_drift_mm": fist,
        "arm_hold_ok": all(v <= LOOP_FIST_DRIFT_MAX_MM for v in fist.values()),
        "pelvis_z_std_mm": round(_std(pz), 4),
        "sink_pose_ok": _std(pz) <= SINK_STD_MAX_MM,
        "sink_mm": round(pz[0] - 830.0 + 0.0, 2),
        "loop_euler_first": {k: [round(v, 4) for v in val]
                             for k, val in sorted(first["euler"].items())},
        "loop_euler_last": {k: [round(v, 4) for v in val]
                            for k, val in sorted(last["euler"].items())},
    }


# =============================================================== 主流程
def main():
    global SEAM_POSE, SEAM_EULER, SEAM_DIRS, Z_SEAM, ANKLE_0, IDLE_POSE
    global IDLE_KNEE_DIR, IDLE_BASIS, IDLE_DIR, ARM_LEN, ARM_BASIS
    global E0, E_END, E_END_UNW, SRC_MATS, ARM_BASIS_END
    global START_RX, REL_RX, START_LOC, REL_LOC

    for store in (SEAM_POSE, SEAM_EULER, SEAM_DIRS, ANKLE_0, IDLE_POSE,
                  IDLE_KNEE_DIR, IDLE_BASIS, IDLE_DIR, ARM_LEN,
                  ARM_BASIS, E0, E_END, E_END_UNW, _HIT_FROZEN, LOG,
                  HIT_POINT):
        store.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("C08_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
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
    SEAM_DIRS = {bone: tuple(A.bone_direction(arm, bone)) for bone in ARM_BONES}
    SRC_MATS = RS.action_world_matrices(arm, src, 0)
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}

    # ---- Idle 骨基座（`leg_seat` / `aim_bone_ref` 的缺省滚转基准）
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

    # ---- 位移轨道：**相对 Z_SEAM 的偏移**（米），不许走 `patch()`（C07 教训 1）
    START_LOC["y"] = ((0, 0.0), (8, -0.004), (LOOP_IN, PY_SUNK))
    START_LOC["z"] = ((0, 0.0), (8, -0.055), (LOOP_IN, PZ_SUNK - Z_SEAM))
    REL_LOC["x"] = ((LOOP_OUT, PX_SUNK), (HIT, 0.0), (HOLD_END, 0.0))
    REL_LOC["y"] = ((LOOP_OUT, PY_SUNK), (HIT, PY_BURST), (HOLD_END, PY_BURST))
    REL_LOC["z"] = ((LOOP_OUT, PZ_SUNK - Z_SEAM),
                    (HIT, PZ_BURST - Z_SEAM),
                    (HOLD_END, PZ_BURST + MOMENTUM_MM / 1000.0 - Z_SEAM))

    # ---- 躯干轨道：f0 回填 Idle 真值（★ 必须 global，见 C01 教训 1）
    def patch(track, bone, channel=0):
        return ((0, SEAM_EULER[bone][channel]),) + tuple(
            k for k in track if k[0] != 0)

    START_RX["pelvis"] = patch(START_RX["pelvis"], "pelvis")
    START_RX["spine_01"] = patch(START_RX["spine_01"], "spine_01")
    START_RX["spine_02"] = patch(START_RX["spine_02"], "spine_02")
    START_RX["chest"] = patch(START_RX["chest"], "chest")
    START_RX["neck"] = patch(START_RX["neck"], "neck")
    START_RX["head"] = patch(START_RX["head"], "head")
    START_RX["shoulder.rx"] = patch(START_RX["shoulder.rx"], "shoulder.L")
    START_RX["shoulder.rz"] = ((0, 0.0),) + tuple(
        k for k in START_RX["shoulder.rz"] if k[0] != 0)
    # ★ 释放轨道首键 = 起手末值（逐位接得上，不靠"两个手写常量碰巧相等"）
    for key in REL_RX:
        REL_RX[key] = ((LOOP_OUT, START_RX[key][-1][1]),) + tuple(REL_RX[key])
    for axis in REL_LOC:
        assert REL_LOC[axis][0][0] == LOOP_OUT, "REL_LOC 首键必须是 LOOP_OUT"
    for axis, track in START_LOC.items():
        assert track[0] == (0, 0.0), "START_LOC[%s] 必须 (0, 0.0) 起手" % axis
        assert track[-1][0] == LOOP_IN, "START_LOC[%s] 末键必须是 LOOP_IN" % axis
    # 自检：patch() 之后轨道首点必须是 Idle 真值（"静默不回填"的守卫，C01 教训 1）
    assert START_RX["pelvis"][0][1] == SEAM_EULER["pelvis"][0], "pelvis 未回填"
    assert START_RX["chest"][0][1] == SEAM_EULER["chest"][0], "chest 未回填"
    assert all(k[0] <= LOOP_IN for k in START_RX["chest"]), \
        "起手轨道不许越过 LOOP_IN（否则循环窗会被插值污染）"

    A.report("C08_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "start_end": LOOP_IN, "loop_in": LOOP_IN, "loop_out": LOOP_OUT,
        "hit": HIT, "hold": HOLD, "hold_end": HOLD_END,
        "return_start": RETURN_START, "settle": SETTLE, "cancel": CANCEL,
        "seam_source": [I1.NAME, 0],
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                      for s in SIDES},
        "pz_sunk_mm": round(PZ_SUNK * 1000.0, 1),
        "pz_burst_mm": round(PZ_BURST * 1000.0, 1),
        "pz_peak_with_momentum_mm": round(
            (PZ_BURST + MOMENTUM_MM / 1000.0) * 1000.0, 1),
        "end_pelvis_m": [END_PX, END_PY, END_PZ],
        "hitstop_bones": list(HITSTOP_BONES),
        "momentum_mm": MOMENTUM_MM,
        "tremble": {"k": TREMBLE_K, "hz": round(TREMBLE_K / (
            (LOOP_OUT - LOOP_IN) / float(A.FPS)), 3),
            "pelvis_x_mm": TREMBLE_PX_MM, "pelvis_z_mm": TREMBLE_PZ_MM,
            "chest_deg": TREMBLE_CHEST_DEG, "neck_deg": TREMBLE_NECK_DEG,
            "head_deg": TREMBLE_HEAD_DEG},
        "note": ("蓄力：首帧 = `Idle_01@0`（逐位）；起手 20f 下沉 100 mm 扎稳；"
                 "循环 36f 骨盆稳住、头颈 5 Hz 颤振、双拳握死；释放 16f 双拳"
                 "向两侧上方爆发 + 骨盆上顶；命停 3 帧 14 骨全冻、骨盆继续上爬；"
                 "收招单向减速到「半蹲戒备」。原地，无 Root Motion。"),
    })

    ARM_BASIS.clear()
    ARM_BASIS.update(build_arm_basis())
    # ★ 收招终点的臂世界基准：与相位表**同一构造**（= 从 Idle 基准做最小旋转），
    #   这样收招的 slerp 两端同源，中段不会冒出额外滚转。
    ARM_BASIS_END.clear()
    ARM_BASIS_END.update(key_basis(END_DIRS))
    A.report("C08_ARM_BASIS", {
        "phases": sorted(ARM_BASIS),
        "dirs": {name: {b: [round(c, 4) for c in (
            SEAM_DIRS if name == "SEAM" else ARM_KEYS[name])[b]]
            for b in ARM_BONES}
            for name in sorted(ARM_BASIS)},
        "end_dirs": {b: [round(c, 4) for c in END_DIRS[b]] for b in ARM_BONES},
        "recover_slerp_deg": {
            b: round(math.degrees(
                ARM_BASIS["BURST"][b].to_quaternion().rotation_difference(
                    ARM_BASIS_END[b].to_quaternion()).angle), 3)
            for b in ARM_BONES},
    })

    E_END = solve_end_arm(arm)
    A.report("C08_END_ARM", {
        "end_dirs": END_DIRS,
        "end_euler_deg": {k: [round(v, 4) for v in E_END[k]]
                          for k in ARM_BONES},
    })

    # ---- 建主片段
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
        "note": ("蓄力（三段）：起手 20f 下沉扎稳 → 循环 36f 握死蓄力 → "
                 "释放 16f 爆发上顶；命停 %d 帧 14 骨全冻；收招单向减速到"
                 "「半蹲戒备」。循环段另存独立 Action `%s`（loop=true）。"
                 % (HOLD, LOOP_NAME)),
        "antic_frame": LOOP_IN,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HOLD,
        "root_motion_m": [0.0, 0.0],
        "inherit_from": None,
        "segments": {"start": [0, LOOP_IN], "loop": [LOOP_IN, LOOP_OUT],
                     "release": [LOOP_OUT, HIT], "hold": [HIT, HOLD_END],
                     "recover": [HOLD_END, TOTAL]},
        "loop_partner": LOOP_NAME,
        "hit_point_m": dict(HIT_POINT),
        "end_pose_deg": {k: [round(v, 4) for v in val]
                         for k, val in sorted(END_ROT.items())},
        "end_arm_dirs": {k: [round(v, 6) for v in val]
                         for k, val in sorted(END_DIRS.items())},
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "DRAW": 9, "START_END": LOOP_IN, "LOOP_IN": LOOP_IN,
        "LOOP_OUT": LOOP_OUT, "HIT": HIT, "HOLD_END": HOLD_END,
        "RECOV": RETURN_START, "SETTLE": SETTLE, "CANCEL": CANCEL, "END": TOTAL,
    })

    # ---- 建循环片段：**逐帧复用**主片段循环窗的姿态字典（逐位一致）
    loop_keyframes = [(i, keyframes[LOOP_IN + i][1])
                      for i in range(0, LOOP_OUT - LOOP_IN + 1)]
    loop_meta = dict(meta)
    loop_meta.update({
        "anim_id": LOOP_NAME,
        "loop": True,
        "note": ("C08 蓄力循环段：逐帧复用 `%s` 的 [%d, %d] 窗，"
                 "首末帧逐位相同。" % (NAME, LOOP_IN, LOOP_OUT)),
        "parent_anim": NAME,
        "parent_frames": [LOOP_IN, LOOP_OUT],
    })
    loop_meta.pop("segments", None)
    loop_action, loop_meta = A.build_action(arm, LOOP_NAME, loop_keyframes,
                                            loop_meta)
    A.add_markers(loop_action, {"LOOP_IN": 0, "LOOP_OUT": LOOP_OUT - LOOP_IN})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    foots = foot_series(arm, action, meshes, TOTAL)
    if os.environ.get("C08_TRACE") == "1":
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for f in foots:
            fm = (Vector(f["hand_L_tail"]) + Vector(f["hand_R_tail"])) * 0.5
            print("C08_TRACE " + json.dumps({
                "f": f["frame"], "s": round(tremble(f["frame"]), 4),
                "q": round(q_of(f["frame"]), 5),
                "pelvis": [round(v * 1000.0, 2) for v in f["pelvis"]],
                "fist_mid": [round(v * 1000.0, 2) for v in fm],
                "L_sole": (None if f["sole_L"] is None
                           else round(f["sole_L"] * 1000.0, 3)),
                "R_sole": (None if f["sole_R"] is None
                           else round(f["sole_R"] * 1000.0, 3)),
                "L_reach": round(f["reach_L"] * 1000.0 / limit_mm, 4),
                "R_reach": round(f["reach_R"] * 1000.0 / limit_mm, 4),
            }))

    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.update(charge_assertions(arm, action, samples, foots))
    report["loop_action"] = loop_action_assertions(arm, loop_action)
    report["charge_loop_ok"] = bool(
        loop_meta.get("loop") is True
        and report["loop_action"]["loop_seamless"] is True
        and report["charge_loop_window_ok"] is True)

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
    report["hit_point_m"] = dict(HIT_POINT)
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C08_REPORT", report)

    if not SKIP_RENDER:
        # ★ 取景由**实测包围盒**算（C06 教训 2 / C07 教训 4）。
        frames = [0, 9, LOOP_IN, LOOP_IN + 9, LOOP_OUT, HIT, HOLD_END,
                  SETTLE, TOTAL]
        ratio = 780.0 / 1100.0
        keys = [k for k in samples[0]
                if k != "frame" and isinstance(samples[0][k], tuple)]
        pts = [Vector(s[k]) for s in samples for k in keys if k in s]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        zs = [p.z for p in pts]
        center = (0.5 * (min(xs) + max(xs)),
                  0.5 * (min(ys) + max(ys)),
                  0.5 * (min(zs) + max(zs)))
        scale = max(2.10,
                    (max(zs) - min(zs)) * 1.15,
                    (max(xs) - min(xs)) * 1.15 / ratio,
                    (max(ys) - min(ys)) * 1.15 / ratio)

        def reframe(view):
            """保留原视图的**方向**，只按实测包围盒重定中心与跨度。"""
            _name, location, target, _scale, res = view
            direction = (Vector(location) - Vector(target)).normalized()
            new_target = Vector(center)
            new_location = new_target + direction * 4.6
            return (_name, tuple(new_location), tuple(new_target), scale, res)

        A.report("C08_CAMERA", {
            "bbox_min": [round(min(xs), 4), round(min(ys), 4), round(min(zs), 4)],
            "bbox_max": [round(max(xs), 4), round(max(ys), 4), round(max(zs), 4)],
            "center": [round(v, 4) for v in center],
            "ortho_scale": round(scale, 4),
            "z_top_of_frame_m": round(center[2] + scale / 2.0, 4),
            "note": ("爆发帧双拳摆到肩上方，标准视图（中心 0.92）可能切顶，"
                     "故按实测包围盒重定；三视角沿用各自原方向。"),
        })
        for base in (A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q):
            A.render_pose_sheet(arm, action, frames, "charge08",
                                views=(reframe(base),))
    A.save_project()
    A.export_glb(arm)
    print("C08_DONE failed=%s" % report["failed"])
    print("C08_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C08_FAILURE " + traceback.format_exc())
