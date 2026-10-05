#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_v_$tag.log" 2>&1
  echo "== $tag done =="; }
run BASE &                    # 重跑正式默认（确认修 NO_LEGS 没动到基线）
run TP6 D15_TP_NOLEGS=1 &     # ⑥ 抽抬腿驱动 ⟹ legs_lift_ok 必红
wait; echo ALLDONE
