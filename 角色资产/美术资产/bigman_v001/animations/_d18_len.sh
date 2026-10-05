#!/usr/bin/env bash
# D18 帧预算扫描：验证「no_teleport 是否只是帧数不够」
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run () {
  local tag="$1"; shift
  echo "===== $tag ====="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 "$@" "$BL" --background --factory-startup \
      --python anim_getup_b.py > "_d18_len_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_len_$tag.log" | tail -1
  grep -o '"failed": \[[^]]*\]' "_d18_len_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_len_$tag.log" | tail -1
  grep -o '"hand_off_ok": [a-zA-Z]*' "_d18_len_$tag.log" | tail -1
  grep -o '"knee_unfold_start_ok": [a-zA-Z]*' "_d18_len_$tag.log" | tail -1
  grep -o '"rise_reach_ok": [a-zA-Z]*' "_d18_len_$tag.log" | tail -1
}

# A42：定向重排（doc §5 出路 A）
run A42 D18_TOTAL=42 D18_LEGS_DOWN=4 D18_PLANT=8 D18_CHEST_UP=12 \
        D18_HAND_OFF=19 D18_TUCK=22 D18_FOOT_SET=26 D18_RISE_MID=34 D18_STAND=39

# A40：计划允许的硬上界
run A40 D18_TOTAL=40 D18_LEGS_DOWN=4 D18_PLANT=8 D18_CHEST_UP=12 \
        D18_HAND_OFF=18 D18_TUCK=22 D18_FOOT_SET=26 D18_RISE_MID=32 D18_STAND=37

# A45：比 A42 再宽一档
run A45 D18_TOTAL=45 D18_LEGS_DOWN=5 D18_PLANT=10 D18_CHEST_UP=15 \
        D18_HAND_OFF=20 D18_TUCK=23 D18_FOOT_SET=27 D18_RISE_MID=36 D18_STAND=42

# A59：整体等比 1.639×
run A59 D18_TOTAL=59 D18_LEGS_DOWN=7 D18_PLANT=13 D18_CHEST_UP=20 \
        D18_HAND_OFF=28 D18_TUCK=34 D18_FOOT_SET=41 D18_RISE_MID=49 D18_STAND=56
echo "ALL DONE"
