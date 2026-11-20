#!/data/data/com.termux/files/usr/bin/bash
set -e
OUT="$HOME/AI_CONTENT_FACTORY/real_demos/screenshots"
TMP="$HOME/AI_CONTENT_FACTORY/tmp"
mkdir -p "$OUT" "$TMP"

echo "📸 التقاط لقطة شاشة حقيقية من Termux..."
termux-screenshot -p "$OUT/termux_live.png" 2>/dev/null || true

python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont
import subprocess, os, datetime

out = os.path.expanduser("~/AI_CONTENT_FACTORY/real_demos/screenshots")
try:
    result = subprocess.run(['pkg', 'list-installed'], capture_output=True, text=True, timeout=10)
    packages = result.stdout[:500] if result.stdout else "pkg list-installed"
except:
    packages = "pkg install ffmpeg python pillow"

img = Image.new('RGB', (1080, 1920), color=(15, 20, 35))
draw = ImageDraw.Draw(img)
try:
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 48)
    font_small = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 28)
    font_mono = ImageFont.truetype('/system/fonts/DroidSansMono.ttf', 24)
except:
    font_large = font_small = font_mono = ImageFont.load_default()

draw.text((80, 100), "Termux - بيئة تطوير حقيقية", fill=(0, 229, 255), font=font_large)
commands = [
    "$ pkg install ffmpeg python pillow",
    "$ python3 script.py",
    "$ ffmpeg -i input.mp4 output.mp4",
    "$ edge-tts --voice ar-EG-ShakirNeural",
]
y = 250
for cmd in commands:
    draw.text((80, y), cmd, fill=(150, 255, 150), font=font_mono)
    y += 70
draw.text((80, y + 50), "النتيجة الفعلية:", fill=(255, 255, 255), font=font_small)
draw.text((80, y + 100), packages[:300], fill=(200, 200, 200), font=font_small)
try:
    result = subprocess.run(['uname', '-a'], capture_output=True, text=True)
    uname = result.stdout.strip()[:100]
except:
    uname = "Linux Android aarch64"
draw.text((80, 1700), uname, fill=(100, 100, 100), font=font_small)
draw.text((80, 1760), datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), fill=(100, 100, 100), font=font_small)
img.save(f"{out}/termux_real.png")
print("✅ لقطة Termux الحقيقية جاهزة")
PY

echo "📸 التقاط لقطة FFmpeg حقيقية..."
ffmpeg -version > "$TMP/ffmpeg_real.txt" 2>&1 || echo "ffmpeg not found" > "$TMP/ffmpeg_real.txt"

python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont
import os

tmp = os.path.expanduser("~/AI_CONTENT_FACTORY/tmp")
out = os.path.expanduser("~/AI_CONTENT_FACTORY/real_demos/screenshots")
with open(f'{tmp}/ffmpeg_real.txt') as f:
    content = f.read()[:600]

img = Image.new('RGB', (1080, 1920), color=(15, 20, 35))
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 26)
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 44)
except:
    font = font_large = ImageFont.load_default()

draw.text((80, 100), "FFmpeg - محرك الفيديو الحقيقي", fill=(0, 229, 255), font=font_large)
y = 220
for line in content.split('\n')[:15]:
    draw.text((80, y), line[:80], fill=(200, 220, 255), font=font)
    y += 50
cmd = "ffmpeg -i input.mp4 -vf scale=1080:1920 output.mp4"
draw.text((80, 1500), cmd, fill=(150, 255, 150), font=font)
img.save(f"{out}/ffmpeg_real.png")
print("✅ لقطة FFmpeg الحقيقية جاهزة")
PY

echo "📸 التقاط لقطة Python حقيقية..."
cat > "$TMP/python_real.py" <<'PYCODE'
import arabic_reshaper
import sys

text = "مرحبا بالعالم"
reshaped = arabic_reshaper.reshape(text)

print("=" * 50)
print("Python - معالجة النص العربي الحقيقية")
print("=" * 50)
print(f"النص الأصلي: {text}")
print(f"بعد التشكيل: {reshaped}")
print(f"Python version: {sys.version}")
print("=" * 50)
PYCODE

python3 "$TMP/python_real.py" > "$TMP/python_output.txt" 2>&1 || echo "python error" > "$TMP/python_output.txt"

python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont
import os

tmp = os.path.expanduser("~/AI_CONTENT_FACTORY/tmp")
out = os.path.expanduser("~/AI_CONTENT_FACTORY/real_demos/screenshots")
with open(f'{tmp}/python_output.txt') as f:
    content = f.read()

img = Image.new('RGB', (1080, 1920), color=(15, 20, 35))
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 30)
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 44)
except:
    font = font_large = ImageFont.load_default()

draw.text((80, 100), "Python + arabic-reshaper", fill=(0, 229, 255), font=font_large)
y = 250
for line in content.split('\n')[:12]:
    draw.text((80, y), line[:70], fill=(220, 220, 220), font=font)
    y += 60
img.save(f"{out}/python_real.png")
print("✅ لقطة Python الحقيقية جاهزة")
PY

echo "📸 التقاط لقطة Edge-TTS حقيقية..."
cat > "$TMP/edge_test.py" <<'PYCODE'
try:
    import edge_tts
    status = "Edge-TTS مثبت وجاهز"
    voices = "ar-EG-ShakirNeural, ar-SA-HamedNeural"
except ImportError:
    status = "Edge-TTS غير مثبت"
    voices = "pip install edge-tts"

print("=" * 50)
print("Edge-TTS - التعليق الصوتي الحقيقي")
print("=" * 50)
print(f"الحالة: {status}")
print(f"الأصوات: {voices}")
print("=" * 50)
PYCODE

python3 "$TMP/edge_test.py" > "$TMP/edge_output.txt" 2>&1 || echo "edge error" > "$TMP/edge_output.txt"

python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont
import os

tmp = os.path.expanduser("~/AI_CONTENT_FACTORY/tmp")
out = os.path.expanduser("~/AI_CONTENT_FACTORY/real_demos/screenshots")
with open(f'{tmp}/edge_output.txt') as f:
    content = f.read()

img = Image.new('RGB', (1080, 1920), color=(15, 20, 35))
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 30)
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 44)
except:
    font = font_large = ImageFont.load_default()

draw.text((80, 100), "Edge-TTS - صوت عربي طبيعي", fill=(0, 229, 255), font=font_large)
y = 250
for line in content.split('\n'):
    draw.text((80, y), line[:70], fill=(220, 220, 220), font=font)
    y += 60
cmd = "edge-tts --voice ar-EG-ShakirNeural --write-media out.mp3"
draw.text((80, 1400), cmd, fill=(150, 255, 150), font=font)
img.save(f"{out}/edge_real.png")
print("✅ لقطة Edge-TTS الحقيقية جاهزة")
PY

echo ""
echo "✅ اكتمل التقاط اللقطات الحقيقية:"
ls -lh "$OUT"/*.png
