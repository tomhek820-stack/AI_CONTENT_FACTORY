#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/AI_CONTENT_FACTORY"
mkdir -p tmp real_demos/{screenshots,videos} output voice

echo "=========================================="
echo "🎬 إنتاج فيديو حقيقي 50-60 ثانية"
echo "=========================================="
echo ""

TMP="$HOME/AI_CONTENT_FACTORY/tmp"
OUT="$HOME/AI_CONTENT_FACTORY/real_demos/screenshots"
VID_OUT="$HOME/AI_CONTENT_FACTORY/real_demos/videos"

# ============================================
# المرحلة 1: التقاط 7 لقطات حقيقية
# ============================================
echo "المرحلة 1/5: التقاط اللقطات الحقيقية (7 لقطات)..."

# لقطة 1: المقدمة
python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont
import datetime

out = "/data/data/com.termux/files/home/AI_CONTENT_FACTORY/real_demos/screenshots"
img = Image.new('RGB', (1080, 1920), color=(5, 8, 15))
draw = ImageDraw.Draw(img)

try:
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 64)
    font_small = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 36)
except:
    font_large = font_small = ImageFont.load_default()

draw.text((540, 400), "أبو محمد المساوى", fill=(0, 229, 255), font=font_large, anchor="mm")
draw.text((540, 550), "هذه الأدوات الخمس", fill=(255, 255, 255), font=font_large, anchor="mm")
draw.text((540, 650), "صنعت هذا الفيديو", fill=(255, 255, 255), font=font_large, anchor="mm")
draw.text((540, 800), "من هاتفي فقط", fill=(0, 229, 255), font=font_small, anchor="mm")
draw.text((540, 1600), datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), fill=(100, 100, 100), font=font_small, anchor="mm")

img.save(f"{out}/00_intro.png")
print("✅ لقطة المقدمة جاهزة")
PY

# لقطة 2: Termux
python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont
import subprocess, os

out = "/data/data/com.termux/files/home/AI_CONTENT_FACTORY/real_demos/screenshots"
tmp = "/data/data/com.termux/files/home/AI_CONTENT_FACTORY/tmp"

try:
    result = subprocess.run(['pkg', 'list-installed'], capture_output=True, text=True, timeout=10)
    packages = result.stdout[:800] if result.stdout else "pkg install ffmpeg python"
except:
    packages = "pkg install ffmpeg python pillow"

img = Image.new('RGB', (1080, 1920), color=(15, 20, 35))
draw = ImageDraw.Draw(img)
try:
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 52)
    font_small = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 28)
    font_mono = ImageFont.truetype('/system/fonts/DroidSansMono.ttf', 22)
except:
    font_large = font_small = font_mono = ImageFont.load_default()

draw.rectangle([0, 0, 1080, 120], fill=(0, 100, 200))
draw.text((540, 60), "Termux", fill=(255, 255, 255), font=font_large, anchor="mm")

commands = [
    "$ pkg update && pkg upgrade",
    "$ pkg install ffmpeg python pillow",
    "$ pip install arabic-reshaper edge-tts",
    "$ python3 script.py",
]
y = 200
for cmd in commands:
    draw.text((80, y), cmd, fill=(150, 255, 150), font=font_mono)
    y += 60

draw.text((80, y + 30), "الحزم المثبتة:", fill=(255, 255, 255), font=font_small)
y += 80
for line in packages.split('\n')[:12]:
    draw.text((80, y), line[:75], fill=(200, 200, 200), font=font_small)
    y += 45

img.save(f"{out}/01_termux.png")
print("✅ لقطة Termux جاهزة")
PY

# لقطة 3: FFmpeg
python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont
import subprocess

out = "/data/data/com.termux/files/home/AI_CONTENT_FACTORY/real_demos/screenshots"
tmp = "/data/data/com.termux/files/home/AI_CONTENT_FACTORY/tmp"

try:
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
    content = result.stdout[:600] if result.stdout else "FFmpeg version 6.0"
except:
    content = "FFmpeg version 6.0"

img = Image.new('RGB', (1080, 1920), color=(15, 20, 35))
draw = ImageDraw.Draw(img)
try:
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 52)
    font_small = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 28)
except:
    font_large = font_small = ImageFont.load_default()

draw.rectangle([0, 0, 1080, 120], fill=(0, 150, 100))
draw.text((540, 60), "FFmpeg", fill=(255, 255, 255), font=font_large, anchor="mm")

