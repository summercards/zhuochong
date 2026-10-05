"""probe_light02 —— B02 `Light_02` 后手横拳 的开工探针（只读，不改工程）。

为什么非要先跑它（B01 交下来的三件必做，第 1 件）：
  ① 清单要求「开工第一步：量 `Idle_01@0` 双脚世界 Y 定前手」。B01 已实测前脚 = L
     ⟹ 前手 = L、**后手 = R = 本支的出拳手**。本探针重测一遍确认，不手抄。
  ② A13 定案 + B01 第 2 件要求「先量 strike 姿态的 `max_abs_euler_y_deg`，
     >45° 先换等价族再插值」。**横拳把上臂摆过身体中线**，|Y| 很可能显著大于
     B01 的 15.53°，必须在动手前量出来。
  ③ B01 第 3 件：`no_teleport ≤25°/帧` 的预算 = 「guard → strike 的逐分量欧拉差」。
     横拳行程比直拳长，**这个差就是本支真正的约束**，必须先量再定帧数。

顺带量（B02 新判据的可行性）：
  · 拳峰**横向 |ΔX| 增量**（`strike_reach_ok` 改用横向口径 ⟹ 先看能到多少）
  · 腕→肩 / 腕→胸骨的**半径变化**（`strike_arc_ok`，横拳走弧线）
  · 拳峰世界**全行程**（`heavier_than_b01_ok` 要比 B01 的 429.0 mm）
  · 候选 COIL（反向预备）姿态 —— 本支的前摇**真的能把拳往后拉**
    （B01 证过直拳里不可达），这决定 `hip_shoulder_sync_ok` 与视觉蓄力

用法：
    blender --background --factory-startup --python probe_light02.py
"""

import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_jump_start as JS  # noqa: E402

ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")
TRUNK8 = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
          "shoulder.L", "shoulder.R")

B01_PEAK_STEP_DEG = 23.185     # B01 `no_teleport` 峰值（本支 `heavier` 的比较基准）
B01_FIST_TRAVEL_MM = 429.0     # B01 拳峰行程（增量基准）
B01_HITSTOP_FRAMES = 2

# ---------------------------------------------------------------- 躯干姿态
# 出拳躯干（横拳）：**右肩驱动向前** ⟹ ry>0（ry>0 把角色 +X 侧转向 +Y 身后，
# 即左肩后、右肩前）。颈/头反向扭转保持看向正前方。
TRUNK_STRIKE = {
    "pelvis": (6.0, 10.0, 0.0),
    "spine_01": (3.0, 5.0, 0.0),
    "spine_02": (3.0, 5.0, 0.0),
    "chest": (3.0, 10.0, 0.0),
    "neck": (-8.0, -7.0, 0.0),
    "head": (5.0, -5.0, 0.0),
    "shoulder.L": (-17.0, 0.0, -7.0),    # 左肩被带向后（左臂 rz>0=向后，故 −7 是向前？
    "shoulder.R": (-6.0, 0.0, 14.0),     # 右肩向前（右臂 rz>0 = 向前）
}

# 前摇躯干（反向预备）：髋先反向转（ry<0 = 右肩后拉），右肩拉开。
TRUNK_COIL = {
    "pelvis": (5.0, -7.0, 0.0),
    "spine_01": (2.4, -3.5, 0.0),
    "spine_02": (2.4, -3.5, 0.0),
    "chest": (2.0, -7.0, 0.0),
    "neck": (-7.0, 3.5, 0.0),
    "head": (5.0, 2.5, 0.0),
    "shoulder.L": (-17.0, 0.0, 3.0),
    "shoulder.R": (-15.0, 0.0, -10.0),   # 右臂 rz<0 = 向后 ⟹ 拉开
}

