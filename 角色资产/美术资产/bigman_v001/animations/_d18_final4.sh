#!/usr/bin/env bash
# Y1 = X5 + HAND_MIX_END=30 → 28.558 @f25 foot.R（窗口 C 又成瓶颈）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"
B="D18_THIGH_ROLL=1 D18_LEGS_DOWN=4 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=20 D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35 D18_TOTAL=37 D18_HAND_MIX_END=30"
run() { local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 $B "$@" \
    "$BL" --background --factory-startup --python "$SRC" > "_d18_f4_${tag}.log" 2>&1; }

run Z0 &
run Z1 D18_TUCK=19 D18_FOOT_SET=29 &
run Z2 D18_FOOT_SET=30 &
run Z3 D18_TUCK=19 D18_FOOT_SET=29 D18_RISE_MID=33 D18_STAND=37 D18_TOTAL=39 &
run Z4 D18_ANKLE_LINEAR=1 &
run Z5 D18_LIFT_KEYS="0:0.0,18:0.0,19:0.010,20:0.025,21:0.045,22:0.075,23:0.110,24:0.140,25:0.150,31:0.115,38:0.050,40:0.0,42:0.0" &
wait
for t in Z0 Z1 Z2 Z3 Z4 Z5; do
  printf "%-3s " "$t"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_f4_${t}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_f4_${t}.log" | tail -1
done
echo "=== done ==="
