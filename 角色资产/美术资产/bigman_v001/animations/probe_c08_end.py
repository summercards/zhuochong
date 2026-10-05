# -*- coding: utf-8 -*-
"""C08 末帧校验（只读）：片段末帧是否真的走到了登记的 `end_pose_deg`。

背景：初版 `TOTAL=100` 而 `SETTLE=104` / `CANCEL=106` —— 两个标记落在片段区间
之外，`end_pose_deg` 登记的「半蹲戒备」其实只走到 q=0.919。渲染 f104 与 f100
逐像素相同就是现场的指纹。本脚本量末帧实测值，与登记值对账。

    blender --background --factory-startup --python probe_c08_end.py
"""
import os
import sys
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy                                                    # noqa: E402
from mathutils import Vector as V3                            # noqa: E402
import anim_lib as A                                          # noqa: E402
import anim_charge08 as C08                                   # noqa: E402

CHAIN = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
         "shoulder.L", "shoulder.R")


def main():
    arm, _meshes = A.open_animation_project()
    action = bpy.data.actions.get(C08.NAME)
    if action is None:
        print("C08END 缺 %s" % C08.NAME)
        return
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    scene = bpy.context.scene

    print("C08END frames=%s settle=%d cancel=%d total=%d"
          % (list(action.frame_range), C08.SETTLE, C08.CANCEL, C08.TOTAL))
    print("C08END markers=%s"
          % [(m.name, m.frame) for m in action.pose_markers])

    for frame in (C08.HIT, C08.HOLD_END, C08.RETURN_START,
                  C08.SETTLE - 1, C08.SETTLE, C08.CANCEL, C08.TOTAL):
        if frame > C08.TOTAL:
            continue
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        row = {b.name: [round(math.degrees(v), 3)
                        for v in bpy.context.active_object.pose.bones[
                            b.name].rotation_euler]
               for b in arm.pose.bones if b.name in CHAIN}
        pelvis = V3(A.bone_world(arm, "pelvis", "head"))
        head_dir = V3(A.bone_world(arm, "head", "tail")) \
            - V3(A.bone_world(arm, "head", "head"))
        pitch = math.degrees(math.asin(max(-1.0, min(1.0, head_dir.z))))
        fist = V3(A.bone_world(arm, "hand.L", "tail"))
        print("C08END f%03d q=%.4f chain=%s pelvis_z=%.1f head_pitch=%.1f "
              "fist_L=%s"
              % (frame, C08.q_of(frame),
                 {k: v[0] for k, v in row.items()},
                 pelvis.z * 1000.0, pitch,
                 [round(v * 1000.0, 1) for v in fist]))

    # 与登记值对账
    scene.frame_set(C08.TOTAL)
    bpy.context.view_layer.update()
    bad = []
    for name, want in C08.END_ROT.items():
        got = [math.degrees(v)
               for v in arm.pose.bones[name].rotation_euler]
        for c in range(3):
            if abs(got[c] - want[c]) > 0.05:
                bad.append((name, c, round(got[c], 3), want[c]))
    print("C08END_MISMATCH %s" % bad)
    print("C08END_OK %s" % (not bad))

    # 末 6 帧是否逐位静止（`no_snap_stop` 的另一半：落定后可混出）
    prev = None
    for frame in range(C08.SETTLE, C08.TOTAL + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        cur = {b.name: tuple(b.rotation_euler) for b in arm.pose.bones}
        if prev is not None:
            step = max(max(abs(a - b) for a, b in zip(prev[n], cur[n]))
                       for n in cur)
            print("C08END_TAIL f%03d step_deg=%.6f" % (frame,
                                                      math.degrees(step)))
        prev = cur


main()
