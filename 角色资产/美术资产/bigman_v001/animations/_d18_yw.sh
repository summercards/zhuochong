#!/usr/bin/env bash
# D18：臂骨"逃离万向节锁"罚分扫描（滚转窗口保持硬开关默认 16:21）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ROLLWIN_RAMP=0 "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_yw_${tag}.log" 2>&1
  local m s
  m=$(grep -o '"max_frame_step_deg": [0-9.]*' "_d18_yw_${tag}.log" | tail -1 | sed 's/.*: //')
  s=$(grep -o '"max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_yw_${tag}.log" | tail -1 | sed 's/.*at": //')
  printf '%-16s max=%8s  at=%s\n' "$tag" "${m:-ERR}" "${s:-ERR}"
}

run base          D18_ARMYWEIGHT=0
run w05           D18_ARMYWEIGHT=0.5
run w10           D18_ARMYWEIGHT=1.0
run w20           D18_ARMYWEIGHT=2.0
run w40           D18_ARMYWEIGHT=4.0
run s30           D18_ARMYSOFT=3.0
run s100          D18_ARMYSOFT=10.0
run s300          D18_ARMYSOFT=30.0
run w10s30        D18_ARMYWEIGHT=1.0 D18_ARMYSOFT=30.0
run w40s100       D18_ARMYWEIGHT=4.0 D18_ARMYSOFT=100.0
echo "=== done ==="
