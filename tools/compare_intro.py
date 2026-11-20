import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw
try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS

ROOT = Path(__file__).resolve().parent.parent
OLD = ROOT / "golden" / "016" / "frame_10.png"
NEW = ROOT / "spike_tmp" / "intro_v3.png"
OUT = ROOT / "spike_tmp" / "intro_compare.png"

old = Image.open(str(OLD)).convert("RGBA")
new = Image.open(str(NEW)).convert("RGBA")
if old.size != new.size:
    old = old.resize(new.size, RESAMPLE)

gap = 20
label_h = 70
W = old.width + new.width + gap * 3
H = max(old.height, new.height) + label_h + gap * 2

canvas = Image.new("RGBA", (W, H), (20, 20, 30, 255))

try:
    from engine import common as C
    from engine import identity as ID
    d = ID.load_identity()
    font_path = ID.font_path("title", d)
    pen = C.ArabicPen(str(font_path), 42, bold=True, stroke=1)
    old_lbl = pen.line_img("016 (القديم)", (255, 255, 255, 255))
    new_lbl = pen.line_img("017 (الجديد)", (15, 181, 168, 255))
    canvas.alpha_composite(old_lbl, (gap, 15))
    canvas.alpha_composite(new_lbl, (gap * 2 + old.width, 15))
except Exception as e:
    print(f"⚠️ labels: {e}")

canvas.alpha_composite(old, (gap, label_h))
canvas.alpha_composite(new, (gap * 2 + old.width, label_h))

canvas.convert("RGB").save(str(OUT), "PNG", optimize=True)

from PIL import ImageChops, ImageStat
diff = ImageChops.difference(old.convert("RGB"), new.convert("RGB"))
stat = ImageStat.Stat(diff)
mean = sum(stat.mean[:3]) / 3.0
pct = mean / 255.0 * 100.0
print(f"📊 Diff: {pct:.2f}% (للمرجع فقط)")
print(f"✅ {OUT} ({OUT.stat().st_size // 1024} KB)")
