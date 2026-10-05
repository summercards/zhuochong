#!/usr/bin/env bash
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
OFF="D18_ROLLWIN_OFF= D18_LEGROLL_MAX=40"
run () {
  local tag="$1"; shift
  printf "%-14s " "$tag"
  env PYTHONHASHSEED=0 SKIP_RENDER=1 "$@" \
      "$BL" --background --factory-startup --python probe_d18_gate_samples.py \
      > "_d18_bi3_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_bi3_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_bi3_$tag.log" | tail -1
}
run T36off  $OFF
run T37     $OFF D18_TOTAL=37 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=20 D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35
run T38     $OFF D18_TOTAL=38 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=21 D18_FOOT_SET=28 D18_RISE_MID=32 D18_STAND=36
run T39     $OFF D18_TOTAL=39 D18_PLANT=8 D18_CHEST_UP=11 D18_HAND_OFF=19 D18_TUCK=22 D18_FOOT_SET=29 D18_RISE_MID=33 D18_STAND=37
run T40     $OFF D18_TOTAL=40 D18_PLANT=8 D18_CHEST_UP=11 D18_HAND_OFF=19 D18_TUCK=23 D18_FOOT_SET=30 D18_RISE_MID=34 D18_STAND=38
