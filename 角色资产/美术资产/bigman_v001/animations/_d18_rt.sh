#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() {
  local tag="$1"; shift
  echo "=== $tag ==="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_rt_${tag}.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_rt_${tag}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_rt_${tag}.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_rt_${tag}.log" | tail -1
}
run G D18_TOTAL=40 D18_HAND_OFF=18 D18_TUCK=22 D18_FOOT_SET=27 D18_RISE_MID=32 D18_STAND=38 D18_TUCK_LEG=20
run H D18_TOTAL=40 D18_HAND_OFF=19 D18_TUCK=23 D18_FOOT_SET=29 D18_RISE_MID=34 D18_STAND=38 D18_TUCK_LEG=21
run I D18_TOTAL=38 D18_HAND_OFF=18 D18_TUCK=22 D18_FOOT_SET=26 D18_RISE_MID=31 D18_STAND=36 D18_TUCK_LEG=20
run J D18_TOTAL=36 D18_HAND_OFF=18 D18_TUCK=22 D18_FOOT_SET=26 D18_TUCK_LEG=20
echo "=== done ==="
