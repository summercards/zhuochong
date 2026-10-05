"""_e03_twist —— 扫「手骨自转」把拇指从胸腔里转出来（只读，不写工程）。

`_e03_diag3.py` 的结论：贴胸时穿透的**不是拳面，是拇指** ——
    拳心(`hand.tail`) 到胸面 +38 mm 时，拇指网格已经进到 −36 mm，
    而拇指离拳心 101.5 mm、沿胸法线偏出 88.4 mm；
    同一姿态下掌根簇离拳心只有 12 mm。
⟹ 问题在**手的朝向**（`A.aim_bone` 只做最小旋转、不管滚转），
   不在打击深度。

本脚本扫 `HAND_TWIST ∈ [−180, 180] step 15`，对**贴胸帧(28)**量：
    · 全手网格到胸面的最小带符号距离（要 ≥ ~0，越小越穿）
    · **拇指**网格的最小带符号距离（穿模的真凶）
    · **非拇指**（掌/指）最小带符号距离（这才是「拳压下去多深」）
并顺带记录该 twist 下拳心到胸面的距离（应恒 = TOUCH_OFF，用于自检）。

另渲 4 个候选 twist 的正面 + 3/4 静帧到 `previews/anim/_e03_twist/`，
由人眼复核「拳头是拿指节砸胸，还是拿拇指戳胸」。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_twist.py
    E03_TWIST_RENDER=1  额外渲图
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
FRAME = 28
SHOULD_RENDER = os.environ.get("E03_TWIST_RENDER") == "1"


def torso_eval():
    deps = bpy.context.evaluated_depsgraph_get()
    ev = R.TORSO.evaluated_get(deps)
    return ev, ev.matrix_world.copy()


def signed(point):
    ev, mw = torso_eval()
    _ok, loc, nrm, _i = ev.closest_point_on_mesh(mw.inverted() @ Vector(point))
    wl = mw @ loc
    wn = (mw.to_3x3() @ nrm).normalized()
    return (Vector(point) - wl).dot(wn) * 1000.0


def part_verts(side, kind):
    deps = bpy.context.evaluated_depsgraph_get()
    out = []
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
        out += [mw @ v.co for v in me.vertices]
        ev.to_mesh_clear()
    return out


def measure(arm, twist):
    R.HAND_TWIST = {"L": twist, "R": twist}
    pose = R.rage_pose(arm, FRAME)
    A.apply_pose(arm, pose)
    bpy.context.view_layer.update()
    row = {"twist": twist}
    for side in SIDES:
        core = Vector(A.bone_world(arm, "hand." + side, "tail"))
        row[side] = {
            "core_gap_mm": round(signed(core), 2),
            "all_min_mm": round(min(signed(p)
                                      for p in part_verts(side, "all")), 2),
            "thumb_min_mm": round(min(signed(p)
                                        for p in part_verts(side, "thumb")), 2),
            "palm_min_mm": round(min(signed(p)
                                       for p in part_verts(side, "palm")), 2),
        }
    return row


def main():
    arm, _meshes = R.boot()
    rows = []
    for twist in list(range(-180, 181, 15)):
        rows.append(measure(arm, twist))
    for row in rows:
        print("E03_TWIST " + json.dumps(row, ensure_ascii=False))

    ranked = sorted(rows, key=lambda r: -(min(r["L"]["thumb_min_mm"],
                                              r["L"]["palm_min_mm"],
                                              r["R"]["thumb_min_mm"],
                                              r["R"]["palm_min_mm"])))
    print("E03_TWIST_BEST " + json.dumps(
        [r["twist"] for r in ranked[:6]], ensure_ascii=False))

    if SHOULD_RENDER:
        out = os.path.join(A.PREVIEW_DIR, "_e03_twist")
        candidates = [0] + [r["twist"] for r in ranked[:3]]
        for twist in candidates:
            R.HAND_TWIST = {"L": twist, "R": twist}
            pose = R.rage_pose(arm, FRAME)
            # ★ 必须解绑 Action：否则 `render.render` 会按绑定的 Action 重算姿态，
            #   把手工摆的姿态整个盖掉（E03 首版踩过这个坑）。
            if arm.animation_data is not None:
                arm.animation_data.action = None
            A.apply_pose(arm, pose)
            bpy.context.view_layer.update()
            camera = bpy.data.objects["Presentation_Camera"]
            for view in (R.VIEW_E03_FRONT, A.VIEW_3Q):
                name, loc, tgt, scale, res = view
                path = os.path.join(out, "twist%+04d_%s.png" % (twist, name))
                A.render_still(camera, path, loc, tgt, scale, res)
        print("E03_TWIST_RENDER_DONE " + out)


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_TWIST_FAILURE " + traceback.format_exc())
