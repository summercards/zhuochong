import os, json
import numpy as np, bpy
PRE = r"I:\工作项目\BIGMANFIGHT\角色资产\美术资产\bigman_v001\previews\anim"
def mask_of(a):
    al = a[:, :, 3]
    if float(al.min()) < 0.5:
        return al > 0.5
    return a[:, :, :3].min(axis=2) < 0.92
out = {}
for stem in ("knockdownb_side", "knockdownb_front", "knockdownb_three_quarter", "airhit_side"):
    for f in (0, 6, 7, 10, 15, 16, 20, 18):
        p = os.path.join(PRE, "%s_f%04d.png" % (stem, f))
        if not os.path.exists(p):
            continue
        im = bpy.data.images.load(p, check_existing=False)
        w, h = im.size
        a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        bpy.data.images.remove(im)
        m = mask_of(a)
        rows = np.where(m.any(axis=1))[0]; cols = np.where(m.any(axis=0))[0]
        out["%s_f%04d" % (stem, f)] = {
            "col_lo": int(cols.min()), "col_hi": int(cols.max()),
            "row_lo": int(rows.min()), "row_hi": int(rows.max()),
            "clip_R": bool(cols.max() >= w - 1), "clip_L": bool(cols.min() <= 0),
            "clip_T": bool(rows.max() >= h - 1), "clip_B": bool(rows.min() <= 0),
            "npx": int(m.sum())}
print("PXPROBE " + json.dumps(out))
