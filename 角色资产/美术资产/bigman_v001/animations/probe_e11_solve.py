"""probe_e11_solve.py —— E11 右腿参数**真机迭代求解器**（只读，不渲染）。

★★★ 为什么不能像 `probe_e11_foot.py` 那样「事先量一张鞋底深度表」：
    实测发现鞋是**跨踝蒙皮**的（`Shoe_Sole_*` 同时受 `shin` 与 `foot` 影响）
    ⟹ 「鞋底到踝的深度」**不是 (fp, roll) 的函数，还依赖小腿的世界姿态**。
    同一组 `fp=0, roll=0`：
      · 父骨摆成 `TERM`（仰卧，小腿平躺）⟹ 深度 **110.7 mm**
      · 父骨摆成站姿（`shin.R` rx = +43°）    ⟹ 深度 **≈ 80.8 mm**（站姿踝 79.8）
    差 **30 mm** —— 任何「离线深度表」都会把鞋底算错 30 mm，这正是 v3
    `rvw_body_low_min_mm = -65.02` 里那几十毫米的来源。

★★★ 所以改成**闭环**：在**真实姿态**上量鞋底，把误差回灌到踝 z，
    再在**同一姿态的髋**上用一维搜索定踝 y 去命中膝高目标。迭代 5 轮。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e11_solve.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_death as D        # noqa: E402
import anim_revive as RV      # noqa: E402

L1, L2 = D.L1, D.L2
SIDES = ("L", "R")

# 需要反解的帧（f16 之前一律 TERM、f104 之后一律 REST，都不动）
KEY_FRAMES = (24, 30, 38, 44, 52, 60, 68, 84, 92, 100)
# 右鞋鞋底**离地目标**（mm）：贴着地走 / 收腿时抬一点 / 半跪与蹬起全程贴地
SOLE_WANT = {24: 12.0, 30: 26.0, 38: 20.0, 44: 12.0, 52: 5.0, 60: 2.0,
             68: 2.0, 84: 2.0, 92: 2.0, 100: 2.0}
# 右膝**世界高度目标**（mm）：仰卧 140.5 → 收腿抬起 → 半跪落回 107 → 站起收敛
KNEE_WANT = {24: 175.0, 30: 215.0, 38: 200.0, 44: 170.0, 52: 134.0,
             60: 112.0, 68: 107.0, 84: 150.0, 92: 250.0, 100: 360.0}
# 踝 y 的**参考路径**（只用来在「目标可达的整段解」里挑最贴近的那一个，
# 不让搜索跳到另一支解上去）
AY_REF = {24: -0.205, 30: -0.218, 38: -0.150, 44: 0.050, 52: 0.260,
          60: 0.400, 68: 0.460, 84: 0.400, 92: 0.290, 100: 0.190}
AY_WEIGHT = 30.0      # 每偏离参考路径 1 m 折算成多少 mm 的膝高误差

arm, meshes = RV.boot()


def both_branches(hip, tgt):
    """在**给定踝**上，两个膝分支的世界 z（mm）。返回 (z_plus, z_minus)。"""
    hip = Vector(hip)
    d = Vector(tgt) - hip
    dist = d.length
    limit = (L1 + L2) * D.REACH_MAX_RATIO
    dist = max(min(dist, limit), abs(L1 - L2) + 1e-4)
    if d.length < 1e-9:
        return None
    u = d.normalized()
    a = (L1 * L1 - L2 * L2 + dist * dist) / (2.0 * dist)
    h = math.sqrt(max(0.0, L1 * L1 - a * a))
    s = math.hypot(u.y, u.z)
    if s < 1e-6:
        return None
    base = Vector((0.0, u.z, -u.y)) / s
    kz = (hip + u * a).z
    return ((kz + base.z * h) * 1000.0, (kz - base.z * h) * 1000.0)


def measure(frame):
    """把第 `frame` 帧真的摆出来，量：鞋底(左右) / 右膝 z / 右踝 / 右髋。"""
    RV.revive_pose(arm, frame)
    sole = RV._sole_low_mm()
    return (sole,
            A.bone_world(arm, "shin.R").z * 1000.0,
            Vector(A.bone_world(arm, "foot.R")),
            Vector(A.bone_world(arm, "thigh.R", "head")))


CUR = {}
for f in KEY_FRAMES:
    tgt = RV._ankle_target(f, "R")
    CUR[f] = [tgt.x, tgt.y, tgt.z]


def rebuild():
    keys = [(0, "TERM"), (16, "TERM")]
    for f in sorted(CUR):
        keys.append((f, (CUR[f][0], CUR[f][1], CUR[f][2])))
    keys += [(104, "REST"), (120, "REST")]
    RV.ANKLE_KEYS["R"] = tuple(keys)


rebuild()
print("# ================= E11S_ITER 迭代 =================")
for rnd in range(5):
    moved = 0.0
    for f in KEY_FRAMES:
        sole, knee, ank, hip = measure(f)
        err_z = SOLE_WANT[f] - sole["R"]
        CUR[f][2] += err_z / 1000.0
        az = CUR[f][2]
        best = None
        for step in range(-1200, 1201):
            ay = AY_REF[f] + step * 0.001
            zs = both_branches(hip, Vector((CUR[f][0], ay, az)))
            if zs is None:
                continue
            for kz in zs:
                cost = abs(kz - KNEE_WANT[f]) + AY_WEIGHT * abs(ay - AY_REF[f])
                if best is None or cost < best[0]:
                    best = (cost, ay, kz)
        moved = max(moved, abs(best[1] - CUR[f][1]))
        CUR[f][1] = best[1]
        rebuild()
    print("E11S_ITER round=%d max_ay_move_mm=%.1f" % (rnd, moved * 1000.0))
    if moved < 1e-5:
        break

print("# ================= E11S_FINAL 结果 =================")
for f in KEY_FRAMES:
    sole, knee, ank, hip = measure(f)
    print("E11S_FINAL f=%3d ank=(%+.3f,%+.4f,%.4f) hip=(%+.3f,%+.3f) "
          "soleR=%+7.2f soleL=%+7.2f kneeR=%7.2f (want %6.1f) "
          "| 踝步 %.1f mm"
          % (f, CUR[f][0], CUR[f][1], CUR[f][2], hip.y, hip.z,
             sole["R"], sole["L"], knee, KNEE_WANT[f],
             math.hypot(hip.y, 0.0) * 0))

print("# ================= E11S_KEYS 可直接粘贴 =================")
print("ANKLE_KEYS_R = (")
print('    (0, "TERM"), (16, "TERM"),')
for f in sorted(CUR):
    print("    (%d, (%.3f, %+.4f, %.4f))," % (f, CUR[f][0], CUR[f][1], CUR[f][2]))
print('    (104, "REST"), (120, "REST"),')
print(")")
print("KNEE_Z_R = (")
print("    (0, 0.1405), (16, 0.1405),")
for f in sorted(KNEE_WANT):
    print("    (%d, %.4f)," % (f, KNEE_WANT[f] / 1000.0))
print("    (104, 0.4284), (120, 0.4284),")
print(")")

print("# ================= E11S_SCAN 全程逐帧（预测门禁）=========")
prev = None
worst_ank = (0.0, None)
for f in range(0, RV.END + 1):
    sole, knee, ank, hip = measure(f)
    lowa = min(sole["L"], sole["R"])
    flag = ""
    if lowa < RV.BODY_BAND[0] or lowa > RV.BODY_BAND[1]:
        flag += " <<BAND"
    if knee < RV.KNEE_RADIUS_MM - RV.KNEE_PATH_TOL_MM:
        flag += " <<KNEE"
    if prev is not None:
        d = (ank - prev).length * 1000.0
        if d > worst_ank[0]:
            worst_ank = (d, f)
    prev = ank.copy() if hasattr(ank, "copy") else ank
    print("E11S_SCAN f=%3d soleL=%+7.2f soleR=%+7.2f kneeR=%7.2f "
          "ankR=(%+.3f,%+.4f,%+.4f)%s"
          % (f, sole["L"], sole["R"], knee, ank.x, ank.y, ank.z, flag))
print("E11S_WORST ankle_step_mm=%s" % (worst_ank,))
