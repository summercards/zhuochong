#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK_LEG=19 D18_THIGH_ROLL=1 \
  D18_EULERDBG=1 D18_EULERDBG_NAMES=forearm.R,hand.R,upperarm.R,forearm.L \
  D18_EULERDBG_F0=13 D18_EULERDBG_F1=22 \
  "$BL" --background --factory-startup --python anim_getup_b.py > "_d18_eul2.log" 2>&1
grep -o 'D18_EUL .*' "_d18_eul2.log"
echo "=== done ==="
