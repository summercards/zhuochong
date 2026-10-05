"""probe_d19_pixels —— D19 `Wall_Hit` 撞墙 的**像素级**验收（只读 PNG，不改任何工程文件）。

与 `probe_d17_pixels.py` / `probe_d18_pixels.py` 的关系
---------------------------------------------------------------
照抄其全部像素工具（`load` / `mask_of` / `hem_cols_rows` / `strip_hem` / `rows_any` /
`cols_any` / `area_row_centroid` / `bands` / `floor_row_of` / `mm_per_px_of`），
**判据按 D19 的跨族性质全部换口径**（见下）。

★★★ 本支与 D17/D18 的**根本差别**（三件，全部由实测定死）
---------------------------------------------------------------
(A) ★★★ **本支的两条「登记 N/A」必须转正，一条新尺子必须新建。**
    D17/D18 的 `px_hitstop_ok` / `px_seam_steps_ok` 都是 N/A（无命中帧 / 无弹道段），
    本支**两者都有**：
      · 撞墙帧 `f=14` ⟹ `hitstop_present` / `px_hitstop_ok` **真的启用**；
      · 来程承接**共享解析抛物线**（`T_PHASE = 31.5`）⟹ `px_seam_steps_ok` **真的生成**；
      · 撞墙后是**下落**（不是起身）⟹ 新建 `px_fall_ok`（**与 D18 的 `px_rise_ok` 反号**）。
    同时**新增本支独门尺子 `px_wall_side_ok`**（§1 风险 2：墙是竖直平面，侧视下退化成
    一条竖线，剪影顶/底缘**完全量不到墙**，只能用**右缘**量「被墙挡住」）。

(B) ★★★ **「弹道载体」只能是「最高点」，不能是「最低点」—— 这一次是实测把
    我自己的行号标签写反给抓出来的。**
    本工程（D13~D18）的既定行号口径是：
        `bottom` = **最小**行 = **世界最低点**（行号自画面底向上，+Z 向上）
        `top`    = **最大**行 = **世界最高点**
    本支第一版勘察脚本把 `rows_any()` 的 `(min_row, max_row)` 直接写成 `(top, bot)`
    —— **两个标签互换了**。后果（实测，见 `D19PX3` 报表）：
      · 载体取「最低点」（腿脚）时，已知曲率 LS 残差 = **20.65 px**（远超任何合理阈值）
        —— 因为空中姿态里**腿在折叠**，最低点带自己的相对运动（f2 一帧二阶差分 **−18 px**）；
      · 载体取「最高点」（`Hair_Mass`，后仰拱姿态下随骨盆**刚性平移**）时，
        残差 = **0.9509 px**（窗口 0..13）/ **1.1162 px**（窗口 0..14）。
    ⟹ **本支的弹道尺子钉在「最高点」上**。★ 诚实登记：这不是「放宽阈值」，
      而是**换对载体**；错的载体上**基线自己就红**（20.65 px），根本没有阈值可选。

(C) **取景基准**：**另立 `VIEW_D19_SIDE_WIDE`**，机位中心 y = **+200 mm**
    （不照抄 D17 的 −300、也不照抄 D18 的 +250）。
    D19 的 y 跨度是 **−180 … +706 mm**（骨盆从 +318 起、后缘顶到墙面 **705.561**），
    中点 ≈ **+263**；取 **+200** 是为了给「后缘贴墙」留出右侧余量（实测撞墙帧右缘
    落在 **col 540**，墙面解析列 **540.302**，画面宽 780 ⟹ 右余量 240 px 足够）。
    ★ **注意：本支的侧视只有一套机位** ⟹ `wallhit_side_*` 与 `wallhitwide_side_*`
      **是同一台相机的两次渲染**（逐位相同），**不是** D18 那种「side / wide 两套基准」。
      本探针只读 `wallhit_side_*`（帧 0..34 全），`wallhitwide_*` 仅供目检。

★ 反面对照（四组，全部用本工程已有 / 本轮已渲的图，不新拍）
---------------------------------------------------------------
  `px_wall_side_can_fail_ok`   **同一把右缘尺子**改量 `getupbwide_side`（D18 起身）
                               ⟹ 窗口 [4, 40] 右缘 max_dev = **337 px**（起身时四肢持续
                               展开、后缘一直在动）⟹ 必须红。这条证明这把尺子
                               **对「后缘还在动」敏感** —— 而它正是本支要断言的反面。
  `px_fall_can_fail_ok`        **同一把下落尺子**改量 D18 的面积行心 ⟹ 起身是**单调升**
                               （实测升 +182.5 px、29 帧在升）⟹ 必须红。
  `px_hitstop_can_fail_ok`     `D19_TP_NOHITSTOP=1` 重渲的 `wallhitstem_side_f0014/15/16`
                               （**与本支判据逐帧相同的三点**）⟹ 读数 spread 6 px /
                               5.98 px ⟹ 必须红。
  `px_seam_steps_can_fail_ok`  **同一把弹道尺子**改量撞墙后窗口 [17, 34] ⟹ 6.07 px ⟹ 必须红。
                               ★ 这条是「同尺子换窗口」型（照 D18 `px_rise_mono_can_fail_ok`
                               的做法），它同时把「撞墙真的打断了弹道」实测钉死。

本支判据清单
---------------------------------------------------------------
  `px_wall_side_ok`           ★★★ 独门尺子：右缘「来程猛增 → 停留停住（且不越过墙面列）
                              → 离开后回退」三段式
  `px_wall_side_can_fail_ok`  ★ 反面：同尺子量 D18 必须红
  `px_hitstop_ok`             ★★ 转正（D17/D18 是 N/A）：撞墙帧 `f14/15/16` 三点读数全冻
  `px_hitstop_can_fail_ok`    ★ 反面：抽掉停顿必须红
  `px_seam_steps_ok`          ★★ 转正（D18 是 N/A）：最高点 vs 共享抛物线的已知曲率残差
  `px_seam_steps_can_fail_ok` ★ 反面：同尺子量撞墙后窗口必须红
  `px_fall_ok`                ★★ 新建：撞墙后面积行心**单调不升** + 幅度阈值
  `px_fall_can_fail_ok`       ★ 反面：同尺子量 D18（起身）必须红
  `px_hem_excluded_ok`        ★★ 沿用 D18「真算」口径（**不许退回写死**）
  `px_hem_stripped_ok`        ★★ 沿用 D18「真算」口径（**不许退回写死**）

用法
---------------------------------------------------------------
    blender --background --factory-startup --python probe_d19_pixels.py

前置：
  · `anim_wall_hit.py`（要 `wallhit_side_f0000..f0034` 全套 —— **不挂墙**的探针用图）；
  · `D19_STEM_ONLY=1 D19_TP_NOHITSTOP=1` 重渲的 `wallhitstem_side_f0014/15/16`；
  · D18 的 `getupbwide_side_f0000..f0040` 全套（四组反面对照的其中两组）。

★ 行号 ↔ 世界高度（本支取景，登记以免再算错 —— 前两支都是在这里翻过车的）
---------------------------------------------------------------
  Blender `ortho_scale` 作用于**长边**；res = 780x1100 ⟹ 长边是**高**
  ⟹ 竖直世界跨度 = ortho，且
      z_mm = (row − floor_row) x mm_per_px
      floor_row   = (ortho/2 − cam_z) / (ortho/res_y)
      mm_per_px   = ortho/res_y x 1000
      列：col = 780/2 + (y_mm − center_y) / mm_per_px
  `VIEW_D19_SIDE_WIDE`（cam_z 1.45, ortho 3.70, res_y 1100, center_y +200）：
      floor_row = **118.9189**、mm_per_px = **3.363636**
      墙面 `y = +705.561 mm` ⟹ col = **540.302**
  ★ 自检：`wallhit_side_f0000` 最高点 955 ⟹ z = **2812.3 mm**；最低点 444 ⟹ z = **1093.3 mm**
    （★ 1093.294 正是清单 §0 误当成「骨盆 z」的那个数 —— 它其实是**最低点**；
      实测骨盆 z = **1931.937 mm**。本支以实测为准，偏差写进日志）。
    撞墙帧 f14：最高点 824 ⟹ z = 2371.6 mm、最低点 333 ⟹ z = 720.4 mm、右缘 col 540。
"""

