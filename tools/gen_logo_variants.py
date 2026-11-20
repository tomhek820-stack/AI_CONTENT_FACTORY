"""يولّد 6 نماذج شعار لأبو محمد المساوى بأسلوب احترافي."""
import sys, math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from engine import common as C
from engine import identity as ID

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "logos"
OUT.mkdir(parents=True, exist_ok=True)

d = ID.load_identity()
ink = ID.palette_rgb("ink", d)
turq = ID.palette_rgb("turquoise", d)
paper = ID.palette_rgb("paper", d)
gold = ID.palette_rgb("gold", d)

NAME = "أبو محمد المساوى"
SHORT = "أبو محمد"
FONT_AMIRI = ROOT / "assets" / "fonts" / "Amiri-Bold.ttf"
FONT_AREF = ROOT / "assets" / "fonts" / "ArefRuqaa-Bold.ttf"
FONT_LATEEF = ROOT / "assets" / "fonts" / "Lateef-Regular.ttf"
FONT_REEM = ROOT / "assets" / "fonts" / "ReemKufi-Bold.ttf"

SIZE = 1024  # شعار مربع كبير


def safe_font(preferred, fallback=FONT_AMIRI):
    return preferred if preferred.exists() else fallback


def draw_kufic_motif(d_draw, x, y, size, color):
    """زاوية معقلية 5×5."""
    pattern = [
        [0,1,1,1,0],
        [0,1,0,1,0],
        [0,1,1,1,0],
        [0,0,0,1,0],
        [0,0,0,1,1],
    ]
    cell = size // 5
    gap = max(1, cell // 10)
    for ry, row in enumerate(pattern):
        for rx, v in enumerate(row):
            if v:
                d_draw.rectangle(
                    [x + rx*cell, y + ry*cell,
                     x + rx*cell + cell - gap, y + ry*cell + cell - gap],
                    fill=color
                )


def draw_diamond(d_draw, cx, cy, size, color, width=4):
    """معين (diamond) - زخرفة."""
    pts = [(cx, cy-size), (cx+size, cy), (cx, cy+size), (cx-size, cy)]
    d_draw.polygon(pts, outline=color, width=width)


def text_image(text, font_path, size, color, stroke=0):
    """ينتج PIL Image للنص، أو None إن فشل."""
    try:
        pen = C.ArabicPen(str(font_path), size, bold=True, stroke=stroke)
        return pen.line_img(text, color)
    except Exception as e:
        print(f"⚠️ text_image failed: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# Style 1: دائرة كلاسيكية + الاسم داخل + معقلي أعلى
# ═══════════════════════════════════════════════════════════
def style_1_circle():
    im = Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))
    d_draw = ImageDraw.Draw(im)
    cx, cy = SIZE//2, SIZE//2
    r = 420
    # دائرة خارجية (ذهبي)
    d_draw.ellipse([cx-r-8, cy-r-8, cx+r+8, cy+r+8], outline=gold, width=5)
    # دائرة داخلية (فيروزي)
    d_draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=turq, width=12)
    # خلفية داخلية شفافة
    d_draw.ellipse([cx-r+12, cy-r+12, cx+r-12, cy+r-12], fill=(ink[0],ink[1],ink[2],220))
    # معقلي أعلى
    draw_kufic_motif(d_draw, cx-60, cy-r+40, 120, turq[:3]+(255,))
    # نص الاسم (Amiri)
    ti = text_image(NAME, FONT_AMIRI, 130, paper, stroke=1)
    if ti:
        im.alpha_composite(ti, (cx - ti.width//2, cy - ti.height//2 - 20))
    # خط ذهبي أسفل
    d_draw.rectangle([cx-180, cy+130, cx+180, cy+134], fill=gold)
    # معقلي أسفل
    draw_kufic_motif(d_draw, cx-40, cy+160, 80, gold[:3]+(255,))
    return im


# ═══════════════════════════════════════════════════════════
# Style 2: مستطيل ذهبي + زوايا معقلية + الاسم بخط Aref Ruqaa
# ═══════════════════════════════════════════════════════════
def style_2_framed():
    im = Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))
    d_draw = ImageDraw.Draw(im)
    m = 80
    # مستطيل خارجي
    d_draw.rounded_rectangle(
        [m, m+100, SIZE-m, SIZE-m-100],
        radius=20, outline=turq, width=8
    )
    # مستطيل داخلي رفيع
    d_draw.rounded_rectangle(
        [m+20, m+120, SIZE-m-20, SIZE-m-120],
        radius=15, outline=gold, width=2
    )
    # 4 زوايا معقلية
    draw_kufic_motif(d_draw, m+20, m+120, 100, turq[:3]+(255,))
    draw_kufic_motif(d_draw, SIZE-m-120, m+120, 100, turq[:3]+(255,))
    # النص بخط ArefRuqaa (زخرفي)
    fp = safe_font(FONT_AREF)
    ti = text_image(NAME, fp, 130, paper, stroke=1)
    if ti:
        im.alpha_composite(ti, ((SIZE-ti.width)//2, (SIZE-ti.height)//2 - 10))
    # خط ذهبي أسفل النص
    d_draw.rectangle([SIZE//2-200, SIZE//2+90, SIZE//2+200, SIZE//2+94], fill=gold)
    # "EST 2024" صغير
    fp_small = safe_font(FONT_LATEEF, FONT_AMIRI)
    ts = text_image("2024", fp_small, 40, gold, stroke=0)
    if ts:
        im.alpha_composite(ts, ((SIZE-ts.width)//2, SIZE//2+120))
    return im


# ═══════════════════════════════════════════════════════════
# Style 3: Monogram "أ م" كبير + الاسم صغيراً تحت
# ═══════════════════════════════════════════════════════════
def style_3_monogram():
    im = Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))
    d_draw = ImageDraw.Draw(im)
    cx, cy = SIZE//2, SIZE//2 - 80
    # دائرة ذهبية
    d_draw.ellipse([cx-380, cy-380, cx+380, cy+380], outline=gold, width=6)
    d_draw.ellipse([cx-360, cy-360, cx+360, cy+360], outline=turq, width=10)
    # خلفية
    d_draw.ellipse([cx-348, cy-348, cx+348, cy+348], fill=(ink[0],ink[1],ink[2],240))
    # مونوغرام "أم"
    mono = "أ.م"
    fp = safe_font(FONT_AREF)
    ti = text_image(mono, fp, 380, turq, stroke=2)
    if ti:
        im.alpha_composite(ti, (cx - ti.width//2, cy - ti.height//2))
    # الاسم أسفل الدائرة
    fp2 = safe_font(FONT_AMIRI)
    tn = text_image(NAME, fp2, 95, paper, stroke=1)
    if tn:
        im.alpha_composite(tn, ((SIZE-tn.width)//2, cy + 400))
    # خط ذهبي
    d_draw.rectangle([SIZE//2-180, cy+520, SIZE//2+180, cy+524], fill=gold)
    return im


# ═══════════════════════════════════════════════════════════
# Style 4: سداسي (hexagon) + الاسم + شريط ذهبي
# ═══════════════════════════════════════════════════════════
def style_4_hexagon():
    im = Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))
    d_draw = ImageDraw.Draw(im)
    cx, cy = SIZE//2, SIZE//2
    # سداسي
    r = 420
    pts = [(cx + r*math.cos(math.radians(60*i-90)),
            cy + r*math.sin(math.radians(60*i-90))) for i in range(6)]
    d_draw.polygon(pts, outline=gold, width=6)
    # سداسي داخلي
    r2 = 400
    pts2 = [(cx + r2*math.cos(math.radians(60*i-90)),
             cy + r2*math.sin(math.radians(60*i-90))) for i in range(6)]
    d_draw.polygon(pts2, outline=turq, width=8)
    # خلفية
    r3 = 385
    pts3 = [(cx + r3*math.cos(math.radians(60*i-90)),
             cy + r3*math.sin(math.radians(60*i-90))) for i in range(6)]
    d_draw.polygon(pts3, fill=(ink[0],ink[1],ink[2],230))
    # نص
    ti = text_image(NAME, safe_font(FONT_AMIRI), 120, paper, stroke=1)
    if ti:
        im.alpha_composite(ti, (cx - ti.width//2, cy - ti.height//2 - 20))
    # شريط ذهبي
    d_draw.rectangle([cx-220, cy+80, cx+220, cy+86], fill=gold)
    # معقلي صغير أعلى
    draw_kufic_motif(d_draw, cx-40, cy-260, 80, turq[:3]+(255,))
    return im


# ═══════════════════════════════════════════════════════════
# Style 5: طبقات دائرية + الاسم بخط Amiri + ظل
# ═══════════════════════════════════════════════════════════
def style_5_layered():
    im = Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))
    d_draw = ImageDraw.Draw(im)
    cx, cy = SIZE//2, SIZE//2
    # 3 دوائر متحدة المركز (متدرجة)
    for r, w, alpha in [(430, 4, 60), (410, 6, 120), (390, 10, 255)]:
        color = (turq[0], turq[1], turq[2], alpha)
        d_draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=color, width=w)
    # خلفية
    d_draw.ellipse([cx-378, cy-378, cx+378, cy+378],
                   fill=(ink[0],ink[1],ink[2],245))
    # نص بخط Amiri مع ظل
    ti_shadow = text_image(NAME, safe_font(FONT_AMIRI), 140, (0,0,0,180), stroke=1)
    if ti_shadow:
        im.alpha_composite(ti_shadow,
            (cx - ti_shadow.width//2 + 6, cy - ti_shadow.height//2 - 10 + 6))
    ti = text_image(NAME, safe_font(FONT_AMIRI), 140, paper, stroke=1)
    if ti:
        im.alpha_composite(ti, (cx - ti.width//2, cy - ti.height//2 - 10))
    # معقلي أعلى وأسفل (متماثل)
    draw_kufic_motif(d_draw, cx-50, cy-300, 100, turq[:3]+(255,))
    draw_kufic_motif(d_draw, cx-50, cy+200, 100, gold[:3]+(255,))
    return im


# ═══════════════════════════════════════════════════════════
# Style 6: Minimal حديث — شريط أفقي + الاسم في وسطه
# ═══════════════════════════════════════════════════════════
def style_6_minimal():
    im = Image.new("RGBA", (SIZE, SIZE), (0,0,0,0))
    d_draw = ImageDraw.Draw(im)
    cx, cy = SIZE//2, SIZE//2
    # شريط أفقي (خلفية)
    bar_h = 240
    d_draw.rectangle([80, cy - bar_h//2, SIZE-80, cy + bar_h//2],
                     fill=(ink[0],ink[1],ink[2],240),
                     outline=turq, width=4)
    # زخارف معقلية يمين ويسار
    draw_kufic_motif(d_draw, 100, cy-50, 100, turq[:3]+(255,))
    draw_kufic_motif(d_draw, SIZE-200, cy-50, 100, gold[:3]+(255,))
    # نص
    ti = text_image(NAME, safe_font(FONT_AMIRI), 130, paper, stroke=1)
    if ti:
        im.alpha_composite(ti, (cx - ti.width//2, cy - ti.height//2))
    # خط ذهبي رقيق فوق الشريط
    d_draw.rectangle([80, cy - bar_h//2 - 8, SIZE-80, cy - bar_h//2 - 5], fill=gold)
    # خط ذهبي رقيق تحت الشريط
    d_draw.rectangle([80, cy + bar_h//2 + 5, SIZE-80, cy + bar_h//2 + 8], fill=gold)
    return im


# ═══════════════════════════════════════════════════════════
# توليد كل الأنماط
# ═══════════════════════════════════════════════════════════
STYLES = [
    ("style_1_circle",   "1. دائرة كلاسيكية",  style_1_circle),
    ("style_2_framed",   "2. إطار مذهّب",       style_2_framed),
    ("style_3_monogram", "3. مونوغرام أم",       style_3_monogram),
    ("style_4_hexagon",  "4. سداسي هندسي",       style_4_hexagon),
    ("style_5_layered",  "5. طبقات متحدة",       style_5_layered),
    ("style_6_minimal",  "6. شريط حديث",         style_6_minimal),
]

print("═══ توليد 6 نماذج شعار ═══")
logos = []
for name, label, fn in STYLES:
    try:
        im = fn()
        p = OUT / f"{name}.png"
        im.save(str(p), "PNG", optimize=True)
        print(f"✅ {label}: {p.name} ({p.stat().st_size // 1024} KB)")
        logos.append((label, im))
    except Exception as e:
        print(f"❌ {label}: {e}")

# ═══════════════════════════════════════════════════════════
# شبكة مقارنة 3×2
# ═══════════════════════════════════════════════════════════
print("\n═══ بناء شبكة مقارنة ═══")
THUMB = 400
GAP = 30
LABEL_H = 60
COLS, ROWS = 3, 2
W_grid = COLS*THUMB + (COLS+1)*GAP
H_grid = ROWS*(THUMB + LABEL_H) + (ROWS+1)*GAP + 80

grid = Image.new("RGBA", (W_grid, H_grid), (15,15,22,255))

# عنوان
fp_title = safe_font(FONT_AMIRI)
t = text_image("6 نماذج شعار — اختر الأفضل", fp_title, 48, paper, stroke=1)
if t:
    grid.alpha_composite(t, ((W_grid - t.width)//2, 20))

try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS

for idx, (label, im) in enumerate(logos):
    col = idx % COLS
    row = idx // COLS
    x = GAP + col*(THUMB + GAP)
    y = 80 + GAP + row*(THUMB + LABEL_H + GAP)
    thumb = im.resize((THUMB, THUMB), RESAMPLE)
    grid.alpha_composite(thumb, (x, y))
    # label
    lbl = text_image(label, safe_font(FONT_LATEEF), 32, paper, stroke=0)
    if lbl:
        grid.alpha_composite(lbl, (x + (THUMB - lbl.width)//2, y + THUMB + 10))

grid.convert("RGB").save(str(OUT / "logos_compare.png"), "PNG", optimize=True)
print(f"✅ logos_compare.png")
print(f"\n📁 {OUT}")
