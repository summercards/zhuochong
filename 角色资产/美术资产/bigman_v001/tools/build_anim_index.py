# -*- coding: utf-8 -*-
"""三源合并：清单 67 行 × Blend Action × GLB 时长 → doc/_animation_index.json

用法:
    python build_anim_index.py <doc_dir>
"""
import hashlib
import json
import os
import re
import sys

ROW_RE = re.compile(r"^\|\s*([A-E]\d{2})\s*\|\s*`([^`]+)`\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")


def parse_checklist(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("|"):
                continue
            m = ROW_RE.match(line.rstrip("\n"))
            if not m:
                continue
            code, name, cn, desc, status = m.groups()
            rows.append({
                "code": code,
                "name": name,
                "cn": cn,
                "desc": desc,
                "status": status,
            })
    return rows


def main():
    doc = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    checklist = parse_checklist(os.path.join(doc, "动画制作清单.md"))

    with open(os.path.join(doc, "_actions_dump.json"), encoding="utf-8") as fh:
        dump = json.load(fh)
    with open(os.path.join(doc, "_glb_inventory.json"), encoding="utf-8") as fh:
        glb = json.load(fh)

    acts = dump["actions"]
    glb_anims = {a["name"]: a for a in glb["files"][0]["animations"]}

    # 按列表顺序的家族归类
    FAMILY = {
        "A": "基础移动", "B": "普通攻击", "C": "连招与特殊技",
        "D": "防御与受击", "E": "状态与流程",
    }

    entries = []
    used = set()
    for r in checklist:
        name = r["name"]
        act = acts.get(name)
        ga = glb_anims.get(name)
        used.add(name)
        props = act["props"] if act else {}
        fr = act["frame_range"] if act else None
        if fr is None and props.get("frames"):
            fr = [float(v) for v in props["frames"]]
        dur = round((fr[1] - fr[0]) / 60.0, 4) if fr else None
        entries.append({
            "code": r["code"],
            "family": FAMILY.get(r["code"][0], "?"),
            "name": name,
            "cn": r["cn"],
            "status": r["status"],
            "desc": r["desc"],
            "in_blend": bool(act),
            "in_glb": bool(ga),
            "frames": fr,
            "fps": 60,
            "duration_s": dur,
            "duration_glb_s": ga["duration_s"] if ga else None,
            "fcurves": act["fcurves"] if act else None,
            "channels_glb": ga["channels"] if ga else None,
            "loop": bool(props.get("loop", False)),
            "category": props.get("category"),
            "root_motion_m": props.get("root_motion_m"),
            "antic_frame": props.get("antic_frame"),
            "hit_frame": props.get("hit_frame"),
            "cancel_frame": props.get("cancel_frame"),
            "hitstop_frames": props.get("hitstop_frames"),
            "hitstop_span": props.get("hitstop_span"),
            "hit_point_m": props.get("hit_point_m"),
            "seam_in": props.get("seam_in"),
            "seam_out": props.get("seam_out"),
            "note": props.get("note"),
            # 全量原始属性（不丢信息，供文档/程序按需取用）
            "prop_keys": act["prop_keys"] if act else [],
            "props": props,
        })

    extra = sorted(set(acts) - used)
    extras = []
    for n in extra:
        act = acts[n]
        props = act["props"]
        fr = act["frame_range"]
        extras.append({
            "name": n,
            "frames": fr,
            "duration_s": round((fr[1] - fr[0]) / 60.0, 4),
            "loop": bool(props.get("loop", False)),
            "category": props.get("category"),
            "root_motion_m": props.get("root_motion_m"),
            "note": props.get("note"),
            "prop_keys": act["prop_keys"],
        })

    glb_only = sorted(set(glb_anims) - set(acts))

    fam_stats = {}
    for e in entries:
        fam_stats.setdefault(e["family"], []).append(e["code"])

    result = {
        "source": {
            "checklist": "doc/动画制作清单.md",
            "blend": dump["blend"],
            "blend_fps": dump["fps"],
            "armature": dump["armatures"][0]["object"],
            "bones": dump["armatures"][0]["bone_count"],
            "glb": glb["files"][0]["path"],
            "checklist_sha256": hashlib.sha256(
                open(os.path.join(doc, "动画制作清单.md"), "rb").read()).hexdigest(),
        },
        "totals": {
            "checklist_rows": len(entries),
            "blend_actions": len(acts),
            "glb_animations": len(glb_anims),
        },
        "family_counts": {k: len(v) for k, v in sorted(fam_stats.items())},
        "entries": entries,
        "extra_actions_not_in_checklist": extras,
        "glb_only_animations": glb_only,
    }

    out = os.path.join(doc, "_animation_index.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)

    print("WROTE %s" % out)
    print("checklist=%d blend=%d glb=%d" % (len(entries), len(acts), len(glb_anims)))
    print("families=%s" % result["family_counts"])
    print("extra_actions=%s" % extras and [e["name"] for e in extras])
    print("glb_only=%s" % glb_only)
    missing_blend = [e["name"] for e in entries if not e["in_blend"]]
    missing_glb = [e["name"] for e in entries if not e["in_glb"]]
    print("MISSING_IN_BLEND %s" % missing_blend)
    print("MISSING_IN_GLB %s" % missing_glb)
    dur_mismatch = [(e["name"], e["duration_s"], e["duration_glb_s"])
                    for e in entries
                    if e["duration_glb_s"] is not None and e["duration_s"] is not None
                    and abs(e["duration_s"] - e["duration_glb_s"]) > 1e-3]
    print("DURATION_MISMATCH %s" % dur_mismatch)


main()
