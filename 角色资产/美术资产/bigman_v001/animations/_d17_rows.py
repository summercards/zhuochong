import os, sys, json
import bpy, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A
PRE = os.path.join(A.OUT_DIR, "previews", "anim")

def load(stem, f):
    p = os.path.join(PRE, "%s_f%04d.png" % (stem, f))
    if not os.path.exists(p): return None
    im = bpy.data.images.load(p, check_existing=False)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    return px

def mask_of(px):
    a = px[:, :, 3]
    if float(a.min()) < 0.5: return a > 0.5
    return px[:, :, :3].min(axis=2) < 0.92

def stats(px):
    m = mask_of(px)
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    wgt = m.sum(axis=1).astype(np.float64)
    ar = None if wgt.sum() <= 0 else float((np.arange(m.shape[0])*wgt).sum()/wgt.sum())
    return {"bottom": int(rows.min()), "top": int(rows.max()),
            "h": int(rows.max()-rows.min()+1),
            "col_lo": int(cols.min()), "col_hi": int(cols.max()),
            "area": None if ar is None else round(ar, 3)}

for stem in ("getupfwide_side", "groundhitwide_side", "knockdownf_side", "idle01wide_side"):
    fl = range(0, 21) if "knockdownf" in stem and "wide" not in stem else range(0, 37)
    out = {}
    for f in fl:
        px = load(stem, f)
        if px is None: continue
        if stem == "groundhitwide_side" and f > 20: continue
        if stem == "idle01wide_side" and f > 0: continue
        out[f] = stats(px)
    print("STEM", stem, json.dumps({str(k): v for k, v in out.items()}, ensure_ascii=False))

for stem, fl in (("getupf_side", [0, 1, 9, 20, 34, 36]),):
    out = {}
    for f in fl:
        px = load(stem, f)
        if px is not None: out[f] = stats(px)
    print("STEM", stem, json.dumps({str(k): v for k, v in out.items()}, ensure_ascii=False))
