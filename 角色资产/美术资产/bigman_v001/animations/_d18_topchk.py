import os, sys
import bpy, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A
PRE = os.path.join(A.OUT_DIR, "previews", "anim")

def top(path):
    if not os.path.exists(path):
        return None
    im = bpy.data.images.load(path, check_existing=False)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    a = px[:, :, 3]
    m = (a > 0.5) if float(a.min()) < 0.5 else (px[:, :, :3].min(axis=2) < 0.92)
    rows = np.where(m.any(axis=1))[0]
    cols = np.where(m.any(axis=0))[0]
    return (int(rows.min()), int(rows.max()), int(cols.min()), int(cols.max())) if rows.size else None

for f in ("getupfwide_side_f0000", "getupfwide_side_f0004", "getupfwide_side_f0020",
          "getupfwide_side_f0036", "getupbwide_side_f0000", "getupbwide_side_f0020",
          "getupbwide_side_f0046", "idle01wideb_side_f0000", "idle01wide_side_f0000"):
    print("%-26s %s" % (f, top(os.path.join(PRE, f + ".png"))))
