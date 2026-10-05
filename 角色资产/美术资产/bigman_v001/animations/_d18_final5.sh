#!/usr/bin/env bash
# Z0 (=28.558) 实测残余真实角速度：A 34.0 / B 30.7 / C 28.7 ⟹ 还需分别 ×1.36 / ×1.23 / ×1.15
# 按该比例继续摊，总帧数落在清单允许的 **40 帧硬上界**内
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"
run() { local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python "$SRC" > "_d18_f5_${tag}.log" 2>&1; }

run P1 D18_LEGS_DOWN=4 D18_PLANT=7 D18_CHEST_UP=9 D18_HAND_OFF=20 D18_TUCK=22 \
       D18_FOOT_SET=28 D18_RISE_MID=33 D18_STAND=38 D18_TOTAL=40 D18_HAND_MIX_END=32 &
run P2 D18_LEGS_DOWN=4 D18_PLANT=7 D18_CHEST_UP=8 D18_HAND_OFF=21 D18_TUCK=23 \
       D18_FOOT_SET=29 D18_RISE_MID=34 D18_STAND=39 D18_TOTAL=40 D18_HAND_MIX_END=34 &
run P3 D18_LEGS_DOWN=4 D18_PLANT=7 D18_CHEST_UP=9 D18_HAND_OFF=19 D18_TUCK=21 \
       D18_FOOT_SET=27 D18_RISE_MID=32 D18_STAND=37 D18_TOTAL=39 D18_HAND_MIX_END=31 &
run P4 D18_LEGS_DOWN=4 D18_PLANT=7 D18_CHEST_UP=9 D18_HAND_OFF=20 D18_TUCK=22 \
       D18_FOOT_SET=28 D18_RISE_MID=33 D18_STAND=38 D18_TOTAL=40 D18_HAND_MIX_END=32 \
       D18_ANKLE_LINEAR=1 &
wait
for t in P1 P2 P3 P4; do
  printf "%-3s " "$t"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_f5_${t}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_f5_${t}.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_f5_${t}.log" | tail -1
done
echo "=== done ==="
