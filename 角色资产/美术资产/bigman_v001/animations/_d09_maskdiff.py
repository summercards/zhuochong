import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import anim_lib as A
PRE = os.path.join(A.OUT_DIR, "previews", "anim")

def load(p):
    im = bpy.data.images.load(p, check_existing=False)
    w, h = im.size
    a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    return a

def mask(px):
    al = px[:, :, 3]
    if float(al.min()) < 0.5:
        return al > 0.5
    return px[:, :, :3].min(axis=2) < 0.92

for view in ("front", "side"):
    tags = ["f0000", "f0003", "f0005", "f0006", "f0012"]
    d = {t: load(os.path.join(PRE, "hithead_%s_%s.png" % (view, t))) for t in tags}
    m = {t: mask(v) for t, v in d.items()}
    print("== %s ==" % view)
    for a, b in (("f0003","f0005"), ("f0005","f0006"), ("f0003","f0006"), ("f0000","f0003")):
        diff = m[a] ^ m[b]
        n = int(diff.sum())
        px_diff = np.abs(d[a][:, :, :3] - d[b][:, :, :3]).max()
        rows = np.where(diff.any(axis=1))[0]
        allpix = np.abs(d[a] - d[b]).max()
        print("  %s vs %s : mask_xor=%d  rgb_max=%.5f  all_max=%.5f  rows=%s"
              % (a, b, n, float(px_diff), float(allpix),
                 (int(rows.min()), int(rows.max()), len(rows)) if rows.size else None))
