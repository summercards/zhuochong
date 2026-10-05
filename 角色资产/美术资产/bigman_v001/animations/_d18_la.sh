#!/usr/bin/env bash
# D18：收腿锚点 / 踝抬升 的「降速」扫描
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
BASE="D18_ARMYSOFT=8 D18_HAND_MIX_END=30 D18_HAND_MIX_POW=0 D18_STEPDBG=1 D18_STEPDBG_THR=18 D18_ROLLWIN_RAMP=0"

run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 $BASE "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_la_${tag}.log" 2>&1
  local j f
  j=$(grep -o 'D18_STEP_ALL .*' "_d18_la_${tag}.log" | head -1 | sed 's/D18_STEP_ALL //')
  f=$(grep -o '"failed": \[[^]]*\]' "_d18_la_${tag}.log" | tail -1 | sed 's/"failed": //')
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
run dy05   D18_TUCK_ANKLE_DY=0.05
run dy00   D18_TUCK_ANKLE_DY=0.00
run dym10  D18_TUCK_ANKLE_DY=-0.10
run z16    D18_TUCK_ANKLE_Z=0.16
run al06   D18_ANKLE_LIFT=0.6
run al03   D18_ANKLE_LIFT=0.3
run combo  D18_TUCK_ANKLE_DY=0.00 D18_TUCK_ANKLE_Z=0.16 D18_ANKLE_LIFT=0.6
run combo2 D18_TUCK_ANKLE_DY=-0.05 D18_TUCK_ANKLE_Z=0.14 D18_ANKLE_LIFT=0.4
run combo3 D18_TUCK_ANKLE_DY=0.00 D18_TUCK_ANKLE_Z=0.16 D18_ANKLE_LIFT=0.6 D18_ANKLE_CLEAR_MIX=0.5
echo "=== done ==="
