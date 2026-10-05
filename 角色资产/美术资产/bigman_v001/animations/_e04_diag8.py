"""E04 诊断 8：打印 f=86..108 的
  · 站架臂欧拉（`station`）
  · IK 臂欧拉（`ikpt`，原始）
  · `_nearest_family(ikpt, station)` 的结果 b 与 span
  · env
定位 `_blend_local` 的族选择是否在相邻帧之间跳支。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy                                     # noqa: E402
from mathutils import Vector                   # noqa: E402
import anim_lib as A                           # noqa: E402
import anim_spawn as S                         # noqa: E402


def main():
    arm, meshes = S.boot()
    print("%-4s %-4s | %-26s %-26s %-26s %s"
          % ("f", "env", "station hand.L", "ikpt hand.L", "nearest hand.L", "span"))
    for frame in range(86, 109):
        pose = S.spawn_pose(arm, frame)
        # 复算 blend 的输入
        spec = S.torso_at(frame)
        base = dict(pose)
        A.apply_pose(arm, base)
        ik = dict(base)
        dy, dz = spec["loc"]
        S.seat_arm(arm, ik, S.fist_targets(arm, frame,
                                           Vector((0.0, dy, dz))),
                   S.arm_env(frame))
        env = S.arm_env(frame)
        st = {}
        # station 臂姿态 = BASE 里的臂值
        for nm in S.ARM_BONES:
            st[nm] = tuple(S.BASE.get(nm, (0.0, 0.0, 0.0)))
        a = st["hand.L"]
        b_raw = tuple(ik["hand.L"])
        b = S._nearest_family(b_raw, a)
        span = max(abs(y - x) for x, y in zip(a, b))
        print("%-4d %-4.3f | (%7.2f,%7.2f,%7.2f) (%7.2f,%7.2f,%7.2f) "
              "(%7.2f,%7.2f,%7.2f) %7.2f"
              % (frame, env, a[0], a[1], a[2],
                 b_raw[0], b_raw[1], b_raw[2], b[0], b[1], b[2], span))


if __name__ == "__main__":
    main()
