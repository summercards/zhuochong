#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" D15_TRACE=1 SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_sw_$tag.log" 2>&1
  echo "== $tag done =="; }
run E D15_STANCE_Y=-0.06 D15_FOOT_WTIP=15 D15_LIFT_Z=0.20 &
run F D15_STANCE_Y=-0.06 D15_FOOT_WTIP=25 D15_LIFT_Z=0.23 &
run G D15_STANCE_Y=-0.06 D15_FOOT_WTIP=15 D15_LIFT_Z=0.20 D15_LIFT_Y=-0.24 &
run H D15_STANCE_Y=-0.06 D15_FOOT_WTIP=15 D15_LIFT_Z=0.20 D15_LIFT_Y=-0.36 &
wait; echo ALLDONE
