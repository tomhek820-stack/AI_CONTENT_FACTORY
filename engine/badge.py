"""يرسم شارة أبو محمد المساوى."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw
from engine import common as C
from engine import identity as ID


def render_badge(W=1080, d=None):
    """شارة صغيرة أعلى الشاشة."""
    if d is None:
        d = ID.load_identity()
    paper = ID.palette_rgb("paper", d)
    turq = ID.palette_rgb("turquoise", d)
    ink = ID.palette_rgb("ink", d)

    body_fp = ID.font_path("body", d)
    pen = C.ArabicPen(str(body_fp), 32, bold=True, stroke=1)
    txt = pen.line_img("أبو محمد المساوى", paper)

    pad_x, pad_y = 28, 12
    w = txt.width + pad_x * 2
    h = txt.height + pad_y * 2 + 4

    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d_draw = ImageDraw.Draw(im)
    d_draw.rounded_rectangle([0, 0, w-1, h-1], radius=h//2,
                              fill=(ink[0], ink[1], ink[2], 220),
                              outline=(turq[0], turq[1], turq[2], 200),
                              width=2)
    # شريط صغير فيروزي يسار
    d_draw.ellipse([pad_x-10, h//2-4, pad_x-2, h//2+4], fill=turq)

    im.alpha_composite(txt, (pad_x, pad_y))
    return im
