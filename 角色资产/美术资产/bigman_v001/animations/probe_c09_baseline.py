"""probe_c09_baseline —— C09 `Skill_01` 肩撞开工前的「只量不做」探针。

清单 C09 计划 §4 第 2 步的四问：
  ① 站桩下骨盆**水平**位移的许可域（前冲靠骨盆平移，腿是 `leg_seat` 三维 IK，
     脚要在地上「拖」）；
  ② 前倾 35~45° 时躯干各段可达角；
  ③ 肩骨 tail 的世界坐标在「撞出」姿下能到多前（对 `shoulder_hit_ok` 的
     150 mm 定标）；
  ④ 单帧骨盆位移上限（防 `no_teleport`）。

本探针只读不写：不改 Action、不存盘、不导 GLB。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_c09_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A        # noqa: E402
import anim_idle_01 as I1   # noqa: E402
import anim_grab04 as G4    # noqa: E402
import anim_jump_start as JS  # noqa: E402

SIDES = ("L", "R")
ARM_BONES = ("upperarm.L", "forearm.L", "hand.L",
             "upperarm.R", "forearm.R", "hand.R")

IDLE_BASIS = {}
IDLE_DIR = {}
IDLE_KNEE_DIR = {}
ANKLE = {}
Z_SEAM = 0.0
Y_SEAM = 0.0
LIMIT = 0.0

# 撞出姿的臂方向（世界，x 左正 / y 身后正 / z 上正；正面朝 −y）
HIT_DIRS = {
    "upperarm.L": (0.24, 0.80, -0.55),
    "forearm.L": (0.10, 0.88, -0.46),
    "hand.L": (0.05, 0.92, -0.39),
    "upperarm.R": (-0.24, 0.80, -0.55),
    "forearm.R": (-0.10, 0.88, -0.46),
    "hand.R": (-0.05, 0.92, -0.39),
}


def setup_idle():
    global Z_SEAM, Y_SEAM, LIMIT
    if "Idle_01" not in bpy.data.actions:
        print("C09PROBE_BOOTSTRAP 缺 Idle_01，先补跑 A01")
        I1.main()
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    I1.idle_pose(arm, 0.0)
    for store in (IDLE_BASIS, IDLE_DIR, IDLE_KNEE_DIR, ANKLE):
        store.clear()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        IDLE_KNEE_DIR[side] = (knee - hip).normalized()
        for name in ("thigh." + side, "shin." + side):
            IDLE_BASIS[name] = arm.pose.bones[name].matrix.to_3x3().copy()
            IDLE_DIR[name] = A.bone_direction(arm, name)
        ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
    for name in ARM_BONES:
        IDLE_BASIS[name] = arm.pose.bones[name].matrix.to_3x3().copy()
        IDLE_DIR[name] = A.bone_direction(arm, name)
    pelvis = Vector(A.bone_world(arm, "pelvis", "head"))
    Z_SEAM = pelvis.z
    Y_SEAM = pelvis.y
    LIMIT = A.L_THIGH + A.L_SHIN
    G4.IDLE_BASIS.clear()
    G4.IDLE_BASIS.update(IDLE_BASIS)
    G4.IDLE_DIR.clear()
    G4.IDLE_DIR.update(IDLE_DIR)
    G4.IDLE_KNEE_DIR.clear()
    G4.IDLE_KNEE_DIR.update(IDLE_KNEE_DIR)
    return arm


def torso_of(lean, twist):
    """把「总前倾」和「总扭转」分配到骨盆→脊椎→胸。"""
    lean_w = {"pelvis": 0.33, "spine_01": 0.245, "spine_02": 0.245,
              "chest": 0.18}
    twist_w = {"pelvis": 0.28, "spine_01": 0.24, "spine_02": 0.24,
               "chest": 0.24}
    out = {}
    for name in ("pelvis", "spine_01", "spine_02", "chest"):
        out[name] = (lean * lean_w[name], twist * twist_w[name], 0.0)
    # 头颈反向：抵消扭转（头看向正前方）+ 抬头看目标
    out["neck"] = (-lean * 0.30, -twist * 0.55, 0.0)
    out["head"] = (-lean * 0.10, -twist * 0.45, 0.0)
    out["shoulder.L"] = (-10.0, 0.0, 0.0)
    out["shoulder.R"] = (-10.0, 0.0, 0.0)
    return out


def measure(arm, label, py_off, pz_off, lean, twist, lag_l=1.0, lag_r=1.0,
            dirs=None, twist_only=0.0):
    """摆出「骨盆平移到 y+py_off / z+pz_off、躯干 lean 前倾 + twist 扭转、
    踝随骨盆拖行（lag 系数）」的撞出姿，返回实测。"""
    torso = torso_of(lean, twist)
    if twist_only:
        for name in ("pelvis", "spine_01", "spine_02", "chest"):
            r = torso[name]
            torso[name] = (r[0], twist_only, r[2])
    torso["@loc"] = {"pelvis": A.wloc(0.0, Y_SEAM + py_off,
                                      Z_SEAM + pz_off - 0.900)}
    A.apply_pose(arm, torso)
    lags = {"L": lag_l, "R": lag_r}
    for side in SIDES:
        target = (ANKLE[side].x,
                  ANKLE[side].y + py_off * lags[side],
                  ANKLE[side].z)
        G4.leg_seat(arm, torso, side, target, IDLE_KNEE_DIR[side])
    for side in SIDES:
        A.keep_world_orientation(arm, "foot." + side)
    use = dirs or HIT_DIRS
    for name in ARM_BONES:
        G4.aim_bone_ref(arm, name, use[name], IDLE_BASIS[name], IDLE_DIR[name])
    bpy.context.view_layer.update()

    out = {"label": label, "py_off_mm": round(py_off * 1000.0, 1),
           "pz_off_mm": round(pz_off * 1000.0, 1), "lean": lean,
           "twist": twist}
    pelvis = Vector(A.bone_world(arm, "pelvis", "head"))
    out["pelvis_mm"] = [round(v * 1000.0, 2) for v in pelvis]
    out["ratio"] = {}
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        ach = Vector(A.bone_world(arm, "foot." + side, "head"))
        out["ratio"][side] = round((ach - hip).length / LIMIT, 5)
    out["ankle_err_mm"] = {
        side: round((Vector(A.bone_world(arm, "foot." + side, "head"))
                     - Vector((ANKLE[side].x,
                               ANKLE[side].y + py_off * lags[side],
                               ANKLE[side].z))).length * 1000.0, 3)
        for side in SIDES}
    low = A.foot_lowest_by_side()
    out["sole_mm"] = {side: (None if low[side] is None
                             else round(low[side][2] * 1000.0, 2))
                      for side in SIDES}
    out["thigh_rx_deg"] = {s: round(math.degrees(
        arm.pose.bones["thigh." + s].rotation_euler.x), 2) for s in SIDES}
    out["shin_rx_deg"] = {s: round(math.degrees(
        arm.pose.bones["shin." + s].rotation_euler.x), 2) for s in SIDES}
    sh = {s: Vector(A.bone_world(arm, "shoulder." + s, "tail")) for s in SIDES}
    fist = {s: Vector(A.bone_world(arm, "hand." + s, "tail")) for s in SIDES}
    head = Vector(A.bone_world(arm, "head", "tail"))
    out["shoulder_tail_mm"] = {s: [round(v * 1000.0, 1) for v in sh[s]]
                               for s in SIDES}
    out["fist_mm"] = {s: [round(v * 1000.0, 1) for v in fist[s]] for s in SIDES}
    out["head_tail_mm"] = [round(v * 1000.0, 1) for v in head]
    # 肩（左）比「最前的拳」还靠前多少（毫米，正 = 肩更前）
    front_fist_y = min(fist["L"].y, fist["R"].y)
    out["shoulder_lead_mm"] = round((front_fist_y - sh["L"].y) * 1000.0, 2)
    # 肩比另一侧肩更前多少（看扭身有没有把左肩送出去）
    out["shoulder_asym_mm"] = round((sh["R"].y - sh["L"].y) * 1000.0, 2)
    out["torso_sum_rx"] = round(sum(torso[n][0] for n in
                                    ("pelvis", "spine_01", "spine_02",
                                     "chest")), 2)
    return out


def main():
    arm = setup_idle()
    A.report("C09PROBE_IDLE", {
        "pelvis_mm": [round(v * 1000.0, 2)
                      for v in A.bone_world(arm, "pelvis", "head")],
        "ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE[s]]
                     for s in SIDES},
        "stance_width_mm": round(abs(ANKLE["L"].x - ANKLE["R"].x) * 1000.0, 2),
        "stance_span_y_mm": round(abs(ANKLE["L"].y - ANKLE["R"].y) * 1000.0, 2),
        "leg_limit_mm": round(LIMIT * 1000.0, 2),
        "idle_ratio": {s: round(
            (Vector(A.bone_world(arm, "foot." + s, "head"))
             - Vector(A.bone_world(arm, "thigh." + s, "head"))).length
            / LIMIT, 5) for s in SIDES},
        "note": "正面朝 −y；前脚 = 左（y 更小），后脚 = 右",
    })

    # ---------------------------------------------------------- ① ry 扭转方向
    rows = []
    for tw in (-22.0, 22.0):
        rows.append(measure(arm, "twist%+.0f" % tw, 0.0, 0.0, 0.0, 0.0,
                            twist_only=tw))
    A.report("C09PROBE_TWIST", {
        "rows": [{k: r[k] for k in ("label", "twist", "shoulder_tail_mm",
                                    "shoulder_asym_mm")} for r in rows],
        "note": ("shoulder_asym_mm = (R.y − L.y)：正值 = 左肩比右肩更靠前"
                 "（撞出侧要的是左肩在前）。据此定 twist 符号。"),
    })

    # ---------------------------------------------------------- ② 前冲扫描
    rows = []
    plan = [("IDLE", 0.0, 0.0, 0.0, 0.0, 1.0, 1.0),
            ("COIL", 0.030, -0.030, 8.0, 10.0, 1.0, 1.0),
            ("DASH1", -0.15, -0.050, 25.0, -6.0, 1.04, 0.94),
            ("DASH2", -0.30, -0.070, 35.0, -13.0, 1.04, 0.94),
            ("DASH3", -0.45, -0.085, 42.0, -18.0, 1.04, 0.94),
            ("HIT", -0.560, -0.090, 45.0, -22.0, 1.04, 0.94),
            ("OVER", -0.650, -0.090, 45.0, -22.0, 1.04, 0.94)]
    for label, py, pz, lean, tw, ll, lr in plan:
        rows.append(measure(arm, label, py, pz, lean, tw, ll, lr))
    A.report("C09PROBE_DASH", {
        "rows": rows,
        "note": ("门禁 ik_reach_ok ≤0.995；ground_contact 鞋底 ∈[−2,+6] mm；"
                 "shoulder_lead_mm ≥150 才算「用肩撞」。"),
    })

    # ---------------------------------------------------------- ③ 臂方向标定
    rows = []
    for label, dirs in (("HIT_DIRS", HIT_DIRS),
                        ("STRAIGHT_DOWN", {b: (0.0, 0.0, -1.0)
                                           for b in ARM_BONES}),
                        ("GUARD", {b: tuple(I1.ARM_DIRS[b])
                                   for b in ARM_BONES})):
        rows.append(measure(arm, label, -0.560, -0.090, 45.0, -22.0,
                            1.04, 0.94, dirs=dirs))
    A.report("C09PROBE_ARM", {
        "rows": [{k: r[k] for k in ("label", "shoulder_lead_mm", "fist_mm",
                                    "shoulder_tail_mm")} for r in rows],
        "note": ("撞出侧左肩必须比双拳更靠前 ≥150 mm ⟹ 臂要明确向后甩；"
                 "「自然下垂」会让拳与肩同 y，判据必红。"),
    })


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C09PROBE_FAILURE " + traceback.format_exc())
