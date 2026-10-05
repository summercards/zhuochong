#!/usr/bin/env bash
# D18 收腿段 × 手离地段口径扫描（TUCK_LEG=19 + 大腿滚转 为基线）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run() {
  local tag="$1"; shift
  echo "=== $tag ==="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK_LEG=19 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_ho_${tag}.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' \
    "_d18_ho_${tag}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_ho_${tag}.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_ho_${tag}.log" | tail -1
}

run base
run A D18_HAND_MIX_END=33
run B D18_HAND_MIX_POW=2
run C D18_HAND_MIX_END=33 D18_HAND_MIX_POW=2
run D D18_HAND_OFF=19
run E D18_TUCK_LEG=20
echo "=== done ==="