import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A  # noqa: E402
import anim_jump_start as JS  # noqa: E402

PRE = os.path.join(A.OUT_DIR, "previews", "anim")

# ---- 视图表：(图高 px, 正交宽 m, 相机 z, 取景中心 y mm) -----------------------
#   ★ res_y / ortho 进尺子（`px_per_mm`）；cam_z 进地平线行；center_y 进「列」换算。
D19_SIDE = "wallhit_side"            # ★★ 本支探针唯一读的机位（= `wallhitwide_side`）
STEM_SIDE = "wallhitstem_side"       # ★ 反面对照 ④（NOHITSTOP）
D18_WIDE = "getupbwide_side"         # ★ 反面对照 ①②（D18 起身）
VIEWS = {
    D19_SIDE: (1100, 3.70, 1.45, 200.0),
    STEM_SIDE: (1100, 3.70, 1.45, 200.0),
    D18_WIDE: (1100, 3.60, 0.95, 250.0),
}

# ---- ★★★ 「衣摆静止块」世界包围盒（`probe_c11_belt` 实测；逐帧恒定，两块取并集）----
#   `Jacket_Hem` z [903.0, 926.0] / `Jacket_Hem_Line` z [897.5, 901.5]
#   y 并集 [−121.94, +129.03] mm
HEM_WORLD = (-121.94, 897.5, 129.03, 926.0)          # (y_lo, z_lo, y_hi, z_hi)

# ---- 帧号（**输出帧空间**，与 `anim_wall_hit.py` 的相位逐一对齐）--------------
START = 0
ENTER = 2
WALL_HIT = 14
HITSTOP_END = 16
SLIDE_END = 25
DETACH = 26
FALL_MID = 30
CANCEL = 25
TOTAL = 34

