#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_sw_$tag.log" 2>&1
  echo "== $tag done =="; }
run W0 D15_LIFT_BUMP=0.0 D15_FOOT_RX=0.0 &
run W1 D15_LIFT_BUMP=0.0 D15_FOOT_RX=-2.0 &
run W2 D15_LIFT_BUMP=0.0 D15_FOOT_RX=-3.5 &
run W3 D15_LIFT_BUMP=0.0 D15_FOOT_RX=-5.0 &
wait; echo ALLDONE
