"""يولّد 6 نسخ intro_v3 بخلفيات مختلفة للمقارنة."""
import sys
import math
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter
from engine import common as C
from engine import identity as ID

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "bg_variants"
OUT.mkdir(parents=True, exist_ok=True)
MOTIFS = ROOT / "assets" / "motifs"

W, H = 1080, 1920
d = ID.load_identity()
ink = ID.palette_rgb("ink", d)
turq = ID.palette_rgb("turquoise", d)
paper = ID.palette_rgb("paper", d)
gold = ID.palette_rgb("gold", d)
margin = 96

TITLE = "هاتفك بطيء؟ المشكلة ليست فيه"
SUBTITLE = "الحلقة السادسة: تسريع الهاتف"

def make_solid_ink():
    return Image.new("RGBA", (W, H), ink)

def make_radial_glow():
    """توهج دائري خفيف من المركز."""
    im = Image.new("RGBA", (W, H), ink)
    # توهج ناعم
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    # تدرج عبر دوائر متحدة المركز
    steps = 60
    for i in range(steps):
        r = int((1 - i / steps) * W * 0.9)
        alpha = int(12 * (i / steps))
        cx, cy = W // 2, int(H * 0.42)
        color = (turq[0], turq[1], turq[2], alpha)
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    im.alpha_composite(glow)
    return im

def make_vertical_gradient():
    """تدرج عمودي: ink أعلى → توهج فيروزي خافت أسفل."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = im.load()
    for y in range(H):
        # 0 أعلى (ink) → 1 أسفل (ink + turquoise خفيف)
        t = y / H
        # منحنى غير خطي (يبدأ الضوء عند 60%)
        intensity = max(0.0, (t - 0.55) / 0.45) ** 2
        r = int(ink[0] + (turq[0] - ink[0]) * intensity * 0.15)
        g = int(ink[1] + (turq[1] - ink[1]) * intensity * 0.15)
        b = int(ink[2] + (turq[2] - ink[2]) * intensity * 0.15)
        for x in range(W):
            px[x, y] = (r, g, b, 255)
    return im

def make_kufic_texture():
    """خلفية موتيفات معقلية صغيرة خافتة (نمط)."""
    im = Image.new("RGBA", (W, H), ink)
    pattern = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pattern)
    cell = 40
    color = (turq[0], turq[1], turq[2], 10)  # شفاف جداً
    # شبكة خفيفة
    for y in range(0, H, cell):
        for x in range(0, W, cell):
            # نمط متقطع (ليس كل مربع)
            if (x // cell + y // cell) % 3 == 0:
                pd.rectangle([x + 8, y + 8, x + cell - 8, y + cell - 8], fill=color)
    im.alpha_composite(pattern)
    return im

def make_horizon_glow():
    """خط ضوء أفقي رقيق في المنتصف."""
    im = Image.new("RGBA", (W, H), ink)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    # خط أفقي فيروزي خافت جداً
    y_center = int(H * 0.42)
    for offset in range(-80, 81, 4):
        alpha = max(0, 25 - abs(offset) // 4)
        if alpha > 0:
            gd.rectangle([0, y_center + offset, W, y_center + offset + 3],
                         fill=(turq[0], turq[1], turq[2], alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    im.alpha_composite(glow)
    return im

def make_vignette():
    """خلفية ink مع vignette (حواف داكنة، مركز أوضح قليلاً)."""
    im = Image.new("RGBA", (W, H), ink)
    # رفع خفيف للمركز
    lift = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lift)
    steps = 40
    for i in range(steps):
        r = int((1 - i / steps) * W * 0.85)
        alpha = int(8 * (i / steps))
        cx, cy = W // 2, int(H * 0.45)
        ld.ellipse([cx - r, cy - r, cx + r, cy + r],
                   fill=(240, 235, 220, alpha))  # دفء خفيف
    lift = lift.filter(ImageFilter.GaussianBlur(80))
    im.alpha_composite(lift)
    return im

def make_gold_horizon():
    """خط ذهبي أفقي رقيق جداً كعنصر ثابت (الهوية)."""
    im = Image.new("RGBA", (W, H), ink)
    dd = ImageDraw.Draw(im)
    # خط ذهبي رفيع عند y=1400
    y = 1400
    dd.rectangle([margin, y, W - margin, y + 1], fill=(gold[0], gold[1], gold[2], 60))
    return im

BACKGROUNDS = [
    ("v1_solid",         make_solid_ink,     "حبر صلب (الحالي)"),
    ("v2_radial",        make_radial_glow,   "توهج دائري مركزي"),
    ("v3_vertical",      make_vertical_gradient, "تدرج عمودي (فيروز أسفل)"),
    ("v4_kufic_tex",     make_kufic_texture, "نسيج معقلي خافت"),
    ("v5_horizon",       make_horizon_glow,  "خط ضوء أفقي"),
    ("v6_vignette",      make_vignette,      "Vignette (حواف داكنة)"),
]

def render_scene(bg_fn, title, subtitle):
    im = bg_fn()

    # motif
    motif_path = MOTIFS / "corner_kufic.png"
    if motif_path.exists():
        motif = Image.open(str(motif_path)).convert("RGBA")
        im.alpha_composite(motif, (984, 180))

    # title
    title_fp = ID.font_path("title", d)
    pen_t = C.ArabicPen(str(title_fp), 92, bold=True, stroke=1)
    title_img = pen_t.line_img(title, paper)
    tx = W - margin - title_img.width
    ty = 760
    im.alpha_composite(title_img, (tx, ty))

    # gold rule
    dd = ImageDraw.Draw(im)
    rule_y = ty + title_img.height + 20
    rule_w = int(W * 0.40)
    dd.rectangle([W - margin - rule_w, rule_y, W - margin, rule_y + 2], fill=gold)

    # subtitle
    body_fp = ID.font_path("body", d)
    pen_s = C.ArabicPen(str(body_fp), 52, stroke=0)
    sub_img = pen_s.line_img(subtitle, turq)
    sx = W - margin - sub_img.width
    sy = rule_y + 30
    im.alpha_composite(sub_img, (sx, sy))

    # channel name
    wisdom_fp = ID.font_path("wisdom", d)
    pen_w = C.ArabicPen(str(wisdom_fp), 44, bold=True, stroke=1)
    w_img = pen_w.line_img("أبو محمد المساوى", paper)
    alpha = w_img.getchannel("A").point(lambda v: int(v * 0.7))
    w_img.putalpha(alpha)
    wx = W - margin - w_img.width
    wy = H - 260
    im.alpha_composite(w_img, (wx, wy))

    return im

print("═════════════ توليد 6 خلفيات ═════════════")
for name, fn, desc in BACKGROUNDS:
    im = render_scene(fn, TITLE, SUBTITLE)
    path = OUT / f"{name}.png"
    im.convert("RGB").save(str(path), "PNG", optimize=True)
    print(f"✅ {name:20s} | {desc:30s} | {path.stat().st_size // 1024} KB")

print(f"\n📁 {OUT}")
