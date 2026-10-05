"""E07 诊断探针 v2：hint 余量逐帧 / action 末段键值 / R 拳穿模。"""
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

print("=" * 70)
print("E07_DIAG2 A. 逐帧 hint 余量（sin 夹角）+ 手骨 y_dir 与 ±X 夹角")
poses = {}
margin = {}
for f in range(V2.START, V2.END + 1):
    V2.MIN_HINT_MARGIN = 1.0
    p = V2.victory_pose(arm, f)
    poses[f] = p
    margin[f] = V2.MIN_HINT_MARGIN
worst = sorted(((v, k) for k, v in margin.items()))
for v, k in worst[:14]:
    print("  margin=%.4f  f=%3d  (=%.2f deg)" % (v, k, math.degrees(math.asin(max(-1.0, min(1.0, v))))))

print("=" * 70)
print("E07_DIAG2 B. 逐帧 R 拳穿模 f86..f114（limit=%.1f mm）"
      % V2.HAND_PIERCE_MM)
V2.torso_bvh_reset()
for f in range(86, 115, 2):
    A.apply_pose(arm, poses[f])
    st = V2.hand_mesh_stats("R", step=3, limit_mm=V2.HAND_PIERCE_MM)
    core = A.bone_world(arm, "hand.R", "tail")
    print("  f=%3d env=%.3f inside=%3d nothumb=%3d deepest=%7.2f dnothumb=%7.2f "
          "beyond=%3d core=[%7.1f,%7.1f,%7.1f]"
          % (f, V2.arm_env(f), st.get("inside", -1),
             st.get("inside_nothumb", -1), st.get("deepest_mm", 0.0),
             st.get("deepest_nothumb_mm", 0.0), st.get("beyond_limit", -1),
             core.x * 1000, core.y * 1000, core.z * 1000))

print("=" * 70)
print("E07_DIAG2 C. 复现 main() 的键值：compat_euler + seam_canonicalize 之后")
kf = [(f, V2.victory_pose(arm, f)) for f in range(V2.START, V2.END + 1)]
raw_last = {b: tuple(kf[-1][1].get(b, (0, 0, 0))) for b in V2.ARM_BONES}
kf2 = V2.compat_euler(kf)
comp_last = {b: tuple(kf2[-1][1].get(b, (0, 0, 0))) for b in V2.ARM_BONES}
kf3 = V2.seam_canonicalize(kf2)
seam_last = {b: tuple(kf3[-1][1].get(b, (0, 0, 0))) for b in V2.ARM_BONES}
comp_first = {b: tuple(kf2[0][1].get(b, (0, 0, 0))) for b in V2.ARM_BONES}
seam_first = {b: tuple(kf3[0][1].get(b, (0, 0, 0))) for b in V2.ARM_BONES}
for b in V2.ARM_BONES:
    print("  %-12s" % b)
    print("      raw f0 =%s" % (tuple(round(v, 3) for v in kf[0][1].get(b, (0, 0, 0))),))
    print("      raw f120=%s" % (tuple(round(v, 3) for v in raw_last[b]),))
    print("      comp f0 =%s  comp f120=%s" % (tuple(round(v, 3) for v in comp_first[b]),
                                               tuple(round(v, 3) for v in comp_last[b])))
    print("      seam f0 =%s  seam f120=%s" % (tuple(round(v, 3) for v in seam_first[b]),
                                               tuple(round(v, 3) for v in seam_last[b])))
print("  --- 末段 108..120 (compat 后, 未 seam) 每帧 forearm.R / upperarm.R")
for i in range(108, V2.END + 1):
    pz = kf2[i][1]
    print("   f=%3d  upperarm.R=%s  forearm.R=%s  hand.R=%s"
          % (i, tuple(round(v, 2) for v in pz.get("upperarm.R", ())),
             tuple(round(v, 2) for v in pz.get("forearm.R", ())),
             tuple(round(v, 2) for v in pz.get("hand.R", ()))))
print("E07_DIAG2 DONE")
