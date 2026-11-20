#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"
mkdir -p logs tmp output
TS="$(date +%Y%m%d_%H%M%S)"
LOG="logs/studio_$TS.log"
exec > >(tee -a "$LOG") 2>&1

ID="${1:-011}"
PREVIEW=0; FAST=0
for a in "$@"; do
  case "$a" in
    --preview) PREVIEW=1 ;;
    --fast) FAST=1 ;;
  esac
done

SCRIPT="$ROOT/scripts/video_$ID.txt"
[ -s "$SCRIPT" ] || { echo "السيناريو مفقود: $SCRIPT"; exit 1; }

python3 - "$ID" <<'PY'
import json, pathlib, sys
vid = sys.argv[1]
p = pathlib.Path("config.json")
c = json.loads(p.read_text(encoding="utf-8"))
mp = pathlib.Path("scripts/publish_%s.json" % vid)
m = json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
c["video_id"] = vid
if m.get("title"):
    c["title"] = m["title"]
c["project"] = "أبو محمد المساوى"
p.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")
print("ACTIVE:", vid, "|", c["title"])
PY

python3 - "$SCRIPT" <<'PY'
import json, pathlib, re, sys
from PIL import Image, ImageDraw, ImageFont
from engine import common as C
MARKS = re.compile("[\u064B-\u0652\u0670\u0653-\u0655]")
p = pathlib.Path(sys.argv[1])
out = []
for line in p.read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s and not s.startswith("#"):
        f = [x.strip() for x in s.split("|")]
        if f[0] == "LINE":
            f[2] = MARKS.sub("", f[2])
            if len(f) > 3:
                f[3] = MARKS.sub("", f[3])
            out.append("|".join(f)); continue
    out.append(line)
p.write_text("\n".join(out) + "\n", encoding="utf-8")

c = C.cfg(); C._CFG = c
texts = []
for line in p.read_text(encoding="utf-8").splitlines():
    f = [x.strip() for x in line.split("|")]
    if f and f[0] == "LINE":
        texts.append(f[2])
    elif f and f[0] == "SCENE":
        texts += [f[3], f[4]]
        if len(f) > 6 and f[6]:
            texts += [x.strip() for x in f[6].split(",") if x.strip()]
pen = C.ArabicPen(C.resolve_font(verbose=False), 48)
chars = set()
for t in texts:
    for tok in t.split():
        chars.update(ch for ch in pen._prep(tok, True) if not ch.isspace())
def miss(fp):
    f = ImageFont.truetype(str(fp), 64)
    def b(ch):
        im = Image.new("L", (150, 150), 0)
        ImageDraw.Draw(im).text((10, 10), ch, font=f, fill=255)
        return im.tobytes()
    nd = b("\uE123")
    return [ch for ch in chars if b(ch) == nd]
cur = pathlib.Path(C.resolve_font(verbose=False))
m = miss(cur)
if not m:
    print("FONT OK:", cur.name)
else:
    for n in ["Amiri-Bold.ttf", "Amiri-Regular.ttf", "NotoNaskhArabic-Regular.ttf"]:
        q = pathlib.Path("assets/fonts") / n
        if q.exists() and not miss(q):
            cfg = json.loads(pathlib.Path("config.json").read_text(encoding="utf-8"))
            cfg["font"]["override"] = str(q); cfg["font"]["bold_override"] = str(q)
            pathlib.Path("config.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
            print("FONT FIX ->", n); break
PY

export AILAB_SCRIPT="$SCRIPT"
python3 voice/normalize_name.py "$SCRIPT" >/dev/null
PF=""; RF=""
if [ "$PREVIEW" = 1 ]; then PF="--preview"; RF="--preview"; fi
if [ "$FAST" = 1 ]; then RF="$RF --fast"; fi

echo "== 1/3 الصوت =="
python voice/generate_voice.py --engine=edge --force $PF || python voice/generate_voice.py --force $PF

echo "== 2/3 الاستوديو =="
python -m engine.studio --script "$SCRIPT" $RF

echo "== 3/3 التصدير =="
mkdir -p "output/$ID"
cp output/studio_final.mp4 "output/$ID/final_video.mp4"
cp output/studio_thumbnail.jpg "output/$ID/thumbnail.jpg"
cp output/publish_description.txt "output/$ID/publish_description.txt" 2>/dev/null || true
cp scripts/subtitles.srt "output/$ID/" 2>/dev/null || true
cp output/studio_report.json "output/$ID/report.json" 2>/dev/null || true

mkdir -p /sdcard/Movies/ABU_MOHAMMED 2>/dev/null || true
cp "output/$ID/final_video.mp4" "/sdcard/Movies/ABU_MOHAMMED/ABU_MOHAMMED_$ID.mp4" 2>/dev/null || true
cp "output/$ID/thumbnail.jpg" "/sdcard/Movies/ABU_MOHAMMED/ABU_MOHAMMED_$ID.jpg" 2>/dev/null || true

echo ""
echo "✅ الفيديو $ID جاهز"
ls -lh "output/$ID/final_video.mp4"
cat "output/$ID/report.json" 2>/dev/null || true
echo "📱 /sdcard/Movies/ABU_MOHAMMED/ABU_MOHAMMED_$ID.mp4"
