"""E09 逐件剖面 dump（诊断用，不是生产件）。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python _dump_e09_prof.py

复用 `anim_defeat.dft_pose`（纯函数）逐帧重建姿态，打印**每件网格对象**的世界最低 z，
以及膝 / 踝 / 脚尖 pivot 的世界坐标。目的是回答"到底是哪个件、沉了多少"。
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

FRAMES = [int(x) for x in os.environ.get(
    "PROF_FRAMES", "0,10,20,28,32,40,46,56,66,70,90,120").split(",")]

arm, meshes = D.boot()
print("E09_DUMP_ANCHORS " + json.dumps(
    {s: {"ankle": [round(v * 1000.0, 2) for v in
                   A.bone_world(arm, "foot." + s, "head")],
         "toe_head": [round(v * 1000.0, 2) for v in
                      A.bone_world(arm, "toe." + s, "head")],
         "toe_tail": [round(v * 1000.0, 2) for v in
                      A.bone_world(arm, "toe." + s, "tail")],
         "knee": [round(v * 1000.0, 2) for v in
                  A.bone_world(arm, "shin." + s, "head")],
         } for s in D.SIDES}, ensure_ascii=False))

for frame in FRAMES:
    A.apply_pose(arm, D.dft_pose(arm, frame))
    prof = D.body_low_profile()
    lowest = sorted(prof.items(), key=lambda kv: kv[1])[:8]
    pos = {}
    for s in D.SIDES:
        pos[s] = {
            "hip": [round(v * 1000.0, 1) for v in
                    A.bone_world(arm, "thigh." + s, "head")],
            "knee": [round(v * 1000.0, 1) for v in
                     A.bone_world(arm, "shin." + s, "head")],
            "ankle": [round(v * 1000.0, 1) for v in
                      A.bone_world(arm, "foot." + s, "head")],
            "toe": [round(v * 1000.0, 1) for v in
                    A.bone_world(arm, "toe." + s, "tail")],
        }
    print("E09_DUMP f=%3d low=%.2f(%s) top8=%s pos=%s" % (
        frame, min(prof.values()), min(prof.items(), key=lambda kv: kv[1])[0],
        [(k, round(v, 1)) for k, v in lowest], json.dumps(pos)))

print("E09_DUMP_DONE")
