#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" D15_TRACE=1 SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_sw_$tag.log" 2>&1
  echo "== $tag done =="; }
C="D15_FOOT_PIN=local D15_ROLL_LEGS=1 D15_STANCE_X=0.115 D15_STANCE_Y=-0.115 D15_LIFT_X=0.24 D15_LIFT_Y=-0.240 D15_LIFT_Z=0.30"
run U0 $C &
run U1 $C D15_LIFT_BUMP=0.008 &
run U2 $C D15_LIFT_BUMP=0.013 &
run U3 $C D15_LIFT_BUMP=0.018 &
wait; echo ALLDONE
