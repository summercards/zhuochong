"""probe_c04_dump —— 打印 Heavy_01@36 / Idle_01@0 的关键骨欧拉与肩位（只读）。"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
import anim_lib as A  # noqa: E402

WATCH = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
         "shoulder.L", "shoulder.R", "upperarm.L", "forearm.L", "hand.L",
         "upperarm.R", "forearm.R", "hand.R",
         "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R")

arm, _m = A.open_animation_project()
A.setup_scene()
scene = bpy.context.scene
for name, frame in (("Heavy_01", 36), ("Idle_01", 0), ("Combo_Finish", 40)):
    action = bpy.data.actions.get(name)
    if action is None:
        print("MISSING " + name)
        continue
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    print("=== %s@%d ===" % (name, frame))
    print("  pelvis_loc = %s" % [round(v, 6) for v in
                                 arm.pose.bones["pelvis"].location])
    for bone in WATCH:
        e = tuple(round(math.degrees(v), 3)
                  for v in arm.pose.bones[bone].rotation_euler)
        head = A.bone_world(arm, bone, "head")
        tail = A.bone_world(arm, bone, "tail")
        print("  %-12s euler=%-24s head=[%7.2f %7.2f %7.2f] "
              "tail=[%7.2f %7.2f %7.2f]"
              % (bone, str(e), head.x * 1000, head.y * 1000, head.z * 1000,
                 tail.x * 1000, tail.y * 1000, tail.z * 1000))
