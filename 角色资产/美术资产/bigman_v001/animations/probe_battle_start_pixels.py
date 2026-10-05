"""probe_battle_start_pixels —— E05 `Battle_Start` 开战 的**像素级**验收（只读 PNG + 一个 json）。

逐字照抄 `probe_spawn_pixels.py` 的像素工具（`load` / `mask_of` / 行号口径 /
`band_span` / `col_centroid` / `top_row` / `bottom_row` / `strip_hem` / `spread`），
但**尺子的几何轴与机位全部换口径**。

★★★ 本支与 E01~E04 的**根本差别**（三条，写在最前面）
---------------------------------------------------------------------
(A) ★★★ **本支的命门（碰拳）在「手与手之间」，这是全新的一维**。
    E01~E04 的像素尺子量的都是「身体 vs 世界实体」（脚 vs 地面 / 脚 vs 站架锚点 /
    身体 vs 墙）。本支要量的是**两个手部剪影之间的关系** ⟹ 必须**用分层渲染**
    （`bstart_hand_front_*`：只留 `Hand_Palm_*` / `Finger_*` / `Thumb_*` 三族网格）
    —— 全身图里手被袖子和大臂包住，中心距根本读不出来。
    · **碰拳贴合** = 两个手部团块之间的**内侧空隙**（列方向的空条宽度）；
    · **碰拳对称** = 两个团块关于中线的镜像偏差。
    ★ 空隙「小」= 贴上了；★ 但**不能为 0 或负**（负 = 两个团块在图像上重叠 = 穿模）。

(B) ★★★ **「活动肩膀」的像素载体必须选在旋钮真的会动的那一维**。
    骨架级 `bstart_shoulder_ok` 量的是「肩骨行程 + 肩峰世界行程」。像素尺子若也去量
    「肩峰值 == 几何投影值」就是**自指量**（同一个公式的两个输出）。
    ⟹ 本支像素尺子量的是**渲染剪影自身的横向展开**：正面图在**肩高带**里的
    **列跨度**（`band_span` 的宽度）。肩一抬，大臂外沿就外扩 ⟹ 跨度变大；肩不动
    （`TP_NOSHOULDER`）则跨度回到站架读数 ⟹ 判据见红。**这是纯图像量。**
    ★ 为什么不量「剪影顶行」：本支**不跳不躺**，头顶位置被 neck/head 的微小俯仰
    主导（<1°），`TP_NOSHOULDER` **完全不影响它** ⟹ 会造出一个「正反都过」的假绿
    （E04 `px_spawn_head_drop` 第一版同款陷阱）。

(C) ★★ **`Jacket_Hem` / `Jacket_Hem_Line` 是未蒙皮的静止薄片**（`probe_c11_belt`
    实测 `vgroups=0` / `parent=None`）⟹ 世界包围盒**与姿态无关**。本支不跳，但它们
    的世界 z ∈ [897.5, 926] mm 正好落在**鞋底尺子带的上沿附近** ⟹ 必须**算出**
    它们与两条尺子带**不相交**，而不是「应该没事」。

判据清单
---------------------------------------------------------------------
  `px_bstart_clash_gap_ok`            ★★★ 正面·手层：碰拳帧两团块内侧空隙 ≤ 上限
  `px_bstart_clash_gap_can_fail_ok`   ★★★ 反面 ②：`TP_FARCLASH` 重渲必须让上条红
  `px_bstart_clash_sym_ok`            ★★★ 正面·手层：碰拳帧两团块关于中线镜像
  `px_bstart_clash_sym_can_fail_ok`   ★★★ 反面 ⑦：`TP_ASYMCLASH` 重渲必须让上条红
  `px_bstart_shoulder_span_ok`        ★★ 正面·全身：肩高带列跨度 在 SHRUG 明显 > 站架
  `px_bstart_shoulder_span_can_fail_ok` ★★ 反面 ⑤：`TP_NOSHOULDER` 重渲必须让上条红
  `px_bstart_body_sink_ok`            ★★ 侧视·全身：碰拳帧剪影顶行相对站架下移
  `px_bstart_body_sink_can_fail_ok`   ★★ 反面 ⑩：`TP_NOSINK` 重渲必须让上条红
  `px_bstart_foot_lock_ok`            ★★ 侧视：全程脚带（底行 + 列心）不漂
  `px_bstart_foot_lock_can_fail_ok`   ★★ 反面 ⑥：`TP_FOOTSWAY` 重渲必须让上条红
  `px_bstart_hem_excluded_ok`         ★★ 衣摆屏幕盒与全部尺子带**不相交**（算得）
  `px_bstart_hem_stripped_ok`         ★★ 剔除衣摆**真的改变读数**（不是空操作）

用法
---------------------------------------------------------------------
    blender --background --factory-startup --python probe_battle_start_pixels.py
    E05PX_MEASURE=1   只量不判（**开工定阈值用**）

前置（帧集合**逐帧相同**）：
  · 基线：`bstart_hand_front_f*`（手层，正面）/ `bstart_front_front_f*`（全身，正面）
          / `bstart_side_side_f*`（全身，侧视）+ `_e05_landmark.json`；
  · 反面 ②：`SKIP_RENDER=1 E05_STEM_ONLY=1 E05_STEM=bstartfar   E05_TP_FARCLASH=1`；
  · 反面 ⑤：`SKIP_RENDER=1 E05_STEM_ONLY=1 E05_STEM=bstartsho   E05_TP_NOSHOULDER=1`；
  · 反面 ⑥：`SKIP_RENDER=1 E05_STEM_ONLY=1 E05_STEM=bstartfoot  E05_TP_FOOTSWAY=1`；
  · 反面 ⑦：`SKIP_RENDER=1 E05_STEM_ONLY=1 E05_STEM=bstartasym  E05_TP_ASYMCLASH=1`；
  · 反面 ⑩：`SKIP_RENDER=1 E05_STEM_ONLY=1 E05_STEM=bstartnosink E05_TP_NOSINK=1`。
"""
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A            # noqa: E402
import anim_battle_start as B   # noqa: E402

