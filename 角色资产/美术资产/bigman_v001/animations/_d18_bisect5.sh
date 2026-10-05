#!/usr/bin/env bash
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  local tag="$1"; shift
  printf "%-16s " "$tag"
  env PYTHONHASHSEED=0 SKIP_RENDER=1 \
      D18_ROLLWIN_OFF= D18_LEGROLL_MAX=40 \
      D18_TOTAL=37 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=20 \
      D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35 "$@" \
      "$BL" --background --factory-startup --python probe_d18_gate_samples.py \
      > "_d18_bi5_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_bi5_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_bi5_$tag.log" | tail -1
}
run repro1
run repro2
run s4     D18_ARMYSOFT=4
run s8     D18_ARMYSOFT=8
run s12    D18_ARMYSOFT=12
run s20    D18_ARMYSOFT=20
run w0_1   D18_ARMYWEIGHT=0.1
run w0_3   D18_ARMYWEIGHT=0.3
