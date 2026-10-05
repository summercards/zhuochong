#!/bin/bash
# D12 Launch_Hit（腰部受击/被击飞）—— 门禁扫描/迭代助手。
# 用法： _d12_run.sh <tag> [ENV=VAL ...]
#   例： _d12_run.sh base
#        _d12_run.sh lift20 D12_TP_LIFT_MM=20
#        _d12_run.sh nosign D12_TP_SIGN=-1
# 输出：_d12_<tag>.log（完整 Blender 日志） + 屏幕上的全部判据摘要
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
tag="$1"; shift
env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_launch_hit.py > "_d12_$tag.log" 2>&1
python - "$tag" <<'PY'
import sys, json, re

tag = sys.argv[1]
txt = open("_d12_%s.log" % tag, encoding="utf-8", errors="replace").read()


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


d = extract("D12_REPORT")
if not d:
    tail = txt.strip().splitlines()[-24:]
    print("=== %s | NO REPORT" % tag)
    for line in tail:
        print("    " + line[:220])
    raise SystemExit
print("=== %s | failed=%s" % (tag, d.get("failed")))
print("=== %s | non_ok=%s" % (tag, d.get("non_ok_bools")))
skip = {"meta", "failed", "non_ok_bools"}
for k in sorted(d):
    if k in skip:
        continue
    v = d[k]
    if isinstance(v, (dict, list)):
        s = json.dumps(v, ensure_ascii=False)
        print("    %-38s %s" % (k, s[:340]))
    else:
        print("    %-38s %s" % (k, v))

lay = extract("D12_LAYOUT")
if lay:
    print("--- D12_LAYOUT ---")
    for k in sorted(lay):
        s = json.dumps(lay[k], ensure_ascii=False) if isinstance(lay[k], (dict, list)) else lay[k]
        print("    %-44s %s" % (k, str(s)[:340]))

tr = extract("D12_TRACE")
if tr:
    print("--- D12_TRACE present ---")
PY
