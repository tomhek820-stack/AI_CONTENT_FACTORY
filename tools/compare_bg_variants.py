"""يجمع 6 خلفيات في شبكة واحدة للمقارنة."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw
try:
    RESAMPLE = Image.Resampling.LANCZOS
except AttributeError:
    RESAMPLE = Image.LANCZOS

ROOT = Path(__file__).resolve().parent.parent
VARIANTS = ROOT / "spike_tmp" / "bg_variants"
OUT = ROOT / "spike_tmp" / "bg_compare_grid.png"

LABELS = {
    "v1_solid":      "V1 - حبر صلب",
    "v2_radial":     "V2 - توهج مركزي",
    "v3_vertical":   "V3 - تدرج عمودي",
    "v4_kufic_tex":  "V4 - نسيج معقلي",
    "v5_horizon":    "V5 - خط ضوء",
    "v6_vignette":   "V6 - Vignette",
}

# كل صورة 1080×1920 → نُصغّرها إلى 400×711
THUMB_W = 400
THUMB_H = 711
COLS = 3
ROWS = 2
GAP = 20
LABEL_H = 55

canvas_w = COLS * THUMB_W + (COLS + 1) * GAP
canvas_h = ROWS * (THUMB_H + LABEL_H) + (ROWS + 1) * GAP + 70

canvas = Image.new("RGBA", (canvas_w, canvas_h), (15, 15, 22, 255))

# عنوان
try:
    from engine import common as C
    from engine import identity as ID
    d = ID.load_identity()
    fp = ID.font_path("title", d)
    pen = C.ArabicPen(str(fp), 44, bold=True, stroke=1)
    title = pen.line_img("مقارنة الخلفيات الست", (232, 220, 200, 255))
    canvas.alpha_composite(title, ((canvas_w - title.width) // 2, 12))
except Exception as e:
    print(f"⚠️ title: {e}")

for idx, (name, label) in enumerate(LABELS.items()):
    src = VARIANTS / f"{name}.png"
    if not src.exists():
        print(f"⚠️ missing: {src}")
        continue

    im = Image.open(str(src)).convert("RGBA").resize(
        (THUMB_W, THUMB_H), RESAMPLE
    )

    col = idx % COLS
    row = idx // COLS
    x = GAP + col * (THUMB_W + GAP)
    y = 70 + GAP + row * (THUMB_H + LABEL_H + GAP)

    # إطار
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([x - 2, y - 2, x + THUMB_W + 1, y + THUMB_H + 1],
                   outline=(50, 50, 70, 255), width=2)

    canvas.alpha_composite(im, (x, y))

    # label
    try:
        from engine import common as C
        from engine import identity as ID
        d = ID.load_identity()
        fp = ID.font_path("body", d)
        pen = C.ArabicPen(str(fp), 30, stroke=0)
        lbl = pen.line_img(label, (200, 200, 210, 255))
        canvas.alpha_composite(lbl, (x + (THUMB_W - lbl.width) // 2,
                                      y + THUMB_H + 10))
    except Exception as e:
        print(f"⚠️ label {name}: {e}")

canvas.convert("RGB").save(str(OUT), "PNG", optimize=True)
print(f"\n✅ {OUT} ({OUT.stat().st_size // 1024} KB)")
print(f"   {canvas_w}×{canvas_h}")
