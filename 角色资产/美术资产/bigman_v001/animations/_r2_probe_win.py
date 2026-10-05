"""临时探针：查证 `_legroll_window` 在真实管线里到底给了什么、`shin.R` 最终写成什么。用完即删。"""
import os
import sys
import math
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import anim_getup_b as D          # noqa: E402
import anim_jump_start as JS      # noqa: E402
import anim_ultimate_end as UE    # noqa: E402

arm, meshes = D.boot()

print("PROBE_ENV " + json.dumps({
    "spin_final": os.environ.get("D18_LEGROLL_FINAL", "1"),
    "max_deg": D.LEGROLL_MAX_DEG, "lo": D.LEGROLL_LO,
    "mid": D.LEGROLL_MID, "hi": D.LEGROLL_HI,
    "grid_len": len(UE.ROLL_GRID), "grid_step_deg": UE.ROLL_STEP_DEG,
    "shinR_in_rollbones": "shin.R" in UE.ROLL_BONES,
    "eul_y_safe": UE.EULER_Y_SAFE, "eul_y_weight": UE.EULER_Y_WEIGHT}))

for f in (13, 14):
    win = D._legroll_window(f)
    has330 = any(abs(math.degrees(p) - 330.0) < 0.5 for p in win)
    print("PROBE_WIN f=%d n=%d cap_max_deg=%.2f has330=%s"
          % (f, len(win), max(abs(math.degrees(D._wrap_pi(p))) for p in win), has330))

poses = {}
for f in range(0, 15):
    poses[f] = D.build_pose(arm, f)

for f in (13, 14):
    print("PROBE_EUL f=%d shinR=%s prev_recorded=%s"
          % (f, [round(v, 2) for v in poses[f]["shin.R"]],
             [round(v, 2) for v in JS._PREV_EULER.get("shin.R", ())]))
