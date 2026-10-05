#!/usr/bin/env bash
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ROLL_TRANSPORT=0 D18_ROLLWIN_OFF= \
      D18_LEGROLL_MAX=40 D18_FOOT_PIN_BLEND=8 D18_ARM_MIX_FROM=21 \
      "$@" \
      "$BL" --background --factory-startup --python probe_d18_gate_samples.py \
      > "_d18_rp_$tag.log" 2>&1
  printf "== %-14s " "$tag"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]\|"failed": \[[^]]*\]\|"non_ok_bools": \[[^]]*\]' "_d18_rp_$tag.log" | tr '\n' ' '
  echo
}
A="D18_TOTAL=38 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=19 D18_TUCK=21 D18_FOOT_SET=28 \
   D18_RISE_MID=32 D18_STAND=36 D18_ARM_ANCHORS=18,20,27,36 D18_ANCHOR_SLERP_UNTIL=19"
run G1 $A
run G2 $A
run G3 $A
B="D18_TOTAL=38 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=19 D18_TUCK=21 D18_FOOT_SET=28 \
   D18_RISE_MID=32 D18_STAND=36 D18_ARM_ANCHORS=18,20,27,36 D18_ANCHOR_SLERP_UNTIL=19 \
   D18_OUT_TOTAL=38"
run G1o38 $B
run G1o40 D18_TOTAL=38 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=19 D18_TUCK=21 D18_FOOT_SET=28 \
   D18_RISE_MID=32 D18_STAND=36 D18_ARM_ANCHORS=18,20,27,36 D18_ANCHOR_SLERP_UNTIL=19 D18_OUT_TOTAL=40
run G1o44 D18_TOTAL=38 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=19 D18_TUCK=21 D18_FOOT_SET=28 \
   D18_RISE_MID=32 D18_STAND=36 D18_ARM_ANCHORS=18,20,27,36 D18_ANCHOR_SLERP_UNTIL=19 D18_OUT_TOTAL=44
