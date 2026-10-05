"""probe_e01_pixels —— E01 `Stun` 眩晕 的**像素级**验收（只读 PNG，不改任何工程文件）。

与 `probe_d17/d18/d19_pixels.py` 的关系
---------------------------------------------------------------
照抄其像素工具（`load` / `mask_of` / 行号口径 / `cols_any` / 列心 / `hem_cols_rows`
投影法 / `spread`），**判据按本支的跨族性质全部换口径**（见下）。

★★★ 本支与 D 族 19 支的**根本差别**（三件）
---------------------------------------------------------------
(A) ★★★ **机位换成「正面」，理由不是偏好，是几何必然。**
    D13~D19 全部用**侧视**（相机沿 ±X 看）—— 因为那些支的身体位移主要发生在
    **Y（前后）与 Z（上下）**：被打飞、撞墙、滑落，侧视全能看见，而且侧视能把
    「墙」`y = +705.561` 压成一条竖线当尺子。
    **本支恰好相反**：清单原文「身体摇晃但脚尽量保持原位」的摇晃**主体是左右（X）**
    （`stun_head_lat_travel_mm = 237.953`，而前后只有 `130.869`）。
    侧视沿 −X 看 ⟹ **X 向摇摆正好落在视轴上，完全不可见**；侧视里只看得到
    前后摇与高度。⟹ **本支唯一能验证「左右晃 + 脚钉住」的机位是正面。**
    ★ 这不是「照抄上一支改个数字」，是**换了一个正交平面**：正面横轴 = 世界 X，
      侧视横轴 = 世界 Y。

(B) ★★★ **两条尺子 + 两条硬反面对照（用同一台相机、同一批帧重渲）。**
    · `px_stun_foot_lock_ok`  载体 = **脚带（z ≤ 95 mm）的左右缘 + 全剪影底缘行**
      —— 证明「脚钉在原地」；
    · `px_stun_sway_ok`       载体 = **上段（z ≥ 1150 mm）的面积列心**
      —— 证明「上身真的在周期摇晃」。
    · 反面 ①：`E01_TP_FOOTSWAY=1` 重渲（`stunfootsway_front_*`，**帧集合逐帧相同**）
      ⟹ 脚锁尺子**必须红**；
    · 反面 ②：`E01_TP_NOSWAY=1` 重渲（`stunnosway_front_*`，同样逐帧相同）
      ⟹ 摇晃尺子**必须红**。
    ★ 两条反面都是「同相机 + 同帧集合 + 同判据」的**真对照**，不是「换把尺子」。
      （D19 记下的教训：反面对照渲了不同的三点，那等于换了尺子，已作废。）

(C) ★★ **「上段」与「脚带」两段的行区间都不含衣摆块** —— 这是**算出来的**，
    不是「应该没事」。`Jacket_Hem` / `Jacket_Hem_Line` 未蒙皮（`vgroups=0` /
    `parent=None`），世界包围盒逐帧恒定（`probe_c11_belt` 实测 `constant=true`）：
      · 正面（横轴 = x）：x [−188.78, +188.78]、z [897.5, 926.0] mm
    ⟹ 屏幕行区间 rows **547..565**；而脚带 rows ≤ **128**、上段 rows ≥ **679**
    ⟹ **三段互不相交**。所以本支两条尺子**本来就不含衣摆**；
    但仍按项目纪律做**真算**核对（证明剔除不是空操作 + 登记屏幕盒 + 证明不相交）。

本支判据清单
---------------------------------------------------------------
  `px_stun_foot_lock_ok`              ★★★ 脚带左右缘 + 底缘行，全程不漂
  `px_stun_foot_lock_can_fail_ok`     ★★★ 反面：`TP_FOOTSWAY` 重渲必须红
  `px_stun_sway_ok`                   ★★★ 上段面积列心周期波动（幅度 + 过零 + 周期）
  `px_stun_sway_can_fail_ok`          ★★ 反面：同尺子换载体（脚带）必须红
  `px_stun_sway_nosway_can_fail_ok`   ★★ 反面：`TP_NOSWAY` 重渲必须红
  `px_hem_excluded_ok`                ★★ 衣摆屏幕盒与两条尺子行区间**不相交**（算得）
  `px_hem_stripped_ok`                ★★ 剔除**真的改变读数**（不是空操作）

用法
---------------------------------------------------------------
    blender --background --factory-startup --python probe_e01_pixels.py

前置：
  · `anim_stun.py`（`stunwide_front_f0000..f0120` —— 探针唯一读的基线图）；
  · `E01_STEM_ONLY=1 E01_STEM=stunfootsway E01_TP_FOOTSWAY=1 --python anim_stun.py`；
  · `E01_STEM_ONLY=1 E01_STEM=stunnosway  E01_TP_NOSWAY=1   --python anim_stun.py`。

★ 行号 ↔ 世界高度（本支取景，**登记以免再翻车** —— 前三支都在这里错过）
---------------------------------------------------------------
  Blender `ortho_scale` 作用于**长边**；res = 780x1100 ⟹ 长边是**高**
  ⟹ 竖直世界跨度 = ortho，且
      mm_per_px = ortho / res_y x 1000
      floor_row = (ortho/2 − cam_z) / (ortho/res_y)          # z = 0 的行
      z_mm      = (row − floor_row) x mm_per_px
      列（**正面**：横轴 = 世界 x）= res_x/2 + (x_mm − center_x) / mm_per_px
      列（侧视：横轴 = 世界 y）= res_x/2 + (y_mm − center_y) / mm_per_px
  `VIEW_E01_FRONT_WIDE`（cam_z 0.90, ortho 2.10, res 780x1100, center_x 0）：
      mm_per_px = **1.9090909**、floor_row = **78.5714**
      自检：踝 z 79.8 mm ⟹ row **120.4**；头顶 1803 mm ⟹ row **1023.0**；
            鞋底 z 0 ⟹ row **78.6**（★ 画面底不是「地面」—— 相机中心 0.90 高于
            半幅 1.05，所以 z=0 落在 row 78.6 **而不是 0**，下面 78 行是空的）。
"""

