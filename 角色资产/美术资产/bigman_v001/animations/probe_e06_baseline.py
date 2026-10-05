"""probe_e06_baseline —— E06 `Victory_01` 暴力胜利（捶胸）**开工第一件测量**（只量不做）。

清单 §「E06 详细计划」（写在 E05 日志末）第 1 步要求：

    ★★★ **E06（捶胸）与 E03 `Rage` 的 `rage_chest_hit_ok` 会撞车** ——
    E03 已做过「仰头怒吼 + 单臂交替捶胸」。E06 **必须做出差异**。
    开工第一件事：**读 E03 的 `rage_chest_hit_ok` 实现与实测值，明确差在哪一维。**

★ 本探针就是回答那一句。它做四件事：

① **上游接缝**：`Idle_01@0` vs `Battle_Start@96`（E05 末帧）的逐骨世界矩阵差；
   两者都在浮点噪声级时，按**语义**选 —— E06 是「玩家赢了的那一刻」，角色还在
   **战斗站架**上 ⟹ 语义上只能是 `Idle_01@0`。

② ★★★ **E03 的实际形态实测**（推翻/确认计划前提）：`Rage` 在
   蓄力 f=20 / 第一次命中 f=28..30 / 怒吼顶 f=44 / 第二次命中 f=52..54
   各帧的：两拳心世界坐标、**两拳间距**、两侧「拳面（非拇指）到躯干的最小带符号
   距离」、头+颈相对 chest 的后仰角、骨盆 z、躯干俯仰。
   ⟹ 得到「E03 到底是单臂还是双臂」「捶点在哪」的**事实**，再据此设计 E06 的差异。

③ **胸面 pec 探针**：在站架姿下，对若干候选探针点求 `Suit_Torso` 的
   最近表面点 + 外法线（世界），供 E06 的捶击目标 `surf + nrm × 深度` 用。

④ **可达 / 包围盒 / 肘极余量**：肩→pec 距离 vs 臂总长（可行性）；
   头盒 / 躯干盒（`no_face_clip_ok` 与手-躯干判据的几何依据）；
   拳目标位置处的 `手骨滚转基准` 投影余量（E03 v009 那个 83.86°/帧 坑的守卫）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_e06_baseline.py
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
import probe_d01_guard as PD  # noqa: E402

SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
HAND_PREFIX = ("Hand_Palm_", "Finger_", "Thumb_")
TORSO_MESH = "Suit_Torso"

# E03 `Rage` 的实测相位（照 `anim_rage.py` 的默认 env）
E03_WINDUP = 20
E03_HIT1 = 28
E03_ROAR = 44
E03_HIT2 = 52
E03_ROAR2 = 66
E03_HOLD1 = (28, 30)
E03_HOLD2 = (52, 54)

# E06 候选 pec 探针点（世界坐标，站架姿下；x=±，y 取胸前，z 取胸肌高度）
PEC_CANDIDATES = {
    "P_100_1280": (0.100, -0.300, 1.280),
    "P_135_1280": (0.135, -0.300, 1.280),
    "P_175_1280": (0.175, -0.300, 1.280),
    "P_135_1230": (0.135, -0.300, 1.230),
    "P_175_1180": (0.175, -0.300, 1.180),
    "P_135_1330": (0.135, -0.300, 1.330),
}


def _torso_obj():
    return bpy.data.objects[TORSO_MESH]


def torso_query(point):
    """点到躯干面的 (带符号距离 mm, 面上最近点, 外法线)。"""
    obj = _torso_obj()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(depsgraph)
    mw = ev.matrix_world.copy()
    _ok, loc, nrm, _idx = ev.closest_point_on_mesh(mw.inverted() @ Vector(point))
    world_loc = mw @ loc
    world_nrm = (mw.to_3x3() @ nrm).normalized()
    gap = (Vector(point) - world_loc).dot(world_nrm) * 1000.0
    return gap, Vector(world_loc), Vector(world_nrm)


def hand_points(side, step=2):
    """[(世界坐标, 对象名)] —— 该侧手部全部网格顶点。"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not any(obj.name.startswith(p) for p in HAND_PREFIX):
            continue
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for index in range(0, len(me.vertices), step):
            out.append((mw @ me.vertices[index].co, obj.name))
        ev.to_mesh_clear()
    return out


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


