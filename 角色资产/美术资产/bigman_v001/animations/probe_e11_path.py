"""probe_e11_path.py —— E11 定稿参数的**全程逐帧体检**（只读，不渲染）。

为什么要它（而不是直接跑门禁）：
    门禁只在**红的时候**给汇总值，迭代一次要跑完 121 帧 + D18 全帧比对 + 出图。
    这个探针把「膝轨迹 / 踝轨迹 / 鞋底 / 全身最低件 / 单帧台阶」**逐帧摊开**，
    一轮就把下一处该改哪个数直接指出来。

三块输出：
    E11P_TAIL  尾段交接核验：f92..f120 的 euler 单帧台阶 + 与 `Idle_01@0` 的世界差
    E11P_SCAN  全程逐帧表（标出越界）
    E11P_SUM   汇总（膝最低 / 肢体最大单帧位移 / 鞋底带 / 全身最低件带 / 最大 euler 台阶）

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e11_path.py
"""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A           # noqa: E402
import anim_revive as RV       # noqa: E402

arm, meshes = RV.boot()


def snap(frame):
    """摆出第 `frame` 帧，返回一行测量。"""
    pose = RV.revive_pose(arm, frame)
    A.apply_pose(arm, pose)
    lows = RV.D.body_low_profile()
    sole = RV._sole_low_mm()
    knee = {s: A.bone_world(arm, "shin." + s, "head") for s in RV.SIDES}
    ank = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in RV.SIDES}
    top = min(lows.items(), key=lambda kv: kv[1])
    return {
        "pose": pose,
        "knee": knee,
        "ank": ank,
        "sole": sole,
        "low": min(lows.values()),
        "low_at": top[0],
        "head": A.bone_world(arm, "head", "head").z * 1000.0,
        "pel": A.bone_world(arm, "pelvis", "head").z * 1000.0,
    }


def euler_step(pa, pb):
    worst, at = 0.0, None
    for name in set(pa) | set(pb):
        if name == "@loc":
            continue
        va = pa.get(name, (0.0, 0.0, 0.0))
        vb = pb.get(name, (0.0, 0.0, 0.0))
        step = max(abs(x - y) for x, y in zip(va, vb))
        if step > worst:
            worst, at = step, name
    return worst, at


# =============================================================== P1 尾段交接
print("# ================= E11P_TAIL 尾段交接 =================")
idle0 = RV.IDLE.idle_pose(arm, 0.0)
A.apply_pose(arm, idle0)
idle_mats = {n: A.bone_world(arm, n, "head").copy() for n in RV.BONE_LIST}
prev = None
for f in range(88, RV.END + 1):
    row = snap(f)
    step, at = (0.0, None) if prev is None else euler_step(prev, row["pose"])
    diff = max((A.bone_world(arm, n, "head") - idle_mats[n]).length
               for n in RV.BONE_LIST) * 1000.0
    print("E11P_TAIL f=%3d step=%7.3f(%s) vs_Idle=%8.3f mm soleL=%+7.2f "
          "soleR=%+7.2f" % (f, step, at, diff, row["sole"]["L"], row["sole"]["R"]))
    prev = row["pose"]

