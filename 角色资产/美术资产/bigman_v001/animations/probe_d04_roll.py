"""probe_d04_roll —— 只读：把 D 族（防御族）各支动画的**绕骨轴滚转**摊开对比。

为什么单独做这个探针：
    D04 第 1 次渲染实测发现：`end_world_pose_mm` **0.0009 mm**（骨根/骨尖逐位对齐零位），
    但渲染画面 f60 与 f0 差 **3 px**。补测"世界旋转基"口径后查出真因 ——
    手臂骨绕**自身轴**滚了 **30.5°**（`forearm.L`/`hand.L`），而骨根/骨尖一动没动
    ⟹ **位置口径发现不了它**（D02 教训 1 的镜像）。
    这与 D03 报告里"遗留问题 —— `hand.R` 的 18° 零空间滚转"是同一个现象。

本探针对每支动画量三件事：
    ① `f0` 与 `last` 的世界旋转基差（最差骨）—— 「本支自己有没有漂」；
    ② `last` 与 **零位**（`Guard_Start` 末帧）的世界旋转基差 —— 「接回 `Guard_Loop`
       会不会跳」（这才是引擎侧真正关心的量）；
    ③ `f0` 与零位的差 —— 「接缝是否干净」。

用法（纯只读，不改任何文件）：
  "D:/Program Files/Blender Foundation/Blender 4.5/blender.exe" --background \
      --factory-startup --python probe_d04_roll.py
"""
import json
import math
import os
import sys

import bpy
from mathutils import Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anim_lib as A  # noqa: E402

ZERO_ACTION = "Guard_Start"
TARGETS = ("Guard_Start", "Guard_Loop", "Guard_Hit", "Guard_Break")
# 只看躯干 + 双臂（腿由位置 IK 钉死、脚已单独门禁）
WATCH = ("pelvis", "spine_01", "spine_02", "chest", "neck", "head",
         "shoulder.L", "shoulder.R",
         "upperarm.L", "upperarm.R", "forearm.L", "forearm.R",
         "hand.L", "hand.R")


def _bind(arm, action):
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)


def basis_map(arm):
    out = {}
    for name in WATCH:
        if name in arm.pose.bones:
            out[name] = arm.pose.bones[name].matrix.to_3x3().to_quaternion()
    return out


def compare(a, b):
    worst, worst_bone = 0.0, None
    per = {}
    for name in set(a) & set(b):
        dot = abs(max(-1.0, min(1.0, a[name].dot(b[name]))))
        gap = math.degrees(2.0 * math.acos(dot))
        if gap > 0.05:
            per[name] = round(gap, 3)
        if gap > worst:
            worst, worst_bone = gap, name
    return round(worst, 3), worst_bone, per


def main():
    bpy.ops.wm.open_mainfile(filepath=A.ANIM_BLEND)
    arm = bpy.data.objects.get(A.ARM_NAME)
    if arm is None:
        for obj in bpy.data.objects:
            if obj.type == "ARMATURE":
                arm = obj
                break
    scene = bpy.context.scene

    zero = bpy.data.actions.get(ZERO_ACTION)
    if zero is None:
        print("ROLL_PROBE NO_ZERO_ACTION %s" % ZERO_ACTION)
        return
    _bind(arm, zero)
    scene.frame_set(int(zero.frame_range[1]))
    bpy.context.view_layer.update()
    ref = basis_map(arm)

    rows = {}
    for name in TARGETS:
        action = bpy.data.actions.get(name)
        if action is None:
            rows[name] = {"found": False}
            continue
        _bind(arm, action)
        scene.frame_set(int(action.frame_range[0]))
        bpy.context.view_layer.update()
        first = basis_map(arm)
        scene.frame_set(int(action.frame_range[1]))
        bpy.context.view_layer.update()
        last = basis_map(arm)
        d_first_last, b_first_last, per_first_last = compare(first, last)
        d_last_zero, b_last_zero, per_last_zero = compare(last, ref)
        d_first_zero, b_first_zero, _ = compare(first, ref)
        rows[name] = {
            "found": True,
            "frames": [int(v) for v in action.frame_range],
            "roll_f0_vs_last_deg": d_first_last,
            "roll_f0_vs_last_bone": b_first_last,
            "roll_f0_vs_last_bones": per_first_last,
            "roll_last_vs_zero_deg": d_last_zero,
            "roll_last_vs_zero_bone": b_last_zero,
            "roll_last_vs_zero_bones": per_last_zero,
            "roll_f0_vs_zero_deg": d_first_zero,
            "roll_f0_vs_zero_bone": b_first_zero,
        }
    print("ROLL_PROBE " + json.dumps(rows, ensure_ascii=False))
    print("ROLL_PROBE_NOTE " + json.dumps({
        "zero_ref": "%s@%d" % (ZERO_ACTION, int(zero.frame_range[1])),
        "watch_bones": len(WATCH),
        "meaning": ("roll_last_vs_zero_deg = 引擎从本支末帧切回 Guard_Loop 时"
                    "袖子/拳套的瞬时旋转量"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
