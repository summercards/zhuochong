"""probe_c10_baseline —— 只量不做：为 C10 `Skill_02` 抱摔 回答四个问题。

清单 C10 计划 §4「开工顺序」第 2 条要求的四量：

  ① 抓取姿下双手能到的**世界域**（对 `grab_point_m` 定标）
  ② 抱起姿下双手能抬到多高 —— `lift_height_ok` 的 600 mm **能不能达标**（先量再定阈值）
  ③ 髋部发力下沉时骨盆 z 的**许可域**（结合腿可达比 ≤ 0.995）
  ④ 砸地段手从高处到地面的**落点可达域**（对 `slam_speed_ok` / 末帧 z 定标）

做法：把 C10 拟用的**几何**（躯干轨道 + 骨盆位 + 踝拖行 + `leg_seat` + `arm_seat`）
在探针里先跑一遍，逐组打印「指尖误差 / 肩→目标距离比 / 截断标志 / 腿可达比」。
**不建 Action、不出图**。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_c10_baseline.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A            # noqa: E402
import anim_idle_01 as I1       # noqa: E402
import anim_grab04 as G4        # noqa: E402

SIDES = ("L", "R")
XOFF = {"L": 1.0, "R": -1.0}     # +X = 角色左
# 躯干前倾和在各段的分配（与 `anim_skill02.py` 的 `LEAN_SPLIT` 必须一致）
LEAN_SPLIT = {"pelvis": 0.36, "spine_01": 0.20, "spine_02": 0.20, "chest": 0.24}
TWIST_SPLIT = {"pelvis": 0.40, "spine_01": 0.20, "spine_02": 0.20, "chest": 0.20}

SEAM_EULER = {}
Z_SEAM = 0.0
ANKLE_0 = {}
IDLE_KNEE_DIR = {}


def _unit(v):
    v = Vector(v)
    return v / (v.length or 1.0)


def setup(arm):
    """读 `Idle_01@0` 真值 + 骨基座（`leg_seat` / `arm_seat` 缺省滚转基准）。"""
    global SEAM_EULER, Z_SEAM, ANKLE_0, IDLE_KNEE_DIR
    src = bpy.data.actions[I1.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = src
    A._bind_slot(arm, src)
    scene = bpy.context.scene
    scene.frame_set(0)
    bpy.context.view_layer.update()
    SEAM_EULER = {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
                  for b in arm.pose.bones}
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    ANKLE_0 = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}

    idle = I1.idle_pose(arm, 0.0)
    A.apply_pose(arm, idle)
    bpy.context.view_layer.update()
    basis, dirs, knee = {}, {}, {}
    for name in ("thigh.L", "shin.L", "thigh.R", "shin.R",
                 "upperarm.L", "forearm.L", "hand.L",
                 "upperarm.R", "forearm.R", "hand.R"):
        basis[name] = arm.pose.bones[name].matrix.to_3x3().copy()
        dirs[name] = tuple(A.bone_direction(arm, name))
    for s in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + s, "head"))
        kn = Vector(A.bone_world(arm, "thigh." + s, "tail"))
        knee[s] = (kn - hip).normalized()
    G4.IDLE_BASIS.clear()
    G4.IDLE_BASIS.update(basis)
    G4.IDLE_DIR.clear()
    G4.IDLE_DIR.update(dirs)
    G4.IDLE_KNEE_DIR.clear()
    G4.IDLE_KNEE_DIR.update(knee)
    IDLE_KNEE_DIR = knee
    G4.ARM_LEN.clear()
    for s in SIDES:
        G4.ARM_LEN[s] = {
            "upper": arm.pose.bones["upperarm." + s].length,
            "forearm": arm.pose.bones["forearm." + s].length,
            "hand": arm.pose.bones["hand." + s].length}


def geom(arm, py, pz, lean, twist, targets, elbow_dirs, ankle_lag=0.90,
         sole=False):
    """装配一组候选姿态并回报可达量。不建 Action。"""
    pose = {name: (lean * LEAN_SPLIT[name], twist * TWIST_SPLIT[name], 0.0)
            for name in LEAN_SPLIT}
    pose["@loc"] = {"pelvis": A.wloc(0.0, py, pz - 0.900)}
    A.apply_pose(arm, pose)
    ank = {s: (ANKLE_0[s].x, ANKLE_0[s].y + py * ankle_lag, ANKLE_0[s].z)
           for s in SIDES}
    for s in SIDES:
        G4.leg_seat(arm, pose, s, ank[s], IDLE_KNEE_DIR[s])
    for s in SIDES:
        A.keep_world_orientation(arm, "foot." + s)

    out = {"pelvis_z_mm": round(pz * 1000.0, 2), "lean_deg": lean,
           "twist_deg": twist}
    hands = {}
    for s in SIDES:
        clamp, dist_mm, limit_mm = G4.arm_seat(
            arm, pose, s, targets[s], elbow_dirs[s], ref=None)
        got = Vector(A.bone_world(arm, "hand." + s, "tail"))
        want = Vector(targets[s])
        hands[s] = {
            "target_mm": [round(v * 1000.0, 1) for v in want],
            "got_mm": [round(v * 1000.0, 1) for v in got],
            "err_mm": round((got - want).length * 1000.0, 3),
            "dist_mm": round(dist_mm, 2),
            "limit_mm": round(limit_mm, 2),
            "ratio": round(dist_mm / limit_mm, 5),
            "clamp": bool(clamp),
        }
        hip = Vector(A.bone_world(arm, "thigh." + s, "head"))
        hands[s]["leg_ratio"] = round(
            (Vector(ank[s]) - hip).length / (A.L_THIGH + A.L_SHIN), 5)
        hands[s]["shoulder_mm"] = [round(v * 1000.0, 1) for v in
                                   A.bone_world(arm, "upperarm." + s, "head")]
    out["arm"] = hands
    mid = 0.5 * (Vector(A.bone_world(arm, "hand.L", "tail"))
                 + Vector(A.bone_world(arm, "hand.R", "tail")))
    out["hand_mid_mm"] = [round(v * 1000.0, 1) for v in mid]
    out["ankle_mm"] = {s: [round(v * 1000.0, 1) for v in ank[s]]
                       for s in SIDES}
    if sole:
        low = A.foot_lowest_by_side()
        out["sole_mm"] = {s: (None if low[s] is None
                              else round(low[s][2] * 1000.0, 2))
                          for s in SIDES}
    return out


def tgt(x_off, y, z, spread=0.16):
    return {s: (XOFF[s] * spread + x_off, y, z) for s in SIDES}


ELBOW = {s: (XOFF[s] * 0.85, 0.45, -0.35) for s in SIDES}


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    if I1.NAME not in bpy.data.actions:
        I1.main()
        arm, _meshes = A.open_animation_project()
        A.setup_scene()
    setup(arm)

    res = {"seam": {"pelvis_z0_mm": round(Z_SEAM * 1000.0, 3),
                    "ankle0_mm": {s: [round(v * 1000.0, 2) for v in ANKLE_0[s]]
                                  for s in SIDES}},
           "lean_split": LEAN_SPLIT}

    # ---- ① 抓取姿：骨盆下沉 + 前踏，双手前伸够到敌人腰腹
    grab = {}
    for lean in (10.0, 14.0, 18.0):
        for py, pz in ((-0.20, 0.770), (-0.24, 0.780)):
            for ty, tz in ((-0.62, 0.98), (-0.68, 1.04)):
                key = "lean%+05.1f_py%+05.2f_pz%05.2f_ty%+05.2f_tz%05.2f" % (
                    lean, py, pz, ty, tz)
                grab[key] = geom(arm, py, pz, lean, 0.0, tgt(0.0, ty, tz),
                                 ELBOW)
    res["grab"] = grab

    # ---- ② 抱起顶点：能抬多高（lift_height_ok 的 600 mm 定标）
    carry = {}
    for lean in (-10.0, -6.0, -2.0):
        for pz in (0.855, 0.870):
            for ty, tz in ((-0.16, 1.62), (-0.20, 1.70), (-0.24, 1.78)):
                key = "lean%+05.1f_pz%05.3f_ty%+05.2f_tz%05.2f" % (
                    lean, pz, ty, tz)
                carry[key] = geom(arm, -0.20, pz, lean, 0.0,
                                  tgt(0.0, ty, tz, spread=0.20), ELBOW)
    res["carry"] = carry

    # ---- ③④ 砸地：骨盆下沉许可域 + 手落点可达域
    slam = {}
    for lean in (45.0, 55.0, 65.0):
        for pz in (0.520, 0.560, 0.600):
            probe = geom(arm, -0.42, pz, lean, 0.0,
                         tgt(0.0, -0.80, 0.25, spread=0.16), ELBOW)
            sh = Vector(probe["arm"]["L"]["shoulder_mm"]) / 1000.0
            # 以「肩正下方」为最省的可达点定标：手指沿 (0, +0.06, −1) 方向伸直
            base = geom(arm, -0.42, pz, lean, 0.0,
                        {s: (XOFF[s] * 0.16, sh.y + 0.06, sh.z - 0.55)
                         for s in SIDES}, ELBOW, sole=True)
            key = "lean%+05.1f_pz%05.3f" % (lean, pz)
            slam[key] = {"shoulder_L_mm": probe["arm"]["L"]["shoulder_mm"],
                         "straight_down": base}
    res["slam"] = slam

    # ---- 抱起顶点手中部相对抓取点手中部的**净抬升**（一眼看 lift 够不够 600）
    best = {}
    for name, data in carry.items():
        best[name] = data["hand_mid_mm"]
    res["carry_hand_mid_mm"] = best
    res["grab_hand_mid_mm"] = {name: data["hand_mid_mm"]
                               for name, data in list(grab.items())[:3]}

    A.report("C10_BASELINE", res)
    print("C10_PROBE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C10_PROBE_FAILURE " + traceback.format_exc())
