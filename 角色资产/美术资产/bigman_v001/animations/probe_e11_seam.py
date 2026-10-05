"""probe_e11_seam —— E11 `Revive` 开工第一件测量（**不许照抄 E10 读数**）。

要回答清单 E11 详细计划 §0 / §1 里的四件事：
  1) 接缝**入**：`Death@120`（仰卧尸体）的**逐位**世界矩阵快照 + 关键几何
     （骨盆 / 头 / 双肘 / 双踝 / 逐件最低 z）。同时验证
     `anim_death.death_pose(arm, 120)` 复现的末姿与落盘 action 的 `Death@120`
     **逐位一致** —— 这是 E11 起点「直接取上游函数」的前提。
  2) 接缝**出**：`Idle_01@0` 的逐位快照 + 踝世界位置（`ANKLE_REST`）。
  3) ★ 与 D18 `GetUp_B` 的**可分性基准**（清单 §0 第 3 条 / §1 风险 2）：
     逐帧量 D18 的「单膝贴地（膝世界 z ≤ 150 mm）连续帧数」与最小膝高。
     E11 的设计分离维度 =「有明确的半跪**停顿**」⟹ 必须先把 D18 的读数钉死，
     否则「与 D18 撞车」这条无法被量化。
  4) ★ 半跪姿的**几何可行性**（清单 §0 第 1 条 / E10 日志 §六）：
     从尸体末姿出发，构造一个「右膝着地 + 左脚前踏 + 躯干前倾」的半跪姿，
     实测膝 / 踝 / 逐件最低 z，确认：膝能落到入地线以上（≥ 100.7 mm）、
     无穿地、且半跪姿与 D18 的**任何**帧都不同（57 骨世界矩阵朝向差 ≥ 15°）。

运行（离线，不需要 BlenderMCP 桥）：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_e11_seam.py
    E11_SEAM_RENDER=1   额外渲一张尸体末姿与半跪姿（默认不渲，加快迭代）
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A              # noqa: E402
import anim_idle_01 as IDLE       # noqa: E402
import anim_death as D            # noqa: E402

SIDES = ("L", "R")
RENDER = os.environ.get("E11_SEAM_RENDER") == "1"
KNEE_RADIUS_MM = 104.7            # 沿用 E09/E10 的膝网格半径实测值


def _b(key):
    return os.environ.get(key, "0").strip() not in ("", "0", "false", "False")


def world_mats(arm):
    return {pb.name: (arm.matrix_world @ pb.matrix).copy()
            for pb in arm.pose.bones}


def mat_delta(a, b):
    pos = (a.translation - b.translation).length * 1000.0
    worst = 0.0
    for index in range(3):
        va = a.to_3x3().col[index]
        vb = b.to_3x3().col[index]
        if va.length < 1e-9 or vb.length < 1e-9:
            continue
        cos = max(-1.0, min(1.0, va.normalized().dot(vb.normalized())))
        worst = max(worst, math.degrees(math.acos(cos)))
    return pos, worst


def worst_matrix_delta(mats_a, mats_b):
    wp, wd, wb = 0.0, 0.0, None
    for name in mats_a:
        if name not in mats_b:
            continue
        pos, deg = mat_delta(mats_a[name], mats_b[name])
        if deg > wd:
            wd, wb = deg, name
        wp = max(wp, pos)
    return wp, wd, wb


def profile():
    """逐网格对象的最低世界 z（毫米）。"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        out[obj.name] = min((matrix @ v.co).z for v in mesh.vertices) * 1000.0
        evaluated.to_mesh_clear()
    return out


def bone_world(arm, name, which="head"):
    pb = arm.pose.bones[name]
    point = pb.head if which == "head" else pb.tail
    return arm.matrix_world @ point


