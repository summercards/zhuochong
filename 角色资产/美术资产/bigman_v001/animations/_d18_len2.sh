#!/usr/bin/env bash
# D18：加帧 × 滚转逃逸 组合扫描
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run () {
  local tag="$1"; shift
  echo "===== $tag ====="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 "$@" "$BL" --background --factory-startup \
      --python anim_getup_b.py > "_d18_len_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_len_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_len_$tag.log" | tail -1
}

# A42 + 滚转逃逸（腿 + 手臂滚转窗口）
run B42 D18_TOTAL=42 D18_LEGS_DOWN=4 D18_PLANT=8 D18_CHEST_UP=12 \
        D18_HAND_OFF=19 D18_TUCK=22 D18_FOOT_SET=26 D18_RISE_MID=34 D18_STAND=39 \
        D18_TUCK_LEG=20 D18_THIGH_ROLL=1 D18_ROLLWIN_OFF=18:23 D18_LEGROLL_MAX=80

# A42 + 滚转逃逸 + 全超限点 dump（看还剩哪些点）
run B42D D18_TOTAL=42 D18_LEGS_DOWN=4 D18_PLANT=8 D18_CHEST_UP=12 \
        D18_HAND_OFF=19 D18_TUCK=22 D18_FOOT_SET=26 D18_RISE_MID=34 D18_STAND=39 \
        D18_TUCK_LEG=20 D18_THIGH_ROLL=1 D18_ROLLWIN_OFF=18:23 D18_LEGROLL_MAX=80 \
        D18_STEPDBG=1 D18_STEPDBG_THR=18

# A45 + 滚转逃逸
run B45 D18_TOTAL=45 D18_LEGS_DOWN=5 D18_PLANT=10 D18_CHEST_UP=15 \
        D18_HAND_OFF=20 D18_TUCK=23 D18_FOOT_SET=27 D18_RISE_MID=36 D18_STAND=42 \
        D18_TUCK_LEG=21 D18_THIGH_ROLL=1 D18_ROLLWIN_OFF=19:24 D18_LEGROLL_MAX=80
echo "ALL DONE"
