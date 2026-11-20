"""عرض كل الخطوط جنباً إلى جنب — الحكم البصري، لا الرقمي."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw
from engine import common as C
from engine import identity as ID

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "identity_all_fonts.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
d = ID.load_identity()
ink = ID.palette_rgb("ink", d)
turq = ID.palette_rgb("turquoise", d)
paper = ID.palette_rgb("paper", d)
gold = ID.palette_rgb("gold", d)
margin = 60

im = Image.new("RGBA", (W, H), ink)
draw = ImageDraw.Draw(im)

# عنوان
title_pen = C.ArabicPen(str(ROOT / "assets/fonts/Amiri-Bold.ttf"), 42, bold=True, stroke=1)
title = title_pen.line_img("مقارنة الخطوط — اختر الأفضل", paper)
im.alpha_composite(title, ((W - title.width) // 2, 30))

FONTS = [
    ("Amiri",      "Amiri-Bold.ttf"),
    ("Reem Kufi",  "ReemKufi-Bold.ttf"),
    ("IBM Plex",   "IBMPlexSansArabic-Medium.ttf"),
    ("Cairo",      "Cairo-Bold.ttf"),
    ("Tajawal",    "Tajawal-Bold.ttf"),
]

y = 120
for label, file in FONTS:
    fp = ROOT / "assets" / "fonts" / file
    if not fp.exists():
        continue
    # اسم الخط
    lbl_pen = C.ArabicPen(str(ROOT / "assets/fonts/Amiri-Bold.ttf"), 32, bold=True)
    lbl = lbl_pen.line_img(f"◆ {label}", turq)
    im.alpha_composite(lbl, (W - margin - lbl.width, y))
    y += lbl.height + 10

    # عنوان بهذا الخط
    try:
        pen = C.ArabicPen(str(fp), 88, bold=True, stroke=1)
        t = pen.line_img("اختبار الهوية العربية", paper)
        im.alpha_composite(t, (W - margin - t.width, y))
        y += t.height + 8
    except Exception as e:
        print(f"⚠️ {label}: title failed: {e}")
        y += 100

    # نص صغير
    try:
        pen2 = C.ArabicPen(str(fp), 44, stroke=1)
        s = pen2.line_img("بِسْمِ اللَّهِ — ٣ إعدادات خفية", paper)
        im.alpha_composite(s, (W - margin - s.width, y))
        y += s.height + 8
    except Exception as e:
        print(f"⚠️ {label}: body failed: {e}")
        y += 60

    # خط ذهبي
    draw.rectangle([W - margin - 500, y, W - margin, y + 2], fill=gold)
    y += 30

im.convert("RGB").save(str(OUT), "PNG")
print(f"✅ demo: {OUT}")
