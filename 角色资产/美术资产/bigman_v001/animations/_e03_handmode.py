"""_e03_handmode —— 扫 4 种「手的摆法」，用实测挑出不像「拿拇指戳胸」的那一种。

`_e03_diag3.py` 的结论：贴胸时穿透的**不是拳面，是拇指**（拇指离拳心 101.5 mm、
沿胸法线偏出 88.4 mm；而掌/指簇离拳心只有 12 mm）⟹ 这是**手的朝向**问题。
`_e03_handaxis.py` 量出 `hand.L/R` 的 rest 基语义（`local_y`=骨长轴、
`local_x`=拇指侧、`local_z`=上，右手系）⟹ 可以用**显式骨基**摆出手的朝向。

本脚本对 `HAND_AXIS_MODES` 的 4 种摆法，在**全部关键帧**上量：
    · 全手网格到胸面的最小带符号距离（要 ≥ −8 mm）
    · 拇指网格的最小带符号距离（真凶）
    · 非拇指（掌/指）最小带符号距离（这才是「拳压多深」）
并渲染正面 + 3/4 特写供目视复核。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_handmode.py
    E03_MODE_RENDER=1  额外渲图
"""

import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_rage as R         # noqa: E402

SIDES = ("L", "R")
FRAMES = (28, 31, 34, 38, 44, 46, 52, 56, 66)
SHOULD_RENDER = os.environ.get("E03_MODE_RENDER") == "1"


def signed(point):
    return R.signed_to_torso(point)


def part_min(side, kind):
    deps = bpy.context.evaluated_depsgraph_get()
    best, obj_name = 1e9, None
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not any(obj.name.startswith(p) for p in R.HAND_PREFIX):
            continue
        is_thumb = obj.name.startswith("Thumb_")
        if kind == "thumb" and not is_thumb:
            continue
        if kind == "palm" and is_thumb:
            continue
        ev = obj.evaluated_get(deps)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for v in me.vertices:
            gap = signed(mw @ v.co)
            if gap < best:
                best, obj_name = gap, obj.name
        ev.to_mesh_clear()
    return best, obj_name


def main():
    arm, _meshes = R.boot()
    results = {}
    for mode in R.HAND_AXIS_MODES:
        R.HAND_AXIS_MODE = mode
        R.LAST_ELBOW.clear()
        frames = {}
        for frame in FRAMES:
            R.LAST_ELBOW.clear()          # 每个关键帧独立解，避免跨帧污染
            pose = R.rage_pose(arm, frame)
            A.apply_pose(arm, pose)
            bpy.context.view_layer.update()
            row = {}
            for side in SIDES:
                thumb, thumb_obj = part_min(side, "thumb")
                palm, palm_obj = part_min(side, "palm")
                core = signed(Vector(A.bone_world(arm, "hand." + side, "tail")))
                row[side] = {
                    "thumb_mm": round(thumb, 2), "thumb_obj": thumb_obj,
                    "palm_mm": round(palm, 2), "palm_obj": palm_obj,
                    "core_mm": round(core, 2),
                    "all_mm": round(min(thumb, palm), 2),
                }
            frames[str(frame)] = row
        worst_thumb = min(row[s]["thumb_mm"] for row in frames.values()
                          for s in SIDES)
        worst_all = min(row[s]["all_mm"] for row in frames.values()
                        for s in SIDES)
        results[mode] = {
            "worst_thumb_mm": round(worst_thumb, 2),
            "worst_all_mm": round(worst_all, 2),
            "frames": frames,
        }
        print("E03_MODE " + json.dumps(
            {"mode": mode, "worst_thumb_mm": round(worst_thumb, 2),
             "worst_all_mm": round(worst_all, 2)}, ensure_ascii=False))

    ranked = sorted(results.items(), key=lambda kv: -kv[1]["worst_all_mm"])
    print("E03_MODE_RANK " + json.dumps(
        [(k, v["worst_all_mm"]) for k, v in ranked], ensure_ascii=False))

    for mode in R.HAND_AXIS_MODES:
        detail = results[mode]["frames"]
        print("E03_MODE_DETAIL %s %s" % (mode, json.dumps(
            {f: {s: [v[s]["thumb_mm"], v[s]["palm_mm"], v[s]["core_mm"]]
                 for s in SIDES} for f, v in detail.items()})))

    if SHOULD_RENDER:
        out = os.path.join(A.PREVIEW_DIR, "_e03_handmode")
        os.makedirs(out, exist_ok=True)
        camera = bpy.data.objects["Presentation_Camera"]
        close = ("chest_close", (2.6, -3.0, 1.45), (0.0, -0.16, 1.16), 0.85,
                 (900, 900))
        for mode in R.HAND_AXIS_MODES:
            R.HAND_AXIS_MODE = mode
            R.LAST_ELBOW.clear()
            pose = R.rage_pose(arm, 28)
            if arm.animation_data is not None:
                arm.animation_data.action = None
            A.apply_pose(arm, pose)
            bpy.context.view_layer.update()
            for view in (R.VIEW_E03_FRONT, close):
                name, loc, tgt, scale, res = view
                path = os.path.join(out, "%s_%s.png" % (mode, name))
                A.render_still(camera, path, loc, tgt, scale, res)
        print("E03_MODE_RENDER_DONE " + out)

    print("E03_MODE_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_MODE_FAILURE " + traceback.format_exc())
