"""anim_run_stop —— A06 `Run_Stop` 急停。

设计（对着清单「下一支计划 —— A06」逐条落）：
    定位      1~2 步制动，身体因惯性**前冲**后拉回。
    时长      54 帧 / 0.900 s @60fps，**非循环**（急停是一次性动作）。
    首帧      **直接引用 `Run@48`**（`WF.gait_pose(arm, RUN, 0, meshes)`，
              实测 `Run@0` 与 `Run@48` 逐位一致）—— 不是从零猜的站姿。
    结构      0~8   制动 1：后脚（R）从身后 532 mm 前跨落地（前掌先落）
              8~20  制动 2：前脚（L）离地收回，双膝屈，重心继续前冲
              20~34 拉回：骨盆反向往后，上身立起（前压 128 → ≤60 mm）
              34~54 稳定：收招到战斗站姿，末 6 帧角度增量单调收敛
    脚口径    制动期支撑脚**世界坐标钉死**（`no_foot_slide ≤3 mm`）——
              这是站姿类口径，**不是** Walk/Run 族的"匀速滑移"。

---------------------------------------------------------------------------
三处与"老做法"不同的地方（都有实测依据，写在这里备查）

1. **腿的 IK 用 `aim_bone` 反解，不用 `leg_ik` 的 euler 映射。**
   `anim_lib.leg_ik` 是在 **YZ 平面**解两骨 IK，它隐含"腿的旋转轴恰是世界 X"。
   但 pelvis 带了 `ry` 扭转（Run@48 是 −6°）、thigh 又带外展 —— 实测
   `Run@48` 的 `foot.L` 世界 x = **46.6 mm**，而 IK 的输入名义值是 **85 mm**，
   差 38 mm。要"把踝钉在世界某点"，必须走**真逆解**：先读髋的世界实位，
   再用两骨几何直接算 knee，最后 `aim_bone` 把 thigh / shin 指过去。
   实测闭环后踝的世界坐标与目标一致。

2. **脚底最低点按"鞋对象"测，不按"顶点 x 符号"分左右。**
   `lowest_z_by_side` 在两只脚靠近时会串门（Run@48：R 报 8.98 mm，
   真值 108.18 mm —— 那个 8.98 是**左鞋**的内侧边缘）。
   A06 要按脚判"落地窗口"，必须精确 → 新增 `A.foot_lowest_by_side()`。

3. **支撑脚在支撑窗口内"零旋转"。** 脚的世界朝向由 `keep_world_orientation`
   + `add_world_rx(tip)` **绝对**给定，所以只要 (踝世界坐标, tip) 在窗口内
   不变，整只脚就是**世界刚性**的 —— 鞋底接触点、脚尖、脚跟一起不动。
   若中途改 tip（例如"前掌先落再放平"），脚会绕踝转、脚尖要滑 4 mm，
   直接顶红 `no_foot_slide`。故 R 脚落地后 tip 恒为 3°（前掌着地，
   与 `Run` 的触地角一致），L 脚两个支撑窗口内各恒为 3° / 0°。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_run_stop.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_walk_f as WF  # noqa: E402
import anim_run as R  # noqa: E402

NAME = "Run_Stop"
TOTAL = 54                       # 0.900 s @ 60 fps
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")

# ---------------------------------------------------------------- 相位
T_R_ON = 8                       # 后脚落地（第 1 步制动）
T_L_OFF = 10                     # 前脚离地
T_L_ON = 20                      # 前脚落地（第 2 步制动）= 重心最前
T_LIFT = 0.045                   # 前脚收回时的离地峰值

# 各脚的落地帧：从这一帧起，该脚的**世界目标**必须钉死（清单口径：
# 「落地那一刻起，支撑脚的世界坐标必须钉死」）。实现方式见 `solve_pose`
# 的 shift 冻结 —— 贴地闭环只在落地帧跑一次，之后复用同一个 shift，
# 踝不再逐帧追着（受蒙皮混权影响的）鞋底最低点漂。
PLANT_SINCE = {"L": T_L_ON, "R": T_R_ON}
FROZEN_SHIFT = {}

# ---------------------------------------------------------------- 踝世界目标
# 首帧值全部取自 `Run@48` 实测（见 probe_rs）—— 不是估计值。
LX0, LY0 = 0.0466, -0.3874       # 左踝（前脚，Run@48 已落地）
RX0, RY0 = -0.0195, 0.5320       # 右踝（后脚，Run@48 在空中 108 mm）
RZ0 = 0.1934                     # 右踝 z（Run@48）
LZ0 = 0.0853                     # 左踝 z（Run@48，鞋底恰在 0）
# 站姿（Idle_01）目标：L 前 / R 后，踏宽 ±0.150
LX1, LY1 = 0.150, -0.170
RX1, RY1 = -0.150, 0.140

TIP_R = 3.0                      # R 脚落地角（前掌先落，与 Run 触地角一致）
TIP_L0, TIP_L1 = 3.0, 0.0        # L 脚：第一窗口 3°（承自 Run）→ 第二窗口 0°

# ---------------------------------------------------------------- 骨盆轨迹
PELVIS_X = ((0, -0.0021), (12, -0.0010), (24, 0.0000), (54, 0.0000))
# 前冲：−8 → −82 mm（净前移 74 mm，判据 ≥60），然后拉回到 0（判据 ±30）
PELVIS_Y = ((0, -0.0080), (8, -0.0380), (14, -0.0700), (20, -0.0820),
            (27, -0.0520), (34, -0.0220), (44, -0.0050), (54, 0.0000))
# 下沉吸收（801.3 → 748）再升回战斗站姿 830
PELVIS_Z = ((0, 0.8013), (8, 0.7830), (14, 0.7600), (20, 0.7480),
            (27, 0.7830), (34, 0.8280), (44, 0.8305), (54, 0.8300))

# ---------------------------------------------------------------- 躯干轨迹
# 前压 = stiffening 的量化：pelvis_rx + spine_01 + spine_02 + chest
#   f0  = 8+4+3+3 = 18° → 实测前压 127.9 mm（Run@48 真值）
#   f54 = 4+2+2+1 =  9° → 与 Idle_01@呼吸末**逐项相同**
PELVIS_RX = ((0, 8.0), (8, 11.5), (16, 13.5), (20, 12.5),
             (28, 8.0), (34, 4.6), (44, 3.85), (54, 3.8))
PELVIS_RY = ((0, -6.0), (10, -5.0), (20, 0.0), (54, 0.0))
# 末帧合计前屈 3.8+1.4+1.4+0.8 = **7.4°** → 前压 ≈54 mm（判据 ≤60）。
# 为什么不是 Idle_01 的 4+2+2+1 = 9°：那套实测前压 **65.8 mm**，
# 会顶红 `lean_reduced_ok`（≤60）。差 1.6° 在引擎混合里读不出来，
# 但"门禁不许放宽"——所以改姿态，不改判据。
SPINE01_RX = ((0, 4.0), (16, 5.4), (20, 5.0), (34, 1.8), (54, 1.4))
SPINE02_RX = ((0, 3.0), (16, 4.0), (20, 3.6), (34, 1.8), (54, 1.4))
CHEST_RX = ((0, 3.0), (16, 2.6), (20, 2.2), (34, 1.0), (54, 0.8))
SPINE01_RY = ((0, 3.0), (12, 2.0), (20, 0.0), (54, 0.0))
SPINE02_RY = ((0, 3.0), (12, 2.0), (20, 0.0), (54, 0.0))
CHEST_RY = ((0, 4.0), (12, 2.5), (20, 0.0), (54, 0.0))
# 头：躯干前扑时脖子要把脸抬回来（不然脸朝地）
NECK_RX = ((0, -10.0), (16, -13.5), (24, -9.0), (34, -6.5), (54, -6.0))
HEAD_RX = ((0, 9.0), (16, 12.5), (24, 8.0), (34, 5.5), (54, 5.0))
SHOULDER_RX = ((0, -18.0), (16, -21.0), (34, -18.2), (54, -18.0))
SHOULDER_RZ = ((0, 14.0), (12, 9.0), (20, 5.0), (34, 0.8), (54, 0.0))
# 手臂：从 Run 的摇臂方向 slerp 到 Idle 的护体架势；叠加"急停甩臂"
# （`swung` 绕世界 X 正转 = 末端向 +Y = 身后 → 前冲时手臂往后甩）
ARM_BLEND = ((0, 0.0), (8, 0.15), (14, 0.42), (20, 0.66), (28, 0.86),
             (36, 0.96), (54, 1.0))
ARM_FLARE = ((0, 0.0), (8, 8.0), (14, 22.0), (20, 24.0), (28, 13.0),
             (38, 2.5), (46, 0.6), (54, 0.0))

# 运行期填充
RUN_ARM_DIRS = {}
Z_PLANT_TIP3 = None              # tip = 3° 时"鞋底贴地"的踝高
Z_PLANT_FLAT = None              # tip = 0° 时"鞋底贴地"的踝高


# =============================================================== 插值
def track(keys, f):
    """关键点间的 Hermite 插值（切线取中心差分 = Catmull-Rom）。

    为什么不用"逐段 smoothstep"：smoothstep 在**每个关键点**上导数为 0，
    于是每个关键点处动作会"顿一下"，密关键点连起来就是脉冲式抖动；
    急停这种"要一口气减速到底"的动作会被切成好几截。
    中心差分切线只在首末点导数为 0（正是我们要的"起于静止、止于静止"）。
    """
    if f <= keys[0][0]:
        return keys[0][1]
    if f >= keys[-1][0]:
        return keys[-1][1]
    for index in range(len(keys) - 1):
        frame_a, value_a = keys[index]
        frame_b, value_b = keys[index + 1]
        if not (frame_a <= f <= frame_b):
            continue
        span = float(frame_b - frame_a)
        s = (f - frame_a) / span
        prev = keys[index - 1] if index > 0 else keys[index]
        nxt = keys[index + 2] if index + 2 < len(keys) else keys[index + 1]
        m_a = (value_b - prev[1]) / float(frame_b - prev[0])
        # **末段切线强制为 0**（"收招落定"）。用中心差分算末段切线会得到
        # `(v_n − v_{n−1}) / 跨度` 的非零值 —— 于是曲线在终点仍以恒定速度掠过去，
        # 末 6 帧的角度增量**越接近终点越大**（实测 0.082 → 0.240 递增），
        # `decel_smooth_ok`（单调收敛）红。急停的末段本来就该"滑停"，不是"走停"。
        m_b = 0.0 if index + 2 >= len(keys) else \
            (nxt[1] - value_a) / float(nxt[0] - frame_a)
        h00 = 2.0 * s ** 3 - 3.0 * s ** 2 + 1.0
        h10 = s ** 3 - 2.0 * s ** 2 + s
        h01 = -2.0 * s ** 3 + 3.0 * s ** 2
        h11 = s ** 3 - s ** 2
        return (h00 * value_a + h10 * span * m_a
                + h01 * value_b + h11 * span * m_b)
    return keys[-1][1]


def smooth(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def slerp_dir(a, b, t):
    """两个单位方向之间的球面插值。"""
    va, vb = Vector(a).normalized(), Vector(b).normalized()
    dot = max(-1.0, min(1.0, va.dot(vb)))
    angle = math.acos(dot)
    if angle < 1e-6:
        return tuple(va)
    sin_angle = math.sin(angle)
    return tuple((math.sin((1.0 - t) * angle) / sin_angle) * va
                 + (math.sin(t * angle) / sin_angle) * vb)


# =============================================================== 腿的真逆解
def leg_to(arm, pose, side, target):
    """把 `thigh`/`shin` 指向，使踝（`foot.head`）落在世界 `target`。

    两骨几何逆解 + `aim_bone`：
      1. 读髋的**世界实位**（父链已经摆好，含 pelvis 的 rx/ry）；
      2. 由 |髋→踝| 解出膝角，膝向**正前方**（−Y）鼓出（人腿只能这么弯）；
      3. 直接给出 thigh / shin 的目标方向，交给 `aim_bone` 反解 euler。
    这样绕开了"局部 rx 轴被父链扭转带偏"的老坑（见文件头第 1 条）。
    """
    thigh_len, shin_len = A.L_THIGH, A.L_SHIN
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    target = Vector(target)
    delta = target - hip
    distance = max(1e-4, min(delta.length, (thigh_len + shin_len) * 0.9995))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    forward = Vector((0.0, -1.0, 0.0))
    bulge = forward - axis * forward.dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    cos_hip = (thigh_len ** 2 + distance ** 2 - shin_len ** 2) \
        / (2.0 * thigh_len * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    knee = hip + (axis * cos_hip + bulge * sin_hip) * thigh_len
    pose["thigh." + side] = A.aim_bone(arm, "thigh." + side, knee - hip)
    pose["shin." + side] = A.aim_bone(arm, "shin." + side, target - knee)


# =============================================================== 目标
def sole_target(f):
    """该帧每只脚的"期望鞋底离地量"（米）。支撑期 0，摆动期按包络。"""
    if f <= T_L_OFF:
        left = 0.0
    elif f < T_L_ON:
        s = (f - T_L_OFF) / float(T_L_ON - T_L_OFF)
        left = T_LIFT * math.sin(math.pi * s) ** 0.8
    else:
        left = 0.0
    if f <= T_R_ON:
        # 后脚从 108 mm 高处**加速拍下**：指数 1.7 让触地前一帧速度最大
        right = 0.108 * (1.0 - (f / float(T_R_ON)) ** 1.7)
    else:
        right = 0.0
    return {"L": left, "R": right}


def ankle_targets(f, shift):
    """返回 {"L": (x, y, z, tip), "R": (...)}：踝世界目标 + 脚背角。"""
    out = {}
    dz_l, dz_r = shift["L"], shift["R"]

    if f <= T_L_OFF:
        out["L"] = (LX0, LY0, Z_PLANT_TIP3 + dz_l, TIP_L0)
    elif f < T_L_ON:
        s = (f - T_L_OFF) / float(T_L_ON - T_L_OFF)
        u = smooth(s)
        out["L"] = (LX0 + (LX1 - LX0) * u, LY0 + (LY1 - LY0) * u,
                    Z_PLANT_FLAT + sole_target(f)["L"] + dz_l,
                    TIP_L0 + (TIP_L1 - TIP_L0) * u)
    else:
        out["L"] = (LX1, LY1, Z_PLANT_FLAT + dz_l, TIP_L1)

    if f <= T_R_ON:
        s = f / float(T_R_ON)
        u = smooth(s)
        out["R"] = (RX0 + (RX1 - RX0) * u, RY0 + (RY1 - RY0) * u,
                    Z_PLANT_TIP3 + sole_target(f)["R"] + dz_r, TIP_R)
    else:
        out["R"] = (RX1, RY1, Z_PLANT_TIP3 + dz_r, TIP_R)
    return out


def torso_pose(f):
    return {
        "pelvis": (track(PELVIS_RX, f), track(PELVIS_RY, f), 0.0),
        "spine_01": (track(SPINE01_RX, f), track(SPINE01_RY, f), 0.0),
        "spine_02": (track(SPINE02_RX, f), track(SPINE02_RY, f), 0.0),
        "chest": (track(CHEST_RX, f), track(CHEST_RY, f), 0.0),
        "neck": (track(NECK_RX, f), 0.0, 0.0),
        "head": (track(HEAD_RX, f), 0.0, 0.0),
        "shoulder.L": (track(SHOULDER_RX, f), 0.0, track(SHOULDER_RZ, f)),
        "shoulder.R": (track(SHOULDER_RX, f), 0.0, track(SHOULDER_RZ, f)),
        "@loc": {"pelvis": A.wloc(track(PELVIS_X, f), track(PELVIS_Y, f),
                                  track(PELVIS_Z, f) - 0.900)},
    }


def build_pose(arm, f, shift):
    """构造并写入第 f 帧姿态（一次姿态，不含贴地闭环）。"""
    pose = torso_pose(f)
    A.apply_pose(arm, pose)

    targets = ankle_targets(f, shift)
    for side in ("L", "R"):
        x, y, z, _tip = targets[side]
        leg_to(arm, pose, side, (x, y, z))

    for side in ("L", "R"):
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        WF.add_world_rx(arm, name, targets[side][3])
        pose[name] = tuple(math.degrees(v)
                           for v in arm.pose.bones[name].rotation_euler)

    pose.update(A.FIST)
    blend = track(ARM_BLEND, f)
    flare = track(ARM_FLARE, f)
    for bone in ARM_BONES:
        direction = slerp_dir(RUN_ARM_DIRS[bone], I1.ARM_DIRS[bone], blend)
        pose[bone] = A.aim_bone(arm, bone, WF.swung(direction, flare))
    return pose


def solve_pose(arm, f, meshes=None):
    """两遍**实测贴地闭环**：第一遍后测鞋底，按误差平移踝 z 再摆一遍。

    支撑期特例：脚一旦落地（`f >= PLANT_SINCE[side]`），该侧的 shift 就
    **冻结**在落地帧收敛出的值上，不再逐帧重算。理由——
      1) 清单口径要求"落地后支撑脚的世界坐标钉死"；逐帧重算 shift 会让
         踝持续微沉（A06 实测 1.7977 mm），那是"脚在往下爬"，不是钉死；
      2) 逐帧追鞋底最低点会形成**蒙皮反馈环**：鞋顶点的世界位置同时受
         `shin` 权重影响，膝一弯顶点就动，闭环于是把踝一路往下拉。
    冻结后踝是世界常量，剩下的只是骨骼刚体解 —— 与 `anim_lib` 的
    `no_foot_slide`（同样按骨骼世界坐标量）口径一致。
    """
    shift = {"L": 0.0, "R": 0.0}
    locked = [side for side in ("L", "R")
              if side in FROZEN_SHIFT and f > PLANT_SINCE[side]]
    for side in locked:
        shift[side] = FROZEN_SHIFT[side]

    pose = build_pose(arm, f, shift)
    if meshes is None:
        return pose
    for _ in range(2):
        want = sole_target(f)
        low = A.foot_lowest_by_side()
        error = {side: want[side] - low[side][2]
                 for side in ("L", "R") if side not in locked}
        if not error or max(abs(v) for v in error.values()) < 5e-5:
            break
        for side, value in error.items():
            shift[side] += value
        pose = build_pose(arm, f, shift)

    # 落地帧：把收敛出的 shift 冻结下来，作为这一整段支撑期的世界常量。
    for side in ("L", "R"):
        if f == PLANT_SINCE[side] and side not in FROZEN_SHIFT:
            FROZEN_SHIFT[side] = shift[side]
    return pose


def measure_plant_z(arm, tip, torso, ankle_xy, z_probe):
    """测"鞋底恰好贴地"时该脚踝的世界高度（tip 固定）。

    只做**一次测量**：踝以下的脚是刚体，`踝高 − 鞋底最低点` 是常数偏移，
    与踝在哪儿无关。故 offset = 实测踝高 − 实测鞋底高，即所求。
    踩过的坑：第一版写成迭代 `z -= 鞋底高`，而标定姿态给的是**中性站姿**
    （髋 z = 0.900）—— 此时"脚前伸 387 mm 且落到 85 mm"在几何上**不可达**
    （|髋→踝| = 903 mm > 腿长 822 mm），`leg_to` 把目标截到腿长上，
    踝根本不在 z 上，迭代把标定值一路推到 **−102 mm**（踝在地面以下 10 cm）。
    警告：标定姿态必须与动画里的姿态**量级接近**。
    """
    pose = dict(torso)
    A.apply_pose(arm, pose)
    leg_to(arm, pose, "L", (ankle_xy[0], ankle_xy[1], z_probe))
    A.keep_world_orientation(arm, "foot.L")
    WF.add_world_rx(arm, "foot.L", tip)
    reached = A.bone_world(arm, "foot.L", "head")
    reach_error = abs(reached.z - z_probe)
    ankle_z = reached.z
    low = A.foot_lowest_by_side()["L"][2]
    return ankle_z - low, round(reach_error * 1000.0, 3)


# =============================================================== 测量
def action_world_matrices(arm, action, frame):
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    out = {bone.name: tuple(v for row in bone.matrix for v in row)
           for bone in arm.pose.bones}
    if previous is not None:
        arm.animation_data.action = previous
    return out


def matrix_delta(a, b):
    return max(abs(x - y) for name in a for x, y in zip(a[name], b[name]))


def spacing_spans(frames):
    spans = []
    for frame in frames:
        if spans and frame == spans[-1][1] + 1:
            spans[-1][1] = frame
        else:
            spans.append([frame, frame])
    return spans


# =============================================================== 专属门禁
def run_stop_assertions(arm, action, samples, meshes, run_mats):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [s["pelvis"] for s in samples]

    # 0) 首帧必须**逐位**等于 `Run@48`（世界矩阵，不是 euler）。
    mats = action_world_matrices(arm, action, 0)
    delta = matrix_delta(mats, run_mats)
    res["first_frame_delta"] = float("%.3e" % delta)
    res["first_frame_matches_run_end_ok"] = delta <= 1e-6

    # 1) 每只脚各自的鞋底高度（按**对象**测，不按 x 符号）—— 落地窗口的尺子。
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    sole = {"L": [], "R": []}
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        low = A.foot_lowest_by_side()
        for side in ("L", "R"):
            sole[side].append(low[side][2])
    if previous is not None:
        arm.animation_data.action = previous

    contact = 0.003
    planted = {}
    for side in ("L", "R"):
        planted[side] = [f for f, z in zip(frames, sole[side]) if z <= contact]
    res["planted_frames"] = {k: spacing_spans(v) for k, v in planted.items()}
    res["swing_clearance_mm"] = {
        "L": round(max(sole["L"][i] for i, f in enumerate(frames)
                       if f not in planted["L"]) * 1000.0, 2)
        if any(f not in planted["L"] for f in frames) else 0.0,
        "R": round(max(sole["R"][i] for i, f in enumerate(frames)
                       if f not in planted["R"]) * 1000.0, 2)
        if any(f not in planted["R"] for f in frames) else 0.0,
    }
    res["left_foot_retracts_ok"] = res["swing_clearance_mm"]["L"] >= 25.0
    res["right_foot_slams_ok"] = sole["R"][0] >= 0.090

    # 2) 制动跨步数 = 每只脚"由空中变落地"的次数之和（判据 1~2）。
    steps = 0
    for side in ("L", "R"):
        was_air = False
        for z in sole[side]:
            now_air = z > contact
            if was_air and not now_air:
                steps += 1
            was_air = now_air
    res["brake_steps"] = steps
    res["brake_steps_ok"] = 1 <= steps <= 2

    # 3) **惯性前冲**：骨盆 y 相对首帧继续向前 ≥60 mm（−Y 是正面）。
    forward = (pelvis[0][1] - min(p[1] for p in pelvis)) * 1000.0
    res["inertia_forward_mm"] = round(forward, 2)
    res["inertia_forward_ok"] = forward >= 60.0

    # 4) **拉回**：末帧骨盆 y 回到首帧 ±30 mm。
    back = abs(pelvis[-1][1] - pelvis[0][1]) * 1000.0
    res["recover_back_mm"] = round(back, 3)
    res["recover_back_ok"] = back <= 30.0

    # 5) **前压收敛**：首帧 ~128 mm（承自 Run）→ 末帧 ≤60 mm（战斗站姿）。
    leans = [(p[1] - s["neck"][1]) * 1000.0
             for p, s in zip(pelvis, samples)]
    res["lean_forward_mm"] = round(leans[0], 2)
    res["lean_forward_peak_mm"] = round(max(leans), 2)
    res["lean_final_mm"] = round(leans[-1], 2)
    res["lean_reduced_ok"] = leans[0] >= 100.0 and leans[-1] <= 60.0

    # 6) **支撑脚世界钉死**：各自落地窗口内，踝与脚尖的**骨骼世界坐标**行程
    #    ≤3 mm。这是清单的原文口径 ——「落地那一刻起，支撑脚的世界坐标必须
    #    钉死」（`anim_lib.no_foot_slide` 量的也是骨骼，A01~A05 同一把尺子）。
    # 必须**按每个连续支撑窗口分别量**：L 脚有两个窗口（0~10 与 20~54），
    # 两窗口的站姿位置本来就不同（前脚从 −387 收回 −170），把它们连起来量
    # 得到的是"跨步距离 240 mm"，不是"脚在滑"。
    #
    # 另记 `sole_low`（鞋底最低**网格顶点**的世界行程）—— 只报不判。
    # 理由（实测，见 probe_sole_baseline.py）：鞋顶点是**蒙皮**的，`foot.L`
    # 与 `shin.L` 混权，膝一弯顶点就被带偏。同一把尺子量：
    #     Idle_01（膝几乎不弯）脚骨 0.192 mm / 顶点局部残差 0.246 mm；
    #     A06 L[20,54]（膝随骨盆升降 82 mm）脚骨 **0.003** mm / 顶点残差
    #     **5.63** mm。
    # 鞋是刚体、脚骨是刚体，唯一变的是权重混合 ⇒ 这 5.6 mm 是**绑定属性**，
    # 不是动画误差；拿它当门禁等于要求"屈膝时鞋不许变形"，A08 蹲伏 / A13
    # 落地 / D03 防御受击这类"脚踩地 + 屈膝"的动作全部无法通过。
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    worst = 0.0
    detail = {}
    drift = {}
    for side in ("L", "R"):
        spans = spacing_spans(planted[side])
        detail[side] = []
        drift[side] = []
        for start, end in spans:
            index = [i for i, f in enumerate(frames) if start <= f <= end]
            travel = {}
            for key in ("foot." + side, "toe." + side):
                points = [Vector(samples[i][key]) for i in index]
                travel[key] = round(max((p - points[0]).length
                                        for p in points) * 1000.0, 3)
            scene.frame_set(frames[index[0]])
            bpy.context.view_layer.update()
            first_low = Vector(A.foot_lowest_by_side()[side])
            low_travel = 0.0
            for i in index:
                scene.frame_set(frames[i])
                bpy.context.view_layer.update()
                point = Vector(A.foot_lowest_by_side()[side])
                low_travel = max(low_travel,
                                 (point - first_low).length * 1000.0)
            travel["span"] = [start, end]
            detail[side].append(travel)
            drift[side].append({"sole_low_mm": round(low_travel, 3),
                                "span": [start, end]})
            worst = max(worst, max(travel[k] for k in ("foot." + side,
                                                       "toe." + side)))
    res["planted_travel_mm"] = detail
    res["planted_sole_drift_mm"] = drift
    res["planted_feet_frozen_ok"] = worst <= 3.0

    # 7) **收招不许瞬停**：末 6 帧的角度增量绝对值单调收敛。
    deltas = []
    tail_bones = []
    for index in range(len(samples) - 6, len(samples)):
        before, after = samples[index - 1]["euler"], samples[index]["euler"]
        worst_step = 0.0
        worst_bone = None
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
    res["decel_smooth_ok"] = all(
        deltas[i + 1] <= deltas[i] + 1e-9 for i in range(len(deltas) - 1))

    # 8) 末帧站姿：双脚落到战斗站姿（前 L / 后 R，踏宽 ≥0.25 m）。
    last = samples[-1]
    lx, ly = last["foot.L"][0], last["foot.L"][1]
    rx, ry = last["foot.R"][0], last["foot.R"][1]
    res["stance_last_mm"] = {"L": [round(lx * 1000.0, 1),
                                   round(ly * 1000.0, 1)],
                             "R": [round(rx * 1000.0, 1),
                                   round(ry * 1000.0, 1)]}
    res["stance_width_mm"] = round(abs(lx - rx) * 1000.0, 1)
    res["stance_ok"] = (abs(lx - rx) >= 0.25 and ly < ry
                        and abs(ly + 0.170) <= 0.025
                        and abs(ry - 0.140) <= 0.025)

    # 9) 力量传导链：脚→腿→髋→腰→肩→手，不许"只有手在动"。
    res.update(WF.power_chain(samples))
    return res


# =============================================================== 主流程
def main():
    global RUN_ARM_DIRS, Z_PLANT_TIP3, Z_PLANT_FLAT

    FROZEN_SHIFT.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Run" not in bpy.data.actions:
        print("RUNSTOP_BOOTSTRAP 动画工程缺 Run，先补跑 A05")
        R.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # 首帧真值：直接复用 Run 的第 0 帧姿态（= Run@48，逐位一致）
    run_pose = WF.gait_pose(arm, R.RUN, 0, meshes)
    A.apply_pose(arm, run_pose)
    RUN_ARM_DIRS = {bone: tuple(A.bone_direction(arm, bone))
                    for bone in ARM_BONES}

    # tip=3° 的标定直接用 `Run@48` 的姿态（同样的前伸量，保证几何可达）
    torso_run = {
        "pelvis": (8.0, -6.0, 0.0), "spine_01": (4.0, 3.0, 0.0),
        "spine_02": (3.0, 3.0, 0.0), "chest": (3.0, 4.0, 0.0),
        "@loc": {"pelvis": A.wloc(-0.0021, -0.008, 0.8013 - 0.900)},
    }
    Z_PLANT_TIP3, err3 = measure_plant_z(arm, TIP_R, torso_run,
                                         (LX0, LY0), LZ0)
    Z_PLANT_FLAT, err0 = measure_plant_z(arm, TIP_L1, torso_pose(TOTAL),
                                         (LX1, LY1), 0.120)
    A.report("RUNSTOP_CALIBRATION", {
        "plant_z_tip3_mm": round(Z_PLANT_TIP3 * 1000.0, 3),
        "plant_z_flat_mm": round(Z_PLANT_FLAT * 1000.0, 3),
        "plant_z_tip3_reach_err_mm": err3,
        "plant_z_flat_reach_err_mm": err0,
        "run48_left_ankle_z_mm": round(LZ0 * 1000.0, 3),
    })

    keyframes = [(0, run_pose)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "基础移动",
        "note": ("急停：后脚前跨制动 + 前脚收回，骨盆前冲 74 mm 后拉回；"
                 "支撑脚世界钉死（≤3 mm）"),
        "entry_speed_mps": round(R.RUN.locomotion_mps, 4),
        "exit_speed_mps": 0.0,
        "antic_frame": None,
        "hit_frame": None,
        "cancel_frame": 34,
        "hitstop_frames": 0,
        "root_motion_m": [0.0, 0.0],
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "START": 0, "R_TOUCH": T_R_ON, "L_OFF": T_L_OFF, "L_TOUCH": T_L_ON,
        "RECOVER_END": 34, "SETTLE_END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # foot_probe 置空：通用门禁的"脚位移 ≤3 mm"要按**落地窗口**判，不能整段判
    # （这一段里脚本来就要跨两步），改用专属的 `planted_feet_frozen_ok`。
    report = A.run_common_assertions(samples, meta, foot_probe=())

    run_mats = action_world_matrices(arm, bpy.data.actions["Run"], 48)
    report.update(run_stop_assertions(arm, action, samples, meshes, run_mats))
    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True)
    report["failed"] = failed
    A.report("RUNSTOP_REPORT", report)

    if not SKIP_RENDER:
        # 侧视：0 起（左脚在前、右脚身后腾空）、2/5 后脚拍下、8 落地、
        #       14 前脚收回、20 双脚站定、30/44 立起、54 战斗站姿。
        A.render_pose_sheet(arm, action, [0, 3, 8, 12, 16, 20, 28, 38, 54],
                            "runstop", views=(A.VIEW_SIDE,))
        A.render_pose_sheet(arm, action, [0, 8, 20, 54], "runstop",
                            views=(A.VIEW_FRONT,))
    A.save_project()
    A.export_glb(arm)
    print("RUNSTOP_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("RUNSTOP_FAILURE " + traceback.format_exc())
