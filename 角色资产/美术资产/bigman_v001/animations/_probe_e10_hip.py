"""_probe_e10_hip —— 量清「骨盆 → 髋」的真实几何（E10 腿链设计的地基）。

为什么要单独量：`anim_death.py` 的腿目标要以**髋**为基准插值，就必须先知道
髋相对骨盆的真实偏移（是不是 (0.09, 0, −0.41)），以及站架/仰卧两态下的
髋—踝向量。凭"想当然"推错过一次（推出 |髋→踝| = 0.09 m，腿折成两折）。
"""
import json
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A              # noqa: E402
import anim_idle_01 as IDLE       # noqa: E402
import probe_e10_baseline as PB   # noqa: E402

TERM_KW = dict(pz=0.141, leg_dz=-0.06, foot_pitch=-15.0, foot_roll=45.0,
               arm_out=0.50, arm_fwd=0.10, wrist_z=0.055,
               neck_rx=-14.0, head_rx=-11.0, prx=-86.0)

NAMES = ("pelvis", "thigh.L", "shin.L", "foot.L", "toe.L",
         "thigh.R", "shin.R", "foot.R", "toe.R", "chest", "head")


def dump(tag, arm):
    row = {}
    for n in NAMES:
        if n not in arm.pose.bones:
            continue
        row[n] = [round(v * 1000.0, 2) for v in A.bone_world(arm, n, "head")]
        row[n + "/tail"] = [round(v * 1000.0, 2) for v in A.bone_world(arm, n,
                                                                      "tail")]
    for s in ("L", "R"):
        hip = Vector(A.bone_world(arm, "thigh." + s, "head"))
        ank = Vector(A.bone_world(arm, "foot." + s, "head"))
        row["vec." + s] = [round(v * 1000.0, 2) for v in (ank - hip)]
        row["len." + s] = round((ank - hip).length * 1000.0, 2)
    print("E10HIP_%s %s" % (tag, json.dumps(row, ensure_ascii=False)))
    return row


def main():
    arm, _meshes = A.open_animation_project()
    A.setup_scene()

    # ---- 骨骼 rest 几何（armature 空间 = 世界，若对象无变换）----------------
    bones = arm.data.bones
    geom = {}
    for n in ("pelvis", "thigh.L", "thigh.R", "shin.L", "foot.L", "spine_01"):
        if n in bones:
            b = bones[n]
            geom[n] = {
                "parent": b.parent.name if b.parent else None,
                "head_local": [round(v * 1000.0, 2) for v in b.head_local],
                "tail_local": [round(v * 1000.0, 2) for v in b.tail_local],
                "length": round(b.length * 1000.0, 3),
            }
    print("E10HIP_GEOM %s" % json.dumps(geom, ensure_ascii=False))
    m = arm.matrix_world
    print("E10HIP_XFORM %s" % json.dumps({
        "translation": [round(v * 1000.0, 3) for v in m.translation],
        "scale": [round(v, 6) for v in m.to_scale()],
        "rot_deg": [round(v, 4) for v in m.to_euler()],
    }, ensure_ascii=False))

    A.apply_pose(arm, {})
    dump("ZERO", arm)

    A.apply_pose(arm, IDLE.idle_pose(arm, 0.0))
    dump("IDLE0", arm)

    PB.build_supine(arm, **TERM_KW)
    dump("SUPINE", arm)
    print("E10HIP_DONE")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("E10HIP_FAILURE " + traceback.format_exc())
