"""جسر بين studio.py و scene_graph.
   لا يُستدعى إلا لو LEVEL3_SCENE_GRAPH=1 في البيئة."""
from __future__ import annotations
import os, json
from pathlib import Path
from PIL import Image, ImageDraw
from engine import common as C
from engine import identity as ID
from engine import scene_graph as SG
from engine import backgrounds
from engine import icon_fetcher
from engine import badge

ROOT = Path(__file__).resolve().parent.parent
MOTIFS = ROOT / "assets" / "motifs"


def is_active() -> bool:
    return os.environ.get("LEVEL3_SCENE_GRAPH", "0") == "1"


def render_card(sc, idx, total, W, H, out_dir: Path) -> Path:
    d = ID.load_identity()
    paper = ID.palette_rgb("paper", d)
    turq = ID.palette_rgb("turquoise", d)
    gold = ID.palette_rgb("gold", d)
    margin = ID.get("layout.margin_side", 96, d)
    kind = sc.get("kind", "tool")

    out_dir.mkdir(parents=True, exist_ok=True)
    base = out_dir / f"l3_{idx:02d}"

    # خلفية + motif
    bg = backgrounds.horizon_glow(W, H, d)
    motif_path = MOTIFS / "corner_kufic.png"
    if motif_path.exists():
        bg.alpha_composite(Image.open(str(motif_path)).convert("RGBA"), (984, 180))
    bg_path = base.parent / f"{base.name}_bg.png"
    bg.save(str(bg_path), "PNG", optimize=True)

    layers = []
    # ═══ Badge (شارة علوية) — لكل مشهد ═══
    try:
        badge_img = badge.render_badge(W, d)
        badge_path = base.parent / f"{base.name}_badge.png"
        badge_img.save(str(badge_path), "PNG", optimize=True)
        # موضع: أعلى اليسار (معكوس عن الـ motif)
        bx = 40
        by = 40
        layers.append(SG.Layer(badge_path, bx, by, t_in=0.0, entry="static"))
    except Exception as e:
        print(f"   [{idx}] badge failed: {e}")
    y_cursor = 400 if kind == "intro" else 550

    # ═══ الأيقونة hero — من Iconify (fetcher) ═══
    icon_name = sc.get("icon", "")
    if icon_name:
        icon_size = 160 if kind == "tool" else 120
        icon_y = 260
        icon_path = base.parent / f"{base.name}_icon.png"
        try:
            icon_img = icon_fetcher.fetch(icon_name, size=icon_size)
            icon_img.save(str(icon_path), "PNG", optimize=True)
            used = "Iconify"
        except Exception as e:
            print(f"   [{idx}] icon fetch failed ({e}), using fallback")
            from engine import icon_renderer
            icon_img = icon_renderer.draw_icon(
                icon_name, icon_size, turq[:3] + (255,)
            )
            icon_img.save(str(icon_path), "PNG", optimize=True)
            used = "programmatic"

        ix = (W - icon_size) // 2
        layers.append(SG.Layer(icon_path, ix, icon_y, t_in=0.2, entry="fade_in"))
        y_cursor = icon_y + icon_size + 40
        print(f"   [{idx}] icon: {icon_name} via {used} @ {icon_size}px")

    # ═══ العنوان (auto-fit) ═══
    title = sc.get("title_ar", "")
    if title:
        title_fp = ID.font_path("title", d)
        max_w = W - 2 * margin
        size = 92 if kind == "intro" else 82
        while size >= 56:
            pen = C.ArabicPen(str(title_fp), size, bold=True, stroke=1)
            ti = pen.line_img(title, paper)
            if ti.width <= max_w:
                break
            size -= 4
        tx = W - margin - ti.width
        ty = y_cursor
        t_path = base.parent / f"{base.name}_title.png"
        ti.save(str(t_path), "PNG", optimize=True)
        layers.append(SG.Layer(t_path, tx, ty, t_in=0.2, entry="right"))

        # خط ذهبي
        rule_w = int(W * 0.40)
        rule = Image.new("RGBA", (rule_w, 2), gold)
        rx = W - margin - rule_w
        ry = ty + ti.height + 20
        r_path = base.parent / f"{base.name}_rule.png"
        rule.save(str(r_path), "PNG")
        layers.append(SG.Layer(r_path, rx, ry, t_in=0.5, entry="right"))
        y_cursor = ry + 40

    # ═══ subtitle ═══
    subtitle = sc.get("subtitle", "")
    if subtitle:
        body_fp = ID.font_path("body", d)
        pen = C.ArabicPen(str(body_fp), 52, stroke=0)
        si = pen.line_img(subtitle, turq)
        sx = W - margin - si.width
        s_path = base.parent / f"{base.name}_sub.png"
        si.save(str(s_path), "PNG", optimize=True)
        layers.append(SG.Layer(s_path, sx, y_cursor, t_in=0.7, entry="fade_in"))

    # ═══ اسم القناة (intro/outro) ═══
    if kind in ("intro", "outro"):
        wisdom_fp = ID.font_path("wisdom", d)
        pen = C.ArabicPen(str(wisdom_fp), 44, bold=True, stroke=1)
        wi = pen.line_img("أبو محمد المساوى", paper)
        alpha = wi.getchannel("A").point(lambda v: int(v * 0.7))
        wi.putalpha(alpha)
        wx = W - margin - wi.width
        wy = H - 260
        w_path = base.parent / f"{base.name}_ch.png"
        wi.save(str(w_path), "PNG", optimize=True)
        layers.append(SG.Layer(w_path, wx, wy, t_in=1.5, entry="fade_in"))

    # manifest
    manifest = {
        "scene_idx": idx, "kind": kind,
        "background": str(bg_path),
        "layers": [
            {"path": str(l.path), "x": l.x, "y": l.y,
             "t_in": l.t_in, "entry": l.entry}
            for l in layers
        ],
    }
    (base.parent / f"{base.name}_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # composite (للتوافق)
    composite = bg.copy()
    for l in layers:
        composite.alpha_composite(Image.open(str(l.path)).convert("RGBA"),
                                   (l.x, l.y))
    out_png = base.parent / f"{base.name}_card.png"
    composite.convert("RGB").save(str(out_png), "PNG", optimize=True)
    return out_png
