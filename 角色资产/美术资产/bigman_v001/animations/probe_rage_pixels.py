"""probe_rage_pixels —— E03 `Rage` 狂暴 的**像素级**验收（只读 PNG + 两个 json，不改工程）。

与 `probe_e01_pixels.py` / `probe_e02_pixels.py` 的关系
---------------------------------------------------------------
照抄其像素工具（`load` / `mask_of` / 行号口径 / `band_span` / 列心 / `strip_hem` /
`spread`），但**两条尺子的载体与机位全部换口径**。

★★★ 本支与 E01 / E02 的**根本差别**（三条，写在最前面）
---------------------------------------------------------------
(A) ★★★ **两个判据、两个机位**（E01 = 正面、E02 = 侧视，都是单机位）。
    E03 的两条尺子**几何朝向互相垂直**：
      · **捶胸**：双拳从两侧向**中线**收拢 ⟹ 横向 = 世界 **X** ⟹ **必须正面**。
        侧视会把「向中线收拢」压在视轴上（横轴变成世界 Y）—— 这正是
        E02 修正 ③ 的同一类陷阱（扰动方向必须落在**本支机位可见的那一维**）。
      · **仰头**：头在**矢状面**里向后倒 ⟹ 纵向 = 世界 **YZ** ⟹ **必须侧视**。
        正面只看得到下巴抬起，位移弱。
    ⟹ 本支**新立两条机位基准**（`VIEW_E03_SIDE` / `VIEW_E03_FRONT`，由
       本支几何算出），**不照抄** E01 / E02 的任何一条。

(B) ★★★ **捶胸的像素尺子不能拿「拳目标点」当期望值（自指量）**。
    与骨架级 ① 段同一个坑：拳目标点 `surf + nrm*TOUCH_OFF` 本身就是**由几何
    算出来的**，把「像素重心 ≈ 目标点」当判据，量的是一个**同一个公式的两个
    输出**，永远自洽 ⟹ 那个量不出错。
    ⟹ 本探针的期望值取 `chest_screen()` 输出的 **`handmesh_centroid_*`**
      = **真实手网格顶点的重心**（独立量：它由 `hand_mesh_vertices` 世界坐标
      投影而来，与「目标点」是两个不同来源）。判据 = 渲染层重心 ≈ 该重心
      （**一致性**：渲染确实画出了几何说的那个位置）。
    ★ 同时**单独登记**「重心 ↔ 目标点」的距离（不给判据，只给数字）——
      它是「拳有没有收进中线」的读数。

(C) ★★ **`Jacket_Hem` / `Jacket_Hem_Line` 是未蒙皮的静止薄片**（`probe_c11_belt`
    实测 `vgroups=0` / `parent=None`）⟹ 世界包围盒**与姿态无关**。本支躯干
    几乎不位移，但仰头/含胸会改变剪影 ⟹ **正面机位下它可能落进手部尺子所在
    的行带**，必须**算出**它与三条尺子的屏幕盒**不相交**，而不是「应该没事」。

判据清单
---------------------------------------------------------------
  `px_rage_pound_ok`              ★★★ 正面手层两侧重心 ≈ 几何投影的真实手网格重心
  `px_rage_pound_can_fail_ok`     ★★★ 反面 ②：`TP_CHESTFAR` 重渲必须红（本支命门）
  `px_rage_pound_symmetry_ok`     ★★ 两侧重心列关于中线镜像（双拳对称收拢）
  `px_rage_head_back_ok`          ★★★ 侧视头层重心**向后（+Y）**位移 ≥ 阈值
  `px_rage_head_back_can_fail_ok` ★★★ 反面 ④a：`TP_HEADDOWN` 重渲必须红
  `px_rage_foot_lock_ok`          ★★ 正面脚带左右缘 + 全剪影底缘行，hold 段不漂
  `px_rage_foot_lock_can_fail_ok` ★★ 反面 ⑥：`TP_FOOTSWAY` 重渲必须红
  `px_rage_hem_excluded_ok`       ★★ 衣摆屏幕盒与三条尺子盒**不相交**（算得）
  `px_rage_hem_stripped_ok`       ★★ 剔除**真的改变读数**（不是空操作）

用法
---------------------------------------------------------------
    blender --background --factory-startup --python probe_rage_pixels.py

前置（帧集合**逐帧相同**；`anim_rage.py` 非 `SKIP_RENDER` 跑一次即全部产出）：
  · 基线：`ragewide_{side,front}_f*`（全幅）、`ragehand_front_f*`（手层）、
          `ragehead_side_f*`（头层）、`_e03_chestscreen.json`；
  · 反面 ②：`E03_STEM_ONLY=1 E03_STEM=ragefar E03_STEM_HAND=ragefarhand
             E03_STEM_HEAD=ragefarhead E03_TP_CHESTFAR=1`；
  · 反面 ④a：同上前缀换成 `ragedown*` 并 `E03_TP_HEADDOWN=1`；
  · 反面 ⑥：同上前缀换成 `ragefoot*` 并 `E03_TP_FOOTSWAY=1`。
"""
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A        # noqa: E402
import anim_rage as R       # noqa: E402

