"""يحدد بالضبط أي حرف يفشل في أي خط."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import ImageFont

ROOT = Path(__file__).resolve().parent.parent
TEST_TEXT = "بِسْمِ اللَّهِ — ٣ إعدادات خفية"
FONTS = ["ReemKufi-Bold.ttf", "Cairo-Bold.ttf", "Tajawal-Bold.ttf"]

def is_missing(fp, ch):
    font = ImageFont.truetype(str(fp), 64)
    try:
        bbox = font.getbbox(ch)
        return not bbox or bbox == (0, 0, 0, 0)
    except Exception:
        return True

for font_file in FONTS:
    fp = ROOT / "assets" / "fonts" / font_file
    if not fp.exists():
        continue
    print(f"\n=== {font_file} ===")
    missing = []
    for ch in set(TEST_TEXT):
        if ch.isspace():
            continue
        if is_missing(fp, ch):
            missing.append(f"'{ch}' (U+{ord(ch):04X})")
    if missing:
        print(f"  مفقود: {', '.join(missing)}")
    else:
        print("  ✅ كل الأحرف موجودة")
