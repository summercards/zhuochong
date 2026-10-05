#!/usr/bin/env bash
# D18：手离地节奏（释放段）旋钮扫描 —— 真实旋转峰值就在交接帧
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
LIFT="0:0,17:0,18:0.02,19:0.05,20:0.09,21:0.12,23:0.10,24:0.05,25:0,36:0"

run () {
  local tag="$1"; shift
  echo "===== $tag ====="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK_LEG=19 D18_THIGH_ROLL=1 \
      D18_LEGROLL_MAX=80 D18_ROLLWIN_OFF=16:21 "$@" \
      "$BL" --background --factory-startup --python anim_getup_b.py \
      > "_d18_rel_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_rel_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_rel_$tag.log" | tail -1
}

run BASE
run L1 D18_LIFT_KEYS="$LIFT"
run L2 D18_HAND_MIX_END=32
run L3 D18_HAND_MIX_END=32 D18_HAND_MIX_POW=2.0
run L4 D18_LIFT_KEYS="$LIFT" D18_HAND_MIX_END=30
run L5 D18_ARM_MIX_FROM=21 D18_HAND_MIX_END=30
echo "ALL DONE"
