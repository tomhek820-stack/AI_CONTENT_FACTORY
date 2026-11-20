#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
mkdir -p logs output/scenes assets/images assets/backgrounds assets/music voice/lines
TS="$(date +%Y%m%d_%H%M%S)"; LOG="logs/build_$TS.log"
exec > >(tee -a "$LOG") 2>&1
PREVIEW=0; FAST=0; ENGINE="auto"; OFFLINE=0; FORCE=0; VISUAL=0; CHECK=0; ZIP=1; EXPORT=0
for a in "$@"; do
  case "$a" in
    --preview) PREVIEW=1 ;;
    --fast) FAST=1 ;;
    --offline) OFFLINE=1 ;;
    --force-voice) FORCE=1 ;;
    --visual-only) VISUAL=1 ;;
    --check-only) CHECK=1 ;;
    --no-zip) ZIP=0 ;;
    --export) EXPORT=1 ;;
    --engine=*) ENGINE="${a#*=}" ;;
    --help|-h) echo "bash generate.sh [--preview] [--fast] [--engine=auto|piper|edge|espeak|manual] [--offline] [--force-voice] [--visual-only] [--check-only] [--no-zip] [--export]"; exit 0 ;;
    *) echo "خيار غير معروف: $a"; exit 2 ;;
  esac
done
STATUS="logs/status_$TS.json"; CURRENT="preflight"
fail(){ printf '{"status":"failed","step":"%s","log":"%s"}\n' "$1" "$LOG" > "$STATUS"; echo ""; echo "❌ فشل في: $1"; echo "السجل: $LOG"; }
trap 'fail "$CURRENT"' ERR
trap 'command -v termux-wake-unlock >/dev/null 2>&1 && termux-wake-unlock >/dev/null 2>&1 || true' EXIT
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock >/dev/null 2>&1 || true
VID="$(python -c 'import json;print(json.load(open("config.json"))["video_id"])')"
VID="$(python -c 'import json;print(json.load(open("config.json"))["video_id"])')"
echo "ABU MOHAMMED — VIDEO $VID | $(date)"
echo "== 1/12 الأدوات =="
for b in ffmpeg ffprobe python; do command -v "$b" >/dev/null 2>&1 || { echo "مفقود: $b"; exit 1; }; done
ffmpeg -hide_banner -version | head -n 1
python -c 'import PIL,sys;print("Pillow",PIL.__version__,"py",sys.version.split()[0])'
echo "== 2/12 الملفات =="
for f in config.json scripts/video_001.txt voice/generate_voice.py engine/common.py engine/scenes.py engine/subtitles.py engine/audio.py engine/render.py; do
  [ -s "$f" ] || { echo "مفقود: $f"; exit 1; }
done
bash -n generate.sh
PF=""
if [ "$PREVIEW" = 1 ]; then PF="--preview"; fi
if [ "$CHECK" = 1 ]; then
  CURRENT="selftest"; python -m engine.selftest $PF
  printf '{"status":"checked"}\n' > "$STATUS"; exit 0
fi
echo "== 3/12 الأصول البصرية =="
CURRENT="assets"; python -m engine.scenes $PF
echo "== 4/12 التعليق الصوتي =="
CURRENT="voice"
if [ "$VISUAL" = 1 ]; then
  python voice/generate_voice.py --dry-timeline $PF
else
  VO="--engine=$ENGINE"
  if [ "$OFFLINE" = 1 ]; then VO="$VO --offline"; fi
  if [ "$FORCE" = 1 ]; then VO="$VO --force"; fi
  python voice/generate_voice.py $VO $PF
fi
echo "== 5/12 الترجمة =="
CURRENT="subtitles"
if [ "$VISUAL" = 1 ]; then python -m engine.subtitles --srt-only; else python -m engine.subtitles $PF; python -m engine.karaoke_v2 $PF; fi
echo "== 6/12 الموسيقى =="
CURRENT="music"
if [ "$VISUAL" != 1 ]; then python -m engine.audio; fi
echo "== 7-10/12 الرندر والمونتاج =="
CURRENT="render"
RO=""
if [ "$PREVIEW" = 1 ]; then RO="$RO --preview"; fi
if [ "$FAST" = 1 ]; then RO="$RO --fast"; fi
if [ "$VISUAL" = 1 ]; then RO="$RO --visual-only"; fi
python -m engine.render $RO
echo "== 11/12 ملفات النشر =="
CURRENT="publish"; python -m engine.publish
echo "== 12/12 الفحص النهائي =="
CURRENT="selftest"
if [ "$VISUAL" = 1 ]; then
  python -m engine.selftest --structure-only
  echo "⚠ معاينة بصرية فقط: output/preview_visual_only.mp4"
else
  python -m engine.selftest $PF
fi
if [ "$EXPORT" = 1 ] && [ -d /sdcard/Movies ] && [ "$VISUAL" != 1 ]; then
  mkdir -p /sdcard/Movies/ABU_MOHAMMED
  cp output/final_video.mp4 "/sdcard/Movies/ABU_MOHAMMED/ABU_MOHAMMED_${VID}.mp4" || true
  cp output/thumbnail.jpg "/sdcard/Movies/ABU_MOHAMMED/ABU_MOHAMMED_${VID}.jpg" || true
  echo "نُسخ إلى /sdcard/Movies/ABU_MOHAMMED"
fi
if [ "$ZIP" = 1 ] && command -v zip >/dev/null 2>&1; then
  CURRENT="zip"; Z="$ROOT/../ABU_MOHAMMED_VIDEO_${VID}.zip"; rm -f "$Z"
  ( cd "$ROOT/.." && zip -rq "$Z" "$(basename "$ROOT")" -x "*/logs/*" "*/output/scenes/*" "*/assets/backgrounds/*" "*/assets/images/*" "*/assets/voices/*" "*/voice/lines/*" "*/output/*.mp4" "*/output/*.wav" "*/__pycache__/*" "*/engine/__pycache__/*" )
  echo "ZIP: $ROOT/../ABU_MOHAMMED_VIDEO_${VID}.zip"
fi
printf '{"status":"success","log":"%s"}\n' "$LOG" > "$STATUS"
echo ""; echo "✅ نجح الإنتاج."
if [ "$VISUAL" != 1 ]; then ls -lh output/final_video.mp4 output/thumbnail.jpg; fi
