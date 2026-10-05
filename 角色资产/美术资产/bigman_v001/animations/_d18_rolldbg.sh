#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
env PYTHONHASHSEED=0 SKIP_RENDER=1 \
  D18_ROLLDBG=forearm.R,hand.R,forearm.L \
  D18_ROLLDBG_F=12 D18_ROLLDBG_F1=24 \
  "$BL" --background --factory-startup --python anim_getup_b.py > "_d18_rolldbg.log" 2>&1
grep -o 'D18_ROLL .*' "_d18_rolldbg.log"
echo "=== done ==="