# ---- 弹道（与 `anim_wall_hit.py` **同一真源**，不许另抄一份常量）--------------
T_PHASE = 31.5
G_MM = JS.G_PER_FRAME * 1000.0                       # = 2.722222 mm/帧²

# ---- 墙（本支唯一的「世界实体」，来自 `anim_wall_hit.py` 的两遍实测冻结值）-----
WALL_Y_MM = 705.561

# ---- D18 对照帧区间（起身窗口；D18 的 LEGS_DOWN = 4、TOTAL = 40）-------------
D18_WIN = (4, 40)

# ---- 阈值（**全部由实测导出**，见文末 `D19PX_REPORT`）-------------------------
#   ★ 铁律：**不许为了变绿而放宽**。下面每个数字都注明实测值与余量。
APPROACH_MIN_PX = float(os.environ.get("D19PX_APPROACH_MIN", "60.0"))     # 实测 +101
STAY_TOL_PX = float(os.environ.get("D19PX_STAY_TOL", "3.0"))              # 实测 max_dev 2
WALL_COL_TOL_PX = float(os.environ.get("D19PX_WALLCOL_TOL", "2.0"))       # 实测 0.302
FALL_RETREAT_MIN_PX = float(os.environ.get("D19PX_RETREAT_MIN", "12.0"))  # 实测 26
FREEZE_TOL_PX = float(os.environ.get("D19PX_FREEZE_TOL", "1.0"))          # 实测 spread 0
SEAM_TOL_PX = float(os.environ.get("D19PX_SEAM_TOL", "2.0"))              # 实测 1.1162
FALL_MONO_TOL_PX = float(os.environ.get("D19PX_FALL_TOL", "1.0"))         # 实测最大上抬 0
FALL_DROP_MIN_PX = float(os.environ.get("D19PX_FALL_DROP_MIN", "100.0"))  # 实测 165.97


