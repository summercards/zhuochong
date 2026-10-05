#!/usr/bin/env bash
# D18：滚转窗口「帐篷斜坡」扫描
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_rr_${tag}.log" 2>&1
  local m s
  m=$(grep -o '"max_frame_step_deg": [0-9.]*' "_d18_rr_${tag}.log" | tail -1 | sed 's/.*: //')
  s=$(grep -o '"max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_rr_${tag}.log" | tail -1)
  printf '%-14s max=%8s  at=%s\n' "$tag" "${m:-ERR}" "${s:-ERR}"
}

run R0        D18_ROLLWIN_RAMP=0
run R1        D18_ROLLWIN_RAMP=1
run R2        D18_ROLLWIN_RAMP=2
run R3        D18_ROLLWIN_RAMP=3
run R4        D18_ROLLWIN_RAMP=4
run R5        D18_ROLLWIN_RAMP=5
run W15_21R3  D18_ROLLWIN_OFF=15:21 D18_ROLLWIN_RAMP=3
run W16_22R3  D18_ROLLWIN_OFF=16:22 D18_ROLLWIN_RAMP=3
run W14_21R3  D18_ROLLWIN_OFF=14:21 D18_ROLLWIN_RAMP=3
run W16_20R3  D18_ROLLWIN_OFF=16:20 D18_ROLLWIN_RAMP=3
echo "=== done ==="
