"""probe_dash10b —— B10 开工前的符号标定（第二轮）。

量四件：
  1. `chest.ry` / `pelvis.ry` 的正负号 ↔ 哪一侧肩膀向前（扭腰方向）。
  2. `Run@0` 的真值细节：L/R 踝的世界 x、足尖世界角、拳的世界位置。
  3. `Idle_01@0` 的 R 拳 / L 拳世界位置（收招终点参照）。
  4. 手臂伸直时的拳世界行程（冲拳幅度预算）。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_dash10b.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_idle_01 as I1  # noqa: E402
import anim_run as R  # noqa: E402
import anim_walk_f as WF  # noqa: E402


def report(name, payload):
    print("%s %s" % (name, json.dumps(payload, ensure_ascii=False, default=str)))


def mm(v):
    return [round(x * 1000.0, 2) for x in v]


def twist_sign(arm):
    out = {}
    for bone in ("pelvis", "chest"):
        for ry in (-20.0, 20.0):
            A.reset_pose(arm)
            arm.pose.bones[bone].rotation_euler = (0.0, math.radians(ry), 0.0)
            bpy.context.view_layer.update()
            out["%s_ry%+d" % (bone, int(ry))] = {
                "shoulder_L_y": round(A.bone_world(arm, "shoulder.L", "head").y
                                      * 1000.0, 2),
                "shoulder_R_y": round(A.bone_world(arm, "shoulder.R", "head").y
                                      * 1000.0, 2),
                "thigh_L_y": round(A.bone_world(arm, "thigh.L", "head").y
                                   * 1000.0, 2),
                "thigh_R_y": round(A.bone_world(arm, "thigh.R", "head").y
                                   * 1000.0, 2),
            }
    A.reset_pose(arm)
    bpy.context.view_layer.update()
    return out


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    report("DASH10B_TWIST_SIGN", {
        "rows": twist_sign(arm),
        "note": "y 越小 = 越靠前（角色正面朝 −Y）。",
    })

    # Run@0 真值
    A.apply_pose(arm, WF.gait_pose(arm, R.RUN, 0, meshes))
    run0 = {
        "ankle_L": mm(A.bone_world(arm, "foot.L", "head")),
        "ankle_R": mm(A.bone_world(arm, "foot.R", "head")),
        "fist_L": mm(A.bone_world(arm, "hand.L", "tail")),
        "fist_R": mm(A.bone_world(arm, "hand.R", "tail")),
        "shoulder_L": mm(A.bone_world(arm, "shoulder.L", "head")),
        "shoulder_R": mm(A.bone_world(arm, "shoulder.R", "head")),
        "tip_L_deg": round(A.world_tip_deg(arm, "foot.L"), 3),
        "tip_R_deg": round(A.world_tip_deg(arm, "foot.R"), 3),
        "sole": {k: round(v[2] * 1000.0, 2)
                 for k, v in A.foot_lowest_by_side().items()},
    }
    report("DASH10B_RUN0", run0)

    # Idle_01@0 真值
    A.apply_pose(arm, I1.idle_pose(arm, 0.0))
    idle0 = {
        "fist_L": mm(A.bone_world(arm, "hand.L", "tail")),
        "fist_R": mm(A.bone_world(arm, "hand.R", "tail")),
        "shoulder_L": mm(A.bone_world(arm, "shoulder.L", "head")),
        "shoulder_R": mm(A.bone_world(arm, "shoulder.R", "head")),
        "ankle_L": mm(A.bone_world(arm, "foot.L", "head")),
        "ankle_R": mm(A.bone_world(arm, "foot.R", "head")),
    }
    report("DASH10B_IDLE0", idle0)

    # 手臂骨长（伸直长度预算）
    A.reset_pose(arm)
    bpy.context.view_layer.update()
    lens = {}
    for name in ("shoulder.R", "upperarm.R", "forearm.R", "hand.R",
                 "upperarm.L", "forearm.L", "hand.L"):
        head = A.bone_world(arm, name, "head")
        tail = A.bone_world(arm, name, "tail")
        lens[name] = round((Vector(tail) - Vector(head)).length * 1000.0, 2)
    lens["arm_R_shoulder_to_fist_mm"] = round(
        sum(lens[n] for n in ("shoulder.R", "upperarm.R", "forearm.R",
                              "hand.R")), 2)
    report("DASH10B_BONE_LENGTH", lens)
    print("DASH10B_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("DASH10B_FAILURE " + traceback.format_exc())
