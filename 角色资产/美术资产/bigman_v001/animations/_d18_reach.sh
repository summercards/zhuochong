#!/usr/bin/env bash
# 假设：窗口 A 尖峰 = 手臂在 f17 逼近伸展极限（reach_max 0.95881 @f17），IK 角增益发散
# 做法：把掌撑点拉回（减小 reach），看尖峰是否随之下降 —— 只改位姿，不动阈值
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"
run() { local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK=19 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python "$SRC" > "_d18_rc_${tag}.log" 2>&1; }
for v in -0.45 -0.40 -0.25 -0.15 -0.05 0.10; do
  run "dy2_${v}" D18_PLANT_DY2=$v &
done
wait
for v in -0.45 -0.40 -0.25 -0.15 -0.05 0.10; do
  printf "dy2=%-6s " "$v"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_rc_dy2_${v}.log" | head -1
  grep -o '"reach_ratio_max": [0-9.]*' "_d18_rc_dy2_${v}.log" | head -1
  grep -o '"hand_plant_ok": [a-z]*' "_d18_rc_dy2_${v}.log" | head -1
done
echo "=== done ==="
