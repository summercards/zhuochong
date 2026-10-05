#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" D15_TRACE=1 SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_sw_$tag.log" 2>&1
  echo "== $tag done =="; }
C="D15_FOOT_PIN=local"
run P1 $C D15_STANCE_X=0.115 D15_STANCE_Y=-0.184 D15_LIFT_X=0.150 D15_LIFT_Y=-0.240 D15_LIFT_Z=0.30 &
run P2 $C D15_STANCE_X=0.115 D15_STANCE_Y=-0.184 D15_LIFT_X=0.150 D15_LIFT_Y=-0.240 D15_LIFT_Z=0.38 &
run P3 $C D15_STANCE_X=0.115 D15_STANCE_Y=-0.138 D15_LIFT_X=0.150 D15_LIFT_Y=-0.180 D15_LIFT_Z=0.34 &
run P4 $C D15_STANCE_X=0.140 D15_STANCE_Y=-0.224 D15_LIFT_X=0.150 D15_LIFT_Y=-0.240 D15_LIFT_Z=0.34 &
wait; echo ALLDONE