y = 200
for line in content.split('\n')[:12]:
    draw.text((80, y), line[:80], fill=(200, 220, 255), font=font_small)
    y += 50

commands = [
    "$ ffmpeg -i input.mp4 -vf scale=1080:1920 output.mp4",
    "$ ffmpeg -i audio.mp3 -i video.mp4 final.mp4",
    "$ ffmpeg -i clip1.mp4 -i clip2.mp4 -filter_complex xfade merged.mp4",
]
y += 50
draw.text((80, y), "أوامر حقيقية:", fill=(255, 255, 255), font=font_small)
y += 60
for cmd in commands:
    draw.text((80, y), cmd, fill=(150, 255, 150), font=font_small)
    y += 50

img.save(f"{out}/02_ffmpeg.png")
print("✅ لقطة FFmpeg جاهزة")
PY

# لقطة 4: Python
python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont
import sys

out = "/data/data/com.termux/files/home/AI_CONTENT_FACTORY/real_demos/screenshots"

img = Image.new('RGB', (1080, 1920), color=(15, 20, 35))
draw = ImageDraw.Draw(img)
try:
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 52)
    font_small = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 30)
except:
    font_large = font_small = ImageFont.load_default()

draw.rectangle([0, 0, 1080, 120], fill=(100, 100, 0))
draw.text((540, 60), "Python", fill=(255, 255, 255), font=font_large, anchor="mm")

code = [
    "import arabic_reshaper",
    "",
    "text = 'مرحبا بالعالم'",
    "reshaped = arabic_reshaper.reshape(text)",
    "",
    "print(f'Before: {text}')",
    "print(f'After:  {reshaped}')",
    f"# Python {sys.version.split()[0]}",
]

y = 200
draw.text((80, y), "الكود:", fill=(255, 255, 255), font=font_small)
y += 60
for line in code:
    draw.text((80, y), line, fill=(150, 255, 150), font=font_small)
    y += 50

y += 30
draw.text((80, y), "النتيجة:", fill=(255, 255, 255), font=font_small)
y += 60
draw.text((80, y), "Before: مرحبا بالعالم", fill=(200, 200, 200), font=font_small)
y += 50
draw.text((80, y), "After: ﻣﺮﺣﺒﺎ ﺑﺎﻟﻌﺎﻟﻢ", fill=(200, 200, 200), font=font_small)

img.save(f"{out}/03_python.png")
print("✅ لقطة Python جاهزة")
PY

# لقطة 5: arabic-reshaper
python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper

out = "/data/data/com.termux/files/home/AI_CONTENT_FACTORY/real_demos/screenshots"

img = Image.new('RGB', (1080, 1920), color=(15, 20, 35))
draw = ImageDraw.Draw(img)
try:
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 52)
    font_small = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 32)
except:
    font_large = font_small = ImageFont.load_default()

draw.rectangle([0, 0, 1080, 120], fill=(150, 50, 150))
draw.text((540, 60), "arabic-reshaper", fill=(255, 255, 255), font=font_large, anchor="mm")

examples = [
    ("قبل التشكيل", "مرحبا بالعالم"),
    ("بعد التشكيل", arabic_reshaper.reshape("مرحبا بالعالم")),
    ("قبل", "هذه الأدوات الخمس"),
    ("بعد", arabic_reshaper.reshape("هذه الأدوات الخمس")),
]

y = 250
for label, text in examples:
    draw.text((80, y), f"{label}:", fill=(0, 229, 255), font=font_small)
    y += 50
    draw.text((80, y), text, fill=(255, 255, 255), font=font_small)
    y += 80

img.save(f"{out}/04_reshaper.png")
print("✅ لقطة arabic-reshaper جاهزة")
PY

# لقطة 6: Edge-TTS
python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont

out = "/data/data/com.termux/files/home/AI_CONTENT_FACTORY/real_demos/screenshots"

img = Image.new('RGB', (1080, 1920), color=(15, 20, 35))
draw = ImageDraw.Draw(img)
try:
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 52)
    font_small = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 30)
except:
    font_large = font_small = ImageFont.load_default()

draw.rectangle([0, 0, 1080, 120], fill=(200, 100, 0))
draw.text((540, 60), "Edge-TTS", fill=(255, 255, 255), font=font_large, anchor="mm")

commands = [
    "$ edge-tts --list-voices",
    "$ edge-tts --voice ar-EG-ShakirNeural \\",
    "    --text 'مرحبا بالعالم' \\",
    "    --write-media output.mp3",
]

