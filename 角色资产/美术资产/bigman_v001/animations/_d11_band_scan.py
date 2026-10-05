"""_d11_band_scan —— 逐区间实测：哪一段前视横带**峰值帧**早于上身侧倾。

动机：`probe_d11_pixels.py` 首次运行 `px_lower_leads_ok=false` ——
  骨盆带（0.42~0.56 全高）横向位移峰值落在 **f8**，与上身侧倾峰**同帧**（lag=0）。
  但门禁 `lower_body_leads_ok` 说骨盆侧倾峰在 f3、胸峰在 f8。
  ⟹ 怀疑前视横带里混进了**手臂**（肩→肘挂在胸/脊上，sway 一并把它们甩过去）。
  逐段实测：哪个 band 的峰值帧是 **f3**（= 真正的下盘）且幅度够大。
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
STEM = "hitleg"
TAGS = ["f0000", "f0003", "f0006", "f0008", "f0012", "f0016", "f0019", "f0030"]

cache = {}


def load(path):
    if path in cache:
        return cache[path]
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32)
    pixels = pixels.reshape(height, width, 4)
    bpy.data.images.remove(image)
    cache[path] = pixels
    return pixels


def mask_of(pixels):
    alpha = pixels[:, :, 3]
    if float(alpha.min()) < 0.5:
        return alpha > 0.5
    return pixels[:, :, :3].min(axis=2) < 0.92


def centroid(mask, rows):
    band = mask[rows[0]:rows[1], :]
    cols = np.where(band.any(axis=0))[0]
    if cols.size == 0:
        return None, None, 0
    weights = band.sum(axis=0).astype(np.float64)
    center = float((np.arange(band.shape[1]) * weights).sum() / weights.sum())
    return (center,
            (int(cols.min()), int(cols.max())),
            int(band.sum()))


def main():
    f0 = mask_of(load(os.path.join(PRE, "%s_front_f0000.png" % STEM)))
    rows_any = np.where(f0.any(axis=1))[0]
    lo, hi = int(rows_any.min()), int(rows_any.max())
    span = hi - lo
    print("SCAN_LAYOUT " + json.dumps({"char_rows": [lo, hi], "span": span}))

    # 1) f0 逐行左右缘 —— 找手臂在哪一段（手臂会让行宽突然变大）
    print("SCAN_ROWS " + json.dumps({
        "rows": [[r, int(f0[r].sum())] for r in range(lo, hi + 1)],
    }))

    # 2) 逐区间（0.05 宽）实测 f3/f8 的横向 delta 与峰值帧
    out = []
    step = 0.05
    frac = 0.02
    while frac + step <= 1.0001:
        rows = (lo + int(span * frac), lo + int(span * (frac + step)))
        series = {}
        for tag in TAGS:
            m = mask_of(load(os.path.join(PRE, "%s_front_%s.png" % (STEM, tag))))
            c, _e, npx = centroid(m, rows)
            series[tag] = (c, npx)
        base = series["f0000"][0]
        vals = [(t, series[t][0] - base) for t in TAGS]
        peak_tag = max(vals, key=lambda kv: abs(kv[1]))[0]
        out.append({
            "frac": [round(frac, 2), round(frac + step, 2)],
            "z_mm": [round((rows[0] - 550) * 1.909 + 920, 0),
                     round((rows[1] - 550) * 1.909 + 920, 0)],
            "f0_px": round(base, 2),
            "npx_f0": series["f0000"][1],
            "d_f3": round(series["f0003"][0] - base, 2),
            "d_f8": round(series["f0008"][0] - base, 2),
            "peak_tag": peak_tag,
            "peak_val": round(max(abs(v) for _t, v in vals), 2),
            "series": [[t, round(v, 2)] for t, v in vals],
        })
        frac += step
    print("SCAN_BANDS " + json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
