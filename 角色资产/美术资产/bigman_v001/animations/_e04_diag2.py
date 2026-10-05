"""E04 诊断 2：拳目标 / 肘 / 肩 逐帧（定位摆臂回程的异常）。"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SKIP_RENDER", "1")

import bpy                                    # noqa: E402
from mathutils import Vector                  # noqa: E402

import anim_spawn as S                        # noqa: E402
import anim_lib as A                          # noqa: E402

arm, meshes = S.boot()

print("STATION_FIST L=%s R=%s" % (S.STATION_FIST["L"][:], S.STATION_FIST["R"][:]))
print("FIST_OUT   L=%s" % (S.FIST_OUT["L"][:],))
print("FIST_OUT2  L=%s" % (S.FIST_OUT2["L"][:],))
print("FIST_UP    L=%s" % (S.FIST_UP["L"][:],))
print("STATION_HAND_Y L=%s R=%s" % (S.STATION_HAND_Y["L"][:],
                                     S.STATION_HAND_Y["R"][:]))

print("frame | tgt.L | elbow.L | sh.L | fore.L | tgt.R | elbow.R | sh.R | fore.R")
for frame in range(0, S.END + 1):
    if not (frame % 2 == 0):
        continue
    S.spawn_pose(arm, frame)
    if not ((40 <= frame <= 80) or (84 <= frame <= 112)):
        continue
    row = []
    for side in S.SIDES:
        sho = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elb = Vector(A.bone_world(arm, "forearm." + side, "head"))
        dy, dz = S.torso_at(frame)["loc"]
        tgt = Vector(S.fist_targets(arm, frame, Vector((0.0, dy, dz)))[side])
        fore = (tgt - elb)
        fore = fore.normalized() if fore.length > 1e-6 else Vector()
        row.append("t(%+.3f,%+.3f,%+.3f) e(%+.3f,%+.3f,%+.3f) f(%+.2f,%+.2f,%+.2f)"
                   % (tgt.x, tgt.y, tgt.z, elb.x, elb.y, elb.z,
                      fore.x, fore.y, fore.z))
    print("f=%3d | %s | %s" % (frame, row[0], row[1]))
