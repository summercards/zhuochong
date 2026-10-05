"""probe_e10_baseline —— E10 `Death` 开工第一件测量（**不许照抄 E09 读数**）。

要回答五件事（对应清单 E10 详细计划 §0）：
  1) 接缝：`Idle_01@0` 的实测站架锚点（踝 / 骨盆 / 拳 / 头顶 / 各件最低 z）。
  2) ★ E09 `Defeat@120` 的**逐位快照** —— 作为 E10 尸体姿的**可分性基准**
     （口径照抄 `_probe_e07_vs_e06.py`：57 骨世界矩阵，取「位置 mm 差」与「朝向 度 差」的最大值）。
  3) ★ 仰卧尸体姿扫描（本支唯一全新几何），**分四段定标**：
       A) 颈/头的**后仰量**（俯卧是 rx>0，仰卧必须 rx<0 —— 第一轮实测踩到的坑）
       B) 骨盆 z × 腿的下垂量（躯干贴地与腿贴地互相拉扯，必须一起扫）
       C) 脚的俯仰 × 外翻（E09 明说「脚的自然翻倒留给 E10」）
       D) 臂的外展 × 前后 × 腕高（3D 两骨 IK，手要落在地面带内）
  4) ★ E10 末姿 → 半跪姿 的**连续路径可行性**（单帧旋转 ≤ `no_teleport` 25°）。
  5) 未蒙皮件清单（`Jacket_Hem*` 是否仍在原地 —— 本支会比 E09 更严重）。

★★★ 前两轮实测踩到的坑，记在这里免得再踩：
  · `leg_ik` 的屈膝方向是**父链 +rx**。仰卧时骨盆 rx≈−86 ⟹ 父链 +Y ≈ 世界 **−Z（朝下）**
    ⟹ `leg_ik` 会把膝关节**往地下顶**；而直腿要求 q≈L1+L2（全伸），
    实测 q 只要比 L1+L2 短 1.5% 膝就下沉 **62 mm**。
    ⟹ 仰卧腿**不用** `leg_ik`，改用 `aim_bone` 直接指定大腿 / 小腿的**世界方向**。
  · 世界矩阵**行主序**：平移在展平索引 3 / 7 / 11（不是 12/13/14）。
  · 仰卧时 `neck_rx / head_rx` 必须**取负**：`+rx` 在仰卧坐标系里是把下巴往胸口收
    （头离地），`−rx` 才是后仰（后脑勺落地）。

运行：
    blender --background --factory-startup --python probe_e10_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as IDLE   # noqa: E402

SIDES = ("L", "R")

HEAD_KEYS = ("Head", "Hair_Mass", "Hair_Sweep", "Nose", "Ear_L", "Ear_R",
             "Lower_Lip", "Upper_Lip", "Mouth_Line", "Glasses_Bridge",
             "Glasses_Frame_L", "Glasses_Frame_R", "Glasses_Temple_L",
             "Glasses_Temple_R", "Iris_L", "Iris_R", "Pupil_L", "Pupil_R",
             "Eye_White_L", "Eye_White_R", "Eyebrow_L", "Eyebrow_R",
             "Eyelid_Upper_L", "Eyelid_Upper_R", "Eyelid_Lower_L",
             "Eyelid_Lower_R", "Nose_Wing_L", "Nose_Wing_R", "Ear_Lobe_L",
             "Ear_Lobe_R", "Ear_Inner_L", "Ear_Inner_R", "Eye_Glint_L",
             "Eye_Glint_R", "Eye_Line_Upper_L", "Eye_Line_Upper_R",
             "Iris_Ring_L", "Iris_Ring_R")
TORSO_KEYS = ("Suit_Torso", "Jacket_Collar", "Jacket_Lapel_L",
              "Jacket_Lapel_R", "Jacket_Vent", "Jacket_Back_Seam",
              "Jacket_Button_1", "Jacket_Button_2", "Pocket_Flap_L",
              "Pocket_Flap_R", "Shirt_Front", "Shirt_Collar",
              "Collar_Point_L", "Collar_Point_R", "Lapel_Fold_L",
              "Lapel_Fold_R", "Lapel_Notch_L", "Lapel_Notch_R", "Neck",
              "Jacket_Hem", "Jacket_Hem_Line")
ARM_KEYS = {s: ("Sleeve_" + s, "Shirt_Cuff_" + s, "Hand_Palm_" + s,
                "Finger_Index_" + s, "Finger_Middle_" + s,
                "Finger_Ring_" + s, "Finger_Pinky_" + s, "Thumb_" + s)
            for s in SIDES}
LEG_KEYS = {s: ("Trouser_" + s, "Shoe_Heel_" + s, "Shoe_Sole_" + s,
                "Shoe_Toe_Cap_" + s, "Shoe_Upper_" + s) for s in SIDES}


# --------------------------------------------------------------- 工具
def profile():
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


def part_low(prof, keys):
    vals = [prof[k] for k in keys if k in prof]
    return min(vals) if vals else float("nan")


def bone_world(arm, name, which="head"):
    pose_bone = arm.pose.bones[name]
    point = pose_bone.head if which == "head" else pose_bone.tail
    return arm.matrix_world @ point


def world_pose_dump(arm):
    """逐骨世界矩阵（4x4 → 16 数，行主序）。★ 平移在索引 3/7/11。"""
    out = {}
    for pose_bone in arm.pose.bones:
        matrix = arm.matrix_world @ pose_bone.matrix
        out[pose_bone.name] = [round(v, 6) for row in matrix for v in row]
    return out


def mat_delta(a_flat, b_flat):
    pa = Vector((a_flat[3], a_flat[7], a_flat[11]))
    pb = Vector((b_flat[3], b_flat[7], b_flat[11]))
    pos = (pa - pb).length * 1000.0
    worst = 0.0
    for col in range(3):
        va = Vector((a_flat[col], a_flat[4 + col], a_flat[8 + col]))
        vb = Vector((b_flat[col], b_flat[4 + col], b_flat[8 + col]))
        if va.length < 1e-9 or vb.length < 1e-9:
            continue
        cos = max(-1.0, min(1.0, va.normalized().dot(vb.normalized())))
        worst = max(worst, math.degrees(math.acos(cos)))
    return pos, worst


# --------------------------------------------------------------- 摆骨
def keep_foot_orient(arm, name, fp_deg, roll_deg):
    """世界朝向 = rest 先绕世界 X 俯仰 `fp_deg`、再绕世界 Y 外翻 `roll_deg`。

    仰卧时身体长轴 = 世界 Y ⟹ 绕世界 Y 转 = **脚向内/外倒**，
    正是 E09 明说「留给 E10 `Death`」的那件事。
    """
    pose_bone = arm.pose.bones[name]
    rest_basis = pose_bone.bone.matrix_local.to_3x3()
    rot = (Matrix.Rotation(math.radians(roll_deg), 3, "Y")
           @ Matrix.Rotation(math.radians(fp_deg), 3, "X"))
    target = (rot @ rest_basis).to_4x4()
    target.translation = pose_bone.matrix.translation
    pose_bone.matrix = target
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pose_bone.rotation_euler)


def arm_ik(shoulder, target, l1, l2, pole=(0.0, 0.0, 1.0)):
    """3D 两骨 IK：返回 (上臂世界方向, 前臂世界方向, 肘位置)。"""
    d = Vector(target) - Vector(shoulder)
    dist = d.length
    limit = (l1 + l2) * 0.999
    if dist > limit:
        d = d.normalized() * limit
        dist = limit
    dist = max(dist, abs(l1 - l2) + 1e-4)
    u = d.normalized()
    cos_a = (l1 * l1 + dist * dist - l2 * l2) / (2.0 * l1 * dist)
    ang = math.acos(max(-1.0, min(1.0, cos_a)))
    pv = Vector(pole)
    n = pv - u * pv.dot(u)
    if n.length < 1e-6:
        n = Vector((0.0, 0.0, 1.0)) - u * u.z
    n.normalize()
    dir_u = (u * math.cos(ang) + n * math.sin(ang)).normalized()
    elbow = Vector(shoulder) + dir_u * l1
    dir_f = (Vector(shoulder) + u * dist - elbow).normalized()
    return dir_u, dir_f, elbow


# --------------------------------------------------------------- 仰卧装配
def build_supine(arm, pz=0.145, py=0.64, prx=-86.0, spine=0.0,
                 neck_rx=-20.0, head_rx=-18.0, head_ry=22.0,
                 shoulder_rx=-6.0,
                 leg_dz=-0.045, leg_splay=0.150, knee_up_deg=3.0,
                 foot_pitch=-40.0, foot_roll=50.0,
                 arm_out=0.36, arm_fwd=0.02, wrist_z=0.055,
                 elbow_pole=(0.0, 0.0, 1.0)):
    """装配一个仰卧尸体姿。所有姿态均以「世界方向 / 世界目标」参数化。"""
    pose = {
        "pelvis": (prx, 0.0, 0.0),
        "spine_01": (spine, 0.0, 0.0),
        "spine_02": (spine, 0.0, 0.0),
        "chest": (spine, 0.0, 0.0),
        "neck": (neck_rx, 0.0, 0.0),
        "head": (head_rx, head_ry, 0.0),
        "shoulder.L": (shoulder_rx, 0.0, 0.0),
        "shoulder.R": (shoulder_rx, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, py, pz - 0.900)},
    }
    pose.update(A.FIST)
    A.apply_pose(arm, pose)

    # ---- 腿：直腿，用世界方向直接指定（不用 leg_ik，见文件头注释）----------
    for side in SIDES:
        s = 1.0 if side == "L" else -1.0
        d_leg = Vector((s * leg_splay, -1.0, leg_dz)).normalized()
        pose["thigh." + side] = A.aim_bone(arm, "thigh." + side, d_leg)
        up = math.tan(math.radians(knee_up_deg))
        d_shin = Vector((d_leg.x, d_leg.y, d_leg.z + up)).normalized()
        pose["shin." + side] = A.aim_bone(arm, "shin." + side, d_shin)
        pose["foot." + side] = keep_foot_orient(arm, "foot." + side,
                                                foot_pitch, foot_roll * s)

    # ---- 臂：3D 两骨 IK（上臂 + 前臂），手再单独压平 ------------------------
    A.apply_pose(arm, pose)
    l1 = arm.data.bones["upperarm.L"].length
    l2 = arm.data.bones["forearm.L"].length
    for side in SIDES:
        s = 1.0 if side == "L" else -1.0
        sh = Vector(bone_world(arm, "upperarm." + side, "head"))
        tgt = Vector((sh.x + s * arm_out, sh.y - arm_fwd, wrist_z))
        dir_u, dir_f, _elbow = arm_ik(sh, tgt, l1, l2, elbow_pole)
        pose["upperarm." + side] = A.aim_bone(arm, "upperarm." + side, dir_u)
        pose["forearm." + side] = A.aim_bone(arm, "forearm." + side, dir_f)
        d_hand = Vector((dir_f.x, dir_f.y, 0.0))
        if d_hand.length < 1e-6:
            d_hand = Vector((s, 0.0, 0.0))
        pose["hand." + side] = A.aim_bone(arm, "hand." + side,
                                          d_hand.normalized())
    A.apply_pose(arm, pose)
    return pose


def supine_row(arm, prof, tag, **kw):
    pose = build_supine(arm, **kw)
    prof.clear()
    prof.update(profile())
    low = min(prof.values())
    return {
        "tag": tag,
        "low": round(low, 2),
        "part": min(prof.items(), key=lambda kv: kv[1])[0],
        "pz": kw.get("pz"), "prx": kw.get("prx"),
        "head": round(part_low(prof, HEAD_KEYS), 2),
        "torso": round(part_low(prof, TORSO_KEYS), 2),
        "armL": round(part_low(prof, ARM_KEYS["L"]), 2),
        "armR": round(part_low(prof, ARM_KEYS["R"]), 2),
        "legL": round(part_low(prof, LEG_KEYS["L"]), 2),
        "legR": round(part_low(prof, LEG_KEYS["R"]), 2),
        "kneeL": round(bone_world(arm, "shin.L", "head").z * 1000.0, 1),
        "kneeR": round(bone_world(arm, "shin.R", "head").z * 1000.0, 1),
        "elbowL": round(bone_world(arm, "forearm.L", "head").z * 1000.0, 1),
        "elbowR": round(bone_world(arm, "forearm.R", "head").z * 1000.0, 1),
        "shoulderL": round(bone_world(arm, "upperarm.L", "head").z * 1000.0, 1),
        "ankL": [round(v * 1000.0, 1) for v in bone_world(arm, "foot.L")],
        "pelvis": [round(v * 1000.0, 1) for v in bone_world(arm, "pelvis")],
        "headmid": [round(v * 1000.0, 1) for v in bone_world(arm, "head")],
        "neckmid": [round(v * 1000.0, 1) for v in bone_world(arm, "neck")],
        "handL": [round(v * 1000.0, 1)
                  for v in bone_world(arm, "hand.L", "tail")],
    }, pose


def emit(tag, rows):
    print("%s %s" % (tag, json.dumps(rows, ensure_ascii=False)))


def main():  # noqa: C901
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    names = sorted(o.name for o in bpy.data.objects if o.type == "MESH")
    print("E10_MESH_COUNT %d" % len(names))

    l1 = arm.data.bones["upperarm.L"].length
    l2 = arm.data.bones["forearm.L"].length
    l3 = arm.data.bones["hand.L"].length
    print("E10_ARM_LEN %s" % json.dumps({
        "upperarm": round(l1, 6), "forearm": round(l2, 6),
        "hand": round(l3, 6),
        "thigh": round(arm.data.bones["thigh.L"].length, 6),
        "shin": round(arm.data.bones["shin.L"].length, 6),
        "neck": round(arm.data.bones["neck"].length, 6),
        "head": round(arm.data.bones["head"].length, 6),
        "arm_chain": round(l1 + l2 + l3, 6),
    }, ensure_ascii=False))

    # ---------------------------------------------------------- 1) 接缝
    base = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, base)
    seam = {n: [round(v * 1000.0, 2) for v in bone_world(arm, n, "head")]
            for n in ("pelvis", "foot.L", "foot.R", "toe.L", "toe.R",
                      "hand.L", "hand.R", "head", "chest", "shin.L", "shin.R",
                      "thigh.L", "thigh.R", "upperarm.L", "upperarm.R")}
    print("E10_SEAM %s" % json.dumps(seam, ensure_ascii=False))
    prof = profile()
    print("E10_SEAM_LOW %s" % json.dumps(
        {k: round(v, 2) for k, v in sorted(prof.items(),
                                           key=lambda kv: kv[1])[:8]},
        ensure_ascii=False))

    # ---------------------------------------------------------- 2) E09 终姿
    e09 = bpy.data.actions.get("Defeat")
    e09_dump = {}
    if e09 is None:
        print("E10_E09_MISSING")
    else:
        arm.animation_data.action = e09
        A._bind_slot(arm, e09)
        bpy.context.scene.frame_set(120)
        bpy.context.view_layer.update()
        e09_dump = world_pose_dump(arm)
        e09_prof = profile()
        print("E10_E09_TERM_GEOM %s" % json.dumps({
            "pelvis": [round(v * 1000.0, 2) for v in bone_world(arm, "pelvis")],
            "head_mid": [round(v * 1000.0, 2)
                         for v in bone_world(arm, "head")],
            "handL": [round(v * 1000.0, 2)
                      for v in bone_world(arm, "hand.L", "tail")],
            "footL": [round(v * 1000.0, 2) for v in bone_world(arm, "foot.L")],
            "lowest": round(min(e09_prof.values()), 2),
            "lowest_part": min(e09_prof.items(), key=lambda kv: kv[1])[0],
        }, ensure_ascii=False))
        arm.animation_data.action = None

    buf = {}

    # ------------------------------------------------ A) 颈/头 后仰量定标
    head_scan = []
    for neck_rx in (-10.0, -14.0, -18.0, -22.0):
        for head_rx in (-3.0, -7.0, -11.0, -15.0):
            row, _p = supine_row(arm, buf, "head", pz=0.15, prx=-86.0,
                                 leg_dz=-0.060, foot_pitch=-40.0,
                                 foot_roll=50.0, arm_out=0.36, arm_fwd=0.02,
                                 wrist_z=0.055, neck_rx=neck_rx,
                                 head_rx=head_rx)
            row.update({"neck_rx": neck_rx, "head_rx": head_rx})
            head_scan.append(row)
    emit("E10_HEAD_SCAN", head_scan)
    best_head = min(head_scan, key=lambda r: abs(r["head"]))
    print("E10_HEAD_BEST %s" % json.dumps(best_head, ensure_ascii=False))
    nk, hd = best_head["neck_rx"], best_head["head_rx"]

    # ------------------------------------------------ B) 骨盆 z × 腿下垂量
    pz_scan = []
    for pz in (0.126, 0.131, 0.136, 0.141, 0.146):
        for leg_dz in (-0.045, -0.060, -0.075):
            row, _p = supine_row(arm, buf, "pz", pz=pz, prx=-86.0,
                                 leg_dz=leg_dz, foot_pitch=-40.0,
                                 foot_roll=50.0, arm_out=0.36, arm_fwd=0.02,
                                 wrist_z=0.055, neck_rx=nk, head_rx=hd)
            row.update({"pz": pz, "leg_dz": leg_dz})
            pz_scan.append(row)
    emit("E10_PZ_SCAN", pz_scan)

    def _score(r):
        band = []
        for v in (r["torso"], r["legL"], r["head"], r["armL"]):
            band.append(max(0.0, v - 8.0) + max(0.0, -6.0 - v))
        return sum(band) + 2.0 * max(0.0, r["low"] - 8.0) \
            + 4.0 * max(0.0, -6.0 - r["low"])

    best_pz = min(pz_scan, key=_score)
    print("E10_PZ_BEST %s" % json.dumps(best_pz, ensure_ascii=False))

    # ------------------------------------------------ C) 脚俯仰 × 外翻
    foot_scan = []
    for foot_pitch in (-55.0, -45.0, -35.0, -25.0, -15.0):
        for foot_roll in (0.0, 25.0, 45.0, 65.0):
            row, _p = supine_row(arm, buf, "foot", pz=best_pz["pz"],
                                 prx=-86.0, leg_dz=best_pz["leg_dz"],
                                 foot_pitch=foot_pitch, foot_roll=foot_roll,
                                 arm_out=0.36, arm_fwd=0.02, wrist_z=0.055,
                                 neck_rx=nk, head_rx=hd)
            row.update({"foot_pitch": foot_pitch, "foot_roll": foot_roll})
            foot_scan.append(row)
    emit("E10_FOOT_SCAN", foot_scan)
    best_foot = min(foot_scan, key=lambda r: abs(r["legL"]))
    print("E10_FOOT_BEST %s" % json.dumps(best_foot, ensure_ascii=False))

    # ------------------------------------------------ D) 臂 外展 × 前后 × 腕高
    arm_scan = []
    for arm_out in (0.34, 0.42, 0.50, 0.58):
        for arm_fwd in (0.02, 0.10, 0.18):
            for wrist_z in (0.055, 0.070, 0.085):
                row, _p = supine_row(
                    arm, buf, "arm", pz=best_pz["pz"], prx=-86.0,
                    leg_dz=best_pz["leg_dz"],
                    foot_pitch=best_foot["foot_pitch"],
                    foot_roll=best_foot["foot_roll"], arm_out=arm_out,
                    arm_fwd=arm_fwd, wrist_z=wrist_z, neck_rx=nk, head_rx=hd)
                row.update({"arm_out": arm_out, "arm_fwd": arm_fwd,
                            "wrist_z": wrist_z})
                arm_scan.append(row)
    emit("E10_ARM_SCAN", arm_scan)

    def _arm_score(r):
        # 手要贴地、肘不许挑到天上（肘高 ≈ 肩高 ⟹ 手臂基本摊平）
        return (abs(r["armL"]) + abs(r["armR"])
                + max(0.0, -6.0 - r["low"]) * 4.0
                + 0.30 * abs(r["elbowL"] - r["shoulderL"]))

    best_arm = min(arm_scan, key=_arm_score)
    print("E10_ARM_BEST %s" % json.dumps(best_arm, ensure_ascii=False))

    # ------------------------------------------------ E) 最终合成
    final_kw = dict(pz=best_pz["pz"], leg_dz=best_pz["leg_dz"],
                    foot_pitch=best_foot["foot_pitch"],
                    foot_roll=best_foot["foot_roll"],
                    arm_out=best_arm["arm_out"],
                    arm_fwd=best_arm["arm_fwd"],
                    wrist_z=best_arm["wrist_z"], neck_rx=nk, head_rx=hd,
                    prx=-86.0)
    final_row, final_pose = supine_row(arm, buf, "final", **final_kw)
    emit("E10_FINAL", final_row)
    print("E10_FINAL_KW %s" % json.dumps(final_kw, ensure_ascii=False))
    print("E10_FINAL_LOW20 %s" % json.dumps(
        {k: round(v, 2) for k, v in sorted(buf.items(),
                                           key=lambda kv: kv[1])[:20]},
        ensure_ascii=False))
    # 末姿各骨的**世界方向**（anim_death.py 的臂/腿插值端点用）
    A.apply_pose(arm, final_pose)
    print("E10_TERM_DIRS %s" % json.dumps({
        n: [round(v, 5) for v in A.bone_direction(arm, n)]
        for n in ("upperarm.L", "forearm.L", "hand.L",
                  "upperarm.R", "forearm.R", "hand.R",
                  "thigh.L", "shin.L", "foot.L",
                  "thigh.R", "shin.R", "foot.R",
                  "chest", "neck", "head", "pelvis")
    }, ensure_ascii=False))
    print("E10_TERM_EULER %s" % json.dumps(
        {k: [round(x, 4) for x in v] for k, v in final_pose.items()
         if not k.startswith("@")}, ensure_ascii=False))
    print("E10_TERM_LOC %s" % json.dumps(
        {k: [round(x, 6) for x in v]
         for k, v in final_pose.get("@loc", {}).items()},
        ensure_ascii=False))

    # ------------------------------------------------ F) 末姿 → 半跪
    A.apply_pose(arm, final_pose)
    term_mats = world_pose_dump(arm)
    half_kneel = {
        "pelvis": (30.0, 0.0, 0.0),
        "spine_01": (10.0, 0.0, 0.0), "spine_02": (10.0, 0.0, 0.0),
        "chest": (8.0, 0.0, 0.0),
        "neck": (8.0, 0.0, 0.0), "head": (-6.0, 0.0, 0.0),
        "shoulder.L": (-24.0, 0.0, 0.0), "shoulder.R": (-24.0, 0.0, 0.0),
        "thigh.L": (62.0, 0.0, -8.0), "shin.L": (86.0, 0.0, 0.0),
        "foot.L": (0.0, 0.0, 0.0), "toe.L": (0.0, 0.0, 0.0),
        "thigh.R": (58.0, 0.0, 8.0), "shin.R": (90.0, 0.0, 0.0),
        "foot.R": (0.0, 0.0, 0.0), "toe.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(0.0, 0.30, 0.52 - 0.900)},
    }
    half_kneel.update(A.FIST)
    A.apply_pose(arm, half_kneel)
    hk_mats = world_pose_dump(arm)
    worst_pos, worst_dir, worst_bone = 0.0, 0.0, None
    for name in term_mats:
        if name not in hk_mats:
            continue
        pos, deg = mat_delta(term_mats[name], hk_mats[name])
        if deg > worst_dir:
            worst_dir, worst_bone = deg, name
        worst_pos = max(worst_pos, pos)
    print("E10_TO_HALFKNEEL %s" % json.dumps({
        "max_pos_mm": round(worst_pos, 2),
        "max_dir_deg": round(worst_dir, 3),
        "worst_bone": worst_bone,
        "frames_needed_at_25deg": int(math.ceil(worst_dir / 25.0)),
    }, ensure_ascii=False))

    # ------------------------------------------------ G) E09 ⇄ E10 可分性
    if e09_dump:
        A.apply_pose(arm, final_pose)
        e10_mats = world_pose_dump(arm)
        wp, wd, wb = 0.0, 0.0, None
        for name in e09_dump:
            if name not in e10_mats:
                continue
            pos, deg = mat_delta(e10_mats[name], e09_dump[name])
            if deg > wd:
                wd, wb = deg, name
            wp = max(wp, pos)
        print("E10_SEP_E09 %s" % json.dumps({
            "max_pos_mm": round(wp, 2), "max_dir_deg": round(wd, 3),
            "worst_bone": wb, "threshold_deg": 15.0,
            "ok": bool(wd >= 15.0),
        }, ensure_ascii=False))

    # ------------------------------------------------ H) 未蒙皮件
    unskinned = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        groups = len(obj.vertex_groups)
        parent = obj.parent.name if obj.parent else None
        if groups == 0 or parent != "Character_Rig":
            unskinned.append({"name": obj.name, "vgroups": groups,
                              "parent": parent,
                              "mods": [m.type for m in obj.modifiers]})
    print("E10_UNSKINNED %s" % json.dumps(unskinned, ensure_ascii=False))

    # ------------------------------------------------ I) 出图
    A.apply_pose(arm, final_pose)
    camera = bpy.data.objects.get("Presentation_Camera")
    if camera is None:
        print("E10_NO_CAMERA")
    else:
        out_dir = A.PREVIEW_DIR
        os.makedirs(out_dir, exist_ok=True)
        for tag, loc, tgt, scale, res in (
                ("side", (4.8, 0.32, 0.55), (0.0, 0.32, 0.55), 2.40,
                 (1200, 700)),
                ("front", (0.0, -4.6, 0.55), (0.0, 0.32, 0.55), 2.40,
                 (1200, 700)),
                ("three_quarter", (3.3, -3.1, 1.35), (0.0, 0.32, 0.42), 2.40,
                 (1200, 700))):
            A.render_still(camera, os.path.join(out_dir,
                                                "e10probe_%s.png" % tag),
                           loc, tgt, scale, res)
    print("E10_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E10_PROBE_FAILURE " + traceback.format_exc())
