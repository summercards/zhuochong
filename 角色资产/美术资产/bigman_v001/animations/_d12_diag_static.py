import os, sys
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A

arm, meshes = A.open_animation_project()
action = bpy.data.actions.get("Launch_Hit")
arm.animation_data.action = action
A._bind_slot(arm, action)
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()

def bbox(obj, frame):
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    ev = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    pts = [obj.matrix_world @ Vector(c) for c in ev.bound_box]
    return (min(p.z for p in pts), max(p.z for p in pts),
            min(p.x for p in pts), max(p.x for p in pts))

rows = []
for o in bpy.data.objects:
    if o.type != "MESH":
        continue
    a = bbox(o, 0)
    b = bbox(o, 30)
    dz = abs(b[0] - a[0])
    dx = abs(b[2] - a[2])
    rows.append((dz + dx, o.name, a, b))
rows.sort()
print("STATIC_CANDIDATES (top 12 by 'did not move'):")
for score, name, a, b in rows[:12]:
    print("  %-26s move=%.4f  f0 z=[%.3f..%.3f] x=[%.3f..%.3f]  f30 z=[%.3f..%.3f] x=[%.3f..%.3f]"
          % (name, score, a[0], a[1], a[2], a[3], b[0], b[1], b[2], b[3]))
print("MOVERS (top 3):")
for score, name, a, b in rows[-3:]:
    print("  %-26s move=%.4f  f0 z=[%.3f..%.3f]  f30 z=[%.3f..%.3f]" % (name, score, a[0], a[1], b[0], b[1]))
print("N_MESH", len(rows))
