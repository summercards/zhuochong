"""C04 诊断：逐帧列出收招段（f24~f54）的"最大动骨"与肩位。

只读，不改任何东西。用法：
    "D:/.../blender.exe" --background --factory-startup --python _c04_tail_dump.py
"""
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

arm, meshes = A.open_animation_project()
act = bpy.data.actions.get("Grab_Start")
if act is None:
    raise SystemExit("Grab_Start 不存在")

root = A.bone_world(arm, "pelvis", "head")
samples = A.sample_animation(arm, act, 24, 54, meshes)

prev_euler = None
prev_shoulder = None
for s in samples:
    e = s["euler"]
    if prev_euler is not None:
        movers = []
        for name in set(e) | set(prev_euler):
            a = prev_euler.get(name, (0.0, 0.0, 0.0))
            b = e.get(name, (0.0, 0.0, 0.0))
            d = max(abs(x - y) for x, y in zip(a, b))
            if d > 0.2:
                movers.append((round(d, 3), name,
                               [round(v, 2) for v in b]))
        movers.sort(reverse=True)
        bpy.context.scene.frame_set(s["frame"])
        bpy.context.view_layer.update()
        sh = [round((v - o) * 1000.0, 2) for v, o in
              zip(A.bone_world(arm, "upperarm.L", "head"), root)]
        dsh = (None if prev_shoulder is None
               else round(sum((a - b) ** 2 for a, b in
                              zip(sh, prev_shoulder)) ** 0.5, 2))
        print("C04_D f=%d shr=%s d_shr=%s top=%s"
              % (s["frame"], sh, dsh, movers[:4]))
        prev_shoulder = sh
    prev_euler = e
