# -*- coding: utf-8 -*-
"""实测每个攻击动画在命中帧的**攻击肢端世界坐标**。

用途：格斗游戏的判定盒位置。资产里 `hit_point_m` 属性基本是空的，
所以这里不猜 —— 直接把骨架摆到命中帧，读肢端骨骼的位置。

输出（Blender 世界坐标，与人形属性一致）：
    x = 角色左手侧, y = 角色背后（**前向 = -y**）, z = 上
    前进距离 reach_m = -y
    高度     height_m = z

用法:
    blender --background --factory-startup <anim.blend> --python measure_hit_points.py -- <out.json>
"""
import bpy
import json
import os
import sys

# 可能作为攻击端的骨骼
LIMBS = {
    "punch": ["hand.L", "hand.R"],
    "kick": ["foot.L", "foot.R", "toe.L", "toe.R"],
    "shoulder": ["shoulder.L", "shoulder.R"],
    "elbow": ["forearm.L", "forearm.R"],
}
ALL_PROBES = [b for v in LIMBS.values() for b in v]


def prop(act, key, default=None):
    if key not in act.keys():
        return default
    v = act[key]
    if hasattr(v, "to_list"):
        return v.to_list()
    return v


def norm_int(v):
    """把 4.0 / '4' / None 统一成 int 或 None。"""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(round(v))
    if isinstance(v, str):
        try:
            return int(round(float(v)))
        except ValueError:
            return None
    return None


def hit_frames_of(act):
    """收集该 Action 的全部命中帧（单个或数组）。"""
    out = []
    multi = prop(act, "hit_frames")
    if isinstance(multi, list):
        for x in multi:
            i = norm_int(x)
            if i is not None:
                out.append(i)
    if not out:
        i = norm_int(prop(act, "hit_frame"))
        if i is not None:
            out.append(i)
    return sorted(set(out))


def main():
    argv = sys.argv
    out_path = argv[argv.index("--") + 1] if "--" in argv else None

    arm = None
    for o in bpy.data.objects:
        if o.type == "ARMATURE":
            arm = o
            break
    if arm is None:
        print("MEASURE_FAIL 场景里没有骨架")
        return

    scene = bpy.context.scene
    if arm.animation_data is None:
        arm.animation_data_create()

    report = {
        "armature": arm.name,
        "fps": scene.render.fps / (scene.render.fps_base or 1.0),
        "note": "Blender 世界坐标: +x=左手侧, +y=背后(前向=-y), +z=上; reach_m = -y, height_m = z",
        "clips": {},
    }

    for act in sorted(bpy.data.actions, key=lambda a: a.name):
        frames = hit_frames_of(act)
        if not frames:
            continue
        arm.animation_data.action = act
        rec = {"code": str(prop(act, "anim_id", act.name)), "hit_frames": frames, "samples": []}
        for f in frames:
            scene.frame_set(f)
            bpy.context.view_layer.update()
            poses = {}
            for p in ALL_PROBES:
                pb = arm.pose.bones.get(p)
                if pb is None:
                    continue
                w = arm.matrix_world @ pb.tail
                poses[p] = [round(w.x, 4), round(w.y, 4), round(w.z, 4)]

            # 找出各肢体类别里"最靠前"（y 最小）的那一只
            best = {}
            for kind, names in LIMBS.items():
                cand = [(p, poses[p]) for p in names if p in poses]
                if not cand:
                    continue
                p, w = min(cand, key=lambda t: t[1][1])
                best[kind] = {
                    "limb": p,
                    "reach_m": round(-w[1], 4),
                    "height_m": round(w[2], 4),
                    "lateral_m": round(w[0], 4),
                }

            # 手臂长度用于判定盒尺寸：肘到拳
            arm_span = None
            if "hand.L" in poses and "forearm.L" in poses:
                h = poses["hand.L"]
                e = poses["forearm.L"]
                arm_span = round(((h[0] - e[0]) ** 2 + (h[1] - e[1]) ** 2 + (h[2] - e[2]) ** 2) ** 0.5, 4)

            rec["samples"].append({
                "frame": f,
                "probes": poses,
                "best": best,
                "elbow_to_hand_m": arm_span,
            })
        report["clips"][act.name] = rec

    text = json.dumps(report, ensure_ascii=False, indent=1)
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("WROTE %s (%d bytes)" % (out_path, len(text.encode("utf-8"))))
    print("CLIPS_MEASURED %d" % len(report["clips"]))
    for name, rec in report["clips"].items():
        line = ["%-20s" % name]
        for s in rec["samples"]:
            b = s["best"]
            line.append("f%d: %s reach=%.3f h=%.3f" % (
                s["frame"], b.get("punch", b.get("kick", {})).get("limb", "?"),
                b.get("punch", b.get("kick", {})).get("reach_m", 0.0),
                b.get("punch", b.get("kick", {})).get("height_m", 0.0)))
        print("  " + " | ".join(line))


main()
