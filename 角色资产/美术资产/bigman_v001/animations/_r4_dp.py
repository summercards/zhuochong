import math, json
from mathutils import Euler, Matrix

def cands(m):
    y = math.asin(max(-1.0, min(1.0, -m[2][0])))
    cy = math.cos(y)
    if abs(cy) > 1e-6:
        x = math.atan2(m[2][1], m[2][2]); z = math.atan2(m[1][0], m[0][0])
    else:
        x = 0.0; z = math.atan2(-m[0][1], m[1][1])
    return ((x, y, z), (x + math.pi, math.pi - y, z + math.pi))

def unwrap(v, ref):
    v = list(v)
    for i in range(3):
        while v[i] - ref[i] > 180.0: v[i] -= 360.0
        while v[i] - ref[i] < -180.0: v[i] += 360.0
    return v

E = {0:(45.09,-68.16,-1.00),1:(61.31,-74.62,12.16),2:(45.74,-81.99,48.62),
     3:(-3.41,-19.52,112.89),4:(-9.73,-3.84,128.75),5:(-11.83,-2.69,130.54),
     6:(-14.74,0.01,131.35),7:(-17.21,0.61,131.56),8:(-19.45,0.38,130.74),
     9:(-19.21,-3.59,126.69)}
FR = sorted(E)
R = {f: Euler([math.radians(v) for v in E[f]], "XYZ").to_matrix() for f in FR}
ROT = {p: Matrix.Rotation(math.radians(p), 3, "Y") for p in range(0,360)}

def states(f):
    out = []
    for p in range(0, 360, 1):
        if f == 0 and p != 0:
            continue
        m = R[f] @ ROT[p]
        for bi, c in enumerate(cands(m)):
            v = [math.degrees(t) for t in c]
            out.append((p, bi, v))
    return out

def run(mode):
    # DP: minimise max step along path; states (phi, branch)
    paths = {f: states(f) for f in FR}
    # dp[f] = list of (maxstep_so_far, value)  index aligned to paths[f]
    INF = 1e9
    prev = [(0.0, x[2]) for x in paths[FR[0]]]
    for i in range(1, len(FR)):
        f = FR[i]
        cur = []
        for (p, bi, v) in paths[f]:
            best = INF; bestv = None
            for j, (ms, pv) in enumerate(prev):
                w = unwrap(v, pv)
                st = max(abs(a - b) for a, b in zip(w, pv))
                if mode == "minimax":
                    c = max(ms, st)
                else:
                    c = ms + st
                if c < best:
                    best = c; bestv = w
            cur.append((best, bestv))
        prev = cur
    # recover
    best = min(range(len(prev)), key=lambda k: prev[k][0])
    print("mode=%s  best=%s" % (mode, round(prev[best][0], 2)))
    return best, paths, prev

# forward reconstruction
def reconstruct(mode):
    paths = {f: states(f) for f in FR}
    INF = 1e9
    dp = [ [(0.0, x[2], None) for x in paths[FR[0]]] ]
    for i in range(1, len(FR)):
        f = FR[i]
        row = []
        for (p, bi, v) in paths[f]:
            best = INF; bestj = -1; bestv = None
            for j, (ms, pv, bp) in enumerate(dp[-1]):
                w = unwrap(v, pv)
                st = max(abs(a - b) for a, b in zip(w, pv))
                c = max(ms, st) if mode == "minimax" else ms + st + 0.02*max(0.0, abs(w[1])-60.0)
                if c < best:
                    best = c; bestj = j; bestv = w
            row.append((best, bestv, bestj))
        dp.append(row)
    k = min(range(len(dp[-1])), key=lambda j: dp[-1][j][0])
    seq = []
    for i in range(len(FR)-1, -1, -1):
        ms, v, j = dp[i][k]
        seq.append((FR[i], paths[FR[i]][k][0], round(ms,2), [round(q,2) for q in v], j))
        k = j if (j is not None and j >= 0) else 0
    seq.reverse()
    print("== %s ==" % mode)
    for f, p, ms, v, j in seq:
        print("  f%-2d phi=%-4d maxstep=%-7.2f eul=%s" % (f, p, ms, v))
    return seq

reconstruct("minimax")
reconstruct("sum")
