"""_e03_diag —— E03 `Rage` 的**量具标定**（只读，不改工程）。

要标定三件事（捶胸判据全靠它们）：
  (1) `R_FIST`：**拳的等效半径** —— 手网格顶点到手骨轴（`hand.head→tail`）的
      **垂直距离**分布（max / p98 / p90）。用它把「骨轴带符号距离」换算成
      「拳表面到胸面的距离」。
  (2) **模型误差**：同一姿态下，分别用
        (a) 骨轴采样 + `R_FIST`  推算的拳面距离
        (b) **手网格顶点 → 躯干网格面** 的带符号距离（真值）
      两者差多少 ⟹ 模型可信度。
  (3) **躯干网格面查询**（`closest_point_on_mesh` + 求值对象）在本工程里真的可用，
      并给出站架下「拳面到胸面」的实测距离（解释为什么站架不算穿模）。

用法：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_diag.py
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
HAND_PREFIX = ("Hand_Palm_", "Finger_", "Thumb_")
TORSO = "Suit_Torso"


def hand_vertices(side, step=3):
    dg = bpy.context.evaluated_depsgraph_get()
    out = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        base = obj.name.rsplit("_", 1)[0]
        if (not obj.name.endswith("_" + side)
                or not any(obj.name.startswith(p) for p in HAND_PREFIX)):
            continue
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        out += [mw @ me.vertices[i].co for i in range(0, len(me.vertices), step)]
        ev.to_mesh_clear()
    return out


def torso_query():
    """返回 (signed(p)->mm, surface_hit_count) —— 用求值后的躯干网格做最近面查询。"""
    obj = bpy.data.objects[TORSO]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    mw = ev.matrix_world.copy()
    inv = mw.inverted()
    rot = mw.to_3x3()
    hits = {"n": 0}

    def signed(p):
        local = inv @ Vector(p)
        ok, loc, nrm, _idx = ev.closest_point_on_mesh(local)
        if not ok:
            hits["n"] += 1
            return None
        world_loc = mw @ loc
        world_nrm = (rot @ nrm).normalized()
        return (Vector(p) - world_loc).dot(world_nrm) * 1000.0, world_loc, world_nrm

    return signed, hits


def perp_to_axis(p, a, b):
    ab = b - a
    if ab.length_squared < 1e-12:
        return (p - a).length
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    out = {}

    base = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, base)
    signed, hits = torso_query()

    for side in SIDES:
        hd = Vector(A.bone_world(arm, "hand." + side, "head"))
        ht = Vector(A.bone_world(arm, "hand." + side, "tail"))
        verts = hand_vertices(side)
        perp = sorted(perp_to_axis(p, hd, ht) for p in verts)
        n = len(perp)

        def pct(q):
            return round(perp[min(n - 1, int(q * n))] * 1000.0, 2)

        out["R_fist_mm_" + side] = {
            "max": round(perp[-1] * 1000.0, 2), "p98": pct(0.98),
            "p90": pct(0.90), "p50": pct(0.50), "verts": n,
            "hand_head": [round(v * 1000.0, 2) for v in hd],
            "hand_tail": [round(v * 1000.0, 2) for v in ht]}

        # (a) 骨轴采样 + R_FIST 模型
        r_model = perp[-1]
        best_model = None
        for i in range(9):
            p = hd.lerp(ht, i / 8.0)
            s = signed(p)
            if s is None:
                continue
            gap = s[0] - r_model * 1000.0
            best_model = gap if best_model is None else min(best_model, gap)
        # (b) 真值：手网格顶点 → 躯干面
        best_true = None
        for p in verts:
            s = signed(p)
            if s is None:
                continue
            best_true = s[0] if best_true is None else min(best_true, s[0])
        out["station_gap_mm_" + side] = {
            "model_axis_minus_Rfist": round(best_model, 2),
            "true_mesh_min": round(best_true, 2),
            "model_error_mm": round(best_model - best_true, 2)}

        # (c) ★★★ 拳心（`hand.tail` = 指节中心）到胸面的带符号距离 —— 本支主尺子
        core = signed(ht)
        out["core_gap_station_mm_" + side] = {
            "hand_tail": [round(v * 1000.0, 2) for v in ht],
            "signed_mm": round(core[0], 2),
            "surface": [round(v * 1000.0, 2) for v in core[1]],
            "normal": [round(v, 4) for v in core[2]]}

    # 胸口表面（x=±135 mm 处）+ 法线
    ch = Vector(A.bone_world(arm, "chest", "head"))
    ct = Vector(A.bone_world(arm, "neck", "head"))
    mid = ch.lerp(ct, 0.45)
    for side in SIDES:
        sx = 1.0 if side == "L" else -1.0
        probe = Vector((sx * 0.135, mid.y - 0.55, mid.z))
        s = signed(probe)
        out["chest_surface_" + side] = {
            "probe": [round(v * 1000.0, 2) for v in probe],
            "surface": [round(v * 1000.0, 2) for v in s[1]],
            "normal": [round(v, 4) for v in s[2]],
            "signed_mm": round(s[0], 2)}
    out["chest_axis_mid"] = [round(v * 1000.0, 2) for v in mid]
    out["query_misses"] = hits["n"]
    A.report("E03_DIAG", out)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E03_DIAG_FAILURE " + traceback.format_exc())
