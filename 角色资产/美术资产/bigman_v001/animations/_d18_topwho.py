import os, sys, json
import bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A

arm, meshes = A.open_animation_project()
A.setup_scene()
action = bpy.data.actions["GetUp_B"]
arm.animation_data.action = action
A._bind_slot(arm, action)
scene = bpy.context.scene

def hi_by_object():
    dg = bpy.context.evaluated_depsgraph_get()
    rows = {}
    for obj in meshes:
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) == 0:
            ev.to_mesh_clear(); continue
        mw = ev.matrix_world
        rows[obj.name] = max((mw @ v.co).z for v in me.vertices) * 1000.0
        ev.to_mesh_clear()
    return rows

for f in (0, 1, 2, 5, 9, 12, 22, 25, 34, 46):
    scene.frame_set(f)
    bpy.context.view_layer.update()
    rows = hi_by_object()
    top = sorted(rows.items(), key=lambda kv: -kv[1])[:5]
    print("f%-3d top5: %s" % (f, [(n, round(z, 1)) for n, z in top]))