PRE = A.PREVIEW_DIR

MAIN_SIDE = "bstart_side"
MAIN_FRONT = "bstart_front"
MAIN_HAND = "bstart_hand"
STEM_FAR = "bstartfar"          # 反面 ②：两拳拉开
STEM_SHO = "bstartsho"          # 反面 ⑤：肩膀不动
STEM_FOOT = "bstartfoot"        # 反面 ⑥：脚滑
STEM_ASYM = "bstartasym"        # 反面 ⑦：碰拳不对称
STEM_NOSINK = "bstartnosink"    # 反面 ⑩：不沉不发力

# ---- ★ 两条机位基准：**从 `anim_battle_start` 现算**，不另抄一份数字 ----------
_S_NAME, _S_LOC, _S_TGT, _S_SCALE, _S_RES = B.VIEW_E05_SIDE
_F_NAME, _F_LOC, _F_TGT, _F_SCALE, _F_RES = B.VIEW_E05_FRONT

SIDE = {"res_x": _S_RES[0], "res_y": _S_RES[1], "ortho": _S_SCALE,
        "cam_z": _S_LOC[2], "center_y_mm": _S_TGT[1] * 1000.0}
FRONT = {"res_x": _F_RES[0], "res_y": _F_RES[1], "ortho": _F_SCALE,
         "cam_z": _F_LOC[2], "mid_col": _F_RES[0] / 2.0}

S_MMP = SIDE["ortho"] / float(SIDE["res_y"]) * 1000.0
S_FLOOR = (SIDE["ortho"] / 2.0 - SIDE["cam_z"]) / (SIDE["ortho"]
                                                   / float(SIDE["res_y"]))
