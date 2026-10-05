"""_d11_bar_locate —— 定位侧视命中帧与零位帧的**逐处差异**（只读，不渲图）。

用法：改 PAIR 换对照对。
输出：
  ① `BAR_CHANGEMAP` —— 粗粒度 ASCII 变化图（整人物）。
  ② `BAR_ZONES`     —— 每个连通变化块的行/列范围 + 像素数。
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
PAIR = (os.environ.get("BAR_STEM", "hitleg"),
        os.environ.get("BAR_TAG_A", "f0000"),
        os.environ.get("BAR_TAG_B", "f0003"))
R0, C0, STEP = 60, 120, 8


def load_mask(path):
    image = bpy.data.images.load(path, check_existing=False)
    w, h = image.size
    pix = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)
    bpy.data.images.remove(image)
    alpha = pix[:, :, 3]
    if float(alpha.min()) < 0.5:
        return alpha > 0.5
    return pix[:, :, :3].min(axis=2) < 0.92


def main():
    stem, ta, tb = PAIR
    a = load_mask(os.path.join(PRE, "%s_side_%s.png" % (stem, ta)))
    b = load_mask(os.path.join(PRE, "%s_side_%s.png" % (stem, tb)))
    print("BAR_PAIR %s %s -> %s" % (stem, ta, tb))
    h, w = a.shape
    diff = (a != b)
    rows = np.where(diff.any(axis=1))[0]
    print("BAR_DIFF px=%d rows=[%s..%s]"
          % (int(diff.sum()), int(rows.min()) if rows.size else None,
             int(rows.max()) if rows.size else None))

    lines = []
    for r in range(h - 1, -1, -STEP):
        chunk = diff[max(0, r - STEP + 1):r + 1, ::STEP]
        lines.append("".join("#" if c.any() else "." for c in chunk.T))
    print("BAR_CHANGEMAP (每字符 = %dpx 宽 × %dpx 高，上=头)" % (STEP, STEP))
    for line in lines:
        print("  " + line)

    # 连通块（简易：按行分组 + 列间隙切分）
    zones = []
    cur = None
    for r in rows:
        cols = np.where(diff[r])[0]
        if cur is None or r - cur["rows"][1] > 3:
            if cur:
                zones.append(cur)
            cur = {"rows": [int(r), int(r)], "cols": [int(cols.min()), int(cols.max())],
                   "n": int(cols.size)}
        else:
            cur["rows"][1] = int(r)
            cur["cols"][0] = min(cur["cols"][0], int(cols.min()))
            cur["cols"][1] = max(cur["cols"][1], int(cols.max()))
            cur["n"] += int(cols.size)
    if cur:
        zones.append(cur)
    zones.sort(key=lambda z: -z["n"])
    for z in zones:
        z["z_mm"] = [round(z["rows"][0] * 1.9 - 125, 0), round(z["rows"][1] * 1.9 - 125, 0)]
    print("BAR_ZONES " + json.dumps(zones[:12], ensure_ascii=False))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("BAR_FAILURE " + traceback.format_exc())
