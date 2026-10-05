"""临时探针：钉死 pelvis.location ↔ 世界位移的映射（D11 起步前的一次性标定）。"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
from mathutils import Vector  # noqa: E402

arm, meshes = A.open_animation_project()
A.setup_scene()

A.reset_pose(arm)
if arm.animation_data:
    arm.animation_data.action = None
bpy.context.view_layer.update()
base = Vector(A.bone_world(arm, "pelvis", "head"))
base_t = Vector(A.bone_world(arm, "thigh.L", "head"))
print("ZSEAM_BASE pelvis_head=%s thighL_head=%s"
      % ([round(v * 1000, 2) for v in base], [round(v * 1000, 2) for v in base_t]))

Z_SEAM = base.z
for label, off in (("wloc_drop_12", A.wloc(0.0, 0.0, Z_SEAM - 0.012 - 0.900)),
                   ("wloc_side_30", A.wloc(0.030, 0.0, Z_SEAM - 0.900)),
                   ("wloc_back_30", A.wloc(0.0, 0.030, Z_SEAM - 0.900)),
                   ("raw_y_m012", (0.0, -0.012, 0.0))):
    A.reset_pose(arm)
    arm.pose.bones["pelvis"].location = off
    bpy.context.view_layer.update()
    now = Vector(A.bone_world(arm, "pelvis", "head"))
    print("ZSEAM_%s local=%s world_delta_mm=%s"
          % (label, [round(v, 6) for v in off],
             [round(v * 1000, 3) for v in (now - base)]))

A.reset_pose(arm)
bpy.context.view_layer.update()
print("ZSEAM_done")
