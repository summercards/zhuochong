"""probe_cal —— 调试 `calibrate_plant_z`：逐轮打印"踝目标 / 踝实测 / 鞋底实测"。"""

import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402
import anim_walk_f as WF  # noqa: E402
import anim_run_stop as RS  # noqa: E402


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    print("ACTION_BOUND " + str(arm.animation_data.action if arm.animation_data
                                else None))
    z = 0.200
    rows = []
    for i in range(4):
        pose = {"pelvis": (0.0, 0.0, 0.0),
                "@loc": {"pelvis": A.wloc(0.0, 0.0, 0.0)}}
        A.apply_pose(arm, pose)
        RS.leg_to(arm, pose, "L", (RS.LX0, RS.LY0, z))
        A.keep_world_orientation(arm, "foot.L")
        WF.add_world_rx(arm, "foot.L", 3.0)
        ankle = A.bone_world(arm, "foot.L", "head")
        low_l = A.foot_lowest_by_side()["L"]
        low_side = A.lowest_z_by_side(meshes)
        rows.append({
            "iter": i, "z_in_mm": round(z * 1000.0, 2),
            "ankle_mm": [round(v * 1000.0, 2) for v in ankle],
            "footL_low_mm": [round(v * 1000.0, 2) for v in low_l],
            "side_low_mm": {k: round(v * 1000.0, 2)
                            for k, v in low_side.items()},
            "thigh_euler": [round(v, 2) for v in
                            arm.pose.bones["thigh.L"].rotation_euler],
            "shin_euler": [round(v, 2) for v in
                           arm.pose.bones["shin.L"].rotation_euler],
        })
        z -= low_l[2]
    A.report("CAL_TRACE", rows)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PROBE_CAL_FAILURE " + traceback.format_exc())
