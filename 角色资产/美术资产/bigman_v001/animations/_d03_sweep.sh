#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  local tag="$1"; shift
  env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_guard_hit.py > "_d03_sw_$tag.log" 2>&1
  python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d03_sw_%s.log" % tag, encoding="utf-8", errors="replace").read()
m = re.search(r'D03_REPORT (\{.*)', txt)
d = json.loads(m.group(1))
keys = ["guard_hit_ok","arm_pushed_back_ok","torso_lean_back_ok","head_snap_back_ok",
        "guard_hit_impact_ok","guard_hit_recover_ok","guard_no_face_clip_ok",
        "guard_cover_ok","guard_elbow_ok","guard_symmetry_hold_ok","guard_no_face_clip_ok",
        "fist_back_pull_mm","chest_pitch_delta_deg","head_back_mm","neck_back_mm",
        "clip_max_mm","impact_arm_clip_mm","zero_arm_clip_mm","ground_min_mm",
        "max_frame_step_deg","plant_mm","reach_ratio_max","min_raise_mm","min_lateral_mm",
        "min_in_front_mm"]
print("=== %s | failed=%s" % (tag, d.get("failed")))
for k in keys:
    if k in d: print("    %-26s %s" % (k, d[k]))
PY
}
run A_base        D03_BACK=40
run B_back10      D03_BACK=10
run C_lean_mid    D03_BACK=40 D03_TP_CHEST=-2.4 D03_TP_S1=-1.3 D03_TP_S2=-1.3 D03_TP_PELVIS=-0.8 D03_TP_NECK=-0.9 D03_TP_HEAD=-1.2
run D_lean_strong D03_BACK=40 D03_TP_CHEST=-3.2 D03_TP_S1=-1.8 D03_TP_S2=-1.8 D03_TP_PELVIS=-1.1 D03_TP_NECK=-1.2 D03_TP_HEAD=-1.6
