import argparse, json
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from engine import common as C

CFG = {
    "vertical": dict(W=1080, H=1920, scrim=.42, band=(.50, .80), lines=3,
                     size=.062, name_size=.030, name_bottom=.10),
    "tiktok":   dict(W=1080, H=1440, scrim=.32, band=(.34, .74), lines=3,
                     size=.066, name_size=.032, name_bottom=.225),
    "wide":     dict(W=1280, H=720,  scrim=.28, band=(.32, .72), lines=2,
                     size=.115, name_size=.062, name_bottom=.16),
}


def get_title(vid, override):
    if override:
        return override
    pj = Path(f"scripts/publish_{vid}.json")
    if pj.exists():
        m = json.loads(pj.read_text(encoding="utf-8"))
        if m.get("cover_title"):
            return m["cover_title"]
    sj = Path(f"scripts/video_{vid}.txt")
    if sj.exists():
        for line in sj.read_text(encoding="utf-8").splitlines():
            f = [x.strip() for x in line.split("|")]
            if f and f[0] == "SCENE":
                return f[3]
    return C.cfg().get("title", "أبو محمد المساوى")


def prep_bg(path, W, H):
    if path and Path(path).exists():
        im = Image.open(path).convert("RGB")
        return ImageOps.fit(im, (W, H), Image.LANCZOS, centering=(0.5, 0.30))
    import engine.studio as ST
    p = ST.bg_image(99, W, H, "outro")
    return Image.open(str(p)).convert("RGB").resize((W, H), Image.LANCZOS)


def compose(bg, title, vid, kind, guides=False):
    k = CFG[kind]
    W, H = k["W"], k["H"]
    b = C.cfg()["brand"]
    im = bg.copy().convert("RGBA")

    scrim = Image.new("L", (1, H), 0)
    s0 = k["scrim"]
    for y in range(H):
        t = y / H
        v = 0 if t < s0 else int(228 * ((t - s0) / (1 - s0)) ** 0.72)
        scrim.putpixel((0, y), min(238, v))
    im = Image.composite(Image.new("RGBA", (W, H), (2, 4, 9, 255)), im, scrim.resize((W, H)))
    d = ImageDraw.Draw(im)

    f = C.resolve_font(bold=True, verbose=False)
    maxw = W - 2 * int(W * 0.085)
    band_h = int(H * (k["band"][1] - k["band"][0]))
    size = int(H * k["size"])
    while size > 40:
        pen = C.ArabicPen(f, size, bold=True, stroke=max(2, size // 32))
        lines = pen.wrap(title, maxw, max_lines=k["lines"])
        imgs = [pen.line_img(l, C.hex2rgb(b["white"]) + (255,)) for l in lines]
        gap = int(size * 0.08)
        th = sum(i.height for i in imgs) + gap * (len(imgs) - 1)
        if th <= band_h:
            break
        size -= 4

    y = int(H * k["band"][0]) + max(0, (band_h - th) // 2)
    for i in imgs:
        im.alpha_composite(i, ((W - i.width) // 2, y))
        y += i.height + gap

    bw = int(W * 0.17)
    by = y + int(size * 0.14)
    d.rectangle([(W - bw) // 2, by, (W + bw) // 2, by + max(4, H // 260)],
                fill=C.hex2rgb(b["electric"]) + (255,))

    np = C.ArabicPen(f, int(H * k["name_size"]), bold=True)
    ni = np.line_img(C.cfg().get("project", "أبو محمد المساوى"), C.hex2rgb(b["electric"]) + (255,))
    im.alpha_composite(ni, ((W - ni.width) // 2, int(H * (1 - k["name_bottom"]))))

    label = "تعريفي" if vid == "000" else f"حلقة {int(vid)}"
    lp = C.ArabicPen(C.resolve_font(verbose=False), int(H * 0.026))
    li = lp.line_img(label, C.hex2rgb(b["white"]) + (240,))
    pad = int(H * 0.013)
    pill = Image.new("RGBA", (li.width + 2 * pad, li.height + pad), (0, 0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([0, 0, pill.width - 1, pill.height - 1], radius=pill.height // 2,
                         fill=(6, 12, 22, 215), outline=C.hex2rgb(b["blue"]) + (190,), width=2)
    pill.alpha_composite(li, (pad, pad // 2))
    im.alpha_composite(pill, (W - pill.width - int(W * 0.07), int(H * 0.055)))

    d.rectangle([0, H - max(6, H // 150), W, H - 1], fill=C.hex2rgb(b["electric"]) + (255,))

    if guides:
        gh = int(W * 4 / 3)
        top = (H - gh) // 2
        d.rectangle([2, top, W - 3, top + gh], outline=(255, 190, 60, 230), width=5)
        rb = int(H * 0.13)
        d.rectangle([2, H - rb, W - 3, H - 3], outline=(255, 90, 90, 200), width=4)

    return im.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("vid")
    ap.add_argument("image", nargs="?", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--guides", action="store_true")
    a = ap.parse_args()
    title = get_title(a.vid, a.title)
    out = Path("output") / a.vid
    out.mkdir(parents=True, exist_ok=True)
    jobs = [("thumbnail.jpg", "vertical"), ("thumbnail_tiktok.jpg", "tiktok"), ("thumbnail_yt.jpg", "wide")]
    for fname, kind in jobs:
        k = CFG[kind]
        img = compose(prep_bg(a.image, k["W"], k["H"]), title, a.vid, kind,
                      guides=(a.guides and kind == "vertical"))
        img.save(str(out / fname), "JPEG", quality=94, optimize=True)
        print(f"✅ {fname}  {k['W']}x{k['H']}")
    print("📝 العنوان:", title)
    print("📁", out)


if __name__ == "__main__":
    main()
