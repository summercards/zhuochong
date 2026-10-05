"""E04 逐帧诊断：手骨朝向 / 肘连续性 / 定格窗口。
用法：SKIP_RENDER=1 blender --background --factory-startup --python _e04_diag.py
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SKIP_RENDER", "1")

import bpy                                    # noqa: E402
from mathutils import Vector, Matrix          # noqa: E402

import anim_spawn as S                        # noqa: E402
import anim_lib as A                          # noqa: E402

RANGES = []
for spec in ("50:70", "84:106"):
    a, b = spec.split(":")
    RANGES.append((int(a), int(b)))

arm, meshes = S.boot()
posemat = {}
for frame in range(S.START, S.END + 1):
    p = S.spawn_pose(arm, frame)
    A.apply_pose(arm, p)
    snap = {}
    for side in S.SIDES:
        for bone in ("upperarm." + side, "forearm." + side, "hand." + side,
                     "thumb_01." + side):
            pb = arm.pose.bones[bone]
            snap[bone] = (Vector(pb.matrix.translation).copy(),
                          pb.matrix.to_3x3().copy(),
                          tuple(math.degrees(v) for v in pb.rotation_euler))
    posemat[frame] = snap

print("=== E04 诊断 ===")
BONES = ["hand.L", "hand.R", "forearm.L", "forearm.R"]
for lo, hi in RANGES:
    print("---- frames %d..%d ----" % (lo, hi))
    prev = None
    for frame in range(lo, hi + 1):
        row = []
        for bone in BONES:
            t, m, e = posemat[frame][bone]
            x = m.col[0].normalized()
            y = m.col[1].normalized()
            row.append("%s x=(%+.3f,%+.3f,%+.3f) y=(%+.3f,%+.3f,%+.3f)"
                       % (bone, x.x, x.y, x.z, y.x, y.y, y.z))
        step = 0.0
        at = None
        if prev is not None:
            for bone in posemat[frame]:
                a3, b3 = prev[bone][1], posemat[frame][bone][1]
                for c in range(3):
                    va = a3.col[c].normalized()
                    vb = b3.col[c].normalized()
                    d = math.degrees(math.acos(max(-1.0, min(1.0,
                                                              va.dot(vb)))))
                    if d > step:
                        step, at = d, bone
        print("f=%3d step=%7.3f @%-14s | %s" % (frame, step, str(at),
                                                " | ".join(row)))
        prev = posemat[frame]

# 逐帧 hand.L / hand.R 的 euler 步长（口径与门禁一致）
print("=== euler 步长（hand / thumb）===")
for frame in range(S.START + 1, S.END + 1):
    worst = 0.0
    at = None
    for bone in posemat[frame]:
        ea = posemat[frame - 1][bone][2]
        eb = posemat[frame][bone][2]
        d = max(abs(x - y) for x, y in zip(ea, eb))
        if d > worst:
            worst, at = d, bone
    if worst > 3.0:
        print("f=%3d euler_step=%7.3f @%s" % (frame, worst, at))

print("MIN_HINT_MARGIN=%.4f" % S.MIN_HINT_MARGIN)
