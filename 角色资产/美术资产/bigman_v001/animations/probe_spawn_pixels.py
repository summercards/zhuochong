"""probe_spawn_pixels —— E04 `Spawn` 入场 的**像素级**验收（只读 PNG + 一个 json，不改工程）。

与 `probe_e01/e02/e03_pixels.py` 的关系
---------------------------------------------------------------------
逐字照抄其像素工具（`load` / `mask_of` / 行号口径 / `band_span` / 列心 / `strip_hem` /
`spread` / `centroid`），但**尺子的几何轴与机位全部换口径**。

★★★ 本支与 E01 / E02 / E03 的**根本差别**（三条，写在最前面）
---------------------------------------------------------------------
(A) ★★★ **本支是 E 族第一支「有根位移」的动画**（E01~E03 全程锁踝不迈步）。
    ⟹ 像素尺子**不能**再假设「脚钉在世界点、躯干不动」：
      · **落地冲击**（本支命门）= 躯干**垂直下沉** ⟹ 垂直方向 = 世界 **Z**
        ⟹ **侧视与正面都可见**，但侧视不被「双脚左右分开」干扰 ⟹ 取 **侧视**。
      · **腾空**（脚真的离地）= Z 方向 ⟹ 同上，取 **侧视**。
      · **落地脚滑**（⑦ `FOOTSWAY` 骑骨盆）= 位移只落在 **Y / Z** ⟹ **侧视可见、
        正面不可见**（E02/E03 同一类陷阱）⟹ 取 **侧视**。
      · **双脚对称** = 世界 **X** ⟹ **正面可见、侧视不可见** ⟹ 取 **正面**。
    ⟹ 本支**新立两条机位基准**（`VIEW_E04_SIDE` / `VIEW_E04_FRONT`，由 `anim_spawn`
       现算），**不照抄** E01 / E02 / E03 的任何一条。

(B) ★★★ **「下沉」的像素尺子不拿几何投影当期望值（自指量）**。
    骨架级 `spawn_land_sink_mm` 是「站架骨盆 z − 落地骨盆 z」，若像素尺子也去
    比「渲染行 == 几何投影行」就是在量**同一个公式的两个输出**，永远自洽。
    ⟹ 本支像素尺子量的是**渲染剪影自身的位移**：
      · `px_spawn_head_drop_ok` = 「落地帧剪影**顶行**相对站架帧下移多少」（纯图像量）；
      · `px_spawn_airborne_ok`  = 「顶点帧剪影**底行**相对站架帧上抬多少」（纯图像量）。
    ★ 另**单独登记**几何投影（`_e04_landmark.json` 的骨盆行）与渲染顶行的**一致性**
      （不给判据，只给数字）—— 它是「渲染确实画出了几何说的那个位置」的读数。

(C) ★★ **`Jacket_Hem` / `Jacket_Hem_Line` 是未蒙皮的静止薄片**（`probe_c11_belt`
    实测 `vgroups=0` / `parent=None`）⟹ 世界包围盒**与姿态 / 根位移无关**（本支跳
    400 mm 它们**不动**）⟹ 必须**算出**它们与三条尺子的屏幕盒**不相交**，
    而不是「应该没事」。

判据清单
---------------------------------------------------------------------
  `px_spawn_head_drop_ok`               ★★★ 侧视：落地帧剪影顶行相对站架下移 ≥ 阈值
  `px_spawn_head_drop_can_fail_ok`      ★★★ 反面 ②：`TP_NOSINK` 重渲必须让上条红
  `px_spawn_airborne_ok`                ★★★ 侧视：顶点帧剪影底行相对站架上抬 ≥ 阈值
  `px_spawn_airborne_can_fail_ok`       ★★★ 反面 ⑤：`TP_GLUED` 重渲必须让上条红
  `px_spawn_foot_lock_ok`               ★★ 侧视：地面段脚带（底行 + 列心）不漂
  `px_spawn_foot_lock_can_fail_ok`      ★★ 反面 ⑦：`TP_FOOTSWAY` 重渲必须让上条红
  `px_spawn_feet_sym_ok`                ★★ 正面：地面段双脚关于中线镜像
  `px_spawn_feet_sym_can_fail_ok`       ★★ 反面 ⑨：`TP_FOOTASYM` 重渲必须让上条红
  `px_spawn_hem_excluded_ok`            ★★ 衣摆屏幕盒与四条尺子盒**不相交**（算得）
  `px_spawn_hem_stripped_ok`            ★★ 剔除衣摆**真的改变读数**（不是空操作）

用法
---------------------------------------------------------------------
    blender --background --factory-startup --python probe_spawn_pixels.py

前置（帧集合**逐帧相同**）：
  · 基线：`spawn_side_f*` / `spawn_front_f*`（`anim_spawn.py` 非 `SKIP_RENDER` 跑一次即产出）
          + `_e04_landmark.json`（同一次运行写出）；
  · 反面 ②：`SKIP_RENDER=1 E04_STEM_ONLY=1 E04_STEM=spawnsink    E04_TP_NOSINK=1`；
  · 反面 ⑤：`SKIP_RENDER=1 E04_STEM_ONLY=1 E04_STEM=spawnlift    E04_TP_GLUED=1`；
  · 反面 ⑦：`SKIP_RENDER=1 E04_STEM_ONLY=1 E04_STEM=spawnfoot    E04_TP_FOOTSWAY=1`；
  · 反面 ⑨：`SKIP_RENDER=1 E04_STEM_ONLY=1 E04_STEM=spawnasym    E04_TP_FOOTASYM=1`。
"""
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A        # noqa: E402
import anim_spawn as S      # noqa: E402

