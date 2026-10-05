"""probe_e08_baseline —— E08 `Victory_03` 胜利C（擦拳套）**开工第一件测量**（只量不做）。

清单 §「下一支详细制作计划 —— E08」第 1 步要求（**四件**，比前两支多一件）：

① 接缝：`Victory_02@120`(E07 末帧) 与 `Idle_01@0` 的逐骨世界矩阵差 —— 确认
   E08 起点仍可安全取 `Idle_01@0`。★ 必须**实测复核**，不许引用 E06/E07 的读数。

② ★★ 连播不自洽的真风险：E06 / E07 / E08 **三支首帧同一姿态**。已有两拍：
   E06 = 沉髋**收拳向前**（f14 拳心 y = −310 mm），E07 = 半蹲**甩拳向后**（f14 y = +166 mm）。
   ⟹ E08 的**第一拍必须第三样**，且位移最小。本探针把两支的第一拍读数**实测**出来。

③ ★★★ **两手互擦的自接触几何**（本支第一次出现）：站架时左右拳心相距多少？
   拳网格（`Hand_Palm_*` / `Finger_*` / `Thumb_*`）的包络多大？在「胸前中线」摆位时，
   两拳网格的**最近带符号距离**能否做到 0~15 mm（贴合但不穿透）？

④ **小幅度下的可达区间 + 缓动时相**：在「拳心距站架 ≤ 120 mm」的预算内，两拳能靠多近；
   一次往复在 6~8 帧内完成时臂的最大角步是多少。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_e08_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_victory_02 as V2  # noqa: E402

SIDES = ("L", "R")
HAND_PREFIX = V2.HAND_PREFIX


def hand_mesh_box(side):
    """该侧手部网格的世界包围盒（lo, hi）。"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not any(obj.name.startswith(p) for p in HAND_PREFIX):
            continue
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for v in me.vertices:
            p = mw @ v.co
            for i in range(3):
                lo[i] = min(lo[i], p[i])
                hi[i] = max(hi[i], p[i])
        ev.to_mesh_clear()
    return Vector(lo), Vector(hi)


def hand_bvh(side, step=1):
    """该侧手部网格的 BVH（世界空间）。"""
    import mathutils.bvhtree as bvhtree
    depsgraph = bpy.context.evaluated_depsgraph_get()
    verts, polys = [], []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not any(obj.name.startswith(p) for p in HAND_PREFIX):
            continue
        ev = obj.evaluated_get(depsgraph)
        me = ev.to_mesh()
        mw = ev.matrix_world
        off = len(verts)
        for v in me.vertices:
            verts.append((mw @ v.co)[:])
        for poly in me.polygons:
            polys.append([off + i for i in poly.vertices])
        ev.to_mesh_clear()
    if not verts:
        return None
    return bvhtree.BVHTree.FromPolygons(verts, polys)


def points_of(side, step=2):
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
        for i in range(0, len(me.vertices), step):
            out.append(mw @ me.vertices[i].co)
        ev.to_mesh_clear()
    return out


def _parity(tree, point, direction):
    origin = Vector(point)
    hits = 0
    for _ in range(64):
        loc, _n, index, dist = tree.ray_cast(origin, direction)
        if loc is None or index is None:
            break
        hits += 1
        origin = loc + direction * max(1e-7, dist * 1e-6 + 1e-7)
    return hits % 2 == 1


def hand_vs_hand_gap(step=2, ray_dir=Vector((0.0, 0.0, 1.0))):
    """L 手网格 → R 手网格的**最小带符号距离**（mm）。

    ★ 本支第一次出现「手 vs 手」的自接触：口径照抄 `fist_face_gap`，只把参照物
      从躯干 `Suit_Torso` 换成**对侧手网格**。左右**互为目标**（A 查 B、B 查 A），
      各取最小，返回 (gap_mm, which) —— 负 = 穿透。
    """
    out = []
    for a, b in (("L", "R"), ("R", "L")):
        tree = hand_bvh(b)
        if tree is None:
            continue
        worst, worst_p = None, None
        for p in points_of(a, step=step):
            loc, _n, _i, dist = tree.find_nearest(Vector(p))
            if loc is None:
                continue
            # ★ 只有贴近表面（< 25 mm）才做射线奇偶判定，否则直接取正距离（提速）。
            if dist * 1000.0 < 25.0 and _parity(tree, p, ray_dir):
                signed = -dist
            else:
                signed = dist
            if worst is None or signed < worst:
                worst, worst_p = signed, (loc - Vector(p)).length
        if worst is not None:
            out.append((a + "->" + b, worst * 1000.0))
    if not out:
        return None, None
    who, mm = min(out, key=lambda kv: kv[1])
    return round(mm, 3), who


