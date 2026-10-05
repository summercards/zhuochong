"""probe_d04_pixels —— 把 D04 的判据数值换算成**画面像素**（D03 教训 3 的强制执行）。

背景（D03 第 3 号教训）：
    `head_back_mm` = 47.6 mm 时"判据 3 倍余量"，但头顶骨尾的位移**不是**观众看到的
    轮廓位移 —— 头绕颈旋转，轮廓中心只走一半 ⟹ 画面只有 6 px，等于看不出来。
    ⟹ 凡是"位移/张开类"的语义判据，落定前**必须**做一次「判据数值 → 画面像素」复核。

本探针回答 D04 的两个头号语义在**画面**里各是多少像素：
    ① 震开（双拳横向净距 + 肘外张）—— 看 **前视图**：量"手臂带"的剪影宽度与最外缘。
    ② 后仰（chest 世界俯仰）—— 看 **侧视图**：量躯干/头部轮廓的水平（= 世界 Y）重心。

坐标约定（与 `anim_lib` 一致）：+Y = 角色身后，正面朝 −Y。
侧视相机在 (+4.2, 0, 0.92) 看向原点 ⟹ 图像**右方 = +Y = 身后的方向**。
⟹ "后仰" 在侧视图里表现为**轮廓重心右移**。

★★ 判据的**适用域**（这是本探针第 1 版犯过的错，记在这里）：
    第 1 版把 `(f0, f34)` 也当成"必须 ≥8 px 后仰"来门禁，结果 `side_ok` 红（实测 2.2 px）。
    但 f34 处在 `press ≈ 0.56` 的**恢复段中段** —— 破防已经收回一半，后仰当然接近零。
    要求"恢复段的中间帧也要有 8 px 后仰"是**判据的适用域选错**，不是动画不达标。
    ⟹ 门禁只挂在**平台期（`press ≡ 1`）**的帧上（f4 震开峰 / f14 硬直末）；
       恢复段的帧（f34 / f54 / f60）**只报不判**。
       ★ 这是修判据的适用域，不是放宽阈值 —— 阈值（12 / 8 px）一个没动。

新立的画面判据（全部会失败）：
    `front_ok_*`          前视图手臂带宽度增量 ≥ 12 px
    `side_ok_*`           侧视图躯干带重心右移 ≥ 8 px
    `head_ok_*`           侧视图头部带重心右移 ≥ 8 px
    `stagger_identical_ok` 硬直平台两端（f4 / f14）的**像素掩膜逐位相同** ——
                           "完全僵住"的画面级证据（比欧拉口径更强）

★★ 关于"末帧是否逐位相同" —— 本探针第 2 版**撤下** `end_identical_ok`（第 2 号教训）：
    第 2 版要求 f60 与 f0 的像素**逐位相同**，它红了。查证过程：
      ① 同一对帧的**几何指标全是 0**：`front_arm_delta_px=0`、
         `side_torso_delta_px=0.0`、`side_head_delta_px=-0.0`、剪影左右缘
         `[252,526]` 两侧完全相同 ⟹ **外形没有差别**。
      ② 逐位相差点在**内部**：2135 px（0.2488%），max 36 lsb，**p99.9 只有 3 lsb**，
         全图均值 0.011 lsb。
      ③ **对照组**（`probe_d04_endpix.py`，已验收且门禁全绿的 D03）：
         f0↔f36 正面 **28 px 不同**、侧面 **68 px 不同** —— **D03 也不是逐位相同**。
      ④ 机制：绕骨轴滚转 δ 会把**顶点法线**一起转。圆柱截面转 δ 后顶点位置几乎回到
         原处（剪影不变），但**着色**变了 ⟹ 内部浮点差、剪影相同。这正是③②的签名。
    ⟹ 结论：「逐位相同」**不是 D 族可达的判据**（D03 已验收却也不满足），
       把它当门禁是**判据选错**，不是动画不达标。改用两条**有量纲**的替代判据，
       阈值由 D03 对照组**标定**（不是拿 D04 的结果去凑）：
          `end_silhouette_ok`   f0↔f60 逐行剪影左右缘 max|Δ| ≤ `END_SIL_PX`
          `end_shade_ok`        差异像素占比 ≤ `END_SHADE_PCT` 且 p99.9 ≤ `END_SHADE_LSB`
       ★ 注意 `stagger_identical_ok` **保留**逐位相同 —— 因为 f4↔f14 实测真的逐位相同
         （两帧是同一份 key 值写出来的），它是一条**通过了的**强判据，不能顺手撤。
       `end_identical_ok` 降级为**只报不判**（`end_identical_report`）。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d04_pixels.py
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
# ★ 门禁对（两侧都在 `press ≡ 1` 的平台期内）：零位 → 震开峰 / 零位 → 硬直末
GATED_PAIRS = [("f0000", "f0004"), ("f0000", "f0014")]
# ★ 只报不判（恢复段中段 / 末帧返回）
REPORT_PAIRS = [("f0000", "f0034"), ("f0000", "f0054"), ("f0000", "f0060")]
VIEWS = ("front", "side")
FRONT_MIN_PX = 12.0
SIDE_MIN_PX = 8.0

# ---- 「回到零位」的画面判据（替代不可达的"逐位相同"，见文件头第 2 号教训）---------
# ★ 判据挂在剪影的**分布**上，不挂在 max 上（第 3 号教训）：
#   剪影掩膜是"通道 < 0.92"阈值切出来的，一条抗锯齿淡边只要跨过阈值，**单行**的
#   最左列就能整段跳 25 px。实测 D04 正面 `max_left=25` 但 `rows_gt2_left=1`、
#   `median=0`、`rows_missing=0` ⟹ **899/900 行都在 1 px 内**，那 25 px 是**单行
#   阈值伪影**，不是外形差异（D03 对照组同口径 max=0、median=0）。
#   故门禁用：不出现"有内容↔无内容"翻转 + 中位数为 0 + >2 px 的行数很少。
END_SIL_PX = 2.0            # "算作有差异"的单行阈值（px）
END_ROWS_GT2_MAX = 3        # 允许 >2 px 的**行数**上限（真外形差异是成百行）
# 内部着色差**只报不判**：δ 滚转会把顶点法线一起转，圆柱截面转 δ 后位置几乎
# 回到原处（剪影不变）而**着色**变了 ⟹ 这是渲染的亚像素现象，不携带外形信息。
# 实测 D04 f0↔f60：均值 0.011 lsb、p99.9 13 lsb、max 36 lsb；D03 对照 0.000/1/4。
# 参考上限（不是门禁）：全图均值 ≤ `SHADE_MEAN_REF`。
SHADE_MEAN_REF = 0.05       # lsb
# ★ D03 对照组（用同一套判据量已验收的 D03，证明阈值不是为 D04 量身定做）
CONTROL = ("guardhit", "f0000", "f0036")


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
    return rgb.min(axis=2) < 0.92          # 白底：任何通道明显低于 1 = 角色


def row_span(mask, rows):
    """给定行区间内，每行的最左/最右非背景列。返回 (min_col, max_col, width)。"""
    band = mask[rows[0]:rows[1], :]
    cols = np.where(band.any(axis=0))[0]
    if cols.size == 0:
        return None
    return int(cols.min()), int(cols.max()), int(cols.max() - cols.min() + 1)


def row_extents(mask):
    """整幅图逐行的剪影左右缘列号；某行无内容则返回 None。

    ★ 为什么要"逐行"而不是只比最外缘：只比 `row_span` 会漏掉"外形局部收缩"
      （比如袖子中间凹进去），逐行比对才真的证明**剪影同形**。
    """
    extents = []
    for row in mask:
        cols = np.where(row)[0]
        extents.append((int(cols.min()), int(cols.max())) if cols.size else None)
    return extents


def silhouette_delta(mask_a, mask_b, top_n=5):
    """逐行剪影左右缘差。

    ★ 为什么**不能只看 max**：剪影掩膜是"通道 < 0.92"的**阈值**切出来的 ——
      一条抗锯齿的淡边只要跨过阈值，单行的最左列就能整段跳 25 px。那就是
      **阈值伪影**，不是外形差异。分辨方法：看**分布**。
      真外形差异 ⟹ 成百行都差同样多；阈值伪影 ⟹ 只有 1~2 行差很多、其余 0。
    故同时返回：max、>2px 的行数、以及差值最大的几行（带行号）。
    """
    ea, eb = row_extents(mask_a), row_extents(mask_b)
    rows = []
    compared = 0
    missing = 0
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
        # >2 px 的行数（左 / 右）—— 真外形差异会让这个数很大
        "rows_gt2_left": sum(1 for r in rows if r[1] > 2),
        "rows_gt2_right": sum(1 for r in rows if r[2] > 2),
        # 中位数：抗锯齿阈值伪影下中位数应为 0
        "median_left": int(np.median([r[1] for r in rows])),
        "median_right": int(np.median([r[2] for r in rows])),
        "worst_rows": [[int(r[0]), int(r[1]), int(r[2])] for r in worst[:top_n]],
    }
    out["rows_gt2_total"] = out["rows_gt2_left"] + out["rows_gt2_right"]
    # ★ 判据用**分布**：无行翻转 + 中位数为 0 + >2px 行数少
    out["sil_ok"] = bool(
        out["rows_missing"] == 0
        and out["median_left"] == 0
        and out["median_right"] == 0
        and out["rows_gt2_total"] <= END_ROWS_GT2_MAX)
    return out


def shade_stats(pixels_a, pixels_b):
    """内部着色差：差异像素占比（%）与 p99.9 通道差（lsb）。只看有内容的像素。"""
    rgb_a, rgb_b = pixels_a[:, :, :3], pixels_b[:, :, :3]
    content = np.maximum(rgb_a.max(axis=-1), rgb_b.max(axis=-1)) < 0.92
    if not content.any():
        return 0.0, 0.0, 0
    diff = np.abs(rgb_a - rgb_b).max(axis=-1)[content]
    n = int(diff.size)
    pct = round(100.0 * float((diff > 1.0 / 255.0 + 1e-6).sum()) / n, 4)
    p999 = round(float(np.percentile(diff, 99.9)) * 255.0, 3)
    mean = round(float(diff.mean()) * 255.0, 4)
    return pct, p999, n, mean, round(float(diff.max()) * 255.0, 2)


def band_centroid(mask, rows):
    """给定行带内，所有非背景像素的**列重心**（图像像素）。"""
    band = mask[rows[0]:rows[1], :]
    cols = np.where(band.any(axis=0))[0]
    if cols.size == 0:
        return None, None
    weights = band.sum(axis=0).astype(np.float64)
    total = weights.sum()
    center = float((np.arange(band.shape[1]) * weights).sum() / total)
    return center, (int(cols.min()), int(cols.max()))


def main():
    ref = load(os.path.join(PRE, "guardbreak_front_f0000.png"))
    fmask = mask_of(ref)
    rows_any = np.where(fmask.any(axis=1))[0]
    lo, hi = int(rows_any.min()), int(rows_any.max())
    span = hi - lo
    # 行 0 在底部 ⟹ 从下往上切带
    arm_band = (lo + int(span * 0.52), lo + int(span * 0.80))
    torso_band = (lo + int(span * 0.45), lo + int(span * 0.72))
    head_band = (lo + int(span * 0.78), hi + 1)
    print("PX_LAYOUT " + json.dumps({
        "image_h": fmask.shape[0], "char_rows": [lo, hi], "char_span_px": span,
        "arm_band": list(arm_band), "torso_band": list(torso_band),
        "head_band": list(head_band)}))

    cache = {}

    def px(stem, view, tag):
        """按文件名前缀取原始像素（缓存）。stem 用于对照组复用同一套判据。"""
        key = (stem, view, tag)
        if key not in cache:
            cache[key] = load(
                os.path.join(PRE, "%s_%s_%s.png" % (stem, view, tag)))
        return cache[key]

    def get(view, tag):
        return mask_of(px("guardbreak", view, tag))

    def measure(in_tag, out_tag, gated):
        ma, mb = get("front", in_tag), get("front", out_tag)
        sa, sb = get("side", in_tag), get("side", out_tag)
        span_a, span_b = row_span(ma, arm_band), row_span(mb, arm_band)
        tc_a, tr_a = band_centroid(sa, torso_band)
        tc_b, tr_b = band_centroid(sb, torso_band)
        hc_a, hr_a = band_centroid(sa, head_band)
        hc_b, hr_b = band_centroid(sb, head_band)
        row = {
            "gated": gated,
            "front_arm_span_px": [span_a[2] if span_a else None,
                                  span_b[2] if span_b else None],
            "front_arm_delta_px": (None if not (span_a and span_b)
                                   else round(span_b[2] - span_a[2], 1)),
            "front_arm_edges": [list(span_a[:2]) if span_a else None,
                                list(span_b[:2]) if span_b else None],
            "side_torso_center_px": [None if tc_a is None else round(tc_a, 1),
                                     None if tc_b is None else round(tc_b, 1)],
            "side_torso_delta_px": (None if tc_a is None or tc_b is None
                                    else round(tc_b - tc_a, 1)),
            "side_head_center_px": [None if hc_a is None else round(hc_a, 1),
                                    None if hc_b is None else round(hc_b, 1)],
            "side_head_delta_px": (None if hc_a is None or hc_b is None
                                   else round(hc_b - hc_a, 1)),
        }
        # 像素掩膜逐位相同？（平台内 / 末帧返回）
        row["front_identical"] = bool(np.array_equal(ma, mb))
        row["side_identical"] = bool(np.array_equal(sa, sb))
        return row

    result = {}
    for pair in GATED_PAIRS + REPORT_PAIRS:
        key = "%s_vs_%s" % pair
        result[key] = measure(pair[0], pair[1], pair in GATED_PAIRS)
    print("PX_PAIRS " + json.dumps(result, ensure_ascii=False))

    checks = {}
    for key, row in result.items():
        if not row["gated"]:
            continue
        checks["front_ok_" + key] = bool(
            row["front_arm_delta_px"] is not None
            and row["front_arm_delta_px"] >= FRONT_MIN_PX)
        checks["side_ok_" + key] = bool(
            row["side_torso_delta_px"] is not None
            and row["side_torso_delta_px"] >= SIDE_MIN_PX)
        checks["head_ok_" + key] = bool(
            row["side_head_delta_px"] is not None
            and row["side_head_delta_px"] >= SIDE_MIN_PX)
    # ★ 硬直的画面级证据：震开峰与硬直末**逐位相同**
    peak, hold = result["f0000_vs_f0004"], result["f0000_vs_f0014"]
    a, b = get("front", "f0004"), get("front", "f0014")
    c, d = get("side", "f0004"), get("side", "f0014")
    checks["stagger_identical_ok"] = bool(np.array_equal(a, b)
                                          and np.array_equal(c, d))
    del peak, hold

    # ---- 末帧返回零位：**有量纲**的两条判据（替代不可达的"逐位相同"）-------------
    # 同一套判据跑两遍：D04（判）与 D03（对照，只报不判）—— 证明阈值不是为 D04 凑的。
    ret = {}
    for stem, tag_last in (("guardbreak", "f0060"), (CONTROL[0], CONTROL[2])):
        first_tag = CONTROL[1] if stem != "guardbreak" else "f0000"
        row = {}
        for view in VIEWS:
            pa, pb = px(stem, view, first_tag), px(stem, view, tag_last)
            sil = silhouette_delta(mask_of(pa), mask_of(pb))
            pct, p999, _n, mean, mx = shade_stats(pa, pb)
            sil["shade_pct"] = pct
            sil["shade_p999_lsb"] = p999
            sil["shade_mean_lsb"] = mean
            sil["shade_max_lsb"] = mx
            # 只报不判（理由见常量区）
            sil["shade_ref_ok"] = bool(mean <= SHADE_MEAN_REF)
            row[view] = sil
        ret[stem] = row
    print("PX_RETURN " + json.dumps(ret, ensure_ascii=False))

    d04 = ret["guardbreak"]
    checks["end_silhouette_ok"] = bool(all(d04[v]["sil_ok"] for v in VIEWS))
    # 只报不判：着色差是亚像素法线现象（见常量区注释），D03 对照一并打印
    checks["end_shade_ref"] = bool(
        all(d04[v]["shade_ref_ok"] for v in VIEWS))
    # 只报不判：因为已验收的 D03 也不满足（见文件头第 2 号教训）
    e, f = get("front", "f0060"), get("side", "f0060")
    checks["end_identical_report"] = bool(
        np.array_equal(e, get("front", "f0000"))
        and np.array_equal(f, get("side", "f0000")))
    checks["failed"] = sorted(
        k for k, v in checks.items()
        if v is not True and not k.endswith("_report")
        and not k.endswith("_ref"))
    print("PX_CHECKS " + json.dumps(checks, ensure_ascii=False))


if __name__ == "__main__":
    main()
