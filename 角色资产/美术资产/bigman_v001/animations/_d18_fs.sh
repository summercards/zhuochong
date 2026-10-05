#!/usr/bin/env bash
# D18：最终一轮结构扫描（落脚窗口加长 / 收腿提前 / 离地曲线重塑）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
BASE="D18_ARMYSOFT=8 D18_HAND_MIX_END=30 D18_HAND_MIX_POW=0 D18_STEPDBG=1 D18_STEPDBG_THR=18 D18_ROLLWIN_RAMP=0"

run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 $BASE "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_fs_${tag}.log" 2>&1
  local j f
  j=$(grep -o 'D18_STEP_ALL .*' "_d18_fs_${tag}.log" | head -1 | sed 's/D18_STEP_ALL //')
  f=$(grep -o '"failed": \[[^]]*\]' "_d18_fs_${tag}.log" | tail -1 | sed 's/"failed": //')
  if [ -z "$j" ]; then
    printf '%-16s  <none>=18  failed=%s\n' "$tag" "$f"
  else
    printf '%-16s  %s  failed=%s\n' "$tag" "$(printf '%s' "$j" | python -c "
import sys,json
d=json.loads(sys.stdin.read())
print(' '.join('%s@%d->%d(%.1f)'%(r[3],r[1],r[2],r[0]) for r in d[:4]), '| n>25=%d n>=18=%d'%(sum(1 for r in d if r[0]>25), len(d)))
")" "$f"
  fi
}

run base
run fs27        D18_FOOT_SET=27 D18_RISE_MID=31
run fs28        D18_FOOT_SET=28 D18_RISE_MID=32
run t19fs27     D18_TUCK=19 D18_TUCK_LEG=17 D18_FOOT_SET=27 D18_RISE_MID=31
run t19fs28     D18_TUCK=19 D18_TUCK_LEG=16 D18_FOOT_SET=28 D18_RISE_MID=32
CK="D18_ANKLE_CLEAR_KEYS=0:0,21:0,22:0.45,23:0.85,24:0.50,25:0,36:0"
run ck          $CK
run ckfs27      $CK D18_FOOT_SET=27 D18_RISE_MID=31
run ckfs27t19   $CK D18_FOOT_SET=27 D18_RISE_MID=31 D18_TUCK=19 D18_TUCK_LEG=17
run allbest     $CK D18_FOOT_SET=27 D18_RISE_MID=31 D18_TUCK=19 D18_TUCK_LEG=17 \
                D18_TUCK_ANKLE_DY=0.00 D18_TUCK_ANKLE_Z=0.16 D18_ANKLE_LIFT=0.6
echo "=== done ==="
