"""probe_heavy02 —— B05 `Heavy_02` 重击 **只读**探针（定盘数）。

清单「下一支计划 —— B05」的 ★ 三件事在这里落地：
  1. **先选"哪种重击"（双手锤击 / 肘击 / 肩撞）** —— 用数据定，不靠猜：
     对每个候选算「命中点世界位置 / 前伸量 / 伸展率 / 几何风险」。
  2. **双手过顶的 `|Y|` 双高 + 两肘 `|pole⊥axis|`**：
     B03 已证「|Y|>45° 换族」在大幅度动作上失效 ⟹ `|Y|` 只报数，判据交 `no_teleport`。
     但 pole 必须实测：低于 0.30 就走 `_elbow_bulge` 接力（**不许硬阈值**，B04 第 3 件事）。
  3. **锤击命中点高度**：`hit_reach` 的 z 必须**明显低于** B04 的 1117.7 mm
     （打腰以下）。压不下去就把 `O_STRIKE` 的 z 分量给负值 −0.30~−0.45。

本探针**只读**：只摆姿态、只测量，不建 Action、不存盘、不导 GLB。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_heavy02.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402

ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")
SIDES = ("L", "R")

# B04 的基准（"锤击必须打得更低、幅度不能更小"）
B04_HIT_REACH_MM = 723.1      # 拳峰前伸（= 胸骨顶 y − 拳峰 y）
B04_HIT_Z_MM = 1117.7         # 命中帧拳峰 z
B04_TRAVEL_MM = 788.8         # 拳峰世界行程
B04_SWEEP_DEG = 214.06        # 以肩为轴的累计扫掠角
B04_SEGMENT_RANGES = {"foot": 20.278, "leg": 16.065, "hip": 23.168,
                      "waist": 23.168, "shoulder": 31.218, "hand": 136.4}
GUARD_FIST_Z_MM = 1271.0      # 护体架势拳峰 z（raise_window_ok 的基准，探针复核）


def mm(v):
    return [round(x * 1000.0, 1) for x in v]


def _pole_from_pose(arm, side):
    """实测「肘的鼓出方向」= (肘−肩) 去掉沿 肩→腕 轴分量后的单位垂足。

    与 `anim_heavy_01._pole_from_pose` 同一口径：**必须从 idle 实测**，
    否则 f0（= idle）到 f1（IK 解）会翻肘（B04 文件头第 2(a) 件）。
    """
    up = Vector(A.bone_world(arm, "upperarm." + side, "head"))
    elbow = Vector(A.bone_world(arm, "upperarm." + side, "tail"))
    wrist = Vector(A.bone_world(arm, "forearm." + side, "tail"))
    delta = wrist - up
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    bulge = (elbow - up) - axis * (elbow - up).dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, -1.0)) - axis * axis.z
    return bulge.normalized()


def _bone_len(arm, name):
    return (Vector(A.bone_world(arm, name, "tail"))
            - Vector(A.bone_world(arm, name, "head"))).length


def _pullback(shoulder, wrist_target, pole, len_up, len_fore):
    """纯几何预报：给定肩→腕目标，返回 (伸展率, 肘内角°, |pole⊥axis|, 是否可达)。

    `|pole⊥axis|` 是**本支的决策量**：轴与 pole 近乎共线时鼓出方向由噪声决定
    （B04 蓄力到位时只有 sin 8.7° = 0.151）⟹ 肘会单帧甩几十度。
    """
    delta = Vector(wrist_target) - Vector(shoulder)
    raw = delta.length
    limit = (len_up + len_fore) * 0.9995
    axis = delta.normalized() if delta.length > 1e-9 else Vector((0.0, -1.0, 0.0))
    distance = max(1e-4, min(raw, limit))
    cos_hip = (len_up ** 2 + distance ** 2 - len_fore ** 2) / (2.0 * len_up * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    elbow_inner = math.degrees(math.acos(cos_hip))
    pole_v = Vector(pole)
    bulge = pole_v - axis * pole_v.dot(axis)
    return (raw / (len_up + len_fore), elbow_inner, bulge.length,
            bool(raw <= limit))


def _apply_two_bone(arm, side, fist_target, hand_dir, pole):
    """把一侧手臂摆到「拳峰落到 `fist_target`、手骨指向 `hand_dir`」，读回 |Y|。

    与 `anim_heavy_01.arm_to` 同几何（叉积平面内的二骨解），只是用裸 `A.aim_bone`
    —— 探针只测**单个姿态**的几何，不需要欧拉接力的连续性。
    """
    upper, fore, handb = ("upperarm." + side, "forearm." + side, "hand." + side)
    len_up, len_fore = _bone_len(arm, upper), _bone_len(arm, fore)
    len_hand = _bone_len(arm, handb)
    direction = Vector(hand_dir).normalized()
    wrist_target = Vector(fist_target) - direction * len_hand
    shoulder = Vector(A.bone_world(arm, upper, "head"))
    delta = wrist_target - shoulder
    limit = (len_up + len_fore) * 0.9995
    distance = max(1e-4, min(delta.length, limit))
    axis = (delta.normalized() if delta.length > 1e-9
            else Vector((0.0, -1.0, 0.0)))
    pole_v = Vector(pole)
    bulge = pole_v - axis * pole_v.dot(axis)
    if bulge.length < 1e-6:
        bulge = Vector((0.0, 0.0, 1.0)) - axis * axis.z
    bulge.normalize()
    cos_hip = (len_up ** 2 + distance ** 2 - len_fore ** 2) / (2.0 * len_up * distance)
    cos_hip = max(-1.0, min(1.0, cos_hip))
    sin_hip = math.sqrt(max(0.0, 1.0 - cos_hip * cos_hip))
    elbow = shoulder + (axis * cos_hip + bulge * sin_hip) * len_up
    e_up = A.aim_bone(arm, upper, elbow - shoulder)
    e_fo = A.aim_bone(arm, fore, wrist_target - elbow)
    e_ha = A.aim_bone(arm, handb, direction)
    return {"euler": {upper: e_up, fore: e_fo, handb: e_ha},
            "max_abs_y": max(abs(e_up[1]), abs(e_fo[1]), abs(e_ha[1])),
            "extension": delta.length / (len_up + len_fore),
            "elbow_inner_deg": math.degrees(math.acos(cos_hip)),
            "elbow_world_mm": mm(elbow),
            "wrist_world_mm": mm(wrist_target)}


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)

    SHO = {s: Vector(A.bone_world(arm, "upperarm." + s, "head")) for s in SIDES}
    ELB = {s: Vector(A.bone_world(arm, "upperarm." + s, "tail")) for s in SIDES}
    WRI = {s: Vector(A.bone_world(arm, "hand." + s, "head")) for s in SIDES}
    FIS = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    ANK = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}
    HIP = {s: Vector(A.bone_world(arm, "thigh." + s, "head")) for s in SIDES}
    STERNUM = Vector(A.bone_world(arm, "neck", "head"))
    POLE = {s: _pole_from_pose(arm, s) for s in SIDES}
    LEN = {name: _bone_len(arm, name) for name in ARM6}
    ARM_REACH = {s: LEN["upperarm." + s] + LEN["forearm." + s] + LEN["hand." + s]
                 for s in SIDES}

    front = "L" if ANK["L"].y < ANK["R"].y else "R"

    A.report("H02_IDENTITY", {
        "front_foot": front,
        "ankle_mm": {s: mm(ANK[s]) for s in SIDES},
        "hip_mm": {s: mm(HIP[s]) for s in SIDES},
        "shoulder_mm": {s: mm(SHO[s]) for s in SIDES},
        "elbow_mm": {s: mm(ELB[s]) for s in SIDES},
        "wrist_mm": {s: mm(WRI[s]) for s in SIDES},
        "fist_mm": {s: mm(FIS[s]) for s in SIDES},
        "sternum_mm": mm(STERNUM),
        "arm_bone_len_mm": {k: round(v * 1000.0, 1) for k, v in LEN.items()},
        "arm_reach_mm": {s: round(ARM_REACH[s] * 1000.0, 1) for s in SIDES},
        "leg_reach_limit_mm": round((A.L_THIGH + A.L_SHIN) * 1000.0, 1),
        "leg_headroom_mm": {
            s: round((A.L_THIGH + A.L_SHIN - (ANK[s] - HIP[s]).length) * 1000.0, 1)
            for s in SIDES},
        "pole_mm": {s: mm(POLE[s]) for s in SIDES},
        "guard_fist_offset_from_shoulder_mm": {
            s: mm(FIS[s] - SHO[s]) for s in SIDES},
        "guard_fist_z_mm": {s: round(FIS[s].z * 1000.0, 1) for s in SIDES},
        "note": ("前脚 ⟹ 前手；双手锤击是**双臂合力**，手位不区分前后手，"
                 "但与 B04 单臂后手重拳形成「单臂/双臂」「打胸/打腰以下」互补"),
    })

    # ---------------------------------------------------------------- 候选 A：双手锤击
    # 过顶目标扫描：两拳在头顶上方，找"高度最高且不吃奇点"的一档。
    # 判据（探针口径，非门禁）：伸展率 ≤ 0.95、肘内角 ≥ 35°、|pole⊥axis| 报数。
    over_rows = []
    for z_mm in (1480, 1540, 1600, 1660, 1720, 1780):
        for y_off in (-0.02, -0.10):
            for pole_twist in (0.0,):
                fist = {s: SHO[s] + Vector(((-0.055 if s == "L" else 0.055)
                                            * (0.0), y_off, 0.0))
                        for s in SIDES}
                # 拳峰目标：肩正上方偏内，z 由扫描给出（绝对世界高度）
                fist = {s: Vector((SHO[s].x * 0.55, SHO[s].y + y_off,
                                   z_mm / 1000.0)) for s in SIDES}
                hand_dir = (0.0, -0.35, 0.94)   # 手骨指向上前（拳头朝上）
                row = {"z_mm": z_mm, "y_off": y_off, "pole_twist": pole_twist}
                for s in SIDES:
                    wrist = fist[s] - Vector(hand_dir).normalized() * LEN["hand." + s]
                    ext, inner, psin, ok = _pullback(
                        SHO[s], wrist, POLE[s],
                        LEN["upperarm." + s], LEN["forearm." + s])
                    row[s] = {"extension": round(ext, 4),
                              "elbow_inner_deg": round(inner, 2),
                              "pole_sin": round(psin, 4),
                              "reachable": ok}
                row["pair_ok"] = all(row[s]["reachable"]
                                     and row[s]["extension"] <= 0.95
                                     and row[s]["elbow_inner_deg"] >= 35.0
                                     for s in SIDES)
                over_rows.append(row)
    A.report("H02_HAMMER_OVERHEAD_SCAN", over_rows)

    # 命中目标扫描：两拳在身前下方（打腰以下）。
    strike_rows = []
    for z_mm in (760, 840, 920, 1000, 1080):
        for y_mm in (-360, -420, -480, -540):
            for x_mm in (100, 130, 160):
                row = {"z_mm": z_mm, "y_mm": y_mm, "x_mm": x_mm}
                row["survives_gate"] = True
                for s in SIDES:
                    fist = Vector((x_mm / 1000.0 * (1 if s == "L" else -1),
                                   y_mm / 1000.0, z_mm / 1000.0))
                    hand_dir = (0.0, -0.80, -0.60)   # 手骨朝前下（拳砸下去）
                    wrist = fist - Vector(hand_dir).normalized() * LEN["hand." + s]
                    ext, inner, psin, ok = _pullback(
                        SHO[s], wrist, POLE[s],
                        LEN["upperarm." + s], LEN["forearm." + s])
                    row[s] = {"extension": round(ext, 4),
                              "elbow_inner_deg": round(inner, 2),
                              "pole_sin": round(psin, 4),
                              "reachable": ok}
                    row["survives_gate"] = row["survives_gate"] and ok
                row["fist_z_below_b04_mm"] = round(z_mm - B04_HIT_Z_MM, 1)
                row["reach_mm"] = round((STERNUM.y - y_mm / 1000.0) * 1000.0, 1)
                row["pair_ok"] = all(row[s]["reachable"]
                                     and row[s]["extension"] <= 0.95
                                     for s in SIDES)
                strike_rows.append(row)
    A.report("H02_HAMMER_STRIKE_SCAN", strike_rows)

    # 选定档位实际摆出来读 |Y|（"双手过顶"最担心的就是双高 |Y|）。
    chosen_over = max((r for r in over_rows if r["pair_ok"]),
                      key=lambda r: r["z_mm"], default=None)
    chosen_strike = min((r for r in strike_rows if r["pair_ok"]),
                        key=lambda r: r["z_mm"], default=None)
    pose_rows = {}
    if chosen_over is not None:
        z_mm, y_off = chosen_over["z_mm"], chosen_over["y_off"]
        A.apply_pose(arm, idle)
        row = {"fist_target_z_mm": z_mm}
        for s in SIDES:
            fist = Vector((SHO[s].x * 0.55, SHO[s].y + y_off, z_mm / 1000.0))
            res = _apply_two_bone(arm, s, fist, (0.0, -0.35, 0.94), POLE[s])
            row[s] = {"max_abs_y_deg": round(res["max_abs_y"], 2),
                      "extension": round(res["extension"], 4),
                      "elbow_inner_deg": round(res["elbow_inner_deg"], 2),
                      "elbow_world_mm": res["elbow_world_mm"]}
            row[s]["euler_deg"] = {k: [round(v, 2) for v in e]
                                   for k, e in res["euler"].items()}
        pose_rows["overhead_posed"] = row
    if chosen_strike is not None:
        z_mm, y_mm, x_mm = (chosen_strike["z_mm"], chosen_strike["y_mm"],
                            chosen_strike["x_mm"])
        A.apply_pose(arm, idle)
        row = {"fist_target_mm": [x_mm, y_mm, z_mm],
               "fist_z_below_b04_mm": round(z_mm - B04_HIT_Z_MM, 1)}
        for s in SIDES:
            fist = Vector((x_mm / 1000.0 * (1 if s == "L" else -1),
                           y_mm / 1000.0, z_mm / 1000.0))
            res = _apply_two_bone(arm, s, fist, (0.0, -0.80, -0.60), POLE[s])
            row[s] = {"max_abs_y_deg": round(res["max_abs_y"], 2),
                      "extension": round(res["extension"], 4),
                      "elbow_inner_deg": round(res["elbow_inner_deg"], 2),
                      "elbow_world_mm": res["elbow_world_mm"]}
            row[s]["euler_deg"] = {k: [round(v, 2) for v in e]
                                   for k, e in res["euler"].items()}
        pose_rows["strike_posed"] = row
    A.report("H02_CHOSEN_POSES", pose_rows)

    # ---------------------------------------------------------------- 候选 B/C 对照
    # 候选 B「肘击」：命中点 = 肘尖（upperarm.tail）。量它从 idle 到"肘前顶"的可达前伸。
    elbow_rows = []
    for y_mm in (-200, -260, -320, -380):
        for z_mm in (1080, 1160, 1240):
            best = None
            for s in SIDES:
                # 肘尖目标 = 肩 + 偏移；腕反折到身体侧后（前臂回折）
                elbow_target = SHO[s] + Vector((0.0, y_mm / 1000.0,
                                                (z_mm - SHO[s].z * 1000.0) / 1000.0))
                wrist_target = Vector((SHO[s].x, SHO[s].y + 0.10,
                                       SHO[s].z - 0.22))
                ext, inner, psin, ok = _pullback(
                    SHO[s], wrist_target, POLE[s],
                    LEN["upperarm." + s], LEN["forearm." + s])
                reach = (STERNUM.y - elbow_target.y) * 1000.0
                if best is None or reach > best["elbow_reach_mm"]:
                    best = {"side": s, "elbow_reach_mm": round(reach, 1),
                            "elbow_z_mm": z_mm, "elbow_y_mm": y_mm,
                            "forearm_fold_inner_deg": round(inner, 2),
                            "pole_sin": round(psin, 4), "reachable": ok}
            elbow_rows.append(best)
    A.report("H02_CAND_B_ELBOW", elbow_rows)

    # 候选 C「肩撞」：命中点 = 肩峰（upperarm.head）。量它从 idle 到"侧身前顶"的可达前伸。
    shoulder_rows = []
    for y_mm in (-160, -220, -280):
        for rz_deg in (18, 26, 34):
            # 躯干侧倾 rz 把左肩（或右肩）推向前方；这里用一阶近似（绕髋的杠杆）
            lever = (SHO["L"].z - HIP["L"].z)
            fwd = -(math.radians(rz_deg)) * lever * 1000.0
            shoulder_rows.append({
                "side": "L", "y_drive_mm": y_mm, "torso_rz_deg": rz_deg,
                "shoulder_forward_mm": round(fwd + abs(y_mm) * 0.0, 1),
                "note": "肩撞≈B04 的跨步同轴（位移主导）⟹ 表现轴重复风险高",
            })
    A.report("H02_CAND_C_SHOULDER", shoulder_rows)

    # ---------------------------------------------------------------- 决策表
    A.report("H02_DECISION", {
        "b04_reference": {"hit_reach_mm": B04_HIT_REACH_MM,
                          "hit_z_mm": B04_HIT_Z_MM,
                          "travel_mm": B04_TRAVEL_MM,
                          "sweep_deg": B04_SWEEP_DEG,
                          "segment_ranges": B04_SEGMENT_RANGES},
        "guard_fist_z_mm": round(min(FIS["L"].z, FIS["R"].z) * 1000.0, 1),
        "guard_fist_z_reference_mm": GUARD_FIST_Z_MM,
        "overhead_best_z_mm": (chosen_over["z_mm"] if chosen_over else None),
        "strike_best_z_mm": (chosen_strike["z_mm"] if chosen_strike else None),
        "height_span_mm": ((chosen_over["z_mm"] - chosen_strike["z_mm"])
                           if (chosen_over and chosen_strike) else None),
        "rule_note": ("选「双手锤击」当且仅当：过顶档存在（伸展率≤0.95、肘内角≥35°、"
                      "pole 报数）、命中 z 明显低于 B04 的 1117.7、且高度落差 ≥450 mm。"
                      "肘击 = 前臂回折 ⟹ 肘尖朝向由 forearm 决定（又一个 pole 问题）；"
                      "肩撞 = 位移主导 ⟹ 与 B04 跨步同轴，表现轴重复。"),
    })
    print("PROBE_HEAVY02_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_HEAVY02_FAILURE " + traceback.format_exc())
