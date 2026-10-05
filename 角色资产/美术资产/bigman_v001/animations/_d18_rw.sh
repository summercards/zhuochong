#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() {
  local tag="$1"; shift
  echo "=== $tag ==="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK_LEG=19 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_rw_${tag}.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_rw_${tag}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_rw_${tag}.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_rw_${tag}.log" | tail -1
}
run W1 D18_ROLLWIN_OFF=16:19
run W2 D18_ROLLWIN_OFF=15:20
run W3 D18_ROLLWIN_OFF=14:21
run W4 D18_ROLLWIN_OFF=16:21
echo "=== done ==="
