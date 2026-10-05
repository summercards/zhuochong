#!/usr/bin/env bash
# 出路 A 验证：唯一变量 = 帧预算（其余旋钮冻结在 07:11:12 快照 + T19R 最优）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"

run() {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK=19 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python "$SRC" \
    > "_d18_ra_${tag}.log" 2>&1
}

run RA0 &                                  # 基线复现
run RA1 D18_TOTAL=42 D18_HAND_OFF=19 D18_TUCK=20 D18_FOOT_SET=26 D18_RISE_MID=34 D18_STAND=39 &
run RA2 D18_TOTAL=46 D18_HAND_OFF=20 D18_TUCK=23 D18_FOOT_SET=27 D18_RISE_MID=37 D18_STAND=42 &
run RA3 D18_TOTAL=52 D18_HAND_OFF=22 D18_TUCK=25 D18_FOOT_SET=30 D18_RISE_MID=41 D18_STAND=47 &
wait
for t in RA0 RA1 RA2 RA3; do
  printf "%-4s " "$t"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_ra_${t}.log" | head -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_ra_${t}.log" | tail -1
  grep -o '"rise_reach_ok": [a-z]*' "_d18_ra_${t}.log" | head -1
  grep -o '"end_matches_idle_ok": [a-z]*' "_d18_ra_${t}.log" | head -1
done
echo "=== done ==="
