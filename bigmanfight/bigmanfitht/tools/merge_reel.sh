#!/usr/bin/env bash
# =====================================================================
# 合成完整展示片：多动画展示 + 转场卡 + 实机对局
# =====================================================================
#
# 输入（三段各自独立产出，本脚本只做归一化与拼接）：
#   1. bigman_reel_v001/bigman_showcase_v001.mp4   多动画展示片 1280×720 / 30 fps
#   2. (本脚本生成) 转场字幕卡 2.5 s                与上同规格
#   3. gameplay_v001/gameplay_raw.avi              Godot 影片录制器直出 1280×720 / 60 fps
#
# 产物：
#   bigman_reel_v001/bigman_full_v001.mp4
#
# ---------------------------------------------------------------------
# **为什么不能直接把三段 concat 起来**（这是这个脚本存在的唯一理由）
#
# ① 帧率不同。实机录制必须是 60 fps（见 record.gd 头部：影片录制器把 delta
#    钉成 1/fps，60 Hz 是引擎物理帧的原生节奏）；而展示片是 30 fps。
#    直接 concat 会让合并点之后的时间基突变。
#
# ② 色彩范围不同 —— 而且**看不出来，只能量**。
#    影片录制器的 AVI(MJPEG) 是 **full range（pc，Y 0~255）**，
#    而展示片的 PNG 源经 libx264 编码后是 **limited range（tv，Y 16~235）**。
#    实测（RGB 往返比对，帧 0）：
#        AVI  → 解码回 RGB：YMIN 0, YAVG 70.9
#        PNG 源          ：YMIN 14, YAVG 59.3
#      两者差 14 个亮度级 ≈ 5.5%。直接 concat 的话，**实机那一段会整体发灰发亮**，
#      而且是渐变式的不一致（暗部差得多、亮部差得少），越看越像"这两段不是一个游戏"。
#
#    修法不是加 `tv_range` 标签，而是要**真的做一次范围映射**。
#    这里踩过一个坑：写
#        scale=1280:720:in_range=pc:out_range=tv
#    会**转换两次**（scale 转一次，输出又被当 full-range 转一次），
#    结果 YMIN 掉到 5~6（比 tv 的 16 还低，暗部被压爆）。实测三个变体：
#        A: scale=1280:720                            → YMIN 0,  YAVG 71.7   ✗ 没转
#        B: scale=...:in_range=pc:out_range=tv        → YMIN 5,  YAVG 81.1   ✗ 转两次
#        C: scale=...,format=rgb24,scale=...          → YMIN 0,  YAVG 70.9   ✗ 没转
#        ✓ 正确：scale=1280:720,format=yuv420p  → 由 ffmpeg 自动做一次 pc→tv 映射，
#                再用 `-color_range tv` 打上标签，RGB 往返与源逐级一致。
#
# ③ 音轨。录制器写的 AVI 带一条 28.9 s 的 PCM 占位音轨（项目里没有音频资产），
#    展示片无音轨。片子里不掺假声音，所以统一去掉音轨（`-an`）。
#
# 用法：
#   bash tools/merge_reel.sh              # 默认 full：展示片 + 字幕卡 + 实机对局
#   bash tools/merge_reel.sh gameplay     # 只出对局版：字幕卡 + 实机对局（不含展示片）
#   FFMPEG=/path/to/ffmpeg bash tools/merge_reel.sh     # 指定 ffmpeg
#
# 环境变量：
#   FFMPEG      ffmpeg 可执行文件（默认 /c/ffmpeg/bin/ffmpeg）
#   FONT        字幕字体（默认 C:/Windows/Fonts/msyh.ttc，微软雅黑）
#   WORKSPACE   工作区根（默认由脚本位置往上推两级）
# =====================================================================
set -euo pipefail

MODE="${1:-full}"
case "$MODE" in
  full|gameplay) ;;
  *) echo "未知模式：$MODE（可选 full | gameplay）" >&2; exit 2 ;;
esac

FFMPEG="${FFMPEG:-/c/ffmpeg/bin/ffmpeg}"
FFPROBE="${FFPROBE:-$(dirname "$FFMPEG")/ffprobe}"
FONT="${FONT:-C:/Windows/Fonts/msyh.ttc}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"           # .../BIGMANFIGHT/bigmanfight/bigmanfitht/tools
# 上三级 = 工作区根（tools → bigmanfitht → bigmanfight → BIGMANFIGHT）。
# 别想当然写成上两级：产物目录 outputs/ 挂在**最外层**的 BIGMANFIGHT 上，
# 和 record.gd 的 `_resolve_out_dir()` 对齐（那边从 res:// 往上退两级，
# 而 res:// 本身已经包含 bigmanfitht 这一层，所以正好等价）。
WORKSPACE="${WORKSPACE:-$(cd "$HERE/../../.." && pwd)}"

OUT_BASE="$WORKSPACE/outputs/bigman_reel_v001"
GAME_BASE="$WORKSPACE/outputs/gameplay_v001"
TMP="$WORKSPACE/outputs/_merge"

SHOWCASE="$OUT_BASE/bigman_showcase_v001.mp4"
RAW_AVI="$GAME_BASE/gameplay_raw.avi"
NORM_MP4="$GAME_BASE/gameplay_v001_720p30.mp4"
CARD_MP4="$TMP/card_gameplay.mp4"

# 产物名随模式走 —— 两个版本是**不同的片子**，不能共用一个文件名互相覆盖。
if [ "$MODE" = "gameplay" ]; then
  FINAL_MP4="$OUT_BASE/bigman_gameplay_v001.mp4"
