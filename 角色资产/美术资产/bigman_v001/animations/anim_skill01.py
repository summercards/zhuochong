"""anim_skill01 —— C09 `Skill_01` 肩撞（C 族第九支，**两段：起步 / 冲刺撞击**）。

=============================================================================
清单原文
=============================================================================
「起步短、前冲强，**肩膀作为明确命中点**。」

=============================================================================
第 0 件 —— 分段形态：**一次性单段片段**（起步 8f + 冲刺 + 命停 + 收招）
=============================================================================
与 C08（三段、有循环）不同，本支清单没有循环要求 ⟹ 一个 Action 即可：

    (0)─起步 8f─>(8)─冲刺 28f─>(36 命中)─命停 4f─>(39)─收招 51f─>(90 定)─6f─>(96)

    起步  8 帧 = 0.133 s  ← 清单「起步短」的字面量化（门禁 `start_short_ok` ≤8f）
    冲刺 28 帧 = 0.467 s  ← 骨盆前冲 590 mm（速度线性上升 ⟹ 越冲越快，见第 2 件）
    命停  4 帧 = 0.067 s  ← §0.1 的 2~4 帧区间上界（肩撞是重技能，取满）
    收招 57 帧 = 0.950 s  ← 单向减速回到「战斗待机」

=============================================================================
第 1 件 —— 首帧 = `Idle_01@0`，逐位（`SEAM_TOL = 1e-6`）
=============================================================================
读 `Idle_01` Action 在 f0 的真值（全 57 骨 `rotation_euler` + `pelvis.location`），
`patch()` 把 f0 回填成同一批值。**末帧有意不回 Idle**（同 C07/C08）：
本支腿走 `leg_seat`（三维 IK），Idle 腿走 `leg_ik`（平面解析），两者世界方向一致
但欧拉滚转不逐位一致 ⟹ 强行「末帧 = Idle」会被逐位门禁打回。
末帧登记在 Action 自定义属性 `end_pose_deg`（= **战斗待机**的躯干姿），
并由门禁 `tail_settle_ok` 盯着「实测 == 登记」。

=============================================================================
第 2 件 —— ★「前冲强」与「脚不滑」：清单 §0.4 允许 Root Motion，代价写进门禁
=============================================================================
清单把「前冲惯性 vs 脚不滑」列为本支核心难点。本支的取舍（按计划 §2）：

* **允许 Root Motion**：骨盆世界 y 从 0 冲到 **−560 mm**（净 −545 mm）。
* **支撑脚在地上「拖」**（脚随骨盆平移，鞋底全程钉在 0）—— 这正是「前冲强」的
  视觉本体：猛男型角色不是「跳过去」，是**整个身体压着地面推过去**。
* ⟹ 通用 `no_foot_slide_*`（位移 ≤3 mm）**必须撤下**，但**不许裸撤**：
  改判 **`drag_speed_ok`（冲刺段每帧前进量单调非减：起步即有速、撞击前最快）**。
  这条会被失败：若把拖行做成「匀速」或「先快后慢」，它立刻红。
  ★ 窗口**只到 HIT 为止**，不含命停段（那段骨盆只再压 25 mm/4f = 6.25 mm/f，
    远慢于冲刺末的 31 mm/f ⟹ 算进来必然破单调）。

`probe_c09_baseline.py` 实测（`C09PROBE_DASH`，踝随骨盆拖行）：

| 骨盆 y (mm) | 骨盆 z (mm) | 腿可达比 L / R | 读法 |
|---|---|---|---|
| 0（Idle） | 830 | 0.938 / 0.931 | 站架起点 |
| −150 | 780 | 0.880 / 0.873 | —— |
| −300 | 760 | 0.857 / 0.850 | —— |
| −450 | 745 | 0.841 / 0.835 | —— |
| **−560（HIT）** | **740** | **0.836 / 0.830** | ★ 余量 0.16，远不到锁死区 |
| −650 | 740 | 0.837 / 0.832 | 兜住上限 |

**结论**：前冲 560 mm 对腿是**放松**方向（髋踝距离随身体前压 + 屈膝而缩短），
真正的约束是「前冲太远会读成瞬移」—— 由 `root_motion_ok` 的 900 mm 上限兜。

=============================================================================
第 3 件 —— ★「肩膀作为明确命中点」怎么量化
=============================================================================
`shoulder_hit_ok`：命中帧 **`shoulder.<撞出侧>` 的 tail** 必须比**双拳**更靠前
（`−y` 更小）**≥ 150 mm**。`probe_c09_baseline.py` 的 `C09PROBE_ARM` 实测：

| 臂姿 | 肩相对「最前的拳」的领先量 |
|---|---|
| **HIT_DIRS（双臂向后甩）** | **+550 mm** ✓ |
| STRAIGHT_DOWN（自然下垂） | −0 mm ✗ |
| GUARD（Idle 拳架） | −257 mm ✗ |

根因：臂长 ~0.65 m，若臂自然下垂则拳与肩**同 y**（都在肩下），判据必红。
⟹ 撞出瞬间双臂必须**明确向后甩**（拳落在肩后 ~0.5 m），读作「用肩撞」而不是「用手撞」。

另：躯干**扭转**是送左肩出去的手段。`C09PROBE_TWIST` 实测
`shoulder_asym_mm = (shoulder.R.y − shoulder.L.y)`：**twist −22° → +303 mm**
（即**负号**扭转才把左肩送到前面，起步蓄力用 +13° 反向拉回）。本支撞出侧 = **左**。

=============================================================================
第 4 件 —— 命停：骨冻住、身体还在前压（C08 第 2 号教训的延续）
=============================================================================
命停 [36, 39]：**14 骨旋转逐位冻结**（躯干 8 + 臂 6），而骨盆**继续前压 25 mm**
（`hitstop_keeps_momentum_ok` 要 > 10 mm）⟹ 读作「撞上去了，力还在往前灌」。
位移与旋转**分开决定**冻不冻（`freeze_hold`），否则动量判据恒红。

=============================================================================
第 5 件 —— 收招回「战斗待机」：登记值 = Idle@0 的躯干真值（C08 第 5 号教训）
=============================================================================
收招段把**旋转与位移**都按 `q(frame) = 1 − (1−u)^POST_POW` 仿射到末姿
（★ 旋转也必须混，否则 `RS.track` 会把躯干钳在末键、登记值与实测差十几度）。
末姿 `END_ROT` **直接取 `Idle_01@0` 的躯干真值**（不是手写常量）⟹
`tail_settle_ok` 用 0.05° 公差盯住「实测 == 登记」。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_skill01.py
    SKIP_RENDER=1 只跑门禁（迭代用）；C09_TRACE=1 打逐帧轨迹。
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

NAME = "Skill_01"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")
HIT_SIDE = "L"                  # 撞出侧（清单「肩膀作为明确命中点」）
LEAD_SIDE = HIT_SIDE


def _env_f(key, default):
    return float(os.environ[key]) if os.environ.get(key) else float(default)


def _env_i(key, default):
    return int(os.environ[key]) if os.environ.get(key) else int(default)


SOLE_DIAG = os.environ.get("C09_SOLE_DIAG") == "1"
SOLE_DIAG_FRAMES = frozenset(
    int(v) for v in (os.environ.get("C09_SOLE_DIAG_FRAMES") or "8,36,39,45,60,96")
    .split(",") if v.strip())


# ---------------------------------------------------------------- 帧预算
TOTAL = _env_i("C09_TOTAL", 96)           # 1.600 s @60fps
ANTIC = _env_i("C09_ANTIC", 8)            # 起步段末（清单「起步短」⟹ ≤8）
DASH_IN = ANTIC
HIT = _env_i("C09_HIT", 36)               # 命中帧（肩撞上目标）
HOLD = _env_i("C09_HOLD", 4)              # 命停 4 帧（§0.1 的 2~4 上界）
HOLD_END = HIT + HOLD - 1                 # 39
RETURN_START = HOLD_END + 1               # 40
SETTLE = _env_i("C09_SETTLE", 90)         # 收招落定（此后逐位静止）
CANCEL = _env_i("C09_CANCEL", 92)         # 可取消帧
# ★ TOTAL = SETTLE + 6（C07/C08 约定）：落定后留 6 帧静止窗给引擎混合。
POST_POW = _env_f("C09_POSTPOW", 1.25)    # 收招缓动 q = 1 − (1−u)^p
# ★ 前冲速度剖面：v(u) = v0 + (v1−v0)·u，v0 = DASH_R0·v1。
#   归一化位移 y(u) = Δ·(r·u + (1−r)·u²/2) / ((1+r)/2)，速度是 **u 的线性函数**
#   ⟹ 单调非减（`dash_speed_ok`）。r<1 保证严格递增。
#   ★ 为什么不是 y = Δ·u^p：p=2 时首帧只走 Δ/n² = 0.59/784 = **0.75 mm**
#     （≈0.04% 身高，肉眼是「卡住」），与清单「起步短、前冲强」直接打架 ——
#     实测前 5 帧只推进 19 mm。改成本剖面后首帧 **11.3 mm**（4 倍），
#     末帧 31.2 mm（1.87 m/s，仍是最快），单调判据不变。
DASH_R0 = _env_f("C09_DASH_R0", 0.35)

# 命停窗内骨盆继续前压的量（`hitstop_keeps_momentum_ok` 要 > 10 mm）
MOMENTUM_MM = _env_f("C09_MOMENTUM", 25.0)

# ---------------------------------------------------------------- 姿态常量
# 骨盆世界位置（米）。Idle 的骨盆世界 y 实测 = 0.000（`C09PROBE_IDLE`）。
PY_COIL = _env_f("C09_PY_COIL", 0.030)    # 起步末：重心微后坐（蓄力）
PZ_COIL_DROP = _env_f("C09_PZ_COIL", 0.030)   # 起步末：下沉
PY_HIT = _env_f("C09_PY_HIT", -0.560)     # 命中帧：前冲 560 mm
PZ_HIT_DROP = _env_f("C09_PZ_HIT", 0.090)     # 命中帧：压低重心
PY_END = _env_f("C09_PY_END", -0.545)     # 末帧：略回坐（净 Root Motion 545 mm）
# 拖行系数：两脚都不许追过骨盆 —— 身体是**从脚上压过去**的（推地前冲），
# 不是脚抢在前面。★ 首版 LAG_L=1.04（前脚抢）导致命中帧脚尖比肩还前 38 mm，
# 被 `hit_point_frontmost_ok` 当场抓住（"脚先撞上"）。改 0.90 / 0.80 后
# 前脚回退 78 mm，站架改由**后脚多拖**来压开（前后脚差 64 mm）。
LAG_L = _env_f("C09_LAG_L", 0.90)
LAG_R = _env_f("C09_LAG_R", 0.80)
LAG = {"L": LAG_L, "R": LAG_R}

# 躯干轨道（度）。分**起步（START）/ 撞击（REL）两条**；两端在 ANTIC 处数值相接。
# START 的 f0 由 `patch()` 回填 `Idle_01@0` 真值（禁手写）。
# ★ 头颈的收（负 rx = 向后）是**本支的命中点成立条件**：躯干前压 45° 后，
#   头若还保持相对竖直就会被顶到肩前面去。见 `hit_point_frontmost_ok`。
NECK_RX_HIT = _env_f("C09_NECK_RX", -46.0)
HEAD_RX_HIT = _env_f("C09_HEAD_RX", -26.0)
NECK_RX_ANTIC = _env_f("C09_NECK_RX_ANTIC", -11.0)
HEAD_RX_ANTIC = _env_f("C09_HEAD_RX_ANTIC", -6.0)
START_RX = {
    "pelvis": ((0, 0.0), (ANTIC, 5.0)),
    "spine_01": ((0, 0.0), (ANTIC, 3.0)),
    "spine_02": ((0, 0.0), (ANTIC, 3.0)),
    "chest": ((0, 0.0), (ANTIC, 3.0)),
    "neck": ((0, 0.0), (ANTIC, NECK_RX_ANTIC)),
    "head": ((0, 0.0), (ANTIC, HEAD_RX_ANTIC)),
    "shoulder.L": ((0, 0.0), (ANTIC, -14.0)),
    "shoulder.R": ((0, 0.0), (ANTIC, -14.0)),
}
REL_RX = {
    "pelvis": ((HIT, 15.0), (HOLD_END, 15.0)),
    "spine_01": ((HIT, 11.0), (HOLD_END, 11.0)),
    "spine_02": ((HIT, 11.0), (HOLD_END, 11.0)),
    "chest": ((HIT, 8.0), (HOLD_END, 8.0)),
    # ★ 头颈必须**明确向后收**（rx<0 = 向后，见 `rig_axis_map.md`）。
    #   首版 neck −14 / head −5 ⟹ 头随躯干 45° 前压后仍在**肩前 132 mm**
    #   （`head_m` y=−0.992 vs `shoulder` y=−0.860）⟹ 剪影读成「用脸撞」，
    #   与清单「肩膀作为明确命中点」不符。改判据见 `hit_point_frontmost_ok`。
    "neck": ((HIT, NECK_RX_HIT), (HOLD_END, NECK_RX_HIT)),
    "head": ((HIT, HEAD_RX_HIT), (HOLD_END, HEAD_RX_HIT)),
    "shoulder.L": ((HIT, -10.0), (HOLD_END, -10.0)),
    "shoulder.R": ((HIT, -10.0), (HOLD_END, -10.0)),
}
# 扭转：**负号 = 左肩向前**（`C09PROBE_TWIST` 定标）。起步蓄力反向拉回 +13。
START_RY = {
    "pelvis": ((0, 0.0), (ANTIC, 3.6)),
    "spine_01": ((0, 0.0), (ANTIC, 3.1)),
    "spine_02": ((0, 0.0), (ANTIC, 3.1)),
    "chest": ((0, 0.0), (ANTIC, 3.1)),
    "neck": ((0, 0.0), (ANTIC, -7.0)),
    "head": ((0, 0.0), (ANTIC, -6.0)),
}
REL_RY = {
    "pelvis": ((HIT, -7.9), (HOLD_END, -7.9)),
    "spine_01": ((HIT, -6.7), (HOLD_END, -6.7)),
    "spine_02": ((HIT, -6.7), (HOLD_END, -6.7)),
    "chest": ((HIT, -6.7), (HOLD_END, -6.7)),
    "neck": ((HIT, 15.0), (HOLD_END, 15.0)),
    "head": ((HIT, 13.0), (HOLD_END, 13.0)),
}
# ★ 撞出侧肩的**前送**（`shoulder.L` rz<0 = 向前，见 `rig_axis_map.md`：
#   15° ⟹ tail 位移 29.19 mm「后」）。这是「肩膀作为明确命中点」最直接的一根控制：
#   躯干扭转只能把肩绕轴带出去（实测 ~1.06 mm/度），而肩自己的前伸是 1.95 mm/度。
#   首版没有这根通道 ⟹ 命中帧胸部端点只落后肩 23 mm，`hit_point_frontmost_ok`
#   的 40 mm 剪影余量过不去（视觉上「胸和肩一起撞」）。
SHOULDER_L_RZ_HIT = _env_f("C09_SH_RZ", -18.0)
START_RZ = {
    "shoulder.L": ((0, 0.0), (ANTIC, 6.0)),      # 蓄力时反向夹紧（含胸）
    "shoulder.R": ((0, 0.0), (ANTIC, 6.0)),
}
REL_RZ = {
    "shoulder.L": ((HIT, SHOULDER_L_RZ_HIT), (HOLD_END, SHOULDER_L_RZ_HIT)),
    "shoulder.R": ((HIT, 4.0), (HOLD_END, 4.0)),  # 非撞出侧略后收，拉开剪影
}
RX_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
            "shoulder.L", "shoulder.R")
RY_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head")
RZ_BONES = ("shoulder.L", "shoulder.R")

# ---------------------------------------------------------------- 收招末姿
# ★ 登记值 = **Idle_01@0 的躯干真值**（战斗待机），main() 里从 SEAM_EULER 回填。
END_ROT = {}

# ---------------------------------------------------------------- 手臂方向轨道
# 世界单位向量：x = 左正，y = 身后正，z = 上正，角色正面朝 −y。
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
ARM_KEYS = {
    # ★ 命中：双臂完全甩到身后 ⟹ 肩成为最前点（`shoulder_hit_ok` 的来源）
    "HIT": {
        "upperarm.L": (0.24, 0.80, -0.55),
        "forearm.L": (0.10, 0.88, -0.46),
        "hand.L": (0.05, 0.92, -0.39),
        "upperarm.R": (-0.24, 0.80, -0.55),
        "forearm.R": (-0.10, 0.88, -0.46),
        "hand.R": (-0.05, 0.92, -0.39),
    },
}
# 中间键 `MID1` / `MID2` **在运行时**由 `SEAM → HIT` 的测地线等分生成（`build_arm_basis`）。
# ★ 为什么不能手写：Idle 拳架的前臂指向前上方（−y,+z），命中姿指向上后方（+y,−z），
#   两者夹角实测 **141°**；手写的中间键若不在测地线上，会让某一帧的世界转角
#   飙到 30°+（首版 `world_step_ok` 31.6 @f4、`no_teleport` 86.0 @f16 的现场指纹）。
#
# ★ 等分点**必须**取在 `SEAM→HIT` 的**同一条 SO(3) 测地线**上（用矩阵 slerp 生成），
#   这样「分段 slerp」与「整段 slerp」逐位等价 ⟹ 臂的世界角速度全程恒定，
#   不存在换段的折角。若改成在帧号上等分**方向**再重新解算基准（`key_basis`），
#   三段会各走各的测地线，接缝处出现 1~2° 的折角。
MID1_F = _env_i("C09_MID1", 10)
MID2_F = _env_i("C09_MID2", 22)
ARM_PHASES = ((0, "SEAM", "linear"), (MID1_F, "MID1", "linear"),
              (MID2_F, "MID2", "linear"), (HIT, "HIT", "linear"),
              (HOLD_END, "HIT", "linear"))

# ★ 14 骨全冻（C04/C07/C08 那套；本支无位置逆解 ⟹ 冻结欧拉 = 冻结视觉）
HITSTOP_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "shoulder.L", "shoulder.R",
                 "upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R")

# ---------------------------------------------------------------- 门禁阈值
SOLE_RANGE_MM = (-2.0, 6.0)
NO_TELEPORT_MAX_DEG = 25.0
SEAM_TOL = 1e-6
REACH_MAX_RATIO = 0.995
# C09 新增门禁
SHOULDER_LEAD_MIN_MM = _env_f("C09_LEAD_MIN", 150.0)     # 肩必须比双拳更前
# ★★ 命中点必须是全身最前点（比 `shoulder_hit_ok` 严）：头/胸/膝/脚/拳都要被甩开。
#    0 mm 是"严格最前"；实际给 40 mm 的剪影余量，免得平手帧被判成肩撞。
HIT_POINT_LEAD_MIN_MM = _env_f("C09_FRONT_MIN", 40.0)
# ★★ 网格面剪影：躯干最前面必须比头面更前 ≥ 60 mm、比鞋尖更前 ≥ 30 mm
SILHOUETTE_HEAD_MIN_MM = _env_f("C09_SIL_HEAD_MIN", 60.0)
SILHOUETTE_SHOE_MIN_MM = _env_f("C09_SIL_SHOE_MIN", 30.0)
ROOT_MIN_MM = _env_f("C09_ROOT_MIN", 400.0)              # 前冲 ≥ 400 mm
ROOT_MAX_MM = _env_f("C09_ROOT_MAX", 900.0)              # 前冲 ≤ 900 mm
LEAN_MIN_DEG = _env_f("C09_LEAN_MIN", 35.0)              # 撞击帧躯干前倾和
DRAG_STEP_TOL_MM = _env_f("C09_DRAG_TOL", 0.05)          # 单调判据的浮点余量
END_POSE_TOL_DEG = _env_f("C09_END_TOL", 0.05)           # 元数据不许撒谎

# ---------------------------------------------------------------- 观测量
SEAM_POSE = {}
SEAM_EULER = {}
SEAM_DIRS = {}
Z_SEAM = 0.0
Y_SEAM = 0.0
ANKLE_0 = {}
IDLE_POSE = {}
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
ARM_LEN = {}
ARM_BASIS = {}
E0 = {}
E_END = {}
E_END_UNW = {}
_HIT_FROZEN = {}
HIT_POINT = {}
SRC_MATS = {}
LOG = {}


def _hold(frame):
    return HIT < frame <= HOLD_END


def in_dash(frame):
    return DASH_IN < frame <= HIT


def in_drag(frame):
    return DASH_IN < frame <= HOLD_END


def q_of(frame):
    """收招进度：0 = 命中（冻结值），1 = 战斗待机。增量单调递减 ⟹ 步长单调不增。"""
    if frame <= HOLD_END:
        return 0.0
    if frame >= SETTLE:
        return 1.0
    u = (frame - HOLD_END) / float(SETTLE - HOLD_END)
    return 1.0 - (1.0 - u) ** POST_POW


# =============================================================== 姿态
def _seg(keys_start, keys_release, frame):
    """两段取值：起步插值 / （命停冻结在 HIT）/ 撞击插值。

    与 C08 的三段版相比少了「循环窗」—— 本支无循环，故不需要显式冻结段。
    命停窗映射到 HIT ⟹ 旋转轨道逐位冻住（REL_* 在 HIT / HOLD_END 同值）。
    """
    if frame <= ANTIC:
        return RS.track(keys_start, frame)
    probe = HIT if _hold(frame) else frame
    return RS.track(keys_release, probe)


def dash_ramp(u):
    """冲刺位移比：速度随 u 线性上升（首帧已有 DASH_R0 的速度），末帧最快。"""
    return (DASH_R0 * u + (1.0 - DASH_R0) * u * u * 0.5) / ((1.0 + DASH_R0) * 0.5)


def pelvis_pos(frame):
    """骨盆世界 (x, y, z)。前冲 y 用**速度线性上升**的剖面（第 2 件）。"""
    if frame <= ANTIC:
        py = RS.track(((0, 0.0), (ANTIC, PY_COIL)), frame)
        pz = Z_SEAM - RS.track(((0, 0.0), (ANTIC, PZ_COIL_DROP)), frame)
    elif frame <= HIT:
        u = (frame - ANTIC) / float(HIT - ANTIC)
        py = PY_COIL + (PY_HIT - PY_COIL) * dash_ramp(u)
        pz = (Z_SEAM - PZ_COIL_DROP) + (
            (Z_SEAM - PZ_HIT_DROP) - (Z_SEAM - PZ_COIL_DROP)) * (u ** 1.4)
    elif frame <= HOLD_END:
        # 命停期：旋转冻在 HIT，但骨盆**继续前压**（顿感的另一半，第 4 件）
        u = (frame - HIT) / float(HOLD_END - HIT)
        py = PY_HIT - (MOMENTUM_MM / 1000.0) * u
        pz = (Z_SEAM - PZ_HIT_DROP) - 0.008 * u
    else:
        q = q_of(frame)
        py0 = PY_HIT - MOMENTUM_MM / 1000.0
        pz0 = (Z_SEAM - PZ_HIT_DROP) - 0.008
        py = py0 + (PY_END - py0) * q
        pz = pz0 + (Z_SEAM - pz0) * q
    return 0.0, py, pz


def ankle_targets(frame):
    """踝世界目标：踝随骨盆**拖行**（lag 系数），鞋底 z 由 `solve_pose` 闭环钉到 0。"""
    _, py, _ = pelvis_pos(frame)
    drag = 0.0 if frame <= ANTIC else (py - PY_COIL)
    return {side: (ANKLE_0[side].x,
                   ANKLE_0[side].y + drag * LAG[side],
                   ANKLE_0[side].z) for side in SIDES}


def torso_pose(frame):
    """躯干旋转 + 骨盆位移。收招段用 `q()` 仿射到「战斗待机」。"""
    rx = {name: _seg(START_RX[name], REL_RX[name], frame) for name in RX_BONES}
    ry = {name: _seg(START_RY[name], REL_RY[name], frame) for name in RY_BONES}
    rz = {name: _seg(START_RZ[name], REL_RZ[name], frame) for name in RZ_BONES}
    base = {name: (rx[name], ry.get(name, 0.0), rz.get(name, 0.0))
            for name in RX_BONES}
    _, py, pz = pelvis_pos(frame)

    if frame > HOLD_END:
        q = q_of(frame)
        # ★★ 旋转必须跟着 `q` 走（C08 第 5 号教训）：否则 `RS.track` 会把躯干钳在
        #   末键 ⟹ 登记的末姿与实测差十几度，而所有步长类门禁都量不到。
        for name, end in END_ROT.items():
            cur = base[name]
            base[name] = tuple(cur[c] + (end[c] - cur[c]) * q
                               for c in range(3))
    rot = dict(base)
    rot["@loc"] = {"pelvis": A.wloc(0.0, py, pz - 0.900)}
    return rot


def key_basis(dirs):
    """把一组世界方向解成各骨的**世界基准 3×3**（= 从 Idle 基准做最小旋转）。"""
    out = {}
    for bone in ARM_BONES:
        quat = (Vector(IDLE_DIR[bone]).normalized()
                .rotation_difference(Vector(dirs[bone]).normalized()))
        out[bone] = quat.to_matrix() @ IDLE_BASIS[bone]
    return out


def _basis_slerp(basis_a, basis_b, t):
    """两个世界 3×3 之间的测地线插值（走最短弧，处理 q/−q 双覆盖）。"""
    qa = basis_a.to_quaternion()
    qb = basis_b.to_quaternion()
    if qa.dot(qb) < 0.0:
        qb = Quaternion((-qb.w, -qb.x, -qb.y, -qb.z))
    return qa.slerp(qb, t).to_matrix()


def build_arm_basis():
    """SEAM / HIT 两个端点基准 + 由**端点基准 slerp** 得到的 MID1/MID2。

    ★ MID1/MID2 不许用 `key_basis(中间方向)` 重新解算 —— 那会换一条测地线，
      段落接缝处出现折角；必须直接在 `SEAM → HIT` 的基准测地线上取点。
    """
    table = {"SEAM": key_basis(SEAM_DIRS), "HIT": key_basis(ARM_KEYS["HIT"])}
    for name, at in (("MID1", MID1_F), ("MID2", MID2_F)):
        t = at / float(HIT)
        table[name] = {bone: _basis_slerp(table["SEAM"][bone],
                                          table["HIT"][bone], t)
                       for bone in ARM_BONES}
    return table


def arm_phase(frame):
    if _hold(frame):
        frame = HIT
    bounds = [item[0] for item in ARM_PHASES]
    if frame <= bounds[0]:
        return ("SEAM", "SEAM", 0.0)
    if frame >= bounds[-1]:
        return ("HIT", "HIT", 1.0)
    for index in range(len(ARM_PHASES) - 1):
        fa, na, mode = ARM_PHASES[index]
        fb, nb, _mb = ARM_PHASES[index + 1]
        if not (fa <= frame <= fb) or fa == fb:
            continue
        u = (frame - fa) / float(fb - fa)
        t = (u if mode == "linear" else RS.smooth(u))
        return (na, nb, t)
    return ("HIT", "HIT", 1.0)


def arm_basis(frame):
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

    # ★ `shift` 必须加进踝目标 z —— 贴地闭环靠的正是它（首版漏在 `ankle_targets`
    #   里没带上，闭环变成空转，右脚鞋底全程骑在 −1~−2 mm）。
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

    if frame <= HOLD_END:
        basis = arm_basis(frame)
        for bone in ARM_BONES:
            pose[bone] = JS._unwrap_xyz(
                JS._PREV_EULER.get(bone),
                aim_world_basis(arm, bone, basis[bone]))
    else:
        # ★ 收招的臂 = **欧拉仿射**（C08 第 4 件：幅度大时「单段欧拉仿射 + 拉长帧数」
        #   优于「换插值路径」——slerp 的局部欧拉模长中段最大，会破坏单调收敛）。
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
        # ★ 登记命中点的世界坐标（**肩**，不是拳）—— 供下游 VFX / 镜头 / D 族定位。
        sh = Vector(A.bone_world(arm, "shoulder." + HIT_SIDE, "tail"))
        fist = {s: Vector(A.bone_world(arm, "hand." + s, "tail"))
                for s in SIDES}
        front_fist_y = min(fist[s].y for s in SIDES)
        HIT_POINT.clear()
        HIT_POINT.update({
            "frame": HIT,
            "side": HIT_SIDE,
            "shoulder_m": [round(v, 4) for v in sh],
            "fist_L_m": [round(v, 4) for v in fist["L"]],
            "fist_R_m": [round(v, 4) for v in fist["R"]],
            "shoulder_lead_mm": round((front_fist_y - sh.y) * 1000.0, 2),
            "pelvis_m": [round(v, 4)
                         for v in A.bone_world(arm, "pelvis", "head")],
            "head_m": [round(v, 4)
                       for v in A.bone_world(arm, "head", "tail")],
            # ★★ 真正的"接触面"= 躯干组最前顶点（骨端点埋在肉里 107 mm，不能当
            #    下游 VFX / 命中判定的落点）。两者都给：`shoulder_m` 给绑定位，
            #    `contact_m` 给贴面位。
            "contact_m": ([round(v, 4) for v in _frontmost_of(TORSO_MESHES)]
                          if CONTACT_MEASURE else None),
            "rivals_m": {
                name: [round(v, 4) for v in A.bone_world(arm, name, "tail")]
                for name in ("head", "chest", "shin.L", "shin.R",
                             "foot.L", "foot.R")},
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

    ★ `C09PROBE_DASH` 实测 HIT 姿右脚鞋底 **−2.07 mm**（越过 ground_contact 的
    −2 mm 下限，因为前冲压低重心让鞋形微变）⟹ 必须闭环顶回 0。
    """
    shift = {side: 0.0 for side in SIDES}
    snap = _snapshot_carry()
    pose = build_pose(arm, frame, shift)
    if meshes is None:
        return pose
    for step in range(6):
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        if SOLE_DIAG and frame in SOLE_DIAG_FRAMES:
            print("C09_SOLE_DIAG " + json.dumps({
                "f": frame, "it": step,
                "shift_mm": {s: round(shift[s] * 1000.0, 4) for s in SIDES},
                "sole_mm": {s: (None if low[s] is None
                                else round(low[s][2] * 1000.0, 4))
                            for s in SIDES},
                "hip_ankle_ratio": {s: round(
                    (Vector(A.bone_world(arm, "thigh." + s, "head"))
                     - Vector(A.bone_world(arm, "foot." + s, "head"))).length
                    / (A.L_THIGH + A.L_SHIN), 4) for s in SIDES},
            }))
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
    # 末帧骨盆位置 = 战斗待机高度 + Root Motion 后的前向位移
    torso["@loc"] = {"pelvis": A.wloc(0.0, PY_END, Z_SEAM - 0.900)}
    A.apply_pose(arm, torso)
    for side in SIDES:
        G4.leg_seat(arm, torso, side, ankle_targets(TOTAL)[side],
                    IDLE_KNEE_DIR[side])
    for side in SIDES:
        A.keep_world_orientation(arm, "foot." + side)
    out = {}
    for bone in ARM_BONES:
        out[bone] = JS._unwrap_xyz(
            None, G4.aim_bone_ref(arm, bone, I1.ARM_DIRS[bone],
                                  IDLE_BASIS[bone], IDLE_DIR[bone]))
    return out


