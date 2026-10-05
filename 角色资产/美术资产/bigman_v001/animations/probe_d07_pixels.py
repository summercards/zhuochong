"""probe_d07_pixels —— 把 D07 `Hit_Heavy_F` 的判据数值换算成**画面像素**。

（由 `probe_d06_pixels.py` 派生；D07 计划 §3 要求「复制后改名，只动 STEM /
  GATED_PAIRS / REPORT_PAIRS / SIDE_SIGN」。）

背景（D03 第 3 号教训）：
    判据数值 ≠ 观众看到的轮廓位移；头绕颈旋转时轮廓中心只走一半。
    ⟹ 凡是"位移/张开类"的语义判据，落定前**必须**做一次
       「判据数值 → 画面像素」复核（1 mm ≈ 0.556 px）。

═══ D07 与 D06 的画面判据**符号是反的**（★ 本支头号陷阱，与 D05 同号）═══
    D07「正面重受击」：上身被往**身后**推 ⟹ 侧视图轮廓重心**右移**（图像右 = +Y = 身后）。
    这正是 D05 的正确方向 ⟹ `SIDE_SIGN = +1`（与 D05 相同、与 D06 相反）。
    若有人把 D06 的 `−1` 照抄过来，该判据会**立刻变红**，而不是"方向做反也能过"。
    对照组 D04（破防·后仰）同样是右移 ⟹ 用 `CONTROL_SIDE_SIGN = +1`，
    尺子依然不是为 D07 量身定做。

坐标约定（与 `anim_lib` 一致）：+Y = 角色身后，正面朝 −Y。
侧视相机在 (+4.2, 0, 0.92) 看向原点 ⟹ 图像**右方 = +Y = 身后的方向**。
前视相机看向 −Y ⟹ 图像右方 = −X = 角色**右手侧** ⟹ 侧移/偏转是**横向重心**。

判据的**适用域**：门禁只挂在 `press ≡ 1` 的停顿平台内（本支 f4 ~ f8）。
    退步段与落定段的帧**只报不判**。

═══ ★★ 本支与 D05/D06 最大的一处口径变更：末帧**不回原位** ═══
    计划 §1 写死「后脚退 1 步、骨盆被推走 0.25 m」，且**登记 `root_motion_m`** ⟹
    末帧是"零位**形状** + 新站位"，世界位置**故意**不回来。
    ⟹ D05/D06 的 `end_silhouette_ok`（f0 ↔ 末帧剪影分布）在本支是**错的口径**
       （拿它判必然红 —— 这不是动画不达标，是判据适用域选错，D04 第 1 号教训）。
    换成两条**D07 专属**的、会失败的画面判据：
      `end_torso_shape_ok`   末帧躯干带的**列跨度**与 f0 相同（≤2 px）⟹ 形状回去了
      `end_body_shift_ok`    末帧整体剪影重心**右移**落在 [下界, 上界] 内⟹ 确实被推走了
    外加 `end_settled_ok`：f34 ↔ f42 像素掩膜**逐位相同**（落定段冻结，同 `hitstop` 口径）。

画面判据（全部会失败）：
    `side_head_ok_*`       侧视头部带重心**右**移 ≥ `SIDE_MIN_PX`（后仰下界）
    `side_torso_ok_*`      侧视躯干带重心**右**移 ≥ `TORSO_MIN_PX`（后仰下界）
    `front_hit_visible_ok_*` 前视手臂带宽度增量 |Δ| ≥ `FRONT_MIN_PX`（被打要看得见）
    `front_arms_held_ok_*` 前视手臂带宽度增量 ≤ `ARMS_MAX_PX`（**上界**：保持防御形状）
    `hitstop_identical_ok` 停顿平台内两张（f4 / f6）像素掩膜**逐位相同**
    `end_torso_shape_ok` / `end_body_shift_ok` / `end_settled_ok`  见上
    `px_bound_can_fail_ok` 上界"能失败"的当场证据（D04 的张开峰必须越界）
    `px_control_lower_ok`  同一条下界判据在 D04 上也通过

只报不判：着色差（亚像素法线现象）、`end_identical_report`、剪影/长宽比、前视横向重心。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d07_pixels.py
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
STEM = "hitheavyf"
# ★ 门禁对：两侧都落在 `press ≡ 1` 的停顿平台内（本支 IMPACT=4、HOLD_END=8）
GATED_PAIRS = [("f0000", "f0004"), ("f0000", "f0006")]
# ★ 报告对：起蹬后 / 退步中 / 落步 / 末帧（**只报不判**，见模块头适用域）
REPORT_PAIRS = [("f0000", "f0011"), ("f0000", "f0017"),
                ("f0000", "f0029"), ("f0000", "f0042")]
VIEWS = ("front", "side")

# ---- ★★ 方向符号（本支头号陷阱）：正面重受击 ⟹ 侧视重心**右**移 ----------------
#   与 D05 同号、与 D06 相反。照抄 D06 的 −1 会立刻把本支判红。
SIDE_SIGN = 1.0           # D07：图像右 = +Y = 身后 ⟹ "被往后推" = 往右
CONTROL_SIDE_SIGN = 1.0   # D04（破防·后仰）：同样右移 ⟹ 尺子同一把

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
# ---- ★★ D07 专属：末帧口径（**不是** D05/D06 的"回原位"）--------------------
#   ★ 比例尺方向（D07 新增的坑）：计划 §4 给的是「1 mm ≈ 0.556 px」⟹
#     **px → mm 要除以 0.556**（= 乘 1.7986），不是乘 0.556。
#     本支首轮就是在这里把 0.246 m 读成 0.076 m、把判据判红。
MM_PER_PX = 1.0 / 0.556
#   `end_torso_shape_ok`：末帧**胸腔带**的列跨度与 f0 相同 ⟹ 躯干**形状**回去了
#     ★ 带子必须只盖胸腔：`torso_band`（45%~72% 身高）是**髋/大腿**区，
#       末帧步距从 0.31 m 拉到 0.387 m ⟹ 它的跨度**本来就该变大**（实测 +16 px）。
#       那不是动画不达标，是判据适用域选错（D04 第 1 号教训）。
CHEST_BAND_FRAC = (0.70, 0.80)
END_TORSO_SPAN_TOL_PX = 2.0
#   `end_body_shift_ok`：整体剪影重心右移量必须落在带宽内。
#     下界：必须**读得出**被推走（0.18 m ⟹ 与登记 root_motion 0.25 m 同量级）。
#     上界：不能被推成"飞出去"（0.45 m ⟹ 与 `step_back_ok` 的 0.60 m 上界同源）。
END_SHIFT_MIN_M = 0.18
END_SHIFT_MAX_M = 0.45
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
    # ★ D07 专属：整体剪影带（"被推走"用），去掉最底的脚（脚的位移方向相反）
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
    # ★ 停顿平台的画面级证据：f4 与 f6 **逐位相同**（本支平台 = f4 ~ f8）
    checks["hitstop_identical_ok"] = bool(
        np.array_equal(get(STEM, "front", "f0004"), get(STEM, "front", "f0006"))
        and np.array_equal(get(STEM, "side", "f0004"),
                           get(STEM, "side", "f0006")))

    # ---- ★★ 末帧口径（D07 与 D05/D06 **不同**：不回原位，见模块头）------------
    #   `ret` 里的剪影分布口径对 **D04** 仍然适用（它回原位）⟹ 保留作对照；
    #   对 D07 只作**报告**，门禁改用下面两条专属判据。
    ret = {}
    for stem, first_tag, last_tag in ((STEM, "f0000", "f0042"),
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
    # ★ 对照组 D04 的"回零"口径仍是**判据**（它确实回原位 ⟹ 顺手证伪）
    checks["end_silhouette_control_ok"] = bool(
        all(ret[CONTROL_END[0]][v]["sil_ok"] for v in VIEWS))
    print("PX_RETURN " + json.dumps(ret, ensure_ascii=False))

    # ---- ★ D07 专属末帧判据（两条都会失败）------------------------------------
    #   ① 躯干**形状**回去了：末帧**胸腔带**的列跨度 = f0（≤ `END_TORSO_SPAN_TOL_PX`）
    #      ★ 用胸腔带，不用 `torso_band`（髋/大腿区 ⟹ 步距变了它本来就该变）
    chest_band = (lo + int(span * CHEST_BAND_FRAC[0]),
                  lo + int(span * CHEST_BAND_FRAC[1]))
    ref_span = row_span(mask_of(px(STEM, "side", "f0000")), chest_band)
    end_span = row_span(mask_of(px(STEM, "side", "f0042")), chest_band)
    span_delta = (None if not (ref_span and end_span)
                  else round(end_span[2] - ref_span[2], 1))
    checks["end_torso_shape_ok"] = bool(
        span_delta is not None and abs(span_delta) <= END_TORSO_SPAN_TOL_PX)
    print("PX_END_SHAPE " + json.dumps({
        "chest_band": list(chest_band), "chest_band_frac": list(CHEST_BAND_FRAC),
        "side_chest_span_f0000_px": ref_span[2] if ref_span else None,
        "side_chest_span_f0042_px": end_span[2] if end_span else None,
        "span_delta_px": span_delta, "tol_px": END_TORSO_SPAN_TOL_PX,
        "span_delta_mm": (None if span_delta is None
                          else round(span_delta * MM_PER_PX, 2)),
        "hip_band_report": {
            "torso_band": list(torso_band),
            "f0000_px": (row_span(mask_of(px(STEM, "side", "f0000")),
                                  torso_band) or [None, None, None])[2],
            "f0042_px": (row_span(mask_of(px(STEM, "side", "f0042")),
                                  torso_band) or [None, None, None])[2]}}))

    #   ② 整体剪影重心**右移**（被推走）—— 带宽口径：既不能"读不出"，也不能"飞出去"
    m0 = mask_of(px(STEM, "side", "f0000"))
    m1 = mask_of(px(STEM, "side", "f0042"))
    c0, _ = band_centroid(m0, char_band)
    c1, _ = band_centroid(m1, char_band)
    shift_px = None if (c0 is None or c1 is None) else round(c1 - c0, 1)
    # ★ px → mm 是**乘** `MM_PER_PX`（= 1/0.556），不是乘 0.556
    shift_m = None if shift_px is None else round(
        SIDE_SIGN * shift_px * MM_PER_PX / 1000.0, 4)
    checks["end_body_shift_ok"] = bool(
        shift_m is not None and END_SHIFT_MIN_M <= shift_m <= END_SHIFT_MAX_M)
    print("PX_END_SHIFT " + json.dumps({
        "side_char_centroid_f0000_px": None if c0 is None else round(c0, 1),
        "side_char_centroid_f0042_px": None if c1 is None else round(c1, 1),
        "shift_px": shift_px, "mm_per_px": round(MM_PER_PX, 4),
        "signed_shift_m": shift_m,
        "gate_m": [END_SHIFT_MIN_M, END_SHIFT_MAX_M],
        "reg_root_motion_m": 0.25}))

    #   ③ 落定段冻结：f34 ↔ f42 **逐位相同**
    checks["end_settled_ok"] = bool(
        np.array_equal(get(STEM, "front", "f0034"), get(STEM, "front", "f0042"))
        and np.array_equal(get(STEM, "side", "f0034"),
                           get(STEM, "side", "f0042")))

    checks["end_shade_ref"] = bool(all(ret[STEM][v]["shade_ref_ok"]
                                       for v in VIEWS))
    checks["end_identical_report"] = bool(
        np.array_equal(get(STEM, "front", "f0042"),
                       get(STEM, "front", "f0000"))
        and np.array_equal(get(STEM, "side", "f0042"),
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
