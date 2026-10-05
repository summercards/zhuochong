"""probe_c08_baseline —— C08 `Charge` 开工前的「只量不做」探针。

清单 C08 计划 §4 第 2 步：
    「量 Idle 站架下**骨盆能沉到多低而 `leg_seat` 可达比仍 ≤0.95**，
      以及**两脚保持扎稳的骨盆 xy 许可域**。」

本探针只读不写：不改 Action、不存盘、不导 GLB。回答四个数字问题：

  ① Idle_01@0 站架的地面真值：骨盆 z、两踝世界坐标、站宽、腿可达比、鞋底 z。
  ② 下沉扫描：骨盆 z 从 Idle 值一路降到 −220 mm，逐档解 `leg_seat`
     （踝钉在 Idle 原位）⟹ 腿可达比、膝角（shin rx）、髋角（thigh rx）、
     鞋底 z。回答"沉到多低仍然 ratio ≤ 0.95 且鞋底不穿地"。
  ③ 上顶扫描：骨盆 z 升到 +100 mm ⟹ 腿会不会被拉爆（ratio > 0.995）？
     —— 释放段要"爆发上顶"，这条决定上顶上限。
  ④ xy 许可域：骨盆在固定 z 下横移 ±120 mm / 前后移 ±120 mm，
     逐档量 ratio。回答"扎稳时骨盆只能晃多少"。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python probe_c08_baseline.py
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

IDLE_BASIS = {}
IDLE_DIR = {}
IDLE_KNEE_DIR = {}
ANKLE = {}
Z_SEAM = 0.0
LIMIT = 0.0


def setup_idle():
    """Idle_01@0 站架 + 骨基座（`leg_seat` 的缺省基准）。"""
    global Z_SEAM, LIMIT
    if "Idle_01" not in bpy.data.actions:
        print("C08PROBE_BOOTSTRAP 缺 Idle_01，先补跑 A01")
        I1.main()
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    I1.idle_pose(arm, 0.0)
    IDLE_BASIS.clear()
    IDLE_DIR.clear()
    IDLE_KNEE_DIR.clear()
    ANKLE.clear()
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        IDLE_KNEE_DIR[side] = (knee - hip).normalized()
        for name in ("thigh." + side, "shin." + side):
            IDLE_BASIS[name] = arm.pose.bones[name].matrix.to_3x3().copy()
            IDLE_DIR[name] = A.bone_direction(arm, name)
        ANKLE[side] = Vector(A.bone_world(arm, "foot." + side, "head"))
    Z_SEAM = A.bone_world(arm, "pelvis", "head").z
    LIMIT = A.L_THIGH + A.L_SHIN
    G4.IDLE_BASIS.clear()
    G4.IDLE_BASIS.update(IDLE_BASIS)
    G4.IDLE_DIR.clear()
    G4.IDLE_DIR.update(IDLE_DIR)
    G4.IDLE_KNEE_DIR.clear()
    G4.IDLE_KNEE_DIR.update(IDLE_KNEE_DIR)
    return arm


def measure(arm, label, torso_rx, pz, px=0.0, py=0.0):
    """摆出「给定躯干前屈 + 骨盆世界位置」，踝钉在 Idle 原处，返回实测。"""
    pose = {
        "pelvis": (torso_rx, 0.0, 0.0),
        "spine_01": (torso_rx * 0.5, 0.0, 0.0),
        "spine_02": (torso_rx * 0.5, 0.0, 0.0),
        "chest": (torso_rx * 0.5, 0.0, 0.0),
        "neck": (-torso_rx * 0.5, 0.0, 0.0),
        "head": (-torso_rx * 0.25, 0.0, 0.0),
        "shoulder.L": (0.0, 0.0, 0.0),
        "shoulder.R": (0.0, 0.0, 0.0),
        "@loc": {"pelvis": A.wloc(px, py, pz - 0.900)},
    }
    A.apply_pose(arm, pose)
    for side in SIDES:
        G4.leg_seat(arm, pose, side, tuple(ANKLE[side]), IDLE_KNEE_DIR[side])
    for side in SIDES:
        A.keep_world_orientation(arm, "foot." + side)
    bpy.context.view_layer.update()

    out = {"label": label, "torso_rx": torso_rx,
           "pelvis_z_arg_mm": round(pz * 1000.0, 2)}
    pelvis = Vector(A.bone_world(arm, "pelvis", "head"))
    out["pelvis_mm"] = [round(v * 1000.0, 2) for v in pelvis]
    out["ratio"] = {}
    out["knee_delta_mm"] = {}
    for side in SIDES:
        hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
        ach = Vector(A.bone_world(arm, "foot." + side, "head"))
        knee = Vector(A.bone_world(arm, "thigh." + side, "tail"))
        out["ratio"][side] = round((ach - hip).length / LIMIT, 5)
        # 膝相对髋踝连线的**垂直偏出量**：读"膝锁死 / 膝超前"用
        seg = (ach - hip)
        t = (knee - hip).dot(seg) / max(1e-9, seg.length_squared)
        out["knee_delta_mm"][side] = round(
            ((knee - hip) - seg * t).length * 1000.0, 2)
    out["ankle_err_mm"] = {
        side: round((Vector(A.bone_world(arm, "foot." + side, "head"))
                     - ANKLE[side]).length * 1000.0, 4) for side in SIDES}
    out["thigh_rx_deg"] = {side: round(math.degrees(
        arm.pose.bones["thigh." + side].rotation_euler.x), 2) for side in SIDES}
    out["shin_rx_deg"] = {side: round(math.degrees(
        arm.pose.bones["shin." + side].rotation_euler.x), 2) for side in SIDES}
    low = A.foot_lowest_by_side()
    out["sole_mm"] = {side: (None if low[side] is None
                             else round(low[side][2] * 1000.0, 2))
                      for side in SIDES}
    return out


def main():
    arm = setup_idle()
    A.report("C08PROBE_IDLE", {
        "pelvis_z_mm": round(Z_SEAM * 1000.0, 3),
        "ankle_mm": {s: [round(v * 1000.0, 2) for v in ANKLE[s]]
                     for s in SIDES},
        "stance_width_mm": round(abs(ANKLE["L"].x - ANKLE["R"].x) * 1000.0, 2),
        "leg_limit_mm": round(LIMIT * 1000.0, 2),
        "idle_ratio": {s: round(
            (Vector(A.bone_world(arm, "foot." + s, "head"))
             - Vector(A.bone_world(arm, "thigh." + s, "head"))).length
            / LIMIT, 5) for s in SIDES},
        "note": "腿长上限 = L_THIGH+L_SHIN；扎稳时踝钉死 ⟹ 骨盆动 = 腿伸缩",
    })

    # ---------------------------------------------------------------- ② 下沉扫描
    rows = []
    for mm in (0, -20, -40, -60, -80, -100, -120, -140, -160, -180, -200, -220):
        for rx in (0.0, 10.0, 20.0):
            rows.append(measure(arm, "sink", rx, Z_SEAM + mm / 1000.0))
    A.report("C08PROBE_SINK", {
        "rows": rows,
        "note": ("门禁 charge_leg_reach_ok：循环段 ratio ≤ 0.95；"
                 "ground_contact：鞋底 ∈ [−2,+6] mm。"
                 "rx = pelvis 前屈（躯干会跟着下沉，踝仍钉死）"),
        "best": {
            "min_ratio_le_095": max(
                [r["pelvis_z_arg_mm"] for r in rows
                 if max(r["ratio"].values()) <= 0.95] or [None]),
        },
    })

    # ---------------------------------------------------------------- ③ 上顶扫描
    rows = []
    for mm in (0, 20, 40, 60, 80, 100, 120):
        rows.append(measure(arm, "rise", 0.0, Z_SEAM + mm / 1000.0))
    A.report("C08PROBE_RISE", {
        "rows": rows,
        "note": ("释放段「爆发上顶」的上限：ratio 必须 ≤ 0.995（通用 ik_reach），"
                 "且 ≤0.995 之上腿被截断 ⟹ 支撑脚会滑。"),
    })

    # ---------------------------------------------------------------- ④ xy 许可域
    sink_z = Z_SEAM - 0.100
    rows = []
    for d in (-120, -80, -40, 0, 40, 80, 120):
        rows.append(measure(arm, "dx%d" % d, 0.0, sink_z, px=d / 1000.0))
        rows.append(measure(arm, "dy%d" % d, 0.0, sink_z, py=d / 1000.0))
    A.report("C08PROBE_XY", {
        "rows": rows,
        "note": "骨盆横移/前后移的许可域（踝钉死，ratio ≤ 0.995 为界）",
        "z_mm": round(sink_z * 1000.0, 2),
    })


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("C08PROBE_FAILURE " + traceback.format_exc())
