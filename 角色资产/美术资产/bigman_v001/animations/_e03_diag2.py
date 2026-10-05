"""E03 四处红项的根因数据一次性打全（只读）。

(A) 手骨热点帧：`along`（肩→拳心）、`∠(along, −胸法线)`、`face_blend`、
    euler(rx,ry,rz)、**矩阵步**、**euler 步**、**穷举 54 候选后的最小 euler 步**。
    ⟹ 判定 f=18 / f=76 是「真转」还是「欧拉病态」，以及 ramp 速率是不是元凶。
(B) `push_out` 的原始/推出目标：`resolve_fist` 的原点、`torso_query` 的最近面点
    与法线、推出后的点与位移 ⟹ 判定 L 拳面 14.71 mm 与推出抖动来自哪里。
(C) 收招段 f=85..96 的 arm_env 斜率 ⟹ 判定 `no_snap_stop` 16.58° 的来源。

用法：
  blender -b --factory-startup -P _e03_diag2.py
"""
import os
import sys
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import anim_rage as R  # noqa: E402
import anim_lib as A  # noqa: E402

arm, meshes = R.boot()


def mat_step(a, b):
    q = (a.transposed() @ b).to_quaternion()
    return math.degrees(abs(q.angle))


def min_euler_step(ea, eb):
    """等价族（2 换元 x 3^3 平移）里「最大单轴步」的最小值。"""
    best = None
    for fam in (0, 1):
        a = (list(ea) if fam == 0
             else [ea[0] + 180.0, 180.0 - ea[1], ea[2] + 180.0])
        for kx in (-1, 0, 1):
            for ky in (-1, 0, 1):
                for kz in (-1, 0, 1):
                    cand = [a[0] + 360.0 * kx, a[1] + 360.0 * ky,
                            a[2] + 360.0 * kz]
                    step = max(abs(x - y) for x, y in zip(cand, eb))
                    if best is None or step < best:
                        best = step
    return best


print("=" * 104)
print("(A) 手骨热点帧（R 侧优先，本支 matrix/euler 峰都在 R）")
print("  侧    f    env  blend   along·(-nrm)  ∠      rx       ry       rz"
      "     euler步   mat步  穷举步")
prev = {}
for f in list(range(12, 31)) + list(range(70, 82)) + list(range(85, 97)):
    A.apply_pose(arm, R.rage_pose(arm, f))
    bpy.context.view_layer.update()
    env, blend = R.arm_env(f), R.face_blend(f)
    tg = R.fist_targets(arm, f)
    for side in ("R", "L"):
        surf, nrm = R.chest_surface(arm, side)
        sh = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        along = Vector(tg[side]) - sh
        along = (along.normalized() if along.length > 1e-6
                 else Vector((0.0, 0.0, -1.0)))
        dotn = along.dot(-nrm)
        ang = math.degrees(math.acos(max(-1.0, min(1.0, dotn))))
        b = "hand." + side
        e = [math.degrees(v) for v in arm.pose.bones[b].rotation_euler]
        m = arm.pose.bones[b].matrix.to_3x3().normalized()
        de = dm = dex = None
        if b in prev:
            pe, pm = prev[b]
            de = max(abs(x - y) for x, y in zip(e, pe))
            dm = mat_step(pm, m)
            dex = min_euler_step(pe, e)
        prev[b] = (e, m)
        if de is not None and (de > 8 or dm > 15 or f >= 88):
            print("%4s %4d %6.3f %6.3f   %+8.3f  %6.1f %8.1f %8.1f %8.1f"
                  "   %7.2f  %7.2f  %7.2f"
                  % (side, f, env, blend, dotn, ang, e[0], e[1], e[2],
                     de, dm, dex))
    if f < 31:
        print("-" * 104)

print("=" * 104)
print("(B) push_out 原始/推出（f=28 / 51 / 52）")
for f in (28, 51, 52):
    A.apply_pose(arm, R.rage_pose(arm, f))
    bpy.context.view_layer.update()
    print("f=%d  FIST_MIN_CLEAR_MM=%.2f  TOUCH_OFF=%.1f mm  blend=%.3f"
          % (f, R.FIST_MIN_CLEAR_MM, R.TOUCH_OFF * 1000.0, R.face_blend(f)))
    for side in R.SIDES:
        surf, nrm = R.chest_surface(arm, side)
        raw = R.resolve_fist("CHEST", side, arm)
        r_gap, r_pt, r_nrm = R.torso_query(raw)
        pushed = R.push_out(raw, R.FIST_MIN_CLEAR_MM)
        p_gap, p_pt, p_nrm = R.torso_query(pushed)
        print("  [%s] 胸面=(%+.3f %+.3f %+.3f) nrm=(%+.3f %+.3f %+.3f)"
              % (side, surf.x, surf.y, surf.z, nrm.x, nrm.y, nrm.z))
        print("       raw gap=%+7.2f  最近面=(%+.3f %+.3f %+.3f)"
              " ∠(最近法线,nrm)=%5.1f°  raw沿nrm=%+7.2f"
              % (r_gap, r_pt.x, r_pt.y, r_pt.z,
                 math.degrees(math.acos(max(-1.0, min(1.0,
                                                     r_nrm.dot(nrm))))),
                 (raw - surf).dot(nrm) * 1000.0))
        print("       pushed gap=%+7.2f  位移=%7.2f mm  (raw→pushed)"
              % (p_gap, (pushed - raw).length * 1000.0))

print("=" * 104)
print("(C) 收招段臂包络（ARM_DN_AT=%d TOTAL=%d）" % (R.ARM_DN_AT, R.TOTAL))
for f in range(R.ARM_DN_AT - 2, R.TOTAL + 1):
    print("   f=%3d env=%.4f  Δ=%+.4f" % (f, R.arm_env(f),
                                          R.arm_env(f) - R.arm_env(f - 1)))
print("E03_DIAG2_DONE")
