import math
from mathutils import Euler, Matrix, Quaternion
def uw(v, ref):
    v=list(v)
    for i in range(3):
        while v[i]-ref[i]>180.0: v[i]-=360.0
        while v[i]-ref[i]<-180.0: v[i]+=360.0
    return v
def cands(m):
    y = math.asin(max(-1.0, min(1.0, -m[2][0])))
    cy = math.cos(y)
    if abs(cy) > 1e-6:
        x = math.atan2(m[2][1], m[2][2]); z = math.atan2(m[1][0], m[0][0])
    else:
        x = 0.0; z = math.atan2(-m[0][1], m[1][1])
    return ((x, y, z), (x + math.pi, math.pi - y, z + math.pi))
E = {19:[36.35,45.32,51.31],20:[42.45,43.98,58.84],21:[41.98,46.2,60.48],
     22:[-2.15,58.93,24.85],23:[-56.58,58.37,-10.24],24:[-56.55,58.37,-13.18],
     25:[-46.75,56.1,-14.31],26:[-51.65,51.85,-19.24]}
FR=sorted(E)
R={f: Euler([math.radians(v) for v in E[f]],"XYZ").to_matrix() for f in FR}
print("frame  real_local_rot_deg   euler_step   |ry|   best_rolled_step(full)")
G=[p for p in range(0,360,5)]
for i in range(1,len(FR)):
    f, p = FR[i], FR[i-1]
    qa = R[p].to_quaternion(); qb = R[f].to_quaternion()
    ang = math.degrees(qb.rotation_difference(qa).angle)
    if ang > 180: ang = 360-ang
    st = max(abs(a-b) for a,b in zip(E[f],E[p]))
    # best rolled step
    best=None
    for ph in G:
        m = R[f] @ Matrix.Rotation(math.radians(ph),3,"Y")
        for c in cands(m):
            v=[math.degrees(t) for t in c]; w=uw(v,E[p])
            s=max(abs(a-b) for a,b in zip(w,E[p]))
            if best is None or s<best[0]: best=(s,ph,[round(z,2) for z in w])
    print("  f%-2d  %8.2f            %7.2f    %6.2f   %6.2f phi=%-4d" % (f, ang, st, E[f][1], best[0], best[1]))
print()
print("2-step minimax check (f21..f25): can we get all <= 25 with a roll plan?")
import itertools
frames=[21,22,23,24,25]
states={}
for f in frames:
    s=[]
    for ph in G:
        m=R[f]@Matrix.Rotation(math.radians(ph),3,"Y")
        for c in cands(m):
            s.append((ph,[math.degrees(t) for t in c]))
    states[f]=s
dp=[[(0.0,v,None) for (ph,v) in states[frames[0]]]]
for i in range(1,len(frames)):
    row=[]
    for (ph,v) in states[frames[i]]:
        best=(1e9,None,-1)
        for j,(ms,pv,bp) in enumerate(dp[-1]):
            w=uw(v,pv); st=max(abs(a-b) for a,b in zip(w,pv)); c=max(ms,st)
            if c<best[0]: best=(c,w,j)
        row.append((best[0],best[1],best[2]))
    dp.append(row)
best=min(dp[-1], key=lambda t:t[0])
print("  minimax over f21..f25 =", round(best[0],2))
