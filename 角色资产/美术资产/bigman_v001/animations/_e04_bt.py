"""临时：打印臂局部旋转（站架 vs IK）夹角。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("SKIP_RENDER", "1")

import anim_spawn as S                        # noqa: E402

arm, meshes = S.boot()
for frame in range(0, 26):
    print("E04_F frame=%d" % frame)
    S.spawn_pose(arm, frame)
