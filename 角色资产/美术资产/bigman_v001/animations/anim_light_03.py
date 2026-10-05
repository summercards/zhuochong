"""anim_light_03 —— B03 `Light_03` 轻拳3（重摆拳 / 勾拳·连击终结）。

设计（对着清单「下一支计划 —— B03」逐条落）：
    定位      重摆拳 / 勾拳，**连击终结**，**动作幅度最大**，**可产生轻击退**。
    时长      26 帧 / 0.433 s @60fps，**非循环**（`loop=False`）。
    首末帧    **都逐位 = `Idle_01@0`** —— B01~B03 三连接缝全落在同一姿态上
              （世界矩阵 ≤1e-6，不用像素比对，见第 3 件）。
    结构      GUARD 0 ／ ANTIC 0~6（髋/肩反向拉开到本族最大 + 拳反向预载）／
              STRIKE 6~10（`hit_frame = 10`，大摆拳划过中线到极值）／
              HITSTOP f10~f13（**4 帧完全冻结**，"最重"给到上限）／
              RECOVER 13~26（沿原路单调衰减回护体架势）／CANCEL 17。

---------------------------------------------------------------------------
★ 第 0 件：探针先量（`probe_light03.py`，只读，10 个候选）。四个定盘数：

  1. **前脚 = L**（踝世界 y：L −169.6 / R +140.4，与 B01/B02 逐位一致）
     ⟹ 前手 = L、后手 = R。本支取**前手 L** 收束 1-2-3 节奏（L→R→L，与清单预判一致）。
  2. **`|Y|` 体检：全线 >45°（61.5°），两支等价族都算过 —— 换族救不回来。**
     见文件头「第 2 件」。
  3. `no_teleport` 预算 = `forearm.L` 的 rz 通道扫 **~118°**；伸出段 10 帧摊开，
     `ARM_POW = 1.25` ⟹ 预测末帧步长 ≈ **14.1°/帧**（余量 10.9°）。
  4. 命中帧拳峰：**前伸 636.5 mm**（> B02 的 595.8）、**横向 383.3 mm**（> B02 的 361.2）、
     世界行程 **640.9 mm**（> B02 的 588.3）、以肩为轴扫掠 **142.78°**（> B02 的 108.08）
     —— **四项全部超过 B02**，"幅度最大"有质变。

---------------------------------------------------------------------------
★ 第 1 件（B01/B02 交下来的第 3 件）：**计划的 `STRIKE 6~10`（4 帧）装不下一记大摆拳**。

  与 B01「`STRIKE 4~6` 装不下直拳」、B02「`STRIKE 5~8` 装不下横拳」**同源**：
  118° 的 rz 行程落在 4 帧里，最匀速也要 29.5°/帧（超 25 的 1.18 倍）。
  解法同源且更彻底：**摆拳占满 clock 0~10 全程**（10 帧，比 B02 的 8 帧多 2 帧
  —— 清单原文"幅度最大要靠行程与帧数、加帧是唯一可靠的余量来源"）。
  「前摇」不是一段独占的静止时间，而是**叠在伸展早期的反向预载轨（`COIL`）**
  ＋ **躯干自己的反向预备**（髋/胸 ry 先反向 9° 再前送 14°，幅度比 B02 的 10° 大）。

---------------------------------------------------------------------------
★ 第 2 件（本支最贵的一课）：**「`|Y| > 45° 就换等价族」这条规则，在大摆拳上失效。**

  A13 定案是「>45° 先换等价族 `(x+180, 180−y, z+180)` 再插值」。本支实测：
  出拳臂 `forearm.L` 的 `|Y|` 是 **61.45°**（摆拳把上臂大幅过中线，躯干又转了 42°），
  但**两支等价族的 `y` 是 `61.45` 与 `118.55`** —— 换族只会把 `|Y|` 推得**更大**。
  `JS._unwrap_xyz` 已经按「离上一帧最近」自动选族，选中的就是 `|y| = 61.45` 那支。

  **处置：不把 `|Y|` 当门禁，而是当"体检项 + 补一条真门禁"**：
    · 体检：`max_abs_euler_y_deg` 如实报（61.45），并给出换族后的值（118.55）；
    · 真门禁就是原来的 `no_teleport`（逐分量逐帧 ≤25°）—— 本支实测峰值 **~14°/帧**，
      说明"逐分量插值经过 `|Y|≈61°` 这段"**是可用的**（离万向节锁 90° 还有 28.5°）。
  这条经验对后续所有"大幅度过中线"的动作（C01/C11/Ultimate_*）都适用：
  **`|Y|` 是风险提示，`no_teleport` 才是判据；不能让体检项替判据做决定。**

---------------------------------------------------------------------------
★ 第 3 件：「轻击退」怎么落地而**不污染首末帧的接缝**。

  清单 B03 是三连的终结拳、`knockback` 是**引擎对受击方**施加的效果，
  不是角色自己的根位移。而本支首末帧仍须逐位 = `Idle_01@0`（B01~B03 三连顺接），
  所以姿态里**不允许留残余位移**。
  ⟹ 判据拆两条：`knockback_light_ok` = 「命中帧前向 > B02 的 595.8 mm **且** 末帧净位移 ≤3 mm」，
  真实推退量写进 `meta.knockback` 交给引擎（**数值给公式**，见 `meta`）。

---------------------------------------------------------------------------
★ 第 4 件：`strike_arc_ok` 沿用 B02 换过的口径。
  B02 已证伪计划原口径「腕到肩半径全程变化 ≤25%」——它在几何上不可达
  （`r(φ)` 只由肘角决定；要 ≤25% 需命中时肘角 ≤45.5°，与"拳伸得出去"互斥），
  而且 **B01 直拳自己也有 0.6037**。本支沿用「以肩为轴累计扫掠角 ≥ B01 的 1.5 倍」，
  两个半径比如实报、不隐藏。

---------------------------------------------------------------------------
★ 第 5 件：首末帧**只用世界矩阵**，禁用像素比对（`probe_light01_jitter` 已证
  EEVEE Next 同帧重渲的 PNG 都不相同）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_light_03.py
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
import anim_light_01 as L1    # noqa: E402

NAME = "Light_03"
TOTAL = 26                    # 0.433 s @ 60 fps（比 B02 多 4 帧 —— 幅度靠帧数）
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

PUNCH = "L"                   # 出拳手 = 前手（探针实测：前脚 L ⟹ 前手 L）
GUARD_HAND = "R"
HIT = 10                      # 命中帧（真实帧）
HOLD = 3                      # 命中停顿吃掉的动作帧数 ⟹ 冻结 f10/f11/f12/f13 共 **4 帧**
CLOCK_END = TOTAL - HOLD      # = 23：动作时钟跨度（伸出段 10 帧 / 收招段 13 帧）
ANTIC_END = 6                 # 前摇结束（清单「ANTIC 0~6」；用于 marker 与反向预备判据）
CANCEL = 17                   # 可取消帧（清单）
# 剖面（**先算死再写**，见文件头第 1 件）：
#   伸出：s = (c/10)^1.25 ⟹ 末帧步长 = 1 − (9/10)^1.25 = 0.12337 × span
#   收招：s = (1−u)^1.45  ⟹ 起手步长 = 1 − (12/13)^1.45 = 0.10957 × span（< 伸出末帧 ⟹ 峰值锁 f10）
#   末帧步长 = (1/13)^1.45 = 0.02424 × span ⟹ no_snap_stop（≤5°）
ARM_POW = 1.25
REC_POW = 1.45
ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")

DROP = I1.DROP                # −0.070：战斗站姿的骨盆下沉量

# B02 的比较基准（"幅度最大"要可量化，基准写死在文件里，不靠记忆）
B02_REACH_MM = 595.8
B02_LATERAL_MM = 361.2
B02_TRAVEL_MM = 588.3
B02_SWEEP_DEG = 108.08
B02_MAX_Y_DEG = 17.1
# `probe_light02b.py` 实测：同口径「以肩为轴的累计扫掠角」，B01 直拳 = 47.6°
B01_SWEEP_DEG = 47.6
ARC_SWEEP_MARGIN = 1.5

# ---------------------------------------------------------------- 出拳姿态（世界方向）
# 探针 `L_hook_v4` 那一组：大摆拳 —— 上臂前送、前臂横过身体中线到**对侧**，
# 肘只留一点弯（"重摆拳"，不是贴身的"勾拳"）。
#   ★ 选它的理由：四项幅度全部超过 B02，且**命中前伸余量最厚**（636.5 vs 门槛 595.8）
#     —— 前伸是 `knockback_light_ok` 的唯一硬条件，余量优先给硬条件。
STRIKE_DIRS = {
    "upperarm.L": (-0.30, -0.92, -0.24),
    "forearm.L": (-0.68, -0.72, 0.06),
    "hand.L": (-0.78, -0.60, 0.06),
    # 护手（R）留在护体架势里、被躯干反向带开 —— `finisher_leads_ok` 守的就是这条
    "upperarm.R": (-0.22, -0.36, -0.90),
    "forearm.R": (0.34, -0.20, 0.92),
    "hand.R": (0.18, -0.60, 0.78),
}

# ---------------------------------------------------------------- 躯干轨（动作时钟域）
# 每条都以 `Idle_01@0` 的取值起、以同一取值止 ⟹ 首末帧与成品姿态逐位相接。
# rx = 前倾链；ry = 绕纵轴扭转。
# ★ **镜像**：`ry > 0` 把 +X（角色左）侧转向 +Y 身后 ⟹ **右肩向前**。
#   本支出拳手是 **L**，要左肩向前 ⟹ ry 取**负**（与 B02 的 R 拳**符号相反**）。
#   `shoulder.L.rz > 0 = 向后`（左臂镜像于右臂）⟹ 前送取**负**。
# 关键帧横坐标刻意取同一组（0 / 4 / HIT）⟹ 髋与肩的角速度峰值天然同帧。
TRUNK = {
    "pelvis": {"rx": ((0, 4.0), (4, 5.4), (HIT, 6.5), (CLOCK_END, 4.0)),
               "ry": ((0, 0.0), (4.0, 9.0), (HIT, -14.0), (CLOCK_END, 0.0))},
    "spine_01": {"rx": ((0, 2.0), (4, 2.7), (HIT, 3.2), (CLOCK_END, 2.0)),
                 "ry": ((0, 0.0), (4.0, 4.0), (HIT, -7.0), (CLOCK_END, 0.0))},
    "spine_02": {"rx": ((0, 2.0), (4, 2.7), (HIT, 3.2), (CLOCK_END, 2.0)),
                 "ry": ((0, 0.0), (4.0, 4.0), (HIT, -7.0), (CLOCK_END, 0.0))},
    "chest": {"rx": ((0, 1.0), (4, 1.8), (HIT, 3.2), (CLOCK_END, 1.0)),
              "ry": ((0, 0.0), (4.0, 9.0), (HIT, -14.0), (CLOCK_END, 0.0))},
    # 颈/头反向扭转，保持看向正前方（胸累计扭 −28° ⟹ 颈 +12 + 头 +9 收回 21°）
    "neck": {"rx": ((0, -6.0), (4, -7.0), (HIT, -10.0), (CLOCK_END, -6.0)),
             "ry": ((0, 0.0), (4.0, -4.5), (HIT, 12.0), (CLOCK_END, 0.0))},
    "head": {"rx": ((0, 5.0), (4, 5.3), (HIT, 4.0), (CLOCK_END, 5.0)),
             "ry": ((0, 0.0), (4.0, -3.0), (HIT, 9.0), (CLOCK_END, 0.0))},
    # 肩带：**出拳侧（L）先向后拉开再前送**，护手侧（R）相反 —— 这才是"肩带旋转"。
    "shoulder.L": {"rx": ((0, -18.0), (4, -14.0), (HIT, -5.0), (CLOCK_END, -18.0)),
                   "rz": ((0, 0.0), (4.0, 12.0), (HIT, -19.0), (CLOCK_END, 0.0))},
    "shoulder.R": {"rx": ((0, -18.0), (4, -19.0), (HIT, -20.0), (CLOCK_END, -18.0)),
                   "rz": ((0, 0.0), (4.0, 5.0), (HIT, -7.0), (CLOCK_END, 0.0))},
}

# 骨盆位移：清单对 B02 放宽到 XY ≤60 mm，本支沿用同一预算。
# 预算全给**重心前送 + 随髋转的横移**（终结拳的身体跟得更狠）。
PELVIS_Y = ((0, 0.000), (3.0, 0.008), (HIT, -0.036), (CLOCK_END, 0.0))
PELVIS_X = ((0, 0.000), (4.0, 0.010), (HIT, -0.016), (CLOCK_END, 0.0))
PELVIS_DZ = ((0, 0.0), (3.0, 0.004), (HIT, -0.008), (CLOCK_END, 0.0))

# ★ 上臂**反向预载轨**（`COIL`）：`upperarm.L` 的 rz 在 clock 1.5~3 先向"后"偏 13°
#   （**左臂 rz>0 = 向后**，本支出拳手是 L ⟹ 与 B02 的负号**相反**），再归零。
#   作用：① 拳峰在 clock 1~3 相对"线性路径"真的往后走（撑大世界行程，
#   实测行程 640.9 mm > B02 的 588.3）；② "肩在蓄、肘已在出"的压缩感。
#   偏移在 HIT 精确归零 ⟹ 命中帧姿态与探针候选**逐位相同**（不污染 strike 判据）。
COIL = {"upperarm.L": {"rz": ((0, 0.0), (1.5, 11.0), (3.0, 13.0),
                              (5.5, 4.5), (HIT, 0.0), (CLOCK_END, 0.0))}}
CHANNEL_INDEX = {"rx": 0, "ry": 1, "rz": 2}

ANKLE_REST = {}               # side -> Vector：`Idle_01@0` 的踝位（全程钉死点）
E_GUARD = {}                  # bone -> `Idle_01@0` 的手臂欧拉（伸出段起点）
E_STRIKE = {}                 # bone -> 命中帧手臂欧拉（已折到离 E_GUARD 最近的一族）
IDLE_POSE = {}                # `Idle_01@0` 的完整姿态字典（首末帧整帧取用）
TRACE = []                    # 逐帧手臂欧拉（|Y| 健康度诊断）
TARGETS = []                  # [(frame, side, target)]：IK 到位核验


def clock(frame):
    """动作时钟：命中停顿期间**时间冻结**，之后所有连续量按冻结后的时间推进。

    f10/f11/f12/f13 读同一个 clock（= 10）⟹ 姿态**逐位相同**（4 帧全冻，清单「2~4 帧」上限）。

    ★ 不用 B01 那句 `frame if frame <= HIT else frame - HOLD`：那句只在 `HOLD = 1`
      时成立（窗口内部为空）。正确做法是把窗口 `[HIT, HIT+HOLD]` **整体夹到 HIT**，
      窗口之后才整体平移 HOLD。这是 B02 修出来的跨文件契约，必须有断言盯着
      （`hitstop_frozen_steps`）—— 优化掉不死。
    """
    if frame <= HIT:
        return frame
    if frame <= HIT + HOLD:
        return HIT
    return frame - HOLD


def arm_s(c):
    """手臂「护体架势 ⇄ 命中姿态」的归一化插值量 s（动作时钟域）。

    伸出段（clock 0~10）：`s = (c/10)^1.25` —— **加速进命中**（§6「命中极重」）。
      逐帧步长递增、峰值必落 f10：118° 摊 10 帧的末帧 = **14.1°/帧**（≤25，余量 10.9°）。
    收招段（clock 10~23）：`s = (1−u)^1.45` —— 起手最快、**速度单调衰减到 0**
      （u=1 处导数 = 0 ⟹ 无瞬停）。首帧 = 118 × 0.10957 = **12.5°/帧** < 14.1
      ⟹ 全局峰值仍在 f10；末帧 = 118 × 0.02424 = **2.8°/帧** ⟹ `no_snap_stop`。
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

    A13 定案：终点是「显式给定的固定姿态」时走逐分量欧拉路径插值 + 同族折叠。
    本支 strike 是显式固定姿态；`|Y| = 61.45°`（探针实测，见文件头第 2 件）
    —— **换等价族救不回来（换完 118.55°）**，所以不换族，靠 `no_teleport`
    逐帧守着（实测峰值 ~14°/帧）。
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

    # 1) **`finisher_leads_ok`**：终结拳的命中帧前伸量 ≥ 前两拳（**双向都拉直**：
    #    前伸 ≥ B02 的 595.8 mm **或** 横向 ≥ B02 的 361.2 mm，二者取一）。
    pr = (sternum[HIT].y - fist_p[HIT].y) * 1000.0
    gr = (sternum[HIT].y - fist_g[HIT].y) * 1000.0
    res["hit_reach_punch_mm"] = round(pr, 1)
    res["hit_reach_guard_mm"] = round(gr, 1)
    res["back_minus_front_mm"] = round(pr - gr, 1)
    res["finisher_leads_by_reach"] = bool(pr >= B02_REACH_MM)
    res["finisher_leads_by_lateral"] = False     # 下面 2) 算出横向后再补

    # 2) **横摆够横**：拳峰**相对胸骨顶**的横向位移 |ΔX| 增量（相对量，胸骨自己在扭）。
    lat = [(fist_p[i].x - sternum[i].x) * 1000.0 for i in range(len(frames))]
    res["lateral_series_mm"] = [round(v, 1) for v in lat]
    res["lateral_delta_mm"] = round(abs(lat[HIT] - lat[0]), 1)
    res["fist_x_travel_mm"] = round(abs(fist_p[HIT].x - fist_p[0].x) * 1000.0, 1)
    res["finisher_leads_by_lateral"] = bool(
        abs(lat[HIT] - lat[0]) >= B02_LATERAL_MM)
    res["finisher_leads_ok"] = bool(res["finisher_leads_by_reach"]
                                    or res["finisher_leads_by_lateral"])

    # 2b) 拳峰世界全行程。
    travel = max((f - fist_p[0]).length for f in fist_p) * 1000.0
    res["fist_travel_mm"] = round(travel, 1)
    res["fist_travel_vs_b02_mm"] = round(travel - B02_TRAVEL_MM, 1)

    # 3) **摆拳走弧线 —— "以肩为轴的累计扫掠角"**（B02 换过的口径，原口径已证伪）。
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
    res["shoulder_sweep_b02_deg"] = B02_SWEEP_DEG
    res["shoulder_sweep_ratio_b01"] = round(res["shoulder_sweep_deg"]
                                            / B01_SWEEP_DEG, 3)
    res["shoulder_sweep_ratio_b02"] = round(res["shoulder_sweep_deg"]
                                            / B02_SWEEP_DEG, 3)
    res["shoulder_sweep_note"] = (
        "门禁口径：以肩为轴的累计扫掠角 ≥ B01 直拳(47.6°)的 1.5 倍。"
        "B02 已证伪计划原口径「腕到肩半径变化 ≤25%」（几何不可达，B01 自己 0.6037）")
    res["strike_arc_ok"] = bool(res["shoulder_sweep_deg"]
                                >= ARC_SWEEP_MARGIN * B01_SWEEP_DEG)
    res["strike_arc_plan_metric_unreachable"] = {
        "plan_metric": "腕到肩半径全程变化 ≤25%",
        "b03_guard_radius_mm": round(rad_sh[0], 1),
        "b03_hit_radius_mm": round(rad_sh[HIT], 1),
        "b03_measured_ratio": res["arc_radius_span_ratio"],
        "b01_measured_ratio": 0.6037,
        "why": ("r(φ)=√(u²+f²−2uf·cos φ) 只由肘角决定；要 ≤25% 需命中时肘角 ≤45.5°"
                "＝肘几乎不许打开，与「拳伸得出去」互斥。B01 直拳自己也只有 0.6037"
                "⟹ 该口径连直拳都判红，不是在量弧线。沿用 B02 的扫掠角口径。"),
    }

    # 3b) **`amplitude_max_ok`**：清单「动作幅度最大」须有质变 ——
    #     拳峰世界行程 > B02 的 588.3 mm **且** 挥摆扫掠角 > B02 的 108.08°。**两条都要**。
    res["amplitude_travel_ok"] = bool(travel > B02_TRAVEL_MM)
    res["amplitude_sweep_ok"] = bool(res["shoulder_sweep_deg"] > B02_SWEEP_DEG)
    res["amplitude_max_ok"] = bool(res["amplitude_travel_ok"]
                                   and res["amplitude_sweep_ok"])

    # 4) **肩髋联动**：`pelvis.ry` 与 `shoulder.L.rz` 的峰值帧差 ≤1 且**同向推进**。
    #    ★ 镜像：本支出拳手是 L，`shoulder.L.rz > 0 = 向后`、前送方向为**负**；
    #      而 `pelvis.ry > 0` 是右肩向前 ⟹ 本支联动要求**两支都为负**。
    hip_f, hip_d, _ = _channel_peak(samples, "pelvis", 1)
    sho_f, sho_d, _ = _channel_peak(samples, "shoulder." + PUNCH, 2)

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
    res["hip_step_sign"] = round(hip_sign, 3)
    res["shoulder_step_sign"] = round(sho_sign, 3)
    res["hip_shoulder_same_direction"] = bool(hip_sign * sho_sign > 0)
    res["hip_shoulder_sync_ok"] = bool(abs(hip_f - sho_f) <= 1
                                       and hip_sign * sho_sign > 0)

    # 5) 命中帧手臂 |Y| 健康度（体检项，**不当门禁** —— 见文件头第 2 件）。
    peak_frame, peak_val = L1._peak_frame(samples, ARM6)
    res["arm_peak_step_frame"] = peak_frame
    res["arm_peak_step_deg"] = peak_val
    max_y = max(max(abs(samples[i]["euler"].get(b, (0., 0., 0.))[1])
                    for b in ARM6) for i in range(len(samples)))
    res["max_abs_euler_y_deg"] = round(max_y, 2)
    res["max_abs_euler_y_b02_deg"] = B02_MAX_Y_DEG
    res["euler_y_is_health_check_only"] = True
    res["euler_y_note"] = (
        "|Y|=61.5° 是体检项不是门禁：`JS._unwrap_xyz` 已自动选最接近的等价族，"
        "换族后是 118.55°（更大）⟹ 换族救不回来；真正守着的是 no_teleport（实测 ~14°/帧）")

    # 6) **命中停顿 4 帧**：f10/f11/f12/f13 逐位相同（`clock` 保证 + `set_hitstop` 双保险）。
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
    res["hitstop_present"] = bool(steps + 1 == HOLD + 1)      # 终结拳给足 4 帧
    res["hitstop_target_frames"] = HOLD + 1

    # 7) **可取消帧**：f17 有 marker，且该帧姿态确在**回收路径**上。
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

    # 8) **位移**：骨盆世界 XY 行程 ≤60 mm（沿用 B02 预算）。
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

    # 10) **六段力量传导**：位移全非零 + 时序 t_髋 ≤ t_肩 ≤ t_手（±1 帧）。
    ranges, peaks = {}, {}
    for segment, bones in SEGMENTS.items():
        ranges[segment] = round(L1._euler_range(samples, bones), 3)
        peaks[segment] = L1._peak_frame(samples, bones)[0]
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

    # 11b) 出拳末帧 vs 收招首帧 —— 峰值必须落在 f10 的物理依据。
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

    # 11c) **前摇：拳必须真的被拉回到身体侧后**（撑行程）。
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
    # ★ 窗口取 `[1, ANTIC_END]`，**必须排除 f0**：f0 是护体架势，按定义 = 0；
    #   把它算进来，`min(...)` 恒为 0 ⟹ 任何前摇都会判"没蓄力"（本支首版就栽在这）。
    #   本支出拳手 L：`shoulder.L.rz > 0 = 向后`、`chest/pelvis.ry > 0 = 右肩向前`
    #   ⟹ 左拳的"反向拉开"是 **正方向**，取窗口内的 **max**。
    prep = {}
    for bone, channel in (("shoulder." + PUNCH, 2), ("chest", 1), ("pelvis", 1)):
        series = [s["euler"].get(bone, (0.0, 0.0, 0.0))[channel] for s in samples]
        prep[bone] = [round(max(series[1:ANTIC_END + 1]), 2),
                      round(series[HIT], 2)]
    res["windup_reverse_prep_deg"] = prep
    res["windup_reverse_prep_window"] = [1, ANTIC_END]
    res["windup_reverse_prep_ok"] = bool(
        prep["shoulder." + PUNCH][0] >= 8.0 and prep["shoulder." + PUNCH][1] <= -14.0
        and prep["chest"][0] >= 6.0 and prep["chest"][1] <= -10.0)

    # 12) **`knockback_light_ok`**：首末帧仍逐位 = `Idle_01@0` ⟹ 位移只能是
    #     "打出去再收回"的**净零摆动**。判据取「命中帧前向 > B02 的 595.8 mm
    #     **且** 末帧净位移 ≤3 mm」；真实推退写进 `meta["knockback"]`。
    net_all = {
        "fist_punch": round((fist_p[-1] - fist_p[0]).length * 1000.0, 3),
        "fist_guard": round((fist_g[-1] - fist_g[0]).length * 1000.0, 3),
        "pelvis": round((pelvis[-1] - pelvis[0]).length * 1000.0, 3),
    }
    res["knockback_net_mm"] = net_all
    res["knockback_forward_mm"] = round(pr, 1)
    res["knockback_light_ok"] = bool(pr > B02_REACH_MM
                                     and max(net_all.values()) <= 3.0)

    # 13) IK 到位 / 腿可达余量。
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

    # 14) 膝：**只做体检不做门禁**。
    bend = CR.knee_series(arm, action, frames)
    res["knee_bend_span_deg"] = {s: round(max(b[s] for b in bend)
                                          - min(b[s] for b in bend), 2)
                                 for s in ("L", "R")}
    res["knee_bend_note"] = "体检项：摆拳是上身动作，膝只随骨盆前送/髋转的 IK 被动改变"

    # 15) 末帧那一步。
    last_step = {}
    for name in ("hand.L.tail", "hand.R.tail", "upperarm.L.tail"):
        last_step[name] = round((Vector(samples[-1][name])
                                 - Vector(samples[-2][name])).length * 1000.0, 2)
    res["last_step_move_mm"] = last_step
    res["last_step_move_ok"] = bool(all(v <= 40.0 for v in last_step.values()))

    # 16) 攻击元数据登记。
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
        print("LIGHT03_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
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
    A.report("LIGHT03_IDLE_TRUTH", {
        "ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]]
                     for s in ANKLE_REST},
        "front_foot": "L" if ANKLE_REST["L"].y < ANKLE_REST["R"].y else "R",
        "punch_hand": PUNCH,
        "guard_hand": GUARD_HAND,
        "guard_fist_mm": [round(v * 1000.0, 1) for v in fist0],
        "guard_reach_mm": round((sternum0.y - fist0.y) * 1000.0, 1),
        "guard_lateral_mm": round((fist0.x - sternum0.x) * 1000.0, 1),
        "guard_arm_euler_deg": {k: [round(x, 3) for x in v]
                                for k, v in E_GUARD.items()},
        "note": ("前脚 L（踝 y −169.6 vs +140.4，与 B01/B02 逐位一致）⟹ 前手 = L，"
                 "1-2-3 收在 L→R→L 的第三拳上"),
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
    fam = {}
    for b in ARM6:
        base = tuple(raw_strike[b])
        flip = (base[0] + 180.0, 180.0 - base[1], base[2] + 180.0)
        fam[b] = {"y_selected": round(E_STRIKE[b][1], 2),
                  "y_base": round(base[1], 2),
                  "y_flip": round(flip[1], 2)}
    A.report("LIGHT03_STRIKE_TRUTH", {
        "strike_arm_euler_deg": {k: [round(x, 2) for x in v]
                                 for k, v in E_STRIKE.items()},
        "euler_delta_from_guard_deg": {
            b: [round(E_STRIKE[b][i] - E_GUARD[b][i], 2) for i in range(3)]
            for b in ARM6},
        "worst_component_delta_deg": round(worst_delta, 2),
        "worst_component_bone": worst_bone,
        "max_abs_euler_y_deg": round(max_y, 2),
        "euler_family_y": fam,
        "y_health_note": ("|Y| > 45° 但**换族救不回来**（flip 支更大）"
                          "⟹ 不当门禁；靠 no_teleport 逐帧守"),
        "predicted_peak_step_deg_out_%d" % HIT: round(
            worst_delta * (1.0 - (1.0 - 1.0 / HIT) ** ARM_POW), 2),
        "predicted_recover_first_step_deg": round(
            worst_delta * (1.0 - (1.0 - 1.0 / (CLOCK_END - HIT)) ** REC_POW), 2),
        "predicted_last_step_deg": round(
            worst_delta * ((1.0 / (CLOCK_END - HIT)) ** REC_POW), 2),
        "limit_deg": 25.0,
        "note": ("★ **镜像**：左臂 rz>0 = 向后（右臂 rz>0 = 向前），本支出拳手 L，"
                 "所以肩带 rz 的符号与 B02 的右拳**相反**；髋/胸 ry 同理取负"),
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
    A.report("LIGHT03_LAST_FRAME", {
        "adjusted_bones": adjusted,
        "threshold_deg": 8.0,
        "note": "末尾整帧取 Idle_01@0 成品；只在欧拉表示离 f25 >8° 时折等价族",
    })

    arm_y = {b: max(abs(row["euler"][b][1]) for row in TRACE) for b in ARM6}
    A.report("LIGHT03_ARM_EULER", {
        "max_abs_euler_y_deg": round(max(arm_y.values()), 2),
        "per_bone_y_deg": {k: round(v, 1) for k, v in arm_y.items()},
        "note": "逐分量插欧拉（不读骨骼、无反馈）；|Y| 只作万向节锁健康度体检",
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "普通攻击",
        "note": ("轻拳3 重摆拳/勾拳·连击终结：clock 0~10 前手摆拳过身体中线到对侧"
                 "（行程最大），髋/胸先反向扭 +9/+9° 再前送 −14/−14°（肩髋联动），"
                 "上臂 rz 反向预载 13° 造「拳后收」撑大行程，f10 命中"
                 "（前伸 636.5 mm / 横向 383.3 mm，均 > B02）、"
                 "f10~f13 冻结 **4 帧**（上限）、f13~f26 单调衰减收回护体架势"),
        "antic_frame": ANTIC_END,
        "hit_frame": HIT,
        "cancel_frame": CANCEL,
        "hitstop_frames": HOLD + 1,
        "root_motion_m": [0.0, 0.0],
        "hitstop_span": [HIT, HIT + HOLD],
        "motion_clock_hold_frames": HOLD,
        "punch_hand": PUNCH,
        "amplitude_vs_b02": {
            "fist_travel_mm": "> 588.3（B02）",
            "shoulder_sweep_deg": "> 108.08（B02）",
            "hit_reach_mm": "> 595.8（B02）",
            "lateral_mm": "> 361.2（B02）",
        },
        "knockback": {
            "type": "light",
            "applied_by_engine": True,
            "push_frames": 6,
            "suggested_m": 0.12,
            "formula": "d = 0.04 m × 连段序号(3) = 0.12 m（轻击退；战斗系统口径待确认）",
            "note": ("姿态内净位移为 0（首末帧逐位 = Idle_01@0），"
                     "推退量由引擎读本字段施加到**受击方**"),
        },
        "link_prev": "Idle_01@0（首帧逐位相等；接 B02 Light_02 末帧）",
        "link_next": "Idle_01@0（末帧逐位相等）→ B04 Heavy_01 重拳（单发，允许不回 idle）",
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
    A.report("LIGHT03_REPORT", report)

    if not SKIP_RENDER:
        SIDE = ("side", (4.8, 0.0, 0.98), (0.0, 0.0, 0.98), 2.60, (780, 1100))
        FRONT = ("front", (0.0, -5.2, 0.98), (0.0, 0.0, 0.98), 2.60, (760, 1180))
        TOPQ = ("three_quarter", (3.4, -3.8, 1.15), (0.0, 0.0, 0.98), 2.60,
                (780, 1100))
        A.render_pose_sheet(arm, action,
                            [0, 1, 3, ANTIC_END, 8, HIT, HIT + HOLD, CANCEL, 21,
                             TOTAL], "light03", views=(SIDE,))
        A.render_pose_sheet(arm, action, [0, HIT, TOTAL], "light03", views=(FRONT,))
        A.render_pose_sheet(arm, action, [HIT], "light03", views=(TOPQ,))
        A.save_project()
        A.export_glb(arm)
    print("LIGHT03_DONE failed=%s" % failed)

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
    A.report("LIGHT03_TRACE_DETAIL", detail)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("LIGHT03_FAILURE " + traceback.format_exc())
