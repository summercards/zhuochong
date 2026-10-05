"""E07 诊断探针（临时件）：逐帧定位 4 处异常。

用法：
  blender.exe --background --factory-startup --python _probe_e07_diag.py
"""
import os
import sys
import math

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import anim_victory_02 as V2  # noqa: E402
import anim_lib as A  # noqa: E402
from mathutils import Vector  # noqa: E402

arm, meshes = V2.boot()

WATCH = list(V2.ARM_BONES) + ["ring_03.L", "ring_03.R", "shoulder.L",
                              "shoulder.R", "chest", "head"]

poses = {}
rec = {}
for f in range(V2.START, V2.END + 1):
    p = V2.victory_pose(arm, f)
    poses[f] = p
    rec[f] = {b: tuple(p.get(b, (0.0, 0.0, 0.0))) for b in WATCH}

print("=" * 70)
print("E07_DIAG A. 逐帧 euler 最大步（只看 WATCH）")
steps = []
for f in range(V2.START + 1, V2.END + 1):
    for b in WATCH:
        a = rec[f - 1][b]
        c = rec[f][b]
        st = max(abs(x - y) for x, y in zip(a, c))
        steps.append((st, f, b, a, c))
steps.sort(reverse=True)
for st, f, b, a, c in steps[:14]:
    print("  step=%8.3f  f=%3d  %-12s  %s -> %s"
          % (st, f, b, tuple(round(v, 2) for v in a),
             tuple(round(v, 2) for v in c)))

print("=" * 70)
print("E07_DIAG B. 定格窗 [%d,%d] 逐帧 R 臂 / L 臂 euler" % V2.HOLD)
for f in range(V2.HOLD[0] - 1, V2.HOLD[1] + 2):
    if f not in rec:
        continue
    print("  f=%3d env=%.4f" % (f, V2.arm_env(f)))
    for b in V2.ARM_BONES:
        print("      %-12s %s" % (b, tuple(round(v, 4) for v in rec[f][b])))

print("=" * 70)
print("E07_DIAG C. 末段 f108..120 arm euler（找 180 跳）")
for f in range(105, V2.END + 1):
    print("  f=%3d env=%.4f  forearm.R=%s  hand.R=%s  upperarm.R=%s"
          % (f, V2.arm_env(f),
             tuple(round(v, 3) for v in rec[f]["forearm.R"]),
             tuple(round(v, 3) for v in rec[f]["hand.R"]),
             tuple(round(v, 3) for v in rec[f]["upperarm.R"])))

print("=" * 70)
print("E07_DIAG D. 环指 f8..f14")
for f in range(6, 16):
    print("  f=%3d ring_03.L=%s ring_03.R=%s"
          % (f, tuple(round(v, 3) for v in rec[f]["ring_03.L"]),
             tuple(round(v, 3) for v in rec[f]["ring_03.R"])))

print("=" * 70)
print("E07_DIAG E. R 拳穿模 f90..f112（hand_mesh_stats, limit=10mm）")
A.torso_bvh_reset()
for f in range(88, 113, 2):
    A.apply_pose(arm, poses[f])
    st = V2.hand_mesh_stats("R", step=3, limit_mm=V2.HAND_PIERCE_MM)
    core = A.bone_world(arm, "hand.R", "tail")
    print("  f=%3d env=%.3f inside=%3d inside_nothumb=%3d deepest=%.2f "
          "deepest_nothumb=%.2f beyond=%3d core=[%.1f,%.1f,%.1f]"
          % (f, V2.arm_env(f), st.get("inside", -1),
             st.get("inside_nothumb", -1), st.get("deepest_mm", 0.0),
             st.get("deepest_nothumb_mm", 0.0), st.get("beyond_limit", -1),
             core.x * 1000, core.y * 1000, core.z * 1000))

print("=" * 70)
print("E07_DIAG F. hint 余量：逐帧量 hand_x_hint 的可用性")
A.apply_pose(arm, poses[0])
print("  STATION_HAND_Y L=%s R=%s"
      % (tuple(round(v, 3) for v in V2.STATION_HAND_Y["L"]),
         tuple(round(v, 3) for v in V2.STATION_HAND_Y["R"])))
print("  STATION_HAND_X L=%s R=%s"
      % (tuple(round(v, 3) for v in V2.STATION_HAND_X["L"]),
         tuple(round(v, 3) for v in V2.STATION_HAND_X["R"])))
print("E07_DIAG DONE")
