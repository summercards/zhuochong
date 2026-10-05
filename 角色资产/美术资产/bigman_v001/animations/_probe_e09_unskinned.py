"""E09 目检辅助：列出**未蒙皮 / 不跟随骨架**的网格对象（诊断用，不是生产件）。

为什么需要：3/4 视图 f66 里有一根蓝色横条**浮在半空**。先用几何确认它是不是
登记过的 `Jacket_Hem` / `Jacket_Hem_Line` 遗留（`parent=None` / `vgroups=0`
⟹ 逐帧恒定），而不是本支新引入的穿帮。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _probe_e09_unskinned.py
"""
import json
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A          # noqa: E402
import anim_defeat as D       # noqa: E402

arm, meshes = D.boot()
action = bpy.data.actions.get("Defeat")
if action is not None:
    arm.animation_data.action = action
    A._bind_slot(arm, action)

FEET = {}
for fr in (0, 66, 120):
    bpy.context.scene.frame_set(fr)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        ev = obj.evaluated_get(depsgraph)
        mesh = ev.to_mesh()
        m = ev.matrix_world
        lo = min((m @ v.co).z for v in mesh.vertices) * 1000.0
        hi = max((m @ v.co).z for v in mesh.vertices) * 1000.0
        ev.to_mesh_clear()
        FEET.setdefault(obj.name, {})[fr] = (round(lo, 2), round(hi, 2))

for name in sorted(FEET):
    obj = bpy.data.objects[name]
    vg = len(obj.vertex_groups)
    par = obj.parent.name if obj.parent else None
    boxes = FEET[name]
    const = len(set(boxes.values())) == 1
    if vg == 0 or par is None or const:
        print("E09_UNSKIN " + json.dumps({
            "obj": name, "vgroups": vg, "parent": par,
            "armature_mod": [m.type for m in obj.modifiers],
            "bbox_z_mm": {str(k): v for k, v in boxes.items()},
            "constant": const}))
print("E09_UNSKIN_DONE")
