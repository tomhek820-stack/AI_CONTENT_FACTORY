#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; cd "$ROOT"
ID="${1:-}"; shift || true
if [ -z "$ID" ]; then echo "usage: bash produce.sh 002 [--preview] [--fast] [--export]"; exit 2; fi
SC="scripts/video_$ID.txt"
[ -s "$SC" ] || { echo "مفقود: $SC"; exit 1; }
mkdir -p logs archive output
LAST="$(cat logs/last_id 2>/dev/null || true)"
if [ -n "$LAST" ] && [ "$LAST" != "$ID" ]; then
  mkdir -p "archive/$LAST"
  for f in output/final_video.mp4 output/thumbnail.jpg output/thumbnail_yt.jpg output/publish_description.txt scripts/subtitles.srt voice/timeline.json; do
    if [ -s "$f" ]; then cp "$f" "archive/$LAST/"; fi
  done
  echo "أُرشف إنتاج $LAST في archive/$LAST"
fi
python - "$ID" <<'PY'
import json, sys, pathlib
vid = sys.argv[1]
p = pathlib.Path("config.json"); c = json.loads(p.read_text(encoding="utf-8"))
mp = pathlib.Path("scripts/publish_%s.json" % vid)
m = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
c["video_id"] = vid
if m.get("title"): c["title"] = m["title"]
p.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
print("ACTIVE:", vid, "|", c["title"])
PY
export AILAB_SCRIPT="$ROOT/$SC"
bash generate.sh --force-voice "$@"
echo "$ID" > logs/last_id
mkdir -p "output/$ID"
for f in output/final_video.mp4 output/thumbnail.jpg output/thumbnail_yt.jpg output/publish_description.txt; do
  if [ -s "$f" ]; then cp "$f" "output/$ID/"; fi
done
cp scripts/subtitles.srt "output/$ID/" 2>/dev/null || true
echo "✅ منشور $ID جاهز في output/$ID/"
