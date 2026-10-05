"""probe_e07_baseline —— E07 `Victory_02` 胜利B（举拳）**开工第一件测量**（只量不做）。

清单 §「下一支详细制作计划 —— E07 `Victory_02`」第 1 步要求（三条）：

① 接缝：`Victory_01@120`(E06 末帧) 与 `Idle_01@0` 的逐骨世界矩阵差 —— 确认
   E07 起点仍可安全取 `Idle_01@0`。

② ★★ 连播不自洽的真风险：E06 与 E07 首帧同一姿态，E07 必须在**第一拍**就做出
   与 E06 不同的第一动作。本探针量 E06 在 f0~8 的姿态（沉髋量），给 E07 的
   「先下沉半蹲、再单臂上举」定标。

③ ★★★ 单臂举过头顶的**肩/肘/腕欧拉奇异性**实测 + **可达高度上限**：
   - 举手过顶会让 `hand` / `forearm` 逼近 `ry = ±90°` 奇异带；
   - 用 anim_victory_01 的成熟 `seat_arm`（IK 连续性 + 滚转基准 + 包络）**真解一遍**，
     扫「举臂目标高度」找**拳心实际可达 z** 与 euler 读数。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_e07_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_victory_01 as V1  # noqa: E402

SIDES = ("L", "R")


def mesh_box(names):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for vertex in me.vertices:
            p = mw @ vertex.co
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
        ev.to_mesh_clear()
    return Vector(lo), Vector(hi)


def main():  # noqa: C901
    # ★ `V1.boot()` 内部会 `open_animation_project()`（重开 .blend）—— 必须用**它返回的**
    #   arm，否则拿到的是重开前那个已被移除的 StructRNA（实测 ReferenceError）。
    arm, _meshes = V1.boot()       # 装好 station / IK 基（BASE=Idle_01@0）
    A.setup_scene()
    scene = bpy.context.scene

    for needed in ("Idle_01", "Victory_01"):
        if needed not in bpy.data.actions:
            print("E07_BASE 缺 Action %s（现有 %s）"
                  % (needed, [a.name for a in bpy.data.actions]))

    BONES = sorted(arm.pose.bones.keys())

    def hold(action, frame):
        act = bpy.data.actions[action]
        if arm.animation_data is None:
            arm.animation_data_create()
        arm.animation_data.action = act
        A._bind_slot(arm, act)
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        return {n: (arm.matrix_world @ arm.pose.bones[n].matrix).copy()
                for n in BONES if n in arm.pose.bones}

    def mat_delta(a, b):
        pos = (a.translation - b.translation).length * 1000.0
        worst = 0.0
        for k in range(3):
            va = a.to_3x3().col[k].normalized()
            vb = b.to_3x3().col[k].normalized()
            worst = max(worst, math.degrees(math.acos(
                max(-1.0, min(1.0, va.dot(vb))))))
        return pos, worst

    # ------------------------------------------------------------- ① 接缝
    idle0 = hold("Idle_01", 0)
    vic120 = hold("Victory_01", 120)
    worst_pos, worst_dir, worst_at = 0.0, 0.0, None
    for n in BONES:
        if n in idle0 and n in vic120:
            pos, deg = mat_delta(idle0[n], vic120[n])
            if pos > worst_pos or deg > worst_dir:
                worst_at = n
            worst_pos = max(worst_pos, pos)
            worst_dir = max(worst_dir, deg)
    print("E07_BASE_SEAM " + json.dumps({
        "pair": "Victory_01@120 vs Idle_01@0",
        "pos_max_mm": round(worst_pos, 6),
        "dir_max_deg": round(worst_dir, 6),
        "at": worst_at,
        "verdict": ("逐位一致（浮点噪声级）⟹ E07 起点取 Idle_01@0 可连播"
                    if worst_pos < 0.01 and worst_dir < 0.05 else "有差异，需裁决"),
    }, ensure_ascii=False))

    # ------------------------------------------------------------- ①b 站架实测
    hold("Idle_01", 0)
    station = {s: Vector(A.bone_world(arm, "hand." + s, "tail"))
               for s in SIDES}
    shoulder = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                for s in SIDES}
    pelvis0 = Vector(A.bone_world(arm, "pelvis", "head"))
    head_top = Vector(A.bone_world(arm, "head", "tail"))
    arm_len = {s: {"up": arm.pose.bones["upperarm." + s].length,
                   "fo": arm.pose.bones["forearm." + s].length,
                   "ha": arm.pose.bones["hand." + s].length} for s in SIDES}
    lo, hi = mesh_box(("Head", "Hair_Mass", "Hair_Sweep", "Nose"))
    tlo, thi = mesh_box(("Suit_Torso",))
    reach = {s: round((arm_len[s]["up"] + arm_len[s]["fo"]
                       + arm_len[s]["ha"]) * 1000.0, 1) for s in SIDES}
    print("E07_BASE_STATION " + json.dumps({
        "fist_mm": {s: [round(v * 1000.0, 1) for v in station[s]] for s in SIDES},
        "shoulder_mm": {s: [round(v * 1000.0, 1) for v in shoulder[s]]
                        for s in SIDES},
        "pelvis_z_mm": round(pelvis0.z * 1000.0, 1),
        "head_tail_z_mm": round(head_top.z * 1000.0, 1),
        "arm_len_mm": {s: {k: round(v * 1000.0, 1)
                           for k, v in arm_len[s].items()} for s in SIDES},
        "arm_total_mm": reach,
        "max_fist_z_geom_mm": {
            s: round((shoulder[s].z + (arm_len[s]["up"] + arm_len[s]["fo"]
                                      + arm_len[s]["ha"])) * 1000.0, 1)
            for s in SIDES},
        "head_box_mm": {"lo": [round(v * 1000.0, 1) for v in lo],
                        "hi": [round(v * 1000.0, 1) for v in hi]},
        "torso_box_mm": {"lo": [round(v * 1000.0, 1) for v in tlo],
                         "hi": [round(v * 1000.0, 1) for v in thi]},
    }, ensure_ascii=False))

    # ------------------------------------------------------------- ② E06 起手
    e06 = {}
    for frame in (0, 4, 8, 12, 14):
        hold("Victory_01", frame)
        e06[str(frame)] = {
            "pelvis_z_mm": round(
                Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 2),
            "fist_L_mm": [round(v * 1000.0, 1)
                          for v in A.bone_world(arm, "hand.L", "tail")],
            "fist_R_mm": [round(v * 1000.0, 1)
                          for v in A.bone_world(arm, "hand.R", "tail")],
        }
    print("E07_BASE_E06START " + json.dumps(e06, ensure_ascii=False))

    # ------------------------------------------------------------- ③ 举臂扫描
    # 真解 IK：用 V1.seat_arm（blend=0 → 拳沿前臂，即「举拳」而非「拳面朝内」）。
    # 目标：L 臂举到 (x, y, z)；R 臂下放体侧。
    base = V1.victory_pose(arm, 0)
    scans = {}
    for z in (1780, 1840, 1900, 1940, 1980, 2020, 2060):
        targets = {
            "L": Vector((0.30, -0.06, z / 1000.0)),
            "R": Vector((-0.34, 0.10, 1.02)),
        }
        normals = {s: Vector((0.0, -1.0, 0.0)) for s in SIDES}
        pose = dict(base)
        V1.LAST_ELBOW = {}
        V1.LAST_TWIST_ANGLE = {}
        V1.MIN_HINT_MARGIN = 1.0
        V1.seat_arm(arm, pose, targets, normals, blend=0.0, env=1.0)
        A.apply_pose(arm, pose)
        core = Vector(A.bone_world(arm, "hand.L", "tail"))
        shoulder_l = Vector(A.bone_world(arm, "upperarm.L", "head"))
        eul = {}
        for name in ("upperarm.L", "forearm.L", "hand.L"):
            eul[name] = [round(math.degrees(v), 2)
                         for v in arm.pose.bones[name].rotation_euler]
        scans[str(z)] = {
            "want_z_mm": z,
            "got_core_mm": [round(v * 1000.0, 1) for v in core],
            "core_from_shoulder_mm": round((core - shoulder_l).length * 1000.0, 1),
            "euler_deg": eul,
            "hint_margin": round(V1.MIN_HINT_MARGIN, 4),
        }
    print("E07_BASE_RAISE " + json.dumps(scans, ensure_ascii=False))

    # 举臂姿态的**手 vs 头盒**最小距离（no_face_clip 的几何依据）
    for z in (1900, 1980):
        targets = {"L": Vector((0.30, -0.06, z / 1000.0)),
                   "R": Vector((-0.34, 0.10, 1.02))}
        normals = {s: Vector((0.0, -1.0, 0.0)) for s in SIDES}
        pose = dict(base)
        V1.LAST_ELBOW = {}
        V1.LAST_TWIST_ANGLE = {}
        V1.seat_arm(arm, pose, targets, normals, blend=0.0, env=1.0)
        A.apply_pose(arm, pose)
        clip = V1.PD.clip_metrics(arm)
        print("E07_BASE_CLIP z=%d %s" % (z, json.dumps(clip, ensure_ascii=False)))

    print("E07_BASE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E07_BASE_FAILURE " + traceback.format_exc())