# =============================================================== 像素工具
#   ★ 逐字照抄 `probe_d16_pixels.py` / `probe_d17_pixels.py` / `probe_d18_pixels.py`
def load(view, frame):
    _res, _ortho, _cz, _cy = VIEWS[view]
    path = os.path.join(PRE, "%s_f%04d.png" % (view, frame))
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

    纯投影：`col = 780/2 + (y − center_y) / mm_per_px`、`row = floor_row + z / mm_per_px`。
    盒外再各放 1 px 余量（抗 float32 半像素误差）。
    """
    res_y, ortho, cam_z, cy = VIEWS[view]
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
    res_y, ortho, _cam_z, _cy = VIEWS[view]
    return (float(res_y) / ortho) / 1000.0


def rows_any(mask):
    """返回 `(最小行, 最大行)` —— ★ 最小行 = **世界最低点**，最大行 = **世界最高点**。"""
    rows = np.where(mask.any(axis=1))[0]
    return None if rows.size == 0 else (int(rows.min()), int(rows.max()))


def cols_any(mask):
    cols = np.where(mask.any(axis=0))[0]
    return None if cols.size == 0 else (int(cols.min()), int(cols.max()))


def area_row_centroid(mask):
    """**全剪影**面积行心（row 0 = 画面底，+Z 向上）。"""
    weights = mask.sum(axis=1).astype(np.float64)
    if weights.sum() <= 0:
        return None
    return float((np.arange(mask.shape[0]) * weights).sum() / weights.sum())


def bands(view, mask):
    """★ 命名口径与 D13~D18 **完全一致**（本支最容易在这里翻车）：
    `bottom` = 最小行 = 世界最低点；`top` = 最大行 = 世界最高点。"""
    ext = rows_any(mask)
    if ext is None:
        return None
    span = cols_any(mask)
    return {
        "bottom": ext[0], "top": ext[1],
        "area_row": area_row_centroid(mask),
        "col_lo": (None if span is None else span[0]),
        "col_hi": (None if span is None else span[1]),
        "height_px": int(ext[1] - ext[0] + 1),
        "width_px": (None if span is None else int(span[1] - span[0] + 1)),
    }


def floor_row_of(view):
    """地平线行：z = 0 对应 `(ortho/2 − cam_z) / (ortho/res_y)`。"""
    res_y, ortho, cam_z, _cy = VIEWS[view]
    return (ortho / 2.0 - cam_z) / (ortho / float(res_y))


def mm_per_px_of(view):
    res_y, ortho, _cz, _cy = VIEWS[view]
    return ortho / float(res_y) * 1000.0


def wall_col_of(view, wall_y_mm):
    """墙（`y = wall_y_mm` 的竖直平面）在**本视图**里的列 —— 解析算得，不靠看图。"""
    res_y, ortho, _cz, cy = VIEWS[view]
    mm = ortho / float(res_y) * 1000.0
    return 780 / 2.0 + (wall_y_mm - cy) / mm


# =============================================================== 形状工具
def mono_rising_violations(frames, values, tol):
    """序列**单调不降**（容差 tol）被违反的帧 —— 返回「比前一帧低超过 tol」的帧。"""
    bad = []
    for i in range(1, len(values)):
        if values[i] < values[i - 1] - tol:
            bad.append(frames[i])
    return bad


def mono_falling_violations(frames, values, tol):
    """序列**单调不升**（容差 tol）被违反的帧 —— 返回「比前一帧高超过 tol」的帧。"""
    bad = []
    for i in range(1, len(values)):
        if values[i] > values[i - 1] + tol:
            bad.append(frames[i])
    return bad


def known_curvature_residual(frames, values, mm_per_px):
    """★★★ **已知曲率**最小二乘残差。

    共享解析抛物线在**帧空间**里是
        z(f) = A + B f − (1/2) g f²          （`t = T_PHASE + f` 展开即得）
    ⟹ 行空间里 `row(f) = a + b f − (1/2)(g/mm_per_px) f²`。
    本函数**冻结**二次项系数为理论值（`−G/2/mm`），只最小二乘拟合 `a` / `b`，
    返回 `max|残差|`（px）。★ 这样量的是「**与共享抛物线有多远**」，而不是
    「这条曲线有多平滑」 —— 后者对相位错误完全不敏感。
    """
    x = np.array([float(f) for f in frames], dtype=np.float64)
    y = np.array([values[f] for f in frames], dtype=np.float64)
    c2 = -0.5 * G_MM / mm_per_px
    yy = y - c2 * x * x
    design = np.vstack([np.ones_like(x), x]).T
    coef, *_ = np.linalg.lstsq(design, yy, rcond=None)
    resid = yy - design @ coef
    return float(np.max(np.abs(resid))), [round(float(c), 6) for c in coef]


def spread(values):
    """一列读数的极差（px）—— 用于「冻结」判据。"""
    return float(max(values) - min(values))


# =============================================================== 主流程
def main():  # noqa: C901
    res = {}
    res["probe"] = "probe_d19_pixels"
    res["anim"] = "Wall_Hit"
    res["timeline"] = {"START": START, "ENTER": ENTER, "WALL_HIT": WALL_HIT,
                       "HITSTOP_END": HITSTOP_END, "SLIDE_END": SLIDE_END,
                       "DETACH": DETACH, "FALL_MID": FALL_MID,
                       "CANCEL": CANCEL, "TOTAL": TOTAL}

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
            band["raw_area_row"] = band_raw["area_row"]
            table[frame] = band
        return table

    d19 = scan(D19_SIDE, list(range(START, TOTAL + 1)))
    if not d19:
        raise RuntimeError("D19 side 静帧一张都没有：%s（stem=%s）" % (PRE, D19_SIDE))
    frames = sorted(d19)
    missing = [f for f in range(START, TOTAL + 1) if f not in d19]
    if missing:
        raise RuntimeError("D19 side 静帧缺帧：%s" % missing)

    stem = scan(STEM_SIDE, [WALL_HIT, WALL_HIT + 1, HITSTOP_END])
    if len(stem) != 3:
        raise RuntimeError(
            "反面对照图缺失（要 %s_f%04d/15/16，用 D19_STEM_ONLY=1 "
            "D19_TP_NOHITSTOP=1 --python anim_wall_hit.py 重渲）：%s"
            % (STEM_SIDE, WALL_HIT, STEM_SIDE))
    d18 = scan(D18_WIDE, list(range(0, D18_WIN[1] + 1)))
    if not d18:
        raise RuntimeError("D18 对照图缺失：%s" % D18_WIDE)
    d18_frames = sorted(d18)
    d18_win = [f for f in d18_frames if D18_WIN[0] <= f <= D18_WIN[1]]

    mmp = mm_per_px_of(D19_SIDE)
    floor = floor_row_of(D19_SIDE)
    wall_col = wall_col_of(D19_SIDE, WALL_Y_MM)
    res["view"] = {"stem": D19_SIDE, "res_y": VIEWS[D19_SIDE][0],
                   "ortho_m": VIEWS[D19_SIDE][1], "cam_z_m": VIEWS[D19_SIDE][2],
                   "center_y_mm": VIEWS[D19_SIDE][3]}
    res["view_note"] = (
        "★ 本支侧视**只有一套机位**（`wallhit_side_*` 与 `wallhitwide_side_*` "
        "逐位相同），不是 D18 的 side/wide 两套。取景中心 y = **+200 mm**"
        "（不照抄 D17 的 −300、也不照抄 D18 的 +250）：本支 y 跨度 −180…+706 mm"
        "（后缘顶到墙面 **705.561**），取 +200 给「贴墙」留出右侧余量"
        "（撞墙帧右缘实测落 col **540**，墙面解析列 **%.3f**，"
        "画面宽 780 ⟹ 右余量 240 px）。" % wall_col)
    res["mm_per_px"] = round(mmp, 6)
    res["floor_row"] = round(floor, 4)
    res["wall_y_mm"] = WALL_Y_MM
    res["wall_col_px"] = round(wall_col, 3)
    res["row_ruler"] = (
        "行号自画面底向上。z_mm = (row − %.4f) x %.6f。"
        "**bottom = 最小行 = 世界最低点；top = 最大行 = 世界最高点**"
        "（与 D13~D18 同口径）。列：col = 390 + (y_mm − 200) / %.6f；"
        "图像右 = +Y = 身后。" % (floor, mmp, mmp))

    res["top_row"] = {str(f): d19[f]["top"] for f in frames}
    res["bottom_row"] = {str(f): d19[f]["bottom"] for f in frames}
    res["raw_top_row"] = {str(f): d19[f]["raw_top"] for f in frames}
    res["raw_bottom_row"] = {str(f): d19[f]["raw_bottom"] for f in frames}
    res["col_hi"] = {str(f): d19[f]["col_hi"] for f in frames}
    res["area_row"] = {str(f): r3(d19[f]["area_row"]) for f in frames}
    res["top_z_mm"] = {str(f): round((d19[f]["top"] - floor) * mmp, 2)
                       for f in frames}
    res["bottom_z_mm"] = {str(f): round((d19[f]["bottom"] - floor) * mmp, 2)
                          for f in frames}

    # ---------------- (1) ★★★ 独门尺子 `px_wall_side_ok` ----------------------
    #   载体 = **右缘**（`col_hi`，剔除后）。逻辑三段：
    #     ① 来程 `[START, WALL_HIT]`：右缘猛增（人真的被击飞向墙去）
    #     ② 停留 `[WALL_HIT, SLIDE_END]`：右缘**停住**（被墙挡住）且**不越过墙面列**
    #     ③ 离开 `[DETACH, TOTAL]`：右缘**回退**（离开墙面、开始下落）
    appr = d19[WALL_HIT]["col_hi"] - d19[START]["col_hi"]
    stay_vals = [d19[f]["col_hi"] for f in range(WALL_HIT, SLIDE_END + 1)]
    stay_dev = spread(stay_vals)
    stay_max = max(stay_vals)
    cross = stay_max - wall_col
    fall_from = d19[DETACH]["col_hi"]
    fall_to = d19[TOTAL]["col_hi"]
    retreat = fall_from - fall_to
    res["px_wall_side_approach_px"] = int(appr)
    res["px_wall_side_stay_vals"] = stay_vals
    res["px_wall_side_stay_max_dev_px"] = stay_dev
    res["px_wall_side_stay_max_col"] = int(stay_max)
    res["px_wall_side_cross_px"] = round(cross, 3)
    res["px_wall_side_cross_mm"] = round(cross * mmp, 3)
    res["px_wall_side_fall_retreat_px"] = int(retreat)
    res["px_wall_side_thresholds"] = {
        "approach_min_px": APPROACH_MIN_PX, "stay_tol_px": STAY_TOL_PX,
        "wall_col_tol_px": WALL_COL_TOL_PX, "retreat_min_px": FALL_RETREAT_MIN_PX}
    res["px_wall_side_ok"] = bool(
        appr >= APPROACH_MIN_PX
        and stay_dev <= STAY_TOL_PX
        and cross <= WALL_COL_TOL_PX
        and retreat >= FALL_RETREAT_MIN_PX)
    res["px_wall_side_note"] = (
        "★★★ **本支独门尺子**（见 §B：墙是竖直平面 ⟹ 侧视下退化成一条竖线，"
        "剪影顶/底缘**完全量不到墙**，只能用**右缘**）。三段式："
        "① 来程 `[%d, %d]` 右缘 %d → %d = **%+d px**（阈值 ≥ %.0f）；"
        "② 停留 `[%d, %d]` 右缘 %s，**max_dev = %d px**（阈值 ≤ %.0f），"
        "且最大 %d **不越过墙面解析列 %.3f**（越过量 %+.3f px = %+.3f mm，"
        "阈值 ≤ %.0f px）；③ 离开 `[%d, %d]` 右缘 %d → %d = **回退 %d px**"
        "（阈值 ≥ %.0f）。★ 三段的**物理含义各不相同**，缺一段都不足以证明"
        "「被墙挡住」：只有②会误判「人压根没动」；只有①会误判「一直在动没停过」。"
        % (START, WALL_HIT, d19[START]["col_hi"], d19[WALL_HIT]["col_hi"], appr,
           APPROACH_MIN_PX, WALL_HIT, SLIDE_END, stay_vals, stay_dev, STAY_TOL_PX,
           stay_max, wall_col, cross, cross * mmp, WALL_COL_TOL_PX,
           DETACH, TOTAL, fall_from, fall_to, retreat, FALL_RETREAT_MIN_PX))

    # ---------------- (2) ★ 反面对照：同尺子量 D18 必须红 ----------------------
    d18_chi = [d18[f]["col_hi"] for f in d18_win]
    d18_chi_dev = spread(d18_chi)
    res["px_wall_side_control_d18"] = {
        "view": D18_WIDE, "window": list(D18_WIN),
        "col_hi_first": d18_chi[0], "col_hi_last": d18_chi[-1],
        "col_hi_max_dev": d18_chi_dev}
    res["px_wall_side_can_fail_ok"] = bool(d18_chi_dev > STAY_TOL_PX)
    res["px_wall_side_can_fail_note"] = (
        "★ 反向：**同一把右缘尺子**（判据 = 窗口内 `max_dev <= %.0f px`）改量 "
        "`%s`（D18 起身，窗口 `%s`）⟹ 右缘 max_dev = **%.0f px**（%d → %d，"
        "四肢持续展开、后缘一直在动）⟹ **必须红**。这条证明这把尺子"
        "**对「后缘还在动」敏感** —— 而「后缘停住」正是本支要断言的。"
        % (STAY_TOL_PX, D18_WIDE, list(D18_WIN), d18_chi_dev,
           d18_chi[0], d18_chi[-1]))

    # ---------------- (3) ★★ `px_hitstop_ok`（转正）---------------------------
    #   载体 = **四点读数向量** `(bottom, top, col_hi, area_row)` 在 `f = 14/15/16` 上全冻。
    keys = ("bottom", "top", "col_hi", "area_row")
    hit_frames = (WALL_HIT, WALL_HIT + 1, HITSTOP_END)
    base_spread = {k: spread([d19[f][k] for f in hit_frames]) for k in keys}
    stem_spread = {k: spread([stem[f][k] for f in hit_frames]) for k in keys}
    res["px_hitstop_frame"] = WALL_HIT
    res["px_hitstop_frames"] = list(hit_frames)
    res["px_hitstop_reading"] = {str(f): {k: r3(d19[f][k]) for k in keys}
                                 for f in hit_frames}
    res["px_hitstop_spread_px"] = {k: round(v, 4) for k, v in base_spread.items()}
    res["px_hitstop_tol_px"] = FREEZE_TOL_PX
    res["px_hitstop_ok"] = bool(max(base_spread.values()) <= FREEZE_TOL_PX)
    res["px_hitstop_note"] = (
        "★★ **本判据在本支转正（D17/D18 都是 N/A：它们没有命中帧）**。"
        "撞墙帧 `f = %d`（清单 §6：命中关键帧做 **2~4 帧**完全停顿），实测 "
        "`f = %d/%d/%d` 四点读数 `(bottom, top, col_hi, area_row)` "
        "**逐位完全相同**：%s（spread 全 %.1f，阈值 ≤ %.1f px）。"
        "★ 载体取**四点向量**而不是单点：撞墙时**姿态与位置全冻**（见 "
        "`anim_wall_hit.py` 的 `wall_hitstop_ok`）⟹ 只要有任何一维在动，"
        "这条就该红。★ 骨架级同族判据 = `wall_hitstop_ok` / `hitstop_present`。"
        % (WALL_HIT, WALL_HIT, WALL_HIT + 1, HITSTOP_END,
           res["px_hitstop_reading"], max(base_spread.values()), FREEZE_TOL_PX))

    # ---------------- (4) ★ 反面对照 ④：抽掉停顿必须红 ------------------------
    res["px_hitstop_control_nohitstop"] = {
        "stem": STEM_SIDE, "frames": list(hit_frames),
        "reading": {str(f): {k: r3(stem[f][k]) for k in keys} for f in hit_frames},
        "spread_px": {k: round(v, 4) for k, v in stem_spread.items()}}
    res["px_hitstop_can_fail_ok"] = bool(max(stem_spread.values()) > FREEZE_TOL_PX)
    res["px_hitstop_can_fail_note"] = (
        "★ 反向：`D19_TP_NOHITSTOP=1` 重渲的 `%s_f%04d/%d/%d`"
        "（**与本支判据逐帧相同的三点** —— 第一版渲的是 `[14, 16, 30]`，缺 f15，"
        "那等于**换了尺子**，已改掉）⟹ 实测 spread `bottom` **%.0f px** / "
        "`top` **%.0f px** / `area_row` **%.2f px** ⟹ **必须红**。"
        "★ 顺带登记：`col_hi` 的 spread 在反对照里是 **%.0f**"
        "（右缘本来就被墙钉着）—— 所以本判据**必须**用四点向量；"
        "只量右缘会让 ④ 组漏过去。"
        % (STEM_SIDE, WALL_HIT, WALL_HIT + 1, HITSTOP_END,
           stem_spread["bottom"], stem_spread["top"], stem_spread["area_row"],
           stem_spread["col_hi"]))

    # ---------------- (5) ★★ `px_seam_steps_ok`（转正）-----------------------
    #   载体 = **最高点**（`top` = 最大行 = `Hair_Mass`，后仰拱姿态下随骨盆刚性平移）。
    seam_win = list(range(START, WALL_HIT + 1))
    tops = {f: float(d19[f]["top"]) for f in frames}
    seam_res, seam_coef = known_curvature_residual(seam_win, tops, mmp)
    res["px_seam_window"] = [START, WALL_HIT]
    res["px_seam_carrier"] = "top（最大行 = 世界最高点 = Hair_Mass）"
    res["px_seam_max_residual_px"] = round(seam_res, 4)
    res["px_seam_max_residual_mm"] = round(seam_res * mmp, 3)
    res["px_seam_ls_coef"] = seam_coef
    res["px_seam_tol_px"] = SEAM_TOL_PX
    res["px_seam_ok"] = bool(seam_res <= SEAM_TOL_PX)
    res["px_seam_steps_ok"] = res["px_seam_ok"]
    res["px_seam_steps_note"] = (
        "★★ **本判据在本支转正（D18 是 N/A：D18 的竖直通道没有弹道段）**。"
        "本支来程承接**共享解析抛物线**（`T_PHASE = %.1f`，与 D13 逐位相同）⟹ "
        "在**帧空间**里 `row(f) = a + b f − (1/2)(g/mm_per_px) f²`，"
        "二次项系数**理论值 = −%.6f px/帧²**（`g = %.6f mm/帧²`）。"
        "本判据**冻结二次项**、只最小二乘拟合 `a`/`b`，取 `max|残差|` —— "
        "量的是「**与共享抛物线有多远**」，而不是「曲线有多平滑」"
        "（后者对相位错误完全不敏感）。实测窗口 `[%d, %d]`："
        "**max|残差| = %.4f px = %.3f mm**（阈值 ≤ %.1f px）。"
        "★★★ **载体为什么必须是「最高点」**：本支空中姿态里**腿在折叠**，"
        "「最低点」带自己的相对运动（二阶差分 f2 一帧 **−18 px**）⟹ "
        "同一把尺子钉在最低点上，**基线自己就是 %.2f px**，根本没有阈值可选。"
        "「最高点」（`Hair_Mass`）随骨盆**刚性平移**，才是干净的弹道载体。"
        % (T_PHASE, 0.5 * G_MM / mmp, G_MM, START, WALL_HIT, seam_res,
           seam_res * mmp, SEAM_TOL_PX, 20.6504))

    # ---------------- (6) ★ 反面对照：同尺子量撞墙后窗口必须红 ---------------
    post_win = list(range(HITSTOP_END + 1, TOTAL + 1))
    post_res, _ = known_curvature_residual(post_win, tops, mmp)
    res["px_seam_control_window"] = [HITSTOP_END + 1, TOTAL]
    res["px_seam_control_residual_px"] = round(post_res, 4)
    res["px_seam_steps_can_fail_ok"] = bool(post_res > SEAM_TOL_PX)
    res["px_seam_steps_can_fail_note"] = (
        "★ 反向：**同一把弹道尺子**（判据 = `max|残差| <= %.1f px`）改量**撞墙后**"
        "窗口 `[%d, %d]` ⟹ 实测 **%.4f px** ⟹ **必须红**。物理含义：撞墙"
        "**真的打断了弹道**（硬直冻结 + 贴墙下滑 + 新抛物线），后段不可能还落在"
        "**来程那条**抛物线上。★ 这是「同尺子换窗口」型反对照"
        "（照 D18 `px_rise_mono_can_fail_ok` 的做法）。"
        % (SEAM_TOL_PX, HITSTOP_END + 1, TOTAL, post_res))

    # ---------------- (7) ★★ `px_fall_ok`（新建）----------------------------
    #   载体 = **面积行心**（剔除后）。撞墙后必须**单调不升**（在下落）。
    fall_win = list(range(WALL_HIT, TOTAL + 1))
    fall_vals = [d19[f]["area_row"] for f in fall_win]
    fall_bad = mono_falling_violations(fall_win, fall_vals, FALL_MONO_TOL_PX)
    fall_drop = float(fall_vals[0] - fall_vals[-1])
    res["px_fall_window"] = [WALL_HIT, TOTAL]
    res["px_fall_violation_frames"] = fall_bad
    res["px_fall_drop_px"] = round(fall_drop, 3)
    res["px_fall_drop_mm"] = round(fall_drop * mmp, 2)
    res["px_fall_mono_tol_px"] = FALL_MONO_TOL_PX
    res["px_fall_drop_min_px"] = FALL_DROP_MIN_PX
    res["px_fall_area_row"] = {str(f): r3(d19[f]["area_row"]) for f in fall_win}
    res["px_fall_ok"] = bool(not fall_bad and fall_drop >= FALL_DROP_MIN_PX)
    res["px_fall_note"] = (
        "★★ **本支新建**（撞墙后是**下落**，不是起身 —— 与 D18 的 `px_rise_ok` "
        "**反号**）。载体 = **面积行心**（`area_row_centroid`，剔除衣摆块后）。"
        "行号自画面底向上 ⟹ **下落 = 行心单调不升**。实测窗口 `[%d, %d]`："
        "%.3f → %.3f，**总降幅 %.3f px = %.2f mm**（阈值 ≥ %.0f px），"
        "违反帧 = %s（容差 %.1f px）。★ 幅度守卫（防「绿得太容易」）："
        "阈值取实测的 %.0f%%。"
        % (WALL_HIT, TOTAL, fall_vals[0], fall_vals[-1], fall_drop, fall_drop * mmp,
           FALL_DROP_MIN_PX, fall_bad or "无", FALL_MONO_TOL_PX,
           100.0 * FALL_DROP_MIN_PX / fall_drop if fall_drop else 0.0))

    # ---------------- (8) ★ 反面对照：同尺子量 D18（起身）必须红 ------------
    d18_area = [d18[f]["area_row"] for f in d18_win]
    d18_rise = float(d18_area[-1] - d18_area[0])
    d18_rising = [f for i, f in enumerate(d18_win)
                  if i and d18_area[i] > d18_area[i - 1] + FALL_MONO_TOL_PX]
    res["px_fall_control_d18"] = {
        "view": D18_WIDE, "window": list(D18_WIN),
        "area_row_first": r3(d18_area[0]), "area_row_last": r3(d18_area[-1]),
        "rise_px": round(d18_rise, 3), "rising_frames": d18_rising}
    res["px_fall_can_fail_ok"] = bool(len(d18_rising) >= 1)
    res["px_fall_can_fail_note"] = (
        "★ 反向：**同一把下落尺子**（判据 = 单调不升 + 降幅 ≥ %.0f px）改量 `%s`"
        "（D18 起身，窗口 `%s`）⟹ 面积行心 **%.3f → %.3f = 升 %+.1f px**，"
        "有 **%d** 帧在升 ⟹ **必须红**。★ 这不是「尺子坏了」，"
        "是这支动画在**往上**。"
        % (FALL_DROP_MIN_PX, D18_WIDE, list(D18_WIN),
           d18_area[0], d18_area[-1], d18_rise, len(d18_rising)))

    # ---------------- (9) ★★ 衣摆块：**真的有块可剔**（沿用 D18 真算口径）----
    #   ★★ 本支与 D18 **反号**：D18 从**仰卧**起步（身体全程低于 926 mm）⟹ 衣摆
    #      接管**顶缘**；D19 从**高空**起步（最低点 1093 mm 起）⟹ 衣摆静止块
    #      （z 897.5~926）在**下方**，接管的是**底缘**。这是「同一块布、两支不同侧」。
    owner = [f for f in frames if d19[f]["raw_bottom"] != d19[f]["bottom"]]
    res["hem_owner_frames"] = owner
    res["hem_owner_count"] = len(owner)
    res["hem_owner_side"] = "bottom（最小行 = 世界最低点）"
    res["hem_screen_box_px"] = list(hem_cols_rows(D19_SIDE))
    res["hem_owner_side_top_frames"] = [f for f in frames
                                        if d19[f]["raw_top"] != d19[f]["top"]]
    res["px_hem_excluded_ok"] = bool(len(owner) >= 1)
    res["px_hem_note"] = (
        "★★ **沿用 D18 的「真算」口径（不许退回写死）**：`Jacket_Hem` / "
        "`Jacket_Hem_Line` 未蒙皮（`vgroups=0` / `parent=None`），世界包围盒"
        "**逐帧恒定**（`probe_c11_belt` 实测 `constant=true`，z [897.5, 926.0] mm、"
        "y [−121.94, +129.03] mm）⟹ 在本视图里固定在 **cols 293..370 / "
        "rows 384..396**。实测「raw 底缘 ≠ 剔除后底缘」的帧共 **%d** 帧"
        "（%s…%s）⟹ **必须剔**。★★ **本支与 D18 反号、必须写清楚**：D18 从"
        "**仰卧**起步（身体全程低于 926 mm）⟹ 同一块布接管的是**顶缘**；"
        "D19 从**高空**起步（最低点 **1093.3 mm** 起）⟹ 布在**下方**，"
        "接管的是**底缘**（实测「raw 顶缘 ≠ 剔除后顶缘」的帧 = %s，空）。"
        "**同一块布、两支各占一侧** —— 这也是「不许照抄上一支口径」的又一处实例。"
        % (len(owner), owner[0] if owner else "-", owner[-1] if owner else "-",
           res["hem_owner_side_top_frames"] or "无"))
    res["px_hem_stripped_ok"] = bool(d19[START]["raw_bottom"] != d19[START]["bottom"])
    res["px_hem_stripped_note"] = (
        "★★ 与上一条互为印证：**首帧** raw 底缘 **%d px**（z %.1f mm = 静止薄片底）"
        "→ 剔除后 **%d px**（z %.1f mm = 角色自己的最低点）。读数**确实变了**，"
        "证明剔除**真的生效**（不是空操作）。"
        % (d19[START]["raw_bottom"], (d19[START]["raw_bottom"] - floor) * mmp,
           d19[START]["bottom"], res["bottom_z_mm"][str(START)]))

    # ---------------- 汇总 ---------------------------------------------------
    checks = sorted(k for k in res if k.endswith("_ok"))
    failed = sorted(k for k in checks if res[k] is False)
    res["checks"] = checks
    res["failed"] = failed
    res["verdict"] = "PASS" if not failed else "FAIL"
    print("D19PX_REPORT " + json.dumps(res, ensure_ascii=False))
    print("D19PX_DONE failed=%s" % failed)
    if not failed:
        print("D19PX_DONE verdict=PASS")


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D19PX_FAILURE " + traceback.format_exc())
