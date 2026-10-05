import os, sys, json
import bpy
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A
arm, meshes = A.open_animation_project()
A.setup_scene()
scene = bpy.context.scene
action = bpy.data.actions["GetUp_F"]
arm.animation_data.action = action
A._bind_slot(arm, action)
out = {}
for f in (0, 4, 6, 9):
    scene.frame_set(f); bpy.context.view_layer.update()
    d = {}
    for n in ("hand.L","hand.R"):
        pb = arm.pose.bones[n]
        d[n] = {"head_mm": [round(v*1000,1) for v in (arm.matrix_world @ pb.head)],
                "tail_mm": [round(v*1000,1) for v in (arm.matrix_world @ pb.tail)]}
    for n in ("Finger_Middle_L","Finger_Index_L","Thumb_L","Finger_Pinky_R","Finger_Middle_R"):
        o = bpy.data.objects.get(n)
        if o is None: continue
        d[n] = {"vgroups": [g.name for g in o.vertex_groups],
                "mods": [m.type for m in o.modifiers],
                "parent": (o.parent.name if o.parent else None)}
    out[str(f)] = d
# bones present containing finger
out["bones"] = [b.name for b in arm.pose.bones if "inger" in b.name or "humb" in b.name or b.name.startswith("hand")]
print("D17_HAND " + json.dumps(out, ensure_ascii=False))
