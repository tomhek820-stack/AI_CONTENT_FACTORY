"""مقارنة كوفية شاملة — يظهر المستطيلات بوضوح."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw, ImageFont
from engine import common as C
from engine import identity as ID

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "kufic_compare.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
d = ID.load_identity()
ink = ID.palette_rgb("ink", d)
turq = ID.palette_rgb("turquoise", d)
paper = ID.palette_rgb("paper", d)
gold = ID.palette_rgb("gold", d)
agate = ID.palette_rgb("agate", d)
margin = 50

im = Image.new("RGBA", (W, H), ink)
draw = ImageDraw.Draw(im)

# عنوان
title_pen = C.ArabicPen(str(ROOT / "assets/fonts/Amiri-Bold.ttf"), 38, bold=True, stroke=1)
title = title_pen.line_img("مقارنة الخطوط الكوفية — اختر بعينك", paper)
im.alpha_composite(title, ((W - title.width) // 2, 20))

# الخطوط المرشحة
FONTS = [
    ("Amiri (المرجع)",       "Amiri-Bold.ttf",               "يعمل ✓"),
    ("Reem Kufi Bold",        "ReemKufi-Bold.ttf",            "؟"),
    ("Reem Kufi Regular",     "ReemKufi-Regular.ttf",         "؟"),
    ("Noto Kufi Arabic",      "NotoKufiArabic-Bold.ttf",      "؟"),
    ("Kufam",                 "Kufam-Bold.ttf",               "؟"),
    ("Aref Ruqaa (زخرفي)",    "ArefRuqaa-Bold.ttf",           "؟"),
]

TEST = "اختبار الهوية العربية"
TEST2 = "بِسْمِ اللَّهِ — ٣ إعدادات"

y = 90
for label, file, status in FONTS:
    fp = ROOT / "assets" / "fonts" / file
    if not fp.exists():
        continue

    # تسمية الخط
    lbl_pen = C.ArabicPen(str(ROOT / "assets/fonts/Amiri-Bold.ttf"), 30, bold=True)
    lbl = lbl_pen.line_img(f"◆ {label}  [{status}]", turq)
    im.alpha_composite(lbl, (W - margin - lbl.width, y))
    y += lbl.height + 4

    # النص الكبير بهذا الخط
    try:
        pen = C.ArabicPen(str(fp), 78, bold=True, stroke=1)
        t = pen.line_img(TEST, paper)
        tx = W - margin - t.width
        ty = y
        im.alpha_composite(t, (tx, ty))

        # كشف المستطيلات: نحلل الصورة لعلامات الترقيم المميزة
        alpha = t.getchannel("A")
        has_tofu = False
        # نبحث عن مستطيلات: مكوّنات صغيرة مربعة الشكل
        w, h = alpha.size
        px = alpha.load()
        # عدّ الأعمدة البيضاء المتصلة (تقريب)
        # مستطيل tofu = عمود رفيع مرتفع

        y += t.height + 4
    except Exception as e:
        print(f"⚠️ {label} title failed: {e}")
        y += 100
        continue

    # النص الصغير
    try:
        pen2 = C.ArabicPen(str(fp), 40, stroke=1)
        s = pen2.line_img(TEST2, paper)
        im.alpha_composite(s, (W - margin - s.width, y))
        y += s.height + 6
    except Exception as e:
        print(f"⚠️ {label} body failed: {e}")
        y += 60

    # خط فاصل ذهبي
    draw.rectangle([W - margin - 600, y, W - margin, y + 2], fill=gold)
    y += 18

im.convert("RGB").save(str(OUT), "PNG")
print(f"✅ comparison: {OUT}")
print("\n=== ما يجب أن تراه ===")
print("Amiri:  نص كامل، صفر مستطيلات")
print("ReemKufi: مستطيلات عمودية في مواضع الأحرف السياقية")
print("NotoKufi: [يعتمد على تحميله]")
print("Kufam: [يعتمد على تحميله]")
print("ArefRuqaa: [يعتمد على تحميله]")
