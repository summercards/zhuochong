"""probe_d16_measure —— D16 `Ground_Hit` 开工前的实测标定（只读，不改任何资产）。

回答四件事（清单 D16 计划 §4 第 3 步）：
  (a) 上游 D15 `Knockdown_B` 的 **逐帧骨盆世界 z** —— 确认末帧值可作为 `Z_END`；
  (b) 上游末帧（f20）逐对象最低点 —— 躺平时**最低行由谁接管**（腿是抬着的）；
  (c) 上游末帧「骨盆 → 胸/头/肩/踝/鞋底」的高度表 —— 弹起幅度的基线；
  (d) 「上身弧」试算：把脊柱链按比例抬起，量 chest 尾端 / head 尾端 能升多少。

用法：
    blender.exe --background --factory-startup --python probe_d16_measure.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                    # noqa: E402

SEAM_ACTION = "Knockdown_B"
SEAM_FRAME = 20
SIDES = ("L", "R")


def _pitch(direction):
    return -math.degrees(math.atan2(direction.y, direction.z))


def _obj_lows():
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mw = ev.matrix_world
        pts = [mw @ v.co for v in me.vertices]
        rows.append({"obj": obj.name, "z_min_mm": round(min(p.z for p in pts) * 1000.0, 2),
                     "y_min_mm": round(min(p.y for p in pts) * 1000.0, 1),
                     "y_max_mm": round(max(p.y for p in pts) * 1000.0, 1)})
        ev.to_mesh_clear()
    rows.sort(key=lambda r: r["z_min_mm"])
    return rows


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    action = bpy.data.actions.get(SEAM_ACTION)
    if action is None:
        raise RuntimeError("找不到 %s" % SEAM_ACTION)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    torso = ("root", "pelvis", "spine_01", "spine_02", "chest", "neck", "head")
    per = {}
    for f in range(0, 21):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        ankles = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
        sole = A.foot_lowest_by_side()
        per[str(f)] = {
            "pelvis_z_mm": round(Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 3),
            "pelvis_y_mm": round(Vector(A.bone_world(arm, "pelvis", "head")).y * 1000.0, 3),
            "chest_tail_z_mm": round(Vector(A.bone_world(arm, "chest", "tail")).z * 1000.0, 3),
            "head_tail_z_mm": round(Vector(A.bone_world(arm, "head", "tail")).z * 1000.0, 3),
            "shoulderL_z_mm": round(Vector(A.bone_world(arm, "upperarm.L", "head")).z * 1000.0, 3),
            "shoulderR_z_mm": round(Vector(A.bone_world(arm, "upperarm.R", "head")).z * 1000.0, 3),
            "ankle_z_mm": {s: round(ankles[s].z * 1000.0, 3) for s in SIDES},
            "sole_mm": {s: (None if sole[s] is None else round(sole[s][2] * 1000.0, 3))
                        for s in SIDES},
            "pitches_deg": {n: round(_pitch(Vector(A.bone_direction(arm, n))), 3)
                            for n in torso},
        }
    lows = {str(f): _obj_lows()[:6] for f in (0, 2, 6, 12, 16, 20)}
    # 骨长
    lengths = {}
    for n in ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
              "thigh.L", "shin.L", "foot.L"):
        lengths[n] = round(arm.pose.bones[n].length * 1000.0, 3)
    A.report("D16_MEASURE", {
        "seam": {"action": SEAM_ACTION, "frame": SEAM_FRAME,
                 "frame_range": [int(v) for v in action.frame_range]},
        "per_frame": per,
        "lowest_objects": lows,
        "bone_len_mm": lengths,
    })


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D16_MEASURE_FAILURE " + traceback.format_exc())
