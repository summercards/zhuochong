#!/usr/bin/env bash
# D18：多参数扫描（臂过渡铺开 + 滚转窗口），输出 max 与前几名超限点
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
BASE="D18_ARMYSOFT=8 D18_HAND_MIX_END=30 D18_HAND_MIX_POW=0 D18_STEPDBG=1 D18_STEPDBG_THR=18"

run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 $BASE "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_sw_${tag}.log" 2>&1
  local j
  j=$(grep -o 'D18_STEP_ALL .*' "_d18_sw_${tag}.log" | head -1 | sed 's/D18_STEP_ALL //')
  local f
  f=$(grep -o '"failed": \[[^]]*\]' "_d18_sw_${tag}.log" | tail -1 | sed 's/"failed": //')
  if [ -z "$j" ]; then
    printf '%-16s  <no offenders >=18>   failed=%s\n' "$tag" "$f"
  else
    printf '%-16s  %s   failed=%s\n' "$tag" "$(printf '%s' "$j" | python -c "
import sys,json
d=json.loads(sys.stdin.read())
top=d[:4]
print(' '.join('%s@f%d->%d'%(r[3],r[1],r[2]) for r in top), ' | n>25=%d n>=18=%d'%(sum(1 for r in d if r[0]>25), len(d)))
")" "$f"
  fi
}

run base
run R15         D18_ROLLWIN_OFF=15:21
run R14         D18_ROLLWIN_OFF=14:21
run R15p3       D18_ROLLWIN_OFF=15:21 D18_ROLLWIN_RAMP=3
run R14p3       D18_ROLLWIN_OFF=14:21 D18_ROLLWIN_RAMP=3
run nolift      D18_ANKLE_LIFT=0.0
run lift06      D18_ANKLE_LIFT=0.6
run lego60      D18_LEGROLL_MAX=60
run lego40      D18_LEGROLL_MAX=40
run legmid19    D18_TUCK_LEG=19
run legmid20    D18_TUCK_LEG=20
run nolift_leg  D18_ANKLE_LIFT=0.0 D18_TUCK_LEG=20
echo "=== done ==="
