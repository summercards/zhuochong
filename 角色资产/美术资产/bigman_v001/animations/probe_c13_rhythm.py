"""probe_c13_rhythm —— 只量不做：为 C13 `Ultimate_Attack` 大招攻击 定标「节奏」与「可达性」。

清单「下一支详细制作计划 —— C13 `Ultimate_Attack`」§4「开工顺序」第 2 条要求：

  ① 用**离线速度剖面**试排 3 种段间隔方案（`[6,10,4,14]` / `[8,8,8,8]` / `[5,7,6,16]`
     以及本支自选的 3 个候选），算出各自的**变异系数**与**相邻间隔比**，
     **先量再定阈值**；
  ② 测**各段命中帧的骨可达性**（拳 / 肘 / 膝 / 脚的前伸距离 vs 臂长 / 腿长），
     确认不需要**深折叠**（★ C12 第 2 号教训：`l1=328 mm`、`l23=321.675 mm`，
     两段几乎等长 ⟹ 深折叠 ⟹ 病态反解 ⟹ 角度被放大成 48°/帧）。

★ 本支为什么必须把「节奏」变成可失败的门禁（计划 §1「失败模式」）：

   C12 的失败模式是"运动学全绿但什么也没发生"；C13 的失败模式是
   **「六段变成一个大摆臂」** 与 **「停是假的（把整段拖慢）」**。
   这两样在通用项（贴地 / 不滑 / 不跳变）里**全是绿的** —— 所以节奏必须单独立判据，
   且判据必须能失败。

★ 本支节奏口径（先量后定，见下方 `SCHEMES` 的实测表）：

   · `seg_len[i]` = `HIT_i − HIT_{i-1}`（`HIT_0 = 0`）—— 到达第 i 次命中所用的帧数，
     就是"段间隔"。变异系数 `CV = std/mean` 量化"不许平均"。
   · `adjacent_ratio` = `seg_len[i+1] / seg_len[i]` 的最大值，
     量化"至少一对相邻间隔 ≥ 1.8×"。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c13_rhythm.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402

SIDES = ("L", "R")

# ---------------------------------------------------------------- 候选段间隔方案
# 每个方案是 [start→HIT_1, HIT_1→HIT_2, HIT_2→HIT_3, HIT_3→HIT_4]（4 段重击）。
SCHEMES = {
    "P_flat_8888": [8, 8, 8, 8],
    "P_alt_6_10_4_14": [6, 10, 4, 14],
    "P_alt_5_7_6_16": [5, 7, 6, 16],
    "Q_fast_pause_fast_heavy": [10, 20, 9, 24],
    "Q_fast_pause_fast_heavy_b": [12, 22, 8, 24],
    "Q6_five_seg": [10, 20, 8, 6, 26],
}

# ---------------------------------------------------------------- 门禁草案阈值（先量后定）
CV_MIN = 0.25
ADJ_RATIO_MIN = 1.8


def scheme_stats(lens):
    n = len(lens)
    mean = sum(lens) / float(n)
    var = sum((v - mean) ** 2 for v in lens) / float(n)     # 总体方差
    std = math.sqrt(var)
    ratios = [lens[i + 1] / float(lens[i]) for i in range(n - 1)]
    return {
        "lens": lens,
        "mean": round(mean, 4),
        "std": round(std, 4),
        "cv": round(std / mean, 4),
        "adjacent_ratio": [round(r, 4) for r in ratios],
        "max_adjacent_ratio": round(max(ratios), 4) if ratios else 0.0,
        "cv_ok": bool(std / mean >= CV_MIN),
        "ratio_ok": bool(ratios and max(ratios) >= ADJ_RATIO_MIN),
    }


# ---------------------------------------------------------------- 可达性候选
# 命中目标用「相对该段肩关节」的偏移定义 —— 这样"离肩多远"直接就是臂伸长比例，
# 与 `arm_seat` 的 `cos_sh = (l1²+d²−l23²)/(2·l1·d)` 同口径（C12 第 2 号教训）。
# +X = 角色左、−Y = 角色正面、+Z = 上。
STRIKE_TARGETS = {
    # name: (drive_side, shoulder_offset_m, note)
    "S1_R_jab": ("R", (0.02, -0.42, 0.02),
                 "右直拳：接近满伸（前伸 420 mm）"),
    "S2_L_hook": ("L", (0.30, -0.26, 0.03),
                  "左摆拳：横向抡出（侧向 300 mm）"),
    "S3_R_uppercut": ("R", (0.06, -0.20, 0.20),
                      "右上勾：紧凑上打（合距 ≈300 mm）"),
    "S4_R_overhead_start": ("R", (-0.08, -0.12, 0.52),
                            "重终结蓄力：双拳过顶（上举 520 mm）"),
    "S4_R_smash_hit": ("R", (0.02, -0.30, -0.30),
                       "重终结命中：下砸（前下 420 mm）"),
    "GUARD_L": ("L", (0.14, -0.24, 0.05), "护手拳位（对照）"),
}

# 深折叠警戒：C12 实测 25%（160/650）会病态；40% 起安全。
FOLD_WARN_RATIO = 0.40

# 骨盆高度扫描（相对 Idle 830 mm 的增量，mm）
DROP_SCAN = (0.0, -40.0, -80.0, -120.0, -160.0, -200.0)

SNAPSHOT_BONES = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                  "shoulder.L", "shoulder.R", "upperarm.L", "upperarm.R",
                  "forearm.L", "forearm.R", "hand.L", "hand.R",
                  "thigh.L", "thigh.R", "shin.L", "shin.R",
                  "foot.L", "foot.R", "toe.L", "toe.R")


def snapshot(arm, label):
    out = {"label": label, "bones": {}}
    for name in SNAPSHOT_BONES:
        if name not in arm.pose.bones:
            continue
        head = A.bone_world(arm, name, "head")
        tail = A.bone_world(arm, name, "tail")
        out["bones"][name] = {
            "head_mm": [round(v * 1000.0, 2) for v in head],
            "tail_mm": [round(v * 1000.0, 2) for v in tail],
        }
    low = A.foot_lowest_by_side()
    out["sole_mm"] = {s: (None if low[s] is None
                          else round(low[s][2] * 1000.0, 2)) for s in SIDES}
    return out


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    out = {
        "schemes": {k: scheme_stats(v) for k, v in SCHEMES.items()},
        "thresholds": {"cv_min": CV_MIN, "adjacent_ratio_min": ADJ_RATIO_MIN},
    }

    if I1.NAME not in bpy.data.actions:
        print("C13_PROBE 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, meshes = A.open_animation_project()
        A.setup_scene()

    # ---- 骨架常数（复核 C12 预支值，不重新标定）
    limit = A.L_THIGH + A.L_SHIN
    arm_len = {}
    for side in SIDES:
        arm_len[side] = {
            "upper_mm": round(arm.pose.bones["upperarm." + side].length * 1000, 3),
            "forearm_mm": round(arm.pose.bones["forearm." + side].length * 1000, 3),
            "hand_mm": round(arm.pose.bones["hand." + side].length * 1000, 3),
        }
        arm_len[side]["l23_mm"] = round(
            arm_len[side]["forearm_mm"] + arm_len[side]["hand_mm"], 3)
        arm_len[side]["total_mm"] = round(
            arm_len[side]["upper_mm"] + arm_len[side]["l23_mm"], 3)
        arm_len[side]["abs_diff_mm"] = round(
            abs(arm_len[side]["upper_mm"] - arm_len[side]["l23_mm"]), 3)
    out["arm_len"] = arm_len
    out["leg_len_mm"] = round(limit * 1000.0, 3)

    # ---- `Idle_01@0` 真值
    scene = bpy.context.scene
    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    A.reset_pose(arm)
    scene.frame_set(0)
    bpy.context.view_layer.update()
    idle = snapshot(arm, "Idle_01@0")
    out["idle"] = idle
    z_seam = idle["bones"]["pelvis"]["head_mm"][2]
    out["pelvis_z_idle_mm"] = z_seam
    ankle0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    out["ankle0_mm"] = {s: [round(v * 1000.0, 2) for v in ankle0[s]]
                        for s in SIDES}
    foot0 = {s: arm.pose.bones["foot." + s].matrix.to_3x3().copy()
             for s in SIDES}
    knee_dir = {}
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        knee_dir[side] = [round(v, 5) for v in (knee - hip).normalized()]
    out["idle_knee_dir"] = knee_dir

    idle_hand = {s: tuple(A.bone_world(arm, "hand." + s, "tail"))
                 for s in SIDES}
    idle_shoulder = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                     for s in SIDES}
    idle_elbow = {}
    for side in SIDES:
        elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        idle_elbow[side] = (elbow - idle_shoulder[side]).normalized()
    out["idle_hand_mm"] = {s: [round(v * 1000.0, 2) for v in idle_hand[s]]
                           for s in SIDES}
    out["idle_shoulder_mm"] = {s: [round(v * 1000.0, 2)
                                   for v in idle_shoulder[s]] for s in SIDES}

    # ---- ① 骨盆高度许可域（脚钉原位、站高变化）
    out["drop_scan"] = {}
    for drop_mm in DROP_SCAN:
        pose = I1.idle_pose(arm, 0.0)
        # 只改骨盆高度，腿由 IK 重新解（其余保持 Idle）
        hip_z = 0.900 + (drop_mm + 0.0) / 1000.0
        thigh_f, bend_f = A.leg_ik(0.0, hip_z, I1.FRONT_ANKLE_Y,
                                   A.Z_ANKLE_REST, tilt_deg=I1.PELVIS_TILT)
        thigh_b, bend_b = A.leg_ik(0.0, hip_z, I1.BACK_ANKLE_Y,
                                   A.Z_ANKLE_REST, tilt_deg=I1.PELVIS_TILT)
        pose["thigh.L"] = (thigh_f, 0.0, -I1.ABDUCT_DEG)
        pose["shin.L"] = (bend_f, 0.0, 0.0)
        pose["thigh.R"] = (thigh_b, 0.0, I1.ABDUCT_DEG)
        pose["shin.R"] = (bend_b, 0.0, 0.0)
        pose["@loc"] = {"pelvis": A.wloc(0.0, 0.0, drop_mm / 1000.0)}
        A.apply_pose(arm, pose)
        for side in SIDES:
            pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
        A.apply_pose(arm, pose)
        low = A.foot_lowest_by_side()
        row = {"pelvis_mm": round(A.bone_world(arm, "pelvis", "head").z * 1000, 2),
               "sole_mm": {s: (None if low[s] is None
                               else round(low[s][2] * 1000.0, 2))
                           for s in SIDES}}
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            ankle = Vector(A.bone_world(arm, "foot." + side, "head"))
            row["reach_" + side] = round((ankle - hip).length / limit, 5)
        out["drop_scan"]["%+05.0f" % drop_mm] = row

    # ---- ② 命中目标可达性（肩在"该段躯干姿态"下的世界位置）
    # 躯干姿态取每段命中的近似（前压 + 拧身），只为把肩送到位置，不追求最终值。
    STRIKE_TORSO = {
        "S1_R_jab": {"pelvis": (6.0, -6.0, 0.0), "spine_01": (3.0, -4.0, 0.0),
                     "spine_02": (3.0, -4.0, 0.0), "chest": (2.0, -8.0, 0.0),
                     "neck": (-6.0, 10.0, 0.0), "head": (4.0, 10.0, 0.0),
                     "shoulder.L": (-10.0, 0.0, 0.0),
                     "shoulder.R": (6.0, 0.0, 0.0)},
        "S2_L_hook": {"pelvis": (7.0, 14.0, 0.0), "spine_01": (4.0, 10.0, 0.0),
                      "spine_02": (4.0, 10.0, 0.0), "chest": (3.0, 12.0, 0.0),
                      "neck": (-6.0, -20.0, 0.0), "head": (5.0, -20.0, 0.0),
                      "shoulder.L": (8.0, 0.0, 0.0),
                      "shoulder.R": (-12.0, 0.0, 0.0)},
        "S3_R_uppercut": {"pelvis": (9.0, -10.0, 0.0), "spine_01": (5.0, -6.0, 0.0),
                          "spine_02": (5.0, -6.0, 0.0), "chest": (4.0, -10.0, 0.0),
                          "neck": (-10.0, 14.0, 0.0), "head": (6.0, 14.0, 0.0),
                          "shoulder.L": (-14.0, 0.0, 0.0),
                          "shoulder.R": (10.0, 0.0, 0.0)},
        "S4_R_overhead_start": {"pelvis": (-6.0, 0.0, 0.0),
                                "spine_01": (-4.0, 0.0, 0.0),
                                "spine_02": (-4.0, 0.0, 0.0),
                                "chest": (-6.0, 0.0, 0.0),
                                "neck": (-4.0, 0.0, 0.0), "head": (2.0, 0.0, 0.0),
                                "shoulder.L": (14.0, 0.0, 0.0),
                                "shoulder.R": (14.0, 0.0, 0.0)},
        "S4_R_smash_hit": {"pelvis": (14.0, 0.0, 0.0),
                           "spine_01": (8.0, 0.0, 0.0),
                           "spine_02": (8.0, 0.0, 0.0), "chest": (10.0, 0.0, 0.0),
                           "neck": (-12.0, 0.0, 0.0), "head": (6.0, 0.0, 0.0),
                           "shoulder.L": (-20.0, 0.0, 0.0),
                           "shoulder.R": (-20.0, 0.0, 0.0)},
        "GUARD_L": {"pelvis": (4.0, 0.0, 0.0), "spine_01": (2.0, 0.0, 0.0),
                    "spine_02": (2.0, 0.0, 0.0), "chest": (1.0, 0.0, 0.0),
                    "neck": (-6.0, 0.0, 0.0), "head": (5.0, 0.0, 0.0),
                    "shoulder.L": (-18.0, 0.0, 0.0),
                    "shoulder.R": (-18.0, 0.0, 0.0)},
    }

    out["reach"] = {}
    for name, (side, offset, note) in STRIKE_TARGETS.items():
        base = I1.idle_pose(arm, 0.0)
        torso = dict(base)
        for bone, angles in STRIKE_TORSO.get(name, {}).items():
            torso[bone] = tuple(angles)
        A.apply_pose(arm, torso)
        bpy.context.view_layer.update()
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        target = shoulder + Vector(offset)
        limit_mm = (arm.pose.bones["upperarm." + side].length
                    + arm.pose.bones["forearm." + side].length
                    + arm.pose.bones["hand." + side].length) * 1000.0
        dist_mm = (target - shoulder).length * 1000.0
        ratio = dist_mm / limit_mm
        out["reach"][name] = {
            "side": side, "note": note,
            "offset_mm": [round(v * 1000.0, 1) for v in offset],
            "shoulder_mm": [round(v * 1000.0, 2) for v in shoulder],
            "target_mm": [round(v * 1000.0, 2) for v in target],
            "dist_mm": round(dist_mm, 2),
            "limit_mm": round(limit_mm, 2),
            "ratio": round(ratio, 5),
            "clamp": bool(dist_mm > limit_mm * 0.9995),
            "fold_warn": bool(ratio < FOLD_WARN_RATIO),
        }

    # ---- ③ 后脚"蹬地抬跟"能给出多少 toe / ankle 位移（`chain_per_hit_ok` 的「脚」节点需要）
    out["heel_lift"] = {}
    for lift_deg in (0.0, 4.0, 8.0, 12.0, 16.0):
        pose = I1.idle_pose(arm, 0.0)
        A.apply_pose(arm, pose)
        for side in SIDES:
            pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
        # 只给后脚（R）抬跟：foot.rx > 0 = 踮脚
        pb = arm.pose.bones["foot.R"]
        pb.rotation_euler.rotate_axis("X", math.radians(lift_deg))
        bpy.context.view_layer.update()
        toe = Vector(A.bone_world(arm, "toe.R", "tail"))
        ankle = Vector(A.bone_world(arm, "foot.R", "head"))
        low = A.foot_lowest_by_side()
        out["heel_lift"]["%02.0f" % lift_deg] = {
            "toe_tail_mm": [round(v * 1000.0, 2) for v in toe],
            "ankle_mm": [round(v * 1000.0, 2) for v in ankle],
            "sole_R_mm": (None if low["R"] is None
                          else round(low["R"][2] * 1000.0, 2)),
            "toe_rise_mm": None,
        }
    base_toe = out["heel_lift"]["00"]["toe_tail_mm"]
    base_ankle = out["heel_lift"]["00"]["ankle_mm"]
    for key, row in out["heel_lift"].items():
        row["toe_rise_mm"] = round(row["toe_tail_mm"][2] - base_toe[2], 2)
        row["ankle_rise_mm"] = round(row["ankle_mm"][2] - base_ankle[2], 2)
        row["ankle_slide_mm"] = round(math.hypot(
            row["ankle_mm"][0] - base_ankle[0],
            row["ankle_mm"][1] - base_ankle[1]), 3)

    A.report("C13_PROBE", out)
    print("C13_PROBE_DONE")


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("C13_PROBE_FAILURE " + traceback.format_exc())
