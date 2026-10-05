#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" "$BL" --background --factory-startup --python render_mp4.py > "_e09_mp4_$tag.log" 2>&1
  echo "== $tag done =="; }
# E09 伏地后身体水平横跨 1.3 m+ ⟹ 用 wide 机位（OFFSET_Y 让画面中心跟在身体中段）
run side ANIM=Defeat VIEW=side_wide OFFSET_Y=0.30 OFFSET_Z=0.75 SCALE=2.60 &
run three_quarter ANIM=Defeat VIEW=three_quarter_wide OFFSET_Y=0.30 OFFSET_Z=0.80 SCALE=2.90 &
wait; echo ALLDONE
