import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine.intro_v3 import render_intro_v3

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "intro_v3.png"
OUT.parent.mkdir(parents=True, exist_ok=True)

script_path = ROOT / "scripts" / "video_016.txt"
title = "هاتفك بطيء؟ المشكلة ليست فيه"
subtitle = "الحلقة السادسة: تسريع الهاتف"

if script_path.exists():
    for line in script_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("SCENE|"):
            parts = line.split("|")
            if len(parts) >= 4 and parts[2] == "intro":
                title = parts[3].strip()
                if len(parts) >= 5 and parts[4].strip():
                    subtitle = parts[4].strip()
                break

print(f"Title: {title}")
print(f"Subtitle: {subtitle}")

im = render_intro_v3(title, subtitle)
im.convert("RGB").save(str(OUT), "PNG", optimize=True)
print(f"✅ {OUT} ({OUT.stat().st_size // 1024} KB, {im.size})")
