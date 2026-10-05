"""E04 诊断 7：定位 `hand.L` 在 f≈96 的 90°/帧 —— 是表示跳（临近万向节锁）还是真转。

打印 f=86..110：
  · 每帧的 matrix 步（最大轴角变化）与 euler 步（最大单轴变化），按骨
  · hand.L / forearm.L / upperarm.L 的局部 euler 三元组
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy                                     # noqa: E402
from mathutils import Vector                   # noqa: E402
import anim_lib as A                           # noqa: E402
import anim_spawn as S                         # noqa: E402


def main():
    arm, meshes = S.boot()
    kfs = [(f, S.spawn_pose(arm, f)) for f in range(S.START, S.END + 1)]
    kfs = S.compat_euler(kfs)
    kfs = S.seam_canonicalize(kfs)
    meta = {"anim_id": S.NAME, "loop": False}
    action, meta = A.build_action(arm, S.NAME + "_DIAG7", kfs, meta)

    f0, f1 = 86, 110
    prev_mat, prev_eul = None, None
    print("%-4s %-26s %-26s  %s" % ("f", "mat_step(bone,deg)", "eul_step(bone,deg)",
                                    "hand.L euler / fore.L euler"))
    for frame in range(f0 - 1, f1 + 1):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        mats, euls = {}, {}
        for name in ("upperarm.L", "forearm.L", "hand.L",
                     "upperarm.R", "forearm.R", "hand.R"):
            if name in arm.pose.bones:
                mats[name] = arm.pose.bones[name].matrix.to_3x3().copy()
                euls[name] = tuple(
                    math.degrees(v)
                    for v in arm.pose.bones[name].rotation_euler)
        if prev_mat is not None and frame >= f0:
            wm, wmn = 0.0, None
            for name in mats:
                a, b = prev_mat[name], mats[name]
                for c in range(3):
                    va = a.col[c].normalized()
                    vb = b.col[c].normalized()
                    d = math.degrees(math.acos(max(-1.0, min(1.0,
                                                             va.dot(vb)))))
                    if d > wm:
                        wm, wmn = d, name
            we, wen = 0.0, None
            for name in euls:
                d = max(abs(x - y) for x, y in zip(prev_eul[name], euls[name]))
                if d > we:
                    we, wen = d, name
            hl = euls["hand.L"]
            fl = euls["forearm.L"]
            print("%-4d %-26s %-26s  hL=(%7.2f,%7.2f,%7.2f) fL=(%7.2f,%7.2f,%7.2f)"
                  % (frame, "%s %.2f" % (wmn, wm), "%s %.2f" % (wen, we),
                     hl[0], hl[1], hl[2], fl[0], fl[1], fl[2]))
        prev_mat, prev_eul = mats, euls


if __name__ == "__main__":
    main()
