# -*- coding: utf-8 -*-
"""C08 收招门禁诊断（只读）：谁在收招段制造"先加速后减速"的非单调台阶。

不自建动画 —— 直接打开已保存的 `bigman_anim_v001.blend` 里的 `Charge` Action，
逐帧取**局部位姿欧拉**，按 `anim_charge08.charge_assertions` 同一口径复算
`return_tail` / `return_tail_bones`，并把每帧的 top-3 步长骨打印出来。

    blender --background --factory-startup --python probe_c08_decel.py
"""
import sys
import os
import math

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy                                                    # noqa: E402
import anim_lib as A                                          # noqa: E402
import anim_charge08 as C08                                   # noqa: E402


def top3(ea, eb):
    rows = []
    for name in set(ea) | set(eb):
        va = ea.get(name, (0.0, 0.0, 0.0))
        vb = eb.get(name, (0.0, 0.0, 0.0))
        rows.append((max(abs(a - b) for a, b in zip(va, vb)), name))
    rows.sort(reverse=True)
    return rows[:3]


def main():
    arm, _meshes = A.open_animation_project()
    scene = bpy.context.scene
    if C08.NAME not in bpy.data.actions:
        print("C08DECEL 缺 Action %s，blend 里只有: %s"
              % (C08.NAME, sorted(bpy.data.actions.keys())))
        return
    action = bpy.data.actions[C08.NAME]
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    A._bind_slot(arm, action)

    samples = A.sample_animation(arm, action, 0, C08.TOTAL)
    print("C08DECEL n_samples=%d frames=%d..%d"
          % (len(samples), samples[0]["frame"], samples[-1]["frame"]))

    tails, owners = [], []
    for index in range(1, len(samples)):
        frame = samples[index]["frame"]
        if frame < C08.RETURN_START:
            continue
        ea = samples[index - 1]["euler"]
        eb = samples[index]["euler"]
        rows = top3(ea, eb)
        step, owner = rows[0]
        tails.append(round(step, 4))
        owners.append(owner)
        print("C08DECEL f%03d  step=%7.3f  owner=%-14s  next=[%s]"
              % (frame, step, owner,
                 ", ".join("%s %.2f" % (n, v) for v, n in rows[1:])))

    print("C08DECEL_TAIL %s" % tails)
    print("C08DECEL_OWNERS %s" % owners)

    bad = [i for i in range(len(tails) - 1) if tails[i + 1] > tails[i] + 1e-9]
    print("C08DECEL_RISE_AT %s" % [
        (samples[C08.RETURN_START + i]["frame"], tails[i], tails[i + 1],
         owners[i], owners[i + 1]) for i in bad])
    print("C08DECEL_OK %s" % (not bad))

    # 分族统计：臂 / 腿 / 躯干 各自在收招段的最大步长出现在哪一帧
    fam = {"arm": [], "leg": [], "torso": []}
    for index in range(1, len(samples)):
        if samples[index]["frame"] < C08.RETURN_START:
            continue
        ea = samples[index - 1]["euler"]
        eb = samples[index]["euler"]
        for name in set(ea) | set(eb):
            va = ea.get(name, (0.0, 0.0, 0.0))
            vb = eb.get(name, (0.0, 0.0, 0.0))
            here = max(abs(a - b) for a, b in zip(va, vb))
            key = ("arm" if (name.startswith(("upperarm", "forearm", "hand")))
                   else "leg" if name.startswith(("thigh", "shin", "foot"))
                   else "torso")
            fam[key].append((here, samples[index]["frame"], name))
    for key, rows in fam.items():
        rows.sort(reverse=True)
        print("C08DECEL_FAM %-6s peak=%7.3f @f%d %s  (top5 %s)"
              % (key, rows[0][0], rows[0][1], rows[0][2],
                 ["%s %.1f@f%d" % (n, v, f) for v, f, n in rows[:5]]))


main()
