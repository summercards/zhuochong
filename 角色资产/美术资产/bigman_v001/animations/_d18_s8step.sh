#!/usr/bin/env bash
# D18：ARMYSOFT=8 下的全超限点清单
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ARMYSOFT=8 D18_ROLLWIN_RAMP=0 \
  D18_STEPDBG=1 D18_STEPDBG_THR=20 \
  "$BL" --background --factory-startup --python anim_getup_b.py \
  > "_d18_s8step.log" 2>&1

grep -o 'D18_STEP_ALL .*' "_d18_s8step.log" | head -1 | \
  python -c "import sys,json; d=json.loads(sys.stdin.read().replace('D18_STEP_ALL ','')); [print('%7.3f  f%d->%d  %-12s %s -> %s'%(r[0],r[1],r[2],r[3],r[4],r[5])) for r in d]"
grep -o '"failed": \[[^]]*\]' "_d18_s8step.log" | tail -1
grep -o '"non_ok_bools": \[[^]]*\]' "_d18_s8step.log" | tail -1
echo "=== done ==="
