#!/bin/bash
BL="D:/Program Files/Blender Foundation/Blender 4.5/blender.exe"
run() { local tag="$1"; shift
  env "$@" SKIP_RENDER=1 "$BL" --background --factory-startup --python anim_knockdown_b.py > "_d15_v_$tag.log" 2>&1
  echo "== $tag done =="; }
run BASE &                          # 正式默认（不带任何环境变量）—— 必须全绿
run TP1 D15_TP_SEAM_ZERO=1 &        # ① 首帧改零位 ⟹ seam_in_ok 红
run TP2 D15_TP_BUMP=30 &            # ② 触地帧骨盆 +30mm ⟹ ballistic/landing_no_bounce 红
run TP3 D15_TP_NOVZ=1 &             # ③ 抽 vz 继承 ⟹ vz_fall_then_stop_ok 红
run TP4 D15_TP_NOSUPINE=1 &         # ④ 抽后倒主驱动 ⟹ supine_pitch_ok/compress_present_ok 红
run TP5 D15_TP_FLIPSIGN=1 &         # ⑤ 后倒俯仰翻正 ⟹ supine_pitch_ok 红
run TP6 D15_TP_NOLEGS=1 &           # ⑥ 抽抬腿驱动 ⟹ legs_lift_ok 红
wait; echo ALLDONE
