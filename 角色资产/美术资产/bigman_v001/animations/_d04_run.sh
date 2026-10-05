#!/bin/bash
# D04 破防 —— 门禁扫描/迭代助手。
# 用法： _d04_run.sh <tag> [ENV=VAL ...]
#   例： _d04_run.sh base
#        _d04_run.sh sw2 OUT=90 BACKMM=100
# 输出：_d04_<tag>.log（完整 Blender 日志） + 屏幕上的关键判据摘要
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
tag="$1"; shift
env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_guard_break.py > "_d04_$tag.log" 2>&1
python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d04_%s.log" % tag, encoding="utf-8", errors="replace").read()
m = re.search(r'D04_REPORT (\{.*)', txt)
if not m:
    tail = txt.strip().splitlines()[-6:]
    print("=== %s | NO REPORT" % tag)
    for line in tail:
        print("    " + line[:160])
    raise SystemExit
s = m.group(1); depth = 0; end = None
for i, ch in enumerate(s):
    if ch == "{": depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0: end = i + 1; break
d = json.loads(s[:end])
print("=== %s | failed=%s | non_ok=%s" % (tag, d.get("failed"), d.get("non_ok_bools")))
keys = ["guard_break_ok", "guard_break_torso_ok", "guard_break_stagger_ok",
        "guard_break_recover_ok", "guard_break_impact_ok", "hitstop_present",
        "fist_spread_delta_mm", "fist_spread_zero_mm", "fist_spread_impact_mm",
        "fist_back_pull_mm", "fist_back_vs_pelvis_pull_mm", "any_fist_forward",
        "chest_pitch_delta_deg", "chest_pitch_impact_deg", "head_back_mm", "neck_back_mm",
        "stagger_platform_frames", "stagger_platform_drift_deg", "stagger_platform_drift_at",
        "press_rise_frames", "press_fall_frames",
        "clip_max_mm", "clip_at", "clip_frame", "guard_no_face_clip_ok",
        "ground_min_mm", "ground_contact_ok", "max_frame_step_deg", "max_frame_step_at",
        "plant_mm", "plant_ok", "knee_delta_max_deg", "knee_passive_ok",
        "reach_ratio_max", "reach_ratio_at", "reach_ok", "max_sym_mm", "end_roll_deg", "end_roll_bone", "end_roll_bones", "end_roll_ok",
        "guard_symmetry_hold_ok", "end_world_pose_mm", "end_last2_deg", "end_pose_mm",
        "ua_start_delta_deg", "d01_end_saved_ok", "d01_replay_geom_ok",
        "spread_delta_px", "fist_back_pull_px", "impact_fist_mm", "zero_fist_mm"]
for k in keys:
    if k in d: print("    %-30s %s" % (k, d[k]))
PY