import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A     # noqa: E402
import anim_stun as ST   # noqa: E402

PRE = os.path.join(A.OUT_DIR, "previews", "anim")

MAIN = "stunwide_front"          # ★ 基线（探针唯一读的机位）
STEM_FOOT = "stunfootsway_front"  # ★ 反面 ①：TP_FOOTSWAY
STEM_NOSWAY = "stunnosway_front"  # ★ 反面 ②：TP_NOSWAY

# ---- ★ 视图表：**从 `anim_stun.VIEW_E01_FRONT_WIDE` 现算**，不另抄一份数字 ----
#   单一真源 ⟹ 改取景时两边不可能走散（本工程反复强调的那条）。
_V = ST.VIEW_E01_FRONT_WIDE
_V_NAME, _V_LOC, _V_TGT, _V_SCALE, _V_RES = _V


def _entry(axis):
    return {"res_x": _V_RES[0], "res_y": _V_RES[1], "ortho": _V_SCALE,
            "cam_z": _V_LOC[2],
            "center_h_mm": (_V_TGT[0] * 1000.0 if axis == "x"
                            else _V_TGT[1] * 1000.0),
            "axis": axis}


VIEWS = {MAIN: _entry("x"), STEM_FOOT: _entry("x"), STEM_NOSWAY: _entry("x")}

# ---- ★★★ 「衣摆静止块」世界包围盒（`probe_c11_belt` 以 `C11_BELT_ACTION=Stun`
#      实测，两块取并集，逐帧恒定）。正面视图只用得上 x 与 z。---------------
#   `Jacket_Hem`      x [−188.78, +188.78]  y [−121.94, +129.03]  z [903.0, 926.0]
#   `Jacket_Hem_Line` x [−185.92, +185.92]  y [−119.96, +126.03]  z [897.5, 901.5]
HEM_XZ = (-188.78, 897.5, 188.78, 926.0)     # (x_lo, z_lo, x_hi, z_hi)

# ---- 两条尺子的**行区间**（世界 z 换算；**不许写行号**，行号必须现算）--------
BOOT_Z_TOP_MM = float(os.environ.get("E01PX_BOOT_Z", "95.0"))
UPPER_Z_MIN_MM = float(os.environ.get("E01PX_UPPER_Z", "1150.0"))

