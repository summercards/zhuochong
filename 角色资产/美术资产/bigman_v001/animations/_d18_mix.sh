#!/usr/bin/env bash
# D18 混合口径扫描：腿踝段插值口径 × 大腿滚转开关（只跑门禁）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run() {
  local tag="$1"; shift
  echo "=== $tag ==="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_mix_${tag}.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' \
    "_d18_mix_${tag}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_mix_${tag}.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_mix_${tag}.log" | tail -1
}

run base
run L1 D18_ANKLE_LINEAR=1
run L2 D18_ANKLE_LINEAR=2
run TL1 D18_ANKLE_LINEAR=1 D18_THIGH_ROLL=1
run TL2 D18_ANKLE_LINEAR=2 D18_THIGH_ROLL=1
echo "=== done ==="
