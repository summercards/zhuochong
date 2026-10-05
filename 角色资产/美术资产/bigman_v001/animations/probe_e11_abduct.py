"""probe_e11_abduct.py —— 反解尾段外展起点 `TAIL_ABDUCT_START`（只读）。

要解决的问题：`A.leg_ik` 是 **YZ 平面解**（不含 x），从 `leg_solve` 切过来的那一帧
踝的 x 会从「跪姿的外开值」被拉回「髋的矢状面」—— R 踝实测跳 **78 mm**，
`rvw_limb_step_ok`（≤60 mm）红。

做法：二分每一侧的 `TAIL_ABDUCT_START`，使得 **f93 的踝 x 接上 f92 的踝 x**。
（f93 是尾段的第一帧；外展在 f93 处的值 = a0 + (a1−a0)/12。）

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e11_abduct.py
"""

import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A           # noqa: E402
import anim_revive as RV       # noqa: E402

arm, meshes = RV.boot()

FIRST = RV.TAIL_MIX_START + 1          # 93：尾段第一帧
PREV = RV.TAIL_MIX_START               # 92


def ankle_x(frame, side):
    pose = RV.revive_pose(arm, frame)
    A.apply_pose(arm, pose)
    return A.bone_world(arm, "foot." + side, "head").x * 1000.0


print("# ============ E11A 起点（未反解） ============")
for side in RV.SIDES:
    print("E11A side=%s  x@92=%+8.3f  x@93=%+8.3f  d=%+8.3f  (a0=%+.3f)"
          % (side, ankle_x(PREV, side), ankle_x(FIRST, side),
             ankle_x(FIRST, side) - ankle_x(PREV, side),
             RV.TAIL_ABDUCT_START[side]))

print("# ============ E11A 逐侧二分 ============")
for side in RV.SIDES:
    want = ankle_x(PREV, side)
    lo, hi = -40.0, 40.0
    if RV.TAIL_SIDES[side] < 0:
        lo, hi = hi, lo        # L 侧 x 随 rz 递减
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        RV.TAIL_ABDUCT_START[side] = mid
        got = round(ankle_x(FIRST, side), 6)
        # 单调判据：让 x@93 逼近 want
        if RV.TAIL_SIDES[side] > 0:
            if got > want:
                lo = mid
            else:
                hi = mid
        else:
            if got < want:
                lo = mid
            else:
                hi = mid
    RV.TAIL_ABDUCT_START[side] = 0.5 * (lo + hi)
    print("E11A_SOL side=%s  a0=%+7.3f  ->  x@93=%+8.3f (want %+8.3f, "
          "残差 %+7.3f)" % (side, RV.TAIL_ABDUCT_START[side],
                            ankle_x(FIRST, side), want,
                            ankle_x(FIRST, side) - want))

print("# ============ E11A 反解后逐帧踝 x / 膝 x ============")
for f in range(PREV, 105, 2):
    pose = RV.revive_pose(arm, f)
    A.apply_pose(arm, pose)
    ax = {s: A.bone_world(arm, "foot." + s, "head").x * 1000.0
          for s in RV.SIDES}
    kx = {s: A.bone_world(arm, "shin." + s, "head").x * 1000.0
          for s in RV.SIDES}
    print("E11A_POST f=%3d ankX L=%+8.3f R=%+8.3f kneeX L=%+8.3f R=%+8.3f"
          % (f, ax["L"], ax["R"], kx["L"], kx["R"]))
print("E11A_FINAL TAIL_ABDUCT_START=%r"
      % ({k: round(v, 3) for k, v in RV.TAIL_ABDUCT_START.items()},))
