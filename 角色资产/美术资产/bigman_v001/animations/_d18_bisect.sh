#!/usr/bin/env bash
# D18：把「我的会话改动」逐项摘掉，定位 no_teleport 的回归源
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run () {
  local tag="$1"; local mod="$2"; shift 2
  echo "===== $tag (mod=$mod) ====="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_MODULE="$mod" "$@" \
      "$BL" --background --factory-startup --python probe_d18_gate_samples.py \
      > "_d18_bi_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_bi_$tag.log" | tail -1
  grep -o '"failed": \[[^]]*\]' "_d18_bi_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_bi_$tag.log" | tail -1
}

run CUR_VER   anim_getup_b
run BAK_VER   _bak_getup_b_071112
