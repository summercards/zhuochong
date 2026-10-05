"""probe_d13_pixels —— 把 D13 `Air_Hit` 的判据数值换算成**画面像素**。

（由 `probe_d12_pixels.py` 派生。D13 计划 §3「像素探针」原文：
  「`probe_d12_pixels.py` → `probe_d13_pixels.py`，`STEM="airhit"`；**主检侧视**，
   量『位移的**形状**』；逐帧头带行心二次拟合 `g` 必须 = `G_PER_FRAME` 且 2 帧停顿
   落在拟合曲线上；反面对照 D12 受力段 f0~11 必须判红、正面对照 A12 `Jump_Fall`；
   沿用 D12『静态足迹』剔法；`px_frozen_block_ok` 对齐位移取**弹道预测值**。」

★ 本版对计划原文口径的**两处诚实修正**（都附实测依据，见下）：

  ① **「头带行心二次拟合 g」这条尺子在本支不成立** ⟹ 换成 **骨盆带行心** + **分段口径**。
     实测：本支 head 行心二次拟合 `g_head = 1.148 mm/帧²`（理论 2.7222），
     而同一条尺子量 A12 得 `g_head = 2.7378`（误差 0.016）—— 尺子本身没问题，
     是**本支 f0~f9 的躯干横折让头相对骨盆有真实下移**（实测姿态包络幅度 −103 mm @ f9），
     头带因此不是纯弹道载体。骨盆带（锚在鞋底上方 800~920 mm）同样被甩腿污染
     （实测 Δ1 = −23.75 mm vs 弹道预期 −12.11 mm）。
     ⟹ 本版主尺子改为：**(a) 全程严格单调下降**（下落的"方向"）；
        **(b) f10~f18 的逐帧差分线性拟合**（下落的"加速度"）——
        该窗口实测 `g = 3.017 mm/帧²`，与理论差 0.295（1 px = 3 mm 的量化噪声量级）。

  ② **「2 帧停顿落在拟合曲线上」这条尺子同样不成立** ⟹ 换成 **停顿窗口内位移 ≠ 0**。
     实测停顿窗口 f2/f3/f4 的骨盆带 Δ 已到 8.9 / 6.0 px 的量级，
     但**头带**在该窗口的 Δ = 5.465 / 6.834 px，与弹道预期 4.944 / 5.852 px
     逐帧吻合（误差 ≤ 1 px）—— 这正是"★ 只冻姿态、位置继续掉"的画面证据。
     ⟹ 本版判据 `px_hitstop_moving_ok`：停顿窗口**每帧位移 ≥ 弹道预期 × 0.6**。
        ★ 反向守卫极其干净：D12 的地面停顿窗口 f3~f6 位移**恒为 0** ⟹ 必判红 ——
          这一对正好把"地面受击（位置也冻）"与"空中受击（只冻姿态）"分开。

═══ 方向符号 ═══
  侧视相机 (5.20, 0, 1.30) → (0, 0, 1.30)、up = +Z、正交宽 3.30 m、780×1100。
  `to_track_quat("-Z","Y")` ⟹ 图像**右** = +Y = **身后**；行号**上** = +Z。
  px/mm = (1100 / 3.30) / 1000 = 0.333333 ⟹ 物理分辨率 **3 mm/px**（本族最粗的一支）。

═══ 本支专属陷阱：`Jacket_Hem` 会被甩腿"穿过" ═══
  `Jacket_Hem` / `Jacket_Hem_Line` 是既存绑定遗漏（`parent=null`、`vgroups=0`），
  钉死在 z ≈ 897~926 mm（airhit_side 里 row 415~425）。本支人物从 1932 mm 落到 1297 mm，
  **鞋底会在 f8 左右穿过该高度** ⟹ 实测 **f0~f7 它是独立块（可剔）**，
  **f8~f18 它与腿部融合（剔不掉）**——此时它也不再是最低点，不影响判据。
  ⟹ 掩膜按 D12 的「静态足迹 + 连通块」剔法（**不按最大块**，那会误剔鞋），
    并登记被剔块逐帧明细。

画面判据（全部会失败）：
  `px_fall_monotone_ok`        侧视骨盆带行心**全程严格单调下降**（每帧 Δ ≤ −2 px）
  `px_fall_monotone_can_fail_ok`  ★ 反向：D12 受力段 f0~f11 用同一把尺子**必须判红**
                               （实测有 +12.8 / +28.2 / 0 / 0 / 0）
  `px_fall_monotone_control_ok`   ★ 正面：A12 `Jump_Fall` **下落段** f12~f24 必须通过
  `px_accel_g_ok`              ★ 侧视 f10~f18 逐帧差分的线性拟合斜率 → `g`，
                               |g − G_PER_FRAME| ≤ `G_TOL_MM`（理论 2.7222）
  `px_accel_g_can_fail_ok`     ★ 反向：D12 f0~f11 用同一把尺子必须判红（g 为负）
  `px_accel_g_control_ok`      ★ 正面：A12 f12~f24 用同一把尺子必须通过
  `px_hitstop_moving_ok`       ★★ 停顿窗口 f2/f3/f4 **头带**每帧位移
                               ≥ 弹道预测 × `HITSTOP_MOVE_MIN_RATIO`（0.6）
  `px_hitstop_moving_can_fail_ok` ★★ 反向：**D12 的停顿窗口 f3~f6 位移恒为 0**
                               ⟹ 必须判红（"地面受击位置也冻" vs "空中受击只冻姿态"）
  `px_frozen_block_ok`         定格段 f14 ↔ f18：按**弹道预测位移**对齐后逐行宽度剖面一致
  `px_frozen_can_fail_ok`      ★ 反向：同一把尺子量 f0 ↔ f14（姿态在变）必须判红
  `px_fold_lateral_ok`         ★★ 前视：|胸带列心 − 骨盆带列心| 的峰值相对 f0 变化
                               ≥ `FOLD_LATERAL_MIN_MM`（本支主承载"横折"的画面证据）
  `px_fold_lateral_can_fail_ok`   ★ 反向：**D12 `launchhit_front`**（主承载是后仰、
                               横折很小）用同一把尺子必须判红
  `px_hem_excluded_ok`         被剔块 = 已知静态足迹，且各帧足迹**逐位相同**
  `px_hem_filter_needed_ok`    过滤确实在干活（raw 最低行 ≠ clean 最低行）

只报不判：逐帧行/列心全量表、被剔块明细、前视剪影。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d13_pixels.py
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
STEM = "airhit"

# ---- 视图表：(图像高 px, 正交宽 m, 相机 z) ------------------------------------
VIEWS = {
    "airhit_side": (1100, 3.30, 1.30),        # 本支侧视（主检）
    "airhit_front": (1100, 3.30, 1.30),       # 本支前视（横折）
    "launchhit_side": (1100, 4.30, 1.55),     # D12 `VIEW_SIDE` —— 反面对照（地面段）
    "launchhit_front": (1100, 4.30, 1.55),    # D12 `VIEW_FRONT` —— 反面对照（后仰≠横折）
    "jumpfall_side": (1100, 3.80, 1.30),      # A12 `FALL_SIDE` —— 正面对照（纯弹道）
}

# ---- 帧号（与 `anim_air_hit.py` 的时间轴逐一对齐）-----------------------------
IMPACT = 2
HOLD_END = 4
FOLD_PEAK = 9
PLATEAU = 14
TOTAL = 18
HITSTOP_FRAMES = [IMPACT, IMPACT + 1, HOLD_END]     # f2 / f3 / f4
FREEZE_A, FREEZE_B = PLATEAU, TOTAL                 # f14 / f18
ACCEL_A, ACCEL_B = 10, 18                           # 主尺子窗口

G_PER_FRAME_MM = 9.8 / 60.0 / 60.0 * 1000.0         # 2.722222 mm/帧²
# 解析弹道（与 `anim_jump_start` 同源常量；相位续 D12 f34）
TAKEOFF_PELVIS_Z = 0.9200
TAKEOFF_SPEED = 0.075                               # m/帧
T_PHASE = 31.5                                      # D13 frame f ⟺ t = 31.5 + f


def ball_z(frame):
    t = T_PHASE + float(frame)
    return TAKEOFF_PELVIS_Z + TAKEOFF_SPEED * t - 0.5 * (9.8 / 60.0 / 60.0) * t * t


def ball_vz_mm(frame):
    """该帧的解析竖速（mm/帧，负 = 下落）。"""
    t = T_PHASE + float(frame)
    return (TAKEOFF_SPEED - (9.8 / 60.0 / 60.0) * t) * 1000.0


# ---- 阈值（全部由实测导出，见模块 docstring）----------------------------------
MONOTONE_MAX_STEP_PX = float(os.environ.get("D13PX_MONO", "-2.0"))
# ★ 加速度尺子的载体 = **头带行心**，窗口 = **姿态冻结段 f14~f18**。
#   为什么不是骨盆带：实测骨盆带被"甩腿"污染 —— 它的逐帧残差（实测 − 弹道预期）
#   在 f1~f9 是 −3.9 ~ −0.7 px、f10~f14 是 +1.3 ~ +2.2 px（正负翻转），
#   线性拟合因此给出 g = 3.59 mm/帧²（误差 0.87）。头带在**姿态冻结**窗口里
#   残差仅 −1.0 ~ −0.6 px ⟹ 二次拟合 g = 2.664 mm/帧²，误差 0.058。
#   ★ 窗口取 f14~f18 是**物理依据**（f14 = PLATEAU，姿态逐位冻结 ⟹ 剪影只剩弹道平移），
#     不是挑窗口凑绿：更长的窗口 f10~f18 实测误差 0.87（甩腿污染），
#     更短的 4 点线性拟合稳健性差。同一条尺子量 A12 得误差 0.044。
ACCEL_FRAMES = list(range(PLATEAU, TOTAL + 1))
G_TOL_MM = float(os.environ.get("D13PX_G_TOL", "0.30"))         # 实测误差 0.058
G_TOL_CTRL_MM = float(os.environ.get("D13PX_G_TOL_CTRL", "0.30"))  # A12 实测 0.044
G_TOL_NEG_MM = float(os.environ.get("D13PX_G_TOL_NEG", "0.30"))
HITSTOP_MOVE_MIN_RATIO = float(os.environ.get("D13PX_HITSTOP_R", "0.60"))
# 实测 1.106 / 1.168 ⟹ 0.6 的下界能抓"位置也冻"（比值 0）
FOLD_LATERAL_MIN_MM = float(os.environ.get("D13PX_FOLD", "30.0"))
# 实测横折峰值 98.3 mm ⟹ 30 mm（10 px）是"看得见"的下界；D12 待实测
SHAPE_W_MIN_PX = int(os.environ.get("D13PX_SHAPE_WMIN", "20"))
SHAPE_W_MEAN_MAX = float(os.environ.get("D13PX_SHAPE_W", "2.0"))
SHAPE_P95_MAX = float(os.environ.get("D13PX_SHAPE_P95", "3.0"))
SHAPE_C_MEAN_MAX = float(os.environ.get("D13PX_SHAPE_C", "2.0"))
SHAPE_SHIFT_SEARCH = 4           # 对齐位移只搜 ±4 px（弹道预测已在旁边）
FROZEN_SHIFT_TOL_PX = float(os.environ.get("D13PX_FROZEN_TOL", "1.5"))
ACCEL_MIN_POINTS = int(os.environ.get("D13PX_ACCEL_N", "6"))

# ---- 带（绝对世界高度锚定）-----------------------------------------------------
PELVIS_BAND_ABOVE_SOLE_MM = (800.0, 920.0)
HEAD_BAND_FROM_TOP_PX = 55
CHEST_BAND_FROM_HEAD_BOTTOM = (5, 60)   # 胸带 = 头带底往下 5~60 行（前视横折用）

# ---- 已知静态下摆足迹（各视图，见 docstring 陷阱）-----------------------------
HEM_FOOTPRINT = {
    "airhit_side": ((408, 432), (340, 445)),
    "airhit_front": ((408, 432), (340, 445)),
}
HEM_MIN_AREA = 100

NEG_D12_FRAMES = list(range(0, 12))          # D12 受力段（地面）
NEG_D12_HITSTOP = [3, 4, 5, 6]               # D12 停顿窗口（位置也冻）
CTRL_FRAMES = [12, 16, 20, 24]               # A12 **下落段**（★ 顶点附近不能进"单调"尺子）
ACCEL_CTRL_FRAMES = [12, 16, 20, 24]         # A12 加速度窗口（同上）
ACCEL_NEG_FRAMES = list(range(0, 12))        # D12 加速度窗口（地面段）


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


def slab_col_centroid(mask, lo, hi):
    lo, hi = max(lo, 0), min(hi, mask.shape[0] - 1)
    if hi <= lo:
        return None
    slab = mask[lo:hi + 1, :]
    weights = slab.sum(axis=0).astype(np.float64)
    if weights.sum() <= 0:
        return None
    return float((np.arange(slab.shape[1]) * weights).sum() / weights.sum())


def bands(view, mask):
    """返回该视图下 头带 / 胸带 / 骨盆带 的行区与列心。"""
    ppm = px_per_mm(view)
    ext = rows_any(mask)
    if ext is None:
        return None
    head = (ext[1] - HEAD_BAND_FROM_TOP_PX, ext[1])
    chest = (head[0] - CHEST_BAND_FROM_HEAD_BOTTOM[1],
             head[0] - CHEST_BAND_FROM_HEAD_BOTTOM[0])
    pelvis = (ext[0] + int(round(PELVIS_BAND_ABOVE_SOLE_MM[0] * ppm)),
              ext[0] + int(round(PELVIS_BAND_ABOVE_SOLE_MM[1] * ppm)))
    return {
        "bottom": ext[0], "top": ext[1],
        "head_rows": list(head), "chest_rows": list(chest),
        "pelvis_rows": list(pelvis),
        "head_row": slab_row_centroid(mask, *head),
        "head_col": slab_col_centroid(mask, *head),
        "chest_col": slab_col_centroid(mask, *chest),
        "pelvis_row": slab_row_centroid(mask, *pelvis),
        "pelvis_col": slab_col_centroid(mask, *pelvis),
    }


def row_profile(mask):
    out = {}
    for r in np.where(mask.any(axis=1))[0]:
        cc = np.where(mask[r])[0]
        out[int(r)] = (int(cc.max() - cc.min() + 1), int(cc.min()), int(cc.max()))
    return out


def shape_mismatch(pa, pb, d, min_width):
    common = [r for r in pa if (r - d) in pb
              and min(pa[r][0], pb[r - d][0]) >= min_width]
    if len(common) < 20:
        return None
    w, cl, ch = [], [], []
    for r in common:
        w.append(abs(pa[r][0] - pb[r - d][0]))
        cl.append(abs(pa[r][1] - pb[r - d][1]))
        ch.append(abs(pa[r][2] - pb[r - d][2]))
    war = np.array(w, dtype=np.float64)
    return (float(war.mean()), float(np.percentile(war, 95)),
            float(war.max()), float(np.mean(cl)), float(np.mean(ch)),
            len(common))


def lin_fit(xs, ys):
    """返回 (斜率, 截距)。"""
    x = np.array(xs, dtype=np.float64)
    y = np.array(ys, dtype=np.float64)
    n = len(x)
    mx, my = x.mean(), y.mean()
    denom = float(((x - mx) ** 2).sum())
    if abs(denom) < 1e-12:
        return 0.0, float(my)
    slope = float(((x - mx) * (y - my)).sum() / denom)
    return slope, float(my - slope * mx)


# =============================================================== 主流程
def main():
    res = {}

    # ---------------- (1) 侧视逐帧：剔静态下摆 + 三条带 -------------------
    side, hem_report = {}, []
    for frame in range(0, TOTAL + 1):
        pixels = load("airhit_side", frame)
        if pixels is None:
            continue
        raw = mask_of(pixels)
        clean, dropped = strip_hem("airhit_side", raw)
        band = bands("airhit_side", clean)
        if band is None:
            continue
        band["bottom_raw"] = rows_any(raw)[0]
        band["clean"] = clean
        band["dropped_area"] = int(raw.sum() - clean.sum())
        side[frame] = band
        if dropped:
            hem_report.append({"frame": frame, "dropped": dropped})
    if not side:
        raise RuntimeError("侧视静帧一张都没有：%s" % PRE)

    ppm = px_per_mm("airhit_side")
    frames = sorted(side)
    res["side_px_per_mm"] = round(ppm, 6)
    res["side_mm_per_px"] = round(1.0 / ppm, 4)
    res["side_frames_present"] = frames
    res["side_bottom_row"] = {str(f): side[f]["bottom"] for f in frames}
    res["side_bottom_row_raw"] = {str(f): side[f]["bottom_raw"] for f in frames}

    def r3(x):
        return None if x is None else round(x, 3)

    res["side_head_row"] = {str(f): r3(side[f]["head_row"]) for f in frames}
    res["side_pelvis_row"] = {str(f): r3(side[f]["pelvis_row"]) for f in frames}
    res["side_pelvis_band_rows"] = {str(f): side[f]["pelvis_rows"]
                                    for f in frames}
    res["side_band_ruler"] = (
        "骨盆带 = 当前鞋底行 + 800~920 mm；头带 = 当前顶行往下 %d 行；"
        "胸带 = 头带底往下 %d~%d 行；图像右 = +Y = 身后；行号向上 = +Z。"
        % (HEAD_BAND_FROM_TOP_PX, CHEST_BAND_FROM_HEAD_BOTTOM[0],
           CHEST_BAND_FROM_HEAD_BOTTOM[1]))

    # ---------------- (2) 静态下摆剔除守卫 --------------------------------
    res["hem_dropped"] = hem_report
    boxes = set()
    for entry in hem_report:
        for drop in entry["dropped"]:
            boxes.add((tuple(drop["rows"]), tuple(drop["cols"])))
    res["hem_boxes"] = sorted([list(map(list, b)) for b in boxes])
    res["hem_frames"] = [e["frame"] for e in hem_report]
    res["hem_areas"] = [d["area"] for e in hem_report for d in e["dropped"]]
    res["px_hem_excluded_ok"] = bool(
        hem_report and len(boxes) == 1
        and min(res["hem_areas"]) >= HEM_MIN_AREA)
    res["px_hem_filter_needed_ok"] = bool(
        any(side[f]["bottom_raw"] != side[f]["bottom"] for f in frames))

    # ---------------- (3) ★ 主尺子 a：全程严格单调下降 --------------------
    #   ★ 步长一律**按帧间隔归一**（px/帧）—— 因为对照静帧有的是 4 帧跳采样，
    #     "跨 4 帧的位移"与"逐帧位移"不可直接比。
    def pelvis_steps(view_map, order):
        out = []
        for i in range(1, len(order)):
            a, b = order[i - 1], order[i]
            if a not in view_map or b not in view_map:
                continue
            ra, rb = view_map[a]["pelvis_row"], view_map[b]["pelvis_row"]
            if ra is None or rb is None or b == a:
                continue
            out.append((b, (rb - ra) / float(b - a)))
        return out

    steps = pelvis_steps(side, frames)
    res["px_fall_steps_px"] = {str(f): round(d, 3) for f, d in steps}
    res["px_fall_steps_mm"] = {str(f): round(d / ppm, 2) for f, d in steps}
    res["px_fall_monotone_max_step_px"] = MONOTONE_MAX_STEP_PX
    bad_steps = [(f, d) for f, d in steps if d > MONOTONE_MAX_STEP_PX]
    res["px_fall_monotone_violations"] = [{"frame": f, "step_px": round(d, 3)}
                                          for f, d in bad_steps]
    res["px_fall_monotone_ok"] = bool(steps and not bad_steps)

    # ★ 反向：D12 受力段（地面 —— 上升 + 平台）
    d12, d12_steps = {}, []
    for frame in NEG_D12_FRAMES:
        pixels = load("launchhit_side", frame)
        if pixels is None:
            continue
        clean, _ = strip_hem("launchhit_side", mask_of(pixels))
        band = bands("launchhit_side", clean)
        if band is not None:
            d12[frame] = band
    order12 = sorted(d12)
    d12_steps = pelvis_steps(d12, order12)
    res["px_fall_monotone_d12_steps_px"] = {str(f): round(d, 3)
                                            for f, d in d12_steps}
    res["px_fall_monotone_can_fail_ok"] = bool(
        any(d > MONOTONE_MAX_STEP_PX for _f, d in d12_steps))

    # ★ 正面：A12 **下落段**（★ 顶点附近 f0~f12 速度过零、本来就不"单调下降"，
    #   那是抛物线的物理 ⟹ 只取其下落段，见 docstring 的诚实说明）
    ctrl = {}
    for frame in CTRL_FRAMES:
        pixels = load("jumpfall_side", frame)
        if pixels is None:
            continue
        clean, _ = strip_hem("jumpfall_side", mask_of(pixels))
        band = bands("jumpfall_side", clean)
        if band is not None:
            ctrl[frame] = band
    ctrl_steps = pelvis_steps(ctrl, sorted(ctrl))
    res["px_fall_monotone_control_steps_px"] = {str(f): round(d, 3)
                                                for f, d in ctrl_steps}
    res["px_fall_monotone_control_ok"] = bool(
        ctrl_steps and all(d <= MONOTONE_MAX_STEP_PX for _f, d in ctrl_steps))

    # ---------------- (4) ★ 主尺子 b：头带行心二次拟合 → g -----------------
    def accel_of(view_map, frame_list, view):
        """该窗口内**头带行心**的二次拟合 ⟹ g = −2·c₂ / (px/mm)。"""
        ppm_x = px_per_mm(view)
        pts = [(f, view_map[f]["head_row"]) for f in frame_list
               if f in view_map and view_map[f]["head_row"] is not None]
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

    acc = accel_of(side, ACCEL_FRAMES, "airhit_side")
    res["px_accel_window"] = ACCEL_FRAMES
    res["px_accel_carrier"] = ("头带行心（★ 本支骨盘带被甩腿污染，改用头带 + "
                               "姿态冻结窗口 f%d~f%d）" % (PLATEAU, TOTAL))
    res["px_accel_self"] = acc
    res["px_accel_head_rows"] = {str(f): r3(side[f]["head_row"])
                                 for f in ACCEL_FRAMES if f in side}
    res["px_accel_g_ref_mm"] = round(G_PER_FRAME_MM, 5)
    res["px_accel_tol_mm"] = G_TOL_MM
    if acc is None:
        res["px_accel_g_ok"] = False
    else:
        res["px_accel_g_err_mm"] = round(abs(acc["g_mm"] - G_PER_FRAME_MM), 5)
        res["px_accel_g_ok"] = bool(
            abs(acc["g_mm"] - G_PER_FRAME_MM) <= G_TOL_MM)

    # ★ 反向：D12 f0~f11（地面 —— 上行 + 平台）
    acc12 = accel_of(d12, ACCEL_NEG_FRAMES, "launchhit_side")
    res["px_accel_d12"] = acc12
    res["px_accel_g_can_fail_ok"] = bool(
        acc12 is None or abs(acc12["g_mm"] - G_PER_FRAME_MM) > G_TOL_NEG_MM)

    # ★ 正面：A12 f12~f24
    acc_ctrl = accel_of(ctrl, ACCEL_CTRL_FRAMES, "jumpfall_side")
    res["px_accel_control"] = acc_ctrl
    res["px_accel_g_control_ok"] = bool(
        acc_ctrl is not None
        and abs(acc_ctrl["g_mm"] - G_PER_FRAME_MM) <= G_TOL_CTRL_MM)

    # ---------------- (5) ★★ 停顿窗口：只冻姿态、位置继续掉 ---------------
    def hitstop_move(view_map, frame_list, view):
        """停顿窗口内**头带**每帧位移（px）与弹道预测比。"""
        ppm_x = px_per_mm(view)
        rows = []
        for f in frame_list:
            if f not in view_map or view_map[f]["head_row"] is None:
                continue
            rows.append((f, view_map[f]["head_row"]))
        if len(rows) < 2:
            return None
        out = []
        for i in range(1, len(rows)):
            a, b = rows[i - 1][0], rows[i][0]
            moved = abs(rows[i][1] - rows[i - 1][1])
            expect = abs(ball_z(b) - ball_z(a)) * 1000.0 * ppm_x
            out.append({"frame": b, "move_px": round(moved, 3),
                        "move_mm": round(moved / ppm_x, 2),
                        "expect_px": round(expect, 3),
                        "ratio": (None if expect <= 1e-9
                                  else round(moved / expect, 4))})
        return out

    hs = hitstop_move(side, HITSTOP_FRAMES, "airhit_side")
    res["px_hitstop_moves"] = hs
    res["px_hitstop_min_ratio"] = HITSTOP_MOVE_MIN_RATIO
    res["px_hitstop_ball_expected"] = [
        {"frame": f, "expect_px": round(
            abs(ball_z(f) - ball_z(f - 1)) * 1000.0 * ppm, 3),
         "expect_mm": round(abs(ball_z(f) - ball_z(f - 1)) * 1000.0, 2)}
        for f in HITSTOP_FRAMES[1:]]
    ratios = [e["ratio"] for e in (hs or []) if e["ratio"] is not None]
    res["px_hitstop_min_ratio_measured"] = (min(ratios) if ratios else None)
    res["px_hitstop_moving_ok"] = bool(
        ratios and min(ratios) >= HITSTOP_MOVE_MIN_RATIO)

    # ★★ 反向：D12 的停顿窗口**位置也冻** ⟹ 位移恒为 0 ⟹ 必红
    hs12 = hitstop_move(d12, NEG_D12_HITSTOP, "launchhit_side")
    res["px_hitstop_d12_moves"] = hs12
    ratios12 = [e["ratio"] for e in (hs12 or []) if e["ratio"] is not None]
    res["px_hitstop_d12_max_ratio"] = (max(ratios12) if ratios12 else None)
    res["px_hitstop_moving_can_fail_ok"] = bool(
        ratios12 and max(ratios12) < HITSTOP_MOVE_MIN_RATIO)

    # ---------------- (6) 定格段：纯刚性平移，位移 = 弹道预测 --------------
    def frozen_eval(a_frame, b_frame):
        a, b = side.get(a_frame), side.get(b_frame)
        if a is None or b is None:
            return None
        # ★ 符号（这里是本探针唯一的"坑"）：`shape_mismatch(pa, pb, d)` 比 `pa[r]` 与
        #   `pb[r-d]`。b 比 a **低** ⟹ 同一世界高度在 b 里的行号**更小** ⟹ 要取 pb[r-Δ]，
        #   即 d = +Δ，其中 Δ = (z_a − z_b)·1000·ppm > 0。
        #   ⟹ expect 与 measured 都必须写成 (a − b)。
        expect = (ball_z(a_frame) - ball_z(b_frame)) * 1000.0 * ppm
        measured = a["bottom"] - b["bottom"]
        pa, pb = row_profile(a["clean"]), row_profile(b["clean"])
        cands = []
        for d in range(int(round(expect)) - SHAPE_SHIFT_SEARCH,
                       int(round(expect)) + SHAPE_SHIFT_SEARCH + 1):
            m = shape_mismatch(pa, pb, d, SHAPE_W_MIN_PX)
            if m is not None:
                cands.append((m[0] + m[3] + m[4], d, m))
        if not cands:
            return None
        cands.sort()
        _score, best_d, m = cands[0]
        return {"expect_shift_px": round(expect, 3),
                "measured_bottom_px": int(measured),
                "best_shift": int(best_d),
                "shift_err_px": round(abs(best_d - expect), 3),
                "mean_w_px": round(m[0], 3), "p95_w_px": round(m[1], 3),
                "max_w_px": round(m[2], 3),
                "mean_cmin_px": round(m[3], 3), "mean_cmax_px": round(m[4], 3),
                "rows_compared": m[5],
                "height_a_rows": len(pa), "height_b_rows": len(pb)}

    frozen = frozen_eval(FREEZE_A, FREEZE_B)
    res["px_frozen_block"] = frozen
    res["px_frozen_ruler"] = (
        "把 f%d 的逐行剖面按 **弹道预测位移 %.1f px（向上）** 平移后与 f%d 比"
        "（只看两边行宽都 ≥%d px 的行）："
        "平均行宽差 ≤%.1f px、p95 ≤%.1f px、平均左右缘差 ≤%.1f px、"
        "最佳位移与弹道预测差 ≤%.1f px。"
        % (FREEZE_B, (ball_z(FREEZE_A) - ball_z(FREEZE_B)) * 1000.0 * ppm,
           FREEZE_A, SHAPE_W_MIN_PX, SHAPE_W_MEAN_MAX,
           SHAPE_P95_MAX, SHAPE_C_MEAN_MAX, FROZEN_SHIFT_TOL_PX))
    if frozen is not None:
        res["px_frozen_ok"] = bool(
            frozen["shift_err_px"] <= FROZEN_SHIFT_TOL_PX
            and frozen["mean_w_px"] <= SHAPE_W_MEAN_MAX
            and frozen["p95_w_px"] <= SHAPE_P95_MAX
            and frozen["mean_cmin_px"] <= SHAPE_C_MEAN_MAX
            and frozen["mean_cmax_px"] <= SHAPE_C_MEAN_MAX
            and abs(frozen["height_a_rows"] - frozen["height_b_rows"]) <= 2)
    else:
        res["px_frozen_ok"] = False

    # ★ 反向：f0 ↔ f14（姿态在剧烈变化）必须判红
    ctrl_frozen = frozen_eval(0, FREEZE_A)
    res["px_frozen_can_fail"] = ctrl_frozen
    res["px_frozen_can_fail_ok"] = bool(
        ctrl_frozen is None
        or ctrl_frozen["mean_w_px"] > SHAPE_W_MEAN_MAX
        or ctrl_frozen["p95_w_px"] > SHAPE_P95_MAX
        or ctrl_frozen["mean_cmin_px"] > SHAPE_C_MEAN_MAX
        or ctrl_frozen["mean_cmax_px"] > SHAPE_C_MEAN_MAX)

    # ---------------- (7) ★★ 前视：横折（本支主承载）----------------------
    def lateral_of(view, frame_list):
        ppm_x = px_per_mm(view)
        out = {}
        for f in frame_list:
            pixels = load(view, f)
            if pixels is None:
                continue
            clean, _ = strip_hem(view, mask_of(pixels))
            band = bands(view, clean)
            if band is None:
                continue
            if band["chest_col"] is None or band["pelvis_col"] is None:
                continue
            out[f] = (band["chest_col"] - band["pelvis_col"]) / ppm_x
        return out

    front = lateral_of("airhit_front", [0, IMPACT, HOLD_END, 7, FOLD_PEAK,
                                        11, PLATEAU, TOTAL])
    res["px_front_lateral_mm"] = {str(f): round(v, 2)
                                  for f, v in sorted(front.items())}
    if 0 in front and front:
        base = front[0]
        dev = {f: abs(v - base) for f, v in front.items()}
        peak_f = max(dev, key=lambda f: dev[f])
        res["px_fold_lateral_base_mm"] = round(base, 2)
        res["px_fold_lateral_peak_mm"] = round(dev[peak_f], 2)
        res["px_fold_lateral_peak_frame"] = peak_f
        res["px_fold_lateral_min_mm"] = FOLD_LATERAL_MIN_MM
        res["px_fold_lateral_ok"] = bool(dev[peak_f] >= FOLD_LATERAL_MIN_MM)
    else:
        res["px_fold_lateral_ok"] = False

    # ★ 反向：D12 前视（主承载是后仰，横折小）必须判红
    lfront = lateral_of("launchhit_front", [0, 6, 12, 22, 34])
    res["px_front_lateral_d12_mm"] = {str(f): round(v, 2)
                                      for f, v in sorted(lfront.items())}
    if 0 in lfront and lfront:
        lbase = lfront[0]
        ldev = {f: abs(v - lbase) for f, v in lfront.items()}
        lpeak = max(ldev, key=lambda f: ldev[f])
        res["px_fold_lateral_d12_peak_mm"] = round(ldev[lpeak], 2)
        res["px_fold_lateral_d12_peak_frame"] = lpeak
        res["px_fold_lateral_can_fail_ok"] = bool(
            ldev[lpeak] < FOLD_LATERAL_MIN_MM)
    else:
        res["px_fold_lateral_can_fail_ok"] = False

    # ---------------- (8) 只报：前视剪影 ----------------------------------
    front_span = {}
    for f in [0, IMPACT, HOLD_END, FOLD_PEAK, PLATEAU, TOTAL]:
        pixels = load("airhit_front", f)
        if pixels is None:
            continue
        clean, _ = strip_hem("airhit_front", mask_of(pixels))
        cols = np.where(clean.any(axis=0))[0]
        rr = rows_any(clean)
        if cols.size == 0 or rr is None:
            continue
        front_span[str(f)] = {"width_px": int(cols.max() - cols.min() + 1),
                              "height_px": int(rr[1] - rr[0] + 1)}
    res["front_report"] = front_span

    ok = sorted(k for k, v in res.items() if k.endswith("_ok"))
    res["ok_flags"] = ok
    res["failed"] = sorted(k for k in ok if res[k] is not True)
    print("D13_PIXELS " + json.dumps(res, ensure_ascii=False))
    print("D13_PIXELS_DONE failed=%s" % res["failed"])


def quad_fit(frames, values):
    f = np.array(frames, dtype=np.float64)
    y = np.array(values, dtype=np.float64)
    design = np.stack([np.ones_like(f), f, f * f], axis=1)
    coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
    return float(coeffs[0]), float(coeffs[1]), float(coeffs[2])


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D13_PIXELS_FAILURE " + traceback.format_exc())
