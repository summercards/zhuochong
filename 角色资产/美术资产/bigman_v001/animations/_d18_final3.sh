#!/usr/bin/env bash
# X5 = LEGS_DOWN4 PLANT7 CHEST_UP10 HAND_OFF18 TUCK20 FOOT_SET27 RISE_MID31 STAND35 TOTAL37 → 28.901 @f31 forearm.R
# 瓶颈已移到窗口 B（手臂上摆入 Idle）。围绕 X5 收口。
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"
X5="D18_LEGS_DOWN=4 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=20 D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35 D18_TOTAL=37"
run() { local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_THIGH_ROLL=1 $X5 "$@" \
    "$BL" --background --factory-startup --python "$SRC" > "_d18_f3_${tag}.log" 2>&1; }

run Y0 &
run Y1 D18_HAND_MIX_END=30 &
run Y2 D18_RISE_MID=33 D18_STAND=37 D18_TOTAL=39 &
run Y3 D18_HAND_MIX_END=30 D18_RISE_MID=33 D18_STAND=37 D18_TOTAL=39 &
run Y4 D18_HAND_MIX_END=28 &
run Y5 D18_HAND_MIX_END=30 D18_HAND_MIX_POW=0.7 &
wait
for t in Y0 Y1 Y2 Y3 Y4 Y5; do
  printf "%-3s " "$t"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_f3_${t}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_f3_${t}.log" | tail -1
done
echo "=== done ==="
