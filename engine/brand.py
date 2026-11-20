from engine import common as C

def make_bug(path, W):
    from PIL import Image, ImageDraw
    b = C.cfg()["brand"]
    name = C.cfg().get("project", "أبو محمد المساوى")
    font = C.resolve_font(bold=True, verbose=False)
    pen = C.ArabicPen(font, C.scale(44, W), bold=True, stroke=1)
    ni = pen.line_img(name, C.hex2rgb(b["white"]) + (255,))
    pad = C.scale(22, W)
    w = ni.width + 2 * pad
    h = ni.height + C.scale(22, W)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2,
                        fill=(5, 9, 16, 170),
                        outline=C.hex2rgb(b["blue"]) + (125,),
                        width=max(2, C.scale(2, W)))
    im.alpha_composite(ni, (pad, C.scale(4, W)))
    y = h - C.scale(9, W)
    d.line([(pad, y), (w - pad, y)], fill=C.hex2rgb(b["electric"]) + (225,), width=max(2, C.scale(3, W)))
    im.save(str(path), "PNG", compress_level=3)