y = 200
draw.text((80, y), "الأوامر:", fill=(255, 255, 255), font=font_small)
y += 60
for cmd in commands:
    draw.text((80, y), cmd, fill=(150, 255, 150), font=font_small)
    y += 50

y += 30
draw.text((80, y), "الأصوات العربية:", fill=(255, 255, 255), font=font_small)
y += 60
voices = ["ar-EG-ShakirNeural", "ar-SA-HamedNeural", "ar-EG-SalmaNeural"]
for v in voices:
    draw.text((80, y), f"• {v}", fill=(200, 200, 200), font=font_small)
    y += 50

img.save(f"{out}/05_edge.png")
print("✅ لقطة Edge-TTS جاهزة")
PY

# لقطة 7: الخاتمة
python3 <<'PY'
from PIL import Image, ImageDraw, ImageFont
import datetime

out = "/data/data/com.termux/files/home/AI_CONTENT_FACTORY/real_demos/screenshots"
img = Image.new('RGB', (1080, 1920), color=(5, 8, 15))
draw = ImageDraw.Draw(img)

try:
    font_large = ImageFont.truetype('/system/fonts/NotoSansArabic-Bold.ttf', 56)
    font_small = ImageFont.truetype('/system/fonts/NotoSansArabic-Regular.ttf', 36)
except:
    font_large = font_small = ImageFont.load_default()

draw.text((540, 400), "كل هذا يعمل", fill=(255, 255, 255), font=font_large, anchor="mm")
draw.text((540, 520), "من هاتف واحد", fill=(0, 229, 255), font=font_large, anchor="mm")
draw.text((540, 700), "احفظ الفيديو", fill=(255, 255, 255), font=font_small, anchor="mm")
draw.text((540, 800), "واكتب أي أداة نشرحها", fill=(255, 255, 255), font=font_small, anchor="mm")
draw.text((540, 950), "تابع أبو محمد المساوى", fill=(0, 229, 255), font=font_small, anchor="mm")
draw.text((540, 1600), datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), fill=(100, 100, 100), font=font_small, anchor="mm")

img.save(f"{out}/06_outro.png")
print("✅ لقطة الخاتمة جاهزة")
PY

