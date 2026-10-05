import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Matrix
import anim_lib as A
import anim_spawn as S

NAME = os.environ.get("NAMES", "forearm.L")
F0 = int(os.environ.get("F0", "56")); F1 = int(os.environ.get("F1", "60"))

arm, meshes = S.boot()
kfs = [(f, S.spawn_pose(arm, f)) for f in range(S.START, S.END + 1)]
raw = [dict(p) for (_f, p) in kfs]
kfs = S.compat_euler(kfs)

def mat_of(pose, n):
    # 用 euler 建矩阵（骨局部）
    rx, ry, rz = pose.get(n, (0.0, 0.0, 0.0))
    return (Matrix.Rotation(math.radians(rz), 3, 'Z') @
            Matrix.Rotation(math.radians(ry), 3, 'Y') @
            Matrix.Rotation(math.radians(rx), 3, 'X'))

for i in range(F0, F1 + 1):
    ra, rb = raw[i - 1], raw[i]
    ca, cb = kfs[i - 1][1], kfs[i][1]
    va, vb = ra.get(NAME, (0, 0, 0)), rb.get(NAME, (0, 0, 0))
    d_raw = max(abs(x - y) for x, y in zip(va, vb))
    ka, kb = ca.get(NAME, (0, 0, 0)), cb.get(NAME, (0, 0, 0))
    d_cmp = max(abs(x - y) for x, y in zip(ka, kb))
    # 全等价族里的最优 max-step
    best = 1e9
    for fa in S._euler_family(va):
        for fb in S._euler_family(vb):
            best = min(best, max(abs(x - y) for x, y in zip(fa, fb)))
    print("f=%3d raw=%.2f compat=%.2f family_min=%.2f | raw=%s compat=%s" %
          (i, d_raw, d_cmp, best, tuple(round(v,1) for v in va), tuple(round(v,1) for v in ka)))
