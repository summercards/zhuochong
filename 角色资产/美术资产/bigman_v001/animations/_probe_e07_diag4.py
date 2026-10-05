"""E07 诊断探针 v4：矩阵口径逐帧步长 + 收招段 R 臂目标/穿模。"""
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
BONES = sorted(arm.pose.bones.keys())

poses = {}
mats = {}
for f in range(V2.START, V2.END + 1):
    poses[f] = V2.victory_pose(arm, f)
    A.apply_pose(arm, poses[f])
    mats[f] = {n: arm.pose.bones[n].matrix.to_3x3().copy() for n in BONES}

print("=" * 72)
print("E07_DIAG4 A. 矩阵口径逐帧最大步（真旋转）")
rows = []
for f in range(V2.START + 1, V2.END + 1):
    for n in BONES:
        a, b = mats[f - 1][n], mats[f][n]
        d = 0.0
        for c in range(3):
            ca = a.col[c].normalized()
            cb = b.col[c].normalized()
            d = max(d, math.degrees(math.acos(max(-1.0, min(1.0, ca.dot(cb))))))
        rows.append((d, f, n))
rows.sort(reverse=True)
for d, f, n in rows[:16]:
    print("  MAT %8.3f deg  f=%3d  %s" % (d, f, n))

print("=" * 72)
print("E07_DIAG4 B. euler 口径逐帧最大步")
rows2 = []
for f in range(V2.START + 1, V2.END + 1):
    for n in BONES:
        a = poses[f - 1].get(n, (0.0, 0.0, 0.0))
        b = poses[f].get(n, (0.0, 0.0, 0.0))
        rows2.append((max(abs(x - y) for x, y in zip(a, b)), f, n))
rows2.sort(reverse=True)
for d, f, n in rows2[:16]:
    print("  EUL %8.3f deg  f=%3d  %s" % (d, f, n))

print("=" * 72)
print("E07_DIAG4 C. 收招段 R 臂目标 / 拳心 / 手网格（f96..f112）")
for f in range(96, 113):
    p = poses[f]
    dy, dz = p.get("@loc", {}).get("pelvis", (0, 0, 0))[1:3]
    root_off = Vector((0.0, dy, dz))
    A.apply_pose(arm, p)
    home = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in V2.SIDES}
    tgt = V2.fist_targets(arm, f, root_off, V2.arm_env(f), home)["R"]
    A.apply_pose(arm, p)
    core = Vector(A.bone_world(arm, "hand.R", "tail"))
    V2.torso_bvh_reset()
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
print("E07_DIAG4 D. 站架拳心 / 拳面余量 / 手骨局部 euler")
A.apply_pose(arm, poses[0])
for s in V2.SIDES:
    c = Vector(A.bone_world(arm, "hand." + s, "tail"))
    print("  station %s core=[%7.1f,%7.1f,%7.1f] gap=%7.1f face_gap=%7.2f hd_eul=%s"
          % (s, c.x * 1000, c.y * 1000, c.z * 1000, V2.signed_to_torso(c),
             V2.fist_face_gap(s, step=2),
             tuple(round(v, 2) for v in poses[0]["hand." + s])))
print("E07_DIAG4 DONE")
