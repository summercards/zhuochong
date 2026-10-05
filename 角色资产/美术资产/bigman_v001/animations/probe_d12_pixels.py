"""probe_d12_pixels —— 把 D12 `Launch_Hit` 的判据数值换算成**画面像素**。

（由 `probe_d11_pixels.py` 派生；D12 计划 §3「像素探针」原文：
  「**口径换第四套**：本支主检**侧视**（前后 + **上下**）—— 击飞读的是**后仰 + 抬升**；
   前视只报。
   - 侧视**骨盆带重心的竖直**位移（**行号**方向）必须 ≥ 下界（"被顶起来"看得见）；
   - 侧视**头带/胸带的后仰峰帧**必须**晚于**骨盆带的抬升峰帧 ≥2 帧（`waist_first` 的画面证据）；
   - 以 **D11** 作反面对照：D11「下盘左右晃、完全不离地」⟹ 用 D12 的「竖直抬升」尺子
     量 D11 必须判红（`px_lift_can_fail_ok`）；
   - 以 **A12 `Jump_Fall`** 作正面对照：它的骨盆 z 就在弹道上 ⟹ 用同一条尺子量它
     **必须通过**（`px_ballistic_control_ok`）。」

背景（`_d03_` 第 3 号教训）：
    判据数值 ≠ 观众看到的轮廓位移。凡"位移/抬升类"语义判据，落定前**必须**做一次
    「判据数值 → 画面像素」复核。

═══ 方向符号（侧视：图像右 = +Y = 角色**身后**）═══
    侧视相机在 (5.20, 0, 1.55) 看向 (0, 0, 1.55)、up = +Z。
    `to_track_quat("-Z","Y")` ⟹ 局部 X（= 图像**右**）= (+Z)×(+X) = **+Y**。
    ⟹ `SIDE_SIGN = +1`：图像**右** = +Y = **身后**。
    ★ 与 D05~D11 的 `SIDE_SIGN = −1` **不同**。

═══ 本支头号测量陷阱 ①：`Jacket_Hem` 静态件会伪装成"最低点" ═══
    `Jacket_Hem` / `Jacket_Hem_Line` 是 C01 第 3 件登记的**既存绑定遗漏**
    （`parent=null`、`vgroups=0`、无 ARMATURE ⟹ **钉死在 z ≈ 897~926 mm**）。
    本支人物一离地，它就从"贴在腰上"变成"悬在身下的独立一块"，**且已进 GLB**。
    ⟹ 掩膜必须**只剔除**这一块（按它已知的**静态足迹**判：bbox 完整落在里面才剔），
      并把被剔块逐帧登记（`px_hem_excluded_ok`）。
    ★ **不能按"最大连通块"剔** —— 实测该启发式会把**前脚鞋**（f0/f3，area≈1480）
      和**两只鞋**（f12，area≈1480×2）一起剔掉，那是真身体部位。
      本版改为"只剔静态足迹内的块"，并加 `px_hem_filter_needed_ok` 证明过滤确实在干活。

═══ 本支头号测量陷阱 ②：带不能按"剪影比例"锚定 ═══
    原版骨盆带取"当前剪影的 0.42~0.52 高度"，实测该带会**在解剖上滑动**
    （髋 → 大腿 → 头），使 `px_hip_col_mm` 在 +18 ~ +54 mm 之间乱跳（f14/f16/f18 连跳两次）。
    ⟹ 本版两个带一律用**绝对世界高度**锚定：
      · **骨盆带** = 从**已量到的鞋底行**起算 **+800~920 mm**（该区间由 f0 站架实测导出：
        站架时骨盆在鞋底上 830 mm；留 ±60 mm 容忍膝弯带来的髋-鞋竖直距离变化。
        实测全片该距离 830~890 mm ⟹ 骨盆全程落在带内）；
      · **头带** = 当前剪影**顶行往下 55 行**（≈215 mm，头+颈；头永远是剪影最高点）。
    ★ 骨盆带的锚是"**像素量到的鞋底行** + 一个**由 f0 实测导出**的解剖常量"，
      **不含任何设计里的骨盆高度** ⟹ 对 `px_lift_ok` 不构成循环论证。

═══ 与上一版的实质差异（诚实登记）═══
    上一版把 `px_waist_pivot_ok` 写成"命中帧骨盆带前移(负) / 头带后移(正) = 反号"。
    **该前提是错的**：读 `anim_launch_hit.py` 的 `Y_KEYS=((0,0.0),(IMPACT,0.016),…)`
    ⟹ 设计里骨盆在命中帧是往**身后(+Y)** 走 16 mm，头也往身后 —— **同号**。
    "腰先受力"在本支的真实形式化是**时序**（骨盆竖速峰领先上身折峰），
    不是方向反号（那是清单 §3 `waist_first_ok` 的原文口径）。
    ⟹ 本版按清单原文口径重写为 `px_lift_ok` + `px_waist_first_ok` 两把尺子。

画面判据（全部会失败）：
    `px_airborne_ok`           侧视**鞋底行**在 f≥12 全程离地 ≥ `AIRBORNE_MIN_MM`（★ 主判据）
    `px_airborne_can_fail_ok`  ★ 反向守卫：同一把尺子量 **D11**（踩在地上）必须**判红**
    `px_lift_ok`               ★ 骨盆带（鞋底 +800~920 mm）在命中帧相对 f0 **抬升 ≥50 mm**
    `px_lift_can_fail_ok`      ★ 反向守卫：**D11** 用同一把尺子必须**判红**
    `px_waist_first_ok`        ★★ 头带**后仰峰帧**（逐帧后移最大的那一帧）
                               **晚于**骨盆带**抬升峰帧** ≥2 帧（"腰先受力"的画面证据）
    `px_waist_first_can_fail_ok`
                               ★ 反向守卫：**D11** 用同一把尺子必须**判红**
    `px_ballistic_self_ok`     侧视**头带行心**在定格段 f26~34 的最小二乘二次系数
                               换回毫米/帧²后 = `G_PER_FRAME`，且拟合顶点帧 = 解析顶点
    `px_ballistic_control_ok`  ★ 正面对照：同一把尺子量 **A12 `Jump_Fall`**（同一弹道、
                               **不同正交宽**）也必须通过
    `px_fold_back_ok`          上身最终**整体后折**（头带相对 f0 后移 ≥ `FOLD_MIN_MM`）
    `px_hitstop_ok`            停顿平台 f3 ↔ f5 掩膜**逐位相同**（三帧完全停顿）
    `px_frozen_block_ok`       定格段 f26 ↔ f34：按"设计竖直偏移"对齐后**逐行宽度剖面**
                               一致（纯刚性平移），且最佳对齐位移 = 实测鞋底行差
    `px_frozen_can_fail_ok`    ★ 反向守卫：同一把尺子量 **f0 ↔ f3**（姿态在变）必须**判红**
    `px_hem_excluded_ok`       被剔的块 = 已知静态足迹，且 f≥20 各帧足迹**逐位相同**
    `px_hem_filter_needed_ok`  过滤确实在干活（f26 原掩膜最低行 ≠ 过滤后最低行）

只报不判：前视剪影长宽、逐帧行/列心全量表、被剔块明细。

用法：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d12_pixels.py
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
STEM = "launchhit"

# ---- 视图表：(图像高 px, 正交宽 m, 相机 z) —— 用来把 px 换算回毫米 --------------
#   Blender `ortho_scale` 作用于**较长**的渲染边；本族全部 780×1100（高 > 宽）
#   ⟹ 竖直方向 = ortho_scale 米 ⟹ px/m = res_y / ortho。
VIEWS = {
    "launchhit_side": (1100, 4.30, 1.55),
    "launchhit_front": (1100, 4.30, 1.55),
    "jumpfall_side": (1100, 3.80, 1.30),     # A12 `FALL_SIDE` —— 正面对照
    "hitleg_side": (1100, 2.10, 0.92),       # D11 `VIEW_SIDE` —— 反面对照
}

# ---- 帧号（与 `anim_launch_hit.py` 的时间轴逐一对齐）-------------------------
IMPACT = 3
HOLD_END = 6
AIR_ENTRY = 12
PLATEAU = 25
TOTAL = 34
HITSTOP_A, HITSTOP_B = 3, 5
FREEZE_A, FREEZE_B = 26, 34
AIRBORNE_MIN_MM = 100.0                 # 与门禁 `AIRBORNE_MIN_MM` 同源
LIFT_MIN_MM = 50.0                      # 与门禁 `PELVIS_LIFT_MIN_MM` 同源
READ_MIN_MM = 31.0                      # = 8 px @ 侧视（D05~D11 一族"读得出来"的下界）
PIVOT_MIN_FRAMES = 2                    # 与门禁 `LEAD_MIN_FRAMES` 同源
FOLD_MIN_MM = float(os.environ.get("D12PX_FOLD", "150.0"))
G_PER_FRAME_MM = 9.8 / 60.0 / 60.0 * 1000.0     # = 2.722222 mm/帧²
APEX_FRAME = 30.051                             # 解析顶点（V/g + T_ORIGIN）
G_TOL_MM = float(os.environ.get("D12PX_G_TOL", "0.12"))
G_TOL_CTRL_MM = float(os.environ.get("D12PX_G_TOL_CTRL", "0.20"))
HITSTOP_DIFF_MAX = float(os.environ.get("D12PX_HITSTOP", "0.02"))
HITSTOP_PCT_MAX = float(os.environ.get("D12PX_HITSTOP_PCT", "0.05"))

# ---- 带（绝对世界高度锚定 —— 见 docstring 陷阱 ②）----------------------------
PELVIS_BAND_ABOVE_SOLE_MM = (800.0, 920.0)
HEAD_BAND_FROM_TOP_PX = 55

# ---- 逐行剖面比对（px_frozen_block_ok）--------------------------------------
#   ★ 为什么用 p95 而不是单行 max：实测 f26↔f34 的**单行**最大行宽差 16 px 出现在
#     row 483（该行 106 → 122 px）—— 那是轮廓在**行宽剖面局部极值**处（膝/鞋的切点）的
#     必然表现：0.18 px 的亚像素竖直平移足以让水平切点整行跳过一段。
#     **1 行 / 437 行** 不能承担"轮廓没变"这个结论 ⟹ 取 p95（实测 1.0 px）
#     + 均值（实测 0.293 px）为主判，并保留反向对照（f0↔f3：均值 28.7、p95 57）。
#   `SHAPE_W_MIN_PX` 是额外的**薄片守卫**：排掉头顶/鞋尖那 1~2 行纯 AA 薄片
#     （本对子只排掉 3 行，**不承担主判** —— 不要把它当成"凑绿"的手段）。
SHAPE_W_MIN_PX = int(os.environ.get("D12PX_SHAPE_WMIN", "20"))
SHAPE_W_MEAN_MAX = float(os.environ.get("D12PX_SHAPE_W", "2.0"))
SHAPE_P95_MAX = float(os.environ.get("D12PX_SHAPE_P95", "3.0"))
SHAPE_C_MEAN_MAX = float(os.environ.get("D12PX_SHAPE_C", "2.0"))
SHAPE_SHIFT_SEARCH = 6

# ---- 已知下摆足迹（侧视像素坐标，陷阱 ①）：f20/f26/f34 实测逐位相同 --------
HEM_ROW_RANGE = (378, 395)
HEM_COL_RANGE = (340, 440)
HEM_MIN_AREA = 100

FREEZE_FINGERPRINT = [26, 28, 30, 32, 34]
CONTROL_FRAMES = [0, 4, 8, 12, 16, 20, 24]
NEG_FRAMES_D11 = [0, 3, 5, 8, 12, 16]
NEG_PAIRS_D11 = [(0, 3), (0, 5)]


# =============================================================== 像素工具
def load(view, frame):
    path = os.path.join(PRE, "%s_f%04d.png" % (view, frame))
    if not os.path.exists(path):
        return None
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
    return pixels[:, :, :3].min(axis=2) < 0.92


def px_per_mm(view):
    res_y, ortho, _cam_z = VIEWS[view]
    return (float(res_y) / ortho) / 1000.0


def cam_bottom_z(view):
    res_y, ortho, cam_z = VIEWS[view]
    return cam_z - ortho / 2.0


def z_of_row(view, row):
    return float(row) / (px_per_mm(view) * 1000.0) + cam_bottom_z(view)


def components(mask):
    """四连通块（union-find），按面积降序返回 [dict(area, rows, cols, mask)]。"""
    rows, cols = np.where(mask)
    if rows.size == 0:
        return []
    index = {}
    parent = list(range(rows.size))

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


def strip_hem(mask):
    """只剔**完整落在已知静态下摆足迹内**的连通块；返回 (clean, dropped_meta)。

    ★ 不用"最大块"启发式（实测会误剔鞋，见 docstring 陷阱 ①）。
    """
    parts = components(mask)
    if not parts:
        return mask, []
    clean = mask.copy()
    dropped = []
    for part in parts:
        r0, r1 = part["rows"]
        c0, c1 = part["cols"]
        inside = (HEM_ROW_RANGE[0] <= r0 and r1 <= HEM_ROW_RANGE[1]
                  and HEM_COL_RANGE[0] <= c0 and c1 <= HEM_COL_RANGE[1])
        if inside:
            clean &= ~part["mask"]
            dropped.append({"area": part["area"], "rows": [r0, r1],
                            "cols": [c0, c1]})
    return clean, dropped


def rows_any(mask):
    rows = np.where(mask.any(axis=1))[0]
    if rows.size == 0:
        return None
    return int(rows.min()), int(rows.max())


def rows_with_content(mask):
    return np.where(mask.any(axis=1))[0]


def slab_row_centroid(mask, lo, hi):
    lo = max(lo, 0)
    hi = min(hi, mask.shape[0] - 1)
    if hi <= lo:
        return None
    slab = mask[lo:hi + 1, :]
    weights = slab.sum(axis=1).astype(np.float64)
    if weights.sum() <= 0:
        return None
    index = np.arange(slab.shape[0], dtype=np.float64) + lo
    return float((index * weights).sum() / weights.sum())


def slab_col_centroid(mask, lo, hi):
    lo = max(lo, 0)
    hi = min(hi, mask.shape[0] - 1)
    if hi <= lo:
        return None
    slab = mask[lo:hi + 1, :]
    weights = slab.sum(axis=0).astype(np.float64)
    if weights.sum() <= 0:
        return None
    return float((np.arange(slab.shape[1]) * weights).sum() / weights.sum())


def pelvis_band(mask, ppm):
    """骨盆带 = 当前**鞋底行** + 800~920 mm（见 docstring 陷阱 ②）。

    `ppm` = px / mm ⟹ 毫米常量直接乘，**不要再乘 1000**。
    """
    ext = rows_any(mask)
    if ext is None:
        return None, None
    lo = ext[0] + int(round(PELVIS_BAND_ABOVE_SOLE_MM[0] * ppm))
    hi = ext[0] + int(round(PELVIS_BAND_ABOVE_SOLE_MM[1] * ppm))
    return lo, hi


def head_band(mask):
    """头带 = 当前剪影**顶行往下 55 行**（头永远是最高点）。"""
    ext = rows_any(mask)
    if ext is None:
        return None, None
    return ext[1] - HEAD_BAND_FROM_TOP_PX, ext[1]


def band_centroids(view, mask):
    """返回该视图下 骨盆带/头带 的行心与列心（毫米量都用列心/行心做差）。"""
    ppm = px_per_mm(view)
    pr = pelvis_band(mask, ppm)
    hr = head_band(mask)
    out = {
        "pelvis_rows": list(pr) if pr[0] is not None else None,
        "head_rows": list(hr) if hr[0] is not None else None,
        "pelvis_row": slab_row_centroid(mask, *pr) if pr[0] is not None else None,
        "pelvis_col": slab_col_centroid(mask, *pr) if pr[0] is not None else None,
        "head_row": slab_row_centroid(mask, *hr) if hr[0] is not None else None,
        "head_col": slab_col_centroid(mask, *hr) if hr[0] is not None else None,
    }
    return out


def row_profile(mask):
    """{row: (width, cmin, cmax)} —— 逐行水平剖面（纯刚性竖直平移的不变量）。"""
    out = {}
    for r in rows_with_content(mask):
        cc = np.where(mask[r])[0]
        out[int(r)] = (int(cc.max() - cc.min() + 1), int(cc.min()), int(cc.max()))
    return out


def shape_mismatch(pa, pb, d, min_rows=20, min_width=1):
    """把 pb 抬 d 行后与 pa 比：返回 (mean_w, p95_w, max_w, mean_cmin, mean_cmax,
    n, worst_rows)。

    `min_width`：只统计"两边行宽都 ≥ min_width"的行。顶端一行（头顶/鞋尖的 1~2 px 切片）
    在亚像素平移下宽度本身会跳变（纯 AA 边界），nil 会把最坏值打成噪声 —— 默认 1 表示
    不过滤；`px_frozen_block_ok` 传 `SHAPE_W_MIN_PX` 显式排除这些切片。
    """
    common = [r for r in pa if (r - d) in pb
              and min(pa[r][0], pb[r - d][0]) >= min_width]
    if len(common) < min_rows:
        return None
    w, cl, ch = [], [], []
    for r in common:
        w.append(abs(pa[r][0] - pb[r - d][0]))
        cl.append(abs(pa[r][1] - pb[r - d][1]))
        ch.append(abs(pa[r][2] - pb[r - d][2]))
    war = np.array(w, dtype=np.float64)
    order = np.argsort(-war)[:5]
    worst = [{"row": int(common[i]),
              "w_a": pa[common[i]][0], "w_b": pb[common[i] - d][0],
              "dw": int(war[i])} for i in order]
    return (float(war.mean()), float(np.percentile(war, 95)),
            float(war.max()), float(np.mean(cl)), float(np.mean(ch)),
            len(common), worst)


def col_span(mask):
    cols = np.where(mask.any(axis=0))[0]
    if cols.size == 0:
        return None
    return int(cols.min()), int(cols.max()), int(cols.max() - cols.min() + 1)


def quad_fit(frames, values):
    f = np.array(frames, dtype=np.float64)
    y = np.array(values, dtype=np.float64)
    design = np.stack([np.ones_like(f), f, f * f], axis=1)
    coeffs, *_ = np.linalg.lstsq(design, y, rcond=None)
    return float(coeffs[0]), float(coeffs[1]), float(coeffs[2])


def peak_frame(frames, values):
    """逐帧增量最大处（返回该增量所在帧区间的**右端帧**）。"""
    best_f, best_d = None, None
    for i in range(len(frames) - 1):
        d = values[i + 1] - values[i]
        if best_d is None or d > best_d:
            best_d, best_f = d, frames[i + 1]
    return best_f, (None if best_d is None else best_d)


# =============================================================== 主流程
def main():
    res = {}

    # ---------------- (1) 侧视逐帧：剔静态下摆 + 两条带 -------------------
    side = {}
    hem_report = []
    for frame in range(0, TOTAL + 1):
        pixels = load("launchhit_side", frame)
        if pixels is None:
            continue
        raw = mask_of(pixels)
        clean, dropped = strip_hem(raw)
        ext_raw, ext = rows_any(raw), rows_any(clean)
        band = band_centroids("launchhit_side", clean)
        side[frame] = {"bottom": ext[0], "top": ext[1],
                       "bottom_raw": ext_raw[0], "clean": clean,
                       "raw_area": int(raw.sum()),
                       "dropped_area": int(raw.sum() - clean.sum())}
        side[frame].update(band)
        if dropped:
            hem_report.append({"frame": frame, "dropped": dropped})
    if not side:
        raise RuntimeError("侧视静帧一张都没有：%s" % PRE)

    ppm = px_per_mm("launchhit_side")
    res["side_px_per_mm"] = round(ppm, 6)
    res["side_frames_present"] = sorted(side)
    res["side_bottom_row"] = {str(f): side[f]["bottom"] for f in sorted(side)}
    res["side_bottom_row_raw"] = {str(f): side[f]["bottom_raw"] for f in sorted(side)}
    def r3(x):
        return None if x is None else round(x, 3)

    res["side_head_row"] = {str(f): r3(side[f]["head_row"]) for f in sorted(side)}
    res["side_pelvis_row"] = {str(f): r3(side[f]["pelvis_row"]) for f in sorted(side)}
    res["side_pelvis_band_rows"] = {str(f): side[f]["pelvis_rows"] for f in sorted(side)}
    res["side_band_ruler"] = (
        "骨盆带 = 当前鞋底行 + 800~920 mm；头带 = 当前顶行往下 %d 行；"
        "图像右 = +Y = 身后；行号向上 = +Z。" % HEAD_BAND_FROM_TOP_PX)

    # ---------------- (2) 下摆剔除守卫（陷阱 ①）-------------------------
    res["hem_dropped"] = hem_report
    hem_bad = []
    for entry in hem_report:
        for drop in entry["dropped"]:
            if drop["area"] < HEM_MIN_AREA:
                hem_bad.append({"frame": entry["frame"], "why": "area<min",
                                "drop": drop})
    late = [e for e in hem_report if e["frame"] >= 20]
    late_boxes = set()
    for entry in late:
        for drop in entry["dropped"]:
            late_boxes.add((tuple(drop["rows"]), tuple(drop["cols"])))
    res["hem_late_boxes"] = sorted([list(map(list, b)) for b in late_boxes])
    res["hem_static_consistent"] = bool(len(late_boxes) == 1)
    res["hem_clean_bottom_row_f26"] = side[FREEZE_A]["bottom"]
    res["hem_raw_bottom_row_f26"] = side[FREEZE_A]["bottom_raw"]
    res["px_hem_filter_needed_ok"] = bool(
        side[FREEZE_A]["bottom_raw"] != side[FREEZE_A]["bottom"])
    res["px_hem_excluded_ok"] = bool(
        not hem_bad and late and len(late_boxes) == 1
        and side[FREEZE_A]["dropped_area"] >= HEM_MIN_AREA)

    # ---------------- (3) px_airborne_ok —— ★ 主判据（离地）--------------
    def rise_mm(frame):
        if frame not in side:
            return None
        return (side[frame]["bottom"] - side[0]["bottom"]) / ppm

    air = {str(f): round(rise_mm(f), 2) for f in sorted(side)}
    res["px_airborne_mm"] = air
    air_high = {int(f): v for f, v in air.items() if int(f) >= AIR_ENTRY}
    air_min = min(air_high.values())
    res["px_airborne_min_mm"] = round(air_min, 2)
    res["px_airborne_min_at"] = min(air_high, key=lambda f: air_high[f])
    res["px_airborne_end_mm"] = round(rise_mm(TOTAL), 2)
    res["px_airborne_ruler"] = ("鞋底行相对 f0 的位移 ÷ 该视图 px/mm ⟹ 毫米；"
                                "f≥%d 全程 ≥ %.0f mm" % (AIR_ENTRY, AIRBORNE_MIN_MM))
    res["px_airborne_ok"] = bool(
        air_min >= AIRBORNE_MIN_MM
        and (rise_mm(TOTAL) or 0.0) >= AIRBORNE_MIN_MM
        and (rise_mm(AIR_ENTRY) or 0.0) >= AIRBORNE_MIN_MM)

    # ---------------- (4) px_airborne_can_fail_ok —— 反面对照 D11 ---------
    neg = {}
    nppm = px_per_mm("hitleg_side")
    for a, b in NEG_PAIRS_D11:
        pa, pb = load("hitleg_side", a), load("hitleg_side", b)
        if pa is None or pb is None:
            neg["hitleg_f%d_f%d" % (a, b)] = None
            continue
        ca, _ = strip_hem(mask_of(pa))
        cb, _ = strip_hem(mask_of(pb))
        neg["hitleg_f%d_f%d" % (a, b)] = round(
            (rows_any(cb)[0] - rows_any(ca)[0]) / nppm, 2)
    res["px_airborne_control_mm"] = neg
    neg_vals = [v for v in neg.values() if v is not None]
    res["px_airborne_can_fail_ok"] = bool(neg_vals
                                          and max(neg_vals) < AIRBORNE_MIN_MM)

    # ---------------- (5) px_ballistic_self_ok —— 定格段二次拟合 ----------
    freeze = [f for f in FREEZE_FINGERPRINT if f in side]
    vals = [side[f]["head_row"] for f in freeze]
    _c0, c1, c2 = quad_fit(freeze, vals)
    g_self = -2.0 * c2 / ppm
    vertex = (-c1 / (2.0 * c2)) if abs(c2) > 1e-12 else None
    res["px_ballistic_self_frames"] = freeze
    res["px_ballistic_self_head_rows"] = [round(v, 3) for v in vals]
    res["px_ballistic_self_c2_px"] = round(c2, 6)
    res["px_ballistic_self_g_mm"] = round(g_self, 5)
    res["px_ballistic_self_g_ref_mm"] = round(G_PER_FRAME_MM, 5)
    res["px_ballistic_self_g_err_mm"] = round(abs(g_self - G_PER_FRAME_MM), 5)
    res["px_ballistic_self_g_tol_mm"] = G_TOL_MM
    res["px_ballistic_self_vertex_frame"] = (None if vertex is None
                                             else round(vertex, 3))
    res["px_ballistic_self_apex_ref"] = APEX_FRAME
    res["px_ballistic_self_ok"] = bool(
        abs(g_self - G_PER_FRAME_MM) <= G_TOL_MM
        and vertex is not None and abs(vertex - APEX_FRAME) <= 1.0)

    # ---------------- (6) px_ballistic_control_ok —— 正面对照 A12 --------
    cppm = px_per_mm("jumpfall_side")
    cframes, cvals = [], []
    for frame in CONTROL_FRAMES:
        pixels = load("jumpfall_side", frame)
        if pixels is None:
            continue
        clean, _ = strip_hem(mask_of(pixels))
        band = band_centroids("jumpfall_side", clean)
        if band["head_row"] is None:
            continue
        cframes.append(frame)
        cvals.append(band["head_row"])
    res["px_ballistic_control_frames"] = cframes
    res["px_ballistic_control_px_per_mm"] = round(cppm, 6)
    if len(cframes) >= 3:
        _d0, _d1, cc2 = quad_fit(cframes, cvals)
        g_ctrl = -2.0 * cc2 / cppm
        res["px_ballistic_control_g_mm"] = round(g_ctrl, 5)
        res["px_ballistic_control_g_err_mm"] = round(
            abs(g_ctrl - G_PER_FRAME_MM), 5)
        res["px_ballistic_control_g_tol_mm"] = G_TOL_CTRL_MM
        res["px_ballistic_control_ok"] = bool(
            abs(g_ctrl - G_PER_FRAME_MM) <= G_TOL_CTRL_MM)
    else:
        res["px_ballistic_control_ok"] = False
        res["px_ballistic_control_note"] = (
            "★ 对照静帧缺失 —— 先跑 `_d12_render_control.py` 补渲 "
            "`jumpfall_side_f*.png`。")

    # ---------------- (7) px_lift_ok —— 骨盆带竖直抬升 -------------------
    frames = sorted(side)
    missing = [f for f in frames if side[f]["pelvis_row"] is None]
    if missing:
        raise RuntimeError("骨盆带在下列帧取不到内容（带跑出剪影）：%s" % missing)
    lift = {f: (side[f]["pelvis_row"] - side[0]["pelvis_row"]) / ppm
            for f in frames}
    res["px_lift_mm"] = {str(f): round(lift[f], 2) for f in frames}
    res["px_lift_ruler"] = ("骨盆带行心相对 f0 的上移 ÷ %.6f px/mm ⟹ 毫米" % ppm)
    res["px_lift_impact_mm"] = round(lift[IMPACT], 2)
    res["px_lift_min_mm"] = LIFT_MIN_MM
    lift_peak_f, lift_peak_d = peak_frame(frames, [lift[f] for f in frames])
    res["px_lift_peak_frame"] = lift_peak_f
    res["px_lift_peak_mm_per_frame"] = round(lift_peak_d, 2)
    res["px_lift_ok"] = bool(lift[IMPACT] >= LIFT_MIN_MM
                             and max(lift.values()) >= LIFT_MIN_MM)
    res["px_lift_guard_ruler"] = (
        "★ 该尺子的下界 %d mm ≥ 8 px @ 本视图 —— 用同一把尺子量 D11 必须判红。"
        % int(READ_MIN_MM))

    # ★ 反向守卫：D11 用同一把尺子必须判红
    d11 = {}
    for frame in NEG_FRAMES_D11:
        pixels = load("hitleg_side", frame)
        if pixels is None:
            continue
        clean, _ = strip_hem(mask_of(pixels))
        d11[frame] = band_centroids("hitleg_side", clean)
    if 0 in d11:
        d11_lift = {f: (d11[f]["pelvis_row"] - d11[0]["pelvis_row"]) / nppm
                    for f in d11}
        res["px_lift_d11_mm"] = {str(f): round(d11_lift[f], 2)
                                 for f in sorted(d11_lift)}
        res["px_lift_can_fail_ok"] = bool(
            max(abs(v) for v in d11_lift.values()) < LIFT_MIN_MM)
    else:
        res["px_lift_can_fail_ok"] = False

    # ---------------- (8) px_waist_first_ok —— 抬升峰 vs 后仰峰 ----------
    #   骨盆带：抬升峰帧 = 逐帧上移最大处的右端帧
    #   头带  ：后仰峰帧 = 头带**列心**后移（+Y = 图像右 = 正值）最大处的右端帧
    head_col = {f: (side[f]["head_col"] - side[0]["head_col"]) / ppm
                for f in frames}
    res["px_head_col_mm"] = {str(f): round(head_col[f], 2) for f in frames}
    fold_peak_f, fold_peak_d = peak_frame(frames, [head_col[f] for f in frames])
    res["px_fold_peak_frame"] = fold_peak_f
    res["px_fold_peak_mm_per_frame"] = round(fold_peak_d, 2)
    res["px_fold_max_mm"] = round(max(head_col.values()), 2)
    res["px_waist_first_lead_frames"] = fold_peak_f - lift_peak_f
    res["px_waist_first_ruler"] = (
        "侧视：骨盆带**行心**逐帧上移峰帧，必须早于头带**列心**逐帧后移"
        "（+Y = 身后）峰帧 ≥%d 帧。" % PIVOT_MIN_FRAMES)
    res["px_waist_first_ok"] = bool(
        (fold_peak_f - lift_peak_f) >= PIVOT_MIN_FRAMES
        and lift[IMPACT] >= LIFT_MIN_MM
        and res["px_fold_max_mm"] >= READ_MIN_MM
        and lift_peak_d > 0.0 and fold_peak_d > 0.0)

    # ★ 反向守卫：D11 用同一把尺子必须判红（无抬升 + 无后仰）
    if 0 in d11 and len(d11) >= 3:
        df = sorted(d11)
        d11_lift_seq = [(d11[f]["pelvis_row"] - d11[0]["pelvis_row"]) / nppm
                        for f in df]
        d11_head_seq = [(d11[f]["head_col"] - d11[0]["head_col"]) / nppm
                        for f in df]
        dl_f, dl_d = peak_frame(df, d11_lift_seq)
        dh_f, dh_d = peak_frame(df, d11_head_seq)
        res["px_waist_first_d11"] = {
            "lift_peak_frame": dl_f, "lift_peak_mm": round(dl_d, 2),
            "fold_peak_frame": dh_f, "fold_peak_mm": round(dh_d, 2),
            "fold_max_mm": round(max(d11_head_seq), 2),
            "lift_max_mm": round(max(d11_lift_seq), 2),
        }
        res["px_waist_first_can_fail_ok"] = bool(not (
            (dh_f - dl_f) >= PIVOT_MIN_FRAMES
            and max(d11_lift_seq) >= LIFT_MIN_MM
            and max(d11_head_seq) >= READ_MIN_MM))
    else:
        res["px_waist_first_can_fail_ok"] = False

    # ---------------- (9) px_fold_back_ok —— 上身最终整体后折 -------------
    res["px_fold_back_mm"] = round(head_col[20], 2)
    res["px_fold_min_mm"] = FOLD_MIN_MM
    res["px_fold_back_ok"] = bool(head_col[20] >= FOLD_MIN_MM)

    # ---------------- (10) px_hitstop_ok —— 停顿平台 ---------------------
    pa, pb = load("launchhit_side", HITSTOP_A), load("launchhit_side", HITSTOP_B)
    if pa is not None and pb is not None:
        ca, _ = strip_hem(mask_of(pa))
        cb, _ = strip_hem(mask_of(pb))
        xor = int(np.logical_xor(ca, cb).sum())
        diff = np.abs(pa - pb).max(axis=-1)
        content = np.maximum(pa[:, :, :3].max(axis=-1),
                             pb[:, :, :3].max(axis=-1)) < 0.92
        n = int(content.sum()) or 1
        pct = 100.0 * float((diff[content] > 1.0 / 255.0 + 1e-6).sum()) / n
        mean = float(diff[content].mean())
        res["px_hitstop_mask_xor"] = xor
        res["px_hitstop_diff_pct"] = round(pct, 5)
        res["px_hitstop_diff_mean"] = round(mean, 6)
        res["px_hitstop_ok"] = bool(xor == 0 and pct <= HITSTOP_PCT_MAX
                                    and mean <= HITSTOP_DIFF_MAX)
    else:
        res["px_hitstop_ok"] = False

    # ---------------- (11) px_frozen_block_ok —— 纯刚性平移（逐行剖面）---
    def frozen_eval(a_frame, b_frame):
        a, b = side.get(a_frame), side.get(b_frame)
        if a is None or b is None:
            return None
        d0 = b["bottom"] - a["bottom"]           # 实测竖直偏移
        pa, pb = row_profile(a["clean"]), row_profile(b["clean"])
        cands = []
        for d in range(d0 - SHAPE_SHIFT_SEARCH, d0 + SHAPE_SHIFT_SEARCH + 1):
            m = shape_mismatch(pa, pb, d, min_width=SHAPE_W_MIN_PX)
            if m is not None:
                cands.append((m[0] + m[3] + m[4], d, m))
        if not cands:
            return None
        cands.sort()
        _score, best_d, m = cands[0]
        return {"row_delta_measured": int(d0), "best_shift": int(best_d),
                "mean_w_px": round(m[0], 3), "p95_w_px": round(m[1], 3),
                "max_w_px": round(m[2], 3),
                "mean_cmin_px": round(m[3], 3), "mean_cmax_px": round(m[4], 3),
                "rows_compared": m[5], "worst_rows": m[6],
                "height_a_rows": len(pa), "height_b_rows": len(pb)}

    frozen = frozen_eval(FREEZE_A, FREEZE_B)
    res["px_frozen_block"] = frozen
    res["px_frozen_ruler"] = (
        "把 f%d 的逐行剖面抬 **实测鞋底行差** 行后与 f%d 比（只看两边行宽都 ≥%d px 的行）："
        "平均行宽差 ≤%.1f px、p95 ≤%.1f px、平均左右缘差 ≤%.1f px、"
        "最佳位移必须 = 实测鞋底行差。"
        % (FREEZE_B, FREEZE_A, SHAPE_W_MIN_PX, SHAPE_W_MEAN_MAX,
           SHAPE_P95_MAX, SHAPE_C_MEAN_MAX))
    if frozen is not None:
        res["px_frozen_ok"] = bool(
            frozen["best_shift"] == frozen["row_delta_measured"]
            and frozen["mean_w_px"] <= SHAPE_W_MEAN_MAX
            and frozen["p95_w_px"] <= SHAPE_P95_MAX
            and frozen["mean_cmin_px"] <= SHAPE_C_MEAN_MAX
            and frozen["mean_cmax_px"] <= SHAPE_C_MEAN_MAX
            and abs(frozen["height_a_rows"] - frozen["height_b_rows"]) <= 2)
    else:
        res["px_frozen_ok"] = False

    # ★ 反向守卫：同一把尺子量 f0 ↔ f3（姿态在剧烈变化）必须判红
    ctrl = frozen_eval(0, IMPACT)
    res["px_frozen_can_fail"] = ctrl
    res["px_frozen_can_fail_ok"] = bool(
        ctrl is None
        or ctrl["mean_w_px"] > SHAPE_W_MEAN_MAX
        or ctrl["p95_w_px"] > SHAPE_P95_MAX
        or ctrl["mean_cmin_px"] > SHAPE_C_MEAN_MAX
        or ctrl["mean_cmax_px"] > SHAPE_C_MEAN_MAX)

    # ---------------- (12) 前视（只报：剪影）----------------------------
    front = {}
    for frame in (0, 3, 6, 12, 16, 22, 25, 30, 34):
        pixels = load("launchhit_front", frame)
        if pixels is None:
            continue
        clean, _ = strip_hem(mask_of(pixels))
        span = col_span(clean)
        rr = rows_any(clean)
        front[str(frame)] = {"width_px": span[2], "height_px": rr[1] - rr[0] + 1}
    res["front_report"] = front

    ok = sorted(k for k, v in res.items() if k.endswith("_ok"))
    res["ok_flags"] = ok
    res["failed"] = sorted(k for k in ok if res[k] is not True)
    print("D12_PIXELS " + json.dumps(res, ensure_ascii=False))
    print("D12_PIXELS_DONE failed=%s" % res["failed"])


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D12_PIXELS_FAILURE " + traceback.format_exc())
