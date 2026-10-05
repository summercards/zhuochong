"""probe_e11_sweep.py —— E11 剩余两处 `<<BAND` 的**归因 + 参数扫描**（只读）。

要回答的两个问题：
  A. 尾段 [93,104] 的鞋底压穿（左鞋最低 −65.6）到底是不是 `_tail_mix` 的
     **euler 线性混合**造成的？（把 `TAIL_MIX_START` 推到天上去 = 关掉混合，
     看纯 IK 解的踝/鞋底是否一直在设计路径上。）
  B. 半跪段 [57,92] 的右鞋压穿（最低 −62.5）与「踝世界 z」「右foot俯仰」的
     关系 —— 扫一遍，找出让鞋底回到 [−8, +10] 而**右膝仍然 ≤160** 的组合。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e11_sweep.py
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


def measure(frame, dz_r=0.0, dz_l=0.0, dp_r=0.0, dp_l=0.0):
    """摆一帧并量：膝/踝世界 z、左右鞋最低点、全身最低件。"""
    pose = RV.revive_pose(arm, frame)
    A.apply_pose(arm, pose)
    sole = RV._sole_low_mm()
    lows = RV.D.body_low_profile()
    return {
        "kneeL": A.bone_world(arm, "shin.L", "head").z * 1000.0,
        "kneeR": A.bone_world(arm, "shin.R", "head").z * 1000.0,
        "ankL": A.bone_world(arm, "foot.L", "head").z * 1000.0,
        "ankR": A.bone_world(arm, "foot.R", "head").z * 1000.0,
        "soleL": sole["L"], "soleR": sole["R"],
        "low": min(lows.values()),
        "low_at": min(lows.items(), key=lambda kv: kv[1])[0],
        "model": min((v.z * 1000.0) for v in
                     [Vector(A.bone_world(arm, "shin." + s, "head"))
                      for s in RV.SIDES]),
    }


def _patch(dz_r, dz_l, dp_r, dp_l):
    """给两腿的踝 z 与脚俯仰加常数偏置（只在本轮扫描内生效）。"""
    def ankle(frame, side):
        t = Vector(_ANKLE_ORIG(frame, side))
        if side == "R" and frame >= 44:
            t.z += dz_r / 1000.0
        if side == "L" and frame >= 86:
            t.z += dz_l / 1000.0
        return t
    RV._ankle_target = ankle
    RV.R_FP_KEYS = tuple((f, v + dp_r) for f, v in RV._R_FP_BASE)
    RV.FP_KEYS = tuple((f, v + dp_l) for f, v in RV._FP_BASE)


RV._R_FP_BASE = tuple(RV.R_FP_KEYS)
RV._FP_BASE = tuple(RV.FP_KEYS)

# ======================================================= A 归因：关掉 euler 混合
print("# ============ E11S_A 关掉 _tail_mix（纯 IK）看踝是否跟得上目标 ============")
RV.TAIL_MIX_START = 10 ** 9
for f in range(88, RV.END + 1, 2):
    row = measure(f)
    tgt = RV._ankle_target(f, "L")
    print("E11S_A f=%3d ankL=%7.2f tgtL_z=%7.2f ankR=%7.2f tgtR_z=%7.2f "
          "soleL=%+7.2f soleR=%+7.2f low=%+7.2f(%s)"
          % (f, row["ankL"], tgt.z * 1000.0, row["ankR"],
             RV._ankle_target(f, "R").z * 1000.0,
             row["soleL"] or 0.0, row["soleR"] or 0.0,
             row["low"], row["low_at"]))
RV.TAIL_MIX_START = 92

# ======================================================= B 半跪段右鞋扫描
print("# ============ E11S_B 右鞋：踝 z 偏置 × 脚俯仰偏置 网格 ============")
KNEE_FRAME = (60, 64, 68, 72, 76, 80, 84, 88, 92)
for dz in (0, 20, 40, 60, 80, 100):
    for dp in (0, -15, -30, -45):
        _patch(dz, 0.0, dp, 0.0)
        worst_sole, worst_at = 0.0, None
        knee72, knee_max = None, -1e9
        for f in KNEE_FRAME:
            row = measure(f)
            for side in ("L", "R"):
                if row["sole" + side] is not None \
                        and row["sole" + side] < worst_sole:
                    worst_sole, worst_at = row["sole" + side], (f, side)
            knee_max = max(knee_max, row["kneeR"])
            if f == 72:
                knee72 = row["kneeR"]
        print("E11S_B dz=%4d dp=%4d  worst_sole=%+7.2f@%s  kneeR@72=%7.2f "
              "kneeR_max=%7.2f" % (dz, dp, worst_sole, worst_at, knee72,
                                   knee_max))

# ======================================================= C 逐帧：候选定稿的组合
print("# ============ E11S_C 逐帧（候选组合） ============")
for dz, dp in ((60, -30), (80, -45), (80, -30), (100, -45), (60, -45)):
    _patch(dz, 0.0, dp, 0.0)
    print("--- dz=%d dp=%d ---" % (dz, dp))
    for f in range(56, 105, 4):
        row = measure(f)
        print("E11S_C f=%3d ankR=%7.2f kneeR=%7.2f soleR=%+7.2f soleL=%+7.2f "
              "low=%+7.2f(%s)  fp=%.1f"
              % (f, row["ankR"], row["kneeR"], row["soleR"] or 0.0,
                 row["soleL"] or 0.0, row["low"], row["low_at"],
                 RV._pwl(RV.R_FP_KEYS, f)))