PRE = A.PREVIEW_DIR

MAIN_SIDE = "spawn_side"
MAIN_FRONT = "spawn_front"
STEM_SINK = "spawnsink"        # 反面 ②：落地不下沉
STEM_LIFT = "spawnlift"        # 反面 ⑤：空中段脚没离地
STEM_FOOT = "spawnfoot"        # 反面 ⑦：脚沿 Y/Z 滑（骑骨盆）
STEM_ASYM = "spawnasym"        # 反面 ⑨：L 脚沿 X 平移（只破坏正面对称）

# ---- ★ 两条机位基准：**从 `anim_spawn` 现算**，不另抄一份数字 ----------------
_S_NAME, _S_LOC, _S_TGT, _S_SCALE, _S_RES = S.VIEW_E04_SIDE
_F_NAME, _F_LOC, _F_TGT, _F_SCALE, _F_RES = S.VIEW_E04_FRONT

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


# ---- ★ `Jacket_Hem` / `Jacket_Hem_Line` 世界包围盒（`probe_c11_belt.py`
#      `C11_BELT_ACTION=Spawn` 实测；两件均 `vgroups=0` / `parent=None`
#      ⟹ **逐帧恒定**，与根位移无关 —— 本支跳 400 mm 它们仍在原处）
HEM_WORLD_MM = {
    "Jacket_Hem": ((-125.5, -121.94, 903.0), (125.5, 129.03, 926.0)),
    "Jacket_Hem_Line": ((-123.0, -119.96, 897.5), (123.0, 126.03, 901.5)),
}

# ---- 尺子的世界区间（**不许写行号**，行号现算）-----------------------------
FOOT_Z_TOP_MM = float(os.environ.get("E04PX_FOOT_Z", "95.0"))

# ---- 阈值（**全部由实测导出**，见 `E04PX_REPORT`；铁律：不许为了变绿而放宽）----
#   ★★ 2026-10-04 `HEAD_DROP_MIN_PX` 25.0 → 100.0。**这是收紧，不是放宽**：
#   旧值 25 px（≈68 mm）**没有判别力** —— 头顶行同时被**两件事**压低：
#     (a) 骨盆下沉 175 mm（本支的「重」，骨架级 `spawn_land_sink_ok` 把守）
#     (b) 落地躯干的**前屈**（pelvis 18° + spine 9+9 + chest 7，绕轴压头）
#   反面 ② `TP_NOSINK` 只清掉 (a)（`loc` 的 z 分量），**(b) 原样保留**，所以它的
#   落地头顶**照样**比站架低 **64 px**（≈175 mm 前屈的投影）⟹ 25 px 的阈值下
#   正反两读数**都过**，`can_fail` 必然失败（实测 `px_spawn_airborne_can_fail_ok`
#   那类假绿）。实测两读数：**主渲 129 px / 反面 64 px**，判别中点 ≈ 96 px。
#   取 **100 px** ⟹ 主渲余量 +29%、反面低 36%。★ 骨架级 `spawn_land_sink_mm`
#   仍是「下沉」的**精确**判据（它直接量骨盆 z）；像素 ① 是「渲染确实画出来了」
#   的**粗粒度佐证** —— 两者分工，不是重复。
HEAD_DROP_MIN_PX = float(os.environ.get("E04PX_DROP_MIN", "100.0"))
AIR_LIFT_MIN_PX = float(os.environ.get("E04PX_LIFT_MIN", "60.0"))
FOOT_COL_TOL_PX = float(os.environ.get("E04PX_FOOT_COL", "3.0"))
FOOT_ROW_TOL_PX = float(os.environ.get("E04PX_FOOT_ROW", "3.0"))
SYM_TOL_PX = float(os.environ.get("E04PX_SYM_TOL", "20.0"))

