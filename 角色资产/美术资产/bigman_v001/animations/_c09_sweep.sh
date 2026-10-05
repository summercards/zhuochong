#!/bin/bash
B="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() {
  local tag="$1"; shift
  env "$@" SKIP_RENDER=1 "$B" --background --factory-startup --python anim_skill01.py > "_c09_sw_$tag.log" 2>&1
  python - "$tag" <<'PY'
import json,re,sys
tag=sys.argv[1]
t=open("_c09_sw_%s.log"%tag,encoding="utf-8",errors="replace").read()
m=re.search(r"C09_REPORT (\{.*\})",t)
if not m:
    print("%-8s NO_REPORT"%tag); raise SystemExit
d=json.loads(m.group(1))
sil=d.get("silhouette_lead_mm",{})
print("%-8s failed=%-28s head_tail_lead=%-8s head_mesh_lead=%-8s shoe=%s"%(
  tag, d["failed"], d.get("hit_point_worst_lead_mm"),
  sil.get("head"), sil.get("shoe")))
PY
}
run "$@"
