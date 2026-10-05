"""E07 诊断探针 v3：剩余两红（矩阵步长 / 收招穿模）的现场读数。"""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import anim_victory_02 as V2  # noqa: E402
import anim_lib as A  # noqa: E402
from mathutils import Vector  # noqa: E402

arm, meshes = V2.boot()

print("=" * 72)
print("E07_DIAG3 A. hand.R / forearm.R 逐帧（找 f12 与 f100）")
poses = {}
prev = {}
for f in range(V2.START, V2.END + 1):
    V2.MIN_HINT_MARGIN = 1.0
    poses[f] = V2.victory_pose(arm, f)
    h = poses[f]["hand.R"]
    fo = poses[f]["forearm.R"]
    up = poses[f]["upperarm.R"]
    print("  f=%3d env=%.3f margin=%.4f  up.R=%s fo.R=%s hd.R=%s"
          % (f, V2.arm_env(f), V2.MIN_HINT_MARGIN,
             tuple(round(v, 1) for v in up), tuple(round(v, 1) for v in fo),
             tuple(round(v, 1) for v in h)))

print("=" * 72)
print("E07_DIAG3 B. 收招段 R 臂目标 / 拳心 / 手网格（f96..f112）")
V2.torso_bvh_reset()
for f in range(96, 113):
    p = poses[f]
    dy, dz = p.get("@loc", {}).get("pelvis", (0, 0, 0))[1:3]
    root_off = Vector((0.0, dy, dz))
    A.apply_pose(arm, p)
    home = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in V2.SIDES}
    tgt = V2.fist_targets(arm, f, root_off, V2.arm_env(f), home)
    A.apply_pose(arm, p)
    core = Vector(A.bone_world(arm, "hand.R", "tail"))
    A.torso_bvh_reset()
    tree = V2.torso_bvh()
    st = V2.hand_mesh_stats("R", tree=tree, step=4, limit_mm=V2.HAND_PIERCE_MM)
    print("  f=%3d env=%.3f | tgtR=[%7.1f,%7.1f,%7.1f] gap=%7.1f"
          " | core=[%7.1f,%7.1f,%7.1f] gap=%7.1f | nothumb=%3d deep=%7.2f beyond=%3d"
          % (f, V2.arm_env(f), tgt.x * 1000, tgt.y * 1000, tgt.z * 1000,
             V2.signed_to_torso(tgt),
             core.x * 1000, core.y * 1000, core.z * 1000,
             V2.signed_to_torso(core),
             st["inside_nothumb"], st["deepest_nothumb_mm"],
             st["beyond_limit"]))

print("=" * 72)
print("E07_DIAG3 C. 站架拳心与拳面余量")
A.apply_pose(arm, poses[0])
for s in V2.SIDES:
    c = Vector(A.bone_world(arm, "hand." + s, "tail"))
    print("  station %s core=[%7.1f,%7.1f,%7.1f] gap=%7.1f face_gap=%7.2f"
          % (s, c.x * 1000, c.y * 1000, c.z * 1000, V2.signed_to_torso(c),
             V2.fist_face_gap(s, step=2)))
print("E07_DIAG3 DONE")
