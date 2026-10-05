"""anim_light_01 —— B01 `Light_01` 轻拳1（前手直拳）。

设计（对着清单「下一支计划 —— B01」逐条落）：
    定位      前手直拳，**启动快、收招快，位移极小**（清单原文 B01）。
    时长      18 帧 / 0.300 s @60fps，**非循环**（`loop=False`）。
    首末帧    **都逐位 = `Idle_01@0`** —— 轻拳单发要能独立播放，B01~B03 三连的
              接缝因此全落在同一姿态上（A13 同口径，世界矩阵 ≤1e-6）。
    结构      GUARD 0 ／ ANTIC 0~6（前摇，反向预备在躯干与肩带）／
              HIT 6（拳峰到极值）／HITSTOP f6~f7（**2 帧完全冻结**）／
              RECOVER 7~18（沿原路收回护体架势）／CANCEL 10。

---------------------------------------------------------------------------
★ 本支第 0 件事：探针先量，再动手。
  `probe_light01.py` / `probe_light01b.py` 两支只读探针给出三个定盘数：

  1. **前脚 = L**（踝世界 y：L −169.6 mm、R +140.4 mm）⟹ **前手 = L**，与计划预判一致。
     全文 L = 前手（出拳手），R = 后手，不再对调。
  2. **`max_abs_euler_y_deg` = 15.53**（出拳姿态，六根臂骨全量）。远低于 A13 定案里
     「>45° 先换等价族」的阈值 ⟹ **走逐分量欧拉插值即可，不需要任何换族/去扭转**。
  3. **`forearm.L` 的 rz 通道要扫 131.6°**（guard −137.845 → strike −6.25）。
     这就是 `no_teleport ≤25°/帧` 的全部预算来源 —— 见下。

---------------------------------------------------------------------------
★ 第 1 件（本支最贵的一课）：计划的「`STRIKE 4~6`」装不下一记直拳，必须重排。

  计划原文：「`WINDUP 0~4` 拳略后收 20 mm」＋「`STRIKE 4~6` 拳峰伸到极值」。
  但探针实测：从护体架势到直拳伸直，**前臂要转 131.6°**（护体时肘弯 143°，
  直拳时肘弯 13.7° —— 这是 `Idle_01@0` 的护体架势决定的，不是可调参数）。

  131.6° 的预算能不能摊进 2 帧？`no_teleport` 是**逐分量、逐帧**判的：
  2 帧最多装 50°。差 2.6 倍 ⟹ 伸展只能占满 clock 0~6 全程。这与 A13
  「`IMPACT 4~8` 装不下触地+屈膝到最深」是同一类矛盾（表格把互相排斥的事塞进
  同一个窗口），解法同源：**按物理重排**。

  **重排后的三段**（在 `clock` 域上）：
    clock 0~6   ANTIC+STRIKE 合一：**加速**把肘从 143° 伸到 13.7°（峰值在末帧）；
                与此同时躯干与肩带做反向预备（髋/胸 ry 先正后负、前肩 rz 先正后负），
                并给 `upperarm.L` 的 rz 叠一条**反向偏移轨**（`COIL`）。
    clock 6     HIT：拳峰到极值，上臂−前臂−腕共线比 0.9935。
    真实 f6~f7  HITSTOP：两帧共用同一份姿态对象（`clock(7) = clock(6) = 6`）。
    clock 6~17  RECOVER：`s = (1−u)^1.59`（起手最快、速度**单调衰减到 0**）。

---------------------------------------------------------------------------
★ 第 1b 件（**两跑两红才逼出来的真结论**）：剖面参数只有一条窄缝。

  `no_teleport ≤25°/帧` 与 `windup_fast_ok`（峰值角速度必须在 f6）**同时**约束
  同一条 131.6° 的行程，缝很窄 —— 两条边界我都踩红过：

    跑 1  `ARM_POW = 1.01`（近乎匀速）：末帧 22.13°/帧 **低于收招首帧 22.84**，
          全局峰值落到 f8 ⟹ `windup_fast_ok` 红（`arm_peak_step_frame = 8`）。
    推论  `u^1.5` 那种"启动慢"的剖面：末帧 31.49°/帧 > 25 ⟹ `no_teleport` 红。

  ⟹ 定案 **`ARM_POW = 1.063`（出拳加速进命中）+ `REC_POW = 1.59`（收招单调衰减到 0）**：
      出拳末帧 **23.20**°/帧（≤25，余量 1.80°）＞ 收招首帧 **18.50**°/帧
      ⟹ 全局峰值确定落在 f6；收招末帧 2.91°/帧 ⟹ 无瞬停。
      「启动稍慢」（§6）在本支由**加速度形状**保证（起手慢于均值），
      「启动快」（清单 B01 原文）由**总时长**保证（前摇 ≤4 帧、全程 18 帧）。

---------------------------------------------------------------------------
★ 第 1c 件（本支的**硬结论**）：清单 WINDUP 行的「拳略后收 20 mm」在本支长度下
  **几何不可达**。两条路都堵死，且是**一行不等式**级别的死，不是调参问题。

  路 A —— **收肘**（让 s 在 clock 1 取负 d）：
    一收肘，伸出段就从 6 帧变 5 帧，却仍要摊 (1+d)·131.6°。
    就算按**最匀速**的剖面，单帧也要 (1+d)·131.6/5 = (1+d)·**26.32**°/帧。
        ⟹ **d = 0 时 26.32 > 25 已经红了**（`no_teleport`），任何 d > 0 只会更糟。
    想让 5 帧装下就得让 p < 0.924（剖面**先快后慢**）⟹ 直接违反 `windup_fast_ok`。
    **⟹ 收肘造后收：无解，与 d 的取值无关。**

  路 B —— **上臂后摆**（叠 COIL 反向偏移，唯一剩下的杠杆）：
    两跑实测：COIL 7° → 12.5°（+5.5°）时，拳峰在 f1 的前伸量 308.7 → 291.5 mm，
    其中 ~5.7 mm 来自同期剖面改变 ⟹ **实测灵敏度 ≈ 2.1 mm/°**（护体架势里拳峰
    本来就贴着肩，绕肩转会把它几乎原地带走 —— 这就是灵敏度这么低的原因）。
    要净退 20 mm，需要从 f0 的 242.0 mm 打到 222.0 mm，即额外拉回 69.5 mm
        ⟹ 需反向偏移 69.5 / 2.1 ≈ **33.3°**。
    但 clock 0→1 是**单帧**，受 `no_teleport ≤25°/帧` 约束，且该帧正向（肘伸展）
    已占 5.15°：
        ⟹ 反向偏移上限 = 25 + 5.15 ≈ **30.2°** < 33.3°。
    拿满 30.2° 时拳峰位置 = 291.5 − 2.1 × (30.2 − 12.5) ≈ 254.6 mm
        ⟹ **仍比 f0 前伸 12.6 mm，从未后退。**
    **⟹ 上臂造后收：最好情况也够不着，差 12.6 mm。**

  ⟹ 因此：`COIL` 保留（它是**真的反向预载**，把拳峰相对线性路径拉回 ~17 mm），
    但**如实报 `windup_coil_pullback_mm = 0.0`**，并把判据换成可达的那条
    `windup_reverse_prep_ok`（肩带/躯干的反向预备必须可测）。见 `light_assertions` 第 5b 项。
    **B02/B03 若真要做后收，唯一出路是给 WINDUP 单独加一帧（19~20 帧）。**

---------------------------------------------------------------------------
★ 第 2 件：`clock(frame)` 动作时钟（A13 的基础设施，本支第一次用在**攻击**上）。
  清单 §0.1 要「命中帧保持 2~4 帧，期间姿态完全冻结」，本支取 **2 帧**。
  冻结吃掉的是**动作时间**：`clock(f) = f (f ≤ 6) else f − 1`。
  f6 与 f7 读同一个 clock ⟹ 姿态**逐位相同**（`frozen_delta_deg` 恒为 0，不是"约等于"），
  而收招行程不被压缩（动作时钟跨度 = 18 − 1 = 17）。

---------------------------------------------------------------------------
★ 第 3 件：腿与脚 —— 首末帧逐位对齐的代价。
  `probe_light01b` 实测：`TURN.leg_to`（3D 瞄准式 IK）在**站姿参数**下解出的腿，
  与 `Idle_01@0` 的腿（`leg_ik` + 外展）**逐分量欧拉差 1.2274°**（踝位差 0.023 mm）。
  世界矩阵不是逐位相同 ⟹ **首末帧不能交给 `build_pose` 生成**，只能整帧取
  `I1.idle_pose(arm, 0.0)` 的成品（`_unwrap_xyz` 折到离上一帧最近的一族）。
  1.23° 的替换台阶落在收招尾段（那里每帧 1.1~5.4°）之内，不破 `decel_smooth_ok`。
  贴地常数：本支膝弯几乎不动（±3°），**不需要 A13 那套 z_off**（实测鞋底仍在 −2~+6），
  这正是"能否沿用必须由重跑证明"的结论 —— 不能沿用，因为压根不需要。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_light_01.py
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
import anim_walk_f as WF      # noqa: E402

NAME = "Light_01"
TOTAL = 18                    # 0.300 s @ 60 fps
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

HIT = 6                       # 命中帧（真实帧）
HOLD = 1                      # 命中停顿"吃掉"的动作帧数 ⟹ 冻结 f6/f7 共 2 帧
CLOCK_END = TOTAL - HOLD      # = 17：动作时钟跨度
ANTIC_END = 4                 # 前摇结束（清单「前摇 ≤4 帧」）
CANCEL = 10                   # 可取消帧
ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")
ARM_POW = 1.063               # 伸出段剖面 s = (c/6)^1.063（加速进命中，峰值 = 末帧）
REC_POW = 1.59                # 收招段剖面 s = (1−u)^1.59（起手最快、单调衰减到 0）

DROP = I1.DROP                # −0.070：战斗站姿的骨盆下沉量

# ---------------------------------------------------------------- 出拳姿态（世界方向）
# 探针 S1 那一组：直拳把前臂/上臂/腕摆成一条朝正前方的直线。
STRIKE_DIRS = {
    "upperarm.L": (0.16, -0.96, -0.22),
    "forearm.L": (0.05, -0.999, -0.02),
    "hand.L": (0.02, -1.0, -0.01),
    # 后手留在护体架势里、略后拉（不跟着一起动 —— `front_hand_leads_ok` 守的就是这条）
    "upperarm.R": (-0.30, -0.18, -0.94),
    "forearm.R": (0.34, -0.26, 0.90),
    "hand.R": (0.18, -0.68, 0.71),
}

# ---------------------------------------------------------------- 躯干轨（动作时钟域）
# 每条都以 `Idle_01@0` 的取值起、以同一取值止 ⟹ 首末帧与成品姿态逐位相接。
# rx = 前倾链；ry = 绕纵轴扭转（**负 = 左肩前送**，因为 ry>0 把角色的 +X 侧转向 +Y 身后）。
TRUNK = {
    "pelvis": {"rx": ((0, 4.0), (3, 5.2), (HIT, 6.0), (CLOCK_END, 4.0)),
               "ry": ((0, 0.0), (2.0, 1.6), (HIT, -3.0), (CLOCK_END, 0.0))},
    "spine_01": {"rx": ((0, 2.0), (3, 2.6), (HIT, 3.0), (CLOCK_END, 2.0)),
                 "ry": ((0, 0.0), (2.0, 0.8), (HIT, -2.0), (CLOCK_END, 0.0))},
    "spine_02": {"rx": ((0, 2.0), (3, 2.6), (HIT, 3.0), (CLOCK_END, 2.0)),
                 "ry": ((0, 0.0), (2.2, 1.0), (HIT, -2.0), (CLOCK_END, 0.0))},
    "chest": {"rx": ((0, 1.0), (3, 1.8), (HIT, 3.0), (CLOCK_END, 1.0)),
              "ry": ((0, 0.0), (2.4, 1.8), (HIT, -4.0), (CLOCK_END, 0.0))},
    "neck": {"rx": ((0, -6.0), (3, -6.6), (HIT, -5.0), (CLOCK_END, -6.0)),
             "ry": ((0, 0.0), (3.0, 0.5), (HIT, 0.0), (CLOCK_END, 0.0))},
    "head": {"rx": ((0, 5.0), (3, 5.6), (HIT, 5.0), (CLOCK_END, 5.0)),
             "ry": ((0, 0.0), (3.0, 0.5), (HIT, 0.0), (CLOCK_END, 0.0))},
    # 肩带：**前肩先送** —— rz<0 = 左肩前送（左臂 rz>0 才是向后）。先向后蓄 4° 再送 9°。
    "shoulder.L": {"rx": ((0, -18.0), (3, -16.0), (HIT, -6.0), (CLOCK_END, -18.0)),
                   "rz": ((0, 0.0), (3.5, 4.0), (HIT, -9.0), (CLOCK_END, 0.0))},
    "shoulder.R": {"rx": ((0, -18.0), (3, -18.0), (HIT, -16.0), (CLOCK_END, -18.0)),
                   "rz": ((0, 0.0), (3.5, -2.0), (HIT, -4.0), (CLOCK_END, 0.0))},
}

# 骨盆位移：清单「位移极小」⟹ 水平预算 30 mm 全给**重心前送**（世界 −Y）。
PELVIS_Y = ((0, 0.000), (2.5, 0.005), (HIT, -0.020), (CLOCK_END, 0.0))
PELVIS_DZ = ((0, 0.0), (2.0, 0.002), (HIT, -0.004), (CLOCK_END, 0.0))

# ★ 上臂**反向预载轨**：`upperarm.L` 的 rz 在 clock 1 先向"后"偏 12.5°，再归零。
#
#   **它做不到「拳略后收 20 mm」** —— 这一点是本轮用两跑实测 + 一行不等式证明的，
#   文件头 1c 有完整推导。结论：在本支 18 帧的长度下，拳峰**净后收不可达**，
#   最好情况（偏移顶到 no_teleport 的单帧 25° 极限 = 30.2°）拳峰仍**前伸 12.6 mm**。
#
#   那它还有什么用？实测它是**真的在拉**：偏移 7°→12.5° 时拳峰在 f1 的前伸量
#   由 308.7 → 291.5 mm（其中 ~5.7 mm 来自剖面改变）⟹ 灵敏度 ≈ **2.1 mm/°**，
#   即 12.5° 把拳峰相对"线性插值路径"拉回了 ~17 mm。只是**肘同期伸展 ~19.6°**
#   （+49.5 mm）把它整个吞掉，净位置仍在 f0 之前。
#   所以本轨的**实际作用**是「肩在蓄、肘已在出」的反向预载（视觉上的压缩感），
#   不是拳峰后收 —— 报告里的 `windup_coil_pullback_mm` 如实报 0.0，不修饰。
#
#   偏移在 clock 6 精确归零 ⟹ 命中帧姿态与探针 S1 **逐位相同**
#   （`strike_line_ok` / `strike_reach_ok` 不受影响）。
COIL = {"upperarm.L": {"rz": ((0, 0.0), (1.0, 12.5), (2.0, 6.0),
                              (HIT, 0.0), (CLOCK_END, 0.0))}}
CHANNEL_INDEX = {"rx": 0, "ry": 1, "rz": 2}

ARM_BONES = ARM6
ANKLE_REST = {}               # side -> Vector：`Idle_01@0` 的踝位（全程钉死点）
E_GUARD = {}                  # bone -> `Idle_01@0` 的手臂欧拉（伸出段起点）
E_STRIKE = {}                 # bone -> 命中帧手臂欧拉（已折到离 E_GUARD 最近的一族）
IDLE_POSE = {}                # `Idle_01@0` 的完整姿态字典（首末帧整帧取用）
TRACE = []                    # 逐帧手臂欧拉（|Y| 健康度诊断）
TARGETS = []                  # [(frame, side, target)]：IK 到位核验


def clock(frame):
    """动作时钟：命中停顿期间**时间冻结**，之后所有连续量按冻结后的时间推进。

    A13 的基础设施，本支第一次用在攻击上：f6/f7 读同一个 clock ⟹ 姿态**逐位相同**。
    """
    return frame if frame <= HIT else frame - HOLD


def arm_s(c):
    """手臂「护体架势 ⇄ 命中姿态」的归一化插值量 s（动作时钟域）。

    伸出段（clock 0~6）：`s = (c/6)^1.063` —— **加速进命中**（§6「命中极重」、
    清单「不许先快后慢」）。步长逐帧递增，峰值必落在 f6：
        19.59 / 21.36 / 22.05 / 22.53 / 22.87 / **23.20** °/帧
      两条边界都试过、都红过（这就是本轮改动的原因）：
        · `u^1.5`（更"启动慢"）：末帧 31.49°/帧 > 25，`no_teleport` 红；
        · `u^1.01`（近乎匀速）：末帧 22.13°/帧 **低于收招首帧 22.84**，
          全局峰值落到 f8 ⟹ `windup_fast_ok`（峰值须在 f6）红。
    收招段（clock 6~17）：`s = (1−u)^1.59` —— 起手最快、**速度单调衰减到 0**
      （u=1 处导数 = 0 ⟹ 无瞬停）。首帧 18.50°/帧 < 出拳末帧 23.20 ⟹ 峰值仍在 f6；
      末帧 2.91°/帧 ≤ 5 ⟹ `no_snap_stop`。
    两段在 c = HIT 处都取 1.0，连续。
    """
    if c <= 0.0:
        return 0.0
    if c < HIT:
        return (c / float(HIT)) ** ARM_POW
    if c >= CLOCK_END:
        return 0.0
    u = (c - HIT) / float(CLOCK_END - HIT)
    return (1.0 - u) ** REC_POW


def tval(track, c):
    if not track:
        return 0.0
    return TURN.track(track, c)


def trunk_pose(c):
    """躯干八骨在动作时钟 c 上的完整姿态。"""
    return {bone: (tval(t.get("rx"), c), tval(t.get("ry"), c), tval(t.get("rz"), c))
            for bone, t in TRUNK.items()}


def arm_euler(bone, c):
    """手臂欧拉：guard → strike 的**逐分量**线性插值 + 反向偏移轨（`COIL`）。

    A13 定案的推广：终点是「显式给定的固定姿态」时走逐分量欧拉路径插值 + 同族折叠，
    不走世界朝向 slerp。本支的 strike 正是显式给出的固定姿态，且 `|Y| ≤15.6°`
    （探针实测）离万向节锁很远。
    """
    s = arm_s(c)
    e0, e1 = E_GUARD[bone], E_STRIKE[bone]
    values = [e0[i] + (e1[i] - e0[i]) * s for i in range(3)]
    for channel, track in COIL.get(bone, {}).items():
        values[CHANNEL_INDEX[channel]] += tval(track, c)
    return tuple(values)


def _record_trace(arm, frame, pose):
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    TRACE.append({
        "frame": frame,
        "euler": {b: tuple(round(v, 2) for v in pose[b]) for b in ARM6},
        "quat": {b: arm.pose.bones[b].matrix.to_quaternion() for b in ARM6},
    })


# =============================================================== 姿态生成
def build_pose(arm, frame, record=False):
    """按帧构造完整姿态（内部一律用 `clock(frame)` 驱动）。"""
    c = clock(frame)
    pose = trunk_pose(c)
    pose["toe.L"] = (0.0, 0.0, 0.0)
    pose["toe.R"] = (0.0, 0.0, 0.0)
    pose["@loc"] = {"pelvis": A.wloc(0.0, tval(PELVIS_Y, c),
                                     DROP + tval(PELVIS_DZ, c))}
    for bone in ARM6:
        pose[bone] = arm_euler(bone, c)
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    # 腿：真双骨 IK（3D 瞄准式）。膝弯方向固定世界 −Y（不转身）。
    for side in ("L", "R"):
        target = ANKLE_REST[side]
        if record:
            TARGETS.append((frame, side, tuple(target)))
        TURN.leg_to(arm, pose, side, target, (0.0, -1.0))
    JU._unwrap_legs(arm, pose)

    # 足：钉平到世界水平（rest 朝向）。轻拳不起脚，tip 恒 0。
    for side in ("L", "R"):
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    _record_trace(arm, frame, pose)
    return pose


def idle_frame_pose(arm, prev_euler, threshold=8.0):
    """护体架势帧：整帧取 `Idle_01@0` 成品，必要时折到离上一帧最近的欧拉族。

    为什么必须整帧替换而不是让 `build_pose` 生成：`leg_to` 与 idle 的
    `leg_ik`+外展是两套解算器，实测逐分量差 1.2274°（`probe_light01b`），
    世界矩阵不是逐位相同，`guard_endpoints_ok` 会红。
    折算只改**表示**（同一旋转的 ±360 / 翻转分支），世界朝向不变 ⟹ 判据仍逐位成立。
    """
    out = dict(IDLE_POSE)
    adjusted = {}
    for name, value in IDLE_POSE.items():
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


# =============================================================== 专属门禁
SEGMENTS = {
    "foot": ("foot.L", "foot.R", "toe.L", "toe.R"),
    "leg": ("thigh.L", "shin.L", "thigh.R", "shin.R"),
    "hip": ("pelvis",),
    "waist": ("spine_01", "spine_02", "chest"),
    "shoulder": ("shoulder.L", "shoulder.R"),
    "hand": ARM6,
}


def _euler_range(samples, bones):
    big = 0.0
    for name in bones:
        for channel in range(3):
            vals = [s["euler"].get(name, (0.0, 0.0, 0.0))[channel]
                    for s in samples]
            big = max(big, max(vals) - min(vals))
    return big


def _peak_frame(samples, bones):
    """该段"角速度峰值帧"：逐帧取该段全部骨/通道的最大欧拉增量，取 argmax。"""
    best_frame, best = None, -1.0
    for index in range(1, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst = 0.0
        for name in bones:
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
        if worst > best:
            best, best_frame = worst, samples[index]["frame"]
    return best_frame, round(best, 3)


def light_assertions(arm, action, samples, idle_mats, sole, ankles, reach,
                     target_err):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(s["pelvis"]) for s in samples]
    fist_l = [Vector(s["hand.L.tail"]) for s in samples]
    fist_r = [Vector(s["hand.R.tail"]) for s in samples]
    sternum = [Vector(s["neck"]) for s in samples]      # chest.tail = 胸骨顶

    # 0) **首末帧都逐位 = `Idle_01@0`**（世界矩阵，不是 euler；两侧都量）。
    m0 = CR.action_world_matrices(arm, action, 0)
    mN = CR.action_world_matrices(arm, action, TOTAL)
    d0, dN = CR.matrix_delta(m0, idle_mats), CR.matrix_delta(mN, idle_mats)
    res["first_frame_delta"] = float("%.3e" % d0)
    res["last_frame_delta"] = float("%.3e" % dN)
    res["guard_start_ok"] = bool(d0 <= 1e-6)
    res["guard_end_ok"] = bool(dN <= 1e-6)
    res["guard_endpoints_ok"] = bool(d0 <= 1e-6 and dN <= 1e-6)

    # 1) 拳峰相对胸骨顶的"前伸量"逐帧曲线（后面好几条判据都读它）。
    reach_series = [(sternum[i].y - fist_l[i].y) * 1000.0 for i in range(len(frames))]
    res["front_reach_series_mm"] = [round(v, 1) for v in reach_series]

    # 2) **前手必须真的领先**：命中帧前手前伸量 ≥ 后手 + 300 mm（防"两拳一起动"）。
    fr = (sternum[HIT].y - fist_l[HIT].y) * 1000.0
    br = (sternum[HIT].y - fist_r[HIT].y) * 1000.0
    res["hit_reach_front_mm"] = round(fr, 1)
    res["hit_reach_back_mm"] = round(br, 1)
    res["front_minus_back_mm"] = round(fr - br, 1)
    res["front_hand_leads_ok"] = bool(fr - br >= 300.0)

    # 3) **直拳够远**：相对 f0 的**增量** ≥320 mm（A12 `arms_spread_gain_ok` 的增量范式）。
    gain = reach_series[HIT] - reach_series[0]
    res["strike_reach_gain_mm"] = round(gain, 1)
    res["strike_reach_ok"] = bool(gain >= 320.0)

    # 4) **直拳够"直"**：命中帧 |肩−腕| / (|肩−肘| + |肘−腕|) ≥ 0.92。
    sh = Vector(samples[HIT]["upperarm.L"])
    el = Vector(samples[HIT]["forearm.L"])
    wr = Vector(samples[HIT]["hand.L"])
    ratio = (wr - sh).length / max(1e-9, (el - sh).length + (wr - el).length)
    res["strike_line_ratio"] = round(ratio, 4)
    res["strike_elbow_bend_deg"] = round(180.0 - math.degrees(
        (el - sh).normalized().angle(wr - el)), 2)
    res["strike_line_ok"] = bool(ratio >= 0.92)

    # 5) **前摇 ≤4 帧 + 峰值角速度在命中帧**（"不许先快后慢"）。
    coil_index = min(range(HIT + 1), key=lambda i: reach_series[i])
    res["windup_coil_frame"] = coil_index
    res["windup_coil_pullback_mm"] = round(reach_series[0] - reach_series[coil_index], 1)
    peak_frame, peak_val = _peak_frame(samples, ARM6)
    res["arm_peak_step_frame"] = peak_frame
    res["arm_peak_step_deg"] = peak_val
    res["windup_span_frames"] = coil_index
    res["windup_fast_ok"] = bool(coil_index <= ANTIC_END and peak_frame == HIT)

    # 5b) 清单 WINDUP 行「拳略后收 20 mm」→ **已证几何不可达**（证明见文件头 1c），
    #     所以这里**不放**一条凑绿的假判据，换成**可达且同源**的那条：
    #     命中前肩带/躯干必须出现**可测的反向预备**（先反向、再前送）。
    #     阈值取设计值（肩 +4° / 胸 +1.8° / 髋 +1.6°）的 ~75%，是**先定阈值后看数**。
    prep = {}
    for bone, channel in (("shoulder.L", 2), ("chest", 1), ("pelvis", 1)):
        series = [s["euler"].get(bone, (0.0, 0.0, 0.0))[channel] for s in samples]
        prep[bone] = [round(max(series[:ANTIC_END + 1]), 2),
                      round(series[HIT], 2)]
    res["windup_reverse_prep_deg"] = prep
    res["windup_reverse_prep_ok"] = bool(
        prep["shoulder.L"][0] >= 3.0 and prep["shoulder.L"][1] <= -6.0
        and prep["chest"][0] >= 1.5 and prep["chest"][1] <= -2.5
        and prep["pelvis"][0] >= 1.0 and prep["pelvis"][1] <= -2.0)
    res["windup_chamber_achievable_mm"] = {
        "achieved_net_retreat": res["windup_coil_pullback_mm"],
        "note": ("清单原文「拳略后收 20 mm」不可达：拳峰前伸自 f0 起单调递增；"
                 "收肘路线（5 帧摊 131.6°）最匀速也要 26.32°/帧 > 25；"
                 "上臂路线受第一帧 25° 单帧上限（正向已占 5.15°）约束，"
                 "最好情况拳峰仍前伸 12.6 mm"),
    }

    # 6) **命中停顿**：f6/f7 姿态逐位相同（`clock` 保证 + `set_hitstop` 双保险）。
    steps, cursor = 0, HIT
    while cursor + 1 <= HIT + HOLD:
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
    res["hitstop_frozen_steps"] = steps
    res["hitstop_frames"] = steps + 1
    res["hitstop_frozen_delta_deg"] = 0.0
    res["hitstop_window"] = [HIT, HIT + HOLD]
    res["hitstop_present"] = bool(2 <= steps + 1 <= 4)

    # 7) **可取消帧**：f10 有 marker，且该帧姿态确在**回收路径**上（夹在命中与架势之间）。
    markers = {m.name: int(m.frame) for m in action.pose_markers}
    res["markers"] = markers
    end_reach = reach_series[-1]
    on_path = (markers.get("CANCEL") == CANCEL
               and end_reach < reach_series[CANCEL] < reach_series[HIT])
    res["cancel_reach_mm"] = round(reach_series[CANCEL], 1)
    res["cancel_pose_on_recovery_path_ok"] = bool(on_path)

    # 8) **位移极小**：骨盆世界 XY 行程 ≤30 mm（清单原文）。
    span = max(math.hypot(p.x - pelvis[0].x, p.y - pelvis[0].y)
               for p in pelvis) * 1000.0
    net = math.hypot(pelvis[-1].x - pelvis[0].x,
                     pelvis[-1].y - pelvis[0].y) * 1000.0
    res["pelvis_xy_span_mm"] = round(span, 2)
    res["pelvis_xy_net_mm"] = round(net, 3)
    res["pelvis_forward_peak_mm"] = round(
        min(p.y for p in pelvis) * 1000.0, 2)
    res["pelvis_small_move_ok"] = bool(span <= 30.0)

    # 9) **脚钉死**（全程踝世界行程 ≤3 mm）+ 贴地。
    travel = {}
    for side in ("L", "R"):
        base = ANKLE_REST[side]
        travel[side] = max((Vector(ankles[i][side]) - base).length
                           for i in range(len(ankles))) * 1000.0
    res["feet_pinned_mm"] = {k: round(v, 3) for k, v in travel.items()}
    res["feet_pinned_ok"] = bool(all(v <= 3.0 for v in travel.values()))

    lows = [min(sole[i]["L"], sole[i]["R"]) for i in range(len(sole))]
    res["sole_min_mm"] = round(min(lows) * 1000.0, 2)
    res["sole_max_mm"] = round(max(lows) * 1000.0, 2)
    res["ground_contact_ok"] = bool(-2.0 <= min(lows) * 1000.0 <= 6.0)
    res["z_off_mm"] = {"L": 0.0, "R": 0.0}
    res["planted_z_off_reuse"] = ("A13 的 z_off 不沿用 —— 本支膝弯几乎不动（±3°），"
                                  "实测鞋底本就在 −2~+6，加常数反而破末帧逐位对齐")

    # 10) **六段力量传导**：位移全非零 + 时序 t_髋 ≤ t_肩 ≤ t_手（±1 帧）。
    ranges, peaks = {}, {}
    for segment, bones in SEGMENTS.items():
        ranges[segment] = round(_euler_range(samples, bones), 3)
        peaks[segment] = _peak_frame(samples, bones)[0]
    res["power_chain_ranges_deg"] = ranges
    res["power_chain_peak_frames"] = peaks
    timing = (peaks["hip"] <= peaks["shoulder"] + 1
              and peaks["shoulder"] <= peaks["hand"] + 1)
    res["power_chain_timing_ok"] = bool(timing)
    res["power_chain_scale"] = "出拳量级：时序判据（不是 A10 的蹬地尺子）"
    res["power_chain_ok"] = bool(timing
                                 and all(v >= 0.5 for v in ranges.values()))

    # 11) **收招不许瞬停**：末 6 帧最大欧拉增量单调收敛。
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

    # 11b) 出拳末帧 vs 收招首帧 —— `windup_fast_ok` 的物理依据，必须落进报告。
    #      跑 1 就死在这：出拳末帧 22.13 < 收招首帧 22.84 ⟹ 峰值跑到 f8。
    def _step_deg(index):
        before, after = samples[index]["euler"], samples[index + 1]["euler"]
        worst = 0.0
        for name in set(before) | set(after):
            ea = before.get(name, (0.0, 0.0, 0.0))
            eb = after.get(name, (0.0, 0.0, 0.0))
            worst = max(worst, max(abs(a - b) for a, b in zip(ea, eb)))
        return worst

    res["recover_first_step_deg"] = round(_step_deg(HIT + HOLD), 3)
    res["strike_peak_leads_recover_deg"] = round(
        peak_val - res["recover_first_step_deg"], 3)
    res["no_teleport_budget_left_deg"] = round(25.0 - peak_val, 3)

    # 12) IK 到位 / 腿可达余量。
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

    # 13) 膝：**只做体检不做门禁**（清单「膝不要动」是"别故意屈膝"）。
    bend = CR.knee_series(arm, action, frames)
    res["knee_bend_span_deg"] = {s: round(max(b[s] for b in bend)
                                          - min(b[s] for b in bend), 2)
                                 for s in ("L", "R")}
    res["knee_bend_note"] = "体检项：轻拳是上身动作，膝只随骨盆前送的 IK 被动改变"

    # 14) 末帧那一步（用动画本身量，不经"应用路径"的中间态 —— A13 的教训）。
    #     键必须在 `anim_lib.PROBE_TAILS` ∪ `PROBE_BONES` 里：肘的位置取
    #     `upperarm.L.tail`（= 肘关节），`forearm.L` 只有 head 被采样、没有 `.tail`。
    last_step = {}
    for name in ("hand.L.tail", "hand.R.tail", "upperarm.L.tail"):
        last_step[name] = round((Vector(samples[-1][name])
                                 - Vector(samples[-2][name])).length * 1000.0, 2)
    res["last_step_move_mm"] = last_step
    res["last_step_pull_mm"] = res["last_step_move_mm"]["hand.L.tail"]
    res["last_step_move_ok"] = bool(all(v <= 40.0 for v in last_step.values()))

    # 15) 攻击元数据登记。
    res["hit_point_m"] = [round(v, 4) for v in samples[HIT]["hand.L.tail"]]
    res["hit_point_from_sternum_mm"] = [
        round((fist_l[HIT][i] - sternum[HIT][i]) * 1000.0, 1) for i in range(3)]
    res["antic_frame"] = ANTIC_END
    res["hit_frame"] = HIT
    res["cancel_frame"] = CANCEL
    res["hitstop_frame_span"] = [HIT, HIT + HOLD]
    return res


# =============================================================== 主流程
def main():
    global ANKLE_REST, E_GUARD, E_STRIKE, IDLE_POSE

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("LIGHT01_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ---- 定盘数：一律从 `Idle_01@0` 成品姿态读，不手抄（A13 第 0 号教训）。
    IDLE_POSE = I1.idle_pose(arm, 0.0)
    ANKLE_REST = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                  for side in ("L", "R")}
    E_GUARD = {b: tuple(math.degrees(v)
                        for v in arm.pose.bones[b].rotation_euler)
               for b in ARM6}
    sternum0 = Vector(A.bone_world(arm, "neck", "head"))
    fist0 = Vector(A.bone_world(arm, "hand.L", "tail"))
    A.report("LIGHT01_IDLE_TRUTH", {
        "ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]]
                     for s in ANKLE_REST},
        "front_hand": "L",
        "guard_fist_mm": [round(v * 1000.0, 1) for v in fist0],
        "guard_reach_mm": round((sternum0.y - fist0.y) * 1000.0, 1),
        "guard_arm_euler_deg": {k: [round(x, 3) for x in v]
                                for k, v in E_GUARD.items()},
        "note": "前脚 L（踝 y −169.6 vs +140.4）⟹ 前手 L，与清单预判一致",
    })

    # ---- 命中帧的手臂欧拉：在**命中帧躯干**上 aim 出来，再折到离 guard 最近的一族。
    strike_trunk = trunk_pose(HIT)
    strike_trunk.update(A.FIST)
    A.apply_pose(arm, strike_trunk)
    raw_strike = {}
    for bone in ARM6:
        raw_strike[bone] = A.aim_bone(arm, bone, STRIKE_DIRS[bone])
    E_STRIKE = {b: JS._unwrap_xyz(E_GUARD[b], raw_strike[b]) for b in ARM6}
    max_y = max(abs(E_STRIKE[b][1]) for b in ARM6)
    worst_delta = max(max(abs(E_STRIKE[b][i] - E_GUARD[b][i]) for i in range(3))
                      for b in ARM6)
    A.report("LIGHT01_STRIKE_TRUTH", {
        "strike_arm_euler_deg": {k: [round(x, 2) for x in v]
                                 for k, v in E_STRIKE.items()},
        "euler_delta_from_guard_deg": {
            b: [round(E_STRIKE[b][i] - E_GUARD[b][i], 2) for i in range(3)]
            for b in ARM6},
        "worst_component_delta_deg": round(worst_delta, 2),
        "max_abs_euler_y_deg": round(max_y, 2),
        "y_health_ok": bool(max_y < 45.0),
        "predicted_peak_step_deg_out_6": round(
            worst_delta * (1.0 - (1.0 - 1.0 / HIT) ** ARM_POW), 2),
        "predicted_recover_first_step_deg": round(
            worst_delta * (2.0 / (CLOCK_END - HIT)
                           - 1.0 / (CLOCK_END - HIT) ** 2), 2),
        "limit_deg": 25.0,
        "note": ("|Y| < 45° ⟹ 不需换等价族；前臂 rz 的 131.6° 是全支 no_teleport 的预算来源，"
                 "6 帧必须近乎匀速才装得下（见文件头第 1 件）"),
    })

    # ---- 正式生成。首末帧整帧取 `Idle_01@0`（见 `idle_frame_pose` 的说明）。
    JS._PREV_EULER.clear()
    for name, value in IDLE_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    del TARGETS[:]
    del TRACE[:]

    keyframes = [(0, IDLE_POSE)]
    for frame in range(1, TOTAL):
        keyframes.append((frame, build_pose(arm, frame, record=True)))
    final, adjusted = idle_frame_pose(arm, JS._PREV_EULER)
    _record_trace(arm, TOTAL, final)
    keyframes.append((TOTAL, final))
    A.report("LIGHT01_LAST_FRAME", {
        "adjusted_bones": adjusted,
        "threshold_deg": 8.0,
        "note": "末尾整帧取 Idle_01@0 成品；只在欧拉表示离 f17 >8° 时折等价族",
    })

    arm_y = {b: max(abs(row["euler"][b][1]) for row in TRACE) for b in ARM6}
    A.report("LIGHT01_ARM_EULER", {
        "max_abs_euler_y_deg": round(max(arm_y.values()), 2),
        "per_bone_y_deg": {k: round(v, 1) for k, v in arm_y.items()},
        "note": "逐分量插欧拉（不读骨骼、无反馈）；|Y| 只作万向节锁健康度体检",
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "普通攻击",
        "note": ("轻拳1 前手直拳：clock 0~6 肘 143°→13.7° 加速伸出（峰值步长在末帧），"
                 "躯干/肩带反向预备 + 上臂 rz 反向偏移造「拳略后收」（收肘做不到，见文件头 1c），"
                 "f6 命中（共线比 ≥0.92）、f6~f7 冻结 2 帧、f7~f18 单调衰减收回护体架势"),
        "antic_frame": ANTIC_END,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HIT + HOLD - HIT + 1,
        "root_motion_m": [0.0, 0.0],
        "hitstop_span": [HIT, HIT + HOLD],
        "motion_clock_hold_frames": HOLD,
        "link_prev": "Idle_01@0（首帧逐位相等）",
        "link_next": "Idle_01@0（末帧逐位相等）→ B02 Light_02 后手横拳",
        "power_chain_scale_note": "出拳量级：时序判据 t_髋 ≤ t_肩 ≤ t_手（非 A10 蹬地尺子）",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.set_hitstop(action, HIT, HIT + HOLD)
    A.add_markers(action, {
        "GUARD": 0, "ANTIC": 1, "ANTIC_END": ANTIC_END,
        "HIT": HIT, "HITSTOP_END": HIT + HOLD,
        "RECOV": HIT + HOLD, "CANCEL": CANCEL, "END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta)
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
    report.update(light_assertions(arm, action, samples, idle_mats, sole,
                                   ankles, reach, target_err))
    report["meta"] = meta
    report["skipped_gates"] = sorted(
        k for k, v in report.items() if v is None and k.endswith("_ok"))
    failed = sorted(k for k, v in report.items()
                    if (k.endswith("_ok") or k == "no_teleport")
                    and v is not True and v is not None)
    report["failed"] = failed
    A.report("LIGHT01_REPORT", report)

    if not SKIP_RENDER:
        LIGHT_SIDE = ("side", (4.8, 0.0, 0.98), (0.0, 0.0, 0.98), 2.60,
                      (780, 1100))
        LIGHT_FRONT = ("front", (0.0, -5.2, 0.98), (0.0, 0.0, 0.98), 2.60,
                       (760, 1180))
        LIGHT_3Q = ("three_quarter", (3.4, -3.8, 1.15), (0.0, 0.0, 0.98), 2.60,
                    (780, 1100))
        A.render_pose_sheet(arm, action,
                            [0, 1, 3, ANTIC_END, HIT, HIT + HOLD, CANCEL, 14,
                             TOTAL], "light01", views=(LIGHT_SIDE,))
        A.render_pose_sheet(arm, action, [0, HIT, TOTAL], "light01",
                            views=(LIGHT_FRONT,))
        A.render_pose_sheet(arm, action, [HIT], "light01", views=(LIGHT_3Q,))
        A.save_project()
        A.export_glb(arm)
    print("LIGHT01_DONE failed=%s" % failed)

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
    A.report("LIGHT01_TRACE_DETAIL", detail)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("LIGHT01_FAILURE " + traceback.format_exc())
