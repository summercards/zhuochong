#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" D15_TRACE=1 SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_sw_$tag.log" 2>&1
  echo "== $tag done =="; }
run M1 D15_STANCE_Y=-0.06 D15_FOOT_PIN=local D15_LIFT_Z=0.34 &
run M2 D15_STANCE_Y=-0.06 D15_FOOT_PIN=local D15_LIFT_Z=0.38 &
run M3 D15_STANCE_Y=-0.06 D15_FOOT_PIN=local D15_LIFT_Z=0.42 &
run M4 D15_STANCE_Y=-0.06 D15_FOOT_PIN=local D15_LIFT_Z=0.38 D15_LIFT_Y=-0.24 &
wait; echo ALLDONE
