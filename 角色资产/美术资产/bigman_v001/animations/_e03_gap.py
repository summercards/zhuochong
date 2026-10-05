import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Matrix, Vector, Euler
import anim_rage as R
import anim_lib as A

arm, meshes = R.boot()
kf = [(f, R.rage_pose(arm, f)) for f in range(R.START, R.END + 1)]
kf = R.compat_euler(kf)
act, _m = A.build_action(arm, R.NAME, kf, {"anim_id": R.NAME, "loop": False,
                                           "category": "t", "frames": [0, R.TOTAL]})
A.sample_animation(arm, act, R.START, R.END)


def cands(t):
    flip = (t[0] + 180.0, 180.0 - t[1], t[2] + 180.0)
    out = []
    for base in (t, flip):
        for kx in (-1, 0, 1):
            for ky in (-1, 0, 1):
                for kz in (-1, 0, 1):
                    out.append((base[0] + 360 * kx, base[1] + 360 * ky,
                                base[2] + 360 * kz))
    return out


def mat_step(bone, f0, f1):
    bpy.context.scene.frame_set(f0)
    bpy.context.view_layer.update()
    m0 = arm.pose.bones[bone].matrix.to_3x3().normalized()
    bpy.context.scene.frame_set(f1)
    bpy.context.view_layer.update()
    m1 = arm.pose.bones[bone].matrix.to_3x3().normalized()
    return math.degrees(abs((m0.transposed() @ m1).to_quaternion().angle))


print("f0->f1 bone        keyed_e_step  brute_min_step  matrix_step")
for f0 in (17, 18, 19, 69, 75):
    f1 = f0 + 1
    for bone in ("hand.L", "hand.R", "forearm.L", "forearm.R"):
        bpy.context.scene.frame_set(f0)
        bpy.context.view_layer.update()
        e0 = [math.degrees(v) for v in arm.pose.bones[bone].rotation_euler]
        bpy.context.scene.frame_set(f1)
        bpy.context.view_layer.update()
        e1 = [math.degrees(v) for v in arm.pose.bones[bone].rotation_euler]
        keyed = max(min(abs(a - b) % 360.0, 360.0 - abs(a - b) % 360.0)
                    for a, b in zip(e0, e1))
        brute = min(max(abs(a - b) for a, b in zip(e0, c))
                    for c in cands(e1))
        ms = mat_step(bone, f0, f1)
        print("%2d->%2d %-10s %10.2f %13.2f %12.2f" % (
            f0, f1, bone, keyed, brute, ms))
