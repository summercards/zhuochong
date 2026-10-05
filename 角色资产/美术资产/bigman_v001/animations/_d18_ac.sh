#!/usr/bin/env bash
# D18：踝部离地/抬跟通道扫描
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
BASE="D18_ARMYSOFT=8 D18_HAND_MIX_END=30 D18_HAND_MIX_POW=0 D18_STEPDBG=1 D18_STEPDBG_THR=18 D18_ROLLWIN_RAMP=0"

run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 $BASE "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_ac_${tag}.log" 2>&1
  local j f
  j=$(grep -o 'D18_STEP_ALL .*' "_d18_ac_${tag}.log" | head -1 | sed 's/D18_STEP_ALL //')
  f=$(grep -o '"failed": \[[^]]*\]' "_d18_ac_${tag}.log" | tail -1 | sed 's/"failed": //')
  if [ -z "$j" ]; then
    printf '%-14s  <none>=18  failed=%s\n' "$tag" "$f"
  else
    printf '%-14s  %s  failed=%s\n' "$tag" "$(printf '%s' "$j" | python -c "
import sys,json
d=json.loads(sys.stdin.read())
print(' '.join('%s@%d->%d(%.1f)'%(r[3],r[1],r[2],r[0]) for r in d[:4]), '| n>25=%d n>=18=%d'%(sum(1 for r in d if r[0]>25), len(d)))
")" "$f"
  fi
}

run base
run clear0   D18_ANKLE_CLEAR=0.0
run clear10  D18_ANKLE_CLEAR=0.10
run clear0h0 D18_ANKLE_CLEAR=0.0 D18_HEEL_PEAK=0.0
run clear0leg D18_ANKLE_CLEAR=0.0 D18_LEGROLL_MAX=40
run clear0leg0 D18_ANKLE_CLEAR=0.0 D18_LEGROLL_MAX=0
run nopinfoot D18_FOOT_PIN_BLEND=0
echo "=== done ==="
