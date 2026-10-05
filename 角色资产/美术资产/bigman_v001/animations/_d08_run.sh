#!/bin/bash
# D08 背面重受击 —— 门禁扫描/迭代助手。
# 用法： _d08_run.sh <tag> [ENV=VAL ...]
#   例： _d08_run.sh base
#        _d08_run.sh bod28 D08_BODY=0.28
# 输出：_d08_<tag>.log（完整 Blender 日志） + 屏幕上的关键判据摘要
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
tag="$1"; shift
env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_hit_heavy_b.py > "_d08_$tag.log" 2>&1
python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d08_%s.log" % tag, encoding="utf-8", errors="replace").read()
m = re.search(r'D08_REPORT (\{.*)', txt)
if not m:
    tail = txt.strip().splitlines()[-12:]
    print("=== %s | NO REPORT" % tag)
    for line in tail:
        print("    " + line[:200])
    raise SystemExit
s = m.group(1); depth = 0; end = None
for i, ch in enumerate(s):
    if ch == "{": depth += 1
    elif ch == "}":
        depth -= 1
        if depth == 0: end = i + 1; break
d = json.loads(s[:end])
print("=== %s | failed=%s | non_ok=%s" % (tag, d.get("failed"), d.get("non_ok_bools")))
keys = ["hit_heavy_ok", "hit_heavy_pitch_ok", "hit_heavy_head_ok",
        "hit_heavy_direction_can_fail_ok", "hit_heavy_speed_ok",
        "chest_pitch_delta_deg", "chest_pitch_zero_deg", "chest_pitch_impact_deg",
        "chest_pitch_delta_max_deg", "head_fwd_mm", "head_fwd_max_mm", "neck_fwd_mm",
        "head_back_mm",
        "pelvis_side_shift_mm", "pelvis_fwd_hit_mm", "pelvis_back_hit_mm",
        "fist_fwd_delta_mm", "fist_back_delta_mm", "fist_spread_delta_mm",
        "guard_kept_ok", "fist_delta_mm",
        "press_rise_frames", "press_fall_frames", "press_at_f1",
        "hitstop_frames", "hitstop_drift_deg", "hitstop_drift_at", "hitstop_present",
        "step_axis_mm", "step_back_m", "step_skid_m", "step_back_ok",
        "step_back_dir_can_fail_ok", "step_order_ok",
        "max_foot_step_mm", "max_foot_step_at", "no_foot_teleport_ok",
        "step_foot_lift_peak_mm", "step_foot_low_at_off_mm", "step_foot_low_at_plant_mm",
        "foot_lift_ok",
        "skid_foot_low_min_mm", "skid_foot_low_max_mm", "skid_foot_planted_ok",
        "body_shift_at_off_mm", "body_shift_at_plant_mm", "body_shift_end_mm",
        "body_shift_lead_ok",
        "end_world_pose_mm", "end_world_pose_bone", "end_last2_deg", "end_torso_euler_deg",
        "end_torso_euler_bone", "end_torso_ok", "end_stance_err_mm", "end_stance_bone",
        "end_sole_mm", "end_stance_ok",
        "end_roll_deg", "end_roll_bone", "end_roll_ok", "hit_heavy_recover_ok",
        "zero_shortcut_frames", "zero_shortcut_expect", "zero_shortcut_ok",
        "clip_max_mm", "clip_at", "clip_frame", "no_face_clip_ok",
        "reach_ratio_max", "reach_ratio_at", "reach_ok",
        "leg_reach_ratio_max", "leg_reach_ratio_at", "leg_reach_ok",
        "knee_delta_deg", "knee_delta_max_deg", "knee_passive_ok",
        "ua_start_delta_deg", "ua_start_ok",
        "idle_zero_saved_ok", "idle_zero_geom_pos_mm", "idle_zero_geom_dir_deg",
        "idle_zero_euler_max_diff_deg", "idle_zero_euler_worst_bone",
        "loop_seamless", "ground_contact_ok", "max_frame_step_deg", "max_frame_step_at",
        "bone_travel_mm",
        "zero_fist_mm", "impact_fist_mm", "px_per_mm", "head_fwd_px",
        "body_shift_px", "step_back_px", "aspect", "fill_grid"]
for k in keys:
    if k in d: print("    %-32s %s" % (k, d[k]))
PY

grep -E "^D08_LAYOUT " "_d08_$tag.log" >/dev/null 2>&1 && python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d08_%s.log" % tag, encoding="utf-8", errors="replace").read()
m = re.search(r'D08_LAYOUT (\{.*)', txt)
if not m: raise SystemExit
s = m.group(1); depth=0; end=None
for i,ch in enumerate(s):
    if ch=="{": depth+=1
    elif ch=="}":
        depth-=1
        if depth==0: end=i+1; break
d=json.loads(s[:end])
print("--- D08_LAYOUT ---")
for k in ["total_frames","seconds","impact","hold_end","hit_hold","step_off",
          "step_plant","skid_end","recover_end","cancel","root_motion_m",
          "force_direction","step_foot","skid_foot","step_plan","zero_source",
          "zero_vs_idle_pose_euler_max_diff_deg","zero_vs_idle_pose_worst_bone",
          "zero_vs_idle_pose_geom_pos_mm","zero_vs_idle_pose_geom_dir_deg",
          "zero_pelvis_z_mm","zero_fist_mm","zero_ankle_mm","zero_knee_dir",
          "step_back_m","step_move_m","step_source","body_move_m","push_mm","skid_m",
          "skid_move_m","lift_peak_mm","rel_step_mm","rel_skid_mm","hit_side_mm",
          "hit_fist_offset_mm","torso_hit_deg","pz_keys_mm","elbow_hit_delta",
          "pitch_gate_deg","head_fwd_gate_mm","roll_return","roll_weight_mode"]:
    if k in d: print("    %-36s %s" % (k, d[k]))
PY
