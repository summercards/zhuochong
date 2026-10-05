"""anim_jump_up —— A11 `Jump_Up` 空中上升。

设计（对着清单「下一支计划 —— A11」逐条落）：
    定位      空中上升，四肢略收、保持攻击准备（清单原文 A11 条目）。
    接 A10    首帧**逐位**等于 `Jump_Start@36`（世界矩阵 max_delta = 0）。
    时长      12 帧 / 0.200 s @60fps，**非循环**。
    结构      RISE 0~9：骨盆按弹道继续上升到顶点（竖速 31.44 → ~0 mm/帧），
                     双腿继续收（膝弯 +12° 量级），双臂从前上高位向体侧略收。
              APEX 9~12：速率趋零（顶点），躯干稳定，为 A12 的"展开找落点"留起始姿态。
    原地      清单 §0.4：Jump 属"普通移动"，**不给 Root Motion**（`root_motion_m=[0,0]`）。

---------------------------------------------------------------------------
★ 本支第 0 件事：清单下一支计划里的「16~18 帧」是算错的，我先验后改。

计划原文写：「A10 的 6 帧爆发把骨盆推到 0.920 m、初速 4.50 m/s、apex 1.033 m，
于是"上升"的剩余量只有 0.178 m。如果 A11 老老实实"接着往上升"，它只有 0.18 m 的
行程 —— 按 60 fps 弹道，从 4.50 m/s 到 0 只需 **16 帧**（0.267 s），而 A10 已经
用掉了 16 帧（f20~36）。⟹ A11 的可行长度就是 **16~18 帧**」。

前半段是对的，最后一步错了：**"从 4.50 m/s 到 0 只需 16 帧"里的这 16 帧，正是
A10 已经用掉的 f20~36**。实测（不心算，见运行日志 `JUMPUP_BALLISTIC`）：

    g = 9.8/60² = 0.00272222 m/帧²
    t_apex = 0.075 / g = **27.551 帧**（距离地 f20）
    A10 用掉        = 36 − 20 = **16 帧**
    **剩余到顶点**  = 27.551 − 16 = **11.551 帧**   ← 不是 16~18

所以按弹道走，A11 只能是 **11~12 帧**。取 12 帧的理由是**离散峰**：
z(27) = 1.952750、z(28) = 1.952889、z(29) = 1.950306 —— 逐帧采样后
**顶点落在 t=28**（即 A11 的 f12），于是"末帧即顶点、末帧速率 0.14 mm/帧"
是**弹道自己给的**，不需要夹取、不需要造一个假的平顶。
选 16 帧会让 f13~16 落到下降段上，直接和 `no_downward_ok`（上升段里
不许混进下降）互斥 —— 那才是真的错段。

---------------------------------------------------------------------------
本支的六条关键做法

1. **首帧不重算，直接读 A10 已验收的成品。**
   `aim_carry` 是有状态的 **carry 接力**（基准 = 上一帧已达成朝向），
   单跑一次 `build_pose(36)` 得到的朝向与"从 0 连跑到 36"**不同**。
   要逐位复现只有两条路：重放 0~36 整条链，或**直接读存盘 Action 在 f36 的取值**。
   本支走第二条：`A.reset_pose` → 挂上 `Jump_Start` → `frame_set(36)` → 读回
   全部骨的 euler / location（非关键帧的骨被 reset 归零，不会读到脏值）。
   同一份读取里把六根臂骨的**世界四元数**取出来当 A11 的 carry 起点，
   于是 f0→f1 是**同一个接力**，不是两次独立求解。

2. **骨盆 z 不是"再升一点"，是 A10 解析弹道的直接续写。**
   `z(f) = TAKEOFF_PELVIS_Z + v₀·(16+f) − ½g(16+f)²`，与 A10 共用
   `JS.TAKEOFF_PELVIS_Z / JS.TAKEOFF_SPEED / JS.G_PER_FRAME` **同一组常量**
   —— 所以"首帧等于 A10 f36"与"全段是弹道"是**同一件事**，不是两个约束。
   门禁 `rise_ballistic_ok` 拿同一函数回比，误差是浮点级（实测 0.0000 mm）。

3. **收腿量走 `u = 2s − s²`（同 A10 的 `air_u`），逐帧增量单调递减。**
   `du/ds = 2(1−s)` 连续下降到 0 ⟹ `decel_smooth_ok`（末 6 帧角度增量单调收敛）
   是**构造出来的**。绕开 A06 踩坑 4 里"末段切线非零 ⟹ 收招越到后面越快"。

4. **踝目标不是独立轨，是"髋-踝竖距"轨（同 A10 第 3 条）。**
   空中骨盆按弹道走，若踝另有独立轨，两者速率一旦不同就会把腿拉直或拉穿
   （|髋−踝| 有 0.822 m 上限）。这里 VERT(f) 从 A10 的 `JS.VERT_END`
   起算、收到 `VERT_END_A11`，`x/y` 保持 A10 末帧值（踝停在身体正下方）。
   两侧**分开给末值**：交错架势下同一条竖距曲线对两腿的膝角增量不同。

5. **`power_chain_ok` 的尺子必须换。** A10 的判据是「thigh 摆幅 ≥15°、
   shin ≥15°」，那是**蹬地展开**的量（44.7 / 60.4）。A11 在空中、没有地面反力，
   腿的行程只是"略收"：几何上 thigh 只能到 ~7°、shin 到 ~12°
   （解析：VERT 减 50 mm ⟹ 膝弯 +12.3°，其中 thigh 只分到 7.5°）。
   拿 A10 的尺子量必然恒红 —— 与 A06 踩坑 5 / A09 踩坑 1 同源（**尺子选错**）。
   本支按"**每段都有非零关键帧**"（清单 §6 原文）+ 各自的**可见下限**
   （位移 ≥5 mm / 转角 ≥3°）判，判据与实测值一并登记，不放宽、只换对。

6. **roll 搜索范围按 A10 的遗留警告加大。** A10 日志：「`max_abs_euler_y_deg`
   = 62.35 只比安全带（62.0）低 0.35°，下一支若甩臂幅度更大，应当把
   `ROLL_RANGE` 从 120 加到 150（或把 `Y_SAFE` 降到 55）」。本支把两件都做了
   （`ROLL_RANGE = 150`、`Y_SAFE = 58`），因为手臂要从"前上高位"收到体侧、
   与 A10 的甩臂同一量级。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_jump_up.py
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

NAME = "Jump_Up"
TOTAL = 12                    # 0.200 s @ 60 fps（见文件头：剩余弹道只有 11.55 帧）
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

ARM_BONES = JS.ARM_BONES

# ---------------------------------------------------------------- 弹道继承
# A10 末帧距离地（TAKEOFF）的帧数。**不许硬编码 16**：上游改 A10 长度时自动跟随。
BASE_T = JS.TOTAL - JS.T_TAKEOFF
# 顶点（距离地）—— 只用于登记与断言，不参与生成。
T_APEX = JS.TAKEOFF_SPEED / JS.G_PER_FRAME


def pelvis_z(frame):
    """骨盆世界 z（米）—— A10 解析弹道在 A11 帧号上的直接续写。

    A10 在 f20 离地时骨盆 0.920 m、竖速 4.50 m/s；此后严格弹道。
    A11 的 f 对应"距离地 BASE_T + f"帧。
    """
    t = BASE_T + frame
    return (JS.TAKEOFF_PELVIS_Z + JS.TAKEOFF_SPEED * t
            - 0.5 * JS.G_PER_FRAME * t * t)


Z_START = pelvis_z(0)
Z_END = pelvis_z(TOTAL)

# ---------------------------------------------------------------- 收腿（髋-踝竖距，米）
VERT_FROM = dict(JS.VERT_END)             # A10 末帧 {L: 0.690, R: 0.670}
# 末端竖距：L 减 50 mm、R 减 52 mm。解析预估（q≈0.66~0.69 处）：
#   L 0.690→0.640 ⟹ 膝弯 60.4°→72.7°（+12.3°），其中 thigh 分到 7.5°
#   R 0.670→0.618 ⟹ 膝弯 67.2°→79.1°（+11.9°）
# 上限由 `tuck_more_ok`（≥5°）与"略收"的定位共同约束：再收就变成"团身跳"，
# 那是另一支动画的造型。
VERT_END_A11 = {"L": 0.640, "R": 0.618}

# ---------------------------------------------------------------- 躯干（度）
# f0 取值 = A10 末键（`PELVIS_RX[-1][1]` 式取法，不硬编码 → 上游改了自动跟随）。
PELVIS_RX = ((0, JS.PELVIS_RX[-1][1]), (6, 0.1), (TOTAL, 0.3))
SPINE01_RX = ((0, JS.SPINE01_RX[-1][1]), (6, 1.4), (TOTAL, 1.8))
SPINE02_RX = ((0, JS.SPINE02_RX[-1][1]), (6, 1.3), (TOTAL, 1.7))
CHEST_RX = ((0, JS.CHEST_RX[-1][1]), (6, 1.0), (TOTAL, 1.6))
NECK_RX = ((0, JS.NECK_RX[-1][1]), (6, -4.6), (TOTAL, -4.8))
HEAD_RX = ((0, JS.HEAD_RX[-1][1]), (6, 3.8), (TOTAL, 4.0))
SHOULDER_RX = ((0, JS.SHOULDER_RX[-1][1]), (6, -2.0), (TOTAL, -1.0))
# 骨盆水平：接 A10 的 −1.0 mm，收到 0（原地，清单 §0.4）
PELVIS_Y_KEYS = ((0, JS.PELVIS_Y_KEYS[-1][1]), (6, -0.0003), (TOTAL, 0.0))

# ---------------------------------------------------------------- 足尖（度）
# A10 末帧 TIP_END = 12.0；空中脚背略放松到 8°。
TIP_KEYS = ((0, JS.TIP_END), (6, 10.0), (TOTAL, 8.0))

# ---------------------------------------------------------------- 手臂
# "四肢略收、保持攻击准备"：从前上高位（A10 的 ARM_AIR）向 **A01 的护体架势**
# 收 55%。护体架势就是"攻击准备"的现成定义，且它是已被 10 支动画验证过的造型。
ARM_GATHER = 0.55
# roll 限速（度/帧）。见 `jump_up_aim_carry`：roll 是自由 DOF，但不能一帧用完。
# 6°/帧 × 12 帧 = 72° 的扭转预算，足够把 A10 遗留的 28° 一次性甩动摊平。
# 可用 `JU_ROLLRATE` 覆盖（扫参用）。
ROLL_RATE = float(os.environ.get("JU_ROLLRATE", "6.0"))
ARM_READY = {}
MAX_ABS_EULER_Y = 0.0
TARGETS = []                  # 逐帧登记的 (frame, side, target)
TRACE = []                    # 逐帧的臂骨 euler（诊断用）
ANKLE_REST = {}


def build_arm_targets():
    global ARM_READY
    ARM_READY = {k: JS._slerp(JS.ARM_AIR[k], I1.ARM_DIRS[k], ARM_GATHER)
                 for k in ARM_BONES}


def arm_dirs(frame):
    """手臂世界方向：前上高位 →（收）体侧护体架势。

    定时用 `JS._ease_ramp`（梯形速度剖面，两端速度为 0、中段匀速）。
    两端速度为 0 是关键：A10 的 f30~36 手臂是**静止**的（`arm_dirs` 在
    frame > T_SWING_END 后恒等于 ARM_AIR），若本支 f0 就带速度，A10→A11
    接缝上会出现一次速度跳变。
    """
    s = JS._ease_ramp(frame / float(TOTAL))
    return {k: JS._slerp(JS.ARM_AIR[k], ARM_READY[k], s) for k in ARM_BONES}


# =============================================================== 姿态生成
def ankle_target(arm, frame, side):
    """该侧踝的世界目标位置。

    A10 的空中段把踝收在"身体正下方、离髋 VERT"处；本支原样继承，只让 VERT
    继续收。`x / y` 直接取 A10 末帧的落点（= `ANKLE_REST` 的水平分量）。
    """
    rest = ANKLE_REST[side]
    s = frame / float(TOTAL)
    u = 2.0 * s - s * s                 # 同 A10 的 air_u：逐帧增量单调递减
    vert = VERT_FROM[side] + (VERT_END_A11[side] - VERT_FROM[side]) * u
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    return Vector((rest.x, rest.y, hip.z - vert))


def _unwrap_legs(arm, pose):
    """腿骨欧拉解缠：同一世界朝向在 XYZ 的等价族里取离上一帧最近的一支。

    `TURN.leg_to` 内部用 `A.aim_bone`（`rotation_difference` 最小旋转），
    它不保证表示连续；欧拉通道是逐分量插值的，表示跳 = 真闪帧。
    与 A10 对脚做的事情同理，只是这里对 thigh / shin 也做一遍。
    """
    for side in ("L", "R"):
        for prefix in ("thigh.", "shin."):
            name = prefix + side
            raw = tuple(math.degrees(v)
                        for v in arm.pose.bones[name].rotation_euler)
            pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name), raw)
            arm.pose.bones[name].rotation_euler = \
                [math.radians(v) for v in pose[name]]
    bpy.context.view_layer.update()


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
                                  pelvis_z(frame) - 0.900)},
    }
    A.apply_pose(arm, pose)

    # 腿：真双骨 IK（A06/A07/A10 的 `leg_to`）。膝弯方向固定世界 −Y（不转身）。
    for side in ("L", "R"):
        target = ankle_target(arm, frame, side)
        if record:
            TARGETS.append((frame, side, tuple(target)))
        TURN.leg_to(arm, pose, side, target, (0.0, -1.0))
    _unwrap_legs(arm, pose)

    # 足：先钉平到世界水平（rest 朝向），再绕世界 X 叠 tip 角（A10 同路径）。
    tip = TURN.track(TIP_KEYS, frame)
    for side in ("L", "R"):
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        WF.add_world_rx(arm, name, tip)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    pose.update(A.FIST)
    dirs = arm_dirs(frame)
    # carry 接力（基准 = 上一帧已达成朝向）+ roll 分支搜索 + **roll 限速**
    # —— 见文件头第 6 条与 `jump_up_aim_carry`。
    for bone in ARM_BONES:
        pose[bone] = jump_up_aim_carry(arm, bone, dirs[bone], ROLL_RATE)

    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    TRACE.append({
        "frame": frame,
        "euler": {b: tuple(round(v, 2) for v in pose[b]) for b in ARM_BONES},
        "quat": {b: arm.pose.bones[b].matrix.to_quaternion() for b in ARM_BONES},
        "roll": dict(JS.ARM_ROLL),
    })
    return pose


# =============================================================== 读 A10 成品
def capture_start(arm, action, frame):
    """读存盘 Action 在 `frame` 的**完整姿态** + 六根臂骨的世界四元数。

    为什么读而不是重算：`aim_carry` 是有状态的接力，单跑一次 `build_pose(36)`
    与"从 0 连跑到 36"结果不同。读成品既逐位准确，又省掉 36 帧带 roll 搜索的重算。

    `A.reset_pose` 必须先做：非关键帧通道不会被动画系统写值，不归零会读到上一轮
    残留（例如渲染或门禁留下的姿态）。
    """
    A.reset_pose(arm)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()

    pose, locations = {}, {}
    for pose_bone in arm.pose.bones:
        euler = tuple(math.degrees(v) for v in pose_bone.rotation_euler)
        if any(abs(v) > 1e-9 for v in euler):
            pose[pose_bone.name] = euler
        location = tuple(pose_bone.location)
        if any(abs(v) > 1e-9 for v in location):
            locations[pose_bone.name] = location
    if locations:
        pose["@loc"] = locations
    quats = {name: arm.pose.bones[name].matrix.to_quaternion()
             for name in ARM_BONES}
    return pose, quats


# =============================================================== 测量
def _with_action(arm, action):
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    return previous


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


def hip_ankle_vert(arm, action, frame):
    """该帧的"髋-踝竖距"（米）。`PROBE_BONES` 里没有 thigh，只能现量。"""
    previous = _with_action(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    out = {side: A.bone_world(arm, "thigh." + side, "head").z
           - A.bone_world(arm, "foot." + side, "head").z
           for side in ("L", "R")}
    if previous is not None:
        arm.animation_data.action = previous
    return out


# =============================================================== 专属门禁
def jump_up_aim_carry(arm, name, direction, roll_rate):
    """`JS.aim_carry` + **逐帧 roll 限速**。

    ★ 本支最贵的一课（诊断 `JUMPUP_TRACE_DETAIL` 定案）：
    A10 的 roll 搜索是**逐帧独立**选分支的 —— 一旦代价函数越过阈值，
    它就一帧内把 roll 从 0 甩到 −28°。那不是"换了个等价表示"：
    roll 虽然不改骨轴方向，但它**改的是绕骨轴的扭转**，实测同一帧六根臂骨
    的**真世界旋转**全部跳到 29~33°（`no_teleport` 62.49° @ f8 upperarm.L）。
    也就是说 **roll 搜索自己把 A10 想修的"扭转变"重新造了出来**，只是集中在一帧。

    roll 在物理上是自由 DOF（不改方向），但在**时间**上不是自由的：
    它必须以有限速率变化，否则读作一次翻腕闪帧。于是把每帧施加的 roll
    限到 `roll_rate`（度/帧），把一次 28° 的甩动摊成若干帧的连续扭转。
    方向仍然精确落在目标上 —— 动的是滚转，不是判据。
    """
    pose_bone = arm.pose.bones[name]
    before = JS.ARM_QUAT.get(name)
    euler = JS.aim_carry(arm, name, direction)
    after = JS.ARM_QUAT.get(name)
    raw_roll = JS.ARM_ROLL.get(name, 0.0)
    if before is None or after is None or abs(raw_roll) <= roll_rate + 1e-9:
        return euler
    # 把 roll 截到 ±roll_rate，方向（骨轴）不变，只把扭转摊开。
    want = Vector(direction).normalized()
    limited = math.copysign(roll_rate, raw_roll)
    quat = Quaternion(want, math.radians(limited)) @ (
        Quaternion(want, math.radians(-raw_roll)) @ after)
    euler = JS._unwrap_xyz(JS._PREV_EULER.get(name),
                           JS._set_world_quat(arm, name, quat))
    JS.ARM_ROLL[name] = limited
    JS.ARM_QUAT[name] = quat
    return euler


# =============================================================== 专属门禁
def jump_up_assertions(arm, action, samples, start_mats, sole, target_err,
                       end_vert):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [Vector(s["pelvis"]) for s in samples]
    zs = [p.z for p in pelvis]

    # 0) 首帧必须**逐位**等于 `Jump_Start@36`（世界矩阵，不是 euler）。
    mats = CR.action_world_matrices(arm, action, 0)
    delta = CR.matrix_delta(mats, start_mats)
    res["first_frame_delta"] = float("%.3e" % delta)
    res["first_frame_matches_a10_ok"] = delta <= 1e-6

    # 1) **本支最该守的判据**：骨盆 z 逐帧与解析弹道比对（"上升"就是弹道，没有别的物理）。
    err = max(abs(zs[i] - pelvis_z(frames[i])) for i in range(len(frames))) * 1000.0
    res["ballistic_max_err_mm"] = round(err, 4)
    res["rise_ballistic_ok"] = err <= 2.0

    # 2) 上升段里不许混进下降。
    res["monotone_violations"] = [
        frames[i + 1] for i in range(len(zs) - 1) if zs[i + 1] < zs[i] - 1e-12]
    res["no_downward_ok"] = not res["monotone_violations"]

    # 3) **真的到顶点附近**：末帧速率 ≤5 mm/帧（离散顶点恰在末帧，实测 0.14）。
    end_rate = (zs[-1] - zs[-2]) * 1000.0
    res["end_rate_mm_per_frame"] = round(end_rate, 3)
    res["apex_reached_ok"] = abs(end_rate) <= 5.0
    res["start_rate_mm_per_frame"] = round((zs[1] - zs[0]) * 1000.0, 2)
    res["start_rate_mps"] = round((zs[1] - zs[0]) * A.FPS, 3)
    res["rise_mm"] = round((zs[-1] - zs[0]) * 1000.0, 1)
    res["start_pelvis_z_mm"] = round(zs[0] * 1000.0, 1)
    res["end_pelvis_z_mm"] = round(zs[-1] * 1000.0, 1)
    res["apex_remaining_frames_from_a10_end"] = round(T_APEX - BASE_T, 3)

    # 4) **四肢略收**：膝弯比 A10 末帧再多 ≥5°，且单调（不能收着收着又伸直）。
    bend = CR.knee_series(arm, action, frames)
    res["knee_bend_start_deg"] = {s: round(bend[0][s], 2) for s in ("L", "R")}
    res["knee_bend_end_deg"] = {s: round(bend[-1][s], 2) for s in ("L", "R")}
    gain = {s: bend[-1][s] - bend[0][s] for s in ("L", "R")}
    res["tuck_gain_deg"] = {k: round(v, 2) for k, v in gain.items()}
    res["tuck_more_ok"] = all(v >= 5.0 for v in gain.values())
    mono = {s: all(bend[i + 1][s] >= bend[i][s] - 1e-9
                   for i in range(len(bend) - 1)) for s in ("L", "R")}
    res["tuck_monotone"] = mono
    res["tuck_monotone_ok"] = all(mono.values())

    # 5) **"双臂向身体两侧略收"的量化**：拳相对胸骨顶的"上举量"必须降下来。
    #    为什么量相对量而不是绝对高度：骨盆在这一段升了 181 mm，
    #    绝对高度会被躯干上升掩盖，"手臂到底收没收"量不出来（A06 踩坑口径）。
    def fist_raise(sample, side):
        fist = Vector(sample["hand." + side + ".tail"])
        sternum = Vector(sample["chest.tail"])
        return (fist.z - sternum.z) * 1000.0

    raise_start = {s: fist_raise(samples[0], s) for s in ("L", "R")}
    raise_end = {s: fist_raise(samples[-1], s) for s in ("L", "R")}
    lowered = {s: raise_start[s] - raise_end[s] for s in ("L", "R")}
    res["fist_raise_start_mm"] = {k: round(v, 1) for k, v in raise_start.items()}
    res["fist_raise_end_mm"] = {k: round(v, 1) for k, v in raise_end.items()}
    res["fist_lowered_mm"] = {k: round(v, 1) for k, v in lowered.items()}
    res["arms_gather_ok"] = all(v >= 60.0 for v in lowered.values())
    travel = {}
    for side in ("L", "R"):
        points = [Vector(s["hand." + side + ".tail"]) for s in samples]
        travel[side] = max((p - points[0]).length for p in points) * 1000.0
    res["fist_travel_mm"] = {k: round(v, 1) for k, v in travel.items()}
    res["arm_travel_ok"] = all(v >= 100.0 for v in travel.values())

    # 6) 全段离地 —— 通用门禁的贴地窗口 [−2, +6] mm 本支**不适用**，显式登记原因。
    lows = [min(sole[i]["L"], sole[i]["R"]) for i in range(len(sole))]
    res["min_sole_all_mm"] = round(min(lows) * 1000.0, 1)
    res["all_airborne_ok"] = min(lows) * 1000.0 >= 500.0
    res["ground_contact_ok"] = None
    res["ground_contact_skipped_reason"] = \
        "全段离地（鞋底最低 %.1f mm），-2~+6 mm 窗口不适用" % (min(lows) * 1000.0)
    res["no_foot_slide_skipped_reason"] = "全段离地，支撑脚不存在"

    # 7) 踝的离地高度（给 A12 的交接量之一）。
    ank = A.bone_world(arm, "foot.L", "head")
    res["ankle_z_start_mm"] = round(ank.z * 1000.0, 1)

    # 8) IK 是否到位（腿最长 0.822 m，够不到会静默截断）。
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
    #     ★ 尺子说明（文件头第 5 条）：本支在空中、没有地面反力，腿的行程
    #     只是"略收"。A10 的 thigh ≥15° / shin ≥15° 是**蹬地展开**的量，
    #     拿来量"收腿"必然恒红。这里按清单 §6 原文判"每段都有关键帧且非零"，
    #     阈值取"可见"下限（位移 ≥5 mm / 转角 ≥3°），实测值同时登记供审计。
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

    # 12) 给 A12 的交接真值。
    res["end_ankle_mm"] = {
        side: [round(v * 1000.0, 1) for v in samples[-1]["foot." + side]]
        for side in ("L", "R")}
    res["end_vert_mm"] = {side: round(end_vert[side] * 1000.0, 1)
                          for side in ("L", "R")}
    res["vert_design_mm"] = {side: round(VERT_END_A11[side] * 1000.0, 1)
                             for side in ("L", "R")}
    # 顶点之后逐帧增速率 = −g（A12 的起始竖速，mm/帧）。
    res["fall_rate_after_apex_mm_per_frame"] = round(
        -JS.G_PER_FRAME * 1000.0, 3)
    return res


# =============================================================== 主流程
def main():
    global ANKLE_REST, MAX_ABS_EULER_Y

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("JUMPUP_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()
    if JS.NAME not in bpy.data.actions:
        print("JUMPUP_BOOTSTRAP 动画工程缺 Jump_Start，先补跑 A10")
        JS.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ANKLE_REST = A10 用的同一把尺子（Idle_01@0 的 foot.head）。
    I1.idle_pose(arm, 0.0)
    ANKLE_REST = {side: Vector(A.bone_world(arm, "foot." + side, "head"))
                  for side in ("L", "R")}
    A.report("JUMPUP_ANKLE_REST",
             {s: [round(v * 1000.0, 2) for v in ANKLE_REST[s]] for s in ANKLE_REST})

    A.report("JUMPUP_BALLISTIC", {
        "g_per_frame": JS.G_PER_FRAME,
        "takeoff_speed_mm_per_frame": round(JS.TAKEOFF_SPEED * 1000.0, 3),
        "apex_frames_from_takeoff": round(T_APEX, 4),
        "a10_frames_from_takeoff": BASE_T,
        "remaining_frames_to_apex": round(T_APEX - BASE_T, 4),
        "z_start_mm": round(Z_START * 1000.0, 3),
        "z_end_mm": round(Z_END * 1000.0, 3),
        "rise_mm": round((Z_END - Z_START) * 1000.0, 2),
        "hint": "清单下一支计划的 16~18 帧是算错的：剩余只有 11.55 帧，取 12（离散顶点）",
    })

    # 读 A10 成品（f36）当 A11 的 f0，并把 carry 接力状态接到同一个点上。
    build_arm_targets()
    start_pose, start_quats = capture_start(
        arm, bpy.data.actions[JS.NAME], JS.TOTAL)
    start_mats = CR.action_world_matrices(
        arm, bpy.data.actions[JS.NAME], JS.TOTAL)
    # ★ 必须卸掉 action：留着 Jump_Start 的话，后续 `view_layer.update()` 会在
    #   某些帧把 pelvis 的 f-curve 值重新压回 pose bone 上 —— 实测 f1 的髋被读成
    #   "A10 f36 的高度"（1.7715 而非 1.8016），踝目标因此低了 30 mm，
    #   `ik_reach_ok` 假红在 30.35 mm（踝其实站对了地方，是尺子被污染）。
    arm.animation_data.action = None

    JS._PREV_EULER.clear()
    for name, value in start_pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    JS.ARM_QUAT.clear()
    JS.ARM_ROLL.clear()
    JS.ROLL_MAX.clear()
    for name, quat in start_quats.items():
        JS.ARM_QUAT[name] = quat
    JS.MAX_ABS_EULER_Y = 0.0
    # A10 遗留警告：Y 安全带余量只 0.35°。本支收臂幅度同量级，趁早把范围放大。
    # ★ Y_SAFE 是**本支 no_teleport 的关键旋钮**：roll 分岔切换若发生在 Y 高敏感区
    #   （≈79°），第一下切换就要欧拉掰 45°。把安全带压低 = 让 roll 在 Y 还低时
    #   就介入、并把切换摊到多帧。`JU_YSAFE` 可覆盖（扫参用）。
    JS.ROLL_RANGE = 150.0
    JS.Y_SAFE = float(os.environ.get("JU_YSAFE", "28.0"))

    del TARGETS[:]
    del TRACE[:]
    keyframes = [(0, start_pose)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, build_pose(arm, frame, record=True)))
    A.report("JUMPUP_ARM_ROLL", {
        "max_abs_euler_y_deg": round(JS.MAX_ABS_EULER_Y, 2),
        "max_abs_roll_deg": {k: round(JS.ROLL_MAX.get(k, 0.0), 1)
                             for k in ARM_BONES},
        "roll_range_deg": JS.ROLL_RANGE,
        "y_safe_deg": JS.Y_SAFE,
        "hint": "roll = 绕骨轴自转（只改滚转、不改骨轴方向）；Y = 欧拉中间角",
    })

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "基础移动",
        "note": ("空中上升：接 Jump_Start@36 的弹道（还剩 11.55 帧到顶点），"
                 "骨盆继续升 181 mm、竖速 1.887 → 0 m/s；双腿续收（膝弯 +12°）、"
                 "双臂从前上高位收到体侧护体架势（55%）；末帧即离散顶点"),
        "antic_frame": None,
        "hit_frame": None,
        "cancel_frame": None,
        "hitstop_frames": 0,
        "root_motion_m": [0.0, 0.0],
        "rise_m": round(Z_END - Z_START, 4),
        "start_pelvis_z_m": round(Z_START, 6),
        "end_pelvis_z_m": round(Z_END, 6),
        "start_vertical_speed_mps": round((pelvis_z(1) - pelvis_z(0)) * A.FPS, 4),
        "end_vertical_speed_mps": round((Z_END - pelvis_z(TOTAL - 1)) * A.FPS, 4),
        "apex_rise_from_takeoff_m": round(JS.APEX_RISE, 4),
        "link_prev": "A10 Jump_Start@36",
        "link_next": "A12 Jump_Fall（从顶点 0 m/s 开始下落）",
        "ground_contact_skipped": "全段离地",
        "power_chain_scale_note": ("空中无地面反力：thigh/shin 判据取"
                                   "'可见'下限 3°，A10 的 15° 是蹬地展开的量"),
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "RISE_START": 0, "RISE_MID": 6, "APEX": 9, "APEX_END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # foot_probe 置空：通用门禁的"脚位移 ≤3 mm"量的是 toe 骨，本支脚全在空中。
    report = A.run_common_assertions(samples, meta, foot_probe=())
    report["common_ground_min_all_frames_mm"] = report.get("ground_min_mm")

    sole = JS.sole_series(arm, action, list(range(0, TOTAL + 1)))
    ankles = ankle_series(arm, action, list(range(0, TOTAL + 1)))
    target_err = 0.0
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    for index, frame in enumerate(range(0, TOTAL + 1)):
        if frame == 0:
            continue
        for side in ("L", "R"):
            target_err = max(target_err,
                             (Vector(ankles[index][side])
                              - pair[(frame, side)]).length)

    report.update(jump_up_assertions(
        arm, action, samples, start_mats, sole, target_err,
        hip_ankle_vert(arm, action, TOTAL)))
    report["meta"] = meta
    # 显式登记被跳过的门禁（值 None）：既让 failed 干净，又不静默隐藏。
    report["skipped_gates"] = sorted(
        k for k, v in report.items() if v is None and k.endswith("_ok"))
    failed = sorted(k for k, v in report.items()
                    if (k.endswith("_ok") or k == "no_teleport")
                    and v is not True and v is not None)
    report["failed"] = failed
    A.report("JUMPUP_REPORT", report)

    if not SKIP_RENDER:
        UP_SIDE = ("side", (4.6, 0.0, 1.95), (0.0, 0.0, 1.95), 3.00, (760, 1200))
        UP_FRONT = ("front", (0.0, -5.0, 1.95), (0.0, 0.0, 1.95), 3.00,
                    (760, 1200))
        UP_3Q = ("three_quarter", (3.2, -3.6, 2.05), (0.0, 0.0, 1.85), 3.00,
                 (760, 1200))
        A.render_pose_sheet(arm, action, [0, 3, 6, 9, TOTAL], "jumpup",
                            views=(UP_SIDE,))
        A.render_pose_sheet(arm, action, [0, 6, TOTAL], "jumpup",
                            views=(UP_FRONT,))
        A.render_pose_sheet(arm, action, [0, TOTAL], "jumpup", views=(UP_3Q,))
        # 存盘/导出只在**出图那一遍**做：SKIP_RENDER 是纯门禁迭代，
        # 落盘会和并发扫参的其它进程抢同一个 .blend。
        A.save_project()
        A.export_glb(arm)
    print("JUMPUP_DONE failed=%s" % failed)
    # 诊断：逐帧臂骨 euler 步 + 真世界旋转步（区分"表示跳"与"真扭转变"）。
    rows = []
    for index in range(1, len(TRACE)):
        before, after = TRACE[index - 1], TRACE[index]
        worst, worst_bone = 0.0, None
        for name in ARM_BONES:
            step = max(abs(a - b) for a, b in
                       zip(before["euler"][name], after["euler"][name]))
            if step > worst:
                worst, worst_bone = step, name
        real = 0.0
        real_bone = None
        for name in ARM_BONES:
            ang = math.degrees(before["quat"][name].rotation_difference(
                after["quat"][name]).angle)
            if ang > real:
                real, real_bone = ang, name
        rows.append({"f": after["frame"], "euler_step": round(worst, 2),
                     "bone": worst_bone, "real_step": round(real, 2),
                     "real_bone": real_bone,
                     "y": round(max(abs(v[1]) for v in
                                    after["euler"].values()), 1)})
    A.report("JUMPUP_TRACE", rows)
    # 逐帧逐骨：欧拉步 / 真世界旋转步 / |Y|（诊断表示跳 vs 真扭转变）
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
    A.report("JUMPUP_TRACE_DETAIL", detail)
    # 逐帧踝目标误差（定位 `ik_reach_ok` 红在哪一帧）
    pair = {(f, s): Vector(t) for f, s, t in TARGETS}
    A.report("JUMPUP_TARGET_ERR", [
        {"f": frame, "side": side,
         "err_mm": round((Vector(ankles[frame][side])
                          - pair[(frame, side)]).length * 1000.0, 2),
         "target_mm": [round(v * 1000.0, 1) for v in pair[(frame, side)]],
         "ankle_mm": [round(v * 1000.0, 1) for v in ankles[frame][side]]}
        for frame in range(1, TOTAL + 1) for side in ("L", "R")])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("JUMPUP_FAILURE " + traceback.format_exc())
