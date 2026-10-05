#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_sw_$tag.log" 2>&1
  echo "== $tag done =="; }
run X1 D15_LIFT_BUMP=0.004 D15_FOOT_RX=-5.0 &
run X2 D15_LIFT_BUMP=0.006 D15_FOOT_RX=-5.0 &
run X3 D15_LIFT_BUMP=0.004 D15_FOOT_RX=-7.0 &
run X4 D15_LIFT_BUMP=0.000 D15_FOOT_RX=-7.0 &
wait; echo ALLDONE
