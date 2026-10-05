#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" "$BL" --background --factory-startup --python render_mp4.py > "_d15_mp4_$tag.log" 2>&1
  echo "== $tag done =="; }
run side ANIM=Knockdown_B VIEW=side    OFFSET_Y=0.50 OFFSET_Z=1.00 SCALE=3.30 &
run three_quarter ANIM=Knockdown_B VIEW=three_quarter OFFSET_Y=0.35 OFFSET_Z=0.95 SCALE=4.60 &
wait; echo ALLDONE
