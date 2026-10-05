#!/bin/bash
# D05 正面轻受击 —— 门禁扫描/迭代助手。
# 用法： _d05_run.sh <tag> [ENV=VAL ...]
#   例： _d05_run.sh base
#        _d05_run.sh sw2 TP_HEAD=-3.5 HEAD_MAX=80
# 输出：_d05_<tag>.log（完整 Blender 日志） + 屏幕上的关键判据摘要
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
tag="$1"; shift
env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_hit_light_f.py > "_d05_$tag.log" 2>&1
python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d05_%s.log" % tag, encoding="utf-8", errors="replace").read()
m = re.search(r'D05_REPORT (\{.*)', txt)
if not m:
    tail = txt.strip().splitlines()[-8:]
    print("=== %s | NO REPORT" % tag)
    for line in tail:
        print("    " + line[:180])
    raise SystemExit
s = m.group(1); depth = 0; end = None
for i, ch in enumerate(s):
    if ch == "{": depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0: end = i + 1; break
d = json.loads(s[:end])
print("=== %s | failed=%s | non_ok=%s" % (tag, d.get("failed"), d.get("non_ok_bools")))
keys = ["hit_light_ok", "hit_light_pitch_ok", "hit_light_head_ok",
        "hit_light_speed_ok", "hit_light_recover_ok", "hitstop_present",
        "arms_kept_shape_ok", "no_face_clip_ok",
        "chest_pitch_delta_deg", "chest_pitch_impact_deg", "chest_pitch_zero_deg",
        "chest_pitch_delta_max_deg", "head_back_mm", "head_back_max_mm", "neck_back_mm",
        "head_back_px", "press_rise_frames", "press_fall_frames",
        "hitstop_frames", "hitstop_drift_deg", "hitstop_drift_at",
        "fist_spread_zero_mm", "fist_spread_impact_mm", "fist_spread_delta_mm",
        "fist_delta_mm", "fist_back_delta_mm", "pelvis_side_shift_mm",
        "clip_max_mm", "clip_at", "clip_frame",
        "ground_min_mm", "ground_contact_ok", "max_frame_step_deg", "max_frame_step_at",
        "plant_mm", "plant_ok", "knee_delta_max_deg", "knee_delta_deg", "knee_passive_ok",
        "reach_ratio_max", "reach_ratio_at", "reach_ok",
        "end_roll_deg", "end_roll_bone", "end_roll_bones", "end_roll_ok",
        "end_world_pose_mm", "end_world_pose_bone", "end_last2_deg", "end_pose_mm",
        "end_world_per_bone_mm", "end_hand_rows",
        "ua_start_delta_deg", "ua_start_ok",
        "idle_zero_saved_ok", "idle_zero_euler_max_diff_deg",
        "idle_zero_euler_worst_bone", "idle_zero_geom_pos_mm", "idle_zero_geom_dir_deg",
        "zero_fist_mm", "impact_fist_mm", "aspect", "fill_grid", "width_m", "height_m"]
for k in keys:
    if k in d: print("    %-30s %s" % (k, d[k]))
PY

grep -E "^D05_LAYOUT " "_d05_$tag.log" >/dev/null 2>&1 && python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d05_%s.log" % tag, encoding="utf-8", errors="replace").read()
m = re.search(r'D05_LAYOUT (\{.*)', txt)
if not m: raise SystemExit
s = m.group(1); depth=0; end=None
for i,ch in enumerate(s):
    if ch=="{": depth+=1
    elif ch=="}":
        depth-=1
        if depth==0: end=i+1; break
d=json.loads(s[:end])
print("--- D05_LAYOUT ---")
for k in ["zero_source","zero_pelvis_z_mm","zero_fist_mm","zero_fist_spread_mm",
          "zero_ankle_mm","zero_knee_dir","zero_euler_y_deg","zero_euler_y_lock_risk",
          "zero_wrist_mm","zero_hand_dir","zero_hand_bend_deg",
          "zero_vs_idle_pose_euler_max_diff_deg","zero_vs_idle_pose_worst_bone",
          "zero_vs_idle_pose_geom_pos_mm","zero_vs_idle_pose_geom_dir_deg",
          "roll_return","roll_weight_mode"]:
    if k in d: print("    %-34s %s" % (k, d[k]))
PY
