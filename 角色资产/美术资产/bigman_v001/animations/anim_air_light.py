"""anim_air_light —— B08 `Air_Light` 空中攻击（前手直拳 + 后腿膝撞）。

定位（清单原文 B08）：「快速向前拳击 / 膝撞，**动作不能破坏角色空中整体重心**」。

---------------------------------------------------------------------------
★ 断点范式：**A 族空中接缝**（与 B04~B07 的「末帧停在自持姿态」不同）

B08 在**空中**播：上游 `Jump_Fall`（A12）、下游仍回到下落或接 `Jump_Land`（A13）。
⟹ **首帧逐位 = `Jump_Fall@0`**（世界矩阵 max_delta = 0）。
引擎可以在下落的任意时刻插入、插完直接接回下落，接缝零跳变。

「不破坏空中整体重心」于是有了可判定的形式：
  ① 骨盆 z 必须仍是 A12 的**同一条弹道函数**（`JFE.pelvis_z`，与 A10/A11/A12
     共用 `JS.TAKEOFF_PELVIS_Z / TAKEOFF_SPEED / G_PER_FRAME`）——
     **不许借骨盆改高度去换幅度**（这是与 B07「允许且必须上升 135 mm」的关键区分）；
  ② 骨盆水平漂移 ≤ 60 mm（蹬地类必须 0；空中必有反冲，60 mm 是「看得出但不成漂移」）；
  ③ 出拳的反作用由**躯干反向扭转 + 对侧臂后摆 + 支撑腿后蹬**吃掉，不顶到骨盆。

---------------------------------------------------------------------------
★★ 第 1 件 —— 末帧的「逐位回接缝」**不能**拿 4×4 世界矩阵去比（本支的口径修正）

计划原文写「首帧与末帧都逐位 = `Jump_Fall@0`（世界矩阵 max_delta = 0）」。首帧成立。
**末帧拿 4×4 比是不成立的，也不该成立**：末帧在 f27，骨盆已沿弹道又落了 **951.9 mm**。

    骨盆 z(f0) = 1952.89 mm  →  z(f27) = 1001.0 mm

27 帧自由落体必须落这么多，否则角色在半空"悬停"——那才是真的破坏重心。
直接比 4×4 量到的是那个落差（951.9 mm），不是姿态差 —— **尺子错了**。

修法（同 B05/B06/B07 的「换对窗口/换对尺子」）：末帧判据改成**平移不变**比对 ——
「每根骨的 3×3 朝向 + (骨位置 − 骨盆位置)」逐位一致。**容差仍是 1e-6，没有放宽一字**；
另把原始 4×4 差值登记为诊断量 `seam_end_raw_delta_mm`（应 ≈ 落距 951.9 mm）。

★★ 尺子还差**第二块补丁**（首版实测才暴露）：平移不变**只对会动的那部分骨架成立**。
全世界只有 `pelvis` 带 `@loc` ⟹ 只有它和它的**后代**随弹道平移；
`root`（pelvis 的父骨）**原地不动**，于是它的「相对骨盆位置」必然随落差变化 ——
首版报出的 `seam_end_relpos_delta_mm = 951.889`、`seam_end_relpos_bone = "root"`，
**正好是落距本身**。而 `seam_end_orient_delta = 0.0` ⟹ 姿态其实**逐位回得去**。
改法：**后代骨比「相对骨盆」，非后代骨比「世界绝对」**（`pelvis_moving()`）。
★ 操守：判据红了先怀疑尺子；**尺子错的时候，修尺子不是放宽容差** ——
但必须同时把"合数"拆成「朝向 / 相对位置 / 哪根骨」，否则分不清是尺子错还是姿态错
（B07 诊断教训同款：只报一边会埋红点）。

---------------------------------------------------------------------------
★★ 第 2 件 —— 命中停顿冻结的是**关节**，不是时间；骨盆必须继续落

§6 要求命中帧做 2~4 帧「完全停顿」。但本支的弹道门禁要求骨盆 z 逐帧贴合 A12 弹道。
两条同时满足只有一个解：**冻结全身关节角，骨盆照常落**。

f16→f18 三帧的自由落体是 **89.6 mm**。若连骨盆一起冻住，`air_ballistic_ok`
立刻红 89.6 mm（阈值 2 mm）；若连关节一起放，就没有"顿感"了。
`hitstop_frozen_steps` 量的是**欧拉角通道**（姿态），不含 `location`
⟹ 关节冻结 + 骨盆继续落 = 顿感与弹道同时成立。

同理，命中窗口复用姿态时，**踝目标的派生量必须跟着同一个 clock**（B06 第 1 件）：
锁存的是「踝相对髋」的偏移，不是世界绝对坐标 —— 骨盆每帧落一点，
髋跟着落，靶子跟着落，IK 解算逐位复现。

---------------------------------------------------------------------------
★★ 第 3 件 —— 收招必须落到**接缝姿态**上，且必须一路**欧拉连续**地落上去

「收招不能瞬停」（§6）与「末帧逐位回接缝」同时要满足，做法同 B06/B07 的收招平台：
f25 起把姿态**锁存**成 `Jump_Fall@0` 的克隆，f25/f26/f27 逐位相同 ⟹ 末段步长恒为 0。
`decel_smooth_ok` 要求末段增量单调收敛，**尾部的一串 0 是合法的**（0 ≤ 前一项）。

★ 但首版这里踩了一个坑，值得写下来：
首版收招**仍走 IK 解算**（拳/踝目标线性插值回 A0），只有到底才换成接缝克隆。
实测 f20→f21 的 `hand.L` **单帧 55.4°**（`no_teleport` 红），
末帧姿态差也正好 ≈ 落距 —— 因为**拳峰到位 ≠ 手骨滚转到位**：
`aim_carry_stable` 的 roll 搜索是逐帧独立的偏好，它根本不保证收敛到
`Jump_Fall@0` 当时那一个 roll。到最后一帧硬切克隆 = 把整个 roll 差一次性吃掉。

**修法：收招段不做 IK，直接在欧拉空间线性插值到接缝克隆。**
理由很硬 —— 收招的目标是一个**已知的固定姿态**，没有需要解算的东西：
  · 端点由构造逐位等于接缝 ⟹ 世界朝向逐位回得去；
  · 逐分量插值天然连续，roll 差被摊到每一帧，不集中在最后一帧；
  · `_euler_mix` 的 `s≥1` 直接取克隆（不走 `a+(b−a)·1` 的浮点路径）。
代价：收招段不再有 IK 靶点 ⟹ `ik_reach_ok` 的口径只覆盖 `[1, HOLD_END]` 的 IK 帧，
收招段改由「回接缝的收敛性」把关（`decel_smooth_ok` + `return_tail`）。
★ **这是换对尺子，不是放宽容差。**
实测修完 f17→f18 的释放步 **12.34°**（原来是 55.4°），且逐帧单调收敛到 0。

收招用的缓出是 `s = 1 − (1−u)^1.40`（速度单调递减到 0）。
指数定 1.40 的依据是**单帧步长预算**：`1−(1−u)^p` 的首帧速度 ∝ p，
首帧要吃掉全程的 `1−(1−1/7)^p`；收招要倒着走完整个"出拳 + 蓄力"的欧拉行程 D，
所以要求 `D · [1−(6/7)^p] ≤ 25°`（`no_teleport` 天花板，**一字未动**）。
p = 1.40 ⟹ 首帧 19.4% ⟹ D ≤ 129°；p = 2.00 时首帧 30.6% ⟹ D ≤ 82°，太紧。
**降幂次是改运动曲线，不是放宽容差**（同 B07 第 4 件）。

★★ 命中段长度（7 → **9 帧**）是**量出来的，不是拍的**：
首版 7 帧 + `BURST_POW 1.35` 时，末帧仍是 **27.4° @ f15 `forearm.L`**。
根因不是幂律，是**收拳入怀 → 直拳轰出**让前臂方向**近乎反折 180°**
（折叠时腕在肩上、展开时腕在身前）⟹ `aim_carry` 的平行输运**累积扭转**：
`forearm.L` 的 ry 走 −46° → +47°（共 99°），而**扭转速率对 s 是超线性的**
（实测 d(ry)/ds 由 53°/单位 涨到 144°/单位）。所以只降 `BURST_POW` 不够 ——
把命中段拉到 **9 帧**后末帧 Δs 由 0.1878 降到 0.1470，预估末帧 ≈ 21°。
`ROLL_W` 从 B07 的 0.60 提到 **1.20** —— 首版另一个红点是
`forearm.L` 的 roll 在 4°↔22° 之间"改主意"（B07 第 1 件同病）。
**这是改运动曲线 / 改求解偏好，不是改判据。**

---------------------------------------------------------------------------
★ 探针 `probe_air08.py` 实测（先量再做）定下的四个数

| 量 | 实测 | 用法 |
|---|---|---|
| `Jump_Fall@0` 骨盆 z | **1952.89 mm** | 弹道起点 |
| 髋−踝竖距 (L/R) | 640.0 / 618.0 mm | 接缝腿姿态的基准 |
| guard 拳−肩 (L) | (123.0, **−455.4**, 161.9)，长 **498.7** | 出拳起点 |
| 臂几何 | 上臂+前臂 **552.0**、折叠下界 **176.6**、含手 **650.0** | 拳轨的可行环带 |
| 提膝扫描 | 踝相对髋 (−300, −412) ⟹ 膝前送 **409.7**、膝离髋 **14.9**（原 365.1） | 膝撞目标 |

★ 提膝那一格是本支最有用的一行：`Jump_Fall@0` 时膝在髋下 **365.1 mm**；
把 R 踝收到「髋下 412 / 髋前 320」时**大腿抬到接近水平**（大腿水平 + 小腿下垂
= 标准膝撞造型），膝相对骨盆**上升 350 mm**，而 |髋−踝| 只有 522.5 mm
⟹ 腿长余量还剩 **299.5 mm**（B07 攻击腿只剩 7.7 mm）。**先量过，所以敢给到髋高。**

---------------------------------------------------------------------------
★ 本支的五条关键做法

1. **参照系跟躯干走**（B07 教训 1）：拳峰目标 = **肩的世界坐标 + 相对向量**；
   踝目标 = **髋的世界坐标 + 相对关节量**。躯干在空中会滚转 + 前倾，
   用世界绝对量的话肘会在「折叠芯」和「极限球面」两头撞。
2. **手骨指向 = 拳峰相对肩向量的方向**（`normalize(rel)`）。
   这样腕到肩的距离恒为 `|rel| − hand_len` 落在 **[176.6, 551.7]** 内：
   chamber 0.287−0.098 = **189 mm**、命中 0.618−0.098 = **520 mm**
   ⟹ `arm_to` 的夹取**全程不触发**（夹取只是安全网，不是设计）。
3. **击出用幂律 `u^1.35`**（`p > 1` ⟹ 速度单调升 ⟹ 峰值帧 ≡ HIT）。
   前摇用 `_ease_ramp`（两端速度 0）；收招用 `1−(1−u)^1.40`（速度单调降）。
   ★ `p > 1` 只保证"峰在末帧"，**不保证末帧步长 ≤25°** —— 那要靠**帧数**买
   （见文件头第 3 件：命中段 7 → 9 帧）。
4. **`strike_forward_ok` 量「前摇顶点 → 命中帧」的行程**，不是「f0 → 命中帧」：
   f0 是接缝，guard 拳本来就在肩前 455 mm（A12 f0 的手臂是"伸开找平衡"的姿态），
   臂几何上界只有 552 mm ⟹ 从 f0 出发最多再前移 **97 mm**，**物理上不可能**到 300。
   先「收拳入怀」（−265）再「直拳轰出」（−615）⟹ 行程 **350 mm**。
5. **`ground_contact_ok` / `no_foot_slide` 全段离地 ⟹ 记 None** 并登记理由
   （A11/A12 口径：None = "不适用"，不是"通过"）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_air_light.py
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
import anim_walk_f as WF      # noqa: E402
import anim_turn as TURN      # noqa: E402
import anim_crouch as CR      # noqa: E402
import anim_jump_start as JS  # noqa: E402
import anim_jump_up as JU     # noqa: E402
import anim_jump_fall as JFE  # noqa: E402
import anim_uppercut as UP    # noqa: E402

NAME = "Air_Light"
TOTAL = 27                    # 0.450 s @60fps（帧数按单帧步长预算给，见文件头第 3 件）
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

CHAMBER_END = 7               # 前摇：收拳入怀 + 提膝预备
BURST_START = 7
HIT = 16                      # 命中帧（命中段 **9 帧**，见文件头第 3 件）
HOLD_END = 18                 # f16~f18 = **3 帧关节冻结**（骨盆照常落）
RETURN_START = 18
RETURN_END = 25               # 收招平台起点：f25~f27 逐位 = 接缝姿态克隆
CANCEL = 21                   # 可取消帧（回接缝途中）
BURST_POW = 1.35              # 起缓收快（p > 1 ⟹ 速度峰 ≡ HIT）
RETURN_POW = 1.40             # 收招缓出（首帧速度 ∝ p，见文件头第 3 件）
ROLL_W = 1.20                 # roll 连续性权重（B07 = 0.60；见文件头第 3 件）

SIDES = ("L", "R")
PUNCH = "L"                   # 前手（A01：FRONT_ANKLE_Y < 0 ⟹ 左脚在前）直拳
KNEE = "R"                    # 后腿（R）膝撞
COUNTER = "R"                 # 对侧臂 = 后手，向后摆做配重

ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")
LEG6 = ("thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R")
TRUNK8 = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
          "shoulder.L", "shoulder.R")
# ★ 库里 `PROBE_BONES` 不含 thigh / shin（长期坑，B06 已记），本进程内并入。
PROBE_EXTRA = ("thigh.L", "thigh.R", "shin.L", "shin.R")

# 弹道：与 A12 **同一函数**（不重算，直接借用；B08 插在 A12 的 f0 上）
pelvis_z = JFE.pelvis_z
G_PER_FRAME = JFE.G_PER_FRAME

# ---------------------------------------------------------------- 门禁阈值
AIR_DRIFT_MAX_MM = 60.0        # 骨盆水平漂移（探针定案：空中反冲的「看得见但不漂」量级）
AIR_BALLISTIC_TOL_MM = 2.0     # 骨盆 z 对 A12 弹道的误差（同 A12 的 fall_ballistic_ok）
STRIKE_FORWARD_MIN_MM = 300.0  # 拳峰世界 −y 行程（前摇顶点 → 命中帧）
STRIKE_ARC_MIN_MM = 400.0      # 拳峰弧长（"动作幅度要大"，§6）
KNEE_RISE_MIN_MM = 150.0       # `shin.R` head 相对骨盆高度的上升
COUNTER_BALANCE_RANGE = (0.25, 0.60)   # 对侧臂后摆 / 出拳行程（**给区间**，单边等于没定）
NO_TELEPORT_MAX_DEG = 25.0
AIRBORNE_MIN_CLEARANCE_MM = 0.0        # 只需"真的离地"（>0），见 `airborne_ruler_note`
LEG_DROP_OVER_SEAM_MM = 80.0           # 腿比**接缝姿态**最多多伸多少（姿态口径，与帧数无关）

# ---------------------------------------------------------------- 肘/膝鼓出方向
# 直拳造型：肘一路留在**拳下方略外**（上勾的肘在下方，直拳的肘也是下方略外）。
POLE_ARM_AH = {"L": (0.34, 0.10, -0.94), "R": (-0.34, 0.10, -0.94)}
# 膝：L 支撑腿继续向前鼓（同 A12 的 (0,−1)），R 提膝向前鼓。
POLE_LEG_AH = {"L": (0.16, -1.0, 0.0), "R": (-0.16, -1.0, 0.0)}

# ---------------------------------------------------------------- 足尖（度，正 = 压脚背）
TIP_A0 = 8.0                   # = A11/A12 的 `JU.TIP_KEYS[-1][1]`（不硬编码：A12 末值同源）
TIP_AC = {"L": 6.0, "R": 20.0}
TIP_AH = {"L": 4.0, "R": 30.0}   # 提膝腿的脚背放松下垂

STATE = {}                     # A0（接缝）/ AC（前摇顶）/ AH（命中）
HAND0 = {}                     # side -> 接缝姿态下的手骨世界指向
POLE_LEG_A0 = {}               # side -> 接缝姿态下实测的膝鼓出方向
POLE_ARM_A0 = {}               # side -> 接缝姿态下实测的肘鼓出方向
HIP0 = {}                      # side -> 接缝姿态下的髋位
START_POSE = {}
START_QUATS = {}
START_MATS = None
LOCK = {}                      # key -> pose：命中窗口与收招平台**逐位复用同一姿态**
LOCK_PY = {}                   # key -> 该姿态的骨盆水平位移（米）
LOCK_ANK = {}                  # key -> {side: 踝相对髋偏移}（派生量跟着同一个 clock）
TARGETS = []                   # [(frame, side, 世界目标)]：腿 IK 到位核验
ARMTGT = []                    # [(frame, side, 世界拳峰目标)]
TRACE = []


# =============================================================== 阶段时钟
def stage_of(frame):
    """返回 (段名, 插值参数 s)。"""
    if frame <= 0:
        return ("seam", 0.0)
    if frame <= CHAMBER_END:
        return ("chamber", JS._ease_ramp(frame / float(CHAMBER_END)))
    if frame <= HIT:
        u = (frame - BURST_START) / float(HIT - BURST_START)
        return ("strike", u ** BURST_POW)
    if frame <= HOLD_END:
        return ("hold", 1.0)
    u = min(1.0, (frame - RETURN_START) / float(RETURN_END - RETURN_START))
    # ★ 收招缓出：速度单调递减到 0（梯形剖面做不到 —— 两端速度为 0 不等于会收敛）
    return ("return", 1.0 - (1.0 - u) ** RETURN_POW)


def lerp_state(frame):
    kind, s = stage_of(frame)
    if kind == "seam":
        return kind, 0.0, STATE["A0"], STATE["A0"]
    if kind == "chamber":
        return kind, s, STATE["A0"], STATE["AC"]
    if kind == "strike":
        return kind, s, STATE["AC"], STATE["AH"]
    if kind == "hold":
        return kind, 1.0, STATE["AH"], STATE["AH"]
    return kind, s, STATE["AH"], STATE["A0"]


def _clone(pose):
    return {k: (dict(v) if k == "@loc" else tuple(v)) for k, v in pose.items()}


def _a0_clone():
    """接缝姿态的克隆：欧拉折算到「离上一帧最近」的等价分支（世界朝向逐位不变）。

    ★ 为什么必须折算：直接抄 `Jump_Fall@0` 的 euler 可能落在另一个等价分支上
    （例如 ±180 翻转），世界姿态一样、但欧拉通道差 360° ⟹ 末段步长爆炸。
    """
    pose = _clone(START_POSE)
    for name in list(pose):
        if name.startswith("@"):
            continue
        pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name), pose[name])
    return pose


# =============================================================== 腿 IK（带 roll 连续性）
def leg_aim_stable(arm, pose, side, target, pole, frame):
    """`UP.leg_aim` 的 roll 连续性版：把两次 `JS.aim_carry` 换成 `aim_carry_stable`。

    B07 只在**臂**上加了 roll 连续性惩罚；本支的 R 腿要从 27° 抬到近 90°，
    同一个「逐帧改主意」的病会落在腿上（`aim_carry` 的代价函数只看当前骨），
    所以这里给腿也用同一把尺子。
    """
    thigh_len, shin_len = A.L_THIGH, A.L_SHIN
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    target = Vector(target)
    delta = target - hip
    raw = delta.length
    limit = (thigh_len + shin_len) * 0.9995
    distance = max(1e-4, min(raw, limit))
    UP.REACH.append((side, raw / (thigh_len + shin_len)))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    bulge, sin_pole = UP._bulge(side, axis, pole)
    cos_hip = (thigh_len ** 2 + distance ** 2 - shin_len ** 2) \
        / (2.0 * thigh_len * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    knee = hip + (axis * cos_hip + bulge * sin_hip) * thigh_len
    pose["thigh." + side] = UP.aim_carry_stable(arm, "thigh." + side, knee - hip)
    pose["shin." + side] = UP.aim_carry_stable(arm, "shin." + side, target - knee)
    UP.POLE_SIN.append((frame, side, sin_pole))
    return sin_pole


# =============================================================== 姿态生成
def _euler_mix(pose_a, pose_b, t):
    """欧拉空间**逐分量**插值（收招专用）。`t >= 1` 直接取 `pose_b`（逐位，不走浮点路径）。

    为什么不复用 `A.blend`：`a + (b−a)·1.0` 在浮点下不保证逐位等于 `b`，
    而收招的终点必须**逐位**等于接缝克隆（`air_seam_end_ok` 容差 1e-6）。
    """
    if t >= 1.0:
        return _clone(pose_b)
    out = {}
    for key in set(pose_a) | set(pose_b):
        if key.startswith("@"):
            continue
        va = pose_a.get(key, (0.0, 0.0, 0.0))
        vb = pose_b.get(key, (0.0, 0.0, 0.0))
        out[key] = tuple(a + (b - a) * t for a, b in zip(va, vb))
    return out


def build_pose(arm, frame, record=False):
    """按帧构造完整姿态。

    三类执行：
      ① 命中窗口 f15~f17：复用 f15 解出的**关节姿态**；骨盆 loc 每帧仍按弹道
         （见文件头第 2 件：顿的是关节，不是时间）。
      ② 收招段 f18~f23：**欧拉空间逐分量插值** AH → 接缝克隆（不做 IK）。
      ③ 收招平台 f24~f26：复用「接缝姿态克隆」；骨盆 loc 每帧仍按弹道。
    """
    lock_key = HIT if HIT <= frame <= HOLD_END \
        else (TOTAL if frame >= RETURN_END else None)

    if lock_key is not None and lock_key in LOCK:
        pose = _clone(LOCK[lock_key])
        pose["@loc"]["pelvis"] = A.wloc(0.0, LOCK_PY[lock_key],
                                        pelvis_z(frame) - 0.900)
        A.apply_pose(arm, pose)
        if record:
            for side in SIDES:
                target = (Vector(A.bone_world(arm, "thigh." + side, "head"))
                          + Vector(LOCK_ANK[lock_key][side]))
                TARGETS.append((frame, side, tuple(target)))
        _record(arm, frame, pose)
        return pose

    kind, s, sa, sb = lerp_state(frame)

    if kind == "return":
        # ★★ 收招**不做 IK**：直接在欧拉空间插值到接缝克隆（文件头第 3 件）。
        #   目标是一个**已知的固定姿态** ⟹ 没有需要解算的东西：
        #     · 端点由构造逐位等于接缝（s>=1 直接取克隆）⟹ 世界朝向逐位回得去；
        #     · 逐分量插值天然连续，roll 差被摊到每一帧，不集中在最后一帧；
        #     · 首版走 IK（`aim_carry_stable` 的 roll 搜索逐帧独立）⟹ 最后一帧
        #       硬切克隆，把整个 roll 差（实测 `hand.L` **55.4°**）一次性吃掉。
        #   代价：收招段无 IK 靶点 ⟹ `ik_reach_ok` 口径只覆盖 `[1, HOLD_END]`。
        #   ★ 这是**换对尺子**，不是放宽容差。
        pose = _euler_mix(LOCK[HIT], LOCK[TOTAL], s)
        py = sa["pelvis_y"] + (sb["pelvis_y"] - sa["pelvis_y"]) * s
        pose["@loc"] = {"pelvis": A.wloc(0.0, py, pelvis_z(frame) - 0.900)}
        A.apply_pose(arm, pose)
        _record(arm, frame, pose)
        return pose
    trunk = A.blend(sa["trunk"], sb["trunk"], s)
    rel = {k: sa["rel"][k].lerp(sb["rel"][k], s) for k in SIDES}
    hand = {k: JS._slerp(sa["hand"][k], sb["hand"][k], s) for k in SIDES}
    ankle = {k: sa["ankle"][k].lerp(sb["ankle"][k], s) for k in SIDES}
    tip = {k: sa["tip"][k] + (sb["tip"][k] - sa["tip"][k]) * s for k in SIDES}
    pole_arm = {k: _lerp3(sa["pole_arm"][k], sb["pole_arm"][k], s) for k in SIDES}
    pole_leg = {k: _lerp3(sa["pole_leg"][k], sb["pole_leg"][k], s) for k in SIDES}
    py = sa["pelvis_y"] + (sb["pelvis_y"] - sa["pelvis_y"]) * s

    pose = dict(trunk)
    pose["toe.L"] = (0.0, 0.0, 0.0)
    pose["toe.R"] = (0.0, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(0.0, py, pelvis_z(frame) - 0.900)}
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    for side in SIDES:
        target = Vector(A.bone_world(arm, "thigh." + side, "head")) + ankle[side]
        if record:
            TARGETS.append((frame, side, tuple(target)))
        leg_aim_stable(arm, pose, side, target, pole_leg[side], frame)

    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        WF.add_world_rx(arm, name, tip[side])
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v) for v in arm.pose.bones[name].rotation_euler))

    req_mark = len(UP.REQ)
    for side in SIDES:
        fist = Vector(A.bone_world(arm, "upperarm." + side, "head")) + rel[side]
        if record:
            ARMTGT.append((frame, side, tuple(fist)))
        UP.arm_to(arm, pose, side, fist, hand[side], pole_arm[side])
    # ★ `UP.arm_to` 记的是 3 元组（side, req, used）；补上帧号才能定位红点（B07 写法）。
    for index in range(req_mark, len(UP.REQ)):
        UP.REQ[index] = (frame,) + UP.REQ[index]

    _record(arm, frame, pose)
    if lock_key == HIT and HIT not in LOCK:
        LOCK[HIT] = _clone(pose)
        LOCK_PY[HIT] = py
        LOCK_ANK[HIT] = {s: tuple(ankle[s]) for s in SIDES}
        # ★ 接缝克隆**就在此刻**构造：`_PREV_EULER` 刚被 `_record` 写成命中姿态，
        #   于是 `_unwrap_xyz` 把 `Jump_Fall@0` 的欧拉折到**离命中姿态最近的那一支**
        #   ⟹ 收招的欧拉行程最短、逐分量插值不会绕远路。
        LOCK[TOTAL] = _a0_clone()
        LOCK_PY[TOTAL] = 0.0
        LOCK_ANK[TOTAL] = {s: tuple(STATE["A0"]["ankle"][s]) for s in SIDES}
    return pose


def _lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def _record(arm, frame, pose):
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    TRACE.append({
        "frame": frame,
        "euler": {b: tuple(round(v, 2) for v in pose.get(b, (0.0, 0.0, 0.0)))
                  for b in ARM6 + LEG6},
        "roll": {b: round(JS.ARM_ROLL.get(b, 0.0), 1) for b in ARM6 + LEG6},
    })


# =============================================================== 状态表
def _trunk(start):
    """三张躯干表：A0 = 接缝原值；AC = 前摇（反向扭转蓄力）；AH = 命中。"""
    def g(bone):
        return start.get(bone, (0.0, 0.0, 0.0))[0]

    a0 = {bone: tuple(start.get(bone, (0.0, 0.0, 0.0))) for bone in TRUNK8}
    # ★ 躯干扭转（ry）的符号：骨轴 ≈ 世界 +Z，右手定则下 **ry > 0 把左侧转向身后**。
    #   所以「左肩前送出拳」要 **ry < 0**；前摇反向蓄力用 ry > 0。
    ac = {
        "pelvis": (g("pelvis") + 1.6, 0.0, 0.0),
        "spine_01": (g("spine_01") + 1.0, 4.0, 0.0),
        "spine_02": (g("spine_02") + 0.9, 4.0, 0.0),
        "chest": (g("chest") + 1.2, 6.0, 0.0),
        "neck": (g("neck") - 0.6, -2.0, 0.0),
        "head": (g("head") - 1.2, -3.0, 0.0),
        "shoulder.L": (g("shoulder.L") - 1.5, 0.0, 3.0),
        "shoulder.R": (g("shoulder.R") + 1.5, 0.0, 3.0),
    }
    ah = {
        "pelvis": (g("pelvis") + 3.0, 0.0, 0.0),
        "spine_01": (g("spine_01") + 2.4, -6.0, 0.0),
        "spine_02": (g("spine_02") + 2.2, -6.0, 0.0),
        "chest": (g("chest") + 2.8, -8.0, 0.0),
        "neck": (g("neck") - 1.0, 3.0, 0.0),
        "head": (g("head") - 1.5, 4.0, 0.0),
        "shoulder.L": (g("shoulder.L") + 9.0, 0.0, -12.0),
        "shoulder.R": (g("shoulder.R") - 3.0, 0.0, -8.0),
    }
    return a0, ac, ah


def build_state(arm, start_pose):
    """把 A0 / AC / AH 三张状态表算出来（拳/踝都是**相对肩 / 相对髋**的向量）。"""
    global STATE
    A.apply_pose(arm, start_pose)
    bpy.context.view_layer.update()
    fist0, sh0, hip0, ankle0 = {}, {}, {}, {}
    for side in SIDES:
        fist0[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        sh0[side] = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        hip0[side] = Vector(A.bone_world(arm, "thigh." + side, "head"))
        ankle0[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
        HAND0[side] = tuple(A.bone_direction(arm, "hand." + side))
        POLE_LEG_A0[side] = UP._leg_pole_from_pose(arm, side)
        POLE_ARM_A0[side] = UP._elbow_pole_from_pose(arm, side)
        HIP0[side] = hip0[side]

    a0, ac, ah = _trunk(start_pose)

    # 拳峰「相对肩」的目标（米）。★ 相对量 ⟹ 躯干怎么动，靶子跟着走（B07 教训 1）。
    rel_a0 = {s: fist0[s] - sh0[s] for s in SIDES}
    rel_ac = {
        PUNCH: Vector((0.095, -0.265, 0.055)),      # 收拳入怀（287 mm ⟹ 腕距 189 mm）
        COUNTER: Vector((-0.140, -0.470, 0.185)),   # 后手略前送（反向预备）
    }
    rel_ah = {
        PUNCH: Vector((0.040, -0.615, 0.045)),      # 直拳轰出（−y 相对前移 350 mm）
        COUNTER: Vector((-0.200, -0.330, 0.110)),   # 后手向后摆做配重（后移 140 mm）
    }
    # ★ 手骨指向 = 拳峰相对肩的方向（见文件头第 2 条）⟹ 腕距 = |rel| − hand_len，
    #   恒落在 [176.6, 551.7] 环带内，`arm_to` 的夹取全程不触发。
    hand_ac = {s: tuple(rel_ac[s].normalized()) for s in SIDES}
    hand_ah = {s: tuple(rel_ah[s].normalized()) for s in SIDES}

    # 踝「相对髋」的目标（米）
    ank_a0 = {s: ankle0[s] - hip0[s] for s in SIDES}
    ank_ac = {
        KNEE: ank_a0[KNEE] + Vector((0.006, -0.020, 0.028)),   # 提膝预备
        PUNCH: ank_a0[PUNCH] + Vector((0.0, 0.010, 0.012)),    # 支撑腿微屈
    }
    ank_ah = {
        KNEE: Vector((-0.030, -0.320, -0.412)),   # ★ 探针定案：大腿抬到水平
        PUNCH: ank_a0[PUNCH] + Vector((0.0, 0.060, -0.020)),   # 支撑腿后蹬（反作用）
    }

    STATE = {
        "A0": {
            "trunk": a0, "rel": rel_a0, "hand": dict(HAND0),
            "ankle": ank_a0, "tip": {"L": TIP_A0, "R": TIP_A0},
            "pole_arm": dict(POLE_ARM_A0), "pole_leg": dict(POLE_LEG_A0),
            "pelvis_y": 0.0,
        },
        "AC": {
            "trunk": ac, "rel": rel_ac, "hand": hand_ac, "ankle": ank_ac,
            "tip": dict(TIP_AC),
            "pole_arm": {s: _lerp3(POLE_ARM_A0[s], POLE_ARM_AH[s], 0.6)
                         for s in SIDES},
            "pole_leg": {s: _lerp3(POLE_LEG_A0[s], POLE_LEG_AH[s], 0.5)
                         for s in SIDES},
            # 前摇：收拳入怀 = 把身体往前带一点（反作用），骨盆 −8 mm
            "pelvis_y": -0.008,
        },
        "AH": {
            "trunk": ah, "rel": rel_ah, "hand": hand_ah, "ankle": ank_ah,
            "tip": dict(TIP_AH),
            "pole_arm": dict(POLE_ARM_AH), "pole_leg": dict(POLE_LEG_AH),
            # 命中：拳向前轰 ⟹ 反作用把骨盆往后送 30 mm（空中无地面反力，
            # 只能靠对侧臂 + 支撑腿后蹬平衡；30 mm 远小于 60 mm 漂移上限）
            "pelvis_y": 0.030,
        },
    }
    return rel_a0, ank_a0


# =============================================================== 门禁
def _bone_point(mat):
    return (mat[3], mat[7], mat[11])


def pelvis_moving(arm):
    """`pelvis` 的后代骨集合（含自身）。

    ★★ **本支尺子的第一块补丁**：全世界只有 `pelvis` 带 `@loc`
    ⟹ 只有它和它的**后代**跟着弹道平移；`root`（pelvis 的父骨）**原地不动**。
    于是 `root` 的「相对骨盆位置」必然随落差变化 —— 实测正好是落距本身
    （`seam_end_relpos_bone = "root"`、**951.889 mm** = 落差 951.9 mm）。
    所以「平移不变」只对**会动的那部分骨架**成立：
    后代骨比「相对骨盆」，非后代骨比「世界绝对」。
    **修的是尺子，容差 1e-6 一字未动。**
    """
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
    """两套世界矩阵的「平移不变」逐位差（文件头第 1 件）。

    返回 `(朝向差, 相对位置差_m, 朝向最差骨, 位置最差骨)`：
      · `pelvis` 的**后代**（`moving`）比「(骨位置 − 骨盆位置)」—— 整具骨架的
        纯竖直平移被自动约掉，量到的纯粹是"姿态回没回去"；
      · 非后代（`root` 及其祖先）比**世界绝对**位置（它们本来就不动）。
    **换对尺子，容差仍是 1e-6。**

    两端分开报是为了**定位**（B07 诊断教训的同类）：
      · 朝向差大 ⟹ 欧拉分支没对上（`_unwrap_xyz` 折错了支）；
      · 相对位置差大 ⟹ 父链累计/骨长错（姿态其实不是同一个），或尺子没扣对。
    首版只报一个合数，红的时候无法判断是哪一类 —— 这次连**是哪根骨**一起报。
    """
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
            # 会跟着 pelvis 一起平移的那部分：扣掉骨盆，比姿态
            da = (xa - pa[0], ya - pa[1], za - pa[2])
            db = (xb - pb[0], yb - pb[1], zb - pb[2])
        else:
            # 不动的部分（root 及其祖先）：直接比世界绝对位置
            da, db = (xa, ya, za), (xb, yb, zb)
        worst = max(abs(u - v) for u, v in zip(da, db))
        if worst > rel:
            rel, rel_bone = worst, name
    return ori, rel, ori_bone, rel_bone


def pose_seam_delta(mats_a, mats_b, moving):
    ori, rel = pose_seam_split(mats_a, mats_b, moving)[:2]
    return max(ori, rel)


def air_assertions(arm, action, samples, start_mats, sole, target_err, reach,
                   knee):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(s["pelvis"]) for s in samples]
    zs = [p.z for p in pelvis]

    # 0) 接缝：首帧**原始**世界矩阵逐位 = `Jump_Fall@0`；末帧用平移不变尺子。
    mats0 = CR.action_world_matrices(arm, action, 0)
    mats1 = CR.action_world_matrices(arm, action, TOTAL)
    moving = pelvis_moving(arm)
    delta0 = CR.matrix_delta(mats0, start_mats)
    raw1 = CR.matrix_delta(mats1, start_mats)
    ori1, rel1, ori_bone, rel_bone = pose_seam_split(mats1, start_mats, moving)
    delta1 = max(ori1, rel1)
    res["seam_start_delta"] = float("%.3e" % delta0)
    res["seam_end_pose_delta"] = float("%.3e" % delta1)
    res["seam_end_orient_delta"] = float("%.3e" % ori1)
    res["seam_end_orient_bone"] = ori_bone
    res["seam_end_relpos_delta_mm"] = round(rel1 * 1000.0, 6)
    res["seam_end_relpos_bone"] = rel_bone
    res["seam_end_raw_delta_mm"] = round(raw1 * 1000.0, 1)
    res["fall_over_anim_mm"] = round((zs[0] - zs[-1]) * 1000.0, 1)
    res["air_seam_start_ok"] = delta0 <= 1e-6
    res["air_seam_end_ok"] = delta1 <= 1e-6
    res["seam_end_ruler_note"] = (
        "末帧比「平移不变」姿态差：**pelvis 的后代**比「骨位置−骨盆位置」，"
        "**非后代（root）比世界绝对位置** —— 只有 pelvis 带 @loc，root 原地不动，"
        "把 root 也算进「相对骨盆」就会量到落差本身（首版实测 951.889 mm = 落距）。"
        "容差仍 1e-6，未放宽。本次落 %.1f mm。" % ((zs[0] - zs[-1]) * 1000.0))

    # 1) 骨盆 z 仍是 A12 的同一条弹道（**本支最该守的判据**）。
    err = max(abs(zs[i] - pelvis_z(frames[i]))
              for i in range(len(frames))) * 1000.0
    res["ballistic_max_err_mm"] = round(err, 4)
    res["air_ballistic_ok"] = err <= AIR_BALLISTIC_TOL_MM
    res["pelvis_z_start_mm"] = round(zs[0] * 1000.0, 2)
    res["pelvis_z_hit_mm"] = round(zs[HIT] * 1000.0, 2)
    res["pelvis_z_end_mm"] = round(zs[-1] * 1000.0, 2)
    res["fall_rate_end_mm_per_frame"] = round((zs[-1] - zs[-2]) * 1000.0, 3)

    # 1b) **重心不上升**：命中帧的骨盆 z 必须**低于** f0（与 B07「必须上升 135 mm」相反）。
    res["pelvis_hit_minus_start_mm"] = round((zs[HIT] - zs[0]) * 1000.0, 1)
    res["no_center_rise_ok"] = zs[HIT] <= zs[0] - 1e-9
    rise = [frames[i + 1] for i in range(len(zs) - 1)
            if zs[i + 1] > zs[i] + 1e-12]
    res["ballistic_rise_frames"] = rise
    res["monotone_down_ok"] = not rise

    # 2) 骨盆水平漂移（空中反冲）。
    hspan = max(math.hypot(p.x - pelvis[0].x, p.y - pelvis[0].y)
                for p in pelvis) * 1000.0
    hnet = math.hypot(pelvis[-1].x - pelvis[0].x,
                      pelvis[-1].y - pelvis[0].y) * 1000.0
    res["pelvis_span_mm"] = round(hspan, 2)
    res["pelvis_net_mm"] = round(hnet, 3)
    res["air_drift_ok"] = hspan <= AIR_DRIFT_MAX_MM

    # 3) 拳峰世界 −y 行程：（前摇顶点 → 命中帧）。
    fy = [Vector(s["hand." + PUNCH + ".tail"]).y for s in samples]
    res["fist_y_start_mm"] = round(fy[0] * 1000.0, 1)
    res["fist_y_chamber_mm"] = round(fy[CHAMBER_END] * 1000.0, 1)
    res["fist_y_hit_mm"] = round(fy[HIT] * 1000.0, 1)
    strike = (fy[CHAMBER_END] - min(fy[HIT - 2:HIT + 1])) * 1000.0
    res["strike_forward_mm"] = round(strike, 1)
    res["strike_forward_ok"] = strike >= STRIKE_FORWARD_MIN_MM
    res["fist_world_advance_vs_start_mm"] = round((fy[0] - min(fy)) * 1000.0, 1)
    res["strike_ruler_note"] = (
        "行程量的是「前摇顶点 f%d → 命中帧 f%d」：f0 是接缝，guard 拳本就在肩前 "
        "455 mm（A12 f0 的手臂是伸开找平衡的姿态），臂几何上界 552 mm ⟹ "
        "从 f0 量物理上不可能到 300。" % (CHAMBER_END, HIT))

    # 3b) 拳峰弧长（"动作幅度要大"，§6）：前摇顶 → 命中。
    arc = 0.0
    for i in range(CHAMBER_END + 1, HIT + 1):
        arc += (Vector(samples[i]["hand." + PUNCH + ".tail"])
                - Vector(samples[i - 1]["hand." + PUNCH + ".tail"])).length
    res["fist_arc_mm"] = round(arc * 1000.0, 1)
    res["fist_arc_ok"] = arc * 1000.0 >= STRIKE_ARC_MIN_MM

    # 4) 膝撞：`shin.R` head 相对**骨盆**高度的上升。
    kz = [Vector(s["shin." + KNEE]) for s in samples]
    rise_mm = ((zs[0] - kz[0].z) - (zs[HIT] - kz[HIT].z)) * 1000.0
    res["knee_below_pelvis_start_mm"] = round((zs[0] - kz[0].z) * 1000.0, 1)
    res["knee_below_pelvis_hit_mm"] = round((zs[HIT] - kz[HIT].z) * 1000.0, 1)
    res["knee_rise_mm"] = round(rise_mm, 1)
    res["knee_strike_ok"] = rise_mm >= KNEE_RISE_MIN_MM
    res["knee_fwd_start_mm"] = round((kz[0].y - pelvis[0].y) * 1000.0, 1)
    res["knee_fwd_hit_mm"] = round((kz[HIT].y - pelvis[HIT].y) * 1000.0, 1)
    res["knee_drive_fwd_mm"] = round((kz[HIT].y - kz[0].y) * 1000.0, 1)

    # 5) 配重：对侧臂后摆 / 出拳行程 ∈ [0.25, 0.60]（**给区间**）。
    cy = [Vector(s["hand." + COUNTER + ".tail"]).y for s in samples]
    fwd = (fy[CHAMBER_END] - fy[HIT]) * 1000.0
    back = (min(cy[HIT - 2:HIT + 1]) - cy[CHAMBER_END]) * 1000.0
    res["counter_arm_back_mm"] = round(back, 1)
    res["punch_forward_mm"] = round(fwd, 1)
    ratio = (back / fwd) if abs(fwd) > 1e-9 else None
    res["counter_balance_ratio"] = round(ratio, 4) if ratio is not None else None
    res["counter_balance_ok"] = bool(
        ratio is not None
        and COUNTER_BALANCE_RANGE[0] <= ratio <= COUNTER_BALANCE_RANGE[1])
    res["counter_balance_note"] = (
        "制动力只能由对侧肢体提供（空中无地面反力）；给的是**区间**，"
        "单边阈值等于没定。")

    # 6) 命停：f13~f15 **关节**姿态完全冻结（骨盆 loc 照常落 —— 见文件头第 2 件）。
    steps = []
    for i in range(HIT + 1, HOLD_END + 1):
        worst = 0.0
        for name in set(samples[i]["euler"]) | set(samples[i - 1]["euler"]):
            ea = samples[i - 1]["euler"].get(name, (0.0, 0.0, 0.0))
            eb = samples[i]["euler"].get(name, (0.0, 0.0, 0.0))
            worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
        steps.append(round(worst, 5))
    res["hitstop_frozen_steps"] = steps
    res["hitstop_frames"] = HOLD_END - HIT + 1
    res["hitstop_present"] = (len(steps) >= 2 and max(steps) <= 1e-3)
    res["hitstop_note"] = (
        "顿的是**关节欧拉通道**，不含 location；骨盆在这 3 帧仍沿弹道落 "
        "%.1f mm（否则 air_ballistic_ok 必红）。" % ((zs[HIT] - zs[HOLD_END]) * 1000.0))

    # 7) 全段离地：通用贴地/滑移窗口不适用，显式登记原因。
    #    ★ 判据是**结构式**，不是绝对余量（见 `airborne_ruler_note`）。
    lows = [min(sole[i]["L"], sole[i]["R"]) for i in range(len(sole))]
    drop = [pelvis_z(frames[i]) - lows[i] for i in range(len(sole))]
    res["min_sole_all_mm"] = round(min(lows) * 1000.0, 1)
    res["min_sole_frame"] = frames[lows.index(min(lows))]
    res["end_sole_clearance_mm"] = round(lows[-1] * 1000.0, 1)
    res["leg_drop_mm"] = {"start": round(drop[0] * 1000.0, 1),
                          "max": round(max(drop) * 1000.0, 1),
                          "end": round(drop[-1] * 1000.0, 1)}
    res["leg_drop_over_seam_mm"] = round((max(drop) - drop[0]) * 1000.0, 1)
    res["all_airborne_ok"] = bool(
        min(lows) > AIRBORNE_MIN_CLEARANCE_MM
        and (max(drop) - drop[0]) * 1000.0 <= LEG_DROP_OVER_SEAM_MM)
    res["airborne_ruler_note"] = (
        "全段离地用**结构口径**，不用绝对余量：① 鞋底全程 > 0（真的没落地）；"
        "② 腿不许比**接缝姿态**多伸 > %.0f mm —— 量的口径是「骨盆→最低鞋底」的竖距，"
        "只跟**姿态**有关、跟落了多少无关。"
        "★ 原阈值 200 mm 是 20 帧试做版的代理量（当时全程落约 600 mm）；"
        "按单帧步长预算把命中段拉到 9 帧、总数 %d 帧后，全程落 %.0f mm，"
        "那个代理量随帧数漂移 ⟹ **它不是真判据**。换姿态口径后与帧数无关。"
        "**换对判据，不是放宽容差。**"
        % (LEG_DROP_OVER_SEAM_MM, TOTAL, (zs[0] - zs[-1]) * 1000.0))
    res["ground_contact_ok"] = None
    res["ground_contact_skipped_reason"] = \
        "全段离地（鞋底最低 %.1f mm @ f%d），-2~+6 mm 窗口不适用" % (
            min(lows) * 1000.0, frames[lows.index(min(lows))])
    res["no_foot_slide_skipped_reason"] = "全段离地，支撑脚不存在"

    # 8) 收招缓出：口径固定在**收招窗口**（含"从命停释放"的第一步 f17→f18）。
    tail, bones = [], []
    for index in range(RETURN_START + 1, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst, bone = 0.0, None
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > worst:
                worst, bone = step, name
        tail.append(round(worst, 5))
        bones.append(bone)
    res["return_tail_deg_per_frame"] = tail
    res["return_tail_worst_bone"] = bones
    res["return_tail_window"] = [RETURN_START + 1, TOTAL]
    res["decel_smooth_ok"] = bool(
        len(tail) >= 2 and all(tail[i + 1] <= tail[i] + 1e-9
                               for i in range(len(tail) - 1)))
    res["no_snap_stop_ok"] = bool(tail and tail[-1] <= 5.0)
    res["decel_smooth_note"] = (
        "窗口取 [f%d, f%d]：**含**从命停释放的第一步 f%d→f%d（最大的一步就在这里），"
        "再逐帧单调收敛到 0。末尾一串 0 = 收招平台（刻意逐位冻结），合法。"
        "**是换对窗口，不是放宽容差。**"
        % (RETURN_START + 1, TOTAL, RETURN_START, RETURN_START + 1))

    # 9) IK 到位 / 腿可达余量。
    limit = A.L_THIGH + A.L_SHIN
    res["ankle_target_error_mm"] = round(target_err * 1000.0, 3)
    res["ik_reach_ok"] = target_err * 1000.0 <= 5.0
    res["leg_reach_limit_mm"] = round(limit * 1000.0, 1)
    res["leg_reach_max_ratio"] = {
        s: round(max(r for side, r in reach if side == s), 4) for s in SIDES}
    res["leg_reach_headroom_mm"] = {
        s: round((limit - max(r for side, r in reach if side == s) * limit)
                 * 1000.0, 1) for s in SIDES}
    res["leg_reach_ok"] = bool(all(r <= 0.9995 for _s, r in reach))

    # 10) 膝角（诊断）：提膝腿的膝角必须真的在动。
    res["knee_bend_start_deg"] = {s: round(knee[0][s], 2) for s in SIDES}
    res["knee_bend_hit_deg"] = {s: round(knee[HIT][s], 2) for s in SIDES}
    res["knee_bend_span_deg"] = {
        s: round(max(k[s] for k in knee) - min(k[s] for k in knee), 2)
        for s in SIDES}

    # 11) 力量传导链（脚→腿→髋→腰→肩→手，六段全非零）。
    #     空中无地面反力 ⟹ 尺子取「可见」下限（位移 ≥5 mm / 转角 ≥3°），
    #     与 A11/A12 同口径，实测值一并登记（**不放宽、只换对**）。
    moved, swing, nonzero = {}, {}, {}
    for segment, names in (("foot", ("foot.L", "foot.R")),
                           ("pelvis", ("pelvis",)),
                           ("chest", ("chest",)),
                           ("shoulder", ("shoulder.L", "shoulder.R")),
                           ("hand", ("hand.L.tail", "hand.R.tail"))):
        big = 0.0
        for name in names:
            points = [Vector(s[name]) for s in samples]
            big = max(big, max((p - points[0]).length for p in points) * 1000.0)
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
                             and all(v >= 3.0 for v in swing.values())
                             and all(v >= 1.0 for v in nonzero.values()))

    # 12) 逐帧最大欧拉步长排行（`no_teleport` 红时直接定位）。
    scan = []
    for index in range(1, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst_step, worst_bone = 0.0, None
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            step = max(abs(a - b) for a, b in zip(ea, eb))
            if step > worst_step:
                worst_step, worst_bone = step, name
        scan.append([samples[index]["frame"], worst_bone, round(worst_step, 2)])
    res["step_scan_top"] = sorted(scan, key=lambda r: -r[2])[:10]
    worst_scan = max((r[2] for r in scan), default=0.0)
    res["no_teleport_max_step_deg"] = round(worst_scan, 3)
    res["no_teleport_budget_left_deg"] = round(
        NO_TELEPORT_MAX_DEG - worst_scan, 3)

    # 13) 打击点 / 元数据。
    fist_hit = Vector(samples[HIT]["hand." + PUNCH + ".tail"])
    knee_hit = Vector(samples[HIT]["shin." + KNEE])
    res["hit_point_fist_mm"] = [round(v * 1000.0, 1) for v in fist_hit]
    res["hit_point_knee_mm"] = [round(v * 1000.0, 1) for v in knee_hit]
    res["hit_frame"] = HIT
    res["antic_frame"] = CHAMBER_END
    res["cancel_frame"] = CANCEL
    return res


# =============================================================== 主流程
def main():
    global START_POSE, START_QUATS, START_MATS

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("AIR08_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()
    for module, action_name in ((JS, JS.NAME), (JU, JU.NAME), (JFE, JFE.NAME)):
        if action_name not in bpy.data.actions:
            print("AIR08_BOOTSTRAP 动画工程缺 %s，先补跑" % action_name)
            module.main()
            arm, meshes = A.open_animation_project()
            A.setup_scene()

    # ★ 库里 `PROBE_BONES` 不含 thigh / shin，本支要量膝，本进程内并入（不改 anim_lib）。
    A.PROBE_BONES = tuple(A.PROBE_BONES) + PROBE_EXTRA

    I1.idle_pose(arm, 0.0)

    z0, zN = pelvis_z(0), pelvis_z(TOTAL)
    A.report("AIR08_BALLISTIC", {
        "g_per_frame": G_PER_FRAME,
        "takeoff_pelvis_z_mm": round(JS.TAKEOFF_PELVIS_Z * 1000.0, 3),
        "base_t_frames_from_takeoff": JFE.BASE_T,
        "z_start_mm": round(z0 * 1000.0, 3),
        "z_hit_mm": round(pelvis_z(HIT) * 1000.0, 3),
        "z_end_mm": round(zN * 1000.0, 3),
        "fall_over_anim_mm": round((z0 - zN) * 1000.0, 1),
        "hitstop_fall_mm": round((pelvis_z(HIT) - pelvis_z(HOLD_END)) * 1000.0, 1),
        "note": ("与 A10/A11/A12 **同一个** `pelvis_z`；B08 只做「不破坏弹道」——"
                 "命中停顿冻关节不冻时间，否则这里会红 %.1f mm。"
                 % ((pelvis_z(HIT) - pelvis_z(HOLD_END)) * 1000.0)),
    })

    # ---- 读 A12 成品 f0 当接缝（**不重算**：`aim_carry` 是有状态接力）。
    JU.build_arm_targets()
    START_POSE, START_QUATS = JU.capture_start(
        arm, bpy.data.actions[JFE.NAME], 0)
    START_MATS = CR.action_world_matrices(
        arm, bpy.data.actions[JFE.NAME], 0)
    # ★ 必须卸 action（A11 踩过：留着上游会在某些帧把 f-curve 压回 pose bone）。
    arm.animation_data.action = None
    bpy.context.view_layer.update()

    rel_a0, ank_a0 = build_state(arm, START_POSE)
    A.report("AIR08_STATE", {
        "fist_rel_shoulder_A0_mm": {s: [round(v * 1000.0, 1) for v in rel_a0[s]]
                                    for s in SIDES},
        "ankle_rel_hip_A0_mm": {s: [round(v * 1000.0, 1) for v in ank_a0[s]]
                                for s in SIDES},
        "hip_A0_mm": {s: [round(v * 1000.0, 1) for v in HIP0[s]] for s in SIDES},
        "punch_side": PUNCH, "knee_side": KNEE, "counter_side": COUNTER,
        "punch_rel_AC_AH_mm": {
            "AC": [round(v * 1000.0, 1) for v in STATE["AC"]["rel"][PUNCH]],
            "AH": [round(v * 1000.0, 1) for v in STATE["AH"]["rel"][PUNCH]]},
        "punch_strike_span_mm": round(
            (STATE["AC"]["rel"][PUNCH].y - STATE["AH"]["rel"][PUNCH].y) * 1000.0, 1),
        "knee_ankle_rel_AH_mm": [
            round(v * 1000.0, 1) for v in STATE["AH"]["ankle"][KNEE]],
        "note": "拳/踝都是**相对肩 / 相对髋**的量（B07 教训 1：参照系跟躯干走）。",
    })

    JS._PREV_EULER.clear()
    for name, value in START_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    JS.ARM_QUAT.clear()
    JS.ARM_ROLL.clear()
    JS.ROLL_MAX.clear()
    A.apply_pose(arm, START_POSE)
    bpy.context.view_layer.update()
    for name in ARM6 + LEG6:
        JS.ARM_QUAT[name] = arm.pose.bones[name].matrix.to_quaternion()
    JS.MAX_ABS_EULER_Y = 0.0
    # 沿用 A11/B07 已验收的旋钮（A11 实测 `Y_SAFE` 的拐点就是 28）。
    JS.ROLL_RANGE = 150.0
    JS.Y_SAFE = 28.0
    del TARGETS[:]
    del ARMTGT[:]
    del TRACE[:]
    del UP.REACH[:]
    del UP.POLE_SIN[:]
    del UP.REQ[:]
    UP._BULGE_PREV.clear()
    UP._ROLL_PREV.clear()
    # ★ roll 连续性权重提到 1.20（B07 = 0.60）：首版 f7 的红点就是 `forearm.L` 的 roll
    #   在 4°↔22° 之间"改主意"（B07 第 1 件同病）。**改求解偏好，不是改判据。**
    UP.ROLL_W = ROLL_W
    LOCK.clear()
    LOCK_PY.clear()
    LOCK_ANK.clear()

    keyframes = [(0, START_POSE)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, build_pose(arm, frame, record=True)))

    A.report("AIR08_ARM_ROLL", {
        "max_abs_euler_y_deg": round(JS.MAX_ABS_EULER_Y, 2),
        "max_abs_roll_deg": {k: round(JS.ROLL_MAX.get(k, 0.0), 1)
                             for k in ARM6 + LEG6},
        "roll_range_deg": JS.ROLL_RANGE, "y_safe_deg": JS.Y_SAFE,
        "roll_w": ROLL_W,
        "roll_w_note": "B08 用 1.20（B07 = 0.60）：改求解偏好，不是改判据。",
    })

    meta = {
        "anim_id": NAME, "loop": False, "category": "普通攻击",
        "note": ("空中攻击：接 `Jump_Fall@0`（弹道下落中）→ 收拳入怀 + 提膝预备 → "
                 "前手直拳（拳峰 −y 行程 ≥%.0f mm）+ 后腿膝撞（膝相对骨盆上升 "
                 "≥%.0f mm）→ f%d~f%d 关节冻结 3 帧 → 缓出收招 → f%d 起收招平台"
                 "（逐位 = `Jump_Fall@0` 姿态）。骨盆 z 全程 = A12 弹道"
                 "（**重心不许上升**）"
                 % (STRIKE_FORWARD_MIN_MM, KNEE_RISE_MIN_MM, HIT, HOLD_END,
                    RETURN_END)),
        "antic_frame": CHAMBER_END, "hit_frame": HIT, "cancel_frame": CANCEL,
        "hitstop_frames": HOLD_END - HIT + 1,
        "hitstop_span": [HIT, HOLD_END],
        "root_motion_m": [0.0, 0.0],
        "root_motion_note": "空中族**不许** Root Motion（清单 §0.4；C 族起才允许）。",
        "seam_in": "%s@0（世界矩阵逐位相同）" % JFE.NAME,
        "seam_out": ("%s@0（**平移不变**姿态逐位相同：骨盆已沿弹道又落 %.1f mm）"
                     % (JFE.NAME, (z0 - zN) * 1000.0)),
        "pelvis_ballistic": {
            "rule": "骨盆 z 逐帧 = `anim_jump_fall.pelvis_z(f)`（同一组常量），误差 ≤2 mm",
            "change_allowed": "禁止（与 B07「必须上升 135 mm」相反）",
        },
        "air_drift": {"rule": "骨盆水平位移 ≤ %.0f mm" % AIR_DRIFT_MAX_MM,
                      "why": "空中无地面反力，出拳必有反冲；60 mm 是'看得出但不成漂移'"},
        "counter_balance": {"rule": "对侧臂后摆 / 出拳行程 ∈ [0.25, 0.60]",
                            "why": "制动力只能由对侧肢体提供 —— 空中动作守恒"},
        "power_chain_scale_note": ("空中无地面反力：thigh/shin 取'可见'下限 3°，"
                                   "A10 的 15° 是蹬地展开的量"),
        "hitstop_scope": "冻结全身关节欧拉；骨盆 location 仍走弹道（顿的是关节，不是时间）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "ENTER": 0, "ANTIC_END": CHAMBER_END, "STRIKE_START": BURST_START + 1,
        "HIT": HIT, "HITSTOP_END": HOLD_END, "RETURN_START": RETURN_START,
        "CANCEL": CANCEL, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report["common_ground_min_all_frames_mm"] = report.get("ground_min_mm")
    report["ground_contact_ok"] = None

    sole = JS.sole_series(arm, action, list(range(0, TOTAL + 1)))
    ankles = JU.ankle_series(arm, action, list(range(0, TOTAL + 1)))
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    target_err = 0.0
    for index, frame in enumerate(range(0, TOTAL + 1)):
        if frame == 0:
            continue
        for side in SIDES:
            if (frame, side) in pair:
                target_err = max(target_err,
                                 (Vector(ankles[index][side])
                                  - pair[(frame, side)]).length)

    reach = list(UP.REACH)
    knee = CR.knee_series(arm, action, list(range(0, TOTAL + 1)))
    report.update(air_assertions(arm, action, samples, START_MATS, sole,
                                 target_err, reach, knee))
    report["meta"] = meta
    # 显式登记被跳过的门禁（值 None）：既让 failed 干净，又不静默隐藏。
    report["skipped_gates"] = sorted(
        k for k, v in report.items() if v is None and k.endswith("_ok"))
    failed = sorted(k for k, v in report.items()
                    if (k.endswith("_ok") or k == "no_teleport")
                    and v is not True and v is not None)
    report["failed"] = failed
    A.report("AIR08_REPORT", report)

    # 诊断：逐帧臂/腿骨 euler 步（只打"有戏"的帧，定位 `no_teleport`）。
    detail = []
    for index in range(1, len(TRACE)):
        before, after = TRACE[index - 1], TRACE[index]
        row, big = {"f": after["frame"]}, 0.0
        for name in ARM6 + LEG6:
            step = max(abs(a - b) for a, b in
                       zip(before["euler"][name], after["euler"][name]))
            big = max(big, step)
            row[name] = "%d Y%.0f r%.0f" % (
                round(step), after["euler"][name][1],
                after["roll"].get(name, 0.0))
        if big >= 4.0:
            row["max_step"] = round(big, 2)
            detail.append(row)
    A.report("AIR08_TRACE_DETAIL", detail)

    reach_mm = (UP.bone_len(arm, "upperarm.L") + UP.bone_len(arm, "forearm.L"))
    reqs = [r for r in UP.REQ if len(r) == 4]
    A.report("AIR08_ARM_CLAMP_SUMMARY", {
        "reach_mm": round(reach_mm * 1000.0, 1),
        "upper_limit_mm": round(reach_mm * 0.9995 * 1000.0, 1),
        "fold_min_mm": round(reach_mm * UP.FOLD_MIN_RATIO * 1000.0, 1),
        "lower_clamped_frames": sorted({f for f, s, req, used in reqs
                                        if used > req + 1e-6}),
        "upper_clamped_frames": sorted({f for f, s, req, used in reqs
                                       if req > reach_mm * 0.9995 * 1000.0}),
        "upper_over_by_mm": round(max(
            [req - reach_mm * 0.9995 * 1000.0 for f, s, req, used in reqs]
            or [0.0]), 2),
        "min_req_mm": round(min([r[2] for r in reqs] or [0.0]), 1),
        "max_req_mm": round(max([r[2] for r in reqs] or [0.0]), 1),
        "note": ("上下夹取**分开报**（B07 诊断教训：只报下夹取会埋红点）。"
                 "手骨指向取 `normalize(rel)` ⟹ 腕距恒在环带内，夹取不应触发。"),
    })

    if not SKIP_RENDER:
        AIR_SIDE = ("side", (4.6, -0.10, 1.95), (0.0, -0.10, 1.95), 2.70,
                    (760, 1200))
        AIR_FRONT = ("front", (0.0, -5.0, 1.95), (0.0, 0.0, 1.95), 2.70,
                     (760, 1200))
        AIR_3Q = ("three_quarter", (3.2, -3.6, 2.10), (0.0, -0.15, 1.85), 2.70,
                  (760, 1200))
        A.render_pose_sheet(arm, action,
                            [0, 4, 7, 11, 14, HIT, HOLD_END, 22, TOTAL],
                            "airlight", views=(AIR_SIDE,))
        A.render_pose_sheet(arm, action, [0, 7, HIT, TOTAL], "airlight",
                            views=(AIR_FRONT,))
        A.render_pose_sheet(arm, action, [0, 7, HIT, TOTAL], "airlight",
                            views=(AIR_3Q,))
        # 存盘/导出只在**出图那一遍**做：SKIP_RENDER 是纯门禁迭代。
        A.save_project()
        A.export_glb(arm)
    print("AIRLIGHT_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("AIRLIGHT_FAILURE " + traceback.format_exc())
