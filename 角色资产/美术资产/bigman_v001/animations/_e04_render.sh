#!/usr/bin/env bash
# E04 `Spawn` 出图批次：主渲（静帧 / 侧 / 正 / key / landmark / .blend+GLB）
#   + 四组**反面对照**重渲（同相机、同帧集合、**两个机位**）。
# ★ 反面重渲只走 `E04_STEM_ONLY=1` 分支 —— 该分支**不** save_project / export_glb，
#   所以不会污染正式 .blend / GLB。
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"

echo "=== [1/5] MAIN (spawnwide/spawn_side/spawn_front/spawnkey + landmark + save + glb) ==="
"$BL" --background --factory-startup --python anim_spawn.py > _e04_final_render.log 2>&1
grep -E "E04_DONE|E04_FAILURE" _e04_final_render.log | tail -3

echo "=== [2/5] STEM ② NOSINK (期望：px_spawn_head_drop_ok 红) ==="
E04_STEM_ONLY=1 E04_STEM=spawnsink E04_TP_NOSINK=1 \
  "$BL" --background --factory-startup --python anim_spawn.py > _stem_spawnsink.log 2>&1
grep -E "E04_DONE|E04_FAILURE" _stem_spawnsink.log | tail -2

echo "=== [3/5] STEM ⑤ GLUED (期望：px_spawn_airborne_ok 红) ==="
E04_STEM_ONLY=1 E04_STEM=spawnlift E04_TP_GLUED=1 \
  "$BL" --background --factory-startup --python anim_spawn.py > _stem_spawnlift.log 2>&1
grep -E "E04_DONE|E04_FAILURE" _stem_spawnlift.log | tail -2

echo "=== [4/5] STEM ⑦ FOOTSWAY (期望：px_spawn_foot_lock_ok 红) ==="
E04_STEM_ONLY=1 E04_STEM=spawnfoot E04_TP_FOOTSWAY=1 \
  "$BL" --background --factory-startup --python anim_spawn.py > _stem_spawnfoot.log 2>&1
grep -E "E04_DONE|E04_FAILURE" _stem_spawnfoot.log | tail -2

echo "=== [5/5] STEM ⑨ FOOTASYM (期望：px_spawn_feet_sym_ok 红) ==="
E04_STEM_ONLY=1 E04_STEM=spawnasym E04_TP_FOOTASYM=1 \
  "$BL" --background --factory-startup --python anim_spawn.py > _stem_spawnasym.log 2>&1
grep -E "E04_DONE|E04_FAILURE" _stem_spawnasym.log | tail -2

echo ALL_RENDER_DONE
