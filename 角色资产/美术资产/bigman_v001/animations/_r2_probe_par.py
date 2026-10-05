"""临时探针：查 `forearm.L` 的滚转参考是否撞上"反平行奇点"。用完即删。"""
import os
import sys
import math
import json
import bpy
from mathutils import Vector, Quaternion

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import anim_getup_b as D          # noqa: E402
import anim_lib as A              # noqa: E402

arm, meshes = D.boot()

prev_q = {}
ref_q = {}
for f in range(0, 18):
    p = D.build_pose(arm, f)
    A.apply_pose(arm, p)
    bpy.context.view_layer.update()
    q = arm.pose.bones["forearm.L"].matrix.to_3x3().to_quaternion().normalized()
    d = Vector(A.bone_direction(arm, "forearm.L")).normalized()
    z = Vector(D.ZERO_DIR["forearm.L"]).normalized()
    e = Vector(D.END_DIR["forearm.L"]).normalized()
    # 零位参考朝向：`_roll_return` 在 mix=0 时**强制**把它当作最终滚转
    ref = (z.rotation_difference(d)
           @ Quaternion(D.ZERO_BASIS["forearm.L"])).normalized()
    step = None if (f - 1) not in prev_q else round(
        math.degrees(q.rotation_difference(prev_q[f - 1]).angle), 2)
    ref_step = None if (f - 1) not in ref_q else round(
        math.degrees(ref.rotation_difference(ref_q[f - 1]).angle), 2)
    prev_q[f] = q
    ref_q[f] = ref
    print("PROBE_FA " + json.dumps({
        "f": f, "dw": step, "ref_dw": ref_step,
        "dot_zero": round(d.dot(z), 4), "dot_end": round(d.dot(e), 4),
        "mix": round(D.roll_mix_at(f, "forearm.L"), 3)}))
