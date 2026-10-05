# -*- coding: utf-8 -*-
"""D18 目检拼图 —— 只读，不写工程、不跑 Blender。

★ 2026-10-03 重写：帧数口径从旧的「输出 46 帧 / f0046」改为**定稿 40 帧 / f0040**
（= `anim_getup_b.py` 的纯默认值：`TOTAL = OUT_TOTAL = 40`，恒等映射、无重采样）。

产出 6 张（全部落在 previews/anim/）：
  _d18_check_grid_wide.png   wide 视 全 41 帧（0..40）网格
  _d18_check_end_idle.png    末帧 / f34 与 idle01 同机位并排
  _d18_diff_end_idle.png     末帧 vs idle01 逐像素差分（红 = 不同）
  _d18_key_side.png          side 视 11 个相位关键帧长条
  _d18_plant_zoom.png        wide 视 f0..f20 撑地段放大（自动裁框）
  _d18_rise.png              wide 视 f20..f40 起身段长条（自动裁框）

用法：python _d18_montage.py
"""
import os

from PIL import Image, ImageDraw

P = r"I:\工作项目\BIGMANFIGHT\角色资产\美术资产\bigman_v001\previews\anim"

END_FRAME = 40
TOTAL = 40
# 定稿相位（= anim_getup_b.py 的默认值）
KEYS = [(0, "躺(KD_B@20)"), (4, "腿落地"), (7, "掌撑地"), (11, "胸顶起"),
        (20, "手离地"), (22, "收腿"), (30, "脚接住"), (34, "蹬伸中"),
        (38, "站直"), (40, "=Idle_01@0")]

BG_TOL = 6


def _path(n):
    p = os.path.join(P, n)
    if not os.path.exists(p):
        raise SystemExit("缺文件：%s" % p)
    return p


def _load(n):
    return Image.open(_path(n)).convert("RGB")


def _bg(im):
    return im.getpixel((0, 0))


def _bbox(im, box=None):
    """非背景像素的包围盒 (l, t, r, b)；box 给 (l, t, r, b) 则先限定范围再算。"""
    w, h = im.size
    l0, t0, r0, b0 = box if box else (0, 0, w, h)
    bg = _bg(im)
    px = im.load()
    l = t = 10 ** 9
    r = b = -1
    for y in range(t0, b0):
        for x in range(l0, r0):
            c = px[x, y]
            if (abs(c[0] - bg[0]) > BG_TOL or abs(c[1] - bg[1]) > BG_TOL
                    or abs(c[2] - bg[2]) > BG_TOL):
                if x < l:
                    l = x
                if x > r:
                    r = x
                if y < t:
                    t = y
                if y > b:
                    b = y
    if r < 0:
        return None
    return (l, t, r + 1, b + 1)


