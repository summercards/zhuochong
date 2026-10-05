"""probe_e09_baseline —— E09 `Defeat` 开工第一件测量（**不许照抄别支读数**）。

要回答三件事：
  1) 接缝：`Idle_01@0` 的实测姿态（站架锚点：踝 / 骨盆 / 拳 / 头顶）。
  2) ★ 跪姿几何（本支唯一全新几何）：哪种 (骨盆下降, 大腿 rx, 膝屈, 脚 rx) 能让
     **膝（`shin.*` head）落在 z ≈ 膝半径**、且**全身最低点 ≈ 0（不穿地）**。
  3) ★ 倒地终点：直接读落盘 action `Knockdown_F@20` 的**全骨 euler + location**
     —— D14 的俯卧终点**已被 18 项像素探针 + 6 组反向验证验收过**，
     本支复用它当末帧 = 「躺地终点」的现成安全件（**不是照抄读数，是复用资产**）。

运行：
    blender --background --factory-startup --python probe_e09_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as IDLE   # noqa: E402

SIDES = ("L", "R")
ABDUCT = 6.0


def all_lowest():
    """全身所有网格顶点里的最低 z（世界）。"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    low = 1e9
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            low = min(low, (matrix @ vertex.co).z)
        evaluated.to_mesh_clear()
    return low


