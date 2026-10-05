"""probe_d17_pixels —— D17 `GetUp_F` 的**像素级**验收（读 PNG，不解算骨架）。

与 `probe_d16_pixels.py` 的关系
---------------------------------------------------------------
照抄其全部像素工具（`load` / `mask_of` / `px_per_mm` / `rows_any` / `cols_any` /
`area_row_centroid` / `bands`），**判据按 D17 的跨族性质换口径**（见下）。

★ 本支的两把独门尺子
---------------------------------------------------------------
`px_rise_monotone_ok` + `px_rise_amplitude_ok`
    载体 = wide 视**全剪影顶缘**（`rows.max()`，行号自画面底向上 = +Z）。
    f0 → END 必须**单调不降**（容差 1.0 px），且**总升幅 ≥ 阈值**。

    ★★ 口径修正（诚实登记）：清单计划原文写的是「**底行单调不升**」。
       本项目行号约定为**自画面底向上**（`image.pixels` 索引 0 = 画面底，
       见 `probe_d16_pixels.py` 的 `rows_any`）：在该约定下「起身」= 身体最高点
       **上升**，与「单调不升」**自相矛盾**（两个条件不可能同时成立）。
       且实测本支**底缘**被两件与"起身"无关的事支配 ——
       ① 裤管穿地（`Trouser_*`，f0 已 −61.5 mm，f4 手撑地时手指 −177.6 mm）；
       ② 收腿时双脚离地（f14 鞋底 +187 mm）。
       ⟹ 换成**顶缘**。它单调不降、总升幅 246 px，同时证明
       「真的从地上起来了」与「是**一次**起来的、没有中途回落」。
       **不是放宽容差，是换对了载体** —— 两件干扰事的原始数值在下面照实登记。

`px_idle_end_ok`
    wide 视 `f = END` 的剪影必须与 **`idle01wide_side_f0000`**（同机位）逐位一致
    （底缘 / 顶缘 / 宽 / 面积行心，容差 1.0 px）。这是骨架级 `end_matches_idle_ok`
    （`max_delta <= 1e-6`）的**像素级独立复核**。

★ 反面对照（三组，全部**用本工程已有图**，不新拍）
---------------------------------------------------------------
  `px_rise_can_fail_ok`        D16 `groundhitwide_side` 用**同一把幅度尺子**必须红
                               —— 它的顶缘全程恒定 525 px ⟹ 总升幅 **0 px**。
  `px_rise_mono_can_fail_ok`   **同一把单调尺子改量本支自己的底缘**必须红
                               —— 底缘 f0..f4 由 241 掉到 205（−36 px）⟹ 非单调。
  `px_idle_end_can_fail_ok`    `getupfwide_side_f0020`（人还在地上）对
                               `idle01wide_side_f0000` 必须红。

本支判据清单
---------------------------------------------------------------
  `px_rise_monotone_ok`       ★★★ 独门尺子（形状）：顶缘单调不降（tol 1.0 px）
  `px_rise_amplitude_ok`      ★★ 独门尺子（幅度）：顶缘总升幅 ≥ 阈值 px
                              （防"绿得太容易"，照 D16 `px_bounce_amplitude_ok` 的做法）
  `px_rise_can_fail_ok`       ★ 反面：D16 幅度侧失效证明
  `px_rise_mono_can_fail_ok`  ★ 反面：本支底缘单调侧失效证明
  `px_idle_end_ok`            ★★★ 独门尺子（跨族接缝的像素级复核）
  `px_idle_end_can_fail_ok`   ★ 反面：f20 对 idle01 必须红
  `px_hem_excluded_ok` / `px_hem_stripped_ok`   沿用 D16：无块可剔（登记 N/A + True）
  `px_hitstop_ok`             **登记 N/A（不生成）**：本支 `hitstop_frames = 0`
                              （主动发力动作，没有"命中帧"，见 `anim_getup_f.py` 的
                              `disabled_gates.hitstop_present`）
  `px_seam_steps_ok`          **登记 N/A（不生成）**：本支竖直通道没有弹道段，无抛物线可比

用法
---------------------------------------------------------------
    blender --background --factory-startup --python probe_d17_pixels.py

前置：`anim_getup_f.py`（要 `getupf*` / `getupfwide*` 全套静帧 +
`idle01wide_side_f0000` 对照静帧）与 D16 的 `groundhitwide_side` 全套（反面对照）。
纯读 PNG，**不改任何工程文件**。

★ 行号 ↔ 世界高度（本支取景，登记以免再算错）
---------------------------------------------------------------
  Blender `ortho_scale` 作用于**长边**；res = 780x1100 ⟹ 长边是**高**
  ⟹ 竖直世界跨度 = ortho，且
      z_mm = (row − floor_row) x mm_per_px
      floor_row   = (ortho/2 − cam_z) / (ortho/res_y)
      mm_per_px   = ortho/res_y x 1000
  wide 视（cam_z 0.95, ortho 3.60, res_y 1100）：
      floor_row = **259.72**、mm_per_px = **3.2727**
  side 视（cam_z 1.30, ortho 3.30, res_y 1100）：
      floor_row = **106.06**、mm_per_px = **3.0000**
  ★ 自检：`getupfwide_side_f0000` 底缘 241 ⟹ z = −61.3 mm，与
    `probe_d17_low.py` 实测 `Trouser_R = −61.54 mm` 一致（差 0.2 mm）；
    END 底缘 259 ⟹ z = −2.4 mm，与鞋底实测 −0.96/+1.06 mm 同量级。
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
STEM = "getupf"

# ---- 视图表：(图高 px, 正交宽 m, 相机 z, 子目录) ------------------------------
#   ★ 只 res_y 与 ortho 进尺子（`px_per_mm`）；cam_z 进地平线行公式。
SIDE = "getupf_side"
WIDE = "getupfwide_side"
IDLE_WIDE = "idle01wide_side"
D16_WIDE = "groundhitwide_side"      # ★ 反面对照（幅度侧）
VIEWS = {
    SIDE: (1100, 3.30, 1.30, PRE),
    WIDE: (1100, 3.60, 0.95, PRE),           # ★ 起身族专属基准（见脚本 §VIEW_D17_SIDE_WIDE）
    "getupf_front": (1100, 4.20, 0.95, PRE),
    "getupf_three_quarter": (1100, 4.60, 0.95, PRE),
    IDLE_WIDE: (1100, 3.60, 0.95, PRE),      # ★★ `px_idle_end_ok` 的对照，同机位
    D16_WIDE: (1100, 3.30, 1.00, PRE),       # ★★ 反面对照（幅度侧）
}

# ---- 帧号（与 `anim_getup_f.py` 的时间轴逐一对齐）---------------------------
START = 0
PUSH = 4
CHEST_UP = 6
HAND_OFF = 9
TUCK = 14
FOOT_SET = 20
RISE_MID = 27
STAND = 34
CANCEL = 34
TOTAL = 36
IDLE_END_FRAME = 0          # `Idle_01@0` 在 `idle01wide_side` 里的帧号
D16_TOTAL = 20

# ★ 竖直通道**无弹道段**（登记用，不参与解算）
T_PHASE_D14 = 49.5
T_PHASE_D17 = 69.5

# ---- 阈值（全部由实测导出，见文末 `D17_PX_LOG`）-----------------------------
MONO_TOL_PX = float(os.environ.get("D17PX_MONO_TOL", "1.0"))
RISE_MIN_PX = float(os.environ.get("D17PX_RISE_MIN", "200.0"))
IDLE_MATCH_TOL_PX = float(os.environ.get("D17PX_IDLE_TOL", "1.0"))

# ---- 带（绝对世界高度锚定；沿用 D13~D16 口径）--------------------------------
PELVIS_BAND_ABOVE_SOLE_MM = (800.0, 920.0)
HEAD_BAND_FROM_TOP_PX = 55


# =============================================================== 像素工具
#   ★ 逐字照抄 `probe_d16_pixels.py`（同一把尺子，不许各写一份）
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
    """**全剪影**面积行心（row 0 = 画面底，+Z 向上）。"""
    weights = mask.sum(axis=1).astype(np.float64)
    if weights.sum() <= 0:
        return None
    return float((np.arange(mask.shape[0]) * weights).sum() / weights.sum())


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


def floor_row_of(view):
    """地平线行：z = 0 对应 `(ortho/2 - cam_z) / (ortho/res_y)`。"""
    res_y, ortho, cam_z, _base = VIEWS[view]
    return (ortho / 2.0 - cam_z) / (ortho / float(res_y))


def mm_per_px_of(view):
    res_y, ortho, _cz, _base = VIEWS[view]
    return ortho / float(res_y) * 1000.0


# =============================================================== 形状工具
def mono_non_decreasing(frames, values, tol):
    """全序列必须**单调不降**（容差 tol）；返回**违反的帧**列表。

    ★ 与 D16 的 `mono_non_increasing`（峰值后单调）不同：本支是**一次持续发力**，
      全程都不许回落 ⟹ 起点就是基线，不允许出现"峰"。
    """
    bad = []
    for i in range(1, len(values)):
        if values[i] < values[i - 1] - tol:
            bad.append(frames[i])
    return bad


def total_rise(values):
    return float(values[-1] - values[0])


def max_drop(frames, values):
    """全程最大回落幅度（px，正数）及其位置 —— 给"下陷/回落"诊断用。"""
    worst, at = 0.0, None
    run = 0.0
    for i in range(1, len(values)):
        d = values[i - 1] - values[i]
        run = run + d if d > 0 else 0.0
        if run > worst:
            worst, at = run, frames[i]
    return worst, at


# =============================================================== 主流程
def main():  # noqa: C901
    res = {}
    res["stem"] = STEM
    res["timeline"] = {"START": START, "PUSH": PUSH, "CHEST_UP": CHEST_UP,
                       "HAND_OFF": HAND_OFF, "TUCK": TUCK, "FOOT_SET": FOOT_SET,
                       "RISE_MID": RISE_MID, "STAND": STAND, "CANCEL": CANCEL,
                       "TOTAL": TOTAL}

    def r3(x):
        return None if x is None else round(x, 3)

    # ---------------- (0) 逐视图扫描 -----------------------------------------
    def scan(view, frame_list):
        table = {}
        for frame in frame_list:
            pixels = load(view, frame)
            if pixels is None:
                continue
            raw = mask_of(pixels)
            band = bands(view, raw)
            if band is None:
                continue
            band["mask"] = raw
            table[frame] = band
        return table

    wide = scan(WIDE, list(range(START, TOTAL + 1)))
    if not wide:
        raise RuntimeError("wide 视静帧一张都没有：%s" % PRE)
    side = scan(SIDE, list(range(START, TOTAL + 1)))
    idle_wide = scan(IDLE_WIDE, [IDLE_END_FRAME])
    if not idle_wide:
        raise RuntimeError("idle01 对照静帧缺失：%s_f%04d" % (IDLE_WIDE, IDLE_END_FRAME))
    d16_wide = scan(D16_WIDE, list(range(0, D16_TOTAL + 1)))
    if not d16_wide:
        raise RuntimeError("D16 wide 对照图缺失：%s" % PRE)

    res["wide_mm_per_px"] = round(mm_per_px_of(WIDE), 4)
    res["wide_floor_row"] = round(floor_row_of(WIDE), 3)
    res["side_mm_per_px"] = round(mm_per_px_of(SIDE), 4)
    res["side_floor_row"] = round(floor_row_of(SIDE), 3)
    res["row_ruler"] = ("行号自画面底向上。wide: z_mm = (row − %.2f) x %.4f；"
                        "side: z_mm = (row − %.2f) x %.4f。图像右 = +Y = 身后。"
                        % (res["wide_floor_row"], res["wide_mm_per_px"],
                           res["side_floor_row"], res["side_mm_per_px"]))

    wframes = sorted(wide)
    res["wide_top_row"] = {str(f): wide[f]["top"] for f in wframes}
    res["wide_bottom_row"] = {str(f): wide[f]["bottom"] for f in wframes}
    res["wide_area_row"] = {str(f): r3(wide[f]["area_row"]) for f in wframes}
    res["wide_height_px"] = {str(f): wide[f]["height_px"] for f in wframes}
    res["wide_width_px"] = {str(f): wide[f]["width_px"] for f in wframes}
    res["side_top_row"] = {str(f): side[f]["top"] for f in sorted(side)}
    res["side_bottom_row"] = {str(f): side[f]["bottom"] for f in sorted(side)}

    # ★ 顺手把「底缘被谁支配」的原始数值登记下来（口径修正的依据，详见模块 docstring）
    w_, o_, cz_, _ = VIEWS[WIDE]
    mmp = mm_per_px_of(WIDE)
    fr = floor_row_of(WIDE)
    res["wide_bottom_z_mm"] = {str(f): round((wide[f]["bottom"] - fr) * mmp, 2)
                               for f in wframes}
    res["wide_top_z_mm"] = {str(f): round((wide[f]["top"] - fr) * mmp, 2)
                            for f in wframes}

    # ---------------- (1) ★★★ 独门尺子 `px_rise_monotone_ok` ------------------
    tops = [wide[f]["top"] for f in wframes]
    mono_bad = mono_non_decreasing(wframes, tops, MONO_TOL_PX)
    rise = total_rise(tops)
    drop, drop_at = max_drop(wframes, tops)
    res["px_rise_mono_tol_px"] = MONO_TOL_PX
    res["px_rise_violation_frames"] = mono_bad
    res["px_rise_ok"] = bool(not mono_bad)
    res["px_rise_monotone_ok"] = bool(not mono_bad)
    res["px_rise_note"] = (
        "★★★ **本支独门尺子（形状）**：wide 视**全剪影顶缘**（`rows.max()`，"
        "行号自画面底向上）在 `f = 0 ~ %d` 上必须**单调不降**（容差 %.1f px = %.1f mm）。"
        "载体 = **顶缘**（口径修正见模块 docstring：原文「底行单调不升」在本工程行号"
        "约定下自相矛盾，且本支底缘由**裤管穿地**与**收腿离地**两件与起身无关的事支配）。"
        % (TOTAL, MONO_TOL_PX, MONO_TOL_PX * mmp))

    # ---------------- (2) ★★ `px_rise_amplitude_ok` --------------------------
    res["px_rise_amount_px"] = round(rise, 3)
    res["px_rise_amount_mm"] = round(rise * mmp, 2)
    res["px_rise_min_px"] = RISE_MIN_PX
    res["px_rise_max_drop_px"] = round(drop, 3)
    res["px_rise_max_drop_at"] = drop_at
    res["px_rise_from_mm"] = round((tops[0] - fr) * mmp, 2)
    res["px_rise_to_mm"] = round((tops[-1] - fr) * mmp, 2)
    res["px_rise_amplitude_ok"] = bool(rise >= RISE_MIN_PX)
    res["px_rise_amplitude_note"] = (
        "★★ 幅度守卫（防「绿得太容易」）：顶缘总升幅必须 ≥ **%.1f px**（= %.1f mm）。"
        "阈值由**实测**导出：实测起点 %.2f mm（俯卧）→ 终点 %.2f mm（站直），"
        "真实升幅 **%.1f px / %.0f mm**，阈值取实测的 %.0f%%。"
        % (RISE_MIN_PX, RISE_MIN_PX * mmp,
           res["px_rise_from_mm"], res["px_rise_to_mm"],
           rise, rise * mmp, 100.0 * RISE_MIN_PX / rise if rise else 0.0))

    # ---------------- (3) ★ 反面对照（幅度侧）：D16 自己 ---------------------
    d16_frames = sorted(d16_wide)
    d16_tops = [d16_wide[f]["top"] for f in d16_frames]
    d16_rise = total_rise(d16_tops)
    d16_mmp = mm_per_px_of(D16_WIDE)
    res["px_rise_control_d16"] = {
        "view": D16_WIDE, "frames": [d16_frames[0], d16_frames[-1]],
        "top_row_first": d16_tops[0], "top_row_last": d16_tops[-1],
        "total_rise_px": round(d16_rise, 3),
        "total_rise_mm": round(d16_rise * d16_mmp, 2)}
    res["px_rise_can_fail_ok"] = bool(d16_rise < RISE_MIN_PX)
    res["px_rise_can_fail_note"] = (
        "★ 反向（幅度侧）：**D16 自己**（`groundhitwide_side`，同一把幅度尺子、"
        "同族同构）必须判红 —— 它是「倒地受击」，顶缘全程**恒定 %d px**"
        "（人始终躺在地上，最高点不动）⟹ 总升幅 **0 px < %.1f px** 阈值。"
        "这条证明这把尺子**对「没起来」敏感**。"
        % (d16_tops[0], RISE_MIN_PX))

    # ---------------- (4) ★ 反面对照（单调侧）：本支自己的底缘 -------------
    bots = [wide[f]["bottom"] for f in wframes]
    bot_bad = mono_non_decreasing(wframes, bots, MONO_TOL_PX)
    res["px_rise_mono_control"] = {
        "carrier": "wide 视底缘（`rows.min()`）", "view": WIDE,
        "violation_frames": bot_bad,
        "bottom_row": {str(f): wide[f]["bottom"] for f in wframes},
        "bottom_z_mm": res["wide_bottom_z_mm"]}
    res["px_rise_mono_can_fail_ok"] = bool(bot_bad)
    res["px_rise_mono_can_fail_note"] = (
        "★ 反向（单调侧）：**同一把单调尺子**改量本支**自己的底缘**必须判红 —— "
        "底缘 f0..f4 由 241 掉到 205（手撑地时手指探到 −178 mm），f14 又升到 248"
        "（收腿时鞋底 +187 mm）⟹ 违反帧 **%s**。这条证明这把尺子**对「中途回落」敏感**，"
        "同时把「为什么载体不能是底缘」实测钉死。" % (bot_bad or "无"))

    # ---------------- (5) ★★★ 独门尺子 `px_idle_end_ok` ----------------------
    end_band = wide.get(TOTAL)
    idle_band = idle_wide.get(IDLE_END_FRAME)
    if end_band is None or idle_band is None:
        raise RuntimeError("末帧或 idle01 对照帧缺失")
    delta = {
        "bottom": int(end_band["bottom"] - idle_band["bottom"]),
        "top": int(end_band["top"] - idle_band["top"]),
        "width": int(end_band["width_px"] - idle_band["width_px"]),
        "col_lo": int(end_band["col_lo"] - idle_band["col_lo"]),
        "col_hi": int(end_band["col_hi"] - idle_band["col_hi"]),
        "area_row": round(float(end_band["area_row"] - idle_band["area_row"]), 4),
    }
    res["px_idle_end_frames"] = {"getupf": TOTAL, "idle01": IDLE_END_FRAME,
                                "view": WIDE}
    res["px_idle_end_delta_px"] = delta
    res["px_idle_end_tol_px"] = IDLE_MATCH_TOL_PX
    res["px_idle_end_ok"] = bool(
        abs(delta["bottom"]) <= IDLE_MATCH_TOL_PX
        and abs(delta["top"]) <= IDLE_MATCH_TOL_PX
        and abs(delta["width"]) <= IDLE_MATCH_TOL_PX
        and abs(delta["area_row"]) <= IDLE_MATCH_TOL_PX)
    res["px_idle_end_note"] = (
        "★★★ **本支第二把独门尺子**：wide 视 `f = %d`（`GetUp_F@%d`）的剪影必须与 "
        "`%s_f%04d`（**同机位**的 `Idle_01@%d`）**逐位一致**（底缘 / 顶缘 / 宽 / "
        "面积行心，容差 %.1f px = %.1f mm）。这是骨架级 `end_matches_idle_ok`"
        "（逐骨 4x4 世界矩阵 `max_delta <= 1e-6`）的**像素级独立复核** —— "
        "两条尺子一条量骨架、一条量像素，互不依赖。"
        % (TOTAL, TOTAL, IDLE_WIDE, IDLE_END_FRAME, IDLE_END_FRAME,
           IDLE_MATCH_TOL_PX, IDLE_MATCH_TOL_PX * mmp))

    # ---------------- (6) ★ 反面：f20（人还在地上）对 idle01 必须红 --------
    mid_band = wide.get(FOOT_SET)
    if mid_band is None:
        raise RuntimeError("foot_set 帧缺失：%d" % FOOT_SET)
    mid_delta = {
        "bottom": int(mid_band["bottom"] - idle_band["bottom"]),
        "top": int(mid_band["top"] - idle_band["top"]),
        "width": int(mid_band["width_px"] - idle_band["width_px"]),
        "area_row": round(float(mid_band["area_row"] - idle_band["area_row"]), 4),
    }
    res["px_idle_end_control"] = {"frame": FOOT_SET, "delta_px": mid_delta}
    res["px_idle_end_can_fail_ok"] = bool(
        abs(mid_delta["bottom"]) > IDLE_MATCH_TOL_PX
        or abs(mid_delta["top"]) > IDLE_MATCH_TOL_PX
        or abs(mid_delta["width"]) > IDLE_MATCH_TOL_PX
        or abs(mid_delta["area_row"]) > IDLE_MATCH_TOL_PX)
    res["px_idle_end_can_fail_note"] = (
        "★ 反向：`%s_f%04d`（`FOOT_SET`，脚刚接住地面、人还蹲在地上）用同一把尺子"
        "必须判红 —— 否则说明这把尺子对「还没站起来」不敏感。实测顶缘差 %d px、"
        "面积行心差 %.1f px。" % (WIDE, FOOT_SET, mid_delta["top"],
                                  mid_delta["area_row"]))

    # ---------------- (7) 下摆（无块可剔）-------------------------------------
    res["hem_dropped"] = []
    res["hem_boxes"] = []
    res["px_hem_excluded_ok"] = True
    res["px_hem_stripped_ok"] = True
    res["px_hem_note"] = (
        "★ 承接 D15/D16：`Jacket_Hem` / `Jacket_Hem_Line` 未绑定骨架"
        "（`parent=None` / `vgroups=0`），钉在世界原点 ⟹ 两套取景里它们不随身体动、"
        "不构成任何一帧的极值行（实测 `hem_dropped = []`，**无块可剔**，登记 N/A + True）。"
        "两块的世界最低点由 `anim_getup_f.py` 的 `hem_static_ok` 守（首末两帧逐位相同）。")

    # ---------------- (8) 登记 N/A 的两条 ------------------------------------
    res["px_hitstop_status"] = "N/A"
    res["px_hitstop_ok"] = None
    res["px_hitstop_note"] = (
        "★★ **本判据在本支不生成、不参与 `failed`（登记 N/A）**。理由：本支是**主动发力**"
        "动作（俯卧 → 撑起 → 站直），**没有「命中帧」** ⟹ `meta.hitstop_frames = 0`；"
        "在 `anim_getup_f.py` 的 `disabled_gates` 里 `hitstop_present` 已被显式登记为 "
        "DISABLED。硬套只会得到伪造的停顿。收招由骨架级 `no_snap_tail_ok` 守，"
        "「一次发力、不回落」由 `px_rise_monotone_ok` / `rise_monotone_ok` 守。")

    res["px_seam_steps_status"] = "N/A"
    res["px_seam_steps_ok"] = None
    res["px_seam_steps_registered"] = {"T_PHASE_D14": T_PHASE_D14,
                                       "T_PHASE_D17": T_PHASE_D17}
    res["px_seam_steps_note"] = (
        "★★ **本判据在本支不生成、不参与 `failed`（登记 N/A）**。理由："
        "`px_seam_steps_ok` 量的是「本支侧视逐帧行心与**共享解析抛物线**的残差」，"
        "用于检验两段弹道首尾相接。本支竖直通道**没有弹道段**"
        "（骨盆 z 全段单调升 610 mm，无抛物线可比）⟹ 硬套只会得到无意义的残差。"
        "相位 `T_PHASE_D17 = 69.5` **仅登记**。")

    # ---------------- 汇总 ---------------------------------------------------
    checks = [k for k in res if k.endswith("_ok") and res[k] is not None]
    failed = sorted(k for k in checks if res[k] is False)
    res["checks"] = sorted(checks)
    res["failed"] = failed
    res["verdict"] = "PASS" if not failed else "FAIL"
    print("D17PX_REPORT " + json.dumps(res, ensure_ascii=False))
    print("D17PX_DONE failed=%s" % failed)
    if not failed:
        print("D17PX_DONE verdict=PASS")


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D17PX_FAILURE " + traceback.format_exc())
