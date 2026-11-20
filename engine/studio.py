"""محرك الاستوديو: بطاقات متحركة احترافية + كاريوكي محسّن + موسيقى + ترميز عالي الجودة."""
from __future__ import annotations
import argparse, json, math, random, struct, wave
from pathlib import Path
from engine import common as C

def _draw_tool_icon(d, icon_name, x, y, w, h, color):
    """رسم أيقونات الأدوات برمجياً لضمان العمل دون إنترنت."""
    cx, cy = x + w / 2, y + h / 2
    r = min(w, h) / 2
    
    if icon_name == "python":
        # شعار بايثون مبسط (ثعبانين)
        d.pieslice([x, y, x+w, y+h], start=90, end=270, fill=color, outline=(255,255,255,50), width=3)
        d.ellipse([cx-r*0.3, cy-r*0.3, cx+r*0.3, cy+r*0.3], fill=(255,255,255,200))
    elif icon_name == "git":
        # شعار Git (شكل سداسي مع فروع)
        pts = [(cx + r*math.cos(math.radians(60*i-90)), cy + r*math.sin(math.radians(60*i-90))) for i in range(6)]
        d.polygon(pts, fill=color, outline=(255,255,255,50), width=3)
        d.ellipse([cx-r*0.25, cy-r*0.25, cx+r*0.25, cy+r*0.25], fill=(255,255,255,200))
        d.line([(cx, cy-r*0.25), (cx, cy+r*0.25)], fill=(255,255,255,200), width=4)
        d.line([(cx-r*0.22, cy), (cx+r*0.22, cy)], fill=(255,255,255,200), width=4)
    elif icon_name == "github":
        # شعار GitHub (رأس قطة مبسط)
        d.ellipse([x+2, y+2, x+w-2, y+h-2], fill=color, outline=(255,255,255,50), width=3)
        d.ellipse([cx-r*0.4, cy-r*0.1, cx-r*0.1, cy+r*0.2], fill=(0,0,0,100)) # أذن يسار
        d.ellipse([cx+r*0.1, cy-r*0.1, cx+r*0.4, cy+r*0.2], fill=(0,0,0,100)) # أذن يمين
    elif icon_name == "android":
        # روبوت أندرويد
        d.ellipse([cx-r*0.6, cy-r*0.7, cx+r*0.6, cy-r*0.1], fill=color, outline=(255,255,255,50), width=3)
        d.rectangle([cx-r*0.7, cy-r*0.1, cx+r*0.7, cy+r*0.6], fill=color, outline=(255,255,255,50), width=3)
        d.ellipse([cx-r*0.4, cy-r*0.5, cx-r*0.2, cy-r*0.3], fill=(255,255,255,200)) # عين
        d.ellipse([cx+r*0.2, cy-r*0.5, cx+r*0.4, cy-r*0.3], fill=(255,255,255,200)) # عين
    elif icon_name == "terminal":
        # شاشة طرفية
        d.rounded_rectangle([x+4, y+4, x+w-4, y+h-4], radius=8, fill=color, outline=(255,255,255,50), width=3)
        d.line([(cx-r*0.4, cy), (cx-r*0.1, cy-r*0.3)], fill=(255,255,255,220), width=4)
        d.line([(cx-r*0.1, cy-r*0.3), (cx-r*0.1, cy+r*0.3)], fill=(255,255,255,220), width=4)
        d.line([(cx+r*0.1, cy), (cx+r*0.4, cy)], fill=(255,255,255,220), width=4)
    elif icon_name == "chatgpt":
        # شعار ChatGPT مبسط (نجمة سداسية)
        pts = []
        for i in range(12):
            angle = math.radians(30 * i - 90)
            rad = r if i % 2 == 0 else r * 0.5
            pts.append((cx + rad * math.cos(angle), cy + rad * math.sin(angle)))
        d.polygon(pts, fill=color, outline=(255,255,255,50), width=3)
    elif icon_name == "search":
        d.ellipse([x+4, y+4, x+w*0.7, y+h*0.7], outline=color, width=4)
        d.line([(x+w*0.6, y+h*0.6), (x+w-4, y+h-4)], fill=color, width=5)
    elif icon_name == "design":
        d.rounded_rectangle([x+4, y+4, x+w-4, y+h-4], radius=12, outline=color, width=4)
        d.polygon([(x+w*0.2, y+h*0.8), (x+w*0.5, y+h*0.2), (x+w*0.8, y+h*0.8)], fill=color)
    elif icon_name == "video":
        d.rounded_rectangle([x+4, y+4, x+w-4, y+h-4], radius=12, outline=color, width=4)
        d.polygon([(x+w*0.4, y+h*0.3), (x+w*0.4, y+h*0.7), (x+w*0.75, y+h*0.5)], fill=color)
    elif icon_name == "rocket":
        d.polygon([(cx, y+4), (x+w-4, y+h*0.7), (cx, y+h*0.8), (x+4, y+h*0.7)], outline=color, width=4)
    elif icon_name == "chat":
        d.rounded_rectangle([x+4, y+4, x+w-4, y+h*0.75], radius=12, outline=color, width=4)
        d.polygon([(x+w*0.25, y+h*0.75), (x+w*0.45, y+h*0.75), (x+w*0.25, y+h*0.95)], fill=color)
    else:
        # افتراضي: نجمة أو دائرة
        d.ellipse([x+4, y+4, x+w-4, y+h-4], fill=color, outline=(255,255,255,50), width=3)


def _get_icon_path(icon_name):
    p = ROOT / "assets" / "icons" / f"{icon_name.lower()}.png"
    return p if p.exists() else None


ROOT = C.ROOT
TMP = ROOT / "tmp"
OUT = C.OUT
IMG = C.IMG
BG = C.BG


def ensure_dirs():
    for d in (TMP, OUT, IMG, BG, OUT / "scenes"):
        d.mkdir(parents=True, exist_ok=True)


def parse_script(path):
    scenes = []
    for raw in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        f = [x.strip() for x in line.split("|")]
        if f[0] == "SCENE":
            scenes.append({
                "id": f[1], "kind": f[2], "title_ar": f[3],
                "subtitle": f[4] if len(f) > 4 else "",
                "icon": f[5] if len(f) > 5 else "spark",
                "chips": [x.strip() for x in f[6].split(",") if x.strip()] if len(f) > 6 and f[6] else [],
                "lines": [],
            })
        elif f[0] == "LINE" and scenes:
            scenes[-1]["lines"].append({
                "tts": f[1], "screen": f[2],
                "hl": [x.strip() for x in f[3].split(",") if x.strip()] if len(f) > 3 and f[3] else [],
            })
    if not scenes:
        C.die("السيناريو فارغ")
    return scenes


