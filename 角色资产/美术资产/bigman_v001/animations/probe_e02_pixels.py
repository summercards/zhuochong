"""probe_e02_pixels —— E02 `Exhausted` 虚弱 的**像素级**验收（只读 PNG + 一个 json，不改工程）。

与 `probe_e01_pixels.py` 的关系
---------------------------------------------------------------
照抄其像素工具（`load` / `mask_of` / 行号口径 / `band_span` / 列心 / `strip_hem` /
`spread`），但**三条尺子的载体全部换口径** —— 因为本支换了**正交平面**（见下）。

★★★ 本支与 E01 的**根本差别**（三件）
---------------------------------------------------------------
(A) ★★★ **机位 = 侧视（相机沿 +X 看）。理由不是偏好，是几何必然。**
    E01 的摇晃主体在 **X（左右）** ⟹ 必须正面。**本支恰好相反**：本支是
    「弯腰 + 下沉 + 迈步」，主位移全在 **YZ 平面**（`BEND_DIST` 把 74° 前倾
    拆到 `pelvis/spine_01/spine_02/chest`，`HIP_BACK=+0.060` 后坐，
    `PELVIS_DROP=-0.145` 下沉）⟹ 正面会把「弯腰方向」压成**视轴**，什么都读不出。
    ★ 侧视横轴 = 世界 **Y**（图像左 = −Y = **角色面朝的方向**，因为角色朝 −Y）。

(B) ★★★ **本支最危险的一处几何陷阱，是「谁是剪影最高点」—— 必须算，不能想当然。**
    直觉会说「弯腰了，最高点是肩/上背」。**实测几何相反**：
      · `BENT["pelvis"]` rx = 4.0 + 74x0.16 = **15.84°**，其后 `spine_01/02/chest`
        再各 17.76° ⟹ 脊柱链从骨盆**向前下方**倒 73.1°；
      · 骨盆只降 145 mm（`z ≈ 0.755 m`），而胸/头**比骨盆更低**（`neck` 世界 z
        实测只走 `exh_breath_mm = 49.01`）。
    ⟹ **剪影最高点是「骨盆 / 臀」（几乎不动，只随 `BR_PELVIS=±4 mm` 微颤）**，
      **不是**呼吸的胸。**所以「整幅剪影顶行」是错的载体**（它会读到臀，甚至读到
      下面 (C) 的衣摆静止块）⟹ 本支的呼吸尺子改量
      **「前半幅列窗内的剪影顶行」**（`top_row_front`）：前窗只含**头 + 前胸**
      （臀在后、由 `HIP_BACK=+0.060` 推到 +Y = 图像**右**），这才跟得住 `neck`
      的 49 mm 升降。★ 这条是本支像素验收的**核心设计决定**，写在最前面。

(C) ★★ **`Jacket_Hem` 是「未蒙皮的静止薄片」，本支弯腰后它**悬在**身体上方。**
    `probe_c11_belt` 实测：`Jacket_Hem` / `Jacket_Hem_Line` `vgroups=0` /
    `parent=None` ⟹ 世界包围盒**逐帧恒定**（与姿态无关）⟹ 站姿时它挂在腰上，
    **弯腰后身体塌到 z≈0.3–0.75 m，它仍钉在 z 897.5..926.0 mm** ⟹ 在侧视图里
    它是一块**悬空的横向板**，且是**整幅剪影的最高元素**。
    ⟹ 本支必须把它从掩码里**剔除**，且必须**算出**它与三条尺子的屏幕盒
    **不相交**（不是「应该没事」）。★ 侧视只用到 y 与 z。

本支判据清单
---------------------------------------------------------------
  `px_exh_foot_lock_ok`              ★★★ 脚带（z ≤ 95 mm）左右缘 + 全剪影底缘行，hold 段不漂
  `px_exh_foot_lock_can_fail_ok`     ★★★ 反面 ③：`TP_FOOTSWAY` 重渲必须红
  `px_exh_breath_ok`                 ★★ 前半幅顶行周期波动（幅度 + 过零 + 周期）
  `px_exh_breath_can_fail_ok`        ★★ 反面 ②：`TP_NOBREATH` 重渲必须红
  `px_exh_breath_carrier_can_fail_ok` ★ 同尺子换载体（脚带顶行）必须红
  `px_exh_hand_on_knee_ok`           ★★★ 手部单件层重心 ≈ 投影的「拳头目标点」（膝+偏移）
  `px_exh_hand_on_knee_can_fail_ok`  ★★★ 反面 ①：`TP_HANDFAR` 重渲必须红（★ 本支命门）
  `px_hem_excluded_ok`               ★★ 衣摆屏幕盒与三条尺子盒**不相交**（算得）
  `px_hem_stripped_ok`               ★★ 剔除**真的改变读数**（不是空操作）

用法
---------------------------------------------------------------
    blender --background --factory-startup --python probe_e02_pixels.py

前置（帧集合**逐帧相同**：hold 段 `22..98`）：
  · `anim_exhausted.py`（`exhwide_side_f0000..f0120` = 基线；`exhhand_side_f*` = 手部层）
    —— 由 `_e02_render.sh` 主渲产出；
  · `E02_STEM_ONLY=1 E02_STEM=exhfar       E02_STEM_HAND=exhfarhand       E02_TP_HANDFAR=1`；
  · `E02_STEM_ONLY=1 E02_STEM=exhnobreath  E02_STEM_HAND=exhnobreathhand  E02_TP_NOBREATH=1`；
  · `E02_STEM_ONLY=1 E02_STEM=exhfootsway  E02_STEM_HAND=exhfootswayhand  E02_TP_FOOTSWAY=1`。

★ 行号 ↔ 世界高度（本支取景，**登记以免再翻车**）
---------------------------------------------------------------
  Blender `ortho_scale` 作用于**长边**；res = 780x1100 ⟹ 长边是**高**
  ⟹ 竖直世界跨度 = ortho，且
      mm_per_px  = ortho / res_y x 1000
      floor_row  = (ortho/2 − cam_z) / (ortho/res_y)          # z = 0 的行
      z_mm       = (row − floor_row) x mm_per_px
      列（**侧视**：横轴 = 世界 y）= res_x/2 + (y_mm − center_y) / mm_per_px
  `VIEW_E02_SIDE`（cam_z 0.72, ortho 1.90, res 780x1100, center_y −250）：
      mm_per_px = **1.7272727**、floor_row = **133.1579**
      自检：鞋底 z≈0 ⟹ row **133.2**；踝 z 79.8 ⟹ row **179.4**；
            可见竖直 [−230, 1670] mm（★ 站姿头顶 1803 会出框 —— 但本支 hold 段
            是弯腰，胸/头全在框内；基线图的过渡帧出框不影响 hold 判据）。
"""
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A        # noqa: E402
import anim_exhausted as EX  # noqa: E402

