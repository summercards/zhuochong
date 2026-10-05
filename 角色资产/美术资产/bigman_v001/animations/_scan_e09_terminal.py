"""_scan_e09_terminal —— 为 E09 `Defeat` 找**躺地终点**（伏地）的几何。

★ 为什么不用 `Knockdown_F@20` 现成俯卧：实测它 **`Trouser_R` 陷地 61.54 mm**
  （`Trouser_L` −11.31 mm）—— D14 的贴地判据只盯**鞋底**，躯干/腿的陷地**从未被任何
  判据盯过**（SOUL 铁律："没有任何判据盯着的约束等于不存在"）。
  直接复用会把一处未被验收的缺陷带进 E09 ⟹ 本支**自己立终点**，并用
  **逐件贴地判据** `dft_body_ground_ok` 守住。

扫描维度（几何推导，不是乱调）：
  * 躯干总俯仰 `pitch` 分布在 pelvis/spine_01/spine_02/chest；
  * 骨盆世界 z `pz`（身体多低）；
  * 大腿 `thigh_rx = 90 − pitch` ⟹ **大腿指向世界 +Y 水平向后**（腿平躺）；
  * 膝屈 `shin_rx`；踝 `foot_rx`。

运行：blender --background --factory-startup --python _scan_e09_terminal.py
"""

import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402

WATCH = ("Suit_Torso", "Trouser_L", "Trouser_R", "Shoe_Sole_L", "Shoe_Sole_R",
         "Shoe_Upper_L", "Shoe_Upper_R", "Hand_Palm_L", "Hand_Palm_R",
         "Head", "Hair_Mass", "Jacket_Hem")


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
    for pitch in (70.0, 78.0, 86.0):
        for pz in (0.16, 0.20, 0.24):
            for shin_rx in (0.0, 8.0):
                for foot_rx in (0.0, 35.0):
                    pelvis_rx = pitch * 0.80
                    rest = pitch * 0.20 / 3.0
                    pose = {
                        "pelvis": (pelvis_rx, 0.0, 0.0),
                        "spine_01": (rest, 0.0, 0.0),
                        "spine_02": (rest, 0.0, 0.0),
                        "chest": (rest, 0.0, 0.0),
                        "neck": (8.0, 0.0, 0.0),
                        "head": (6.0, 0.0, 14.0),
                        "shoulder.L": (-18.0, 0.0, 0.0),
                        "shoulder.R": (-18.0, 0.0, 0.0),
                        "thigh.L": (90.0 - pelvis_rx, 0.0, -8.0),
                        "shin.L": (shin_rx, 0.0, 0.0),
                        "foot.L": (foot_rx, 0.0, 0.0),
                        "toe.L": (0.0, 0.0, 0.0),
                        "thigh.R": (90.0 - pelvis_rx, 0.0, 8.0),
                        "shin.R": (shin_rx, 0.0, 0.0),
                        "foot.R": (foot_rx, 0.0, 0.0),
                        "toe.R": (0.0, 0.0, 0.0),
                        "@loc": {"pelvis": A.wloc(0.0, 0.0, pz - 0.900)},
                    }
                    pose.update(A.FIST)
                    A.apply_pose(arm, pose)
                    lows = per_object_lows()
                    rows.append({
                        "pitch": pitch, "pz": pz, "shin_rx": shin_rx,
                        "foot_rx": foot_rx,
                        "pelvis_z": round(
                            A.bone_world(arm, "pelvis", "head").z * 1000.0, 1),
                        "knee_z": round(
                            A.bone_world(arm, "shin.L", "head").z * 1000.0, 1),
                        "min": round(min(lows.values()), 2),
                        "worst": min(lows.items(), key=lambda kv: kv[1])[0],
                        "watch": {k: round(lows.get(k, 999.0), 1) for k in WATCH},
                    })
    print("E09_TERM_SCAN %s" % json.dumps(rows, ensure_ascii=False))
    print("E09_TERM_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E09_TERM_FAILURE " + traceback.format_exc())
