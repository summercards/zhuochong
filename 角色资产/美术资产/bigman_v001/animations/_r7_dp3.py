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
    v=list(v)
    for i in range(3):
        while v[i]-ref[i] > 180.0: v[i]-=360.0
        while v[i]-ref[i] < -180.0: v[i]+=360.0
    return v
E = {
 "upperarm.L": {0:[38.52,0.71,4.69],1:[34.82,8.13,-2.88],2:[33.46,13.05,-7.78],3:[33.59,16.35,-10.44],4:[34.24,16.11,-11.55],5:[33.08,12.21,-8.51],6:[30.93,9.69,-4.5],7:[27.72,7.13,-0.61],8:[23.66,4.74,3.21],9:[21.89,3.15,5.75]},
 "forearm.L": {0:[45.09,-68.16,-1.0],1:[61.31,-74.62,12.16],2:[45.74,-81.99,48.62],3:[-3.41,-19.52,112.89],4:[-9.73,-3.84,128.75],5:[-11.83,-2.69,130.54],6:[-14.74,0.01,131.35],7:[-17.21,0.61,131.56],8:[-19.45,0.38,130.74],9:[-19.21,-3.59,126.69]},
 "hand.L": {0:[-39.47,45.51,-30.17],1:[-55.68,33.94,-47.3],2:[-62.21,22.23,-58.56],3:[-17.51,67.08,-88.41],4:[10.74,39.04,-81.54],5:[14.85,36.97,-85.78],6:[19.61,33.43,-89.49],7:[23.19,32.76,-92.23],8:[25.97,29.56,-95.15],9:[24.73,27.15,-92.8]},
}
GREEDY = [0,5,10,15,20,25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,105,110,115,120,125,130,135,140,145,150,155,160,165,170,175,180,185,190,195,200,205,210,215,220,225,230,235,240,245,250,255,260,265,270,275,280,285,290,295,300,305,310,315,320,325,330,335,340,345,350,355]
for bone, tbl in E.items():
    FR = sorted(tbl)
    R = {f: Euler([math.radians(v) for v in tbl[f]],"XYZ").to_matrix() for f in FR}
    ROT = {p: Matrix.Rotation(math.radians(p),3,"Y") for p in GREEDY}
    states = {}
    for f in FR:
        st=[]
        for p in GREEDY:
            if f==0 and p!=0: continue
            m = R[f] @ ROT[p]
            for ci,c in enumerate(cands(m)):
                if f==0 and ci!=0: continue
                st.append((p,[math.degrees(t) for t in c]))
        states[f]=st
    dp = [[ (0.0, v, None) for (p,v) in states[FR[0]] ]]
    for i in range(1,len(FR)):
        f=FR[i]; row=[]
        for (p,v) in states[f]:
            best=(1e9,None,-1)
            for j,(ms,pv,bp) in enumerate(dp[-1]):
                w=unwrap(v,pv); st=max(abs(a-b) for a,b in zip(w,pv))
                c=max(ms,st)
                if c<best[0]: best=(c,w,j)
            row.append((best[0],best[1],best[2]))
        dp.append(row)
    k=min(range(len(dp[-1])), key=lambda j: dp[-1][j][0])
    seq=[]
    for i in range(len(FR)-1,-1,-1):
        ms,v,j = dp[i][k]
        seq.append((FR[i], states[FR[i]][k][0], round(ms,2), [round(q,2) for q in v]))
        k = j if (j is not None and j>=0) else 0
    seq.reverse()
    print("== %s  minimax = %.2f ==" % (bone, dp[-1][min(range(len(dp[-1])), key=lambda j: dp[-1][j][0])][0]))
    for f,p,ms,v in seq:
        print("   f%-2d phi=%-4d max=%-7.2f eul=%s" % (f,p,ms,v))