PRE = A.PREVIEW_DIR

MAIN_FRONT = "ragewide_front"
HAND_FRONT = "ragehand_front"
MAIN_SIDE = "ragewide_side"
HEAD_SIDE = "ragehead_side"
STEM_HAND = "ragefarhand_front"       # 反面 ②：拳离开胸
STEM_HEAD = "ragedownhead_side"       # 反面 ④a：仰头不够
STEM_FOOT = "ragefoot_front"          # 反面 ⑥：脚滑

# ---- ★ 两条机位基准：**从 `anim_rage` 现算**，不另抄一份数字 ----------------
_F_NAME, _F_LOC, _F_TGT, _F_SCALE, _F_RES = R.VIEW_E03_FRONT
_S_NAME, _S_LOC, _S_TGT, _S_SCALE, _S_RES = R.VIEW_E03_SIDE

FRONT = {"res_x": _F_RES[0], "res_y": _F_RES[1], "ortho": _F_SCALE,
         "cam_z": _F_LOC[2], "mid_col": _F_RES[0] / 2.0}
SIDE = {"res_x": _S_RES[0], "res_y": _S_RES[1], "ortho": _S_SCALE,
        "cam_z": _S_LOC[2], "center_y_mm": _S_TGT[1] * 1000.0}

F_MMP = FRONT["ortho"] / float(FRONT["res_y"]) * 1000.0
F_FLOOR = (FRONT["ortho"] / 2.0 - FRONT["cam_z"]) / (FRONT["ortho"]
                                                     / float(FRONT["res_y"]))
S_MMP = SIDE["ortho"] / float(SIDE["res_y"]) * 1000.0
S_FLOOR = (SIDE["ortho"] / 2.0 - SIDE["cam_z"]) / (SIDE["ortho"]
                                                   / float(SIDE["res_y"]))


def f_row(z_mm):
    return F_FLOOR + z_mm / F_MMP


def f_col(x_mm):
    return FRONT["mid_col"] + x_mm / F_MMP


def s_row(z_mm):
    return S_FLOOR + z_mm / S_MMP


def s_col(y_mm):
    return SIDE["res_x"] / 2.0 + (y_mm - SIDE["center_y_mm"]) / S_MMP


# ---- ★ `Jacket_Hem` / `Jacket_Hem_Line` 世界包围盒（`probe_c11_belt` 实测
#      `C11_BELT_ACTION=Rage`；两件均 `vgroups=0` / `parent=None` ⟹ 逐帧恒定）
#      —— 本支**躯干几乎不位移**，所以这两个盒在两台机位里是**固定的屏幕矩形**。
HEM_WORLD_MM = {
    "Jacket_Hem": ((-125.5, -121.94, 903.0), (125.5, 129.03, 926.0)),
    "Jacket_Hem_Line": ((-123.0, -119.96, 897.5), (123.0, 126.03, 901.5)),
}

