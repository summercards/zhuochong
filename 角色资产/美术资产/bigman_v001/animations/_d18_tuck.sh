#!/usr/bin/env bash
# D18 收腿段宽度扫描（只动 TUCK，其余相位不变）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run() {
  local tag="$1"; shift
  echo "=== $tag ==="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_tk_${tag}.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' \
    "_d18_tk_${tag}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_tk_${tag}.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_tk_${tag}.log" | tail -1
}

run T20 D18_TUCK=20
run T19 D18_TUCK=19
run T18 D18_TUCK=18
run T19R D18_TUCK=19 D18_THIGH_ROLL=1
echo "=== done ==="