def object_low(name):
    obj = bpy.data.objects.get(name)
    if obj is None or obj.type != "MESH":
        return None
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    matrix = evaluated.matrix_world
    low = min((matrix @ v.co).z for v in mesh.vertices) if mesh.vertices else None
    evaluated.to_mesh_clear()
    return low


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    names = sorted(o.name for o in bpy.data.objects if o.type == "MESH")
    print("E09_MESH_COUNT %d" % len(names))
    print("E09_MESH_NAMES %s" % json.dumps(names, ensure_ascii=False))

    # ---------------------------------------------------------- 1) 接缝
    base = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, base)
    seam = {}
    for name in ("pelvis", "foot.L", "foot.R", "toe.L", "toe.R",
                 "hand.L", "hand.R", "head", "chest", "shin.L", "shin.R"):
        seam[name] = [round(v * 1000.0, 1)
                      for v in A.bone_world(arm, name, "head")]
    print("E09_SEAM_BONES %s" % json.dumps(seam, ensure_ascii=False))
    print("E09_IDLE0_EULER %s" % json.dumps(
        {k: [round(x, 4) for x in v] for k, v in base.items()
         if not k.startswith("@")}, ensure_ascii=False))
    print("E09_IDLE0_LOC %s" % json.dumps(
        {k: [round(x, 6) for x in v]
         for k, v in base.get("@loc", {}).items()}, ensure_ascii=False))

    # ---------------------------------------------------------- 2) 跪姿扫描
    # 直接角度（不走 IK）：大腿方向 = (sin a, -cos a)（a>0 膝偏向 +Y/身后），
    # 小腿方向 = (sin(a+b), -cos(a+b))；a+b = 90° ⟹ 小腿**水平向后**贴地。
    rows = []
    for drop in (0.34, 0.36, 0.38, 0.40):
        for thigh_rx in (-6.0, -2.0, 2.0, 6.0):
            for knee_b in (84.0, 90.0, 96.0):
                for foot_rx in (0.0, 40.0):
                    hip_z = 0.900 - drop
                    shin_rx = knee_b - thigh_rx
                    pose = {
                        "pelvis": (4.0, 0.0, 0.0),
                        "spine_01": (2.0, 0.0, 0.0),
                        "spine_02": (2.0, 0.0, 0.0),
                        "chest": (1.0, 0.0, 0.0),
                        "neck": (-6.0, 0.0, 0.0),
                        "head": (5.0, 0.0, 0.0),
                        "thigh.L": (thigh_rx, 0.0, -ABDUCT),
                        "shin.L": (shin_rx, 0.0, 0.0),
                        "foot.L": (foot_rx, 0.0, 0.0),
                        "toe.L": (0.0, 0.0, 0.0),
                        "thigh.R": (thigh_rx, 0.0, ABDUCT),
                        "shin.R": (shin_rx, 0.0, 0.0),
                        "foot.R": (foot_rx, 0.0, 0.0),
                        "toe.R": (0.0, 0.0, 0.0),
                        "@loc": {"pelvis": A.wloc(0.0, 0.0, -drop)},
                    }
                    A.apply_pose(arm, pose)
                    knee = A.bone_world(arm, "shin.L", "head")
                    ankle = A.bone_world(arm, "foot.L", "head")
                    toe = A.bone_world(arm, "toe.L", "head")
                    hip = A.bone_world(arm, "thigh.L", "head")
                    rows.append({
                        "drop": drop, "thigh_rx": thigh_rx, "knee_b": knee_b,
                        "foot_rx": foot_rx,
                        "hip_z": round(hip.z * 1000.0, 1),
                        "knee_z": round(knee.z * 1000.0, 1),
                        "knee_y": round(knee.y * 1000.0, 1),
                        "ankle_z": round(ankle.z * 1000.0, 1),
                        "ankle_y": round(ankle.y * 1000.0, 1),
                        "toe_z": round(toe.z * 1000.0, 1),
                        "low_body": round(all_lowest() * 1000.0, 2),
                    })
    print("E09_KNEEL_SCAN %s" % json.dumps(rows, ensure_ascii=False))

    # 脚掌候选（在最佳跪姿上单独扫 foot_rx）
    foot_rows = []
    for foot_rx in (-10.0, 0.0, 20.0, 40.0, 60.0, 80.0):
        pose = {
            "pelvis": (4.0, 0.0, 0.0),
            "spine_01": (2.0, 0.0, 0.0), "spine_02": (2.0, 0.0, 0.0),
            "chest": (1.0, 0.0, 0.0),
            "thigh.L": (0.0, 0.0, -ABDUCT), "shin.L": (90.0, 0.0, 0.0),
            "foot.L": (foot_rx, 0.0, 0.0), "toe.L": (0.0, 0.0, 0.0),
            "thigh.R": (0.0, 0.0, ABDUCT), "shin.R": (90.0, 0.0, 0.0),
            "foot.R": (foot_rx, 0.0, 0.0), "toe.R": (0.0, 0.0, 0.0),
            "@loc": {"pelvis": A.wloc(0.0, 0.0, -0.40)},
        }
        A.apply_pose(arm, pose)
        foot_rows.append({
            "foot_rx": foot_rx,
            "sole_low_L": None if object_low("Shoe_Sole_L") is None
            else round(object_low("Shoe_Sole_L") * 1000.0, 2),
            "heel_low_L": None if object_low("Shoe_Heel_L") is None
            else round(object_low("Shoe_Heel_L") * 1000.0, 2),
            "toecap_low_L": None if object_low("Shoe_Toe_Cap_L") is None
            else round(object_low("Shoe_Toe_Cap_L") * 1000.0, 2),
            "low_body": round(all_lowest() * 1000.0, 2),
        })
    print("E09_FOOT_SCAN %s" % json.dumps(foot_rows, ensure_ascii=False))

    # ---------------------------------------------------------- 3) 倒地终点复用
    probe_rows = []
    for d16 in (0.0, 0.06, 0.10):     # 躯干在跪姿上再前倾（度，试算用）
        pose = {
            "pelvis": (4.0 + d16, 0.0, 0.0),
            "spine_01": (2.0 + d16, 0.0, 0.0),
            "spine_02": (2.0 + d16, 0.0, 0.0),
            "chest": (1.0 + d16, 0.0, 0.0),
            "thigh.L": (0.0, 0.0, -ABDUCT), "shin.L": (90.0, 0.0, 0.0),
            "thigh.R": (0.0, 0.0, ABDUCT), "shin.R": (90.0, 0.0, 0.0),
            "@loc": {"pelvis": A.wloc(0.0, 0.0, -0.40)},
        }
        A.apply_pose(arm, pose)
        probe_rows.append({"lean_add": d16,
                           "head_y": round(A.bone_world(arm, "head", "tail").y
                                           * 1000.0, 1)})
    print("E09_LEAN_SAMPLE %s" % json.dumps(probe_rows, ensure_ascii=False))

    action = bpy.data.actions.get("Knockdown_F")
    if action is None:
        print("E09_KNOCKDOWN_F_MISSING")
    else:
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        bpy.context.scene.frame_set(20)
        bpy.context.view_layer.update()
        dump = {}
        for pose_bone in arm.pose.bones:
            rot = [round(math.degrees(v), 4) for v in pose_bone.rotation_euler]
            loc = [round(v, 6) for v in pose_bone.location]
            if any(abs(v) > 1e-9 for v in rot) or any(abs(v) > 1e-9 for v in loc):
                dump[pose_bone.name] = {"rot": rot, "loc": loc}
        print("E09_KNOCKDOWN_F_F20 %s" % json.dumps(dump, ensure_ascii=False))
        pelvis = A.bone_world(arm, "pelvis", "head")
        print("E09_KDF_GEOM %s" % json.dumps({
            "pelvis": [round(v * 1000.0, 1) for v in pelvis],
            "low_body": round(all_lowest() * 1000.0, 2),
            "frame_range": list(action.frame_range),
        }))
    print("E09_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E09_PROBE_FAILURE " + traceback.format_exc())
