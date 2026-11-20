"""intro_v3: مشهد المقدمة بالهوية العربية الجديدة (Amiri + V5).
   font auto-fit: يتقلص حتى يناسب العرض دون قطع."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw
from engine import common as C
from engine import identity as ID
from engine import backgrounds

ROOT = Path(__file__).resolve().parent.parent
MOTIFS = ROOT / "assets" / "motifs"


def _fit_title(text, font_path, max_width, start_size=92, min_size=56, step=4):
    """يقلص حجم الخط حتى يناسب النص عرض الشاشة."""
    size = start_size
    while size >= min_size:
        pen = C.ArabicPen(str(font_path), size, bold=True, stroke=1)
        img = pen.line_img(text, (255, 255, 255, 255))
        if img.width <= max_width:
            return img, size
        size -= step
    pen = C.ArabicPen(str(font_path), min_size, bold=True, stroke=1)
    return pen.line_img(text, (255, 255, 255, 255)), min_size


def render_intro_v3(title, subtitle, W=1080, H=1920, d=None):
    if d is None:
        d = ID.load_identity()

    paper = ID.palette_rgb("paper", d)
    turq = ID.palette_rgb("turquoise", d)
    gold = ID.palette_rgb("gold", d)
    margin = ID.get("layout.margin_side", 96, d)

    im = backgrounds.horizon_glow(W, H, d)

    motif_path = MOTIFS / "corner_kufic.png"
    if motif_path.exists():
        motif = Image.open(str(motif_path)).convert("RGBA")
        im.alpha_composite(motif, (984, 180))

    # Title with auto-fit (max_width = W - 2*margin)
    title_fp = ID.font_path("title", d)
    max_w = W - 2 * margin
    title_img, used_size = _fit_title(title, title_fp, max_w)

    tx = W - margin - title_img.width
    ty = 760
    im.alpha_composite(title_img, (tx, ty))
    print(f"   title: {title_img.size} @ {used_size}px → x={tx}")

    dd = ImageDraw.Draw(im)
    rule_y = ty + title_img.height + 20
    rule_w = int(W * 0.40)
    dd.rectangle([W - margin - rule_w, rule_y, W - margin, rule_y + 2], fill=gold)

    body_fp = ID.font_path("body", d)
    pen_s = C.ArabicPen(str(body_fp), 52, stroke=0)
    sub_img = pen_s.line_img(subtitle, turq)
    sx = W - margin - sub_img.width
    sy = rule_y + 30
    im.alpha_composite(sub_img, (sx, sy))

    wisdom_fp = ID.font_path("wisdom", d)
    pen_w = C.ArabicPen(str(wisdom_fp), 44, bold=True, stroke=1)
    w_img = pen_w.line_img("أبو محمد المساوى", paper)
    alpha = w_img.getchannel("A").point(lambda v: int(v * 0.7))
    w_img.putalpha(alpha)
    wx = W - margin - w_img.width
    wy = H - 260
    im.alpha_composite(w_img, (wx, wy))

    return im
