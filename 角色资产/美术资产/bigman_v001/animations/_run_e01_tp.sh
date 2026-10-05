#!/usr/bin/env bash
# E01 反向验证 7 组（每组都必须看到红）。SKIP_RENDER=1 ⟹ 不落盘、不导出。
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run () {
  local tag="$1"; shift
  echo "=== TP $tag : $* ==="
  env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup \
      --python anim_stun.py > "_e01_tp_${tag}.log" 2>&1
  grep -a "^E01_DONE" "_e01_tp_${tag}.log" || echo "TP $tag NO E01_DONE"
}
run seamzero  E01_TP_SEAM_ZERO=1
run footsway  E01_TP_FOOTSWAY=1
run nosway    E01_TP_NOSWAY=1
run oneshot   E01_TP_ONESHOT=1
run loopbreak E01_TP_LOOPBREAK=1
run sink      E01_TP_SINK=1
run lift      E01_TP_LIFT=1
echo "ALL_TP_DONE"
