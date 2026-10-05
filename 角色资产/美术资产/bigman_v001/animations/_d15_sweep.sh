#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() {
  local tag="$1"; shift
  env "$@" D15_TRACE=1 SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_sw_$tag.log" 2>&1
  echo "== $tag done =="
}
run A D15_STANCE_Y=-0.06 &
run B D15_STANCE_Y=-0.06 D15_KNEE_DIR=0.14,-0.14,0.98 &
run C D15_KNEE_DIR=0.14,-0.14,0.98 &
run D D15_STANCE_Y=-0.06 D15_LIFT_Y=-0.24 D15_KNEE_DIR=0.14,-0.14,0.98 &
wait
echo ALLDONE
