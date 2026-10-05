import math
from mathutils import Euler, Matrix, Vector

def cands(m):
    y = math.asin(max(-1.0, min(1.0, -m[2][0])))
    cy = math.cos(y)
    if abs(cy) > 1e-6:
        x = math.atan2(m[2][1], m[2][2]); z = math.atan2(m[1][0], m[0][0])
    else:
        x = 0.0; z = math.atan2(-m[0][1], m[1][1])
    return ((x, y, z), (x + math.pi, math.pi - y, z + math.pi))

def unwrap(val, ref):
    v = list(val)
    for i in range(3):
        while v[i] - ref[i] > 180.0: v[i] -= 360.0
        while v[i] - ref[i] < -180.0: v[i] += 360.0
    return v

def show(tag, m, ref):
    best = None
    for c in cands(m):
        v = unwrap([math.degrees(t) for t in c], ref)
        cost = max(abs(a - b) for a, b in zip(v, ref))
        if best is None or cost < best[0]: best = (cost, v)
    print("%s minstep=%.2f eul=%s" % (tag, best[0], [round(q,2) for q in best[1]]))

E2 = (45.74, -81.99, 48.62)
E3 = (-3.41, -19.52, 112.89)
E1 = (61.31, -74.62, 12.16)
R2 = Euler([math.radians(v) for v in E2], "XYZ").to_matrix()
R3 = Euler([math.radians(v) for v in E3], "XYZ").to_matrix()

print("--- f2 basis, sweep roll phi (deg) ---")
bestyr = []
for phi in range(0, 360, 5):
    rr = Matrix.Rotation(math.radians(phi), 3, "Y")
    m = R2 @ rr
    # min |ry| over branches
    mg = None
    for c in cands(m):
        yy = abs(math.degrees(c[1]))
        if mg is None or yy < mg: mg = yy
    bestyr.append((mg, phi))
bestyr.sort()
print("lowest |ry| at f2:", [(round(a,1), b) for a, b in bestyr[:6]])
print("at phi=0 |ry|=%.1f" % [math.degrees(c[1]) for c in cands(R2)][0])
show("f2->f1 step with phi grid:", R2, E1)
for phi in (0, 10, 20, 30, 40, 50, 60, 90):
    rr = Matrix.Rotation(math.radians(phi), 3, "Y")
    show("  phi=%3d f2:" % phi, R2 @ rr, E1)
print()
print("--- f3 ---")
for phi in (0, 10, 20, 30, 40, 50, 60, 90):
    rr = Matrix.Rotation(math.radians(phi), 3, "Y")
    show("  phi=%3d f3:" % phi, R3 @ rr, E2)
