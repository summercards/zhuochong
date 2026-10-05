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

CAND = {
    "down(0,0,-1)":        Vector((0.0, 0.0, -1.0)),
    "up(0,0,1)":           Vector((0.0, 0.0, 1.0)),
    "X+(1,0,0)":           Vector((1.0, 0.0, 0.0)),
    "X-(-1,0,0)":          Vector((-1.0, 0.0, 0.0)),
    "fwd(0,-1,0)":         Vector((0.0, -1.0, 0.0)),
    "back(0,1,0)":         Vector((0.0, 1.0, 0.0)),
    "out+X+dn(1,0,-1)":    Vector((1.0, 0.0, -1.0)),
    "in-X+dn(-1,0,-1)":    Vector((-1.0, 0.0, -1.0)),
    "out+X+fwd(1,-1,0)":   Vector((1.0, -1.0, 0.0)),
    "out+X(0.6,0,-1)+":    Vector((0.9, 0.0, -1.0)),
}
print("== 候选基准的安全余量（两侧取最差）==")
rows = []
for name, h in CAND.items():
    worst, wf, ws = 1.0, -1, ""
    for s in ("L", "R"):
        hh = h.normalized() * R.HAND_CHIRALITY[s]
        for i, y in enumerate(ys[s]):
            raw = hh - y * hh.dot(y)
            if raw.length < worst:
                worst, wf, ws = raw.length, R.START + i, s
    rows.append((worst, name, wf, ws))
for worst, name, wf, ws in sorted(rows, reverse=True):
    print("  %-20s min|raw|=%.3f (角 %5.1f°) @ f=%d %s" % (
        name, worst, math.degrees(math.asin(min(1.0, worst))), wf, ws))

# 胸腔法线：逐帧变，单独看
worst = 1.0
for s in ("L", "R"):
    for i in range(R.START, R.END + 1):
        pass
print()
print("== 胸腔法线基准（逐帧法线，独立量）==")
alln = []
for f in range(R.START, R.END + 1):
    R.rage_pose(arm, f)
    for s in ("L", "R"):
        alln.append((s, f, R.chest_surface(arm, s)[1]))
for s in ("L", "R"):
    worst, wf = 1.0, -1
    for ss, f, n in alln:
        if ss != s:
            continue
        y = ys[s][f - R.START]
        hh = n.normalized() * R.HAND_CHIRALITY[s]
        raw = hh - y * hh.dot(y)
        if raw.length < worst:
            worst, wf = raw.length, f
    print("  %s  nrm基准 min|raw|=%.3f (角 %.1f°) @ f=%d" % (
        s, worst, math.degrees(math.asin(min(1.0, worst))), wf))
