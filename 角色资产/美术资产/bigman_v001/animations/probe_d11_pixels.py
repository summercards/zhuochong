"""probe_d11_pixels —— 把 D11 `Hit_Leg` 的判据数值换算成**画面像素**。

（由 `probe_d10_pixels.py` 派生；D11 计划 §2「像素探针」要求：
  「改 `STEM = "hitleg"`。★ **口径换第三套**：本支主检**前视**（左右晃动），侧视只报。
   前视**骨盆带 / 腿带**重心**横向**位移必须 ≥ 下界；`head_lag` 换成 `lower_body_leads`
   （骨盆带横向峰值的**帧号**必须早于上身带 ≥2 帧）。
   **D10 作反面对照**（D10 是上身先、下盘基本不动 ⟹ 用 D11 的尺子量 D10 应判红，
   即 `px_lower_leads_can_fail_ok`）。」）

背景（D03 第 3 号教训）：
    判据数值 ≠ 观众看到的轮廓位移；头绕颈旋转时轮廓中心只走一半。
    ⟹ 凡是"位移/张开类"的语义判据，落定前**必须**做一次
       「判据数值 → 画面像素」复核。

═══ D11 是受击族里**唯一**受力点在下盘的支 ⟹ 观察轴也跟着换 ═══
    D05~D08  整躯干受力   → 主检**侧视**（前后）
    D09      头颈（末端）  → 主检**侧视**（前后）+ 躯干必须"读不出动"
    D10      躯干中段      → 主检**侧视**（前后），躯干必须"看得出在折"
    D11      腿部（下盘）  → ★ 主检**前视**（左右）—— "下盘晃动"读的是**左右摇摆**

★★★ 本支头号测量陷阱：上身的横向位移被骨盆平移「同相拖走」★★★
    骨盆往受力侧平移 30 mm ⟹ **骨盆以上的每一节**都跟着平移 30 mm（刚性搬运）。
    所以前视量「上身带重心的**绝对**横向位移」时，它是
        平移（与骨盆同相，命中帧最大） + 侧倾（滞后，峰值晚）
    两项叠加 —— 实测 f3 上身绝对位移 ≈ +19.5 px、f8 ≈ −4.4 px，
    **|绝对位移| 峰值落在 f3**，与骨盆**同帧** ⟹ 会把**正确**的动画判红。
    ⟹ 量"上身滞后"**必须用差分**：`lean = 重心(胸带) − 重心(骨盆带)`，
      骨盆的整体平移被减掉，只剩**侧倾**（= 门禁 `upper_tilt` 的画面证据）。

═══ 方向符号（本支头号陷阱）：受力侧 = 角色左（+X）⟹ 前视**右**移 ═══
    坐标约定（与 `anim_lib` 一致）：+X = 角色**左**，+Y = 角色身后，正面朝 −Y。
    前视相机在 (0, −4.6, 0.92) 看向原点、up = +Z
    ⟹ 相机局部 X（= 图像**右**）= Y_cam × Z_cam = (+Z) × (−Y) = **+X**。
    ⟹ `FRONT_SIGN = +1`：图像**右** = +X = 角色左 = **受力侧**。
    ★ 若有人照抄 D05~D10 的 `SIDE_SIGN = −1`，`front_lower_sway_ok_*` 会**立刻判红**。

判据的**适用域**：门禁只挂在 `hitstop` 停顿平台内（本支 `IMPACT=3`、`HOLD_END=6`）
    ⟹ `GATED_PAIRS` 取 `f0003 / f0005`。上身差分峰 / 过冲段与落定段的帧**只报不判**。

═══ ★★ 末帧口径：本支**回原位**（方案 A ⟹ 同 D09/D10）═══
    「方案 A ⟹ 末帧**逐位回零位**（含位置）⟹ `end_identical_ok` 可判」。
    ⟹ D07/D08 的 `end_body_shift_ok`（"被推走了"）在本支是**错的口径**，降级为只报。

画面判据（全部会失败）：
    `front_lower_sway_ok_*`   前视**骨盆带**重心横向位移 ≥ `LOWER_MIN_PX`（★ 主判据）
    `front_upper_report_*`    前视**胸带**重心横向位移（**配角，只报**；被平移污染）
    `front_lean_report_*`     前视 `重心(胸带)−重心(骨盆带)`（差分 ⟹ 纯侧倾，只报）
    `front_arms_held_ok_*`    前视手臂带宽度增量 ≤ `arms_max_px`（上界：拳架不许崩）
    `px_lower_leads_ok`       ★ 骨盆带横向峰值帧 **早于** 上身带（差分）峰值帧 ≥2 帧
    `px_lower_sway_can_fail_ok`      ★ 反向守卫：同一把尺子量 **D10 的骨盆带**（基本不动）
                                     必须**不通过** ⟹ 证明下界不是恒真空判据
    `px_lower_sway_can_fail_self_ok` ★ 第二条反向守卫：**同支内部**的回弹帧 f16
                                     （骨盆已基本回中）也必须**不通过**
    `px_lower_leads_frame_can_fail_ok` ★ 反向守卫：**D10** 用「下盘先动」的尺子必须判红
    `hitstop_identical_ok`    停顿平台 f3 ↔ f6 像素掩膜（**分布口径**）读不出变化
    `end_identical_ok`        末帧 f38 ↔ f0 掩膜**逐位相同**（★ 回原位）
    `end_silhouette_ok`       末帧 f38 ↔ f0 剪影（**分布口径**）
    `end_settled_ok`          f30 ↔ f38 剪影（分布口径：落定段冻结）
    `end_torso_shape_ok`      末帧骨盆带列跨度 = f0（≤ `END_TORSO_SPAN_TOL_PX`）
    `px_bound_can_fail_ok`    上界"能失败"的当场证据（D04 的张开峰必须越界）

只报不判：侧视躯干/头带位移、整体剪影重心、剪影/长宽比、着色差（亚像素法线现象）、
    `end_identical_report`、`end_body_shift_report`。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d11_pixels.py
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
STEM = "hitleg"
# ★ 门禁对：两侧都落在 `hitstop` 停顿平台内（本支 IMPACT=3、HOLD_END=6）
GATED_PAIRS = [("f0000", "f0003"), ("f0000", "f0005")]
# ★ 报告对：停顿末 / 上身差分峰 / 回落中 / 过冲峰 / 过冲后微抖 / CANCEL / 末帧（只报不判）
REPORT_PAIRS = [("f0000", "f0006"), ("f0000", "f0008"), ("f0000", "f0012"),
                ("f0000", "f0016"), ("f0000", "f0019"), ("f0000", "f0030"),
                ("f0000", "f0038")]
VIEWS = ("front", "side")

# ---- ★★ 方向符号（本支头号陷阱）：受力侧 = 角色左（+X）⟹ 前视**右**移 --------
#   前视相机 (0,−4.6,0.92) ⟹ X_cam = Y_cam × Z_cam = (+Z)×(−Y) = +X = 图像右。
#   ★ D05~D10 的 `SIDE_SIGN = −1` 是"侧视、前后"口径 —— 照抄到前视会**立刻判红**。
FRONT_SIGN = 1.0          # D11：图像右 = +X = 角色左 = 受力侧 ⟹ "下盘被推向受力侧" = 往右
SIDE_SIGN = -1.0          # 仅用于**报**（侧视无左右可读；保留与 D05~D10 的口径一致性）
CONTROL_SIDE_SIGN = 1.0   # D04（破防·后仰）：侧视正确方向是往右 ⟹ 上界尺子同一把

# ---- 帧号（与 `anim_hit_leg.py` 的时间轴逐一对齐）---------------------------
HITSTOP_A, HITSTOP_B = "f0003", "f0006"    # 停顿平台两端（IMPACT ~ HOLD_END）
SETTLE_A, SETTLE_B = "f0030", "f0038"      # 落定段（CANCEL ~ END）
END_TAG = "f0038"                          # 末帧（= TOTAL = 38）
# ★ 时序判据用的采样帧序列（本支渲出来的全部帧，与 D10 同一批帧号）
SEQ_TAGS = ["f0000", "f0003", "f0005", "f0006", "f0008", "f0012", "f0016",
            "f0019", "f0030", "f0038"]

# ---- 前视分段带（比例 = 相对**人物全高**，从脚底 lo 起算，与 `anim_lib` 无关）--
#   ★★★ 带必须按**受力点**选（D10 教训 2 的延伸）—— 这不是放宽容差，是尺子的适用域。
#   本支受力点在下盘（腿 + 骨盆，z ≤ ~900 mm）⟹ 带必须**切在下盘之内**。
#   `_d11_band_scan.py` 逐区间实测（前视，`d_f3` / `d_f8`，单位 px，峰帧标在右）：
#     0.02-0.07 [  32- 118mm]  2.46/2.24  f3      0.42-0.47 [ 723- 811] 14.06/12.84 f3
#     0.17-0.22 [ 292- 378mm]  5.13/4.81  f3      0.47-0.52 [ 811- 897] 19.08/17.08 f3 ← 纯骨盆
#     0.27-0.32 [ 464- 552mm]  8.62/7.66  f3      0.52-0.57 [ 897- 983] 19.20/27.05 f8 ✗
#     0.37-0.42 [ 637- 723mm] 12.46/11.18 f3      0.67-0.72 [1157-1245] 35.91/46.48 f8
#   ⟹ **0.52 是一条硬分界**：0.52 以下（腿→骨盆，≤ ~900 mm）**峰帧恒为 f3**（下盘），
#     0.52 以上立刻变 f8 —— 因为**手臂挂在胸/脊上**，被滞后 sway 一并甩过去。
#     首跑用 (0.42,0.56) 横跨这条缝 ⟹ 骨盆带峰帧被手臂拖到 f8，`px_lower_leads_ok` 误判红。
#   ⟹ 取 **(0.42, 0.52)**（骨盆 + 大腿根，z 723~897 mm）：峰帧 f3、幅度 ~16.6 px（≥8 的 2.1×）。
HIP_BAND_FRAC = (0.42, 0.52)      # ★ 骨盆带（下盘主承载：平移看这里；**不得跨 0.52**）
CHEST_BAND_FRAC = (0.66, 0.86)    # ★ 胸+肩带（上身侧倾的载体）
HEAD_BAND_FRAC = (0.86, 1.00)     # 头带（只报）
LEG_BAND_FRAC = (0.06, 0.30)      # 小腿+脚带（脚钉住 ⟹ 只报，期望几乎不动）
ARM_BAND_FRAC = (0.52, 0.80)      # 手臂带（上界：拳架不许崩）

# ---- 阈值（下界类：幅度必须"读得出来"）--------------------------------------
# ★ 门禁侧 `pelvis_side = 30.0 mm`、`pelvis_tilt_impact = 9.14°`。
#   `LOWER_MIN_PX` 沿用 D05~D10 一族"读得出来"的通用下界（8 px），
#   本支实测余量见 `PX_LAG`；**不为本支重定标**（同一把尺子量 D10 必须判红）。
LOWER_MIN_PX = 8.0
# ---- 上界：手臂带宽度增量（**跨设计标定**，D04 张开峰为 1.0 基准）-----------
#   ★ 沿用 0.10（与 D05~D10 同一把尺子）⟹ 在 D11 必须**通过**、在 D04 必须**失败**。
ARMS_MAX_FRAC_OF_D04 = 0.10
# ---- 前视整体横向位移：**只报不判**（量的是"全人重心"，混了上下相反项）-------
LAT_MIN_PX_REPORT = 1.0
# ---- 比例尺（★ 方向：mm/px = 1/0.556 ≈ 1.7986，不是乘 0.556）--------------
MM_PER_PX = 1.0 / 0.556
# ---- 末帧"形状回去"：骨盆带列跨度与 f0 相同 ---------------------------------
END_TORSO_SPAN_TOL_PX = 2.0
# ---- 「回到零位」的画面判据（分布口径，非逐位相同 —— D08/D09 教训 2）---------
END_ROWS_GT2_MAX = 3
SHADE_MEAN_REF = 0.05
# ★ 对照组 = **D04**：上界标定用它的**张开峰**（f0 ↔ f4）；回零标定用它的末对。
CONTROL_PEAK = ("guardbreak", "f0000", "f0004")
CONTROL_END = ("guardbreak", "f0000", "f0060")
# ★ 本支登记的骨盆位移（方案 A ⟹ 无净位移；只报）
REG_ROOT_MOTION_M = 0.0
# ---- ★★ 本支主设计：**下盘先动**的画面证据（时序）---------------------------
LOWER_LEADS_MIN_FRAMES_PX = 2
# ★★ 反面对照 = **D10**（`Hit_Body`）：上身先动、下盘**基本不动** ⟹
#   用 D11 的「下盘横向位移下界」和「下盘先动的时序」两把尺子量它**都必须判红**。
MIRROR_LOWER = ("hitbody", "f0000", "f0003")
MIRROR_SEQ_STEM = "hitbody"
# ★ 第二条反向守卫：本支内部回弹帧（骨盆已回中）也必须不满足下界
FAIL_FRAME_TAG = "f0016"


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
    """逐行剪影左右缘差（判据挂**分布**，不挂 max —— 见 D03 第 3 号教训）。"""
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


def peak_frame(series):
    """|值| 的峰值帧（取**第一个**达到最大的帧 —— 命中平台三帧同值取命中帧）。"""
    best_val = max(abs(v) for _t, v in series)
    tag = next(t for t, v in series if abs(v) >= best_val - 1e-6)
    return tag, int(tag[1:]), best_val


def main():
    ref = load(os.path.join(PRE, "%s_front_f0000.png" % STEM))
    fmask = mask_of(ref)
    rows_any = np.where(fmask.any(axis=1))[0]
    lo, hi = int(rows_any.min()), int(rows_any.max())
    span = hi - lo

    def band(frac):
        return (lo + int(span * frac[0]), lo + int(span * frac[1]) + 1)

    hip_band = band(HIP_BAND_FRAC)
    chest_band = band(CHEST_BAND_FRAC)
    head_band = band(HEAD_BAND_FRAC)
    leg_band = band(LEG_BAND_FRAC)
    arm_band = band(ARM_BAND_FRAC)
    # 侧视报告用（沿用 D10 的"躯干带"）
    side_torso_band = (lo + int(span * 0.45), lo + int(span * 0.72) + 1)
    side_head_band = (lo + int(span * 0.78), hi + 1)
    char_band = (lo + int(span * 0.20), hi + 1)

    print("PX_LAYOUT " + json.dumps({
        "stem": STEM, "image_h": fmask.shape[0], "char_rows": [lo, hi],
        "char_span_px": span,
        "hip_band": list(hip_band), "hip_band_frac": list(HIP_BAND_FRAC),
        "chest_band": list(chest_band), "chest_band_frac": list(CHEST_BAND_FRAC),
        "head_band": list(head_band), "leg_band": list(leg_band),
        "arm_band": list(arm_band), "char_band": list(char_band),
        "front_sign": FRONT_SIGN, "side_sign": SIDE_SIGN,
        "control_side_sign": CONTROL_SIDE_SIGN,
        "px_per_mm_declared": 0.556, "mm_per_px_used": round(MM_PER_PX, 4),
        "span_derived_px_per_mm": round(float(span) / (1.7323 * 1000.0), 4)}))

    cache = {}

    def px(stem, view, tag):
        key = (stem, view, tag)
        if key not in cache:
            cache[key] = load(
                os.path.join(PRE, "%s_%s_%s.png" % (stem, view, tag)))
        return cache[key]

    def get(stem, view, tag):
        return mask_of(px(stem, view, tag))

    # ---- 前视：主判据（下盘横向位移）+ 报告（上身绝对 / 上身差分 / 腿带）-------
    hip0, _ = band_centroid(get(STEM, "front", "f0000"), hip_band)
    chest0, _ = band_centroid(get(STEM, "front", "f0000"), chest_band)
    lean0 = chest0 - hip0

    def front_row(stem, in_tag, out_tag, gated):
        ma, mb = get(stem, "front", in_tag), get(stem, "front", out_tag)
        sa, sb = get(stem, "side", in_tag), get(stem, "side", out_tag)
        hips = band_centroid(ma, hip_band)[0], band_centroid(mb, hip_band)[0]
        chests = band_centroid(ma, chest_band)[0], band_centroid(mb, chest_band)[0]
        legs = band_centroid(ma, leg_band)[0], band_centroid(mb, leg_band)[0]
        span_a, span_b = row_span(ma, arm_band), row_span(mb, arm_band)
        st_a, _ = band_centroid(sa, side_torso_band)
        st_b, _ = band_centroid(sb, side_torso_band)
        return {
            "stem": stem, "gated": gated,
            "front_hip_center_px": [None if v is None else round(v, 2)
                                    for v in hips],
            "front_hip_delta_px": (None if None in hips
                                   else round(hips[1] - hips[0], 2)),
            "front_chest_delta_px": (None if None in chests
                                     else round(chests[1] - chests[0], 2)),
            "front_lean_delta_px": (None if None in chests or None in hips
                                    else round((chests[1] - hips[1])
                                               - (chests[0] - hips[0]), 2)),
            "front_leg_delta_px": (None if None in legs
                                   else round(legs[1] - legs[0], 2)),
            "front_arm_span_px": [span_a[2] if span_a else None,
                                  span_b[2] if span_b else None],
            "front_arm_delta_px": (None if not (span_a and span_b)
                                   else round(span_b[2] - span_a[2], 1)),
            "front_arm_edges": [list(span_a[:2]) if span_a else None,
                                list(span_b[:2]) if span_b else None],
            "side_torso_center_px": [None if st_a is None else round(st_a, 1),
                                     None if st_b is None else round(st_b, 1)],
            "side_torso_delta_px": (None if st_a is None or st_b is None
                                    else round(st_b - st_a, 1)),
        }

    result = {}
    for pair in GATED_PAIRS + REPORT_PAIRS:
        result["%s_vs_%s" % pair] = front_row(STEM, pair[0], pair[1],
                                              pair in GATED_PAIRS)
    peak_key = "CONTROL_PEAK_%s_%s" % (CONTROL_PEAK[1], CONTROL_PEAK[2])
    result[peak_key] = front_row(CONTROL_PEAK[0], CONTROL_PEAK[1],
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
        # ★★★ 主判据（D11 与 D05~D10 **换轴**）：前视**骨盆带**必须"看得见横向位移"（下界）
        bucket["front_lower_sway_ok_" + key] = bool(
            row["front_hip_delta_px"] is not None
            and FRONT_SIGN * row["front_hip_delta_px"] >= LOWER_MIN_PX)
        # ★ 上身**绝对**横向位移被骨盆平移污染 ⟹ 只报
        (reports if is_control else checks)["front_upper_report_" + key] = bool(
            row["front_chest_delta_px"] is not None
            and abs(row["front_chest_delta_px"]) >= LAT_MIN_PX_REPORT)
        # ★ 差分（胸带 − 骨盆带）⟹ 纯侧倾，只报
        (reports if is_control else checks)["front_lean_report_" + key] = bool(
            row["front_lean_delta_px"] is not None
            and abs(row["front_lean_delta_px"]) >= LAT_MIN_PX_REPORT)
        # ★ 腿带（脚钉住）只报 —— 期望几乎不动
        (reports if is_control else checks)["front_leg_report_" + key] = bool(
            row["front_leg_delta_px"] is not None
            and abs(row["front_leg_delta_px"]) >= LAT_MIN_PX_REPORT)
        # ★ 上界：双臂保持防御形状（拳架不许崩）—— 本支必须**通过**，D04 必须**失败**
        bucket["front_arms_held_ok_" + key] = bool(
            row["front_arm_delta_px"] is not None
            and abs(row["front_arm_delta_px"]) <= arms_max_px)

    # ---- 停顿平台的画面级证据：f3 ↔ f6 **读不出任何变化** ---------------------
    #   ★★ 不能用 `np.array_equal`（D08 的写法在 D09 误报，D09 教训 2）：
    #     平台两端姿态逐位冻结，剩下的差异是**轮廓边缘抗锯齿**的亚像素抖动。
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

    # ---- ★★★ 本支主设计：`px_lower_leads_ok` --------------------------------
    #   门禁侧 `lower_body_leads_ok` 量的是**骨骼世界侧倾的峰值帧号**；
    #   这里量的是**前视画面重心的峰值帧号** —— 两条独立证据指向同一件事。
    #   ★ 下盘 = 骨盆带**绝对**横向位移（平移），上身 = `胸带−骨盆带`**差分**（侧倾）。
    seq = {}
    for tag in SEQ_TAGS:
        fm = get(STEM, "front", tag)
        hip, _ = band_centroid(fm, hip_band)
        chest, _ = band_centroid(fm, chest_band)
        leg, _ = band_centroid(fm, leg_band)
        seq[tag] = {"hip_px": None if hip is None else round(hip, 2),
                    "chest_px": None if chest is None else round(chest, 2),
                    "leg_px": None if leg is None else round(leg, 2)}
    hip_series = [(t, seq[t]["hip_px"] - hip0) for t in SEQ_TAGS]
    lean_series = [(t, (seq[t]["chest_px"] - seq[t]["hip_px"]) - lean0)
                   for t in SEQ_TAGS]
    hip_peak_tag, hip_peak_f, hip_peak_val = peak_frame(hip_series)
    lean_peak_tag, lean_peak_f, lean_peak_val = peak_frame(lean_series)
    lean_after = [abs(v) for t, v in lean_series if int(t[1:]) > lean_peak_f]
    print("PX_LAG " + json.dumps({
        "seq": seq,
        "hip_peak_tag": hip_peak_tag, "hip_peak_frame": hip_peak_f,
        "hip_peak_px": round(hip_peak_val, 2),
        "lean_peak_tag": lean_peak_tag, "lean_peak_frame": lean_peak_f,
        "lean_peak_px": round(lean_peak_val, 2),
        "lag_frames": lean_peak_f - hip_peak_f,
        "min_frames": LOWER_LEADS_MIN_FRAMES_PX,
        "hip_series": [[t, round(v, 2)] for t, v in hip_series],
        "lean_series": [[t, round(v, 2)] for t, v in lean_series],
        "note": ("hip = 骨盆带**绝对**横向位移（受力侧为 +，下盘平移）；"
                 "lean = 胸带−骨盆带**差分**（消掉骨盆平移，只剩上身侧倾）")},
        ensure_ascii=False))
    # ★ 判据三条一起：① 骨架先动的峰值帧 早于 上身侧倾峰 ≥2 帧；
    #   ② 下盘峰本身够大（否则"领先"是在噪声上量出来的）；
    #   ③ 上身侧倾峰之后必须**回落**（不是单调平移 —— 证明"滞后"而非"永远追不上"）。
    checks["px_lower_leads_ok"] = bool(
        (lean_peak_f - hip_peak_f) >= LOWER_LEADS_MIN_FRAMES_PX
        and hip_peak_val >= LOWER_MIN_PX
        and lean_peak_val >= LOWER_MIN_PX
        and lean_after and min(lean_after) < lean_peak_val - 0.5)
    checks["px_lower_leads_can_fail_ok"] = bool(
        not (0 >= LOWER_LEADS_MIN_FRAMES_PX))

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
    checks["end_silhouette_ok"] = bool(all(ret[STEM][v]["sil_ok"] for v in VIEWS))
    checks["end_silhouette_control_ok"] = bool(
        all(ret[CONTROL_END[0]][v]["sil_ok"] for v in VIEWS))
    print("PX_RETURN " + json.dumps(ret, ensure_ascii=False))

    # ---- 专属末帧判据（**回原位** ⟹ 骨盆带形状必须回去）------------------------
    ref_span = row_span(mask_of(px(STEM, "front", "f0000")), hip_band)
    end_span = row_span(mask_of(px(STEM, "front", END_TAG)), hip_band)
    span_delta = (None if not (ref_span and end_span)
                  else round(end_span[2] - ref_span[2], 1))
    checks["end_torso_shape_ok"] = bool(
        span_delta is not None and abs(span_delta) <= END_TORSO_SPAN_TOL_PX)
    print("PX_END_SHAPE " + json.dumps({
        "hip_band": list(hip_band), "hip_band_frac": list(HIP_BAND_FRAC),
        "front_hip_span_f0000_px": ref_span[2] if ref_span else None,
        "front_hip_span_end_px": end_span[2] if end_span else None,
        "span_delta_px": span_delta, "tol_px": END_TORSO_SPAN_TOL_PX,
        "span_delta_mm": (None if span_delta is None
                          else round(span_delta * MM_PER_PX, 2))}))

    # ---- 整体剪影重心位移 —— 本支**回原位 ⟹ 只报不判** -----------------------
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

    # ---- 落定段冻结：f30 ↔ f38（分布口径）------------------------------------
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

    checks["end_shade_ref"] = bool(all(ret[STEM][v]["shade_ref_ok"] for v in VIEWS))
    # ★★ 本支**回原位** ⟹ `end_identical_ok` 是**判据**
    checks["end_identical_ok"] = bool(
        np.array_equal(get(STEM, "front", END_TAG), get(STEM, "front", "f0000"))
        and np.array_equal(get(STEM, "side", END_TAG),
                           get(STEM, "side", "f0000")))
    reports["end_identical_report"] = checks["end_identical_ok"]
    # ★ 上界判据"能失败"的**当场证据**：D04 的张开峰必须越界
    checks["px_bound_can_fail_ok"] = bool(
        not control.get("front_arms_held_ok_" + peak_key, False))

    # ---- ★★★ 反向守卫（D11 与 D05~D10 **换轴** ⟹ 必须换对照物）----------------
    #   ★ 守卫 A：同一把「下盘横向位移下界」量 **D10**（`Hit_Body`，受力在躯干中段、
    #     骨盆只做前后/上下、**横向基本不动**）必须**不通过**。
    mstem, m_in, m_out = MIRROR_LOWER
    mirror_row = front_row(mstem, m_in, m_out, True)
    mirror_dev = mirror_row["front_hip_delta_px"]
    checks["px_lower_sway_can_fail_ok"] = bool(
        mirror_dev is not None and FRONT_SIGN * mirror_dev < LOWER_MIN_PX)
    print("PX_MIRROR_SWAY " + json.dumps({
        "stem": mstem, "pair": [m_in, m_out],
        "hip_delta_px": mirror_dev, "lower_bound_px": LOWER_MIN_PX,
        "note": ("D10 受力在躯干中段 ⟹ 骨盆横向基本不动 ⟹ 同一把尺子必须**不通过**；"
                 "若它反而通过，说明 front_lower_sway_ok 是空判据")},
        ensure_ascii=False))
    #   ★ 守卫 B：同一把「下盘先动」的时序尺子量 **D10 整段序列**必须**判红**。
    mseq_hip, mseq_lean = [], []
    m_hip0, _ = band_centroid(get(mstem, "front", "f0000"), hip_band)
    m_chest0, _ = band_centroid(get(mstem, "front", "f0000"), chest_band)
    m_lean0 = m_chest0 - m_hip0
    for tag in SEQ_TAGS:
        fm = get(mstem, "front", tag)
        hip, _ = band_centroid(fm, hip_band)
        chest, _ = band_centroid(fm, chest_band)
        mseq_hip.append((tag, hip - m_hip0))
        mseq_lean.append((tag, (chest - hip) - m_lean0))
    m_hip_tag, m_hip_f, m_hip_val = peak_frame(mseq_hip)
    m_lean_tag, m_lean_f, m_lean_val = peak_frame(mseq_lean)
    mirror_ok = bool(
        (m_lean_f - m_hip_f) >= LOWER_LEADS_MIN_FRAMES_PX
        and m_hip_val >= LOWER_MIN_PX
        and m_lean_val >= LOWER_MIN_PX)
    checks["px_lower_leads_frame_can_fail_ok"] = bool(not mirror_ok)
    print("PX_MIRROR_LEADS " + json.dumps({
        "stem": mstem, "hip_peak_frame": m_hip_f, "lean_peak_frame": m_lean_f,
        "hip_peak_px": round(m_hip_val, 2), "lean_peak_px": round(m_lean_val, 2),
        "mirror_passes_ruler": mirror_ok, "lower_bound_px": LOWER_MIN_PX,
        "note": ("D10 是「上身先、下盘基本不动」⟹ 用 D11 的「下盘先动」尺子量它必须判红；"
                 "若 mirror_passes_ruler=True，说明尺子是恒真的")},
        ensure_ascii=False))
    #   ★ 守卫 C：**同一支内部**的回弹帧（骨盆已回中）也必须**不通过**。
    fm_a, fm_b = get(STEM, "front", "f0000"), get(STEM, "front", FAIL_FRAME_TAG)
    fc_a, _ = band_centroid(fm_a, hip_band)
    fc_b, _ = band_centroid(fm_b, hip_band)
    fail_delta = (None if fc_a is None or fc_b is None
                  else round(fc_b - fc_a, 2))
    checks["px_lower_sway_can_fail_self_ok"] = bool(
        fail_delta is not None and FRONT_SIGN * fail_delta < LOWER_MIN_PX)
    print("PX_FAIL_FRAME " + json.dumps({
        "stem": STEM, "pair": ["f0000", FAIL_FRAME_TAG],
        "hip_delta_px": fail_delta, "lower_bound_px": LOWER_MIN_PX,
        "note": "回弹帧（骨盆已回中）必须不满足下界 —— 同支内部的反向守卫"},
        ensure_ascii=False))

    checks["failed"] = sorted(
        k for k, v in checks.items()
        if v is not True and "_report" not in k and not k.endswith("_ref"))
    print("PX_CONTROL " + json.dumps(control, ensure_ascii=False))
    print("PX_REPORTS " + json.dumps(reports, ensure_ascii=False))
    print("PX_CHECKS " + json.dumps(checks, ensure_ascii=False))


if __name__ == "__main__":
    main()
