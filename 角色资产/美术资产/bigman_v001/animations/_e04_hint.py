"""E04 诊断 10：记录逐帧 `y_dir`（前臂方向），评估各候选「恒定滚转基准」
在整个 f=0..120 扫程上的**最小法向投影余量**。余量越大 = 越不会退化翻帧。
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy                                     # noqa: E402
from mathutils import Vector                   # noqa: E402
import anim_lib as A                           # noqa: E402
import anim_spawn as S                         # noqa: E402

REC = {"L": [], "R": []}
_orig = S.orient_hand


def hooked(arm, side, y_dir, x_hint):
    REC[side].append(Vector(y_dir).normalized())
    return _orig(arm, side, y_dir, x_hint)


def main():
    S.orient_hand = hooked
    arm, meshes = S.boot()
    for frame in range(S.START, S.END + 1):
        S.spawn_pose(arm, frame)

    cands = {
        "world+X": Vector((1, 0, 0)),
        "world-X": Vector((-1, 0, 0)),
        "world+Y": Vector((0, 1, 0)),
        "world-Y": Vector((0, -1, 0)),
        "world+Z": Vector((0, 0, 1)),
        "world-Z": Vector((0, 0, -1)),
        "STATION_HAND_X": None,
        "ELBOW_DIR": None,
    }
    for side in ("L", "R"):
        cands["STATION_HAND_X_" + side] = Vector(S.STATION_HAND_X[side])
        cands["STATION_HAND_Y_" + side] = Vector(S.STATION_HAND_Y[side])
        cands["ELBOW_dir_" + side] = Vector(S.ELBOW_DIR[side]).normalized()
        cands["pole_dir_" + side] = Vector(S.STATION_POLE_DIR[side])

    print("%-22s %8s %8s %8s" % ("candidate", "min|L|", "min|R|", "worst"))
    rows = []
    for name, axis in cands.items():
        if axis is None:
            continue
        a = axis.normalized()
        mins = {}
        for side in ("L", "R"):
            m = 1.0
            for y in REC[side]:
                proj = (a - y * a.dot(y))
                m = min(m, proj.length)
            mins[side] = m
        rooms = S.ARM_BONES
        _ = rooms
        rows.append((min(mins["L"], mins["R"]), name, mins["L"], mins["R"]))
    rows.sort(reverse=True)
    for worst, name, ml, mr in rows:
        print("%-22s %8.4f %8.4f %8.4f" % (name, ml, mr, worst))


if __name__ == "__main__":
    main()