def geom(arm, prof):
    return {
        "pelvis": [round(v * 1000.0, 2) for v in bone_world(arm, "pelvis")],
        "head_mid": [round(v * 1000.0, 2) for v in bone_world(arm, "head")],
        "chest_tail": [round(v * 1000.0, 2)
                       for v in bone_world(arm, "chest", "tail")],
        "elbow.L": [round(v * 1000.0, 2)
                    for v in bone_world(arm, "forearm.L")],
        "elbow.R": [round(v * 1000.0, 2)
                    for v in bone_world(arm, "forearm.R")],
        "knee.L": [round(v * 1000.0, 2) for v in bone_world(arm, "shin.L")],
        "knee.R": [round(v * 1000.0, 2) for v in bone_world(arm, "shin.R")],
        "ankle.L": [round(v * 1000.0, 2) for v in bone_world(arm, "foot.L")],
        "ankle.R": [round(v * 1000.0, 2) for v in bone_world(arm, "foot.R")],
        "toe.L": [round(v * 1000.0, 2) for v in bone_world(arm, "toe.L", "tail")],
        "toe.R": [round(v * 1000.0, 2) for v in bone_world(arm, "toe.R", "tail")],
        "hand.L": [round(v * 1000.0, 2)
                   for v in bone_world(arm, "hand.L", "tail")],
        "fist_z": round(bone_world(arm, "hand.L", "tail").z * 1000.0, 2),
        "low_mm": round(min(prof.values()), 2),
        "low_part": min(prof.items(), key=lambda kv: kv[1])[0],
        "knee_min_z": round(min(bone_world(arm, "shin." + s).z
                                for s in SIDES) * 1000.0, 2),
    }


# =============================================================== 半跪姿原型
# ★ 与清单 §1 风险 6 一致的**右膝着地**半跪：骨盆前倾、右小腿贴地、左脚前踏。
#   ankle 目标按「世界空间两骨解」反求（见 anim_death.leg_solve）：
#     右（跪）：膝 z 要落在入地线 104.7 附近 ⟹ 踝取到身后 (y≈+0.98, z≈0.105)；
#     左（踏）：踝取到身前（≈ `Idle_01` 的前脚 y=−0.170）。
HALF_KNEEL_PELVIS = (0.320, 0.418, 28.0)     # (world_y, world_z, rx_deg)
HALF_KNEEL_TORSO = {
    "spine_01": (8.0, 0.0, 0.0), "spine_02": (8.0, 0.0, 0.0),
    "chest": (6.0, 0.0, 0.0), "neck": (-4.0, 0.0, 0.0),
    "head": (6.0, 0.0, 0.0),
    "shoulder.L": (-20.0, 0.0, 0.0), "shoulder.R": (-20.0, 0.0, 0.0),
}
HALF_KNEEL_ANKLE_R = (-0.120, 0.980, 0.105)
HALF_KNEEL_FOOT_PITCH = -6.0
HALF_KNEEL_FOOT_ROLL = 6.0


def build_half_kneel(arm, L1, L2, ankle_rest):
    """装配半跪姿（右膝着地）。返回 (pose, info)。"""
    py, pz, prx = HALF_KNEEL_PELVIS
    pose = {}
    pose["pelvis"] = (prx, 0.0, 0.0)
    pose.update(HALF_KNEEL_TORSO)
    pose["@loc"] = {"pelvis": A.wloc(0.0, py, pz - 0.900)}
    pose["root"] = (0.0, 0.0, 0.0)
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    pole = D.leg_pole(prx)
    targets = {"L": tuple(ankle_rest["L"]), "R": HALF_KNEEL_ANKLE_R}
    info = {}
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        tgt = Vector(targets[side])
        du, df, knee, clipped = D.leg_solve(hip, tgt, L1, L2, pole)
        pose["thigh." + side] = A.aim_bone(arm, "thigh." + side, du)
        A.apply_pose(arm, pose)
        pose["shin." + side] = A.aim_bone(arm, "shin." + side, df)
        A.apply_pose(arm, pose)
        info[side] = {
            "reach_mm": round((tgt - hip).length * 1000.0, 2),
            "knee_z_mm": round(knee.z * 1000.0, 2),
            "clipped": bool(clipped),
        }
    for side in SIDES:
        pose["foot." + side] = D.keep_foot_orient(
            arm, "foot." + side, HALF_KNEEL_FOOT_PITCH,
            HALF_KNEEL_FOOT_ROLL * (1.0 if side == "L" else -1.0))
        A.apply_pose(arm, pose)
    # 臂：垂在体侧略前（不是尸体姿的摊平，也不是站架）
    for bone, direction in (
            ("upperarm.L", (0.30, -0.20, -0.93)),
            ("forearm.L", (0.20, -0.34, -0.92)),
            ("hand.L", (0.16, -0.42, -0.89)),
            ("upperarm.R", (-0.30, -0.20, -0.93)),
            ("forearm.R", (-0.20, -0.34, -0.92)),
            ("hand.R", (-0.16, -0.42, -0.89))):
        pose[bone] = A.aim_bone(arm, bone, direction)
        A.apply_pose(arm, pose)
    return pose, info