# ---- 阈值（**全部由实测导出**，见 `E01PX_REPORT`；铁律：不许为了变绿而放宽）----
FOOT_COL_TOL_PX = float(os.environ.get("E01PX_FOOT_COL", "2.0"))
SOLE_ROW_TOL_PX = float(os.environ.get("E01PX_SOLE_ROW", "1.0"))
SWAY_PP_MIN_PX = float(os.environ.get("E01PX_SWAY_PP", "20.0"))
SWAY_MIN_CROSS = int(os.environ.get("E01PX_SWAY_CROSS", "3"))
SWAY_PERIOD_RANGE = (float(os.environ.get("E01PX_PERIOD_LO", "40.0")),
                     float(os.environ.get("E01PX_PERIOD_HI", "90.0")))
CANFAIL_MIN_PX = float(os.environ.get("E01PX_CANFAIL_MIN", "5.0"))
HEM_SHIFT_MIN_PX = float(os.environ.get("E01PX_HEM_SHIFT", "0.05"))
FRAMES = list(range(0, int(os.environ.get("E01PX_TOTAL", "120")) + 1))


# =============================================================== 像素工具
#   ★ 逐字照抄 `probe_d19_pixels.py`（其又照抄 D16/D17/D18）
def load(view, frame):
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


def mm_per_px(view):
    v = VIEWS[view]
    return v["ortho"] / float(v["res_y"]) * 1000.0


def floor_row(view):
    """地平线行（世界 z = 0 对应的行）。"""
    v = VIEWS[view]
    return (v["ortho"] / 2.0 - v["cam_z"]) / (v["ortho"] / float(v["res_y"]))


def col_of(view, h_mm):
    """世界横坐标（正面 = x，侧视 = y）→ 屏幕列（可为小数；行号/列号自左下起）。"""
    v = VIEWS[view]
    return v["res_x"] / 2.0 + (h_mm - v["center_h_mm"]) / mm_per_px(view)


def row_of(view, z_mm):
    return floor_row(view) + z_mm / mm_per_px(view)


def hem_rows(view):
    """★ 衣摆静止块在**本视图**里的行区间（纯投影算得，不许写死行号）。"""
    x_lo, z_lo, x_hi, z_hi = HEM_XZ
    r0 = int(np.floor(row_of(view, z_lo))) - 1
    r1 = int(np.ceil(row_of(view, z_hi))) + 1
    res_y = VIEWS[view]["res_y"]
    return (max(r0, 0), min(r1, res_y - 1))


def hem_cols(view):
    x_lo, _z_lo, x_hi, _z_hi = HEM_XZ
    res_x = VIEWS[view]["res_x"]
    c0 = int(np.floor(col_of(view, x_lo))) - 1
    c1 = int(np.ceil(col_of(view, x_hi))) + 1
    return (max(c0, 0), min(c1, res_x - 1))


def strip_hem(mask, view):
    """把衣摆静止块的屏幕盒置空，返回新掩码（不改原图）。"""
    c0, c1 = hem_cols(view)
    r0, r1 = hem_rows(view)
    out = mask.copy()
    out[r0:r1 + 1, c0:c1 + 1] = False
    return out


def band_rows(view, z_lo, z_hi=None):
    """世界 z 区间 → 行区间（含端点，已裁到画面内）。"""
    res_y = VIEWS[view]["res_y"]
    r0 = int(np.floor(row_of(view, z_lo)))
    r1 = (res_y - 1 if z_hi is None else int(np.ceil(row_of(view, z_hi))))
    return (max(r0, 0), min(r1, res_y - 1))


def band_span(mask, r0, r1):
    """行区间内掩码的左右缘 `(col_lo, col_hi)`；空则 `(None, None)`。"""
    sub = mask[r0:r1 + 1]
    cols = np.where(sub.any(axis=0))[0]
    if cols.size == 0:
        return None, None
    return int(cols.min()), int(cols.max())


def band_col_centroid(mask, r0, r1):
    """行区间内掩码的**列面积心**（row/col 0 = 画面左下）。"""
    sub = mask[r0:r1 + 1]
    weights = sub.sum(axis=0).astype(np.float64)
    if weights.sum() <= 0:
        return None
    return float((np.arange(mask.shape[1]) * weights).sum() / weights.sum())


