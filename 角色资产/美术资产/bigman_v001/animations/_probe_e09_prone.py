"""_probe_e09_prone —— 单独复核 `Knockdown_F@20`（拟作 E09 末帧的「躺地终点」）的
**逐对象最低点**，确认它到底哪个件最贴近地面、有没有陷地。

为什么要单独复核：`probe_e09_baseline` 给出的全身最低点是 **−61.54 mm**，
而 D14 日志登记的只有**鞋底** −1.24 mm ⟹ 必须查清那 −61.5 是**哪个网格**，
否则把它当末帧就是把一处未被人盯过的陷地带进 E09。
"""

import json
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A  # noqa: E402


def main():
    arm, meshes = A.open_animation_project()
    A.setup_scene()
    target = os.environ.get("KDF_ACTION", "Knockdown_F")
    frame = int(os.environ.get("KDF_FRAME", "20"))
    action = bpy.data.actions.get(target)
    if action is None:
        print("KDF_MISSING %s" % target)
        return
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    lows = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        matrix = evaluated.matrix_world
        low = min((matrix @ v.co).z for v in mesh.vertices)
        lows.append((low * 1000.0, obj.name))
        evaluated.to_mesh_clear()
    lows.sort()
    print("KDF_LOWEST %s" % json.dumps(
        [[round(z, 2), n] for z, n in lows[:14]], ensure_ascii=False))
    print("KDF_FRAME_MIN %.2f" % lows[0][0])
    print("KDF_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("KDF_FAILURE " + traceback.format_exc())
