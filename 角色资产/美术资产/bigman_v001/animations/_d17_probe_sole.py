"""D17 一次性探针：鞋底穿透到底归谁 —— 脚（`foot`）还是小腿（`shin`）？

`Shoe_Heel` / `Shoe_Sole` 同时绑 `foot` 与 `shin` ⟹ 二者之一的世界 3×3 偏一点，
鞋底就动。本探针逐帧做**受控替换**：
  (a) 现状；
  (b) 把 `shin` 的世界 3×3 强钉成 `Idle_01@0`（只动旋转）再看鞋底。
若 (b) 回到 ≈ −0.96，则穿透的载体是 **shin 的滚转**，不是 foot。
"""
import sys
import os
import math

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector, Quaternion  # noqa: E402
import anim_getup_f as G  # noqa: E402
import anim_lib as A  # noqa: E402

arm, meshes = G.boot()
G.JS._PREV_EULER.clear()
G.UE.CARRY_Q.clear()
A.apply_pose(arm, G.ZERO)
bpy.context.view_layer.update()
for name in G.ARM_BONES + G.LEG_BONES:
    G.UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
for name, value in G.ZERO.items():
    if not name.startswith("@"):
        G.JS._PREV_EULER[name] = tuple(value)


def shoe():
    return G._foot_clearance()


def shin_err(side):
    m = arm.pose.bones["shin." + side].matrix.to_3x3()
    e = G.END_BASIS["shin." + side]

    q = m.to_quaternion()
    base = Quaternion(e)
    if q.dot(base) < 0.0:
        base.negate()
    return math.degrees(q.rotation_difference(base).angle)


for f in (17, 18, 19, 20, 21, 22, 25, 30, 33, 34):
    A.apply_pose(arm, G.solve_pose(arm, f, meshes))
    bpy.context.view_layer.update()
    s0 = shoe()
    e0 = {s: round(shin_err(s), 2) for s in G.SIDES}
    # (b) 强钉 shin 世界 3×3（只动旋转）
    for side in G.SIDES:
        pb = arm.pose.bones["shin." + side]
        target = Quaternion(G.END_BASIS["shin." + side]).to_matrix().to_4x4()
        target.translation = pb.matrix.translation
        pb.matrix = target
    bpy.context.view_layer.update()
    s1 = shoe()
    e1 = {s: round(shin_err(s), 2) for s in G.SIDES}
    print("P f=%2d  shoe0=(%s,%s)  shinerr=%s  ->  shoe1=(%s,%s) shinerr=%s"
          % (f,
             "None" if s0["L"] is None else round(s0["L"] * 1000, 2),
             "None" if s0["R"] is None else round(s0["R"] * 1000, 2),
             e0,
             "None" if s1["L"] is None else round(s1["L"] * 1000, 2),
             "None" if s1["R"] is None else round(s1["R"] * 1000, 2),
             e1))
