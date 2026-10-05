"""anim_guard_start —— D01 `Guard_Start` 举防。

设计（对着清单 §四 D01 的原文「双臂快速挡住头胸」逐条落）：

    段结构    起手接合 → 举防到位 → 短保持。**1 段**、**0 命中点**、**0 位移**。
    时长      24 帧 = 0.400 s @60fps（计划要 0.3~0.5 s）
    起手      `Idle_01@0` **逐位相同**（SEAM_TOL = 1e-6）。引擎 `Idle_01 → Guard_Start`
              直接连播，接缝必须无跳。
    收尾      末帧 = **举防定格真值**（逐位冻结 20..24），供 D02 `Guard_Loop` f0 直接照抄
              （引擎 `Guard_Start → Guard_Loop` 直连）。
    速度剖面  前 21%（5 帧）只走 12% 行程（"慢起"）→ 中段加速 → 过冲 10 mm → 回落定格。
              末段 5 帧**逐位冻结**（`guard_hold_ok` 的构造性来源）。
    双脚      钉死在 `ANKLE_0`，`foot` 朝向钉 rest。脚滑 = 0 mm。

举防真值来源（★ 先量再定，`probe_d01_guard.py` 第 3 轮 `H5_150_1510`）：
    本支是全项目**第一支"保护姿"** —— 前 37 支的手永远在"肩为中心的轨道"上
    （`hand_target = shoulder + u·len`），从没进过脸前面。探针 32 个候选量下来，
    踩了两个**只能靠目检发现**的坑：

    坑 1（肘）  第 1 轮 16 个候选**全部**在正视里读成"投降 / 抱头"。不在拳，在**肘**：
                所有族的 `elbow_dir` 都带 +0.4~0.65 的 X 分量 ⟹ 肘向体侧**外张**
                （肘尖比肩还外 100+ mm），前臂从外上方插向面前 —— 剪影就是"举手"。
                ⟹ 新立判据 `elbow_in_ok`：肘尖 `|x|` 不得比肩宽出 20 mm。
    坑 2（拳）  第 2 轮把肘改成朝下后 `elbow_in_ok` 全过，但**正视仍读成"捂脸/抱头"**：
                拳 x 只有 ±60~110，而脸半宽 85 ⟹ 双拳并拢在脸**正前**。
                拳击护架的正解是**双拳分列脸两侧**（拳 |x| ≥ 130）。
                ⟹ 再加 `lateral_lo_ok`：拳 |x| ∈ [130, 200]。

    还撞到一个**实测出来的硬几何限制**（不是估的）：
      上臂 234 / 前臂+手 325 / 肩高 1345。要把拳升到 1560（肩上方 215）而**肘朝下**，
      肘最低只能压到 z ≈ 1141（肩下 204）⟹ 肘→拳竖直距离 ≥ 419 > 325，**够不着**。
      ⟹ 定稿把拳落在**下巴高度 1510**：护住"胸 + 下巴 + 由前臂构成的正面墙"。
        这是这个骨架能做出的拳击护架，不是"本来的设计"。

    定稿 `H5_150_1510` 实测：拳 (±150, −230, 1510)、身前 186.1 mm、举起 238.9 mm、
      穿模 0.0 mm、肘内收 116.5 mm、肘 z 1254.5（在拳下 255.5 mm）、
      鞋底 L 0.87 / R −1.11 mm、对称差 0/0/0 mm。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python anim_guard_start.py
    SKIP_RENDER=1  只跑门禁不渲图（迭代用）
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                     # noqa: E402
import anim_idle_01 as I1                # noqa: E402
import anim_jump_start as JS             # noqa: E402
import anim_run_stop as RS               # noqa: E402
import anim_ultimate_end as UE           # noqa: E402
import probe_c12_baseline as P           # noqa: E402
import probe_d01_guard as PD             # noqa: E402

NAME = "Guard_Start"
SKIP_RENDER = os.environ.get("SKIP_RENDER") == "1"
SIDES = ("L", "R")


def _env_i(key, default):
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_f(key, default):
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


# =============================================================== 时间轴
TOTAL = _env_i("D01_TOTAL", 24)          # 0.400 s @60fps（计划 0.3~0.5 s）
EASE_END = _env_i("D01_EASE", 4)         # 起手接合
SLOW_END = _env_i("D01_SLOW", 5)         # "慢起"中间键（只走 12% 行程）
GUARD = _env_i("D01_GUARD", 13)          # 举防到位
PEAK = _env_i("D01_PEAK", 16)            # 微过冲峰值
SETTLE = _env_i("D01_SETTLE", 20)        # 回到定格真值；20..TOTAL 逐位冻结

# =============================================================== 阈值
SEAM_TOL = 1e-6
NO_TELEPORT_MAX_DEG = 25.0
PLANT_MAX_MM = 3.0                       # 踝水平位移
SLIDE_MAX_MM = 3.0                       # 脚滑（通用门禁）
GROUND_MIN_MM, GROUND_MAX_MM = -2.0, 6.0
REACH_MAX_RATIO = 0.995

# ★ 举防判据（全部会失败；数值由 `probe_d01_guard.py` 第 3 轮实测确定）
GUARD_IN_FRONT_MIN_MM = 150.0            # 拳在躯干前平面之前（定稿 186.1）
GUARD_LATERAL_MIN_MM = _env_f("D01_LATMIN", 130.0)   # 拳 |x| 下界（"分列脸两侧"）
GUARD_LATERAL_MAX_MM = 200.0             # 拳 |x| 上界（不能张开手臂）
GUARD_RAISE_MIN_MM = 80.0                # 相对 Idle 拳举起量（定稿 238.9）
GUARD_HEAD_MARGIN_MM = 100.0             # 允许高过头顶 100 mm
GUARD_SYM_MAX_MM = 25.0                  # 左右对称差
GUARD_ELBOW_OUT_MAX_MM = 20.0            # 肘尖不得比肩外张（定稿 −116.5）
GUARD_ELBOW_DROP_MIN_MM = 150.0          # 肘必须在拳下方（定稿 255.5）
GUARD_CLIP_MAX_MM = 0.0                  # 拳/前臂不得插进头部包围盒
GUARD_FIST_SPREAD_MIN_MM = 260.0         # 双拳横向净距（2×130）
HOLD_MAX_MM = _env_f("D01_HOLD_MAX", 0.5)      # 定格窗内最大漂移
SETTLE_LAST2_MAX_DEG = _env_f("D01_LAST2", 0.5)  # 末 2 帧欧拉步长

# =============================================================== 定格真值
# 来源：`probe_d01_guard.py` `build_candidates()` 第 3 轮 `H5_150_1510`
#   （elbow_dir = (±0.30, −0.10, −0.95)）
GUARD_FIST = {"L": Vector((0.150, -0.230, 1.510)),
              "R": Vector((-0.150, -0.230, 1.510))}
GUARD_ELBOW = {"L": Vector((-0.30, -0.10, -0.95)),
               "R": Vector((0.30, -0.10, -0.95))}
# 骨盆升降信封：单位 = **相对 `Idle_01@0`**（Idle 骨盆 830 mm）的位移 mm。
# ★ 探针 `GUARD_DROP = −0.080` 是**相对 rest 900 mm** 的口径 ⟹ 骨盆 820 mm
#   ⟹ 相对 Idle = **−10 mm**。第 1 轮把 −80 直接抄进来，骨盆落到了 750 mm
#   （比 Idle 低 80 mm 的深蹲），躯干整体矮 70 mm。报告里 `chest_top_mm`
#   1281 而探针是 1351，差值恰好 70 ⟹ 一条减法就把这个口径错误抓了出来。
GUARD_DROP_MM = -10.0
SINK_DROP_MM = -14.0
PEAK_OFFSET = Vector((0.0, -0.010, 0.008))   # 过冲：再前 10 mm、再高 8 mm
SLOW_FRACTION = 0.12                     # 前 21% 帧只走 12% 行程

# 躯干（定格值 = 探针 `GUARD_TORSO`）
TORSO_GUARD = {"pelvis": 5.0, "spine_01": 2.0, "spine_02": 2.0,
               "chest": 6.0, "neck": -8.0, "head": 6.0}
TORSO_SINK = {"pelvis": 7.0, "spine_01": 3.0, "spine_02": 3.0,
              "chest": 3.0, "neck": -5.0, "head": 4.0}
SHOULDER_SINK, SHOULDER_GUARD, SHOULDER_PEAK = -20.0, 8.0, 10.0

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
LEG_BONES = ("thigh.L", "shin.L", "thigh.R", "shin.R")
TARGET_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                "shoulder.L", "shoulder.R")
HEAD_MESHES = PD.HEAD_MESHES

# ---------------------------------------------------------------- 欧拉支搜索调参
# ★ `UE` 的滚转搜索（C14 建立）在本支**默认参数下不够好**：`ROLL_STEP_DEG = 5°`、
#   `EULER_Y_SAFE = 70°`、`EULER_Y_WEIGHT = 1.5` 时，`upperarm.R` 在抬起最快的
#   那一帧单步 **23.53°**（C14 定稿 14.7°）。逐帧轨迹是一个**孤峰**
#   （前 12.5、峰值 23.5、后 7.6）⟹ 不是真实加速，是搜索挑到了
#   "步长大但 y 更小"的等价欧拉支。
#   根因：代价函数把"|y| 超过 70° 的惩罚（1.5 / 度）"和"步长"放在同一量纲上比，
#   在 y ≈ 70 的边界上等于**用 1.5° 的步长换 1° 的 y**，把路径推离真实解。
#   ★ 实测扫描（每一组都是完整跑一遍门禁，不是在纸上算）：
#       ysafe=70 yw=1.5 roll=5.0（C14 默认）→ 23.534
#       ysafe=70 yw=1.5 roll=2.5              → 22.215
#       ysafe=88 yw=0.0 roll=5.0              → 38.580   ← 粗网格 + 无惩罚 = 乱走
#       ysafe=88 yw=0.0 roll=2.5              → 12.969
#       ysafe=88 yw=0.0 roll=2.0              → 12.283   ← 定稿
#       ysafe=88 yw=0.0 roll=1.25             → 12.821（更细反而略差，收益到顶）
#       ysafe=88 yw=0.0 roll=3.0              → 14.272
#       ysafe=80 yw=0.3 roll=2.5              → 15.104
#   ⟹ 定稿 `YSAFE = 88`（留 2° 不触发惩罚即可）、`YWEIGHT = 0`、`ROLLSTEP = 2.0°`。
#     滚转只绕骨轴、过骨根 ⟹ 骨根/骨尖不动 ⟹ IK / 贴地 / 剪影一致（C14 结论）。
UE.ROLL_STEP_DEG = _env_f("D01_ROLLSTEP", 2.0)
UE.ROLL_GRID = UE._roll_grid()
UE.EULER_Y_SAFE = _env_f("D01_YSAFE", 88.0)
UE.EULER_Y_WEIGHT = _env_f("D01_YWEIGHT", 0.0)

# =============================================================== 模块级表
SEAM_POSE = {}
SEAM_EULER = {}
Z_SEAM = 0.0
ANKLE_0 = {}
ARM_REF = None
IDLE_FIST = {}
IDLE_ELBOW_DIR = {}
KNEE_DIR = Vector((0.0, -0.94, -0.34))   # 膝盖朝前下
FIST_KEYS = {}
ELBOW_KEYS = {}
ROT_HISTORY = {}          # 末帧真值（与 D02 对表用）


def _lerp_vec(a, b, t):
    return Vector(a) * (1.0 - t) + Vector(b) * t


def _head_bbox_mm():
    """头顶/头框（毫米），用于定 `z` 窗上界与穿模判据。"""
    lo, hi = PD.head_box()
    return ([round(v * 1000.0, 1) for v in lo],
            [round(v * 1000.0, 1) for v in hi])


def guard_target(side, frame):
    """第 `frame` 帧的拳世界目标（缓慢起 → 加速 → 过冲 → 定格）。"""
    keys = FIST_KEYS[side]
    return UE.pwl_vec(keys, float(frame), tuple(keys[-1][1]))


def guard_elbow_dir(side, frame):
    keys = ELBOW_KEYS[side]
    return UE.pwl_vec(keys, float(frame), tuple(keys[-1][1]))


def build_envelopes():
    """现算信封（依赖 `Idle_01@0` 真值，必须在 `boot()` 之后调用）。"""
    FIST_KEYS.clear()
    ELBOW_KEYS.clear()
    for side in SIDES:
        #
        start = tuple(IDLE_FIST[side])
        goal = tuple(GUARD_FIST[side])
        peak = tuple(GUARD_FIST[side] + PEAK_OFFSET)
        slow = tuple(_lerp_vec(start, goal, SLOW_FRACTION))
        FIST_KEYS[side] = ((0, start), (SLOW_END, slow), (GUARD, goal),
                           (PEAK, peak), (SETTLE, goal), (TOTAL, goal))
        e_start = tuple(IDLE_ELBOW_DIR[side])
        e_goal = tuple(GUARD_ELBOW[side])
        e_peak = tuple((GUARD_ELBOW[side] * 1.06).normalized())
        e_slow = tuple(_lerp_vec(e_start, e_goal, SLOW_FRACTION))
        e_slow = tuple(Vector(e_slow).normalized())
        ELBOW_KEYS[side] = ((0, e_start), (SLOW_END, e_slow), (GUARD, e_goal),
                            (PEAK, e_peak), (SETTLE, e_goal), (TOTAL, e_goal))


def torso_pose(frame):
    out = {}
    for name in TARGET_BONES:
        out[name] = tuple(SEAM_EULER[name])
    for name, guard in TORSO_GUARD.items():
        out[name] = (UE.pwl(((0, None), (SLOW_END, TORSO_SINK[name]),
                             (GUARD, guard), (SETTLE, guard), (TOTAL, guard)),
                            frame, SEAM_EULER[name][0]),
                     SEAM_EULER[name][1], SEAM_EULER[name][2])
    for side in SIDES:
        name = "shoulder." + side
        out[name] = (UE.pwl(((0, None), (SLOW_END, SHOULDER_SINK),
                             (GUARD, SHOULDER_GUARD), (PEAK, SHOULDER_PEAK),
                             (SETTLE, SHOULDER_GUARD), (TOTAL, SHOULDER_GUARD)),
                            frame, SEAM_EULER[name][0]),
                     SEAM_EULER[name][1], 0.0)
    drop = UE.pwl(((0, None), (SLOW_END, SINK_DROP_MM), (GUARD, GUARD_DROP_MM),
                   (SETTLE, GUARD_DROP_MM), (TOTAL, GUARD_DROP_MM)),
                  frame, 0.0)
    out["@loc"] = {"pelvis": A.wloc(0.0, 0.0, Z_SEAM + drop / 1000.0 - 0.900)}
    return out


def build_pose(arm, frame):
    pose = torso_pose(frame)
    A.apply_pose(arm, pose)
    # 腿：**位置 IK**（`UE.leg_seat`，与 C14 同口径），踝目标钉死在 `ANKLE_0`。
    # ★ 为什么不用 `Idle_01` 的解析 `leg_ik`（第 1 轮的错）：
    #   `leg_ik` 假设"髋关节 = (y=0, z=骨盆高)"，而真实大腿根有横向与前后偏移；
    #   骨盆一动，这个模型误差就跟着变 —— 实测骨盆降 14 mm，**踝关节实际漂了
    #   6.17 / 5.25 mm**（`plant_ok` ≤3 mm 直接红），鞋底也掉到 −2.04 mm。
    #   `leg_seat` 直接把"踝关节世界坐标"钉住 ⟹ 脚零位移、鞋底回到 Idle 真值。
    #   首帧仍是 `SEAM_POSE`（逐位 Idle），故 `ua_start_ok` 不受影响。
    for side in SIDES:
        UE.leg_seat(arm, pose, side, ANKLE_0[side], KNEE_DIR)
    for side in SIDES:
        name = "foot." + side
        pose[name] = JS._unwrap_xyz(JS._PREV_EULER.get(name),
                                    A.keep_world_orientation(arm, name))
    for side in SIDES:
        # ★ 拳目标必须在 `apply_pose` 之后按**当前**肩位现取（肩随躯干走）
        target = guard_target(side, frame)
        UE.arm_seat(arm, pose, side, target, guard_elbow_dir(side, frame))

    # 起手接合：`arm_seat` 隐含"腕直"，Idle 戒备是**屈腕**的，第 1 帧会被掰直
    # ⟹ 单帧欧拉步长超标。f0..EASE_END 平滑接上（C10~C14 复用）。
    if frame < EASE_END:
        weight = RS.smooth(frame / float(EASE_END))
        for name in ARM_BONES:
            base = SEAM_EULER[name]
            got = JS._unwrap_xyz(base, pose[name])
            pose[name] = tuple(a + (b - a) * weight for a, b in zip(base, got))

    pose.update(A.FIST)
    for name, value in pose.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    return pose


def solve_pose(arm, frame, meshes=None):
    """单帧装配（无贴地闭环；踝由位置 IK 钉死，脚纹丝不动）。"""
    return build_pose(arm, frame)


# =============================================================== 专属门禁
def guard_metrics(arm):
    """量定格帧的举防真值（全部单位 mm）。"""
    row = {}
    torso_y = A.bone_world(arm, "chest", "head").y
    chest_top = A.bone_world(arm, "neck", "head").z
    head_top = A.bone_world(arm, "head", "tail").z

    fists, elbows, shoulders = {}, {}, {}
    for side in SIDES:
        fists[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        shoulders[side] = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbows[side] = Vector(A.bone_world(arm, "upperarm." + side, "tail"))

    row["chest_top_mm"] = round(chest_top * 1000.0, 1)
    row["head_top_mm"] = round(head_top * 1000.0, 1)
    row["torso_front_y_mm"] = round(torso_y * 1000.0, 1)
    row["fist_mm"] = {s: [round(v * 1000.0, 1) for v in fists[s]]
                      for s in SIDES}
    row["elbow_z_mm"] = {s: round(elbows[s].z * 1000.0, 1) for s in SIDES}
    row["elbow_out_mm"] = {s: round((abs(elbows[s].x) - abs(shoulders[s].x))
                                    * 1000.0, 1) for s in SIDES}
    row["elbow_drop_mm"] = {s: round((fists[s].z - elbows[s].z) * 1000.0, 1)
                            for s in SIDES}

    in_front = {s: round((torso_y - fists[s].y) * 1000.0, 1) for s in SIDES}
    lateral = {s: round(abs(fists[s].x) * 1000.0, 1) for s in SIDES}
    raise_mm = {s: round((fists[s].z - IDLE_FIST[s].z) * 1000.0, 1)
                for s in SIDES}
    row["in_front_mm"] = in_front
    row["lateral_mm"] = lateral
    row["raise_mm"] = raise_mm

    lo_z = chest_top * 1000.0
    hi_z = head_top * 1000.0 + GUARD_HEAD_MARGIN_MM
    row["z_window_mm"] = [round(lo_z, 1), round(hi_z, 1)]
    row["in_front_ok"] = all(v >= GUARD_IN_FRONT_MIN_MM
                             for v in in_front.values())
    row["lateral_ok"] = all(GUARD_LATERAL_MIN_MM <= v <= GUARD_LATERAL_MAX_MM
                            for v in lateral.values())
    row["z_window_ok"] = all(lo_z <= fists[s].z * 1000.0 <= hi_z
                             for s in SIDES)
    row["raise_ok"] = all(v >= GUARD_RAISE_MIN_MM for v in raise_mm.values())
    row["guard_cover_ok"] = bool(row["in_front_ok"] and row["lateral_ok"]
                                 and row["z_window_ok"] and row["raise_ok"])

    dx = abs(abs(fists["L"].x) - abs(fists["R"].x)) * 1000.0
    dz = abs(fists["L"].z - fists["R"].z) * 1000.0
    dy = abs(fists["L"].y - fists["R"].y) * 1000.0
    row["sym_dx_mm"], row["sym_dz_mm"], row["sym_dy_mm"] = (
        round(dx, 2), round(dz, 2), round(dy, 2))
    row["guard_symmetry_ok"] = bool(max(dx, dz, dy) <= GUARD_SYM_MAX_MM)
    spread = (abs(fists["L"].x) + abs(fists["R"].x)) * 1000.0
    row["fist_spread_mm"] = round(spread, 1)
    row["fist_spread_ok"] = bool(spread >= GUARD_FIST_SPREAD_MIN_MM)

    row["guard_elbow_ok"] = bool(
        all(v <= GUARD_ELBOW_OUT_MAX_MM for v in row["elbow_out_mm"].values())
        and all(v >= GUARD_ELBOW_DROP_MIN_MM
                for v in row["elbow_drop_mm"].values()))

    clip = PD.clip_metrics(arm)
    row["clip_max_mm"] = clip["clip_max_mm"]
    row["clip_at"] = clip["clip_at"]
    row["guard_no_face_clip_ok"] = bool(clip["clip_max_mm"] <= GUARD_CLIP_MAX_MM)

    row["head_box_mm"] = [list(v) for v in _head_bbox_mm()]
    return row


def guard_assertions(arm, action, samples):
    """D01 专属门禁：定格帧量"挡不挡得住"，定格窗量"稳不稳"。"""
    res = {}
    scene = bpy.context.scene
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # ---- 定格帧真值
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()
    res.update(guard_metrics(arm))

    # ---- 定格窗漂移（20..24 逐位冻结）
    drift = 0.0
    scene.frame_set(SETTLE)
    bpy.context.view_layer.update()
    ref = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    for frame in range(SETTLE + 1, TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        for side in SIDES:
            got = Vector(A.bone_world(arm, "hand." + side, "tail"))
            drift = max(drift, (got - ref[side]).length * 1000.0)
    res["guard_window_drift_mm"] = round(drift, 3)
    res["guard_hold_ok"] = bool(drift <= HOLD_MAX_MM)

    # ---- 末 2 帧步长（"没有瞬停"的反面：收尾必须真的停住）
    last2 = 0.0
    for index in range(len(samples) - 2, len(samples)):
        ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
        for name in set(ea) | set(eb):
            a = ea.get(name, (0.0, 0.0, 0.0))
            b = eb.get(name, (0.0, 0.0, 0.0))
            last2 = max(last2, max(abs(x - y) for x, y in zip(a, b)))
    res["settle_last2_deg"] = round(last2, 4)
    res["settle"] = bool(last2 <= SETTLE_LAST2_MAX_DEG)

    # ---- 踝贴死（本支 0 位移）
    plant = {}
    for side in SIDES:
        point = samples[0].get("foot." + side)
        if point is None:
            continue
        travel = max(math.hypot(Vector(s["foot." + side]).x - Vector(point).x,
                                Vector(s["foot." + side]).y - Vector(point).y)
                     for s in samples) * 1000.0
        plant[side] = round(travel, 3)
    res["plant_mm"] = plant
    res["plant_ok"] = bool(all(v <= PLANT_MAX_MM for v in plant.values()))

    # ---- 举防到位帧（举防必须在 GUARD 帧就成，而不是拖到末帧）
    scene.frame_set(GUARD)
    bpy.context.view_layer.update()
    fists_guard = {s: Vector(A.bone_world(arm, "hand." + s, "tail"))
                   for s in SIDES}
    lag = max((fists_guard[s] - GUARD_FIST[s]).length for s in SIDES) * 1000.0
    res["guard_arrive_lag_mm"] = round(lag, 2)
    res["guard_arrive_ok"] = bool(lag <= 12.0)

    # ---- 末帧 = 定格真值（供 D02 f0 直连）
    end = {}
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()
    for side in SIDES:
        got = Vector(A.bone_world(arm, "hand." + side, "tail"))
        end[side] = round((got - GUARD_FIST[side]).length * 1000.0, 3)
    res["end_pose_mm"] = end
    res["end_pose_ok"] = bool(all(v <= 0.5 for v in end.values()))

    # ---- 可达性（探针里 clamp 必须全过）
    scene.frame_set(TOTAL)
    bpy.context.view_layer.update()
    res["reach_ok"] = True
    for side in SIDES:
        up = "upperarm." + side
        shoulder = Vector(A.bone_world(arm, up, "head"))
        dims = UE.ARM_LEN[side]
        limit = (dims["upper"] + dims["forearm"] + dims["hand"]) * 0.9995
        need = (GUARD_FIST[side] - shoulder).length
        res["reach_ratio_" + side] = round(need / limit, 5)
        if need / limit > REACH_MAX_RATIO:
            res["reach_ok"] = False

    # ---- 剪影（本支双手捧在面前，剪影指标大概率失效 —— 只报不用）
    sil = P.silhouette(arm, "d01")
    res["aspect"] = sil["aspect"]
    res["fill_grid"] = sil["fill_grid"]
    res["width_m"] = sil["width_m"]
    res["height_m"] = sil["height_m"]
    res["com_inside_support"] = sil["com_inside_support"]

    # 末帧姿态真值（D02 直接照抄；入 clip 范围）
    res["end_euler_ref"] = {b: [round(v, 4) for v in ROT_HISTORY[b]]
                            for b in TARGET_BONES + ARM_BONES + LEG_BONES
                            + ("foot.L", "foot.R")}
    return res


# =============================================================== 引导
def boot():
    global SEAM_POSE, SEAM_EULER, Z_SEAM, ANKLE_0, ARM_REF
    for store in (SEAM_POSE, SEAM_EULER, ANKLE_0, IDLE_FIST, IDLE_ELBOW_DIR,
                  ROT_HISTORY):
        store.clear()

    arm, meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("D01_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    for side in SIDES:
        UE.ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}
    ARM_REF = arm
    for extra in LEG_BONES + ("foot.L", "foot.R"):
        if extra not in A.PROBE_BONES:
            A.PROBE_BONES = tuple(A.PROBE_BONES) + (extra,)
        if extra not in A.PROBE_TAILS:
            A.PROBE_TAILS = tuple(A.PROBE_TAILS) + (extra,)
    A.PROBE_KEYS = A.PROBE_BONES + tuple(n + ".tail" for n in A.PROBE_TAILS)

    # ---- 首帧真值：`Idle_01@0`（★ 先归零再求值，否则读到上次运行留下的陈旧姿态）
    scene = bpy.context.scene
    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    A.reset_pose(arm)
    scene.frame_set(0)
    bpy.context.view_layer.update()
    SEAM_EULER = {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
                  for b in arm.pose.bones}
    SEAM_POSE = dict(SEAM_EULER)
    SEAM_POSE["@loc"] = {"pelvis": tuple(arm.pose.bones["pelvis"].location)}
    SEAM_POSE.update(A.FIST)
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    for side in SIDES:
        IDLE_FIST[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))

    # ---- Idle 骨基座（逆解基准）
    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)
    bpy.context.view_layer.update()
    for side in SIDES:
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        IDLE_ELBOW_DIR[side] = tuple((elbow - shoulder).normalized())
    for bone in ARM_BONES + LEG_BONES:
        UE.IDLE_BASIS[bone] = arm.pose.bones[bone].matrix.to_3x3().copy()
        UE.IDLE_DIR[bone] = A.bone_direction(arm, bone)

    build_envelopes()
    A.report("D01_LAYOUT", {
        "total_frames": TOTAL, "seconds": round(TOTAL / float(A.FPS), 3),
        "ease_end": EASE_END, "slow_end": SLOW_END, "guard": GUARD,
        "peak": PEAK, "settle": SETTLE, "frozen_tail": TOTAL - SETTLE,
        "segments": 1, "hit_points": 0, "root_motion_m": [0.0, 0.0],
        "pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
        "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                      for s in SIDES},
        "idle_fist_mm": {s: [round(v * 1000.0, 2) for v in IDLE_FIST[s]]
                         for s in SIDES},
        "guard_fist_mm": {s: [round(v * 1000.0, 2) for v in GUARD_FIST[s]]
                          for s in SIDES},
        "guard_elbow_dir": {s: [round(v, 4) for v in GUARD_ELBOW[s]]
                            for s in SIDES},
        "tour": ("起手接合 %d 帧 → 慢起至 %d 帧（走 %.0f%% 行程）→ 举防到位 %d 帧"
                 " → 过冲 %d 帧 → 定格 %d 帧（%d..%d 逐位冻结）"
                 % (EASE_END, SLOW_END, SLOW_FRACTION * 100.0, GUARD, PEAK,
                    SETTLE, SETTLE, TOTAL)),
        "note": ("D01 举防：本支是全项目第一支持护姿；肘内收 + 拳分列脸两侧"
                 "（探针两轮目检回炉后定稿）"),
    })
    return arm, meshes


def main():
    global ROT_HISTORY
    arm, meshes = boot()

    JS._PREV_EULER.clear()
    A.apply_pose(arm, SEAM_POSE)
    bpy.context.view_layer.update()
    for name, value in SEAM_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)

    keyframes = [(0, SEAM_POSE)]
    for frame in range(1, TOTAL + 1):
        keyframes.append((frame, solve_pose(arm, frame, meshes)))

    # ★ 定格窗：把 `SETTLE` 姿态**逐位复用**到 `TOTAL`
    #   （`guard_hold_ok` 的构造性来源 —— 共用同一 dict，漂移恒 0.0 mm）
    hold_pose = keyframes[SETTLE][1]
    for frame in range(SETTLE + 1, TOTAL + 1):
        keyframes[frame] = (frame, dict(hold_pose))

    ROT_HISTORY = {k: tuple(v) for k, v in hold_pose.items()
                   if not k.startswith("@")}

    meta = {
        "anim_id": NAME,
        "loop": False,
        "category": "防御",
        "note": "举防：双臂快速挡住头胸（肘内收、拳分列脸两侧），0 命中点、0 位移",
        "antic_frame": SLOW_END,
        "guard_frame": GUARD,
        "cancel_frame": SETTLE,
        "hitstop_frames": 0,
        "hit_points": 0,
        "root_motion_m": [0.0, 0.0],
        "hit_point_m": None,
        "end_pose_ref": "D02 Guard_Loop f0",
    }
    action, meta = A.build_action(arm, NAME, keyframes, meta)
    A.add_markers(action, {"START": 0, "EASE_END": EASE_END,
                           "ANTIC": SLOW_END, "GUARD": GUARD,
                           "OVERSHOOT": PEAK, "SETTLE": SETTLE,
                           "END": TOTAL})

    samples = A.sample_animation(arm, action, 0, TOTAL, meshes)
    report = A.run_common_assertions(samples, meta,
                                     foot_probe=("foot.L", "foot.R"),
                                     slide_tolerance_mm=SLIDE_MAX_MM)
    report.update(guard_assertions(arm, action, samples))
    report["meta"] = meta
    report["failed"] = sorted(k for k, v in report.items()
                              if k.endswith("_ok") and v is not True)
    report["non_ok_bools"] = sorted(
        k for k, v in report.items()
        if isinstance(v, bool) and not k.endswith("_ok") and v is not True)

    # 起手接合：f0 必须与 `Idle_01@0` 逐位相同
    delta0 = 0.0
    for name in SEAM_EULER:
        got = samples[0]["euler"].get(name)
        if got is None:
            continue
        delta0 = max(delta0, max(abs(a - b) for a, b in
                                 zip(got, SEAM_EULER[name])))
    report["ua_start_delta_deg"] = round(delta0, 8)
    report["ua_start_ok"] = bool(delta0 <= SEAM_TOL)

    # 逐帧步长轨迹（只报不判）：用于判断 23.5°/帧 是**真实快速抬臂**还是
    # 欧拉支/锁造成的假跳 —— 假跳会表现为"孤峰 + 前后帧都很小"。
    if os.environ.get("D01_TRACE"):
        trace = {}
        for index in range(1, len(samples)):
            ea, eb = samples[index - 1]["euler"], samples[index]["euler"]
            for name in ARM_BONES:
                a = ea.get(name, (0.0, 0.0, 0.0))
                b = eb.get(name, (0.0, 0.0, 0.0))
                step = max(abs(x - y) for x, y in zip(a, b))
                trace.setdefault(name, []).append(round(step, 2))
        report["arm_step_trace"] = trace
        report["arm_euler_trace"] = {
            name: [[s["frame"]] + [round(v, 2) for v in s["euler"].get(name,
                                                                       (0.0,) * 3)]
                   for s in samples]
            for name in ARM_BONES}

    A.report("D01_REPORT", report)

    if not SKIP_RENDER:
        frames = [0, EASE_END, SLOW_END, GUARD, PEAK, SETTLE, TOTAL]
        A.render_pose_sheet(arm, action, frames, "guardstart",
                            views=(A.VIEW_SIDE, A.VIEW_FRONT, A.VIEW_3Q))
        A.save_project()
        A.export_glb(arm)
    print("D01_DONE failed=%s" % report["failed"])
    print("D01_DONE non_ok_bools=%s" % report["non_ok_bools"])


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D01_FAILURE " + traceback.format_exc())
