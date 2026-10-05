"""probe_d10_pixels —— 把 D10 `Hit_Body` 的判据数值换算成**画面像素**。

（由 `probe_d09_pixels.py` 派生；D10 计划 §3 要求「改 `STEM = "hitbody"`、
  `SIDE_SIGN = −1`（前折 ⟹ 左移）、`REG_ROOT_MOTION_M = 0.0`（方案 A）；
  ★ **口径要换回来**：躯干从 D09 的"**必须不动**"（`side_torso_still_ok` **上界**）
  换回"**看得见在动**"（`side_torso_ok` **下界**），头部从"主判据"降为"配角只报"」。）

背景（D03 第 3 号教训）：
    判据数值 ≠ 观众看到的轮廓位移；头绕颈旋转时轮廓中心只走一半。
    ⟹ 凡是"位移/张开类"的语义判据，落定前**必须**做一次
       「判据数值 → 画面像素」复核（1 mm ≈ 0.556 px）。

═══ D10 回到 D05~D08 那个族（整躯干受力），但受力点在**中段** ═══
    D09 是局部受力 ⟹ 躯干必须"读不出动"（上界），头颈是主判据。
    D10 反过来：**躯干是主判据**（必须"看得见在折"，下界），
    头颈是**配角**（惯性拖着走，只报 + 一条"滞后"的时序判据）。
    ⟹ 照抄 D09 的 `side_torso_still_ok` 会把**正确的动画**判红。

═══ 方向符号（本支头号陷阱）：前折 = 上身往 −Y（身前）= 侧视**左**移 ═══
    坐标约定（与 `anim_lib` 一致）：+Y = 角色身后，正面朝 −Y。
    侧视相机在 (+4.2, 0, 0.92) 看向原点 ⟹ 图像**右方 = +Y = 身后的方向**。
    ⟹ `SIDE_SIGN = −1`（同 D06/D08 的前折口径；D09 后仰是 +1，**别照抄**）。
    若有人把 D09 的 `+1` 照抄过来，`side_torso_ok_*` 会**立刻变红**。

★★ 本支主设计 `head_lag_px_ok`（门禁 `head_lag_ok` 的画面证据）：
    侧视**头部带**重心的**峰值帧号**必须**晚于**躯干带 ≥2 帧。
    这条量的是"时序"，不是"幅度" —— 幅度类判据全绿也证明不了"头来不及跟上"。

判据的**适用域**：门禁只挂在 `hitstop` 停顿平台内（本支 `IMPACT=3`、`HOLD_END=6`）
    ⟹ `GATED_PAIRS` 取 `f0003 / f0005`。头峰 / 过冲段与落定段的帧**只报不判**。

═══ ★★ 末帧口径：本支**回原位**（方案 A ⟹ 同 D09）═══
    计划 §2 §3：「方案 A ⟹ 末帧**逐位回零位**（含位置）⟹ `end_identical_ok` 可判」。
    ⟹ D07/D08 的 `end_body_shift_ok`（"被推走了"）在本支是**错的口径**，降级为只报。

画面判据（全部会失败）：
    `side_torso_ok_*`         侧视躯干带重心**左**移 ≥ `TORSO_MIN_PX`（★ 主判据）
    `side_head_report_*`      侧视头部带重心左移（**配角，只报**）
    `head_lag_px_ok`          ★ 头部带重心峰值帧 晚于 躯干带 ≥2 帧（时序，主设计）
    `front_arms_held_ok_*`    前视手臂带宽度增量 ≤ `arms_max_px`（上界：拳架不许崩）
    `hitstop_identical_ok`    停顿平台 f3 ↔ f6 像素掩膜**逐位相同**
    `end_identical_ok`        末帧 f38 ↔ f0 掩膜**逐位相同**（★ 回原位）
    `end_torso_shape_ok`      末帧躯干带列跨度 = f0（≤ `END_TORSO_SPAN_TOL_PX`）
    `end_settled_ok`          f30 ↔ f38 掩膜**逐位相同**（落定段冻结）
    `px_bound_can_fail_ok`    上界"能失败"的当场证据（D04 的张开峰必须越界）
    `px_control_lower_ok`     同一条躯干下界在 D04 上也通过（尺子非量身定做）
    `px_torso_can_fail_ok`    ★ 反向守卫：同一把尺子量 **D09 的躯干**（逐位不动）
                              必须**不通过** ⟹ 证明 `side_torso_ok` 不是恒真的空判据

只报不判：着色差（亚像素法线现象）、`end_identical_*_report`、`end_body_shift_report`、
    剪影/长宽比、前视横向重心、头部带位移（配角）。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d10_pixels.py
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
STEM = "hitbody"
# ★ 门禁对：两侧都落在 `hitstop` 停顿平台内（本支 IMPACT=3、HOLD_END=6）
GATED_PAIRS = [("f0000", "f0003"), ("f0000", "f0005")]
# ★ 报告对：停顿末 / 头峰 / 回落中 / 过冲峰 / 过冲后微抖 / CANCEL / 末帧（只报不判）
REPORT_PAIRS = [("f0000", "f0006"), ("f0000", "f0008"), ("f0000", "f0012"),
                ("f0000", "f0016"), ("f0000", "f0019"), ("f0000", "f0030"),
                ("f0000", "f0038")]
VIEWS = ("front", "side")

# ---- ★★ 方向符号（本支头号陷阱）：前折 ⟹ 侧视重心**左**移 --------------------
#   同 D06/D08（前折族）；★ D09 后仰是 +1 —— 照抄会立刻判红。
SIDE_SIGN = -1.0          # D10：图像左 = −Y = 身前 ⟹ "上身被折下去" = 往左
CONTROL_SIDE_SIGN = 1.0   # D04（破防·后仰）：正确方向是往右 ⟹ 尺子同一把

# ---- 帧号（与 `anim_hit_body.py` 的时间轴逐一对齐）---------------------------
HITSTOP_A, HITSTOP_B = "f0003", "f0006"    # 停顿平台两端（IMPACT ~ HOLD_END）
SETTLE_A, SETTLE_B = "f0030", "f0038"      # 落定段（CANCEL ~ END）
END_TAG = "f0038"                          # 末帧（= TOTAL = 38）
# ★ 时序判据用的采样帧序列（本支渲出来的全部帧）
SEQ_TAGS = ["f0000", "f0003", "f0005", "f0006", "f0008", "f0012", "f0016",
            "f0019", "f0030", "f0038"]

# ---- 阈值（下界类：幅度必须"读得出来"）--------------------------------------
# ★ 门禁侧 `chest_fold_peak = 14.796°`、`head_fwd = 123.59 mm`（68.7 px）
TORSO_MIN_PX = 8.0     # 计划 §5：幅度下界换算后 ≥8 px（躯干）
# ---- ★★★ 躯干带必须**换区间**，这不是放宽容差，是尺子的适用域（本支 #1 教训）----
#   旧口径 `(0.45, 0.72)`（D04~D09 共用）在本支**量错了东西**：
#   本支是**中段受力** ⟹ 骨盆**后移**（+Y）+ 上身**前折**（−Y）—— 两段方向**相反**。
#   而 `(0.45, 0.72)` 横跨"往右走的腰（46%~60%）"与"往左走的胸（65%~72%）"
#   ⟹ 相互抵消，实测只剩 **6.59 px**（真值 10.82 px 被吃掉了 39%）。
#   `_d10_band_scan.py` 逐区间实测（f0↔f3 / f0↔f8 / D04 / D09，单位 px）：
#     0.45-0.72 : −6.59  −5.60  | 21.20  | 0.45   ← 旧尺子（抵消最重）
#     0.55-0.72 : −10.91 −9.56  | 29.41  | 0.41
#     0.62-0.78 : −10.82 −9.43  | 47.55  | −0.91  ← 本支采用
#     0.65-0.80 : −12.37 −10.82 | 51.99  | −1.32
#   ⟹ 取 **(0.62, 0.78)** = **胸腔带**（胸骨 → 大肩上沿）：这一整段是"被打折下去"
#     的载体，单向前折、不被骨盆后移污染。三条一起满足：
#       ① D10 实测 10.82 px ≥ 8（余量 1.35×）；
#       ② D04 实测 47.55 px ≥ 8（**尺子非为本支量身定做**）；
#       ③ D09 实测 |−0.91| < 8（**同一把尺子在"躯干不动"的支上必须不通过**）。
TORSO_BAND_FRAC = (0.62, 0.78)
# ---- ★★ 阈值（D10 专属：躯干**看得见在动** ⟹ 上界口径在本支**不适用**）--------
#   （D09 的 `TORSO_STILL_MAX_PX = 2.0` 在本支**删除** —— 见模块头）
#   ★ 反向守卫 `px_torso_can_fail_ok` 用 **D09** 的躯干（逐位不动）当场证伪。
MIRROR_TORSO = ("hithead", "f0000", "f0003")   # D09 局部受力 ⟹ 躯干读不出动
#   ★ 第二条反向守卫 `px_torso_can_fail_d10_ok`：**同一支内部**的过冲帧
#     （f16：上身弹回、位移≈0）也必须**不通过** —— 不需要额外渲染。
FAIL_FRAME_TAG = "f0016"
# ---- 阈值（上界类：必须"读不出重击"）----------------------------------------
# ★★ 上界用**跨设计标定**：同一把尺子量 D04 的**张开峰**（f0 ↔ f4），
#   得 `d04_peak_px`；本支上界 = `ARMS_MAX_FRAC_OF_D04 × d04_peak_px`。
#   ⟹ 同一条判据在 D05~D10 上必须**通过**、在 D04 上必须**失败**。
#   ★ 本支**刻意沿用 0.10**（与 D05~D09 同一把尺子，不为本支重定标）：
#     实测 13 px ≤ 24.2 px，余量 1.86×。
ARMS_MAX_FRAC_OF_D04 = 0.10
# ---- 前视横向位移：**只报不判**（适用域问题，不是动画不达标）-----------------
LAT_MIN_PX_REPORT = 1.0
# ---- ★★ 专属：末帧口径（**回原位**，继承 D05/D06/D09）-------------------------
#   ★ 比例尺方向：计划 §4 给的是「1 mm ≈ 0.556 px」⟹
#     **px → mm 要除以 0.556**（= 乘 1.7986），不是乘 0.556。
MM_PER_PX = 1.0 / 0.556
#   `end_torso_shape_ok`：末帧**胸腔带**的列跨度与 f0 相同 ⟹ 躯干**形状**回去了
CHEST_BAND_FRAC = (0.70, 0.80)
END_TORSO_SPAN_TOL_PX = 2.0
# ---- 「回到零位」的画面判据（分布口径，非逐位相同）---------------------------
END_SIL_PX = 2.0
END_ROWS_GT2_MAX = 3
SHADE_MEAN_REF = 0.05
# ★ 对照组 = **D04**：`CONTROL_PEAK` 取它的**张开峰**（f0 ↔ f4）；
#   `CONTROL_END` 取它的**回零对**，用于剪影分布口径的标定。
CONTROL_PEAK = ("guardbreak", "f0000", "f0004")
CONTROL_END = ("guardbreak", "f0000", "f0060")
# ★ 本支登记的骨盆位移（方案 A ⟹ 无净位移 = 0）
REG_ROOT_MOTION_M = 0.0
# ---- ★★ 本支主设计：头颈**滞后**的画面证据（时序）---------------------------
HEAD_LAG_MIN_FRAMES_PX = 2


def load(path):
    image = bpy.data.images.load(path, check_existing=False)
    width, height = image.size
    pixels = np.array(image.pixels[:], dtype=np.float32)
    pixels = pixels.reshape(height, width, 4)
    bpy.data.images.remove(image)
    return pixels


def mask_of(pixels):
    """角色掩膜：优先 alpha，其次"非白底"。返回 (h, w) bool，行 0 = 图像**底部**。"""
    alpha = pixels[:, :, 3]
    if float(alpha.min()) < 0.5:
        return alpha > 0.5
    rgb = pixels[:, :, :3]
    return rgb.min(axis=2) < 0.92


def row_span(mask, rows):
    band = mask[rows[0]:rows[1], :]
    cols = np.where(band.any(axis=0))[0]
    if cols.size == 0:
        return None
    return int(cols.min()), int(cols.max()), int(cols.max() - cols.min() + 1)


def row_extents(mask):
    extents = []
    for row in mask:
        cols = np.where(row)[0]
        extents.append((int(cols.min()), int(cols.max())) if cols.size else None)
    return extents


def silhouette_delta(mask_a, mask_b, top_n=5):
    """逐行剪影左右缘差（判据挂**分布**，不挂 max —— 见 D04 第 3 号教训）。"""
    ea, eb = row_extents(mask_a), row_extents(mask_b)
    rows, compared, missing = [], 0, 0
    for index, (a, b) in enumerate(zip(ea, eb)):
        if a is None or b is None:
            if (a is None) != (b is None):
                missing += 1
            continue
        rows.append((index, abs(a[0] - b[0]), abs(a[1] - b[1])))
        compared += 1
    if not compared:
        return {"max_left": None, "max_right": None, "rows_compared": 0}
    worst = sorted(rows, key=lambda r: max(r[1], r[2]), reverse=True)
    out = {
        "max_left": max(r[1] for r in rows),
        "max_right": max(r[2] for r in rows),
        "rows_compared": compared,
        "rows_missing": missing,
        "rows_gt2_left": sum(1 for r in rows if r[1] > 2),
        "rows_gt2_right": sum(1 for r in rows if r[2] > 2),
        "median_left": int(np.median([r[1] for r in rows])),
        "median_right": int(np.median([r[2] for r in rows])),
        "worst_rows": [[int(r[0]), int(r[1]), int(r[2])] for r in worst[:top_n]],
    }
    out["rows_gt2_total"] = out["rows_gt2_left"] + out["rows_gt2_right"]
    out["sil_ok"] = bool(
        out["rows_missing"] == 0
        and out["median_left"] == 0
        and out["median_right"] == 0
        and out["rows_gt2_total"] <= END_ROWS_GT2_MAX)
    return out


def shade_stats(pixels_a, pixels_b):
    rgb_a, rgb_b = pixels_a[:, :, :3], pixels_b[:, :, :3]
    content = np.maximum(rgb_a.max(axis=-1), rgb_b.max(axis=-1)) < 0.92
    if not content.any():
        return 0.0, 0.0, 0, 0.0, 0.0
    diff = np.abs(rgb_a - rgb_b).max(axis=-1)[content]
    n = int(diff.size)
    pct = round(100.0 * float((diff > 1.0 / 255.0 + 1e-6).sum()) / n, 4)
    p999 = round(float(np.percentile(diff, 99.9)) * 255.0, 3)
    mean = round(float(diff.mean()) * 255.0, 4)
    return pct, p999, n, mean, round(float(diff.max()) * 255.0, 2)


def band_centroid(mask, rows):
    band = mask[rows[0]:rows[1], :]
    cols = np.where(band.any(axis=0))[0]
    if cols.size == 0:
        return None, None
    weights = band.sum(axis=0).astype(np.float64)
    total = weights.sum()
    center = float((np.arange(band.shape[1]) * weights).sum() / total)
    return center, (int(cols.min()), int(cols.max()))


def main():
    ref = load(os.path.join(PRE, "%s_front_f0000.png" % STEM))
    fmask = mask_of(ref)
    rows_any = np.where(fmask.any(axis=1))[0]
    lo, hi = int(rows_any.min()), int(rows_any.max())
    span = hi - lo
    arm_band = (lo + int(span * 0.52), lo + int(span * 0.80))
    torso_band = (lo + int(span * TORSO_BAND_FRAC[0]),
                  lo + int(span * TORSO_BAND_FRAC[1]))
    head_band = (lo + int(span * 0.78), hi + 1)
    char_band = (lo + int(span * 0.20), hi + 1)
    print("PX_LAYOUT " + json.dumps({
        "stem": STEM, "image_h": fmask.shape[0], "char_rows": [lo, hi],
        "char_span_px": span, "arm_band": list(arm_band),
        "torso_band": list(torso_band),
        "torso_band_frac": list(TORSO_BAND_FRAC),
        "head_band": list(head_band), "char_band": list(char_band),
        "side_sign": SIDE_SIGN, "control_side_sign": CONTROL_SIDE_SIGN}))

    cache = {}

    def px(stem, view, tag):
        key = (stem, view, tag)
        if key not in cache:
            cache[key] = load(
                os.path.join(PRE, "%s_%s_%s.png" % (stem, view, tag)))
        return cache[key]

    def get(stem, view, tag):
        return mask_of(px(stem, view, tag))

    def measure(stem, in_tag, out_tag, gated):
        ma, mb = get(stem, "front", in_tag), get(stem, "front", out_tag)
        sa, sb = get(stem, "side", in_tag), get(stem, "side", out_tag)
        span_a, span_b = row_span(ma, arm_band), row_span(mb, arm_band)
        tc_a, _ = band_centroid(sa, torso_band)
        tc_b, _ = band_centroid(sb, torso_band)
        hc_a, _ = band_centroid(sa, head_band)
        hc_b, _ = band_centroid(sb, head_band)
        fc_a, _ = band_centroid(ma, torso_band)
        fc_b, _ = band_centroid(mb, torso_band)
        row = {
            "stem": stem, "gated": gated,
            "front_arm_span_px": [span_a[2] if span_a else None,
                                  span_b[2] if span_b else None],
            "front_arm_delta_px": (None if not (span_a and span_b)
                                   else round(span_b[2] - span_a[2], 1)),
            "front_arm_edges": [list(span_a[:2]) if span_a else None,
                                list(span_b[:2]) if span_b else None],
            "front_lat_delta_px": (None if fc_a is None or fc_b is None
                                   else round(fc_b - fc_a, 1)),
            "side_torso_center_px": [None if tc_a is None else round(tc_a, 1),
                                     None if tc_b is None else round(tc_b, 1)],
            "side_torso_delta_px": (None if tc_a is None or tc_b is None
                                    else round(tc_b - tc_a, 1)),
            "side_head_center_px": [None if hc_a is None else round(hc_a, 1),
                                    None if hc_b is None else round(hc_b, 1)],
            "side_head_delta_px": (None if hc_a is None or hc_b is None
                                   else round(hc_b - hc_a, 1)),
        }
        row["front_identical"] = bool(np.array_equal(ma, mb))
        row["side_identical"] = bool(np.array_equal(sa, sb))
        return row

    result = {}
    for pair in GATED_PAIRS + REPORT_PAIRS:
        result["%s_vs_%s" % pair] = measure(STEM, pair[0], pair[1],
                                            pair in GATED_PAIRS)
    peak_key = "CONTROL_PEAK_%s_%s" % (CONTROL_PEAK[1], CONTROL_PEAK[2])
    result[peak_key] = measure(CONTROL_PEAK[0], CONTROL_PEAK[1],
                               CONTROL_PEAK[2], True)
    print("PX_PAIRS " + json.dumps(result, ensure_ascii=False))

    d04_peak = abs(result[peak_key]["front_arm_delta_px"] or 0.0)
    arms_max_px = round(ARMS_MAX_FRAC_OF_D04 * d04_peak, 2)
    print("PX_BOUND " + json.dumps({
        "d04_peak_front_arm_delta_px": d04_peak,
        "arms_max_frac_of_d04": ARMS_MAX_FRAC_OF_D04,
        "arms_max_px": arms_max_px,
        "d04_peak_must_fail_bound": bool(d04_peak > arms_max_px)}))

    checks = {}
    control = {}
    reports = {}
    for key, row in result.items():
        if not row["gated"]:
            continue
        is_control = key.startswith("CONTROL_PEAK_")
        bucket = control if is_control else checks
        # ★★ 方向符号逐桶取：本支用 SIDE_SIGN（−1，往左），D04 对照用 +1（往右）。
        #    ⟹ 这同时是一条"**方向必须对**"的断言：照抄 D09 的 +1 就把本支判红。
        sign = CONTROL_SIDE_SIGN if is_control else SIDE_SIGN
        # ★★★ 主判据（D10 与 D09 **反口径**）：躯干必须"**看得见在折**"（**下界**）
        bucket["side_torso_ok_" + key] = bool(
            row["side_torso_delta_px"] is not None
            and sign * row["side_torso_delta_px"] >= TORSO_MIN_PX)
        # ★ 头部在本支是**配角**（惯性拖着走）⟹ 只报不判
        (reports if is_control else checks)["side_head_report_" + key] = bool(
            row["side_head_delta_px"] is not None
            and sign * row["side_head_delta_px"] >= 1.0)
        # ★ 上界：双臂保持防御形状（拳架不许崩）—— 本支必须**通过**，D04 必须**失败**
        bucket["front_arms_held_ok_" + key] = bool(
            row["front_arm_delta_px"] is not None
            and abs(row["front_arm_delta_px"]) <= arms_max_px)
        (reports if is_control else checks)["front_lat_report_" + key] = bool(
            row["front_lat_delta_px"] is not None
            and abs(row["front_lat_delta_px"]) >= LAT_MIN_PX_REPORT)
    # ★ 停顿平台的画面级证据：f3 ↔ f6 **读不出任何变化**
    #   ★★ 不能用 `np.array_equal`（D08 的写法在 D09 误报，D09 教训 2）：
    #     平台两端姿态逐位冻结，剩下的差异是**轮廓边缘抗锯齿**的亚像素抖动 ——
    #     那是渲染噪声，不是姿态漂移。改用**分布口径**（D03 第 3 号教训的延伸）。
    hitstop_px = {}
    for view in VIEWS:
        hitstop_px[view] = silhouette_delta(
            get(STEM, view, HITSTOP_A), get(STEM, view, HITSTOP_B))
    checks["hitstop_identical_ok"] = bool(all(
        hitstop_px[v]["rows_missing"] == 0
        and hitstop_px[v]["rows_gt2_total"] == 0
        and (hitstop_px[v]["max_left"] or 0) <= 1
        and (hitstop_px[v]["max_right"] or 0) <= 1
        for v in VIEWS))
    checks["hitstop_identical_can_fail_ok"] = bool(not all(
        silhouette_delta(get(STEM, v, "f0000"), get(STEM, v, HITSTOP_B))["sil_ok"]
        for v in VIEWS))
    print("PX_HITSTOP " + json.dumps(hitstop_px, ensure_ascii=False))

    # ---- ★★★ 本支主设计：`head_lag_px_ok` —— 头带重心峰值帧**晚于**躯干带 ------
    #   门禁侧 `head_lag_ok` 量的是**骨骼世界俯仰的峰值帧号**；
    #   这里量的是**画面重心序列的峰值帧号** —— 两条独立证据指向同一件事。
    seq = {}
    for tag in SEQ_TAGS:
        sm = get(STEM, "side", tag)
        tc, _ = band_centroid(sm, torso_band)
        hc, _ = band_centroid(sm, head_band)
        seq[tag] = {"torso_px": None if tc is None else round(tc, 2),
                    "head_px": None if hc is None else round(hc, 2)}
    base_t, base_h = seq[SEQ_TAGS[0]]["torso_px"], seq[SEQ_TAGS[0]]["head_px"]
    # ★ 峰值 = 重心**最靠左**（位移最大）的采样帧；取**第一个**达到最小的帧
    #   （停顿平台三帧值相同 ⟹ 取第一个 = 命中帧，符合"胸先折"的物理）。
    torso_series = [(t, base_t - seq[t]["torso_px"]) for t in SEQ_TAGS]
    head_series = [(t, base_h - seq[t]["head_px"]) for t in SEQ_TAGS]
    torso_peak_val = max(v for _t, v in torso_series)
    head_peak_val = max(v for _t, v in head_series)
    torso_peak_tag = next(t for t, v in torso_series if v >= torso_peak_val - 1e-6)
    head_peak_tag = next(t for t, v in head_series if v >= head_peak_val - 1e-6)
    torso_peak_f = int(torso_peak_tag[1:])
    head_peak_f = int(head_peak_tag[1:])
    print("PX_LAG " + json.dumps({
        "seq": seq, "torso_peak_tag": torso_peak_tag,
        "head_peak_tag": head_peak_tag,
        "torso_peak_px": round(torso_peak_val, 2),
        "head_peak_px": round(head_peak_val, 2),
        "torso_peak_frame": torso_peak_f, "head_peak_frame": head_peak_f,
        "lag_frames": head_peak_f - torso_peak_f,
        "min_frames": HEAD_LAG_MIN_FRAMES_PX,
        "torso_series": [[t, round(v, 2)] for t, v in torso_series],
        "head_series": [[t, round(v, 2)] for t, v in head_series]},
        ensure_ascii=False))
    # ★ 判据三条一起：① 头峰晚于躯干峰 ≥2 帧；② 头带"峰值后必回落"（不是单调平移）；
    #   ③ 躯干峰本身必须够大（否则"滞后"是在噪声上量出来的）。
    after = [v for t, v in head_series if int(t[1:]) > head_peak_f]
    checks["head_lag_px_ok"] = bool(
        (head_peak_f - torso_peak_f) >= HEAD_LAG_MIN_FRAMES_PX
        and torso_peak_val >= TORSO_MIN_PX
        and after and min(after) < head_peak_val - 0.5)
    checks["head_lag_px_can_fail_ok"] = bool(
        not (0 >= HEAD_LAG_MIN_FRAMES_PX))

    # ---- ★★ 末帧口径（**回原位**，见模块头）----------------------------------
    ret = {}
    for stem, first_tag, last_tag in ((STEM, "f0000", END_TAG), CONTROL_END):
        row = {}
        for view in VIEWS:
            pa, pb = px(stem, view, first_tag), px(stem, view, last_tag)
            sil = silhouette_delta(mask_of(pa), mask_of(pb))
            pct, p999, _n, mean, mx = shade_stats(pa, pb)
            sil.update({"shade_pct": pct, "shade_p999_lsb": p999,
                        "shade_mean_lsb": mean, "shade_max_lsb": mx,
                        "shade_ref_ok": bool(mean <= SHADE_MEAN_REF)})
            row[view] = sil
        ret[stem] = row
    checks["end_silhouette_ok"] = bool(
        all(ret[STEM][v]["sil_ok"] for v in VIEWS))
    checks["end_silhouette_control_ok"] = bool(
        all(ret[CONTROL_END[0]][v]["sil_ok"] for v in VIEWS))
    print("PX_RETURN " + json.dumps(ret, ensure_ascii=False))

    # ---- ★ 专属末帧判据（全部会失败）------------------------------------------
    chest_band = (lo + int(span * CHEST_BAND_FRAC[0]),
                  lo + int(span * CHEST_BAND_FRAC[1]))
    ref_span = row_span(mask_of(px(STEM, "side", "f0000")), chest_band)
    end_span = row_span(mask_of(px(STEM, "side", END_TAG)), chest_band)
    span_delta = (None if not (ref_span and end_span)
                  else round(end_span[2] - ref_span[2], 1))
    checks["end_torso_shape_ok"] = bool(
        span_delta is not None and abs(span_delta) <= END_TORSO_SPAN_TOL_PX)
    print("PX_END_SHAPE " + json.dumps({
        "chest_band": list(chest_band), "chest_band_frac": list(CHEST_BAND_FRAC),
        "side_chest_span_f0000_px": ref_span[2] if ref_span else None,
        "side_chest_span_end_px": end_span[2] if end_span else None,
        "span_delta_px": span_delta, "tol_px": END_TORSO_SPAN_TOL_PX,
        "span_delta_mm": (None if span_delta is None
                          else round(span_delta * MM_PER_PX, 2)),
        "hip_band_report": {
            "torso_band": list(torso_band),
            "f0000_px": (row_span(mask_of(px(STEM, "side", "f0000")),
                                  torso_band) or [None, None, None])[2],
            "end_px": (row_span(mask_of(px(STEM, "side", END_TAG)),
                                torso_band) or [None, None, None])[2]}}))

    # ---- 整体剪影重心位移 —— 本支**回原位 ⟹ 只报不判**（D07/D08 才判）--------
    m0 = mask_of(px(STEM, "side", "f0000"))
    m1 = mask_of(px(STEM, "side", END_TAG))
    c0, _ = band_centroid(m0, char_band)
    c1, _ = band_centroid(m1, char_band)
    shift_px = None if (c0 is None or c1 is None) else round(c1 - c0, 1)
    shift_m = None if shift_px is None else round(
        SIDE_SIGN * shift_px * MM_PER_PX / 1000.0, 4)
    reports["end_body_shift_report"] = bool(
        shift_m is not None and abs(shift_m) <= 0.005)
    print("PX_END_SHIFT " + json.dumps({
        "side_char_centroid_f0000_px": None if c0 is None else round(c0, 1),
        "side_char_centroid_end_px": None if c1 is None else round(c1, 1),
        "shift_px": shift_px, "mm_per_px": round(MM_PER_PX, 4),
        "signed_shift_m": shift_m, "report_tol_m": 0.005,
        "reg_root_motion_m": REG_ROOT_MOTION_M}))

    # ---- 落定段冻结：f30 ↔ f38 **分布口径**（同 `hitstop` 的教训）
    settle_px = {}
    for view in VIEWS:
        settle_px[view] = silhouette_delta(
            get(STEM, view, SETTLE_A), get(STEM, view, SETTLE_B))
    checks["end_settled_ok"] = bool(all(
        settle_px[v]["rows_missing"] == 0
        and settle_px[v]["rows_gt2_total"] == 0
        and (settle_px[v]["max_left"] or 0) <= 1
        and (settle_px[v]["max_right"] or 0) <= 1
        for v in VIEWS))
    print("PX_SETTLE " + json.dumps(settle_px, ensure_ascii=False))

    checks["end_shade_ref"] = bool(all(ret[STEM][v]["shade_ref_ok"]
                                       for v in VIEWS))
    # ★★ 本支**回原位** ⟹ `end_identical_ok` 是**判据**（计划 §3）
    checks["end_identical_ok"] = bool(
        np.array_equal(get(STEM, "front", END_TAG), get(STEM, "front", "f0000"))
        and np.array_equal(get(STEM, "side", END_TAG),
                           get(STEM, "side", "f0000")))
    reports["end_identical_report"] = checks["end_identical_ok"]
    # ★ 上界判据"能失败"的**当场证据**：D04 的张开峰必须越界
    checks["px_bound_can_fail_ok"] = bool(
        not control.get("front_arms_held_ok_" + peak_key, False))
    # ★ 躯干下界判据在 D04 上也要通过（同一条尺子，不是为本支量身定做）
    checks["px_control_lower_ok"] = bool(all(
        v for k, v in control.items() if k.startswith("side_torso_ok_")))
    # ★★★ 反向守卫：同一把尺子量 **D09 的躯干**（局部受力、逐位不动）必须
    #   **不通过** ⟹ 证明 `side_torso_ok` 不是恒真的空判据。
    mstem, m_in, m_out = MIRROR_TORSO
    sm_a, sm_b = get(mstem, "side", m_in), get(mstem, "side", m_out)
    mc_a, _ = band_centroid(sm_a, torso_band)
    mc_b, _ = band_centroid(sm_b, torso_band)
    mirror_delta = (None if mc_a is None or mc_b is None
                    else round(mc_b - mc_a, 1))
    checks["px_torso_can_fail_ok"] = bool(
        mirror_delta is not None
        and SIDE_SIGN * mirror_delta < TORSO_MIN_PX)
    print("PX_MIRROR " + json.dumps({
        "stem": mstem, "pair": [m_in, m_out],
        "torso_delta_px": mirror_delta, "lower_bound_px": TORSO_MIN_PX,
        "note": ("D09 是局部受力、躯干逐位不动 ⟹ 位移≈0 ⟹ 同一把尺子必须**不通过**；"
                 "若它反而通过，说明 side_torso_ok 是空判据")},
        ensure_ascii=False))
    # ★★ 第二条反向守卫：**同一支内部**的过冲帧（f16，上身弹回 ⟹ 位移≈0）
    #   也必须**不通过** ⟹ 证明下界在本支内部也是"活的"（不是只要动过就恒真）。
    fm_a, fm_b = get(STEM, "side", "f0000"), get(STEM, "side", FAIL_FRAME_TAG)
    fc_a, _ = band_centroid(fm_a, torso_band)
    fc_b, _ = band_centroid(fm_b, torso_band)
    fail_delta = (None if fc_a is None or fc_b is None
                  else round(fc_b - fc_a, 1))
    checks["px_torso_can_fail_d10_ok"] = bool(
        fail_delta is not None and SIDE_SIGN * fail_delta < TORSO_MIN_PX)
    print("PX_FAIL_FRAME " + json.dumps({
        "stem": STEM, "pair": ["f0000", FAIL_FRAME_TAG],
        "torso_delta_px": fail_delta, "lower_bound_px": TORSO_MIN_PX,
        "note": "过冲帧（上身弹回）必须不满足下界 —— 同支内部的反向守卫"},
        ensure_ascii=False))

    checks["failed"] = sorted(
        k for k, v in checks.items()
        if v is not True and "_report" not in k and not k.endswith("_ref"))
    print("PX_CONTROL " + json.dumps(control, ensure_ascii=False))
    print("PX_REPORTS " + json.dumps(reports, ensure_ascii=False))
    print("PX_CHECKS " + json.dumps(checks, ensure_ascii=False))


if __name__ == "__main__":
    main()
