import os, json
import numpy as np, bpy
PRE = r"I:\工作项目\BIGMANFIGHT\角色资产\美术资产\bigman_v001\previews\anim"
def mask_of(a):
    al = a[:, :, 3]
    if float(al.min()) < 0.5:
        return al > 0.5
    return a[:, :, :3].min(axis=2) < 0.92
def stats(stem, f):
    base = PRE2 if stem.endswith("W_side") else PRE
    p = os.path.join(base, "%s_f%04d.png" % (stem, f))
    if not os.path.exists(p): return None
    im = bpy.data.images.load(p, check_existing=False)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    m = mask_of(a); rgb = a[:, :, :3]
    lum = 0.2126*rgb[:,:,0]+0.7152*rgb[:,:,1]+0.0722*rgb[:,:,2]
    rb = rgb[:,:,0]-rgb[:,:,2]
    def cc(mm):
        if int(mm.sum()) == 0:
            return None
        cols = np.where(mm.any(axis=0))[0]
        return (round(float((np.arange(w)*mm.sum(axis=0)).sum()/mm.sum()),1),
                [int(cols.min()), int(cols.max())], int(mm.sum()))
    cols_all = np.where(m.any(axis=0))[0]
    skin = m & (rb > 0.04) & (lum > 0.42) & (lum < 0.90)
    gray = m & (np.abs(rb) <= 0.04) & (lum < 0.35)
    return {"col_all":[int(cols_all.min()),int(cols_all.max())],
            "skin": cc(skin), "gray": cc(gray)}
res = {}
for stem, f in (("knockdownbwide_side",20),("knockdownbwide_side",15),
                ("knockdownbwide_side",7),("knockdownbwide_side",0),
                ("knockdownfW_side",20),("knockdownfW_side",15),
                ("knockdownfW_side",7),("knockdownfW_side",0)):
    k="%s_f%04d"%(stem,f); res[k]=stats(stem,f)
print("CAL2 " + json.dumps(res))
