"""_d12_diag_profile —— D12 侧视逐帧**轮廓剖面**诊断（只报不判）。

目的：看清 `px_waist_pivot_ok` / `px_frozen_block_ok` / `hem_excluded_ok` 三个红项的
真实像素结构 —— 特别是「骨盆到底落在哪一行」。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python _d12_diag_profile.py
"""

import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A  # noqa: E402

PRE = os.path.join(A.OUT_DIR, "previews", "anim")
SIDE_RES_Y, SIDE_ORTHO = 1100, 4.30
CAM_Z = 1.55
PPM = (float(SIDE_RES_Y) / SIDE_ORTHO) / 1000.0     # px/mm
FRAMES = [0, 1, 2, 3, 4, 5, 6, 9, 12, 16, 20, 25, 26, 30, 34]
NB = 26


def z_of_row(row):
    return (float(row) / (PPM * 1000.0)) + (CAM_Z - SIDE_ORTHO / 2.0)


def load(frame):
    path = os.path.join(PRE, "launchhit_side_f%04d.png" % frame)
    if not os.path.exists(path):
        return None
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    px = np.array(image.pixels[:], dtype=np.float32).reshape(height, width, 4)
    bpy.data.images.remove(image)
    return px


def mask_of(pixels):
    alpha = pixels[:, :, 3]
    if float(alpha.min()) < 0.5:
        return alpha > 0.5
    return pixels[:, :, :3].min(axis=2) < 0.92


def comps(mask):
    rows, cols = np.where(mask)
    if rows.size == 0:
        return []
    index, parent = {}, list(range(rows.size))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for k in range(rows.size):
        r, c = int(rows[k]), int(cols[k])
        for key in ((r - 1, c), (r, c - 1)):
            j = index.get(key)
            if j is not None:
                ra, rb = find(k), find(j)
                if ra != rb:
                    parent[rb] = ra
        index[(r, c)] = k
    groups = {}
    for k in range(rows.size):
        groups.setdefault(find(k), []).append(k)
    out = []
    for members in groups.values():
        sel = np.array(members, dtype=np.int64)
        rr, cc = rows[sel], cols[sel]
        sub = np.zeros_like(mask)
        sub[rr, cc] = True
        out.append({"area": int(len(members)),
                    "rows": [int(rr.min()), int(rr.max())],
                    "cols": [int(cc.min()), int(cc.max())],
                    "row_center": round(float(rr.mean()), 1),
                    "col_center": round(float(cc.mean()), 1),
                    "mask": sub})
    out.sort(key=lambda d: -d["area"])
    return out


def profile(mask):
    rows = np.where(mask.any(axis=1))[0]
    if rows.size == 0:
        return []
    lo, hi = int(rows.min()), int(rows.max())
    out = []
    for k in range(NB + 1):
        r = int(round(lo + (hi - lo) * k / float(NB)))
        line = mask[r, :]
        cc = np.where(line)[0]
        if cc.size == 0:
            out.append({"row": r, "z_mm": round(z_of_row(r) * 1000.0, 1),
                        "width": 0, "col": None})
            continue
        out.append({"row": r, "z_mm": round(z_of_row(r) * 1000.0, 1),
                    "width": int(cc.max() - cc.min() + 1),
                    "cmin": int(cc.min()), "cmax": int(cc.max()),
                    "ccent": round(float(cc.mean()), 1),
                    "nrun": int(np.count_nonzero(np.diff(cc) > 1) + 1)})
    return out


def main():
    rep = {}
    for f in FRAMES:
        px = load(f)
        if px is None:
            continue
        raw = mask_of(px)
        cs = comps(raw)
        clean = cs[0]["mask"] if cs else raw
        meta = [{k: v for k, v in d.items() if k != "mask"} for d in cs]
        rows = np.where(raw.any(axis=1))[0]
        rep[str(f)] = {
            "raw_rows": [int(rows.min()), int(rows.max())],
            "raw_z_mm": [round(z_of_row(rows.min()) * 1000.0, 1),
                         round(z_of_row(rows.max()) * 1000.0, 1)],
            "components": meta,
            "profile": profile(raw),
            "profile_top_only": profile(clean),
        }
    print("D12_PROFILE " + json.dumps(rep, ensure_ascii=False))
    print("D12_PROFILE_DONE frames=%d ppm=%f" % (len(rep), PPM))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D12_PROFILE_FAILURE " + traceback.format_exc())