def bg_image(idx, W, H, variant="tool"):
    from PIL import Image, ImageDraw, ImageChops, ImageOps, ImageFilter, ImageEnhance
    b = C.cfg()["brand"]
    rnd = random.Random(7100 + idx * 211)
    sc = 1.30
    W2, H2 = int(W * sc), int(H * sc)
    qw, qh = max(2, W2 // 4), max(2, H2 // 4)

    # تدرّج فيلمي ثلاثي: أسود مزرق -> navy -> أسود، مع لمسة بنفسجية في الظلال
    g = Image.new("RGB", (1, 512)); px = g.load()
    A = (4, 6, 13); B = (11, 24, 48); D = (4, 7, 16)
    for y in range(512):
        t = y / 511.0
        if t < 0.46:
            k = t / 0.46
            col = tuple(int(A[i] + (B[i] - A[i]) * k) for i in range(3))
        else:
            k = (t - 0.46) / 0.54
            col = tuple(int(B[i] + (D[i] - B[i]) * k) for i in range(3))
        px[0, y] = (int(col[0] * 0.96 + 6), int(col[1] * 0.94 + 5), int(col[2] * 0.98 + 9))
    base = g.resize((W2, H2), Image.BILINEAR)

    # مركز البطاقة = موضع عنصر البطل
    cy_map = {"intro": 0.42, "tool": 0.45, "outro": 0.48}
    cyf = cy_map.get(variant, 0.45)
    cx, cy = W2 * 0.5, H2 * cyf
    ring_r = W2 * 0.44
    power = 1.16 if variant == "intro" else (0.90 if variant == "outro" else 1.0)

    # 1) مخروط ضوء علوي (spotlight)
    cone = Image.new("L", (qw, qh), 0)
    cd = ImageDraw.Draw(cone)
    ox = qw * (0.5 + (0.10 if idx % 2 else -0.10))
    cd.polygon([(ox, -qh * 0.05), (qw * 0.02, qh * 0.72), (qw * 0.98, qh * 0.72)], fill=52)
    cone = cone.filter(ImageFilter.GaussianBlur(10))
    tint = Image.merge("RGB", (cone.point(lambda v: int(v * 0.34)),
                               cone.point(lambda v: int(v * 0.72)), cone))
    base = ImageChops.screen(base, tint.resize((W2, H2), Image.BILINEAR))

    # 2) قوس البطل حول البطاقة (عنصر التركيز الوحيد)
    ring = Image.new("L", (qw, qh), 0)
    rdw = ImageDraw.Draw(ring)
    rx, ry, rr = cx / 4, cy / 4, ring_r / 4
    lw = max(2, int(qw * 0.010))
    rdw.arc([rx - rr, ry - rr, rx + rr, ry + rr], start=196, end=344, fill=225, width=lw)
    rdw.arc([rx - rr, ry - rr, rx + rr, ry + rr], start=16, end=164, fill=150, width=lw)
    rr2 = rr * 1.10
    rdw.arc([rx - rr2, ry - rr2, rx + rr2, ry + rr2], start=205, end=335, fill=70, width=max(1, lw // 2))
    halo = ring.filter(ImageFilter.GaussianBlur(7))
    core = ring.filter(ImageFilter.GaussianBlur(1.4))
    for layer, gain in ((halo, 0.85), (core, 1.0)):
        L = layer.point(lambda v: int(v * gain * power))
        rgb = Image.merge("RGB", (L.point(lambda v: int(v * 0.22)),
                                  L.point(lambda v: int(v * 0.74)), L))
        base = ImageChops.screen(base, rgb.resize((W2, H2), Image.BILINEAR))

    # 3) شريط أنامورفي أفقي واحد عند مستوى القوس
    st = Image.new("L", (qw, qh), 0)
    ImageDraw.Draw(st).ellipse([qw * 0.03, ry - qh * 0.008, qw * 0.97, ry + qh * 0.008], fill=105)
    st = st.filter(ImageFilter.GaussianBlur(3))
    base = ImageChops.screen(base, Image.merge("RGB", (st.point(lambda v: int(v * 0.28)),
                                                       st.point(lambda v: int(v * 0.80)), st)
                                               ).resize((W2, H2), Image.BILINEAR))

    # 4) نسيج خفيف جدًا: نقاط فقط + خط أفق واحد
    d = ImageDraw.Draw(base, "RGBA")
    step = max(34, int(W2 * 0.052))
    for yy in range(0, H2, step):
        for xx in range(0, W2, step):
            d.ellipse([xx, yy, xx + 2, yy + 2], fill=(60, 128, 210, 16))
    hz = int(H2 * 0.74)
    d.line([(0, hz), (W2, hz)], fill=(40, 120, 205, 30), width=2)
    for i in range(-6, 7):
        d.line([(W2 // 2, hz), (W2 // 2 + i * int(W2 * 0.26), H2)], fill=(34, 112, 196, 20), width=2)

    # 5) جزيئات: طبقة بعيدة ناعمة + قريبة حادة
    far = Image.new("RGBA", (W2, H2), (0, 0, 0, 0)); fd = ImageDraw.Draw(far)
    for _ in range(110):
        x = rnd.randint(0, W2); y = rnd.randint(0, H2); r = rnd.choice([1, 1, 2])
        fd.ellipse([x - r, y - r, x + r, y + r], fill=(130, 190, 245, rnd.randint(18, 48)))
    far = far.filter(ImageFilter.GaussianBlur(1.5))
    base = Image.alpha_composite(base.convert("RGBA"), far).convert("RGB")

    near = Image.new("RGBA", (W2, H2), (0, 0, 0, 0)); nd = ImageDraw.Draw(near)
    for _ in range(26):
        x = rnd.randint(0, W2); y = rnd.randint(0, H2); r = rnd.choice([2, 3, 3, 4])
        col = (0, 229, 255, rnd.randint(90, 160)) if rnd.random() < 0.7 else (255, 255, 255, rnd.randint(80, 140))
        nd.ellipse([x - r, y - r, x + r, y + r], fill=col)
    nb = near.resize((qw, qh), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)).resize((W2, H2), Image.BILINEAR)
    base = Image.alpha_composite(base.convert("RGBA"), near).convert("RGB")
    base = ImageChops.screen(base, nb.convert("RGB"))

    # 6) بلوم + حبيبات + فينييت قوي + انحراف لوني
    sm = base.resize((qw, qh), Image.BILINEAR)
    bright = sm.point(lambda v: 0 if v < 116 else min(255, int((v - 116) * 2.0)))
    bloom = bright.filter(ImageFilter.GaussianBlur(8)).resize((W2, H2), Image.BILINEAR)
    base = ImageChops.screen(base, bloom.point(lambda v: int(v * 0.50)))

    grain = Image.effect_noise((max(2, W2 // 2), max(2, H2 // 2)), 10).convert("RGB").resize((W2, H2), Image.BILINEAR)
    base = Image.blend(base, ImageChops.screen(base, grain), 0.032)

    vig = Image.radial_gradient("L").resize((W2, H2), Image.BILINEAR)
    r_, g_, b_ = base.split()
    fringe = Image.merge("RGB", (ImageChops.offset(r_, 2, 0), g_, ImageChops.offset(b_, -2, 0)))
    base = Image.composite(fringe, base, vig.point(lambda v: int(v * 0.5)))
    base = Image.composite(ImageEnhance.Color(base).enhance(0.62), base, vig.point(lambda v: int(v * 0.4)))
    base = Image.composite(Image.new("RGB", (W2, H2), (0, 0, 0)), base, vig.point(lambda v: int(v * 0.80)))

    p = BG / ("studio_bg_%02d_%dx%d.png" % (idx, W2, H2))
    base.save(str(p), "PNG", compress_level=3)
    return p


def glow_image(W):
    from PIL import Image, ImageOps, ImageFilter, ImageDraw, ImageChops
    size = max(64, C.scale(880, W))
    m = ImageOps.invert(Image.radial_gradient("L")).resize((size, size), Image.BILINEAR).point(lambda v: int(v * 0.26))
    im = Image.new("RGBA", (size, size), C.hex2rgb(C.cfg()["brand"]["blue"]) + (0,))
    im.putalpha(m)
    st = Image.new("L", (size, size), 0)
    ImageDraw.Draw(st).ellipse([size * 0.02, size * 0.47, size * 0.98, size * 0.53], fill=70)
    st = st.filter(ImageFilter.GaussianBlur(size // 90 + 2))
    streak = Image.new("RGBA", (size, size), C.hex2rgb(C.cfg()["brand"]["electric"]) + (0,))
    streak.putalpha(st)
    im = ImageChops.screen(im.convert("RGB"), streak.convert("RGB")).convert("RGBA")
    im.putalpha(ImageChops.lighter(m, st))
    p = IMG / ("studio_glow_%d.png" % W)
    im.save(str(p), "PNG", compress_level=3)
    return p


def particle_image(W, H):
    from PIL import Image, ImageDraw
    rnd = random.Random(4242)
    im = Image.new("RGBA", (W, H + 180), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _ in range(80):
        x = rnd.randint(0, W - 1)
        y = rnd.randint(0, H + 179)
        r = rnd.choice([2, 2, 3, 4])
        a = rnd.randint(35, 130)
        col = (0, 229, 255, a) if rnd.random() < 0.72 else (255, 255, 255, a)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    p = IMG / ("studio_particles_%dx%d.png" % (W, H))
    im.save(str(p), "PNG", compress_level=3)
    return p


def draw_icon(d, kind, box, color):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    if kind == "chat":
        d.rounded_rectangle([x0, y0, x1, y0 + h * 0.72], radius=int(h * 0.20), outline=color, width=4)
        d.polygon([(x0 + w * 0.24, y0 + h * 0.70), (x0 + w * 0.44, y0 + h * 0.70), (x0 + w * 0.26, y1)], fill=color)
    elif kind == "search":
        d.ellipse([x0, y0, x0 + w * 0.70, y0 + h * 0.70], outline=color, width=5)
        d.line([(x0 + w * 0.60, y0 + h * 0.60), (x1, y1)], fill=color, width=6)
    elif kind == "design":
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(h * 0.16), outline=color, width=4)
        d.polygon([(x0 + w * 0.18, y1 - h * 0.18), (x0 + w * 0.46, y0 + h * 0.30), (x0 + w * 0.76, y1 - h * 0.18)], fill=color)
    elif kind == "video":
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(h * 0.16), outline=color, width=4)
        d.polygon([(x0 + w * 0.38, y0 + h * 0.26), (x0 + w * 0.38, y0 + h * 0.74), (x0 + w * 0.76, y0 + h * 0.50)], fill=color)
    elif kind == "rocket":
        d.polygon([(x0 + w * 0.5, y0), (x1, y1), (x0 + w * 0.5, y0 + h * 0.76), (x0, y1)], outline=color, width=4)
    else:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        d.polygon([(cx, y0), (cx + w * 0.16, cy - h * 0.16), (x1, cy), (cx + w * 0.16, cy + h * 0.16),
                   (cx, y1), (cx - w * 0.16, cy + h * 0.16), (x0, cy), (cx - w * 0.16, cy - h * 0.16)], fill=color)


def _card_shadow(im):
    from PIL import Image, ImageFilter
    W, H = im.size
    a = im.getchannel("A")
    sh = Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 205)),
                         Image.new("RGBA", (W, H), (0, 0, 0, 0)), a)
    sh = sh.filter(ImageFilter.GaussianBlur(max(6, W // 80)))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.alpha_composite(sh, (0, max(6, H // 55)))
    out.alpha_composite(im)
    return out


def _studio_icon_v2(d, name, x, y, w, h, col):
    import math
    cx = x + w / 2.0
    cy = y + h / 2.0
    r = min(w, h) / 2.0
    white = (255, 255, 255, 235)
    dark = (5, 9, 16, 255)
    name = (name or "").lower()

    if name == "android":
        d.pieslice([cx - r * 0.72, cy - r * 0.86, cx + r * 0.72, cy + r * 0.18], 180, 360, fill=col)
        d.rectangle([cx - r * 0.72, cy - r * 0.08, cx + r * 0.72, cy + r * 0.62], fill=col)
        d.line([(cx - r * 0.45, cy - r * 0.72), (cx - r * 0.62, cy - r * 0.98)], fill=col, width=max(2, int(r * 0.08)))
        d.line([(cx + r * 0.45, cy - r * 0.72), (cx + r * 0.62, cy - r * 0.98)], fill=col, width=max(2, int(r * 0.08)))
        d.ellipse([cx - r * 0.42, cy - r * 0.52, cx - r * 0.22, cy - r * 0.32], fill=dark)
        d.ellipse([cx + r * 0.22, cy - r * 0.52, cx + r * 0.42, cy - r * 0.32], fill=dark)
    elif name in ("settings", "gear"):
        for i in range(8):
            a = math.radians(i * 45)
            tx = cx + math.cos(a) * r * 0.92
            ty = cy + math.sin(a) * r * 0.92
            d.ellipse([tx - r * 0.16, ty - r * 0.16, tx + r * 0.16, ty + r * 0.16], fill=col)
        d.ellipse([cx - r * 0.78, cy - r * 0.78, cx + r * 0.78, cy + r * 0.78], fill=col)
        d.ellipse([cx - r * 0.34, cy - r * 0.34, cx + r * 0.34, cy + r * 0.34], fill=dark)
    elif name == "battery":
        d.rounded_rectangle([x + r * 0.18, y + r * 0.42, x + w - r * 0.34, y + h - r * 0.42],
                            radius=int(r * 0.18), outline=col, width=max(3, int(r * 0.12)))
        d.rectangle([x + w - r * 0.28, cy - r * 0.22, x + w - r * 0.10, cy + r * 0.22], fill=col)
        d.rectangle([x + r * 0.34, cy - r * 0.34, x + w * 0.62, cy + r * 0.34], fill=col)
    elif name in ("storage", "database"):
        d.ellipse([cx - r * 0.72, cy - r * 0.82, cx + r * 0.72, cy - r * 0.42], fill=col)
        d.rectangle([cx - r * 0.72, cy - r * 0.62, cx + r * 0.72, cy + r * 0.58], fill=col)
        d.ellipse([cx - r * 0.72, cy + r * 0.38, cx + r * 0.72, cy + r * 0.78], fill=col)
        d.line([(cx - r * 0.72, cy - r * 0.12), (cx + r * 0.72, cy - r * 0.12)], fill=dark, width=max(2, int(r * 0.08)))
        d.line([(cx - r * 0.72, cy + r * 0.28), (cx + r * 0.72, cy + r * 0.28)], fill=dark, width=max(2, int(r * 0.08)))
    elif name == "terminal":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h - 4], radius=int(r * 0.22),
                            fill=(8, 14, 26, 255), outline=col, width=max(3, int(r * 0.1)))
        d.line([(cx - r * 0.45, cy - r * 0.28), (cx - r * 0.12, cy)], fill=white, width=max(3, int(r * 0.12)))
        d.line([(cx - r * 0.12, cy), (cx - r * 0.45, cy + r * 0.28)], fill=white, width=max(3, int(r * 0.12)))
        d.line([(cx + r * 0.05, cy + r * 0.28), (cx + r * 0.48, cy + r * 0.28)], fill=white, width=max(3, int(r * 0.12)))
    elif name == "python":
        d.rounded_rectangle([cx - r * 0.72, cy - r * 0.82, cx + r * 0.18, cy + r * 0.08], radius=int(r * 0.28), fill=col)
        d.rounded_rectangle([cx - r * 0.18, cy - r * 0.08, cx + r * 0.72, cy + r * 0.82], radius=int(r * 0.28), fill=col)
        d.ellipse([cx - r * 0.48, cy - r * 0.58, cx - r * 0.28, cy - r * 0.38], fill=dark)
        d.ellipse([cx + r * 0.28, cy + r * 0.38, cx + r * 0.48, cy + r * 0.58], fill=dark)
    elif name == "git":
        pts = [(cx + r * math.cos(math.radians(60 * i - 90)), cy + r * math.sin(math.radians(60 * i - 90))) for i in range(6)]
        d.polygon(pts, fill=col)
        d.line([(cx - r * 0.35, cy + r * 0.35), (cx + r * 0.35, cy - r * 0.35)], fill=dark, width=max(3, int(r * 0.12)))
        d.ellipse([cx - r * 0.5, cy + r * 0.2, cx - r * 0.2, cy + r * 0.5], fill=dark)
        d.ellipse([cx + r * 0.2, cy - r * 0.5, cx + r * 0.5, cy - r * 0.2], fill=dark)
    elif name == "github":
        d.ellipse([cx - r * 0.78, cy - r * 0.62, cx + r * 0.78, cy + r * 0.82], fill=col)
        d.polygon([(cx - r * 0.62, cy - r * 0.42), (cx - r * 0.38, cy - r * 0.86), (cx - r * 0.12, cy - r * 0.48)], fill=col)
        d.polygon([(cx + r * 0.62, cy - r * 0.42), (cx + r * 0.38, cy - r * 0.86), (cx + r * 0.12, cy - r * 0.48)], fill=col)
        d.ellipse([cx - r * 0.34, cy - r * 0.12, cx - r * 0.12, cy + r * 0.1], fill=dark)
        d.ellipse([cx + r * 0.12, cy - r * 0.12, cx + r * 0.34, cy + r * 0.1], fill=dark)
    elif name in ("chatgpt", "openai"):
        pts = []
        for i in range(12):
            a = math.radians(30 * i - 90)
            rr = r if i % 2 == 0 else r * 0.48
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=col)
        d.ellipse([cx - r * 0.2, cy - r * 0.2, cx + r * 0.2, cy + r * 0.2], fill=dark)
    elif name == "search":
        d.ellipse([x + r * 0.18, y + r * 0.18, x + w * 0.68, y + h * 0.68], outline=col, width=max(4, int(r * 0.16)))
        d.line([(x + w * 0.58, y + h * 0.58), (x + w - r * 0.18, y + h - r * 0.18)], fill=col, width=max(5, int(r * 0.2)))
    elif name == "design":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h - 4], radius=int(r * 0.22), outline=col, width=max(4, int(r * 0.14)))
        d.polygon([(x + w * 0.22, y + h * 0.78), (x + w * 0.5, y + h * 0.22), (x + w * 0.78, y + h * 0.78)], fill=col)
    elif name == "video":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h - 4], radius=int(r * 0.22), outline=col, width=max(4, int(r * 0.14)))
        d.polygon([(x + w * 0.4, y + h * 0.3), (x + w * 0.4, y + h * 0.7), (x + w * 0.74, y + h * 0.5)], fill=col)
    elif name == "rocket":
        d.polygon([(cx, y + 4), (x + w - r * 0.22, y + h * 0.68), (cx, y + h * 0.82), (x + r * 0.22, y + h * 0.68)], fill=col)
        d.ellipse([cx - r * 0.16, cy - r * 0.34, cx + r * 0.16, cy - r * 0.02], fill=dark)
    elif name == "chat":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h * 0.74], radius=int(r * 0.24), fill=col)
        d.polygon([(x + w * 0.24, y + h * 0.72), (x + w * 0.46, y + h * 0.72), (x + w * 0.24, y + h * 0.94)], fill=col)
    else:
        pts = []
        for i in range(8):
            a = math.radians(45 * i - 90)
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=col)