# =============================================================== P2 逐帧表
print("# ================= E11P_SCAN 全程逐帧 =================")
rows = {}
prev = None
for f in range(RV.START, RV.END + 1):
    row = snap(f)
    rows[f] = row
    flags = ""
    if row["low"] < RV.BODY_BAND[0] or row["low"] > RV.BODY_BAND[1]:
        flags += " <<BAND"
    if min(v.z for v in row["knee"].values()) * 1000.0 \
            < RV.KNEE_RADIUS_MM - RV.KNEE_PATH_TOL_MM:
        flags += " <<KNEE"
    if f >= RV.STAND_START:
        for s in RV.SIDES:
            if row["sole"][s] is None:
                continue
            if not (RV.SOLE_BAND_MM[0] <= row["sole"][s] <= RV.SOLE_BAND_MM[1]):
                flags += " <<SOLE" + s
    dk = da = de = 0.0
    if prev is not None:
        dk = max((row["knee"][s] - prev["knee"][s]).length for s in RV.SIDES) * 1000.0
        da = max((row["ank"][s] - prev["ank"][s]).length for s in RV.SIDES) * 1000.0
        de, _at = euler_step(prev["pose"], row["pose"])
        if max(dk, da) > RV.LIMB_STEP_MAX_MM:
            flags += " <<STEP%.0f" % max(dk, da)
    print("E11P_SCAN f=%3d pel=%7.2f kneeL=%7.2f kneeR=%7.2f ankL=%7.2f "
          "ankR=%7.2f soleL=%+7.2f soleR=%+7.2f low=%+7.2f(%-18s) head=%7.1f "
          "dk=%6.2f da=%6.2f de=%6.2f%s"
          % (f, row["pel"], row["knee"]["L"].z * 1000, row["knee"]["R"].z * 1000,
             row["ank"]["L"].z * 1000, row["ank"]["R"].z * 1000,
             row["sole"]["L"] or 0.0, row["sole"]["R"] or 0.0,
             row["low"], row["low_at"], row["head"], dk, da, de, flags))
    prev = row

# =============================================================== P3 汇总
print("# ================= E11P_SUM 汇总 =================")
lows = [rows[f]["low"] for f in rows]
all_sole = [rows[f]["sole"][s] for f in rows for s in RV.SIDES
            if rows[f]["sole"][s] is not None]
stand_sole = [rows[f]["sole"][s] for f in rows if f >= RV.STAND_START
              for s in RV.SIDES if rows[f]["sole"][s] is not None]
knee_min = min(min(v.z for v in rows[f]["knee"].values()) * 1000.0 for f in rows)
knee_min_at = min(rows, key=lambda f: min(v.z for v in rows[f]["knee"].values()))
steps = []
prev = None
for f in range(RV.START, RV.END + 1):
    if prev is not None:
        dk = max((rows[f]["knee"][s] - rows[prev]["knee"][s]).length
                 for s in RV.SIDES) * 1000.0
        da = max((rows[f]["ank"][s] - rows[prev]["ank"][s]).length
                 for s in RV.SIDES) * 1000.0
        de, at = euler_step(rows[prev]["pose"], rows[f]["pose"])
        steps.append((max(dk, da), de, f, at))
    prev = f
worst_limb = max(steps, key=lambda t: t[0])
worst_eul = max(steps, key=lambda t: t[1])
print("E11P_SUM body_low_min=%+.2f body_low_max=%+.2f (band %s)"
      % (min(lows), max(lows), RV.BODY_BAND))
print("E11P_SUM sole_min=%+.2f sole_max=%+.2f (band %s) | 站姿窗 [%d,%d] 内 "
      "min=%+.2f max=%+.2f" % (min(all_sole), max(all_sole), RV.SOLE_BAND_MM,
                               RV.STAND_START, RV.END,
                               min(stand_sole), max(stand_sole)))
print("E11P_SUM knee_min=%7.2f @f%s (需 ≥ %.1f)"
      % (knee_min, knee_min_at, RV.KNEE_RADIUS_MM - RV.KNEE_PATH_TOL_MM))
print("E11P_SUM limb_step_max=%7.2f @f%s | euler_step_max=%7.2f @f%s(%s)"
      % (worst_limb[0], worst_limb[2], worst_eul[1], worst_eul[2], worst_eul[3]))
print("E11P_SUM halfkneel f%d: kneeL=%7.2f kneeR=%7.2f (低≤%.0f 高≥%.0f)"
      % (RV.HK_FRAME, rows[RV.HK_FRAME]["knee"]["L"].z * 1000,
         rows[RV.HK_FRAME]["knee"]["R"].z * 1000,
         RV.HK_DOWN_KNEE_MAX_MM, RV.HK_UP_KNEE_MIN_MM))
print("E11P_SUM stand f%d: pel=%7.2f head=%7.1f (pel %s, head ≥ %.0f)"
      % (RV.END, rows[RV.END]["pel"], rows[RV.END]["head"],
         RV.STAND_PELVIS_Z_MM, RV.STAND_HEAD_MIN_MM))
