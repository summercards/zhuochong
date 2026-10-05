"""E04 诊断 5：复现 main() 流水线，定位
   ① `forearm.L` 在 f=8 的 111°/帧 是**真转**还是**欧拉表示跳**；
   ② `loop_angle_deg = 360` 是哪根骨、首末各是多少。
只打印，不改任何正式文件。
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

    print("=== RAW keyframe first/last diff (before compat) ===")
    for name in sorted(set(kfs[0][1]) | set(kfs[-1][1])):
        if name.startswith("@"):
            continue
        a = kfs[0][1].get(name, (0.0, 0.0, 0.0))
        b = kfs[-1][1].get(name, (0.0, 0.0, 0.0))
        d = max(abs(x - y) for x, y in zip(a, b))
        if d > 1e-6:
            print("  %-14s first=%s last=%s maxdiff=%.3f"
                  % (name, tuple(round(v, 2) for v in a),
                     tuple(round(v, 2) for v in b), d))

    kfs = S.compat_euler(kfs)
    print("=== after compat_euler ===")
    for name in sorted(set(kfs[0][1]) | set(kfs[-1][1])):
        if name.startswith("@"):
            continue
        a = kfs[0][1].get(name, (0.0, 0.0, 0.0))
        b = kfs[-1][1].get(name, (0.0, 0.0, 0.0))
        d = max(abs(x - y) for x, y in zip(a, b))
        if d > 1e-6:
            print("  %-14s first=%s last=%s maxdiff=%.3f"
                  % (name, tuple(round(v, 2) for v in a),
                     tuple(round(v, 2) for v in b), d))

    kfs = S.seam_canonicalize(kfs)
    print("=== after seam_canonicalize ===")
    for name in sorted(set(kfs[0][1]) | set(kfs[-1][1])):
        if name.startswith("@"):
            continue
        a = kfs[0][1].get(name, (0.0, 0.0, 0.0))
        b = kfs[-1][1].get(name, (0.0, 0.0, 0.0))
        d = max(abs(x - y) for x, y in zip(a, b))
        if d > 1e-6:
            print("  %-14s first=%s last=%s maxdiff=%.3f"
                  % (name, tuple(round(v, 2) for v in a),
                     tuple(round(v, 2) for v in b), d))

    meta = {"anim_id": S.NAME, "loop": False}
    action, meta = A.build_action(arm, S.NAME + "_DIAG", kfs, meta)
    samples = A.sample_animation(arm, action, S.START, S.END, meshes)

    print("=== sample first/last euler diff ===")
    for name in sorted(set(samples[0]["euler"]) | set(samples[-1]["euler"])):
        a = samples[0]["euler"].get(name, (0.0, 0.0, 0.0))
        b = samples[-1]["euler"].get(name, (0.0, 0.0, 0.0))
        d = max(abs(x - y) for x, y in zip(a, b))
        if d > 1e-4:
            print("  %-14s first=%s last=%s maxdiff=%.3f"
                  % (name, tuple(round(v, 2) for v in a),
                     tuple(round(v, 2) for v in b), d))

    print("=== per-frame euler step (top offenders, f%02d..%02d) ===")
    rows = []
    for i in range(1, len(samples)):
        ea, eb = samples[i - 1]["euler"], samples[i]["euler"]
        for name in set(ea) | set(eb):
            va = ea.get(name, (0.0, 0.0, 0.0))
            vb = eb.get(name, (0.0, 0.0, 0.0))
            for axis, (x, y) in enumerate(zip(va, vb)):
                if abs(x - y) > 8.0:
                    rows.append((samples[i]["frame"], name, axis, x, y))
    for frame, name, axis, x, y in rows:
        print("  f=%3d %-14s axis=%d  %.1f -> %.1f  (%.1f)"
              % (frame, name, axis, x, y, y - x))

    print("=== forearm.L / hand.L / upperarm.L euler by frame 0..26 ===")
    for i in range(0, min(27, len(samples))):
        s = samples[i]
        line = "f=%3d" % s["frame"]
        for nm in ("upperarm.L", "forearm.L", "hand.L"):
            v = s["euler"].get(nm, (0.0, 0.0, 0.0))
            line += " | %s %s" % (nm.split(".")[0][:5],
                                  "(" + ",".join("%7.1f" % q for q in v) + ")")
        print(line)


if __name__ == "__main__":
    main()
