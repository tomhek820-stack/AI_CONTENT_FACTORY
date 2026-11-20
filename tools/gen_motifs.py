"""يولّد موتيفات معقلية: زاوية + شريط."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw
from engine import identity as ID

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "motifs"
OUT.mkdir(parents=True, exist_ok=True)

d = ID.load_identity()
turq = ID.palette_rgb("turquoise", d)

PATTERN = [
    [0, 1, 1, 1, 0],
    [0, 1, 0, 1, 0],
    [0, 1, 1, 1, 0],
    [0, 0, 0, 1, 0],
    [0, 0, 0, 1, 1],
]

def make_corner(size=48):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    cell = size // 5
    gap = 1
    for ry, row in enumerate(PATTERN):
        for rx, v in enumerate(row):
            if v:
                x = rx * cell
                y = ry * cell
                dd.rectangle([x, y, x + cell - gap, y + cell - gap], fill=turq)
    return im

def make_wipe(w=1080, h=120):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(im)
    cell = 12
    color = (turq[0], turq[1], turq[2], 180)
    n = w // (cell + 2)
    for i in range(n):
        x = i * (cell + 2)
        y = (h - cell) // 2
        dd.rectangle([x, y, x + cell - 1, y + cell - 1], fill=color)
    return im

corner = make_corner()
corner.save(str(OUT / "corner_kufic.png"), "PNG")
print(f"✅ {OUT / 'corner_kufic.png'} ({corner.size})")

wipe = make_wipe()
wipe.save(str(OUT / "wipe_kufic.png"), "PNG")
print(f"✅ {OUT / 'wipe_kufic.png'} ({wipe.size})")
