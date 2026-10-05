#!/usr/bin/env bash
# D18：手掌离地过渡「铺开」扫描（不改容差，只摊速度）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ROLLWIN_RAMP=0 D18_ARMYSOFT=8 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_hw_${tag}.log" 2>&1
  local m s f n
  m=$(grep -o '"max_frame_step_deg": [0-9.]*' "_d18_hw_${tag}.log" | tail -1 | sed 's/.*: //')
  s=$(grep -o '"max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_hw_${tag}.log" | tail -1 | sed 's/.*at": //')
  f=$(grep -o '"failed": \[[^]]*\]' "_d18_hw_${tag}.log" | tail -1 | sed 's/"failed": //')
  printf '%-18s max=%8s at=%-22s failed=%s\n' "$tag" "${m:-ERR}" "${s:-ERR}" "${f:-ERR}"
}

L="D18_LIFT_KEYS=0:0,17:0,18:0.022,19:0.045,20:0.060,21:0.150,22:0.115,23:0.050,25:0.0,36:0.0"

run base
run mx28            D18_HAND_MIX_END=28
run mx30            D18_HAND_MIX_END=30
run mx32            D18_HAND_MIX_END=32
run mx30pw0         D18_HAND_MIX_END=30 D18_HAND_MIX_POW=0
run mx32pw0         D18_HAND_MIX_END=32 D18_HAND_MIX_POW=0
run lift            "$L"
run lift_mx30       $L D18_HAND_MIX_END=30
run lift_mx30pw0    $L D18_HAND_MIX_END=30 D18_HAND_MIX_POW=0
run lift_mx32pw0    $L D18_HAND_MIX_END=32 D18_HAND_MIX_POW=0
echo "=== done ==="
