"""يبني tool scene نموذجي بالهوية الجديدة + scene graph."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw
from engine import common as C
from engine import identity as ID
from engine import backgrounds
from engine import scene_graph as SG

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "scene_graph"
OUT.mkdir(parents=True, exist_ok=True)

W, H = 1080, 1920
d = ID.load_identity()
margin = 96

TITLE = "أولا: رسوم الانتقال"
SUBTITLE = "اذهب إلى خيارات المطور"
CHIPS = ["رسوم", "انتقال", "استجابة"]

paper = ID.palette_rgb("paper", d)
turq  = ID.palette_rgb("turquoise", d)

# 1. خلفية
bg = backgrounds.horizon_glow(W, H, d)
bg.save(str(OUT / "l0_bg.png"), "PNG", optimize=True)

# 2. عنوان (auto-fit)
title_fp = ID.font_path("title", d)
size = 82
max_w = W - 2 * margin
while size >= 56:
    pen = C.ArabicPen(str(title_fp), size, bold=True, stroke=1)
    ti = pen.line_img(TITLE, paper)
    if ti.width <= max_w:
        break
    size -= 4
tx = W - margin - ti.width
ty = 400
ti.save(str(OUT / "l1_title.png"), "PNG", optimize=True)
print(f"   title: {ti.size} @ {size}px → x={tx}")

# 3. subtitle
body_fp = ID.font_path("body", d)
pen_s = C.ArabicPen(str(body_fp), 48, stroke=0)
si = pen_s.line_img(SUBTITLE, turq)
sx = W - margin - si.width
sy = ty + ti.height + 30
si.save(str(OUT / "l2_subtitle.png"), "PNG", optimize=True)

# 4. chips (كطبقة واحدة)
chip_pen = C.ArabicPen(str(body_fp), 38, stroke=0)
boxes = []
for ch in CHIPS:
    ci = chip_pen.line_img(ch, paper)
    pad_x, pad_y = 28, 14
    w = ci.width + pad_x * 2
    h = ci.height + pad_y * 2
    box = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([0, 0, w-1, h-1], radius=h//2,
                         fill=(13, 32, 60, 220),
                         outline=(turq[0], turq[1], turq[2], 180), width=2)
    box.alpha_composite(ci, (pad_x, pad_y))
    boxes.append(box)

gap = 16
total_w = sum(b.width for b in boxes) + gap * (len(boxes) - 1)
max_h = max(b.height for b in boxes)
chips = Image.new("RGBA", (total_w, max_h), (0, 0, 0, 0))
cx = total_w
for b in boxes:
    cx -= b.width
    chips.alpha_composite(b, (cx, (max_h - b.height) // 2))
    cx -= gap

chips_x = W - margin - chips.width
chips_y = H - 500
chips.save(str(OUT / "l3_chips.png"), "PNG", optimize=True)

# 5. بناء scene
scene = SG.Scene(
    duration=8.0,
    background=OUT / "l0_bg.png",
    layers=[
        SG.Layer(OUT / "l1_title.png",    tx,      ty,      t_in=0.2, entry="right"),
        SG.Layer(OUT / "l2_subtitle.png", sx,      sy,      t_in=0.6, entry="fade_in"),
        SG.Layer(OUT / "l3_chips.png",    chips_x, chips_y, t_in=1.0, entry="rise"),
    ],
    W=W, H=H, fps=30,
)

video = OUT / "tool_v3.mp4"
scene.render(video)
print(f"✅ {video} ({video.stat().st_size // 1024} KB)")

SG.last_frame(video, OUT / "tool_v3_last.png")
print(f"✅ {OUT / 'tool_v3_last.png'}")