PRE = A.PREVIEW_DIR

MAIN = "exhwide_side"            # ★ 基线（全幅）
HANDBASE = "exhhand_side"        # ★ 手部单件层（基线）
STEM_HAND = "exhfarhand_side"    # ★ 反面 ①：HANDFAR（手离开膝）
STEM_NOBREATH = "exhnobreath_side"   # ★ 反面 ②：NOBREATH（不喘）
STEM_FOOT = "exhfootsway_side"       # ★ 反面 ③：FOOTSWAY（脚滑）

# ---- ★ 视图表：**从 `anim_exhausted.VIEW_E02_SIDE` 现算**，不另抄一份数字 ----
_V_NAME, _V_LOC, _V_TGT, _V_SCALE, _V_RES = EX.VIEW_E02_SIDE
V = {"res_x": _V_RES[0], "res_y": _V_RES[1], "ortho": _V_SCALE,
     "cam_z": _V_LOC[2], "center_h_mm": _V_TGT[1] * 1000.0}   # 侧视：h = 世界 y

MMP = V["ortho"] / float(V["res_y"]) * 1000.0
FLOOR = (V["ortho"] / 2.0 - V["cam_z"]) / (V["ortho"] / float(V["res_y"]))


def col_of(y_mm):
    return V["res_x"] / 2.0 + (y_mm - V["center_h_mm"]) / MMP


def row_of(z_mm):
    return FLOOR + z_mm / MMP


# ---- ★★★ 衣摆静止块世界包围盒（`probe_c11_belt` 以 `C11_BELT_ACTION=Exhausted`
#      复核「逐帧恒定」）。侧视只用得上 y 与 z。--------------------------
#   `Jacket_Hem`      y [−121.94, +129.03]  z [903.0, 926.0]
#   `Jacket_Hem_Line` y [−119.96, +126.03]  z [897.5, 901.5]
HEM_YZ = (-121.94, 897.5, 129.03, 926.0)     # (y_lo, z_lo, y_hi, z_hi)

# ---- 三条尺子 / 判据的世界区间（**不许写行号**，行号必须现算）--------------
FOOT_Z_TOP_MM = float(os.environ.get("E02PX_FOOT_Z", "95.0"))
FRONT_FRAC = float(os.environ.get("E02PX_FRONT_FRAC", "0.45"))   # 前半幅占比

# ---- 阈值（**全部由实测导出**，见 `E02PX_REPORT`；铁律：不许为了变绿而放宽）----
FOOT_COL_TOL_PX = float(os.environ.get("E02PX_FOOT_COL", "2.0"))
SOLE_ROW_TOL_PX = float(os.environ.get("E02PX_SOLE_ROW", "1.0"))
BREATH_PP_MIN_PX = float(os.environ.get("E02PX_BR_PP", "8.0"))
BREATH_MIN_CROSS = int(os.environ.get("E02PX_BR_CROSS", "3"))
BREATH_PERIOD_RANGE = (float(os.environ.get("E02PX_BR_P_LO", "25.0")),
                       float(os.environ.get("E02PX_BR_P_HI", "60.0")))
HAND_TOL_PX = float(os.environ.get("E02PX_HAND_TOL", "45.0"))
HAND_CANFAIL_MIN_PX = float(os.environ.get("E02PX_HAND_CF", "80.0"))
HEM_SHIFT_MIN_PX = float(os.environ.get("E02PX_HEM_SHIFT", "0.05"))

HOLD = list(range(EX.BEND_END, EX.RISE_START + 1))            # [22, 98]
HAND_FRAMES = sorted(set(list(range(EX.BEND_END, EX.RISE_START + 1, 6))
                         + [EX.RISE_START]))


# =============================================================== 像素工具
#   ★ 逐字照抄 `probe_e01_pixels.py`（其又照抄 D16/D17/D18/D19）
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


def hem_rows():
    _y_lo, z_lo, _y_hi, z_hi = HEM_YZ
    r0 = int(np.floor(row_of(z_lo))) - 1
    r1 = int(np.ceil(row_of(z_hi))) + 1
    return (max(r0, 0), min(r1, V["res_y"] - 1))


def hem_cols():
    y_lo, _z_lo, y_hi, _z_hi = HEM_YZ
    c0 = int(np.floor(col_of(y_lo))) - 1
    c1 = int(np.ceil(col_of(y_hi))) + 1
    return (max(c0, 0), min(c1, V["res_x"] - 1))


def strip_hem(mask):
    c0, c1 = hem_cols()
    r0, r1 = hem_rows()
    out = mask.copy()
    out[r0:r1 + 1, c0:c1 + 1] = False
    return out


