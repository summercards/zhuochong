#!/usr/bin/env bash
# 死旋钮证伪：给极端值，若输出逐位不变 ⟹ 该旋钮未接线
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
SRC="_bak_getup_b_071112.py"
run() { local tag="$1"; shift
  env PYTHONHASHSEED=0 SKIP_RENDER=1 D18_TUCK=19 D18_THIGH_ROLL=1 "$@" \
    "$BL" --background --factory-startup --python "$SRC" > "_d18_dd_${tag}.log" 2>&1; }

run D0 &                                                          # 对照
run D1 D18_LIFT_KEYS="0:0.0,17:0.0,18:0.500,25:0.0,36:0.0" &       # 抬升 500 mm 单帧
run D2 D18_ARM_ANCHORS="0,36" &                                    # 只剩 2 个锚点
run D3 D18_ANCHOR_SLERP=0 &                                        # 关掉锚点 slerp
run D4 D18_HAND_MIX_END=36 &                                       # 混音窗推到末帧
run D5 D18_ARM_MIX_FROM=0 &
wait
for t in D0 D1 D2 D3 D4 D5; do
  printf "%-3s " "$t"
  grep -o '"max_frame_step_deg": [0-9.]*, "max_frame_step_at": \[[0-9]*, "[^"]*"\]' "_d18_dd_${t}.log" | head -1
  grep -o '"hand_off_ok": [a-z]*' "_d18_dd_${t}.log" | head -1
  grep -o '"reach_ok": [a-z]*' "_d18_dd_${t}.log" | head -1
done
echo "=== done ==="
