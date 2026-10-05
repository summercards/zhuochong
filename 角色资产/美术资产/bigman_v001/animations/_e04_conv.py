"""_e04_conv —— 只读：量 `lock_feet` **收敛后**（最后一次迭代）的踝残差，
并回答一个 E04 专属问题：**下沉时「全网格最低点」为什么会往下走？**

`probe_e04_baseline` 报的 `lock_err_mm` 是 8 次迭代里的**最差值**（含第 1 次的
大修正），不能用来判「这个下沉量腿够不够得到」。本脚本量**末次**残差。

★ 第二个问题（本脚本要回答的）：
  探针里 `mesh_box()`（**全部**网格）在 dz=0 时最低 −0.96 mm，到 dz=−400 变成
   −3.51 mm。可 `lock_feet` 把**踝**钉死了、`keep_world_orientation` 又把**脚**
   的世界朝向钉回 rest ⟹ 鞋**不该**动。所以「−0.96 → −3.51」一定来自**另一块网格**
   （或被蒙皮到 shin 的那部分鞋面）。本脚本逐对象量：
     · `sole_shoe_mm`  = 只用 4 个鞋对象（即门禁 `foot_lowest_by_side` 的口径）
     · `mesh_low_mm`   = 全部网格的最低点
     · `low_obj`       = 那个最低点属于**哪个对象**（回答「到底谁在往下走」）
"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as IDLE   # noqa: E402

SIDES = ("L", "R")


def lock_feet_final(arm, pose, want, iters=40, damp=0.85):
    tgt = {s: Vector(want[s]) for s in SIDES}
    rz = {s: pose.get("thigh." + s, (0.0, 0.0, 0.0))[2] for s in SIDES}
    pelvis_rx = pose.get("pelvis", (0.0, 0.0, 0.0))[0]
    last = 0.0
    for _it in range(iters):
        A.apply_pose(arm, pose)
        for side in SIDES:
            hip = Vector(A.bone_world(arm, "thigh." + side, "head"))
            th, sh = A.leg_ik(hip.y, hip.z, tgt[side].y, tgt[side].z,
                              tilt_deg=pelvis_rx)
            pose["thigh." + side] = (th, 0.0, rz[side])
            pose["shin." + side] = (sh, 0.0, 0.0)
        A.apply_pose(arm, pose)
        for side in SIDES:
            pose["foot." + side] = A.keep_world_orientation(arm, "foot." + side)
        A.apply_pose(arm, pose)
        last = 0.0
        for side in SIDES:
            err = Vector(A.bone_world(arm, "foot." + side, "head")) - want[side]
            tgt[side] = tgt[side] - err * damp
            rz[side] = rz[side] + (1.0 / 0.01309) * err.x * damp
            last = max(last, err.length * 1000.0)
    return last


def build(base, anchor, dz=0.0, foot_lift=0.0, tilts=None):
    pose = {}
    for key, value in base.items():
        pose[key] = ({k: tuple(v) for k, v in value.items()}
                     if key.startswith("@") else tuple(value))
    for name, delta in (tilts or {}).items():
        cur = pose.get(name, (0.0, 0.0, 0.0))
        pose[name] = (cur[0] + delta, cur[1], cur[2])
    base_loc = pose.get("@loc", {}).get("pelvis", (0.0, 0.0, 0.0))
    off = A.wloc(0.0, 0.0, dz)
    pose["@loc"] = {"pelvis": tuple(a + b for a, b in zip(base_loc, off))}
    want = {s: Vector(anchor[s]) + Vector((0.0, 0.0, foot_lift)) for s in SIDES}
    return pose, want


def lowest_obj():
    """返回 (最低 z 米, 对象名) —— 全部网格。"""
    dg = bpy.context.evaluated_depsgraph_get()
    best = (1e9, None)
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        mw = ev.matrix_world
        for v in me.vertices:
            z = (mw @ v.co).z
            if z < best[0]:
                best = (z, obj.name)
        ev.to_mesh_clear()
    return best


def main():
    arm, _m = A.open_animation_project()
    A.setup_scene()
    base = IDLE.idle_pose(arm, 0.0)
    A.apply_pose(arm, base)
    anchor = {s: Vector(A.bone_world(arm, "foot." + s, "head")) for s in SIDES}

    rows = []
    for dz in (0.0, -0.10, -0.16, -0.20, -0.24, -0.28, -0.32, -0.36,
               -0.40, 0.02, 0.046, 0.06):
        pose, want = build(base, anchor, dz=dz)
        fin = lock_feet_final(arm, pose, want)
        sole = A.foot_lowest_by_side()
        low_z, low_obj = lowest_obj()
        knee = max(math.degrees(arm.pose.bones["shin." + s].rotation_euler.x)
                   for s in SIDES)
        rows.append({"dz_mm": round(dz * 1000.0, 1),
                     "final_err_mm": round(fin, 5),
                     "knee_deg": round(knee, 2),
                     "sole_shoe_mm": round(min(sole["L"][2], sole["R"][2])
                                           * 1000.0, 2),
                     "mesh_low_mm": round(low_z * 1000.0, 2),
                     "low_obj": low_obj})
    print("E04_CONV " + str(rows).replace("'", '"'))

    # 腾空段：踝抬升 + 骨盆同步（脚随体），确认腿不超伸
    air = []
    for dz, lift in ((0.046, 0.0), (0.10, 0.06), (0.20, 0.14), (0.30, 0.24),
                     (0.40, 0.40), (0.42, 0.52), (0.30, 0.34), (0.15, 0.16),
                     (0.02, 0.02), (-0.10, 0.0)):
        pose, want = build(base, anchor, dz=dz, foot_lift=lift)
        fin = lock_feet_final(arm, pose, want)
        hip = Vector(A.bone_world(arm, "thigh.L", "head"))
        ank = Vector(A.bone_world(arm, "foot.L", "head"))
        sole = A.foot_lowest_by_side()
        knee = max(math.degrees(arm.pose.bones["shin." + s].rotation_euler.x)
                   for s in SIDES)
        air.append({"dz_mm": round(dz * 1000.0, 1),
                    "lift_mm": round(lift * 1000.0, 1),
                    "final_err_mm": round(fin, 5),
                    "hip_ankle_mm": round((hip - ank).length * 1000.0, 2),
                    "knee_deg": round(knee, 2),
                    "sole_min_mm": round(min(sole["L"][2],
                                             sole["R"][2]) * 1000.0, 2)})
    print("E04_AIR " + str(air).replace("'", '"'))


try:
    main()
except Exception:  # noqa: BLE001
    import traceback
    print("E04_CONV_FAILURE " + traceback.format_exc())
