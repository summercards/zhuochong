#!/usr/bin/env bash
# C03 decel_smooth 扫描：串行跑若干组脚部时序 / 摆动缓动配置，只抽 return_tail。
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
      grep -E "return_tail |return_tail_bones|failed |pivot_drift|z_drop_world|fwd_ratio_net|local_step_max|world_step_max|always_supported|unsupported_frames|leg_reach_max|decel_smooth"
}

run lin   C03_L_SWING_MODE=linear
run sm32  C03_L_SWING_MODE=smooth C03_L_OFF=32 C03_R_ON=32
run lin30 C03_L_SWING_MODE=linear C03_L_OFF=30 C03_R_ON=30 C03_R_PIVOT=28
echo "全部完成"
