#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() {
  local tag="$1"; shift
  echo "=== $tag ==="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK_LEG=19 D18_THIGH_ROLL=1 \
      D18_LEGROLL_MAX=80 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_ho2_${tag}.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_ho2_${tag}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_ho2_${tag}.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_ho2_${tag}.log" | tail -1
}
run H13 D18_HAND_OFF=13 D18_ROLLWIN_OFF=13:19
run H14 D18_HAND_OFF=14 D18_ROLLWIN_OFF=14:21
run H15 D18_HAND_OFF=15 D18_ROLLWIN_OFF=15:21
run H13D D18_HAND_OFF=13 D18_ROLLWIN_OFF=13:19 D18_STEPDBG=1 D18_STEPDBG_THR=20
grep -o 'D18_STEP_ALL .*' "_d18_ho2_H13D.log" | head -1
echo "=== done ==="
