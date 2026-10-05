"""probe_c04_baseline —— C04 `Grab_Start` 开工第一探针（**只读，不写任何资产**）。

清单对 C04 的要求：「快速伸手抓住敌人，**必须明确双手最终抓取位置**，便于双角色对位」。

C04 详细计划（清单尾部）要求"只量不做"三件事，本探针一次量完：

① **臂长可达域** —— 手臂三骨的真实骨长，以及在**上游接缝姿态**下
   双手能前伸到的最远世界坐标（沿 −y）。抓取点必须落在这个域内，
   否则要么够不着（IK 截断 = 手贴在肩前不动），要么靠"神臂"假拉伸。

② **上游接缝真值** —— `Heavy_01@CANCEL(36)`（C01/C02/C03 同源）与
   `Idle_01@0`（C01~C03 的出口）。C04 的上游候选就是这两个。
   量：骨盆世界坐标 + 局部 location、双踝、鞋底、六根臂骨的世界朝向。

③ **可达域的方向切片** —— 在几个候选"抓取方向"（前上 / 水平 / 前下）
   上各解一次满伸姿态，给出 hand.tail 的世界落点。抓取点要
   **明确、可复现、落在双腿站架之内**（方便敌人对位），所以先看这张表再定姿态。

④ **臂展比率的量法** —— `grab_reach_ok` 要一个"手能够到多远 / 臂有多长"的比值。
   计划写的是"髋距 / 臂长"，但**髋（骨盆）不是臂的根**：骨盆到肩还有约 0.5 m，
   拿髋当根会得到 ~1.6 的无意义比值。本探针同时量
   `手→肩` 与 `手→骨盆` 两套，把口径在数据上定死（登记进报告，日志里说明）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c04_baseline.py
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import anim_lib as A  # noqa: E402

ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
SHOULDERS = ("shoulder.L", "shoulder.R")
LEG_BONES = ("thigh.L", "shin.L", "foot.L",
             "thigh.R", "shin.R", "foot.R")

# 候选抓取方向（世界系：x = 左正，y = 身后正，z = 上正；角色正面朝 −y）
CANDIDATE_DIRS = {
    "fwd":      (0.00, -1.00, 0.00),
    "fwd_up15": (0.00, -0.966, 0.259),
    "fwd_up30": (0.00, -0.866, 0.500),
    "fwd_dn15": (0.00, -0.966, -0.259),
    "fwd_dn30": (0.00, -0.866, -0.500),
    # 实战抓取：两手不完全平行，略向外张（抓对手左右衣领 / 双肩）
    "fwd_up15_out": (0.22, -0.936, 0.275),
    "fwd_up15_in": (-0.22, -0.936, 0.275),
    "fwd_dn10_out": (0.24, -0.929, -0.282),
}


def bone_lengths(arm):
    out = {}
    for bone in arm.pose.bones:
        out[bone.name] = round(bone.bone.length * 1000.0, 3)
    return out


def snapshot(arm, action, frame, label):
    """读某 Action 某帧的全部姿态量（供接缝用）。"""
    scene = bpy.context.scene
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(frame)
    bpy.context.view_layer.update()

    euler = {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
             for b in arm.pose.bones}
    loc = {b.name: tuple(b.location) for b in arm.pose.bones}
    low = A.foot_lowest_by_side()
    out = {
        "label": label, "action": action.name, "frame": frame,
        "pelvis_mm": [round(v * 1000.0, 2)
                      for v in A.bone_world(arm, "pelvis", "head")],
        "pelvis_loc": [round(v, 6) for v in loc["pelvis"]],
        "neck_mm": [round(v * 1000.0, 2)
                    for v in A.bone_world(arm, "neck", "head")],
        "head_mm": [round(v * 1000.0, 2)
                    for v in A.bone_world(arm, "head", "head")],
        "nonempty_euler": sorted(k for k, v in euler.items()
                                 if max(abs(x) for x in v) > 1e-9),
    }
    for side in ("L", "R"):
        ank = Vector(A.bone_world(arm, "foot." + side, "head"))
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        out["ankle_" + side + "_mm"] = [round(v * 1000.0, 2) for v in ank]
        out["ankle_" + side + "_rel_pelvis_y_mm"] = round(
            (ank.y - A.bone_world(arm, "pelvis", "head").y) * 1000.0, 2)
        out["hip_" + side + "_mm"] = [round(v * 1000.0, 2) for v in hip]
        out["leg_reach_" + side + "_mm"] = round((ank - hip).length * 1000.0, 2)
        out["sole_" + side + "_mm"] = (None if low[side] is None
                                       else round(low[side][2] * 1000.0, 3))
    out["stance_width_mm"] = round(abs(
        A.bone_world(arm, "foot.L", "head").y
        - A.bone_world(arm, "foot.R", "head").y) * 1000.0, 2)
    out["euler"] = euler
    out["loc"] = loc
    return out


def reach_scan(arm, seam, dirs):
    """在上游接缝姿态下，把六根臂骨全部指向 `d`（满伸），量 hand.tail 落点。"""
    base = {k: v for k, v in seam["euler"].items()}
    base["@loc"] = {"pelvis": seam["loc"]["pelvis"]}
    base.update(A.FIST)
    rows = []
    for label, d in dirs.items():
        A.apply_pose(arm, base)
        for bone in ARM_BONES:
            dir_v = (d[0], d[1], d[2])
            if bone.endswith(".R"):
                dir_v = (-d[0], d[1], d[2])   # 右手方向镜像 x
            A.aim_bone(arm, bone, dir_v)
        bpy.context.view_layer.update()
        row = {"dir": label, "vec": d}
        for hand in ("hand.L", "hand.R"):
            tail = Vector(A.bone_world(arm, hand, "tail"))
            row[hand + "_tail_mm"] = [round(v * 1000.0, 2) for v in tail]
            sh = Vector(A.bone_world(arm, hand.replace("hand", "upperarm"),
                                     "head"))
            pel = Vector(A.bone_world(arm, "pelvis", "head"))
            row[hand + "_to_shoulder_mm"] = round((tail - sh).length * 1000.0, 2)
            row[hand + "_to_pelvis_mm"] = round((tail - pel).length * 1000.0, 2)
        rows.append(row)
    return rows


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    lengths = bone_lengths(arm)
    arm_len_l = (lengths["upperarm.L"] + lengths["forearm.L"]
                 + lengths["hand.L"])
    arm_len_r = (lengths["upperarm.R"] + lengths["forearm.R"]
                 + lengths["hand.R"])
    leg_len = lengths["thigh.L"] + lengths["shin.L"]
    A.report("C04_LENGTHS", {
        "upperarm_mm": lengths["upperarm.L"], "forearm_mm": lengths["forearm.L"],
        "hand_mm": lengths["hand.L"], "shoulder_mm": lengths["shoulder.L"],
        "clavicle_span_mm": lengths["shoulder.L"],
        "arm_total_L_mm": round(arm_len_l, 3),
        "arm_total_R_mm": round(arm_len_r, 3),
        "thigh_mm": lengths["thigh.L"], "shin_mm": lengths["shin.L"],
        "foot_mm": lengths["foot.L"], "leg_total_mm": round(leg_len, 3),
        "leg_lib_total_mm": round((A.L_THIGH + A.L_SHIN) * 1000.0, 3),
        "torso_pelvis_to_neck_mm": lengths.get("spine_01", 0.0),
    })

    heavy = bpy.data.actions.get("Heavy_01")
    idle = bpy.data.actions.get("Idle_01")
    snapshots = {}
    if heavy is not None:
        s = snapshot(arm, heavy, 36, "Heavy_01@36")
        snapshots["Heavy_01@36"] = s
    if idle is not None:
        s2 = snapshot(arm, idle, 0, "Idle_01@0")
        snapshots["Idle_01@0"] = s2

    for label, snap in snapshots.items():
        slim = {k: v for k, v in snap.items() if k not in ("euler", "loc")}
        A.report("C04_SEAM", slim)

    seam = snapshots.get("Heavy_01@36")
    if seam is None:
        print("C04_PROBE 缺 Heavy_01")
        return

    # 接缝姿态下的肩宽 / 肩高（抓取点的可行域上界由它决定）
    base = {k: v for k, v in seam["euler"].items()}
    base["@loc"] = {"pelvis": seam["loc"]["pelvis"]}
    A.apply_pose(arm, base)
    bpy.context.view_layer.update()
    A.report("C04_FRAME0_ARMS", {
        "shoulder_L_mm": [round(v * 1000.0, 2)
                          for v in A.bone_world(arm, "upperarm.L", "head")],
        "shoulder_R_mm": [round(v * 1000.0, 2)
                          for v in A.bone_world(arm, "upperarm.R", "head")],
        "hand_L_tail_mm": [round(v * 1000.0, 2)
                           for v in A.bone_world(arm, "hand.L", "tail")],
        "hand_R_tail_mm": [round(v * 1000.0, 2)
                           for v in A.bone_world(arm, "hand.R", "tail")],
        "arm_dirs": {b: [round(v, 4) for v in A.bone_direction(arm, b)]
                     for b in ARM_BONES},
        "arm_total_L_mm": round(arm_len_l, 3),
        "arm_total_R_mm": round(arm_len_r, 3),
    })

    # ★ 满伸扫描：注意 `aim_bone` 只定方向，三骨同向 = 手臂**完全伸直**
    #   ⟹ 这是"可达域的外壳"（上界），不是可以交付的抓取姿态。
    rows = reach_scan(arm, seam, CANDIDATE_DIRS)
    A.report("C04_REACH", {"full_extension_rows": rows,
                           "arm_len_L_mm": round(arm_len_l, 3),
                           "arm_len_R_mm": round(arm_len_r, 3),
                           "note": "full extension = 三骨同向；真实抓取要留肘弯"})

    # 满伸下"手→肩 / 臂长"必然 ≈ 1.0 —— 量出来确认口径
    for row in rows:
        for hand in ("hand.L", "hand.R"):
            key = hand + "_ratio"
            row[key] = round(row[hand + "_to_shoulder_mm"]
                             / (arm_len_l if hand.endswith(".L") else arm_len_r),
                             5)
    print("C04_REACH_JSON " + json.dumps(rows, ensure_ascii=False))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("C04_PROBE_FAILURE " + traceback.format_exc())
