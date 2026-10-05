"""bigman_v001 —— 骨架形变实测（导出前门禁）。

不信任"绑定代码跑通了"：真的转控制骨，量网格顶点位移，再复位。
判据：每根被测骨都必须让对应网格产生位移，且残差（复位后）归零。

输出 RIG_CHECK {json}
"""

import json
import sys

OUT_DIR = r"I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001"
if OUT_DIR not in sys.path:
    sys.path.insert(0, OUT_DIR)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

# (骨名, 绕哪个轴, 角度, 期望跟随的网格前缀, 期望位移下限 m)
CASES = (
    ("upperarm.L", 2, 0.60, ("Sleeve_L",), 0.080),
    ("forearm.L", 2, 0.50, ("Sleeve_L",), 0.020),
    ("thigh.L", 0, 0.50, ("Trouser_L",), 0.100),
    ("shin.L", 0, 0.50, ("Trouser_L",), 0.050),
    ("head", 0, 0.40, ("Hair_Mass", "Head"), 0.030),
    ("jaw", 2, 0.25, ("Lower_Lip",), 0.002),
    ("hand.L", 2, 0.50, ("Hand_Palm_L",), 0.030),
    ("index_01.L", 2, 0.50, ("Finger_Index_L",), 0.004),
)


def depsgraph_eval(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    mesh = ev.to_mesh()
    coords = [v.co.copy() for v in mesh.vertices]
    ev.to_mesh_clear()
    return coords


def snapshot(names):
    out = {}
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            out[name] = depsgraph_eval(obj)
    return out


def max_delta(a, b):
    if not a:
        return 0.0
    return max((p - q).length for p, q in zip(a, b)) if a else 0.0


def main():
    arm = bpy.data.objects.get("Character_Rig")
    if arm is None:
        print("RIG_CHECK " + json.dumps({"ok": False,
                                         "error": "Character_Rig 不存在"}))
        return
    watch = sorted({n for _, _, _, pre, _ in CASES for n in pre})
    base = snapshot(watch)

    results = []
    ok = True
    for bone_name, axis, angle, prefixes, floor in CASES:
        pb = arm.pose.bones.get(bone_name)
        if pb is None:
            results.append({"bone": bone_name, "ok": False,
                            "error": "骨不存在"})
            ok = False
            continue

        for p in arm.pose.bones:
            p.rotation_mode = "XYZ"
            p.rotation_euler = (0.0, 0.0, 0.0)
        bpy.context.view_layer.update()

        rot = [0.0, 0.0, 0.0]
        rot[axis] = angle
        pb.rotation_euler = tuple(rot)
        bpy.context.view_layer.update()

        moved = {}
        for name in watch:
            if not any(name.startswith(pre) for pre in prefixes):
                continue
            cur = depsgraph_eval(bpy.data.objects[name])
            moved[name] = round(max_delta(base[name], cur), 5)

        peak = max(moved.values()) if moved else 0.0
        passed = bool(moved) and peak >= floor
        ok = ok and passed
        results.append({"bone": bone_name, "peak_m": peak, "floor_m": floor,
                        "followed": sorted(moved), "ok": passed})

    # 复位 + 残差核验
    for p in arm.pose.bones:
        p.rotation_mode = "XYZ"
        p.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()
    residual = 0.0
    for name in watch:
        cur = depsgraph_eval(bpy.data.objects[name])
        residual = max(residual, max_delta(base[name], cur))
    residual = round(residual, 6)
    ok = ok and residual < 1e-5

    print("RIG_CHECK " + json.dumps(
        {"ok": ok, "residual_m": residual, "cases": results},
        ensure_ascii=False))


main()
