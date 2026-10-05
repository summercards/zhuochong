#!/usr/bin/env bash
# 真凶：`[CHEST_UP, HAND_OFF]` 段肩每帧升 44 mm，手钉地 ⟹ 手臂角速度被放大（真旋转 40.88°/帧）
# 只加宽该段（CHEST_UP 提前 / HAND_OFF 后移），并顺带加宽窗口 B/C。全部 reach 安全。
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"
run() { local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python "$SRC" > "_d18_f2_${tag}.log" 2>&1; }

run X1 D18_LEGS_DOWN=3 D18_PLANT=7 D18_CHEST_UP=10 D18_TUCK=19 D18_FOOT_SET=26 &
run X2 D18_LEGS_DOWN=3 D18_PLANT=7 D18_CHEST_UP=10 D18_TUCK=19 D18_FOOT_SET=26 \
       D18_RISE_MID=31 D18_STAND=36 D18_TOTAL=38 &
run X3 D18_LEGS_DOWN=3 D18_PLANT=7 D18_CHEST_UP=10 D18_TUCK=19 D18_FOOT_SET=26 \
       D18_RISE_MID=32 D18_STAND=36 D18_TOTAL=38 &
run X4 D18_LEGS_DOWN=3 D18_PLANT=7 D18_CHEST_UP=10 D18_TUCK=19 D18_FOOT_SET=26 \
       D18_PLANT_DY2=-0.40 &
run X5 D18_LEGS_DOWN=4 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=18 D18_TUCK=20 \
       D18_FOOT_SET=27 D18_RISE_MID=31 D18_STAND=35 D18_TOTAL=37 &
run X6 D18_LEGS_DOWN=4 D18_PLANT=7 D18_CHEST_UP=10 D18_HAND_OFF=19 D18_TUCK=21 \
       D18_FOOT_SET=28 D18_RISE_MID=32 D18_STAND=36 D18_TOTAL=38 D18_STEPDBG=1 &
wait
for t in X1 X2 X3 X4 X5 X6; do
  printf "%-3s " "$t"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_f2_${t}.log" | head -1
  grep -o '"failed": \[[^]]*\]' "_d18_f2_${t}.log" | tail -1
  grep -o '"non_ok_bools": \[[^]]*\]' "_d18_f2_${t}.log" | tail -1
done
echo "=== done ==="
