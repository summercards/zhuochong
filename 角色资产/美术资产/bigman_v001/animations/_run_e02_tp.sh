#!/usr/bin/env bash
# E02 反向验证 9 组（每组**都必须看到目标门禁变红**）。SKIP_RENDER=1 ⟹ 不落盘、不导出。
# 用法：bash _run_e02_tp.sh
set -u
cd "$(dirname "$0")"
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
PY="C:/Users/zhuangmenghong/.workbuddy/binaries/python/versions/3.13.12/python.exe"

run () {
  local tag="$1"; local target="$2"; shift 2
  echo "=== TP ${tag} (期望红: ${target}) : $* ==="
  env SKIP_RENDER=1 "$@" "$BL" --background --factory-startup \
      --python anim_exhausted.py > "_e02_tp_${tag}.log" 2>&1
  "$PY" - "$tag" "$target" "_e02_tp_${tag}.log" <<'PYEOF'
import json, sys
tag, target, path = sys.argv[1], sys.argv[2], sys.argv[3]
try:
    s = open(path, encoding="utf-8").read()
    i = s.index("E02_REPORT ") + len("E02_REPORT ")
    d = json.loads(s[i:s.index("\n", i)])
except Exception as exc:                       # noqa: BLE001
    print("  TP %-9s READ_FAIL %s" % (tag, exc))
    sys.exit(0)
failed = d.get("failed", [])
hit = target in failed
print("  TP %-9s failed=%-55s %s"
      % (tag, str(failed), "RED_OK" if hit else "★惰性旋钮★ NOT_RED"))
PYEOF
}

run seamzero  seam_in_ok               E02_TP_SEAM_ZERO=1
run handfar   exh_hand_on_knee_ok      E02_TP_HANDFAR=1
run nobreath  exh_breath_ok            E02_TP_NOBREATH=1
run nobend    exh_bend_depth_ok        E02_TP_NOBEND=1
run toodeep   exh_bend_depth_ok        E02_TP_TOODEEP=1
run handclip  hand_leg_no_clip_ok      E02_TP_HANDCLIP=1
run footsway  exh_foot_lock_ok         E02_TP_FOOTSWAY=1
run loopbreak loop_seamless            E02_TP_LOOPBREAK=1
run oneshot   exh_breath_period_ok     E02_TP_ONESHOT=1
echo "ALL_TP_DONE"
