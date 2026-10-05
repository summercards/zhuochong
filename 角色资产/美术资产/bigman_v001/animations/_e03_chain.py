import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import anim_rage as R
import anim_lib as A

arm, meshes = R.boot()
pb = arm.pose.bones["hand.L"]
print("hand.L parent =", pb.parent.name if pb.parent else None,
      "connect =", pb.bone.use_connect)
print("forearm.L parent =", arm.pose.bones["forearm.L"].parent.name)
print("twist env =", R.FOREARM_TWIST_DEG)
for f in (22, 23, 26, 28, 76):
    pose = R.rage_pose(arm, f)
    print("f=%d fo=%s hd=%s" % (
        f,
        ["%.1f" % v for v in pose["forearm.L"]],
        ["%.1f" % v for v in pose["hand.L"]]))
    print("      hand.L world cols: x=%s y=%s" % (
        ["%.3f" % v for v in arm.pose.bones["hand.L"].matrix.to_3x3().col[0]],
        ["%.3f" % v for v in arm.pose.bones["hand.L"].matrix.to_3x3().col[1]]))