# ---------------------------------------------------------------- 候选出拳姿态
# 出拳手 = 右（后手）。★ 镜像陷阱：右臂 rz>0 = 向前，与左臂相反，别照抄 B01。
STRIKE_CANDIDATES = {
    "S1": {   # 宽横摆：上臂前送 + 前臂横过中线（肘 ~150°），拳到身体左侧
        "upperarm.R": (0.35, -0.90, -0.25),
        "forearm.R": (0.70, -0.70, 0.10),
        "hand.R": (0.80, -0.58, 0.10),
        "upperarm.L": (0.30, -0.20, -0.93),
        "forearm.L": (-0.30, -0.30, 0.90),
        "hand.L": (-0.18, -0.60, 0.78),
    },
    "S2": {   # 收紧横拳：肘更弯（~120°），拳停在脸前偏左
        "upperarm.R": (0.42, -0.86, -0.30),
        "forearm.R": (0.62, -0.55, 0.56),
        "hand.R": (0.72, -0.68, 0.14),
        "upperarm.L": (0.30, -0.20, -0.93),
        "forearm.L": (-0.30, -0.30, 0.90),
        "hand.L": (-0.18, -0.60, 0.78),
    },
    "S3": {   # 高位横摆：拳打头高，上臂更外展
        "upperarm.R": (0.46, -0.84, 0.28),
        "forearm.R": (0.74, -0.66, 0.10),
        "hand.R": (0.82, -0.56, 0.06),
        "upperarm.L": (0.30, -0.20, -0.93),
        "forearm.L": (-0.30, -0.30, 0.90),
        "hand.L": (-0.18, -0.60, 0.78),
    },
}

COIL_CANDIDATES = {
    "C1": {   # 拳收到肩侧后方，肘后拉（经典后手蓄力）
        "upperarm.R": (-0.34, 0.30, -0.89),
        "forearm.R": (0.26, -0.12, 0.96),
        "hand.R": (0.16, -0.50, 0.85),
        "upperarm.L": (0.28, -0.26, -0.92),
        "forearm.L": (-0.34, -0.30, 0.89),
        "hand.L": (-0.20, -0.58, 0.79),
    },
    "C2": {   # 拳拉到身体右侧更外、更低（抡起来更开）
        "upperarm.R": (-0.58, 0.22, -0.78),
        "forearm.R": (0.34, 0.10, 0.94),
        "hand.R": (0.22, -0.42, 0.88),
        "upperarm.L": (0.28, -0.28, -0.92),
        "forearm.L": (-0.34, -0.30, 0.89),
        "hand.L": (-0.20, -0.58, 0.79),
    },
}


def mm(v):
    return [round(x * 1000.0, 1) for x in v]


def trunk_pose(trunk):
    return {name: tuple(trunk[name]) for name in TRUNK8}


def euler_of(arm, names):
    return {n: tuple(math.degrees(v) for v in arm.pose.bones[n].rotation_euler)
            for n in names}


def aim_arms(arm, pose, dirs):
    A.apply_pose(arm, pose)
    out = {}
    for bone in ARM6:
        out[bone] = A.aim_bone(arm, bone, dirs[bone])
    return out


