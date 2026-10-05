"""临时：列出网格对象名 + 包围盒 + 现有 Action 数 / 名字（只读）。"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

arm, meshes = A.open_animation_project()
print("ACTIONS n=%d" % len(bpy.data.actions))
print("ACTION_NAMES " + repr(sorted(a.name for a in bpy.data.actions)))
print("MESH_COUNT %d" % len(meshes))
for obj in sorted(meshes, key=lambda o: o.name):
    bb = [obj.matrix_world @ __import__("mathutils").Vector(c) for c in obj.bound_box]
    xs = [p.x for p in bb]
    ys = [p.y for p in bb]
    zs = [p.z for p in bb]
    print("MESH %-28s x[%7.3f,%7.3f] y[%7.3f,%7.3f] z[%7.3f,%7.3f]"
          % (obj.name, min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
