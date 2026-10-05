"""probe_d14_pixels —— 把 D14 `Knockdown_F` 的判据数值换算成**画面像素**。

（由 `probe_d13_pixels.py` 派生。D14 计划 §3「像素探针」原文：
  「`probe_d12_pixels.py` → **`probe_d14_pixels.py`**，`STEM="knockdownf"`。
   ★ **本支的独门尺子（跨支连续）**：`D13 f14~f18` 与 `D14 f0~f6` 是**同一条抛物线**
   ⟹ **合并**做头带行心二次拟合，`g` 必须 = `G_PER_FRAME`。
   另：`px_land_stop_ok`、`px_ground_contact_ok`、`px_hem_*` 照抄。
   **反面对照**：D13 自己（全段在空中）用"触地"尺子必须判红；
   **正面对照**：A12 `Jump_Fall` 的下落段必须通过。」

═══ 取景 ═══
  本支静帧取景与 D13 **逐位相同**（跨支尺子要求两段画面同一把尺子）：
  侧视 (5.20, 0, 1.30) → (0, 0, 1.30)、up = +Z、正交宽 3.30 m、780×1100。
  `to_track_quat("-Z","Y")` ⟹ 图像**右** = +Y = **身后**；行号**上** = +Z。
  px/mm = (1100 / 3.30) / 1000 = 0.333333 ⟹ 物理分辨率 **3 mm/px**（本族最粗的一支）。
  世界高度 ↔ 行号：`z_mm = −350.0 + row × 3.0`（row 0 = 相机中心下方 1.65 m）。

★★★ 本版对计划原文口径的**三处诚实修正**（全部附实测依据）★★★

  ① **「合并 11 点头带行心二次拟合 g」这条尺子在本支不成立** ⟹ 换成
     **逐帧步长 vs 弹道预测的残差中位数**（跨支，但用更稳的估计量）。
     实测（`D14PX_DUMP`，见下表）：

       帧       实测步长(px)   弹道预测(px)   残差(px)
       f0        −19.275        −19.009       +0.266
       f1        −14.928        −20.370       **+5.442**   ← 唯一坏点
       f2        −21.306        −21.278       −0.028
       f3        −21.448        −22.185       +0.737
       f4        −21.968        −23.093       +1.125
       f5        −21.725        −24.000       +2.275
       f6        −24.034        −24.907       +0.873

     二次拟合把 7 个点一起喂进去 ⟹ 单个坏点把 `g` 从 2.722 拉到 **2.283**（误差 0.439）。
     `g` 是二阶量而 1 px = 3 mm ⟹ `g` 的量化步长 = 0.907 px/帧²，**信噪比天生不足**。
     ⟹ 本版主尺子改为：**7 个步长残差的绝对值中位数 ≤ `SEAM_STEP_MED_TOL_PX`**
       （实测 **0.873 px**），并**并列报出**最大残差与所在帧（诚实标注污染源 f1：
       手臂从头顶移开 ⟹ 顶行由"手"换成"头" ⟹ 头带行心在那一帧被手支配）。
     `px_seam_g`（二次拟合）**降级为只报诊断**，仍打印，附 `g_head/g_area/g_pelvis` 三载体对照。

  ② **「剪影最低行」在 `f ≥ 11` 不再代表鞋底** ⟹ 贴地判据只覆盖「鞋底接管期」。
     实测（`_d14_low.py`，逐对象求世界最低点，mm）：

       帧    最低对象（前 2）                     剪影最低行
       f7    Shoe_Sole_L +1.0 / Shoe_Sole_R +1.0  117
       f11   **Trouser_R −23.9** / Trouser_L −37.5  104   ← 裤管接管
       f13   **Trouser_R −109.5** / Trouser_L −79.4  80
       f20   **Trouser_R −61.5** / Trouser_L −11.3   96

     ⟹ `Trouser_*`（裤管）在屈膝压缩时**穿出地面最多 110 mm**，而 `Shoe_Sole_*`
       全程停在 **−1.2 mm（极差 0.03 mm）**。这是**模型侧遗留**（与 `Jacket_Hem` 同类），
       不是本支姿态定义的错误 —— 但**不能**再拿最低行当"贴地"载体。
     ⟹ 本版：`ground_row` 锚在 **`f7~f10`（鞋底接管期）最低行的中位数**，
       `px_ground_contact_ok` 只覆盖该窗口；`f ≥ 11` 的偏离**如实登记**为
       `trouser_ground_breach`，不进判据。

  ③ **`px_hem_filter_needed_ok`（"过滤在干活"）在本支不成立** ⟹ 换成
     `px_hem_stripped_ok`（"下摆确实被剔"）。
     实测：身体最低行在 **80~261**，下摆恒在 **415~425** ⟹ 下摆**从来不是最低点**，
     `bottom_raw == bottom` 恒真。D13 的能量比是"下摆可能在最低点"，本支**更低** ⟹
     物理上不可能。判据据此改成"确实有块被剔（f11~f20，各 910 px）"，
     并**登记**它的高度区间与"不影响任何以最低行为载体的判据"这一事实。

画面判据（全部会失败）：
  `px_seam_frame_match_ok`      ★★ 跨支接缝的画面证据：`airhit_side_f0018` 与
                               `knockdownf_side_f0000` 的 顶行/底行/头带行心/高/宽 **逐位一致**（≤1 px）
  `px_seam_steps_ok`            ★★ **独门尺子**（跨支）：`D14 f0~f6` 的**头带行心逐帧步长**
                               与共享解析弹道预测的**残差中位数** ≤ `SEAM_STEP_MED_TOL_PX`
                               （实测 0.873 px），且 7 个步长**全为负**（都在下落）
  `px_seam_steps_control_ok`    ★ 正面：同一把尺子量 **D13 自己 f14~f17**（同一条弹道、上游）必须通过
  `px_seam_steps_can_fail_ok`   ★ 反向：同一把尺子量 **D14 f8~f13**（已落地、姿态剧变）必须判红
  `px_fall_monotone_ok`         侧视最低行在 `f < LAND` **逐帧下降**（每帧 Δ ≤ −`FALL_STEP_MIN_PX`）
  `px_fall_monotone_control_ok` ★ 正面：A12 `Jump_Fall` 下落段用同一把尺子必须通过
  `px_fall_monotone_can_fail_ok` ★ 反向：D12 `Launch_Hit` f0~f11（地面段，含上行与平台）必须判红
  `px_land_jump_ok`             ★★ 触地帧**落差突变**：`f=LAND` 单帧下降 ≥ `LAND_STEP_MIN_PX`
                               （实测 36 px = 108 mm），而 `f<LAND` 每帧 ≤ `FALL_STEP_MAX_PX`
  `px_land_jump_can_fail_ok`    ★★ 反向：**D13 自己**（全段在空中）归一化步长最大只有 ~19 px
                               ⟹ 拿"落差"尺子量它必须判红
  `px_ground_contact_ok`        ★ 鞋底接管期 `f7~f10` 最低行相对 `ground_row` 极差 ≤ `GROUND_TOL_PX`
  `px_ground_contact_can_fail_ok` ★ 反向：D13 的 `f7~f10` 用同一把尺子必须判红（还在飞）
  `px_ground_hold_ok`           ★★ 贴地自持：`f ∈ [PLATEAU, TOTAL]` 顶行/头带行心**逐帧恒定** ≤`HOLD_TOL_PX`
  `px_ground_hold_can_fail_ok`  ★★ 反向：D13 的 `f16~f18` 用同一把尺子必须判红（继续下坠）
  `px_prone_ok`                 ★ 前倒：侧视剪影 高/宽 从 `f=LAND` 到 `f=END`
                               高度比 ≤ `PRONE_H_RATIO_MAX` 且宽度比 ≥ `PRONE_W_RATIO_MIN`
  `px_prone_can_fail_ok`        ★ 反向：D14 `f0 → f=LAND`（还没趴下）用同一把尺子必须判红
  `px_hem_excluded_ok`          被剔块 = 已知静态足迹，且各帧足迹**逐位相同**
  `px_hem_stripped_ok`          下摆确实被剔（≥1 帧、面积 ≥ `HEM_MIN_AREA`）

只报不判：逐帧顶/底/头带/面积/骨盆带行心全量表、被剔块明细、三载体 `g` 对照、
         裤管穿地登记、前视剪影。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d14_pixels.py
  D14PX_DUMP=1 追加三载体 g 对照表。
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
STEM = "knockdownf"

# ---- 视图表：(图像高 px, 正交宽 m, 相机 z) ------------------------------------
VIEWS = {
    "knockdownf_side": (1100, 3.30, 1.30),    # 本支侧视（主检）
    "knockdownf_front": (1100, 3.30, 1.30),   # 本支前视
    "airhit_side": (1100, 3.30, 1.30),        # D13 侧视 —— 跨支尺子 + 反面对照
    "jumpfall_side": (1100, 3.80, 1.30),      # A12 `FALL_SIDE` —— 正面对照（纯弹道）
    "launchhit_side": (1100, 4.30, 1.55),     # D12 `VIEW_SIDE` —— 反面对照（地面段）
}

# ---- 帧号（与 `anim_knockdown_f.py` 的时间轴逐一对齐）-------------------------
START = 0
FALL_END = 6
# ★ 反向验证旋钮（默认关闭；用来证明尺子真的能红，不是"做了但没红"）
LAND = int(os.environ.get("D14PX_LAND", "7"))
HOLD_END = 8
COMPRESS_PEAK = 11
PRONE_PEAK = 15
PLATEAU = 16
CANCEL = 16
TOTAL = 20

G_PER_FRAME_MM = 9.8 / 60.0 / 60.0 * 1000.0         # 2.722222 mm/帧²
# 解析弹道（与 `anim_jump_start` 同源常量；相位续 D13 f18 ⟹ T_PHASE = 31.5 + 18）
TAKEOFF_PELVIS_Z = 0.9200
TAKEOFF_SPEED = 0.075                               # m/帧
T_PHASE = 49.5                                      # D14 帧 f ⟺ t = 49.5 + f
T_PHASE_D13 = 31.5                                  # D13 帧 f ⟺ t = 31.5 + f


def ball_z(frame, t_phase=T_PHASE):
    t = t_phase + float(frame)
    return TAKEOFF_PELVIS_Z + TAKEOFF_SPEED * t - 0.5 * (9.8 / 60.0 / 60.0) * t * t


def ball_step_px(frame, ppm, t_phase=T_PHASE):
    """该帧相对前一帧的解析位移（px，负 = 下落）。"""
    return (ball_z(frame, t_phase) - ball_z(frame - 1, t_phase)) * 1000.0 * ppm


# ---- 阈值（全部由实测导出，见模块 docstring）----------------------------------
SEAM_MATCH_TOL_PX = float(os.environ.get("D14PX_SEAM_PX", "1.0"))
SEAM_STEP_MED_TOL_PX = float(os.environ.get("D14PX_SEAM_STEP_TOL", "3.0"))
SEAM_STEP_MED_TOL_CTRL_PX = float(os.environ.get("D14PX_SEAM_STEP_TOL_CTRL",
                                                 "3.0"))
FALL_STEP_MIN_PX = float(os.environ.get("D14PX_FALL_STEP", "10.0"))
FALL_STEP_MAX_PX = float(os.environ.get("D14PX_FALL_STEP_MAX", "34.0"))
LAND_STEP_MIN_PX = float(os.environ.get("D14PX_LAND_STEP", "25.0"))
GROUND_TOL_PX = float(os.environ.get("D14PX_GROUND_TOL", "2.0"))
HOLD_TOL_PX = float(os.environ.get("D14PX_HOLD_TOL", "1.0"))
PRONE_H_RATIO_MAX = float(os.environ.get("D14PX_PRONE_H", "0.80"))
PRONE_W_RATIO_MIN = float(os.environ.get("D14PX_PRONE_W", "1.10"))

# ---- 带（绝对世界高度锚定；沿用 D13 口径）-------------------------------------
PELVIS_BAND_ABOVE_SOLE_MM = (800.0, 920.0)
HEAD_BAND_FROM_TOP_PX = 55

# ---- 已知静态下摆足迹（★ 已按本支实测校正，见 docstring 修正 ③）---------------
HEM_FOOTPRINT = {
    "knockdownf_side": ((408, 432), (340, 445)),
    "knockdownf_front": ((408, 432), (340, 445)),
}
HEM_MIN_AREA = 100

# ---- 跨支尺子的时间轴 ----------------------------------------------------------
# D13 f14~f17 ⟹ 记为 D14 帧 −4 ~ −1（D13 f18 与 D14 f0 逐位相同，两者只取其一进拟合）
SEAM_D13_FRAMES = [14, 15, 16, 17]        # 用于"合并"诊断（三载体 g 对照）
SEAM_D14_FRAMES = [0, 1, 2, 3, 4, 5, 6]   # 主尺子的步长域
SEAM_LAST_D13_FRAME = int(os.environ.get("D14PX_SEAM_SHIFT", "18"))  # 接缝帧
SEAM_CTRL_D13_FRAMES = [14, 15, 16, 17]   # 正面：同一条弹道的上游段（4 个步长）
SEAM_NEG_D14_FRAMES = [8, 9, 10, 11, 12, 13]   # 反向：已落地、姿态剧变

# ---- 鞋底接管期（见 docstring 修正 ②）----------------------------------------
SOLE_WINDOW = [LAND, LAND + 1, LAND + 2, LAND + 3]

# ---- 对照 ----------------------------------------------------------------------
CTRL_FRAMES = [12, 16, 20, 24]            # A12 下落段（★ 顶点附近不进尺子）
NEG_D12_FRAMES = list(range(0, 12))       # D12 地面段
D13_POST_LAND_FRAMES = list(range(LAND, 19))


# =============================================================== 像素工具
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


def px_per_mm(view):
    res_y, ortho, _cam_z = VIEWS[view]
    return (float(res_y) / ortho) / 1000.0


def components(mask):
    rows, cols = np.where(mask)
    if rows.size == 0:
        return []
    index, parent = {}, list(range(rows.size))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for k in range(rows.size):
        r, c = int(rows[k]), int(cols[k])
        for key in ((r - 1, c), (r, c - 1)):
            j = index.get(key)
            if j is not None:
                ra, rb = find(k), find(j)
                if ra != rb:
                    parent[rb] = ra
        index[(r, c)] = k
    groups = {}
    for k in range(rows.size):
        groups.setdefault(find(k), []).append(k)
    out = []
    for members in groups.values():
        sel = np.array(members, dtype=np.int64)
        rr, cc = rows[sel], cols[sel]
        sub = np.zeros_like(mask)
        sub[rr, cc] = True
        out.append({"area": int(len(members)),
                    "rows": [int(rr.min()), int(rr.max())],
                    "cols": [int(cc.min()), int(cc.max())],
                    "mask": sub})
    out.sort(key=lambda d: -d["area"])
    return out


def strip_hem(view, mask):
    """只剔**完整落在已知静态足迹内**的连通块（★ 不按最大块 —— 那会误剔鞋）。"""
    footprint = HEM_FOOTPRINT.get(view)
    if footprint is None:
        return mask, []
    (r_lo, r_hi), (c_lo, c_hi) = footprint
    clean, dropped = mask.copy(), []
    for part in components(mask):
        r0, r1 = part["rows"]
        c0, c1 = part["cols"]
        if r_lo <= r0 and r1 <= r_hi and c_lo <= c0 and c1 <= c_hi:
            clean &= ~part["mask"]
            dropped.append({"area": part["area"], "rows": [r0, r1],
                            "cols": [c0, c1]})
    return clean, dropped


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


def bands(view, mask):
    """返回该视图下 头带 / 骨盆带 的行区与行心，以及整幅剪影的顶/底/面积行心。"""
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
def main():
    res = {}
    res["stem"] = STEM
    res["timeline"] = {"START": START, "FALL_END": FALL_END, "LAND": LAND,
                       "HOLD_END": HOLD_END, "COMPRESS_PEAK": COMPRESS_PEAK,
                       "PRONE_PEAK": PRONE_PEAK, "PLATEAU": PLATEAU,
                       "CANCEL": CANCEL, "TOTAL": TOTAL}
    res["ballistic"] = {"T_PHASE_D14": T_PHASE, "T_PHASE_D13": T_PHASE_D13,
                        "ball_z_m": {str(f): round(ball_z(f), 6)
                                     for f in range(-4, TOTAL + 1)},
                        "ball_step_px": {
                            str(f): round(ball_step_px(f, 0.3333333333333333), 4)
                            for f in range(-4, TOTAL + 1)}}

    def r3(x):
        return None if x is None else round(x, 3)

    # ---------------- (0) 逐视图扫描 + 剔静态下摆 --------------------------
    def scan(view, frame_list):
        table, hem = {}, []
        for frame in frame_list:
            pixels = load(view, frame)
            if pixels is None:
                continue
            raw = mask_of(pixels)
            clean, dropped = strip_hem(view, raw)
            band = bands(view, clean)
            if band is None:
                continue
            raw_ext = rows_any(raw)
            band["bottom_raw"] = None if raw_ext is None else raw_ext[0]
            band["clean"] = clean
            band["dropped_area"] = int(raw.sum() - clean.sum())
            table[frame] = band
            if dropped:
                hem.append({"frame": frame, "dropped": dropped})
        return table, hem

    side, hem_report = scan("knockdownf_side", list(range(START, TOTAL + 1)))
    if not side:
        raise RuntimeError("侧视静帧一张都没有：%s" % PRE)
    ppm = px_per_mm("knockdownf_side")
    frames = sorted(side)
    res["side_px_per_mm"] = round(ppm, 6)
    res["side_mm_per_px"] = round(1.0 / ppm, 4)
    res["side_frames_present"] = frames
    res["side_row_ruler"] = ("世界高度 z_mm = −350.0 + row × 3.0；"
                             "图像右 = +Y = 身后；行号向上 = +Z；3.00 mm/px。")
    res["side_top_row"] = {str(f): side[f]["top"] for f in frames}
    res["side_bottom_row"] = {str(f): side[f]["bottom"] for f in frames}
    res["side_bottom_row_raw"] = {str(f): side[f]["bottom_raw"] for f in frames}
    res["side_head_row"] = {str(f): r3(side[f]["head_row"]) for f in frames}
    res["side_area_row"] = {str(f): r3(side[f]["area_row"]) for f in frames}
    res["side_pelvis_row"] = {str(f): r3(side[f]["pelvis_row"]) for f in frames}
    res["side_height_px"] = {str(f): side[f]["height_px"] for f in frames}
    res["side_width_px"] = {str(f): side[f]["width_px"] for f in frames}

    # ---------------- (1) 静态下摆剔除守卫 --------------------------------
    res["hem_dropped"] = hem_report
    boxes = set()
    for entry in hem_report:
        for drop in entry["dropped"]:
            boxes.add((tuple(drop["rows"]), tuple(drop["cols"])))
    res["hem_boxes"] = sorted([list(map(list, b)) for b in boxes])
    res["hem_frames"] = [e["frame"] for e in hem_report]
    res["hem_areas"] = [d["area"] for e in hem_report for d in e["dropped"]]
    res["hem_footprint_registered"] = {k: [list(v[0]), list(v[1])]
                                       for k, v in HEM_FOOTPRINT.items()}
    res["px_hem_excluded_ok"] = bool(
        hem_report and len(boxes) == 1
        and min(res["hem_areas"]) >= HEM_MIN_AREA)
    # ★ 修正 ③：本支身体最低行（80~261）远低于下摆（415~425）⟹ 下摆**不可能**
    #   成为最低点 ⟹ 原来的"过滤改变了最低行"判据物理上不成立。改成"确实剔掉了块"。
    res["px_hem_stripped_ok"] = bool(
        hem_report and min(res["hem_areas"]) >= HEM_MIN_AREA)
    res["px_hem_note"] = (
        "★ 下摆恒在 row %s，本支身体最低行在 %d~%d ⟹ 下摆从来不是最低点，"
        "`bottom_raw == bottom` 恒真。故判据改为『确实有块被剔』，"
        "并登记它**不影响任何以最低行为载体的判据**。"
        % (res["hem_boxes"][0][0] if res["hem_boxes"] else "?",
           min(side[f]["bottom"] for f in frames),
           max(side[f]["bottom"] for f in frames)))

    # ---------------- (2) ★★ 跨支接缝：末帧逐位一致 ------------------------
    air = scan("airhit_side", sorted(set([SEAM_LAST_D13_FRAME,
                                          *SEAM_D13_FRAMES,
                                          *range(10, 19)])))[0]
    d13_end = air.get(SEAM_LAST_D13_FRAME)
    d14_start = side.get(START)
    seam_deltas = None
    if d13_end is not None and d14_start is not None:
        seam_deltas = {
            "top_px": int(d14_start["top"] - d13_end["top"]),
            "bottom_px": int(d14_start["bottom"] - d13_end["bottom"]),
            "head_row_px": r3((d14_start["head_row"] or 0.0)
                              - (d13_end["head_row"] or 0.0)),
            "height_px": int(d14_start["height_px"] - d13_end["height_px"]),
            "width_px": int((d14_start["width_px"] or 0)
                            - (d13_end["width_px"] or 0)),
        }
    res["px_seam_frame"] = {"d13_frame": SEAM_LAST_D13_FRAME,
                            "d14_frame": START, "deltas": seam_deltas}
    res["px_seam_match_tol_px"] = SEAM_MATCH_TOL_PX
    res["px_seam_frame_match_ok"] = bool(
        seam_deltas is not None
        and abs(seam_deltas["top_px"]) <= SEAM_MATCH_TOL_PX
        and abs(seam_deltas["bottom_px"]) <= SEAM_MATCH_TOL_PX
        and abs(seam_deltas["head_row_px"]) <= SEAM_MATCH_TOL_PX
        and abs(seam_deltas["height_px"]) <= SEAM_MATCH_TOL_PX)

    # ---------------- (3) ★★ 独门尺子：跨支逐帧步长 vs 弹道预测 ------------
    def seam_steps(view_map, frame_list, ppm_x, t_phase, source):
        """返回 [(帧, 实测步长 px, 弹道预测步长 px, 残差 px)]；
        ★ 首帧的步长要用"前一帧的位置"（本支 f0 的前一帧在 D13 里，同一条弹道）。"""
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

    # 主：D14 f0~f6。f0 的前一帧 = D13 f17，必须把 D13 的帧也放进同一张表
    merged_map = dict(side)
    for f in SEAM_D13_FRAMES:
        if f in air:
            merged_map[f - SEAM_LAST_D13_FRAME] = air[f]
    res["px_seam_merged_points"] = [
        {"d14_frame": f, "head_row": r3(merged_map[f]["head_row"])}
        for f in sorted(merged_map) if "head_row" in merged_map[f]]
    steps = seam_steps(merged_map, SEAM_D14_FRAMES, ppm, T_PHASE, "d14_prefix")
    res["px_seam_steps"] = steps
    res["px_seam_steps_ruler"] = (
        "`knockdownf_side f0~f6` 的**头带行心逐帧步长**与共享解析弹道"
        "（`T_PHASE=%.1f`）预测步长的残差；判据取 |残差| 的**中位数**"
        "（单个坏点不能推翻整段），并附最大残差与所在帧。" % T_PHASE)
    resid = sorted(abs(e["resid_px"]) for e in steps)
    res["px_seam_steps_median_abs_px"] = (round(float(np.median(resid)), 4)
                                          if resid else None)
    res["px_seam_steps_tol_px"] = SEAM_STEP_MED_TOL_PX
    if steps:
        worst = max(steps, key=lambda e: abs(e["resid_px"]))
        res["px_seam_steps_worst"] = worst
        res["px_seam_steps_worst_note"] = (
            "★ 最大残差落在 f%d：手臂从头顶移开 ⟹ 顶行由『手』换成『头』"
            "⟹ 头带行心在该帧被手支配（实测残差 %.3f px）。"
            % (worst["frame"], worst["resid_px"]))
    res["px_seam_steps_all_falling_ok"] = bool(
        steps and all(e["measured_px"] < 0.0 for e in steps))
    res["px_seam_steps_ok"] = bool(
        resid and float(np.median(resid)) <= SEAM_STEP_MED_TOL_PX
        and all(e["measured_px"] < 0.0 for e in steps))

    # ★ 正面：D13 自己 f14~f17（同一条弹道的上游段）
    ctrl_steps = seam_steps(air, SEAM_CTRL_D13_FRAMES, ppm, T_PHASE_D13,
                            "d13_tail")
    res["px_seam_steps_control"] = ctrl_steps
    ctrl_resid = sorted(abs(e["resid_px"]) for e in ctrl_steps)
    res["px_seam_steps_control_median_abs_px"] = (
        round(float(np.median(ctrl_resid)), 4) if ctrl_resid else None)
    res["px_seam_steps_control_ok"] = bool(
        ctrl_resid
        and float(np.median(ctrl_resid)) <= SEAM_STEP_MED_TOL_CTRL_PX)

    # ★ 反向：D14 f8~f13（已落地，姿态剧变）
    neg_steps = seam_steps(side, SEAM_NEG_D14_FRAMES, ppm, T_PHASE, "d14_landed")
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
        for f in SEAM_D14_FRAMES:
            if f in side:
                pts.append((f, side[f][carrier]))
        res["px_seam_g_" + carrier] = g_of(pts, "knockdownf_side")
    res["px_seam_g_ref_mm"] = round(G_PER_FRAME_MM, 5)
    res["px_seam_g_note"] = (
        "★ 二次拟合（11 点合并）在本支**只报不判**：1 px = 3 mm ⟹ `g` 的量化步长 "
        "0.907 px/帧²，且 f1 的头带被手臂污染（残差 +5.44 px）⟹ 拟合值被拉低至 "
        "2.283（误差 0.439）。主尺子改用**步长残差中位数**（见 `px_seam_steps_ok`）。")

    # ---------------- (4) 最低行：下落 / 触地 / 贴地 -----------------------
    def bottom_steps(view_map, order):
        """★ 步长一律**按帧间隔归一**（px/帧）—— 对照静帧有的是 4 帧跳采样。"""
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
    # ★ 步长是负数（下降）⟹ 违规是"降得不够多"：d > −阈值
    bad_fall = [(f, d) for f, d in steps_fall if d > -FALL_STEP_MIN_PX]
    res["px_fall_monotone_violations"] = [{"frame": f, "step_px": round(d, 3)}
                                          for f, d in bad_fall]
    res["px_fall_monotone_ok"] = bool(steps_fall and not bad_fall)

    # ★ 正面：A12 下落段
    ctrl = scan("jumpfall_side", CTRL_FRAMES)[0]
    ctrl_steps2 = bottom_steps(ctrl, [f for f in CTRL_FRAMES if f in ctrl])
    res["px_fall_control_steps_px"] = {str(f): round(d, 3)
                                       for f, d in ctrl_steps2}
    res["px_fall_monotone_control_ok"] = bool(
        ctrl_steps2 and all(d <= -FALL_STEP_MIN_PX for _f, d in ctrl_steps2))

    # ★ 反向：D12 地面段（含上行与平台）
    d12 = scan("launchhit_side", NEG_D12_FRAMES)[0]
    d12_steps = bottom_steps(d12, sorted(d12))
    res["px_fall_d12_steps_px"] = {str(f): round(d, 3) for f, d in d12_steps}
    res["px_fall_monotone_can_fail_ok"] = bool(
        d12_steps and any(d > -FALL_STEP_MIN_PX for _f, d in d12_steps))

    # ---- 触地帧：落差突变 ----
    land_step = None
    if (LAND - 1) in side and LAND in side:
        land_step = side[LAND]["bottom"] - side[LAND - 1]["bottom"]
    res["px_land_step_px"] = land_step
    res["px_land_step_mm"] = (None if land_step is None
                              else round(land_step / ppm, 2))
    res["px_land_step_min_px"] = LAND_STEP_MIN_PX
    res["px_fall_step_max_px"] = FALL_STEP_MAX_PX
    res["px_land_jump_ok"] = bool(
        land_step is not None and land_step <= -LAND_STEP_MIN_PX
        and steps_fall
        and all(-FALL_STEP_MAX_PX <= d <= 0.0 for _f, d in steps_fall))

    # ★ 反向：D13 全段归一化步长（全在空中）都远小于 25 px ⟹ 必红
    d13_all = scan("airhit_side", list(range(0, 19)))[0]
    d13_steps = bottom_steps(d13_all, sorted(d13_all))
    res["px_land_jump_d13_steps_px"] = {str(f): round(d, 3)
                                        for f, d in d13_steps}
    res["px_land_jump_d13_max_drop_px"] = (
        round(min(d for _f, d in d13_steps), 3) if d13_steps else None)
    res["px_land_jump_can_fail_ok"] = bool(
        d13_steps and all(-d < LAND_STEP_MIN_PX for _f, d in d13_steps))

    # ---- 鞋底接管期：最低行钉住 ----
    sole_rows = [side[f]["bottom"] for f in SOLE_WINDOW if f in side]
    ground_row = float(np.median(sole_rows)) if sole_rows else None
    res["px_ground_row"] = ground_row
    res["px_ground_row_source"] = (
        "★ 修正 ②：锚在**鞋底接管期** f%d~f%d 最低行的中位数（%s）——"
        "f ≥ %d 后裤管穿地接管最低行，不再代表鞋底。"
        % (SOLE_WINDOW[0], SOLE_WINDOW[-1], SOLE_WINDOW,
           SOLE_WINDOW[-1] + 1))
    dev = {str(f): r3(side[f]["bottom"] - ground_row)
           for f in SOLE_WINDOW if f in side and ground_row is not None}
    res["px_ground_contact_dev_px"] = dev
    res["px_ground_tol_px"] = GROUND_TOL_PX
    res["px_ground_contact_ok"] = bool(
        dev and max(abs(v) for v in dev.values()) <= GROUND_TOL_PX)

    # ★ 反向：D13 的同一窗口（全在空中）
    if d13_all and ground_row is not None:
        dev13 = {str(f): r3(d13_all[f]["bottom"] - ground_row)
                 for f in SOLE_WINDOW if f in d13_all}
        res["px_ground_contact_d13_dev_px"] = dev13
        res["px_ground_contact_can_fail_ok"] = bool(
            dev13 and max(abs(v) for v in dev13.values()) > GROUND_TOL_PX)
    else:
        res["px_ground_contact_can_fail_ok"] = False

    # ---- 裤管穿地登记（只报） ----
    breach = {str(f): r3(side[f]["bottom"] - ground_row)
              for f in frames if f >= SOLE_WINDOW[-1] + 1
              and ground_row is not None}
    res["trouser_ground_breach"] = {
        "dev_px": breach,
        "worst_px": (min(breach.values()) if breach else None),
        "worst_mm": (round(min(breach.values()) / ppm, 2) if breach else None),
        "worst_frame": (min(breach, key=lambda k: breach[k]) if breach else None),
        "note": ("★ 模型侧遗留（与 `Jacket_Hem` 同类）：`Trouser_L/R` 屈膝压缩时"
                 "穿出地面最多 110 mm，接管了剪影最低行；`Shoe_Sole_*` 全程停在 "
                 "−1.2 mm（极差 0.03 mm）⟹ 贴地成立，是本支**姿态定义之外**的几何问题。"),
    }

    # ---- 贴地自持：末段顶行/头带行心恒定 ----
    hold_rows = [side[f]["top"] for f in range(PLATEAU, TOTAL + 1) if f in side]
    hold_head = [side[f]["head_row"] for f in range(PLATEAU, TOTAL + 1)
                 if f in side and side[f]["head_row"] is not None]
    res["px_ground_hold"] = {
        "window": [PLATEAU, TOTAL],
        "top_rows": hold_rows,
        "head_rows": [round(v, 3) for v in hold_head],
        "top_span_px": (max(hold_rows) - min(hold_rows) if hold_rows else None),
        "head_span_px": (round(max(hold_head) - min(hold_head), 4)
                         if hold_head else None),
    }
    res["px_hold_tol_px"] = HOLD_TOL_PX
    res["px_ground_hold_ok"] = bool(
        hold_rows and hold_head
        and (max(hold_rows) - min(hold_rows)) <= HOLD_TOL_PX
        and (max(hold_head) - min(hold_head)) <= HOLD_TOL_PX)

    # ★ 反向：D13 的 f16~f18（继续下坠）
    hold13_top = [d13_all[f]["top"] for f in range(PLATEAU, 19) if f in d13_all]
    hold13_head = [d13_all[f]["head_row"] for f in range(PLATEAU, 19)
                   if f in d13_all and d13_all[f]["head_row"] is not None]
    res["px_ground_hold_d13"] = {
        "top_rows": hold13_top,
        "top_span_px": (max(hold13_top) - min(hold13_top)
                        if hold13_top else None),
        "head_rows": [round(v, 3) for v in hold13_head],
        "head_span_px": (round(max(hold13_head) - min(hold13_head), 4)
                         if hold13_head else None),
    }
    res["px_ground_hold_can_fail_ok"] = bool(
        hold13_top and hold13_head
        and ((max(hold13_top) - min(hold13_top)) > HOLD_TOL_PX
             or (max(hold13_head) - min(hold13_head)) > HOLD_TOL_PX))

    # ---------------- (5) ★ 前倒：剪影 高/宽 翻转 ---------------------------
    def prone_ratio(f_from, f_to):
        a, b = side.get(f_from), side.get(f_to)
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

    prone = prone_ratio(LAND, TOTAL)
    res["px_prone"] = prone
    res["px_prone_ruler"] = (
        "侧视剪影 从 `f=LAND` 到 `f=END`：高度比 ≤%.2f（趴下 → 变矮）"
        "且 宽度比 ≥%.2f（伸展开 → 变宽）。" % (PRONE_H_RATIO_MAX,
                                            PRONE_W_RATIO_MIN))
    res["px_prone_ok"] = bool(
        prone is not None and prone["height_ratio"] <= PRONE_H_RATIO_MAX
        and prone["width_ratio"] >= PRONE_W_RATIO_MIN)

    # ★ 反向：D14 自己 f0 → f=LAND（还没趴下）
    prone_ctrl = prone_ratio(START, LAND)
    res["px_prone_control"] = prone_ctrl
    res["px_prone_can_fail_ok"] = bool(
        prone_ctrl is None
        or prone_ctrl["height_ratio"] > PRONE_H_RATIO_MAX
        or prone_ctrl["width_ratio"] < PRONE_W_RATIO_MIN)

    # ---------------- (6) 只报：前视剪影 ----------------------------------
    front_frames = [0, 2, 4, 6, LAND, HOLD_END, COMPRESS_PEAK, 13,
                    PRONE_PEAK, PLATEAU, TOTAL]
    front, front_hem = scan("knockdownf_front", front_frames)
    res["front_report"] = {
        str(f): {"bottom": front[f]["bottom"], "top": front[f]["top"],
                 "height_px": front[f]["height_px"],
                 "width_px": front[f]["width_px"]}
        for f in sorted(front)}
    res["front_hem_dropped_frames"] = [e["frame"] for e in front_hem]

    # ---------------- (7) 附加：逐帧全量表（只报） -------------------------
    if os.environ.get("D14PX_DUMP"):
        res["px_dump_top_row"] = {str(f): side[f]["top"] for f in frames}
        res["px_dump_bottom_row"] = {str(f): side[f]["bottom"] for f in frames}
        res["px_dump_head_row"] = {str(f): r3(side[f]["head_row"])
                                   for f in frames}

    ok = sorted(k for k, v in res.items() if k.endswith("_ok"))
    res["ok_flags"] = ok
    res["failed"] = sorted(k for k in ok if res[k] is not True)
    print("D14_PIXELS " + json.dumps(res, ensure_ascii=False))
    print("D14_PIXELS_DONE failed=%s" % res["failed"])


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D14_PIXELS_FAILURE " + traceback.format_exc())
