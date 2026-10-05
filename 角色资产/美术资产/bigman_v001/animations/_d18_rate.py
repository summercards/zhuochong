import math,re,json,sys
def Rx(a):
    c,s=math.cos(a),math.sin(a); return ((1,0,0),(0,c,-s),(0,s,c))
def Ry(a):
    c,s=math.cos(a),math.sin(a); return ((c,0,s),(0,1,0),(-s,0,c))
def Rz(a):
    c,s=math.cos(a),math.sin(a); return ((c,-s,0),(s,c,0),(0,0,1))
def mm(A,B): return tuple(tuple(sum(A[i][k]*B[k][j] for k in range(3)) for j in range(3)) for i in range(3))
def T(A): return tuple(tuple(A[j][i] for j in range(3)) for i in range(3))
def geo(e1,e2):
    A=mm(Rz(math.radians(e1[2])),mm(Ry(math.radians(e1[1])),Rx(math.radians(e1[0]))))
    B=mm(Rz(math.radians(e2[2])),mm(Ry(math.radians(e2[1])),Rx(math.radians(e2[0]))))
    M=mm(T(A),B); t=M[0][0]+M[1][1]+M[2][2]
    c=max(-1.0,min(1.0,(t-1.0)/2.0)); return math.degrees(math.acos(c))
p=sys.argv[1]
s=open(p,encoding="utf-8",errors="replace").read()
i=s.index("D18_STEP_ALL "); j=s.index("\n",i)
data=json.loads(s[i+len("D18_STEP_ALL "):j])
print(f"{'bone':<12} {'f':>3} {'step':>7} {'real':>7} {'amp':>5}  prev -> cur")
over=[]
for step,f0,f1,bone,e0,e1 in data:
    g=geo(e0,e1); amp=step/g if g>1e-9 else 0
    flag="REAL>25" if g>25 else ""
    print(f"{bone:<12} {f1:>3} {step:>7.2f} {g:>7.2f} {amp:>5.2f}  {flag}")
    if g>25: over.append((bone,f0,f1,g))
print("\n真实超 25°/帧的点：",len(over))
for o in sorted(over,key=lambda x:-x[3]): print("   ",o)
