"""anim_turn —— A07 `Turn` 转身。

设计（对着清单「下一支计划 —— A07」逐条落）：
    定位      以髋部带动上身快速转向，脚下有换步，**不可原地镜像瞬切**。
    时长      30 帧 / 0.500 s @60fps，**非循环**（一次性动作）。
    衔接      首帧 = `Idle_01@0` 的战斗站姿（世界矩阵逐位一致）。
    结构      0~6   预备：头先转瞄准（头 yaw 领先髋 ≥3 帧），重心移向前脚 L，
                      **轴心脚 R 向身体中线收半步**并落地（这一步同时是"跟半步"）
              6~14  发力：**髋先转**，上身被甩过去（胸 yaw 滞后髋 **2 帧**）
              14~22 换步：非轴心脚 L **绕轴心脚跨过去**落地（绕 P_R 扫过 84°）
              22~30 收势：落进新朝向的战斗站姿，末 6 帧角度增量单调收敛
    轴心脚    R 脚踝世界坐标钉死（骨架口径 ≤3 mm）
    转向      +90°（绕世界 Z，角色原朝 −Y → 新朝 +X）＝ 向角色左侧转身

---------------------------------------------------------------------------
本支最关键的一个几何结论（决定了整支的骨架，写在这里备查）

**"原地转身 + 轴心脚钉死"这两条同时成立 ⟹ 旋转轴必须穿过骨盆。**

推导：设轴心脚踝在骨盆系里的水平偏移为 r，则绕轴心脚转 90° 会把骨盆搬走
`|r|·√2`。Idle_01 的站姿里 |r| = 0.205~0.227 m ⟹ 骨盆会被搬走 **29~32 cm**，
那已经不是"原地"了（清单 §0.4：Turn 属普通移动，位移由程序控制）。

所以本支把**轴心脚先收半步到骨盆正下方**（`P_R ≈ (0, 10mm)`），
再绕它转 90°：
  · 转轴穿过骨盆 ⟹ 骨盆水平行程只有几厘米（实测 24 mm 峰值、末帧回 0）；
  · 轴心脚踝钉死 ≤3 mm（它就是旋转轴本身）；
  · 非轴心脚仍绕轴心脚扫过 **84°** —— "看得见过程"（`not_mirror_instant_ok`）。

代价 / 口径说明（不改正文，在此备案）：
  1) 平面里"绕轴心脚转 90°"必然把该脚踝当成旋转轴心，于是**脚掌绕踝原地碾转**
     （真实人踢转是绕脚掌前掌转、踝会小幅移动）。本支按清单门禁的原文口径
     把**踝**钉死（`anim_lib.no_foot_slide` 量的也是骨骼世界坐标），
     脚趾扫掠量 `pivot_toe_sweep_mm` 只报不判。
  2) 末帧站姿的踏宽 0.234 m，比 Idle_01 的 0.300 m 窄 —— 轴心脚收到中线后
     两脚本来就靠得更近；再往外站会顶到腿的可达上限（骨盆 z=0.830 时
     踝最多离髋 **332 mm** 水平，见 A05 的几何上限推导）。

---------------------------------------------------------------------------
三处与"老做法"不同的地方（都有实测依据）

1. **yaw 用 `probe_turn.py` 补测过**（清单注意第一条要求先补测再动手）。
   实测结论：竖直骨（pelvis/spine/chest/neck/head）的局部系严格是
   `X_local = +X_w, Y_local = +Z_w, Z_local = −Y_w`，且 `rotation_euler.ry`
   **精确等于**世界 Z 转角 —— 前倾 rx 取到 8° 时误差仍是 **0.000°**。
   所以本支直接写 `ry`，朝向仍用"局部 X 轴在世界 XY 平面的投影"实测复核
   （不读 euler 分量，见 `heading_deg`）。
2. **腿用真双骨 IK（`leg_to`）并按身体当前朝向给"膝弯方向"**。
   转身时骨盆一直在绕世界 Z 转，膝鼓出方向必须跟着转（否则膝盖会拧向侧面）。
3. **轴心脚绕踝碾转**：脚的世界朝向 = `Rz(身体 yaw) · rest`，
   踝的位置不动 ⟹ 踝世界行程 ≈ 0，而脚掌读得出"转过去了"。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_turn.py
    SKIP_RENDER=1 只跑门禁（迭代用）。
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_walk_f as WF  # noqa: E402

NAME = "Turn"
TOTAL = 30                       # 0.500 s @ 60 fps
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")

# ---------------------------------------------------------------- 脚位（世界踝坐标，米）
# 两个初始值直接取自 Idle_01（`FRONT_ANKLE_Y` / `BACK_ANKLE_Y` / `STANCE_HALF_X`）。
P_L = (0.150, -0.170)            # 非轴心脚（L，前脚）
R0 = (-0.150, 0.140)             # 轴心脚（R，后脚）初始
# 轴心脚收半步的落点：**骨盆正下方**（这是"原地转身"能成立的前提，见文件头推导）
P_R = (0.000, 0.010)
# 非轴心脚落点 = 把 P_L 绕 P_R 刚性转 90°（在 `main` 里算，保证半径严格相等）
L_END = None

# 相位
T_PLANT = 6                      # 轴心脚 R 落地（此后钉死）
T_OFF = 7                        # 非轴心脚 L 离地
T_LAND = 22                      # 非轴心脚 L 落地
LEAD_HIP = 2.0                   # 胸 yaw 相对髋的滞后帧数（清单：≤2 帧）

LIFT_MOVER = 0.070               # 非轴心脚离地峰值（绕轴心脚跨步，要抬得起来）
LIFT_PIVOT = 0.045               # 轴心脚"跟半步"时的离地峰值

# ---------------------------------------------------------------- 偏航轨迹
# 中段接近线性（~4.3°/帧）：`not_mirror_instant_ok` 要求 5°→85° 占 ≥20 帧，
# 两端各留 4 帧的"启动/收势"，中间 22 帧承担 80° 的主体旋转。
YAW = ((0, 0.0), (3, 1.0), (6, 8.0), (9, 19.0), (12, 32.0), (15, 45.0),
       (18, 58.0), (21, 71.0), (24, 82.0), (26, 86.0), (28, 90.0), (30, 90.0))

# 头/眼先转（预备段"瞄准"）：头 yaw 走自己的轨，比髋早 3 帧过 45°
HEAD_YAW = ((0, 0.0), (2, 7.0), (5, 18.0), (9, 32.0), (12, 45.0), (15, 56.0),
            (18, 66.0), (21, 75.0), (24, 82.0), (26, 86.0), (28, 90.0),
            (30, 90.0))

# ---------------------------------------------------------------- 骨盆轨迹（原地）
# 水平只做"重心压向轴心脚"的一点点转移（峰值 24 mm，末帧回 0）。
PELVIS_X = ((0, 0.0000), (5, -0.0140), (10, -0.0240), (16, -0.0200),
            (22, -0.0100), (30, 0.0000))
PELVIS_Y = ((0, 0.0000), (5, 0.0080), (10, 0.0140), (16, 0.0100),
            (22, 0.0040), (30, 0.0000))
# 下沉蓄力（830 → 802）再回到战斗站姿 830
PELVIS_Z = ((0, 0.830), (6, 0.814), (12, 0.802), (18, 0.806),
            (24, 0.824), (30, 0.830))

# ---------------------------------------------------------------- 躯干轨迹
PELVIS_RX = ((0, 4.0), (8, 6.5), (16, 5.6), (24, 4.4), (30, 4.0))
SPINE01_RX = ((0, 2.0), (10, 3.0), (20, 2.4), (30, 2.0))
SPINE02_RX = ((0, 2.0), (10, 2.8), (20, 2.3), (30, 2.0))
CHEST_RX = ((0, 1.0), (10, 1.4), (20, 1.2), (30, 1.0))
NECK_RX = ((0, -6.0), (10, -8.0), (20, -7.0), (30, -6.0))
HEAD_RX = ((0, 5.0), (10, 6.5), (20, 5.5), (30, 5.0))
SHOULDER_RX = ((0, -18.0), (10, -20.0), (20, -19.0), (30, -18.0))

# 手臂：跟随胸的世界 yaw，叠加"惯性甩"（滞后角）。负值 = 手臂落后于躯干。
ARM_LAG = ((0, 0.0), (5, -4.0), (10, -13.0), (15, -17.0), (20, -14.0),
           (25, -5.0), (28, -1.0), (30, 0.0))

# 支撑窗口（用于"脚不滑"的分窗判定 + 贴地闭环的 shift 冻结）
WINDOWS = {"L": ((0, T_OFF), (T_LAND, TOTAL)), "R": ((T_PLANT, TOTAL),)}

FROZEN = {}
Z_PLANT = None                   # 平放脚"鞋底贴地"的踝高（一次实测，常数偏移）


# =============================================================== 基础数学
def track(keys, f):
    """分段 Hermite（切线取中心差分），**末段切线强制为 0**。

    末段切线置 0 是 A06 踩坑 4 的修法：Catmull-Rom 末段切线天然非零，
    曲线会以恒定速度掠过终点，末 6 帧角度增量**越接近终点越大**，
    `decel_smooth_ok`（单调收敛）红。收招本来就该"滑停"，不是"走停"。
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


