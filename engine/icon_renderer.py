"""راسم أيقونات مستقل — قابل للاستخدام في أي مكان.
   نسخة من _p0_icon في studio.py لتجنب الاستيراد الثقيل."""
import math
from PIL import Image, ImageDraw


def draw_icon(name, size, color):
    """يرسم أيقونة بالاسم المحدد. يعيد Image RGBA بحجم (size, size)."""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    _draw(d, (name or "").lower(), 0, 0, size, size, color)
    return im


def _draw(d, name, x, y, w, h, col):
    cx, cy = x + w / 2, y + h / 2
    r = min(w, h) / 2
    dark = (5, 9, 16, 255)
    white = (255, 255, 255, 235)

    if name == "android":
        d.pieslice([cx - r*0.72, cy - r*0.86, cx + r*0.72, cy + r*0.18], 180, 360, fill=col)
        d.rectangle([cx - r*0.72, cy - r*0.08, cx + r*0.72, cy + r*0.62], fill=col)
        d.line([(cx - r*0.45, cy - r*0.72), (cx - r*0.62, cy - r*0.98)],
               fill=col, width=max(2, int(r*0.08)))
        d.line([(cx + r*0.45, cy - r*0.72), (cx + r*0.62, cy - r*0.98)],
               fill=col, width=max(2, int(r*0.08)))
        d.ellipse([cx - r*0.42, cy - r*0.52, cx - r*0.22, cy - r*0.32], fill=dark)
        d.ellipse([cx + r*0.22, cy - r*0.52, cx + r*0.42, cy - r*0.32], fill=dark)
    elif name in ("settings", "gear"):
        for i in range(8):
            a = math.radians(i * 45)
            tx = cx + math.cos(a) * r * 0.92
            ty = cy + math.sin(a) * r * 0.92
            d.ellipse([tx - r*0.16, ty - r*0.16, tx + r*0.16, ty + r*0.16], fill=col)
        d.ellipse([cx - r*0.78, cy - r*0.78, cx + r*0.78, cy + r*0.78], fill=col)
        d.ellipse([cx - r*0.34, cy - r*0.34, cx + r*0.34, cy + r*0.34], fill=dark)
    elif name == "battery":
        d.rounded_rectangle([x + r*0.18, y + r*0.42, x + w - r*0.34, y + h - r*0.42],
                            radius=int(r*0.18), outline=col, width=max(3, int(r*0.12)))
        d.rectangle([x + w - r*0.28, cy - r*0.22, x + w - r*0.10, cy + r*0.22], fill=col)
        d.rectangle([x + r*0.34, cy - r*0.34, x + w*0.62, cy + r*0.34], fill=col)
    elif name in ("storage", "database"):
        d.ellipse([cx - r*0.72, cy - r*0.82, cx + r*0.72, cy - r*0.42], fill=col)
        d.rectangle([cx - r*0.72, cy - r*0.62, cx + r*0.72, cy + r*0.58], fill=col)
        d.ellipse([cx - r*0.72, cy + r*0.38, cx + r*0.72, cy + r*0.78], fill=col)
        d.line([(cx - r*0.72, cy - r*0.12), (cx + r*0.72, cy - r*0.12)],
               fill=dark, width=max(2, int(r*0.08)))
        d.line([(cx - r*0.72, cy + r*0.28), (cx + r*0.72, cy + r*0.28)],
               fill=dark, width=max(2, int(r*0.08)))
    elif name == "terminal":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h - 4], radius=int(r*0.22),
                            fill=(8, 14, 26, 255), outline=col, width=max(3, int(r*0.1)))
        d.line([(cx - r*0.45, cy - r*0.28), (cx - r*0.12, cy)],
               fill=white, width=max(3, int(r*0.12)))
        d.line([(cx - r*0.12, cy), (cx - r*0.45, cy + r*0.28)],
               fill=white, width=max(3, int(r*0.12)))
        d.line([(cx + r*0.05, cy + r*0.28), (cx + r*0.48, cy + r*0.28)],
               fill=white, width=max(3, int(r*0.12)))
    elif name == "python":
        d.rounded_rectangle([cx - r*0.72, cy - r*0.82, cx + r*0.18, cy + r*0.08],
                            radius=int(r*0.28), fill=col)
        d.rounded_rectangle([cx - r*0.18, cy - r*0.08, cx + r*0.72, cy + r*0.82],
                            radius=int(r*0.28), fill=col)
        d.ellipse([cx - r*0.48, cy - r*0.58, cx - r*0.28, cy - r*0.38], fill=dark)
        d.ellipse([cx + r*0.28, cy + r*0.38, cx + r*0.48, cy + r*0.58], fill=dark)
    elif name == "git":
        pts = [(cx + r*math.cos(math.radians(60*i - 90)),
                cy + r*math.sin(math.radians(60*i - 90))) for i in range(6)]
        d.polygon(pts, fill=col)
        d.line([(cx - r*0.35, cy + r*0.35), (cx + r*0.35, cy - r*0.35)],
               fill=dark, width=max(3, int(r*0.12)))
        d.ellipse([cx - r*0.5, cy + r*0.2, cx - r*0.2, cy + r*0.5], fill=dark)
        d.ellipse([cx + r*0.2, cy - r*0.5, cx + r*0.5, cy - r*0.2], fill=dark)
    elif name == "github":
        d.ellipse([cx - r*0.78, cy - r*0.62, cx + r*0.78, cy + r*0.82], fill=col)
        d.polygon([(cx - r*0.62, cy - r*0.42), (cx - r*0.38, cy - r*0.86),
                   (cx - r*0.12, cy - r*0.48)], fill=col)
        d.polygon([(cx + r*0.62, cy - r*0.42), (cx + r*0.38, cy - r*0.86),
                   (cx + r*0.12, cy - r*0.48)], fill=col)
        d.ellipse([cx - r*0.34, cy - r*0.12, cx - r*0.12, cy + r*0.1], fill=dark)
        d.ellipse([cx + r*0.12, cy - r*0.12, cx + r*0.34, cy + r*0.1], fill=dark)
    elif name in ("chatgpt", "openai"):
        pts = []
        for i in range(12):
            a = math.radians(30*i - 90)
            rr = r if i % 2 == 0 else r * 0.48
            pts.append((cx + rr*math.cos(a), cy + rr*math.sin(a)))
        d.polygon(pts, fill=col)
        d.ellipse([cx - r*0.2, cy - r*0.2, cx + r*0.2, cy + r*0.2], fill=dark)
    elif name == "search":
        d.ellipse([x + r*0.18, y + r*0.18, x + w*0.68, y + h*0.68],
                  outline=col, width=max(4, int(r*0.16)))
        d.line([(x + w*0.58, y + h*0.58), (x + w - r*0.18, y + h - r*0.18)],
               fill=col, width=max(5, int(r*0.2)))
    elif name == "design":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h - 4],
                            radius=int(r*0.22), outline=col, width=max(4, int(r*0.14)))
        d.polygon([(x + w*0.22, y + h*0.78), (x + w*0.5, y + h*0.22),
                   (x + w*0.78, y + h*0.78)], fill=col)
    elif name == "video":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h - 4],
                            radius=int(r*0.22), outline=col, width=max(4, int(r*0.14)))
        d.polygon([(x + w*0.4, y + h*0.3), (x + w*0.4, y + h*0.7),
                   (x + w*0.74, y + h*0.5)], fill=col)
    elif name == "rocket":
        d.polygon([(cx, y + 4), (x + w - r*0.22, y + h*0.68),
                   (cx, y + h*0.82), (x + r*0.22, y + h*0.68)], fill=col)
        d.ellipse([cx - r*0.16, cy - r*0.34, cx + r*0.16, cy - r*0.02], fill=dark)
    elif name == "chat":
        d.rounded_rectangle([x + 4, y + 4, x + w - 4, y + h*0.74],
                            radius=int(r*0.24), fill=col)
        d.polygon([(x + w*0.24, y + h*0.72), (x + w*0.46, y + h*0.72),
                   (x + w*0.24, y + h*0.94)], fill=col)
    else:
        # fallback: نجمة
        pts = []
        for i in range(8):
            a = math.radians(45*i - 90)
            rr = r if i % 2 == 0 else r * 0.42
            pts.append((cx + rr*math.cos(a), cy + rr*math.sin(a)))
        d.polygon(pts, fill=col)