# ---- 尺子的世界区间（**不许写行号**，行号现算）-----------------------------
FOOT_Z_TOP_MM = float(os.environ.get("E03PX_FOOT_Z", "95.0"))

# ---- 阈值（**全部由实测导出**，见 `E03PX_REPORT`；铁律：不许为了变绿而放宽）----
POUND_TOL_PX = float(os.environ.get("E03PX_POUND_TOL", "55.0"))
POUND_CANFAIL_MIN_PX = float(os.environ.get("E03PX_POUND_CF", "90.0"))
SYM_TOL_PX = float(os.environ.get("E03PX_SYM_TOL", "25.0"))
HEAD_BACK_MIN_PX = float(os.environ.get("E03PX_HEAD_MIN", "12.0"))
HEAD_BACK_CANFAIL_MAX_PX = float(os.environ.get("E03PX_HEAD_CF", "6.0"))
FOOT_COL_TOL_PX = float(os.environ.get("E03PX_FOOT_COL", "2.0"))
SOLE_ROW_TOL_PX = float(os.environ.get("E03PX_SOLE_ROW", "1.5"))
HEM_SHIFT_MIN_PX = float(os.environ.get("E03PX_HEM_SHIFT", "0.05"))

STEM_FRAMES = list(R.STEM_FRAMES)
CONTACT = sorted(set(R.CONTACT))
POUND_FRAMES = [f for f in STEM_FRAMES if f in set(CONTACT)]
HOLD = sorted(set(list(range(R.HOLD_1[0], R.HOLD_1[1] + 1))
                  + list(range(R.HOLD_2[0], R.HOLD_2[1] + 1))))
HEAD_FRAMES = [R.START, R.ROAR]


# =============================================================== 像素工具
#   ★ 逐字照抄 `probe_e02_pixels.py`（其又照抄 E01 / D16~D19）
def load(stem, frame):
    path = os.path.join(PRE, "%s_f%04d.png" % (stem, frame))
    if not os.path.exists(path):
        return None
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32).reshape(height, width, 4)
    bpy.data.images.remove(image)
    return pixels


def mask_of(pixels):
    alpha = pixels[:, :, 3]
    if float(alpha.min()) < 0.5:
        return alpha > 0.5
    return pixels[:, :, :3].min(axis=2) < 0.92


def centroid(mask, c0=0, c1=None):
    c1 = mask.shape[1] - 1 if c1 is None else c1
    sub = mask[:, c0:c1 + 1]
    total = sub.sum()
    if total <= 0:
        return None
    rows = np.arange(mask.shape[0])
    cols = np.arange(c0, c1 + 1)
    return (float((rows * sub.sum(axis=1)).sum() / total),
            float((cols * sub.sum(axis=0)).sum() / total))


def band_span(mask, r0, r1):
    sub = mask[r0:r1 + 1]
    cols = np.where(sub.any(axis=0))[0]
    if cols.size == 0:
        return None, None
    return int(cols.min()), int(cols.max())


def bbox(mask):
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return None
    return (int(rows.min()), int(rows.max()),
            int(cols.min()), int(cols.max()))


