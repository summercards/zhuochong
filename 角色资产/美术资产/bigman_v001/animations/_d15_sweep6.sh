#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" D15_TRACE=1 SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_sw_$tag.log" 2>&1
  echo "== $tag done =="; }
C="D15_FOOT_PIN=local"
run S1 $C D15_STANCE_X=0.115 D15_STANCE_Y=-0.138 D15_LIFT_X=0.24 D15_LIFT_Y=-0.288 D15_LIFT_Z=0.34 &
run S2 $C D15_STANCE_X=0.115 D15_STANCE_Y=-0.138 D15_LIFT_X=0.20 D15_LIFT_Y=-0.240 D15_LIFT_Z=0.34 &
run S3 $C D15_STANCE_X=0.115 D15_STANCE_Y=-0.115 D15_LIFT_X=0.24 D15_LIFT_Y=-0.240 D15_LIFT_Z=0.30 &
run S4 $C D15_STANCE_X=0.115 D15_STANCE_Y=-0.138 D15_LIFT_X=0.24 D15_LIFT_Y=-0.288 D15_LIFT_Z=0.26 &
wait; echo ALLDONE
