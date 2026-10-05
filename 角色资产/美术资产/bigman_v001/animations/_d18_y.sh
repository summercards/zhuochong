#!/usr/bin/env bash
# D18：欧拉「Y 惩罚」（避开万向节锁）扫描
# 代价函数：cost = max欧拉步长 + max(0,|ry| - YSAFE) * YWEIGHT
# C14（已验收）用的是 70 / 1.5；D18 自己改成了 88 / 0.0 —— 等于关掉了避锁。
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

run () {
  local tag="$1"; shift
  echo "===== $tag ====="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK_LEG=19 D18_THIGH_ROLL=1 \
      D18_LEGROLL_MAX=80 D18_ROLLWIN_OFF=16:21 "$@" \
      "$BL" --background --factory-startup --python anim_getup_b.py \
      > "_d18_y_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_y_$tag.log" | tail -1
  grep -o '"failed": \[[^]]*\]' "_d18_y_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_y_$tag.log" | tail -1
}

run Y1 D18_YSAFE=70 D18_YWEIGHT=1.5
run Y2 D18_YSAFE=80 D18_YWEIGHT=0.6
run Y3 D18_YSAFE=70 D18_YWEIGHT=0.4
run Y4 D18_YSAFE=60 D18_YWEIGHT=2.0
run Y5 D18_YSAFE=70 D18_YWEIGHT=1.5 D18_ARM_ROLL_PENALTY=0
echo "ALL DONE"