def rot2(vector, deg):
    """二维向量绕原点转 deg（度）。"""
    r = math.radians(deg)
    x, y = vector
    return (x * math.cos(r) - y * math.sin(r), x * math.sin(r) + y * math.cos(r))


def rot_about(center, deg, point):
    """点 point 绕 center 转 deg（世界 XY 平面）。"""
    moved = rot2((point[0] - center[0], point[1] - center[1]), deg)
    return (center[0] + moved[0], center[1] + moved[1])


def ang_deg(vector):
    return math.degrees(math.atan2(vector[1], vector[0]))


def rot_z3(vector, deg):
    r = math.radians(deg)
    return (vector[0] * math.cos(r) - vector[1] * math.sin(r),
            vector[0] * math.sin(r) + vector[1] * math.cos(r),
            vector[2])


# =============================================================== 姿态生成
def torso_twist(t):
    """返回 (髋 yaw, 脊椎合计扭转, 颈+头合计扭转)，单位度。

    构造方式：三条 yaw 轨（髋 / 胸 / 头）各自独立，然后**相减得到扭转量**——
    这样"髋领先胸 2 帧、头领先髋 ≥1 帧"是**构造出来的**，不是调参调出来的。
    """
    yaw_hip = track(YAW, t)
    yaw_chest = track(YAW, t - LEAD_HIP)
    yaw_head = track(HEAD_YAW, t)
    return yaw_hip, yaw_chest - yaw_hip, yaw_head - yaw_chest