echo ""
echo "✅ اكتمل التقاط اللقطات:"
ls -lh "$OUT"/*.png
echo ""

# ============================================
# المرحلة 2: تحويل اللقطات إلى فيديوهات (9 ثوانٍ لكل لقطة)
# ============================================
echo "المرحلة 2/5: تحويل اللقطات إلى فيديوهات (9 ثوانٍ لكل لقطة)..."

convert_shot() {
    local input="$1"
    local output="$2"
    local duration="$3"
    
    if [ ! -f "$input" ]; then
        echo "  ⚠️  ملف غير موجود: $input"
        return 0
    fi
    
    echo "  معالجة: $(basename "$input")"
    
    ffmpeg -y -loop 1 -i "$input" \
        -c:v libx264 \
        -t "$duration" \
        -pix_fmt yuv420p \
        -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0006,1.08)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$((duration * 30)):s=1080x1920:fps=30,format=yuv420p" \
        "$output" 2>/dev/null
    
    echo "  ✅ تم: $(basename "$output")"
}

convert_shot "$OUT/00_intro.png" "$VID_OUT/00_intro.mp4" 7
convert_shot "$OUT/01_termux.png" "$VID_OUT/01_termux.mp4" 9
convert_shot "$OUT/02_ffmpeg.png" "$VID_OUT/02_ffmpeg.mp4" 9
convert_shot "$OUT/03_python.png" "$VID_OUT/03_python.mp4" 9
convert_shot "$OUT/04_reshaper.png" "$VID_OUT/04_reshaper.mp4" 9
convert_shot "$OUT/05_edge.png" "$VID_OUT/05_edge.mp4" 9
convert_shot "$OUT/06_outro.png" "$VID_OUT/06_outro.mp4" 7

echo ""
echo "✅ اكتمل تحويل اللقطات:"
ls -lh "$VID_OUT"/*.mp4
echo ""

# ============================================
# المرحلة 3: توليد الصوت (50-60 ثانية)
# ============================================
echo "المرحلة 3/5: توليد الصوت..."

TEXT="هذه الأدوات الخمس صنعت هذا الفيديو من هاتفي. تيرمكس بيئة تطوير حقيقية على الهاتف بدون روت، منه أثبت كل شيء. إف إف إمبيج محرك الفيديو الذي يدمج المقاطع ويحولها ويصدرها بجودة عالية. بايثون مع أرابيك ريشيبر يعالجان النص العربي ويوصلان الحروف بشكل صحيح. إيدج تي تي إس يولد صوتا عربيا طبيعيا بدون حاجة لخدمات مدفوعة. كل هذا يعمل من هاتف واحد بدون حاسوب وبدون كاميرا. احفظ الفيديو واكتب في التعليقات أي أداة تريد أن نشرحها بالتفصيل. وتابع أبو محمد المساوى فالمستقبل بدأ بالفعل."

if [ ! -f "voice/voice.wav" ] || [ ! -s "voice/voice.wav" ]; then
    if command -v edge-tts >/dev/null 2>&1; then
        echo "  توليد الصوت بـ Edge-TTS..."
        edge-tts --voice ar-EG-ShakirNeural --text "$TEXT" --write-media "$TMP/voice_real.mp3" 2>/dev/null || true
        if [ -f "$TMP/voice_real.mp3" ] && [ -s "$TMP/voice_real.mp3" ]; then
            ffmpeg -y -i "$TMP/voice_real.mp3" -ar 48000 -ac 1 voice/voice.wav 2>/dev/null
            echo "  ✅ الصوت جاهز (Edge-TTS)"
        fi
    fi
    
    if [ ! -f "voice/voice.wav" ] || [ ! -s "voice/voice.wav" ]; then
        if command -v espeak >/dev/null 2>&1; then
            echo "  توليد الصوت بـ espeak..."
            espeak -v ar -s 160 -w voice/voice.wav "$TEXT" 2>/dev/null || true
            echo "  ✅ الصوت جاهز (espeak)"
        else
            echo "  ⚠️  لا يوجد محرك صوت"
            touch voice/voice.wav
        fi
    fi
else
    echo "  ✅ الصوت موجود مسبقاً"
fi

# قياس مدة الصوت
if [ -f "voice/voice.wav" ] && [ -s "voice/voice.wav" ]; then
    DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 voice/voice.wav 2>/dev/null | cut -d. -f1)
    echo "  مدة الصوت: ${DURATION} ثانية"
fi
echo ""

# ============================================
# المرحلة 4: دمج الفيديوهات
# ============================================
echo "المرحلة 4/5: دمج الفيديوهات..."

> "$TMP/real_concat.txt"
for v in "$VID_OUT"/0*.mp4; do
    [ -f "$v" ] && echo "file '$v'" >> "$TMP/real_concat.txt"
done

echo "  دمج المقاطع..."
ffmpeg -y -f concat -safe 0 -i "$TMP/real_concat.txt" \
    -c:v libx264 \
    -preset fast \
    -crf 23 \
    -pix_fmt yuv420p \
    "$TMP/real_merged.mp4" 2>/dev/null

echo "  ✅ تم دمج المقاطع"

# ============================================
# المرحلة 5: إضافة الصوت والفحص النهائي
# ============================================
echo "المرحلة 5/5: إضافة الصوت والفحص..."

if [ -f "voice/voice.wav" ] && [ -s "voice/voice.wav" ]; then
    ffmpeg -y -i "$TMP/real_merged.mp4" -i voice/voice.wav \
        -c:v copy \
        -c:a aac \
        -b:a 128k \
        -map 0:v:0 -map 1:a:0 \
        -shortest \
        output/real_video_final.mp4 2>/dev/null
    echo "  ✅ تم إضافة الصوت"
else
    cp "$TMP/real_merged.mp4" output/real_video_final.mp4
    echo "  ⚠️  الفيديو بدون صوت"
fi

echo ""
echo "=========================================="
echo "✅ اكتمل إنتاج الفيديو الحقيقي!"
echo "=========================================="
echo ""

# فحص الفيديو النهائي
echo "📊 فحص الفيديو النهائي:"
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate -of default=noprint_wrappers=1 output/real_video_final.mp4 2>/dev/null || echo "فحص غير متاح"

echo ""
echo "المخرجات:"
echo "  📁 اللقطات: real_demos/screenshots/ ($(ls real_demos/screenshots/*.png 2>/dev/null | wc -l) لقطات)"
echo "  🎬 المقاطع: real_demos/videos/ ($(ls real_demos/videos/*.mp4 2>/dev/null | wc -l) مقاطع)"
echo "  📹 الفيديو النهائي: output/real_video_final.mp4"
echo ""
echo "لمشاهدة الفيديو:"
echo "  cp output/real_video_final.mp4 /sdcard/Movies/real_video_$(date +%Y%m%d_%H%M%S).mp4"
echo ""
