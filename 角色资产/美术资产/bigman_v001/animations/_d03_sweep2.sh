#!/bin/bash
# D03 第二轮扫描：在「去尾部钉值」修复之后，重新标定 幅度 ↔ 穿模 ↔ 节奏 边界。
# 目的：当前 A_base（back=40, chest=-1.5）判据全绿但**画面偏保守**
#       （实测剪影位移 拳 8px / 前臂 11px / 头 6px）。要挑一个更读得出来、
#       又不至于抢掉 D04 `Guard_Break`（"身体后仰、明显硬直"）戏份的档位。
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  local tag="$1"; shift
  env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_guard_hit.py > "_d03_sw2_$tag.log" 2>&1
  python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d03_sw2_%s.log" % tag, encoding="utf-8", errors="replace").read()
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
keys = ["failed", "non_ok_bools",
        "guard_hit_ok", "arm_pushed_back_ok", "torso_lean_back_ok", "head_snap_back_ok",
        "guard_hit_impact_ok", "guard_hit_recover_ok", "guard_no_face_clip_ok",
        "guard_cover_ok", "guard_elbow_ok", "guard_symmetry_hold_ok",
        "fist_back_pull_mm", "chest_pitch_delta_deg", "head_back_mm", "neck_back_mm",
        "clip_max_mm", "clip_at", "clip_frame", "ground_min_mm", "ground_contact_ok",
        "max_frame_step_deg", "plant_mm", "reach_ratio_max", "end_world_pose_mm",
        "end_last2_deg", "press_rise_frames", "press_fall_frames"]
print("=== %s | failed=%s" % (tag, d.get("failed")))
for k in keys:
    if k in d: print("    %-26s %s" % (k, d[k]))
PY
}
run E_mid_back50   D03_BACK=50 D03_TP_CHEST=-2.4 D03_TP_S1=-1.3 D03_TP_S2=-1.3 D03_TP_PELVIS=-0.8 D03_TP_NECK=-0.9 D03_TP_HEAD=-1.2
run F_strong_bk50  D03_BACK=50 D03_TP_CHEST=-3.2 D03_TP_S1=-1.8 D03_TP_S2=-1.8 D03_TP_PELVIS=-1.1 D03_TP_NECK=-1.2 D03_TP_HEAD=-1.6