def leg_to(arm, pose, side, target, forward):
    """把 `thigh`/`shin` 指向，使踝（`foot.head`）落到世界 `target`。

    与 A06 的 `leg_to` 差别只有一处：**膝弯方向 `forward` 由调用方给**
    （A06 硬编码世界 −Y）。转身时骨盆绕世界 Z 转 90°，膝鼓出方向必须跟着转，
    否则膝盖会拧向侧面、脚也解不到位（这正是清单注意里"骨骼局部轴会被带偏"
    在腿上的体现）。
    """
    thigh_len, shin_len = A.L_THIGH, A.L_SHIN
    hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
    target = Vector(target)
    delta = target - hip
    distance = max(1e-4, min(delta.length, (thigh_len + shin_len) * 0.9995))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, 0.0, -1.0)))
    knee_out = Vector((forward[0], forward[1], 0.0)).normalized()
    bulge = knee_out - axis * knee_out.dot(axis)
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


def orient_foot(arm, name, yaw_deg, tip_deg):
    """把脚的世界朝向设成 `Rz(yaw)·Rx(tip)·rest`（只改朝向，不动位置）。

    为什么不用 `anim_lib.keep_world_orientation`：那个把脚钉成**rest**（朝世界 −Y），
    转身时脚掌必须跟着身体转过去；但直接用腿的欧拉补偿又会踩 A01 的老坑
    （父链外展角把补偿轴带偏 4.3°）。这里在世界系里给定朝向，没有累积误差。
    先 Rx 再 Rz：tip（踮脚/勾脚）在**脚的自身侧向轴**上给，转过 yaw 之后
    tip 的方向才是对的（否则 45° 时绕世界 X 会把脚拧成侧翻）。
    """
    pose_bone = arm.pose.bones[name]
    rest = pose_bone.bone.matrix_local.to_3x3()
    target = (Matrix.Rotation(math.radians(yaw_deg), 3, "Z")
              @ Matrix.Rotation(math.radians(tip_deg), 3, "X")
              @ rest).to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def ankle_targets(t, shift, yaw_hip):
    """返回 {"L": (x, y, z, 脚 yaw), "R": (...)}：踝世界目标 + 脚的朝向角。"""
    out = {}
    # ---- 非轴心脚 L：绕轴心脚 P_R 扫过（半径 = |P_L − P_R|，落点半径严格相等）
    if t <= T_OFF:
        lx, ly = P_L
        lift_l = 0.0
    elif t < T_LAND:
        s = (t - T_OFF) / float(T_LAND - T_OFF)
        u = smooth(s)
        a0 = ang_deg((P_L[0] - P_R[0], P_L[1] - P_R[1]))
        a1 = ang_deg((L_END[0] - P_R[0], L_END[1] - P_R[1]))
        radius = math.hypot(P_L[0] - P_R[0], P_L[1] - P_R[1])
        ang = math.radians(a0 + (a1 - a0) * u)
        lx = P_R[0] + radius * math.cos(ang)
        ly = P_R[1] + radius * math.sin(ang)
        lift_l = LIFT_MOVER * math.sin(math.pi * s) ** 0.8
    else:
        lx, ly = L_END
        lift_l = 0.0

    # ---- 轴心脚 R：从 R0 收半步到 P_R（骨盆正下方），落地后钉死
    if t <= T_PLANT:
        s = t / float(T_PLANT)
        u = smooth(s)
        rx = R0[0] + (P_R[0] - R0[0]) * u
        ry = R0[1] + (P_R[1] - R0[1]) * u
        lift_r = LIFT_PIVOT * math.sin(math.pi * s) ** 0.8
    else:
        rx, ry = P_R
        lift_r = 0.0

    # 脚的朝向 = 身体当前 yaw（轴心脚"绕踝原地碾转"，脚踝不动而脚掌转过去）
    out["L"] = (lx, ly, Z_PLANT + lift_l + shift["L"], yaw_hip)
    out["R"] = (rx, ry, Z_PLANT + lift_r + shift["R"], yaw_hip)
    return out


