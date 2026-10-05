#!/usr/bin/env bash
# D18：ARM_Y_SOFT 精扫 + 全门禁核对
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ROLLWIN_RAMP=0 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_ys_${tag}.log" 2>&1
  local m s f n
  m=$(grep -o '"max_frame_step_deg": [0-9.]*' "_d18_ys_${tag}.log" | tail -1 | sed 's/.*: //')
  s=$(grep -o '"max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_ys_${tag}.log" | tail -1 | sed 's/.*at": //')
  f=$(grep -o '"failed": \[[^]]*\]' "_d18_ys_${tag}.log" | tail -1)
  n=$(grep -o '"non_ok_bools": \[[^]]*\]' "_d18_ys_${tag}.log" | tail -1)
  printf '%-14s max=%8s at=%-22s %s %s\n' "$tag" "${m:-ERR}" "${s:-ERR}" "$f" "$n"
}

for v in 4 6 8 10 12 15 20 25 40 60; do
  run "s$v" D18_ARMYSOFT=$v
done
echo "=== done ==="
