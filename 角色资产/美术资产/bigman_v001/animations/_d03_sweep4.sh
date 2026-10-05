#!/bin/bash
# D03 第四轮：把"头部后甩"的可读性做出来 —— 靠 neck/head 自身旋转加大，
# 而不是加大 chest（chest 后仰 3° 以上会抢 D04 Guard_Break "身体后仰" 的戏份）。
# 目标：head_back 从 47.6 mm 推到 80~110 mm（画面头顶位移 ~7 px 以上），clip 仍为 0。
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  local tag="$1"; shift
  env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_guard_hit.py > "_d03_sw4_$tag.log" 2>&1
  python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d03_sw4_%s.log" % tag, encoding="utf-8", errors="replace").read()
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
for k in ["guard_hit_ok", "torso_lean_back_ok", "head_snap_back_ok", "guard_cover_ok",
          "min_in_front_mm", "guard_no_face_clip_ok", "guard_elbow_ok", "guard_symmetry_hold_ok",
          "guard_hit_recover_ok", "fist_back_pull_mm", "chest_pitch_delta_deg",
          "head_back_mm", "neck_back_mm", "clip_max_mm", "clip_at", "clip_frame",
          "ground_min_mm", "ground_contact_ok", "max_frame_step_deg", "plant_mm",
          "reach_ratio_max", "end_world_pose_mm", "end_last2_deg", "end_pose_mm"]:
    if k in d: print("    %-24s %s" % (k, d[k]))
PY
}
run I_n16_h22  D03_BACK=44 D03_TP_CHEST=-1.8 D03_TP_S1=-0.95 D03_TP_S2=-0.95 D03_TP_PELVIS=-0.6 D03_TP_NECK=-1.6 D03_TP_HEAD=-2.2
run J_n20_h28  D03_BACK=44 D03_TP_CHEST=-1.8 D03_TP_S1=-0.95 D03_TP_S2=-0.95 D03_TP_PELVIS=-0.6 D03_TP_NECK=-2.0 D03_TP_HEAD=-2.8
run K_n24_h34  D03_BACK=44 D03_TP_CHEST=-1.8 D03_TP_S1=-0.95 D03_TP_S2=-0.95 D03_TP_PELVIS=-0.6 D03_TP_NECK=-2.4 D03_TP_HEAD=-3.4
