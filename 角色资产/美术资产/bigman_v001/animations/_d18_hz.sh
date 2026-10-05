#!/usr/bin/env bash
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ROLL_TRANSPORT=0 D18_ROLLWIN_OFF= \
      D18_FOOT_PIN_BLEND=8 \
      "$@" \
      "$BL" --background --factory-startup --python probe_d18_gate_samples.py \
      > "_d18_hz_$tag.log" 2>&1
  printf "== %-14s " "$tag"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]\|"failed": \[[^]]*\]\|"non_ok_bools": \[[^]]*\]' "_d18_hz_$tag.log" | tr '\n' ' '
  echo
}
C="D18_OUT_TOTAL=40 D18_TOTAL=40 D18_LEGS_DOWN=4 D18_PLANT=7 D18_CHEST_UP=10 \
   D18_HAND_OFF=18 D18_TUCK=20 D18_FOOT_SET=31 D18_RISE_MID=34 D18_STAND=38 \
   D18_ARM_MIX_FROM=20 D18_ARM_ANCHORS=17,19,30,38 D18_ANCHOR_SLERP_UNTIL=18"
run base   $C D18_LEGROLL_MAX=40
run hi34   $C D18_LEGROLL_MAX=40 D18_LEGROLL_HI=34
run hi36   $C D18_LEGROLL_MAX=40 D18_LEGROLL_HI=36
run hi38   $C D18_LEGROLL_MAX=40 D18_LEGROLL_HI=38
run hi38m80 $C D18_LEGROLL_MAX=80 D18_LEGROLL_HI=38
run hi38m20 $C D18_LEGROLL_MAX=20 D18_LEGROLL_HI=38
run hi38g1 $C D18_LEGROLL_MAX=40 D18_LEGROLL_HI=38 D18_ROLLWIN_POW=1
run hi38g2 $C D18_LEGROLL_MAX=40 D18_LEGROLL_HI=38 D18_ROLLWIN_POW=2
run hi38rt1 $C D18_LEGROLL_MAX=40 D18_LEGROLL_HI=38 D18_LEGROLL_RAMP=6
run hi38mid24 $C D18_LEGROLL_MAX=40 D18_LEGROLL_HI=38 D18_LEGROLL_MID=24
