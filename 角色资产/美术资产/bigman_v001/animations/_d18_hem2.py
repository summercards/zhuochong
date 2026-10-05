import os, sys
import bpy, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A
PRE = os.path.join(A.OUT_DIR, "previews", "anim")

VIEWS = {  # name: (res_y, ortho, cam_z, center_y)
    "getupbwide_side":  (1100, 3.60, 0.95, 250.0),
    "groundhitwide_side": (1100, 3.30, 1.00, 500.0),
    "getupfwide_side":  (1100, 3.60, 0.95, -300.0),
    "knockdownbwide_side": (1100, 3.30, 1.00, 0.0),
}
HEM = (-188.78, -121.94, 897.5, 188.78, 129.03, 926.0)  # 并集（两块）

def box(view):
    res_y, ortho, cam_z, cy = VIEWS[view]
    mm = ortho / float(res_y) * 1000.0
    col_c = 780.0 / 2.0
    row_floor = (ortho / 2.0 - cam_z) / (ortho / float(res_y))
    c0 = int(np.floor(col_c + (HEM[1] - cy) / mm)) - 1
    c1 = int(np.ceil(col_c + (HEM[4] - cy) / mm)) + 1
    r0 = int(np.floor(row_floor + HEM[2] / mm)) - 1
    r1 = int(np.ceil(row_floor + HEM[5] / mm)) + 1
    return max(c0, 0), min(c1, 779), max(r0, 0), min(r1, 1099)

def load(view, f):
    p = os.path.join(PRE, "%s_f%04d.png" % (view, f))
    if not os.path.exists(p): return None
    im = bpy.data.images.load(p, check_existing=False)
    w, h = im.size
    px = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(im)
    a = px[:, :, 3]
    return (a > 0.5) if float(a.min()) < 0.5 else (px[:, :, :3].min(axis=2) < 0.92)

def ext(m):
    r = np.where(m.any(axis=1))[0]
    return (int(r.min()), int(r.max())) if r.size else None

def series(view, n):
    c0, c1, r0, r1 = box(view)
    raw_t, str_t, str_b = [], [], []
    for f in range(n + 1):
        m = load(view, f)
        if m is None: continue
        m2 = m.copy(); m2[r0:r1 + 1, c0:c1 + 1] = False
        raw_t.append(ext(m)[1]); str_t.append(ext(m2)[1]); str_b.append(ext(m2)[0])
    return raw_t, str_t, str_b

def rep(tag, view, n):
    raw, st, sb = series(view, n)
    drops = [i for i in range(1, len(st)) if st[i] < st[i - 1]]
    print("%-22s n=%d  raw_top f0=%d fN=%d | STRIPPED top f0=%d fN=%d rise=%d drops@%s | "
          "STRIPPED bottom f0=%d fN=%d"
          % (tag, n, raw[0], raw[-1], st[0], st[-1], st[-1] - st[0], drops, sb[0], sb[-1]))
    print("   stripped_top_series=%s" % st)

rep("D18 (hem strip)", "getupbwide_side", 46)
rep("D16 (hem strip)", "groundhitwide_side", 20)
rep("D17 (hem strip)", "getupfwide_side", 36)
