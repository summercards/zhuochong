#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_sw_$tag.log" 2>&1
  echo "== $tag done =="; }
run V0 D15_LIFT_BUMP=0.008 C14_ROLLSTEP=2.0 &
run V1 D15_LIFT_BUMP=0.011 C14_ROLLSTEP=2.0 &
run V2 D15_LIFT_BUMP=0.013 C14_ROLLSTEP=2.0 &
run V3 D15_LIFT_BUMP=0.016 C14_ROLLSTEP=2.0 &
wait; echo ALLDONE
