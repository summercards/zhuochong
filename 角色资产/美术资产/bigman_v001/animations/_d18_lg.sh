#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() {
  local tag="$1"; shift
  echo "=== $tag ==="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK_LEG=19 D18_THIGH_ROLL=1 \
      D18_ROLLWIN_OFF=16:21 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_lg_${tag}.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_lg_${tag}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_lg_${tag}.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_lg_${tag}.log" | tail -1
}
run L60 D18_LEGROLL_MAX=60
run L80 D18_LEGROLL_MAX=80
run L60T18 D18_LEGROLL_MAX=60 D18_TUCK_LEG=18
run L60D D18_LEGROLL_MAX=60 D18_STEPDBG=1 D18_STEPDBG_THR=20
grep -o 'D18_STEP_ALL .*' "_d18_lg_L60D.log" | head -1
echo "=== done ==="
