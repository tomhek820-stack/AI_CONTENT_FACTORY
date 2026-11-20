"""أصول بصرية أصلية 100%: خلفيات تقنية، بطاقات، طبقات حركة، غلاف."""
from __future__ import annotations
import argparse, math, os, random
from pathlib import Path
from engine import common as C


def bg_file(i, W, H):
    s = C.cfg()["video"]["bg_scale"]
    return C.BG / ("bg_%02d_%dx%d.png" % (i, int(W * s), int(H * s)))


def card_file(i, W):
    return C.IMG / ("card_%02d_%d.png" % (i, W))


def glow_file(W):
    return C.IMG / ("glow_%d.png" % W)


def part_file(W, H):
    return C.IMG / ("particles_%dx%d.png" % (W, H))


def scan_file(W):
    return C.IMG / ("scan_%d.png" % W)


def bug_file(W):
    return C.IMG / ("bug_%d.png" % W)


def bar_file(W):
    return C.IMG / ("bar_%d.png" % W)


def label_file(W):
    return C.IMG / ("preview_label_%d.png" % W)


def parse_script(path=None):
    path = Path(path) if path else Path(os.environ.get("AILAB_SCRIPT") or (C.ROOT / "scripts" / "video_001.txt"))
    scenes = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        f = [x.strip() for x in line.split("|")]
        if f[0] == "SCENE":
            scenes.append({"id": f[1], "kind": f[2], "title_ar": f[3], "latin": f[4],
                           "icon": f[5] if len(f) > 5 else "spark",
                           "chips": [c.strip() for c in f[6].split(",") if c.strip()] if len(f) > 6 else [],
                           "lines": []})
        elif f[0] == "LINE":
            if not scenes:
                C.die("سطر LINE قبل أي SCENE")
            scenes[-1]["lines"].append({"tts": f[1], "screen": f[2],
                                        "hl": [x.strip() for x in f[3].split(",") if x.strip()] if len(f) > 3 else []})
    if not scenes:
        C.die("السيناريو فارغ")
    return scenes