# =============================================================== 逐帧实测
def _sole_anchor(side):
    """找该侧鞋底「最前的最低点」顶点的 (对象名, 顶点号) —— 枢轴基准（C07 教训 3）。"""
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
        # ★ 命中点竞争者（`hit_point_frontmost_ok` 要逐帧比 y）
        for key, bone, which in (("chest", "chest", "tail"),
                                 ("head", "head", "tail"),
                                 ("shin_L", "shin.L", "tail"),
                                 ("shin_R", "shin.R", "tail"),
                                 ("foot_L", "foot.L", "tail"),
                                 ("foot_R", "foot.R", "tail")):
            row[key] = tuple(A.bone_world(arm, bone, which))
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
            row["shoulder_" + side] = tuple(
                A.bone_world(arm, "shoulder." + side, "tail"))
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
                         "shin.L", "shin.R", "shoulder.L", "shoulder.R")
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


# # ★ 骨端点是**代理**，量不到"脸"和"胸面"。命中点是否真的最前，要用**网格面**
# 复测一遍：头组（含鼻/发/镜）与躯干组各自的最前顶点。
HEAD_MESHES = ("Head", "Nose", "Hair_Mass", "Hair_Sweep",
               "Glasses_Frame_L", "Glasses_Frame_R", "Glasses_Bridge",
               "Glasses_Temple_L", "Glasses_Temple_R",
               "Ear_L", "Ear_R")
