"""_d12_diag_mask —— 诊断 D12 侧视静帧里"最低那一坨"到底是什么。"""
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A  # noqa: E402

PRE = os.path.join(A.OUT_DIR, "previews", "anim")
PPM = (1100.0 / 4.30) / 1000.0      # px per mm
ROW0_Z_MM = (1.55 - 4.30 / 2.0) * 1000.0


def load(frame):
    path = os.path.join(PRE, "launchhit_side_f%04d.png" % frame)
    image = bpy.data.images.load(path, check_existing=False)
    w, h = image.size
    px = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(image)
    return px


def mask_of(px):
    alpha = px[:, :, 3]
    if float(alpha.min()) < 0.5:
        return alpha > 0.5
    return px[:, :, :3].min(axis=2) < 0.92


def z_of(row):
    return ROW0_Z_MM + row / PPM


for frame in (0, 12, 20, 30):
    px = load(frame)
    m = mask_of(px)
    rows = np.where(m.any(axis=1))[0]
    print("=== f%02d  min_row=%d (z=%.1f mm)  max_row=%d (z=%.1f mm)  px_alpha_min=%.3f"
          % (frame, rows.min(), z_of(rows.min()), rows.max(), z_of(rows.max()),
             float(px[:, :, 3].min())))
    for row in range(rows.min(), min(rows.min() + 60, rows.max() + 1), 4):
        cols = np.where(m[row])[0]
        if cols.size:
            print("    row %4d z=%7.1f mm  cols %3d..%3d  n=%3d"
                  % (row, z_of(row), cols.min(), cols.max(), cols.size))
    # 逐"连通块"（按行分段）报告：找到最低的**孤立**横条
    segs = []
    for row in range(rows.min(), rows.max() + 1):
        cols = np.where(m[row])[0]
        if cols.size:
            segs.append((row, int(cols.min()), int(cols.max()), cols.size))
    print("    lowest 6 rows:", [(r, c0, c1, n) for r, c0, c1, n in segs[:6]])