F_MMP = FRONT["ortho"] / float(FRONT["res_y"]) * 1000.0
F_FLOOR = (FRONT["ortho"] / 2.0 - FRONT["cam_z"]) / (FRONT["ortho"]
                                                     / float(FRONT["res_y"]))


def s_row(z_mm):
    return S_FLOOR + z_mm / S_MMP


def s_col(y_mm):
    return SIDE["res_x"] / 2.0 + (y_mm - SIDE["center_y_mm"]) / S_MMP


def f_row(z_mm):
    return F_FLOOR + z_mm / F_MMP


def f_col(x_mm):
    return FRONT["mid_col"] + x_mm / F_MMP


# ---- ★ `Jacket_Hem` / `Jacket_Hem_Line` 世界包围盒（`probe_c11_belt.py` 实测：
#      `C11_BELT_ACTION=Battle_Start` → `BELT11_UNBOUND_COUNT 2`、`constant: true`、
#      两件均 `vgroups=0` / `parent=None` ⟹ **逐帧恒定**，与姿态无关）----------
#      ★ 实测 z ∈ [897.5, 926] mm ⟹ 落在**腰线**高度，与「脚带」（z ≤ 95 mm）和
#        「肩高带」（z ∈ [1250, 1420] mm）都**不相交**（下面 `hem_excluded_ok` 算得出）。
HEM_WORLD_MM = {
    "Jacket_Hem": ((-188.78, -121.94, 903.0), (188.78, 129.03, 926.0)),
    "Jacket_Hem_Line": ((-185.92, -119.96, 897.5), (185.92, 126.03, 901.5)),
}

# ---- 尺子带（**不许写行号**，行号现算）-------------------------------------
FOOT_Z_TOP_MM = float(os.environ.get("E05PX_FOOT_Z", "95.0"))
#   肩高带：站架肩峰 z ≈ 1313 mm、碰拳/耸肩时臂上抬 ⟹ 取 1250~1420 覆盖肩线
SHOULDER_Z_LO_MM = float(os.environ.get("E05PX_SHO_Z0", "1250.0"))
SHOULDER_Z_HI_MM = float(os.environ.get("E05PX_SHO_Z1", "1420.0"))

# ---- 阈值（**全部由实测导出**，见 `E05PX_REPORT`；铁律：不许为了变绿而放宽）----
MEASURE = os.environ.get("E05PX_MEASURE") == "1"
#   碰拳贴合：手层正面剪影**列包络内部**的空列数。0 = 两手连成一片（贴上了）。
INTERIOR_EMPTY_MAX_PX = float(os.environ.get("E05PX_GAP_MAX", "6.0"))
#   碰拳对称：横向（外沿到中线之差）与纵向（行重心之差）**各一条**，互不代替。
CLASH_SYM_COL_TOL_PX = float(os.environ.get("E05PX_SYM_COL", "8.0"))
CLASH_SYM_ROW_TOL_PX = float(os.environ.get("E05PX_SYM_ROW", "6.0"))
#   肩高带列跨度：SHRUG 相对站架**至少**外扩这么多 px。
SHOULDER_SPAN_MIN_PX = float(os.environ.get("E05PX_SHO_SPAN", "150.0"))
#   躯干下沉：碰拳帧剪影顶行相对站架**至少**低这么多 px。
SINK_MIN_PX = float(os.environ.get("E05PX_SINK_MIN", "45.0"))
FOOT_COL_TOL_PX = float(os.environ.get("E05PX_FOOT_COL", "3.0"))
FOOT_ROW_TOL_PX = float(os.environ.get("E05PX_FOOT_ROW", "3.0"))

START, SHRUG, WIND, CLASH = B.START, B.SHRUG, B.WIND, B.CLASH
END = B.END
ALL_FRAMES = sorted(set([START, 6, 12, 18, SHRUG, 28, WIND, 36, 40, 44, CLASH,
                         B.HOLD[1], 52, 56, B.STANCE, 68, 74, B.SETTLE, 88,
                         END]))


