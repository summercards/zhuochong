#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"
run() { local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python "$SRC" > "_d18_ra_${tag}.log" 2>&1; }

# 1) RA4 加 STEPDBG：判定 64.989 是真旋转还是表示跳
run RA4D D18_TOTAL=59 D18_LEGS_DOWN=7 D18_PLANT=13 D18_CHEST_UP=20 D18_HAND_OFF=28 \
         D18_TUCK=31 D18_FOOT_SET=41 D18_RISE_MID=49 D18_STAND=56 \
         D18_STEPDBG=1 D18_STEPDBG_THR=18 &
# 2) 只把窗口 C（TUCK→FOOT_SET）再加宽到 8 帧
run RB1 D18_TUCK=17 &
# 3) 只把窗口 A（CHEST_UP→HAND_OFF）加宽 2 帧，其余保持 T19 最优
run RB2 D18_HAND_OFF=19 D18_TUCK=19 &
wait
for t in RA4D RB1 RB2; do
  printf "%-5s " "$t"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_ra_${t}.log" | head -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_ra_${t}.log" | tail -1
done
echo "=== done ==="
