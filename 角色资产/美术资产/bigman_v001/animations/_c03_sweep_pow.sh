#!/usr/bin/env bash
set -u
cd "$(dirname "$0")" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() {
  local tag="$1"; shift
  echo "=================== $tag ==================="
  env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup \
      --python anim_knockdown03.py > "_c03_sw_${tag}.log" 2>&1
  echo "EXIT=$?"
  python _c03_dump.py "_c03_sw_${tag}.log" 2>&1 | \
      grep -E "return_tail |return_tail_bones|failed |local_step_max|world_step_max|no_snap_stop|decel_smooth"
}
run p120 C03_L_SWING_MODE=pow C03_L_SWING_POW=1.20
run p135 C03_L_SWING_MODE=pow C03_L_SWING_POW=1.35
run p150 C03_L_SWING_MODE=pow C03_L_SWING_POW=1.50
echo "全部完成"
