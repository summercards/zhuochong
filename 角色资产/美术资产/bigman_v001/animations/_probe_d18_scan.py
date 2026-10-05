"""临时探针：扫描 D18 的 ARCH_SCALE / HEEL_PEAK / PELVIS_Z@HAND_OFF。

不进渲染、不存盘、不跑门禁 —— 只回答两件事：
  ① `chest_rise = chest_tail[HAND_OFF] - chest_tail[PLANT]` 对拱起缩放/骨盆曲线的灵敏度；
  ② `sole_min(f ∈ [FOOT_SET, END])` 对抬跟峰值的灵敏度。
用完即删。
"""
import os
import sys
import json
import bpy
from mathutils import Vector

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import anim_getup_b as D          # noqa: E402
import anim_lib as A              # noqa: E402
import anim_jump_start as JS      # noqa: E402
import anim_ultimate_end as UE    # noqa: E402

arm, meshes = D.boot()


def measure():
    """按 f = 0..TOTAL 逐帧求解，返回 (chest_tail 逐帧 z, 鞋底逐帧 z)。"""
    JS._PREV_EULER.clear()
    UE.CARRY_Q.clear()
    D.LOCK_POSE.clear()
    D._LOCK_REUSED[0] = 0
    A.apply_pose(arm, D.ZERO)
    bpy.context.view_layer.update()
    for name in D.ARM_BONES + D.LEG_BONES:
        UE.CARRY_Q[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    for name, value in D.ZERO.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    ct, sole = {}, {}
    for f in range(0, D.TOTAL + 1):
        A.apply_pose(arm, D.solve_pose(arm, f, meshes))
        bpy.context.view_layer.update()
        ct[f] = Vector(A.bone_world(arm, "chest", "tail")).z * 1000.0
        low = D._foot_clearance()
        sole[f] = min(v for v in (low["L"], low["R"]) if v is not None) * 1000.0
    return ct, sole


BASE_Z = D.PELVIS_Z_KEYS
BASE_HEEL = D.HEEL_LIFT_PEAK_DEG

for arch in (0.85, 0.92, 1.00, 1.08, 1.15):
    D.ARCH_SCALE = arch
    D.HEEL_LIFT_PEAK_DEG = BASE_HEEL
    ct, sole = measure()
    print("SCAN_ARCH " + json.dumps({
        "arch": arch,
        "ct_plant": round(ct[D.PLANT], 2),
        "ct_handoff": round(ct[D.HAND_OFF], 2),
        "chest_rise": round(ct[D.HAND_OFF] - ct[D.PLANT], 2),
    }))

D.ARCH_SCALE = 1.0

for heel in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0):
    D.HEEL_LIFT_PEAK_DEG = heel
    ct, sole = measure()
    win = [sole[f] for f in range(D.FOOT_SET, D.TOTAL + 1)]
    print("SCAN_HEEL " + json.dumps({
        "heel": heel,
        "sole25": round(sole[D.FOOT_SET], 2),
        "sole_min": round(min(win), 2),
        "sole_max": round(max(win), 2),
    }))

D.HEEL_LIFT_PEAK_DEG = BASE_HEEL

for zoff in (0.0, 20.0, 40.0, 60.0):
    D.ARCH_SCALE = 1.0
    D.PELVIS_Z_KEYS = tuple((f, z + (zoff if f >= D.HAND_OFF else 0.0))
                            for f, z in BASE_Z)
    ct, sole = measure()
    print("SCAN_PZ " + json.dumps({
        "zoff": zoff,
        "ct_plant": round(ct[D.PLANT], 2),
        "ct_handoff": round(ct[D.HAND_OFF], 2),
        "chest_rise": round(ct[D.HAND_OFF] - ct[D.PLANT], 2),
        "pz_handoff": round(Vector(A.bone_world(arm, "pelvis", "head")).z, 3),
    }))

D.PELVIS_Z_KEYS = BASE_Z
print("SCAN_DONE")
