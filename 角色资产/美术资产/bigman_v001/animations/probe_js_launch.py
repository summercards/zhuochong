"""probe_js_launch —— 扫蹬地几何，找 `no_teleport` 的可行域。

判据来源：腿接近伸直时膝角对"髋-踝距离"极敏感（dθ/dd = 1/(L·sin(θ/2))），
而蹬地末帧髋升得最快 ⟹ 膝伸展速率尖峰。可动的量只有三个：
  · TAKEOFF_PELVIS_Z / LAUNCH_RISE  —— 抬得越高，腿越接近伸直，越敏感
  · 踮脚角 TIP_TAKEOFF 与它的时序   —— 踝也跟着升就少伸一点
  · LAUNCH_POW                      —— 末帧速率 = p·Δ/T
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
    return arm


def set_launch(top, pow_, tip, tip_keys):
    JS.TAKEOFF_PELVIS_Z = top
    JS.LAUNCH_RISE = top - JS.CROUCH_PELVIS_Z
    JS.LAUNCH_POW = pow_
    JS.TAKEOFF_SPEED = pow_ * JS.LAUNCH_RISE / JS.LAUNCH_FRAMES
    JS.APEX_RISE = JS.TAKEOFF_SPEED ** 2 / (2.0 * JS.G_PER_FRAME)
    JS.TIP_TAKEOFF = tip
    JS.TIP_KEYS = tip_keys
    for s in ("L", "R"):
        piv, rest = JS.PIVOT_FWD[s], JS.ANKLE_REST[s]
        z0 = rest.z + JS.Z_OFF[s]
        t = math.radians(tip)
        JS.TAKEOFF_ANKLE_Z[s] = piv * math.sin(t) + z0 * math.cos(t)
        JS.TAKEOFF_VERT[s] = top - JS.TAKEOFF_ANKLE_Z[s]


def trial(arm, top, pow_, tip, tip_keys):
    set_launch(top, pow_, tip, tip_keys)
    I1.idle_pose(arm, 0.0)
    JS._PREV_EULER.clear()
    for n, v in I1.idle_pose(arm, 0.0).items():
        if not n.startswith("@"):
            JS._PREV_EULER[n] = tuple(v)
    JS.ARM_QUAT.clear()
    for n in JS.ARM_BONES:
        JS.ARM_QUAT[n] = arm.pose.bones[n].matrix.to_quaternion()
    prev, worst, w_at, tail, bones = {}, 0.0, None, [], None
    prev = {n: tuple(v) for n, v in JS._PREV_EULER.items()}
    for f in range(1, JS.TOTAL + 1):
        pose = JS.build_pose(arm, f)
        if bones is None:
            bones = [n for n in pose if not n.startswith("@")]
        step, at = 0.0, None
        for n in bones:
            cur = pose.get(n)
            if cur is None:
                continue
            s = max(abs(x - y) for x, y in zip(cur, prev.get(n, cur)))
            if s > step:
                step, at = s, n
        if step > worst:
            worst, w_at = step, (f, at)
        for n in bones:
            if n in pose:
                prev[n] = tuple(pose[n])
        tail.append(round(step, 3))
    mono = all(tail[i + 1] <= tail[i] + 1e-9
               for i in range(len(tail) - 6, len(tail) - 1))
    knee = JS.CR.knee_series
    return {"top_mm": round(top * 1000), "pow": pow_, "tip": tip,
            "avg_mm": round(JS.LAUNCH_RISE / JS.LAUNCH_FRAMES * 1000, 1),
            "v_end_mps": round(JS.TAKEOFF_SPEED * 60, 2),
            "apex_m": round(JS.APEX_RISE, 3),
            "max_step": round(worst, 2), "at": w_at,
            "tail_ok": mono}


arm = setup()
TK_A = ((0, 0.0), (14, 0.0), (17, 8.0), (20, 29.0), (24, 27.0), (28, 21.0),
        (32, 16.0), (36, 12.0))
TK_B = ((0, 0.0), (14, 0.0), (16, 14.0), (18, 30.0), (20, 44.0), (24, 30.0),
        (28, 22.0), (32, 16.0), (36, 12.0))
for combo in ((0.920, 1.5, 29.0, TK_A),
              (0.920, 1.5, 44.0, TK_B),
              (0.900, 1.5, 44.0, TK_B),
              (0.880, 1.5, 44.0, TK_B),
              (0.880, 1.3, 44.0, TK_B),
              (0.880, 1.1, 44.0, TK_B)):
    A.report("JSLAUNCH", trial(arm, *combo))
