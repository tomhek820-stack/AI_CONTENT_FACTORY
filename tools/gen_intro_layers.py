"""يفصل intro_v3 إلى 5 طبقات PNG منفصلة."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image
from engine import common as C
from engine import identity as ID
from engine import backgrounds

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "intro_layers"
OUT.mkdir(parents=True, exist_ok=True)
MOTIFS = ROOT / "assets" / "motifs"

W, H = 1080, 1920
d = ID.load_identity()
paper = ID.palette_rgb("paper", d)
turq = ID.palette_rgb("turquoise", d)
gold = ID.palette_rgb("gold", d)
margin = ID.get("layout.margin_side", 96, d)

TITLE = "هاتفك بطيء؟ المشكلة ليست فيه"
SUBTITLE = "الحلقة السادسة: تسريع الهاتف"

# ── Layer 1: bg + motif (static)
bg = backgrounds.horizon_glow(W, H, d)
motif_path = MOTIFS / "corner_kufic.png"
if motif_path.exists():
    bg.alpha_composite(Image.open(str(motif_path)).convert("RGBA"), (984, 180))
bg.convert("RGB").save(str(OUT / "01_bg_motif.png"), "PNG", optimize=True)

# ── Layer 2: title (small, at final position)
title_fp = ID.font_path("title", d)
pen_t = C.ArabicPen(str(title_fp), 92, bold=True, stroke=1)
title_img = pen_t.line_img(TITLE, paper)
tx = W - margin - title_img.width
ty = 760
title_img.save(str(OUT / "02_title.png"), "PNG", optimize=True)
print(f"   title: {title_img.size} → x={tx}, y={ty}")

# ── Layer 3: gold rule
rule_w = int(W * 0.40)
gold_img = Image.new("RGBA", (rule_w, 2), gold)
gx = W - margin - rule_w
gy = ty + title_img.height + 20
gold_img.save(str(OUT / "03_gold.png"), "PNG")
print(f"   gold: {gold_img.size} → x={gx}, y={gy}")

# ── Layer 4: subtitle
body_fp = ID.font_path("body", d)
pen_s = C.ArabicPen(str(body_fp), 52, stroke=0)
sub_img = pen_s.line_img(SUBTITLE, turq)
sx = W - margin - sub_img.width
sy = gy + 30
sub_img.save(str(OUT / "04_subtitle.png"), "PNG", optimize=True)
print(f"   subtitle: {sub_img.size} → x={sx}, y={sy}")

# ── Layer 5: channel
wisdom_fp = ID.font_path("wisdom", d)
pen_w = C.ArabicPen(str(wisdom_fp), 44, bold=True, stroke=1)
w_img = pen_w.line_img("أبو محمد المساوى", paper)
alpha = w_img.getchannel("A").point(lambda v: int(v * 0.7))
w_img.putalpha(alpha)
cx = W - margin - w_img.width
cy = H - 260
w_img.save(str(OUT / "05_channel.png"), "PNG", optimize=True)
print(f"   channel: {w_img.size} → x={cx}, y={cy}")

# حفظ المواضع للاستخدام في FFmpeg
import json
(OUT / "positions.json").write_text(json.dumps({
    "title": [tx, ty], "gold": [gx, gy],
    "subtitle": [sx, sy], "channel": [cx, cy],
    "W": W, "H": H, "duration": 2.5
}, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n✅ 5 layers in {OUT}")
