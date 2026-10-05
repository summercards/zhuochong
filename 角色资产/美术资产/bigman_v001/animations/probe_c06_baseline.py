"""probe_c06_baseline —— 只量不做：读 `Grab_Hold@120`（C05 末帧），
量出 C06 `Throw` 起手所需的全部基座量、**可达余量**与**髋部可转范围**。

要回答的问题（清单 C06 计划第 4 步第 2 条）：
  1. 双手位置逆解还能再往外/往上走多少（`arm_seat` 的 margin）？
     C05 只剩 ~20 mm ⟹ 释放前的动作必须是"收"。
  2. 该姿态下腿的可达余量（髋能不能大幅旋转 / 下沉）。
  3. 骨盆、踝、双手的世界基线 → C06 首帧逐位复现用。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c06_baseline.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_grab04 as G4        # noqa: E402
import anim_grab05 as G5        # noqa: E402

SIDES = ("L", "R")
SRC_FRAME = 120                 # Grab_Hold 末帧


def unit(v):
    v = Vector(v)
    n = v.length or 1.0
    return v / n


def ang(a, b):
    return math.degrees(unit(a).angle(unit(b)))


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()

    action = bpy.data.actions[G5.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene = bpy.context.scene
    scene.frame_set(SRC_FRAME)
    bpy.context.view_layer.update()

    out = {"source": [G5.NAME, SRC_FRAME]}

    # ---- 世界坐标基线
    pts = {}
    for name in ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
                 "shoulder.L", "shoulder.R", "upperarm.L", "upperarm.R",
                 "forearm.L", "forearm.R", "hand.L", "hand.R",
                 "thigh.L", "thigh.R", "shin.L", "shin.R",
                 "foot.L", "foot.R", "toe.L", "toe.R"):
        pts[name] = {
            "head_mm": [round(v * 1000.0, 3)
                        for v in A.bone_world(arm, name, "head")],
            "tail_mm": [round(v * 1000.0, 3)
                        for v in A.bone_world(arm, name, "tail")],
        }
    out["bones"] = pts

    # ---- 双手可达余量（最关键）
    arm_len = {}
    reach = {}
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        l1 = arm.pose.bones[up].length
        l23 = arm.pose.bones[fo].length + arm.pose.bones[hd].length
        arm_len[side] = {
            "upper": round(l1 * 1000.0, 3),
            "forearm": round(arm.pose.bones[fo].length * 1000.0, 3),
            "hand": round(arm.pose.bones[hd].length * 1000.0, 3),
        }
        sh = Vector(A.bone_world(arm, up, "head"))
        tg = Vector(A.bone_world(arm, hd, "tail"))
        limit = (l1 + l23) * 0.9995
        d = (tg - sh).length
        reach[side] = {
            "grab_point_mm": [round(v * 1000.0, 4) for v in tg],
            "shoulder_mm": [round(v * 1000.0, 4) for v in sh],
            "dist_mm": round(d * 1000.0, 4),
            "limit_mm": round(limit * 1000.0, 4),
            "margin_mm": round((limit - d) * 1000.0, 4),
            "reach_ratio": round(d / (l1 + l23), 6),
        }
    out["arm_len_mm"] = arm_len
    out["reach_margin"] = reach

    # ---- 腿可达余量
    lim_leg = A.L_THIGH + A.L_SHIN
    leg = {}
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        ank = Vector(A.bone_world(arm, "foot." + side, "head"))
        d = (ank - hip).length
        leg[side] = {
            "hip_mm": [round(v * 1000.0, 4) for v in hip],
            "ankle_mm": [round(v * 1000.0, 4) for v in ank],
            "dist_mm": round(d * 1000.0, 4),
            "limit_mm": round(lim_leg * 1000.0, 4),
            "margin_mm": round((lim_leg - d) * 1000.0, 4),
            "reach_ratio": round(d / lim_leg, 6),
        }
    out["leg"] = leg

    # ---- 非静止骨骼的 euler / loc（C06 首帧逐位复现 + 回填用）
    euler = {}
    for b in arm.pose.bones:
        val = tuple(round(math.degrees(v), 6) for v in b.rotation_euler)
        loc = tuple(round(v, 12) for v in b.location)
        if any(abs(x) > 1e-9 for x in val) or any(abs(x) > 1e-12 for x in loc):
            euler[b.name] = {"euler_deg": val, "loc": loc}
    out["nonrest_bones"] = euler

    # ---- 躯干链累计前倾
    chain = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head")
    out["trunk_rx_deg"] = {
        n: round(math.degrees(arm.pose.bones[n].rotation_euler[0]), 4)
        for n in chain}

    # ---- 骨盆旋转能力试探：在保持双脚踝钉死的前提下，
    #      把 pelvis.ry 额外加 d，用 leg_seat 解回去，看腿可达比 & 支点漂移。
    base_pose = {}
    for b in arm.pose.bones:
        base_pose[b.name] = tuple(math.degrees(v) for v in b.rotation_euler)
    base_loc = {b.name: tuple(b.location) for b in arm.pose.bones
                if any(abs(v) > 1e-12 for v in b.location)}
    base_pose["@loc"] = base_loc
    base_pose.pop("thigh.L", None)
    base_pose.pop("shin.L", None)
    base_pose.pop("foot.L", None)
    base_pose.pop("thigh.R", None)
    base_pose.pop("shin.R", None)
    base_pose.pop("foot.R", None)

    ankle = {s: Vector(A.bone_world(arm, "foot." + s, "head")).copy()
             for s in SIDES}
    knee_dir = {}
    for s in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + s, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + s, "tail"))
        knee_dir[s] = (knee - hip).normalized()

    # 骨架基准（Idle 站架）
    I1 = __import__("anim_idle_01")
    arm.animation_data.action = bpy.data.actions[I1.NAME]
    A._bind_slot(arm, bpy.data.actions[I1.NAME])
    A.apply_pose(arm, I1.idle_pose(arm, 0.0))
    bpy.context.view_layer.update()
    idle_basis = {}
    idle_dir = {}
    for name in ("thigh.L", "shin.L", "thigh.R", "shin.R"):
        idle_basis[name] = arm.pose.bones[name].matrix.to_3x3().copy()
        idle_dir[name] = A.bone_direction(arm, name)
    G4.IDLE_BASIS.clear()
    G4.IDLE_BASIS.update(idle_basis)
    G4.IDLE_DIR.clear()
    G4.IDLE_DIR.update(idle_dir)
    G4.IDLE_KNEE_DIR.clear()
    G4.IDLE_KNEE_DIR.update(knee_dir)

    sweep = {}
    for dry in (0.0, 10.0, 20.0, 30.0, 40.0):
        for drx in (0.0, -5.0):
            pose = dict(base_pose)
            p = pose.get("pelvis", (0.0, 0.0, 0.0))
            pose["pelvis"] = (p[0] + drx, p[1] + dry, p[2])
            A.apply_pose(arm, pose)
            worst = 0.0
            ratios = {}
            for s in SIDES:
                G4.leg_seat(arm, pose, s, ankle[s], knee_dir[s])
                hip = Vector(A.bone_world(arm, "thigh." + s, "head"))
                got = Vector(A.bone_world(arm, "foot." + s, "head"))
                err = (got - ankle[s]).length * 1000.0
                worst = max(worst, err)
                ratios[s] = round((ankle[s] - hip).length / lim_leg, 5)
            key = "ry%+05.1f_rx%+05.1f" % (dry, drx)
            sweep[key] = {"ankle_err_mm": round(worst, 4),
                          "leg_reach_ratio": ratios}
    out["pelvis_sweep"] = sweep

    A.report("C06_BASELINE", out)
    print("C06_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C06_PROBE_FAILURE " + traceback.format_exc())
