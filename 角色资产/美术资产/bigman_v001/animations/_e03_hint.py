import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import anim_rage as R
import anim_lib as A

arm, meshes = R.boot()
ys = {"L": [], "R": []}
for f in range(R.START, R.END + 1):
    R.rage_pose(arm, f)
    for s in ("L", "R"):
        ys[s].append(arm.pose.bones["hand." + s].matrix.to_3x3().col[1].normalized())
print("== 实际 y_dir 分布（每侧 97 帧）==")
worst_all = []
for s in ("L", "R"):
    zs = [y.z for y in ys[s]]
    print("  %s  y.z 范围 [%.3f, %.3f]" % (s, min(zs), max(zs)))
print()
print("== 基准 = normalize((0, -t, -1)) 的余量扫描：min|raw| = min sin(角) ==")
for t in [0.0, 0.2, 0.35, 0.5, 0.6, 0.75, 0.9, 1.1]:
    hint = Vector((0.0, -t, -1.0)).normalized()
    worst, wf, ws = 1.0, -1, ""
    for s in ("L", "R"):
        for i, y in enumerate(ys[s]):
            raw = hint - y * hint.dot(y)
            if raw.length < worst:
                worst, wf, ws = raw.length, R.START + i, s
    print("  t=%.2f  min|raw|=%.3f (角 %.1f°) @ f=%d %s" % (
        t, worst, math.degrees(math.asin(min(1.0, worst))), wf, ws))
