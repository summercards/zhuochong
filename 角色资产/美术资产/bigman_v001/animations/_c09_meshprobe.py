"""列出 bigman_anim_v001 里所有网格对象名 + 各自的顶点数，用于定位"头"网格。"""
import os, sys
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa
arm, meshes = A.open_animation_project()
names = sorted(o.name for o in bpy.data.objects if o.type == "MESH")
print("C09MP_COUNT %d" % len(names))
print("C09MP_NAMES " + repr(names))
