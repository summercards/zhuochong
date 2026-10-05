"""probe_c11_belt —— 只读：在 C11 `Skill_03` 语境下复核「不跟随骨架」的网格对象。

背景：C01 时代 `probe_belt.py` 已查清，模型里有两个**未蒙皮**对象
（`Jacket_Hem` 251x23 mm、`Jacket_Hem_Line` 246x4 mm，均 `vgroups=0`、
无 armature 父级）—— 它们在世界里恒定不动，而 C01 整角色移动近 1 m，
于是侧视图腰后露出一根"横插的薄片"。

本支（C11）是 C 族第一支「世界朝向变化」：骨盆 yaw 累计 390° + 位移，
身体会**转走**，薄片留在原处 ⟹ 相对位置变化比 C01 更大。本探针回答三件事：

① 未蒙皮对象是否仍是那 2 个（没多、没少）—— 即「查无回归」；
② 它们的世界位姿在整段动画里是否**逐位恒定**（证明与本支姿态无关）；
③ 它们的高度区间是否与腰带同高（解释侧视图里那根薄片的来路）。

判据是**事实核对**，不是门槛：只要是那 2 个对象、且跨帧逐位不变，
就说明渲染里的薄片属**模型侧遗留**，与 `anim_skill03.py` 的姿态无关。
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
import anim_lib as A  # noqa: E402

ACTION = os.environ.get("C11_BELT_ACTION", "Skill_03")
FRAMES = (0, 16, 33, 46, 104)


def world_bounds(obj):
    pts = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    return lo, hi


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()
    scene = bpy.context.scene

    action = bpy.data.actions.get(ACTION)
    if action is None:
        print("BELT11 no action %s (现有 %s)"
              % (ACTION, [a.name for a in bpy.data.actions]))
        return
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    # 只认「既没有顶点组、又没有任何 armature 祖先」的网格 ——
    # 这类对象原理上不可能被骨骼带动，世界位姿必定恒定。
    unbound = []
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        has_arm_parent = False
        node = obj.parent
        while node is not None:
            if node.type == "ARMATURE":
                has_arm_parent = True
                break
            node = node.parent
        if obj.vertex_groups or has_arm_parent:
            continue
        unbound.append(obj)

    print("BELT11_UNBOUND_COUNT %d" % len(unbound))

    rows = []
    for obj in unbound:
        rec = {"name": obj.name,
               "vgroups": len(obj.vertex_groups),
               "parent": obj.parent.name if obj.parent else None,
               "mods": [m.type for m in obj.modifiers],
               "bbox_mm": {}}
        for frame in FRAMES:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            lo, hi = world_bounds(obj)
            rec["bbox_mm"][str(frame)] = [
                round(v * 1000.0, 2) for v in (lo + hi)]
        vals = list(rec["bbox_mm"].values())
        rec["constant"] = all(v == vals[0] for v in vals)
        rec["size_mm"] = [round(vals[0][i + 3] - vals[0][i], 1)
                          for i in range(3)]
        rows.append(rec)
    print("BELT11_UNBOUND " + json.dumps(rows, ensure_ascii=False))

    # 对照组：确定蒙皮的躯干 —— 用来证明"薄片不动"不是场景没刷新。
    ref = bpy.data.objects.get("Suit_Torso")
    if ref is not None:
        refrows = []
        for frame in FRAMES:
            scene.frame_set(frame)
            bpy.context.view_layer.update()
            lo, hi = world_bounds(ref)
            refrows.append({"f": frame,
                            "lo": [round(v * 1000.0, 2) for v in lo],
                            "hi": [round(v * 1000.0, 2) for v in hi]})
        print("BELT11_REF " + json.dumps(refrows, ensure_ascii=False))

    names = sorted(r["name"] for r in rows)
    expected = ["Jacket_Hem", "Jacket_Hem_Line"]
    print("BELT11_NO_REGRESSION %s" % (
        "True" if names == expected else "False (%s)" % names))
    print("BELT11_DONE")


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("BELT11_FAILURE " + traceback.format_exc())
