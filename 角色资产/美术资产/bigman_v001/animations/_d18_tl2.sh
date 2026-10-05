#!/usr/bin/env bash
# D18：时间轴重排扫描（把「收腿→落脚」摊到更多帧）
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
BASE="D18_ARMYSOFT=8 D18_HAND_MIX_END=30 D18_HAND_MIX_POW=0 D18_STEPDBG=1 D18_STEPDBG_THR=18 D18_ROLLWIN_RAMP=0"

run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 $BASE "$@" \
    "$BL" --background --factory-startup --python anim_getup_b.py \
    > "_d18_tl2_${tag}.log" 2>&1
  local j f
  j=$(grep -o 'D18_STEP_ALL .*' "_d18_tl2_${tag}.log" | head -1 | sed 's/D18_STEP_ALL //')
  f=$(grep -o '"failed": \[[^]]*\]' "_d18_tl2_${tag}.log" | tail -1 | sed 's/"failed": //')
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

# 基准（36 帧）
run base

# 40 帧：把 TUCK_LEG 提前、FOOT_SET 推后
run T40a D18_TOTAL=40 D18_LEGS_DOWN=5 D18_PLANT=9 D18_CHEST_UP=14 D18_HAND_OFF=19 \
         D18_TUCK=23 D18_TUCK_LEG=15 D18_FOOT_SET=29 D18_RISE_MID=33 D18_STAND=37
run T40b D18_TOTAL=40 D18_LEGS_DOWN=5 D18_PLANT=9 D18_CHEST_UP=14 D18_HAND_OFF=19 \
         D18_TUCK=22 D18_TUCK_LEG=14 D18_FOOT_SET=30 D18_RISE_MID=34 D18_STAND=38
run T40c D18_TOTAL=40 D18_LEGS_DOWN=5 D18_PLANT=10 D18_CHEST_UP=15 D18_HAND_OFF=20 \
         D18_TUCK=23 D18_TUCK_LEG=13 D18_FOOT_SET=31 D18_RISE_MID=35 D18_STAND=39
# 42 / 44 帧
run T42a D18_TOTAL=42 D18_LEGS_DOWN=6 D18_PLANT=11 D18_CHEST_UP=16 D18_HAND_OFF=21 \
         D18_TUCK=24 D18_TUCK_LEG=15 D18_FOOT_SET=32 D18_RISE_MID=36 D18_STAND=40
run T44a D18_TOTAL=44 D18_LEGS_DOWN=6 D18_PLANT=11 D18_CHEST_UP=17 D18_HAND_OFF=22 \
         D18_TUCK=25 D18_TUCK_LEG=15 D18_FOOT_SET=33 D18_RISE_MID=37 D18_STAND=41
echo "=== done ==="
