"""probe_air09 —— B09 `Air_Heavy` 开工前的四项实测（先量再做，不许拍脑袋）。

清单下一支计划要求量的四项：

1. **A13 `Jump_Land@0` 的接口**（B09 的**下游接缝**，B08 的下游是 A12，本支换成 A13）：
   骨盆 z、髋−踝竖距、踝相对髋、全部骨 euler、臂骨世界四元数。
   ★ 若 A13 首帧骨盆 z ≠ 0.90 附近，说明它自带上抛量 —— 本支末帧要对到**那个**数。
   ★ 顺带量 B09 的**上游接缝** `Jump_Fall@0`（= B08 的首帧）。
   ★ 两个接缝的骨盆 z 之差 = **本支的总落距**，是一个**死数**：
     清单写「允许改变下落速度」⟹ 落速可以改，但**落距不能改**（首末帧都钉死在接缝上）。
     ⟹ 「下砸段要砸得更快」必须由「前摇段吊得更慢」来付账（**落距守恒**）。

2. **下砸速度包的上限**：把落速表（前摇吊速 / 下砸加速 / 命停 / 回落）解出来，
   量：① 下砸段总落距 / 同时长自由落体落距（`slam_accel_ok` 的区间）；
   ② 全程鞋底最低点（`all_airborne_ok`）；③ 末帧落速 vs A13 首帧落速（交接顺不顺）。
   ★ 腿的伸展量**只跟姿态有关、跟弹道无关**（踝目标是「髋相对」量）⟹
     腿会不会被压到僵死由 ③ 姿态项决定，见第 4 项。

3. **双臂同向下砸的可达性**：B08 只测单臂；B09 是**双拳同时**。
   B08 的 `rel` 法（手骨指向 = `normalize(rel)`）⟹ 腕距 = `|rel| − hand_len`，
   恒落在 [fold_min, 0.9995·(Lu+Lf)] 内。**两臂各扫一遍**（左右镜像，但要各自验），
   别等门禁红了才发现有一侧冲出了环带。

4. **末帧回得去吗**：末姿态能否在 5 帧内收敛到 A13@0 且单帧 ≤25°。
   ★ 纯几何估算：逐骨**世界方向**的转角 × 欧拉放大系数的经验区间。
   B08 实测 9 帧收招释放步 12.34°；本支收招只有 5 帧 ⟹ **先量再定**。

本探针**不改任何文件**、只读 + 纯几何计算。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_air09.py
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
import anim_jump_fall as JFE  # noqa: E402
import anim_jump_land as JL   # noqa: E402

SIDES = ("L", "R")
UP0 = ("upperarm.L", "upperarm.R")
LO0 = ("forearm.L", "forearm.R")
HD0 = ("hand.L", "hand.R")
ARM6 = UP0 + LO0 + HD0

# ---------------------------------------------------------------- 帧结构（与本体一致）
TOTAL = 22
CHAMBER_END = 6               # 前摇 0~6（7 帧，**吊速**：落得比自由落体慢）
SLAM_START = CHAMBER_END      # 下砸 6~14（9 帧）
HIT = 15
HOLD_END = 17                 # 命停 f15~f17（3 帧关节冻结）
RETURN_START = HOLD_END
RETURN_END = TOTAL
SLAM_A = 20.0                 # 下砸段起始落速（mm/帧）
SLAM_P = 4.00                 # 下砸段第一段速度增量
SLAM_Q = 0.45                 # 速度增量的增量（>0 ⟹ 帧间落距**严格递增**）
RECOIL = 8.0                  # 命停后回落的"卸力"量（mm/帧）

# ---------------------------------------------------------------- 设计候选（本支的骨架）
# 拳峰**相对肩**的世界偏移（米）。x = 左正；y = 身后正（角色正面朝 −y）；z = 上正。
REL_AC = {"L": Vector((0.075, -0.215, 0.470)),      # 前摇顶：双拳举到肩上（蓄力）
          "R": Vector((-0.075, -0.215, 0.470))}
REL_AH = {"L": Vector((0.075, -0.330, -0.460)),     # 命中：双拳砸到肩下前方
          "R": Vector((-0.075, -0.330, -0.460))}
# 踝**相对髋**的增量（米）：前摇把膝收起来，命中回到 A13@0 的落地构型
ANK_AC_DELTA = Vector((0.0, 0.055, 0.175))
POLE_ARM_AC = {"L": (0.62, 0.12, -0.77), "R": (-0.62, 0.12, -0.77)}
POLE_ARM_AH = {"L": (0.30, 0.62, -0.72), "R": (-0.30, 0.62, -0.72)}
POLE_LEG_AH = {"L": (0.16, -1.0, 0.0), "R": (-0.16, -1.0, 0.0)}


def mm(v):
    return [round(x * 1000.0, 1) for x in v]


def v_free(f):
    """A12 弹道在第 f 帧的落距（mm，正 = 往下落）。"""
    return (JFE.pelvis_z(f) - JFE.pelvis_z(f + 1)) * 1000.0


def knee_of(hip, ankle, thigh, shin, bulge):
    """两骨 IK 的膝位置（与 `anim_uppercut.leg_aim` 同一公式，纯几何）。"""
    delta = Vector(ankle) - Vector(hip)
    raw = delta.length
    distance = max(1e-4, min(raw, (thigh + shin) * 0.9995))
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, 0.0, -1.0))
    b = Vector(bulge)
    b = b - axis * b.dot(axis)
    b = b.normalized() if b.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    cos_hip = (thigh ** 2 + distance ** 2 - shin ** 2) / (2.0 * thigh * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    return Vector(hip) + (axis * cos_hip + b * sin_hip) * thigh, raw, distance


def fall_profile(c):
    """落距表（mm/帧）—— 前摇吊速、下砸加速、命停续落、回落卸力。

    ★ 前摇的"吊速比例" `c` 是**唯一自由量**，由「总落距必须精确等于两个接缝
      的骨盆 z 差」**反解**得到（不硬编码残差）。
    """
    v = [c * v_free(f) for f in range(0, CHAMBER_END + 1)]
    for k in range(HIT - SLAM_START):
        step = SLAM_A + sum(SLAM_P + SLAM_Q * j for j in range(k))
        v.append(step)
    slam_end = v[HIT - 1]
    v.append(slam_end - 1.0)
    v.append(slam_end - 2.0)
    base = slam_end - RECOIL
    g = JFE.G_PER_FRAME * 1000.0
    for i in range(RETURN_END - RETURN_START):
        v.append(base + i * g)
    return v


def solve_chamber_scale(target_mm):
    lo, hi = 0.0, 1.5
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if sum(fall_profile(mid)) < target_mm:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    for module in (JFE, JL):
        if module.NAME not in bpy.data.actions:
            print("AIR09_PROBE 动画工程缺 %s —— 无法读接缝" % module.NAME)
            return

    # ---------------------------------------------------------- 0) 两条接缝
    in_pose, in_quats = JU.capture_start(arm, bpy.data.actions[JFE.NAME], 0)
    in_mats = JFE.CR.action_world_matrices(arm, bpy.data.actions[JFE.NAME], 0)
    out_pose, out_quats = JU.capture_start(arm, bpy.data.actions[JL.NAME], 0)
    out_mats = JFE.CR.action_world_matrices(arm, bpy.data.actions[JL.NAME], 0)
    # ★ 读完立刻卸 action：否则后续 view_layer.update() 会把上游 f-curve 压回 pose bone
    arm.animation_data.action = None
    bpy.context.view_layer.update()

    I1.idle_pose(arm, 0.0)
    rest_ankle = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}

    def measure(pose):
        A.apply_pose(arm, pose)
        bpy.context.view_layer.update()
        world = {}
        for name in ("pelvis", "chest", "neck", "head",
                     "shoulder.L", "shoulder.R",
                     "upperarm.L", "upperarm.R", "forearm.L", "forearm.R",
                     "hand.L", "hand.R",
                     "thigh.L", "thigh.R", "shin.L", "shin.R",
                     "foot.L", "foot.R"):
            world[name] = Vector(A.bone_world(arm, name, "head"))
        for s in SIDES:
            world["hand.%s.tail" % s] = Vector(A.bone_world(arm, "hand." + s, "tail"))
            world["chest.tail"] = Vector(A.bone_world(arm, "chest", "tail"))
        return world

    W_IN = measure(in_pose)
    W_OUT = measure(out_pose)

    def seam_block(world, pose, quats):
        euler = {k: [round(x, 3) for x in v] for k, v in pose.items()
                 if not k.startswith("@")}
        return {
            "pelvis_z_mm": round(world["pelvis"].z * 1000.0, 3),
            "pelvis_xy_mm": mm(world["pelvis"])[:2],
            "pelvis_loc_local": mm(pose.get("@loc", {}).get("pelvis", (0, 0, 0))),
            "hip_z_mm": {s: round(world["thigh." + s].z * 1000.0, 1) for s in SIDES},
            "hip_ankle_mm": {s: round((world["foot." + s]
                                       - world["thigh." + s]).length * 1000.0, 1)
                             for s in SIDES},
            "hip_ankle_vert_mm": {s: round((world["thigh." + s].z
                                            - world["foot." + s].z) * 1000.0, 1)
                                  for s in SIDES},
            "ankle_rel_hip_mm": {s: mm(world["foot." + s] - world["thigh." + s])
                                 for s in SIDES},
            "knee_mm": {s: mm(world["shin." + s]) for s in SIDES},
            "ankle_mm": {s: mm(world["foot." + s]) for s in SIDES},
            "fist_mm": {s: mm(world["hand.%s.tail" % s]) for s in SIDES},
            "fist_rel_shoulder_mm": {
                s: mm(world["hand.%s.tail" % s] - world["upperarm." + s])
                for s in SIDES},
            "hand_dir": {s: [round(x, 4) for x in
                             A.bone_direction(arm, "hand." + s)] for s in SIDES},
            "chest_tail_rel_pelvis_mm": mm(world["chest.tail"] - world["pelvis"]),
            "euler_channels": len(euler),
            "euler": euler,
            "arm_quat_present": sorted(quats.keys()),
        }

    A.report("AIR09_SEAM_IN", dict(
        seam_block(W_IN, in_pose, in_quats),
        source="%s@0（= B08 的首帧）" % JFE.NAME))
    A.report("AIR09_SEAM_OUT", dict(
        seam_block(W_OUT, out_pose, out_quats),
        source="%s@0（= A12@24 的姿态）" % JL.NAME))

    start_z = W_IN["pelvis"].z
    end_z = W_OUT["pelvis"].z
    total_fall = (start_z - end_z) * 1000.0
    A.report("AIR09_SEAM_GAP", {
        "start_pelvis_z_mm": round(start_z * 1000.0, 3),
        "end_pelvis_z_mm": round(end_z * 1000.0, 3),
        "total_fall_mm": round(total_fall, 3),
        "free_fall_24f_mm": round(JFE.pelvis_z(0) - JFE.pelvis_z(24), 5) * 1000.0,
        "note": ("★ 清单写「允许改变下落速度」= 落速可改、**落距不可改**："
                 "首帧钉在 Jump_Fall@0、末帧钉在 Jump_Land@0，"
                 "两帧骨盆 z 之差就是本支的总落距（死数）。"
                 "所以想在下砸段砸得更快，只能让前摇段吊得更慢 —— **落距守恒**。"),
    })

    # ---------------------------------------------------------- 臂的几何环带
    arm_len = {s: (W_IN["upperarm.%s" % s] - W_IN["forearm.%s" % s]).length
               + (W_IN["forearm.%s" % s] - W_IN["hand.%s" % s]).length
               for s in SIDES}
    hand_len = {s: (W_IN["hand.%s.tail" % s] - W_IN["hand.%s" % s]).length
                for s in SIDES}
    A.report("AIR09_ARM_BAND", {
        "arm_len_mm": {s: round(arm_len[s] * 1000.0, 2) for s in SIDES},
        "hand_len_mm": {s: round(hand_len[s] * 1000.0, 2) for s in SIDES},
        "reach_max_mm": {s: round((arm_len[s] + hand_len[s]) * 1000.0, 1)
                         for s in SIDES},
        "wrist_upper_mm": {s: round(arm_len[s] * 0.9995 * 1000.0, 1)
                           for s in SIDES},
        "fold_min_mm": {s: round(arm_len[s] * 0.32 * 1000.0, 1) for s in SIDES},
        "a0_fist_rel_len_mm": {
            s: round((W_IN["hand.%s.tail" % s]
                      - W_IN["upperarm.%s" % s]).length * 1000.0, 1)
            for s in SIDES},
        "note": ("`rel` 法（手骨指向 = normalize(rel)）⟹ 腕距 = |rel| − hand_len，"
                 "必须落在 [fold_min, 0.9995·(Lu+Lf)] 内；否则 `arm_to` 会夹取，"
                 "夹取方向在请求距离趋 0 时转动速度发散 ⟹ `no_teleport` 必红。"),
    })

    # ---------------------------------------------------------- 状态几何（双拳对称）
    rows = []
    for tag, rel, pole in (("A0", {s: W_IN["hand.%s.tail" % s]
                                   - W_IN["upperarm.%s" % s] for s in SIDES},
                           POLE_ARM_AC),
                           ("AC", REL_AC, POLE_ARM_AC),
                           ("AH", REL_AH, POLE_ARM_AH)):
        for s in SIDES:
            r = Vector(rel[s])
            wrist = (r.length - hand_len[s]) * 1000.0
            axis = r.normalized()
            pv = Vector(pole[s])
            sin_pole = (pv - axis * pv.dot(axis)).length
            rows.append({
                "state": tag, "side": s,
                "rel_mm": mm(r), "rel_len_mm": round(r.length * 1000.0, 1),
                "wrist_req_mm": round(wrist, 1),
                "in_band": bool(arm_len[s] * 0.32 * 1000.0 <= wrist
                                <= arm_len[s] * 0.9995 * 1000.0),
                "axis": [round(x, 4) for x in axis],
                "pole_sin": round(sin_pole, 4),
            })
    d_ac = math.degrees(Vector(REL_AC["L"]).normalized().angle(
        (W_IN["hand.L.tail"] - W_IN["upperarm.L"]).normalized()))
    d_ah = math.degrees(Vector(REL_AH["L"]).normalized().angle(
        Vector(REL_AC["L"]).normalized()))
    A.report("AIR09_ARM_TARGETS", {
        "rows": rows,
        "all_in_band": all(r["in_band"] for r in rows),
        "dir_swing_deg": {"A0→AC(前摇举拳)": round(d_ac, 1),
                          "AC→AH(下砸)": round(d_ah, 1)},
        "fist_down_travel_mm": round((REL_AC["L"].z - REL_AH["L"].z) * 1000.0, 1),
        "fist_up_travel_mm": round(
            (REL_AC["L"].z - (W_IN["hand.L.tail"] - W_IN["upperarm.L"]).z)
            * 1000.0, 1),
        "note": "双拳左右镜像；两臂的 `arm_to` 请求距离各自验一遍（B08 只测了单臂）。",
    })

    # ---------------------------------------------------------- 腿的姿态几何
    leg_rows = []
    a0_ank = {s: W_IN["foot." + s] - W_IN["thigh." + s] for s in SIDES}
    ah_ank = {s: W_OUT["foot." + s] - W_OUT["thigh." + s] for s in SIDES}
    for tag, ank in (("A0(接缝)", a0_ank),
                     ("AC(收膝)", {s: a0_ank[s] + ANK_AC_DELTA for s in SIDES}),
                     ("AH(落地构型)", ah_ank)):
        for s in SIDES:
            v = -ank[s].z
            length = ank[s].length
            leg_rows.append({
                "state": tag, "side": s,
                "ankle_rel_hip_mm": mm(ank[s]),
                "vert_mm": round(v * 1000.0, 1),
                "hip_ankle_mm": round(length * 1000.0, 1),
                "ratio": round(length / (A.L_THIGH + A.L_SHIN), 4),
                "headroom_mm": round((A.L_THIGH + A.L_SHIN - length) * 1000.0, 1),
            })
    A.report("AIR09_LEG_TARGETS", {
        "rows": leg_rows,
        "limit_mm": round((A.L_THIGH + A.L_SHIN) * 1000.0, 1),
        "vert_seam_out_mm": {s: round(W_OUT["thigh." + s].z
                                      - W_OUT["foot." + s].z, 6) * 1000.0
                             for s in SIDES},
        "note": ("腿的伸展只跟**姿态**有关、与弹道无关（踝目标是「髋相对」量）⟹ "
                 "`all_airborne_ok` 的腿口径改用**结构尺子**："
                 "不许比**落地姿态（出口接缝）**伸得更长（B08 拿入口接缝当基准，"
                 "那是把 640 mm 的屈腿姿势当上限 —— 而本支的任务就是把它伸到 782）。"),
    })

    # ---------------------------------------------------------- 落速表
    c = solve_chamber_scale(total_fall)
    prof = fall_profile(c)
    cum, z = [], start_z * 1000.0
    for i, step in enumerate(prof):
        cum.append(round(z, 2))
        z -= step
    cum.append(round(z, 2))
    vf = [round(v_free(f), 3) for f in range(0, HIT)]
    slam_free = sum(v_free(f) for f in range(SLAM_START, HIT))
    slam_real = sum(prof[SLAM_START:HIT])
    deltas = [round(prof[i + 1] - prof[i], 4) for i in range(SLAM_START, HIT - 1)]
    A.report("AIR09_VELOCITY", {
        "chamber_scale": round(c, 6),
        "chamber_scale_note": ("前摇吊速比例 = 唯一自由量，由「总落距 = 两接缝骨盆 z 差」"
                               "**反解**（200 步二分），不是手调的残差。"),
        "v_mm_per_frame": [round(v, 3) for v in prof],
        "v_free_reference_mm": vf + ["—"] * (len(prof) - len(vf)),
        "pelvis_z_mm": cum,
        "sum_mm": round(sum(prof), 4),
        "target_fall_mm": round(total_fall, 4),
        "residual_mm": round(sum(prof) - total_fall, 9),
        "slam_range": [SLAM_START, HIT],
        "slam_total_mm": round(slam_real, 2),
        "slam_free_equiv_mm": round(slam_free, 2),
        "slam_ratio": round(slam_real / slam_free, 4),
        "slam_deltas_strictly_increasing": all(
            deltas[i + 1] > deltas[i] for i in range(len(deltas) - 1)),
        "slam_deltas_mm": deltas,
        "monotone_down": all(v > 0.0 for v in prof),
        "end_v_mm": round(prof[-1], 3),
        "a13_entry_v_mm": round(v_free(24 - 22 + (TOTAL - 1 - 0)) if False
                                else (JFE.pelvis_z(24) - JFE.pelvis_z(25)) * 1000.0, 3),
        "hitstop_fall_mm": round(prof[HIT] + prof[HIT + 1], 2),
        "hint": ("区间 [1.2, 2.2] 的物理含义：下界 = 真的砸下去了（不只是滑落），"
                 "上界 = 不是瞬移。**落距守恒** ⟹ 前摇 c 越小（吊得越狠）"
                 "下砸就能砸得越重。"),
    })

    # ---------------------------------------------------------- 末帧回收预算
    ramp = RETURN_END - RETURN_START
    est = {}
    for tag, swing in (("AC→AH(下砸)", d_ah), ("AH→A13@0(收招)", None)):
        if swing is None:
            continue
        est[tag] = round(swing, 1)
    # 收招段的角度行程：用「命中姿态 → A13@0」的**世界方向**差做下界估计
    A.report("AIR09_RETURN_BUDGET", {
        "return_frames": ramp,
        "method": ("末帧 = A13@0 的**姿态克隆**（`_euler_mix` 落在同一支上）⟹ "
                   "首步占比 = 1−(1−1/%d)^1.40 = %.4f；"
                   "单帧 ≤25° ⟹ 欧拉行程 D 必须 ≤ %.1f°。"
                   % (ramp, 1.0 - (1.0 - 1.0 / ramp) ** 1.40,
                      25.0 / (1.0 - (1.0 - 1.0 / ramp) ** 1.40))),
        "euler_travel_budget_deg": round(
            25.0 / (1.0 - (1.0 - 1.0 / ramp) ** 1.40), 2),
        "slam_dir_swing_deg": est,
        "hand_dir_A0": {s: [round(x, 4) for x in
                            (W_IN["hand.%s.tail" % s]
                             - W_IN["upperarm.%s" % s]).normalized()]
                        for s in SIDES},
        "hand_dir_AC": {s: [round(x, 4) for x in Vector(REL_AC[s]).normalized()]
                        for s in SIDES},
        "hand_dir_AH": {s: [round(x, 4) for x in Vector(REL_AH[s]).normalized()]
                        for s in SIDES},
        "hand_dir_out": {s: [round(x, 4) for x in
                             (W_OUT["hand.%s.tail" % s]
                              - W_OUT["upperarm.%s" % s]).normalized()]
                         for s in SIDES},
        "risk": ("镜像对称 ⟹ 躯干无 ry 扭转（B08 的 99° 前臂扭转不会出现），"
                 "下砸是**矢状面**摆动（主要吃 arm 的 rz），欧拉放大系数接近 1.1；"
                 "但仍要跑一遍门禁确认（`no_teleport` 阈值 25 **一字不放宽**）。"),
    })

    print("AIR09_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("AIR09_PROBE_FAILURE " + traceback.format_exc())