TORSO_MESHES = ("Suit_Torso", "Shirt_Front", "Shirt_Collar", "Jacket_Collar",
                "Jacket_Hem", "Jacket_Vent", "Jacket_Back_Seam",
                "Collar_Point_L", "Collar_Point_R",
                "Jacket_Lapel_L", "Jacket_Lapel_R", "Lapel_Fold_L",
                "Lapel_Fold_R", "Lapel_Notch_L", "Lapel_Notch_R",
                "Pocket_Flap_L", "Pocket_Flap_R", "Jacket_Button_1",
                "Jacket_Button_2", "Jacket_Hem_Line")


def _frontmost_of(names):
    """一组网格里**最靠前（y 最小）**的顶点世界坐标 —— 剪影前沿实测。"""
    deps = bpy.context.evaluated_depsgraph_get()
    best = None
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            point = matrix @ vertex.co
            if best is None or point.y < best[1]:
                best = (point.x, point.y, point.z)
        evaluated.to_mesh_clear()
    return best


CONTACT_MEASURE = True


def silhouette_front(arm, action, frames):
    """在**最终 Action** 上复测剪影前沿（头组 / 躯干组 / 鞋组的最前顶点）。

    ★ 为什么要另做一遍：`bone_world` 取的是**骨端点**（`head` 的 tail 是颅顶），
      而观众看到的是**网格面**。首版据此判"肩最前"为真，实际剪影是脸先到 ——
      两个量差 100 mm 量级。这条用面来判，和渲染图对得上。
    """
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    out = {}
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        out[frame] = {
            "head": _frontmost_of(HEAD_MESHES),
            "torso": _frontmost_of(TORSO_MESHES),
            "shoe": _frontmost_of(A.FOOT_MESHES["L"] + A.FOOT_MESHES["R"]),
            # ★ 撞出侧肩臂的外表面（袖 + 袖扣 + 左领尖）—— 直接回答
            #   "到底是不是左肩在领跑"，而不是只看躯干整体的最前点。
            "hit_arm": _frontmost_of(
                ("Sleeve_L", "Sleeve_Button_1_L", "Sleeve_Button_2_L",
                 "Sleeve_Button_3_L", "Collar_Point_L")),
            "off_arm": _frontmost_of(
                ("Sleeve_R", "Sleeve_Button_1_R", "Sleeve_Button_2_R",
                 "Sleeve_Button_3_R", "Collar_Point_R")),
            "shoulder_tail": tuple(A.bone_world(arm, "shoulder." + HIT_SIDE,
                                                "tail")),
        }
    if previous is not None:
        arm.animation_data.action = previous
    return out