def make_background(path, W, H, seed, variant):
    from PIL import Image, ImageDraw, ImageChops, ImageOps
    b = C.cfg()["brand"]; rnd = random.Random(seed)
    s = C.cfg()["video"]["bg_scale"]
    W2, H2 = int(W * s), int(H * s)
    top = C.hex2rgb(b["black"])
    bot = C.hex2rgb(b["navy"] if variant != "outro" else "#081226")
    g = Image.new("RGB", (1, 512)); px = g.load()
    for y in range(512):
        t = y / 511.0
        px[0, y] = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
    base = g.resize((W2, H2), Image.BILINEAR)
    qw, qh = max(2, W2 // 4), max(2, H2 // 4)
    gl = Image.new("RGB", (qw, qh), (0, 0, 0))
    rad = ImageOps.invert(Image.radial_gradient("L"))
    spots = [(0.50, 0.20, 0.60, b["blue"], 0.60),
             (0.16, 0.60, 0.42, b["electric"], 0.26),
             (0.86, 0.82, 0.48, "#0B4FA8", 0.45)]
    if variant == "outro":
        spots[0] = (0.50, 0.30, 0.70, b["electric"], 0.42)
    for cx, cy, rr, col, inten in spots:
        r = max(4, int(qw * rr))
        m = rad.resize((2 * r, 2 * r), Image.BILINEAR).point(lambda v: int(v * inten))
        patch = Image.new("RGB", (2 * r, 2 * r), C.hex2rgb(col))
        gl.paste(patch, (int(qw * cx) - r, int(qh * cy) - r), m)
    base = ImageChops.screen(base, gl.resize((W2, H2), Image.BILINEAR))
    d = ImageDraw.Draw(base, "RGBA")
    horizon = int(H2 * 0.60); vpx = W2 // 2
    for i in range(-9, 10):
        d.line([(vpx, horizon), (vpx + i * int(W2 * 0.17), H2)], fill=(30, 110, 200, 52), width=2)
    y = horizon; step = 6
    while y < H2:
        d.line([(0, y), (W2, y)], fill=(30, 110, 200, 44), width=2)
        y += step; step = int(step * 1.35) + 2
    for _ in range(18):
        x = rnd.randint(0, W2); yy = rnd.randint(0, int(H2 * 0.55)); pts = [(x, yy)]
        for _ in range(rnd.randint(3, 6)):
            if rnd.random() < 0.5:
                x += rnd.choice([-1, 1]) * rnd.randint(40, 190)
            else:
                yy += rnd.choice([-1, 1]) * rnd.randint(40, 170)
            x = max(0, min(W2, x)); yy = max(0, min(int(H2 * 0.58), yy))
            pts.append((x, yy))
        d.line(pts, fill=(24, 86, 160, 115), width=3)
        d.ellipse([pts[-1][0] - 6, pts[-1][1] - 6, pts[-1][0] + 6, pts[-1][1] + 6], fill=(0, 229, 255, 140))
    for yy in range(0, int(H2 * 0.56), 46):
        for xx in range(0, W2, 46):
            d.ellipse([xx, yy, xx + 2, yy + 2], fill=(70, 140, 220, 38))
    if variant == "intro":
        layers = [[(int(W2 * 0.14), int(H2 * (0.16 + 0.09 * i))) for i in range(4)],
                  [(int(W2 * 0.50), int(H2 * (0.11 + 0.07 * i))) for i in range(6)],
                  [(int(W2 * 0.86), int(H2 * (0.18 + 0.11 * i))) for i in range(3)]]
        for a, bb in ((0, 1), (1, 2)):
            for p in layers[a]:
                for q in layers[bb]:
                    d.line([p, q], fill=(0, 180, 255, 46), width=2)
        for lay in layers:
            for p in lay:
                d.ellipse([p[0] - 11, p[1] - 11, p[0] + 11, p[1] + 11], fill=(0, 229, 255, 130))
                d.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], fill=(255, 255, 255, 200))
    noise = Image.effect_noise((max(2, W2 // 2), max(2, H2 // 2)), 14).convert("RGB").resize((W2, H2), Image.BILINEAR)
    base = Image.blend(base, ImageChops.screen(base, noise), 0.05)
    vig = Image.radial_gradient("L").resize((W2, H2), Image.BILINEAR).point(lambda v: int(v * 0.72))
    base = Image.composite(Image.new("RGB", (W2, H2), (0, 0, 0)), base, vig)
    path.parent.mkdir(parents=True, exist_ok=True)
    base.save(str(path), "PNG", compress_level=3)
    return path


def make_glow(path, size):
    from PIL import Image, ImageOps
    b = C.cfg()["brand"]
    m = ImageOps.invert(Image.radial_gradient("L")).resize((size, size), Image.BILINEAR).point(lambda v: int(v * 0.30))
    im = Image.new("RGBA", (size, size), C.hex2rgb(b["blue"]) + (0,))
    im.putalpha(m)
    im.save(str(path), "PNG", compress_level=3)


def make_particles(path, W, H, seed=11, count=90):
    from PIL import Image, ImageDraw
    rnd = random.Random(seed)
    im = Image.new("RGBA", (W, H + 160), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for _ in range(count):
        x = rnd.randint(0, W - 1); y = rnd.randint(0, H + 159)
        r = rnd.choice([2, 2, 3, 4]); a = rnd.randint(35, 140)
        col = (0, 229, 255, a) if rnd.random() < 0.7 else (255, 255, 255, a)
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    im.save(str(path), "PNG", compress_level=3)


def make_scan(path, W):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (W, 12), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 3, W, 8], fill=(0, 229, 255, 22))
    d.rectangle([0, 5, W, 6], fill=(190, 245, 255, 42))
    im.save(str(path), "PNG", compress_level=3)


def _hexmark(d, cx, cy, r, color, width=4):
    pts = [(cx + r * math.cos(math.radians(60 * i - 30)), cy + r * math.sin(math.radians(60 * i - 30))) for i in range(6)]
    d.polygon(pts, outline=color, width=width)
    d.ellipse([cx - r * 0.30, cy - r * 0.30, cx + r * 0.30, cy + r * 0.30], fill=color)


def draw_icon(d, kind, box, color):
    x0, y0, x1, y1 = box; w = x1 - x0; h = y1 - y0
    if kind == "chat":
        d.rounded_rectangle([x0, y0, x1, y0 + h * 0.74], radius=int(h * 0.20), outline=color, width=4)
        d.polygon([(x0 + w * 0.24, y0 + h * 0.72), (x0 + w * 0.44, y0 + h * 0.72), (x0 + w * 0.26, y1)], fill=color)
        for i in range(3):
            d.ellipse([x0 + w * (0.24 + 0.22 * i), y0 + h * 0.30, x0 + w * (0.32 + 0.22 * i), y0 + h * 0.38], fill=color)
    elif kind == "search":
        d.ellipse([x0, y0, x0 + w * 0.72, y0 + h * 0.72], outline=color, width=5)
        d.line([(x0 + w * 0.62, y0 + h * 0.62), (x1, y1)], fill=color, width=6)
        d.ellipse([x0 + w * 0.28, y0 + h * 0.28, x0 + w * 0.42, y0 + h * 0.42], fill=color)
    elif kind == "design":
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(h * 0.16), outline=color, width=4)
        d.polygon([(x0 + w * 0.18, y1 - h * 0.18), (x0 + w * 0.46, y0 + h * 0.30), (x0 + w * 0.74, y1 - h * 0.18)], fill=color)
        d.ellipse([x0 + w * 0.66, y0 + h * 0.16, x0 + w * 0.84, y0 + h * 0.34], fill=color)
    elif kind == "video":
        d.rounded_rectangle([x0, y0, x1, y1], radius=int(h * 0.16), outline=color, width=4)
        d.polygon([(x0 + w * 0.38, y0 + h * 0.26), (x0 + w * 0.38, y0 + h * 0.74), (x0 + w * 0.74, y0 + h * 0.50)], fill=color)
    elif kind == "rocket":
        d.polygon([(x0 + w * 0.5, y0), (x1, y1), (x0 + w * 0.5, y0 + h * 0.76), (x0, y1)], outline=color, width=4)
        d.ellipse([x0 + w * 0.36, y0 + h * 0.30, x0 + w * 0.64, y0 + h * 0.58], fill=color)
    else:
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        d.polygon([(cx, y0), (cx + w * 0.16, cy - h * 0.16), (x1, cy), (cx + w * 0.16, cy + h * 0.16),
                   (cx, y1), (cx - w * 0.16, cy + h * 0.16), (x0, cy), (cx - w * 0.16, cy - h * 0.16)], fill=color)


def make_bug(path, W):
    from engine import brand
    brand.make_bug(path, W)


def make_bar(path, W):
    from PIL import Image, ImageDraw
    b = C.cfg()["brand"]
    im = Image.new("RGBA", (W, 10), (0, 0, 0, 0))
    ImageDraw.Draw(im).rectangle([0, 0, W, 9], fill=C.hex2rgb(b["electric"]) + (215,))
    im.save(str(path), "PNG", compress_level=3)


def make_label(path, W, text):
    from PIL import Image
    pen = C.ArabicPen(C.resolve_font(verbose=False), C.scale(44, W), bold=True)
    li = pen.line_img(text, (255, 235, 120, 255))
    im = Image.new("RGBA", (li.width + 40, li.height + 20), (120, 20, 20, 190))
    im.alpha_composite(li, (20, 10))
    im.save(str(path), "PNG", compress_level=3)


def _chips_row(pen, chips, brand):
    from PIL import Image, ImageDraw
    imgs = []
    for ch in chips[:3]:
        li = pen.line_img(ch, C.hex2rgb(brand["white"]) + (240,))
        pad = C.scale(22, 1080)
        box = Image.new("RGBA", (li.width + 2 * pad, li.height + C.scale(10, 1080)), (0, 0, 0, 0))
        d = ImageDraw.Draw(box)
        d.rounded_rectangle([0, 0, box.width - 1, box.height - 1], radius=box.height // 2,
                            fill=(12, 30, 56, 210), outline=C.hex2rgb(brand["blue"]) + (170,), width=2)
        box.alpha_composite(li, (pad, C.scale(5, 1080)))
        imgs.append(box)
    if not imgs:
        return None
    gap = C.scale(16, 1080)
    total = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    row = Image.new("RGBA", (total, max(i.height for i in imgs)), (0, 0, 0, 0))
    x = total
    for i in imgs:
        x -= i.width; row.alpha_composite(i, (x, 0)); x -= gap
    return row


def make_card(path, W, idx, sc):
    from PIL import Image, ImageDraw
    b = C.cfg()["brand"]
    f = C.resolve_font(verbose=False); fb = C.resolve_font(bold=True, verbose=False)
    kind = sc["kind"]; m = C.scale(70, W)
    if kind == "intro":
        h = C.scale(700, W)
        pbig = C.ArabicPen(fb, C.scale(120, W), bold=True, stroke=1)
        pt = C.ArabicPen(fb, C.scale(74, W), bold=True, stroke=1)
        ps = C.ArabicPen(f, C.scale(46, W))
        im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([m, 0, W - m, h - 1], radius=C.scale(38, W), fill=(6, 11, 20, 195),
                            outline=C.hex2rgb(b["blue"]) + (150,), width=3)
        num = pbig.latin_img("5", C.hex2rgb(b["electric"]) + (255,))
        im.alpha_composite(num, ((W - num.width) // 2, C.scale(30, W)))
        for txt, col, yy in (("أدوات ذكاء اصطناعي", b["white"], 230), ("تبدأ بها مجاناً", b["electric"], 330)):
            li = pt.line_img(txt, C.hex2rgb(col) + (255,))
            im.alpha_composite(li, ((W - li.width) // 2, C.scale(yy, W)))
        li = ps.line_img("الخطط المجانية محدودة وقد تتغير", C.hex2rgb(b["muted"]) + (255,))
        im.alpha_composite(li, ((W - li.width) // 2, C.scale(470, W)))
        draw_icon(d, "spark", (W // 2 - C.scale(40, W), C.scale(560, W), W // 2 + C.scale(40, W), C.scale(640, W)),
                  C.hex2rgb(b["blue"]) + (220,))
        im.save(str(path), "PNG", compress_level=3); return
    if kind == "outro":
        h = C.scale(560, W)
        pt = C.ArabicPen(fb, C.scale(66, W), bold=True, stroke=1)
        ps = C.ArabicPen(f, C.scale(48, W))
        pl = C.ArabicPen(fb, C.scale(56, W), bold=True)
        im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([m, 0, W - m, h - 1], radius=C.scale(38, W), fill=(6, 11, 20, 200),
                            outline=C.hex2rgb(b["electric"]) + (170,), width=3)
        for i, (txt, col) in enumerate([("احفظ الفيديو", b["white"]), ("علّق: أي أداة نشرحها؟", b["electric"])]):
            li = pt.line_img(txt, C.hex2rgb(col) + (255,))
            im.alpha_composite(li, ((W - li.width) // 2, C.scale(40 + 110 * i, W)))
        lg = pl.line_img(C.cfg()["project"], C.hex2rgb(b["white"]) + (255,))
        im.alpha_composite(lg, ((W - lg.width) // 2, C.scale(290, W)))
        li = ps.line_img("تابعنا — المستقبل بدأ بالفعل", C.hex2rgb(b["muted"]) + (255,))
        im.alpha_composite(li, ((W - li.width) // 2, C.scale(400, W)))
        im.save(str(path), "PNG", compress_level=3); return
    h = C.scale(C.cfg()["layout"]["card_h"], W)
    pl = C.ArabicPen(fb, C.scale(86, W), bold=True)
    pa = C.ArabicPen(fb, C.scale(60, W), bold=True, stroke=1)
    pc = C.ArabicPen(f, C.scale(38, W))
    pn = C.ArabicPen(f, C.scale(32, W))
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([m, 0, W - m, h - 1], radius=C.scale(34, W), fill=(6, 11, 20, 195),
                        outline=C.hex2rgb(b["blue"]) + (150,), width=3)
    d.rectangle([W - m - C.scale(8, W), C.scale(30, W), W - m - C.scale(2, W), h - C.scale(30, W)],
                fill=C.hex2rgb(b["electric"]) + (220,))
    br = C.scale(84, W); bx = W - m - C.scale(40, W) - br; by = C.scale(36, W)
    d.ellipse([bx, by, bx + br, by + br], fill=(0, 229, 255, 40), outline=C.hex2rgb(b["electric"]) + (220,), width=3)
    nb = pl.latin_img("%02d" % idx, C.hex2rgb(b["electric"]) + (255,))
    im.alpha_composite(nb, (bx + (br - nb.width) // 2, by + (br - nb.height) // 2))
    ic = C.scale(74, W)
    draw_icon(d, sc["icon"], (m + C.scale(40, W), C.scale(46, W), m + C.scale(40, W) + ic, C.scale(46, W) + ic),
              C.hex2rgb(b["blue"]) + (230,))
    lg = pl.latin_img(sc["latin"], C.hex2rgb(b["white"]) + (255,))
    im.alpha_composite(lg, (max(m + C.scale(130, W), bx - C.scale(24, W) - lg.width), C.scale(30, W)))
    ar = pa.line_img(sc["title_ar"], C.hex2rgb(b["electric"]) + (255,))
    im.alpha_composite(ar, ((W - ar.width) // 2, C.scale(150, W)))
    row = _chips_row(pc, sc["chips"], b)
    if row is not None:
        im.alpha_composite(row, ((W - row.width) // 2, C.scale(265, W)))
    nt = pn.line_img("خطة مجانية محدودة", C.hex2rgb(b["muted"]) + (255,))
    im.alpha_composite(nt, ((W - nt.width) // 2, h - C.scale(80, W)))
    im.save(str(path), "PNG", compress_level=3)


def make_thumbnail(path, W, H, wide=False):
    from PIL import Image, ImageDraw
    b = C.cfg()["brand"]
    bgp = C.BG / ("thumb_bg_%dx%d.png" % (W, H))
    make_background(bgp, W, H, 99, "outro")
    base = Image.open(str(bgp)).convert("RGBA").resize((W, H), Image.BILINEAR)
    d = ImageDraw.Draw(base)
    fb = C.resolve_font(bold=True, verbose=False)
    if wide:
        p5 = C.ArabicPen(fb, int(H * 0.42), bold=True, stroke=2)
        pt = C.ArabicPen(fb, int(H * 0.15), bold=True, stroke=1)
        pl = C.ArabicPen(fb, int(H * 0.075), bold=True)
        num = p5.latin_img("5", C.hex2rgb(b["electric"]) + (255,))
        base.alpha_composite(num, (int(W * 0.05), int(H * 0.20)))
        xr = int(W * 0.95)
        for i, txt in enumerate(["أدوات AI", "مجانية!"]):
            li = pt.line_img(txt, C.hex2rgb(b["white"] if i == 0 else b["electric"]) + (255,))
            base.alpha_composite(li, (xr - li.width, int(H * (0.20 + 0.26 * i))))
        lg = pl.line_img(C.cfg()["project"], C.hex2rgb(b["muted"]) + (255,))
        base.alpha_composite(lg, (xr - lg.width, int(H * 0.80)))
    else:
        p5 = C.ArabicPen(fb, C.scale(430, W), bold=True, stroke=3)
        pt = C.ArabicPen(fb, C.scale(118, W), bold=True, stroke=2)
        ps = C.ArabicPen(fb, C.scale(64, W), bold=True)
        pl = C.ArabicPen(fb, C.scale(52, W), bold=True)
        num = p5.latin_img("5", C.hex2rgb(b["electric"]) + (255,))
        base.alpha_composite(num, ((W - num.width) // 2, C.scale(230, W)))
        for i, (txt, col) in enumerate([("أدوات AI", b["white"]), ("مجانية!", b["electric"])]):
            li = pt.line_img(txt, C.hex2rgb(col) + (255,))
            base.alpha_composite(li, ((W - li.width) // 2, C.scale(700 + 150 * i, W)))
        yy = C.scale(1080, W)
        for n in ["ChatGPT", "Gemini", "Perplexity", "Canva", "CapCut"]:
            li = ps.latin_img(n, C.hex2rgb(b["white"]) + (245,))
            pad = C.scale(26, W)
            box = Image.new("RGBA", (li.width + 2 * pad, li.height + C.scale(8, W)), (0, 0, 0, 0))
            dd = ImageDraw.Draw(box)
            dd.rounded_rectangle([0, 0, box.width - 1, box.height - 1], radius=box.height // 2,
                                 fill=(10, 24, 46, 215), outline=C.hex2rgb(b["blue"]) + (190,), width=3)
            box.alpha_composite(li, (pad, C.scale(4, W)))
            base.alpha_composite(box, ((W - box.width) // 2, yy))
            yy += box.height + C.scale(16, W)
        lg = pl.line_img(C.cfg()["project"], C.hex2rgb(b["electric"]) + (255,))
        base.alpha_composite(lg, ((W - lg.width) // 2, H - C.scale(190, W)))
        d.rectangle([0, H - C.scale(16, W), W, H - 1], fill=C.hex2rgb(b["electric"]) + (255,))
    base.convert("RGB").save(str(path), "JPEG", quality=93, optimize=True)


def build_all(preview=False):
    W, H, fps = C.dims(preview)
    scenes = parse_script()
    C.log("ASSETS: %dx%d preview=%s scenes=%d" % (W, H, preview, len(scenes)))
    make_glow(glow_file(W), max(64, C.scale(900, W)))
    make_particles(part_file(W, H), W, H)
    make_scan(scan_file(W), W)
    make_bug(bug_file(W), W)
    make_bar(bar_file(W), W)
    make_label(label_file(W), W, "معاينة بصرية — بدون صوت")
    ti = 0
    for i, sc in enumerate(scenes):
        make_background(bg_file(i, W, H), W, H, 1000 + i * 37, sc["kind"])
        if sc["kind"] == "tool":
            ti += 1
        make_card(card_file(i, W), W, ti, sc)
        C.log("  scene %02d (%s) ok" % (i, sc["id"]))
    make_thumbnail(C.OUT / "thumbnail.jpg", W, H, wide=False)
    make_thumbnail(C.OUT / "thumbnail_yt.jpg", 1280, 720, wide=True)
    C.log("ASSETS done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--preview", action="store_true")
    build_all(ap.parse_args().preview)
