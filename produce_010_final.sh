#!/data/data/com.termux/files/usr/bin/bash
set -e
cd ~/AI_CONTENT_FACTORY

echo "=========================================="
echo "🎬 إنتاج الفيديو 010 النهائي"
echo "=========================================="

# تحديث خريطة اللقطات في المحرك الهجين
python3 - <<'PY'
import pathlib
p = pathlib.Path("engine/hybrid_scenes.py")
if p.exists():
    s = p.read_text(encoding="utf-8")
    old_map = '''    real_map = {
        "real1": "01_termux.mp4",
        "real2": "03_python.mp4",
        "real3": "02_ffmpeg.mp4",
    }'''
    new_map = '''    real_map = {
        "real1": "01_termux_pro.mp4",
        "real2": "03_python_pro.mp4",
        "real3": "02_ffmpeg_pro.mp4",
    }'''
    if old_map in s:
        s = s.replace(old_map, new_map, 1)
        p.write_text(s, encoding="utf-8")
        print("✅ hybrid_scenes محدث")
    elif new_map in s:
        print("✅ hybrid_scenes محدث مسبقاً")
    else:
        print("⚠️  لم أجد الخريطة القديمة")
else:
    print("⚠️  engine/hybrid_scenes.py غير موجود")
PY

# توليد الصوت
echo ""
echo "الخطوة 1/4: توليد الصوت..."
export AILAB_SCRIPT="$PWD/scripts/video_010.txt"
if [ ! -f voice/voice.wav ] || [ ! -s voice/voice.wav ]; then
    python voice/generate_voice.py --engine=edge --force 2>/dev/null || python voice/generate_voice.py --force
fi

# الكاريوكي
echo ""
echo "الخطوة 2/4: الكاريوكي..."
python -m engine.karaoke_v2 2>/dev/null || python -m engine.karaoke

# المشاهد الهجينة
echo ""
echo "الخطوة 3/4: المشاهد الهجينة..."
python -m engine.hybrid_scenes

# الرندر
echo ""
echo "الخطوة 4/4: الرندر..."
python -m engine.hybrid_render

# نسخ النتيجة
mkdir -p /sdcard/Movies/ABU_MOHAMMED 2>/dev/null || true
cp output/hybrid_final.mp4 /sdcard/Movies/ABU_MOHAMMED/ABU_MOHAMMED_010_pro.mp4 2>/dev/null || true

echo ""
echo "=========================================="
echo "✅ اكتمل إنتاج الفيديو 010"
echo "=========================================="
echo ""
echo "📹 الفيديو: output/hybrid_final.mp4"
echo "📱 على الهاتف: /sdcard/Movies/ABU_MOHAMMED/ABU_MOHAMMED_010_pro.mp4"
echo ""

# فحص سريع
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate -of default=noprint_wrappers=1 output/hybrid_final.mp4 2>/dev/null || echo "فحص غير متاح"
