"""خلفيات الهوية العربية الجديدة."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageDraw, ImageFilter
from engine import identity as ID


def horizon_glow(W=1080, H=1920, d=None):
    """V5 — خط ضوء أفقي سينمائي (الخلفية المعتمدة)."""
    if d is None:
        d = ID.load_identity()
    ink = ID.palette_rgb("ink", d)
    turq = ID.palette_rgb("turquoise", d)

    bg = Image.new("RGBA", (W, H), ink)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)

    y_center = int(H * ID.get("background.horizon_y_ratio", 0.42, d))
    thickness = ID.get("background.horizon_thickness", 3, d)
    max_alpha = ID.get("background.horizon_alpha", 25, d)

    for offset in range(-80, 81, 4):
        alpha = max(0, max_alpha - abs(offset) // 4)
        if alpha > 0:
            gd.rectangle(
                [0, y_center + offset, W, y_center + offset + thickness],
                fill=(turq[0], turq[1], turq[2], alpha)
            )

    blur = ID.get("background.horizon_blur", 30, d)
    glow = glow.filter(ImageFilter.GaussianBlur(blur))
    bg.alpha_composite(glow)
    return bg
