import math
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

def wrap_pi(p):
    return (p + math.pi) % (2*math.pi) - math.pi

E = {0:(45.09,-68.16,-1.00),1:(61.31,-74.62,12.16),2:(45.74,-81.99,48.62),
     3:(-3.41,-19.52,112.89),4:(-9.73,-3.84,128.75),5:(-11.83,-2.69,130.54),
     6:(-14.74,0.01,131.35),7:(-17.21,0.61,131.56),8:(-19.45,0.38,130.74),
     9:(-19.21,-3.59,126.69)}
FR = sorted(E)
R = {f: Euler([math.radians(v) for v in E[f]], "XYZ").to_matrix() for f in FR}
ROT = {p: Matrix.Rotation(math.radians(p), 3, "Y") for p in FR and range(0,360)}

def greedy(lam, T, window, lookahead=0):
    prev = list(E[0])
    total, worst = 0.0, 0.0
    seq = [(0, 0.0)]
    for f in FR[1:]:
        best = None
        for p in window:
            m = R[f] @ ROT[p]
            for c in cands(m):
                v = [math.degrees(t) for t in c]
                w = unwrap(v, prev)
                step = max(abs(a-b) for a,b in zip(w, prev))
                cost = step + lam * max(0.0, abs(w[1]) - T)
                # 1-step lookahead
                if lookahead:
                    nxt = FR.index(f) + 1
                    if nxt < len(FR):
                        f2 = FR[nxt]
                        pen = 1e9
                        for p2 in window:
                            m2 = R[f2] @ ROT[p2]
                            for c2 in cands(m2):
                                v2 = [math.degrees(t) for t in c2]
                                w2 = unwrap(v2, w)
                                st2 = max(abs(a-b) for a,b in zip(w2, w))
                                c2cost = st2 + lam * max(0.0, abs(w2[1]) - T)
                                pen = min(pen, c2cost)
                        cost += 0.5 * pen
                if best is None or cost < best[0]:
                    best = (cost, p, w, step)
        _, p, w, step = best
        total += step; worst = max(worst, step)
        prev = w
        seq.append((f, p, round(step,2), [round(q,2) for q in w]))
    return worst, total, seq

full = list(range(0,360,5))
half = list(range(0,181,5))
for name, win in (("full-circle", full), ("cur[0..180]", half)):
    for lam, T in ((0.0,88.0),(1.0,70.0),(3.0,70.0),(6.0,70.0),(12.0,60.0),(30.0,50.0)):
        w,t,seq = greedy(lam,T,win)
        print("win=%-12s lam=%-5.1f T=%-5.1f  worst=%6.2f total=%7.2f  phi=%s" % (name,lam,T,w,t,[q[1] for q in seq]))
    print()
print("--- with 1-step lookahead, full circle ---")
for lam, T in ((1.0,70.0),(3.0,70.0),(6.0,70.0),(12.0,60.0)):
    w,t,seq = greedy(lam,T,full,lookahead=1)
    print("lam=%-5.1f T=%-5.1f worst=%6.2f total=%7.2f phi=%s" % (lam,T,w,t,[q[1] for q in seq]))