def build_pose(arm, t, shift):
    yaw_hip, spine_twist, head_twist = torso_twist(t)
    pose = {
        "pelvis": (track(PELVIS_RX, t), yaw_hip, 0.0),
        "spine_01": (track(SPINE01_RX, t), spine_twist * 0.30, 0.0),
        "spine_02": (track(SPINE02_RX, t), spine_twist * 0.30, 0.0),
        "chest": (track(CHEST_RX, t), spine_twist * 0.40, 0.0),
        "neck": (track(NECK_RX, t), head_twist * 0.45, 0.0),
        "head": (track(HEAD_RX, t), head_twist * 0.55, 0.0),
        "shoulder.L": (track(SHOULDER_RX, t), 0.0, 0.0),
        "shoulder.R": (track(SHOULDER_RX, t), 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(track(PELVIS_X, t), track(PELVIS_Y, t),
                                  track(PELVIS_Z, t) - 0.900)},
    }
    A.apply_pose(arm, pose)

    yaw_rad = math.radians(yaw_hip)
    forward = (math.sin(yaw_rad), -math.cos(yaw_rad))   # 身体正前方（世界 XY）
    targets = ankle_targets(t, shift, yaw_hip)
    for side in ("L", "R"):
        x, y, z, _yaw = targets[side]
        leg_to(arm, pose, side, (x, y, z), forward)

    for side in ("L", "R"):
        name = "foot." + side
        orient_foot(arm, name, targets[side][3], 0.0)   # 平放，tip 恒 0
        pose[name] = tuple(math.degrees(v)
                           for v in arm.pose.bones[name].rotation_euler)

    pose.update(A.FIST)
    arm_yaw = (track(YAW, t - LEAD_HIP) + track(ARM_LAG, t))
    for bone in ARM_BONES:
        pose[bone] = A.aim_bone(arm, bone, rot_z3(I1.ARM_DIRS[bone], arm_yaw))
    return pose


def window_of(side, t):
    for index, (start, end) in enumerate(WINDOWS[side]):
        if start <= t <= end:
            return index
    return None


def target_sole(t, side):
    """该帧该脚的期望鞋底离地量（米）。支撑期 0，摆动期按包络。"""
    if side == "L":
        if t <= T_OFF or t >= T_LAND:
            return 0.0
        s = (t - T_OFF) / float(T_LAND - T_OFF)
        return LIFT_MOVER * math.sin(math.pi * s) ** 0.8
    if t <= T_PLANT:
        s = t / float(T_PLANT)
        return LIFT_PIVOT * math.sin(math.pi * s) ** 0.8
    return 0.0


