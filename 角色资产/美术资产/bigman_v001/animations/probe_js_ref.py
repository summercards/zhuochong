"""probe_js_ref —— 给 A10 的手臂定位"单帧欧拉跳变"的真正根因，并选参数。

根因假设：`aim_bone` 的 Q = rotation_difference(F·ŷ, want)。F 是**父链带过来的
静止朝向**。手臂大角度甩动时 F·ŷ 会与 want 接近**反平行**，此时最小旋转的解
病态（转轴不确定）⟹ 骨的局部欧拉爆掉。

本探针逐帧输出：
  · 每根臂骨的 euler（解缠后）、**世界旋转测地角**变化、**方向**变化
  · 上一帧→本帧的 Q 转角（= F·ŷ 与 want 的夹角），找它接近 180° 的帧
  · 参考与方向的 max|cos|（越大越接近退化）
并对若干"甩臂幅度"取值扫描，看 no_teleport 是否随幅度线性下降。
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A          # noqa: E402
import anim_idle_01 as I1     # noqa: E402
import anim_jump_start as JS  # noqa: E402


def aim(arm, name, direction, ref):
    pb = arm.pose.bones[name]
    y = Vector(direction).normalized()
    r = Vector(ref)
    x = r - y * r.dot(y)
    if x.length < 1e-6:
        fb = Vector((0.0, 0.0, 1.0))
        x = fb - y * fb.dot(y)
    x.normalize()
    m = Matrix((x, y, x.cross(y))).transposed().to_4x4()
    m.translation = pb.matrix.translation
    pb.matrix = m
    bpy.context.view_layer.update()
    return tuple(math.degrees(v) for v in pb.rotation_euler)


def dir_of(arm, name):
    return (arm.pose.bones[name].matrix.to_3x3()
            @ Vector((0.0, 1.0, 0.0))).normalized()


def rot3(arm, name):
    return arm.pose.bones[name].matrix.to_3x3().copy()


def geo_deg(a, b):
    q = a.to_quaternion().rotation_difference(b.to_quaternion())
    return math.degrees(q.angle)


def setup():
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
    return arm


def unwrap(prev, e):
    out = []
    for p, v in zip(prev, e):
        while v - p > 180.0:
            v -= 360.0
        while v - p < -180.0:
            v += 360.0
        out.append(v)
    return tuple(out)


def scan(arm, scale, mode, trace=False):
    """scale：甩臂幅度（1.0 = ARM_DIRS↔ARM_BACK/UP 全行程）。"""
    I1.idle_pose(arm, 0.0)
    ref0 = {n: (arm.pose.bones[n].matrix.to_3x3() @ Vector((1.0, 0.0, 0.0)))
            for n in JS.ARM_BONES}
    prev_e = {n: tuple(math.degrees(v)
                       for v in arm.pose.bones[n].rotation_euler)
              for n in JS.ARM_BONES}
    prev_r = {n: rot3(arm, n) for n in JS.ARM_BONES}
    prev_d = {n: dir_of(arm, n) for n in JS.ARM_BONES}
    worst = 0.0
    worst_at = None
    worst_rot = 0.0
    worst_rot_at = None
    worst_q = 0.0
    max_cos = 0.0
    for frame in range(1, JS.TOTAL + 1):
        JS.build_pose(arm, frame)
        a = JS.TURN.track(JS.ARM_A, frame) * scale
        base = (I1.ARM_DIRS, JS.ARM_UP) if a >= 0.0 else (I1.ARM_DIRS, JS.ARM_BACK)
        t = abs(a)
        dirs = {k: JS._nlerp(base[0][k], base[1][k], t) for k in I1.ARM_DIRS}
        for name in JS.ARM_BONES:
            want = Vector(dirs[name]).normalized()
            if mode == "orig":
                pb = arm.pose.bones[name]
                pb.rotation_euler = (0.0, 0.0, 0.0)
                bpy.context.view_layer.update()
                cur = pb.matrix.copy()
                cur_dir = (cur.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()
                q_ang = math.degrees(cur_dir.angle(want))
                worst_q = max(worst_q, q_ang)
                e = A.aim_bone(arm, name, dirs[name])
            else:
                ref = ref0[name]
                max_cos = max(max_cos, abs(want.dot(Vector(ref).normalized())))
                e = aim(arm, name, dirs[name], ref)
            e = unwrap(prev_e[name], e)
            step = max(abs(x - y) for x, y in zip(e, prev_e[name]))
            rot = geo_deg(prev_r[name], rot3(arm, name))
            if frame == 1:
                step *= 1.0
            if step > worst:
                worst, worst_at = step, (frame, name)
            if rot > worst_rot:
                worst_rot, worst_rot_at = rot, (frame, name)
            if trace and frame <= 12 and name == "forearm.R":
                A.report("JSTRACE", {
                    "f": frame, "euler": [round(v, 2) for v in e],
                    "step": round(step, 2), "worldrot": round(rot, 2),
                    "dir": round(math.degrees(
                        prev_d[name].angle(dir_of(arm, name))), 2),
                    "q_ang": round(q_ang if mode == "orig" else -1, 2)})
            prev_e[name], prev_r[name] = e, rot3(arm, name)
            prev_d[name] = dir_of(arm, name)
    return {"scale": scale, "mode": mode, "max_euler_step": round(worst, 2),
            "at": worst_at, "max_world_rot_step": round(worst_rot, 2),
            "rot_at": worst_rot_at, "max_q_deg": round(worst_q, 2),
            "max_ref_cos": round(max_cos, 3)}


arm = setup()
for _scale in (1.0, 0.7, 0.5):
    A.report("JSSCAN", scan(arm, _scale, "orig"))
A.report("JSSCAN", scan(arm, 1.0, "fixed", trace=True))
