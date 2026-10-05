#!/usr/bin/env bash
# E02 `Exhausted` 出图批次：主渲（静帧 / 单件层 / kneescreen / .blend+GLB）
#   + 三组**反面对照**重渲（同相机、同 hold 帧集合）。
# ★ 反面重渲只走 `E02_STEM_ONLY=1` 分支 —— 该分支**不** save_project / export_glb，
#   所以不会污染正式 .blend / GLB。
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

echo "=== [1/4] MAIN (exhwide / exh / exhkey / exhhand + kneescreen + save + glb) ==="
"$BL" --background --factory-startup --python anim_exhausted.py 2>&1 \
  | grep -E "E02_DONE|E02_FAILURE" | tail -3

echo "=== [2/4] STEM ① HANDFAR (期望: exh_hand_on_knee_ok 红) ==="
E02_STEM_ONLY=1 E02_STEM=exhfar E02_STEM_HAND=exhfarhand E02_TP_HANDFAR=1 \
  "$BL" --background --factory-startup --python anim_exhausted.py 2>&1 \
  | grep -E "E02_DONE|E02_FAILURE" | tail -2

echo "=== [3/4] STEM ② NOBREATH (期望: exh_breath_ok 红) ==="
E02_STEM_ONLY=1 E02_STEM=exhnobreath E02_STEM_HAND=exhnobreathhand E02_TP_NOBREATH=1 \
  "$BL" --background --factory-startup --python anim_exhausted.py 2>&1 \
  | grep -E "E02_DONE|E02_FAILURE" | tail -2

echo "=== [4/4] STEM ③ FOOTSWAY (期望: exh_foot_lock_ok 红) ==="
E02_STEM_ONLY=1 E02_STEM=exhfootsway E02_STEM_HAND=exhfootswayhand E02_TP_FOOTSWAY=1 \
  "$BL" --background --factory-startup --python anim_exhausted.py 2>&1 \
  | grep -E "E02_DONE|E02_FAILURE" | tail -2

echo ALL_RENDER_DONE
