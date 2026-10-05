"""E04 快速迭代探针：复现 main() 的建帧流水线，打印
  · euler 口径 top-N 逐帧最大单轴步
  · matrix 口径 top-N 逐帧最大真实旋转步
  · 穿模 top-N（非拇指体内顶点 / 最深带符号距离）
不做渲染、不落盘。迭代用。
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy                                     # noqa: E402
from mathutils import Vector                   # noqa: E402
import anim_lib as A                           # noqa: E402
import anim_spawn as S                         # noqa: E402

TOP = int(os.environ.get("E04_TOP", "14"))
BONES = ("upperarm.L", "forearm.L", "hand.L",
         "upperarm.R", "forearm.R", "hand.R")


def main():
    arm, meshes = S.boot()
    kfs = [(f, S.spawn_pose(arm, f)) for f in range(S.START, S.END + 1)]
    kfs = S.compat_euler(kfs)
    kfs = S.seam_canonicalize(kfs)
    meta = {"anim_id": S.NAME, "loop": False}
    action, meta = A.build_action(arm, S.NAME + "_PROBE", kfs, meta)
    samples = A.sample_animation(arm, action, S.START, S.END, meshes)

    eul = []
    for i in range(1, len(samples)):
        ea, eb = samples[i - 1]["euler"], samples[i]["euler"]
        for name in set(ea) | set(eb):
            va = ea.get(name, (0.0, 0.0, 0.0))
            vb = eb.get(name, (0.0, 0.0, 0.0))
            eul.append((max(abs(x - y) for x, y in zip(va, vb)),
                        samples[i]["frame"], name))
    eul.sort(reverse=True)
    print("--- euler step top%d ---" % TOP)
    for d, f, n in eul[:TOP]:
        print("   %7.2f  f=%3d %s" % (d, f, n))

    prev = None
    mat = []
    for frame in range(S.START, S.END + 1):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        cur = {n: arm.pose.bones[n].matrix.to_3x3().copy()
               for n in A.BONE_LIST if n in arm.pose.bones} \
            if hasattr(A, "BONE_LIST") else \
            {n: arm.pose.bones[n].matrix.to_3x3().copy()
             for n in arm.pose.bones.keys()}
        if prev is not None:
            for name in set(cur) & set(prev):
                a, b = prev[name], cur[name]
                for c in range(3):
                    va = a.col[c].normalized()
                    vb = b.col[c].normalized()
                    d = math.degrees(math.acos(max(-1.0, min(1.0,
                                                             va.dot(vb)))))
                    mat.append((d, frame, name))
        prev = cur
    mat.sort(reverse=True)
    print("--- matrix step top%d ---" % TOP)
    for d, f, n in mat[:TOP]:
        print("   %7.2f  f=%3d %s" % (d, f, n))

    print("--- pierce (non-thumb inside) top%d ---" % TOP)
    rows = []
    for frame in list(range(S.START, S.END + 1, 3)):
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        S.torso_bvh_reset()
        tree = S.torso_bvh()
        for side in S.SIDES:
            c = S.hand_mesh_stats(side, tree=tree, step=4)
            rows.append((c["inside_nothumb"], c["deepest_nothumb_mm"],
                         frame, side))
    rows.sort(key=lambda r: (-r[0], r[1] if r[1] is not None else 0.0))
    for inside, deep, frame, side in rows[:TOP]:
        print("   inside=%4d deep=%8.2f  f=%3d %s" % (inside, deep, frame, side))

    print("--- hint margin %.4f ---" % S.MIN_HINT_MARGIN)

    # 万向节锁越界检查：逐帧 |ry|
    print("--- |ry| near 90 (hand.L/R, forearm.L/R) ---")
    hits = []
    for s in samples:
        for n in ("hand.L", "hand.R", "forearm.L", "forearm.R"):
            v = s["euler"].get(n)
            if v is None:
                continue
            ry = v[1]
            ry = abs(((ry + 180.0) % 360.0) - 180.0)
            if ry > 78.0:
                hits.append((ry, s["frame"], n))
    hits.sort(reverse=True)
    for ry, f, n in hits[:TOP]:
        print("   |ry|=%6.2f  f=%3d %s" % (ry, f, n))


if __name__ == "__main__":
    main()