def _p0_icon(d, name, x, y, w, h, col):
    import math
    cx = x + w / 2.0
    cy = y + h / 2.0
    r = min(w, h) / 2.0
    dark = (5, 9, 16, 255)
    white = (255, 255, 255, 235)
    name = (name or "").lower()

    if name == "android":
        d.pieslice([cx - r * 0.72, cy - r * 0.86, cx + r * 0.72, cy + r * 0.18], 180, 360, fill=col)
        d.rectangle([cx - r * 0.72, cy - r * 0.08, cx + r * 0.72, cy + r * 0.62], fill=col)
        d.line([(cx - r * 0.45, cy - r * 0.72), (cx - r * 0.62, cy - r * 0.98)], fill=col, width=max(2, int(r * 0.08)))
        d.line([(cx + r * 0.45, cy - r * 0.72), (cx + r * 0.62, cy - r * 0.98)], fill=col, width=max(2, int(r * 0.08)))
        d.ellipse([cx - r * 0.42, cy - r * 0.52, cx - r * 0.22, cy - r * 0.32], fill=dark)
        d.ellipse([cx + r * 0.22, cy - r * 0.52, cx + r * 0.42, cy - r * 0.32], fill=dark)
    elif name in ("settings", "gear"):
        for i in range(8):
            a = math.radians(i * 45)
            tx = cx + math.cos(a) * r * 0.92
            ty = cy + math.sin(a) * r * 0.92
            d.ellipse([tx - r * 0.16, ty - r * 0.16, tx + r * 0.16, ty + r * 0.16], fill=col)
        d.ellipse([cx - r * 0.78, cy - r * 0.78, cx + r * 0.78, cy + r * 0.78], fill=col)
        d.ellipse([cx - r * 0.34, cy - r * 0.34, cx + r * 0.34, cy + r * 0.34], fill=dark)
    elif name == "battery":
        d.rounded_rectangle([x + r * 0.18, y + r * 0.42, x + w - r * 0.34, y + h - r * 0.42],
                            radius=int(r * 0.18), outline=col, width=max(3, int(r * 0.12)))
        d.rectangle([x + w - r * 0.28, cy - r * 0.22, x + w - r * 0.10, cy + r * 0.22], fill=col)
        d.rectangle([x + r * 0.34, cy - r * 0.34, x + w * 0.62, cy + r * 0.34], fill=col)
    elif name in ("storage", "database"):
        d.ellipse([cx - r * 0.72, cy - r * 0.82, cx + r * 0.72, cy - r * 0.42], fill=col)
        d.rectangle([cx - r * 0.72, cy - r * 0.62, cx + r * 0.72, cy + r * 0.58], fill=col)
        d.ellipse([cx - r * 0.72, cy + r * 0.38, cx + r * 0.72, cy + r * 0.78], fill=col)
        d.line([(cx - r * 0.72, cy - r * 0.12), (cx + r * 0.72, cy - r * 0.12)], fill=dark, width=max(2, int(r * 0.08)))
        d.line([(cx - r * 0.72, cy + r * 0.28), (cx + r * 0.72, cy + r * 0.28)], fill=dark, width=max(2, int(r * 0.08)))
    elif name == "terminal":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h - 4], radius=int(r * 0.22),
                            fill=(8, 14, 26, 255), outline=col, width=max(3, int(r * 0.1)))
        d.line([(cx - r * 0.45, cy - r * 0.28), (cx - r * 0.12, cy)], fill=white, width=max(3, int(r * 0.12)))
        d.line([(cx - r * 0.12, cy), (cx - r * 0.45, cy + r * 0.28)], fill=white, width=max(3, int(r * 0.12)))
        d.line([(cx + r * 0.05, cy + r * 0.28), (cx + r * 0.48, cy + r * 0.28)], fill=white, width=max(3, int(r * 0.12)))
    elif name == "python":
        d.rounded_rectangle([cx - r * 0.72, cy - r * 0.82, cx + r * 0.18, cy + r * 0.08], radius=int(r * 0.28), fill=col)
        d.rounded_rectangle([cx - r * 0.18, cy - r * 0.08, cx + r * 0.72, cy + r * 0.82], radius=int(r * 0.28), fill=col)
        d.ellipse([cx - r * 0.48, cy - r * 0.58, cx - r * 0.28, cy - r * 0.38], fill=dark)
        d.ellipse([cx + r * 0.28, cy + r * 0.38, cx + r * 0.48, cy + r * 0.58], fill=dark)
    elif name == "git":
        pts = [(cx + r * math.cos(math.radians(60 * i - 90)), cy + r * math.sin(math.radians(60 * i - 90))) for i in range(6)]
        d.polygon(pts, fill=col)
        d.line([(cx - r * 0.35, cy + r * 0.35), (cx + r * 0.35, cy - r * 0.35)], fill=dark, width=max(3, int(r * 0.12)))
        d.ellipse([cx - r * 0.5, cy + r * 0.2, cx - r * 0.2, cy + r * 0.5], fill=dark)
        d.ellipse([cx + r * 0.2, cy - r * 0.5, cx + r * 0.5, cy - r * 0.2], fill=dark)
    elif name == "github":
        d.ellipse([cx - r * 0.78, cy - r * 0.62, cx + r * 0.78, cy + r * 0.82], fill=col)
        d.polygon([(cx - r * 0.62, cy - r * 0.42), (cx - r * 0.38, cy - r * 0.86), (cx - r * 0.12, cy - r * 0.48)], fill=col)
        d.polygon([(cx + r * 0.62, cy - r * 0.42), (cx + r * 0.38, cy - r * 0.86), (cx + r * 0.12, cy - r * 0.48)], fill=col)
        d.ellipse([cx - r * 0.34, cy - r * 0.12, cx - r * 0.12, cy + r * 0.1], fill=dark)
        d.ellipse([cx + r * 0.12, cy - r * 0.12, cx + r * 0.34, cy + r * 0.1], fill=dark)
    elif name in ("chatgpt", "openai"):
        pts = []
        for i in range(12):
            a = math.radians(30 * i - 90)
            rr = r if i % 2 == 0 else r * 0.48
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=col)
        d.ellipse([cx - r * 0.2, cy - r * 0.2, cx + r * 0.2, cy + r * 0.2], fill=dark)
    elif name == "search":
        d.ellipse([x + r * 0.18, y + r * 0.18, x + w * 0.68, y + h * 0.68], outline=col, width=max(4, int(r * 0.16)))
        d.line([(x + w * 0.58, y + h * 0.58), (x + w - r * 0.18, y + h - r * 0.18)], fill=col, width=max(5, int(r * 0.2)))
    elif name == "design":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h - 4], radius=int(r * 0.22), outline=col, width=max(4, int(r * 0.14)))
        d.polygon([(x + w * 0.22, y + h * 0.78), (x + w * 0.5, y + h * 0.22), (x + w * 0.78, y + h * 0.78)], fill=col)
    elif name == "video":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h - 4], radius=int(r * 0.22), outline=col, width=max(4, int(r * 0.14)))
        d.polygon([(x + w * 0.4, y + h * 0.3), (x + w * 0.4, y + h * 0.7), (x + w * 0.74, y + h * 0.5)], fill=col)
    elif name == "rocket":
        d.polygon([(cx, y + 4), (x + w - r * 0.22, y + h * 0.68), (cx, y + h * 0.82), (x + r * 0.22, y + h * 0.68)], fill=col)
        d.ellipse([cx - r * 0.16, cy - r * 0.34, cx + r * 0.16, cy - r * 0.02], fill=dark)
    elif name == "chat":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h * 0.74], radius=int(r * 0.24), fill=col)
        d.polygon([(x + w * 0.24, y + h * 0.72), (x + w * 0.46, y + h * 0.72), (x + w * 0.24, y + h * 0.94)], fill=col)
    else:
        pts = []
        for i in range(8):
            a = math.radians(45 * i - 90)
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=col)


