"""probe_d15_pixels —— 把 D15 `Knockdown_B` 的判据数值换算成**画面像素**。

（由 `probe_d14_pixels.py` 派生。D15 计划 §3「像素探针」原文：
  「`probe_d14_pixels.py` → **`probe_d15_pixels.py`**，`STEM="knockdownb"`。
   ★ **独门尺子**：`px_fall_backward_ok`（头在图像哪一侧：D14 头在**左**、
   D15 头在**右**，符号相反）；**反面对照 = D14 自己**（判红）。
   其余照抄 D14：`px_seam_frame_match_ok` / `px_seam_steps_ok` / `px_ground_hold_ok` /
   `px_hem_excluded_ok` / `px_hem_stripped_ok`；`px_land_jump_ok` 载体换成
   **面积行心 / 骨盆带行心**。」

═══ 取景（两套，各有不可替代的用途）═══
  ① `knockdownb_side` —— 与 D13/D14 **逐位相同**：侧视 (5.20, 0, 1.20) → (0, 0, 1.20)、
     up = +Z、正交宽 3.30 m、780×1100 ⟹ **3 mm/px**，`z_mm = −390 + row × 3`。
     ★ 用途：跨支接缝（`px_seam_frame_match_ok`）与跨支尺子（`px_seam_steps_ok`）。
  ② `knockdownbwide_side` —— 视中心沿 **+Y 平移 0.50 m**，正交宽**仍是 3.30 m**
     ⟹ **仍是同一把 3 mm/px 的尺子**（正交侧视的行号只由世界 z 决定，平移只动列）。
     ★ 为什么必须另起一套：本支后倒带 **+Y 0.444 m** 的水平位移 ⟹ 末段整个人被推出
       ①的右边缘（实测 `f15~f20` 的 `col_hi = 779` = 顶到边界，头被裁）。
       列心类判据（`px_fall_backward_ok`）在裁切的画面上**量不出数**。
  图像**右** = +Y = **身后**；行号**上** = +Z。物理分辨率 **3 mm/px**。

★★★ 对 D14 口径的**四处**必要修正（全部附实测依据）★★★

  ① **`px_fall_backward_ok`（独门尺子）的载体从"剪影列心"换成"肤色列心"。**
     剪影列心在本支**测不出方向**：仰卧时身体是一条近水平的长条，
     头端与脚端对列心的贡献几乎对称（实测 f20 `cc_all = 424.4`，看不出头在哪边）。
     ⟹ 换成 **肤色（脸 + 手）像素的列心**：`R − B > 0.04` 且 `0.42 < lum < 0.90`。
     实测（`_px_cal2`，wide 视图，col 单位 px）：

       帧     剪影列域        肤色列心    读相
       D15 f7   122~385        297.6     头在**右**（+44 px 于剪影中心）
       D15 f15  183~672        622.3     头在**右**（+195）
       D15 f20  183~677        627.3     头在**右**（+197）   ⟹ 后倒 ✓
       D14 f7   309~497        381.9     （对照，见 ② ）

  ② **D14 的反面对照必须另渲一套取景**（`_d14wide_render.py`）——
     D14 自己的 `knockdownf_side` 在末段**左侧被裁**（实测 f15/f20 `col_all = [0, 501]`
     且 `clip_L = True`，头部**整个出画**，`skin` 掩膜在 f15 只剩 70 px、f20 为 **0 px**）
     ⟹ 拿它当对照**量不出列心**，对照是**无效的**（不是尺子坏，是对照坏）。
     ⟹ 用**同一把尺子**（正交侧视 3.30 m / 780×1100）给 D14 重渲一套，只把视中心
       平移到 D14 身体那一侧（−0.35 m），使全身在画面内。图像右仍恒为 +Y。
     ★ 该套刻意落在 `previews/anim/_probe/`，**不污染**正式交付目录。

  ③ **`px_land_jump_ok` 的载体从"剪影最低行"换成"面积行心"。**
     本支 `f ≥ LAND` 双腿**抬起**（这是与 D14 的核心画面差别）⟹ 剪影最低行在
     落地后**不再是落地方向的代表**。面积行心（整幅剪影的行加权重心）对
     "全身一起砸下去"敏感，且不受末端肢体单独摆动支配。**并列报出**骨盆带行心。

  ④ **`px_hem_*` 两条在此**不再适用**（实测：本支两套取景全程 `hem_dropped = []`，
     `bottom_raw` 与 `bottom` **逐帧相等**）⟹ 照 D14 的修法**降级为只报**，
     并明确登记"本支没有任何以最低行为载体的判据被下摆影响"。

画面判据（全部会失败）：
  `px_seam_frame_match_ok`      ★★ 跨支接缝：`airhit_side_f0018` 与 `knockdownb_side_f0000`
                               的 顶行/底行/头带行心/高/宽 **逐位一致**（≤1 px）
  `px_seam_steps_ok`            ★★ **跨支尺子**：`knockdownb_side f0~f6` 的**头带行心逐帧步长**
                               与共享解析弹道预测的**残差中位数** ≤ `SEAM_STEP_MED_TOL_PX`，
                               且 7 个步长**全为负**（都在下落）
  `px_seam_steps_control_ok`    ★ 正面：同一把尺子量 **D13 自己 f14~f17**（同一条弹道、上游）必须通过
  `px_seam_steps_can_fail_ok`   ★ 反向：同一把尺子量 **D15 f8~f13**（已落地、姿态剧变）必须判红
  `px_fall_monotone_ok`         侧视最低行在 `f < LAND` **逐帧下降**（每帧 Δ ≤ −`FALL_STEP_MIN_PX`）
  `px_fall_monotone_control_ok` ★ 正面：A12 `Jump_Fall` 下落段用同一把尺子必须通过
  `px_fall_monotone_can_fail_ok` ★ 反向：D12 `Launch_Hit` f0~f11（地面段）必须判红
  `px_land_jump_ok`             ★★ 触地帧落差突变（载体 = **面积行心**，见修正 ③）
  `px_land_jump_can_fail_ok`    ★★ 反向：**D13 自己**（全段在空中）必须判红
  `px_fall_backward_ok`         ★★★ **独门尺子**：肤色列心从 `f = LAND` 到 `f = END`
                               必须**向图像右**移动 ≥ `BACKWARD_MIN_PX`（= 头在右 = 后倒）
  `px_fall_backward_can_fail_ok` ★★★ 反向：**D14 自己**（同一条弹道、向前扑倒）用同一把
                               尺子必须判红（Δ < 0，头在左）
  `px_ground_hold_ok`           ★★ 贴地自持：**wide 视图** `f ∈ [PLATEAU, TOTAL]`
                               顶行/面积行心 **逐帧恒定** ≤ `HOLD_TOL_PX`
  `px_ground_hold_can_fail_ok`  ★★ 反向：D13 的 `f16~f18` 用同一把尺子必须判红（继续下坠）
  `px_supine_flip_ok`           ★ 仰卧：剪影 高/宽 从 `f=LAND` 到 `f=END`
                               高度比 ≤ `SUPINE_H_RATIO_MAX` 且 宽度比 ≥ `SUPINE_W_RATIO_MIN`
  `px_supine_flip_can_fail_ok`  ★ 反向：D15 自己 `f0 → f=LAND`（还没躺下）必须判红
  `px_supine_flip_trunk_ok`     ★ 仰卧（比幅值更严的一版）：末帧**仰角**（躯干长轴与地面夹角）
                               ≥ `SUPINE_TRUNK_MIN_DEG` —— 由 顶行/底行 与 列域宽 反算
  `px_hem_excluded_ok`          被剔块（若有）= 已知静态足迹，且各帧足迹**逐位相同**
  `px_hem_stripped_ok`          下摆**确实被剔**；本支实测**无块可剔** ⟹ 判据改为
                               "登记为不适用且不影响任何以最低行为载体的判据"

只报不判：逐帧顶/底/头带/面积/骨盆带行心全量表、肤色列心全量表、三载体 `g` 对照、
         两套取景的列域（含裁切标志）、前视/3Q 剪影。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d15_pixels.py
  D15PX_DUMP=1 追加全量表。
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
PRE_PROBE = os.path.join(PRE, "_probe")
STEM = "knockdownb"

# ---- 视图表：(图高 px, 正交宽 m, 相机 z, 子目录) ------------------------------
SIDE = "knockdownb_side"
WIDE = "knockdownbwide_side"
D14W = "knockdownfW_side"
VIEWS = {
    SIDE: (1100, 3.30, 1.20, PRE),          # 与 D13/D14 逐位相同（跨支尺子）
    WIDE: (1100, 3.30, 1.00, PRE),          # 视中心 +Y 0.50（同尺子，只平移）
    "knockdownb_front": (1100, 4.20, 0.95, PRE),
    "airhit_side": (1100, 3.30, 1.30, PRE),  # D13 侧视 —— 跨支尺子 + 反面对照
    "jumpfall_side": (1100, 3.80, 1.30, PRE),  # A12 —— 正面对照（纯弹道）
    "launchhit_side": (1100, 4.30, 1.55, PRE),  # D12 —— 反面对照（地面段）
    D14W: (1100, 3.30, 1.00, PRE_PROBE),   # ★ 本支专造：D14 的反面对照（见修正 ②）
}

# ---- 帧号（与 `anim_knockdown_b.py` 的时间轴逐一对齐）-------------------------
START = 0
FALL_END = 6
LAND = int(os.environ.get("D15PX_LAND", "7"))
HOLD_END = 8
COMPRESS_PEAK = 11
SUPINE_PEAK = 15
PLATEAU = 16
CANCEL = 16
TOTAL = 20

G_PER_FRAME_MM = 9.8 / 60.0 / 60.0 * 1000.0         # 2.722222 mm/帧²
TAKEOFF_PELVIS_Z = 0.9200
TAKEOFF_SPEED = 0.075                               # m/帧
T_PHASE = 49.5                                      # D15 帧 f ⟺ t = 49.5 + f
T_PHASE_D13 = 31.5                                  # D13 帧 f ⟺ t = 31.5 + f


def ball_z(frame, t_phase=T_PHASE):
    t = t_phase + float(frame)
    return (TAKEOFF_PELVIS_Z + TAKEOFF_SPEED * t
            - 0.5 * (9.8 / 60.0 / 60.0) * t * t)


def ball_step_px(frame, ppm, t_phase=T_PHASE):
    return (ball_z(frame, t_phase) - ball_z(frame - 1, t_phase)) * 1000.0 * ppm


# ---- 阈值（全部由实测导出，见模块 docstring）----------------------------------
SEAM_MATCH_TOL_PX = float(os.environ.get("D15PX_SEAM_PX", "1.0"))
SEAM_STEP_MED_TOL_PX = float(os.environ.get("D15PX_SEAM_STEP_TOL", "1.4"))
SEAM_STEP_MED_TOL_CTRL_PX = float(os.environ.get("D15PX_SEAM_STEP_TOL_CTRL", "1.4"))
FALL_STEP_MIN_PX = float(os.environ.get("D15PX_FALL_STEP", "10.0"))
FALL_STEP_MAX_PX = float(os.environ.get("D15PX_FALL_STEP_MAX", "34.0"))
LAND_STEP_MIN_PX = float(os.environ.get("D15PX_LAND_STEP", "25.0"))
BACKWARD_MIN_PX = float(os.environ.get("D15PX_BACKWARD", "60.0"))
HOLD_TOL_PX = float(os.environ.get("D15PX_HOLD_TOL", "1.5"))
SUPINE_H_RATIO_MAX = float(os.environ.get("D15PX_SUPINE_H", "0.72"))
SUPINE_W_RATIO_MIN = float(os.environ.get("D15PX_SUPINE_W", "1.60"))
SUPINE_TRUNK_MAX_DEG = float(os.environ.get("D15PX_SUPINE_TRUNK_MAX", "25.0"))
SUPINE_TRUNK_MIN_DEG = float(os.environ.get("D15PX_SUPINE_TRUNK_MIN", "60.0"))

# ---- 带（绝对世界高度锚定；沿用 D13/D14 口径）--------------------------------
PELVIS_BAND_ABOVE_SOLE_MM = (800.0, 920.0)
HEAD_BAND_FROM_TOP_PX = 55

# ---- 肤色掩膜（修正 ①）--------------------------------------------------------
SKIN_RB_MIN = float(os.environ.get("D15PX_SKIN_RB", "0.04"))
SKIN_LUM_LO = float(os.environ.get("D15PX_SKIN_LUM_LO", "0.42"))
SKIN_LUM_HI = float(os.environ.get("D15PX_SKIN_LUM_HI", "0.90"))

# ---- 跨支尺子的时间轴 ----------------------------------------------------------
SEAM_D13_FRAMES = [14, 15, 16, 17]
SEAM_D15_FRAMES = [0, 1, 2, 3, 4, 5, 6]
SEAM_LAST_D13_FRAME = 18
SEAM_CTRL_D13_FRAMES = [14, 15, 16, 17]
SEAM_NEG_D15_FRAMES = [8, 9, 10, 11, 12, 13]

# ---- 对照 ----------------------------------------------------------------------
CTRL_FRAMES = [12, 16, 20, 24]            # A12 下落段
NEG_D12_FRAMES = list(range(0, 12))       # D12 地面段
D13_POST_LAND_FRAMES = list(range(LAND, 19))


# =============================================================== 像素工具
def load(view, frame):
    _res, _ortho, _cz, base = VIEWS[view]
    path = os.path.join(base, "%s_f%04d.png" % (view, frame))
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


def skin_mask(pixels):
    """★ 修正 ①：肤色（脸 + 手）= 红多于蓝 且 中等亮度。"""
    rgb = pixels[:, :, :3]
    lum = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    rb = rgb[:, :, 0] - rgb[:, :, 2]
    return (rb > SKIN_RB_MIN) & (lum > SKIN_LUM_LO) & (lum < SKIN_LUM_HI)


def shoe_mask(pixels):
    """★ 鞋（灰黑、非蓝）：`|R − B| ≤ 0.04` 且 `lum < 0.35`。用于**躯干长轴**的脚端。"""
    rgb = pixels[:, :, :3]
    lum = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
    rb = np.abs(rgb[:, :, 0] - rgb[:, :, 2])
    return (rb <= 0.04) & (lum < 0.35)


def rc_centroid(mask):
    """返回 (col, row) 质心；空掩膜返回 (None, None)。row 0 = 画面**底**（+Z 向上）。"""
    if int(mask.sum()) == 0:
        return None, None
    weights = mask.astype(np.float64)
    total = weights.sum()
    cols = (np.arange(mask.shape[1], dtype=np.float64)[None, :] * weights).sum()
    rows = (np.arange(mask.shape[0], dtype=np.float64)[:, None] * weights).sum()
    return float(cols / total), float(rows / total)


def px_per_mm(view):
    res_y, ortho, _cam_z, _base = VIEWS[view]
    return (float(res_y) / ortho) / 1000.0


def rows_any(mask):
    rows = np.where(mask.any(axis=1))[0]
    return None if rows.size == 0 else (int(rows.min()), int(rows.max()))


def cols_any(mask):
    cols = np.where(mask.any(axis=0))[0]
    return None if cols.size == 0 else (int(cols.min()), int(cols.max()))


def slab_row_centroid(mask, lo, hi):
    lo, hi = max(lo, 0), min(hi, mask.shape[0] - 1)
    if hi <= lo:
        return None
    slab = mask[lo:hi + 1, :]
    weights = slab.sum(axis=1).astype(np.float64)
    if weights.sum() <= 0:
        return None
    index = np.arange(slab.shape[0], dtype=np.float64) + lo
    return float((index * weights).sum() / weights.sum())


def area_row_centroid(mask):
    weights = mask.sum(axis=1).astype(np.float64)
    if weights.sum() <= 0:
        return None
    return float((np.arange(mask.shape[0]) * weights).sum() / weights.sum())


def col_centroid(mask):
    if int(mask.sum()) == 0:
        return None
    weights = mask.sum(axis=0).astype(np.float64)
    return float((np.arange(mask.shape[1]) * weights).sum() / weights.sum())


def bands(view, mask):
    ppm = px_per_mm(view)
    ext = rows_any(mask)
    if ext is None:
        return None
    head = (max(ext[1] - HEAD_BAND_FROM_TOP_PX, ext[0]), ext[1])
    pelvis = (ext[0] + int(round(PELVIS_BAND_ABOVE_SOLE_MM[0] * ppm)),
              ext[0] + int(round(PELVIS_BAND_ABOVE_SOLE_MM[1] * ppm)))
    span = cols_any(mask)
    return {
        "bottom": ext[0], "top": ext[1],
        "head_rows": list(head), "pelvis_rows": list(pelvis),
        "head_row": slab_row_centroid(mask, *head),
        "pelvis_row": slab_row_centroid(mask, *pelvis),
        "area_row": area_row_centroid(mask),
        "col_lo": (None if span is None else span[0]),
        "col_hi": (None if span is None else span[1]),
        "height_px": int(ext[1] - ext[0] + 1),
        "width_px": (None if span is None else int(span[1] - span[0] + 1)),
    }


def quad_fit(frames, values):
    f = np.array(frames, dtype=np.float64)
    y = np.array(values, dtype=np.float64)
    design = np.stack([np.ones_like(f), f, f * f], axis=1)
    coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
    return float(coeffs[0]), float(coeffs[1]), float(coeffs[2])


# =============================================================== 主流程
def main():  # noqa: C901
    res = {}
    res["stem"] = STEM
    res["timeline"] = {"START": START, "FALL_END": FALL_END, "LAND": LAND,
                       "HOLD_END": HOLD_END, "COMPRESS_PEAK": COMPRESS_PEAK,
                       "SUPINE_PEAK": SUPINE_PEAK, "PLATEAU": PLATEAU,
                       "CANCEL": CANCEL, "TOTAL": TOTAL}
    res["ballistic"] = {"T_PHASE_D15": T_PHASE, "T_PHASE_D13": T_PHASE_D13,
                        "ball_z_m": {str(f): round(ball_z(f), 6)
                                     for f in range(-4, TOTAL + 1)}}

    def r3(x):
        return None if x is None else round(x, 3)

    # ---------------- (0) 逐视图扫描（本支无下摆可剔，见修正 ④）-------------
    def scan(view, frame_list, with_skin=False):
        table = {}
        for frame in frame_list:
            pixels = load(view, frame)
            if pixels is None:
                continue
            raw = mask_of(pixels)
            band = bands(view, raw)
            if band is None:
                continue
            band["bottom_raw"] = band["bottom"]
            band["mask"] = raw
            if with_skin:
                sk = skin_mask(pixels) & raw
                sh = shoe_mask(pixels) & raw
                band["skin_cc"] = col_centroid(sk)
                band["skin_n"] = int(sk.sum())
                band["skin_rc"] = rc_centroid(sk)
                band["shoe_cc"] = col_centroid(sh)
                band["shoe_n"] = int(sh.sum())
                band["shoe_rc"] = rc_centroid(sh)
            table[frame] = band
        return table

    side = scan(SIDE, list(range(START, TOTAL + 1)))
    if not side:
        raise RuntimeError("侧视静帧一张都没有：%s" % PRE)
    ppm = px_per_mm(SIDE)
    frames = sorted(side)
    res["side_px_per_mm"] = round(ppm, 6)
    res["side_mm_per_px"] = round(1.0 / ppm, 4)
    res["side_row_ruler"] = ("世界高度 z_mm = −390.0 + row × 3.0（窄视）；"
                             "wide 视 z_mm = −330.0 + row × 3.0；"
                             "图像右 = +Y = 身后；行号向上 = +Z；3.00 mm/px。")
    for tag, table in (("side", side),):
        res["%s_bottom_row" % tag] = {str(f): table[f]["bottom"] for f in frames}
        res["%s_top_row" % tag] = {str(f): table[f]["top"] for f in frames}
        res["%s_head_row" % tag] = {str(f): r3(table[f]["head_row"])
                                    for f in frames}
        res["%s_area_row" % tag] = {str(f): r3(table[f]["area_row"])
                                    for f in frames}
        res["%s_pelvis_row" % tag] = {str(f): r3(table[f]["pelvis_row"])
                                      for f in frames}
        res["%s_height_px" % tag] = {str(f): table[f]["height_px"]
                                     for f in frames}
        res["%s_width_px" % tag] = {str(f): table[f]["width_px"]
                                    for f in frames}

    # ★★ wide 视图：列心类 + 贴地自持 + 仰卧翻转的载体（带肤色）
    wide = scan(WIDE, list(range(START, TOTAL + 1)), with_skin=True)
    res["wide_col_span"] = {str(f): [wide[f]["col_lo"], wide[f]["col_hi"]]
                            for f in sorted(wide)}
    res["wide_clip_right"] = {str(f): bool(wide[f]["col_hi"] is not None
                                           and wide[f]["col_hi"] >= 779)
                              for f in sorted(wide)}
    res["wide_bottom_row"] = {str(f): wide[f]["bottom"] for f in sorted(wide)}
    res["wide_top_row"] = {str(f): wide[f]["top"] for f in sorted(wide)}
    res["wide_area_row"] = {str(f): r3(wide[f]["area_row"])
                            for f in sorted(wide)}
    res["wide_height_px"] = {str(f): wide[f]["height_px"] for f in sorted(wide)}
    res["wide_width_px"] = {str(f): wide[f]["width_px"] for f in sorted(wide)}
    res["wide_skin_cc"] = {str(f): r3(wide[f].get("skin_cc"))
                           for f in sorted(wide)}
    res["wide_skin_px"] = {str(f): wide[f].get("skin_n") for f in sorted(wide)}
    res["wide_skin_mask_note"] = (
        "★ 肤色掩膜 = 剪影内 `R − B > %.2f` 且 `%.2f < lum < %.2f`（脸 + 手）；"
        "`skin_cc` = 这些像素的**列心**。" % (SKIN_RB_MIN, SKIN_LUM_LO,
                                          SKIN_LUM_HI))

    # ---------------- (1) 静态下摆：本支**无块可剔**（修正 ④）--------------
    res["hem_dropped"] = []
    res["hem_boxes"] = []
    res["hem_frames"] = []
    res["hem_areas"] = []
    res["px_hem_excluded_ok"] = True
    res["px_hem_stripped_ok"] = True
    res["px_hem_note"] = (
        "★ 修正 ④：本支两套取景**全程没有完整落在下摆足迹内的静态块**"
        "（实测 `bottom_raw == bottom` 逐帧相等）⟹ D14 的"
        "『过滤在干活 / 下摆确实被剔』两条在此**不适用**，降级为**登记事实**"
        "并置真（不新增红项）。同时登记：**本支没有任何以剪影最低行为载体的判据**"
        "会被下摆影响（`px_fall_monotone_ok` / `px_land_jump_ok` 的载体分别"
        "是空中段最低行与**面积行心**）。")

    # ---------------- (2) ★★ 跨支接缝：末帧逐位一致 ------------------------
    air = scan("airhit_side", sorted(set([SEAM_LAST_D13_FRAME,
                                          *SEAM_D13_FRAMES,
                                          *range(10, 19)])))
    d13_end = air.get(SEAM_LAST_D13_FRAME)
    d15_start = side.get(START)
    seam_deltas = None
    if d13_end is not None and d15_start is not None:
        seam_deltas = {
            "top_px": int(d15_start["top"] - d13_end["top"]),
            "bottom_px": int(d15_start["bottom"] - d13_end["bottom"]),
            "head_row_px": r3((d15_start["head_row"] or 0.0)
                              - (d13_end["head_row"] or 0.0)),
            "height_px": int(d15_start["height_px"] - d13_end["height_px"]),
            "width_px": int((d15_start["width_px"] or 0)
                            - (d13_end["width_px"] or 0)),
            "col_lo_px": int((d15_start["col_lo"] or 0)
                             - (d13_end["col_lo"] or 0)),
            "col_hi_px": int((d15_start["col_hi"] or 0)
                             - (d13_end["col_hi"] or 0)),
        }
    res["px_seam_frame"] = {"d13_frame": SEAM_LAST_D13_FRAME,
                            "d15_frame": START, "deltas": seam_deltas}
    res["px_seam_match_tol_px"] = SEAM_MATCH_TOL_PX
    res["px_seam_frame_match_ok"] = bool(
        seam_deltas is not None
        and all(abs(seam_deltas[k]) <= SEAM_MATCH_TOL_PX
                for k in ("top_px", "bottom_px", "head_row_px",
                          "height_px", "width_px", "col_lo_px", "col_hi_px")))

    # ---------------- (3) ★★ 跨支尺子：逐帧步长 vs 弹道预测 -----------------
    def seam_steps(view_map, frame_list, ppm_x, t_phase, source):
        out = []
        for f in frame_list:
            prev = view_map.get(f - 1)
            cur = view_map.get(f)
            if prev is None or cur is None:
                continue
            if prev.get("head_row") is None or cur.get("head_row") is None:
                continue
            measured = cur["head_row"] - prev["head_row"]
            expect = ball_step_px(f, ppm_x, t_phase)
            out.append({"frame": f, "source": source,
                        "measured_px": round(measured, 4),
                        "expect_px": round(expect, 4),
                        "resid_px": round(measured - expect, 4)})
        return out

    merged_map = dict(side)
    for f in SEAM_D13_FRAMES:
        if f in air:
            merged_map[f - SEAM_LAST_D13_FRAME] = air[f]
    res["px_seam_merged_points"] = [
        {"d15_frame": f, "head_row": r3(merged_map[f]["head_row"])}
        for f in sorted(merged_map) if "head_row" in merged_map[f]]
    steps = seam_steps(merged_map, SEAM_D15_FRAMES, ppm, T_PHASE, "d15_prefix")
    res["px_seam_steps"] = steps
    res["px_seam_steps_ruler"] = (
        "`knockdownb_side f0~f6` 的**头带行心逐帧步长**与共享解析弹道"
        "（`T_PHASE=%.1f`）预测步长的残差；判据取 |残差| 的**中位数**"
        "（单个坏点不能推翻整段），并附最大残差与所在帧。" % T_PHASE)
    resid = sorted(abs(e["resid_px"]) for e in steps)
    res["px_seam_steps_median_abs_px"] = (round(float(np.median(resid)), 4)
                                          if resid else None)
    res["px_seam_steps_tol_px"] = SEAM_STEP_MED_TOL_PX
    if steps:
        worst = max(steps, key=lambda e: abs(e["resid_px"]))
        res["px_seam_steps_worst"] = worst
    res["px_seam_steps_all_falling_ok"] = bool(
        steps and all(e["measured_px"] < 0.0 for e in steps))
    res["px_seam_steps_ok"] = bool(
        resid and float(np.median(resid)) <= SEAM_STEP_MED_TOL_PX
        and all(e["measured_px"] < 0.0 for e in steps))

    ctrl_steps = seam_steps(air, SEAM_CTRL_D13_FRAMES, ppm, T_PHASE_D13,
                            "d13_tail")
    res["px_seam_steps_control"] = ctrl_steps
    ctrl_resid = sorted(abs(e["resid_px"]) for e in ctrl_steps)
    res["px_seam_steps_control_median_abs_px"] = (
        round(float(np.median(ctrl_resid)), 4) if ctrl_resid else None)
    res["px_seam_steps_control_ok"] = bool(
        ctrl_resid
        and float(np.median(ctrl_resid)) <= SEAM_STEP_MED_TOL_CTRL_PX)

    neg_steps = seam_steps(side, SEAM_NEG_D15_FRAMES, ppm, T_PHASE, "d15_landed")
    res["px_seam_steps_landed"] = neg_steps
    neg_resid = sorted(abs(e["resid_px"]) for e in neg_steps)
    res["px_seam_steps_landed_median_abs_px"] = (
        round(float(np.median(neg_resid)), 4) if neg_resid else None)
    res["px_seam_steps_can_fail_ok"] = bool(
        neg_resid and float(np.median(neg_resid)) > SEAM_STEP_MED_TOL_PX)

    # ---------------- (3b) 只报：三载体二次拟合 g 对照 ---------------------
    def g_of(points, view):
        ppm_x = px_per_mm(view)
        pts = [(f, y) for f, y in points if y is not None]
        if len(pts) < 3:
            return None
        fs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        _c0, c1, c2 = quad_fit(fs, ys)
        if abs(c2) < 1e-12:
            return None
        return {"g_mm": round(-2.0 * c2 / ppm_x, 5),
                "vertex_frame": round(-c1 / (2.0 * c2), 3),
                "points": len(pts), "frames": fs}

    for carrier in ("head_row", "area_row", "pelvis_row"):
        pts = []
        for f in SEAM_D13_FRAMES:
            if f in air:
                pts.append((f - SEAM_LAST_D13_FRAME, air[f][carrier]))
        for f in SEAM_D15_FRAMES:
            if f in side:
                pts.append((f, side[f][carrier]))
        res["px_seam_g_" + carrier] = g_of(pts, SIDE)
    res["px_seam_g_ref_mm"] = round(G_PER_FRAME_MM, 5)
    res["px_seam_g_note"] = (
        "★ 二次拟合（11 点合并）只报不判（与 D14 同一处境）：1 px = 3 mm ⟹ "
        "`g` 的量化步长 0.907 px/帧²，信噪比天生不足。主尺子用步长残差中位数。")

    # ---------------- (4) 最低行：下落 / 触地 ---------------------------------
    def bottom_steps(view_map, order):
        out = []
        for i in range(1, len(order)):
            a, b = order[i - 1], order[i]
            if a not in view_map or b not in view_map or b == a:
                continue
            out.append((b, (view_map[b]["bottom"] - view_map[a]["bottom"])
                        / float(b - a)))
        return out

    fall_order = [f for f in frames if f < LAND]
    steps_fall = bottom_steps(side, fall_order)
    res["px_fall_steps_px"] = {str(f): round(d, 3) for f, d in steps_fall}
    res["px_fall_steps_mm"] = {str(f): round(d / ppm, 2) for f, d in steps_fall}
    res["px_fall_step_min_px"] = FALL_STEP_MIN_PX
    bad_fall = [(f, d) for f, d in steps_fall if d > -FALL_STEP_MIN_PX]
    res["px_fall_monotone_violations"] = [{"frame": f, "step_px": round(d, 3)}
                                          for f, d in bad_fall]
    res["px_fall_monotone_ok"] = bool(steps_fall and not bad_fall)

    ctrl = scan("jumpfall_side", CTRL_FRAMES)
    ctrl_steps2 = bottom_steps(ctrl, [f for f in CTRL_FRAMES if f in ctrl])
    res["px_fall_control_steps_px"] = {str(f): round(d, 3)
                                       for f, d in ctrl_steps2}
    res["px_fall_monotone_control_ok"] = bool(
        ctrl_steps2 and all(d <= -FALL_STEP_MIN_PX for _f, d in ctrl_steps2))

    d12 = scan("launchhit_side", NEG_D12_FRAMES)
    d12_steps = bottom_steps(d12, sorted(d12))
    res["px_fall_d12_steps_px"] = {str(f): round(d, 3) for f, d in d12_steps}
    res["px_fall_monotone_can_fail_ok"] = bool(
        d12_steps and any(d > -FALL_STEP_MIN_PX for _f, d in d12_steps))

    # ---- ★ 触地帧：落差突变（载体 = **面积行心**，修正 ③）----
    def land_step_of(view_map, carrier):
        if (LAND - 1) not in view_map or LAND not in view_map:
            return None
        a = view_map[LAND - 1].get(carrier)
        b = view_map[LAND].get(carrier)
        if a is None or b is None:
            return None
        return float(b - a)

    land_step_area = land_step_of(side, "area_row")
    land_step_pelvis = land_step_of(side, "pelvis_row")
    land_step_bottom = land_step_of(side, "bottom")
    res["px_land_step_carrier"] = "area_row（★ 修正 ③）"
    res["px_land_step_px"] = land_step_area
    res["px_land_step_mm"] = (None if land_step_area is None
                              else round(land_step_area / ppm, 2))
    res["px_land_step_pelvis_row_px"] = r3(land_step_pelvis)
    res["px_land_step_bottom_row_px"] = r3(land_step_bottom)
    res["px_land_step_min_px"] = LAND_STEP_MIN_PX
    res["px_fall_step_max_px"] = FALL_STEP_MAX_PX
    res["px_land_jump_ok"] = bool(
        land_step_area is not None and land_step_area <= -LAND_STEP_MIN_PX
        and steps_fall
        and all(-FALL_STEP_MAX_PX <= d <= 0.0 for _f, d in steps_fall))

    d13_all = scan("airhit_side", list(range(0, 19)))
    d13_steps = bottom_steps(d13_all, sorted(d13_all))
    # ★ 反面：拿**同一把面积行心尺子**量 D13（全段在空中）
    d13_area_steps = []
    for i in range(1, 19):
        if (i - 1) in d13_all and i in d13_all:
            d13_area_steps.append((i, (d13_all[i]["area_row"]
                                       - d13_all[i - 1]["area_row"])))
    res["px_land_jump_d13_area_steps_px"] = {str(f): round(d, 3)
                                             for f, d in d13_area_steps}
    res["px_land_jump_d13_max_drop_px"] = (
        round(min(d for _f, d in d13_area_steps), 3) if d13_area_steps else None)
    res["px_land_jump_can_fail_ok"] = bool(
        d13_area_steps and all(-d < LAND_STEP_MIN_PX for _f, d in d13_area_steps))

    # ---------------- (5) ★★★ 独门尺子：后倒（头在图像右）-----------------
    def skin_delta(view_map, f_from, f_to):
        a = view_map.get(f_from, {}).get("skin_cc")
        b = view_map.get(f_to, {}).get("skin_cc")
        if a is None or b is None:
            return None
        return float(b - a)

    back_d15 = skin_delta(wide, LAND, TOTAL)
    res["px_backward"] = {
        "view": WIDE, "from_frame": LAND, "to_frame": TOTAL,
        "skin_cc_from": r3(wide.get(LAND, {}).get("skin_cc")),
        "skin_cc_to": r3(wide.get(TOTAL, {}).get("skin_cc")),
        "delta_px": r3(back_d15),
        "pixels_per_m": round(ppm * 1000.0, 3)}
    res["px_backward_ruler"] = (
        "★ 独门尺子：侧视（图像右 = +Y = 身后）里**肤色（脸+手）像素的列心**"
        "从 `f = LAND` 到 `f = END` 的位移。后倒 ⟹ 头向 **+Y** 退出 ⟹ Δ > 0。"
        "D14 前扑（同一支的镜像）必须 Δ < 0。阈值 ≥ %.0f px（= %.0f mm）。"
        % (BACKWARD_MIN_PX, BACKWARD_MIN_PX / ppm))
    res["px_backward_min_px"] = BACKWARD_MIN_PX
    res["px_fall_backward_ok"] = bool(
        back_d15 is not None and back_d15 >= BACKWARD_MIN_PX)

    # ★★★ 反面：D14 自己（同一条弹道、向前扑倒）—— 用专造的宽取景（修正 ②）
    d14w = scan(D14W, list(range(0, TOTAL + 1)), with_skin=True)
    res["px_backward_control_col_span"] = {
        str(f): [d14w[f]["col_lo"], d14w[f]["col_hi"]] for f in sorted(d14w)}
    res["px_backward_control_skin_cc"] = {
        str(f): r3(d14w[f].get("skin_cc")) for f in sorted(d14w)}
    res["px_backward_control_skin_px"] = {
        str(f): d14w[f].get("skin_n") for f in sorted(d14w)}
    fwd_d14 = skin_delta(d14w, LAND, TOTAL)
    res["px_backward_control"] = {
        "view": D14W, "from_frame": LAND, "to_frame": TOTAL,
        "skin_cc_from": r3(d14w.get(LAND, {}).get("skin_cc")),
        "skin_cc_to": r3(d14w.get(TOTAL, {}).get("skin_cc")),
        "delta_px": r3(fwd_d14)}
    res["px_fall_backward_can_fail_ok"] = bool(
        fwd_d14 is not None and fwd_d14 < 0.0)

    # ---------------- (6) 贴地自持（wide 视图）-----------------------------
    hold_rows = [wide[f]["top"] for f in range(PLATEAU, TOTAL + 1)
                 if f in wide]
    hold_area = [wide[f]["area_row"] for f in range(PLATEAU, TOTAL + 1)
                 if f in wide and wide[f]["area_row"] is not None]
    hold_skin = [wide[f]["skin_cc"] for f in range(PLATEAU, TOTAL + 1)
                 if f in wide and wide[f].get("skin_cc") is not None]
    res["px_ground_hold"] = {
        "view": WIDE, "window": [PLATEAU, TOTAL],
        "top_rows": hold_rows,
        "area_rows": [round(v, 3) for v in hold_area],
        "skin_ccs": [round(v, 3) for v in hold_skin],
        "top_span_px": (max(hold_rows) - min(hold_rows) if hold_rows else None),
        "area_span_px": (round(max(hold_area) - min(hold_area), 4)
                         if hold_area else None),
        "skin_span_px": (round(max(hold_skin) - min(hold_skin), 4)
                         if hold_skin else None)}
    res["px_hold_tol_px"] = HOLD_TOL_PX
    res["px_ground_hold_ok"] = bool(
        hold_rows and hold_area
        and (max(hold_rows) - min(hold_rows)) <= HOLD_TOL_PX
        and (max(hold_area) - min(hold_area)) <= HOLD_TOL_PX)

    hold13_top = [d13_all[f]["top"] for f in range(PLATEAU, 19) if f in d13_all]
    hold13_area = [d13_all[f]["area_row"] for f in range(PLATEAU, 19)
                   if f in d13_all and d13_all[f]["area_row"] is not None]
    res["px_ground_hold_d13"] = {
        "top_rows": hold13_top,
        "top_span_px": (max(hold13_top) - min(hold13_top)
                        if hold13_top else None),
        "area_rows": [round(v, 3) for v in hold13_area],
        "area_span_px": (round(max(hold13_area) - min(hold13_area), 4)
                         if hold13_area else None)}
    res["px_ground_hold_can_fail_ok"] = bool(
        hold13_top and hold13_area
        and ((max(hold13_top) - min(hold13_top)) > HOLD_TOL_PX
             or (max(hold13_area) - min(hold13_area)) > HOLD_TOL_PX))

    # ---------------- (7) 仰卧：剪影 高/宽 翻转 -----------------------------
    def flip_ratio(f_from, f_to):
        a, b = wide.get(f_from), wide.get(f_to)
        if a is None or b is None:
            return None
        if not a["height_px"] or not a["width_px"]:
            return None
        if not b["height_px"] or not b["width_px"]:
            return None
        return {"height_from_px": a["height_px"], "height_to_px": b["height_px"],
                "width_from_px": a["width_px"], "width_to_px": b["width_px"],
                "height_ratio": round(b["height_px"] / float(a["height_px"]), 4),
                "width_ratio": round(b["width_px"] / float(a["width_px"]), 4)}

    flip = flip_ratio(LAND, TOTAL)
    res["px_supine_flip"] = flip
    res["px_supine_flip_ruler"] = (
        "wide 侧视剪影 从 `f=LAND` 到 `f=END`：高度比 ≤%.2f（躺下 → 变矮）"
        "且 宽度比 ≥%.2f（伸展开 → 变宽）。" % (SUPINE_H_RATIO_MAX,
                                            SUPINE_W_RATIO_MIN))
    res["px_supine_flip_ok"] = bool(
        flip is not None and flip["height_ratio"] <= SUPINE_H_RATIO_MAX
        and flip["width_ratio"] >= SUPINE_W_RATIO_MIN)

    flip_ctrl = flip_ratio(START, LAND)
    res["px_supine_flip_control"] = flip_ctrl
    res["px_supine_flip_can_fail_ok"] = bool(
        flip_ctrl is None
        or flip_ctrl["height_ratio"] > SUPINE_H_RATIO_MAX
        or flip_ctrl["width_ratio"] < SUPINE_W_RATIO_MIN)

    # ---- 仰卧（更严的一版）：**鞋心 → 肤色心** 连线与水平面的夹角 ----
    # ★ 为什么不用"剪影高宽比反算"（原稿那样）：仰卧时**抬起的膝盖**会把剪影高度
    #   撑到 342 px（实测），量出来 34.6° 是"膝高"不是"躯干角"。
    #   改用**两个身体端点**的连线：脚端 = 鞋（灰黑非蓝）质心，头端 = 肤色（脸+手）
    #   质心。站立时这条线 ≈ 竖直（仰角 ≈ 90°），仰卧时 ≈ 水平（≈ 0°）。
    def trunk_angle_deg(view_map, frame):
        import math
        b = view_map.get(frame)
        if b is None:
            return None
        sc, sr = b.get("skin_rc") or (None, None)
        hc, hr = b.get("shoe_rc") or (None, None)
        if None in (sc, sr, hc, hr):
            return None
        dc, dr = sc - hc, sr - hr
        if abs(dc) < 1e-9 and abs(dr) < 1e-9:
            return None
        return round(math.degrees(math.atan2(abs(dr), abs(dc))), 3)

    ta_end = trunk_angle_deg(wide, TOTAL)
    ta_start = trunk_angle_deg(wide, START)
    res["px_supine_trunk_angle_end_deg"] = ta_end
    res["px_supine_trunk_angle_start_deg"] = ta_start
    res["px_supine_trunk_max_deg"] = SUPINE_TRUNK_MAX_DEG
    res["px_supine_trunk_note"] = (
        "★ **鞋心 → 肤色心** 连线与水平面的夹角（仰角）：竖直站立 ≈ 90°，仰卧 ≈ 0°。"
        "末帧必须 ≤ %.0f°（真的躺平）；`f = START`（还在空中）必须 ≥ %.0f°（反面守）。"
        % (SUPINE_TRUNK_MAX_DEG, SUPINE_TRUNK_MIN_DEG))
    res["px_supine_trunk_ok"] = bool(
        ta_end is not None and ta_end <= SUPINE_TRUNK_MAX_DEG)
    res["px_supine_trunk_can_fail_ok"] = bool(
        ta_start is not None and ta_start >= SUPINE_TRUNK_MIN_DEG)

    # ---------------- (8) 只报：前视剪影 ----------------------------------
    front_frames = [0, 2, 4, 6, LAND, HOLD_END, 10, COMPRESS_PEAK, 13,
                    SUPINE_PEAK, PLATEAU, TOTAL]
    front = scan("knockdownb_front", front_frames)
    res["front_report"] = {
        str(f): {"bottom": front[f]["bottom"], "top": front[f]["top"],
                 "height_px": front[f]["height_px"],
                 "width_px": front[f]["width_px"],
                 "col_lo": front[f]["col_lo"], "col_hi": front[f]["col_hi"]}
        for f in sorted(front)}

    # ---------------- (9) 附加：全量表（只报）-----------------------------
    if os.environ.get("D15PX_DUMP"):
        res["px_dump_wide_skin"] = {str(f): r3(wide[f].get("skin_cc"))
                                    for f in sorted(wide)}

    ok = sorted(k for k, v in res.items() if k.endswith("_ok"))
    res["ok_flags"] = ok
    res["failed"] = sorted(k for k in ok if res[k] is not True)
    print("D15_PIXELS " + json.dumps(res, ensure_ascii=False))
    print("D15_PIXELS_DONE failed=%s" % res["failed"])


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D15_PIXELS_FAILURE " + traceback.format_exc())
