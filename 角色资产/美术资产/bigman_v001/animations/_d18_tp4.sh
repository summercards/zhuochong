#!/usr/bin/env bash
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
BASE="PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ROLL_TRANSPORT=0 D18_ROLLWIN_OFF=
      D18_LEGROLL_MAX=40 D18_FOOT_PIN_BLEND=8 D18_ANKLE_LIFT=1.0
      D18_TOTAL=37 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=20
      D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35 D18_ARM_MIX_FROM=21
      D18_OUT_TOTAL=46"
run () {
  local tag="$1"; shift
  env $(echo $BASE) "$@" \
      "$BL" --background --factory-startup --python anim_getup_b.py \
      > "_d18_tp_$tag.log" 2>&1
  printf "== %-12s " "$tag"
  grep -o 'failed=\[[^]]*\]' "_d18_tp_$tag.log" | tail -1 | tr -d '\n'
  printf " | non_ok="
  grep -o 'non_ok_bools=\[[^]]*\]' "_d18_tp_$tag.log" | tail -1 | sed 's/non_ok_bools=//' | tr -d '\n'
  printf " | "
  grep -o '"max_frame_step_deg": [0-9.]*' "_d18_tp_$tag.log" | tail -1
}
run base2
run tp4_sticky D18_TP_STICKYHAND=1
