#!/usr/bin/env bash
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
PY="C:/Users/zhuangmenghong/.workbuddy/binaries/python/versions/3.13.12/python.exe"
BASE="PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ROLL_TRANSPORT=0 D18_ROLLWIN_OFF=
      D18_LEGROLL_MAX=40 D18_FOOT_PIN_BLEND=8 D18_ANKLE_LIFT=1.0
      D18_TOTAL=37 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=20
      D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35 D18_ARM_MIX_FROM=21"
dump () {
  local tag="$1"; shift
  env $(echo $BASE) D18_STEPDBG=1 D18_STEPDBG_THR=20 "$@" \
      "$BL" --background --factory-startup --python anim_getup_b.py \
      > "_d18_dbg_$tag.log" 2>&1
  printf "== %-8s " "$tag"
  grep -o '"max_frame_step_deg": [0-9.]*' "_d18_dbg_$tag.log" | tail -1
  echo "   --- top steps ---"
  grep -o 'D18_STEP_ALL .*' "_d18_dbg_$tag.log" | head -1 | \
    "$PY" -c "
import json,sys
line=sys.stdin.read().strip()
line=line[len('D18_STEP_ALL '):]
rows=json.loads(line)
for s,f0,f1,n,a,b in rows[:10]:
    print('     %7.2f  f%d->f%d  %-12s %s -> %s'%(s,f0,f1,n,a,b))
"
  echo "   --- hand_off / windows ---"
  grep -o '"hand_off_ok": [a-z]*\|"hand_off_min_mm": [0-9.]*\|"hand_off_violations": \[[^]]*\]\|"hand_off_contact_frames": \[[^]]*\]\|"foot_takeover_ok": [a-z]*\|"foot_touch_frames": \[[^]]*\]' "_d18_dbg_$tag.log" | tail -8
}
dump base37 D18_OUT_TOTAL=37
dump out42  D18_OUT_TOTAL=42