def spread(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return float(max(vals) - min(vals))


def hem_screen_boxes():
    """衣摆两件在**两台机位**下的屏幕盒 (r0, r1, c0, c1)。"""
    out = {}
    for name, (lo, hi) in HEM_WORLD_MM.items():
        out[name + "@front"] = (int(np.floor(f_row(lo[2]))) - 1,
                                int(np.ceil(f_row(hi[2]))) + 1,
                                int(np.floor(f_col(lo[0]))) - 1,
                                int(np.ceil(f_col(hi[0]))) + 1)
        out[name + "@side"] = (int(np.floor(s_row(lo[2]))) - 1,
                               int(np.ceil(s_row(hi[2]))) + 1,
                               int(np.floor(s_col(lo[1]))) - 1,
                               int(np.ceil(s_col(hi[1]))) + 1)
    return out


def strip_hem(mask, prefix):
    out = mask.copy()
    for name, (r0, r1, c0, c1) in hem_screen_boxes().items():
        if not name.endswith(prefix):
            continue
        rr0, rr1 = max(r0, 0), min(r1, mask.shape[0] - 1)
        cc0, cc1 = max(c0, 0), min(c1, mask.shape[1] - 1)
        if rr1 >= rr0 and cc1 >= cc0:
            out[rr0:rr1 + 1, cc0:cc1 + 1] = False
    return out


# =============================================================== 主流程
def main():  # noqa: C901
    res = {}
    res["probe"] = "probe_rage_pixels"
    res["anim"] = "Rage"
    res["views"] = {
        "front": {"res": list(_F_RES), "ortho_m": _F_SCALE,
                  "cam_z_m": _F_LOC[2], "mm_per_px": round(F_MMP, 7),
                  "floor_row": round(F_FLOOR, 4)},
        "side": {"res": list(_S_RES), "ortho_m": _S_SCALE,
                 "cam_z_m": _S_LOC[2], "center_y_mm": SIDE["center_y_mm"],
                 "mm_per_px": round(S_MMP, 7), "floor_row": round(S_FLOOR, 4)},
    }
    res["row_ruler"] = (
        "行号自画面底向上。**front**（横轴 = 世界 X）：z_mm = (row − %.4f) x "
        "%.7f；col = %.1f + x_mm / %.7f。**side**（横轴 = 世界 Y）：z_mm = "
        "(row − %.4f) x %.7f；col = %.1f + (y_mm − %.1f) / %.7f；**图像右 = +Y "
        "= 身后**（角色朝 −Y）。"
        % (F_FLOOR, F_MMP, FRONT["mid_col"], F_MMP,
           S_FLOOR, S_MMP, SIDE["res_x"] / 2.0, SIDE["center_y_mm"], S_MMP))
    res["pound_frames"] = POUND_FRAMES
    res["hold_frames"] = HOLD
    res["head_frames"] = HEAD_FRAMES
    res["hem_screen_boxes"] = {k: list(v) for k, v in
                               hem_screen_boxes().items()}

    # ---- ① 捶胸（正面手层）------------------------------------------------
    hand_json = {}
    path = os.path.join(PRE, "_e03_chestscreen.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            hand_json = json.load(handle)
    res["chestscreen_loaded"] = bool(hand_json)
    expected = hand_json.get("rows", {}) if hand_json else {}

    rows = {}
    for frame in POUND_FRAMES:
        pixels = load(HAND_FRONT, frame)
        if pixels is None:
            continue
        mask = mask_of(pixels)
        row = {}
        for side in ("L", "R"):
            c0 = int(FRONT["mid_col"]) if side == "L" else 0
            c1 = FRONT["res_x"] - 1 if side == "L" else int(FRONT["mid_col"])
            cen = centroid(mask, c0, c1)
            exp = expected.get(str(frame), {}).get(side)
            row[side] = {
                "measured_row": None if cen is None else round(cen[0], 2),
                "measured_col": None if cen is None else round(cen[1], 2),
                "geom_row": None if exp is None else exp[2],
                "geom_col": None if exp is None else exp[3],
                "target_row": None if exp is None else exp[0],
                "target_col": None if exp is None else exp[1],
            }
            if cen is not None and exp is not None:
                row[side]["d_px"] = round(float(np.hypot(cen[0] - exp[2],
                                                         cen[1] - exp[3])), 2)
                row[side]["d_to_target_px"] = round(
                    float(np.hypot(cen[0] - exp[0], cen[1] - exp[1])), 2)
        rows[str(frame)] = row
    res["pound_detail"] = rows

    worst_d, worst_d_at = 0.0, None
    worst_sym, worst_sym_at = 0.0, None
    for frame in POUND_FRAMES:
        row = rows.get(str(frame))
        if not row:
            continue
        for side in ("L", "R"):
            d = row[side].get("d_px")
            if d is not None and d > worst_d:
                worst_d, worst_d_at = d, (frame, side)
        cl = row["L"].get("measured_col")
        cr = row["R"].get("measured_col")
        if cl is not None and cr is not None:
            sym = abs(cl - (2.0 * FRONT["mid_col"] - cr))
            if sym > worst_sym:
                worst_sym, worst_sym_at = sym, frame
    res["px_rage_pound_worst_px"] = round(worst_d, 2)
    res["px_rage_pound_worst_at"] = worst_d_at
    res["px_rage_pound_symmetry_worst_px"] = round(worst_sym, 2)
    res["px_rage_pound_symmetry_worst_at"] = worst_sym_at
    res["px_rage_pound_ok"] = bool(nan_guard(worst_d) <= POUND_TOL_PX
                                   and worst_d_at is not None)
    res["px_rage_pound_symmetry_ok"] = bool(
        worst_sym <= SYM_TOL_PX and worst_sym_at is not None)

    # ---- 反面 ②：拳离开胸 -------------------------------------------------
    far = {}
    for frame in POUND_FRAMES:
        pixels = load(STEM_HAND, frame)
        base = load(HAND_FRONT, frame)
        if pixels is None or base is None:
            continue
        fmask, bmask = mask_of(pixels), mask_of(base)
        row = {}
        for side in ("L", "R"):
            c0 = int(FRONT["mid_col"]) if side == "L" else 0
            c1 = FRONT["res_x"] - 1 if side == "L" else int(FRONT["mid_col"])
            fa, ba = centroid(fmask, c0, c1), centroid(bmask, c0, c1)
            if fa is None or ba is None:
                continue
            row[side] = round(float(np.hypot(fa[0] - ba[0],
                                             fa[1] - ba[1])), 2)
        far[str(frame)] = row
    res["px_rage_pound_canfail_detail"] = far
    shift = max([v for row in far.values() for v in row.values()] or [0.0])
    res["px_rage_pound_canfail_max_px"] = round(max(shift, 0.0), 2)
    res["px_rage_pound_can_fail_ok"] = bool(shift >= POUND_CANFAIL_MIN_PX)

    # ---- ② 仰头（侧视头层）------------------------------------------------
    head = {}
    for frame in HEAD_FRAMES:
        pixels = load(HEAD_SIDE, frame)
        if pixels is None:
            continue
        cen = centroid(mask_of(pixels))
        head[str(frame)] = None if cen is None else [round(cen[0], 2),
                                                     round(cen[1], 2)]
    res["px_rage_head_detail"] = head
    base_head = head.get(str(R.START))
    roar_head = head.get(str(R.ROAR))
    back_px = (None if base_head is None or roar_head is None
               else round(roar_head[1] - base_head[1], 2))
    res["px_rage_head_back_px"] = back_px
    res["px_rage_head_back_ok"] = bool(back_px is not None
                                       and back_px >= HEAD_BACK_MIN_PX)

    down = {}
    for frame in HEAD_FRAMES:
        pixels = load(STEM_HEAD, frame)
        if pixels is None:
            continue
        cen = centroid(mask_of(pixels))
        down[str(frame)] = None if cen is None else [round(cen[0], 2),
                                                     round(cen[1], 2)]
    res["px_rage_head_canfail_detail"] = down
    d_base = down.get(str(R.START))
    d_roar = down.get(str(R.ROAR))
    down_px = (None if d_base is None or d_roar is None
               else round(d_roar[1] - d_base[1], 2))
    res["px_rage_head_canfail_px"] = down_px
    res["px_rage_head_back_can_fail_ok"] = bool(
        down_px is not None and down_px <= HEAD_BACK_CANFAIL_MAX_PX)

    # ---- ③ 脚不动（正面）--------------------------------------------------
    foot_r0, foot_r1 = (int(np.floor(f_row(0.0))),
                        int(np.ceil(f_row(FOOT_Z_TOP_MM))))
    cols, soles, mans = [], [], []
    for frame in HOLD + [R.START, R.END]:
        pixels = load(MAIN_FRONT, frame)
        if pixels is None:
            continue
        mask = strip_hem(mask_of(pixels), "@front")
        lo, hi = band_span(mask, max(foot_r0, 0),
                           min(foot_r1, FRONT["res_y"] - 1))
        if lo is None:
            continue
        cols.append(hi - lo)
        rows = np.where(mask.any(axis=1))[0]
        soles.append(int(rows.min()) if rows.size else None)
        box = bbox(mask)
        mans.append(None if box is None else box[2])
    res["px_rage_foot_band_rows"] = [foot_r0, foot_r1]
    res["px_rage_foot_col_spread_px"] = round(spread(cols) or 0.0, 2)
    res["px_rage_foot_sole_spread_px"] = round(spread(soles) or 0.0, 2)
    res["px_rage_foot_cols"] = cols
    res["px_rage_foot_soles"] = soles
    res["px_rage_foot_lock_ok"] = bool(
        cols and (spread(cols) or 0.0) <= FOOT_COL_TOL_PX
        and (spread(soles) or 0.0) <= SOLE_ROW_TOL_PX)

    sway_cols, sway_sole = [], []
    for frame in HOLD:
        pixels = load(STEM_FOOT, frame)
        if pixels is None:
            continue
        mask = strip_hem(mask_of(pixels), "@front")
        lo, hi = band_span(mask, max(foot_r0, 0),
                           min(foot_r1, FRONT["res_y"] - 1))
        if lo is None:
            continue
        sway_cols.append(hi - lo)
        rows = np.where(mask.any(axis=1))[0]
        sway_sole.append(int(rows.min()) if rows.size else None)
    sway = max(spread(sway_cols) or 0.0, spread(sway_sole) or 0.0)
    res["px_rage_foot_canfail_spread_px"] = round(sway, 2)
    res["px_rage_foot_lock_can_fail_ok"] = bool(
        sway > max(FOOT_COL_TOL_PX, SOLE_ROW_TOL_PX))

    # ---- ④ 衣摆：与尺子盒不相交 + 剔除真的改变读数 -------------------------
    boxes = hem_screen_boxes()
    rulers = {
        "pound_front": (int(np.floor(f_row(1150.0))), int(np.ceil(f_row(1350.0))),
                        int(np.floor(f_col(-260.0))), int(np.ceil(f_col(260.0)))),
        "foot_front": (max(foot_r0, 0), min(foot_r1, FRONT["res_y"] - 1),
                       0, FRONT["res_x"] - 1),
        "head_side": (int(np.floor(s_row(1450.0))),
                      int(np.ceil(s_row(1830.0))),
                      int(np.floor(s_col(-260.0))), int(np.ceil(s_col(260.0)))),
    }
    overlap = {}
    for key, (r0, r1, c0, c1) in rulers.items():
        suffix = "@side" if key.endswith("side") else "@front"
        for name, (hr0, hr1, hc0, hc1) in boxes.items():
            if not name.endswith(suffix):
                continue
            hit = (min(r1, hr1) >= max(r0, hr0)
                   and min(c1, hc1) >= max(c0, hc0))
            if hit:
                overlap[name + " vs " + key] = True
    res["px_rage_hem_rulers"] = {k: list(v) for k, v in rulers.items()}
    res["px_rage_hem_overlaps"] = overlap
    res["px_rage_hem_excluded_ok"] = not overlap

    strip_delta = 0
    for frame in HOLD:
        pixels = load(MAIN_FRONT, frame)
        if pixels is None:
            continue
        raw = mask_of(pixels)
        cut = strip_hem(raw, "@front")
        strip_delta += int(raw.sum() - cut.sum())
    res["px_rage_hem_strip_delta_px"] = strip_delta
    res["px_rage_hem_stripped_ok"] = bool(strip_delta > 0)

    failed = sorted(k for k, v in res.items()
                    if k.startswith("px_") and k.endswith("_ok") and v is not True)
    res["failed"] = failed
    A.report("E03PX_REPORT", res)


def nan_guard(value):
    return 1e9 if value is None else value


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E03PX_FAILURE " + traceback.format_exc())