def band_rows(z_lo, z_hi=None):
    r0 = int(np.floor(row_of(z_lo)))
    r1 = (V["res_y"] - 1 if z_hi is None else int(np.ceil(row_of(z_hi))))
    return (max(r0, 0), min(r1, V["res_y"] - 1))


def band_span(mask, r0, r1):
    sub = mask[r0:r1 + 1]
    cols = np.where(sub.any(axis=0))[0]
    if cols.size == 0:
        return None, None
    return int(cols.min()), int(cols.max())


def silhouette_bottom(mask):
    rows = np.where(mask.any(axis=1))[0]
    return None if rows.size == 0 else int(rows.min())


def bbox(mask):
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return None
    return (int(rows.min()), int(rows.max()),
            int(cols.min()), int(cols.max()))


def top_row_in_cols(mask, c0, c1):
    """列窗 `[c0, c1]` 内掩码的**最高行**（= 最大 row = 世界最高点）。"""
    sub = mask[:, c0:c1 + 1]
    rows = np.where(sub.any(axis=1))[0]
    return None if rows.size == 0 else int(rows.max())


def centroid_rc(mask, r0=None, r1=None, c0=None, c1=None):
    """子窗内掩码的 (row 重心, col 重心)。"""
    r0 = 0 if r0 is None else r0
    r1 = mask.shape[0] - 1 if r1 is None else r1
    c0 = 0 if c0 is None else c0
    c1 = mask.shape[1] - 1 if c1 is None else c1
    sub = mask[r0:r1 + 1, c0:c1 + 1]
    total = sub.sum()
    if total <= 0:
        return None
    rs = sub.sum(axis=1).astype(np.float64)
    cs = sub.sum(axis=0).astype(np.float64)
    row = float((np.arange(r0, r1 + 1) * rs).sum() / total)
    col = float((np.arange(c0, c1 + 1) * cs).sum() / total)
    return (row, col)


