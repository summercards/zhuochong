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
      grep -E "return_tail |return_tail_bones|failed |local_step_max|world_step_max|always_supported|pivot_drift|z_drop_world|fwd_ratio_net|leg_reach_max"
}
run lo38  C03_L_ON=38
run lo37  C03_L_ON=37 C03_L_OFF=32
run lo36  C03_L_ON=36 C03_L_OFF=32
echo "全部完成"
