#!/usr/bin/env bash
# D18 全超限点清单（T19 + 大腿滚转）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK=19 D18_THIGH_ROLL=1 \
  D18_STEPDBG=1 D18_STEPDBG_THR=18 \
  "$BL" --background --factory-startup --python anim_getup_b.py \
  > "_d18_step_t19r.log" 2>&1
grep -o 'D18_STEP_ALL .*' "_d18_step_t19r.log" | head -1
echo "=== done ==="
