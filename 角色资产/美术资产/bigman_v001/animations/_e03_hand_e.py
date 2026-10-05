import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import anim_rage as R
import anim_lib as A
arm, meshes = R.boot()
kf = [(f, R.rage_pose(arm, f)) for f in range(R.START, R.END + 1)]
kf = R.compat_euler(kf); kf = R.seam_canonicalize(kf)
act, _m = A.build_action(arm, R.NAME, kf, {"anim_id": R.NAME, "loop": False,
                                           "category": "t", "frames": [0, R.TOTAL]})
A.sample_animation(arm, act, R.START, R.END)
prev = None
hot = []
for f in range(R.START, R.END + 1):
    bpy.context.scene.frame_set(f); bpy.context.view_layer.update()
    e = [math.degrees(v) for v in arm.pose.bones["hand.L"].rotation_euler]
    if prev is not None:
        s = max(min(abs(a-b) % 360, 360-abs(a-b) % 360) for a, b in zip(e, prev))
        hot.append((s, f))
    prev = e
hot.sort(reverse=True)
print("hand.L euler 步最大的 8 帧：", [(round(s,1), f) for s, f in hot[:8]])
for f in (16, 17, 18, 19, 20, 40, 44, 70, 74, 76):
    bpy.context.scene.frame_set(f); bpy.context.view_layer.update()
    e = [math.degrees(v) for v in arm.pose.bones["hand.L"].rotation_euler]
    print("f=%3d hand.L euler=[%8.1f %8.1f %8.1f]" % (f, e[0], e[1], e[2]))