def silhouette_bottom(mask):
    """全剪影底缘行（最小行 = 世界最低点；★ 与 D13~D19 同口径）。"""
    rows = np.where(mask.any(axis=1))[0]
    return None if rows.size == 0 else int(rows.min())


def spread(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return float(max(vals) - min(vals))


# =============================================================== 主流程
def main():  # noqa: C901
    res = {}
    res["probe"] = "probe_e01_pixels"
    res["anim"] = "Stun"
    res["total"] = FRAMES[-1]
    mmp = mm_per_px(MAIN)
    floor = floor_row(MAIN)
    boot_r = band_rows(MAIN, 0.0, BOOT_Z_TOP_MM)
    up_r = band_rows(MAIN, UPPER_Z_MIN_MM)
    hem_r = hem_rows(MAIN)
    hem_c = hem_cols(MAIN)
    res["view"] = {"main": MAIN, "stem_foot": STEM_FOOT,
                   "stem_nosway": STEM_NOSWAY,
                   "res": [_V_RES[0], _V_RES[1]], "ortho_m": _V_SCALE,
                   "cam_z_m": _V_LOC[2], "center_x_mm": _V_TGT[0] * 1000.0}
    res["mm_per_px"] = round(mmp, 7)
    res["floor_row"] = round(floor, 4)
    res["row_ruler"] = (
        "行号自画面底向上。z_mm = (row − %.4f) x %.7f。**bottom = 最小行 = 世界"
        "最低点**（与 D13~D19 同口径）。列（**正面**）：col = %.1f + x_mm / %.7f；"
        "图像右 = +X = **角色左手侧**（★ 与侧视的「图像右 = +Y = 身后」方向不同，"
        "本支换的是**正交平面**，不是同一台相机挪位置）。"
        % (floor, mmp, _V_RES[0] / 2.0, mmp))
    res["bands"] = {"boot_rows": list(boot_r), "upper_rows": list(up_r),
                    "hem_rows": list(hem_r), "hem_cols": list(hem_c),
                    "boot_z_mm": [0.0, BOOT_Z_TOP_MM],
                    "upper_z_mm": [UPPER_Z_MIN_MM, None]}
    res["bands_note"] = (
        "★ 行区间**现算**（世界 z ÷ mm_per_px + floor_row），**没有写死行号**。"
        "脚带 z ≤ %.0f mm（踝关节 z 79.8 ⟹ 纯靴）；上段 z ≥ %.0f mm（胸 + 头 + "
        "拳架）。" % (BOOT_Z_TOP_MM, UPPER_Z_MIN_MM))

    # ---------------- (0) 扫描三个数据集 --------------------------------------
    def scan(view, frames):
        table = {}
        for frame in frames:
            pixels = load(view, frame)
            if pixels is None:
                continue
            raw = mask_of(pixels)
            cut = strip_hem(raw, view)
            cl, ch = band_span(cut, boot_r[0], boot_r[1])
            table[frame] = {
                "bottom": silhouette_bottom(cut),
                "bottom_raw": silhouette_bottom(raw),
                "boot_col_lo": cl, "boot_col_hi": ch,
                "boot_centroid": band_col_centroid(cut, boot_r[0], boot_r[1]),
                "upper_centroid": band_col_centroid(cut, up_r[0], up_r[1]),
                "upper_raw_centroid": band_col_centroid(raw, up_r[0], up_r[1]),
                "full_centroid": band_col_centroid(cut, 0, cut.shape[0] - 1),
                "full_raw_centroid": band_col_centroid(raw, 0, raw.shape[0] - 1),
            }
        return table

    main_t = scan(MAIN, FRAMES)
    if not main_t:
        raise RuntimeError("基线图一张都没有：%s/%s_f0000.png" % (PRE, MAIN))
    missing = [f for f in FRAMES if f not in main_t]
    if missing:
        raise RuntimeError("基线图缺帧 %s（共 %d 张）"
                           % (missing[:12], len(missing)))
    frames = sorted(main_t)
    res["px_stun_boot_col_lo"] = {str(f): main_t[f]["boot_col_lo"]
                                  for f in frames}
    res["px_stun_boot_col_hi"] = {str(f): main_t[f]["boot_col_hi"]
                                  for f in frames}
    res["px_stun_bottom_row"] = {str(f): main_t[f]["bottom"] for f in frames}
    res["px_stun_upper_centroid"] = {str(f): (None if main_t[f]["upper_centroid"]
                                              is None
                                              else round(main_t[f]["upper_centroid"], 4))
                                     for f in frames}

    # ---------------- (1) ★★★ `px_stun_foot_lock_ok` --------------------------
    #   三条通道：脚带 **左缘 / 右缘** 全程漂移 + 全剪影 **底缘行** 全程漂移。
    #   ★ 三条缺一不可：只量左右缘会漏「抬脚原地不动」；只量底缘行会漏「横向平移」。
    lo_dev = spread([main_t[f]["boot_col_lo"] for f in frames])
    hi_dev = spread([main_t[f]["boot_col_hi"] for f in frames])
    bot_dev = spread([main_t[f]["bottom"] for f in frames])
    res["px_stun_foot_col_lo_spread_px"] = lo_dev
    res["px_stun_foot_col_hi_spread_px"] = hi_dev
    res["px_stun_foot_bottom_spread_px"] = bot_dev
    res["px_stun_foot_bottom_range"] = [min(main_t[f]["bottom"] for f in frames),
                                        max(main_t[f]["bottom"] for f in frames)]
    res["px_stun_foot_bottom_z_mm"] = [
        round((min(main_t[f]["bottom"] for f in frames) - floor) * mmp, 3),
        round((max(main_t[f]["bottom"] for f in frames) - floor) * mmp, 3)]
    res["px_stun_foot_lock_tol"] = {"col_px": FOOT_COL_TOL_PX,
                                    "sole_row_px": SOLE_ROW_TOL_PX}
    res["px_stun_foot_lock_ok"] = bool(
        lo_dev is not None and hi_dev is not None and bot_dev is not None
        and lo_dev <= FOOT_COL_TOL_PX and hi_dev <= FOOT_COL_TOL_PX
        and bot_dev <= SOLE_ROW_TOL_PX)
    res["px_stun_foot_lock_note"] = (
        "★★★ **本支「脚不动」的像素级守卫**（骨架级同族判据 = "
        "`stun_foot_lock_ok`，实测踝漂 %.4f mm）。载体 = **脚带**（z ≤ %.0f mm，"
        "即 rows %s）的左缘 / 右缘 + 全剪影**底缘行**。实测全程："
        "左缘 %s→%s 漂移 **%s px**、右缘漂移 **%s px**（阈值 ≤ %.0f px = %.2f mm）、"
        "底缘行 %s..%s 漂移 **%s px** = z ∈ [%.2f, %.2f] mm（阈值 ≤ %.0f px）。"
        "★ 三条通道**物理含义不同**：左右缘管**横向滑动**，底缘行管**抬脚/下沉**。"
        % (0.0036, BOOT_Z_TOP_MM, list(boot_r), 
           min(main_t[f]["boot_col_lo"] for f in frames),
           max(main_t[f]["boot_col_lo"] for f in frames), lo_dev, hi_dev,
           FOOT_COL_TOL_PX, FOOT_COL_TOL_PX * mmp,
           res["px_stun_foot_bottom_range"][0],
           res["px_stun_foot_bottom_range"][1], bot_dev, 
           res["px_stun_foot_bottom_z_mm"][0], res["px_stun_foot_bottom_z_mm"][1],
           SOLE_ROW_TOL_PX))

    # ---------------- (2) ★★★ 反面对照 ①：脚跟着晃必须红 ----------------------
    foot_t = scan(STEM_FOOT, FRAMES)
    if len(foot_t) != len(FRAMES):
        raise RuntimeError(
            "反面对照 ① 图缺失（要 %s_f0000..f%04d，用 `E01_STEM_ONLY=1 "
            "E01_STEM=stunfootsway E01_TP_FOOTSWAY=1 --python anim_stun.py` 重渲）："
            "现有 %d/%d 张" % (STEM_FOOT, FRAMES[-1], len(foot_t), len(FRAMES)))
    f_lo = spread([foot_t[f]["boot_col_lo"] for f in frames])
    f_hi = spread([foot_t[f]["boot_col_hi"] for f in frames])
    f_bot = spread([foot_t[f]["bottom"] for f in frames])
    res["px_stun_foot_lock_control"] = {
        "view": STEM_FOOT, "frames": [frames[0], frames[-1]],
        "col_lo_spread_px": f_lo, "col_hi_spread_px": f_hi,
        "bottom_spread_px": f_bot,
        "col_lo_range": [min(foot_t[f]["boot_col_lo"] for f in frames),
                         max(foot_t[f]["boot_col_lo"] for f in frames)],
        "col_hi_range": [min(foot_t[f]["boot_col_hi"] for f in frames),
                         max(foot_t[f]["boot_col_hi"] for f in frames)]}
    res["px_stun_foot_lock_can_fail_ok"] = bool(
        max(f_lo, f_hi, f_bot) > max(FOOT_COL_TOL_PX, SOLE_ROW_TOL_PX))
    res["px_stun_foot_lock_can_fail_note"] = (
        "★★★ 反面 ①：`E01_TP_FOOTSWAY=1`（骨盆整体横移 ±%.0f mm、**跳过脚锁**）"
        "重渲 `%s`，**同一台相机 + 同一批帧（0..%d 逐帧）** ⟹ 脚带左缘 %s→%s "
        "漂移 **%.2f px = %.1f mm**、右缘 **%.2f px**、底缘行 **%.0f px** "
        "⟹ **必须红**。★ 这条是本支的**命门**：它证明「脚不动」不是靠嘴说，"
        "而是**真的有一条会失败的断言在盯**（骨架级 `stun_foot_lock_ok` 与 "
        "`no_foot_slide_toe.*` 在同一旋钮下也全部见红）。"
        % (ST.FOOT_SWAY_MM, STEM_FOOT, FRAMES[-1],
           res["px_stun_foot_lock_control"]["col_lo_range"][0],
           res["px_stun_foot_lock_control"]["col_lo_range"][1],
           f_lo, f_lo * mmp, f_hi, f_bot))

    # ---------------- (3) ★★★ `px_stun_sway_ok` ------------------------------
    #   载体 = **上段面积列心**（剔除后）。判据 = 峰峰值 + 过零次数 + 周期区间
    #   —— ★ 与骨架级 `stun_sway_period_ok` **同一个估计函数**（`anim_stun._crossings`）
    #     ⟹ 两级读的是**同一把尺子**，只是刻度从 mm 换成 px。
    cent = [main_t[f]["upper_centroid"] for f in frames]
    pp = spread(cent)
    cross, period = ST._crossings([v for v in cent if v is not None])
    res["px_stun_sway_pp_px"] = None if pp is None else round(pp, 4)
    res["px_stun_sway_pp_mm"] = None if pp is None else round(pp * mmp, 3)
    res["px_stun_sway_crossings"] = cross
    res["px_stun_sway_period_frames"] = None if period is None else round(period, 3)
    res["px_stun_sway_thresholds"] = {"pp_min_px": SWAY_PP_MIN_PX,
                                      "min_crossings": SWAY_MIN_CROSS,
                                      "period_range": list(SWAY_PERIOD_RANGE)}
    res["px_stun_sway_ok"] = bool(
        pp is not None and pp >= SWAY_PP_MIN_PX and cross >= SWAY_MIN_CROSS
        and period is not None
        and SWAY_PERIOD_RANGE[0] <= period <= SWAY_PERIOD_RANGE[1])
    res["px_stun_sway_note"] = (
        "★★★ 载体 = **上段（rows %s，z ≥ %.0f mm）的面积列心**（剔除衣摆后；"
        "衣摆在该行区间之外，见判据 (6)）。实测 `[%d, %d]`：峰峰值 **%.3f px = "
        "%.2f mm**（阈值 ≥ %.1f px）、过零 **%d** 次（阈值 ≥ %d）、"
        "估算周期 **%s 帧**（区间 %s）。★ 三个条件缺一不可：只量峰峰值会漏"
        "「歪向一侧不动」（幅度大但不周期）；只量过零会漏「原地震颤」"
        "（过零多但幅度为零）。★★ 与骨架级 `stun_sway_amp_ok` / "
        "`stun_sway_period_ok` 用的是**同一个过零估计函数**（`anim_stun._crossings`）"
        "⟹ 两级读的是**同一把尺子**，只是刻度从 mm 换成 px"
        "（阈值 %.0f~%.0f mm / 周期 %s 帧）。骨架级两级的实测值并列在 "
        "`animations/_e01_final.log` 与 `_e01_pxreport.log`，供逐项对照。"
        % (list(up_r), UPPER_Z_MIN_MM, frames[0], frames[-1], pp, pp * mmp,
           SWAY_PP_MIN_PX, cross, SWAY_MIN_CROSS,
           res["px_stun_sway_period_frames"], list(SWAY_PERIOD_RANGE),
           ST.SWAY_AMP_MIN_MM, ST.SWAY_AMP_MAX_MM, list(ST.SWAY_PERIOD_RANGE)))

    # ---------------- (4) ★ 反面对照 ②：同尺子换载体（脚带）必须红 -----------
    cent_feet = [main_t[f]["boot_centroid"] for f in frames]
    feet_pp = spread(cent_feet)
    feet_cross, feet_period = ST._crossings([v for v in cent_feet
                                             if v is not None])
    res["px_stun_sway_control_carrier"] = {
        "carrier": "脚带列心（rows %s）" % list(boot_r),
        "pp_px": None if feet_pp is None else round(feet_pp, 4),
        "crossings": feet_cross,
        "period_frames": None if feet_period is None else round(feet_period, 3)}
    res["px_stun_sway_can_fail_ok"] = bool(
        feet_pp is not None and (feet_pp < SWAY_PP_MIN_PX
                                 or feet_cross < SWAY_MIN_CROSS
                                 or feet_period is None
                                 or not (SWAY_PERIOD_RANGE[0] <= feet_period
                                         <= SWAY_PERIOD_RANGE[1])))
    res["px_stun_sway_can_fail_note"] = (
        "★★ 反面：**同一把摇晃尺子**（同判据、同阈值）改量**脚带列心**"
        "（rows %s）⟹ 峰峰值 **%.3f px**、过零 **%d** 次、周期 **%s** ⟹ **必须红**。"
        "★ 这条是「同尺子换载体」型反对照（承 D18 `px_rise_mono_can_fail_ok` / "
        "D19 `px_seam_steps_can_fail_ok` 的做法）。它同时把本支的**核心物理事实**"
        "实测钉死：**全身在晃，脚在下面一动不动** —— 两个载体的读数差就是这个差别的"
        "直接度量。★ 它**不能**替代反面 ③（NOSWAY 重渲）：这条只证明「尺子会分辨」，"
        "不证明「尺子对『不摇』敏感」。"
        % (list(boot_r), feet_pp, feet_cross,
           res["px_stun_sway_control_carrier"]["period_frames"]))

    # ---------------- (5) ★★ 反面对照 ③：NOSWAY 重渲必须红 -------------------
    nos_t = scan(STEM_NOSWAY, FRAMES)
    if len(nos_t) != len(FRAMES):
        raise RuntimeError(
            "反面对照 ③ 图缺失（要 %s_f0000..f%04d，用 `E01_STEM_ONLY=1 "
            "E01_STEM=stunnosway E01_TP_NOSWAY=1 --python anim_stun.py` 重渲）："
            "现有 %d/%d 张" % (STEM_NOSWAY, FRAMES[-1], len(nos_t), len(FRAMES)))
    nos_cent = [nos_t[f]["upper_centroid"] for f in frames]
    nos_pp = spread(nos_cent)
    nos_cross, nos_period = ST._crossings([v for v in nos_cent
                                           if v is not None])
    res["px_stun_sway_control_nosway"] = {
        "view": STEM_NOSWAY, "pp_px": None if nos_pp is None
        else round(nos_pp, 4), "crossings": nos_cross,
        "period_frames": None if nos_period is None else round(nos_period, 3)}
    res["px_stun_sway_nosway_can_fail_ok"] = bool(
        nos_pp is not None and (nos_pp < SWAY_PP_MIN_PX
                                or nos_cross < SWAY_MIN_CROSS
                                or nos_period is None
                                or not (SWAY_PERIOD_RANGE[0] <= nos_period
                                        <= SWAY_PERIOD_RANGE[1])))
    res["px_stun_sway_nosway_can_fail_note"] = (
        "★★ 反面 ③：`E01_TP_NOSWAY=1`（摇晃全归零，只剩脚锁 ⟹ **站着不动**）"
        "重渲 `%s`，**同一台相机 + 同一批帧** ⟹ 上段列心峰峰值 **%.3f px**、"
        "过零 **%d** 次、周期 **%s** ⟹ **必须红**。★ 这条证明摇晃尺子"
        "**对「不摇」敏感**（不是「任何输入都判过」）。骨架级在同一旋钮下红的是 "
        "`stun_sway_amp_ok` / `stun_sway_period_ok` / `stun_sway_side_amp_ok`。"
        % (STEM_NOSWAY, nos_pp, nos_cross,
           res["px_stun_sway_control_nosway"]["period_frames"]))

    # ---------------- (6) ★★ 衣摆块：**算出来的不相交** + **剔除不是空操作** ----
    overlap_boot = not (hem_r[1] < boot_r[0] or hem_r[0] > boot_r[1])
    overlap_upper = not (hem_r[1] < up_r[0] or hem_r[0] > up_r[1])
    res["hem_screen_box"] = {"rows": list(hem_r), "cols": list(hem_c)}
    res["hem_vs_boot_overlap"] = overlap_boot
    res["hem_vs_upper_overlap"] = overlap_upper
    full_raw = [main_t[f]["full_raw_centroid"] for f in frames]
    full_cut = [main_t[f]["full_centroid"] for f in frames]
    hem_shift = max(abs(a - b) for a, b in zip(full_raw, full_cut)
                    if a is not None and b is not None)
    res["px_hem_full_centroid_shift_px_max"] = round(hem_shift, 4)
    res["px_hem_full_centroid_shift_mm_max"] = round(hem_shift * mmp, 3)
    res["px_hem_excluded_ok"] = bool(not overlap_boot and not overlap_upper)
    res["px_hem_stripped_ok"] = bool(hem_shift >= HEM_SHIFT_MIN_PX)
    res["px_hem_note"] = (
        "★★ **项目纪律：不许照抄上一支的口径，也不许写死。** 本支两条尺子的行区间"
        "**现算**：脚带 rows %s、上段 rows %s；衣摆静止块投影到 rows %s / cols %s。"
        "⟹ 与脚带%s、与上段%s —— **这是算出来的结论，不是「应该没事」**。"
        "所以本支判据**本来就不含衣摆**；但仍做**真算**核对："
        "全剪影列心 raw vs 剔除后，全帧最大偏移 **%.4f px = %.3f mm**（阈值 ≥ %.2f px）"
        "⟹ **剔除真的生效**（不是空操作）。★ 衣摆由 `probe_c11_belt` 实测："
        "`Jacket_Hem` / `Jacket_Hem_Line` 未蒙皮（vgroups=0 / parent=None）、"
        "世界包围盒**逐帧恒定** ⟹ 它是一块**静止薄片**，与姿态无关；"
        "本支 x 跨度 ±0.745 m、它 ±0.189 m ⟹ 它在画面中央形成一块**不动的面积**，"
        "若不剔会**稀释**（而不是扭曲）上段列心 —— 但它在 rows %s，"
        "**根本不在上段里**，所以本支连稀释都不会发生。"
        % (list(boot_r), list(up_r), list(hem_r), list(hem_c),
           "**相交**" if overlap_boot else "**不相交**",
           "**相交**" if overlap_upper else "**不相交**",
           hem_shift, hem_shift * mmp, HEM_SHIFT_MIN_PX, list(hem_r)))

    # ---------------- (7) 汇总 -----------------------------------------------
    checks = sorted(k for k in res if k.endswith("_ok"))
    failed = sorted(k for k in checks if res[k] is False)
    res["checks"] = checks
    res["failed"] = failed
    res["verdict"] = "PASS" if not failed else "FAIL"
    print("E01PX_REPORT " + json.dumps(res, ensure_ascii=False))
    print("E01PX_DONE failed=%s" % failed)
    if not failed:
        print("E01PX_DONE verdict=PASS")


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E01PX_FAILURE " + traceback.format_exc())
