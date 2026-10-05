"""probe_d18_pixels —— D18 `GetUp_B` 的**像素级**验收（只读 PNG，不改任何工程文件）。

与 `probe_d17_pixels.py` 的关系
---------------------------------------------------------------
照抄其全部像素工具（`load` / `mask_of` / `px_per_mm` / `rows_any` / `cols_any` /
`area_row_centroid` / `bands`），**判据按 D18 的跨族性质换口径**（见下）。

★★★ 本支实测出三件**必须换**的事（全部由实测钉死，不是放宽容差）
---------------------------------------------------------------
(A) ★★★ **「衣摆静止块」必须真的剔掉 —— D15/D16/D17 登记的「无块可剔」是错的。**
    `Jacket_Hem` / `Jacket_Hem_Line` 未蒙皮（`vgroups=0`、`parent=None`），
    世界包围盒**逐帧恒定**（`probe_c11_belt` 实测）：
        `Jacket_Hem`       z [903.0, 926.0] mm、y [−121.94, +129.03] mm
        `Jacket_Hem_Line`  z [897.5, 901.5] mm、y [−119.96, +126.03] mm
    在 wide 视里它落在 **cols 276..354、rows 533..543**。而 D18 **从仰卧起步**，
    身体在 f0~f22 **全程低于 926 mm** ⟹ **顶缘整段被这块静止薄片接管**：
        实测 raw 顶缘 f0~f22 **恒 542 px**（= (926 − 259.722×mm) 那一行），
        剔除后 f0 顶缘 = **390 px**（= 角色自己：`Shoe_Sole_L` z **427.8 mm**）。
    ⟹ 不剔这块，本支的"顶缘尺子"**量的是一块不动的布**，`px_rise_amplitude_ok`
    会被算成 542→788 = 246 px（**正好等于 D17 当年报的 246 px**）。
    ★ **诚实登记：D17 的 `px_rise_*` 也是被同一块布污染的**（它的 `hem_dropped = []`
    是**硬编码**，从来没有真的算过）。剔除后 D17 的真实顶缘升幅是 **391 px**（不是 246 px）。
    D17 的**结论不变**（两种口径都单调、都 ≥ 阈值；`px_rise_can_fail_ok` 用 D16
    的顶缘，剔除后升幅 **−2 px** 仍然见红）⟹ **不回改 D17 已完成条目**，
    但把修正后的数字登记在此 + 写进 D18 日志的「遗留问题」，交给下一支决定是否回补。

(B) **取景基准**：**另立 `VIEW_D18_SIDE_WIDE`**，机位中心 y = **+250 mm**。
    D17 从 y = −550 走到 0（中点 −275）⟹ 基准取中心 −300；
    D18 从 y = **+470** 走到 0（中点 **+235**）⟹ 新基准取 **+250**。
    ★ 照抄 D17 的 −300 会让起点（y = +470）**被切出画面右缘**。
    跨支尺子**只比行、不比列**（列随取景中心平移，行只随 cam_z / ortho 变）。

(C) **独门尺子的窗口**：`px_rise_monotone_ok` 的载体仍是**全剪影顶缘**
    （与 D17 同一把尺子、同一口径），但**起点从 `START` 挪到 `LEGS_DOWN`**。
    实测（`_d18_topwho.py`，逐对象求最高点）——**顶缘由谁接管是分段的**：
        f0~f2   **抬起的鞋底**（`Shoe_Sole_L` z **427.8 → 409.1 → 393.2 mm**）
        f3~f22  **躯干 / 翻领**（`Jacket_Lapel_R` 等）
        f25~    **头**（`Hair_Mass`，1139 → 1731 mm）
    ⟹ 起身第一段是"**腿先落下**"，顶缘**先降 34.6 mm = 10.6 px**（f0 390 → f2 379），
    然后一次不停地升到站姿。**"从 f0 起单调"在 D18 上必红，而且是正确的**。
    ★ **反面对照 ② = 同一把尺子量 `[START, END]`**（含落腿段）**必须红**，
      它同时把"为什么不能用从 f0 起的顶缘"实测钉死。
    ★ 诚实登记：清单 §1 风险 2 **预告对了机制**（最高点是脚、落腿段先降），
      但**幅度比预告小得多**（不是"脚尖 391 mm 落到地面"，而是**只降 34.6 mm**）——
      因为落腿段还没走完，躯干就已经接管了顶缘。**以实测为准。**

`px_idle_end_ok`
    wide 视 `f = END(46)` 的剪影必须与 **`idle01wideb_side_f0000`**（**D18 同机位**重渲的
    `Idle_01@0`）逐位一致（底缘 / 顶缘 / 宽 / 面积行心，容差 1.0 px）。这是骨架级
    `end_matches_idle_ok`（逐骨 4×4 世界矩阵 `max_delta <= 1e-6`）的**像素级独立复核**。
    ★ 用 `idle01wideb_*`（D18 机位、中心 +250，本轮新渲）**不是** `idle01wide_*`
    （D17 机位、中心 −300）。

★ 反面对照（三组，全部用本工程已有 / 本轮已渲的图，不新拍）
---------------------------------------------------------------
  `px_rise_can_fail_ok`        D16 `groundhitwide_side` 用**同一把幅度尺子**必须红
                               —— 剔除衣摆块后顶缘总升幅 **−2 px** ⟹ 见红。
  `px_rise_mono_can_fail_ok`   **同一把单调尺子**改量本支 `[START, END]`（含落腿段）
                               必须红 —— 违反帧 **`[1, 2]`**（390 → 384 → 379）。
  `px_idle_end_can_fail_ok`    `getupbwide_side_f0030`（`FOOT_SET`，人还蹲着）对
                               `idle01wideb_side_f0000` 必须红。

本支判据清单
---------------------------------------------------------------
  `px_rise_monotone_ok`       ★★★ 独门尺子（形状）：顶缘单调不降，窗口 `[LEGS_DOWN, END]`
  `px_rise_amplitude_ok`      ★★ 独门尺子（幅度）：顶缘总升幅 ≥ 阈值 px（实测 80%）
  `px_rise_can_fail_ok`       ★ 反面：幅度侧失效证明（D16）
  `px_rise_mono_can_fail_ok`  ★ 反面：单调侧失效证明（本支 `[START, END]`）
  `px_idle_end_ok`            ★★★ 独门尺子（跨族接缝的像素级复核）
  `px_idle_end_can_fail_ok`   ★ 反面：`FOOT_SET` 对 idle01 必须红
  `px_hem_excluded_ok`        ★★ **本支新增，真判据（不是 N/A）**：
                              实测"衣摆块**真的占据了极值行**"（raw 顶缘 ≠ 剔除后顶缘的帧数 ≥ 1）
                              —— 证明这块布**确实必须剔**，而不是"无块可剔"。
  `px_hem_stripped_ok`        ★★ **本支新增，真判据**：剔除后顶缘读数**确实变了**
                              （首帧 raw 542 px → 剔除后 390 px）—— 与上一条互为印证。
  `px_hitstop_ok`             **登记 N/A（不生成）**：本支 `hitstop_frames = 0`
  `px_seam_steps_ok`          **登记 N/A（不生成）**：本支竖直通道没有弹道段

用法
---------------------------------------------------------------
    blender --background --factory-startup --python probe_d18_pixels.py

前置：`anim_getup_b.py`（要 `getupb*` / `getupbwide*` 全套静帧 +
`idle01wideb_side_f0000` 同机位对照静帧）与 D16 的 `groundhitwide_side` 全套（反面对照）。

★ 行号 ↔ 世界高度（本支取景，登记以免再算错）
---------------------------------------------------------------
  Blender `ortho_scale` 作用于**长边**；res = 780x1100 ⟹ 长边是**高**
  ⟹ 竖直世界跨度 = ortho，且
      z_mm = (row − floor_row) x mm_per_px
      floor_row   = (ortho/2 − cam_z) / (ortho/res_y)
      mm_per_px   = ortho/res_y x 1000
  wide 视（cam_z 0.95, ortho 3.60, res_y 1100）：floor_row = 259.722、mm_per_px = 3.2727
  side 视（cam_z 1.30, ortho 3.30, res_y 1100）：floor_row = 116.667、mm_per_px = 3.0000
  ★ 自检：`getupbwide_side_f0000` 底缘 230 ⟹ z = −97.2 mm，与 `probe_d18_baseline`
    实测 `Trouser_R = −97.21 mm` 一致（差 0.01 mm）；剔除衣摆后顶缘 390 ⟹ z = 426.3 mm，
    与 `_d18_topwho.py` 实测 `Shoe_Sole_L = 427.8 mm` 一致（差 1.5 mm）。
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
STEM = "getupb"

# ---- 视图表：(图高 px, 正交宽 m, 相机 z, 取景中心 y mm, 子目录) ---------------
#   ★ res_y / ortho 进尺子（`px_per_mm`）；cam_z 进地平线行；center_y 进"列"换算。
SIDE = "getupb_side"
WIDE = "getupbwide_side"
IDLE_WIDE = "idle01wideb_side"       # ★★ D18 **同机位**重渲的 idle01（不是 D17 的）
D16_WIDE = "groundhitwide_side"      # ★ 反面对照（幅度侧）
VIEWS = {
    SIDE: (1100, 3.30, 1.30, 235.0, PRE),            # = VIEW_D18_SIDE
    WIDE: (1100, 3.60, 0.95, 250.0, PRE),            # ★ 起身族第二套基准（中心 y = +250）
    "getupb_front": (1100, 4.20, 0.95, 250.0, PRE),
    "getupb_three_quarter": (1100, 4.60, 0.95, 250.0, PRE),
    IDLE_WIDE: (1100, 3.60, 0.95, 250.0, PRE),       # ★★ 与 WIDE 同机位
    D16_WIDE: (1100, 3.30, 1.00, 500.0, PRE),        # ★★ 反面对照（幅度侧）
}

# ---- ★★★ 「衣摆静止块」世界包围盒（`probe_c11_belt` 实测；逐帧恒定，两块取并集）----
#   `Jacket_Hem` z [903.0, 926.0] / `Jacket_Hem_Line` z [897.5, 901.5]
#   y 并集 [−121.94, +129.03] mm
HEM_WORLD = (-121.94, 897.5, 129.03, 926.0)          # (y_lo, z_lo, y_hi, z_hi)

# ---- 帧号（**输出帧空间**，与 `anim_getup_b.py` 的 `_OUT_PHASES` 逐一对齐）-----
START = 0
LEGS_DOWN = 4
PLANT = 7
CHEST_UP = 11
HAND_OFF = 20
TUCK = 22
FOOT_SET = 30
RISE_MID = 34
STAND = 38
CANCEL = 38
TOTAL = 40
IDLE_END_FRAME = 0
D16_TOTAL = 20
SRC_TOTAL = 40                       # 定稿：源帧 == 输出帧（`OUT_TOTAL=40`，恒等映射）

# ★ 竖直通道**无弹道段**（登记用，不参与解算）
T_PHASE_D17 = 69.5
T_PHASE_D18 = 89.5

# ---- 阈值（全部由实测导出，见文末 `D18PX_REPORT`）---------------------------
MONO_TOL_PX = float(os.environ.get("D18PX_MONO_TOL", "1.0"))
RISE_MIN_PX = float(os.environ.get("D18PX_RISE_MIN", "320.0"))
IDLE_MATCH_TOL_PX = float(os.environ.get("D18PX_IDLE_TOL", "1.0"))

# ---- 带（绝对世界高度锚定；沿用 D13~D17 口径）--------------------------------
PELVIS_BAND_ABOVE_SOLE_MM = (800.0, 920.0)
HEAD_BAND_FROM_TOP_PX = 55


# =============================================================== 像素工具
#   ★ 逐字照抄 `probe_d16_pixels.py` / `probe_d17_pixels.py`（同一把尺子）
def load(view, frame):
    _res, _ortho, _cz, _cy, base = VIEWS[view]
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


def hem_cols_rows(view):
    """★ 衣摆静止块在**本视图**里的屏幕盒 `(col_lo, col_hi, row_lo, row_hi)`。

    纯投影：`col = W/2 + (y − center_y) / mm_per_px`、`row = floor_row + z / mm_per_px`。
    盒外再各放 1 px 余量（抗 float32 半像素误差）。
    """
    res_y, ortho, cam_z, cy, _base = VIEWS[view]
    mm = ortho / float(res_y) * 1000.0
    width = 780
    col_c = width / 2.0
    floor = (ortho / 2.0 - cam_z) / (ortho / float(res_y))
    y_lo, z_lo, y_hi, z_hi = HEM_WORLD
    c0 = int(np.floor(col_c + (y_lo - cy) / mm)) - 1
    c1 = int(np.ceil(col_c + (y_hi - cy) / mm)) + 1
    r0 = int(np.floor(floor + z_lo / mm)) - 1
    r1 = int(np.ceil(floor + z_hi / mm)) + 1
    return (max(c0, 0), min(c1, width - 1),
            max(r0, 0), min(r1, res_y - 1))


def strip_hem(mask, view):
    """把衣摆静止块的屏幕盒**置空**，返回新掩码（不改原图）。"""
    c0, c1, r0, r1 = hem_cols_rows(view)
    out = mask.copy()
    out[r0:r1 + 1, c0:c1 + 1] = False
    return out


def px_per_mm(view):
    res_y, ortho, _cam_z, _cy, _base = VIEWS[view]
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
    res_y, ortho, cam_z, _cy, _base = VIEWS[view]
    return (ortho / 2.0 - cam_z) / (ortho / float(res_y))


def mm_per_px_of(view):
    res_y, ortho, _cz, _cy, _base = VIEWS[view]
    return ortho / float(res_y) * 1000.0


# =============================================================== 形状工具
def mono_non_decreasing(frames, values, tol):
    """全序列必须**单调不降**（容差 tol）；返回**违反的帧**列表。"""
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


def cum_drop_into(frames, values, stop_frame):
    """`[frames[0], stop_frame]` 区间内的**累计**回落（px）—— 量"落腿段"那一下。"""
    total, last = 0.0, values[0]
    for f, v in zip(frames, values):
        if f > stop_frame:
            break
        if v < last:
            total += last - v
        last = v
    return total


# =============================================================== 主流程
def main():  # noqa: C901
    res = {}
    res["stem"] = STEM
    res["timeline"] = {"START": START, "LEGS_DOWN": LEGS_DOWN, "PLANT": PLANT,
                       "CHEST_UP": CHEST_UP, "HAND_OFF": HAND_OFF, "TUCK": TUCK,
                       "FOOT_SET": FOOT_SET, "RISE_MID": RISE_MID,
                       "STAND": STAND, "CANCEL": CANCEL, "TOTAL": TOTAL,
                       "src_total": SRC_TOTAL}

    def r3(x):
        return None if x is None else round(x, 3)

    # ---------------- (0) 逐视图扫描（同时留 raw 与 stripped 两套）------------
    def scan(view, frame_list):
        table = {}
        for frame in frame_list:
            pixels = load(view, frame)
            if pixels is None:
                continue
            raw = mask_of(pixels)
            cut = strip_hem(raw, view)
            band_raw = bands(view, raw)
            band = bands(view, cut)
            if band is None:
                continue
            band["raw_top"] = band_raw["top"]
            band["raw_bottom"] = band_raw["bottom"]
            band["mask"] = cut
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
    res["hem_world_box_mm"] = {"y": [HEM_WORLD[0], HEM_WORLD[2]],
                               "z": [HEM_WORLD[1], HEM_WORLD[3]]}
    res["hem_screen_box_px"] = {v: list(hem_cols_rows(v)) for v in (WIDE, SIDE, D16_WIDE)}
    res["row_ruler"] = ("行号自画面底向上。wide: z_mm = (row − %.2f) x %.4f；"
                        "side: z_mm = (row − %.2f) x %.4f。图像右 = +Y = 身后。"
                        % (res["wide_floor_row"], res["wide_mm_per_px"],
                           res["side_floor_row"], res["side_mm_per_px"]))

    wframes = sorted(wide)
    res["wide_top_row"] = {str(f): wide[f]["top"] for f in wframes}
    res["wide_raw_top_row"] = {str(f): wide[f]["raw_top"] for f in wframes}
    res["wide_bottom_row"] = {str(f): wide[f]["bottom"] for f in wframes}
    res["wide_area_row"] = {str(f): r3(wide[f]["area_row"]) for f in wframes}
    res["wide_height_px"] = {str(f): wide[f]["height_px"] for f in wframes}
    res["wide_width_px"] = {str(f): wide[f]["width_px"] for f in wframes}
    res["side_top_row"] = {str(f): side[f]["top"] for f in sorted(side)}
    res["side_bottom_row"] = {str(f): side[f]["bottom"] for f in sorted(side)}

    mmp = mm_per_px_of(WIDE)
    fr = floor_row_of(WIDE)
    res["wide_bottom_z_mm"] = {str(f): round((wide[f]["bottom"] - fr) * mmp, 2)
                               for f in wframes}
    res["wide_top_z_mm"] = {str(f): round((wide[f]["top"] - fr) * mmp, 2)
                            for f in wframes}
    res["wide_raw_top_z_mm"] = {str(f): round((wide[f]["raw_top"] - fr) * mmp, 2)
                                for f in wframes}

    # ---------------- (1) ★★★ 独门尺子 `px_rise_monotone_ok` --------------
    win = [f for f in wframes if f >= LEGS_DOWN]
    tops_w = [wide[f]["top"] for f in win]
    mono_bad = mono_non_decreasing(win, tops_w, MONO_TOL_PX)
    rise = total_rise(tops_w)
    res["px_rise_window"] = [LEGS_DOWN, TOTAL]
    res["px_rise_mono_tol_px"] = MONO_TOL_PX
    res["px_rise_violation_frames"] = mono_bad
    res["px_rise_ok"] = bool(not mono_bad)
    res["px_rise_monotone_ok"] = bool(not mono_bad)
    res["px_rise_note"] = (
        "★★★ **本支独门尺子（形状）**：wide 视**全剪影顶缘**（`rows.max()`，"
        "行号自画面底向上、**已剔除衣摆静止块**）在 `f = LEGS_DOWN(%d) ~ %d` 上必须"
        "**单调不降**（容差 %.1f px = %.1f mm）。载体仍是**顶缘**（与 D17 同一把尺子），"
        "**两处换口径**：① 剔除衣摆块（见 §A）；② 起点从 `START` 挪到 `LEGS_DOWN`"
        "（见 §C：落腿段顶缘先降 %.1f mm = %.1f px）。"
        % (LEGS_DOWN, TOTAL, MONO_TOL_PX, MONO_TOL_PX * mmp,
           cum_drop_into(wframes, [wide[f]["top"] for f in wframes], LEGS_DOWN) * mmp,
           cum_drop_into(wframes, [wide[f]["top"] for f in wframes], LEGS_DOWN)))

    # ---------------- (2) ★★ `px_rise_amplitude_ok` --------------------------
    res["px_rise_amount_px"] = round(rise, 3)
    res["px_rise_amount_mm"] = round(rise * mmp, 2)
    res["px_rise_min_px"] = RISE_MIN_PX
    res["px_rise_from_mm"] = round((tops_w[0] - fr) * mmp, 2)
    res["px_rise_to_mm"] = round((tops_w[-1] - fr) * mmp, 2)
    res["px_rise_amplitude_ok"] = bool(rise >= RISE_MIN_PX)
    res["px_rise_amplitude_note"] = (
        "★★ 幅度守卫（防「绿得太容易」）：顶缘总升幅必须 ≥ **%.1f px**（= %.1f mm）。"
        "阈值由**实测**导出：实测起点 %.2f mm（腿已落地、还仰卧）→ 终点 %.2f mm（站直），"
        "真实升幅 **%.1f px / %.0f mm**，阈值取实测的 %.0f%%（D17 的口径是 81%%）。"
        "★ 注意：这是**剔除衣摆块之后**的读数 —— 不剔会算成 246 px（= 静止薄片到头顶），"
        "少算 39%%。"
        % (RISE_MIN_PX, RISE_MIN_PX * mmp,
           res["px_rise_from_mm"], res["px_rise_to_mm"],
           rise, rise * mmp, 100.0 * RISE_MIN_PX / rise if rise else 0.0))

    # ---------------- (3) ★ 反面对照（幅度侧）：D16 自己 ---------------------
    d16_frames = sorted(d16_wide)
    d16_tops = [d16_wide[f]["top"] for f in d16_frames]
    d16_rise = total_rise(d16_tops)
    d16_raw = [d16_wide[f]["raw_top"] for f in d16_frames]
    d16_mmp = mm_per_px_of(D16_WIDE)
    res["px_rise_control_d16"] = {
        "view": D16_WIDE, "frames": [d16_frames[0], d16_frames[-1]],
        "top_row_first": d16_tops[0], "top_row_last": d16_tops[-1],
        "raw_top_first": d16_raw[0], "raw_top_last": d16_raw[-1],
        "total_rise_px": round(d16_rise, 3),
        "total_rise_mm": round(d16_rise * d16_mmp, 2)}
    res["px_rise_can_fail_ok"] = bool(d16_rise < RISE_MIN_PX)
    res["px_rise_can_fail_note"] = (
        "★ 反向（幅度侧）：**D16 自己**（`groundhitwide_side`，同一把幅度尺子、"
        "同族同构、**同口径剔衣摆**）必须判红 —— 它是「倒地受击」，人始终躺在地上，"
        "剔除后顶缘 f0 %d → f20 %d ⟹ 总升幅 **%.1f px < %.1f px** 阈值。"
        "这条证明这把尺子**对「没起来」敏感**。★ 顺带登记：D16 的 raw 顶缘是"
        "**恒定 %d px**（= 同一块衣摆薄片），正是 §A 说的污染。"
        % (d16_tops[0], d16_tops[-1], d16_rise, RISE_MIN_PX, d16_raw[0]))

    # ---------------- (4) ★ 反面对照（单调侧）：本支 `[START, END]` ----------
    tops_all = [wide[f]["top"] for f in wframes]
    all_bad = mono_non_decreasing(wframes, tops_all, MONO_TOL_PX)
    leg_drop = cum_drop_into(wframes, tops_all, LEGS_DOWN)
    drop, drop_at = max_drop(wframes, tops_all)
    res["px_rise_mono_control"] = {
        "carrier": "wide 视全剪影顶缘（`rows.max()`，已剔衣摆块）",
        "window": [START, TOTAL],
        "view": WIDE,
        "violation_frames": all_bad,
        "top_row": {str(f): wide[f]["top"] for f in wframes},
        "top_z_mm": res["wide_top_z_mm"],
        "leg_drop_px": round(leg_drop, 3),
        "leg_drop_mm": round(leg_drop * mmp, 2),
        "max_drop_px": round(drop, 3),
        "max_drop_at": drop_at,
    }
    res["px_rise_mono_can_fail_ok"] = bool(all_bad)
    res["px_rise_mono_can_fail_note"] = (
        "★ 反向（单调侧）：**同一把单调尺子**改量本支 `[START, END]`（含落腿段）"
        "必须判红 —— 实测 `f=START` 顶缘 **%d px**（z %.1f mm = 抬起的鞋底），"
        "落腿段累计回落 **%.1f px = %.1f mm**，违反帧 **%s**。"
        "这条同时把「为什么载体不能是**从 f0 起的**顶缘」实测钉死。"
        % (wide[START]["top"], res["wide_top_z_mm"][str(START)],
           leg_drop, leg_drop * mmp, all_bad or "无"))

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
    res["px_idle_end_frames"] = {"getupb": TOTAL, "idle01": IDLE_END_FRAME,
                                "view": WIDE}
    res["px_idle_end_delta_px"] = delta
    res["px_idle_end_tol_px"] = IDLE_MATCH_TOL_PX
    res["px_idle_end_ok"] = bool(
        abs(delta["bottom"]) <= IDLE_MATCH_TOL_PX
        and abs(delta["top"]) <= IDLE_MATCH_TOL_PX
        and abs(delta["width"]) <= IDLE_MATCH_TOL_PX
        and abs(delta["area_row"]) <= IDLE_MATCH_TOL_PX)
    res["px_idle_end_note"] = (
        "★★★ **本支第二把独门尺子**：wide 视 `f = %d`（`GetUp_B@%d`）的剪影必须与 "
        "`%s_f%04d`（**D18 同机位**重渲的 `Idle_01@%d`）**逐位一致**"
        "（底缘 / 顶缘 / 宽 / 面积行心，容差 %.1f px = %.1f mm）。这是骨架级 "
        "`end_matches_idle_ok`（逐骨 4x4 世界矩阵 `max_delta <= 1e-6`）的**像素级独立复核**。"
        "★ 用 `idle01wideb_*`（D18 机位，中心 y=+250 mm）而**不是** `idle01wide_*`"
        "（D17 机位，中心 y=−300 mm）。两帧都**同口径剔衣摆**，所以 delta 只反映姿态差。"
        % (TOTAL, TOTAL, IDLE_WIDE, IDLE_END_FRAME, IDLE_END_FRAME,
           IDLE_MATCH_TOL_PX, IDLE_MATCH_TOL_PX * mmp))

    # ---------------- (6) ★ 反面：`FOOT_SET`（人还蹲着）对 idle01 必须红 -----
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
        "★ 反向：`%s_f%04d`（`FOOT_SET`，脚刚接住地面、人还蹲着）用同一把尺子"
        "必须判红 —— 否则说明这把尺子对「还没站起来」不敏感。实测顶缘差 %d px、"
        "宽差 %d px、面积行心差 %.1f px。"
        % (WIDE, FOOT_SET, mid_delta["top"], mid_delta["width"],
           mid_delta["area_row"]))

    # ---------------- (7) ★★ 衣摆块：**真的有块可剔**（不是 N/A）------------
    owner = [f for f in wframes if wide[f]["raw_top"] != wide[f]["top"]]
    res["hem_owner_frames"] = owner
    res["hem_owner_count"] = len(owner)
    res["px_hem_excluded_ok"] = bool(len(owner) >= 1)
    res["px_hem_note"] = (
        "★★ **本支新增的真判据（不是 N/A）**：`Jacket_Hem` / `Jacket_Hem_Line` 未蒙皮"
        "（`vgroups=0` / `parent=None`），世界包围盒**逐帧恒定**"
        "（`probe_c11_belt` 实测 `constant=true`，z [897.5, 926.0] mm、"
        "y [−121.94, +129.03] mm）⟹ 在 wide 视里固定在 **cols %s / rows %s**。"
        "D18 **从仰卧起步、身体全程低于 926 mm**，所以 f0~f22 **顶缘整段被这块布接管**："
        "实测 raw 顶缘 **恒 542 px**，剔除后 f0 = **390 px**（角色自己的 `Shoe_Sole_L` "
        "z 427.8 mm）。实测「raw 顶缘 ≠ 剔除后顶缘」的帧共 **%d** 帧（%s…%s）。"
        "⟹ **必须剔**。★ 诚实登记：D15/D16/D17 报的「无块可剔 / N/A + True」"
        "**是被硬编码写死的**（`hem_dropped = []`），从来没有真的算过；"
        "D17 的 `px_rise_*` 因此把静止薄片当成了身体（报 246 px，真实 391 px）。"
        "**D17 的结论不变**（两种口径都单调、都过阈值），故不回改已完成条目，"
        "只在 D18 日志里登记修正值。"
        % (list(hem_cols_rows(WIDE)[:2]), list(hem_cols_rows(WIDE)[2:]),
           len(owner), owner[0] if owner else "-", owner[-1] if owner else "-"))
    res["px_hem_stripped_ok"] = bool(wide[START]["raw_top"] != wide[START]["top"])
    res["px_hem_stripped_note"] = (
        "★★ 与上一条互为印证：首帧 raw 顶缘 **%d px**（z %.1f mm = 静止薄片顶）→ "
        "剔除后 **%d px**（z %.1f mm = 抬起的鞋底）。读数**确实变了**，"
        "证明剔除**真的生效**（不是空操作）。"
        % (wide[START]["raw_top"], res["wide_raw_top_z_mm"][str(START)],
           wide[START]["top"], res["wide_top_z_mm"][str(START)]))

    # ---------------- (8) 登记 N/A 的两条 ------------------------------------
    res["px_hitstop_status"] = "N/A"
    res["px_hitstop_ok"] = None
    res["px_hitstop_note"] = (
        "★★ **本判据在本支不生成、不参与 `failed`（登记 N/A）**。理由：本支是**主动发力**"
        "动作（仰卧 → 撑起 → 站直），**没有「命中帧」** ⟹ `meta.hitstop_frames = 0`；"
        "在 `anim_getup_b.py` 的 `disabled_gates` 里 `hitstop_present` 已被显式登记为 "
        "DISABLED。硬套只会得到伪造的停顿。收招由骨架级 `no_snap_stop_ok` 守，"
        "「一次发力、不回落」由 `px_rise_monotone_ok` / `rise_monotone_ok` 守。")

    res["px_seam_steps_status"] = "N/A"
    res["px_seam_steps_ok"] = None
    res["px_seam_steps_registered"] = {"T_PHASE_D17": T_PHASE_D17,
                                       "T_PHASE_D18": T_PHASE_D18}
    res["px_seam_steps_note"] = (
        "★★ **本判据在本支不生成、不参与 `failed`（登记 N/A）**。理由："
        "`px_seam_steps_ok` 量的是「本支侧视逐帧行心与**共享解析抛物线**的残差」，"
        "用于检验两段弹道首尾相接。本支竖直通道**没有弹道段**"
        "（骨盆 z 全段单调升 702 mm，无抛物线可比）⟹ 硬套只会得到无意义的残差。"
        "相位 `T_PHASE_D18 = %.1f` **仅登记**。" % T_PHASE_D18)

    # ---------------- 汇总 ---------------------------------------------------
    checks = [k for k in res if k.endswith("_ok") and res[k] is not None]
    failed = sorted(k for k in checks if res[k] is False)
    res["checks"] = sorted(checks)
    res["failed"] = failed
    res["verdict"] = "PASS" if not failed else "FAIL"
    print("D18PX_REPORT " + json.dumps(res, ensure_ascii=False))
    print("D18PX_DONE failed=%s" % failed)
    if not failed:
        print("D18PX_DONE verdict=PASS")


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D18PX_FAILURE " + traceback.format_exc())