else
  FINAL_MP4="$OUT_BASE/bigman_full_v002.mp4"
fi

# 全片统一规格 —— 三段都必须落在这上面，否则拼接点会露出破绽。
W=1280; H=720; FPS=30
# 编码参数取展示片同一套（High@4.1 / tv / bt709）。
VENC=(-c:v libx264 -preset slow -crf 18 -profile:v high -level 4.1
      -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv)

step() { printf '\n\033[36m== %s\033[0m\n' "$*"; }

REQUIRED=("$RAW_AVI")
[ "$MODE" = "full" ] && REQUIRED+=("$SHOWCASE")
for f in "${REQUIRED[@]}"; do
  if [ ! -f "$f" ]; then
    echo "缺少输入：$f" >&2
    echo "  $RAW_AVI 由 godot --write-movie 产生，见 tools/record.gd 头部用法。" >&2
    echo "  $SHOWCASE 由 godot res://tools/reel.tscn 出图后 ffmpeg 合成，见 tools/reel.gd 头部。" >&2
    exit 1
  fi
done

mkdir -p "$TMP"

# ---------------------------------------------------------------------
step "1/4  归一化实机录制：${FPS} fps + pc→tv 范围映射"
# 60 → 30 fps 取的是"每两帧留一帧"：录制器的 delta 被钉死在 1/60，
# 所以游戏时间 n/60 秒恰好是第 n 帧 —— 抽帧后第 m 帧 = 游戏时间 m/30 秒，
# 时间轴仍是严格的等距，不会有累积漂移。
# `scale` 里不写 in_range/out_range（会转两次，见脚本头部 ②），交给到
# yuv420p 的自动转换做一次映射，再用 -color_range tv 打标签。
# 已归一化过且比源 AVI 新 → 跳过（重压 191 MB AVI 要几十秒，重跑没必要重做）。
if [ -f "$NORM_MP4" ] && [ "$NORM_MP4" -nt "$RAW_AVI" ]; then
  echo "  已存在且比源新，跳过：$(basename "$NORM_MP4")"
else
  "$FFMPEG" -y -hide_banner -loglevel warning -stats \
    -i "$RAW_AVI" \
    -vf "fps=$FPS,scale=$W:$H,format=yuv420p" \
    -an "${VENC[@]}" -movflags +faststart \
    "$NORM_MP4"
fi

# ---------------------------------------------------------------------
step "2/4  生成转场字幕卡（2.5 s）"
"$FFMPEG" -y -hide_banner -loglevel warning \
  -f lavfi -i "color=c=0x070B08:s=${W}x${H}:d=2.5:r=$FPS" \
  -vf "drawtext=fontfile='${FONT//:/\\:}':text='实机对局':fontcolor=0x8CFFB0:fontsize=64:x=(w-text_w)/2:y=(h-text_h)/2-56,\
drawtext=fontfile='${FONT//:/\\:}':text='完整一局 · 连段 · 投技 · 技能 · 必杀 · K.O.':fontcolor=0x4FBF7A:fontsize=30:x=(w-text_w)/2:y=(h-text_h)/2+40" \
  "${VENC[@]}" -pix_fmt yuv420p -t 2.5 \
  "$CARD_MP4"

# ---------------------------------------------------------------------
step "3/4  拼接"
# 用 concat **滤镜**而不是 concat 分离器：各段的时间基/色彩元数据未必一致，
# 滤镜会把它们统一解码成同一种帧再拼，最稳。片子里不要假声音，统一 -an。
if [ "$MODE" = "gameplay" ]; then
  echo "  字幕卡 + 实机对局（不含展示片）"
  "$FFMPEG" -y -hide_banner -loglevel warning -stats \
    -i "$CARD_MP4" -i "$NORM_MP4" \
    -filter_complex "[0:v][1:v]concat=n=2:v=1:a=0,format=yuv420p[v]" \
    -map "[v]" -an "${VENC[@]}" -muxpreload 0 -muxdelay 0 -movflags +faststart \
    "$FINAL_MP4"
else
  echo "  展示片 + 字幕卡 + 实机对局"
  "$FFMPEG" -y -hide_banner -loglevel warning -stats \
    -i "$SHOWCASE" -i "$CARD_MP4" -i "$NORM_MP4" \
    -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0,format=yuv420p[v]" \
    -map "[v]" -an "${VENC[@]}" -muxpreload 0 -muxdelay 0 -movflags +faststart \
    "$FINAL_MP4"
fi

# ---------------------------------------------------------------------
step "4/4  核验：规格是否全片一致 + 各段边界是否对得上"
"$FFPROBE" -v error -select_streams v:0 \
  -show_entries stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,pix_fmt,profile,level,color_range \
  -show_entries format=duration,size -of default=noprint_wrappers=1 "$FINAL_MP4"

# 逐段时长（用 ffprobe 自己算，不手写 → 免得改了参数忘了改这里）
dur() { "$FFPROBE" -v error -show_entries format=duration -of csv=p=0 "$1"; }
D_CARD=$(dur "$CARD_MP4"); D_GAME=$(dur "$NORM_MP4"); D_OUT=$(dur "$FINAL_MP4")
if [ "$MODE" = "gameplay" ]; then
  D_SHOW=0
else
  D_SHOW=$(dur "$SHOWCASE")
fi
python - "$D_SHOW" "$D_CARD" "$D_GAME" "$D_OUT" "$MODE" <<'PY'
import sys
show, card, game, out, mode = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]
show, card, game, out = (float(x) for x in (show, card, game, out))
exp = show + card + game
if mode == "full":
    print(f"  展示片 {show:7.3f} s")
print(f"  字幕卡 {car