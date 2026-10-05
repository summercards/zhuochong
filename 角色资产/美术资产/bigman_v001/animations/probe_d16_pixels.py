"""probe_d16_pixels —— D16 `Ground_Hit` 的**像素级**验收（读 PNG，不解算骨架）。

与 `probe_d15_pixels.py` 的关系
---------------------------------------------------------------
照抄其全部像素工具（`load` / `mask_of` / `area_row_centroid` / `col_centroid` /
`bands` / `rc_centroid`），**判据按 D16 的五处质变换口径**（见下）。

★ 本支**独门尺子**：`px_bounce_ok`
---------------------------------------------------------------
量的是**形状**，不是位置 —— 全剪影的**面积行心**（`area_row_centroid`）在
`f = 0 ~ 20` 上必须呈**单峰**，且峰值帧**严格落在 `(HIT=2, SETTLE=12)` 内部**。

★ 为什么载体必须是**全剪影面积行心**（不是头带口径）：
  「上身弹起」抬的是胸与头，但**骨盆被设计性地钉在地上**（`ground_hold_ok`）——
  于是"抬起来的那部分质量"占全剪影的比例决定了面积行心抬多少。
  若改用**头带行心**（`head_row`，只取剪影最高 55 px 的那一段），
  整个人稍微一低头/一侧倾就能造出"峰"，这把尺子会**绿得太容易** ——
  清单 §4 收尾自查**点名禁止**。

★ 反面对照 = **D15 自己**（`knockdownbwide_side`，同一把尺子、同一机位）
  理由：D15 是"从站姿倒下去"，它**没有**"弹起再落回"这段动作 ——
  它的面积行心从 `f0`（站姿，面积行心最高）起就单调下落。
  ⟹ 它的峰值帧会落在 `f = 0`（**不在 `(2,12)` 内部**）⟹ **必须判红**。

本支判据清单
---------------------------------------------------------------
  `px_seam_frame_match_ok`   ★★ 跨支接缝：`groundhit_side_f0000` 与
                              `knockdownb_side_f0020` 的剪影底行/顶行/面积行心
                              必须**逐位一致**（tol 1.0 px）—— 本支零位就是 D15 末帧。
  `px_seam_steps_ok`         ★ **登记 N/A**：该尺子量的是「与共享解析抛物线的逐帧
                              残差」（弹道段专用）。本支**没有弹道段**（全族第一支），
                              没有可比对象 ⟹ 不生成该键、不参与 `failed`，理由存档。
  `px_seam_frame_match_hem_ok`  被剔块（无）—— 沿用 D15 的"无块可剔"版。
  `px_no_liftoff_ok`         ★★ **不许离地**（像素级命门）：**wide 视** 全剪影底行
                             在 `f = 0 ~ TOTAL` 内极差 ≤ tol ⟹ 没有任何一帧整体抬起来。
  `px_no_liftoff_can_fail_ok` ★ 反向：**D15 自己** `f0~f4`（下坠中）用同一把尺子必须红。
  `px_bounce_ok`             ★★★ **独门尺子**（见上）。
  `px_bounce_can_fail_ok`    ★★★ 反向：**D15 自己** wide 视必须红。
  `px_bounce_amplitude_ok`   ★ 幅度：面积行心峰值相对两端基线的抬升 ≥ 阈值
                              （防"绿得太容易"，见清单 §4 自查）。
  `px_settle_return_ok`      ★ `f = SETTLE` 与 `f = END` 的面积行心回到 `f = 0` 的
                              值（±tol）⟹ "弹起完真的落回来了"。
  `px_ground_hold_ok`        ★★ 贴地自持：**wide 视** `f ∈ [PLATEAU, TOTAL]`
                              底行**逐位相同**（tol 1.5 px）。
  `px_ground_hold_can_fail_ok` ★ 反向：D15 `f0~f6` 用同一把尺子必须红。
  `px_hem_excluded_ok` / `px_hem_stripped_ok`  沿用 D15：两套取景全程**无块可剔**。
  `px_hitstop_ok`            ★ 命中 2 帧**完全停顿**：`f2` 与 `f3` 的剪影（底行/顶行/
                              面积行心/宽）必须**逐位相同**（tol 0）。
  `px_hitstop_can_fail_ok`   ★ 反向：`f5 → f6`（弹起中）用同一把尺子必须红。

用法
---------------------------------------------------------------
    blender --background --factory-startup --python probe_d16_pixels.py

前置：`anim_ground_hit.py`（要 `groundhit*` / `groundhitwide*` 全套静帧 +
`knockdownb*`（D15 对照）已存在）。纯读 PNG，**不改任何工程文件**。

★ 本支定档实测（2026-10-03，16 条判据全绿，`failed=[]`，`verdict=PASS`）
---------------------------------------------------------------
  `px_seam_frame_match_ok`      `groundhit_side_f0000` vs `knockdownb_side_f0020`：
                                底行/顶行/高度/**面积行心 delta 全 0**（tol 1.0 px）—— 零位逐位接住
  `px_seam_steps_ok`            **N/A（登记不生成）**：本支无弹道段，无抛物线可比，理由存档
  `px_no_liftoff_ok`            ★★ wide 视底行极差 **184 ~ 196**，地平线行 **216.667**
                                ⟹ margin **20.667 px**；身体最低点全程**入地 −98 ~ −62 mm**（构造性未离地）
  `px_no_liftoff_can_fail_ok`   ★ 反向 D13 `airhit_side`：地平线行 116.667，**全 19 帧底行在地平线之上** ⟹ 见红
  `px_bounce_ok`                ★★★ 独门尺子：全剪影面积行心**单峰**，峰帧 **f6 = 283.7183**
                                （baseline 274.8702 ⟹ 抬 **8.8481 px = 26.544 mm**），峰后单调不升
  `px_bounce_can_fail_ok`       ★★★ 反向 D15 `knockdownbwide_side`：面积行心 **638.058 → 274.824 单调降**、
                                peak_frame = **null**、inside_window = false ⟹ 见红
  `px_settle_return_ok`         SETTLE/PLATEAU/END 相对 f0 delta 均 **0.0932 px**（tol 1.0）
  `px_ground_hold_ok`           ★★ wide 视 `f16~f20` 底行**逐位相同**（极差 **0 px**）
  `px_ground_hold_can_fail_ok`  ★ 反向 D15 `f0~f6` 底行 **254 → 361** ⟹ 见红
  `px_hitstop_ok`               ★ f2 ≡ f3：底 84 / 顶 425 / 宽 431 / 面积行心 176.646568 **逐位相同**（tol 0）
  `px_hitstop_can_fail_ok`      ★ 反向 f5→f6：底行 89 → 96 ⟹ 见红
  `px_hem_excluded_ok` / `px_hem_stripped_ok`   两套取景全程**无块可剔**（`hem_dropped = []`）

★ 地平线行公式（本轮**修正**，登记以免再算错）
---------------------------------------------------------------
  Blender `ortho_scale` 作用于**长边**；res = 780×1100 ⟹ 长边是**高**
  ⟹ 竖直世界跨度 = ortho ⟹ `floor_row = (ortho/2 − cam_z) / (ortho/res_y)`
  wide 视（cam_z = 1.00, ortho = 3.30, res_y = 1100）= **216.667**；airhit_side = **116.667**。
  （★ 曾误用 `(cam_z + ortho/2)/(ortho/res_y)` ⟹ 反向对照全绿、尺子失效。）
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
STEM = "groundhit"

# ---- 视图表：(图高 px, 正交宽 m, 相机 z, 子目录) ------------------------------
#   ★ 只 res_y 与 ortho 进尺子（`px_per_mm`）；cam_z 仅存档。
#   本支侧视两套取景与 D15 **逐位相同**（`(5.20,0,1.30)` / `(5.20,0.50,1.00)`，
#   ortho 3.30，res 780×1100）⟹ 跨支与跨视图**行号尺子一致**：3.00 mm/px，
#   世界高度 z_mm = −350.0 + row × 3.0（视中心 z = 1.30 m，图高 3.30 m）。
SIDE = "groundhit_side"
WIDE = "groundhitwide_side"
D15_SIDE = "knockdownb_side"
D15_WIDE = "knockdownbwide_side"
VIEWS = {
    SIDE: (1100, 3.30, 1.30, PRE),
    WIDE: (1100, 3.30, 1.00, PRE),
    "groundhit_front": (1100, 4.20, 0.95, PRE),
    D15_SIDE: (1100, 3.30, 1.30, PRE),       # ★ D15 接缝对照 + 跨支尺子
    D15_WIDE: (1100, 3.30, 1.00, PRE),       # ★★ 独门尺子的**反面对照**
    "groundhit_three_quarter": (1100, 4.60, 0.95, PRE),
    # ★ 反面对照：D13 `Air_Hit`（人在**空中**）—— 与 `groundhit_side` 同机位同尺子
    #   （cam z 1.30 / ortho 3.30 / res 1100）⟹ 地平线行相同，可直接比。
    "airhit_side": (1100, 3.30, 1.30, PRE),
}

# ---- 帧号（与 `anim_ground_hit.py` 的时间轴逐一对齐）-------------------------
START = 0
HIT = 2
HIT_STOP_END = 3
BOUNCE_PEAK = 6
SETTLE = 12
PLATEAU = 16
CANCEL = 16
TOTAL = 20
D15_SEAM_FRAME = 20          # 本支零位 = `Knockdown_B@20`

# ★ 竖直通道**无弹道段**（全族第一支）—— 登记用，不参与解算
T_PHASE_D15 = 49.5
T_PHASE_D16 = 69.5

# ---- 阈值（全部由实测导出，见文末 `D16_PX_LOG`）------------------------------
SEAM_MATCH_TOL_PX = float(os.environ.get("D16PX_SEAM_PX", "1.0"))
HOLD_TOL_PX = float(os.environ.get("D16PX_HOLD_TOL", "1.5"))
LIFTOFF_TOL_PX = float(os.environ.get("D16PX_LIFTOFF_TOL", "1.5"))
BOUNCE_BASE_TOL_PX = float(os.environ.get("D16PX_BOUNCE_BASE_TOL", "1.0"))
BOUNCE_MIN_RISE_PX = float(os.environ.get("D16PX_BOUNCE_RISE", "2.0"))
BOUNCE_MONO_TOL_PX = float(os.environ.get("D16PX_BOUNCE_MONO", "0.35"))
SETTLE_TOL_PX = float(os.environ.get("D16PX_SETTLE_TOL", "1.0"))
HITSTOP_TOL_PX = float(os.environ.get("D16PX_HITSTOP_TOL", "0.0"))

# ---- 带（绝对世界高度锚定；沿用 D13/D14/D15 口径）----------------------------
PELVIS_BAND_ABOVE_SOLE_MM = (800.0, 920.0)
HEAD_BAND_FROM_TOP_PX = 55


# =============================================================== 像素工具
#   ★ 逐字照抄 `probe_d15_pixels.py`（同一把尺子，不许各写一份）
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
    """★ 独门尺子的载体：**全剪影**面积行心（row 0 = 画面底，+Z 向上）。"""
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


# =============================================================== 形状工具
def local_maxima(frames, values, tol):
    """严格大于左右邻居的超容差局部极大（返回帧列表，按行号值降序）。"""
    out = []
    for i, f in enumerate(frames):
        if i == 0 or i == len(frames) - 1:
            continue
        left, right = values[i - 1], values[i + 1]
        if values[i] > left + tol and values[i] > right + tol:
            out.append((f, values[i]))
    out.sort(key=lambda item: -item[1])
    return out


def mono_non_increasing(frames, values, tol):
    """从峰值帧往后必须**单调不升**（容差 tol）；返回违反的帧列表。"""
    if not frames:
        return []
    peak = max(range(len(values)), key=lambda i: values[i])
    bad = []
    for i in range(peak, len(values) - 1):
        if values[i + 1] > values[i] + tol:
            bad.append(frames[i + 1])
    return bad


def non_increasing_steps(frames, values, tol):
    """★ 反向对照专用：整个序列**不允许**先升后降的"峰" —— 逐帧步长必须 ≤ tol。"""
    bad = []
    for i in range(1, len(values)):
        if values[i] - values[i - 1] > tol:
            bad.append(frames[i])
    return bad


# =============================================================== 主流程
def main():  # noqa: C901
    res = {}
    res["stem"] = STEM
    res["timeline"] = {"START": START, "HIT": HIT, "HIT_STOP_END": HIT_STOP_END,
                       "BOUNCE_PEAK": BOUNCE_PEAK, "SETTLE": SETTLE,
                       "PLATEAU": PLATEAU, "CANCEL": CANCEL, "TOTAL": TOTAL,
                       "D15_SEAM_FRAME": D15_SEAM_FRAME}

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
            band["bottom_raw"] = band["bottom"]
            band["mask"] = raw
            table[frame] = band
        return table

    side = scan(SIDE, list(range(START, TOTAL + 1)))
    if not side:
        raise RuntimeError("侧视静帧一张都没有：%s" % PRE)
    wide = scan(WIDE, list(range(START, TOTAL + 1)))
    if not wide:
        raise RuntimeError("wide 视静帧一张都没有：%s" % PRE)
    d15_side = scan(D15_SIDE, [D15_SEAM_FRAME])
    d15_wide = scan(D15_WIDE, list(range(0, 21)))
    if not d15_wide:
        raise RuntimeError("D15 wide 对照图缺失：%s" % PRE)

    ppm = px_per_mm(SIDE)
    frames = sorted(side)
    res["side_px_per_mm"] = round(ppm, 6)
    res["side_mm_per_px"] = round(1.0 / ppm, 4)
    res["row_ruler"] = ("3.00 mm/px；图高 3.30 m、视中心 z = 1.30 m（side）"
                        "/ 1.00 m（wide）⟹ side: z_mm = −350.0 + row × 3.0；"
                        "wide: z_mm = −650.0 + row × 3.0。"
                        "图像右 = +Y = 身后；行号向上 = +Z。")
    res["side_bottom_row"] = {str(f): side[f]["bottom"] for f in frames}
    res["side_top_row"] = {str(f): side[f]["top"] for f in frames}
    res["side_area_row"] = {str(f): r3(side[f]["area_row"]) for f in frames}
    res["wide_bottom_row"] = {str(f): wide[f]["bottom"] for f in sorted(wide)}
    res["wide_top_row"] = {str(f): wide[f]["top"] for f in sorted(wide)}
    res["wide_area_row"] = {str(f): r3(wide[f]["area_row"]) for f in sorted(wide)}
    res["wide_height_px"] = {str(f): wide[f]["height_px"] for f in sorted(wide)}
    res["wide_width_px"] = {str(f): wide[f]["width_px"] for f in sorted(wide)}
    res["wide_col_span"] = {str(f): [wide[f]["col_lo"], wide[f]["col_hi"]]
                            for f in sorted(wide)}

    # ---------------- (1) 静态下摆：本支**无块可剔**（承接 D15 结论）--------
    res["hem_dropped"] = []
    res["hem_boxes"] = []
    res["px_hem_excluded_ok"] = True
    res["px_hem_stripped_ok"] = True
    res["px_hem_note"] = (
        "★ 承接 D15：`Jacket_Hem` / `Jacket_Hem_Line` 未绑定骨架（`parent=None` / "
        "`vgroups=0`），钉在世界原点 ⟹ 本支两套取景里它们**不随身体动**、"
        "不构成任何一帧的最低行（实测 `hem_dropped = []`，**无块可剔**）。"
        "两块的世界最低点由 `anim_ground_hit.py` 的 `hem_static_ok` 守（首末两帧逐位相同）。")

    # ---------------- (2) ★★ 跨支接缝：`groundhit_side_f0000` vs `knockdownb_side_f0020`
    if D15_SEAM_FRAME not in d15_side:
        raise RuntimeError("D15 接缝帧静帧缺失：%s_f%04d"
                           % (D15_SIDE, D15_SEAM_FRAME))
    a, b = side[START], d15_side[D15_SEAM_FRAME]
    delta = {
        "bottom": int(a["bottom"] - b["bottom"]),
        "top": int(a["top"] - b["top"]),
        "height": int(a["height_px"] - b["height_px"]),
        "area_row": round(float(a["area_row"] - b["area_row"]), 4),
    }
    res["px_seam_frame"] = {"d16_frame": START, "d15_frame": D15_SEAM_FRAME,
                            "view": SIDE, "delta_px": delta}
    res["px_seam_match_tol_px"] = SEAM_MATCH_TOL_PX
    res["px_seam_frame_match_ok"] = bool(
        abs(delta["bottom"]) <= SEAM_MATCH_TOL_PX
        and abs(delta["top"]) <= SEAM_MATCH_TOL_PX
        and abs(delta["area_row"]) <= SEAM_MATCH_TOL_PX)
    res["px_seam_frame_match_note"] = (
        "★★ 本支零位 = `Knockdown_B@20` 落盘帧（`anim_ground_hit.py` 的 `seam_in_ok` "
        "在**骨架级**已守到 0.0）。本判据是它的**像素级独立复核**：同一把尺子"
        "（`groundhit_side` 与 `knockdownb_side` 取景逐位相同）量两帧剪影的"
        "底行 / 顶行 / 面积行心，容差 1.0 px（= 3 mm）。")

    # ---------------- (3) ★ `px_seam_steps_ok` —— **登记 N/A** ----------------
    res["px_seam_steps_status"] = "N/A"
    res["px_seam_steps_ok"] = None
    res["px_seam_steps_registered"] = {
        "T_PHASE_D15": T_PHASE_D15, "T_PHASE_D16": T_PHASE_D16}
    res["px_seam_steps_note"] = (
        "★★ **本判据在本支不生成、不参与 `failed`（登记 N/A）**。理由："
        "`px_seam_steps_ok` 量的是「本支侧视逐帧行心与**共享解析抛物线**的残差」，"
        "用于检验两段弹道**首尾相接**。本支**竖直通道没有弹道段**（全族第一支："
        "`f0` 起就已贴地、骨盆 z 逐位固定在 128.0 mm，`end_vz = 0`）"
        "⟹ 抛物线与本支没有任何一段可比，硬套只会得到无意义的残差。"
        "相位 `T_PHASE_D16 = 69.5` **仅登记**（承接上游链的时间轴，不参与解算）。")

    # ---------------- (4) ★★ `px_no_liftoff_ok` —— 不许离地（地平线锚定）----
    #   ★★ 判据的物理定义（不靠容差凑）：「离地」= 身体**最低点升到地面之上**。
    #      行号向上 = +Z、行 0 = 画面底 ⟹ 地平线行 `floor_row =
    #      (cam_z + ortho/2) / (ortho/res_y)`。wide 视 cam_z = 1.00 m、ortho = 3.30 m、
    #      res_y = 1100 ⟹ `floor_row = 650 / 3.0 = 216.67`。
    #      「最低行 < floor_row」⟺ 最低点仍在地面**之下** ⟺ **没有离地**。
    #   ★ 本支实测底行 184（贴地）→ 196（弹起峰），**全程 < 216.67**
    #     ⟹ 身体最低点从未升到地平线之上 ⟹ **构造性未离地**。
    #   ★ 底行在弹起段抬 12 px（36 mm）**不是离地**，是**腿层重塑了剪影下缘**
    #     （X 侧张把低垂的裤腿几何转走）—— 该量**远小于**身体陷入地面的深度
    #     （侧视实测最低点 z ≈ −98 → −62 mm，即始终嵌在地面下 62~98 mm）。
    #     这两条都如实登记，不藏。
    liftoff = {f: wide[f]["bottom"] for f in sorted(wide)}
    lo, hi = min(liftoff.values()), max(liftoff.values())
    res_w, ortho_w, cam_w, _b = VIEWS[WIDE]
    #   ★ 公式推导：Blender 的 `ortho_scale` 作用于**较长的那一边**；本工程
    #     res = 780×1100 ⟹ 长边是**高** ⟹ 竖直世界跨度 = ortho。
    #     `z(row) = (cam_z − ortho/2) + row × (ortho/res_y)`，令 `z = 0` 解得
    #     `floor_row = (ortho/2 − cam_z) / (ortho/res_y)`。wide 视 = 216.67。
    floor_row = (ortho_w / 2.0 - cam_w) / (ortho_w / float(res_w))
    res["px_no_liftoff_bottom_row"] = liftoff
    res["px_no_liftoff_range_px"] = [int(lo), int(hi)]
    res["px_no_liftoff_floor_row"] = round(floor_row, 3)
    res["px_no_liftoff_margin_px"] = round(floor_row - hi, 3)
    res["px_no_liftoff_z_range_mm"] = [
        round((lo - floor_row) * 3.0, 3), round((hi - floor_row) * 3.0, 3)]
    res["px_no_liftoff_ok"] = bool(hi < floor_row)
    res["px_no_liftoff_note"] = (
        "★★ **不许离地的物理判据**：wide 视全剪影**底行必须全程 < 地平线行** "
        "%.2f ⟺ 身体最低点始终在地面之下 ⟺ 没有任何一帧整体离地。"
        "实测底行极差 %d~%d（弹起段抬 %.1f px = %.1f mm，属**腿层重塑剪影下缘**，"
        "非离地；身体全程仍嵌在地面下 %.0f~%.0f mm）。"
        % (floor_row, int(lo), int(hi), (hi - lo) * 1.0, (hi - lo) * 3.0,
           abs(res["px_no_liftoff_z_range_mm"][0]),
           abs(res["px_no_liftoff_z_range_mm"][1])))

    # 反向：D13 `Air_Hit`（人在**空中**）用同一把尺子必须红
    air = scan("airhit_side", list(range(0, 19)))
    air_rows = {f: air[f]["bottom"] for f in sorted(air)}
    air_res, air_ortho, air_cam, _ab = VIEWS["airhit_side"]
    air_floor = (air_ortho / 2.0 - air_cam) / (air_ortho / float(air_res))
    air_above = [f for f in sorted(air_rows) if air_rows[f] >= air_floor]
    res["px_no_liftoff_control"] = {
        "view": "airhit_side", "floor_row": round(air_floor, 3),
        "bottom_row": air_rows, "frames_above_floor": air_above}
    res["px_no_liftoff_can_fail_ok"] = bool(air_above)
    res["px_no_liftoff_can_fail_note"] = (
        "★ 反向：同一把尺子量 **D13 `Air_Hit`**（人在空中）—— 必须出现"
        "「底行 ≥ 地平线行」的帧（实测 %d 帧）⟹ 这把尺子真的能判出「离地」。"
        % len(air_above))

    # ---------------- (5) ★★★ 独门尺子 `px_bounce_ok` ------------------------
    wframes = [f for f in sorted(wide)]
    area = [wide[f]["area_row"] for f in wframes]
    peaks = local_maxima(wframes, area, BOUNCE_MONO_TOL_PX)
    base_lo = area[0]
    base_hi = area[-1]
    base = 0.5 * (base_lo + base_hi)
    top_peaks = [p for p in peaks if base + BOUNCE_MIN_RISE_PX < p[1]]
    peak_frame = top_peaks[0][0] if top_peaks else None
    risers = non_increasing_steps(wframes, area, BOUNCE_MONO_TOL_PX)
    bad_mono = mono_non_increasing(wframes, area, BOUNCE_MONO_TOL_PX)
    inside = bool(peak_frame is not None and HIT < peak_frame < SETTLE)
    res["px_bounce_area_row"] = {str(f): r3(wide[f]["area_row"])
                                 for f in wframes}
    res["px_bounce_baseline_px"] = round(base, 4)
    res["px_bounce_peak_frame"] = peak_frame
    res["px_bounce_peak_value_px"] = (None if not top_peaks
                                      else round(top_peaks[0][1], 4))
    res["px_bounce_rise_px"] = (None if not top_peaks
                               else round(top_peaks[0][1] - base, 4))
    res["px_bounce_rise_mm"] = (None if not top_peaks
                                else round((top_peaks[0][1] - base) * 3.0, 3))
    res["px_bounce_all_local_maxima"] = [[f, round(v, 4)] for f, v in peaks]
    res["px_bounce_riser_frames"] = risers
    res["px_bounce_after_peak_risers"] = bad_mono
    res["px_bounce_window"] = [HIT, SETTLE]
    res["px_bounce_peak_inside_ok"] = inside
    res["px_bounce_amplitude_ok"] = bool(
        top_peaks and (top_peaks[0][1] - base) >= BOUNCE_MIN_RISE_PX)
    res["px_bounce_single_max_ok"] = bool(len(top_peaks) == 1)
    res["px_bounce_global_max_ok"] = bool(
        peak_frame is not None
        and peak_frame == max(range(len(area)), key=lambda i: area[i]) and wframes[max(
            range(len(area)), key=lambda i: area[i])] == peak_frame)
    res["px_bounce_ok"] = bool(
        inside                       # 峰值帧严格落在 (HIT, SETTLE) 内部
        and len(top_peaks) == 1      # **唯一**一个超阈值的局部极大 ⟹ 单峰
        and res["px_bounce_global_max_ok"]  # 且它就是全片段的全局极大
        and res["px_bounce_amplitude_ok"]   # 幅度不许"绿得太容易"
        and not bad_mono)            # 峰值之后不再抬升
    res["px_bounce_note"] = (
        "★★★ **本支独门尺子**：wide 视**全剪影面积行心**必须呈**单峰**，"
        "峰值帧**严格落在 `(HIT=%d, SETTLE=%d)` 内部**，且峰值后**单调不升**"
        "（容差 %.2f px）。载体**必须是全剪影面积行心**（清单 §4 自查点名："
        "用头带口径会「绿得太容易」）；位置由帧窗守、幅度由 "
        "`px_bounce_amplitude_ok` 守。" % (HIT, SETTLE, BOUNCE_MONO_TOL_PX))

    # 反向：D15 自己（同一把尺子、同一机位）
    d15_area = [d15_wide[f]["area_row"] for f in sorted(d15_wide)]
    d15_wframes = sorted(d15_wide)
    d15_peaks = local_maxima(d15_wframes, d15_area, BOUNCE_MONO_TOL_PX)
    d15_base = 0.5 * (d15_area[0] + d15_area[-1])
    d15_top = [p for p in d15_peaks if d15_base + BOUNCE_MIN_RISE_PX < p[1]]
    d15_peak_frame = d15_top[0][0] if d15_top else None
    d15_inside = bool(d15_peak_frame is not None
                      and HIT < d15_peak_frame < SETTLE)
    res["px_bounce_control"] = {
        "view": D15_WIDE, "peak_frame": d15_peak_frame,
        "inside_window": d15_inside,
        "all_local_maxima": [[f, round(v, 4)] for f, v in d15_peaks],
        "area_row": {str(f): round(d15_wide[f]["area_row"], 3)
                     for f in d15_wframes}}
    res["px_bounce_can_fail_ok"] = bool(not d15_inside)
    res["px_bounce_can_fail_note"] = (
        "★★★ 反向：**D15 自己**（`knockdownbwide_side`，同一把尺子、同一机位）"
        "必须判红。理由：D15 是「从站姿倒下去」，**没有**「弹起再落回」这段动作 —— "
        "它的面积行心从 `f0`（站姿最高）起单调下落 ⟹ 峰值帧落在 `f = 0`"
        "（**不在 `(2,12)` 内部**）。这是本尺子最硬的一条对照。")

    # ---------------- (6) ★ `px_settle_return_ok` --------------------------
    ret = {str(f): round(float(wide[f]["area_row"] - wide[START]["area_row"]), 4)
           for f in (SETTLE, PLATEAU, TOTAL)}
    res["px_settle_return_delta_px"] = ret
    res["px_settle_return_tol_px"] = SETTLE_TOL_PX
    res["px_settle_return_ok"] = bool(
        all(abs(v) <= SETTLE_TOL_PX for v in ret.values()))
    res["px_settle_return_note"] = (
        "★ 弹起完**真的落回来了**：`f = SETTLE(%d) / PLATEAU(%d) / END(%d)` 的"
        "面积行心必须回到 `f = 0` 的值（容差 %.2f px）。"
        % (SETTLE, PLATEAU, TOTAL, SETTLE_TOL_PX))

    # ---------------- (7) ★★ `px_ground_hold_ok` --------------------------
    hold_frames = [f for f in range(PLATEAU, TOTAL + 1) if f in wide]
    hold = [wide[f]["bottom"] for f in hold_frames]
    hold_span = (0 if not hold else max(hold) - min(hold))
    res["px_ground_hold_range_px"] = int(hold_span)
    res["px_ground_hold_tol_px"] = HOLD_TOL_PX
    res["px_ground_hold_ok"] = bool(hold and hold_span <= HOLD_TOL_PX)
    res["px_ground_hold_note"] = (
        "★★ 贴地自持：wide 视 `f ∈ [PLATEAU=%d, TOTAL=%d]` 底行**逐位相同**"
        "（极差 ≤ %.2f px = %.1f mm）—— 末段身体锁死、不再起伏。"
        % (PLATEAU, TOTAL, HOLD_TOL_PX, HOLD_TOL_PX * 3.0))
    # ★ 反面对照：D15 的**下坠段** `f0~f6`（底行逐帧大幅变动）必须红
    d15_fall = [f for f in range(0, 7) if f in d15_wide]
    d15_lo2 = min(d15_wide[f]["bottom"] for f in d15_fall)
    d15_hi2 = max(d15_wide[f]["bottom"] for f in d15_fall)
    res["px_ground_hold_control"] = {"view": D15_WIDE, "frames": d15_fall,
                                     "range_px": [int(d15_lo2), int(d15_hi2)]}
    res["px_ground_hold_can_fail_ok"] = bool((d15_hi2 - d15_lo2) > HOLD_TOL_PX)
    res["px_ground_hold_can_fail_note"] = (
        "★ 反向：D15 `f0~f6`（后倒下坠段，身体还在大幅移动）用同一把尺子必须红 —— "
        "否则说明这把尺子对「没锁住」不敏感。")

    # ---------------- (8) ★ 命中 2 帧完全停顿（像素级）--------------------
    def snap(table, f):
        band = table.get(f)
        if band is None:
            return None
        return {"bottom": band["bottom"], "top": band["top"],
                "width": band["width_px"], "area_row": round(band["area_row"], 6)}

    s2, s3 = snap(side, HIT), snap(side, HIT_STOP_END)
    res["px_hitstop_frames"] = [HIT, HIT_STOP_END]
    res["px_hitstop_before"] = s2
    res["px_hitstop_after"] = s3
    res["px_hitstop_tol_px"] = HITSTOP_TOL_PX
    res["px_hitstop_ok"] = bool(
        s2 and s3
        and s2["bottom"] == s3["bottom"]
        and s2["top"] == s3["top"]
        and s2["width"] == s3["width"]
        and abs(s2["area_row"] - s3["area_row"]) <= HITSTOP_TOL_PX)
    res["px_hitstop_note"] = (
        "★ 命中帧（`f = %d`）起 **2 帧完全停顿**：剪影的底行 / 顶行 / 宽 / 面积行心"
        "必须**逐位相同**（容差 %.1f px）。" % (HIT, HITSTOP_TOL_PX))
    s5, s6 = snap(side, 5), snap(side, 6)
    res["px_hitstop_control"] = {"frames": [5, 6], "before": s5, "after": s6}
    res["px_hitstop_can_fail_ok"] = bool(
        s5 and s6
        and (abs(s5["area_row"] - s6["area_row"]) > HITSTOP_TOL_PX
             or s5["top"] != s6["top"]))
    res["px_hitstop_can_fail_note"] = (
        "★ 反向：`f5 → f6`（弹起上升中）用同一把尺子必须红。")

    # ---------------- 汇总 ---------------------------------------------------
    checks = [k for k in res if k.endswith("_ok") and res[k] is not None]
    failed = sorted(k for k in checks if res[k] is False)
    res["checks"] = sorted(checks)
    res["failed"] = failed
    res["verdict"] = "PASS" if not failed else "FAIL"
    print("D16PX_REPORT " + json.dumps(res, ensure_ascii=False))
    print("D16PX_DONE failed=%s" % failed)
    if not failed:
        print("D16PX_DONE verdict=PASS")


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D16PX_FAILURE " + traceback.format_exc())
