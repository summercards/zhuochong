"""扫各高度区间的侧视重心位移 —— 给 D10 的躯干带定区间（先扫再定）。"""
import os, sys, json
import bpy, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A

PRE = os.path.join(A.OUT_DIR, "previews", "anim")

def load(path):
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    return px

def mask_of(p):
    a = p[:, :, 3]
    if float(a.min()) < 0.5:
        return a > 0.5
    return p[:, :, :3].min(axis=2) < 0.92

def centroid(m, rows):
    b = m[rows[0]:rows[1], :]
    cols = np.where(b.any(axis=0))[0]
    if cols.size == 0:
        return None
    w = b.sum(axis=0).astype(np.float64)
    return float((np.arange(b.shape[1]) * w).sum() / w.sum())

ref = load(os.path.join(PRE, "hitbody_front_f0000.png"))
fm = mask_of(ref)
ra = np.where(fm.any(axis=1))[0]
lo, hi = int(ra.min()), int(ra.max()); span = hi - lo
print("ROWS lo=%d hi=%d span=%d" % (lo, hi, span))

CASES = [("hitbody", "f0000", "f0003"), ("hitbody", "f0000", "f0008"),
         ("guardbreak", "f0000", "f0004"), ("hithead", "f0000", "f0003")]
cache = {}
def M(stem, tag):
    k = (stem, tag)
    if k not in cache:
        cache[k] = mask_of(load(os.path.join(PRE, "%s_side_%s.png" % (stem, tag))))
    return cache[k]

BANDS = [(0.40,0.60),(0.45,0.65),(0.50,0.70),(0.55,0.75),(0.60,0.75),
         (0.62,0.78),(0.65,0.80),(0.55,0.72),(0.45,0.72),(0.58,0.78),(0.60,0.80)]
for f0, f1 in BANDS:
    rows = (lo + int(span*f0), lo + int(span*f1))
    line = "band %.2f-%.2f rows=%s | " % (f0, f1, list(rows))
    for stem, a, b in CASES:
        ca, cb = centroid(M(stem,a), rows), centroid(M(stem,b), rows)
        d = None if (ca is None or cb is None) else round(cb-ca, 2)
        line += "%s:%s " % (stem, d)
    print(line)
