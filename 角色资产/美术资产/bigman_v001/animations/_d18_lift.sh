#!/usr/bin/env bash
# 假设：窗口 A 尖峰 = 手离地是**离散单帧事件**（抬升 1 帧跳 60 mm + 1 帧锚点 slerp）
# 做法：把它摊到多帧 —— 只改角速度剖面，两端逐位不变，**不放宽任何阈值**
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"
LIFT="0:0.0,17:0.0,18:0.015,19:0.040,20:0.080,21:0.150,25:0.0,36:0.0"
run() { local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK=19 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python "$SRC" > "_d18_lf_${tag}.log" 2>&1; }

run LA1 D18_LIFT_KEYS="$LIFT" &
run LA2 D18_ARM_ANCHORS="17,19,24,34" &
run LA3 D18_LIFT_KEYS="$LIFT" D18_ARM_ANCHORS="17,19,24,34" &
run LA4 D18_LIFT_KEYS="$LIFT" D18_ARM_ANCHORS="17,19,24,34" D18_ANCHOR_SLERP_UNTIL=19 &
wait
for t in LA1 LA2 LA3 LA4; do
  printf "%-5s " "$t"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_lf_${t}.log" | head -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_lf_${t}.log" | tail -1
  grep -o '"hand_plant_ok": [a-z]*' "_d18_lf_${t}.log" | head -1
  grep -o '"hand_off_ok": [a-z]*' "_d18_lf_${t}.log" | head -1
done
echo "=== done ==="
