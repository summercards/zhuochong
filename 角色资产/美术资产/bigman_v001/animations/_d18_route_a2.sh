#!/usr/bin/env bash
# 出路 A 第二轮：**等比拉伸**（保持相位比例，只改帧率）vs 形状重排
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"

run() {
  local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python "$SRC" \
    > "_d18_ra_${tag}.log" 2>&1
}
# k = 拉伸系数；相位 = round(k × 36 帧原相位)，TUCK=round(k×19)（保留 T19 的加宽收益）
run RA4 D18_TOTAL=59 D18_LEGS_DOWN=7 D18_PLANT=13 D18_CHEST_UP=20 D18_HAND_OFF=28 \
       D18_TUCK=31 D18_FOOT_SET=41 D18_RISE_MID=49 D18_STAND=56 &
run RA5 D18_TOTAL=48 D18_LEGS_DOWN=5 D18_PLANT=11 D18_CHEST_UP=16 D18_HAND_OFF=23 \
       D18_TUCK=25 D18_FOOT_SET=33 D18_RISE_MID=40 D18_STAND=45 &
run RA6 D18_TOTAL=42 D18_LEGS_DOWN=5 D18_PLANT=9 D18_CHEST_UP=14 D18_HAND_OFF=20 \
       D18_TUCK=22 D18_FOOT_SET=29 D18_RISE_MID=35 D18_STAND=40 &
run RA1D D18_TOTAL=42 D18_LEGS_DOWN=5 D18_PLANT=9 D18_CHEST_UP=14 D18_HAND_OFF=20 \
       D18_TUCK=22 D18_FOOT_SET=29 D18_RISE_MID=35 D18_STAND=40 \
       D18_STEPDBG=1 D18_STEPDBG_THR=18 &
wait
for t in RA4 RA5 RA6 RA1D; do
  printf "%-5s " "$t"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_ra_${t}.log" | head -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_ra_${t}.log" | tail -1
done
echo "=== done ==="
