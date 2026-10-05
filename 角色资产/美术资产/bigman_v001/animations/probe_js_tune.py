"""probe_js_tune —— 定位 28.3°/帧 的骨与帧，并扫"摆臂窗口 × 摆幅"。

产出每个组合的：手臂最大单帧欧拉步、出现在哪一帧哪根骨、
以及末 6 帧（f30→36）**全体**骨的最大步（`decel_smooth_ok` 的输入）。
"""
import math, os, sys
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A
import anim_idle_01 as I1
import anim_jump_start as JS


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
    return arm


def trial(arm, swing_end, back_amp, up_amp):
    # 摆幅缩放：把极值姿态按 slerp 从护体拉回来
    JS.ARM_BACK = {k: JS._slerp(I1.ARM_DIRS[k], JS.ARM_BACK_RAW[k], back_amp)
                   for k in I1.ARM_DIRS}
    JS.ARM_UP = {k: JS._slerp(I1.ARM_DIRS[k], JS.ARM_UP_RAW[k], up_amp)
                 for k in I1.ARM_DIRS}
    JS.T_SWING_END = swing_end
    I1.idle_pose(arm, 0.0)
    JS._PREV_EULER.clear()
    for n, v in I1.idle_pose(arm, 0.0).items():
        if not n.startswith("@"):
            JS._PREV_EULER[n] = tuple(v)
    JS.ARM_QUAT.clear()
    for n in JS.ARM_BONES:
        JS.ARM_QUAT[n] = arm.pose.bones[n].matrix.to_quaternion()
    prev = {n: tuple(JS._PREV_EULER[n]) for n in JS.ARM_BONES}
    worst, w_at, tail = 0.0, None, []
    all_bones = None
    for f in range(1, JS.TOTAL + 1):
        pose = JS.build_pose(arm, f)
        if all_bones is None:
            all_bones = [n for n in pose if not n.startswith("@")]
        step, at = 0.0, None
        for n in all_bones:
            cur = pose.get(n)
            if cur is None:
                continue
            s = max(abs(x - y) for x, y in zip(cur, prev.get(n, cur)))
            if s > step:
                step, at = s, n
        if step > worst:
            worst, w_at = step, (f, at)
        for n in all_bones:
            if n in pose:
                prev[n] = tuple(pose[n])
        tail.append(round(step, 3))
    mono = all(tail[i + 1] <= tail[i] + 1e-9 for i in range(len(tail) - 6,
                                                         len(tail) - 1))
    return {"swing_end": swing_end, "back_amp": back_amp, "up_amp": up_amp,
            "arm_max_euler_step": round(worst, 2), "at": w_at,
            "tail_max": tail[-6:], "tail_monotone": mono}


arm = setup()
JS.ARM_BACK_RAW = dict(JS.ARM_BACK)
JS.ARM_UP_RAW = dict(JS.ARM_UP)
for combo in ((30, 1.0, 1.0), (32, 1.0, 1.0), (34, 1.0, 1.0),
              (32, 0.85, 1.0), (34, 0.85, 0.9)):
    A.report("JSTUNE", trial(arm, *combo))
