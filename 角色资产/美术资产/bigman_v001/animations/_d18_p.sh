#!/usr/bin/env bash
# D18：落掌点（手撑在身后的多远）扫描 —— 风险 1 的正面缓解
# 现状：plant 点 y ≈ +985 mm、肩-拳 reach_ratio = 95.9%（贴满臂长）
#       ⟹ 手臂被逼到接近伸直 ⟹ 前臂穿过 |ry|≈90° 的万向节锁。
# 把手往脚方向收 ⟹ 缩短后伸行程、降低 reach_ratio。
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
BASE="D18_TUCK_LEG=19 D18_THIGH_ROLL=1 D18_LEGROLL_MAX=80 D18_ROLLWIN_OFF=16:21"

run () {
  local tag="$1"; shift
  echo "===== $tag ====="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 $BASE "$@" \
      "$BL" --background --factory-startup --python anim_getup_b.py \
      > "_d18_p_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_p_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_p_$tag.log" | tail -1
  grep -o '"reach_ratio_max": [0-9.]*' "_d18_p_$tag.log" | tail -1
  grep -o '"reach_ok": [a-z]*' "_d18_p_$tag.log" | tail -1
  grep -o '"hand_plant_ok": [a-z]*' "_d18_p_$tag.log" | tail -1
}

run P1 D18_PLANT_DY=-0.36 D18_PLANT_DY2=-0.41 D18_PLANT_DY_PULL=-0.24
run P2 D18_PLANT_DY=-0.43 D18_PLANT_DY2=-0.48 D18_PLANT_DY_PULL=-0.30
run P3 D18_PLANT_DY=-0.50 D18_PLANT_DY2=-0.55 D18_PLANT_DY_PULL=-0.35
run P4 D18_PLANT_DY=-0.36 D18_PLANT_DY2=-0.41 D18_PLANT_DY_PULL=-0.24 D18_HAND_FWD=0.62
run P5 D18_PLANT_DY=-0.43 D18_PLANT_DY2=-0.48 D18_PLANT_DY_PULL=-0.30 D18_HAND_DOWN=-0.12
echo "ALL DONE"
