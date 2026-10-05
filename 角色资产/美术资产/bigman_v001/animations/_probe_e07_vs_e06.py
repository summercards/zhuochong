"""E07 vs E06 逐帧姿态距离（判「两支援胜利支是否撞车」）。
只读：打开工程、取两支 action、按帧号逐帧比对 57 骨的矩阵口径最大差 + 举拳手的高度曲线。
"""
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

ARM_A = "Victory_01"
ARM_B = "Victory_02"
TOTAL = 120


def mat_deg(ma, mb):
    worst = 0.0
    for c in range(3):
        va = ma.col[c].normalized()
        vb = mb.col[c].normalized()
        worst = max(worst, math.degrees(math.acos(max(-1.0, min(1.0,
                                                              va.dot(vb))))))
    return worst


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    bones = sorted(arm.pose.bones.keys())
    act_a = bpy.data.actions[ARM_A]
    act_b = bpy.data.actions[ARM_B]
    scene = bpy.context.scene
    rows = []
    for frame in range(TOTAL + 1):
        mats = {}
        for act in (act_a, act_b):
            arm.animation_data.action = act
            A._bind_slot(arm, act)
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            mats[act.name] = {b: arm.pose.bones[b].matrix.to_3x3().copy()
                              for b in bones if b in arm.pose.bones}
        diff = max(mat_deg(mats[ARM_A][b], mats[ARM_B][b]) for b in bones
                   if b in mats[ARM_A] and b in mats[ARM_B])
        rows.append((frame, diff))
    mx = max(rows, key=lambda r: r[1])
    print("E07_VS_E06 max_deg=%.3f @ frame=%d" % (mx[1], mx[0]))
    print("E07_VS_E06 identical_frames=%d (<=1.0 deg)"
          % sum(1 for _f, d in rows if d <= 1.0))
    for frame in (0, 14, 26, 34, 60, 76, 88, 108, 120):
        if frame <= TOTAL:
            print("  f=%3d diff=%7.3f deg" % (frame, rows[frame][1]))


main()
