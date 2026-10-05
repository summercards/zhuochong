# -*- coding: utf-8 -*-
"""由 doc/_animation_index.json 生成引擎侧运行时清单 manifest.json。

用法:
    python gen_anim_manifest.py <doc_dir> <out_manifest.json>
"""
import json
import os
import sys

FAMILY_LABEL = {
    "基础移动": "Locomotion",
    "普通攻击": "NormalAttack",
    "连招与特殊技": "ComboSpecial",
    "防御与受击": "GuardHit",
    "状态与流程": "StateFlow",
}

# ---------------------------------------------------------------------
# 命中点：资产里 hit_point_m 属性基本为空，所以由 tools/measure_hit_points.py
# 把骨架摆到命中帧、直接读肢端世界坐标量出来（Blender 世界系，前向 = -y）。
#
# 取哪根骨头当"攻击端"由招式意图决定，不靠"谁最靠前"自动猜：
#   拳招 -> hand.L/R          腿招 -> foot.L/R, toe.L/R      肩撞 -> shoulder.L/R
# ---------------------------------------------------------------------
LIMB_INTENT = {
    "Low_Attack": "foot",
    "Launcher": "foot",
    "Skill_01": "shoulder",
}
LIMB_SETS = {
    "hand": ("hand.L", "hand.R"),
    "foot": ("toe.L", "toe.R", "foot.L", "foot.R"),
    "shoulder": ("shoulder.L", "shoulder.R"),
}


def pick_hit_points(hit_data, clip_name):
    """从实测数据里挑出每个命中帧的攻击端位置。"""
    rec = (hit_data.get("clips") or {}).get(clip_name)
    if not rec:
        return None
    intent = LIMB_INTENT.get(clip_name, "hand")
    names = LIMB_SETS[intent]
    out = []
    for s in rec["samples"]:
        probes = s["probes"]
        cand = [(p, probes[p]) for p in names if p in probes]
        if not cand:
            continue
        p, w = min(cand, key=lambda t: t[1][1])  # y 最小 = 最靠前
        out.append({
            "frame": s["frame"],
            "limb": p,
            "intent": intent,
            "reach_m": round(-w[1], 4),
            "height_m": round(w[2], 4),
            "lateral_m": round(w[0], 4),
        })
    return out or None


def main():
    doc = os.path.abspath(sys.argv[1])
    out = os.path.abspath(sys.argv[2])

    with open(os.path.join(doc, "_animation_index.json"), encoding="utf-8") as fh:
        idx = json.load(fh)

    hit_path = os.path.join(doc, "_hit_points.json")
    hit_data = {}
    if os.path.isfile(hit_path):
        with open(hit_path, encoding="utf-8") as fh:
            hit_data = json.load(fh)
    else:
        print("WARN 没有 %s，命中点字段将为空" % hit_path)

    clips = {}
    groups = {}
    for e in idx["entries"]:
        fam = e["family"]
        groups.setdefault(fam, []).append(e["name"])
        # 命中点：Blender 世界坐标 [x, y, z]（x=左手侧, y=后方, z=上）。
        # 引擎侧换算到 Godot: (x, z, -y) —— 前向分量 = -y。
        hp = e["props"].get("hit_point_m")
        if isinstance(hp, str) or hp is None:
            hp = None
        elif isinstance(hp, list) and len(hp) == 3:
            hp = [float(v) for v in hp]
        else:
            hp = None
        clips[e["name"]] = {
            "code": e["code"],
            "cn": e["cn"],
            "group": fam,
            "group_key": FAMILY_LABEL.get(fam, "Other"),
            "frames": e["frames"],
            "fps": 60,
            "duration_s": e["duration_s"],
            "loop": e["loop"],
            "root_motion_m": e["root_motion_m"],
            "antic_frame": e["antic_frame"],
            "hit_frame": e["hit_frame"],
            "cancel_frame": e["cancel_frame"],
            "hitstop_frames": e["hitstop_frames"],
            "hit_point_m": hp,
            "hit_points": pick_hit_points(hit_data, e["name"]),
            "seam_in": e["seam_in"],
            "seam_out": e["seam_out"],
        }

    for x in idx["extra_actions_not_in_checklist"]:
        clips[x["name"]] = {
            "code": "C08b",
            "cn": "蓄力循环",
            "group": "连招与特殊技",
            "group_key": "ComboSpecial",
            "frames": x["frames"],
            "fps": 60,
            "duration_s": x["duration_s"],
            "loop": x["loop"],
            "root_motion_m": x["root_motion_m"],
            "antic_frame": None,
            "hit_frame": None,
            "cancel_frame": None,
            "hitstop_frames": None,
            "hit_point_m": None,
            "hit_points": None,
            "seam_in": "Charge@110",
            "seam_out": "Charge 释放段",
        }
        groups.setdefault("连招与特殊技", []).append(x["name"])

    manifest = {
        "character_id": "bigman",
        "version": "v001",
        "fps": 60,
        "source_glb": "bigman_anim_v001.glb",
        "total_clips": len(clips),
        "runtime_character_height_m": 1.803,
        "axis": {
            "up": "+Z",
            "forward": "-Y",
            "right": "-X",
            "left": "+X",
            "behind": "+Y",
            "ground_z": 0.0,
        },
        "groups": {FAMILY_LABEL.get(k, k): v for k, v in groups.items()},
        "clips": clips,
    }

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print("WROTE %s (%d clips)" % (out, len(clips)))


main()
