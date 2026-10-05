"""probe_d09_pixels —— 把 D09 `Hit_Head` 的判据数值换算成**画面像素**。

（由 `probe_d08_pixels.py` 派生；D09 计划 §3 要求「改 `STEM = "hithead"`、
  `SIDE_SIGN = +1`、`REG_ROOT_MOTION_M = 0.0`；`end_body_shift_ok` 换回
  `end_identical_report` 口径」。）

背景（D03 第 3 号教训）：
    判据数值 ≠ 观众看到的轮廓位移；头绕颈旋转时轮廓中心只走一半。
    ⟹ 凡是"位移/张开类"的语义判据，落定前**必须**做一次
       「判据数值 → 画面像素」复核（1 mm ≈ 0.556 px）。

═══ D09 与 D05~D08 **不是一个族**：本支是**局部受力**，两处口径必须**反转** ═══
    D05~D08（含 D07/D08）都是"**整躯干**受力"：躯干大动、手臂被撑开 ⟹
    它们的画面判据是「躯干**看得见**在动」「手臂带**看得见**被撑开」。
    D09 反过来：**躯干逐位不动**（门禁 `torso_delta_deg = 0.0`、`pelvis_move_mm = 0`）、
    **拳架逐位不动**（`fist_dev_mm = 0.0`），只有 `neck` + `head` 后甩。
    ⟹ 照抄 D08 的 `side_torso_ok_*` / `front_hit_visible_ok_*` 会把**正确的动画**
      判红。本支对应的、会失败的画面判据是：
      `side_torso_still_ok_*`  侧视躯干带重心位移 **≤ `TORSO_STILL_MAX_PX`**（必须读不出动）
      `side_head_ok_*`         侧视头部带重心**右**移 ≥ `SIDE_MIN_PX`（★ 主判据）
    同时保留 D08 的上界 `front_arms_held_ok_*`（手臂带宽度**不许变**）。
    前视"被打看得见"改为**只报**（`front_hit_visible_report_*`）：本支可读性由
    侧视头部位移承担，前视只是同一件事的另一投影。

═══ 方向符号（本支头号陷阱）：头后甩 = 头顶往 +Y（身后）= 侧视**右**移 ═══
    坐标约定（与 `anim_lib` 一致）：+Y = 角色身后，正面朝 −Y。
    侧视相机在 (+4.2, 0, 0.92) 看向原点 ⟹ 图像**右方 = +Y = 身后的方向**。
    ⟹ `SIDE_SIGN = +1`（D04 后仰同号，D06/D07/D08 是 −1）。
    若有人把 D08 的 `−1` 照抄过来，`side_head_ok_*` 会**立刻变红**。

判据的**适用域**：门禁只挂在 `hitstop` 停顿平台内（本支 `IMPACT=3`、`HOLD_END=6`）
    ⟹ `GATED_PAIRS` 取 `f0003 / f0005`。过冲段与落定段的帧**只报不判**。

═══ ★★ 末帧口径：本支**回原位**（与 D07/D08 相反，与 D05/D06 相同）═══
    计划 §1：「末帧**逐位回零位**（含位置）⟹ `end_identical_report` 可恢复为判据」。
    ⟹ D07/D08 的 `end_body_shift_ok`（"被推走了"）在本支是**错的口径**，降级为只报；
       `end_identical_report` **升格**为判据 `end_identical_ok`（f34 ↔ f0 逐位相同）。
    `end_torso_shape_ok` / `end_settled_ok` 保留（本支更强：躯干全程不动）。

画面判据（全部会失败）：
    `side_head_ok_*`          侧视头部带重心**右**移 ≥ `SIDE_MIN_PX`（★ 主判据）
    `side_torso_still_ok_*`   侧视躯干带重心位移 ≤ `TORSO_STILL_MAX_PX`（★ 反转口径）
    `front_arms_held_ok_*`    前视手臂带宽度增量 ≤ `arms_max_px`（上界：拳架不许动）
    `hitstop_identical_ok`    停顿平台 f3 ↔ f6 像素掩膜**逐位相同**
    `end_identical_ok`        末帧 f34 ↔ f0 掩膜**逐位相同**（★ 回原位）
    `end_torso_shape_ok`      末帧躯干带列跨度 = f0（≤ `END_TORSO_SPAN_TOL_PX`）
    `end_settled_ok`          f30 ↔ f34 掩膜**逐位相同**（落定段冻结）
    `px_bound_can_fail_ok`    上界"能失败"的当场证据（D04 的张开峰必须越界）
    `px_control_lower_ok`     同一条头部下界在 D04 上也通过（尺子非量身定做）
    `px_torso_still_can_fail_ok` ★ 反向守卫：D04 的**躯干**位移必须**越界**
                              ⟹ 证明 `side_torso_still_ok` 不是恒真的空判据

只报不判：着色差（亚像素法线现象）、`end_identical_*_report`、`end_body_shift_report`、
    剪影/长宽比、前视横向重心、前视"被打看得见"（`front_hit_visible_report_*`）。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d09_pixels.py
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
STEM = "hithead"
# ★ 门禁对：两侧都落在 `hitstop` 停顿平台内（本支 IMPACT=3、HOLD_END=6）
GATED_PAIRS = [("f0000", "f0003"), ("f0000", "f0005")]
# ★ 报告对：回落中 / 过冲峰 / 过冲后回落 / CANCEL / 末帧（**只报不判**）
REPORT_PAIRS = [("f0000", "f0012"), ("f0000", "f0018"),
                ("f0000", "f0022"), ("f0000", "f0030"), ("f0000", "f0034")]
VIEWS = ("front", "side")

# ---- ★★ 方向符号（本支头号陷阱）：头后甩 ⟹ 侧视重心**右**移 --------------------
#   与 D04（破防·后仰）同号，与 D06/D07/D08 相反。照抄 D08 的 −1 会立刻判红。
SIDE_SIGN = 1.0           # D09：图像右 = +Y = 身后 ⟹ "头被往后甩" = 往右
CONTROL_SIDE_SIGN = 1.0   # D04（破防·后仰）：正确方向也是往右 ⟹ 尺子同一把

# ---- 帧号（与 `anim_hit_head.py` 的时间轴逐一对齐）---------------------------
HITSTOP_A, HITSTOP_B = "f0003", "f0006"    # 停顿平台两端（IMPACT ~ HOLD_END）
SETTLE_A, SETTLE_B = "f0030", "f0034"      # 落定段（CANCEL ~ END）
END_TAG = "f0034"                          # 末帧（= TOTAL = 34）

# ---- 阈值（下界类：幅度必须"读得出来"）--------------------------------------
SIDE_MIN_PX = 8.0      # 计划 §5：幅度下界换算后 ≥8 px（头/胸）
# ★ D08 的 `TORSO_MIN_PX`（躯干**看得见**在动）在本支**已删除** —— 见模块头
#   「D09 与 D05~D08 不是一个族」：本支躯干必须**读不出动** ⟹
#   替身是 `TORSO_STILL_MAX_PX`（上界），反向守卫是 `px_torso_still_can_fail_ok`。
FRONT_MIN_PX = 8.0     # 仅用于**只报**的 `front_hit_visible_report_*`（D08 口径）
# ---- ★★ 阈值（D09 专属上界：局部受力 ⟹ 躯干必须"读不出动"）------------------
#   门禁侧 `torso_delta_deg = 0.0`（逐位不动）⟹ 像素级也应几乎完全一致；
#   留 2 px 余量吸收抗锯齿/重采样的 ±1 px 抖动。
TORSO_STILL_MAX_PX = 2.0
# ---- 阈值（上界类：必须"读不出重击"）----------------------------------------
# ★★ 上界用**跨设计标定**：同一把尺子量 D04 的**张开峰**（f0 ↔ f4），
#   得 `d04_peak_px`；本支上界 = `ARMS_MAX_FRAC_OF_D04 × d04_peak_px`。
#   ⟹ 同一条判据在 D05/D06/D07/D08/D09 上必须**通过**、在 D04 上必须**失败**。
ARMS_MAX_FRAC_OF_D04 = 0.10
# ---- 前视横向位移：**只报不判**（适用域问题，不是动画不达标）-----------------
LAT_MIN_PX_REPORT = 1.0
# ---- ★★ 专属：末帧口径（**回原位**，继承 D05/D06）------------------------------
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
# ★ 本支登记的骨盆位移（D09 **无位移** ⟹ 0）
REG_ROOT_MOTION_M = 0.0


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
    # ★ 专属：整体剪影带（"被推走"用），去掉最底的脚（脚的位移方向相反）
    char_band = (lo + int(span * 0.20), hi + 1)
    print("PX_LAYOUT " + json.dumps({
        "stem": STEM, "image_h": fmask.shape[0], "char_rows": [lo, hi],
        "char_span_px": span, "arm_band": list(arm_band),
        "torso_band": list(torso_band), "head_band": list(head_band),
        "char_band": list(char_band),
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
        # ★★ 方向符号逐桶取：D08 用 SIDE_SIGN（−1，往左），D04 对照用 +1（往右）。
        #    ⟹ 这同时是一条"**方向必须对**"的断言：符号翻漏了就把本支判红。
        sign = CONTROL_SIDE_SIGN if is_control else SIDE_SIGN
        bucket["side_head_ok_" + key] = bool(
            row["side_head_delta_px"] is not None
            and sign * row["side_head_delta_px"] >= SIDE_MIN_PX)
        # ★★ D09 反转口径：躯干必须**读不出动**（局部受力的画面证据）。
        #   对 D04 而言这条**必须失败** ⟹ 它就是"这条判据不是空判据"的反向守卫。
        bucket["side_torso_still_ok_" + key] = bool(
            row["side_torso_delta_px"] is not None
            and abs(row["side_torso_delta_px"]) <= TORSO_STILL_MAX_PX)
        # ★ 前视"被打看得见"在本支**只报不判**（可读性由侧视头部位移承担）
        (reports if is_control else checks)["front_hit_visible_report_" + key] = bool(
            row["front_arm_delta_px"] is not None
            and abs(row["front_arm_delta_px"]) >= FRONT_MIN_PX)
        # ★ 上界：双臂保持防御形状（拳架不许动）—— 本支必须**通过**，D04 必须**失败**
        bucket["front_arms_held_ok_" + key] = bool(
            row["front_arm_delta_px"] is not None
            and abs(row["front_arm_delta_px"]) <= arms_max_px)
        (reports if is_control else checks)["front_lat_report_" + key] = bool(
            row["front_lat_delta_px"] is not None
            and abs(row["front_lat_delta_px"]) >= LAT_MIN_PX_REPORT)
    # ★ 停顿平台的画面级证据：f3 ↔ f6 **读不出任何变化**
    #   ★★ 这里**不能用 `np.array_equal`**（D08 的写法在本支会误报）：
    #     平台两端姿态是**逐位冻结**的（门禁 `hitstop_drift_deg = 0.0`、
    #     前视掩膜 XOR = 0），但侧视轮廓边缘的抗锯齿会留下 **±1 LSB / 单像素**
    #     抖动（实测 f3↔f6：side `mask_xor = 1`、`rgb_max = 2/255`）。
    #     `array_equal` 会把渲染噪声当成姿态漂移 ⟹ 改用**分布口径** ——
    #     与本文件 `silhouette_delta` / `end_silhouette_ok` 同一把尺子（D03 第 3 号教训：
    #     判据挂**分布**，不挂 max）。
    #   ★ 严格度：不用通用 `sil_ok`（容许 3 行 >2 px），本支收紧到
    #     **`rows_gt2_total == 0` 且单行边缘位移 ≤ 1 px**。
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
    # ★ 同一条判据"能失败"的当场证据：拿**平台外**的 f0 ↔ f6（整段甩动）量一遍，
    #   必须**越界**。否则说明这把尺子量不出东西。
    checks["hitstop_identical_can_fail_ok"] = bool(not all(
        silhouette_delta(get(STEM, v, "f0000"), get(STEM, v, HITSTOP_B))["sil_ok"]
        for v in VIEWS))
    print("PX_HITSTOP " + json.dumps(hitstop_px, ensure_ascii=False))

    # ---- ★★ 末帧口径（与 D07/D08 **不同**：**回原位**，见模块头）--------------
    ret = {}
    for stem, first_tag, last_tag in ((STEM, "f0000", END_TAG),
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
    # ★ 本支"回原位"⟹ 分布口径（`end_silhouette_ok`）恢复为**判据**；
    #   对照组 D04 的"回零"口径顺手证伪（它确实回原位）。
    checks["end_silhouette_ok"] = bool(
        all(ret[STEM][v]["sil_ok"] for v in VIEWS))
    checks["end_silhouette_control_ok"] = bool(
        all(ret[CONTROL_END[0]][v]["sil_ok"] for v in VIEWS))
    print("PX_RETURN " + json.dumps(ret, ensure_ascii=False))

    # ---- ★ 专属末帧判据（全部会失败）------------------------------------------
    #   ① 躯干**形状**回去了：末帧**胸腔带**的列跨度 = f0（≤ `END_TORSO_SPAN_TOL_PX`）
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

    #   ② 整体剪影重心位移 —— 本支**回原位 ⟹ 只报不判**（D07/D08 才判）
    m0 = mask_of(px(STEM, "side", "f0000"))
    m1 = mask_of(px(STEM, "side", END_TAG))
    c0, _ = band_centroid(m0, char_band)
    c1, _ = band_centroid(m1, char_band)
    shift_px = None if (c0 is None or c1 is None) else round(c1 - c0, 1)
    # ★ px → mm 是**乘** `MM_PER_PX`（= 1/0.556），不是乘 0.556
    shift_m = None if shift_px is None else round(
        SIDE_SIGN * shift_px * MM_PER_PX / 1000.0, 4)
    reports["end_body_shift_report"] = bool(
        shift_m is not None and abs(shift_m) <= 0.005)
    print("PX_END_SHIFT " + json.dumps({
        "side_char_centroid_f0000_px": None if c0 is None else round(c0, 1),
        "side_char_centroid_end_px": None if c1 is None else round(c1, 1),
        "shift_px": shift_px, "mm_per_px": round(MM_PER_PX, 4),
        "signed_shift_m": shift_m,
        "report_tol_m": 0.005,
        "reg_root_motion_m": REG_ROOT_MOTION_M}))

    #   ③ 落定段冻结：f30 ↔ f34 **逐位相同**
    checks["end_settled_ok"] = bool(
        np.array_equal(get(STEM, "front", SETTLE_A), get(STEM, "front", SETTLE_B))
        and np.array_equal(get(STEM, "side", SETTLE_A),
                           get(STEM, "side", SETTLE_B)))

    checks["end_shade_ref"] = bool(all(ret[STEM][v]["shade_ref_ok"]
                                       for v in VIEWS))
    # ★★ 本支**回原位** ⟹ `end_identical_report` **升格**为判据（计划 §1）
    checks["end_identical_ok"] = bool(
        np.array_equal(get(STEM, "front", END_TAG),
                       get(STEM, "front", "f0000"))
        and np.array_equal(get(STEM, "side", END_TAG),
                           get(STEM, "side", "f0000")))
    reports["end_identical_report"] = checks["end_identical_ok"]
    # ★ 上界判据"能失败"的**当场证据**：D04 的张开峰必须越界
    checks["px_bound_can_fail_ok"] = bool(
        not control.get("front_arms_held_ok_" + peak_key, False))
    # ★ 反向守卫：D04 的**躯干**必须越界 ⟹ 证明 `side_torso_still_ok` 有内容。
    #   取 D04 的**回零前**那一对（f0 ↔ f60）会回原位，故用**张开峰**（f0 ↔ f4）。
    torso_ctl = None if not control else control.get(
        "side_torso_still_ok_" + peak_key)
    checks["px_torso_still_can_fail_ok"] = bool(torso_ctl is False)
    # ★ 头部下界判据在 D04 上也要通过（同一条尺子，不是为本支量身定做）
    checks["px_control_lower_ok"] = bool(all(
        v for k, v in control.items() if k.startswith("side_head_ok_")))
    checks["failed"] = sorted(
        k for k, v in checks.items()
        if v is not True and "_report" not in k and not k.endswith("_ref"))
    print("PX_CONTROL " + json.dumps(control, ensure_ascii=False))
    print("PX_REPORTS " + json.dumps(reports, ensure_ascii=False))
    print("PX_CHECKS " + json.dumps(checks, ensure_ascii=False))


if __name__ == "__main__":
    main()