def _tile_strip(names, labels, out, tw, th, cols=None, bgc=(18, 18, 20),
                lab_col=(255, 255, 0)):
    cols = cols or len(names)
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), bgc)
    d = ImageDraw.Draw(sheet)
    for k, n in enumerate(names):
        im = _load(n).resize((tw - 2, th - 2), Image.LANCZOS)
        cx, cy = (k % cols) * tw, (k // cols) * th
        sheet.paste(im, (cx + 1, cy + 1))
        d.text((cx + 4, cy + 4), labels[k], fill=lab_col)
    sheet.save(out)
    print("OUT %s %s" % (os.path.basename(out), sheet.size))


def _union_bbox(names, limit=None, pad=12):
    l = t = 10 ** 9
    r = b = -1
    for n in names:
        im = _load(n)
        bb = _bbox(im, limit)
        if bb:
            l, t = min(l, bb[0]), min(t, bb[1])
            r, b = max(r, bb[2]), max(b, bb[3])
    w, h = im.size
    return (max(0, l - pad), max(0, t - pad),
            min(w, r + pad), min(h, b + pad))


def _tile_crop(names, labels, out, box, tw, th, cols=None, zoom=2,
               bgc=(18, 18, 20), lab_col=(255, 255, 0)):
    """按同一 box 裁剪 + 放大，保证各帧逐位可比。"""
    cols = cols or len(names)
    rows = (len(names) + cols - 1) // cols
    l, t, r, b = box
    cw, ch = (r - l) * zoom, (b - t) * zoom
    sheet = Image.new("RGB", (cols * cw, rows * ch), bgc)
    d = ImageDraw.Draw(sheet)
    for k, n in enumerate(names):
        im = _load(n).crop(box).resize((cw - 2, ch - 2), Image.LANCZOS)
        cx, cy = (k % cols) * cw, (k // cols) * ch
        sheet.paste(im, (cx + 1, cy + 1))
        d.text((cx + 4, cy + 4), labels[k], fill=lab_col)
    sheet.save(out)
    print("OUT %s %s box=%s" % (os.path.basename(out), sheet.size, box))


# ---- 1) wide 全 41 帧网格 -------------------------------------------------
allf = list(range(0, TOTAL + 1))
_tile_strip(["getupbwide_side_f%04d.png" % i for i in allf],
            ["f%d" % i for i in allf],
            os.path.join(P, "_d18_check_grid_wide.png"), 160, 226, cols=7)

# ---- 2) 末帧 / f34 vs idle01 同机位并排 -----------------------------------
idle_n = "idle01wideb_side_f0000.png"
pairs = [("getupbwide_side_f%04d.png" % END_FRAME, idle_n, "f40 vs IDLE01"),
         ("getupbwide_side_f0034.png", idle_n, "f34 vs IDLE01")]
SW, SH = 300, 424
cmp_img = Image.new("RGB", (SW * len(pairs) * 2, SH), (18, 18, 20))
dc = ImageDraw.Draw(cmp_img)
for i, (a, b, tag) in enumerate(pairs):
    for j, n in enumerate((a, b)):
        im = _load(n).resize((SW - 2, SH - 20), Image.LANCZOS)
        x = (i * 2 + j) * SW
        cmp_img.paste(im, (x + 1, 18))
        dc.text((x + 4, 3), n.replace("_side_f", " f").replace(".png", ""),
                fill=(0, 255, 128))
    dc.text((i * 2 * SW + 4, SH - 16), tag, fill=(255, 200, 0))
cmp_img.save(os.path.join(P, "_d18_check_end_idle.png"))
print("OUT _d18_check_end_idle.png %s" % (cmp_img.size,))

# ---- 3) 像素级差分：末帧 vs IDLE01 ----------------------------------------
a = _load("getupbwide_side_f%04d.png" % END_FRAME)
b = _load(idle_n)
diff = Image.new("RGB", a.size, (0, 0, 0))
pa, pb, pd = a.load(), b.load(), diff.load()
cnt = 0
for y in range(a.size[1]):
    for x in range(a.size[0]):
        if pa[x, y] != pb[x, y]:
            pd[x, y] = (255, 0, 0)
            cnt += 1
diff.save(os.path.join(P, "_d18_diff_end_idle.png"))
print("OUT _d18_diff_end_idle.png diff_px=%d of %d"
      % (cnt, a.size[0] * a.size[1]))

# ---- 4) side 关键相位长条 -------------------------------------------------
_tile_strip(["getupb_side_f%04d.png" % f for f, _ in KEYS],
            ["f%d %s" % (f, s) for f, s in KEYS],
            os.path.join(P, "_d18_key_side.png"), 200, 283, cols=5)

# ---- 5) 撑地段放大（f0..f20，隔 2 帧）-------------------------------------
pf = list(range(0, 21, 2))
_pw, _ph = _load("getupbwide_side_f0000.png").size
# 撑地段只看画面纵向 15%~60% 一带（上半是空天、下半被地面/衣摆占）
box = _union_bbox(["getupbwide_side_f%04d.png" % f for f in pf],
                  limit=(0, int(_ph * 0.15), _pw, int(_ph * 0.60)))
_tile_crop(["getupbwide_side_f%04d.png" % f for f in pf],
           ["f%d" % f for f in pf],
           os.path.join(P, "_d18_plant_zoom.png"), box, 200, 200, cols=6)

# ---- 6) 起身段长条（f20..f40，隔 2 帧）------------------------------------
rf = list(range(20, TOTAL + 1, 2))
box = _union_bbox(["getupbwide_side_f%04d.png" % f for f in rf])
_tile_crop(["getupbwide_side_f%04d.png" % f for f in rf],
           ["f%d" % f for f in rf],
           os.path.join(P, "_d18_rise.png"), box, 200, 200, cols=6)

print("MONTAGE_DONE")
