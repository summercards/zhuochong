import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import anim_lib as A

NAME = "Knockdown_F"

def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    action = bpy.data.actions.get(NAME)
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    for f in (0, 6, 7, 11, 13, 16, 20):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        rows = []
        for obj in bpy.data.objects:
            if obj.type != "MESH":
                continue
            ev = obj.evaluated_get(dg)
            me = ev.to_mesh()
            if len(me.vertices) == 0:
                ev.to_mesh_clear(); continue
            mw = ev.matrix_world
            zs = [ (mw @ v.co).z for v in me.vertices ]
            rows.append((min(zs)*1000.0, obj.name))
            ev.to_mesh_clear()
        rows.sort()
        out[str(f)] = [{"z_mm": round(z,1), "obj": n} for z, n in rows[:5]]
    print("D14_LOW " + json.dumps(out, ensure_ascii=False))

try:
    main()
except Exception:
    import traceback
    print("D14_LOW_FAILURE " + traceback.format_exc())