START, CROUCH, APEX = S.START, S.CROUCH, S.APEX
LAND, HOLD, END = S.LAND, S.HOLD, S.END
GROUND_FRAMES = sorted(set([START, CROUCH, LAND, HOLD[1], S.SETTLE, END]))


# =============================================================== 像素工具
#   ★ 逐字照抄 `probe_rage_pixels.py`（其又照抄 E01/E02 与 D16~D19）
def load(stem, frame, view):
    # ★ 文件名 = `<prefix>_<view.name>_f<NNNN>.png`（`render_pose_sheet` 的命名）。
    #   早期版本漏了 `_<view>` 一段，会去读不存在的 `spawn_side_f0000.png`
    #   ⟹ 全判据 None ⟹ 假红。**定义必须与产出对齐**。
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


def nan_guard(value):
    return 1e9 if value is None else value


def silhouette(stem, frame, suffix, strip=False):
    pixels = load(stem, frame, suffix.lstrip("@"))
    if pixels is None:
        return None
    mask = mask_of(pixels)
    if strip:
        mask = strip_hem(mask, suffix)
    return mask


# =============================================================== 主流程
def main():  # noqa: C901
    res = {}
    res["probe"] = "probe_spawn_pixels"
    res["anim"] = "Spawn"
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
    res["ground_frames"] = GROUND_FRAMES
    res["hem_screen_boxes"] = {k: list(v) for k, v in
                               hem_screen_boxes().items()}

    # ---- 几何投影（一致性数字，不给判据）---------------------------------
    landmark = {}
    path = os.path.join(PRE, "_e04_landmark.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as handle:
            landmark = json.load(handle)
    res["landmark_loaded"] = bool(landmark)
    lm_rows = landmark.get("rows", {}) if landmark else {}

    # ---- ① ★★★ 落地下沉：侧视剪影顶行下移 ---------------------------------
    #   ★★ 2026-10-04 修：`top_row` 走的是 **numpy 行索引**（`pixels` 由
    #   `reshape(height, width, 4)` 得到，row 0 = **图像底部** ⟹ `rows.max()`
    #   = **最高处**）。落地时头更低 ⟹ `tops[LAND] < tops[START]`，差值**天然为负**。
    #   旧版写成 `tops[LAND] - tops[START]` 且要求 `>= +阈值` ⟹ **方向反了、永远为假**。
    #   改成 `tops[START] - tops[LAND]`（正数 = 下沉了多少 px）。
    tops = {}
    for frame in (START, APEX, LAND):
        mask = silhouette(MAIN_SIDE, frame, "@side")
        tops[str(frame)] = None if mask is None else top_row(mask)
    res["px_spawn_top_rows_side"] = tops
    drop_px = (None if tops.get(str(START)) is None or tops.get(str(LAND)) is None
               else float(tops[str(START)] - tops[str(LAND)]))
    res["px_spawn_head_drop_px"] = None if drop_px is None else round(drop_px, 2)
    res["px_spawn_head_drop_ok"] = bool(drop_px is not None
                                        and drop_px >= HEAD_DROP_MIN_PX)

    # 几何投影对照（骨盆行）—— 只登记数字
    geo_rows = {}
    for frame in (START, APEX, LAND):
        row = lm_rows.get(str(frame), {})
        geo_rows[str(frame)] = row.get("pelvis")
    res["px_spawn_pelvis_geom_rows"] = geo_rows
    if (tops.get(str(LAND)) is not None and geo_rows.get(str(LAND)) is not None
            and top_row is not None):
        res["px_spawn_toprow_vs_pelvis_px"] = round(
            float(tops[str(LAND)] - geo_rows[str(LAND)][0]), 2)

    sink_tops = {}
    for frame in (START, LAND):
        mask = silhouette(STEM_SINK, frame, "@side")
        sink_tops[str(frame)] = None if mask is None else top_row(mask)
    res["px_spawn_sink_stem_top_rows"] = sink_tops
    sink_drop = (None if sink_tops.get(str(START)) is None
                 or sink_tops.get(str(LAND)) is None
                 else float(sink_tops[str(START)] - sink_tops[str(LAND)]))
    res["px_spawn_head_drop_canfail_px"] = (None if sink_drop is None
                                            else round(sink_drop, 2))
    res["px_spawn_head_drop_can_fail_ok"] = bool(
        sink_drop is not None and sink_drop < HEAD_DROP_MIN_PX)

    # ---- ② ★★★ 腾空：侧视剪影底行上抬 -------------------------------------
    bots = {}
    for frame in (START, APEX, LAND):
        mask = silhouette(MAIN_SIDE, frame, "@side")
        bots[str(frame)] = None if mask is None else bottom_row(mask)
    res["px_spawn_bottom_rows_side"] = bots
    lift_px = (None if bots.get(str(START)) is None
               or bots.get(str(APEX)) is None
               else float(bots[str(APEX)] - bots[str(START)]))
    res["px_spawn_air_lift_px"] = None if lift_px is None else round(lift_px, 2)
    res["px_spawn_airborne_ok"] = bool(lift_px is not None
                                       and lift_px >= AIR_LIFT_MIN_PX)

    lift2 = {}
    for frame in (START, APEX):
        mask = silhouette(STEM_LIFT, frame, "@side")
        lift2[str(frame)] = None if mask is None else bottom_row(mask)
    res["px_spawn_lift_stem_bottom_rows"] = lift2
    lift_stem = (None if lift2.get(str(START)) is None
                 or lift2.get(str(APEX)) is None
                 else float(lift2[str(APEX)] - lift2[str(START)]))
    res["px_spawn_air_lift_canfail_px"] = (None if lift_stem is None
                                           else round(lift_stem, 2))
    res["px_spawn_airborne_can_fail_ok"] = bool(
        lift_stem is not None and lift_stem < AIR_LIFT_MIN_PX)

    # ---- ③ ★★ 地面段脚锁：侧视脚带（底行 + 列心）不漂 ----------------------
    foot_r0 = int(np.floor(s_row(0.0)))
    foot_r1 = int(np.ceil(s_row(FOOT_Z_TOP_MM)))
    res["px_spawn_foot_band_rows_side"] = [foot_r0, foot_r1]

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

    f_bots, f_cents = foot_stats(MAIN_SIDE, GROUND_FRAMES)
    res["px_spawn_foot_bottoms_side"] = f_bots
    res["px_spawn_foot_colcents_side"] = [None if c is None else round(c, 2)
                                          for c in f_cents]
    row_spread = spread(f_bots)
    col_spread = spread(f_cents)
    res["px_spawn_foot_row_spread_px"] = (None if row_spread is None
                                          else round(row_spread, 2))
    res["px_spawn_foot_col_spread_px"] = (None if col_spread is None
                                          else round(col_spread, 2))
    res["px_spawn_foot_lock_ok"] = bool(
        row_spread is not None and col_spread is not None
        and row_spread <= FOOT_ROW_TOL_PX and col_spread <= FOOT_COL_TOL_PX)

    s_bots, s_cents = foot_stats(STEM_FOOT, GROUND_FRAMES)
    s_row_spread = spread(s_bots)
    s_col_spread = spread(s_cents)
    res["px_spawn_foot_canfail_row_spread_px"] = (
        None if s_row_spread is None else round(s_row_spread, 2))
    res["px_spawn_foot_canfail_col_spread_px"] = (
        None if s_col_spread is None else round(s_col_spread, 2))
    visible = (any(v is None for v in s_bots) or (s_row_spread or 0.0) > FOOT_ROW_TOL_PX
               or any(v is None for v in s_cents) or (s_col_spread or 0.0) > FOOT_COL_TOL_PX)
    res["px_spawn_foot_lock_can_fail_ok"] = bool(visible)

    # ---- ④ ★★ 正面双脚对称 ------------------------------------------------
    ffoot_r0 = int(np.floor(f_row(0.0)))
    ffoot_r1 = int(np.ceil(f_row(FOOT_Z_TOP_MM)))
    res["px_spawn_foot_band_rows_front"] = [ffoot_r0, ffoot_r1]

    def sym_rows(stem, frames):
        out = {}
        for frame in frames:
            mask = silhouette(stem, frame, "@front", strip=True)
            if mask is None:
                continue
            lo = max(ffoot_r0, 0)
            hi = min(ffoot_r1, FRONT["res_y"] - 1)
            left = np.where(mask[lo:hi + 1, :int(FRONT["mid_col"])].any(axis=0))[0]
            right_rel = np.where(mask[lo:hi + 1, int(FRONT["mid_col"]):].any(axis=0))[0]
            if left.size == 0 or right_rel.size == 0:
                out[str(frame)] = None
                continue
            right = right_rel + int(FRONT["mid_col"])
            mirror_lo = 2.0 * FRONT["mid_col"] - float(right.max())
            mirror_hi = 2.0 * FRONT["mid_col"] - float(right.min())
            out[str(frame)] = round(max(abs(mirror_lo - float(left.min())),
                                        abs(mirror_hi - float(left.max()))), 2)
        return out

    sym = sym_rows(MAIN_FRONT, GROUND_FRAMES)
    res["px_spawn_feet_sym_px"] = sym
    sym_vals = [v for v in sym.values() if v is not None]
    worst_sym = max(sym_vals) if sym_vals else None
    res["px_spawn_feet_sym_worst_px"] = worst_sym
    res["px_spawn_feet_sym_ok"] = bool(
        worst_sym is not None and len(sym_vals) == len(GROUND_FRAMES)
        and worst_sym <= SYM_TOL_PX)

    asym = sym_rows(STEM_ASYM, GROUND_FRAMES)
    res["px_spawn_feet_sym_canfail_px"] = asym
    asym_vals = [v for v in asym.values() if v is not None]
    worst_asym = max(asym_vals) if asym_vals else None
    res["px_spawn_feet_sym_canfail_worst_px"] = worst_asym
    res["px_spawn_feet_sym_can_fail_ok"] = bool(
        worst_asym is not None and worst_asym > SYM_TOL_PX)

    # ---- ⑤ ★★ 衣摆：与尺子盒不相交 + 剔除真的改变读数 ---------------------
    boxes = hem_screen_boxes()
    #   ★★ 2026-10-04 修：`air_side` 的世界区间 200~1600 mm → **0~700 mm**。
    #   旧区间把**整个躯干**都圈了进去 ⟹ 静止薄片 `Jacket_Hem`（z=903~926 mm）
    #   必然落在盒内 ⟹ `px_spawn_hem_excluded_ok` **恒假**（与动作无关，是尺子
    #   自己画错了）。语义上这把尺子量的是「**脚**离地后可能到达的区域」：
    #   实测空中段鞋底峰值 **547.6 mm**，取 0~700 mm 留 150 mm 余量。衣摆
    #   897~926 mm 在区间**外** ⟹ 不相交可判。★ 这是**修正一个几何上不自洽的
    #   尺子**，不是给判据开口子：`foot_side`（0~95 mm）仍在，`air_side` ⊃ 它。
    rulers = {
        "head_side": (int(np.floor(s_row(1400.0))), int(np.ceil(s_row(1900.0))),
                      int(np.floor(s_col(-400.0))), int(np.ceil(s_col(400.0)))),
        "air_side": (int(np.floor(s_row(0.0))), int(np.ceil(s_row(700.0))),
                     int(np.floor(s_col(-400.0))), int(np.ceil(s_col(400.0)))),
        "foot_side": (max(foot_r0, 0), min(foot_r1, SIDE["res_y"] - 1),
                      int(np.floor(s_col(-400.0))), int(np.ceil(s_col(400.0)))),
        "foot_front": (max(ffoot_r0, 0), min(ffoot_r1, FRONT["res_y"] - 1),
                       int(np.floor(f_col(-400.0))), int(np.ceil(f_col(400.0)))),
    }
    overlap = {}
    for key, (r0, r1, c0, c1) in rulers.items():
        suffix = "@front" if key.endswith("front") else "@side"
        for name, (hr0, hr1, hc0, hc1) in boxes.items():
            if not name.endswith(suffix):
                continue
            hit = (min(r1, hr1) >= max(r0, hr0)
                   and min(c1, hc1) >= max(c0, hc0))
            if hit:
                overlap[name + " vs " + key] = True
    res["px_spawn_hem_rulers"] = {k: list(v) for k, v in rulers.items()}
    res["px_spawn_hem_overlaps"] = overlap
    res["px_spawn_hem_excluded_ok"] = not overlap

    strip_delta = 0
    for frame in GROUND_FRAMES + [APEX]:
        pixels = load(MAIN_SIDE, frame, "side")
        if pixels is None:
            continue
        raw = mask_of(pixels)
        cut = strip_hem(raw, "@side")
        strip_delta += int(raw.sum() - cut.sum())
    res["px_spawn_hem_strip_delta_px"] = strip_delta
    res["px_spawn_hem_stripped_ok"] = bool(strip_delta > 0)

    failed = sorted(k for k, v in res.items()
                    if k.startswith("px_") and k.endswith("_ok") and v is not True)
    res["failed"] = failed
    A.report("E04PX_REPORT", res)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E04PX_FAILURE " + traceback.format_exc())
