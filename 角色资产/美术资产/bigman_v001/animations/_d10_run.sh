#!/bin/bash
# D10 腹部受击 —— 门禁扫描/迭代助手。
# 用法： _d10_run.sh <tag> [ENV=VAL ...]
#   例： _d10_run.sh base
#        _d10_run.sh fold20 D10_TP_S1=6.5
# 输出：_d10_<tag>.log（完整 Blender 日志） + 屏幕上的全部判据摘要
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
tag="$1"; shift
env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_hit_body.py > "_d10_$tag.log" 2>&1
python - "$tag" <<'PY'
import sys, json, re

tag = sys.argv[1]
txt = open("_d10_%s.log" % tag, encoding="utf-8", errors="replace").read()


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


d = extract("D10_REPORT")
if not d:
    tail = txt.strip().splitlines()[-16:]
    print("=== %s | NO REPORT" % tag)
    for line in tail:
        print("    " + line[:220])
    raise SystemExit
print("=== %s | failed=%s" % (tag, d.get("failed")))
print("=== %s | non_ok=%s" % (tag, d.get("non_ok_bools")))
skip = {"meta", "failed", "non_ok_bools", "bone_travel_mm",
        "idle_zero_euler_roll_free_bones", "fold_keys", "lag_keys",
        "zero_fist_mm", "impact_fist_mm", "zero_ankle_mm", "zero_knee_dir",
        "amp_deg", "yaw_deg", "hip_shift_mm", "fist_shift_mm"}
for k in sorted(d):
    if k in skip:
        continue
    print("    %-38s %s" % (k, d[k]))

lay = extract("D10_LAYOUT")
if lay:
    print("--- D10_LAYOUT ---")
    for k in sorted(lay):
        print("    %-44s %s" % (k, lay[k]))
PY
