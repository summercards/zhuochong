#!/usr/bin/env bash
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  local tag="$1"; shift
  printf "%-14s " "$tag"
  env PYTHONHASHSEED=0 SKIP_RENDER=1 \
      D18_ROLLWIN_OFF= D18_LEGROLL_MAX=40 D18_ARM_MIX_FROM=21 \
      D18_TOTAL=37 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=20 \
      D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35 "$@" \
      "$BL" --background --factory-startup --python probe_d18_gate_samples.py \
      > "_d18_foot_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_foot_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_foot_$tag.log" | tail -1
  grep -o '"failed": \[[^]]*\]' "_d18_foot_$tag.log" | tail -1
}
run base
run pin6          D18_FOOT_PIN_BLEND=6
run pin7          D18_FOOT_PIN_BLEND=7
run pin8          D18_FOOT_PIN_BLEND=8
run pin9          D18_FOOT_PIN_BLEND=9
run pin8hde14     D18_FOOT_PIN_BLEND=8 D18_HAND_DIR_END=14
run pin8hde12     D18_FOOT_PIN_BLEND=8 D18_HAND_DIR_END=12
run pin8tl19      D18_FOOT_PIN_BLEND=8 D18_TUCK_LEG=19
run pin8tdy05     D18_FOOT_PIN_BLEND=8 D18_TUCK_ANKLE_DY=0.05
run pin8tz16      D18_FOOT_PIN_BLEND=8 D18_TUCK_ANKLE_Z=0.16
