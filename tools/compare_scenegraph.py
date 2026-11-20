"""يقارن آخر إطار scene_graph مع intro_v3.png المخبوز."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parent.parent
BAKED = ROOT / "spike_tmp" / "intro_v3.png"
SG_LAST = ROOT / "spike_tmp" / "intro_scenegraph_last.png"
SIDE = ROOT / "spike_tmp" / "scenegraph_vs_baked.png"

a = Image.open(str(BAKED)).convert("RGB")
b = Image.open(str(SG_LAST)).convert("RGB")
if a.size != b.size:
    b = b.resize(a.size)

diff = ImageChops.difference(a, b)
stat = ImageStat.Stat(diff)
pct = sum(stat.mean[:3]) / 3.0 / 255.0 * 100.0

# صورة مقارنة جنباً إلى جنب
canvas = Image.new("RGB", (a.width * 2 + 40, a.height + 20), (20, 20, 30))
canvas.paste(a, (10, 10))
canvas.paste(b, (a.width + 30, 10))
canvas.save(str(SIDE), "PNG", optimize=True)

print(f"📊 Diff (last frame vs baked): {pct:.3f}%")
if pct <= 3.0:
    print(f"✅ PASS (≤ 3%)")
elif pct <= 5.0:
    print(f"⚠️  مقبول (3-5%)")
else:
    print(f"❌ FAIL (>{5.0}%)")
print(f"🖼️ {SIDE}")
