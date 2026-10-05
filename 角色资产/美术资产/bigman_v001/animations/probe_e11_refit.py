"""probe_e11_refit.py —— 反解 `R_FP_KEYS`：让右鞋底全程落在 [0, +6]（只读）。

原理（已由 `probe_e11_sweep.py` 证明）：
    · 右脚俯仰 `fp` **不影响膝高、也不影响踝位置** —— 它只转鞋。
      （`E11S_B` 里 kneeR@72 在所有 dp 下恒为 111.00。）
    · `soleR` 对 `fp` **单调递减**（fp 越大鞋压得越深）⟹ 可以二分。
    所以「右鞋压穿」是一个**一元方程**，不需要动任何腿的几何。

做法：把 `R_FP_KEYS` 展开成**逐帧表**（`_pwl` 在整数帧处精确取键值），
逐帧二分出 `soleR = +3.0` 的 `fp`，最后打印整条曲线 + 单帧跳变。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e11_refit.py
"""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A           # noqa: E402
import anim_revive as RV       # noqa: E402

arm, meshes = RV.boot()

SOLVE_LO, SOLVE_HI = 56, 103           # 这一段要求鞋底落地
TARGET = 3.0                           # 目标鞋底高度（mm）
_ORIG = tuple(RV.R_FP_KEYS)
SOL = {f: RV._pwl(_ORIG, f) for f in range(0, RV.END + 1)}


def apply_sol():
    RV.R_FP_KEYS = tuple(sorted(SOL.items()))


def measure(frame):
    pose = RV.revive_pose(arm, frame)
    A.apply_pose(arm, pose)
    sole = RV._sole_low_mm()
    return {
        "soleR": sole["R"], "soleL": sole["L"],
        "kneeR": A.bone_world(arm, "shin.R", "head").z * 1000.0,
        "ankR": A.bone_world(arm, "foot.R", "head").z * 1000.0,
        "toeR": A.bone_world(arm, "toe.R", "tail").z * 1000.0,
    }


apply_sol()
print("# ============ E11R 基线（逐帧，未反解） ============")
for f in range(SOLVE_LO, SOLVE_HI + 1, 2):
    row = measure(f)
    print("E11R_PRE f=%3d fp=%+7.2f soleR=%+8.2f soleL=%+7.2f kneeR=%7.2f "
          "ankR=%7.2f toeRtail=%7.2f"
          % (f, SOL[f], row["soleR"] or 0.0, row["soleL"] or 0.0,
             row["kneeR"], row["ankR"], row["toeR"]))

print("# ============ E11R 逐帧二分反解 ============")
for f in range(SOLVE_LO, SOLVE_HI + 1):
    lo, hi = -90.0, 80.0
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        SOL[f] = mid
        apply_sol()
        s = measure(f)["soleR"]
        if s is None:
            break
        if s > TARGET:      # 鞋底还太高 ⟹ fp 要更大
            lo = mid
        else:
            hi = mid
    SOL[f] = 0.5 * (lo + hi)
apply_sol()

print("# ============ E11R 反解后逐帧 ============")
worst_step, worst_at = 0.0, None
prev = None
for f in range(SOLVE_LO, SOLVE_HI + 1):
    row = measure(f)
    if prev is not None:
        d = abs(SOL[f] - prev)
        if d > worst_step:
            worst_step, worst_at = d, f
    prev = SOL[f]
    print("E11R_POST f=%3d fp=%+7.2f soleR=%+8.2f soleL=%+7.2f kneeR=%7.2f "
          "ankR=%7.2f toeRtail=%7.2f"
          % (f, SOL[f], row["soleR"] or 0.0, row["soleL"] or 0.0,
             row["kneeR"], row["ankR"], row["toeR"]))
print("E11R_STEP max_dfp=%.2f @f%s" % (worst_step, worst_at))

print("# ============ E11R 压缩成关键帧表（每 4 帧 + 端点） ============")
keys = [f for f in range(0, RV.END + 1, 4)]
keys += [f for f in (SOLVE_LO, SOLVE_HI, 104, 120) if f not in keys]
keys = sorted(set(keys))
for f in keys:
    if f < SOLVE_LO:
        v = SOL[f]
    else:
        v = SOL[f]
    print("E11R_KEY (%3d, %+7.2f)," % (f, v))
