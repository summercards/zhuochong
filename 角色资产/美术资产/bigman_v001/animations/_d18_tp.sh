#!/usr/bin/env bash
# D18 反向验证 8 组：每个 D18_TP_* 旋钮都必须把它对应的守卫打红。
# 生产配置 = OUT_TOTAL 46。SKIP_RENDER=1（只要门禁数据）。
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
BASE="PYTHONHASHSEED=0 SKIP_RENDER=1 D18_ROLL_TRANSPORT=0 D18_ROLLWIN_OFF=
      D18_LEGROLL_MAX=40 D18_FOOT_PIN_BLEND=8 D18_ANKLE_LIFT=1.0
      D18_TOTAL=37 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=20
      D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35 D18_ARM_MIX_FROM=21
      D18_OUT_TOTAL=46"

GATES="seam_in_ok end_matches_idle_ok chest_rise_ok foot_takeover_ok hand_off_ok
       rise_monotone_ok knee_unfold_start_ok no_snap_stop_ok end_vz_zero_ok
       sole_ground_ok no_foot_slide_ok reach_ok hand_plant_ok"

show () {
  local tag="$1"
  printf "== %-14s " "$tag"
  grep -o 'failed=\[[^]]*\]' "_d18_tp_$tag.log" | tail -1 | tr -d '\n'
  printf " | non_ok="
  grep -o 'non_ok_bools=\[[^]]*\]' "_d18_tp_$tag.log" | tail -1 | sed 's/non_ok_bools=//' | tr -d '\n'
  printf " | "
  grep -o '"max_frame_step_deg": [0-9.]*' "_d18_tp_$tag.log" | tail -1 | tr -d '\n'
  echo ""
  # 逐条目标门禁的当前值
  for g in $GATES; do
    v=$(grep -o "\"$g\": [a-zA-Z]*" "_d18_tp_$tag.log" | tail -1 | sed "s/\"$g\": //")
    [ -n "$v" ] && printf "     %-24s %s\n" "$g" "$v"
  done
}

run () {
  local tag="$1"; shift
  env $(echo $BASE) "$@" \
      "$BL" --background --factory-startup --python anim_getup_b.py \
      > "_d18_tp_$tag.log" 2>&1
  show "$tag"
}

run base
run tp1_seamzero  D18_TP_SEAM_ZERO=1
run tp2_nopush    D18_TP_NOPUSH=1
run tp3_notuck    D18_TP_NOTUCK=1
run tp4_sticky    D18_TP_STICKYHAND=1
run tp5_noidle    D18_TP_NOIDLE=1
run tp6_dip       D18_TP_DIP=1
run tp7_endzero   D18_TP_ENDZERO=1
run tp8_nolegdrop D18_TP_NOLEGDROP=1
echo "=== DONE ==="
