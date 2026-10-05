#!/bin/bash
# 验证新门禁 `knee_passive_ok`：① 默认（下沉 14 mm）应绿；
# ② 故意把下沉调到 20 mm，膝角应变大 ⟹ 门禁**必须红**（证明它不是橡皮图章）。
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  local tag="$1"; shift
  env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_guard_hit.py > "_d03_sw5_$tag.log" 2>&1
  python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d03_sw5_%s.log" % tag, encoding="utf-8", errors="replace").read()
m = re.search(r'D03_REPORT (\{.*)', txt)
if not m:
    print("=== %s | NO REPORT" % tag); raise SystemExit
s = m.group(1); depth = 0; end = None
for i, ch in enumerate(s):
    if ch == "{": depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0: end = i + 1; break
d = json.loads(s[:end])
print("=== %s" % tag)
print("    failed        = %s" % d.get("failed"))
print("    non_ok_bools  = %s" % d.get("non_ok_bools"))
for k in ["knee_delta_deg", "knee_delta_max_deg", "knee_passive_ok", "plant_ok",
          "plant_mm", "ground_contact_ok", "ground_min_mm", "guard_hit_ok",
          "guard_co1ver_ok", "guard_cover_ok", "clip_max_mm", "no_teleport",
          "max_frame_step_deg", "guard_hit_recover_ok"]:
    if k in d: print("    %-22s %s" % (k, d[k]))
PY
}
run M_default      D03_KNEE=6.0
run N_knee_should_fail  D03_KNEE=6.0 D03_DROP=-20
