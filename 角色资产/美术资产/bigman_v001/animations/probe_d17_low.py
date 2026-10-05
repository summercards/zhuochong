"""probe_d16_low —— 逐帧「谁是最低行」+ 网格绑定体检（只读）。"""

import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402


def obj_rows():
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
        rows.append((min((mw @ v.co).z for v in me.vertices) * 1000.0, obj.name))
        ev.to_mesh_clear()
    rows.sort()
    return [{"z_mm": round(z, 2), "obj": n} for z, n in rows[:8]]


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    action = bpy.data.actions["GetUp_F"]
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    out = {}
    for f in (0, 4, 6, 9, 10, 14, 18, 20, 24, 30, 34, 36):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        out[str(f)] = obj_rows()
    bind = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        mods = [m.type for m in obj.modifiers]
        bind[obj.name] = {
            "parent": (obj.parent.name if obj.parent else None),
            "vgroups": len(obj.vertex_groups),
            "mods": mods,
        }
    A.report("D17_LOW", {"frames": out, "bind": bind})


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D17_LOW_FAILURE " + traceback.format_exc())
