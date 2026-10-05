"""probe_d15_objects —— 列出全部网格对象，并在接缝帧 `Air_Hit@18` 上逐对象实测最低 z。

用途（D15 §4 第 3 步 (b)）：确认"仰卧时最低行由谁接管"，据此定 `butt_contact_ok`
的载体对象集合。**只读**，不改任何落盘文件。
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import anim_lib as A

SEAM_ACTION = os.environ.get("D15_SEAM_ACTION", "Air_Hit")
SEAM_FRAME = int(os.environ.get("D15_SEAM_FRAME", "18"))


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene

    names = sorted(o.name for o in bpy.data.objects if o.type == "MESH")
    print("D15_OBJ_NAMES " + json.dumps(names, ensure_ascii=False))

    action = bpy.data.actions.get(SEAM_ACTION)
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(SEAM_FRAME)
    bpy.context.view_layer.update()
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
        zz = [(mw @ v.co).z for v in me.vertices]
        yy = [(mw @ v.co).y for v in me.vertices]
        rows.append((min(zz) * 1000.0, min(yy) * 1000.0, max(yy) * 1000.0,
                     obj.name))
        ev.to_mesh_clear()
    rows.sort()
    print("D15_OBJ_LOW " + json.dumps(
        [{"z_mm": round(z, 1), "y_min_mm": round(a, 1), "y_max_mm": round(b, 1),
          "obj": n} for z, a, b, n in rows], ensure_ascii=False))

    for bone in ("pelvis", "thigh.L", "thigh.R", "chest", "head"):
        h = Vector(A.bone_world(arm, bone, "head"))
        t = Vector(A.bone_world(arm, bone, "tail"))
        print("D15_BONE %s head=%s tail=%s" % (
            bone,
            [round(v * 1000.0, 1) for v in h],
            [round(v * 1000.0, 1) for v in t]))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D15_OBJ_FAILURE " + traceback.format_exc())
