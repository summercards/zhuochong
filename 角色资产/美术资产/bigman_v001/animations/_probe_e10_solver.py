"""_probe_e10_solver —— E10 腿解算器验证：**世界空间两骨解 + 世界极点**。

动机（承接 `_probe_e10_legblend.py` 的实测）：
  · 纯欧拉混合在 t=0.1 就让鞋底掉到 **−92.81 mm**、踝自身入地 −13 mm
    ⟹ `A.blend` 在「站立↔仰卧」之间**不是合法的链插值**，不能用。
  · E09 的 `leg_ik` 带 `tilt_deg` 小角假设，仰卧（rx=−86）时不可靠。

本解算器（`leg_solve`）：
  给定 髋 h（世界）、踝目标 T（世界）、骨长 L1/L2、**极点 p**（世界，膝往哪边弯），
     u = (T−h)/d,  a = (L1²−L2²+d²)/(2d),  k = sqrt(L1²−a²)
     K = h + u·a + perp(p,u)·k          ← 膝的**世界位置**（不是欧拉角）
     thigh 世界方向 = (K−h)/L1,  shin 世界方向 = (T−K)/L2
  极点 p 取「**骨盆局部 −Y 的世界方向**」= 绕世界 X 转 pelvis_rx 后的 (0,−1,0)：
    站架 p ≈ (0,−1,0)（膝朝前）；仰卧 p ≈ (0,0,+1)（膝朝**上**）。
    这正是 `leg_ik` 的语义，但**没有小角假设**。

本探针回答两件事（决定 anim_death.py 的腿用哪种驱动）：
  ① 站架下 `leg_solve` + `aim_bone` 能否**逐位复现** `Idle_01@0` 的腿？
     若世界矩阵逐位相同 ⟹ 腿也可以全程走解算器，起点天然接缝，无需特判。
  ② 仰卧下 `leg_solve` 给出的膝高 / 踝位是否与 `probe_e10_baseline` 的 aim_bone
     结果一致（膝 z ≈ 116.7 / 踝 [211.8,−172.2,113.9]）？

运行：
    blender --background --factory-startup --python _probe_e10_solver.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                      # noqa: E402
import anim_idle_01 as IDLE               # noqa: E402
import probe_e10_baseline as PB           # noqa: E402

SIDES = ("L", "R")
TERM_KW = dict(pz=0.141, leg_dz=-0.06, foot_pitch=-15.0, foot_roll=45.0,
               arm_out=0.50, arm_fwd=0.10, wrist_z=0.055,
               neck_rx=-14.0, head_rx=-11.0, prx=-86.0)


def leg_pole(prx_deg, ry_deg=0.0):
    """极点 = 骨盆局部 −Y 的世界方向（膝的弯曲侧）。"""
    rot = (Matrix.Rotation(math.radians(ry_deg), 3, "Y")
           @ Matrix.Rotation(math.radians(prx_deg), 3, "X"))
    return (rot @ Vector((0.0, -1.0, 0.0))).normalized()


def leg_solve(hip, target, l1, l2, pole):
    """返回 (thigh 世界方向, shin 世界方向, 膝世界位置, 是否被可达上限截断)。"""
    d = Vector(target) - Vector(hip)
    dist = d.length
    limit = (l1 + l2) * 0.9995
    clipped = dist > limit
    if clipped:
        d = d.normalized() * limit
        dist = limit
    dist = max(dist, abs(l1 - l2) + 1e-4)
    u = d.normalized()
    a = (l1 * l1 - l2 * l2 + dist * dist) / (2.0 * dist)
    h2 = max(0.0, l1 * l1 - a * a)
    h = math.sqrt(h2)
    pv = Vector(pole).normalized()
    n = pv - u * pv.dot(u)
    if n.length < 1e-6:
        n = Vector((0.0, 0.0, 1.0)) - u * u.z
    n.normalize()
    knee = Vector(hip) + u * a + n * h
    dir_u = (knee - Vector(hip)).normalized()
    dir_f = (Vector(target) - knee).normalized()
    return dir_u, dir_f, knee, clipped


def mats(arm):
    return {b.name: (arm.matrix_world @ b.matrix).copy()
            for b in arm.pose.bones}


def delta(a, b):
    pos = (a.translation - b.translation).length * 1000.0
    worst = 0.0
    for i in range(3):
        va, vb = a.to_3x3().col[i], b.to_3x3().col[i]
        cos = max(-1.0, min(1.0, va.normalized().dot(vb.normalized())))
        worst = max(worst, math.degrees(math.acos(cos)))
    return pos, worst


def main():  # noqa: C901
    arm, _m = A.open_animation_project()
    A.setup_scene()

    # ---------------- ① 站架：解算器 + aim_bone 能否复现 Idle_01@0 -------------
    ref_pose = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, ref_pose)
    ref_mats = mats(arm)
    ref_ankle = {s: Vector(PB.bone_world(arm, "foot." + s, "head"))
                 for s in SIDES}
    ref_hip = {s: Vector(PB.bone_world(arm, "thigh." + s, "head"))
               for s in SIDES}

    # 用解算器重建同一姿（躯干欧拉照抄 ref_pose，腿走解算器）
    pose = dict(ref_pose)
    A.apply_pose(arm, pose)
    l1 = arm.data.bones["thigh.L"].length
    l2 = arm.data.bones["shin.L"].length
    pole = leg_pole(4.0)
    info = {}
    for side in SIDES:
        hip = Vector(PB.bone_world(arm, "thigh." + side, "head"))
        du, df, knee, clipped = leg_solve(hip, ref_ankle[side], l1, l2, pole)
        pose["thigh." + side] = A.aim_bone(arm, "thigh." + side, du)
        A.apply_pose(arm, pose)
        pose["shin." + side] = A.aim_bone(arm, "shin." + side, df)
        A.apply_pose(arm, pose)
        info[side] = {
            "knee_calc": [round(v * 1000.0, 1) for v in knee],
            "clipped": clipped,
        }
    for side in SIDES:
        pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
        A.apply_pose(arm, pose)
    new_mats = mats(arm)

    worst_pos, worst_dir, worst_at = 0.0, 0.0, None
    for name in ref_mats:
        p, dg = delta(new_mats[name], ref_mats[name])
        if p > worst_pos or dg > worst_dir:
            worst_at = name
        worst_pos, worst_dir = max(worst_pos, p), max(worst_dir, dg)
    print("E10SV_REST_REBUILD %s" % json.dumps({
        "max_pos_mm": round(worst_pos, 4), "max_dir_deg": round(worst_dir, 4),
        "at": worst_at,
        "knee_calc": info,
    }, ensure_ascii=False))
    per = {}
    for name in ("thigh.L", "shin.L", "foot.L", "toe.L",
                 "thigh.R", "shin.R", "foot.R", "toe.R"):
        p, dg = delta(new_mats[name], ref_mats[name])
        per[name] = {"pos_mm": round(p, 4), "dir_deg": round(dg, 4)}
    print("E10SV_REST_PERBONE %s" % json.dumps(per, ensure_ascii=False))

    # ---------------- ② 仰卧：解算器 vs 探测值 ---------------------------------
    A.apply_pose(arm, {})                      # 清空
    term_pose = PB.build_supine(arm, **TERM_KW)
    A.apply_pose(arm, term_pose)
    aim_ankle = {s: Vector(PB.bone_world(arm, "foot." + s, "head"))
                 for s in SIDES}
    aim_knee = {s: Vector(PB.bone_world(arm, "shin." + s, "head"))
                for s in SIDES}
    sup_prof = PB.profile()
    print("E10SV_AIM_TARGETS %s" % json.dumps({
        "ankle": {s: [round(v * 1000.0, 1) for v in aim_ankle[s]]
                  for s in SIDES},
        "knee": {s: [round(v * 1000.0, 1) for v in aim_knee[s]]
                 for s in SIDES},
        "low": round(min(sup_prof.values()), 2),
    }, ensure_ascii=False))

    # 躯干照抄仰卧姿（欧拉），腿重走解算器
    torso = {k: v for k, v in term_pose.items()
             if not k.startswith(("thigh.", "shin.", "foot.", "toe."))}
    pose2 = dict(torso)
    A.apply_pose(arm, pose2)
    pole2 = leg_pole(-86.0)
    for side in SIDES:
        hip = Vector(PB.bone_world(arm, "thigh." + side, "head"))
        du, df, knee, clipped = leg_solve(hip, aim_ankle[side], l1, l2, pole2)
        pose2["thigh." + side] = A.aim_bone(arm, "thigh." + side, du)
        A.apply_pose(arm, pose2)
        pose2["shin." + side] = A.aim_bone(arm, "shin." + side, df)
        A.apply_pose(arm, pose2)
    for side in SIDES:
        pose2["foot." + side] = PB.keep_foot_orient(arm, "foot." + side,
                                                    -15.0, 45.0 * (1 if side == "L" else -1))
        A.apply_pose(arm, pose2)
    A.apply_pose(arm, pose2)
    prof2 = PB.profile()
    r = {}
    for side in SIDES:
        k = Vector(PB.bone_world(arm, "shin." + side, "head"))
        an = Vector(PB.bone_world(arm, "foot." + side, "head"))
        r[side] = {
            "knee_mm": [round(v * 1000.0, 1) for v in k],
            "knee_err_mm": round((k - aim_knee[side]).length * 1000.0, 2),
            "ankle_mm": [round(v * 1000.0, 1) for v in an],
            "ankle_err_mm": round((an - aim_ankle[side]).length * 1000.0, 2),
        }
    print("E10SV_SUPINE_SOLVE %s" % json.dumps({
        "per_side": r, "low": round(min(prof2.values()), 2),
        "part": min(prof2.items(), key=lambda kv: kv[1])[0],
        "trouser_min": round(min(prof2.get("Trouser_L", 1e9),
                                 prof2.get("Trouser_R", 1e9)), 2),
    }, ensure_ascii=False))
    print("E10SV_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E10SV_FAILURE " + traceback.format_exc())