def solve_pose(arm, t, meshes=None):
    """两遍**实测贴地闭环**；支撑窗口内的 shift 在窗口首帧**冻结**（A06 踩坑 5）。

    为什么冻结：逐帧追着鞋底最低点重算 shift 会形成**蒙皮反馈环** ——
    鞋顶点同时受 `shin` 权重影响，膝一弯顶点就动，闭环于是把踝一路往下拉。
    冻结后踝是世界常量，与 `anim_lib.no_foot_slide`（同按骨骼世界坐标量）口径一致。
    """
    shift = {"L": 0.0, "R": 0.0}
    for side in ("L", "R"):
        window = window_of(side, t)
        if window is not None and (side, window) in FROZEN:
            shift[side] = FROZEN[(side, window)]

    pose = build_pose(arm, t, shift)
    if meshes is None:
        return pose
    for _ in range(2):
        low = A.foot_lowest_by_side()
        error = {}
        for side in ("L", "R"):
            window = window_of(side, t)
            if window is not None and (side, window) in FROZEN:
                continue
            error[side] = target_sole(t, side) - low[side][2]
        if not error or max(abs(v) for v in error.values()) < 5e-5:
            break
        for side, value in error.items():
            shift[side] += value
        pose = build_pose(arm, t, shift)

    for side in ("L", "R"):
        window = window_of(side, t)
        if window is not None and (side, window) not in FROZEN:
            FROZEN[(side, window)] = shift[side]
    return pose


def measure_plant_z(arm):
    """测"鞋底恰好贴地"时的踝世界高度（单次测量，见 A06 踩坑 2）。"""
    pose = {"pelvis": (4.0, 0.0, 0.0), "spine_01": (2.0, 0.0, 0.0),
            "spine_02": (2.0, 0.0, 0.0), "chest": (1.0, 0.0, 0.0),
            "@loc": {"pelvis": A.wloc(0.0, 0.0, -0.070)}}
    A.apply_pose(arm, pose)
    leg_to(arm, pose, "L", (P_L[0], P_L[1], 0.120), (0.0, -1.0))
    orient_foot(arm, "foot.L", 0.0, 0.0)
    reached = A.bone_world(arm, "foot.L", "head")
    low = A.foot_lowest_by_side()["L"][2]
    return reached.z - low, round(abs(reached.z - 0.120) * 1000.0, 3)


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


def per_frame_probe(arm, action, frames, names):
    """逐帧读：指定骨的**世界朝向角**（投影法）+ 两只鞋的最低点。"""
    scene = bpy.context.scene
    previous = arm.animation_data.action if arm.animation_data else None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    heading = {name: [] for name in names}
    sole = {"L": [], "R": []}
    for frame in frames:
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for name in names:
            basis = arm.pose.bones[name].matrix.to_3x3()
            vector = basis @ Vector((1.0, 0.0, 0.0))
            heading[name].append(math.degrees(math.atan2(vector.y, vector.x)))
        low = A.foot_lowest_by_side()
        for side in ("L", "R"):
            sole[side].append(low[side][2])
    if previous is not None:
        arm.animation_data.action = previous
    return heading, sole


def cross_frame(series, frames, level):
    for value, frame in zip(series, frames):
        if value >= level:
            return frame
    return None


