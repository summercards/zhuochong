"""anim_grab05 —— C05 `Grab_Hold` 抓住循环（C 族第五支，**循环动画**）。

=============================================================================
清单原文
=============================================================================
「控制敌人时的短循环动画」。

=============================================================================
第 0 件 —— 这支与 C04 的**根本区别**（认清了再动手）
=============================================================================
C04 是**一次性动作**（进了就出）；C05 是**循环**（`loop = True`）。三条后果：

1. **首尾必须逐位一致**：`loop_seamless` 逐骨比 `euler`（≤0.5°）+ 逐 `PROBE_KEYS`
   比世界坐标（≤0.5 mm）。C04 的末帧（f54）本来就是 `SETTLE` 常值，所以 C05 的
   首帧**直接取 C04 末帧**、末帧再取同一个值，循环闭合是构造出来的。
2. **抓取点全程不许动**：C05 的语义是「抓住并控制敌人」，双手必须钉死在 C04
   登记的抓取点上（漂移 ≤3 mm）。C04 的 `arm_seat` 已经证明能做到
   0.0006 mm —— 本支沿用同一条逆解路径与同一个滚转基准 `ARM_REF`。
3. **身体只做呼吸级微动**：髋/胸腔的小幅起伏 + 手指的握紧放松；手臂本身由
   位置逆解接管，敌人不会在手里晃。

=============================================================================
第 1 件 —— 接缝：上游 = **C04 `Grab_Start` 的末帧（f54）**，首次「上游是自己刚做完的一支」
=============================================================================
这是本链最硬的一条接缝：`SEAM_TOL = 1e-6`，且 `grab_anchor_ok` 要求
**末帧**也逐位等于 C04 末帧（因为下游 C06 `Throw` 要从持握姿起手）。

做法不是「再算一遍希望对上」，而是**读 Action 的真值**：
把 `Grab_Start` 绑到骨架上、`frame_set(54)`，逐骨抄下 `rotation_euler`
（度）与 `pelvis.location`，组成 `SEAM_POSE`；首帧与末帧都用它**逐位**写入。
于是 `seam_start_delta` 与 `grab_anchor_delta` 都是 0，不靠运气。

=============================================================================
第 2 件 —— ★★ 可达余量只有 18.5 mm：呼吸**只能往"更近"的方向做**
=============================================================================
`probe_c05_baseline.py` 实测 C04 末帧：

    肩→抓取点   L 629.20 mm / R 631.19 mm
    臂长上限    L/R 649.675 mm       （(328 + 224 + 98) × 0.9995）
    **余量      L 20.47 mm / R 18.49 mm**

C04 第 1~2 件已经证明：`arm_seat` 一旦截断，手就**同步**离开抓取点
（`grab_hold_drift` = 截断量，逐位吻合）。所以呼吸幅度不是"看着差不多"定的，
而是"**不许把肩推向远处**"这个约束定出来的：

  · **骨盆 rx 恒定 14°**（不动）—— 它是最长的杠杆（肩在骨盆上方 660 mm），
    1° 就搬动肩 ~11 mm，直接吃掉余量。这条与 A01/A09 的结论同源：
    「呼吸是胸腔的事，骨盆不参与」。
  · 允许动的量全部选**把肩往前送**的方向：`chest rx +`（前倾）、
    `spine_02 rx +`（前倾）。实测肩因此**靠近**抓取点 1~3 mm/帧量级 ⟹ 最大
    距离仍等于基座距离 ⟹ 余量不被吃掉。
  · `pelvis z` 升降是**竖向**的，对"肩→抓取点"距离的敏感度只有 0.45 mm/mm
    （dz/dist = 0.285/0.635）⟹ 5 mm 呼吸只换来 0.5 mm 距离变化。它是本支
    **最主要、也最安全**的可见呼吸量。

=============================================================================
第 3 件 —— 头朝向：base 只差 1.33°，所以 `head_track_ok` 是**可满足**的
=============================================================================
清单计划给 `head_track_ok` 定的口径是「头部朝向全程对着抓取点，世界朝向偏差
≤8°」。这句能不能满足，取决于 C04 末帧的头到底朝哪 ——**先量再写**（探测结果）：

    面朝方向（rest −Y 用 head 世界 3×3 转出）= (−0.0043, −0.8480, −0.5299)
    眼→抓取点方向                              = ( 0.0035, −0.8362, −0.5484)
    **夹角 1.3309°**

C04 确实把视线转正盯住了敌人（文件头第 1 件）。既然 base 只差 1.33°，本支
只要**不把头的俯仰搞坏**就行：颈/头在吸气时各回 0.6° / 1.0°，净俯仰变化
+1.1°（胸 +1.8° + 腰 +0.9° − 颈 0.6° − 头 1.0°）⟹ 夹角变化 ~1°，全程 ≤3°。

=============================================================================
第 4 件 —— 判据的取舍：`hitstop_present_ok` **必须去掉**（不许造一个假绿）
=============================================================================
清单计划沿用 C04 全套判据并删掉 `antic_frames_ok` / `hitstop_frames_ok` /
`hitstop_keeps_momentum_ok` / `decel_smooth_ok`（C05 没有前摇/命中/后摇）。
但 `hitstop_present_ok` 的构造是「命停窗内旋转逐位冻结」——

    bool(frozen) and max(frozen) <= 1e-6

C05 **没有命停窗**，`frozen` 恒为空 ⟹ `bool([]) = False` ⟹ **恒红**。这不是
"某支没做好"，是这个判据在本支**没有指称对象**（同 `decel_smooth_ok` 之于循环）。
留着它只能靠改写成恒 True 来凑绿，那正是 §6 禁止的事。⟹ **删掉**，并在报告里
把删除清单登记进 `dropped_assertions`，不放宽任何一条其余判据。

`no_snap_stop_ok` 同理要换口径：循环没有"收招末段"，真正要守的是
**循环点两侧速度都≈0**（呼吸曲线两端平出平入，否则连播会"卡一下"）。
改用同一名字、口径换成 `max(首帧步长, 末帧步长) ≤ 0.5°`。

=============================================================================
运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python anim_grab05.py
    SKIP_RENDER=1 只跑门禁（迭代用）；C05_TRACE=1 打逐帧轨迹。
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402
import anim_run_stop as RS      # noqa: E402
import anim_jump_start as JS    # noqa: E402
import anim_grab04 as G4        # noqa: E402

NAME = "Grab_Hold"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
C04_FRAME = 54                                  # Grab_Start 末帧（上游接缝）
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
TOTAL = _env_i("C05_TOTAL", 120)                # 2.000 s @60fps（循环）
# 呼吸关键帧：(帧, 幅度)。0 = 呼气末（= C04 末帧），1 = 吸气峰。
# 吸 0.8 s / 顶尖保持 0.4 s / 呼 0.8 s —— 与 A09 同形（A09 是 A01 的 2/3 压缩）。
BREATH_KEYS = ((0, 0.0), (_env_i("C05_PEAK", 48), 1.0),
               (_env_i("C05_PEAK_END", 72), 1.0), (TOTAL, 0.0))

# ---------------------------------------------------------------- 呼吸幅度
# ★ 取值依据见文件头第 2 件（余量 18.5 mm ⟹ 只往"更近"的方向做）。
# ★ 第 2 轮的取舍：肩峰起伏是本支**最容易被看见**的通道，第 1 轮只给了 1.2°
#   （实测肩峰只走 0.43 mm —— 因为"胸腔前倾"会同量把肩往下压，两者抵消）。
#   改成 ①胸腔只留 +0.9° 前倾（保住"重量压向敌人"的读感）、②肩峰 +2.6°。
#   实测肩峰行程 0.43 → **4.15 mm**（落进 A01 的 3~20 mm 读感带），
#   而 `grab_reach_ratio` **逐位不变**（0.96801 / 0.97106）——
#   原因是最大可达比恒在 `breath = 0` 那一帧取得，呼吸只会把肩往前送。
PELVIS_Z_AMP = _env_f("C05_PZ", 0.0050)         # 骨盆升降 5 mm（竖向，最安全）
CHEST_AMP = _env_f("C05_CH", 0.9)               # 胸腔前倾（把肩往前送）
SPINE02_AMP = _env_f("C05_S2", 0.9)             # 腰二段前倾（同上）
NECK_AMP = _env_f("C05_NK", -0.9)               # 颈/头各回 0.9°，把俯仰拉平
HEAD_AMP = _env_f("C05_HD", -0.9)
SHOULDER_AMP = _env_f("C05_SH", 2.6)            # 肩峰随呼吸起伏（读感的一半）
FINGER_AMP = _env_f("C05_FG", 0.15)             # 握力周期：1.0 → 0.85 → 1.0

# ---------------------------------------------------------------- 门禁阈值
SEAM_TOL = 1e-6
ANCHOR_TOL = 1e-6
SOLE_RANGE_MM = (-2.0, 6.0)
PIVOT_DRIFT_MAX_MM = 3.0
GRAB_HOLD_DRIFT_MAX_MM = 3.0
GRAB_REACH_MAX_RATIO = 0.995
REACH_MAX_RATIO = 0.995
NO_TELEPORT_MAX_DEG = 25.0
FEET_PINNED_MAX_MM = 3.0
PELVIS_HORIZONTAL_MAX_MM = 1.0
HEAD_TRACK_MAX_DEG = 8.0
BREATH_MIN_MM = 1.0
BREATH_VISIBLE_RANGE_MM = (3.0, 30.0)
FINGER_MIN_DEG = 0.5
LOOP_SEAM_STEP_MAX_DEG = 0.5

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
FINGER_BONES = tuple(name for name in A.FIST)
WINDOWS = {"L": ((0, TOTAL),), "R": ((0, TOTAL),)}   # 双脚全程支撑

# ---------------------------------------------------------------- 模块级状态
SEAM_POSE = {}       # 完整姿态（apply_pose 直接可用）
BASE_RX = {}         # 躯干链基座 rx（度）
BASE_RY = {}
BASE_RZ = {}
GRAB_POINT = {}      # side -> Vector（世界，米）
GRAB_ELBOW = {}      # side -> 单位方向
ARM_REF = {}         # bone -> (基准 3×3, 基准方向)
ANKLE = {}           # side -> Vector（世界，米）：脚钉死在这里
PELVIS_W = None      # Vector（世界，米）：C04 末帧骨盆位置，取景跟随用
IDLE_KNEE_DIR = {}
IDLE_BASIS = {}
IDLE_DIR = {}
ARM_SEAT_CLAMP = {}
PIVOT_VERT = {}
WINDOW_SOLE = {}
ALL_SOLE = {}
C04_MATS = {}
C04_META = {}


def _smoothstep(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def breath_at(frame):
    """分段 smoothstep 呼吸包络。

    ★ 为什么不用 `RS.track`：它只把**末段**切线置 0、首段用割线斜率，于是
      循环点的两侧速度不等（末帧平着滑进来、首帧斜着冲出去）—— `loop_seamless`
      量不出来（它只比姿态），但连播里读作"呼吸卡了一下"。
      smoothstep 在每个键上速度天然为 0，循环点真正闭合。
    """
    keys = BREATH_KEYS
    if frame <= keys[0][0]:
        return keys[0][1]
    if frame >= keys[-1][0]:
        return keys[-1][1]
    for index in range(len(keys) - 1):
        fa, va = keys[index]
        fb, vb = keys[index + 1]
        if fa <= frame <= fb:
            span = float(fb - fa)
            if span <= 0.0:
                return vb
            return va + (vb - va) * _smoothstep((frame - fa) / span)
    return keys[-1][1]


# =============================================================== 姿态
def c05_pose(arm, frame):
    """抓握保持基座 + 呼吸微动 + 手指握力周期。

    `breath = 0` 时**逐位**等于 `Grab_Start@54`：躯干轨道取基座值不加偏移，
    腿由 `leg_seat` 解到同一组踝目标，臂由 `arm_seat` 解到同一组抓取点。
    （首/末帧不走这里，直接写 `SEAM_POSE`，见文件头第 1 件。）
    """
    b = breath_at(frame)
    pose = {key: value for key, value in SEAM_POSE.items() if key != "@loc"}
    base_loc = SEAM_POSE["@loc"]["pelvis"]

    # 躯干：基座 + 呼吸偏移。★ 骨盆 rx/ry/rz **恒定**（文件头第 2 件）。
    pose["chest"] = (BASE_RX["chest"] + CHEST_AMP * b,
                     BASE_RY["chest"], BASE_RZ["chest"])
    pose["spine_02"] = (BASE_RX["spine_02"] + SPINE02_AMP * b,
                        BASE_RY["spine_02"], BASE_RZ["spine_02"])
    pose["neck"] = (BASE_RX["neck"] + NECK_AMP * b,
                    BASE_RY["neck"], BASE_RZ["neck"])
    pose["head"] = (BASE_RX["head"] + HEAD_AMP * b,
                    BASE_RY["head"], BASE_RZ["head"])
    pose["shoulder.L"] = (BASE_RX["shoulder.L"] + SHOULDER_AMP * b,
                          BASE_RY["shoulder.L"], BASE_RZ["shoulder.L"])
    pose["shoulder.R"] = (BASE_RX["shoulder.R"] + SHOULDER_AMP * b,
                          BASE_RY["shoulder.R"], BASE_RZ["shoulder.R"])
    # 骨盆位移：局部 Y ↔ 世界 +Z ⟹ 呼吸升降只动局部 Y。
    pose["@loc"] = {"pelvis": (base_loc[0],
                               base_loc[1] + PELVIS_Z_AMP * b,
                               base_loc[2])}

    A.apply_pose(arm, pose)

    # 腿：真两骨逆解到**钉死的踝世界目标** ⟹ 骨盆怎么起伏，脚都不动。
    for side in SIDES:
        G4.leg_seat(arm, pose, side, ANKLE[side], IDLE_KNEE_DIR[side])

    # 足：钉平到世界水平（同 C04；本支不踮脚 ⟹ tip 恒 0）。
    for side in SIDES:
        name = "foot." + side
        A.keep_world_orientation(arm, name)
        pose[name] = JS._unwrap_xyz(
            JS._PREV_EULER.get(name),
            tuple(math.degrees(v)
                  for v in arm.pose.bones[name].rotation_euler))

    # 臂：位置逆解钉死在世界抓取点，滚转沿用 C04 的基准（文件头第 2 件）。
    for side in SIDES:
        info = ARM_SEAT_CLAMP.setdefault(
            side, {"any": False, "worst_frame": None, "worst_over_mm": 0.0,
                   "worst_dist_mm": 0.0, "limit_mm": 0.0, "n_frames": 0})
        clamp, dist_mm, limit_mm = G4.arm_seat(
            arm, pose, side, GRAB_POINT[side], GRAB_ELBOW[side], ref=ARM_REF)
        info["limit_mm"] = round(limit_mm, 3)
        info["n_frames"] += 1
        if clamp:
            info["any"] = True
            over = dist_mm - limit_mm
            if over > info["worst_over_mm"]:
                info["worst_frame"] = frame
                info["worst_over_mm"] = round(over, 3)
                info["worst_dist_mm"] = round(dist_mm, 3)

    # 手指：握紧 → 略松 → 握紧（唯一"读得出还在使劲"的通道）。
    k = 1.0 - FINGER_AMP * b
    for name, value in A.FIST.items():
        pose[name] = (value[0] * k, 0.0, 0.0)

    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


# =============================================================== 测量
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
            name: Matrix([raw[name][i * 4:i * 4 + 3] for i in range(3)])
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


def _unit(vector):
    length = math.sqrt(sum(v * v for v in vector)) or 1.0
    return tuple(v / length for v in vector)


def _ang(a, b):
    return math.degrees(math.acos(max(-1.0, min(1.0,
                                                 sum(x * y for x, y in zip(a, b))))))


def _face_axis(arm):
    """head 骨当前的世界「面朝方向」：把 rest 的 −Y 用 head 世界 3×3 转出来。

    ★ 为什么要这么绕：`head` 骨是**竖着**的（骨轴朝上），量骨轴方向得到的是
      "头有没有歪"，不是"眼睛看哪"。竖骨要拿一个横向参考轴才读得出朝向
      （A01 踩坑 2 的同族问题）。
    """
    pose_bone = arm.pose.bones["head"]
    rest_basis = pose_bone.bone.matrix_local.to_3x3()
    local_face = rest_basis.inverted() @ Vector((0.0, -1.0, 0.0))
    return _unit(pose_bone.matrix.to_3x3() @ local_face)


# =============================================================== 专属门禁
def c05_assertions(arm, action, samples, foots, tracks):
    res = {}
    pelvis = [Vector(f["pelvis"]) for f in foots]
    pz = [p.z * 1000.0 for p in pelvis]

    # ---- 0) 上游接缝：C05@0 必须**逐位**等于 Grab_Start@54
    mats0 = RS.action_world_matrices(arm, action, 0)
    delta0 = RS.matrix_delta(mats0, C04_MATS)
    res["seam_source"] = [G4.NAME, C04_FRAME]
    res["seam_start_delta"] = float("%.3e" % delta0)
    res["seam_start_ok"] = delta0 <= SEAM_TOL

    # ---- 1) ★ 抓取锚点：C05@TOTAL 也必须逐位等于 Grab_Start@54
    mats_n = RS.action_world_matrices(arm, action, TOTAL)
    delta_n = RS.matrix_delta(mats_n, C04_MATS)
    res["grab_anchor_delta"] = float("%.3e" % delta_n)
    res["grab_anchor_ok"] = delta_n <= ANCHOR_TOL
    res["anchor_note"] = ("下游 C06 `Throw` 尚未生产 ⟹ 末帧锚点以"
                          "「逐位等于 C04 `Grab_Start@54`」为准；"
                          "C06 直接从这个持握姿起手。")

    # ---- 2) 抓取点（沿用 C04 登记值，本支不许改动它）
    points = {s: [round(v, 6) for v in GRAB_POINT[s]] for s in SIDES}
    res["grabbed_points_m"] = points
    res["grabbed_point_registered_m"] = {
        "L": C04_META.get("grabbed_point_L_m"),
        "R": C04_META.get("grabbed_point_R_m")}
    res["grab_gap_mm"] = round(
        (Vector(GRAB_POINT["L"]) - Vector(GRAB_POINT["R"])).length * 1000.0, 2)
    res["grab_z_mm"] = round(
        (GRAB_POINT["L"].z + GRAB_POINT["R"].z) * 0.5 * 1000.0, 2)
    res["grab_depth_mm"] = round(
        ((GRAB_POINT["L"].y + GRAB_POINT["R"].y) * 0.5
         - pelvis[0].y) * 1000.0, 2)
    pelvis_hold = Vector(foots[0]["pelvis"])
    res["grabbed_points_rel_pelvis_mm"] = {
        s: [round((v - pelvis_hold[i]) * 1000.0, 2) for i, v in
            enumerate(GRAB_POINT[s])] for s in SIDES}
    res["grab_points_ok"] = all(
        len(points[s]) == 3 and any(abs(v) > 1e-9 for v in points[s])
        for s in SIDES)

    # ---- 3) ★ 抓住之后手不许再滑（口径同 C04，窗口换成整段循环）
    drift = {}
    worst_at = {}
    for side in SIDES:
        ref = Vector(GRAB_POINT[side])
        vals = [(Vector(foots[f]["hand_" + side + "_tail"]) - ref).length
                for f in range(0, TOTAL + 1)]
        drift[side] = round(max(vals) * 1000.0, 5)
        worst_at[side] = int(vals.index(max(vals)))
    res["grab_hold_drift_mm"] = drift
    res["grab_hold_drift_at"] = worst_at
    res["grab_hold_drift_max_mm"] = round(max(drift.values()), 5)
    res["grab_hold_steady_ok"] = max(drift.values()) <= GRAB_HOLD_DRIFT_MAX_MM

    # ---- 4) 可达比 & 逆解不许截断
    arm_len = {}
    ratio = {}
    for side in SIDES:
        total = (G4.ARM_LEN[side]["upper"] + G4.ARM_LEN[side]["forearm"]
                 + G4.ARM_LEN[side]["hand"])
        arm_len[side] = round(total * 1000.0, 3)
        ratio[side] = round(max(float(f["armreach_" + side])
                                for f in foots) / total, 5)
    res["arm_total_len_mm"] = arm_len
    res["grab_reach_ratio"] = ratio
    res["grab_reach_ratio_base"] = {
        side: round(float(foots[0]["armreach_" + side])
                    / (G4.ARM_LEN[side]["upper"] + G4.ARM_LEN[side]["forearm"]
                       + G4.ARM_LEN[side]["hand"]), 5) for side in SIDES}
    res["grab_reach_ok"] = all(v <= GRAB_REACH_MAX_RATIO
                               for v in ratio.values())
    res["arm_seat_clamped"] = {s: bool(v.get("any"))
                               for s, v in ARM_SEAT_CLAMP.items()}
    res["arm_seat_detail"] = {s: dict(v) for s, v in ARM_SEAT_CLAMP.items()}
    res["arm_seat_ok"] = not any(v.get("any")
                                 for v in ARM_SEAT_CLAMP.values())

    # ---- 5) ★ 呼吸必须看得见（`breath_amplitude_ok`：不许是死帧）
    breath = max(pz) - min(pz)
    res["pelvis_z_min_mm"] = round(min(pz), 3)
    res["pelvis_z_max_mm"] = round(max(pz), 3)
    res["pelvis_breath_mm"] = round(breath, 3)
    res["breath_amplitude_ok"] = breath >= BREATH_MIN_MM

    sternum = [Vector(f["neck"]) for f in foots]
    travel = max((c - sternum[0]).length for c in sternum) * 1000.0
    res["chest_breath_mm"] = round(travel, 2)
    res["breath_visible_ok"] = (BREATH_VISIBLE_RANGE_MM[0] <= travel
                                <= BREATH_VISIBLE_RANGE_MM[1])
    shoulder = [Vector(s["upperarm.L"]) for s in samples]
    res["shoulder_rise_mm"] = round(
        (max(p.z for p in shoulder) - min(p.z for p in shoulder)) * 1000.0, 2)

    # ---- 6) ★ 手指握力周期（不许是固定握拳的死循环）
    finger_travel = {}
    for name in FINGER_BONES:
        vals = [s["euler"].get(name, (0.0, 0.0, 0.0))[0] for s in samples]
        finger_travel[name] = round(max(vals) - min(vals), 4)
    res["finger_travel_deg"] = finger_travel
    res["finger_travel_max_deg"] = round(max(finger_travel.values()), 4)
    res["fingers_cycle_ok"] = max(finger_travel.values()) >= FINGER_MIN_DEG

    # ---- 7) ★ 头朝向全程对着抓取点
    grab_mid = (Vector(GRAB_POINT["L"]) + Vector(GRAB_POINT["R"])) * 0.5
    angs = []
    for f in foots:
        eye = Vector(f["head"]).lerp(Vector(f["head_tail"]), 0.55)
        angs.append(_ang(_face_axis(arm_at_action(arm, action, f["frame"])),
                         _unit(grab_mid - eye)))
    res["head_track_max_deg"] = round(max(angs), 4)
    res["head_track_min_deg"] = round(min(angs), 4)
    res["head_track_ok"] = max(angs) <= HEAD_TRACK_MAX_DEG

    # ---- 8) 支撑脚：不改写世界坐标的两个口径
    feet = {}
    for side in SIDES:
        points_side = [Vector(f["ankle_" + side]) for f in foots]
        feet[side] = round(max((p - points_side[0]).length
                               for p in points_side) * 1000.0, 4)
    res["feet_pinned_mm"] = feet
    res["feet_pinned_ok"] = all(v <= FEET_PINNED_MAX_MM for v in feet.values())

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
                   if all(not (a <= f <= b) for a, b in WINDOWS["L"])
                   and all(not (a <= f <= b) for a, b in WINDOWS["R"])]
    res["unsupported_frames"] = unsupported
    res["always_supported_ok"] = not unsupported

    # ---- 9) 原地：骨盆水平行程必须≈0（只有竖向呼吸）
    hspan = max(math.hypot(p.x - pelvis[0].x, p.y - pelvis[0].y)
                for p in pelvis) * 1000.0
    res["pelvis_horizontal_span_mm"] = round(hspan, 4)
    res["pelvis_in_place_ok"] = hspan <= PELVIS_HORIZONTAL_MAX_MM
    res["root_motion_m"] = [0.0, round(pelvis[-1].y - pelvis[0].y, 6)]

    # ---- 10) 力矩链（C05 是保持姿，各通道基座值直接非零）
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
        peak = max(f["reach_" + side] for f in foots)
        ratios[side] = round(peak / limit, 5)
    res["leg_reach_max_ratio"] = ratios
    res["ik_reach_ok"] = all(v <= REACH_MAX_RATIO for v in ratios.values())

    # ---- 12) ★ 循环点速度：两侧都≈0 才算闭合（口径见文件头第 4 件）
    first_step = 0.0
    last_step = 0.0
    for name in set(samples[1]["euler"]) | set(samples[0]["euler"]):
        a = samples[0]["euler"].get(name, (0.0, 0.0, 0.0))
        b = samples[1]["euler"].get(name, (0.0, 0.0, 0.0))
        first_step = max(first_step, max(abs(u - v) for u, v in zip(a, b)))
    for name in set(samples[-1]["euler"]) | set(samples[-2]["euler"]):
        a = samples[-2]["euler"].get(name, (0.0, 0.0, 0.0))
        b = samples[-1]["euler"].get(name, (0.0, 0.0, 0.0))
        last_step = max(last_step, max(abs(u - v) for u, v in zip(a, b)))
    res["loop_seam_steps_deg"] = [round(first_step, 5), round(last_step, 5)]
    res["no_snap_stop_ok"] = max(first_step, last_step) <= LOOP_SEAM_STEP_MAX_DEG

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

    # ---- 14) 判据取舍登记（文件头第 4 件）
    res["dropped_assertions"] = ["antic_frames_ok", "hitstop_present_ok",
                                 "hitstop_frames_ok",
                                 "hitstop_keeps_momentum_ok",
                                 "decel_smooth_ok"]
    res["dropped_reason"] = ("C05 是循环保持姿，没有前摇/命中/后摇/收招；"
                             "`hitstop_present_ok` 的「命停窗逐位冻结」在此"
                             "无指称对象（空窗恒红）⟹ 删除，不放宽其余判据。")
    return res


def arm_at_action(arm, action, frame):
    """把 action 绑到骨架并停在 frame，返回骨架（供头朝向测量复用）。"""
    scene = bpy.context.scene
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    return arm


# =============================================================== 主流程
def main():
    global SEAM_POSE, BASE_RX, BASE_RY, BASE_RZ
    global GRAB_POINT, GRAB_ELBOW, ARM_REF, ANKLE
    global IDLE_KNEE_DIR, IDLE_BASIS, IDLE_DIR, C04_MATS, C04_META, PELVIS_W

    for store in (ARM_SEAT_CLAMP, PIVOT_VERT, WINDOW_SOLE, ALL_SOLE):
        store.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()

    if I1.NAME not in bpy.data.actions:
        print("C05_BOOTSTRAP 动画工程缺 Idle_01，先补跑 A01")
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()
    if G4.NAME not in bpy.data.actions:
        print("C05_BOOTSTRAP 动画工程缺 Grab_Start，先补跑 C04")
        G4.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # 骨长实测：`arm_seat` 的 L1 / L2+L3 用它（不准 = 手落不到抓取点）
    G4.ARM_LEN.clear()
    for side in SIDES:
        G4.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
    if "thigh.L" not in A.PROBE_BONES:
        A.PROBE_BONES = tuple(A.PROBE_BONES) + ("thigh.L", "thigh.R",
                                                "shin.L", "shin.R")
        A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail"
                                             for n in A.PROBE_TAILS)

    # ---- 上游接缝：直接读 Grab_Start@54 的**真值**（文件头第 1 件）
    scene = bpy.context.scene
    c04 = bpy.data.actions[G4.NAME]
    arm_at_action(arm, c04, C04_FRAME)
    euler = {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
             for b in arm.pose.bones}
    loc = {b.name: tuple(b.location) for b in arm.pose.bones
           if any(abs(v) > 1e-12 for v in b.location)}
    SEAM_POSE = dict(euler)
    SEAM_POSE["@loc"] = dict(loc)
    BASE_RX = {name: euler[name][0] for name in
               ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")}
    BASE_RY = {name: euler[name][1] for name in BASE_RX}
    BASE_RZ = {name: euler[name][2] for name in BASE_RX}

    PELVIS_W = A.bone_world(arm, "pelvis", "head").copy()
    for side in SIDES:
        GRAB_POINT[side] = A.bone_world(arm, "hand." + side, "tail").copy()
        sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        el = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        GRAB_ELBOW[side] = (el - sh).normalized()
        ANKLE[side] = A.bone_world(arm, "foot." + side, "head").copy()
    ARM_REF.clear()
    for bone in ARM_BONES:
        ARM_REF[bone] = (arm.pose.bones[bone].matrix.to_3x3().copy(),
                         A.bone_direction(arm, bone))
    C04_MATS = RS.action_world_matrices(arm, c04, C04_FRAME)
    C04_META = {}
    for key in ("grabbed_point_L_m", "grabbed_point_R_m", "grab_frame",
                "grab_hold_frame", "grab_reach_ratio"):
        try:
            value = c04[key]
            C04_META[key] = (list(value) if hasattr(value, "__len__")
                             and not isinstance(value, str) else value)
        except (KeyError, TypeError):
            C04_META[key] = None

    # ---- 站架与骨基座：Idle@0（腿的 `leg_seat` 缺省基准要它）
    arm_at_action(arm, bpy.data.actions[I1.NAME], 0)
    A.apply_pose(arm, I1.idle_pose(arm, 0.0))
    bpy.context.view_layer.update()
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
    # `G4.leg_seat` 在 ref=None 时读 G4 模块自己的 IDLE_BASIS / IDLE_DIR
    G4.IDLE_BASIS.clear()
    G4.IDLE_BASIS.update(IDLE_BASIS)
    G4.IDLE_DIR.clear()
    G4.IDLE_DIR.update(IDLE_DIR)
    G4.IDLE_KNEE_DIR.clear()
    G4.IDLE_KNEE_DIR.update(IDLE_KNEE_DIR)

    A.report("C05_LAYOUT", {
        "total_frames": TOTAL,
        "seconds": round(TOTAL / float(A.FPS), 3),
        "loop": True,
        "breath_keys": [list(k) for k in BREATH_KEYS],
        "seam_source": [G4.NAME, C04_FRAME],
        "grabbed_points_m": {s: [round(v, 6) for v in GRAB_POINT[s]]
                             for s in SIDES},
        "registered_points_m": C04_META,
        "ankle_mm": {s: [round(v * 1000.0, 3) for v in ANKLE[s]]
                     for s in SIDES},
        "base_trunk_rx_deg": BASE_RX,
        "amplitudes": {"pelvis_z_mm": PELVIS_Z_AMP * 1000.0,
                       "chest_deg": CHEST_AMP, "spine02_deg": SPINE02_AMP,
                       "neck_deg": NECK_AMP, "head_deg": HEAD_AMP,
                       "shoulder_deg": SHOULDER_AMP, "finger": FINGER_AMP},
        "note": ("抓握保持循环：首帧 = 末帧 = `Grab_Start@54`（逐位），"
                 "双手位置逆解钉死在世界抓取点，双腿逆解钉死在踝世界目标，"
                 "呼吸只走胸/腰二段前倾 + 骨盆竖向升降（骨盆倾角恒定）。"),
    })

    # ---- 关节点标定：鞋底前缘顶点（`stance_pivot_ok` 用）
    torso_base = dict(SEAM_POSE)
    for side in SIDES:
        px, py, pz, ax0, ay0, az0, vobj, vindex = G4.measure_pivot(
            arm, side, (ANKLE[side].x, ANKLE[side].y), ANKLE[side].z,
            torso_base)
        PIVOT_VERT[(side, 0)] = (vobj, vindex)
    A.report("C05_CALIBRATION", {
        "pivot_vertex": {("%s_w0" % s): [PIVOT_VERT[(s, 0)][0],
                                         PIVOT_VERT[(s, 0)][1]]
                         for s in SIDES},
        "note": ("双脚全程支撑 ⟹ 只有一个支撑窗 w0；无踮脚，"
                 "踝目标 = C04 末帧实测值。"),
    })

    # ---- 建帧：首/末帧写 `SEAM_POSE` 本身，中间走呼吸解算
    JS._PREV_EULER.clear()
    JS.ARM_QUAT.clear()
    JS.ARM_ROLL.clear()
    JS.ROLL_MAX.clear()
    JS.MAX_ABS_EULER_Y = 0.0
    A.apply_pose(arm, SEAM_POSE)
    bpy.context.view_layer.update()
    for name, value in SEAM_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    for name in ARM_BONES + ("thigh.L", "shin.L", "foot.L",
                             "thigh.R", "shin.R", "foot.R"):
        JS.ARM_QUAT[name] = arm.pose.bones[name].matrix.to_quaternion()
    JS.ROLL_RANGE = 150.0
    JS.Y_SAFE = 62.0

    keyframes = [(0, SEAM_POSE)]
    for frame in range(1, TOTAL):
        keyframes.append((frame, c05_pose(arm, frame)))
    keyframes.append((TOTAL, SEAM_POSE))

    meta = {
        "anim_id": NAME,
        "loop": True,
        "category": "连招与特殊技",
        "note": ("抓住循环：接 `Grab_Start@54`（首末帧逐位一致）；双手位置逆解"
                 "钉死在世界抓取点（漂移≤3 mm）；双腿逆解钉死踝世界目标；"
                 "呼吸走胸腔前倾 + 骨盆竖向升降，手指做握力周期。"),
        "antic_frame": None,
        "hit_frame": None,
        "cancel_frame": None,
        "hitstop_frames": 0,
        "root_motion_m": [0.0, 0.0],
        "inherit_from": "Grab_Start@54",
        "grab_frame": C04_META.get("grab_frame"),
        "grab_hold_frame": C04_META.get("grab_hold_frame"),
        "grabbed_point_L_m": [round(v, 6) for v in GRAB_POINT["L"]],
        "grabbed_point_R_m": [round(v, 6) for v in GRAB_POINT["R"]],
        "breath_pelvis_z_mm": round(PELVIS_Z_AMP * 1000.0, 3),
        "breath_chest_deg": CHEST_AMP,
        "breath_finger_amp": FINGER_AMP,
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"LOOP_START": 0, "INHALE_PEAK": BREATH_KEYS[1][0],
                           "HOLD_END": BREATH_KEYS[2][0], "LOOP_END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    if os.environ.get("C05_TRACE") == "1":
        for f in foot_series(arm, action, meshes):
            print("C05_TRACE " + json.dumps({
                "f": f["frame"],
                "breath": round(breath_at(f["frame"]), 5),
                "pelvis_z": round(f["pelvis"][2] * 1000.0, 2),
                "L_sole": (None if f["sole_L"] is None
                           else round(f["sole_L"] * 1000.0, 3)),
                "R_sole": (None if f["sole_R"] is None
                           else round(f["sole_R"] * 1000.0, 3)),
                "L_reach": round(f["reach_L"] * 1000.0, 2),
                "R_reach": round(f["reach_R"] * 1000.0, 2),
                "armL_r": round(f["armreach_L"] * 1000.0, 2),
                "armR_r": round(f["armreach_R"] * 1000.0, 2),
                "handL": [round(v * 1000.0, 2) for v in f["hand_L_tail"]],
                "handR": [round(v * 1000.0, 2) for v in f["hand_R_tail"]],
            }))

    report = A.run_common_assertions(samples, meta, foot_probe=())
    foots = foot_series(arm, action, meshes)
    tracks = pivot_series(arm, action, dict(PIVOT_VERT))
    report.update(c05_assertions(arm, action, samples, foots, tracks))
    report["sole_low_frames"] = {
        str(i): v for i, v in sorted(ALL_SOLE.items())
        if min([x for x in v.values() if x is not None] or [0.0]) < -2.0}
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
    report["max_abs_euler_y_deg"] = round(JS.MAX_ABS_EULER_Y, 2)
    report["arm_roll_max_deg"] = {k: round(v, 1)
                                  for k, v in JS.ROLL_MAX.items()}
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)
    A.report("C05_REPORT", report)

    if not SKIP_RENDER:
        # 取景：C04 结束时角色已前冲，骨盆不在世界原点（B10 教训）。
        # 视野中心取「躯干 ↔ 抓取点」的中点 —— 这样前伸的双手和双脚同时进画。
        pel = PELVIS_W if PELVIS_W is not None else Vector((0.0, 0.0, 0.0))
        grab_y = (GRAB_POINT["L"].y + GRAB_POINT["R"].y) * 0.5
        cam_dy = 0.5 * (pel.y + grab_y)
        for base in (A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q):
            name, location, target, _scale, res_v = base
            view = (name, (location[0], location[1] + cam_dy, 0.90),
                    (target[0], target[1] + cam_dy, 0.90), 2.60, res_v)
            A.render_pose_sheet(arm, action, [0, 60, 120], "grab05",
                                views=(view,))
    A.save_project()
    A.export_glb(arm)
    print("C05_DONE failed=%s" % report["failed"])
    print("C05_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C05_FAILURE " + traceback.format_exc())
