#!/usr/bin/env bash
# D18：默认值固化后的复核 + 反向验证（4 组能红的守卫）
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run () {
  local tag="$1"; shift
  echo "===== $tag ====="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 "$@" \
      "$BL" --background --factory-startup --python anim_getup_b.py \
      > "_d18_fin_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_fin_$tag.log" | tail -1
  grep -o '"failed": \[[^]]*\]' "_d18_fin_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_fin_$tag.log" | tail -1
}

run DEF                                   # 裸跑 = 新默认
run TP_SEAM D18_TP_SEAM_ZERO=1            # ① → seam_in_ok 红
run TP_PUSH D18_TP_NOPUSH=1               # ② → chest_rise_ok 红
run TP_TUCK D18_TP_NOTUCK=1               # ③ → foot_takeover_ok 红
run TP_STICKY D18_TP_STICKYHAND=1         # ④ → hand_off_ok 红
run TP_NOIDLE D18_TP_NOIDLE=1             # ⑤ → end_matches_idle_ok 红
run TP_DIP D18_TP_DIP=1                   # ⑥ → rise_monotone_ok 红
run TP_NOLEG D18_TP_NOLEGDROP=1           # ⑧ → knee_unfold_start_ok 红
echo "ALL DONE"