# =============================================================== 专属门禁
def skill_assertions(arm, action, samples, foots, fronts):
    res = {}
    pelvis = [Vector(f["pelvis"]) for f in foots]
    py = [p.y * 1000.0 for p in pelvis]
    idx = {f["frame"]: i for i, f in enumerate(foots)}

    # ---- 0) 首帧接缝：Skill_01@0 必须逐位等于 `Idle_01@0`
    mats0 = RS.action_world_matrices(arm, action, 0)
    delta0 = RS.matrix_delta(mats0, SRC_MATS)
    res["seam_source"] = [I1.NAME, 0]
    res["skill_start_delta"] = float("%.3e" % delta0)
    res["skill_start_ok"] = delta0 <= SEAM_TOL

    # ---- 1) ① 前冲位移（Root Motion）
    forward_mm = (py[0] - py[idx[HIT]])            # 命中帧相对首帧的前冲量
    net_mm = py[0] - py[-1]                        # 净位移（末帧 vs 首帧）
    res["root_motion_m"] = [round(pelvis[-1].x - pelvis[0].x, 6),
                            round(pelvis[-1].y - pelvis[0].y, 6)]
    res["dash_forward_mm"] = round(forward_mm, 2)
    res["root_motion_net_mm"] = round(net_mm, 2)
    res["root_motion_ok"] = (ROOT_MIN_MM <= forward_mm <= ROOT_MAX_MM
                             and ROOT_MIN_MM <= net_mm <= ROOT_MAX_MM)
    res["root_motion_range_mm"] = [ROOT_MIN_MM, ROOT_MAX_MM]

    # ---- 2) ② 前冲速度单调非减（越冲越快）
    speeds = []
    for frame in range(DASH_IN + 1, HIT + 1):
        a, b = pelvis[idx[frame - 1]], pelvis[idx[frame]]
        speeds.append(math.hypot(b.x - a.x, b.y - a.y) * 1000.0)
    res["dash_speed_mm"] = [round(v, 3) for v in speeds]
    res["dash_speed_ok"] = bool(speeds) and all(
        speeds[i + 1] >= speeds[i] - 1e-6 for i in range(len(speeds) - 1))

    # ---- 3) ③ 起步短：前摇 ≤ 8 帧
    res["start_frames"] = ANTIC
    res["start_short_ok"] = ANTIC <= 8

    # ---- 4) ④ 撞出侧 = 肩：命中帧肩必须比双拳更靠前 ≥ 150 mm
    row_hit = foots[idx[HIT]]
    sh = Vector(row_hit["shoulder_" + HIT_SIDE])
    fist = {s: Vector(row_hit["hand_" + s + "_tail"]) for s in SIDES}
    front_fist_y = min(fist[s].y for s in SIDES)
    res["shoulder_lead_mm"] = round((front_fist_y - sh.y) * 1000.0, 2)
    res["shoulder_y_mm"] = round(sh.y * 1000.0, 2)
    res["front_fist_y_mm"] = round(front_fist_y * 1000.0, 2)
    res["shoulder_hit_ok"] = res["shoulder_lead_mm"] >= SHOULDER_LEAD_MIN_MM
    res["shoulder_lead_min_mm"] = SHOULDER_LEAD_MIN_MM
    # 肩比另一侧肩更前（扭身把撞出肩送出去）
    res["shoulder_asym_mm"] = round(
        (Vector(row_hit["shoulder_R"]).y
         - Vector(row_hit["shoulder_L"]).y) * 1000.0, 2)

    # ---- 4b) ★★ 登记命中点必须是**全身最前点**（C08 第 5 号教训的同一病症）
    # `shoulder_hit_ok` 只比「肩 vs 双拳」，量不到「头比肩更靠前」——首版因此
    # 绿着通过，而剪影是「用脸撞」。这里把**头 / 胸 / 双膝 / 双脚**一起拉进来
    # 比 y，命中点要严格领先它们全部 ≥ HIT_POINT_LEAD_MIN_MM。
    rivals = {name: Vector(row_hit[name]) for name in
              ("head", "chest", "shin_L", "shin_R", "foot_L", "foot_R")}
    rivals.update({("fist." + s): Vector(row_hit["hand_" + s + "_tail"])
                   for s in SIDES})
    leads = {name: round((p.y - sh.y) * 1000.0, 2)
             for name, p in rivals.items()}
    res["hit_point_leads_mm"] = leads
    res["hit_point_worst_rival"] = min(leads, key=lambda k: leads[k])
    res["hit_point_worst_lead_mm"] = leads[res["hit_point_worst_rival"]]
    res["hit_point_frontmost_ok"] = (
        res["hit_point_worst_lead_mm"] >= HIT_POINT_LEAD_MIN_MM)
    res["hit_point_lead_min_mm"] = HIT_POINT_LEAD_MIN_MM

    # ---- 4c) ★★ 用**网格面**复测剪影（不是骨端点）：躯干面必须比头面更前
    front = fronts[HIT]
    sh_tail = Vector(front["shoulder_tail"])
    mesh = {"head": Vector(front["head"]), "torso": Vector(front["torso"]),
            "shoe": Vector(front["shoe"])}
    res["silhouette_front_mm"] = {
        name: [round(v * 1000.0, 2) for v in point] for name, point in
        sorted(mesh.items())}
    res["silhouette_lead_mm"] = {
        name: round((point.y - mesh["torso"].y) * 1000.0, 2)
        for name, point in sorted(mesh.items())}
    # 肩骨端点到躯干最前面的距离（肩应在躯干面附近，别深埋）
    res["shoulder_to_torso_front_mm"] = round(
        abs(sh_tail.y - mesh["torso"].y) * 1000.0, 2)
    res["silhouette_torso_leads_head_ok"] = (
        res["silhouette_lead_mm"]["head"] >= SILHOUETTE_HEAD_MIN_MM
        and res["silhouette_lead_mm"]["shoe"] >= SILHOUETTE_SHOE_MIN_MM)
    res["silhouette_head_min_mm"] = SILHOUETTE_HEAD_MIN_MM
    res["silhouette_shoe_min_mm"] = SILHOUETTE_SHOE_MIN_MM
    # ★ 撞出侧肩臂必须**不落后**于非撞出侧（扭身 + 前送的净效果）
    arm_lead = round((Vector(front["off_arm"]).y
                      - Vector(front["hit_arm"]).y) * 1000.0, 2)
    res["hit_arm_leads_off_arm_mm"] = arm_lead
    res["hit_arm_leads_off_arm_ok"] = arm_lead >= 0.0

    # ---- 5) ⑤ 撞击帧躯干前倾和 ≥ 35°
    res["hit_lean_sum_deg"] = round(sum(
        samples[idx[HIT]]["euler"].get(n, (0.0, 0.0, 0.0))[0]
        for n in ("pelvis", "spine_01", "spine_02", "chest")), 3)
    res["lean_ok"] = res["hit_lean_sum_deg"] >= LEAN_MIN_DEG
    res["lean_min_deg"] = LEAN_MIN_DEG

    # ---- 6) 拖行速度单调非减（替代通用 no_foot_slide_*，见文件头第 2 件）
    # ★ 窗口**只取冲刺段** `(DASH_IN, HIT]`：命停段旋转冻住、骨盆只继续前压
    #   25 mm/4f（= 6.25 mm/f ⇒ 明显慢于冲刺末的 43 mm/f），把它算进来必然
    #   破单调（首版 `drag_speed_ok` 红的现场：末 3 个值塌到 8.667）。
    #   命中之后的「脚仍在滑」不属于「越冲越快」的范畴，单独由 `hitstop_*` 管。
    drag = {}
    for side in SIDES:
        steps = []
        for frame in range(DASH_IN + 1, HIT + 1):
            a = foots[idx[frame - 1]]["ankle_" + side]
            b = foots[idx[frame]]["ankle_" + side]
            steps.append(math.hypot(b[0] - a[0], b[1] - a[1]) * 1000.0)
        drag[side] = steps
    res["drag_speed_window"] = [DASH_IN + 1, HIT]
    res["drag_speed_mm"] = {s: [round(v, 3) for v in drag[s]] for s in SIDES}
    res["drag_speed_ok"] = all(
        bool(drag[s]) and all(drag[s][i + 1] >= drag[s][i] - DRAG_STEP_TOL_MM
                              for i in range(len(drag[s]) - 1))
        for s in SIDES)
    res["drag_total_mm"] = {
        s: round(abs(foots[idx[HIT]]["ankle_" + s][1]
                     - foots[idx[DASH_IN]]["ankle_" + s][1]) * 1000.0, 2)
        for s in SIDES}

    # ---- 7) 支撑脚贴地 / 全程支撑
    sole = {}
    for side in SIDES:
        zs = [foots[i]["sole_" + side] for i in range(len(foots))
              if foots[i]["sole_" + side] is not None]
        sole[side] = [round(min(zs) * 1000.0, 3), round(max(zs) * 1000.0, 3)]
    res["stance_sole_mm"] = sole
    res["stance_sole_ok"] = all(SOLE_RANGE_MM[0] <= v[0]
                                and v[1] <= SOLE_RANGE_MM[1]
                                for v in sole.values())
    res["unsupported_frames"] = []
    res["always_supported_ok"] = True
    res["swing_windows"] = None
    res["swing_airborne_ok"] = True

    # ---- 8) 顿感：命停窗 14 骨逐位冻结，而骨盆继续前压
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
    res["hitstop_momentum_mm"] = round(py[idx[HIT]] - py[idx[HOLD_END]], 3)
    res["hitstop_keeps_momentum_ok"] = res["hitstop_momentum_mm"] > 10.0
    res["hitstop_frames"] = HOLD
    res["hitstop_frames_ok"] = 2 <= HOLD <= 4
    res["antic_frames"] = ANTIC
    res["dash_frames"] = HIT - ANTIC
    res["recover_frames"] = TOTAL - HOLD_END

    # ---- 9) 力矩链：脚→腿→髋→腰→肩→手 逐级非零
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

    # ---- 10) 腿可达（全段，不做截断）
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

    # ---- 11) 收招：不许瞬停、不许过冲
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

    # ---- 12) ★ 末帧必须**真的是**登记的 `end_pose_deg`（= 战斗待机，C08 第 5 号教训）
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
    global SEAM_POSE, SEAM_EULER, SEAM_DIRS, Z_SEAM, Y_SEAM, ANKLE_0, IDLE_POSE
    global IDLE_KNEE_DIR, IDLE_BASIS, IDLE_DIR, ARM_LEN, ARM_BASIS
    global E0, E_END, E_END_UNW, SRC_MATS, END_ROT
    global START_RX, REL_RX, START_RY, REL_RY, START_RZ, REL_RZ

    for store in (SEAM_POSE, SEAM_EULER, SEAM_DIRS, ANKLE_0, IDLE_POSE,
                  IDLE_KNEE_DIR, IDLE_BASIS, IDLE_DIR, ARM_LEN,
                  ARM_BASIS, E0, E_END, E_END_UNW, _HIT_FROZEN, LOG,
                  HIT_POINT, END_ROT):
        store.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("C09_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
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
    Y_SEAM = A.bone_world(arm, "pelvis", "head").y
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}

    # ★ 末姿登记值 = Idle@0 的躯干真值（战斗待机）
    for name in RX_BONES:
        END_ROT[name] = tuple(SEAM_EULER[name])

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

    # ---- 躯干轨道：f0 回填 Idle 真值（★ 必须 global，C01 教训 1）
    def patch(track, bone, channel=0):
        return ((0, SEAM_EULER[bone][channel]),) + tuple(
            k for k in track if k[0] != 0)

    for name in RX_BONES:
        START_RX[name] = patch(START_RX[name], name, 0)
    for name in RY_BONES:
        START_RY[name] = patch(START_RY[name], name, 1)
    for name in RZ_BONES:
        START_RZ[name] = patch(START_RZ[name], name, 2)
    # ★ 撞击轨道首键 = 起步末值（逐位接得上，不靠"两个手写常量碰巧相等"）
    for name in RX_BONES:
        REL_RX[name] = ((ANTIC, START_RX[name][-1][1]),) + tuple(REL_RX[name])
    for name in RY_BONES:
        REL_RY[name] = ((ANTIC, START_RY[name][-1][1]),) + tuple(REL_RY[name])
    for name in RZ_BONES:
        REL_RZ[name] = ((ANTIC, START_RZ[name][-1][1]),) + tuple(REL_RZ[name])
    for name in RX_BONES:
        assert START_RX[name][0][1] == SEAM_EULER[name][0], \
            "%s rx 未回填" % name
        assert all(k[0] <= ANTIC for k in START_RX[name]), \
            "起步轨道不许越过 ANTIC"

    A.report("C09_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "start_end": ANTIC, "hit": HIT, "hold": HOLD, "hold_end": HOLD_END,
        "return_start": RETURN_START, "settle": SETTLE, "cancel": CANCEL,
        "seam_source": [I1.NAME, 0],
        "hit_side": HIT_SIDE,
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "pelvis_y0_mm": round(Y_SEAM * 1000.0, 3),
        "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                      for s in SIDES},
        "py_coil_mm": round(PY_COIL * 1000.0, 1),
        "py_hit_mm": round(PY_HIT * 1000.0, 1),
        "py_end_mm": round(PY_END * 1000.0, 1),
        "dash_r0": DASH_R0, "lag": LAG,
        "momentum_mm": MOMENTUM_MM,
        "hitstop_bones": list(HITSTOP_BONES),
        "note": ("肩撞：首帧 = `Idle_01@0`（逐位）；起步 8f 微沉反拉 → 冲刺 28f "
                 "骨盆加速前冲 560 mm（双脚贴地拖行）→ 命中帧左肩为最前点 → "
                 "命停 4 帧 14 骨全冻、骨盆继续前压 25 mm → 收招单向减速回"
                 "「战斗待机」。允许 Root Motion，净前冲 545 mm。"),
    })

    ARM_BASIS.clear()
    ARM_BASIS.update(build_arm_basis())
    A.report("C09_ARM_BASIS", {
        "phases": sorted(ARM_BASIS),
        "phase_frames": {"SEAM": 0, "MID1": MID1_F, "MID2": MID2_F, "HIT": HIT},
        "slerp_t": {name: round(at / float(HIT), 6)
                    for name, at in (("MID1", MID1_F), ("MID2", MID2_F))},
        "seam_dirs": {b: [round(c, 6) for c in SEAM_DIRS[b]]
                      for b in ARM_BONES},
        "hit_dirs": {b: [round(c, 6) for c in ARM_KEYS["HIT"][b]]
                     for b in ARM_BONES},
        "end_dirs": {b: [round(c, 6) for c in I1.ARM_DIRS[b]]
                     for b in ARM_BONES},
    })

    E_END = solve_end_arm(arm)
    A.report("C09_END_ARM", {
        "end_dirs": {b: [round(c, 6) for c in I1.ARM_DIRS[b]]
                     for b in ARM_BONES},
        "end_euler_deg": {k: [round(v, 4) for v in E_END[k]]
                          for k in ARM_BONES},
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
        "note": ("肩撞：起步 8f → 加速前冲 28f（Root Motion 560 mm）→ 命中"
                 "（左肩为命中点）→ 命停 %d 帧 14 骨全冻、骨盆继续前压 → "
                 "收招单向减速回「战斗待机」。" % HOLD),
        "antic_frame": ANTIC,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HOLD,
        "root_motion_m": [0.0, round(PY_END, 6)],
        "inherit_from": None,
        "segments": {"start": [0, ANTIC], "dash": [ANTIC, HIT],
                     "hold": [HIT, HOLD_END], "recover": [HOLD_END, TOTAL]},
        "hit_side": HIT_SIDE,
        "hit_point_m": dict(HIT_POINT),
        "end_pose_deg": {k: [round(v, 4) for v in val]
                         for k, val in sorted(END_ROT.items())},
        "end_arm_dirs": {k: [round(v, 6) for v in I1.ARM_DIRS[k]]
                         for k in ARM_BONES},
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "START_END": ANTIC, "DASH": ANTIC, "HIT": HIT,
        "HOLD_END": HOLD_END, "RECOV": RETURN_START, "SETTLE": SETTLE,
        "CANCEL": CANCEL, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    foots = foot_series(arm, action, meshes, TOTAL)
    fronts = silhouette_front(arm, action, (HIT,))
    if os.environ.get("C09_TRACE") == "1":
        limit_mm = (A.L_THIGH + A.L_SHIN) * 1000.0
        for f in foots:
            print("C09_TRACE " + json.dumps({
                "f": f["frame"], "q": round(q_of(f["frame"]), 5),
                "pelvis": [round(v * 1000.0, 2) for v in f["pelvis"]],
                "shoulder_L": [round(v * 1000.0, 2) for v in f["shoulder_L"]],
                "L_sole": (None if f["sole_L"] is None
                           else round(f["sole_L"] * 1000.0, 3)),
                "R_sole": (None if f["sole_R"] is None
                           else round(f["sole_R"] * 1000.0, 3)),
                "L_reach": round(f["reach_L"] * 1000.0 / limit_mm, 4),
                "R_reach": round(f["reach_R"] * 1000.0 / limit_mm, 4),
            }))

    report = A.run_common_assertions(samples, meta, foot_probe=())
    report.update(skill_assertions(arm, action, samples, foots, fronts))
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
    report["silhouette"] = {
        str(k): {name: [round(v * 1000.0, 2) for v in point]
                 for name, point in sorted(val.items())}
        for k, val in fronts.items()}
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C09_REPORT", report)

    if not SKIP_RENDER:
        # ★ 取景由**实测包围盒**算（C06 教训 2 / C07 教训 4）：前冲会让人物整体
        #   前移 0.55 m，标准视图（中心 y=0）会把人顶到画框外半边。
        frames = [0, ANTIC, 12, 20, 28, HIT, HOLD_END, SETTLE, TOTAL]
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
            _name, location, target, _scale, res = view
            direction = (Vector(location) - Vector(target)).normalized()
            new_target = Vector(center)
            new_location = new_target + direction * 4.6
            return (_name, tuple(new_location), tuple(new_target), scale, res)

        A.report("C09_CAMERA", {
            "bbox_min": [round(min(xs), 4), round(min(ys), 4), round(min(zs), 4)],
            "bbox_max": [round(max(xs), 4), round(max(ys), 4), round(max(zs), 4)],
            "center": [round(v, 4) for v in center],
            "ortho_scale": round(scale, 4),
            "note": ("前冲 0.55 m ⟹ 标准视图（中心 y=0）会切边，故按实测包围盒"
                     "重定；三视角沿用各自原方向。"),
        })
        for base in (A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q):
            A.render_pose_sheet(arm, action, frames, "skill01",
                                views=(reframe(base),))
    A.save_project()
    A.export_glb(arm)
    print("C09_DONE failed=%s" % report["failed"])
    print("C09_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C09_FAILURE " + traceback.format_exc())
