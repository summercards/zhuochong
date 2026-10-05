"""probe_d15_measure —— D15 `Knockdown_B` 开工前的实测标定（只读，不改任何资产）。

回答三件事（清单 D15 计划 §4 第 3 步）：
  (a) 弹道骨盆高 f0~f22 表 —— 确定 `LAND` 候选；
  (b) 接缝姿态（`Air_Hit@18`）逐对象最低点 —— 谁是最低、接缝鞋底多高；
  (c) 接缝躯干世界俯仰 + 手臂朝向 —— 后倒俯仰的基线。

用法：
    blender.exe --background --factory-startup --python probe_d15_measure.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                    # noqa: E402
import anim_jump_start as JS            # noqa: E402
import anim_crouch as CR                # noqa: E402

SEAM_ACTION = "Air_Hit"
SEAM_FRAME = 18
D13_T_PHASE = 31.5
T_PHASE = D13_T_PHASE + SEAM_FRAME      # 49.5


def _pitch(direction):
    return -math.degrees(math.atan2(direction.y, direction.z))


def ball_z(frame):
    t = T_PHASE + float(frame)
    return JS.TAKEOFF_PELVIS_Z + JS.TAKEOFF_SPEED * t - 0.5 * JS.G_PER_FRAME * t * t


def ball_vz(frame):
    return JS.TAKEOFF_SPEED - JS.G_PER_FRAME * (T_PHASE + float(frame))


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene

    # ---- 弹道表 -----------------------------------------------------------
    table = {}
    for f in range(0, 23):
        table[str(f)] = {
            "pelvis_z_mm": round(ball_z(f) * 1000.0, 2),
            "vz_mm_per_frame": round(ball_vz(f) * 1000.0, 4),
            "diff_mm": round((ball_z(f) - ball_z(f - 1)) * 1000.0, 3) if f > 0 else None,
        }

    # ---- 接缝姿态 ---------------------------------------------------------
    action = bpy.data.actions.get(SEAM_ACTION)
    if action is None:
        raise RuntimeError("找不到 %s" % SEAM_ACTION)
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene.frame_set(SEAM_FRAME)
    bpy.context.view_layer.update()

    dg = bpy.context.evaluated_depsgraph_get()
    objs = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        if len(me.vertices) == 0:
            ev.to_mesh_clear()
            continue
        mw = ev.matrix_world
        pts = [mw @ v.co for v in me.vertices]
        zmin = min(p.z for p in pts)
        # 该对象的 y 范围（判断前后）
        ymin = min(p.y for p in pts)
        ymax = max(p.y for p in pts)
        objs.append({"obj": obj.name, "z_min_mm": round(zmin * 1000.0, 2),
                     "y_min_mm": round(ymin * 1000.0, 1),
                     "y_max_mm": round(ymax * 1000.0, 1)})
        ev.to_mesh_clear()
    objs.sort(key=lambda r: r["z_min_mm"])

    torso = ("root", "pelvis", "spine_01", "spine_02", "chest", "neck", "head")
    pitches = {n: round(_pitch(Vector(A.bone_direction(arm, n))), 3) for n in torso}

    bones = {}
    for n in A.PROBE_BONES:
        if n in arm.pose.bones:
            bones[n] = [round(v * 1000.0, 1)
                        for v in Vector(A.bone_world(arm, n, "head"))]
    head_tail = [round(v * 1000.0, 1)
                 for v in Vector(A.bone_world(arm, "head", "tail"))]
    pelvis_head = [round(v * 1000.0, 1)
                   for v in Vector(A.bone_world(arm, "pelvis", "head"))]

    hand_dir = {}
    for s in ("L", "R"):
        hand_dir[s] = [round(v, 4) for v in
                       Vector(A.bone_direction(arm, "hand." + s)).normalized()]
    fist = {s: [round(v * 1000.0, 1) for v in
                Vector(A.bone_world(arm, "hand." + s, "tail"))] for s in ("L", "R")}

    # ---- (b2) 试构一个粗略仰卧姿态，量"骨盆骨 → 臀区最低点"落差 ----------
    #   做法：取接缝姿态，把 root 绕世界 X 转 −90°（整体后倒躺平），再量各对象最低点。
    #   目的：知道"骨盆骨多高时，臀/背刚好贴地"——决定 LAND 与 Z_PELVIS_END。
    supine = {}
    for tilt in (90.0, 75.0, 60.0):
        arm.animation_data.action = action
        A._bind_slot(arm, action)
        scene.frame_set(SEAM_FRAME)
        bpy.context.view_layer.update()
        rig = {b.name: tuple(math.degrees(x) for x in b.rotation_euler)
               for b in arm.pose.bones}
        locs = {b.name: tuple(b.location) for b in arm.pose.bones
                if b.location.length > 1e-9}
        arm.animation_data.action = None
        rig["root"] = (rig["root"][0] - tilt, rig["root"][1], rig["root"][2])
        pp = {k: v for k, v in rig.items()}
        if locs:
            pp["@loc"] = locs
        A.apply_pose(arm, pp)
        bpy.context.view_layer.update()
        dg2 = bpy.context.evaluated_depsgraph_get()
        rows = []
        for obj in bpy.data.objects:
            if obj.type != "MESH":
                continue
            ev = obj.evaluated_get(dg2)
            me = ev.to_mesh()
            if len(me.vertices) == 0:
                ev.to_mesh_clear()
                continue
            mw = ev.matrix_world
            rows.append((min((mw @ v.co).z for v in me.vertices) * 1000.0,
                         obj.name))
            ev.to_mesh_clear()
        rows.sort()
        pel = Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0
        supine[str(int(tilt))] = {
            "pelvis_z_mm": round(pel, 1),
            "low5": [{"z_mm": round(z, 1), "obj": n} for z, n in rows[:5]],
            "pelvis_minus_low_mm": round(pel - rows[0][0], 1),
        }

    A.report("D15_MEASURE", {
        "supine_probe": supine,
        "ballistic": table,
        "t_phase": T_PHASE,
        "seam": {"action": SEAM_ACTION, "frame": SEAM_FRAME,
                 "pelvis_head_mm": pelvis_head,
                 "head_tail_mm": head_tail,
                 "pitches_deg": pitches,
                 "hand_dir": hand_dir,
                 "fist_mm": fist,
                 "bones_mm": bones},
        "lowest_objects": objs[:14],
    })


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("D15_MEASURE_FAILURE " + traceback.format_exc())
