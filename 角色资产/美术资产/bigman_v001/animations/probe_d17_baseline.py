"""probe_d17_baseline —— D17 `GetUp_F` 的**起步实测**（只读，不改任何工程文件）。

回答清单 D17 计划 §4 第 3 步的四件事：

  (a) `f0` 的起点 = **`Knockdown_F@20`**（俯卧）—— 实测其 `pelvis` 世界 z / y，
      作为本支竖直通道的**起点锚**（不许照抄清单里的 220.0 / −576.0，必须实测核对）。
  (b) 终点 = **`Idle_01@0`**（战斗站姿）—— 实测其骨盆 z 与**双脚世界 xy**，
      作为本支末帧锚（不许照抄 900.0 / ±150）。
  (c) **逐对象**最低点（`_d14_low.py` 的做法）—— 确认**撑地段**剪影最低行由谁接管
      （手掌 / 前臂？还是胸腹 / 裤管？），供 `probe_d17_pixels.py` 定 `ground_row` 载体。
  (d) 量「骨盆 680 mm ÷ 可用帧数」，验证 36 帧装得下（装不下先加帧，≤40）。

顺带实测：手臂 / 腿的骨长（`upper/forearm/hand`、`thigh/shin`）、
两个关键姿态的逐骨世界矩阵（供 `end_matches_idle_ok` 的口径核对）。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_d17_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

PROBE_BONES = (
    "root", "pelvis", "spine_01", "spine_02", "chest", "neck", "head", "jaw",
    "shoulder.L", "upperarm.L", "forearm.L", "hand.L",
    "shoulder.R", "upperarm.R", "forearm.R", "hand.R",
    "thigh.L", "shin.L", "foot.L", "toe.L",
    "thigh.R", "shin.R", "foot.R", "toe.R",
)

CASES = (("D14_END", "Knockdown_F", 20), ("IDLE0", "Idle_01", 0))


def _low_by_object(meshes):
    dg = bpy.context.evaluated_depsgraph_get()
    rows = {}
    for obj in meshes:
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mw = ev.matrix_world
        rows[obj.name] = min((mw @ v.co).z for v in me.vertices) * 1000.0
        ev.to_mesh_clear()
    return rows


def main():  # noqa: C901
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene

    out = {"bones": {}, "cases": {}}

    # ---- 骨长（臂 / 腿）----------------------------------------------------
    dims = {}
    for side in ("L", "R"):
        dims[side] = {
            "upper": round(arm.pose.bones["upperarm." + side].length * 1000.0, 3),
            "forearm": round(arm.pose.bones["forearm." + side].length * 1000.0, 3),
            "hand": round(arm.pose.bones["hand." + side].length * 1000.0, 3),
            "thigh": round(arm.pose.bones["thigh." + side].length * 1000.0, 3),
            "shin": round(arm.pose.bones["shin." + side].length * 1000.0, 3),
            "foot": round(arm.pose.bones["foot." + side].length * 1000.0, 3),
        }
    out["limb_mm"] = dims
    out["mesh_count"] = len(meshes)

    for label, action_name, frame in CASES:
        action = bpy.data.actions.get(action_name)
        if action is None:
            raise RuntimeError("动作 %s 不在落盘文件里（现有 %s）"
                               % (action_name, [a.name for a in bpy.data.actions]))
        if arm.animation_data is None:
            arm.animation_data_create()
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        A.reset_pose(arm)
        scene.frame_set(int(frame))
        bpy.context.view_layer.update()

        rec = {"action": action_name, "frame": int(frame),
               "frame_range": [int(v) for v in action.frame_range]}
        rec["head"] = {}
        rec["tail"] = {}
        for name in PROBE_BONES:
            if name not in arm.pose.bones:
                continue
            rec["head"][name] = [round(v * 1000.0, 3)
                                 for v in A.bone_world(arm, name, "head")]
            rec["tail"][name] = [round(v * 1000.0, 3)
                                 for v in A.bone_world(arm, name, "tail")]
        rec["euler_deg"] = {
            name: [round(math.degrees(v), 5) for v in arm.pose.bones[name].rotation_euler]
            for name in PROBE_BONES if name in arm.pose.bones}
        rec["loc_m"] = {pb.name: [round(v, 8) for v in pb.location]
                        for pb in arm.pose.bones
                        if any(abs(v) > 1e-9 for v in pb.location)}

        rows = _low_by_object(meshes)
        rec["object_low_mm"] = {k: round(v, 2) for k, v in rows.items()}
        rec["lowest8"] = [[k, round(v, 2)] for k, v in
                          sorted(rows.items(), key=lambda kv: kv[1])[:8]]

        # 世界俯仰（矢状面）
        def pitch(name):
            d = Vector(A.bone_direction(arm, name))
            return round(-math.degrees(math.atan2(d.y, d.z)), 4)

        rec["pitch_deg"] = {n: pitch(n) for n in
                            ("pelvis", "spine_01", "spine_02", "chest", "neck",
                             "head", "thigh.L", "thigh.R", "shin.L", "shin.R")}
        out["cases"][label] = rec

    # ---- (d) 帧预算：竖直跨度 / 可用帧数 -----------------------------------
    z0 = out["cases"]["D14_END"]["head"]["pelvis"][2]
    z1 = out["cases"]["IDLE0"]["head"]["pelvis"][2]
    y0 = out["cases"]["D14_END"]["head"]["pelvis"][1]
    y1 = out["cases"]["IDLE0"]["head"]["pelvis"][1]
    total = 36
    out["span"] = {
        "pelvis_z_start_mm": z0, "pelvis_z_end_mm": z1, "dz_mm": round(z1 - z0, 3),
        "pelvis_y_start_mm": y0, "pelvis_y_end_mm": y1, "dy_mm": round(y1 - y0, 3),
        "total_frames": total,
        "dz_per_frame_mm": round((z1 - z0) / total, 3),
        "dy_per_frame_mm": round((y1 - y0) / total, 3),
        "rise_stage_frames": total - 24,
        "dz_per_frame_rise_stage_mm": round((z1 - z0) / max(1, total - 24), 3),
    }
    print("D17_BASE " + json.dumps(out, ensure_ascii=False))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D17_BASE_FAILURE " + traceback.format_exc())
