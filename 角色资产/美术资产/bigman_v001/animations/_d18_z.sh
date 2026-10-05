#!/usr/bin/env bash
# D18：★ 关键实验 —— 在「滚转可用」的前提下加 Y 惩罚
# 前一次 Y 惩罚扫描无效的原因：base 里带了 D18_ROLLWIN_OFF=16:21，
# 而 16–21 正是 |ry|≈90° 的万向节锁窗口 —— 滚转被关掉 ⟹ 换支只能在锁里选。
# 本次把窗口打开，让「绕骨轴滚转」真的可用。
cd "I:/工作项目/BIGMANFIGHT/角色资产/美术资产/bigman_v001/animations" || exit 1
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
BASE="D18_TUCK_LEG=19 D18_THIGH_ROLL=1 D18_LEGROLL_MAX=80"

run () {
  local tag="$1"; shift
  echo "===== $tag ====="
  env PYTHONHASHSEED=0 SKIP_RENDER=1 $BASE "$@" \
      "$BL" --background --factory-startup --python anim_getup_b.py \
      > "_d18_z_$tag.log" 2>&1
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[A-Za-z._0-9]*"\]' "_d18_z_$tag.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_z_$tag.log" | tail -1
}

run Z0                                  # 关窗口、无 Y 惩罚
run Z1 D18_YSAFE=80 D18_YWEIGHT=0.6
run Z2 D18_YSAFE=70 D18_YWEIGHT=1.5
run Z3 D18_YSAFE=75 D18_YWEIGHT=1.0
run Z4 D18_YSAFE=85 D18_YWEIGHT=0.3
echo "ALL DONE"