# =============================================================== 像素工具
def load(stem, frame, view):
    path = os.path.join(PRE, "%s_%s_f%04d.png" % (stem, view, frame))
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


def band_span(mask, r0, r1):
    sub = mask[r0:r1 + 1]
    cols = np.where(sub.any(axis=0))[0]
    if cols.size == 0:
        return None, None
    return int(cols.min()), int(cols.max())


def col_centroid(mask, r0, r1):
    sub = mask[r0:r1 + 1]
    total = sub.sum()
    if total <= 0:
        return None
    cols = np.arange(mask.shape[1])
    return float((cols * sub.sum(axis=0)).sum() / total)


def top_row(mask):
    rows = np.where(mask.any(axis=1))[0]
    return None if rows.size == 0 else int(rows.max())


def bottom_row(mask):
    rows = np.where(mask.any(axis=1))[0]
    return None if rows.size == 0 else int(rows.min())


def spread(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return float(max(vals) - min(vals))


def hem_screen_boxes():
    out = {}
    for name, (lo, hi) in HEM_WORLD_MM.items():
        out[name + "@side"] = (int(np.floor(s_row(lo[2]))) - 1,
                               int(np.ceil(s_row(hi[2]))) + 1,
                               int(np.floor(s_col(lo[1]))) - 1,
                               int(np.ceil(s_col(hi[1]))) + 1)
        out[name + "@front"] = (int(np.floor(f_row(lo[2]))) - 1,
                                int(np.ceil(f_row(hi[2]))) + 1,
                                int(np.floor(f_col(lo[0]))) - 1,
                                int(np.ceil(f_col(hi[0]))) + 1)
    return out


def strip_hem(mask, suffix):
    out = mask.copy()
    for name, (r0, r1, c0, c1) in hem_screen_boxes().items():
        if not name.endswith(suffix):
            continue
        rr0, rr1 = max(r0, 0), min(r1, mask.shape[0] - 1)
        cc0, cc1 = max(c0, 0), min(c1, mask.shape[1] - 1)
        if rr1 >= rr0 and cc1 >= cc0:
            out[rr0:rr1 + 1, cc0:cc1 + 1] = False
    return out


def silhouette(stem, frame, suffix, strip=False):
    pixels = load(stem, frame, suffix.lstrip("@"))
    if pixels is None:
        return None
    mask = mask_of(pixels)
    if strip:
        mask = strip_hem(mask, suffix)
    return mask


# ------------------------------------------------------- ★★★ 两团块几何
def hand_blobs(mask):
    """手层正面图：以**中线**把剪影切成左右两半，各量「伸出的多远 / 重心在哪个高度」。

    · 图像横轴 = 世界 X（**右 = +X = 角色左**），纵轴 = 世界 Z（**row 越大越高**）。
    · `interior_empty_px` = 剪影**列包络内部**的空列数。
      ★★★ **这是「贴合」的判据量**：两拳真的碰上时，两手剪影在列方向**连成一片**
      ⟹ 内部空列 = 0；`TP_FARCLASH` 把两拳各拉开 45 mm（合计 90 mm ≈ 45 px）
      ⟹ 内部空列 ≈ 45。★ 为什么不用「最宽空段」（第一版）：正反两侧都是 **0 或
      「找不到」**，把「贴着」与「重叠」混成一个哨兵值，读不出方向。
    · `sym_col_px` = 左右两半**外沿到中线距离**之差（横向对称）。
    · `sym_row_px` = 左右两半**像素行重心**之差（纵向对称 = 一拳高一拳低）。
      ★ 为什么必须分别量两轴：`TP_ASYMCLASH` 抬的是 **L 拳的 z**（100 mm ≈ 50 px）
      ⟹ 只改**行**不改列 —— 单量列对称的尺子对它**完全无感**（会造出假绿）。
    """
    mid = FRONT["mid_col"]
    filled = mask.any(axis=0)
    cols = np.where(filled)[0]
    if cols.size == 0:
        return None
    c0, c1 = int(cols.min()), int(cols.max())
    out = {"mid_col": float(mid), "ink_cols": [c0, c1],
           "ink_width_px": float(c1 - c0 + 1),
           "interior_empty_px": int((~filled[c0:c1 + 1]).sum())}
    left = cols[cols < mid]
    right = cols[cols >= mid]
    if left.size and right.size:
        out["outer_l_px"] = round(mid - float(left.min()), 2)
        out["outer_r_px"] = round(float(right.max()) - mid, 2)
        out["inner_l_px"] = round(mid - float(left.max()), 2)
        out["inner_r_px"] = round(float(right.min()) - mid, 2)
        out["sym_col_px"] = round(abs(out["outer_l_px"] - out["outer_r_px"]), 2)
        out["inner_sym_px"] = round(abs(out["inner_l_px"] - out["inner_r_px"]), 2)
        rows_np = np.arange(mask.shape[0], dtype=np.float64)[:, None]
        sub_l = mask[:, :int(mid)]
        sub_r = mask[:, int(mid):]
        tl, tr = float(sub_l.sum()), float(sub_r.sum())
        out["row_l"] = round(float((rows_np * sub_l).sum() / tl), 2) if tl > 0 \
            else None
        out["row_r"] = round(float((rows_np * sub_r).sum() / tr), 2) if tr > 0 \
            else None
        out["sym_row_px"] = (None if out["row_l"] is None or out["row_r"] is None
                             else round(abs(out["row_l"] - out["row_r"]), 2))
    else:
        out["sym_col_px"] = out["sym_row_px"] = None
    return out


# =============================================================== 主流程
def main():  # noqa: C901
    res = {}
    res["probe"] = "probe_battle_start_pixels"
    res["anim"] = "Battle_Start"
    res["measure_only"] = MEASURE
    res["views"] = {
        "side": {"res": list(_S_RES), "ortho_m": _S_SCALE,
                 "cam_z_m": _S_LOC[2], "center_y_mm": SIDE["center_y_mm"],
                 "mm_per_px": round(S_MMP, 7), "floor_row": round(S_FLOOR, 4),
                 "axis": "横轴 = 世界 Y（右 = +Y = 身后），纵轴 = 世界 Z"},
        "front": {"res": list(_F_RES), "ortho_m": _F_SCALE,
                  "cam_z_m": _F_LOC[2], "mm_per_px": round(F_MMP, 7),
                  "floor_row": round(F_FLOOR, 4),
                  "axis": "横轴 = 世界 X（右 = +X = 角色左），纵轴 = 世界 Z"},
    }
    res["frames"] = ALL_FRAMES
    res["hem_screen_boxes"] = {k: list(v) for k, v in
                               hem_screen_boxes().items()}

    landmark = {}
    path = os.path.join(PRE, "_e05_landmark.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            landmark = json.load(handle)
    res["landmark_loaded"] = bool(landmark)
    lm_rows = landmark.get("rows", {}) if landmark else {}

    # ---- ① ★★★ 碰拳贴合：正面·手层剪影「列包络内部空列数」 -----------------
    main_blob = {}
    for frame in (WIND, CLASH, B.HOLD[1]):
        mask = silhouette(MAIN_HAND, frame, "@front")
        main_blob[str(frame)] = None if mask is None else hand_blobs(mask)
    res["px_bstart_hand_blobs"] = main_blob
    row = main_blob.get(str(CLASH)) or {}
    empty_px = row.get("interior_empty_px")
    res["px_bstart_clash_gap_px"] = empty_px
    res["px_bstart_clash_gap_max_px"] = INTERIOR_EMPTY_MAX_PX
    res["px_bstart_clash_gap_ok"] = bool(
        empty_px is not None and empty_px <= INTERIOR_EMPTY_MAX_PX)

    far_blob = {}
    for frame in (WIND, CLASH):
        mask = silhouette(STEM_FAR + "hand", frame, "@front")
        far_blob[str(frame)] = None if mask is None else hand_blobs(mask)
    res["px_bstart_far_hand_blobs"] = far_blob
    far_gap = (far_blob.get(str(CLASH)) or {}).get("interior_empty_px")
    res["px_bstart_clash_far_gap_px"] = far_gap
    res["px_bstart_clash_gap_can_fail_ok"] = bool(
        far_gap is None or far_gap > INTERIOR_EMPTY_MAX_PX)

    # ---- ② ★★★ 碰拳对称：横向（列）与纵向（行）**各一条** -------------------
    sym_col = row.get("sym_col_px")
    sym_row = row.get("sym_row_px")
    res["px_bstart_clash_sym_col_px"] = sym_col
    res["px_bstart_clash_sym_row_px"] = sym_row
    res["px_bstart_clash_sym_tols_px"] = [CLASH_SYM_COL_TOL_PX,
                                          CLASH_SYM_ROW_TOL_PX]
    res["px_bstart_clash_sym_ok"] = bool(
        sym_col is not None and sym_row is not None
        and sym_col <= CLASH_SYM_COL_TOL_PX
        and sym_row <= CLASH_SYM_ROW_TOL_PX)
    asym_mask = silhouette(STEM_ASYM + "hand", CLASH, "@front")
    asym_row = None if asym_mask is None else hand_blobs(asym_mask)
    res["px_bstart_asym_hand_blob"] = asym_row
    asym_sym_col = (asym_row or {}).get("sym_col_px")
    asym_sym_row = (asym_row or {}).get("sym_row_px")
    res["px_bstart_clash_asym_sym_col_px"] = asym_sym_col
    res["px_bstart_clash_asym_sym_row_px"] = asym_sym_row
    res["px_bstart_clash_sym_can_fail_ok"] = bool(
        asym_sym_col is None or asym_sym_row is None
        or asym_sym_col > CLASH_SYM_COL_TOL_PX
        or asym_sym_row > CLASH_SYM_ROW_TOL_PX)
    res["px_bstart_clash_note"] = (
        "★★★ **本支命门**：正面·**手层**（只留 `Hand_Palm_*` / `Finger_*` / `Thumb_*`）。"
        "● **贴合** = 剪影**列包络内部空列数**：碰拳帧实测 **%s** px（≤ %.0f ⟹ 两手"
        "剪影连成一片）；反面 ② `TP_FARCLASH`（两拳各外撤 45 mm）实测 **%s** px。"
        "● **对称** = 横向 `sym_col` **%s** px（≤ %.0f）＋ 纵向 `sym_row` **%s** px"
        "（≤ %.0f）；反面 ⑦ `TP_ASYMCLASH`（L 拳抬 100 mm）实测 col **%s** / row **%s**"
        "（★ **只改行不改列** ⟹ 判据必须**两轴各一条**，否则该旋钮会惰性）。"
        % (empty_px, INTERIOR_EMPTY_MAX_PX, far_gap, sym_col,
           CLASH_SYM_COL_TOL_PX, sym_row, CLASH_SYM_ROW_TOL_PX, asym_sym_col,
           asym_sym_row))

    # ---- ③ ★★ 活动肩膀：正面·全身「肩高带」列跨度 -------------------------
    sho_r0 = int(np.floor(f_row(SHOULDER_Z_LO_MM)))
    sho_r1 = int(np.ceil(f_row(SHOULDER_Z_HI_MM)))
    res["px_bstart_shoulder_band_rows"] = [sho_r0, sho_r1]

    def shoulder_span(stem, frame):
        mask = silhouette(stem, frame, "@front")
        if mask is None:
            return None
        lo = max(sho_r0, 0)
        hi = min(sho_r1, FRONT["res_y"] - 1)
        a, b = band_span(mask, lo, hi)
        return None if a is None else float(b - a + 1)

    base_span = shoulder_span(MAIN_FRONT, START)
    shrug_span = shoulder_span(MAIN_FRONT, SHRUG)
    res["px_bstart_shoulder_span_px"] = {"START": base_span, "SHRUG": shrug_span}
    delta = (None if base_span is None or shrug_span is None
             else float(shrug_span - base_span))
    res["px_bstart_shoulder_span_delta_px"] = (None if delta is None
                                               else round(delta, 2))
    res["px_bstart_shoulder_span_min_px"] = SHOULDER_SPAN_MIN_PX
    res["px_bstart_shoulder_span_ok"] = bool(
        delta is not None and abs(delta) >= SHOULDER_SPAN_MIN_PX)
    nsho_base = shoulder_span(STEM_SHO, START)
    nsho_shrug = shoulder_span(STEM_SHO, SHRUG)
    nsho_delta = (None if nsho_base is None or nsho_shrug is None
                  else float(nsho_shrug - nsho_base))
    res["px_bstart_shoulder_nosho_span_px"] = {"START": nsho_base,
                                               "SHRUG": nsho_shrug}
    res["px_bstart_shoulder_nosho_delta_px"] = (
        None if nsho_delta is None else round(nsho_delta, 2))
    res["px_bstart_shoulder_span_can_fail_ok"] = bool(
        nsho_delta is None or abs(nsho_delta) < SHOULDER_SPAN_MIN_PX)

    # ---- ④ ★★ 躯干下沉：侧视剪影顶行 --------------------------------------
    tops = {}
    for frame in (START, WIND, CLASH):
        mask = silhouette(MAIN_SIDE, frame, "@side")
        tops[str(frame)] = None if mask is None else top_row(mask)
    res["px_bstart_top_rows_side"] = tops
    sink_px = (None if tops.get(str(START)) is None
               or tops.get(str(CLASH)) is None
               else float(tops[str(START)] - tops[str(CLASH)]))
    res["px_bstart_sink_px"] = None if sink_px is None else round(sink_px, 2)
    res["px_bstart_sink_min_px"] = SINK_MIN_PX
    res["px_bstart_body_sink_ok"] = bool(sink_px is not None
                                         and sink_px >= SINK_MIN_PX)
    ns_tops = {}
    for frame in (START, CLASH):
        mask = silhouette(STEM_NOSINK, frame, "@side")
        ns_tops[str(frame)] = None if mask is None else top_row(mask)
    res["px_bstart_nosink_top_rows"] = ns_tops
    ns_sink = (None if ns_tops.get(str(START)) is None
               or ns_tops.get(str(CLASH)) is None
               else float(ns_tops[str(START)] - ns_tops[str(CLASH)]))
    res["px_bstart_nosink_px"] = None if ns_sink is None else round(ns_sink, 2)
    res["px_bstart_body_sink_can_fail_ok"] = bool(
        ns_sink is None or ns_sink < SINK_MIN_PX)

    # 几何投影一致性（只登记数字，不给判据）
    geo_rows = {str(f): (lm_rows.get(str(f)) or {}).get("pelvis")
                for f in (START, WIND, CLASH)}
    res["px_bstart_pelvis_geom_rows"] = geo_rows

    # ---- ⑤ ★★ 脚锁：侧视脚带（底行 + 列心）不漂 ---------------------------
    foot_r0 = int(np.floor(s_row(0.0)))
    foot_r1 = int(np.ceil(s_row(FOOT_Z_TOP_MM)))
    res["px_bstart_foot_band_rows_side"] = [foot_r0, foot_r1]

    def foot_stats(stem, frames):
        bottoms, cents = [], []
        for frame in frames:
            mask = silhouette(stem, frame, "@side", strip=True)
            if mask is None:
                continue
            lo = max(foot_r0, 0)
            hi = min(foot_r1, SIDE["res_y"] - 1)
            rows = np.where(mask[lo:hi + 1].any(axis=1))[0]
            bottoms.append(None if rows.size == 0 else int(rows.min()) + lo)
            cents.append(col_centroid(mask, lo, hi))
        return bottoms, cents

    f_bots, f_cents = foot_stats(MAIN_SIDE, ALL_FRAMES)
    res["px_bstart_foot_bottoms_side"] = f_bots
    res["px_bstart_foot_colcents_side"] = [None if c is None else round(c, 2)
                                           for c in f_cents]
    row_spread = spread(f_bots)
    col_spread = spread(f_cents)
    res["px_bstart_foot_row_spread_px"] = (None if row_spread is None
                                           else round(row_spread, 2))
    res["px_bstart_foot_col_spread_px"] = (None if col_spread is None
                                           else round(col_spread, 2))
    res["px_bstart_foot_lock_ok"] = bool(
        row_spread is not None and col_spread is not None
        and row_spread <= FOOT_ROW_TOL_PX and col_spread <= FOOT_COL_TOL_PX)
    s_bots, s_cents = foot_stats(STEM_FOOT, ALL_FRAMES)
    s_row_spread = spread(s_bots)
    s_col_spread = spread(s_cents)
    res["px_bstart_foot_canfail_row_spread_px"] = (
        None if s_row_spread is None else round(s_row_spread, 2))
    res["px_bstart_foot_canfail_col_spread_px"] = (
        None if s_col_spread is None else round(s_col_spread, 2))
    res["px_bstart_foot_lock_can_fail_ok"] = bool(
        any(v is None for v in s_bots) or (s_row_spread or 0.0) > FOOT_ROW_TOL_PX
        or any(v is None for v in s_cents)
        or (s_col_spread or 0.0) > FOOT_COL_TOL_PX)

    # ---- ⑥ ★★ 衣摆：屏幕盒与尺子带不相交 + 剔除真的改变读数 ---------------
    boxes = hem_screen_boxes()
    bands = {
        "side@foot": ("@side", foot_r0, foot_r1),
        "front@shoulder": ("@front", sho_r0, sho_r1),
    }
    hits = []
    for name, (r0, r1, c0, c1) in boxes.items():
        for bname, (suffix, b0, b1) in bands.items():
            if not name.endswith(suffix):
                continue
            if not (r1 < b0 or r0 > b1):
                hits.append([name, bname, [r0, r1, c0, c1]])
    res["px_bstart_hem_band_hits"] = hits
    res["px_bstart_hem_excluded_ok"] = bool(not hits)
    raw = silhouette(MAIN_SIDE, CLASH, "@side", strip=False)
    cut = silhouette(MAIN_SIDE, CLASH, "@side", strip=True)
    changed = None
    if raw is not None and cut is not None:
        changed = int((raw & ~cut).sum())
    res["px_bstart_hem_stripped_px"] = changed
    # ★ 「剔除衣摆是空操作」也是一种失败 ⟹ 必须**真的改变了读数**（> 0 px）。
    res["px_bstart_hem_stripped_ok"] = bool(changed is not None and changed > 0)
    res["px_bstart_hem_note"] = (
        "★ `Jacket_Hem` / `Jacket_Hem_Line` 未蒙皮（`vgroups=0` / `parent=None`），"
        "世界 z ∈ [897.5, 926] mm 与**站架腰线**同高 ⟹ 复核它们与「脚带」"
        "（z ≤ %.0f mm）和「肩高带」（z ∈ [%.0f, %.0f] mm）的屏幕行是否相交。"
        "实测相交 **%d** 条。剔除衣摆实际改变 **%s** px（否则是空操作）。"
        % (FOOT_Z_TOP_MM, SHOULDER_Z_LO_MM, SHOULDER_Z_HI_MM, len(hits),
           changed))

    A.report("E05PX_REPORT", res)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E05PX_FAILURE " + traceback.format_exc())