# =============================================================== 专属门禁
def turn_assertions(arm, action, samples, idle_mats):
    res = {}
    frames = [s["frame"] for s in samples]
    pelvis = [s["pelvis"] for s in samples]

    # 0) 首帧必须**逐位**等于 `Idle_01@0`（世界矩阵，不是 euler）。
    mats = action_world_matrices(arm, action, 0)
    delta = matrix_delta(mats, idle_mats)
    res["first_frame_delta"] = float("%.3e" % delta)
    res["first_frame_matches_idle_ok"] = delta <= 1e-6

    # 1) 朝向：髋/胸/头 的世界 yaw（投影法，不读 euler 分量）
    heading, sole = per_frame_probe(
        arm, action, frames, ("pelvis", "chest", "head"))
    hip, chest, head = heading["pelvis"], heading["chest"], heading["head"]

    res["yaw_first_deg"] = round(hip[0], 3)
    res["yaw_last_deg"] = round(hip[-1], 3)
    change = hip[-1] - hip[0]
    res["heading_change_deg"] = round(change, 3)
    res["heading_change_ok"] = abs(change - 90.0) <= 2.0

    # 2) **不是镜像瞬切**：yaw 在 (5°, 85°) 之间的帧数 ≥20。
    inside = sum(1 for v in hip if 5.0 < v < 85.0)
    res["transition_frames"] = inside
    res["not_mirror_instant_ok"] = inside >= 20

    # 3) 髋领先胸 ≥2 帧；头领先髋 ≥1 帧（都拿"过 45° 的帧"当相位尺）。
    frame_hip = cross_frame(hip, frames, 45.0)
    frame_chest = cross_frame(chest, frames, 45.0)
    frame_head = cross_frame(head, frames, 45.0)
    res["frame_at_45"] = {"hip": frame_hip, "chest": frame_chest,
                          "head": frame_head}
    res["hip_leads_chest_frames"] = (frame_chest - frame_hip
                                     if None not in (frame_hip, frame_chest)
                                     else None)
    res["hip_leads_chest_ok"] = (None not in (frame_hip, frame_chest)
                                 and frame_hip <= frame_chest - 2)
    res["head_leads_hip_frames"] = (frame_hip - frame_head
                                    if None not in (frame_hip, frame_head)
                                    else None)
    res["head_leads_hip_ok"] = (None not in (frame_hip, frame_head)
                                and frame_head <= frame_hip - 1)

    # 4) **轴心脚踝世界钉死 ≤3 mm**（骨架口径）。
    index = [i for i, f in enumerate(frames) if f >= T_PLANT]
    ankle = [Vector(samples[i]["foot.R"]) for i in index]
    travel = max((p - ankle[0]).length for p in ankle) * 1000.0
    res["pivot_ankle_travel_mm"] = round(travel, 3)
    res["pivot_foot_pinned_ok"] = travel <= 3.0
    # 只报不判：脚掌绕踝碾转必然带出脚趾扫掠；鞋底网格漂移同理（A06 踩坑 5）。
    toe = [Vector(samples[i]["toe.R"]) for i in index]
    res["pivot_toe_sweep_mm"] = round(
        max((p - toe[0]).length for p in toe) * 1000.0, 2)
    res["pivot_sole_range_mm"] = round(
        (max(sole["R"][i] for i in index)
         - min(sole["R"][i] for i in index)) * 1000.0, 2)

    # 5) **换步**：非轴心脚绕轴心脚扫过的角度 ≥60°，且落点在轴心脚另一侧。
    def angle_around_pivot(point):
        return ang_deg((point[0] - P_R[0], point[1] - P_R[1]))

    base = angle_around_pivot(P_L)
    swept = 0.0
    for i, f in enumerate(frames):
        if not (T_OFF <= f <= T_LAND):
            continue
        value = angle_around_pivot((samples[i]["foot.L"][0],
                                    samples[i]["foot.L"][1]))
        swept = max(swept, abs(value - base))
    res["step_around_deg"] = round(swept, 2)
    res["step_around_ok"] = swept >= 60.0

    # 6) **全程至少一脚支撑**（两只脚同时离地 = 跳跃，不是转身）。
    contact = 0.003
    airborne = [f for i, f in enumerate(frames)
                if sole["L"][i] > contact and sole["R"][i] > contact]
    res["airborne_frames"] = airborne
    res["always_support_ok"] = len(airborne) == 0

    # 7) 原地：骨盆水平行程（清单 §0.4"防自带位移"）。
    span = max(math.hypot(p[0] - pelvis[0][0], p[1] - pelvis[0][1])
               for p in pelvis) * 1000.0
    net = math.hypot(pelvis[-1][0] - pelvis[0][0],
                     pelvis[-1][1] - pelvis[0][1]) * 1000.0
    res["pelvis_span_mm"] = round(span, 2)
    res["pelvis_net_mm"] = round(net, 3)
    res["pelvis_in_place_ok"] = span <= 60.0 and net <= 5.0

    # 8) 收招不许瞬停：末 6 帧角度增量绝对值单调收敛。
    deltas = []
    tail_bones = []
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

    # 9) 末帧站姿：落进新朝向的战斗站姿。
    last = samples[-1]
    lx, ly = last["foot.L"][0], last["foot.L"][1]
    rx, ry = last["foot.R"][0], last["foot.R"][1]
    res["stance_last_mm"] = {"L": [round(lx * 1000.0, 1), round(ly * 1000.0, 1)],
                             "R": [round(rx * 1000.0, 1), round(ry * 1000.0, 1)]}
    width = math.hypot(lx - rx, ly - ry) * 1000.0
    res["stance_width_mm"] = round(width, 1)
    # 新朝向 = +X，角色左 = +Y：前脚 L 应在 R 的 +X（前）侧、且两脚有横向间距
    res["stance_ok"] = (width >= 0.18 and (lx - rx) >= 0.10
                        and abs(ly - ry) >= 0.08)
    res["stance_width_narrow_note"] = (
        "轴心脚收到中线后两脚天然更近；Idle_01 踏宽 300 mm，本支末帧 "
        "%d mm" % round(width))

    # 10) 力量传导链：脚→腿→髋→腰→肩→手，不许"只有手在动"。
    res.update(WF.power_chain(samples))
    return res


