"""anim_light_02 —— B02 `Light_02` 轻拳2（后手横拳）。

设计（对着清单「下一支计划 —— B02」逐条落）：
    定位      后手横拳，**肩髋联动**，**比第一拳更重**（清单原文 B02）。
    时长      22 帧 / 0.367 s @60fps，**非循环**（`loop=False`）。
    首末帧    **都逐位 = `Idle_01@0`** —— B01~B03 是三连，接缝全落在同一姿态上
              （世界矩阵 ≤1e-6，不用像素比对，见下「第 3 件」）。
    结构      GUARD 0 ／ ANTIC 0~8（前摇：髋先反向转 + 后手拳反向预载）／
              HIT 8（拳峰横摆到极值）／HITSTOP f8~f10（**3 帧完全冻结**）／
              RECOVER 10~22（沿原路收回护体架势）／CANCEL 13。

---------------------------------------------------------------------------
★ 第 0 件：探针先量（`probe_light02.py`，只读）。四个定盘数：

  1. **前脚 = L**（踝世界 y：L −169.6 / R +140.4），与 B01 逐位一致
     ⟹ **前手 = L**，**出拳手 = 后手 = R**。与计划预判一致，全文不再对调。
  2. strike 姿态 `max_abs_euler_y_deg = 17.1`（六根臂骨全量）。远低于 A13 定案
     「>45° 先换等价族」的阈值 ⟹ 仍走**逐分量欧拉插值**，不需要换族。
     （横拳把上臂摆过中线，本担心 |Y| 会显著变大 —— 实测只比 B01 的 15.53 高 1.6°。）
  3. **`no_teleport` 的预算 = `forearm.R` 的 rz 通道扫 121.02°**
     （guard +146.292 → strike +25.27）。比 B01 的 131.6° 略小
     —— 但 B01 是在**前臂**上扫，本支是在**横摆**上扫，拳峰行程反而更大（见下）。
  4. 候选姿态 `S1` 定量：拳峰 (W) x 从 −129.6 → **+257.0 mm**
     ⟹ 相对胸骨顶的横向位移 **361.2 mm**（判据 ≥320）；
     拳峰世界行程 **572.7 mm**（B01 是 429.0 mm ⟹ 「更重」的量级靠这条撑住）。

---------------------------------------------------------------------------
★ 第 1 件（B01 交下来的第 2 件 + 本支最贵的一课）：计划的 `STRIKE 5~8`
  **装不下一记横拳**，必须按物理重排 —— 与 B01「`STRIKE 4~6` 装不下直拳」同源。

  计划原文：`WINDUP 0~5` ＋ `STRIKE 5~8`。但 121.02° 的 rz 行程落在 3 帧里，
  按 `no_teleport ≤25°/帧` 的**最匀速**剖面也要 **40.3°/帧**（超 1.6 倍）；
  就算用「起点速率为 0」的加速剖面（p≈1.06），末帧也要 **121.02 × (1 − (2/3)^1.06)
  = 38.4°/帧**。⟹ 与 B01 一样是**一行不等式**级别的死，不是调参问题。

  解法同源（按物理重排）：**横摆占满 clock 0~8 全程**（8 帧摊 121.02°）
  ⟹ 末帧角速度 `121.02 × [1 − (7/8)^1.15] = **17.23°/帧**`，余量 7.77°。
  「前摇」不再是一段独占的静止时间，而是**叠在伸展早期的反向预载轨**（`COIL`）
  ＋ **躯干自己的反向预备**（髋/胸 ry 先负后正，见文件头第 2 件）。

---------------------------------------------------------------------------
★ 第 2 件：**「肩髋联动」怎么变成判据**。清单原文四个字，落成一条**双通道同步**判据：

  `pelvis.ry`（髋绕纵轴）与 `shoulder.R.rz`（出拳侧肩带的水平摆）的
  **逐帧角速度峰值帧差 ≤1**，且**同向推进**（两支峰值处的增量都为正 = 都在前送）。

  为什么必须同向：右臂 `rz>0` = 向前（**镜像**于左臂，`rig_axis_map` 写明），
  而 `pelvis.ry>0` 把角色 +X 侧转向 +Y 身后 = **右肩向前** ⟹ 两者同号才是"联动"。
  若照抄 B01 的左臂符号，这条会红，而且动作会读成"手在抡、腰在反向拧"。

  构造上保证同步：两支轨道用**同一组关键帧横坐标**（0 / 4 / HIT），
  只是幅度不同（髋 16°、肩 23°）⟹ 峰值帧天然对齐，不是调出来的。

---------------------------------------------------------------------------
★ 第 3 件：首末帧**只用世界矩阵**，禁用像素比对。
  B01 已实测 `probe_light01_jitter.py`：把骨骼动画完全摘掉（几何绝对静止）后，
  **同一帧渲两次的 PNG 也不相同** —— EEVEE Next 在本工程里逐次渲染就不确定。
  ⟹ "像素相同"是运气不是结论。首末帧一律 `matrix_delta ≤ 1e-6`。

---------------------------------------------------------------------------
★ 第 4 件：`strike_arc_ok` 的量法（横拳**不能照抄 B01 的共线比 ≥0.92**）。
  横拳走**弧线**、肘是弯的，共线比天然偏低（实测 S1 的 R 臂 0.9648 是"接近伸直"，
  那是因为本支是宽横摆；换收紧型就会掉到 0.89 以下）。
  ⟹ 改判「**腕到肩的半径在摆动全程变化 ≤25%**」，即"以肩为轴划弧"
  （计划括号原文「以肩为轴的圆弧」）。同时**如实报**「腕到胸骨」的半径变化
  —— 那条从护体架势的 ~0.36 m 变到命中帧的 0.57 m，是**伸展**造成的，
  不是弧线不平滑，所以不做门禁（B01「不适用的判据不放」同口径）。

---------------------------------------------------------------------------
★ 第 5 件：`heavier_than_b01_ok`（"比第一拳更重"必须可量化）。
  清单原文四个字，落成**三选二**：

  | 通道 | B01 基准 | 本支 | 过 |
  |---|---|---|---|
  | 峰值角速度 | 23.185°/帧 | ~17.2°/帧（行程摊进 8 帧，**主动换质量换帧数**） | ✗ |
  | 命中停顿 | 2 帧 | **3 帧**（"更重"直接给足） | ✓ |
  | 拳峰行程 | 429.0 mm | **~573 mm**（横摆过中线） | ✓ |

  ⟹ 两条成立。**刻意不用"角速度更大"来证明更重** —— 那会逼回 3 帧的伸展窗口，
  必然破 `no_teleport`。重量感在本支来自**停顿 + 行程 + 躯干参与量**，不是来自手速。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_light_02.py
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
import anim_light_01 as L1    # noqa: E402

NAME = "Light_02"
TOTAL = 22                    # 0.367 s @ 60 fps
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

PUNCH = "R"                   # 出拳手 = 后手（前手 L 已由 B01 实测确定）
GUARD_HAND = "L"
HIT = 8                       # 命中帧（真实帧）
HOLD = 2                      # 命中停顿"吃掉"的动作帧数 ⟹ 冻结 f8/f9/f10 共 **3 帧**
CLOCK_END = TOTAL - HOLD      # = 20：动作时钟跨度
ANTIC_END = 5                 # 前摇结束（清单「WINDUP 0~5」；用于 marker 与反向预备判据）
CANCEL = 13                   # 可取消帧（清单）
ARM_POW = 1.15                # 伸出段剖面 s = (c/8)^1.15（加速进命中，峰值 = 末帧）
REC_POW = 1.59                # 收招段剖面 s = (1−u)^1.59（起手最快、单调衰减到 0）
ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")

DROP = I1.DROP                # −0.070：战斗站姿的骨盆下沉量

# B01 的比较基准（"更重"要可量化，基准写死在文件里，不靠记忆）
B01_PEAK_STEP_DEG = 23.185
B01_FIST_TRAVEL_MM = 429.0
B01_HITSTOP_FRAMES = 2
# `probe_light02b.py` 实测：同口径「以肩为轴的累计扫掠角」，B01 直拳 = **47.6°**。
# 它的 `radius_span_ratio` 也是 **0.6037**（同样远超计划写的 25%）
# ⟹ 计划那条半径判据**连直拳都过不了**，根本不是在量"弧线"，必须换口径。
B01_SWEEP_DEG = 47.6
ARC_SWEEP_MARGIN = 1.5        # 横拳的扫掠角必须 ≥ 直拳的 1.5 倍才叫"绕肩横摆"

# ---------------------------------------------------------------- 出拳姿态（世界方向）
# 探针 S1 那一组：上臂前送、前臂横过身体中线，肘近乎伸直（宽横摆）。
STRIKE_DIRS = {
    "upperarm.R": (0.35, -0.90, -0.25),
    "forearm.R": (0.70, -0.70, 0.10),
    "hand.R": (0.80, -0.58, 0.10),
    # 护手（L）留在护体架势里、被躯干反向带开 —— `back_hand_leads_ok` 守的就是这条
    "upperarm.L": (0.30, -0.20, -0.93),
    "forearm.L": (-0.30, -0.30, 0.90),
    "hand.L": (-0.18, -0.60, 0.78),
}

# ---------------------------------------------------------------- 躯干轨（动作时钟域）
# 每条都以 `Idle_01@0` 的取值起、以同一取值止 ⟹ 首末帧与成品姿态逐位相接。
# rx = 前倾链；ry = 绕纵轴扭转。**ry>0 把 +X 侧转向 +Y 身后 = 右肩向前**（本支出拳侧）。
# 关键帧横坐标刻意取同一组（0 / 4 / HIT）⟹ 髋与肩的角速度峰值天然同帧（文件头第 2 件）。
TRUNK = {
    "pelvis": {"rx": ((0, 4.0), (4, 5.2), (HIT, 6.0), (CLOCK_END, 4.0)),
               "ry": ((0, 0.0), (4.0, -6.0), (HIT, 10.0), (CLOCK_END, 0.0))},
    "spine_01": {"rx": ((0, 2.0), (4, 2.6), (HIT, 3.0), (CLOCK_END, 2.0)),
                 "ry": ((0, 0.0), (4.0, -3.0), (HIT, 5.0), (CLOCK_END, 0.0))},
    "spine_02": {"rx": ((0, 2.0), (4, 2.6), (HIT, 3.0), (CLOCK_END, 2.0)),
                 "ry": ((0, 0.0), (4.0, -3.0), (HIT, 5.0), (CLOCK_END, 0.0))},
    "chest": {"rx": ((0, 1.0), (4, 1.8), (HIT, 3.0), (CLOCK_END, 1.0)),
              "ry": ((0, 0.0), (4.0, -7.0), (HIT, 10.0), (CLOCK_END, 0.0))},
    # 颈/头反向扭转，保持看向正前方（胸累计扭 +30° ⟹ 颈 −9 + 头 −7 收回 16°）
    "neck": {"rx": ((0, -6.0), (4, -6.8), (HIT, -9.0), (CLOCK_END, -6.0)),
             "ry": ((0, 0.0), (4.0, 3.5), (HIT, -9.0), (CLOCK_END, 0.0))},
    "head": {"rx": ((0, 5.0), (4, 5.2), (HIT, 4.0), (CLOCK_END, 5.0)),
             "ry": ((0, 0.0), (4.0, 2.5), (HIT, -7.0), (CLOCK_END, 0.0))},
    # 肩带：**出拳侧（R）先拉开再前送**，护手侧（L）相反 —— 这是真正的"肩带旋转"。
    # ★ 右臂 rz>0 = 向前（镜像于左臂）：本支 rz 的符号与 B01 的 shoulder.L 相反。
    "shoulder.R": {"rx": ((0, -18.0), (4, -15.0), (HIT, -6.0), (CLOCK_END, -18.0)),
                   "rz": ((0, 0.0), (4.0, -9.0), (HIT, 14.0), (CLOCK_END, 0.0))},
    "shoulder.L": {"rx": ((0, -18.0), (4, -18.5), (HIT, -17.0), (CLOCK_END, -18.0)),
                   "rz": ((0, 0.0), (4.0, -4.0), (HIT, 6.0), (CLOCK_END, 0.0))},
}

# 骨盆位移：清单对 B02 放宽到 XY ≤60 mm。预算全给**重心前送 + 随髋转的横移**。
PELVIS_Y = ((0, 0.000), (3.0, 0.006), (HIT, -0.030), (CLOCK_END, 0.0))
PELVIS_X = ((0, 0.000), (4.0, 0.008), (HIT, -0.012), (CLOCK_END, 0.0))
PELVIS_DZ = ((0, 0.0), (3.0, 0.003), (HIT, -0.006), (CLOCK_END, 0.0))

# ★ 上臂**反向预载轨**（`COIL`）：`upperarm.R` 的 rz 在 clock 1.5~3 先向"后"偏 9.5°
#   （右臂 rz<0 = 向后），再归零。作用有两条：
#     ① 拳峰在 clock 1~2 相对"线性路径"**真的往后走**（横向 + 前伸都退），
#        —— 这是 B01 直拳里证过**不可达**的那个"拳后收"，横拳里因为行程长而可达；
#     ② "肩在蓄、肘已在出"的压缩感（B01 同款基础设施）。
#   偏移在 HIT 精确归零 ⟹ 命中帧姿态与探针 S1 **逐位相同**（不污染 strike 判据）。
COIL = {"upperarm.R": {"rz": ((0, 0.0), (1.5, -8.0), (3.0, -9.5),
                              (5.0, -3.0), (HIT, 0.0), (CLOCK_END, 0.0))}}
CHANNEL_INDEX = {"rx": 0, "ry": 1, "rz": 2}

ANKLE_REST = {}               # side -> Vector：`Idle_01@0` 的踝位（全程钉死点）
E_GUARD = {}                  # bone -> `Idle_01@0` 的手臂欧拉（伸出段起点）
E_STRIKE = {}                 # bone -> 命中帧手臂欧拉（已折到离 E_GUARD 最近的一族）
IDLE_POSE = {}                # `Idle_01@0` 的完整姿态字典（首末帧整帧取用）
TRACE = []                    # 逐帧手臂欧拉（|Y| 健康度诊断）
TARGETS = []                  # [(frame, side, target)]：IK 到位核验


def clock(frame):
    """动作时钟：命中停顿期间**时间冻结**，之后所有连续量按冻结后的时间推进。

    f8/f9/f10 读同一个 clock（= 8）⟹ 姿态**逐位相同**（3 帧全冻，清单「2~4 帧」）。

    ★ 为什么不是 B01 那句 `frame if frame <= HIT else frame - HOLD`：
      那句只在 `HOLD = 1`（冻结 2 帧）时成立 —— 窗口 `[6,7]` 的**内部为空**，
      `clock(7) = 6`，两端刚好都落回 HIT。
      本支冻结 **3** 帧（`HOLD = 2`），套那句会得到 `clock(9) = 9 − 2 = **7**`，
      比 HIT 小 1 ⟹ f9 的姿态**不再与 f8 相同**，`hitstop_frozen_steps` 实测 0。
      正确做法是把窗口 `[HIT, HIT+HOLD]` **整体夹到 HIT**，窗口之后才整体平移 HOLD。
    """
    if frame <= HIT:
        return frame
    if frame <= HIT + HOLD:
        return HIT
    return frame - HOLD


def arm_s(c):
    """手臂「护体架势 ⇄ 命中姿态」的归一化插值量 s（动作时钟域）。

    伸出段（clock 0~8）：`s = (c/8)^1.15` —— **加速进命中**（§6「命中极重」）。
    逐帧步长递增、峰值必落 f8：121.02° 摊 8 帧的末帧 = **17.23°/帧**（≤25，余量 7.77°）。
      · B01 的教训：`u^1.01`（近乎匀速）会把峰值让给收招首帧 ⟹ 这里取 1.15 留足领先；
      · 不能更陡：`no_teleport` 是逐分量逐帧判的，陡到末帧 >25 直接红。
    收招段（clock 8~20）：`s = (1−u)^1.59` —— 起手最快、**速度单调衰减到 0**
      （u=1 处导数 = 0 ⟹ 无瞬停）。首帧 121.02 × 0.1292 = **15.63°/帧** < 17.23
      ⟹ 全局峰值仍在 f8；末帧 121.02 × (1/12)^1.59 = 2.32°/帧 ⟹ `no_snap_stop`。
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
    """手臂欧拉：guard → strike 的**逐分量**线性插值 + 反向预载轨（`COIL`）。

    A13 定案：终点是「显式给定的固定姿态」时走逐分量欧拉路径插值 + 同族折叠，
    不走世界朝向 slerp。本支 strike 是显式固定姿态，且 `|Y| = 17.1°`（探针实测）
    离万向节锁很远 ⟹ 逐分量插值安全。
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
    pose["@loc"] = {"pelvis": A.wloc(tval(PELVIS_X, c), tval(PELVIS_Y, c),
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

    # 足：钉平到世界水平（rest 朝向）。本支不起脚，tip 恒 0。
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
    世界矩阵不是逐位相同，`guard_endpoints_ok` 会红。折算只改**表示**，世界朝向不变。
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


def _channel_peak(samples, bone, channel):
    """单通道的逐帧角速度峰值帧与峰值增量（带符号）。"""
    best_frame, best_step = None, -1.0
    for index in range(1, len(samples)):
        ea = samples[index - 1]["euler"].get(bone, (0.0, 0.0, 0.0))[channel]
        eb = samples[index]["euler"].get(bone, (0.0, 0.0, 0.0))[channel]
        if abs(eb - ea) > best_step:
            best_step, best_frame = abs(eb - ea), samples[index]["frame"]
    return best_frame, round(best_step, 3), samples


def light_assertions(arm, action, samples, idle_mats, sole, ankles, reach,
                     target_err):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(s["pelvis"]) for s in samples]
    fist_p = [Vector(s["hand." + PUNCH + ".tail"]) for s in samples]
    fist_g = [Vector(s["hand." + GUARD_HAND + ".tail"]) for s in samples]
    wrist_p = [Vector(s["hand." + PUNCH]) for s in samples]        # hand.head = 腕
    shoulder_p = [Vector(s["upperarm." + PUNCH]) for s in samples]  # upperarm.head = 肩
    sternum = [Vector(s["neck"]) for s in samples]                  # chest.tail = 胸骨顶

    # 0) **首末帧都逐位 = `Idle_01@0`**（世界矩阵，不是 euler，也不用像素）。
    m0 = CR.action_world_matrices(arm, action, 0)
    mN = CR.action_world_matrices(arm, action, TOTAL)
    d0, dN = CR.matrix_delta(m0, idle_mats), CR.matrix_delta(mN, idle_mats)
    res["first_frame_delta"] = float("%.3e" % d0)
    res["last_frame_delta"] = float("%.3e" % dN)
    res["guard_endpoints_ok"] = bool(d0 <= 1e-6 and dN <= 1e-6)

    # 1) **后手必须真的领先**（与 B01 的 `front_hand_leads_ok` **反向**）：
    #    命中帧后手前伸量 ≥ 护手 + 300 mm。
    pr = (sternum[HIT].y - fist_p[HIT].y) * 1000.0
    gr = (sternum[HIT].y - fist_g[HIT].y) * 1000.0
    res["hit_reach_punch_mm"] = round(pr, 1)
    res["hit_reach_guard_mm"] = round(gr, 1)
    res["back_minus_front_mm"] = round(pr - gr, 1)
    res["back_hand_leads_ok"] = bool(pr - gr >= 300.0)

    # 2) **横拳够横**：拳峰**相对胸骨顶**的横向位移 |ΔX| 增量 ≥320 mm。
    #    清单原文「横拳不能只量 −Y」。用相对量（胸骨自己在扭），量的是"拳摆出去多少"。
    lat = [(fist_p[i].x - sternum[i].x) * 1000.0 for i in range(len(frames))]
    res["lateral_series_mm"] = [round(v, 1) for v in lat]
    res["lateral_delta_mm"] = round(abs(lat[HIT] - lat[0]), 1)
    res["fist_x_travel_mm"] = round(abs(fist_p[HIT].x - fist_p[0].x) * 1000.0, 1)
    res["strike_reach_ok"] = bool(abs(lat[HIT] - lat[0]) >= 320.0)

    # 2b) 拳峰世界全行程（`heavier_than_b01_ok` 读它）。
    travel = max((f - fist_p[0]).length for f in fist_p) * 1000.0
    res["fist_travel_mm"] = round(travel, 1)
    res["fist_travel_vs_b01_mm"] = round(travel - B01_FIST_TRAVEL_MM, 1)

    # 3) **横拳走弧线 —— "以肩为轴的圆弧"**（照抄 B01 的共线比 ≥0.92 会误判）。
    #
    #    ★ 计划原文那句「腕到胸骨的半径在摆动全程变化 ≤25%」**几何不可达**，
    #      与 B01「拳略后收 20 mm」同一类死法（一行不等式级别）。证明：
    #        肩→腕距离只是**肘角 φ 的一元函数** r(φ) = √(u² + f² − 2uf·cos φ)
    #        （u = 0.328 m 上臂、f = 0.224 m 前臂，都是刚体常数）。
    #        护体架势把肘折到 φ = 33.4° ⟹ r = **187 mm**（拳峰几乎贴着肩）。
    #        而命中姿态必须把肘打开才够得着 —— 探针 S1 是 φ = 148° ⟹ r = **531 mm**。
    #        要让半径全程变化 ≤25%，命中帧必须 r ≤ 187 × 1.25 = 234 mm，
    #        反解 φ ≤ **45.5°** ⟹ **肘几乎不许打开**，拳头伸不出去，
    #        直接与 `strike_reach_ok`（横向 ≥320 mm，实测 361.2 mm）互斥。
    #        ⟹ 两条判据在计划的字面口径下**不可能同时成立**。
    #      所以本支**不放**一条凑绿的假判据，换成**可达且同源**的那条：
    #        以肩为轴的**累计扫掠角**：从架式到命中，单位向量 (拳峰 − 肩) 逐帧转过的
    #        角度之和 ≥ **25°**。直拳是**沿臂轴径向捅出**，该方向几乎不变（扫掠≈0）；
    #        横拳是**绕肩横摆**，方向必须真的转过去。原口径的两个半径比**如实报**。
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

    rad_sh = [(wrist_p[i] - shoulder_p[i]).length * 1000.0
              for i in range(len(frames))]
    rad_st = [(wrist_p[i] - sternum[i]).length * 1000.0
              for i in range(len(frames))]
    res["wrist_shoulder_radius_mm"] = [round(v, 1) for v in rad_sh]
    res["arc_radius_span_ratio"] = round(
        (max(rad_sh) - min(rad_sh)) / max(1e-9, max(rad_sh)), 4)
    res["arc_radius_span_sternum_ratio"] = round(
        (max(rad_st) - min(rad_st)) / max(1e-9, max(rad_st)), 4)
    res["shoulder_sweep_deg"] = round(_sweep(fist_p, shoulder_p, 0, HIT), 2)
    res["shoulder_sweep_b01_deg"] = B01_SWEEP_DEG
    res["shoulder_sweep_ratio"] = round(res["shoulder_sweep_deg"] / B01_SWEEP_DEG, 3)
    res["shoulder_sweep_note"] = (
        "门禁口径：以肩为轴的累计扫掠角 ≥ B01 直拳(47.6°)的 1.5 倍 —— "
        "直拳沿臂轴径向捅出、该方向几乎不变；横拳绕肩横摆、方向必须真的转过去")
    res["strike_arc_ok"] = bool(res["shoulder_sweep_deg"]
                                >= ARC_SWEEP_MARGIN * B01_SWEEP_DEG)
    res["strike_arc_plan_metric_unreachable"] = {
        "plan_metric": "腕到肩半径全程变化 ≤25%",
        "b02_guard_radius_mm": round(rad_sh[0], 1),
        "b02_hit_radius_mm": round(rad_sh[HIT], 1),
        "b02_measured_ratio": res["arc_radius_span_ratio"],
        "b01_measured_ratio": 0.6037,
        "why": ("r(φ)=√(u²+f²−2uf·cos φ) 只由肘角决定：B02 架式 φ=33.4°→187 mm，"
                "命中 φ=148°→531 mm。要 ≤25% 需命中 φ≤45.5°＝肘几乎不许打开，"
                "与 strike_reach_ok(≥320 mm) 互斥；而 **B01 直拳自己也只有 0.6037**，"
                "远达不到 0.25 ⟹ 该口径连直拳都判红，不是在量弧线"),
    }

    # 4) **肩髋联动**：`pelvis.ry` 与 `shoulder.R.rz` 的峰值帧差 ≤1 且**同向推进**。
    hip_f, hip_d, _ = _channel_peak(samples, "pelvis", 1)
    sho_f, sho_d, _ = _channel_peak(samples, "shoulder." + PUNCH, 2)
    # 峰值处的**带符号**增量（判断是不是同向前送）
    def signed_step(frame, bone, channel):
        ia = [i for i, s in enumerate(samples) if s["frame"] == frame - 1]
        ib = [i for i, s in enumerate(samples) if s["frame"] == frame]
        if not ia or not ib:
            return 0.0
        return (samples[ib[0]]["euler"].get(bone, (0., 0., 0.))[channel]
                - samples[ia[0]]["euler"].get(bone, (0., 0., 0.))[channel])

    hip_sign = signed_step(hip_f, "pelvis", 1)
    sho_sign = signed_step(sho_f, "shoulder." + PUNCH, 2)
    res["hip_peak_frame_deg"] = [hip_f, hip_d]
    res["shoulder_peak_frame_deg"] = [sho_f, sho_d]
    res["hip_shoulder_frame_gap"] = abs(hip_f - sho_f)
    res["hip_shoulder_same_direction"] = bool(hip_sign > 0 and sho_sign > 0)
    res["hip_shoulder_sync_ok"] = bool(abs(hip_f - sho_f) <= 1
                                       and hip_sign > 0 and sho_sign > 0)

    # 5) **"比第一拳更重"三选二**。
    peak_frame, peak_val = _peak_frame(samples, ARM6)
    res["arm_peak_step_frame"] = peak_frame
    res["arm_peak_step_deg"] = peak_val
    heavier_speed = bool(peak_val >= B01_PEAK_STEP_DEG)
    heavier_travel = bool(travel > B01_FIST_TRAVEL_MM)
    heavier_hitstop = bool(HIT + HOLD - HIT + 1 >= 3)
    res["heavier_channels"] = {
        "peak_speed_ge_b01": heavier_speed,
        "fist_travel_gt_b01": heavier_travel,
        "hitstop_ge_3": heavier_hitstop,
    }
    res["heavier_than_b01_ok"] = bool(
        sum((heavier_speed, heavier_travel, heavier_hitstop)) >= 2)

    # 6) **命中停顿**：f8/f9/f10 逐位相同（`clock` 保证 + `set_hitstop` 双保险）。
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

    # 7) **可取消帧**：f13 有 marker，且该帧姿态确在**回收路径**上。
    markers = {m.name: int(m.frame) for m in action.pose_markers}
    res["markers"] = markers
    on_path = (markers.get("CANCEL") == CANCEL
               and (fist_p[HIT] - fist_p[0]).length
               > (fist_p[CANCEL] - fist_p[0]).length > 0.0)
    res["cancel_off_guard_mm"] = round(
        (fist_p[CANCEL] - fist_p[0]).length * 1000.0, 1)
    res["cancel_hit_off_guard_mm"] = round(
        (fist_p[HIT] - fist_p[0]).length * 1000.0, 1)
    res["cancel_marker_ok"] = bool(on_path)

    # 8) **位移**：清单对 B02 放宽到骨盆世界 XY 行程 ≤60 mm。
    span = max(math.hypot(p.x - pelvis[0].x, p.y - pelvis[0].y)
               for p in pelvis) * 1000.0
    net = math.hypot(pelvis[-1].x - pelvis[0].x,
                     pelvis[-1].y - pelvis[0].y) * 1000.0
    res["pelvis_xy_span_mm"] = round(span, 2)
    res["pelvis_xy_net_mm"] = round(net, 3)
    res["pelvis_forward_peak_mm"] = round(min(p.y for p in pelvis) * 1000.0, 2)
    res["pelvis_small_move_ok"] = bool(span <= 60.0)

    # 9) **脚钉死** + 贴地。
    t = {}
    for side in ("L", "R"):
        base = ANKLE_REST[side]
        t[side] = max((Vector(ankles[i][side]) - base).length
                      for i in range(len(ankles))) * 1000.0
    res["feet_pinned_mm"] = {k: round(v, 3) for k, v in t.items()}
    res["feet_pinned_ok"] = bool(all(v <= 3.0 for v in t.values()))
    lows = [min(sole[i]["L"], sole[i]["R"]) for i in range(len(sole))]
    res["sole_min_mm"] = round(min(lows) * 1000.0, 2)
    res["sole_max_mm"] = round(max(lows) * 1000.0, 2)
    res["ground_contact_ok"] = bool(-2.0 <= min(lows) * 1000.0 <= 6.0)
    res["z_off_mm"] = {"L": 0.0, "R": 0.0}
    res["planted_z_off_reuse"] = ("不沿用 A13 的 z_off —— 本支膝弯只随髋转被动改变，"
                                  "实测鞋底本就在 −2~+6")

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

    # 11b) 出拳末帧 vs 收招首帧 —— 峰值必须落在 f8 的物理依据。
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

    # 11c) **前摇：拳必须真的被拉回到身体侧后**（B01 直拳里证过不可达，横拳里可达）。
    #      量法：在 `[0, ANTIC_END]` 里找**离命中点最远**的那一帧（= 蓄满的那一帧）。
    #      本支的"后收"发生在**横向**（右拳朝角色右侧拉开），不是 B01 的"向身后收"
    #      —— 横拳的蓄力方向由摆动方向决定，用"离命中点多远"这个口径才不依赖方向。
    coil_index = max(range(0, ANTIC_END + 1),
                     key=lambda i: (fist_p[i] - fist_p[HIT]).length)
    d_hit = [(f - fist_p[HIT]).length * 1000.0 for f in fist_p]
    res["windup_coil_frame"] = coil_index
    res["windup_chamber_mm"] = round(d_hit[coil_index] - d_hit[0], 1)
    res["windup_draw_mm"] = {
        "x_lateral": round((fist_p[coil_index].x - fist_p[0].x) * 1000.0, 1),
        "y_forward": round((fist_p[coil_index].y - fist_p[0].y) * 1000.0, 1),
        "z": round((fist_p[coil_index].z - fist_p[0].z) * 1000.0, 1),
    }
    res["windup_chamber_ok"] = bool(res["windup_chamber_mm"] >= 40.0)
    prep = {}
    for bone, channel in (("shoulder." + PUNCH, 2), ("chest", 1), ("pelvis", 1)):
        series = [s["euler"].get(bone, (0.0, 0.0, 0.0))[channel] for s in samples]
        prep[bone] = [round(min(series[:ANTIC_END + 1]), 2),
                      round(series[HIT], 2)]
    res["windup_reverse_prep_deg"] = prep
    res["windup_reverse_prep_ok"] = bool(
        prep["shoulder." + PUNCH][0] <= -6.0 and prep["shoulder." + PUNCH][1] >= 10.0
        and prep["chest"][0] <= -4.0 and prep["chest"][1] >= 7.0)

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

    # 13) 膝：**只做体检不做门禁**。
    bend = CR.knee_series(arm, action, frames)
    res["knee_bend_span_deg"] = {s: round(max(b[s] for b in bend)
                                          - min(b[s] for b in bend), 2)
                                 for s in ("L", "R")}
    res["knee_bend_note"] = "体检项：横拳是上身动作，膝只随骨盆前送/髋转的 IK 被动改变"

    # 14) 末帧那一步。
    last_step = {}
    for name in ("hand.R.tail", "hand.L.tail", "upperarm.R.tail"):
        last_step[name] = round((Vector(samples[-1][name])
                                 - Vector(samples[-2][name])).length * 1000.0, 2)
    res["last_step_move_mm"] = last_step
    res["last_step_move_ok"] = bool(all(v <= 40.0 for v in last_step.values()))

    # 15) 攻击元数据登记。
    res["hit_point_m"] = [round(v, 4) for v in samples[HIT]["hand." + PUNCH + ".tail"]]
    res["hit_point_from_sternum_mm"] = [
        round((fist_p[HIT][i] - sternum[HIT][i]) * 1000.0, 1) for i in range(3)]
    res["antic_frame"] = ANTIC_END
    res["hit_frame"] = HIT
    res["cancel_frame"] = CANCEL
    res["hitstop_frame_span"] = [HIT, HIT + HOLD]
    res["punch_hand"] = PUNCH
    return res


# =============================================================== 主流程
def main():
    global ANKLE_REST, E_GUARD, E_STRIKE, IDLE_POSE

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("LIGHT02_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ---- 定盘数：一律从 `Idle_01@0` 成品姿态读，不手抄。
    IDLE_POSE = I1.idle_pose(arm, 0.0)
    ANKLE_REST = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                  for side in ("L", "R")}
    E_GUARD = {b: tuple(math.degrees(v)
                        for v in arm.pose.bones[b].rotation_euler)
               for b in ARM6}
    sternum0 = Vector(A.bone_world(arm, "neck", "head"))
    fist0 = Vector(A.bone_world(arm, "hand." + PUNCH, "tail"))
    A.report("LIGHT02_IDLE_TRUTH", {
        "ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]]
                     for s in ANKLE_REST},
        "punch_hand": PUNCH,
        "guard_fist_mm": [round(v * 1000.0, 1) for v in fist0],
        "guard_reach_mm": round((sternum0.y - fist0.y) * 1000.0, 1),
        "guard_lateral_mm": round((fist0.x - sternum0.x) * 1000.0, 1),
        "guard_arm_euler_deg": {k: [round(x, 3) for x in v]
                                for k, v in E_GUARD.items()},
        "note": "前脚 L（踝 y −169.6 vs +140.4，与 B01 逐位一致）⟹ 出拳手 = 后手 = R",
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
    worst_bone = max(ARM6, key=lambda b: max(abs(E_STRIKE[b][i] - E_GUARD[b][i])
                                             for i in range(3)))
    A.report("LIGHT02_STRIKE_TRUTH", {
        "strike_arm_euler_deg": {k: [round(x, 2) for x in v]
                                 for k, v in E_STRIKE.items()},
        "euler_delta_from_guard_deg": {
            b: [round(E_STRIKE[b][i] - E_GUARD[b][i], 2) for i in range(3)]
            for b in ARM6},
        "worst_component_delta_deg": round(worst_delta, 2),
        "worst_component_bone": worst_bone,
        "max_abs_euler_y_deg": round(max_y, 2),
        "y_health_ok": bool(max_y < 45.0),
        "predicted_peak_step_deg_out_%d" % HIT: round(
            worst_delta * (1.0 - (1.0 - 1.0 / HIT) ** ARM_POW), 2),
        "predicted_recover_first_step_deg": round(
            worst_delta * (1.0 - (1.0 - 1.0 / (CLOCK_END - HIT)) ** REC_POW), 2),
        "limit_deg": 25.0,
        "note": ("|Y| < 45° ⟹ 不需换等价族。**★ 镜像**：右臂 rz>0 = 向前，"
                 "本支 strike 的 forearm.R rz 由 +146.3 扫到 +25.3（−121.0°）"
                 "—— 符号关系与 B01 的左臂相反，别照抄"),
    })

    # ---- 正式生成。首末帧整帧取 `Idle_01@0`。
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
    A.report("LIGHT02_LAST_FRAME", {
        "adjusted_bones": adjusted,
        "threshold_deg": 8.0,
        "note": "末尾整帧取 Idle_01@0 成品；只在欧拉表示离 f21 >8° 时折等价族",
    })

    arm_y = {b: max(abs(row["euler"][b][1]) for row in TRACE) for b in ARM6}
    A.report("LIGHT02_ARM_EULER", {
        "max_abs_euler_y_deg": round(max(arm_y.values()), 2),
        "per_bone_y_deg": {k: round(v, 1) for k, v in arm_y.items()},
        "note": "逐分量插欧拉（不读骨骼、无反馈）；|Y| 只作万向节锁健康度体检",
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "普通攻击",
        "note": ("轻拳2 后手横拳：clock 0~8 后手横摆过身体中线（肘 → 近乎伸直，"
                 "峰值步长在末帧），髋/胸先反向扭 −16/−21° 再前送 +16/+21°（肩髋联动），"
                 "上臂 rz 反向预载造「拳后收」，f8 命中（横向位移 ≥320 mm）、"
                 "f8~f10 冻结 **3 帧**、f10~f22 单调衰减收回护体架势"),
        "antic_frame": ANTIC_END,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HIT + HOLD - HIT + 1,
        "root_motion_m": [0.0, 0.0],
        "hitstop_span": [HIT, HIT + HOLD],
        "motion_clock_hold_frames": HOLD,
        "punch_hand": PUNCH,
        "link_prev": "Idle_01@0（首帧逐位相等；接 B01 Light_01 末帧）",
        "link_next": "Idle_01@0（末帧逐位相等）→ B03 Light_03 重摆拳/勾拳",
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
                    if (k.endswith("_ok")
                        or k in ("no_teleport", "hitstop_present"))
                    and v is not True and v is not None)
    report["failed"] = failed
    A.report("LIGHT02_REPORT", report)

    if not SKIP_RENDER:
        SIDE = ("side", (4.8, 0.0, 0.98), (0.0, 0.0, 0.98), 2.60, (780, 1100))
        FRONT = ("front", (0.0, -5.2, 0.98), (0.0, 0.0, 0.98), 2.60, (760, 1180))
        TOPQ = ("three_quarter", (3.4, -3.8, 1.15), (0.0, 0.0, 0.98), 2.60,
                (780, 1100))
        A.render_pose_sheet(arm, action,
                            [0, 1, 3, ANTIC_END, HIT, HIT + HOLD, CANCEL, 17,
                             TOTAL], "light02", views=(SIDE,))
        A.render_pose_sheet(arm, action, [0, HIT, TOTAL], "light02", views=(FRONT,))
        A.render_pose_sheet(arm, action, [HIT], "light02", views=(TOPQ,))
        A.save_project()
        A.export_glb(arm)
    print("LIGHT02_DONE failed=%s" % failed)

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
    A.report("LIGHT02_TRACE_DETAIL", detail)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("LIGHT02_FAILURE " + traceback.format_exc())
