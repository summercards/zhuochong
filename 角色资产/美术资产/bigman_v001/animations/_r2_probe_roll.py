"""临时探针：在 f = 14 单帧上扫"绕小腿轴滚 φ"对 `no_teleport` 步长的影响。

只回答一件事：把 `shin.R` 滚多少度，欧拉的逐分量步长才能掉到 25° 以下？
用完即删。
"""
import os
import sys
import math
import json
import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import anim_getup_b as D          # noqa: E402
import anim_lib as A              # noqa: E402
import anim_jump_start as JS      # noqa: E402
import anim_ultimate_end as UE    # noqa: E402

arm, meshes = D.boot()

F_TARGET = int(os.environ.get("PROBE_F", "14"))

# 逐帧解到 F_TARGET，并把**未加窗口**时的 shin 欧拉记下来
prev = {}
for f in range(0, F_TARGET + 1):
    p = D.build_pose(arm, f)
    if f == F_TARGET - 1:
        prev = dict(p)

eul_t = tuple(prev["shin.R"])
print("PROBE_HEAD " + json.dumps({
    "f": F_TARGET, "prev_shinR": [round(v, 2) for v in eul_t]}))

# 现在骨架停在 f = F_TARGET 的姿态上；扫 φ
full = UE._roll_grid()
rows = []
for deg in range(-180, 181, 5):
    phi = math.radians(deg)
    UE.ROLL_GRID = (phi,)
    # `_set_euler_nearest` 会把该骨写成"离 prev 最近"的欧拉（含 ±360 与两支候选）
    got = UE._set_euler_nearest(arm, "shin.R", prev=list(eul_t))
    step = max(abs(a - b) for a, b in zip(got, eul_t))
    rows.append((deg, round(step, 2), [round(v, 2) for v in got]))
UE.ROLL_GRID = full

# 还原姿态（扫描过程改了骨架）
D.build_pose(arm, F_TARGET)

best = sorted(rows, key=lambda r: r[1])[:8]
print("PROBE_BEST " + json.dumps(best))
ok = [r for r in rows if r[1] <= 25.0]
print("PROBE_OK " + json.dumps({
    "n_ok": len(ok),
    "deg_range": [ok[0][0], ok[-1][0]] if ok else None}))
