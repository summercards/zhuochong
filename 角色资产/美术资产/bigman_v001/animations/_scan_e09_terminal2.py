"""_scan_e09_terminal2 —— 细化 E09 躺地终点的**贴地**组合。

第一轮结论（`E09_TERM_SCAN`）：
  * 大腿取 `thigh_rx = 90 − pelvis_rx`（世界水平向后）后，**腿和躯干等高** ⟹
    骨盆 z 必须降到 ~0.10 才让**躯干**贴地 —— 但同时**鞋**会深陷（foot_rx=0 时鞋尖朝下）。
  * 头的载体 `neck/head rx` 必须明显正转（俯卧时 rx>0 = 朝地面压）才落得了地。

本轮扫：骨盆 z × 膝屈 × 踝 rx × 颈/头压。
"""

import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

WATCH = ("Suit_Torso", "Trouser_L", "Trouser_R", "Shoe_Sole_L", "Shoe_Sole_R",
         "Shoe_Upper_L", "Shoe_Toe_Cap_L", "Head", "Hair_Mass", "Neck",
         "Jacket_Hem", "Sleeve_L")
PELVIS_PITCH = 68.0
REST = 6.0


def per_object_lows():
    depsgraph = bpy.context.evaluated_depsgraph_get()
    out = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        out[obj.name] = min((matrix @ v.co).z for v in mesh.vertices) * 1000.0
        evaluated.to_mesh_clear()
    return out


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    rows = []
    for pz in (0.10, 0.12, 0.14):
        for shin_rx in (0.0, 8.0):
            for foot_rx in (-60.0, -40.0, -20.0):
                for neck in (8.0, 20.0):
                    pose = {
                        "pelvis": (PELVIS_PITCH, 0.0, 0.0),
                        "spine_01": (REST, 0.0, 0.0),
                        "spine_02": (REST, 0.0, 0.0),
                        "chest": (REST, 0.0, 0.0),
                        "neck": (neck, 0.0, 0.0),
                        "head": (14.0, 0.0, 14.0),
                        "shoulder.L": (-18.0, 0.0, 0.0),
                        "shoulder.R": (-18.0, 0.0, 0.0),
                        "thigh.L": (90.0 - PELVIS_PITCH, 0.0, -8.0),
                        "shin.L": (shin_rx, 0.0, 0.0),
                        "foot.L": (foot_rx, 0.0, 0.0),
                        "toe.L": (0.0, 0.0, 0.0),
                        "thigh.R": (90.0 - PELVIS_PITCH, 0.0, 8.0),
                        "shin.R": (shin_rx, 0.0, 0.0),
                        "foot.R": (foot_rx, 0.0, 0.0),
                        "toe.R": (0.0, 0.0, 0.0),
                        "@loc": {"pelvis": A.wloc(0.0, 0.0, pz - 0.900)},
                    }
                    pose.update(A.FIST)
                    A.apply_pose(arm, pose)
                    lows = per_object_lows()
                    rows.append({
                        "pz": pz, "shin_rx": shin_rx, "foot_rx": foot_rx,
                        "neck_rx": neck,
                        "min": round(min(lows.values()), 2),
                        "worst": min(lows.items(), key=lambda kv: kv[1])[0],
                        "watch": {k: round(lows.get(k, 999.0), 1) for k in WATCH},
                    })
    print("E09_TERM2 %s" % json.dumps(rows, ensure_ascii=False))
    print("E09_TERM2_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E09_TERM2_FAILURE " + traceback.format_exc())