# =============================================================== 主流程
def main():
    global L_END, Z_PLANT

    from mathutils import Matrix as _M
    turn = 90.0
    # 非轴心脚落点 = 绕轴心脚刚性转 90°（保证与 P_L 到 P_R 的距离**严格相等**）
    L_END = rot_about(P_R, turn, P_L)

    FROZEN.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("TURN_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    Z_PLANT, reach_err = measure_plant_z(arm)
    A.report("TURN_CALIBRATION", {
        "plant_z_mm": round(Z_PLANT * 1000.0, 3),
        "reach_err_mm": reach_err,
        "pivot_P_R_mm": [round(v * 1000.0, 1) for v in P_R],
        "mover_L_END_mm": [round(v * 1000.0, 1) for v in L_END],
        "mover_arc_radius_mm": round(
            math.hypot(P_L[0] - P_R[0], P_L[1] - P_R[1]) * 1000.0, 1),
        "mover_arc_deg": round(abs(
            ang_deg((L_END[0] - P_R[0], L_END[1] - P_R[1]))
            - ang_deg((P_L[0] - P_R[0], P_L[1] - P_R[1]))), 2),
    })

    # 首帧 = Idle_01@0（逐位衔接）
    first_pose = I1.idle_pose(arm, 0.0)

    keyframes = [(0, first_pose)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "基础移动",
        "note": ("原地转身 90°：头/眼先转 → 髋领先胸 2 帧 → 非轴心脚绕轴心脚"
                 "跨过去；轴心脚踝世界钉死 ≤3 mm"),
        "turn_deg": turn,
        "pivot_foot": "R",
        "pivot_plant_frame": T_PLANT,
        "antic_frame": T_OFF,
        "hit_frame": None,
        "cancel_frame": 24,
        "hitstop_frames": 0,
        "root_motion_m": [0.0, 0.0],
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {
        "START": 0, "HEAD_LEAD": 3, "PIVOT_PLANT": T_PLANT, "ANTIC_END": T_OFF,
        "STEP_AROUND": 15, "LAND": T_LAND, "RECOV_END": 26, "SETTLE_END": TOTAL,
    })

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    # foot_probe 置空：通用门禁的"脚位移 ≤3 mm"要按**支撑窗口**分窗判
    # （本支两只脚本来就各自要跨步/碾转），改用专属 `pivot_foot_pinned_ok`。
    report = A.run_common_assertions(samples, meta, foot_probe=())

    idle_mats = action_world_matrices(arm, bpy.data.actions["Idle_01"], 0)
    report.update(turn_assertions(arm, action, samples, idle_mats))
    report["meta"] = meta
    failed = sorted(k for k, v in report.items()
                    if k.endswith("_ok") and v is not True)
    report["failed"] = failed
    A.report("TURN_REPORT", report)

    if not SKIP_RENDER:
        # 侧视看"髋先转 / 换步 / 收势"；3/4 视最能看清"绕轴心脚跨过去"。
        A.render_pose_sheet(arm, action, [0, 3, 6, 9, 13, 17, 22, 26, 30],
                            "turn", views=(A.VIEW_SIDE,))
        A.render_pose_sheet(arm, action, [0, 6, 13, 22, 30], "turn",
                            views=(A.VIEW_3Q,))
    A.save_project()
    A.export_glb(arm)
    print("TURN_DONE failed=%s" % failed)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("TURN_FAILURE " + traceback.format_exc())