def main():  # noqa: C901
    # ★ `V2.boot()` 内部会 `open_animation_project()`（重开 .blend）—— 必须用它返回的 arm。
    arm, _meshes = V2.boot()
    A.setup_scene()
    scene = bpy.context.scene
    # ★★ 本支**双臂都动**（擦拳套）⟹ 关掉 E07 的「守护手整臂继承站架」口径，
    #    并让非举起手按 `FIST_TABLE` 正常解 IK（否则 R 臂不会被求解）。
    V2.GUARD_HAND_RIGID = False
    V2.OFFHAND_MODE = "side"

    for needed in ("Idle_01", "Victory_01", "Victory_02"):
        if needed not in bpy.data.actions:
            print("E08_BASE 缺 Action %s（现有 %s）"
                  % (needed, sorted(a.name for a in bpy.data.actions)))

    BONES = sorted(arm.pose.bones.keys())

    def hold(action, frame):
        act = bpy.data.actions[action]
        if arm.animation_data is None:
            arm.animation_data_create()
        arm.animation_data.action = act
        A._bind_slot(arm, act)
        scene.frame_set(frame)
        bpy.context.view_layer.update()

    def snapshot(action, frame):
        hold(action, frame)
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

    # =========================================================== ① 接缝
    idle0 = snapshot("Idle_01", 0)
    for upstream in ("Victory_02", "Victory_01"):
        up = snapshot(upstream, 120)
        worst_pos, worst_dir, worst_at = 0.0, 0.0, None
        for n in BONES:
            if n in idle0 and n in up:
                pos, deg = mat_delta(idle0[n], up[n])
                if pos > worst_pos or deg > worst_dir:
                    worst_at = n
                worst_pos = max(worst_pos, pos)
                worst_dir = max(worst_dir, deg)
        print("E08_BASE_SEAM " + json.dumps({
            "pair": "%s@120 vs Idle_01@0" % upstream,
            "pos_max_mm": round(worst_pos, 6),
            "dir_max_deg": round(worst_dir, 6),
            "at": worst_at,
            "verdict": ("逐位一致（浮点噪声级）⟹ E08 起点取 Idle_01@0 可连播"
                        if worst_pos < 0.01 and worst_dir < 0.05
                        else "有差异，需裁决"),
        }, ensure_ascii=False))

    # =========================================================== ①b 站架实测
    hold("Idle_01", 0)
    station = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    wrist = {s: Vector(A.bone_world(arm, "hand." + s, "head")) for s in SIDES}
    shoulder = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                for s in SIDES}
    arm_len = {s: {"up": arm.pose.bones["upperarm." + s].length,
                   "fo": arm.pose.bones["forearm." + s].length,
                   "ha": arm.pose.bones["hand." + s].length} for s in SIDES}
    box = {s: hand_mesh_box(s) for s in SIDES}
    st_gap, st_who = hand_vs_hand_gap()
    print("E08_BASE_STATION " + json.dumps({
        "fist_core_mm": {s: [round(v * 1000.0, 1) for v in station[s]]
                         for s in SIDES},
        "wrist_mm": {s: [round(v * 1000.0, 1) for v in wrist[s]]
                     for s in SIDES},
        "shoulder_mm": {s: [round(v * 1000.0, 1) for v in shoulder[s]]
                        for s in SIDES},
        "arm_len_mm": {s: {k: round(v * 1000.0, 1)
                           for k, v in arm_len[s].items()} for s in SIDES},
        "hand_box_mm": {s: {"lo": [round(v * 1000.0, 1) for v in box[s][0]],
                            "hi": [round(v * 1000.0, 1) for v in box[s][1]],
                            "size": [round((box[s][1][i] - box[s][0][i]) * 1000.0,
                                           1) for i in range(3)]}
                        for s in SIDES},
        "station_fist_x_gap_mm": round(
            (station["L"].x - station["R"].x) * 1000.0, 1),
        "station_mesh_gap_mm": st_gap,
        "station_mesh_gap_who": st_who,
    }, ensure_ascii=False))

    # =========================================================== ② 第一拍实测
    beat = {}
    for action, frames in (("Victory_01", (0, 8, 14, 20)),
                           ("Victory_02", (0, 8, 14, 20))):
        rows = {}
        for frame in frames:
            hold(action, frame)
            rows[str(frame)] = {
                "fist_L_mm": [round(v * 1000.0, 1)
                              for v in A.bone_world(arm, "hand.L", "tail")],
                "fist_R_mm": [round(v * 1000.0, 1)
                              for v in A.bone_world(arm, "hand.R", "tail")],
                "pelvis_z_mm": round(
                    Vector(A.bone_world(arm, "pelvis", "head")).z * 1000.0, 2),
            }
        beat[action] = rows
    print("E08_BASE_FIRSTBEAT " + json.dumps(beat, ensure_ascii=False))

    # =========================================================== ③ 擦拳套贴合扫描
    base = V2.victory_pose(arm, 0)
    normals = {s: Vector((0.0, -1.0, 0.0)) for s in SIDES}

    def solve(x_half, y, z, dz_l=0.0, dz_r=0.0):
        """把两拳摆到 (±x_half, y, z+dz_*) 上，返回 (cores, gap, who, reach)。"""
        targets = {"L": Vector((+x_half, y, z + dz_l)),
                   "R": Vector((-x_half, y, z + dz_r))}
        pose = dict(base)
        V2.LAST_ELBOW = {}
        V2.LAST_TWIST_ANGLE = {}
        V2.LAST_BULGE = {}
        V2.LAST_BLENDED = {}
        V2.LAST_HAND_Q = {}
        V2.LAST_HAND_X = dict(V2.STATION_HAND_X)
        V2.MIN_HINT_MARGIN = 1.0
        V2.seat_arm(arm, pose, targets, normals, blend=0.0, env=1.0)
        A.apply_pose(arm, pose)
        cores = {s: Vector(A.bone_world(arm, "hand." + s, "tail"))
                 for s in SIDES}
        gap, who = hand_vs_hand_gap(step=2)
        reach = max((cores[s] - shoulder[s]).length
                    / ((arm_len[s]["up"] + arm_len[s]["fo"] + arm_len[s]["ha"])
                       * 0.995) for s in SIDES)
        return cores, gap, who, reach, V2.MIN_HINT_MARGIN

    scan = {}
    for x_half in (0.030, 0.045, 0.060, 0.075, 0.090, 0.105, 0.120):
        for z in (1.300,):
            for y in (-0.260,):
                cores, gap, who, reach, hint = solve(x_half, y, z)
                scan["x%.0f_z%.2f_y%.2f" % (x_half * 1000, z, y)] = {
                    "gap_mm": gap, "who": who,
                    "core_L_mm": [round(v * 1000.0, 1) for v in cores["L"]],
                    "core_R_mm": [round(v * 1000.0, 1) for v in cores["R"]],
                    "reach": round(reach, 4), "hint": round(hint, 4),
                    "dL_from_station_mm": round(
                        (cores["L"] - station["L"]).length * 1000.0, 1),
                    "dR_from_station_mm": round(
                        (cores["R"] - station["R"]).length * 1000.0, 1),
                }
    print("E08_BASE_CLASP_X " + json.dumps(scan, ensure_ascii=False))

    # 高度 / 前后微调（用上一步最佳 x 附近）
    scan2 = {}
    for x_half in (0.045, 0.060, 0.075):
        for z in (1.240, 1.280, 1.320):
            for y in (-0.300, -0.260, -0.220):
                cores, gap, who, reach, hint = solve(x_half, y, z)
                scan2["x%.0f_z%.2f_y%.2f" % (x_half * 1000, z, y)] = {
                    "gap_mm": gap, "reach": round(reach, 4),
                    "dL_mm": round((cores["L"] - station["L"]).length * 1000.0, 1),
                    "dR_mm": round((cores["R"] - station["R"]).length * 1000.0, 1),
                    "core_L_z_mm": round(cores["L"].z * 1000.0, 1),
                    "core_R_z_mm": round(cores["R"].z * 1000.0, 1),
                }
    print("E08_BASE_CLASP_XZ " + json.dumps(scan2, ensure_ascii=False))

    # 单侧上/下擦（验证滑动时 gap 是否稳定）
    slide = {}
    for dz_l, dz_r in ((0.0, 0.0), (-0.032, 0.032), (0.032, -0.032)):
        cores, gap, who, reach, hint = solve(0.060, -0.260, 1.300,
                                             dz_l=dz_l, dz_r=dz_r)
        slide["dzL%+.3f_dzR%+.3f" % (dz_l, dz_r)] = {
            "gap_mm": gap, "core_L_mm": [round(v * 1000.0, 1)
                                         for v in cores["L"]],
            "core_R_mm": [round(v * 1000.0, 1) for v in cores["R"]],
            "dL_mm": round((cores["L"] - station["L"]).length * 1000.0, 1),
            "dR_mm": round((cores["R"] - station["R"]).length * 1000.0, 1),
        }
    print("E08_BASE_SLIDE " + json.dumps(slide, ensure_ascii=False))

    # =========================================================== ④ 英雄姿体侧可达
    side_t = {}
    for x_half, z in ((0.300, 1.150), (0.320, 1.100), (0.280, 1.200)):
        cores, gap, who, reach, hint = solve(x_half, -0.050, z)
        side_t["x%.0f_z%.2f" % (x_half * 1000, z)] = {
            "reach": round(reach, 4), "hint": round(hint, 4),
            "core_L_mm": [round(v * 1000.0, 1) for v in cores["L"]],
            "gap_mm": gap,
        }
    print("E08_BASE_HEROSIDE " + json.dumps(side_t, ensure_ascii=False))

    print("E08_BASE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E08_BASE_FAILURE " + traceback.format_exc())
