"""E04 诊断 9：打印 hand.L 的
  · blend 原始输出（compat 之前）
  · compat_euler 之后
  · 最终 action 采样值
定位 85°/帧 到底是哪一步引入的。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy                                     # noqa: E402
import anim_lib as A                           # noqa: E402
import anim_spawn as S                         # noqa: E402


def fmt(v):
    return "(%7.2f,%7.2f,%7.2f)" % v


def main():
    arm, meshes = S.boot()
    kfs = [(f, S.spawn_pose(arm, f)) for f in range(S.START, S.END + 1)]
    after = dict(kfs)
    ck = S.compat_euler([(f, dict(p)) for f, p in kfs])
    ckd = dict(ck)
    sk = S.seam_canonicalize([(f, dict(p)) for f, p in ck])
    skd = dict(sk)
    meta = {"anim_id": S.NAME, "loop": False}
    action, _ = A.build_action(arm, S.NAME + "_DIAG9", sk, meta)
    samples = A.sample_animation(arm, action, S.START, S.END, meshes)
    smp = {s["frame"]: s for s in samples}

    print("%-4s %-26s %-26s %-26s %-26s"
          % ("f", "blend(raw)", "compat", "seam_canon", "sampled"))
    prev = None
    for frame in range(90, 103):
        b = tuple(after[frame].get("hand.L", (0.0, 0.0, 0.0)))
        c = tuple(ckd[frame].get("hand.L", (0.0, 0.0, 0.0)))
        s = tuple(skd[frame].get("hand.L", (0.0, 0.0, 0.0)))
        p = tuple(smp[frame]["euler"].get("hand.L", (0.0, 0.0, 0.0)))
        step = ""
        if prev is not None:
            step = " step=%.2f" % max(abs(x - y) for x, y in zip(prev, p))
        print("%-4d %-26s %-26s %-26s %-26s%s"
              % (frame, fmt(b), fmt(c), fmt(s), fmt(p), step))
        prev = p


if __name__ == "__main__":
    main()