def geom(arm, sternum):
    """当前姿态下的手臂几何量。"""
    world_fist = {s: Vector(A.bone_world(arm, "hand." + s, "tail"))
                  for s in ("L", "R")}
    world_sh = {s: Vector(A.bone_world(arm, "upperarm." + s, "head"))
                for s in ("L", "R")}
    world_elbow = {s: Vector(A.bone_world(arm, "forearm." + s, "head"))
                   for s in ("L", "R")}
    world_wrist = {s: Vector(A.bone_world(arm, "hand." + s, "head"))
                   for s in ("L", "R")}
    line, radius_shoulder, radius_sternum = {}, {}, {}
    for s in ("L", "R"):
        upper = (world_elbow[s] - world_sh[s]).length
        fore = (world_wrist[s] - world_elbow[s]).length
        span = (world_wrist[s] - world_sh[s]).length
        line[s] = round(span / max(1e-9, upper + fore), 4)
        radius_shoulder[s] = round(span * 1000.0, 1)
        radius_sternum[s] = round((world_wrist[s] - sternum).length * 1000.0, 1)
    return {
        "fist_mm": {s: mm(world_fist[s]) for s in ("L", "R")},
        "wrist_mm": {s: mm(world_wrist[s]) for s in ("L", "R")},
        "elbow_mm": {s: mm(world_elbow[s]) for s in ("L", "R")},
        "shoulder_mm": {s: mm(world_sh[s]) for s in ("L", "R")},
        "strike_line_ratio": line,
        "wrist_shoulder_radius_mm": radius_shoulder,
        "wrist_sternum_radius_mm": radius_sternum,
        "lateral_dx_from_sternum_mm": {
            s: round((world_fist[s].x - sternum.x) * 1000.0, 1)
            for s in ("L", "R")},
        "reach_from_sternum_mm": {
            s: round((sternum.y - world_fist[s].y) * 1000.0, 1)
            for s in ("L", "R")},
    }


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    if "Idle_01" not in bpy.data.actions:
        print("PROBE_BOOTSTRAP 缺 Idle_01，先补跑 A01")
        I1.main()
        arm, _meshes = A.open_animation_project()
        A.setup_scene()

    # ---------- ① `Idle_01@0` 站架真值 + 护体架势手臂欧拉（strike 的起点） ----------
    I1.idle_pose(arm, 0.0)
    ankle = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in ("L", "R")}
    sternum = Vector(A.bone_world(arm, "neck", "head"))
    fist0 = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in ("L", "R")}
    E_GUARD = euler_of(arm, ARM6)
    front = "L" if ankle["L"].y < ankle["R"].y else "R"
    A.report("LIGHT02_IDLE_TRUTH", {
        "ankle_mm": {s: mm(ankle[s]) for s in ankle},
        "sternum_mm": mm(sternum),
        "fist_mm": {s: mm(fist0[s]) for s in fist0},
        "front_foot": front,
        "front_hand": front,
        "back_hand_puncher": "R" if front == "L" else "L",
        "guard_arm_euler_deg": {k: [round(x, 3) for x in v]
                                for k, v in E_GUARD.items()},
        "guard_reach_mm": {s: round((sternum.y - fist0[s].y) * 1000.0, 1)
                           for s in ("L", "R")},
        "guard_lateral_dx_mm": {s: round((fist0[s].x - sternum.x) * 1000.0, 1)
                                for s in ("L", "R")},
        "note": "B01 已定前脚 L ⟹ 出拳手 = 后手 = R（本支不重判，只复核）",
    })

    # ---------- ② 候选姿态体检 ----------
    rows = {}
    all_candidates = {}
    all_candidates.update({k: (v, TRUNK_STRIKE) for k, v in STRIKE_CANDIDATES.items()})
    all_candidates.update({k: (v, TRUNK_COIL) for k, v in COIL_CANDIDATES.items()})

    for tag, (dirs, trunk) in all_candidates.items():
        pose = dict(trunk_pose(trunk))
        pose.update(A.FIST)
        e = aim_arms(arm, pose, dirs)
        sternum_now = Vector(A.bone_world(arm, "neck", "head"))
        g = geom(arm, sternum_now)
        # 折到离 guard 最近的一族（与正式脚本同口径）后，再算逐分量差。
        e_folded = {b: JS._unwrap_xyz(E_GUARD[b], e[b]) for b in ARM6}
        delta = {b: [round(e_folded[b][i] - E_GUARD[b][i], 2) for i in range(3)]
                 for b in ARM6}
        worst_comp = max(max(abs(x) for x in delta[b]) for b in ARM6)
        worst_where = max(((b, i) for b in ARM6 for i in range(3)),
                          key=lambda bi: abs(delta[bi[0]][bi[1]]))
        rows[tag] = {
            "raw_euler_deg": {b: [round(x, 2) for x in e[b]] for b in ARM6},
            "folded_euler_deg": {b: [round(x, 2) for x in e_folded[b]]
                                 for b in ARM6},
            "euler_delta_from_guard_deg": delta,
            "worst_comp_delta_deg": round(worst_comp, 2),
            "worst_comp_at": "%s[%d]" % worst_where,
            "max_abs_euler_y_deg": round(max(abs(x[1]) for x in e_folded.values()),
                                         2),
            "max_abs_euler_x_deg": round(max(abs(x[0]) for x in e_folded.values()),
                                         2),
            "max_abs_euler_z_deg": round(max(abs(x[2]) for x in e_folded.values()),
                                         2),
            "geom": g,
            "puncher_lateral_dx_mm": g["lateral_dx_from_sternum_mm"]["R"],
            "puncher_reach_mm": g["reach_from_sternum_mm"]["R"],
        }
    A.report("LIGHT02_CANDIDATES", rows)

    # ---------- ③ 结合「guard ⇄ strike」推 no_teleport 预算 ----------
    def coef_strike(n, p=1.06):
        return 1.0 - (1.0 - 1.0 / n) ** p

    def coef_rec(n, p=1.59):
        return 1.0 - (1.0 - 1.0 / n) ** p

    budget = {}
    for tag in STRIKE_CANDIDATES:
        total = rows[tag]["worst_comp_delta_deg"]
        entry = {"guard_to_strike_worst_comp_deg": total,
                 "puncher_lateral_dx_mm": rows[tag]["puncher_lateral_dx_mm"],
                 "puncher_reach_mm": rows[tag]["puncher_reach_mm"],
                 "max_abs_euler_y_deg": rows[tag]["max_abs_euler_y_deg"]}
        for n in (5, 6, 7, 8):
            peak = total * coef_strike(n)
            entry["strike_%d_frames" % n] = {
                "peak_step_deg": round(peak, 2),
                "over_25": bool(peak > 25.0)}
        budget[tag] = entry
    A.report("LIGHT02_NO_TELEPORT_BUDGET", {
        "strike_profile_coef": {n: round(coef_strike(n), 4)
                                for n in (5, 6, 7, 8)},
        "recover_profile_coef": {n: round(coef_rec(n), 4)
                                 for n in (9, 10, 11, 12)},
        "per_candidate": budget,
        "punch_arm": "R",
        "note": ("本支是**后手横拳**：出拳手 = R。逐分量欧拉差 = no_teleport 预算；"
                 "横拳行程比 B01 直拳长，帧数只能多不能少"),
    })

    # ---------- ④ 反向预备可行性（B02 的前摇能不能真把拳往后拉） ----------
    pullback = {}
    guard_lat = (fist0["R"].x - sternum.x) * 1000.0
    guard_reach = (sternum.y - fist0["R"].y) * 1000.0
    for tag in COIL_CANDIDATES:
        g = rows[tag]["geom"]
        pullback[tag] = {
            "fist_mm": g["fist_mm"]["R"],
            "lateral_dx_mm": g["lateral_dx_from_sternum_mm"]["R"],
            "reach_mm": g["reach_from_sternum_mm"]["R"],
            "delta_lateral_mm": round(g["lateral_dx_from_sternum_mm"]["R"]
                                      - guard_lat, 1),
            "delta_reach_mm": round(g["reach_from_sternum_mm"]["R"]
                                    - guard_reach, 1),
            "worst_comp_delta_deg": rows[tag]["worst_comp_delta_deg"],
            "max_abs_euler_y_deg": rows[tag]["max_abs_euler_y_deg"],
        }
    A.report("LIGHT02_COIL_PULLBACK", {
        "guard_lateral_dx_mm": round(guard_lat, 1),
        "guard_reach_mm": round(guard_reach, 1),
        "coil": pullback,
        "note": "delta_reach_mm < 0 才叫\"拳向后收\"；B01 直拳里做不到，横拳里应当可以",
    })

    print("LIGHT02_NOTE 前脚=%s / 前手=%s / 出拳手(后手)=%s"
          % (front, front, "R" if front == "L" else "L"))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_LIGHT02_FAILURE " + traceback.format_exc())
