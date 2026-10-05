"""probe_e11_foot.py —— E11 半跪段右鞋的 **(踝世界 z, 脚俯仰)** 二维网格（只读）。

目的：把 [44,104] 每帧的 `Shoe_Sole_R` 最低点写成一张表，
直接读出「脚俯仰多少度 + 踝抬多高 = 鞋底落在 [0, +6]」的那条线。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e11_foot.py
"""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A           # noqa: E402
import anim_revive as RV       # noqa: E402

arm, meshes = RV.boot()

_ANKLE_ORIG = RV._ankle_target
_R_FP_BASE = tuple(RV.R_FP_KEYS)
_L_FP_BASE = tuple(RV.FP_KEYS)
_ROLL_BASE = tuple(RV.ROLL_KEYS)


def set_params(dz_r, fp_r, dz_l=0.0, fp_l=0.0):
    def ankle(frame, side):
        t = Vector(_ANKLE_ORIG(frame, side))
        if side == "R" and frame >= 30:
            t.z += dz_r / 1000.0
        if side == "L" and frame >= 86:
            t.z += dz_l / 1000.0
        return t
    RV._ankle_target = ankle
    RV.R_FP_KEYS = tuple((f, v + fp_r) for f, v in _R_FP_BASE)
    RV.FP_KEYS = tuple((f, v + fp_l) for f, v in _L_FP_BASE)


def measure(frame):
    pose = RV.revive_pose(arm, frame)
    A.apply_pose(arm, pose)
    sole = RV._sole_low_mm()
    return {
        "soleR": sole["R"], "soleL": sole["L"],
        "kneeR": A.bone_world(arm, "shin.R", "head").z * 1000.0,
        "kneeL": A.bone_world(arm, "shin.L", "head").z * 1000.0,
        "ankR": A.bone_world(arm, "foot.R", "head").z * 1000.0,
        "toeR": A.bone_world(arm, "toe.R", "tail").z * 1000.0,
    }


FRAMES = tuple(range(44, 105, 4))
DZS = (0, 20, 40, 60)
FPS = (-60, -45, -30, -15, 0, 15, 30, 45)

print("# ========= E11F 二维网格：soleR / kneeR（行=每帧，列=dz,dp） ========")
for f in FRAMES:
    cells = []
    for dz in DZS:
        for fp in FPS:
            set_params(dz, fp)
            row = measure(f)
            cells.append((dz, fp, row["soleR"], row["kneeR"]))
    good = [(dz, fp, s) for dz, fp, s, _k in cells if 0.0 <= s <= 6.0]
    print("E11F f=%3d  base_soleR=%+7.2f base_kneeR=%7.2f | 达标(dz,dp,sole)="
          % (f, cells[4 * 4][2], cells[4 * 4][3]), good[:6])

print("# ========= E11F 逐帧最优（在 dz∈0..80, dp∈-60..60 中取 |sole-1| 最小） ==")
for f in FRAMES:
    best = None
    for dz in (0, 10, 20, 30, 40, 50, 60, 70, 80):
        for fp in (-60, -52, -45, -37, -30, -22, -15, -8, 0, 8, 15, 22, 30):
            set_params(dz, fp)
            row = measure(f)
            s = row["soleR"]
            if s is None:
                continue
            if best is None or abs(s - 1.0) < abs(best[2] - 1.0):
                best = (dz, fp, s, row["kneeR"], row["ankR"], row["toeR"])
    print("E11F_BEST f=%3d dz=%3d dp=%4d soleR=%+7.2f kneeR=%7.2f ankR=%7.2f "
          "toeRtail=%7.2f" % (f, best[0], best[1], best[2], best[3], best[4],
                              best[5]))
