#!/bin/bash
# D06 参数扫描：膝弯（HIT_BACK_MM / HIT_DROP_MM）与末帧滚转（ROLL_RETURN）。
# 用法： _d06_sweep_knee.sh
cd "$(dirname "$0")" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  tag="$1"; shift
  env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup --python anim_hit_light_b.py > "_d06_$tag.log" 2>&1
  python - "$tag" <<'PY'
import sys, json, re
tag = sys.argv[1]
txt = open("_d06_%s.log" % tag, encoding="utf-8", errors="replace").read()
m = re.search(r'D06_REPORT (\{.*)', txt)
if not m:
    print("=== %s | NO REPORT" % tag)
    for line in txt.strip().splitlines()[-6:]:
        print("    " + line[:170])
    raise SystemExit
s = m.group(1); depth=0; end=None
for i,ch in enumerate(s):
    if ch=="{": depth+=1
    elif ch=="}":
        depth-=1
        if depth==0: end=i+1; break
d=json.loads(s[:end])
keys=["failed","non_ok_bools","chest_pitch_delta_deg","head_fwd_mm","knee_delta_deg",
      "knee_delta_max_deg","end_roll_deg","end_roll_bones","end_last2_deg",
      "end_world_pose_mm","max_frame_step_deg","max_frame_step_at",
      "arms_kept_shape_ok","fist_back_delta_mm","ground_min_mm"]
print("=== %s"%tag)
for k in keys:
    if k in d: print("    %-26s %s"%(k,d[k]))
PY
}
run swA D06_BACK=-4 D06_ROLL_RETURN=1
run swB D06_BACK=-5 D06_DROP=-2 D06_ROLL_RETURN=1
run swC D06_BACK=-3 D06_DROP=-2 D06_ROLL_RETURN=1
