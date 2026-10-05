#!/bin/bash
# D09 头部受击 —— 门禁扫描/迭代助手。
# 用法： _d09_run.sh <tag> [ENV=VAL ...]
#   例： _d09_run.sh base
#        _d09_run.sh whip20 D09_NECK_WHIP=-20
# 输出：_d09_<tag>.log（完整 Blender 日志） + 屏幕上的全部判据摘要
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
tag="$1"; shift
env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_hit_head.py > "_d09_$tag.log" 2>&1
python - "$tag" <<'PY'
import sys, json, re

tag = sys.argv[1]
txt = open("_d09_%s.log" % tag, encoding="utf-8", errors="replace").read()


def extract(marker):
    m = re.search(re.escape(marker) + r' (\{.*)', txt)
    if not m:
        return None
    s = m.group(1)
    depth = 0
    end = None
    for i, ch in enumerate(s):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    return json.loads(s[:end])


d = extract("D09_REPORT")
if not d:
    tail = txt.strip().splitlines()[-14:]
    print("=== %s | NO REPORT" % tag)
    for line in tail:
        print("    " + line[:220])
    raise SystemExit
print("=== %s | failed=%s" % (tag, d.get("failed")))
print("=== %s | non_ok=%s" % (tag, d.get("non_ok_bools")))
skip = {"meta", "failed", "non_ok_bools", "bone_travel_mm",
        "idle_zero_euler_roll_free_bones", "whip_keys"}
for k in sorted(d):
    if k in skip:
        continue
    print("    %-38s %s" % (k, d[k]))

lay = extract("D09_LAYOUT")
if lay:
    print("--- D09_LAYOUT ---")
    for k in sorted(lay):
        print("    %-44s %s" % (k, lay[k]))
PY
