"""probe_heavy01 —— B04 `Heavy_01` 重拳 **只读**探针（定盘数）。

清单「下一支计划 —— B04」的 ★ 三件事在这里落地：
  1. **「跨步」的几何量**：先量 Idle_01@0 的踝位与髋-踝距离余量，
     据此定「前脚前移多少 mm 仍可解」——这是本支最大几何风险。
  2. **`|Y|` 体检**：重拳拳峰更"直"，`|Y|` 预计小于 B03 的 61.45°；
     按 B03 结论办 —— 换族只是体检项，判据交回 `no_teleport`。
  3. **预算先算死**：本支放弃「guard→strike 单一插值」，改成**三段姿态路径**
     （guard → chamber → strike → end）。每段的欧拉跨度先量出来，
     再按 `峰值 = span×(1−(1−1/n)^p) ≤ 25` 定帧数与幂次。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_heavy01.py
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
import anim_turn as TURN      # noqa: E402

ARM6 = ("upperarm.L", "forearm.L", "hand.L",
        "upperarm.R", "forearm.R", "hand.R")
ARMS = ("shoulder.L", "shoulder.R") + ARM6
LEGS = ("thigh.L", "shin.L", "foot.L", "toe.L",
        "thigh.R", "shin.R", "foot.R", "toe.R")
TORSO = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head")

# ---- 候选「腕（hand.head）世界目标」：以 Idle_01@0 的实测位为基准，
#      offsets 用 mm 表达，便于读。arm_to 双骨 IK 会把腕解到这些点。
#      chamber：后手收到身后（重心后坐）；strike：跨步轰拳的命中姿态。
CANDIDATES = {}


def mm(v):
    return [round(x * 1000.0, 1) for x in v]


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)

    world = {}
    for name in TORSO + ARMS + LEGS:
        if name in arm.pose.bones:
            world[name] = {
                "head": tuple(A.bone_world(arm, name, "head")),
                "tail": tuple(A.bone_world(arm, name, "tail")),
            }
    lengths = {name: (Vector(world[name]["tail"]) - Vector(world[name]["head"])).length
               for name in world}

    ANKLE = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in ("L", "R")}
    HIP = {s: Vector(A.bone_world(arm, "thigh." + s, "head")) for s in ("L", "R")}
    WRIST = {s: Vector(A.bone_world(arm, "hand." + s, "head")) for s in ("L", "R")}
    FIST = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in ("L", "R")}
    SHO = {s: Vector(A.bone_world(arm, "upperarm." + s, "head")) for s in ("L", "R")}
    STERNUM = Vector(A.bone_world(arm, "neck", "head"))

    front = "L" if ANKLE["L"].y < ANKLE["R"].y else "R"
    back = "R" if front == "L" else "L"

    A.report("HEAVY01_IDENTITY", {
        "front_foot": front,
        "back_foot": back,
        "punch_hand": back,
        "guard_hand": front,
        "ankle_mm": {s: mm(ANKLE[s]) for s in ("L", "R")},
        "hip_mm": {s: mm(HIP[s]) for s in ("L", "R")},
        "shoulder_mm": {s: mm(SHO[s]) for s in ("L", "R")},
        "wrist_mm": {s: mm(WRIST[s]) for s in ("L", "R")},
        "fist_mm": {s: mm(FIST[s]) for s in ("L", "R")},
        "sternum_mm": mm(STERNUM),
        "bone_len_mm": {k: round(v * 1000.0, 2) for k, v in lengths.items()},
        "leg_reach_limit_mm": round((lengths["thigh.L"] + lengths["shin.L"]) * 1000.0, 1),
        "hip_ankle_mm": {s: round((ANKLE[s] - HIP[s]).length * 1000.0, 1)
                         for s in ("L", "R")},
        "leg_headroom_mm": {
            s: round((lengths["thigh." + s] + lengths["shin." + s]
                      - (ANKLE[s] - HIP[s]).length) * 1000.0, 1)
            for s in ("L", "R")},
        "guard_reach_mm": {s: round((STERNUM.y - FIST[s].y) * 1000.0, 1)
                           for s in ("L", "R")},
        "guard_arm_euler_deg": {
            b: [round(math.degrees(v), 3) for v in arm.pose.bones[b].rotation_euler]
            for b in ARM6},
        "note": ("前脚 ⟹ 出拳手 = 后手（重拳用后手）；前脚前移量受 leg_headroom 限制"),
    })

    # ---- 跨步可达性扫描：前脚前移 x mm 时，前腿在「骨盆前移/下沉」各档下的余量。
    rows = []
    for step_mm in (100, 120, 140, 160, 180, 200):
        for pelvis_y_mm in (30, 0, -40, -60):
            for pelvis_dz_mm in (0, -30, -45):
                hip = HIP["L"] + Vector((0.0, pelvis_y_mm / 1000.0,
                                         pelvis_dz_mm / 1000.0))
                ankle = ANKLE["L"] + Vector((0.0, -step_mm / 1000.0, 0.0))
                need = (ankle - hip).length
                limit = lengths["thigh.L"] + lengths["shin.L"]
                rows.append({
                    "step_mm": step_mm, "pelvis_y_mm": pelvis_y_mm,
                    "pelvis_dz_mm": pelvis_dz_mm,
                    "reach_mm": round(need * 1000.0, 1),
                    "headroom_mm": round((limit - need) * 1000.0, 1),
                    "ok": bool(need <= limit * 0.9995),
                })
    A.report("HEAVY01_CROSS_STEP_SCAN", rows)

    # ---- 横移/纵移对前腿余量的影响（后脚也要够得着）
    back_rows = []
    for step_mm in (140, 160):
        for pelvis_y_mm in (30, 0, -60):
            hip = HIP["R"] + Vector((0.0, pelvis_y_mm / 1000.0, -0.030))
            need = (ANKLE["R"] - hip).length
            limit = lengths["thigh.R"] + lengths["shin.R"]
            back_rows.append({
                "front_step_mm": step_mm, "pelvis_y_mm": pelvis_y_mm,
                "back_reach_mm": round(need * 1000.0, 1),
                "back_headroom_mm": round((limit - need) * 1000.0, 1),
                "ok": bool(need <= limit * 0.9995),
            })
    A.report("HEAVY01_BACK_LEG_SCAN", back_rows)

    # ---- |Y| 体检用的等价族成本：把「命中姿态」用 aim_bone 直接解一遍。
    #      这里只报 guard 的 |Y|，真正的 strike |Y| 在动画脚本的 STRIKE_TRUTH 里报。
    guard_e = {b: tuple(math.degrees(v)
                        for v in arm.pose.bones[b].rotation_euler) for b in ARM6}
    A.report("HEAVY01_Y_HEALTH", {
        "guard_max_abs_y_deg": round(max(abs(guard_e[b][1]) for b in ARM6), 2),
        "b03_max_abs_y_deg": 61.45,
        "b02_max_abs_y_deg": 17.1,
        "rule": ("|Y| 只作体检：B03 已证「>45° 换族」在大幅度动作上失效"
                 "（flip 支 y 更大）⟹ 判据交回 no_teleport"),
    })
    print("PROBE_HEAVY01_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_HEAVY01_FAILURE " + traceback.format_exc())
