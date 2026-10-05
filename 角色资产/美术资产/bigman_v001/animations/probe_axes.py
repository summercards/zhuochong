"""probe_axes —— 标定 bigman_v001 rig 的**局部轴语义**。

为什么必须先做这一步：
    pose bone 的 `rotation_euler[i]` 是**骨骼局部**坐标，而 57 根骨的静止朝向
    各不相同 —— 腿骨朝下(-Z)、臂骨朝 ±X、脊椎朝上(+Z)、手指朝外(+X)。
    同一句 `rotation_euler[0] = 0.3` 落在不同骨上，是完全不同的动作。

    凭想象推断"哪根轴是屈伸"在这个项目上已经错过一次（眉型那次是读字面，
    这次会是读几何）。所以让 Blender 自己回答：对每根骨**绕单轴转 15°**，
    实测其末端在世界空间里往哪个方向走了多少毫米。表出来了，写姿态就不猜。

输出：
    doc/rig_axis_map.md   —— 人读的标定表
    animations/axis_map.json —— 机读，供 anim_lib 与后续动画脚本引用

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \
      --background --factory-startup --python probe_axes.py
"""

import json
import math
import os

import bpy

OUT_DIR = os.path.abspath(
    r"I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001")
BLEND_PATH = os.path.join(OUT_DIR, "bigman_tpose_v001.blend")
DOC_PATH = os.path.join(OUT_DIR, "doc", "rig_axis_map.md")
JSON_PATH = os.path.join(OUT_DIR, "animations", "axis_map.json")

ANGLE_DEG = 15.0
ANGLE = math.radians(ANGLE_DEG)

# 只看主控骨 + 一根代表指 —— 57 根全扫表太长，且指骨同构，
# index_01 的结果对 middle/ring/pinky 直接适用。
GROUPS = (
    ("躯干", ("root", "pelvis", "spine_01", "spine_02", "chest", "neck",
              "head", "jaw")),
    ("左臂", ("shoulder.L", "upperarm.L", "forearm.L", "hand.L",
              "index_01.L", "thumb_01.L")),
    ("右臂", ("shoulder.R", "upperarm.R", "forearm.R", "hand.R",
              "index_01.R", "thumb_01.R")),
    ("左腿", ("thigh.L", "shin.L", "foot.L", "toe.L")),
    ("右腿", ("thigh.R", "shin.R", "foot.R", "toe.R")),
)

AXIS_LABELS = ("X", "Y", "Z")


def clear_pose(arm):
    for pose_bone in arm.pose.bones:
        pose_bone.rotation_euler = (0.0, 0.0, 0.0)
        pose_bone.location = (0.0, 0.0, 0.0)
        pose_bone.scale = (1.0, 1.0, 1.0)
    bpy.context.view_layer.update()


def tail_world(arm, name):
    return arm.matrix_world @ arm.pose.bones[name].tail


def describe(vector):
    """把位移向量翻成"左/右/前/后/上/下"的拼词。"""
    pairs = ((abs(vector.x), "左" if vector.x > 0 else "右"),
             (abs(vector.y), "后" if vector.y > 0 else "前"),
             (abs(vector.z), "上" if vector.z > 0 else "下"))
    ranked = sorted(pairs, key=lambda item: -item[0])
    if ranked[0][0] < 1e-6:
        return "—"
    text = ranked[0][1]
    if ranked[1][0] >= ranked[0][0] * 0.45 and ranked[1][0] > 1e-6:
        text = ranked[0][1] + ranked[1][1]
    return text


def main():
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
    arm = bpy.data.objects["Character_Rig"]

    table = {}
    rows = []
    for group_name, bones in GROUPS:
        rows.append(("group", group_name))
        for name in bones:
            if name not in arm.pose.bones:
                rows.append(("missing", name))
                continue
            clear_pose(arm)
            base = tail_world(arm, name)
            entry = {"group": group_name}
            for index, axis in enumerate(AXIS_LABELS):
                clear_pose(arm)
                euler = [0.0, 0.0, 0.0]
                euler[index] = ANGLE
                arm.pose.bones[name].rotation_euler = euler
                bpy.context.view_layer.update()
                moved = tail_world(arm, name) - base
                delta = [round(v * 1000.0, 2) for v in moved]
                entry[axis] = {
                    "delta_mm": delta,
                    "travel_mm": round(moved.length * 1000.0, 2),
                    "dir": describe(moved),
                }
            table[name] = entry
            rows.append(("bone", name, entry))

    clear_pose(arm)

    os.makedirs(os.path.dirname(DOC_PATH), exist_ok=True)
    with open(JSON_PATH, "w", encoding="utf-8") as handle:
        json.dump({"angle_deg": ANGLE_DEG, "bones": table}, handle,
                  ensure_ascii=False, indent=2)

    lines = [
        "# bigman_v001 骨架轴向语义标定表",
        "",
        "> 由 `animations/probe_axes.py` 自动生成，**不要手改**。",
        "> 口径：每根骨单独绕局部 %g° 旋转，实测末端（tail）在世界空间的位移。" % ANGLE_DEG,
        "> 坐标约定：+X = 角色左，+Y = 角色身后，+Z = 上，角色正面朝 −Y。",
        "",
        "| 骨 | 轴 | Δ(mm) dx,dy,dz | 位移量 | 方向 |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        if row[0] == "group":
            lines.append("| **%s** | | | | |" % row[1])
            continue
        if row[0] == "missing":
            lines.append("| %s | — | 骨骼不存在 | | |" % row[1])
            continue
        name, entry = row[1], row[2]
        for axis in AXIS_LABELS:
            item = entry[axis]
            lines.append("| `%s` | %s | %s | %g mm | %s |" % (
                name, axis, ", ".join("%g" % v for v in item["delta_mm"]),
                item["travel_mm"], item["dir"]))
    with open(DOC_PATH, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    print("AXIS_MAP_BONES %d" % len(table))
    for group_name, bones in GROUPS:
        for name in bones:
            entry = table.get(name)
            if entry is None:
                print("AXIS %s MISSING" % name)
                continue
            parts = []
            for axis in AXIS_LABELS:
                item = entry[axis]
                parts.append("%s:%s(%gmm)" % (axis, item["dir"], item["travel_mm"]))
            print("AXIS %-14s %s" % (name, "  ".join(parts)))
    print("AXIS_MAP_DOC " + DOC_PATH)


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("AXIS_MAP_FAILURE " + traceback.format_exc())