def card_image(sc, idx, total, W, H):
    from PIL import Image, ImageDraw
    b = C.cfg()["brand"]
    kind = sc.get("kind", "tool")
    f = C.resolve_font(bold=True, verbose=False)
    fr = C.resolve_font(verbose=False)
    electric = C.hex2rgb(b["electric"]) + (255,)
    white = C.hex2rgb(b["white"]) + (255,)
    muted = C.hex2rgb(b.get("muted", "#9FB6D4")) + (255,)
    blue = C.hex2rgb(b["blue"]) + (155,)

    def add_icon_layer(im, size):
        layer_h = size + C.scale(36, W)
        icon_layer = Image.new("RGBA", (W, layer_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(icon_layer)
        name = (sc.get("icon") or "spark").lower()
        x = (W - size) // 2
        y = C.scale(18, W)
        _p0_icon(d, name, x, y, size, size, electric)
        im.alpha_composite(icon_layer, (0, 0))
        return layer_h

    if kind == "intro":
        h = C.scale(820, W)
        im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        m = C.scale(64, W)
        d.rounded_rectangle([m, 0, W - m, h - 1], radius=C.scale(40, W),
                            fill=(6, 11, 20, 210), outline=C.hex2rgb(b["electric"]) + (170,), width=3)
        ih = add_icon_layer(im, C.scale(112, W))
        pen = C.ArabicPen(f, C.scale(88, W), bold=True, stroke=2)
        lines = pen.wrap(sc.get("title_ar", ""), W - 2 * m - C.scale(80, W), max_lines=2)
        y = ih + C.scale(16, W)
        for ln in lines:
            li = pen.line_img(ln, white)
            im.alpha_composite(li, ((W - li.width) // 2, y))
            y += li.height + C.scale(6, W)
        d.rectangle([(W - C.scale(240, W)) // 2, y + C.scale(22, W),
                     (W + C.scale(240, W)) // 2, y + C.scale(28, W)], fill=electric)
        if sc.get("subtitle"):
            ps = C.ArabicPen(fr, C.scale(48, W))
            si = ps.line_img(sc["subtitle"], electric)
            im.alpha_composite(si, ((W - si.width) // 2, y + C.scale(64, W)))
        try:
            im = _card_shadow(im)
        except NameError:
            pass
        p = IMG / ("studio_card_%02d_%d.png" % (idx, W))
        im.save(str(p), "PNG", compress_level=3)
        return p

    if kind == "outro":
        h = C.scale(620, W)
        im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        m = C.scale(64, W)
        d.rounded_rectangle([m, 0, W - m, h - 1], radius=C.scale(38, W),
                            fill=(6, 11, 20, 215), outline=C.hex2rgb(b["electric"]) + (180,), width=3)
        ih = add_icon_layer(im, C.scale(96, W))
        pt = C.ArabicPen(f, C.scale(70, W), bold=True, stroke=1)
        ti = pt.line_img(sc.get("title_ar", ""), white)
        y = ih + C.scale(12, W)
        im.alpha_composite(ti, ((W - ti.width) // 2, y))
        y += ti.height + C.scale(26, W)
        pn = C.ArabicPen(f, C.scale(56, W), bold=True)
        ni = pn.line_img(C.cfg().get("project", "أبو محمد المساوى"), electric)
        im.alpha_composite(ni, ((W - ni.width) // 2, y))
        y += ni.height + C.scale(22, W)
        if sc.get("subtitle"):
            ps = C.ArabicPen(fr, C.scale(44, W))
            si = ps.line_img(sc["subtitle"], muted)
            im.alpha_composite(si, ((W - si.width) // 2, y))
        d.rectangle([m + C.scale(40, W), h - C.scale(54, W), W - m - C.scale(40, W), h - C.scale(48, W)], fill=electric)
        try:
            im = _card_shadow(im)
        except NameError:
            pass
        p = IMG / ("studio_card_%02d_%d.png" % (idx, W))
        im.save(str(p), "PNG", compress_level=3)
        return p

    h = C.scale(700, W)
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    m = C.scale(64, W)
    d.rounded_rectangle([m, 0, W - m, h - 1], radius=C.scale(36, W),
                        fill=(6, 11, 20, 205), outline=blue, width=3)
    ih = add_icon_layer(im, C.scale(104, W))
    pt = C.ArabicPen(f, C.scale(76, W), bold=True, stroke=1)
    lines = pt.wrap(sc.get("title_ar", ""), W - 2 * m - C.scale(70, W), max_lines=2)
    y = ih + C.scale(12, W)
    for ln in lines:
        li = pt.line_img(ln, white)
        im.alpha_composite(li, ((W - li.width) // 2, y))
        y += li.height + C.scale(4, W)
    if sc.get("subtitle"):
        ps = C.ArabicPen(fr, C.scale(44, W))
        si = ps.line_img(sc["subtitle"], electric)
        im.alpha_composite(si, ((W - si.width) // 2, y + C.scale(14, W)))
        y += si.height + C.scale(14, W)
    if sc.get("chips"):
        pc = C.ArabicPen(fr, C.scale(38, W))
        boxes = []
        for ch in sc["chips"][:3]:
            li = pc.line_img(ch, white)
            pad = C.scale(24, W)
            bx = Image.new("RGBA", (li.width + 2 * pad, li.height + C.scale(12, W)), (0, 0, 0, 0))
            bd = ImageDraw.Draw(bx)
            bd.rounded_rectangle([0, 0, bx.width - 1, bx.height - 1], radius=bx.height // 2,
                                 fill=(13, 32, 60, 215), outline=blue, width=2)
            bx.alpha_composite(li, (pad, C.scale(6, W)))
            boxes.append(bx)
        gap = C.scale(16, W)
        tw = sum(x.width for x in boxes) + gap * (len(boxes) - 1)
        row = Image.new("RGBA", (tw, max(x.height for x in boxes)), (0, 0, 0, 0))
        x = tw
        for bx in boxes:
            x -= bx.width
            row.alpha_composite(bx, (x, 0))
            x -= gap
        im.alpha_composite(row, ((W - row.width) // 2, h - C.scale(120, W)))
    d.rectangle([W - m - C.scale(9, W), C.scale(40, W), W - m - C.scale(3, W), h - C.scale(40, W)], fill=electric)
    try:
        im = _card_shadow(im)
    except NameError:
        pass
    p = IMG / ("studio_card_%02d_%d.png" % (idx, W))
    im.save(str(p), "PNG", compress_level=3)
    return p


def badge_image(W):
    from PIL import Image, ImageDraw
    b = C.cfg()["brand"]
    name = C.cfg().get("project", "أبو محمد المساوى")
    pen = C.ArabicPen(C.resolve_font(bold=True, verbose=False), C.scale(40, W), bold=True, stroke=1)
    ni = pen.line_img(name, C.hex2rgb(b["white"]) + (255,))
    pad = C.scale(24, W)
    w = ni.width + 2 * pad
    h = ni.height + C.scale(20, W)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(5, 9, 16, 165),
                        outline=C.hex2rgb(b["blue"]) + (120,), width=2)
    im.alpha_composite(ni, (pad, C.scale(6, W)))
    d.line([(pad, h - C.scale(8, W)), (w - pad, h - C.scale(8, W))],
           fill=C.hex2rgb(b["electric"]) + (215,), width=max(2, C.scale(3, W)))
    p = IMG / ("studio_badge_%d.png" % W)
    im.save(str(p), "PNG", compress_level=3)
    return p


def bar_image(W):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (W, 10), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle([0, 0, W, 9], fill=C.hex2rgb(C.cfg()["brand"]["electric"]) + (210,))
    p = IMG / ("studio_bar_%d.png" % W)
    im.save(str(p), "PNG", compress_level=3)
    return p


def render_clip(sc, idx, total, W, H, fps, xfade, fast):
    last = idx == total - 1
    span = float(sc["span"])
    L = span + (0.0 if last else xfade)
    nf = max(2, int(round(L * fps)))
    nfm1 = max(1, nf - 1)
    bg = bg_image(idx, W, H, sc["kind"])
    card = card_image(sc, idx, total, W, H)
    glow = glow_image(W)
    part = particle_image(W, H)

    if sc["kind"] == "intro":
        card_y = C.scale(430, W)
    elif sc["kind"] == "outro":
        card_y = C.scale(640, W)
    else:
        card_y = C.scale(560, W)

    cin = 0.18 if idx == 0 else xfade + 0.04
    cout = max(cin + 0.35, span - 0.12)
    z = 0.085
    panx = 0.24 if idx % 2 == 0 else -0.24
    pany = -0.12 if idx % 3 == 0 else 0.10

    fc = []
    fc.append("[0:v]zoompan=z='1+%.4f*on/%d':x='(iw-iw/zoom)*(0.5%+.2f*on/%d)'"
              ":y='(ih-ih/zoom)*(0.5%+.2f*on/%d)':d=%d:s=%dx%d:fps=%d,setsar=1,"
              "eq=saturation=1.07:contrast=1.04[bgv]"
              % (z, nfm1, panx, nfm1, pany, nfm1, nf, W, H, fps))
    fc.append("[bgv][1:v]overlay=x='(W-w)/2+%.1f*sin(t/3.0)':y='H*0.18+%.1f*cos(t/4.1)'[l1]"
              % (W * 0.10, H * 0.045))
    fc.append("[l1][2:v]overlay=x='%.1f*sin(t/6.2)':y='-%d+%d*sin(t/7.4)'[l2]"
              % (W * 0.016, int(H * 0.06), int(H * 0.02)))
    fc.append("[3:v]loop=loop=%d:size=1:start=0,setpts=N/(%d*TB),format=rgba,"
              "fade=t=in:st=%.3f:d=0.34:alpha=1,fade=t=out:st=%.3f:d=0.34:alpha=1[card]"
              % (nf - 1, fps, cin, cout))
    fc.append("[l2][card]overlay=x=0:y='%d+%.1f*(1-min(1,max(0,(t-%.3f)/0.42)))'[vout]"
              % (card_y, H * 0.018, cin))

    out = OUT / "scenes" / ("studio_%02d_%d.mp4" % (idx, W))
    preset = "ultrafast" if fast else "medium"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
           "-i", bg, "-i", glow, "-i", part, "-i", card,
           "-filter_complex", ";".join(fc), "-map", "[vout]",
           "-frames:v", nf, "-r", fps, "-c:v", "libx264", "-preset", preset,
           "-crf", "17", "-pix_fmt", "yuv420p", "-an", str(out)]
    C.run(cmd)
    got = C.duration(out)
    if abs(got - L) > 0.15:
        C.die("مشهد %02d: المدة %.3f بدل %.3f" % (idx, got, L))
    C.log("STUDIO scene %02d ok: %d frames / %.2fs" % (idx, nf, got))
    return out


def merge_clips(clips, timeline, W, H, fps, xfade, fast):
    kinds = ["fade", "slideleft", "circleopen", "smoothright", "wipeleft", "slideright", "fade", "smoothleft", "fade"]
    fc = ["[%d:v]settb=AVTB,fps=%d[v%d]" % (i, fps, i) for i in range(len(clips))]
    prev = "v0"
    off = 0.0
    for i in range(1, len(clips)):
        off += float(timeline["scenes"][i - 1]["span"])
        lab = "x%d" % i
        fc.append("[%s][v%d]xfade=transition=%s:duration=%.3f:offset=%.3f[%s]"
                  % (prev, i, kinds[(i - 1) % len(kinds)], xfade, off, lab))
        prev = lab
    fc.append("[%s]format=yuv420p[vout]" % prev)
    out = OUT / ("studio_master_%d.mp4" % W)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin"]
    for c in clips:
        cmd += ["-i", str(c)]
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-r", fps,
            "-c:v", "libx264", "-preset", "ultrafast" if fast else "medium",
            "-crf", "17", "-pix_fmt", "yuv420p", "-an", str(out)]
    p = C.run(cmd, check=False)
    if p.returncode != 0 or not out.exists():
        lst = TMP / "studio_concat.txt"
        lst.write_text("".join("file '%s'\n" % Path(c).resolve() for c in clips), encoding="utf-8")
        C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
               "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])
    got = C.duration(out)
    if abs(got - timeline["total"]) > 0.25:
        C.die("الماستر %.3fs لا يطابق الصوت %.3fs" % (got, timeline["total"]))
    C.log("STUDIO master ok: %.3fs" % got)
    return out


def split_segments(text, max_words=5):
    words = text.split()
    segs = []
    i = 0
    while i < len(words):
        rem = len(words) - i
        if rem <= max_words:
            segs.append(words[i:])
            break
        take = max_words if rem - max_words >= 3 else max(3, rem // 2)
        segs.append(words[i:i + take])
        i += take
    return segs


def karaoke_frames(timeline, W, H, preview=False):
    from PIL import Image, ImageDraw
    b = C.cfg()["brand"]
    font_path = C.resolve_font(verbose=False)
    pen = C.ArabicPen(font_path, C.scale(74, W), stroke=2)
    col_done = C.hex2rgb(b["muted"]) + (205,)
    col_now = C.hex2rgb(b["electric"]) + (255,)
    col_next = C.hex2rgb(b["white"]) + (105,)
    bottom = int(H * 0.795)
    max_line = W - 2 * C.scale(110, W)
    sp = int(pen.space_w * 1.15)

    cues = []
    for sc in timeline["scenes"]:
        for ln in sc["lines"]:
            cues.append({"start": ln["start"], "end": ln["end"],
                         "text": ln["screen"], "hl": ln.get("hl", [])})

    meta = []
    counter = 0
    for ci, cue in enumerate(cues):
        hlset = {C.norm_word(x) for x in cue["hl"]}
        segs = split_segments(cue["text"], 5)
        if not segs:
            continue
        total_words = sum(len(s) for s in segs)
        dur = cue["end"] - cue["start"]
        per_word = dur / max(1, total_words)
        widx = 0
        frames = []
        for seg in segs:
            for active in range(len(seg)):
                def color_for(global_i, word):
                    if global_i < widx + active:
                        return col_now if C.norm_word(word) in hlset else col_done
                    if global_i == widx + active:
                        return col_now
                    return col_next

                toks = []
                for k, w in enumerate(seg):
                    toks.append(pen.token_img(w, color_for(widx + k, w)))
                line_w = sum(t.width for t in toks) + sp * max(0, len(toks) - 1)

                if line_w > max_line and len(seg) > 3:
                    mid = len(seg) // 2
                    groups = [toks[:mid], toks[mid:]]
                    offsets = [widx, widx + mid]
                    words_g = [seg[:mid], seg[mid:]]
                else:
                    groups = [toks]
                    offsets = [widx]
                    words_g = [seg]

                line_imgs = []
                for gi, gt in enumerate(groups):
                    lw = sum(t.width for t in gt) + sp * max(0, len(gt) - 1)
                    lh = max(t.height for t in gt)
                    li = Image.new("RGBA", (max(2, lw), lh), (0, 0, 0, 0))
                    x = lw
                    for t in gt:
                        x -= t.width
                        li.alpha_composite(t, (max(0, x), 0))
                        x -= sp
                    line_imgs.append(li)

                gap = C.scale(8, W)
                content_w = max(i.width for i in line_imgs)
                content_h = sum(i.height for i in line_imgs) + gap * (len(line_imgs) - 1)
                padx, pady = C.scale(38, W), C.scale(26, W)
                bw = min(W - 2 * C.scale(56, W), content_w + 2 * padx)
                bh = content_h + 2 * pady + C.scale(12, W)
                box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
                d = ImageDraw.Draw(box)
                d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=C.scale(28, W),
                                    fill=(4, 8, 15, 232), outline=C.hex2rgb(b["blue"]) + (145,), width=3)
                d.rectangle([bw - C.scale(10, W), C.scale(18, W), bw - C.scale(4, W), bh - C.scale(18, W)],
                            fill=C.hex2rgb(b["electric"]) + (240,))
                y = pady
                for li in line_imgs:
                    box.alpha_composite(li, ((bw - li.width) // 2, y))
                    y += li.height + gap
                prog = (widx + active + 1) / max(1, total_words)
                by = bh - C.scale(9, W)
                d.rectangle([C.scale(22, W), by, bw - C.scale(22, W), by + C.scale(4, W)], fill=(38, 58, 88, 190))
                pw = int((bw - 2 * C.scale(22, W)) * prog)
                if pw > 0:
                    d.rectangle([C.scale(22, W), by, C.scale(22, W) + pw, by + C.scale(4, W)],
                                fill=C.hex2rgb(b["electric"]) + (255,))

                p = IMG / ("studio_k_%03d_%d.png" % (counter, W))
                box.save(str(p), "PNG", compress_level=3)
                st = cue["start"] + (widx + active) * per_word
                en = st + per_word
                frames.append({"file": str(p), "y": max(0, bottom - bh), "start": st, "end": en,
                               "w": bw, "h": bh})
                counter += 1
            widx += len(seg)
        meta.append({"cue": ci, "frames": frames})

    (OUT / "studio_karaoke.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    C.log("STUDIO karaoke: %d cues -> %d frames" % (len(meta), counter))
    return meta


def music_bed(duration, sr=48000):
    import array
    n = int(duration * sr) + 1
    buf = array.array("d", bytes(8 * n))
    rnd = random.Random(17)
    sin, exp, pi = math.sin, math.exp, math.pi

    def add(start, samples, gain=1.0):
        i0 = int(start * sr)
        for k, v in enumerate(samples):
            j = i0 + k
            if 0 <= j < n:
                buf[j] += v * gain

    def pad(freqs, dur, amp=0.16):
        m = int(dur * sr)
        o = [0.0] * m
        for fq in freqs:
            for det in (0.9976, 1.0032):
                w = 2 * pi * fq * det / sr
                for i in range(m):
                    o[i] += sin(w * i)
        a, r = int(0.9 * sr), int(1.4 * sr)
        k = amp / (len(freqs) * 2)
        for i in range(m):
            e = 1.0
            if i < a:
                e = i / a
            if i > m - r:
                e = min(e, max(0.0, (m - i) / r))
            e *= 0.87 + 0.13 * sin(2 * pi * 0.16 * i / sr)
            o[i] *= e * k
        return o

    def pulse(dur=0.5, f0=94, f1=45, amp=0.20):
        m = int(dur * sr)
        o = [0.0] * m
        ph = 0.0
        for i in range(m):
            t = i / m
            ph += 2 * pi * (f0 + (f1 - f0) * min(1.0, t * 3)) / sr
            o[i] = sin(ph) * exp(-6.2 * t) * amp
        return o

    def pluck(fq, dur=0.28, amp=0.05):
        m = int(dur * sr)
        o = [0.0] * m
        w = 2 * pi * fq / sr
        for i in range(m):
            t = i / sr
            o[i] = (sin(w * i) + 0.32 * sin(2 * w * i)) * exp(-9.5 * t) * amp
        return o

    def whoosh(dur=0.6, amp=0.16, up=False):
        m = int(dur * sr)
        o = [0.0] * m
        lp = 0.0
        for i in range(m):
            t = i / m
            cut = 0.02 + 0.32 * (t if up else (1.0 - t))
            lp += cut * (rnd.uniform(-1, 1) - lp)
            o[i] = lp * (sin(pi * t) ** 2) * amp * 3.0
        return o

    prog = [[110.0, 164.81, 220.0], [87.31, 130.81, 174.61],
            [130.81, 196.0, 261.63], [98.0, 146.83, 196.0]]
    part = duration / 4.0
    for k, ch in enumerate(prog):
        add(k * part, pad(ch, part + 0.7))
    t = 0.6
    while t < duration - 1.2:
        add(t, pulse())
        t += 0.6667
    notes = [440.0, 523.25, 587.33, 659.25, 783.99, 659.25, 587.33, 523.25]
    t, k = 1.8, 0
    while t < duration - 1.6:
        if k % 8 not in (3, 7):
            add(t, pluck(notes[k % len(notes)]))
        t += 0.3333
        k += 1
    return buf, sr, add, whoosh, pulse


def build_music(timeline):
    total = float(timeline["total"])
    buf, sr, add, whoosh, pulse = music_bed(total)
    starts = [float(s["visual_start"]) for s in timeline["scenes"]]
    add(0.02, pulse(0.7, 112, 40, 0.42))
    for i, st in enumerate(starts):
        if i > 0:
            add(max(0.0, st - 0.30), whoosh(0.60, 0.17))
    if starts:
        add(max(0.0, starts[-1] - 0.9), whoosh(0.9, 0.14, up=True))
        add(starts[-1], pulse(0.8, 120, 38, 0.38))
    n = len(buf)
    fi, fo = int(0.3 * sr), int(1.1 * sr)
    for i in range(n):
        if i < fi:
            buf[i] *= i / fi
        if i > n - fo:
            buf[i] *= max(0.0, (n - i) / fo)
    pk = max(1e-9, max(abs(min(buf)), abs(max(buf))))
    g = 0.70 / pk
    left = [v * g * 32767 for v in buf]
    d = int(0.006 * sr)
    right = [(left[i - d] if i >= d else 0.0) * 0.92 for i in range(n)]
    p = C.MUSIC / "studio_bed.wav"
    C.wav_write_stereo(p, sr, left, right)
    C.log("STUDIO music: %.2fs" % total)
    return p


def mix_audio(timeline, bed):
    A = C.cfg()["audio"]
    total = float(timeline["total"])
    voice = C.VOICE / "voice.wav"
    if not voice.exists():
        C.die("voice.wav مفقود")
    mix = OUT / "studio_mix.wav"
    fc = ("[1:a]aresample=%d,volume=%.3f[bed];"
          "[0:a]aresample=%d,highpass=f=80,equalizer=f=140:t=q:w=1:g=1.6,equalizer=f=3200:t=q:w=1.4:g=-2.0,acompressor=threshold=-18dB:ratio=2.5:attack=12:release=220,"
          "volume=%.3f[v];[v]asplit=2[v1][vsc];"
          "[bed][vsc]sidechaincompress=threshold=0.035:ratio=9:attack=18:release=340:makeup=1:knee=6:detection=rms[duck];"
          "[duck][v1]amix=inputs=2:duration=first:dropout_transition=0,volume=2.0,apad[mix]"
          % (int(A["voice_sr"]), 0.26, int(A["voice_sr"]), float(A["voice_gain"])))
    C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
           "-i", str(voice), "-i", str(bed), "-filter_complex", fc, "-map", "[mix]",
           "-ar", str(A["voice_sr"]), "-ac", "2", "-c:a", "pcm_s16le",
           "-t", "%.6f" % total, str(mix)])
    import re
    target = "loudnorm=I=-14.0:TP=-1.5:LRA=11.0"
    p = C.run(["ffmpeg", "-hide_banner", "-nostats", "-nostdin", "-i", str(mix),
               "-af", target + ":print_format=json", "-f", "null", "-"], check=False)
    gain = 6.0
    if p.stderr:
        blocks = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
        if blocks:
            try:
                m = json.loads(blocks[-1])
                gain = max(-12.0, min(18.0, -14.0 - float(m["input_i"])))
            except Exception:
                pass
    norm = OUT / "studio_mix_norm.wav"
    af = "volume=%.3fdB,alimiter=limit=0.8414:attack=5:release=60:level=false,apad" % gain
    C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
           "-i", str(mix), "-af", af, "-ar", str(A["voice_sr"]), "-ac", "2",
           "-c:a", "pcm_s16le", "-t", "%.6f" % total, str(norm)])
    d = C.duration(norm)
    if abs(d - total) > 0.12:
        C.die("المزيج %.3fs لا يطابق %.3fs" % (d, total))
    C.log("STUDIO mix ok: %.3fs (gain %+.2f dB)" % (d, gain))
    return norm


def final_compose(master, audio, kar, timeline, W, H, fps, fast):
    badge = badge_image(W)
    bar = bar_image(W)
    inputs = ["-i", str(master), "-i", str(audio), "-i", str(badge), "-i", str(bar)]
    flat = [fr for cm in kar for fr in cm["frames"]]
    for fr in flat:
        inputs += ["-i", fr["file"]]
    total = float(timeline["total"])
    fc = ["[0:v][2:v]overlay=x=W-w-%d:y=%d:enable='gte(t,0.15)'[b1]"
          % (C.scale(56, W), C.scale(250, W)),
          "[b1][3:v]overlay=x='-w+w*t/%.6f':y=H-%d[b2]" % (total, max(6, C.scale(10, W)))]
    prev = "b2"
    for k, fr in enumerate(flat):
        lab = "k%d" % k
        fc.append("[%s][%d:v]overlay=x='(W-w)/2':y=%d:enable='between(t,%.4f,%.4f)'[%s]"
                  % (prev, 4 + k, fr["y"], fr["start"], fr["end"], lab))
        prev = lab
    fc.append("[%s]format=yuv420p[vout]" % prev)
    out = OUT / "studio_final.mp4"
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin", "-stats"] + inputs
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "ultrafast" if fast else "medium",
            "-b:v", "6M", "-minrate", "6M", "-maxrate", "6M", "-bufsize", "12M", "-x264-params", "nal-hrd=cbr:force-cfr=1",
            "-profile:v", "high", "-level", "4.2", "-pix_fmt", "yuv420p",
            "-r", str(fps), "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-t", "%.6f" % total, "-movflags", "+faststart", str(out)]
    C.run(cmd)
    C.log("STUDIO final: %s" % out)
    return out


def verify(path, timeline, W, H, fps):
    j = C.ffprobe_json(path)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    d = float(j["format"]["duration"])
    br = int(j["format"].get("bit_rate", 0)) / 1e6
    ok = True

    def chk(name, cond, got):
        nonlocal ok
        C.log("  [%s] %s = %s" % ("PASS" if cond else "FAIL", name, got))
        ok = ok and bool(cond)

    chk("h264", v and v["codec_name"] == "h264", v and v["codec_name"])
    chk("size", v and v["width"] == W and v["height"] == H, v and "%sx%s" % (v["width"], v["height"]))
    chk("yuv420p", v and v["pix_fmt"] == "yuv420p", v and v["pix_fmt"])
    chk("duration", abs(d - timeline["total"]) < 0.3, "%.3f" % d)
    chk("45-60s", 45.0 <= d <= 60.5, "%.3f" % d)
    chk("bitrate>=3Mbps", br >= 3.0, "%.2f Mbps" % br)
    chk("aac", a and a["codec_name"] == "aac", a and a["codec_name"])
    chk("48k stereo", a and int(a["sample_rate"]) == 48000 and a["channels"] == 2,
        a and "%s/%sch" % (a["sample_rate"], a["channels"]))
    if not ok:
        C.die("فشل التحقق النهائي")
    return {"duration": d, "bitrate_mbps": br, "size": "%dx%d" % (W, H), "fps": fps}


def make_thumbnail(timeline, W, H):
    from PIL import Image, ImageDraw
    b = C.cfg()["brand"]
    bgp = bg_image(99, W, H, "outro")
    resample = getattr(Image, "Resampling", Image).LANCZOS
    base = Image.open(str(bgp)).convert("RGBA").resize((W, H), resample)
    f = C.resolve_font(bold=True, verbose=False)
    title = timeline["scenes"][0].get("title_ar", C.cfg().get("title", "أبو محمد المساوى"))
    pen = C.ArabicPen(f, C.scale(112, W), bold=True, stroke=3)
    lines = pen.wrap(title, W - 2 * C.scale(90, W), max_lines=3)
    y = C.scale(520, W)
    for ln in lines:
        li = pen.line_img(ln, C.hex2rgb(b["white"]) + (255,))
        base.alpha_composite(li, ((W - li.width) // 2, y))
        y += li.height + C.scale(10, W)
    pn = C.ArabicPen(f, C.scale(54, W), bold=True)
    ni = pn.line_img(C.cfg().get("project", "أبو محمد المساوى"), C.hex2rgb(b["electric"]) + (255,))
    base.alpha_composite(ni, ((W - ni.width) // 2, H - C.scale(230, W)))
    ImageDraw.Draw(base).rectangle([0, H - C.scale(16, W), W, H - 1], fill=C.hex2rgb(b["electric"]) + (255,))
    p = OUT / "studio_thumbnail.jpg"
    base.convert("RGB").save(str(p), "JPEG", quality=94, optimize=True)
    return p


def build(script_path, preview=False, fast=False):
    ensure_dirs()
    W, H, fps = C.dims(preview)
    scenes = parse_script(script_path)
    tl_path = C.VOICE / "timeline.json"
    if not tl_path.exists():
        C.die("شغّل توليد الصوت أولاً: python voice/generate_voice.py --force")
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    if len(tl["scenes"]) != len(scenes):
        C.die("عدد المشاهد في timeline لا يطابق السيناريو — أعد توليد الصوت")
    for i, sc in enumerate(scenes):
        for k in ("span", "visual_start", "lines", "frames"):
            sc[k] = tl["scenes"][i][k]
    tl["scenes"] = scenes
    xfade = C.snap(0.36, fps)
    C.log("STUDIO %dx%d@%d | %.2fs | %d scenes" % (W, H, fps, tl["total"], len(scenes)))

    clips = [render_clip(sc, i, len(scenes), W, H, fps, xfade, fast) for i, sc in enumerate(scenes)]
    master = merge_clips(clips, tl, W, H, fps, xfade, fast)
    kar = karaoke_frames(tl, W, H, preview)
    bed = build_music(tl)
    audio = mix_audio(tl, bed)
    final = final_compose(master, audio, kar, tl, W, H, fps, fast)
    thumb = make_thumbnail(tl, W, H)
    report = verify(final, tl, W, H, fps)

    from engine import publish
    publish.build()
    (OUT / "studio_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    C.log("✅ STUDIO READY: %s | %.2f Mbps" % (final.name, report["bitrate_mbps"]))
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default=str(ROOT / "scripts" / "video_011.txt"))
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--fast", action="store_true")
    a = ap.parse_args()
    build(a.script, a.preview, a.fast)
