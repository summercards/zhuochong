"""probe_d01_guard —— 只量不做：为 D01 `Guard_Start` 举防 定标判据与真值。

清单「下一支详细制作计划 —— D01 `Guard_Start`」§4「开工顺序」第 3 条要求：

    建 `probe_d01_guard.py` —— 扫候选举防姿（双拳叠于脸前 / 双臂交叉挡胸 /
    前臂竖立成"门" / 一高一低 等 4~6 个）× 肘外展几档，量：
    **手是否在身前**、**覆盖的 z 区间**、**是否与头包围盒相交**、**左右对称差**、**接地**。
    **先量再定阈值。**

★ 本支与已完成的 37 支最大差异：**第一次做"防护姿态"**。A~C 族的臂一律挂在
  "肩部相对轨道"上（手在身侧/体前下方），**从未把双手摆到头胸前**。所以：
  ① 剪影指标（`aspect` / `fill_grid`）大概率失效（双手挡胸会把正视图填满）；
  ② 双肘夹紧 + 手举高是 **C14 已实测过的同一个万向节锁坑**（真实局部旋转平滑
     ≤27°/帧，欧拉却跳 90.53°/帧）⟹ 主脚本必须带滚转搜索版 `_set_euler_nearest`。

==================== 口径（全部以 Idle_01@0 为参照）

  · **身前**：角色面向 −Y ⟹ 更负的 y = 更靠前。参照 = `chest` 骨 head 的世界 y。
  · **覆盖 z 区间**：拳（`hand.X` tail）的世界 z；目标带 = [胸高, 头顶 + 100 mm]。
  · **头包围盒**：**求解后网格**的 `Head` + `Hair_Mass` + `Hair_Sweep` + `Nose`
    四件（随姿态求值，不是静态数）⟹ 躯干一低头，盒跟着动。
  · **穿模**：沿 `upperarm/forearm/hand` 骨段等距取 9 点，点到头盒的**外距**
    < `ARM_R`（臂的等效半径）即判"插进去"，取最大穿透量。
  · **对称差**：左右拳的 |x| 差、z 差、y 差（本支是全项目**第一支对称双臂姿**）。
  · **接地**：`foot_lowest_by_side` 的鞋底最低点。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_d01_guard.py
    D01_RENDER=1  额外把前 4 名渲成「侧视 + 正视」静帧到 previews/anim/_d01_cand/
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A              # noqa: E402
import anim_idle_01 as I1         # noqa: E402
import probe_c12_baseline as P    # noqa: E402

SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")
HEAD_MESHES = ("Head", "Hair_Mass", "Hair_Sweep", "Nose")
ARM_R = 0.042                      # 臂骨等效半径（拳/前臂/袖子的可见粗细）
ARM_LEN = {}
FIST0 = {}
HEAD0 = None


# ---------------------------------------------------------------- 头盒
def head_box():
    """当前姿态下头部可见体的世界包围盒（求值后网格）。"""
    deps = bpy.context.evaluated_depsgraph_get()
    lo = [1e9] * 3
    hi = [-1e9] * 3
    for name in HEAD_MESHES:
        obj = bpy.data.objects.get(name)
        if obj is None:
            continue
        evaluated = obj.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        for vertex in mesh.vertices:
            point = matrix @ vertex.co
            for axis in range(3):
                lo[axis] = min(lo[axis], point[axis])
                hi[axis] = max(hi[axis], point[axis])
        evaluated.to_mesh_clear()
    return Vector(lo), Vector(hi)


def _outside_distance(point, lo, hi):
    """点到盒的**外距**（盒内为 0）。"""
    total = 0.0
    for axis in range(3):
        over = max(lo[axis] - point[axis], point[axis] - hi[axis], 0.0)
        total += over * over
    return math.sqrt(total)


def clip_metrics(arm):
    """臂骨段到头盒的最大"插入深度"（>0 = 穿模）。"""
    lo, hi = head_box()
    worst = 0.0
    worst_at = None
    for name in ARM_BONES:
        head = Vector(A.bone_world(arm, name, "head"))
        tail = Vector(A.bone_world(arm, name, "tail"))
        for index in range(9):
            point = head.lerp(tail, index / 8.0)
            penetration = ARM_R - _outside_distance(point, lo, hi)
            if penetration > worst:
                worst, worst_at = penetration, [name, index]
    return {
        "head_box_mm": [[round(v * 1000.0, 1) for v in lo],
                        [round(v * 1000.0, 1) for v in hi]],
        "clip_max_mm": round(worst * 1000.0, 2),
        "clip_at": worst_at,
    }


# ---------------------------------------------------------------- 装臂
def apply_pos(spec):
    """位置逆解装臂（同主脚本 `arm_seat` 口径）：`fist` 世界坐标 + `elbow` 鼓出方向。"""
    pose, _ = P.build(spec)
    A.apply_pose(P.A_RIG, pose)
    for side in SIDES:
        pose["foot." + side] = A.keep_world_orientation(P.A_RIG, "foot." + side)
    clamps = {}
    for side in SIDES:
        up, fo, hd = ("upperarm." + side, "forearm." + side, "hand." + side)
        l1 = ARM_LEN[side]["upper"]
        l23 = ARM_LEN[side]["forearm"] + ARM_LEN[side]["hand"]
        shoulder = Vector(A.bone_world(P.A_RIG, up, "head"))
        target = Vector(spec["fist"][side])
        delta = target - shoulder
        limit = (l1 + l23) * 0.9995
        clamps[side] = delta.length / limit
        distance = max(1e-4, min(delta.length, limit))
        axis = (delta.normalized() if delta.length > 1e-9
                else Vector((0.0, 0.0, -1.0)))
        bulge = Vector(spec["elbow"][side]) - axis * Vector(
            spec["elbow"][side]).dot(axis)
        if bulge.length < 1e-6:
            bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
        bulge.normalize()
        cos_sh = max(-1.0, min(1.0, (l1 * l1 + distance * distance - l23 * l23)
                               / (2.0 * l1 * distance)))
        sin_sh = math.sqrt(max(0.0, 1.0 - cos_sh * cos_sh))
        elbow = shoulder + (axis * cos_sh + bulge * sin_sh) * l1
        for name, direction in ((up, elbow - shoulder),
                                (fo, target - elbow),
                                (hd, target - elbow)):
            pose[name] = A.aim_bone(P.A_RIG, name, direction)
    bpy.context.view_layer.update()
    return pose, clamps


def measure(arm, spec, label):
    _pose, clamps = apply_pos(spec)
    low = A.foot_lowest_by_side()
    torso_y = A.bone_world(arm, "chest", "head").y
    chest_z = A.bone_world(arm, "chest", "head").z
    chest_top_z = A.bone_world(arm, "neck", "head").z      # = chest.tail 胸顶
    head_top_z = A.bone_world(arm, "head", "tail").z
    row = {
        "label": label,
        "_family": spec.get("_family"),
        "drop_mm": round(spec["drop"] * 1000.0, 1),
        "pelvis_z_mm": round(A.bone_world(arm, "pelvis", "head").z * 1000.0, 1),
        "torso_front_y_mm": round(torso_y * 1000.0, 1),
        "chest_z_mm": round(chest_z * 1000.0, 1),
        "chest_top_z_mm": round(chest_top_z * 1000.0, 1),
        "head_top_z_mm": round(head_top_z * 1000.0, 1),
        "sole_mm": {s: (None if low[s] is None else round(low[s][2] * 1000.0, 2))
                    for s in SIDES},
        "clamp_ratio": {s: round(v, 5) for s, v in clamps.items()},
        "clamp_ok": bool(max(clamps.values()) <= 1.0),
        "fist_mm": {}, "shoulder_mm": {}, "elbow_dir": {},
    }
    fist = {}
    elbow_out = []
    elbow_z = []
    for side in SIDES:
        fist[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
        shoulder = Vector(A.bone_world(arm, "upperarm." + side, "head"))
        elbow_tail = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
        row["fist_mm"][side] = [round(v * 1000.0, 1) for v in fist[side]]
        row["shoulder_mm"][side] = [round(v * 1000.0, 1) for v in shoulder]
        row["elbow_dir"][side] = [round(v, 4)
                                  for v in (elbow_tail - shoulder).normalized()]
        # 肘外张 / 肘高：肘尖的 |x| 比肩宽出多少；肘尖的 z（越低 = 肘越收）
        elbow_out.append((abs(elbow_tail.x) - abs(shoulder.x)) * 1000.0)
        elbow_z.append(elbow_tail.z * 1000.0)
    row["elbow_out_mm"] = [round(v, 1) for v in elbow_out]
    row["elbow_z_mm"] = [round(v, 1) for v in elbow_z]
    row["elbow_in_ok"] = bool(all(v <= 20.0 for v in elbow_out))
    row["elbow_below_ok"] = bool(
        all(z <= A.bone_world(arm, "chest", "head").z * 1000.0
            for z in elbow_z))
    # 身前 / 高度窗 / 举起量
    in_front = [round((torso_y - fist[s].y) * 1000.0, 1) for s in SIDES]
    z_mm = [round(fist[s].z * 1000.0, 1) for s in SIDES]
    raise_mm = [round((fist[s].z - FIST0[s].z) * 1000.0, 1) for s in SIDES]
    row["in_front_mm"] = in_front
    row["fist_z_mm"] = z_mm
    row["raise_mm"] = raise_mm
    # ★ `cover` 三段（第 2 轮收紧：F1 只护胸时 raise 只有 78.9 mm，与 80 的边界太脆）：
    #     (a) 在身前 ≥ 150 mm；(b) z ∈ [胸顶, 头顶+100]（胸顶 = neck.head = 锁骨上缘）；
    #     (c) |x| ≤ 200 mm（挡在身**前**，不是张开手臂）。
    #   再加"相对 Idle 举起 ≥ 80 mm"作为"举"的分量。
    row["cover_lo_mm"] = round(chest_top_z * 1000.0, 1)
    row["cover_hi_mm"] = round(head_top_z * 1000.0 + 100.0, 1)
    row["in_front_ok"] = bool(all(v >= 150.0 for v in in_front))
    row["z_window_ok"] = bool(
        all(chest_top_z * 1000.0 <= z <= head_top_z * 1000.0 + 100.0
            for z in z_mm))
    row["lateral_ok"] = bool(
        all(abs(fist[s].x) * 1000.0 <= 200.0 for s in SIDES))
    row["raise_ok"] = bool(all(r >= 80.0 for r in raise_mm))
    row["cover_ok"] = bool(row["z_window_ok"] and row["raise_ok"]
                           and row["in_front_ok"] and row["lateral_ok"])
    # 对称
    dx = abs(abs(fist["L"].x) - abs(fist["R"].x)) * 1000.0
    dz = abs(fist["L"].z - fist["R"].z) * 1000.0
    dy = abs(fist["L"].y - fist["R"].y) * 1000.0
    row["sym_dx_mm"], row["sym_dz_mm"], row["sym_dy_mm"] = (
        round(dx, 2), round(dz, 2), round(dy, 2))
    row["symmetry_ok"] = bool(max(dx, dz, dy) <= 25.0)
    # 穿模
    row.update(clip_metrics(arm))
    row["no_clip_ok"] = bool(row["clip_max_mm"] <= 0.0)
    # 剪影（大概率失效，只报不用）
    sil = P.silhouette(arm, label)
    row["aspect"] = sil["aspect"]
    row["fill_grid"] = sil["fill_grid"]
    row["width_m"] = sil["width_m"]
    row["height_m"] = sil["height_m"]
    row["com_inside_support"] = sil["com_inside_support"]
    return row


# ---------------------------------------------------------------- 候选举防姿
GUARD_TORSO = {"pelvis": (5.0, 0.0, 0.0),
               "spine_01": (2.0, 0.0, 0.0), "spine_02": (2.0, 0.0, 0.0),
               "chest": (6.0, 0.0, 0.0), "neck": (-8.0, 0.0, 0.0),
               "head": (6.0, 0.0, 0.0),
               "shoulder.L": (8.0, 0.0, 0.0), "shoulder.R": (8.0, 0.0, 0.0)}
GUARD_DROP = -0.080


def spec(family, drop, fist_l, fist_r, elbow_l, elbow_r, **torso):
    base = dict(GUARD_TORSO)
    base.update(torso)
    return {"_family": family, "drop": drop, "tilt": base["pelvis"][0],
            "abduct": I1.ABDUCT_DEG,
            "ankle": (I1.FRONT_ANKLE_Y, I1.BACK_ANKLE_Y),
            "torso": base,
            "fist": {"L": fist_l, "R": fist_r},
            "elbow": {"L": elbow_l, "R": elbow_r}}


def mirror(vec):
    return (-vec[0], vec[1], vec[2])


def build_candidates():
    out = {}

    # ★ 全部坐标单位 = **米**（世界）；拳 = `hand.X` tail，肘 = 鼓出方向单位向量。

    # ---- 第 2 轮结论（★ 决定了本支最终位姿）------------------------------------
    # 第 1 轮 16 个候选**全部**在正视里读成"投降 / 抱头"而不是"举防"。原因不在拳，
    # 在**肘**：所有族的 `elbow_dir` 都带 0.4~0.65 的 X 分量 ⟹ **肘向体侧外张**
    # （肘尖离肩比肩自身更外 100+ mm），前臂从外上方插向面前。剪影读起来就是"举手"。
    # 真正的举防（拳击 standard guard）是 **肘尖朝下、前臂竖直、拳在面前**。
    # ⟹ 第 2 轮把 `elbow_dir` 改成朝下型，并**新立一条可失败判据** `elbow_in_ok`
    #    （肘不得比肩更外），量 `elbow_out_mm = |elbow.x| − |shoulder.x|`。

    # G 族 `guard` —— ★ 主形：肘尖朝下、前臂竖直、双拳立在面前（拳距一个拳宽）
    for tag, fx, fy, fz, eb in (
            ("G1_070", 0.070, -0.250, 1.560, (0.14, 0.10, -0.985)),
            ("G2_100", 0.100, -0.250, 1.560, (0.14, 0.10, -0.985)),
            ("G3_100f", 0.100, -0.300, 1.560, (0.14, 0.10, -0.985)),
            ("G4_070f", 0.070, -0.300, 1.580, (0.08, 0.06, -0.995)),
            ("G5_tuck", 0.060, -0.240, 1.540, (-0.06, 0.12, -0.990)),
            ("G6_low", 0.100, -0.270, 1.500, (0.16, 0.06, -0.985)),
            ("G7_cheek", 0.110, -0.240, 1.610, (0.10, 0.14, -0.985)),
            ("G8_deep", 0.070, -0.230, 1.545, (0.02, 0.02, -0.999))):
        out[tag] = spec("guard", GUARD_DROP, (fx, fy, fz), (-fx, fy, fz),
                        eb, mirror(eb))

    # ---- 第 3 轮（★ 最终定稿族）----------------------------------------------
    # 第 2 轮把肘改成朝下后，`elbow_in_ok` 全过（−14 ~ −142 mm），但**正视仍读成
    # "捂脸/抱头"**：G 族的拳 x 只有 ±60~110，而脸半宽 85 ⟹ 双拳并拢在脸**正前**，
    # 前臂向内斜上方收拢。拳击护架的正解是**双拳分列脸两侧**（拳 x ≥ 140）。
    # 但拳 x 一拉大就撞到一个**硬几何限制**（本轮实测）：
    #   上臂 234 / 前臂+手 325 / 肩高 1345。要让拳升到 1560（肩上方 215），
    #   `拳距肩 ≥ 215`，而"肘朝下"能把肘压到的**极限 z ≈ 1141**（肩下 204），
    #   此时肘→拳竖直距离 ≥ 419 > 325 ⟹ **拳到不了 1560 而肘朝下**。
    #   ⟹ 定稿把拳降到 **下巴高度 1430~1510**（护住"胸 + 下巴 + 由前臂构成的正面墙"），
    #      肘夹在身前（比肩内收 ~80 mm）—— 这才是本角色骨架能做出的拳击护架。
    # 另：拳 y 必须**收回贴近下巴**（−0.21 ~ −0.24）。第 2 轮的 −0.30 把臂轴压得
    #   过平，"垂直向下"的鼓出方向会带出 −y 分量 ⟹ 肘被顶到 y ≈ −300（拳的前面），
    #   读成"肘朝前捅"。
    for tag, fx, fy, fz in (("H1_150_1470", 0.150, -0.225, 1.470),
                            ("H2_150_1430", 0.150, -0.225, 1.430),
                            ("H3_170_1470", 0.170, -0.225, 1.470),
                            ("H4_130_1470", 0.130, -0.225, 1.470),
                            ("H5_150_1510", 0.150, -0.230, 1.510),
                            ("H6_150_240", 0.150, -0.240, 1.470),
                            ("H7_170_1430", 0.170, -0.215, 1.430),
                            ("H8_160_1390", 0.160, -0.230, 1.390)):
        out[tag] = spec("boxer", GUARD_DROP, (fx, fy, fz), (-fx, fy, fz),
                        (-0.30, -0.10, -0.95), (0.30, -0.10, -0.95))

    # 对照 Gx —— 第 1 轮那套"肘外张"（用来证明 `elbow_in_ok` 抓得住）
    out["GX_wide_elbow"] = spec("wide_elbow", GUARD_DROP,
                                (0.130, -0.300, 1.560), (-0.130, -0.300, 1.560),
                                (0.55, 0.10, -0.83), (-0.55, 0.10, -0.83))
    # 对照 Gp —— 第 2 轮"捂脸型"（拳并拢在脸正前）
    out["GP_cover_face"] = spec("cover_face", GUARD_DROP,
                                (0.070, -0.250, 1.560), (-0.070, -0.250, 1.560),
                                (0.14, 0.10, -0.985), (-0.14, 0.10, -0.985))

    # A 族 `gate`（第 1 轮，肘外张）—— 保留作对照
    for tag, fx, fy, fz, eb in (
            ("A1_1520", 0.130, -0.300, 1.520, (0.55, 0.10, -0.83)),
            ("A4_tight", 0.110, -0.215, 1.580, (0.60, 0.00, -0.80))):
        out[tag] = spec("gate", GUARD_DROP, (fx, fy, fz), (-fx, fy, fz),
                        eb, mirror(eb))

    # B 族 `stack` —— 双拳并拢护住下巴与前胸（拳距最窄）
    for tag, fx, fy, fz, eb in (
            ("B1_1450", 0.085, -0.300, 1.450, (0.62, 0.10, -0.78)),
            ("B2_1520", 0.090, -0.280, 1.520, (0.62, 0.10, -0.78)),
            ("B3_1500c", 0.075, -0.240, 1.500, (0.65, 0.05, -0.76))):
        out[tag] = spec("stack", GUARD_DROP, (fx, fy, fz), (-fx, fy, fz),
                        eb, mirror(eb))

    # C 族 `cross` —— 双臂交叉挡胸（左拳去到右侧、右拳去到左侧）
    for tag, fx, fy, fz, eb in (
            ("C1_1420", -0.120, -0.300, 1.420, (0.85, 0.10, -0.52)),
            ("C2_1500", -0.140, -0.280, 1.500, (0.85, 0.10, -0.52))):
        out[tag] = spec("cross", GUARD_DROP, (fx, fy, fz), (-fx, fy, fz),
                        eb, mirror(eb))

    # D 族 `cheek` —— 高护颊：双拳护在脸颊外侧、肘夹紧
    for tag, fx, fy, fz, eb in (
            ("D1_1620", 0.165, -0.300, 1.620, (0.42, 0.20, -0.88)),
            ("D2_1650", 0.175, -0.270, 1.650, (0.40, 0.15, -0.90))):
        out[tag] = spec("cheek", GUARD_DROP, (fx, fy, fz), (-fx, fy, fz),
                        eb, mirror(eb))

    # E 族 `wall` —— 前臂近水平横挡（肘向外，拳向内）
    for tag, fx, fy, fz, eb in (
            ("E1_1480", 0.060, -0.290, 1.480, (0.90, 0.15, -0.40)),
            ("E2_1560", 0.070, -0.300, 1.560, (0.88, 0.15, -0.44))):
        out[tag] = spec("wall", GUARD_DROP, (fx, fy, fz), (-fx, fy, fz),
                        eb, mirror(eb))

    # 对照 F —— 只护胸（头裸露）
    out["F1_chest"] = spec("chest_only", GUARD_DROP, (0.140, -0.300, 1.350),
                           (-0.140, -0.300, 1.350), (0.60, 0.10, -0.78),
                           (-0.60, 0.10, -0.78))

    # 对照 G —— 双臂外张（不是举防）
    out["G1_open"] = spec("open_wide", GUARD_DROP, (0.330, -0.200, 1.500),
                          (-0.330, -0.200, 1.500), (0.90, 0.10, -0.40),
                          (-0.90, 0.10, -0.40))

    # 参照 H —— Idle 原姿（用同口径重解一遍，作为"什么都没做"的下界）
    out["H0_idle_like"] = spec(
        "idle_ref", I1.DROP, (0.1445, -0.3077, 1.2711), (-0.1296, -0.2735, 1.2982),
        (-0.9, 0.1, -0.42), (0.9, 0.1, -0.42),
        pelvis=(4.0, 0.0, 0.0), spine_01=(2.0, 0.0, 0.0),
        spine_02=(2.0, 0.0, 0.0), chest=(1.0, 0.0, 0.0),
        neck=(-6.0, 0.0, 0.0), head=(5.0, 0.0, 0.0),
        **{"shoulder.L": (-18.0, 0.0, 0.0), "shoulder.R": (-18.0, 0.0, 0.0)})
    return out


# ---------------------------------------------------------------- 渲染
def render_top(rows, arm, keys=None, n=4):
    by_label = {r["label"]: r for r in rows}
    if keys:
        order = [by_label[k] for k in keys if k in by_label]
    else:
        order = sorted(rows, key=lambda r: -(r["in_front_mm"][0]
                                             + r["raise_mm"][0]))[:n]
    out_dir = os.path.join(A.PREVIEW_DIR, "_d01_cand")
    os.makedirs(out_dir, exist_ok=True)
    camera = bpy.data.objects.get("Presentation_Camera")
    if camera is None:
        raise RuntimeError("展示相机不见了：Presentation_Camera")
    if arm.animation_data is not None:
        arm.animation_data.action = None
    made = []
    for index, row in enumerate(order):
        apply_pos(row["_spec"])
        views = [A.VIEW_SIDE, A.VIEW_FRONT]
        if os.environ.get("D01_RENDER_3Q"):
            views.append(A.VIEW_3Q)
        for view in views:
            path = os.path.join(out_dir, "%02d_%s_%s.png"
                                % (index, row["label"], view[0]))
            made.append(A.render_still(camera, path, view[1], view[2],
                                       view[3], view[4]))
    print("D01_PROBE_RENDER " + json.dumps(made, ensure_ascii=False))
    return made


def main():
    global HEAD0
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        print("D01_PROBE_BOOTSTRAP 缺 %s，先补跑" % I1.NAME)
        I1.main()
        arm, _meshes = A.open_animation_project()
        A.setup_scene()
    P.A_RIG = arm
    for side in SIDES:
        ARM_LEN[side] = {
            "upper": arm.pose.bones["upperarm." + side].length,
            "forearm": arm.pose.bones["forearm." + side].length,
            "hand": arm.pose.bones["hand." + side].length}

    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    A.reset_pose(arm)
    bpy.context.scene.frame_set(0)
    bpy.context.view_layer.update()

    # 基线：Idle_01@0 真值
    for side in SIDES:
        FIST0[side] = Vector(A.bone_world(arm, "hand." + side, "tail"))
    lo, hi = head_box()
    HEAD0 = {"lo_mm": [round(v * 1000.0, 1) for v in lo],
             "hi_mm": [round(v * 1000.0, 1) for v in hi]}
    base_sil = P.silhouette(arm, "Idle_01@0")
    print("D01_PROBE_BASE " + json.dumps({
        "head_box_mm": HEAD0,
        "fist_mm": {s: [round(v * 1000.0, 1) for v in FIST0[s]] for s in SIDES},
        "torso_front_y_mm": round(A.bone_world(arm, "chest", "head").y * 1000.0, 1),
        "chest_z_mm": round(A.bone_world(arm, "chest", "head").z * 1000.0, 1),
        "head_top_z_mm": round(A.bone_world(arm, "head", "tail").z * 1000.0, 1),
        "pelvis_z_mm": round(A.bone_world(arm, "pelvis", "head").z * 1000.0, 1),
        "aspect": base_sil["aspect"], "fill_grid": base_sil["fill_grid"],
        "shoulder_width_m": base_sil["shoulder_width_m"],
    }, ensure_ascii=False))

    cands = build_candidates()
    rows = []
    for key in sorted(cands):
        row = measure(arm, cands[key], key)
        row["_spec"] = cands[key]
        rows.append(row)
        print("D01_PROBE " + json.dumps({
            "key": key, "family": row["_family"],
            "fist_L": row["fist_mm"]["L"], "fist_R": row["fist_mm"]["R"],
            "in_front": row["in_front_mm"], "raise": row["raise_mm"],
            "z": row["fist_z_mm"],
            "cover_ok": row["cover_ok"], "raise_ok": row["raise_ok"],
            "in_front_ok": row["in_front_ok"],
            "z_window_ok": row["z_window_ok"],
            "lateral_ok": row["lateral_ok"],
            "cover_lo_mm": row["cover_lo_mm"],
            "cover_hi_mm": row["cover_hi_mm"],
            "clip_mm": row["clip_max_mm"], "clip_at": row["clip_at"],
            "no_clip_ok": row["no_clip_ok"],
            "sym": [row["sym_dx_mm"], row["sym_dz_mm"], row["sym_dy_mm"]],
            "symmetry_ok": row["symmetry_ok"],
            "sole": row["sole_mm"], "clamp_ok": row["clamp_ok"],
            "com_in": row["com_inside_support"],
            "elbow_out": row["elbow_out_mm"], "elbow_z": row["elbow_z_mm"],
            "elbow_in_ok": row["elbow_in_ok"],
            "aspect": row["aspect"], "fill_grid": row["fill_grid"],
        }, ensure_ascii=False))

    passed = [r for r in rows
              if r["cover_ok"] and r["no_clip_ok"] and r["symmetry_ok"]
              and r["clamp_ok"] and r["elbow_in_ok"]]
    dump = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "_d01_probe_rows.json")
    with open(dump, "w", encoding="utf-8") as handle:
        json.dump([{k: v for k, v in r.items() if k != "_spec"} for r in rows],
                  handle, ensure_ascii=False, indent=1)
    for row in rows:
        print("D01_ROW " + json.dumps({
            "key": row["label"], "family": row["_family"],
            "fist_L": row["fist_mm"]["L"], "fist_R": row["fist_mm"]["R"],
            "elbow_out": row["elbow_out_mm"], "elbow_z": row["elbow_z_mm"],
            "in_front": row["in_front_mm"], "raise": row["raise_mm"],
            "clip": row["clip_max_mm"], "sym": [row["sym_dx_mm"],
                                                row["sym_dz_mm"],
                                                row["sym_dy_mm"]],
            "sole": row["sole_mm"],
            "ok": [row["cover_ok"], row["no_clip_ok"], row["symmetry_ok"],
                   row["clamp_ok"], row["elbow_in_ok"], row["elbow_below_ok"]],
        }, ensure_ascii=False))
    passed.sort(key=lambda r: -min(min(r["raise_mm"]), min(r["in_front_mm"])))
    print("D01_PROBE_PASS " + json.dumps(
        [[r["label"], r["_family"], r["fist_mm"]["L"], r["raise_mm"],
          r["in_front_mm"], r["clip_max_mm"], r["elbow_out_mm"], r["sole_mm"]]
         for r in passed], ensure_ascii=False))

    if passed:
        best = passed[0]
        print("D01_PROBE_WINNER " + json.dumps({
            "label": best["label"], "family": best["_family"],
            "drop_mm": best["drop_mm"], "torso": best["_spec"]["torso"],
            "fist_mm": best["fist_mm"], "elbow_dir": best["elbow_dir"],
            "shoulder_mm": best["shoulder_mm"],
            "in_front_mm": best["in_front_mm"], "raise_mm": best["raise_mm"],
            "clip_max_mm": best["clip_max_mm"],
            "sym": [best["sym_dx_mm"], best["sym_dz_mm"], best["sym_dy_mm"]],
            "sole_mm": best["sole_mm"], "pelvis_z_mm": best["pelvis_z_mm"],
        }, ensure_ascii=False))

    if os.environ.get("D01_RENDER"):
        keys = os.environ.get("D01_RENDER_KEYS")
        render_top(rows, arm,
                   keys=[k for k in keys.split(",") if k] if keys else None,
                   n=int(os.environ.get("D01_RENDER_N", "4")))

    print("D01_PROBE_DONE n=%d pass=%d" % (len(rows), len(passed)))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("D01_PROBE_FAILURE " + traceback.format_exc())
