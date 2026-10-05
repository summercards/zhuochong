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
E = {
 "upperarm.L": {0:[38.52,0.71,4.69],1:[34.82,8.13,-2.88],2:[33.46,13.05,-7.78],3:[33.59,16.35,-10.44],4:[34.24,16.11,-11.55],5:[33.08,12.21,-8.51],6:[30.93,9.69,-4.5],7:[27.72,7.13,-0.61],8:[23.66,4.74,3.21],9:[21.89,3.15,5.75]},
 "forearm.L": {0:[45.09,-68.16,-1.0],1:[61.31,-74.62,12.16],2:[45.74,-81.99,48.62],3:[-3.41,-19.52,112.89],4:[-9.73,-3.84,128.75],5:[-11.83,-2.69,130.54],6:[-14.74,0.01,131.35],7:[-17.21,0.61,131.56],8:[-19.45,0.38,130.74],9:[-19.21,-3.59,126.69]},
 "hand.L": {0:[-39.47,45.51,-30.17],1:[-55.68,33.94,-47.3],2:[-62.21,22.23,-58.56],3:[-17.51,67.08,-88.41],4:[10.74,39.04,-81.54],5:[14.85,36.97,-85.78],6:[19.61,33.43,-89.49],7:[23.19,32.76,-92.23],8:[25.97,29.56,-95.15],9:[24.73,27.15,-92.8]},
}
full = list(range(0,360,5)); half = list(range(0,181,5))
for bone, tbl in E.items():
    FR = sorted(tbl); R = {f: Euler([math.radians(v) for v in tbl[f]],"XYZ").to_matrix() for f in FR}
    ROT = {p: Matrix.Rotation(math.radians(p),3,"Y") for p in full}
    for name, win in (("full", full), ("[0..180]", half)):
        prev = list(tbl[0]); worst=0.0; seq=[(0,0)]
        for f in FR[1:]:
            best=None
            for p in win:
                m = R[f] @ ROT[p]
                for c in cands(m):
                    v=[math.degrees(t) for t in c]; w=unwrap(v,prev)
                    st=max(abs(a-b) for a,b in zip(w,prev))
                    if best is None or st<best[0]: best=(st,p,w,st)
            _,p,w,st = best
            worst=max(worst,st); prev=w; seq.append((f,p,round(st,2)))
        print("%-12s win=%-9s worst=%6.2f  phi=%s" % (bone, name, worst, [q[1] for q in seq]))
    print()
