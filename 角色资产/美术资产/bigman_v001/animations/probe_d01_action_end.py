"""probe_d01_action_end —— 读落盘 `Guard_Start` 动作的末帧真值。

为什么需要它：D01 的 `end_euler_ref` 是**报告里按 4 位小数发布的数字**，
而真正被引擎播放的是 `.blend` 里 `Guard_Start` 这条 action。两者应当是同一份，
但 D01 的报告来自某一次跑，action 来自"最后一次存盘"那一次 —— 先确认它们是否同一。

顺带量清楚：D02 的零位候选（重演 `solve_pose(SETTLE)`）与落盘 action 末帧
逐骨差多少、差在哪里（是不是只差"绕骨轴的滚转"这个零空间）。

运行：
    blender.exe --background --factory-startup --python probe_d01_action_end.py
"""

import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim_lib as A                     # noqa: E402
import anim_jump_start as JS             # noqa: E402
import anim_ultimate_end as UE           # noqa: E402
import anim_guard_start as GS            # noqa: E402


def _keyed_bones(action):
    rot, loc = set(), set()
    for curve in action.fcurves:
        path = curve.data_path
        if not path.startswith('pose.bones["'):
            continue
        name = path.split('"')[1]
        if path.endswith("rotation_euler"):
            rot.add(name)
        elif path.endswith("location"):
            loc.add(name)
    return rot, loc


def _read_action_pose(arm, action, frame):
    """把 action 打到 frame 上，读回**逐骨欧拉（度）+ 位移**。"""
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)
    A.reset_pose(arm)
    bpy.context.scene.frame_set(int(frame))
    bpy.context.view_layer.update()
    return {b.name: tuple(math.degrees(v) for v in b.rotation_euler)
            for b in arm.pose.bones}


def _euler_delta(a, b):
    """逐分量差（度），按 ±360 去环绕。"""
    out = []
    for x, y in zip(a, b):
        d = x - y
        while d > 180.0:
            d -= 360.0
        while d < -180.0:
            d += 360.0
        out.append(d)
    return out


def main():
    arm, meshes = GS.boot()

    action = bpy.data.actions.get(GS.NAME)
    if action is None:
        raise RuntimeError("落盘里没有 `%s` 动作" % GS.NAME)
    rot_keyed, loc_keyed = _keyed_bones(action)
    last = int(action.frame_range[1])
    print("PD01_ACTION last_frame=%d rot_bones=%d loc_bones=%d"
          % (last, len(rot_keyed), len(loc_keyed)))
    print("PD01_ACTION frames=%s" % ([int(v) for v in action.frame_range],))

    saved = _read_action_pose(arm, action, last)
    saved_loc = {n: tuple(arm.pose.bones[n].location) for n in loc_keyed}

    # ---- 重演 D01（与 D02 的 `boot()` 同一条路径）
    JS._PREV_EULER.clear()
    A.apply_pose(arm, GS.SEAM_POSE)
    bpy.context.view_layer.update()
    for name, value in GS.SEAM_POSE.items():
        if not name.startswith("@"):
            JS._PREV_EULER[name] = tuple(value)
    replay = None
    for frame in range(1, GS.TOTAL + 1):
        got = GS.solve_pose(arm, frame, meshes)
        if frame == GS.SETTLE:
            replay = got

    print()
    print("%-14s %-28s %-28s %s" % ("bone", "saved(action)", "replay(solve)",
                                    "delta"))
    worst = 0.0
    worst_bone = None
    for name in sorted(rot_keyed):
        a = saved.get(name)
        b = replay.get(name)
        if a is None or b is None:
            continue
        d = _euler_delta(b, a)
        if max(abs(v) for v in d) > worst:
            worst = max(abs(v) for v in d)
            worst_bone = name
        if max(abs(v) for v in d) > 1e-3:
            print("%-14s %-28s %-28s %s"
                  % (name,
                     "[%s]" % ", ".join("%.4f" % v for v in a),
                     "[%s]" % ", ".join("%.4f" % v for v in b),
                     "[%s]" % ", ".join("%+.5f" % v for v in d)))
    print()
    print("PD01_DELTA worst=%.5f deg @ %s" % (worst, worst_bone))

    # ---- 世界几何是否同解（滚转过骨根 ⟹ 位置/朝向不该变）
    def world_of(pose):
        A.apply_pose(arm, pose)
        bpy.context.view_layer.update()
        heads = {n: tuple(A.bone_world(arm, n, "head"))
                 for n in A.PROBE_BONES if n in arm.pose.bones}
        dirs = {n: tuple(A.bone_direction(arm, n))
                for n in A.PROBE_BONES if n in arm.pose.bones}
        return heads, dirs

    a_pose = dict(saved)
    a_pose["@loc"] = {"pelvis": saved_loc["pelvis"]} if "pelvis" in saved_loc \
        else {}
    b_pose = replay
    ha, da = world_of(a_pose)
    hb, db = world_of(b_pose)
    max_pos = max((sum((x - y) ** 2 for x, y in zip(ha[n], hb[n])) ** 0.5
                   * 1000.0) for n in ha if n in hb)
    max_dir = 0.0
    for n in da:
        if n not in db:
            continue
        dot = sum(x * y for x, y in zip(da[n], db[n]))
        max_dir = max(max_dir, math.degrees(math.acos(max(-1.0, min(1.0, dot)))))
    print("PD01_WORLD max_head_pos_diff_mm=%.6f max_bone_dir_diff_deg=%.6f"
          % (max_pos, max_dir))

    print("PD01_LAYOUT " + json.dumps({
        "action": GS.NAME, "last_frame": last,
        "rot_bones": len(rot_keyed),
        "loc_bones": sorted(loc_keyed),
        "saved_euler": {n: [round(v, 4) for v in saved[n]]
                        for n in sorted(rot_keyed) if n in saved},
        "delta_worst_deg": round(worst, 6),
        "delta_worst_bone": worst_bone,
        "max_head_pos_diff_mm": round(max_pos, 6),
        "max_bone_dir_diff_deg": round(max_dir, 6),
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001
        import traceback
        print("PD01_FAILURE " + traceback.format_exc())