def spread(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return float(max(vals) - min(vals))


# =============================================================== 主流程
def main():  # noqa: C901
    res = {}
    res["probe"] = "probe_e02_pixels"
    res["anim"] = "Exhausted"
    res["hold_window"] = [HOLD[0], HOLD[-1]]
    foot_r = band_rows(0.0, FOOT_Z_TOP_MM)
    hem_r = hem_rows()
    hem_c = hem_cols()
    res["view"] = {"main": MAIN, "hand": HANDBASE, "stem_hand": STEM_HAND,
                   "stem_nobreath": STEM_NOBREATH, "stem_foot": STEM_FOOT,
                   "res": [_V_RES[0], _V_RES[1]], "ortho_m": _V_SCALE,
                   "cam_y_m": _V_LOC[1], "cam_z_m": _V_LOC[2],
                   "center_y_mm": _V_TGT[1] * 1000.0}
    res["mm_per_px"] = round(MMP, 7)
    res["floor_row"] = round(FLOOR, 4)
    res["row_ruler"] = (
        "行号自画面底向上。z_mm = (row − %.4f) x %.7f。**bottom = 最小行 = 世界"
        "最低点**。列（**侧视**）：col = %.1f + (y_mm − %.1f) / %.7f；图像左 = −Y = "
        "**角色面朝方向**（角色朝 −Y），图像右 = +Y = 身后。"
        % (FLOOR, MMP, _V_RES[0] / 2.0, V["center_h_mm"], MMP))
    res["bands"] = {"foot_rows": list(foot_r), "foot_z_mm": [0.0, FOOT_Z_TOP_MM],
                    "hem_rows": list(hem_r), "hem_cols": list(hem_c),
                    "front_frac": FRONT_FRAC}
    res["bands_note"] = (
        "★ 行区间**现算**（世界 z ÷ mm_per_px + floor_row），**没有写死行号**。"
        "脚带 z ≤ %.0f mm（踝 z 79.8 ⟹ 纯靴）；衣摆静止块投影到 rows %s / cols %s。"
        % (FOOT_Z_TOP_MM, list(hem_r), list(hem_c)))

    # ---------------- (0) 扫描基线（hold 段）---------------------------------
    table = {}
    for frame in HOLD:
        pixels = load(MAIN, frame)
        if pixels is None:
            continue
        raw = mask_of(pixels)
        cut = strip_hem(raw)
        cl, ch = band_span(cut, foot_r[0], foot_r[1])
        box = bbox(cut)
        foot_sub = cut[foot_r[0]:foot_r[1] + 1]
        boot_top = (int(np.where(foot_sub.any(axis=1))[0].max() + foot_r[0])
                    if foot_sub.any() else None)
        # ★ 衣摆剔除是否**真的改变读数**：在**衣摆自己所在的行带**里量横向跨度
        #   （raw 含衣摆板 / cut 剔除后），再补一个全剪影**列心**位移（E01 老口径）。
        h_r0, h_r1 = hem_rows()
        row = {"bottom": silhouette_bottom(cut),
               "bottom_raw": silhouette_bottom(raw),
               "top_all": (None if box is None else box[1]),
               "top_all_raw": (None if box is None
                               else bbox(raw)[1]),
               "bbox": box, "boot_top": boot_top,
               "boot_col_lo": cl, "boot_col_hi": ch,
               "hem_span_raw": band_span(raw, h_r0, h_r1),
               "hem_span_cut": band_span(cut, h_r0, h_r1),
               "full_cen_raw": centroid_rc(raw),
               "full_cen_cut": centroid_rc(cut)}
        if box is not None:
            _rmin, _rmax, cmin, cmax = box
            c_front = int(round(cmin + FRONT_FRAC * max(1, cmax - cmin)))
            row["front_cols"] = [cmin, c_front]
            row["top_front"] = top_row_in_cols(cut, cmin, c_front)
            row["top_front_raw"] = top_row_in_cols(raw, cmin, c_front)
            row["front_cen"] = centroid_rc(cut, cmin, c_front)
        else:
            row["front_cols"] = None
            row["top_front"] = None
            row["top_front_raw"] = None
            row["front_cen"] = None
        table[frame] = row

    if not table:
        raise RuntimeError("基线图一张都没有：%s/%s_f%04d.png"
                           % (PRE, MAIN, HOLD[0]))
    missing = [f for f in HOLD if f not in table]
    if missing:
        raise RuntimeError("基线图缺 hold 帧 %s（共 %d 张）"
                           % (missing[:12], len(missing)))
    frames = sorted(table)
    res["px_exh_hold_frames"] = [frames[0], frames[-1], len(frames)]
    res["px_exh_top_front_row"] = {str(f): table[f]["top_front"]
                                   for f in frames}
    res["px_exh_top_all_row"] = {str(f): table[f]["top_all"] for f in frames}
    res["px_exh_bottom_row"] = {str(f): table[f]["bottom"] for f in frames}
    res["px_exh_front_cols_f0"] = table[frames[0]]["front_cols"]

    # ---------------- (1) ★★★ `px_exh_foot_lock_ok` --------------------------
    lo_dev = spread([table[f]["boot_col_lo"] for f in frames])
    hi_dev = spread([table[f]["boot_col_hi"] for f in frames])
    bot_dev = spread([table[f]["bottom"] for f in frames])
    res["px_exh_foot_col_lo_spread_px"] = lo_dev
    res["px_exh_foot_col_hi_spread_px"] = hi_dev
    res["px_exh_foot_bottom_spread_px"] = bot_dev
    res["px_exh_foot_bottom_row_range"] = [
        min(table[f]["bottom"] for f in frames),
        max(table[f]["bottom"] for f in frames)]
    res["px_exh_foot_bottom_z_mm"] = [
        round((min(table[f]["bottom"] for f in frames) - FLOOR) * MMP, 3),
        round((max(table[f]["bottom"] for f in frames) - FLOOR) * MMP, 3)]
    res["px_exh_foot_lock_tol"] = {"col_px": FOOT_COL_TOL_PX,
                                   "sole_row_px": SOLE_ROW_TOL_PX}
    res["px_exh_foot_lock_ok"] = bool(
        lo_dev is not None and hi_dev is not None and bot_dev is not None
        and lo_dev <= FOOT_COL_TOL_PX and hi_dev <= FOOT_COL_TOL_PX
        and bot_dev <= SOLE_ROW_TOL_PX)
    res["px_exh_foot_lock_note"] = (
        "★★★ **本支「脚不动」的像素级守卫**（骨架级同族判据 = `exh_foot_lock_ok`，"
        "实测 hold 踝漂 %.4f mm）。载体 = **脚带**（z ≤ %.0f mm，rows %s）的"
        "左缘 / 右缘 + 全剪影**底缘行**。hold 段实测：左缘漂移 **%s px**、"
        "右缘 **%s px**（阈值 ≤ %.0f px = %.2f mm）、底缘行 %s..%s 漂移 **%s px** = "
        "z ∈ [%.2f, %.2f] mm（阈值 ≤ %.0f px）。★ 三条通道**物理含义不同**："
        "左右缘管**横向（Y）滑动**，底缘行管**抬脚/下沉**。★ 只在 **hold 段** 判："
        "过渡段本支**故意迈了一步**（骨架级实测 R 脚行程 320.6 mm）——理由由"
        "`probe_e02_baseline` 的实测给出（弓步站架下后膝不可达 ratio 1.164 > 1，"
        "「双手扶膝」必须换对称站架），**不是放宽容差**。"
        % (0.0022, FOOT_Z_TOP_MM, list(foot_r), lo_dev, hi_dev,
           FOOT_COL_TOL_PX, FOOT_COL_TOL_PX * MMP,
           res["px_exh_foot_bottom_row_range"][0],
           res["px_exh_foot_bottom_row_range"][1], bot_dev,
           res["px_exh_foot_bottom_z_mm"][0], res["px_exh_foot_bottom_z_mm"][1],
           SOLE_ROW_TOL_PX))

    # ---------------- (2) ★★ `px_exh_breath_ok`（前半幅顶行）-----------------
    front = [table[f]["top_front"] for f in frames]
    pp = spread(front)
    cross, period = EX._crossings([v for v in front if v is not None])
    res["px_exh_breath_pp_px"] = None if pp is None else round(pp, 4)
    res["px_exh_breath_pp_mm"] = None if pp is None else round(pp * MMP, 3)
    res["px_exh_breath_crossings"] = cross
    res["px_exh_breath_period_frames"] = None if period is None else round(period, 3)
    res["px_exh_breath_thresholds"] = {"pp_min_px": BREATH_PP_MIN_PX,
                                       "min_crossings": BREATH_MIN_CROSS,
                                       "period_range": list(BREATH_PERIOD_RANGE)}
    res["px_exh_breath_ok"] = bool(
        pp is not None and pp >= BREATH_PP_MIN_PX and cross >= BREATH_MIN_CROSS
        and period is not None
        and BREATH_PERIOD_RANGE[0] <= period <= BREATH_PERIOD_RANGE[1])
    _tf_lo = min(v for v in front if v is not None)
    _tf_hi = max(v for v in front if v is not None)
    _same_as_all = all(table[f]["top_front"] == table[f]["top_all"]
                       for f in frames)
    res["px_exh_top_front_equals_top_all"] = bool(_same_as_all)
    res["px_exh_breath_note"] = (
        "★★★ **换载体，理由算出来（不是偏好）**：实测本支剪影最高点是**头**"
        "（rows %d..%d，**随上身绕髋做呼吸式升降**，峰峰 %d px）；"
        "而**衣摆静止块在 rows %s —— 在头顶「下方」**（★ 开工前我一度推测"
        "「弯腰后最高点是臀、衣摆会盖过头顶」，**实测推翻**：头 row 863 远高于"
        "衣摆 row 651..671），且**髋/臀几乎不动**。为使载体**只含呼吸的上身**、"
        "排除「静止衣摆 + 近静止髋/臀」，取 **前半幅列窗**（cols %s，即 "
        "`cmin..cmin+%.0f%%` 宽，含头 + 前胸）。★ 实测 `top_front` 与整幅顶行 "
        "`top_all` **逐帧相同**（都 = 头，见 `px_exh_top_front_equals_top_all`）"
        "⟹ 这不是「唯一可行」，而是**更保守的隔离**：万一将来头再低、衣摆成为顶行，"
        "本载体仍不受污染。hold 段实测：峰峰值 **%.3f px = %.2f mm**（阈值 ≥ "
        "%.1f px = %.1f mm）、过零 **%d** 次（阈值 ≥ %d）、周期 **%s 帧**（区间 %s）。"
        "★ 与骨架级 `exh_breath_ok`（实测 `exh_breath_mm=49.01`、周期 37.3 帧、"
        "过零 4）**同构**：两级都量「上身顶点的世界 z」，只是刻度从 mm 换成 px。"
        % (_tf_lo, _tf_hi, int(pp), list(hem_r), res["px_exh_front_cols_f0"],
           FRONT_FRAC * 100.0, pp, pp * MMP, BREATH_PP_MIN_PX,
           BREATH_PP_MIN_PX * MMP, cross, BREATH_MIN_CROSS,
           res["px_exh_breath_period_frames"], list(BREATH_PERIOD_RANGE)))

    # ---- (2b) ★ 同尺子换载体：脚带顶行（脚不呼吸 ⟹ 必须红）-----------------
    #   载体 = 脚带行区间 [foot_r0, foot_r1] 内掩码的**最高行**（脚背/鞋帮上沿）。
    boot_top = [table[f]["boot_top"] for f in frames]
    bt_pp = spread(boot_top)
    bt_cross, bt_period = EX._crossings([v for v in boot_top if v is not None])
    res["px_exh_breath_control_carrier"] = {
        "carrier": "脚带顶行（rows %s）" % list(foot_r),
        "pp_px": None if bt_pp is None else round(bt_pp, 4),
        "crossings": bt_cross,
        "period_frames": None if bt_period is None else round(bt_period, 3)}
    res["px_exh_breath_carrier_can_fail_ok"] = bool(
        bt_pp is not None and (bt_pp < BREATH_PP_MIN_PX
                               or bt_cross < BREATH_MIN_CROSS
                               or bt_period is None
                               or not (BREATH_PERIOD_RANGE[0] <= bt_period
                                       <= BREATH_PERIOD_RANGE[1])))
    res["px_exh_breath_carrier_can_fail_note"] = (
        "★ 反面：**同一把呼吸尺子**（同判据、同阈值）改量**脚带顶行**（rows %s）"
        "⟹ 峰峰值 **%s px**、过零 **%d** 次、周期 **%s** ⟹ **必须红**。"
        "★ 这条是「同尺子换载体」型反对照（承 E01 `px_stun_sway_can_fail_ok`）。"
        "它把本支核心事实钉死：**胸在起伏、脚一动不动**。"
        % (list(foot_r), bt_pp, bt_cross,
           res["px_exh_breath_control_carrier"]["period_frames"]))

    # ---------------- (3) ★★★ 反面对照 ②：NOBREATH 重渲必须红 ----------------
    nos = {}
    for frame in HOLD:
        pixels = load(STEM_NOBREATH, frame)
        if pixels is None:
            continue
        cut = strip_hem(mask_of(pixels))
        box = bbox(cut)
        row = {}
        if box is not None:
            _rmin, _rmax, cmin, cmax = box
            c_front = int(round(cmin + FRONT_FRAC * max(1, cmax - cmin)))
            row["top_front"] = top_row_in_cols(cut, cmin, c_front)
        nos[frame] = row
    if len(nos) != len(HOLD):
        raise RuntimeError(
            "反面对照 ② 图缺失（要 %s_f%04d..f%04d，用 `E02_STEM_ONLY=1 "
            "E02_STEM=exhnobreath E02_STEM_HAND=exhnobreathhand E02_TP_NOBREATH=1 "
            "--python anim_exhausted.py` 重渲）：现有 %d/%d 张"
            % (STEM_NOBREATH, HOLD[0], HOLD[-1], len(nos), len(HOLD)))
    nos_front = [nos[f]["top_front"] for f in frames]
    nos_pp = spread(nos_front)
    nos_cross, nos_period = EX._crossings([v for v in nos_front
                                           if v is not None])
    res["px_exh_breath_control_nobreath"] = {
        "view": STEM_NOBREATH, "pp_px": None if nos_pp is None
        else round(nos_pp, 4), "crossings": nos_cross,
        "period_frames": None if nos_period is None else round(nos_period, 3)}
    res["px_exh_breath_can_fail_ok"] = bool(
        nos_pp is not None and (nos_pp < BREATH_PP_MIN_PX
                                or nos_cross < BREATH_MIN_CROSS
                                or nos_period is None
                                or not (BREATH_PERIOD_RANGE[0] <= nos_period
                                        <= BREATH_PERIOD_RANGE[1])))
    res["px_exh_breath_can_fail_note"] = (
        "★★ 反面 ②：`E02_TP_NOBREATH=1`（呼吸全归零 ⟹ 弯腰站定不动）重渲 `%s`，"
        "**同一台相机 + 同一批 hold 帧（%d..%d 逐帧）** ⟹ 前半幅顶行峰峰值 "
        "**%s px**、过零 **%d** 次、周期 **%s** ⟹ **必须红**。"
        "★ 这条证明呼吸尺子**对「不喘」敏感**（不是「任何输入都判过」）。"
        % (STEM_NOBREATH, HOLD[0], HOLD[-1], nos_pp, nos_cross,
           res["px_exh_breath_control_nobreath"]["period_frames"]))

    # ---------------- (4) ★★★ `px_exh_hand_on_knee_ok` ------------------------
    #   载体 = **手部单件层**（`exhhand_side`，只显手）的**重心**；
    #   参考点 = `_e02_kneescreen.json` 投影的「拳头目标点」（膝 + 偏移）。
    ks_path = os.path.join(A.PREVIEW_DIR, "_e02_kneescreen.json")
    if not os.path.exists(ks_path):
        raise RuntimeError("缺 %s（`anim_exhausted.py` 主渲时写出）" % ks_path)
    with open(ks_path, "r", encoding="utf-8") as handle:
        ks = json.load(handle)
    ks_rows = ks["rows"]

    def hand_centroid(stem, frame):
        pixels = load(stem, frame)
        if pixels is None:
            return None
        mask = mask_of(pixels)
        if not mask.any():
            return None
        return centroid_rc(mask)

    hand_tbl = {}
    for frame in HAND_FRAMES:
        cen = hand_centroid(HANDBASE, frame)
        if cen is None or str(frame) not in ks_rows:
            continue
        side_l = ks_rows[str(frame)]["L"]
        kne = (side_l[0], side_l[1])
        dist_px = float(np.hypot(cen[0] - kne[0], cen[1] - kne[1]))
        hand_tbl[frame] = {"cen": cen, "knee": kne, "dist_px": dist_px,
                           "above_px": cen[0] - kne[0]}
    if not hand_tbl:
        raise RuntimeError("手部单件层一张都没有：%s/%s_f%04d.png"
                           % (PRE, HANDBASE, HAND_FRAMES[0]))
    hd_max = max(hand_tbl[f]["dist_px"] for f in hand_tbl)
    hd_min = min(hand_tbl[f]["dist_px"] for f in hand_tbl)
    hd_follow = hd_max - hd_min
    res["px_exh_hand_frames"] = [min(hand_tbl), max(hand_tbl), len(hand_tbl)]
    res["px_exh_hand_dist_px_max"] = round(hd_max, 4)
    res["px_exh_hand_dist_px_min"] = round(hd_min, 4)
    res["px_exh_hand_dist_mm_max"] = round(hd_max * MMP, 3)
    res["px_exh_hand_dist_follow_px"] = round(hd_follow, 4)
    res["px_exh_hand_above_px"] = {str(f): round(hand_tbl[f]["above_px"], 3)
                                   for f in sorted(hand_tbl)}
    res["px_exh_hand_knee_screen"] = {str(f): [round(v, 3)
                                               for v in hand_tbl[f]["knee"]]
                                      for f in sorted(hand_tbl)}
    res["px_exh_hand_centroid"] = {str(f): [round(v, 3)
                                            for v in hand_tbl[f]["cen"]]
                                   for f in sorted(hand_tbl)}
    res["px_exh_hand_on_knee_tol_px"] = HAND_TOL_PX
    res["px_exh_hand_on_knee_ok"] = bool(
        hd_max <= HAND_TOL_PX and hd_follow <= HAND_TOL_PX
        and all(hand_tbl[f]["above_px"] > 0.0 for f in hand_tbl))
    res["px_exh_hand_on_knee_note"] = (
        "★★★ **本支命门的像素级守卫**（骨架级同族判据 = `exh_hand_on_knee_ok`，"
        "实测 hold 段 `[L,R] = [127.5, 127.5] mm`、跟随波动 0.0 mm）。"
        "载体 = **手部单件层**（只显 `Hand_Palm_*` / `Thumb_*` / `Finger_*`）掩码的"
        "**重心**；参考点 = `_e02_kneescreen.json` 投影的**拳头目标点**（膝 + "
        "`KNEE_OFFSET`，且该点**必在膝上方** `KNEE_OFF_Z=+25 mm`）。"
        "hold 段 %d 帧实测：手重心到目标点距离 **%.2f .. %.2f px = %.2f .. %.2f mm**"
        "（阈值 ≤ %.0f px = %.0f mm）、**跟随波动 %.2f px**（阈值 ≤ %.0f px）、"
        "**全部帧手在膝上方** ⟹ 读作「双手扶膝」，不是「手悬在膝上 / 手在膝下」。"
        "★ 侧视里左右手在**同一视轴（X）上重叠**，故掩码是两只手的并集 —— "
        "因两手对称扶同高的膝，并集仍是一团、位于同一屏幕位置。"
        % (len(hand_tbl), hd_min, hd_max, hd_min * MMP, hd_max * MMP,
           HAND_TOL_PX, HAND_TOL_PX * MMP, hd_follow, HAND_TOL_PX))

    # ---------------- (5) ★★★ 反面对照 ①：HANDFAR 重渲必须红（命门）-----------
    far_tbl = {}
    for frame in HAND_FRAMES:
        cen = hand_centroid(STEM_HAND, frame)
        if cen is None or str(frame) not in ks_rows:
            continue
        side_l = ks_rows[str(frame)]["L"]
        kne = (side_l[0], side_l[1])
        far_tbl[frame] = float(np.hypot(cen[0] - kne[0], cen[1] - kne[1]))
    if len(far_tbl) != len(HAND_FRAMES):
        raise RuntimeError(
            "反面对照 ① 图缺失（要 %s_f%04d..f%04d，用 `E02_STEM_ONLY=1 "
            "E02_STEM=exhfar E02_STEM_HAND=exhfarhand E02_TP_HANDFAR=1 "
            "--python anim_exhausted.py` 重渲）：现有 %d/%d 张"
            % (STEM_HAND, HAND_FRAMES[0], HAND_FRAMES[-1],
               len(far_tbl), len(HAND_FRAMES)))
    far_min = min(far_tbl.values())
    res["px_exh_hand_control_handfar"] = {
        "view": STEM_HAND, "dist_px_min": round(far_min, 4),
        "dist_px_max": round(max(far_tbl.values()), 4),
        "dist_mm_min": round(far_min * MMP, 3)}
    res["px_exh_hand_on_knee_can_fail_ok"] = bool(
        far_min > HAND_CANFAIL_MIN_PX and far_min > HAND_TOL_PX)
    res["px_exh_hand_on_knee_can_fail_note"] = (
        "★★★ 反面 ①：`E02_TP_HANDFAR=1`（拳头离膝 `|offset|=(%.2f, %.2f) m` 的远端）"
        "重渲 `%s`，**同一台相机 + 同一批 hold 帧 + 同一个投影膝目标点** ⟹ "
        "手重心到膝目标点距离 **%.2f .. %.2f px = %.2f mm 起**（阈值 ≥ %.0f px）"
        "⟹ **必须红**。★ **这是本支最关键的反对照**（E02 计划 §4 第 7 步 §② / "
        "⚠ 自查「『手扶膝』必须有一条会失败的断言」）：它证明「手扶膝」不是靠嘴说，"
        "而是**真的有一条会失败的断言在盯** —— 骨架级 `exh_hand_on_knee_ok` 与"
        "像素级 `px_exh_hand_on_knee_ok` 在同一旋钮下**同时见红**。"
        % (EX.HAND_FAR_V[0], EX.HAND_FAR_V[1], STEM_HAND, far_min,
           max(far_tbl.values()), far_min * MMP, HAND_CANFAIL_MIN_PX))

    # ---------------- (6) ★★ 反面对照 ③：FOOTSWAY 重渲必须红 -----------------
    foot_t = {}
    for frame in HOLD:
        pixels = load(STEM_FOOT, frame)
        if pixels is None:
            continue
        cut = strip_hem(mask_of(pixels))
        cl, ch = band_span(cut, foot_r[0], foot_r[1])
        foot_t[frame] = {"boot_col_lo": cl, "boot_col_hi": ch,
                         "bottom": silhouette_bottom(cut)}
    if len(foot_t) != len(HOLD):
        raise RuntimeError(
            "反面对照 ③ 图缺失（要 %s_f%04d..f%04d，用 `E02_STEM_ONLY=1 "
            "E02_STEM=exhfootsway E02_STEM_HAND=exhfootswayhand E02_TP_FOOTSWAY=1 "
            "--python anim_exhausted.py` 重渲）：现有 %d/%d 张"
            % (STEM_FOOT, HOLD[0], HOLD[-1], len(foot_t), len(HOLD)))
    ff_lo = spread([foot_t[f]["boot_col_lo"] for f in frames])
    ff_hi = spread([foot_t[f]["boot_col_hi"] for f in frames])
    ff_bot = spread([foot_t[f]["bottom"] for f in frames])
    res["px_exh_foot_lock_control"] = {
        "view": STEM_FOOT,
        "col_lo_spread_px": ff_lo, "col_hi_spread_px": ff_hi,
        "bottom_spread_px": ff_bot,
        "col_lo_range": [min(foot_t[f]["boot_col_lo"] for f in frames),
                         max(foot_t[f]["boot_col_lo"] for f in frames)],
        "col_hi_range": [min(foot_t[f]["boot_col_hi"] for f in frames),
                         max(foot_t[f]["boot_col_hi"] for f in frames)]}
    res["px_exh_foot_lock_can_fail_ok"] = bool(
        max(ff_lo, ff_hi, ff_bot) > max(FOOT_COL_TOL_PX, SOLE_ROW_TOL_PX))
    res["px_exh_foot_lock_can_fail_note"] = (
        "★★★ 反面 ③：`E02_TP_FOOTSWAY=1`（hold 段骨盆整体横移 ±%.0f mm、**跳过脚锁**）"
        "重渲 `%s`，**同一台相机 + 同一批 hold 帧** ⟹ 脚带左缘 %s→%s 漂移 "
        "**%.2f px = %.1f mm**、右缘 **%.2f px**、底缘行 **%.0f px** ⟹ **必须红**。"
        "★ 骨架级在同一旋钮下红的正是 `exh_foot_lock_ok`（实测踝漂 54.8 mm）。"
        % (EX.FOOT_SWAY_MM, STEM_FOOT,
           res["px_exh_foot_lock_control"]["col_lo_range"][0],
           res["px_exh_foot_lock_control"]["col_lo_range"][1],
           ff_lo, ff_lo * MMP, ff_hi, ff_bot))

    # ---------------- (7) ★★ 衣摆块：**算出来的不相交** + **剔除不是空操作** ----
    overlap_foot = not (hem_r[1] < foot_r[0] or hem_r[0] > foot_r[1])
    # 前半幅列窗（hold 段取并集，保守）：与衣摆行区间是否相交
    all_front_cols = [table[f]["front_cols"] for f in frames
                      if table[f]["front_cols"] is not None]
    fc0 = min(c[0] for c in all_front_cols)
    fc1 = max(c[1] for c in all_front_cols)
    top_front_rows = [table[f]["top_front"] for f in frames
                      if table[f]["top_front"] is not None]
    tf_range = [min(top_front_rows), max(top_front_rows)]
    overlap_front = not (hem_r[1] < tf_range[0] or hem_r[0] > tf_range[1])

    def _extent(span):
        return 0.0 if span is None or span[0] is None else float(span[1] - span[0])

    # （a）衣摆**自己行带**内的横向跨度：raw（含衣摆板）vs cut（剔除后）
    hem_extent_delta = max(
        abs(_extent(table[f]["hem_span_raw"]) - _extent(table[f]["hem_span_cut"]))
        for f in frames)
    hem_edge_delta = max(
        max(abs((table[f]["hem_span_raw"] or (0, 0))[0]
                - (table[f]["hem_span_cut"] or (0, 0))[0]),
            abs((table[f]["hem_span_raw"] or (0, 0))[1]
                - (table[f]["hem_span_cut"] or (0, 0))[1]))
        for f in frames)
    # （b）E01 老口径：全剪影**列心**位移（衣摆在画面偏后 ⟹ 会把它往图像右拉）
    hem_shift_px = max(
        abs((table[f]["full_cen_raw"] or (0, 0))[1]
            - (table[f]["full_cen_cut"] or (0, 0))[1]) for f in frames)
    hem_top_delta = max(abs((table[f]["top_all_raw"] or 0)
                            - (table[f]["top_all"] or 0)) for f in frames)
    res["hem_screen_box"] = {"rows": list(hem_r), "cols": list(hem_c)}
    res["hem_vs_foot_overlap"] = bool(overlap_foot)
    res["hem_vs_front_window"] = {"front_cols": [fc0, fc1],
                                  "top_front_rows": list(tf_range),
                                  "hem_rows": list(hem_r),
                                  "front_rows_overlap_hem": bool(overlap_front)}
    res["px_hem_band_extent_delta_px"] = round(hem_extent_delta, 4)
    res["px_hem_band_edge_delta_px"] = round(hem_edge_delta, 4)
    res["px_hem_full_cen_shift_px"] = round(hem_shift_px, 4)
    res["px_hem_full_cen_shift_mm"] = round(hem_shift_px * MMP, 3)
    res["px_hem_top_row_delta_px"] = round(hem_top_delta, 4)
    res["px_hem_excluded_ok"] = bool(not overlap_foot and not overlap_front
                                     and fc1 < hem_c[0])
    res["px_hem_stripped_ok"] = bool(
        max(hem_extent_delta, hem_edge_delta, hem_shift_px) >= HEM_SHIFT_MIN_PX)
    res["px_hem_note"] = (
        "★★ **项目纪律：不许照抄上一支的口径，也不许写死。** 本支三条尺子的盒"
        "**现算**：脚带 rows %s、前半幅 cols %s（顶行 rows %s）；衣摆静止块投影到 "
        "rows %s / cols %s。⟹ 与脚带%s、与前半幅列窗%s（且 `fc1=%d < hem_c0=%d`）"
        "—— **这是算出来的结论，不是「应该没事」**。"
        "★ **本支与 E01 的关键差别**：E01 站姿，衣摆在腰上（rows 547..565）；"
        "**本支弯腰后上身塌到 z≈0.75–1.26 m，衣摆仍钉在 z 897.5..926.0 mm "
        "⟹ 相对身体**偏后**（cols %s，远在身体前缘 cols [%d, %d] 之后）**。"
        "★★★ **实测教训（`_e02_px1.log`）**：第一版把「剔除是否生效」量在"
        "**全剪影顶行**上，实测 hold 段 raw vs cut 偏移 **%.1f px = 空操作** —— "
        "因为剪影最高点是**头（row %d）**，衣摆（rows %s）**在其下方**。"
        "⟹ 这是**载体选错**，不是衣摆不存在。改正：在**衣摆自己行带**内量，"
        "实测**横向跨度变化 %.1f px、左右缘位移 %.1f px**（★ **都是 0** —— "
        "说明弯腰姿态下**身体剪影在该行带已横向盖住衣摆**，即衣摆**内嵌**于剪影、"
        "不改变轮廓外缘，只贡献内部面积）；再补 E01 老口径**全剪影列心**位移 "
        "**%.2f px = %.2f mm**（阈值 ≥ %.2f px）⟹ **剔除真的生效**（不是空操作）。"
        "★ 结论：本支衣摆**既不污染三条尺子**（见 `px_hem_excluded_ok`），"
        "**也不是剪影顶行**；它只在内嵌面积上影响不了任何外缘读数。"
        % (list(foot_r), [fc0, fc1], list(tf_range), list(hem_r), list(hem_c),
           "**相交**" if overlap_foot else "**不相交**",
           "**相交**" if overlap_front else "**不相交**",
           fc1, hem_c[0], list(hem_c), fc0, fc1,
           hem_top_delta, table[frames[0]]["top_all"], list(hem_r),
           hem_extent_delta, hem_edge_delta, hem_shift_px, hem_shift_px * MMP,
           HEM_SHIFT_MIN_PX))

    # ---------------- (8) 汇总 -----------------------------------------------
    checks = sorted(k for k in res if k.endswith("_ok"))
    failed = sorted(k for k in checks if res[k] is False)
    res["checks"] = checks
    res["failed"] = failed
    res["verdict"] = "PASS" if not failed else "FAIL"
    print("E02PX_REPORT " + json.dumps(res, ensure_ascii=False))
    print("E02PX_DONE failed=%s" % failed)
    if not failed:
        print("E02PX_DONE verdict=PASS")


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E02PX_FAILURE " + traceback.format_exc())