def head_angle(arm, base_neck, base_head):
    """头颈相对站架的后仰角（度，正 = 后仰）。口径照 E03 `current_head_back`。"""
    d_neck = math.degrees(arm.pose.bones["neck"].rotation_euler.x) - base_neck
    d_head = math.degrees(arm.pose.bones["head"].rotation_euler.x) - base_head
    return -(d_neck + d_head)


def hold_action(arm, name):
    action = bpy.data.actions.get(name)
    if action is None:
        return None
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    return action


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene
    BONES = sorted(arm.pose.bones.keys())

    for needed in ("Idle_01", "Battle_Start", "Rage"):
        if needed not in bpy.data.actions:
            print("E06_BASE 缺 Action %s（现有 %s）"
                  % (needed, [a.name for a in bpy.data.actions]))

    def mats(action, frame):
        hold_action(arm, action)
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

    # ---------------------------------------------------------------- ① 接缝
    idle0 = mats("Idle_01", 0)
    bstart96 = mats("Battle_Start", 96)
    worst_pos, worst_dir, worst_at = 0.0, 0.0, None
    for n in BONES:
        if n in idle0 and n in bstart96:
            pos, deg = mat_delta(idle0[n], bstart96[n])
            if pos > worst_pos or deg > worst_dir:
                worst_at = n
            worst_pos = max(worst_pos, pos)
            worst_dir = max(worst_dir, deg)
    print("E06_BASE_SEAM " + json.dumps({
        "pair": "Idle_01@0 vs Battle_Start@96",
        "pos_max_mm": round(worst_pos, 6),
        "dir_max_deg": round(worst_dir, 6),
        "at": worst_at,
        "verdict": ("逐位一致（浮点噪声级）⟹ 按语义选 Idle_01@0"
                    if worst_pos < 0.01 and worst_dir < 0.05 else "有差异，需裁决"),
    }, ensure_ascii=False))

    # ---------------------------------------------------------------- ①b 站架实测
    hold_action(arm, "Idle_01")
    scene.frame_set(0)
    bpy.context.view_layer.update()
    base_neck = math.degrees(arm.pose.bones["neck"].rotation_euler.x)
    base_head = math.degrees(arm.pose.bones["head"].rotation_euler.x)
    station = {}
    for side in SIDES:
        station[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
    pelvis0 = Vector(A.bone_world(arm, "pelvis", "head"))
    head0 = Vector(A.bone_world(arm, "head", "tail"))
    sternum0 = Vector(A.bone_world(arm, "neck", "head"))
    shoulder0 = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                 for s in SIDES}
    arm_len = {}
    for side in SIDES:
        arm_len[side] = {
            "up": arm.pose.bones["upperarm." + side].length,
            "lo": (arm.pose.bones["forearm." + side].length
                   + arm.pose.bones["hand." + side].length)}
    lo, hi = mesh_box(("Head", "Hair_Mass", "Hair_Sweep", "Nose"))
    head_box = {"lo_mm": [round(v * 1000.0, 1) for v in lo],
                "hi_mm": [round(v * 1000.0, 1) for v in hi]}
    tlo, thi = mesh_box((TORSO_MESH,))
    torso_box = {"lo_mm": [round(v * 1000.0, 1) for v in tlo],
                 "hi_mm": [round(v * 1000.0, 1) for v in thi]}
    print("E06_BASE_STATION " + json.dumps({
        "fist_mm": {s: [round(v * 1000.0, 1) for v in station[s]] for s in SIDES},
        "pelvis_z_mm": round(pelvis0.z * 1000.0, 1),
        "head_tail_z_mm": round(head0.z * 1000.0, 1),
        "sternum_z_mm": round(sternum0.z * 1000.0, 1),
        "shoulder_mm": {s: [round(v * 1000.0, 1) for v in shoulder0[s]]
                        for s in SIDES},
        "arm_len_mm": {s: {k: round(v * 1000.0, 1) for k, v in arm_len[s].items()}
                       for s in SIDES},
        "head_box": head_box, "torso_box": torso_box,
    }, ensure_ascii=False))

    # ---------------------------------------------------------------- ② E03 实测
    rows = {}
    for frame in (0, E03_WINDUP, E03_HIT1, E03_HOLD1[1], E03_ROAR,
                  E03_HIT2, E03_HOLD2[1], E03_ROAR2, 96):
        hold_action(arm, "Rage")
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {"pelvis_z_mm": round(
            Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 1),
            "sternum_z_mm": round(
                Vector(A.bone_world(arm, "neck", "head")).z * 1000.0, 1),
            "head_tail_z_mm": round(
                Vector(A.bone_world(arm, "head", "tail")).z * 1000.0, 1),
            "head_back_deg": round(head_angle(arm, base_neck, base_head)
                                   if "neck" in arm.pose.bones else 0.0, 2),
            "chest_rx_deg": round(
                math.degrees(arm.pose.bones["chest"].rotation_euler.x), 2),
            "fist_mm": {}, "face_min_mm": {}, "thumb_min_mm": {},
            "core_gap_mm": {}}
        for side in SIDES:
            c = Vector(A.bone_world(arm, "hand." + side, "tail"))
            row["fist_mm"][side] = [round(v * 1000.0, 1) for v in c]
            pts = hand_points(side, step=2)
            face = [torso_query(p)[0] for p, n in pts
                    if not n.startswith("Thumb_")]
            thumb = [torso_query(p)[0] for p, n in pts if n.startswith("Thumb_")]
            row["face_min_mm"][side] = round(min(face), 2) if face else None
            row["thumb_min_mm"][side] = round(min(thumb), 2) if thumb else None
            row["core_gap_mm"][side] = round(torso_query(c)[0], 2)
        row["fist_dx_mm"] = round(
            (Vector(row["fist_mm"]["L"]) - Vector(row["fist_mm"]["R"])).length, 1)
        rows[str(frame)] = row
    print("E06_BASE_E03 " + json.dumps(rows, ensure_ascii=False))

    # ---------------------------------------------------------------- ③ 胸面 pec 探针
    hold_action(arm, "Idle_01")
    scene.frame_set(0)
    bpy.context.view_layer.update()
    pec = {}
    for tag, (x, y, z) in PEC_CANDIDATES.items():
        gap, surf, nrm = torso_query((x, y, z))
        pec[tag] = {"probe_mm": [round(x * 1000.0, 1), round(y * 1000.0, 1),
                                 round(z * 1000.0, 1)],
                    "surf_mm": [round(v * 1000.0, 1) for v in surf],
                    "nrm": [round(v, 4) for v in nrm],
                    "gap_mm": round(gap, 2),
                    "reach_mm": round((surf - shoulder0["L" if x >= 0 else "R"]
                                       ).length * 1000.0, 1)}
    print("E06_BASE_PEC " + json.dumps(pec, ensure_ascii=False))

    # ---------------------------------------------------------------- ④ 拳位可达 + 滚转余量
    # 站架拳位与 pec 目标的臂长占用 + 手骨滚转基准（前臂局部 x）投影余量
    hold_action(arm, "Idle_01")
    scene.frame_set(0)
    bpy.context.view_layer.update()
    margins = {}
    for side in SIDES:
        mat = arm.pose.bones["forearm." + side].matrix.to_3x3()
        hint = Vector(mat.col[0]).normalized()
        y_dir = Vector((A.bone_world(arm, "hand." + side, "tail")
                        - A.bone_world(arm, "forearm." + side, "head"))).normalized()
        margins["station_" + side] = round(
            (hint - y_dir * hint.dot(y_dir)).length, 4)
    print("E06_BASE_ROLL " + json.dumps(margins, ensure_ascii=False))
    print("E06_BASE_HEADBOX " + json.dumps(head_box, ensure_ascii=False))
    print("E06_BASE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E06_BASE_FAILURE " + traceback.format_exc())
