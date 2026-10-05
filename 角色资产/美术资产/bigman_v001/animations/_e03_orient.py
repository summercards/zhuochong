import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import anim_rage as R
import anim_lib as A

arm, meshes = R.boot()
prev = None
print("blend  yaw_dir(L)                     along                  -nrm   |raw|  ang(raw,carry)  mstep")
for f in range(68, 86):
    R.rage_pose(arm, f)
    hb = arm.pose.bones["hand.L"].matrix.to_3x3().normalized()
    y = hb.col[1].normalized()
    hint = R.hand_x_hint("L", Vector((0.0, 0.0, 0.0))).normalized()
    raw = hint - y * hint.dot(y)
    b = R.face_blend(f)
    if prev is not None:
        q = (prev.transposed() @ hb).to_quaternion()
        mstep = math.degrees(abs(q.angle))
    else:
        mstep = 0.0
    prev = hb
    print("f=%3d b=%.3f y=(%6.3f,%6.3f,%6.3f) |raw|=%.3f  mstep=%.2f" % (
        f, b, y.x, y.y, y.z, raw.length, mstep))
