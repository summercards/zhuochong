import os, json
import numpy as np, bpy
PRE = r"I:\工作项目\BIGMANFIGHT\角色资产\美术资产\bigman_v001\previews\anim"
def mask_of(a):
    al = a[:, :, 3]
    if float(al.min()) < 0.5:
        return al > 0.5
    return a[:, :, :3].min(axis=2) < 0.92
def stats(stem, f):
    p = os.path.join(PRE, "%s_f%04d.png" % (stem, f))
    if not os.path.exists(p):
        return None
    im = bpy.data.images.load(p, check_existing=False)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    m = mask_of(a)
    rgb = a[:, :, :3]
    lum = 0.2126*rgb[:,:,0] + 0.7152*rgb[:,:,1] + 0.0722*rgb[:,:,2]
    blue = rgb[:,:,2] - rgb[:,:,0]
    inside = lum[m]
    cols_all = np.where(m.any(axis=0))[0]
    cc_all = float((np.arange(w)*m.sum(axis=0)).sum()/m.sum())
    dark = m & (lum < 0.30)
    db = m & (blue < 0.10)
    out = {"lum_min": round(float(inside.min()),3), "lum_med": round(float(np.median(inside)),3),
           "lum_p05": round(float(np.percentile(inside,5)),3),
           "col_all": [int(cols_all.min()), int(cols_all.max())], "cc_all": round(cc_all,1)}
    for tag, mm in (("dark", dark), ("nonblue", db)):
        n = int(mm.sum())
        out[tag+"_n"] = n
        if n:
            cols = np.where(mm.any(axis=0))[0]
            out[tag+"_cols"] = [int(cols.min()), int(cols.max())]
            out[tag+"_cc"] = round(float((np.arange(w)*mm.sum(axis=0)).sum()/n),1)
            out[tag+"_lum"] = round(float(lum[mm].mean()),3)
    return out
res = {}
for stem, f in (("knockdownbwide_side",20),("knockdownbwide_side",7),
                ("knockdownbwide_side",0),("knockdownf_side",20),
                ("knockdownf_side",7),("airhit_side",18)):
    res["%s_f%04d"%(stem,f)] = stats(stem, f)
print("CAL " + json.dumps(res))
