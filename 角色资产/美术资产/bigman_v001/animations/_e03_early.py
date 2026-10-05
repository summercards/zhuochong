"""E03 早帧穿透溯源：站架姿下「非拇指但判在体内」的手部顶点到底是谁。

用法（离线）：
    blender.exe --background --factory-startup --python _e03_early.py

只读；不写盘。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import anim_rage as R  # noqa: E402

arm, meshes = R.boot()
tree = R.torso_bvh()

for side in R.SIDES:
    core = R.A.bone_world(arm, "hand." + side, "tail")
    pts = R.hand_mesh_points(side, step=3)
    bad = [(p, n) for p, n in pts
           if not n.startswith("Thumb_") and R.inside_torso(p, tree)]
    thr = [(p, n) for p, n in pts if n.startswith("Thumb_")
           and R.inside_torso(p, tree)]
    span = max((p - core).length for p, _n in pts) * 1000.0
    print("E03_EARLY station %s n=%d core_gap=%+.2f inside_nothumb=%d "
          "inside_thumb=%d farthest_vert=%.1f mm"
          % (side, len(pts), R.signed_to_torso(core), len(bad), len(thr), span))
    for p, n in bad[:10]:
        print("    %-26s gap=%+7.2f  d_core=%6.1f mm"
              % (n, R.signed_to_torso(p), (p - core).length * 1000.0))

print("E03_EARLY done")
