"""probe_d06_pixels —— 把 D06 `Hit_Light_B` 的判据数值换算成**画面像素**。

（由 `probe_d05_pixels.py` 派生；D06 计划 §3 要求「改名前先复制 → `probe_d06_pixels.py`」。）

背景（D03 第 3 号教训）：
    判据数值 ≠ 观众看到的轮廓位移；头绕颈旋转时轮廓中心只走一半。
    ⟹ 凡是"位移/张开类"的语义判据，落定前**必须**做一次
       「判据数值 → 画面像素」复核（1 mm ≈ 0.556 px）。

═══ D06 与 D05 的画面判据**符号是反的**（★ 本支头号陷阱）═══
    D05「正面轻受击」：上身被往**身后**推 ⟹ 侧视图轮廓重心**右移**（图像右 = +Y = 身后）。
    D06「背面轻受击」：上身被往**前**折 ⟹ 侧视图轮廓重心**左移**。
    ⟹ 侧视头部 / 躯干的下界判据必须**取负**（`SIDE_SIGN = −1`），
       并且这本身就构成一条"**方向必须为左**"的断言 ——
       若有人把符号翻漏了（做出"正面受击"），该判据会**立刻变红**，
       而不是"方向做反也能过 8 px 下界"。
    对照组 D04（破防·后仰）用 `CONTROL_SIDE_SIGN = +1`（它的正确方向是右移），
    这样同一条下界判据在 D04 上依然通过 ⟹ 尺子不是为 D06 量身定做。

坐标约定（与 `anim_lib` 一致）：+Y = 角色身后，正面朝 −Y。
侧视相机在 (+4.2, 0, 0.92) 看向原点 ⟹ 图像**右方 = +Y = 身后的方向**。
前视相机看向 −Y ⟹ 图像右方 = −X = 角色**右手侧** ⟹ 侧移/偏转是**横向重心**。

判据的**适用域**：门禁只挂在 `press ≡ 1` 的帧上（本支 f3 ~ f5）。
    恢复段的帧（f12 / f24）**只报不判**。

画面判据（全部会失败）：
    `side_head_ok_*`       侧视头部带重心**左**移 ≥ `SIDE_MIN_PX`（前折下界）
    `side_torso_ok_*`      侧视躯干带重心**左**移 ≥ `TORSO_MIN_PX`（前折下界）
    `front_hit_visible_ok_*` 前视手臂带宽度增量 |Δ| ≥ `FRONT_MIN_PX`（被打要看得见）
    `front_arms_held_ok_*` 前视手臂带宽度增量 ≤ `ARMS_MAX_PX`（**上界**：保持防御）
    `hitstop_identical_ok` 停顿平台两端（f3 / f5）像素掩膜**逐位相同**
    `end_silhouette_ok`    f0 ↔ f24 逐行剪影分布口径
    `px_bound_can_fail_ok` 上界"能失败"的当场证据（D04 的张开峰必须越界）
    `px_control_lower_ok`  同一条下界判据在 D04 上也通过

只报不判：着色差（亚像素法线现象）、`end_identical_report`、剪影/长宽比、前视横向重心。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d06_pixels.py
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
STEM = "hitlightb"
# ★ 门禁对：两侧都落在 `press ≡ 1` 的停顿平台内（本支 IMPACT=3、HOLD_END=5）
GATED_PAIRS = [("f0000", "f0003"), ("f0000", "f0005")]
REPORT_PAIRS = [("f0000", "f0012"), ("f0000", "f0024")]
VIEWS = ("front", "side")

# ---- ★★ 方向符号（本支头号陷阱）：D06 前折 ⟹ 侧视重心**左**移 ----------------
SIDE_SIGN = -1.0          # D06：图像右 = +Y = 身后 ⟹ "往前" = 往左
CONTROL_SIDE_SIGN = 1.0   # D04（破防·后仰）：正确方向是往右 ⟹ 尺子同一把

# ---- 阈值（下界类：幅度必须"读得出来"）--------------------------------------
SIDE_MIN_PX = 8.0      # 计划 §5：幅度下界换算后 ≥8 px（头/胸）
TORSO_MIN_PX = 4.0     # 躯干幅度是头的一半量级（头绕颈放大）
FRONT_MIN_PX = 8.0     # 同一条 8 px 规则，用在前视"手臂带被撑开"上
# ---- 阈值（上界类：必须"读不出重击"）----------------------------------------
# ★★ 上界用**跨设计标定**：同一把尺子量 D04 的**张开峰**（f0 ↔ f4），
#   得 `d04_peak_px`；本支上界 = `ARMS_MAX_FRAC_OF_D04 × d04_peak_px`。
#   ⟹ 同一条判据在 D06 上必须**通过**、在 D04 上必须**失败**（"能失败"由 D04 当场证明）。
#   实测 D04 = 242 px ⟹ 上界 24.2 px。
ARMS_MAX_FRAC_OF_D04 = 0.10
# ---- 前视横向位移：**只报不判**（适用域问题，不是动画不达标）-----------------
LAT_MIN_PX_REPORT = 1.0
# ---- 「回到零位」的画面判据（分布口径，非逐位相同）---------------------------
END_SIL_PX = 2.0
END_ROWS_GT2_MAX = 3
SHADE_MEAN_REF = 0.05
# ★ 对照组 = **D04**：`CONTROL_PEAK` 取它的**张开峰**（f0 ↔ f4）；
#   `CONTROL_END` 取它的**回零对**，用于剪影分布口径的标定。
CONTROL_PEAK = ("guardbreak", "f0000", "f0004")
CONTROL_END = ("guardbreak", "f0000", "f0060")


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
    torso_band = (lo + int(span * 0.45), lo + int(span * 0.72))
    head_band = (lo + int(span * 0.78), hi + 1)
    print("PX_LAYOUT " + json.dumps({
        "stem": STEM, "image_h": fmask.shape[0], "char_rows": [lo, hi],
        "char_span_px": span, "arm_band": list(arm_band),
        "torso_band": list(torso_band), "head_band": list(head_band),
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
        # 前视横向重心（只报）
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
    # ★ 对照：同一把尺子量 D04 的**张开峰**（标定上界）与**回零对**（剪影口径）
    peak_key = "CONTROL_PEAK_%s_%s" % (CONTROL_PEAK[1], CONTROL_PEAK[2])
    result[peak_key] = measure(CONTROL_PEAK[0], CONTROL_PEAK[1],
                               CONTROL_PEAK[2], True)
    print("PX_PAIRS " + json.dumps(result, ensure_ascii=False))

    # ---- 上界由 D04 张开峰**当场标定** ----------------------------------------
    d04_peak = abs(result[peak_key]["front_arm_delta_px"] or 0.0)
    arms_max_px = round(ARMS_MAX_FRAC_OF_D04 * d04_peak, 2)
    print("PX_BOUND " + json.dumps({
        "d04_peak_front_arm_delta_px": d04_peak,
        "arms_max_frac_of_d04": ARMS_MAX_FRAC_OF_D04,
        "arms_max_px": arms_max_px,
        "front_min_px": FRONT_MIN_PX,
        "d04_peak_must_fail_bound": bool(d04_peak > arms_max_px)}))

    checks = {}
    control = {}
    reports = {}
    for key, row in result.items():
        if not row["gated"]:
            continue
        is_control = key.startswith("CONTROL_PEAK_")
        bucket = control if is_control else checks
        # ★★ 方向符号逐桶取：D06 用 SIDE_SIGN（−1，往左），D04 对照用 +1（往右）。
        #    ⟹ 这同时是一条"**方向必须对**"的断言：符号翻漏了就把 D06 判红。
        sign = CONTROL_SIDE_SIGN if is_control else SIDE_SIGN
        bucket["side_head_ok_" + key] = bool(
            row["side_head_delta_px"] is not None
            and sign * row["side_head_delta_px"] >= SIDE_MIN_PX)
        bucket["side_torso_ok_" + key] = bool(
            row["side_torso_delta_px"] is not None
            and sign * row["side_torso_delta_px"] >= TORSO_MIN_PX)
        # ★ 下界：被打要看得见（D04 幅度更大 ⟹ 同一条应一并通过）
        bucket["front_hit_visible_ok_" + key] = bool(
            row["front_arm_delta_px"] is not None
            and abs(row["front_arm_delta_px"]) >= FRONT_MIN_PX)
        # ★ 上界：双臂保持防御形状 —— D06 必须**通过**，D04 必须**失败**
        bucket["front_arms_held_ok_" + key] = bool(
            row["front_arm_delta_px"] is not None
            and abs(row["front_arm_delta_px"]) <= arms_max_px)
        (reports if is_control else checks)["front_lat_report_" + key] = bool(
            row["front_lat_delta_px"] is not None
            and abs(row["front_lat_delta_px"]) >= LAT_MIN_PX_REPORT)
    # ★ 停顿平台的画面级证据：f3 与 f5 **逐位相同**
    checks["hitstop_identical_ok"] = bool(
        np.array_equal(get(STEM, "front", "f0003"), get(STEM, "front", "f0005"))
        and np.array_equal(get(STEM, "side", "f0003"),
                           get(STEM, "side", "f0005")))

    # ---- 末帧返回零位：分布口径（与 D04 同一套判据）---------------------------
    ret = {}
    for stem, first_tag, last_tag in ((STEM, "f0000", "f0024"),
                                      CONTROL_END):
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
    print("PX_RETURN " + json.dumps(ret, ensure_ascii=False))

    checks["end_silhouette_ok"] = bool(all(ret[STEM][v]["sil_ok"]
                                           for v in VIEWS))
    checks["end_shade_ref"] = bool(all(ret[STEM][v]["shade_ref_ok"]
                                       for v in VIEWS))
    checks["end_identical_report"] = bool(
        np.array_equal(get(STEM, "front", "f0024"),
                       get(STEM, "front", "f0000"))
        and np.array_equal(get(STEM, "side", "f0024"),
                           get(STEM, "side", "f0000")))
    # ★ 上界判据"能失败"的**当场证据**：D04 的张开峰必须越界
    checks["px_bound_can_fail_ok"] = bool(
        not control.get("front_arms_held_ok_" + peak_key, False))
    # ★ 下界判据在 D04 上也要通过（同一条尺子，不是为 D06 量身定做）
    checks["px_control_lower_ok"] = bool(all(
        v for k, v in control.items()
        if k.startswith("side_") or k.startswith("front_hit_visible_")))
    checks["failed"] = sorted(
        k for k, v in checks.items()
        if v is not True and "_report" not in k and not k.endswith("_ref"))
    print("PX_CONTROL " + json.dumps(control, ensure_ascii=False))
    print("PX_REPORTS " + json.dumps(reports, ensure_ascii=False))
    print("PX_CHECKS " + json.dumps(checks, ensure_ascii=False))


if __name__ == "__main__":
    main()
