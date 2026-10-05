#!/usr/bin/env bash
# dy2=-0.25 已修掉窗口 A（手臂，34.812→32.750，瓶颈转 `thigh.L` f21 收腿）
# 现在只加宽窗口 C（TUCK→FOOT_SET）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"
run() { local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_THIGH_ROLL=1 D18_PLANT_DY2=-0.25 "$@" \
    "$BL" --background --factory-startup --python "$SRC" > "_d18_f1_${tag}.log" 2>&1; }

run K19 D18_TUCK=19 &                       # 复现 32.750
run K18 D18_TUCK=18 &
run K17 D18_TUCK=17 &
run K20 D18_TUCK=20 &
run K19F26 D18_TUCK=19 D18_FOOT_SET=26 &
run K18F26 D18_TUCK=18 D18_FOOT_SET=26 &
wait
for t in K19 K18 K17 K20 K19F26 K18F26; do
  printf "%-7s " "$t"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_f1_${t}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_f1_${t}.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_f1_${t}.log" | tail -1
done
echo "=== done ==="
