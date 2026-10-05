"""probe_c05_baseline —— 只量不做：读 `Grab_Start@54`（C04 末帧），
量出 C05 `Grab_Hold` 起手所需的全部基座量与**可达余量**。

要回答的问题（清单 C05 计划第 4 步第 2 条）：
  1. 抓取点在世界系里保持不动的公差 = `arm_seat` 的 `worst_over_mm` 余量有多少？
     （决定呼吸幅度上限）
  2. C04 末帧的头朝向到底对着抓取点多少度？（决定 `head_track_ok` 口径怎么写）
  3. 双手/踝/骨盆的世界坐标基线。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c05_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_grab04 as G4        # noqa: E402

SIDES = ("L", "R")
C04_FRAME = 54


def unit(v):
    v = Vector(v)
    n = v.length or 1.0
    return v / n


def ang(a, b):
    return math.degrees(unit(a).angle(unit(b)))


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    action = bpy.data.actions[G4.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene = bpy.context.scene
    scene.frame_set(C04_FRAME)
    bpy.context.view_layer.update()

    out = {}
    out["action_props"] = {}
    for key in ("anim_id", "loop", "grab_frame", "grab_hold_frame",
                "grabbed_point_L_m", "grabbed_point_R_m", "root_motion_m",
                "grab_reach_ratio", "frames"):
        try:
            v = action[key]
            out["action_props"][key] = (list(v) if hasattr(v, "__len__")
                                        and not isinstance(v, str) else v)
        except (KeyError, TypeError):
            out["action_props"][key] = None

    # ---- 世界坐标基线
    pts = {}
    for name in ("pelvis", "chest", "neck", "head", "shoulder.L", "shoulder.R",
                 "upperarm.L", "upperarm.R", "forearm.L", "forearm.R",
                 "hand.L", "hand.R", "foot.L", "foot.R", "toe.L", "toe.R",
                 "thigh.L", "thigh.R", "shin.L", "shin.R"):
        pts[name] = {
            "head_mm": [round(v * 1000.0, 3)
                        for v in A.bone_world(arm, name, "head")],
            "tail_mm": [round(v * 1000.0, 3)
                        for v in A.bone_world(arm, name, "tail")],
        }
    out["bones"] = pts

    # ---- 抓取点与可达余量（本支最关键的两个数）
    arm_len = {}
    grab = {}
    shoulder = {}
    elbow_dir = {}
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        arm_len[side] = {
            "upper": round(arm.pose.bones[up].length * 1000.0, 3),
            "forearm": round(arm.pose.bones[fo].length * 1000.0, 3),
            "hand": round(arm.pose.bones[hd].length * 1000.0, 3),
        }
        total = sum(arm.pose.bones[b].length for b in (up, fo, hd))
        sh = Vector(A.bone_world(arm, up, "head"))
        el = Vector(A.bone_world(arm, up, "tail"))
        tg = Vector(A.bone_world(arm, hd, "tail"))
        grab[side] = {
            "point_mm": [round(v * 1000.0, 4) for v in tg],
            "dist_mm": round((tg - sh).length * 1000.0, 4),
        }
        shoulder[side] = [round(v * 1000.0, 4) for v in sh]
        elbow_dir[side] = [round(v, 6) for v in unit(el - sh)]
    out["arm_len_mm"] = arm_len
    out["grab"] = grab
    out["shoulder_mm"] = shoulder
    out["elbow_dir"] = elbow_dir

    # 可达余量：limit = (L1 + L2 + L3) * 0.9995
    margin = {}
    for side in SIDES:
        l1 = arm_len[side]["upper"] / 1000.0
        l23 = (arm_len[side]["forearm"] + arm_len[side]["hand"]) / 1000.0
        limit = (l1 + l23) * 0.9995
        dist = grab[side]["dist_mm"] / 1000.0
        margin[side] = {
            "limit_mm": round(limit * 1000.0, 4),
            "dist_mm": round(dist * 1000.0, 4),
            "margin_mm": round((limit - dist) * 1000.0, 4),
            "reach_ratio": round(dist / (l1 + l23), 6),
        }
    out["reach_margin"] = margin

    # ---- 头朝向：把 rest 的"面朝前"(-Y) 用 head 的世界 3×3 转出来
    head_pb = arm.pose.bones["head"]
    rest_basis = head_pb.bone.matrix_local.to_3x3()
    local_face = rest_basis.inverted() @ Vector((0.0, -1.0, 0.0))
    face_world = unit(head_pb.matrix.to_3x3() @ local_face)
    head_head = Vector(A.bone_world(arm, "head", "head"))
    head_tail = Vector(A.bone_world(arm, "head", "tail"))
    eye = head_head.lerp(head_tail, 0.55)
    grab_mid = (Vector(A.bone_world(arm, "hand.L", "tail"))
                + Vector(A.bone_world(arm, "hand.R", "tail"))) * 0.5
    to_grab = unit(grab_mid - eye)
    out["head"] = {
        "eye_mm": [round(v * 1000.0, 3) for v in eye],
        "grab_mid_mm": [round(v * 1000.0, 3) for v in grab_mid],
        "face_world": [round(v, 6) for v in face_world],
        "to_grab_dir": [round(v, 6) for v in to_grab],
        "face_to_grab_deg": round(ang(face_world, to_grab), 4),
        "face_pitch_below_horizon_deg": round(
            math.degrees(math.asin(max(-1.0, min(1.0, -face_world.z)))), 4),
        "grab_pitch_below_horizon_deg": round(
            math.degrees(math.asin(max(-1.0, min(1.0, -to_grab.z)))), 4),
    }

    # ---- 全部骨的 euler（方便对照 base）
    euler = {}
    for b in arm.pose.bones:
        val = tuple(round(math.degrees(v), 6) for v in b.rotation_euler)
        loc = tuple(round(v, 9) for v in b.location)
        if any(abs(x) > 1e-9 for x in val) or any(abs(x) > 1e-12 for x in loc):
            euler[b.name] = {"euler_deg": val, "loc": loc}
    out["nonrest_bones"] = euler

    # ---- 躯干链累计前倾（诊断头为什么朝下）
    chain = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head")
    out["trunk_rx_sum_deg"] = round(sum(
        math.degrees(arm.pose.bones[n].rotation_euler[0]) for n in chain), 4)
    out["trunk_rx_each_deg"] = {
        n: round(math.degrees(arm.pose.bones[n].rotation_euler[0]), 4)
        for n in chain}

    A.report("C05_BASELINE", out)
    print("C05_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C05_PROBE_FAILURE " + traceback.format_exc())
