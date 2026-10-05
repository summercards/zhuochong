#!/bin/bash
# D03 第三轮：小幅提升档位 + 显式看护架余量（min_in_front_mm）。
# 约束：back 的上限被 `guard_cover_ok`（拳相对胸身前 ≥150 mm）卡住；
#       chest 后仰的上限被"不能抢 D04 Guard_Break 戏份"卡住。
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  local tag="$1"; shift
  env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_guard_hit.py > "_d03_sw3_$tag.log" 2>&1
  python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d03_sw3_%s.log" % tag, encoding="utf-8", errors="replace").read()
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
print("=== %s | failed=%s | non_ok=%s" % (tag, d.get("failed"), d.get("non_ok_bools")))
for k in ["guard_cover_ok", "min_in_front_mm", "min_raise_mm", "min_lateral_mm",
          "guard_hit_ok", "arm_pushed_back_ok", "torso_lean_back_ok", "head_snap_back_ok",
          "guard_hit_impact_ok", "guard_hit_recover_ok", "guard_no_face_clip_ok",
          "fist_back_pull_mm", "chest_pitch_delta_deg", "head_back_mm", "neck_back_mm",
          "clip_max_mm", "ground_min_mm", "ground_contact_ok", "max_frame_step_deg",
          "plant_mm", "reach_ratio_max", "end_world_pose_mm", "end_last2_deg", "end_pose_mm"]:
    if k in d: print("    %-24s %s" % (k, d[k]))
PY
}
run G_b44_c18  D03_BACK=44 D03_TP_CHEST=-1.8 D03_TP_S1=-0.95 D03_TP_S2=-0.95 D03_TP_PELVIS=-0.6 D03_TP_NECK=-0.7 D03_TP_HEAD=-1.0
run H_b40_c18  D03_BACK=40 D03_TP_CHEST=-1.8 D03_TP_S1=-0.95 D03_TP_S2=-0.95 D03_TP_PELVIS=-0.6 D03_TP_NECK=-0.7 D03_TP_HEAD=-1.0
