"""probe_js_branch —— 判定"单帧欧拉跳变"是**真旋转**还是**表示分支跳**。

依据：`mathutils.Quaternion.angle` 不保证返回 [0,180]，`rotation_difference`
可能给出"绕远路"的四元数（角 >180）。所以先测**世界旋转的真实测地角**
（min(ang, 360-ang)），再对比 euler 分支。

对照三条：
  raw    —— aim_bone / aim_frame 直接交给 Blender 反解（当前实现）
  wrap   —— 手写 ±360 折算（当前 _unwrap）
  compat —— Blender 的相容欧拉 matrix_basis.to_euler('XYZ', prev)
"""
import math, os, sys
import bpy
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A
import anim_idle_01 as I1
import anim_jump_start as JS


def geo(a, b):
    """真实测地角（度）—— 把 rotation_difference 的"绕远路"折回来。"""
    q = a.to_quaternion().rotation_difference(b.to_quaternion())
    ang = math.degrees(q.angle)
    return min(ang, 360.0 - ang)


def wrap(prev, e):
    out = []
    for p, v in zip(prev, e):
        while v - p > 180.0:
            v -= 360.0
        while v - p < -180.0:
            v += 360.0
        out.append(v)
    return tuple(out)


def run(arm, mode):
    I1.idle_pose(arm, 0.0)
    prev_e = {n: tuple(math.degrees(v)
                       for v in arm.pose.bones[n].rotation_euler)
              for n in JS.ARM_BONES}
    prev_r = {n: arm.pose.bones[n].matrix.to_3x3().copy() for n in JS.ARM_BONES}
    worst_e, worst_r = 0.0, 0.0
    at_e = at_r = None
    worst_flip = 0.0
    for frame in range(1, JS.TOTAL + 1):
        JS.build_pose(arm, frame)
        dirs = JS.arm_dirs(frame)
        for name in JS.ARM_BONES:
            pb = arm.pose.bones[name]
            JS.aim_frame(arm, name, dirs[name], JS.ARM_REF[name])
            raw = tuple(math.degrees(v) for v in pb.rotation_euler)
            if mode == "raw":
                e = raw                      # 完全不处理（首版行为）
            elif mode == "wrap":
                e = wrap(prev_e[name], raw)  # 手写 ±360
                for i, v in enumerate(e):
                    pb.rotation_euler[i] = math.radians(v)
                bpy.context.view_layer.update()
            else:                            # compat
                ec = pb.matrix_basis.to_3x3().to_euler(
                    "XYZ", Euler(prev_e[name], "XYZ"))
                pb.rotation_euler = ec
                bpy.context.view_layer.update()
                e = tuple(math.degrees(v) for v in ec)
            step = max(abs(x - y) for x, y in zip(e, prev_e[name]))
            rot = geo(prev_r[name], pb.matrix.to_3x3())
            if step > worst_e:
                worst_e, at_e = step, (frame, name)
            if rot > worst_r:
                worst_r, at_r = rot, (frame, name)
            # 量"同一物理姿态在两种表示下差多少"：raw 与 compat 的欧拉差
            flip = max(abs(x - y) for x, y in zip(raw, prev_e[name]))
            worst_flip = max(worst_flip, flip)
            prev_e[name] = e
            prev_r[name] = pb.matrix.to_3x3().copy()
    return {"mode": mode, "max_euler_step": round(worst_e, 2), "at": at_e,
            "max_true_world_rot_step": round(worst_r, 2), "rot_at": at_r,
            "raw_vs_prev_max": round(worst_flip, 2)}


arm, _ = A.open_animation_project()
A.setup_scene()
I1.idle_pose(arm, 0.0)
JS.ANKLE_REST = {s: Vector(A.bone_world(arm, "foot." + s, "head"))
                 for s in ("L", "R")}
JS.ARM_REF = JS.arm_refs(arm)
JS.PIVOT_FWD = JS.measure_pivot(arm)
JS.Z_OFF, _ = JS.calibrate(arm)
for s in ("L", "R"):
    piv, rest = JS.PIVOT_FWD[s], JS.ANKLE_REST[s]
    z0 = rest.z + JS.Z_OFF[s]
    tip = math.radians(JS.TIP_TAKEOFF)
    JS.TAKEOFF_ANKLE_Z[s] = piv * math.sin(tip) + z0 * math.cos(tip)
    JS.TAKEOFF_VERT[s] = JS.TAKEOFF_PELVIS_Z - JS.TAKEOFF_ANKLE_Z[s]
I1.idle_pose(arm, 0.0)
for mode in ("raw", "wrap", "compat"):
    A.report("JSBRANCH", run(arm, mode))