def main():  # noqa: C901
    # ---- boot：直接复用 E10 的 boot（它会设好 BASE/TERM/ANKLE_REST/ANKLE_TERM/L1/L2）
    arm, meshes = D.boot()
    A.setup_scene()
    L1, L2 = D.L1, D.L2
    print("E11_LEG_LEN %s" % json.dumps({"L1": round(L1, 6),
                                         "L2": round(L2, 6)}))

    prof = profile()
    print("E11_ANKLE_REST %s" % json.dumps(
        {s: [round(v * 1000.0, 2) for v in D.ANKLE_REST[s]] for s in SIDES}))
    print("E11_ANKLE_TERM %s" % json.dumps(
        {s: [round(v * 1000.0, 2) for v in D.ANKLE_TERM[s]] for s in SIDES}))

    # ---------------------------------------------------------- 1) 接缝入
    death = bpy.data.actions.get("Death")
    if death is None:
        print("E11_DEATH_MISSING")
    else:
        arm.animation_data.action = death
        A._bind_slot(arm, death)
        bpy.context.scene.frame_set(120)
        bpy.context.view_layer.update()
        death_mats = world_mats(arm)
        death_prof = profile()
        print("E11_DEATH120_GEOM %s" % json.dumps(geom(arm, death_prof),
                                                  ensure_ascii=False))
        print("E11_DEATH120_EULER %s" % json.dumps(
            {b: [round(math.degrees(v), 4) for v in
                 arm.pose.bones[b].rotation_euler]
             for b in sorted(arm.pose.bones.keys())
             if any(abs(v) > 1e-9 for v in arm.pose.bones[b].rotation_euler)
             or any(abs(v) > 1e-9 for v in arm.pose.bones[b].location)},
            ensure_ascii=False))
        # ★ 关键前提：death_pose(arm, 120) 复现末姿吗？
        pose_fn = D.death_pose(arm, 120)
        A.apply_pose(arm, pose_fn)
        fn_mats = world_mats(arm)
        wp, wd, wb = worst_matrix_delta(fn_mats, death_mats)
        print("E11_DEATH_FN_MATCH %s" % json.dumps({
            "pos_mm": round(wp, 6), "dir_deg": round(wd, 6), "worst": wb,
            "ok": bool(wp <= 1e-6 and wd <= 1e-6)}, ensure_ascii=False))
        arm.animation_data.action = None

    # ---------------------------------------------------------- 2) 接缝出
    base = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, base)
    prof = profile()
    print("E11_IDLE0_GEOM %s" % json.dumps(geom(arm, prof),
                                           ensure_ascii=False))
    print("E11_IDLE0_EULER %s" % json.dumps(
        {k: [round(x, 4) for x in v] for k, v in base.items()
         if not k.startswith("@")}, ensure_ascii=False))
    print("E11_IDLE0_LOC %s" % json.dumps(
        {k: [round(x, 6) for x in v]
         for k, v in base.get("@loc", {}).items()}, ensure_ascii=False))
    idle_mats = world_mats(arm)

    # ★ Idle_01@0 落盘 action 与 idle_pose(arm,0.0) 是否逐位一致
    idle_act = bpy.data.actions.get("Idle_01")
    if idle_act is not None:
        arm.animation_data.action = idle_act
        A._bind_slot(arm, idle_act)
        bpy.context.scene.frame_set(0)
        bpy.context.view_layer.update()
        wp, wd, wb = worst_matrix_delta(idle_mats, world_mats(arm))
        print("E11_IDLE_FN_MATCH %s" % json.dumps({
            "pos_mm": round(wp, 6), "dir_deg": round(wd, 6), "worst": wb,
            "ok": bool(wp <= 1e-6 and wd <= 1e-6)}, ensure_ascii=False))
        arm.animation_data.action = None

    # ---------------------------------------------------------- 3) D18 基准
    gu = bpy.data.actions.get("GetUp_B")
    d18 = {"found": gu is not None}
    if gu is not None:
        arm.animation_data.action = gu
        A._bind_slot(arm, gu)
        start, end = int(gu.frame_range[0]), int(gu.frame_range[1])
        knee_zs, pel_zs, head_zs = [], [], []
        frames_mats = {}
        for frame in range(start, end + 1):
            bpy.context.scene.frame_set(frame)
            bpy.context.view_layer.update()
            knee_zs.append(min(bone_world(arm, "shin." + s).z
                               for s in SIDES) * 1000.0)
            pel_zs.append(bone_world(arm, "pelvis").z * 1000.0)
            head_zs.append(bone_world(arm, "head").z * 1000.0)
            frames_mats[frame] = world_mats(arm)
        # 单膝贴地（膝 ≤ 150 mm）连续帧数
        run = best = 0
        for z in knee_zs:
            if z <= 150.0:
                run += 1
                best = max(best, run)
            else:
                run = 0
        d18.update({
            "range": [start, end],
            "min_knee_z_mm": round(min(knee_zs), 2),
            "knee_min_at": start + knee_zs.index(min(knee_zs)),
            "kneel_plateau_frames": best,
            "pelvis_z_mm": round(pel_zs[-1], 2),
            "head_z_mm": round(head_zs[-1], 2),
        })
        arm.animation_data.action = None
    print("E11_D18_BASELINE %s" % json.dumps(d18, ensure_ascii=False))

    # ---------------------------------------------------------- 4) 半跪几何
    hk_pose, hk_info = build_half_kneel(arm, L1, L2, D.ANKLE_REST)
    hk_prof = profile()
    print("E11_HALF_KNEEL %s" % json.dumps({
        "per_side": hk_info, "geom": geom(arm, hk_prof),
    }, ensure_ascii=False))
    if gu is not None:
        hk_mats = world_mats(arm)
        best_frame, best_wd, best_wb = None, 1e9, None
        for frame, mats in frames_mats.items():
            _p, wd, wb = worst_matrix_delta(hk_mats, mats)
            if wd < best_wd:
                best_wd, best_wb, best_frame = wd, wb, frame
        print("E11_HK_VS_D18 %s" % json.dumps({
            "closest_d18_frame": best_frame,
            "min_max_dir_deg": round(best_wd, 3),
            "worst_bone": best_wb,
            "threshold_deg": 15.0,
            "ok": bool(best_wd >= 15.0)}, ensure_ascii=False))

    # ---------------------------------------------------------- 5) 出图（可选）
    if RENDER:
        camera = bpy.data.objects.get("Presentation_Camera")
        if camera is None:
            print("E11_NO_CAMERA")
        else:
            os.makedirs(A.PREVIEW_DIR, exist_ok=True)
            for tag, pose in (("corpse", D.death_pose(arm, 120)),
                              ("halfkneel", hk_pose)):
                A.apply_pose(arm, pose)
                for view, loc, tgt, scale, res in (
                        ("side", (4.6, 0.32, 0.60), (0.0, 0.32, 0.60),
                         2.60, (1100, 700)),
                        ("three_quarter", (3.4, -3.2, 1.40),
                         (0.0, 0.32, 0.45), 2.60, (1100, 700))):
                    A.render_still(
                        camera, os.path.join(
                            A.PREVIEW_DIR, "e11probe_%s_%s.png" % (tag, view)),
                        loc, tgt, scale, res)
    print("E11_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E11_PROBE_FAILURE " + traceback.format_exc())
