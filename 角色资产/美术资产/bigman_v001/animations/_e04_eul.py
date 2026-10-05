import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import anim_lib as A
import anim_spawn as S

F0 = int(os.environ.get("F0", "50")); F1 = int(os.environ.get("F1", "66"))
NAMES = os.environ.get("NAMES", "forearm.L,upperarm.L,hand.L").split(",")

arm, meshes = S.boot()
kfs = [(f, S.spawn_pose(arm, f)) for f in range(S.START, S.END + 1)]
kfs = S.compat_euler(kfs)
kfs = S.seam_canonicalize(kfs)
action, meta = A.build_action(arm, S.NAME + "_EUL", kfs, meta={"anim_id": S.NAME, "loop": False})
prev = {}
for f in range(F0, F1 + 1):
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    out = []
    for n in NAMES:
        e = arm.pose.bones[n].rotation_euler
        v = (math.degrees(e.x), math.degrees(e.y), math.degrees(e.z))
        d = 0.0
        if n in prev:
            d = max(abs(a - b) for a, b in zip(v, prev[n]))
        prev[n] = v
        out.append("%-11s(%7.1f,%7.1f,%7.1f) d=%5.1f" % (n, v[0], v[1], v[2], d))
    print("f=%3d  %s" % (f, " | ".join(out)))
