"""E04 诊断 4：起手臂段（f=0..24）—— 拳目标 / 肘 / 手网格体内计数。"""
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

# 躯干包围盒
import mathutils.bvhtree as bvhtree           # noqa: E402
deps = bpy.context.evaluated_depsgraph_get()
tree = bvhtree.BVHTree.FromObject(S.TORSO, deps)
bb = []
for i in range(0, len(S.TORSO.evaluated_get(deps).to_mesh().vertices), 7):
    bb.append(S.TORSO.evaluated_get(deps).matrix_world
              @ S.TORSO.evaluated_get(deps).to_mesh().vertices[i].co)
print("TORSO bbox x=[%.3f,%.3f] y=[%.3f,%.3f] z=[%.3f,%.3f]"
      % (min(p.x for p in bb), max(p.x for p in bb),
         min(p.y for p in bb), max(p.y for p in bb),
         min(p.z for p in bb), max(p.z for p in bb)))
print("STATION_FIST L=%s" % (tuple(round(v, 3) for v in S.STATION_FIST["L"]),))

prev = None
for frame in range(0, 25):
    p = S.spawn_pose(arm, frame)
    A.apply_pose(arm, p)
    S.torso_bvh_reset()
    tr = S.torso_bvh()
    row = []
    for side in S.SIDES:
        sho = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elb = Vector(A.bone_world(arm, "forearm." + side, "head"))
        fist = Vector(A.bone_world(arm, "hand." + side, "tail"))
        dy, dz = S.torso_at(frame)["loc"]
        tgt = Vector(S.fist_targets(arm, frame, Vector((0.0, dy, dz)))[side])
        st = S.hand_mesh_stats(side, tree=tr, step=4)
        row.append("tgt(%+.3f,%+.3f,%+.3f) elb(%+.3f,%+.3f,%+.3f) "
                   "fist(%+.3f,%+.3f,%+.3f) in=%d/%d deep=%.1f"
                   % (tgt.x, tgt.y, tgt.z, elb.x, elb.y, elb.z,
                      fist.x, fist.y, fist.z, st["inside_nothumb"],
                      st["inside"], st["deepest_nothumb_mm"] or 0.0))
    step = 0.0
    at = None
    if prev is not None:
        for bone in p:
            if bone.startswith("@") or bone not in arm.pose.bones:
                continue
            a3 = arm.pose.bones[bone].matrix.to_3x3()
            b3 = prev[bone]
            for c in range(3):
                va = a3.col[c].normalized()
                vb = b3.col[c].normalized()
                dd = math.degrees(math.acos(max(-1.0, min(1.0, va.dot(vb)))))
                if dd > step:
                    step, at = dd, bone
    print("f=%2d step=%7.2f @%-12s | %s | %s"
          % (frame, step, str(at), row[0], row[1]))
    prev = {b: arm.pose.bones[b].matrix.to_3x3().copy()
            for b in p if not b.startswith("@") and b in arm.pose.bones}
