import os, sys
import bpy, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import anim_lib as A
PRE=os.path.join(A.OUT_DIR,"previews","anim")
def load_mask(p):
    im=bpy.data.images.load(p,check_existing=False); w,h=im.size
    px=np.array(im.pixels[:],dtype=np.float32).reshape(h,w,4); bpy.data.images.remove(im)
    a=px[:,:,3]
    return a>0.5 if float(a.min())<0.5 else px[:,:,:3].min(axis=2)<0.92
def runs(rowmask):
    cols=np.where(rowmask)[0]
    if cols.size==0: return []
    out=[];s=cols[0];p=cols[0]
    for c in cols[1:]:
        if c!=p+1: out.append((int(s),int(p))); s=c
        p=c
    out.append((int(s),int(p)))
    return out
stem=os.environ.get("BAR_STEM","hitleg")
for tag in ("f0000","f0003",):
    m=load_mask(os.path.join(PRE,"%s_side_%s.png"%(stem,tag)))
    print("### %s %s"%(stem,tag))
    for r in (70,80,90,100,106,110,115,120,125,130,140,150,160):
        print("   row=%-4d z=%4.0fmm  runs=%s"%(r,r*1.9-125,runs(m[r])))
