"""probe_e11_fp.py —— 给一个**候选 `R_FP_KEYS`**，逐帧量右鞋底 / 全身最低件（只读）。

为什么需要它：
    `probe_e11_refit.py` 逐帧二分出「理想 fp」，但那是 **121 个独立值**（含
    f73~f76 的测量假象：`revive_pose` 把半跪停顿冻结到 f72，那几帧的 fp 不可观测）。
    定稿要的是一条**平滑关键帧表**。本探针把候选表直接灌进 `RV.R_FP_KEYS`，
    逐帧打印真实鞋底，用于快速迭代 —— 不用跑 121 帧门禁 + D18 全帧比对 + 出图。

判据（与门禁同口径）：
    · `low` = `D.body_low_profile()` 的最低件（全部网格）⟹ 门禁 `rvw_body_band_ok`
      要求**全程** min ≥ −8.0、max ≤ +10.0。
    · `soleR` / `soleL` = 按鞋对象分左右的最低点。
    · 膝高必须**不受影响**（fp 只转鞋，不动腿）⟹ 顺带打印 `kneeR@HK_FRAME` 自检。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e11_fp.py
"""

import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A           # noqa: E402
import anim_revive as RV       # noqa: E402

# --------------------------------------------------------------- 候选俯仰表
# 来源：`_e11_refit.log` 的逐帧反解值（去掉 f73~f76 假象段与 f103 非单调段），
#       压缩成 4 帧间隔的关键帧，端点 (0,−15) / (120,0) 保持与两端接缝**逐位**一致。
CAND = ((0, -15.0), (16, -15.0),
        (30, -8.0), (44, 0.0),
        (52, 14.0), (56, 22.5), (60, 21.0), (64, 19.5), (68, 18.0),
        (72, 16.4), (80, 16.4), (88, 16.0), (92, 15.7),
        (96, 13.2), (100, 9.0),
        (104, 0.0), (120, 0.0))

BASE = tuple(RV.R_FP_KEYS)

arm, meshes = RV.boot()


def row(frame):
    pose = RV.revive_pose(arm, frame)
    A.apply_pose(arm, pose)
    sole = RV._sole_low_mm()
    lows = RV.D.body_low_profile()
    low_at = min(lows.items(), key=lambda kv: kv[1])[0]
    return {
        "soleL": sole["L"], "soleR": sole["R"],
        "low": min(lows.values()), "low_at": low_at,
        "kneeR": A.bone_world(arm, "shin.R", "head").z * 1000.0,
    }


def sweep(label, table):
    RV.R_FP_KEYS = tuple(table)
    print("# ================= %s =================" % label)
    worst, worst_at, wmax, wmax_at = 1e9, None, -1e9, None
    for f in range(RV.START, RV.END + 1):
        r = row(f)
        flag = ""
        if r["low"] < RV.BODY_BAND[0] or r["low"] > RV.BODY_BAND[1]:
            flag += " <<BAND"
        if r["low"] < worst:
            worst, worst_at = r["low"], f
        if r["low"] > wmax:
            wmax, wmax_at = r["low"], f
        if f >= 52 and f <= 110:
            print("E11F f=%3d fpR=%+7.2f soleL=%+7.2f soleR=%+7.2f low=%+7.2f"
                  "(%-18s) kneeR=%7.2f%s"
                  % (f, RV._pwl(RV.R_FP_KEYS, f), r["soleL"] or 0.0,
                     r["soleR"] or 0.0, r["low"], r["low_at"], r["kneeR"], flag))
    print("E11F_%s body_low_min=%+.2f@f%s body_low_max=%+.2f@f%s  band=%s"
          % (label, worst, worst_at, wmax, wmax_at, RV.BODY_BAND))
    print("E11F_%s halfkneel f%d kneeR=%.2f (需 ≤ %.0f)"
          % (label, RV.HK_FRAME, row(RV.HK_FRAME)["kneeR"], RV.HK_DOWN_KNEE_MAX_MM))


sweep("BASE", BASE)
sweep("CAND", CAND)
