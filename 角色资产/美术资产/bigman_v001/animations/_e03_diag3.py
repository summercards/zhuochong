"""_e03_diag3 —— E03 捶胸的「穿透到底是哪一块肉」定点解剖（只读，不改工程）。

背景：门禁实测「贴胸时手网格最小带符号距离 = −36.3 mm（L/R 近乎一致）」，
但**网格最小距离**说不出穿进去的是「指节」还是「蜷起来的指尖」。
这两者的观感完全不同：
  · 指节压进胸肌 ⟹ 正常的「捶」的观感（挤压）；
  · 指尖戳进胸腔 ⟹ 穿模，必须修。
所以必须把穿透点**逐顶点**调出来看：属于哪个对象、离拳心多远、
沿胸法线方向偏出去多少。

同时量三个候选 `TOUCH_OFF` 下的一组真值，供主脚本标定：
    贴胸核心 = 拳心(`hand.tail`) 到胸面的带符号距离
    拳面 = 该侧手网格顶点到胸面的最小带符号距离
目标：让「拳面」落在 −6 ~ +2 mm（指节刚压住胸面），而不是现在这样
由 `TOUCH_OFF=38 mm` 推出来的 −36 mm。

运行：
    "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" \\
      --background --factory-startup --python _e03_diag3.py
"""

import json
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_rage as R         # noqa: E402

SIDES = ("L", "R")


def torso_eval():
    deps = bpy.context.evaluated_depsgraph_get()
    ev = R.TORSO.evaluated_get(deps)
    return ev, ev.matrix_world.copy()


def signed(point):
    ev, mw = torso_eval()
    ok, loc, nrm, _i = ev.closest_point_on_mesh(mw.inverted() @ Vector(point))
    wl = mw @ loc
    wn = (mw.to_3x3() @ nrm).normalized()
    return (Vector(point) - wl).dot(wn) * 1000.0, wl, wn


def hand_verts(side):
    """[(世界坐标, 对象名)] —— 不降采样。"""
    deps = bpy.context.evaluated_depsgraph_get()
    out = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or not obj.name.endswith("_" + side):
            continue
        if not any(obj.name.startswith(p) for p in R.HAND_PREFIX):
            continue
        ev = obj.evaluated_get(deps)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for v in me.vertices:
            out.append((mw @ v.co, obj.name))
        ev.to_mesh_clear()
    return out


def report_pose(arm, action, frame, label):
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    bpy.context.scene.frame_set(frame)
    bpy.context.view_layer.update()
    row = {"label": label, "frame": frame}
    for side in SIDES:
        core = Vector(A.bone_world(arm, "hand." + side, "tail"))
        core_gap, surf, nrm = signed(core)
        verts = hand_verts(side)
        scored = []
        for point, name in verts:
            gap, wl, _wn = signed(point)
            scored.append((gap, point, name, wl))
        scored.sort(key=lambda item: item[0])
        deepest = scored[:6]
        # 拳心到胸面的法线方向上的「拳肉厚度」：最深点在法线上的投影
        spread = [-(p - core).dot(nrm) * 1000.0 for _g, p, _n, _wl in scored]
        spread.sort()
        row[side] = {
            "core_gap_mm": round(core_gap, 2),
            "surface_mm": [round(v * 1000.0, 1) for v in surf],
            "normal": [round(v, 4) for v in nrm],
            "mesh_min_mm": round(scored[0][0], 2),
            "vert_count": len(scored),
            "radius_p50_mm": round(spread[len(spread) // 2], 1),
            "radius_p90_mm": round(spread[int(len(spread) * 0.90)], 1),
            "radius_p98_mm": round(spread[int(len(spread) * 0.98)], 1),
            "radius_max_mm": round(spread[-1], 1),
            "deepest": [
                {"gap_mm": round(g, 2), "obj": n,
                 "from_core_mm": round((p - core).length * 1000.0, 1),
                 "proj_core_to_normal_mm": round(-(p - core).dot(nrm) * 1000.0,
                                                 1),
                 "world_mm": [round(v * 1000.0, 1) for v in p]}
                for g, p, n, _wl in deepest],
        }
    print("E03_ANATOMY " + json.dumps(row, ensure_ascii=False))
    return row


def main():
    arm, _meshes = R.boot()
    keyframes = [(f, R.rage_pose(arm, f)) for f in range(R.START, R.END + 1)]
    keyframes = R.compat_euler(keyframes)
    action, _meta = A.build_action(arm, R.NAME, keyframes, {"loop": False})
    for win in (R.HOLD_1, R.HOLD_2):
        A.set_hitstop(action, win[0], win[1])

    # 站架基线（不打帧，直接读 STA 姿态）
    for frame in (0, 20, 26, 27, 28, 36, 44, 46, 48, 52, 60, 66):
        report_pose(arm, action, frame, "contact/approach")
    print("E03_DIAG3_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E03_DIAG3_FAILURE " + traceback.format_exc())
