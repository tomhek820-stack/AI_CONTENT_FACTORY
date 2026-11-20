from __future__ import annotations
import sys
from pathlib import Path as _P
_ROOT = _P(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from pathlib import Path
from PIL import Image, ImageDraw
from engine import common as C
from engine import identity as ID

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "identity_demo.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
d = ID.load_identity()
ink = ID.palette_rgb("ink", d)
turq = ID.palette_rgb("turquoise", d)
paper = ID.palette_rgb("paper", d)
gold = ID.palette_rgb("gold", d)
margin = ID.get("layout.margin_side", 96, d)

im = Image.new("RGBA", (W, H), ink)
draw = ImageDraw.Draw(im)

# زاوية معقلية مؤقتة 5x5
cell = 10
mx, my = 984, 180
pattern = [
    [0, 1, 1, 1, 0],
    [0, 1, 0, 1, 0],
    [0, 1, 1, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 1, 1],
]
for ry, row in enumerate(pattern):
    for rx, v in enumerate(row):
        if v:
            x = mx + rx * cell
            y = my + ry * cell
            draw.rectangle([x, y, x + cell - 2, y + cell - 2], fill=turq)

title_fp = ID.font_path("title", d)
body_fp = ID.font_path("body", d)
wisdom_fp = ID.font_path("wisdom", d)

pen_title = C.ArabicPen(str(title_fp), 92, bold=True, stroke=1)
title = pen_title.line_img("اختبار الهوية العربية", paper)
tx = W - margin - title.width
ty = 760
im.alpha_composite(title, (tx, ty))

rule_y = ty + title.height + 20
draw.rectangle([tx, rule_y, W - margin, rule_y + 2], fill=gold)

pen_body = C.ArabicPen(str(body_fp), 56, stroke=0)
body = pen_body.line_img("بِسْمِ اللَّهِ", paper)
im.alpha_composite(body, (W - margin - body.width, 1040))

pen_wisdom = C.ArabicPen(str(wisdom_fp), 64, bold=True, stroke=1)
wisdom = pen_wisdom.line_img("هَذِهِ جُمْلَةٌ مُشَكَّلَة", gold)
im.alpha_composite(wisdom, (W - margin - wisdom.width, 1240))

im.convert("RGB").save(str(OUT), "PNG")
print("✅ demo:", OUT)
print("fonts used:")
print(" title :", title_fp.name)
print(" body  :", body_fp.name)
print(" wisdom:", wisdom_fp.name)
