#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$HOME/AI_CONTENT_FACTORY"
mkdir -p tmp real_demos/{screenshots,videos} output voice

echo "=========================================="
echo "🎬 إنتاج فيديو حقيقي بلقطات شاشة فعلية"
echo "=========================================="
echo ""

echo "المرحلة 1/4: التقاط اللقطات الحقيقية..."
bash tools_capture/capture_real.sh
echo ""

echo "المرحلة 2/4: توليد الصوت..."
if [ ! -f "voice/voice.wav" ] || [ ! -s "voice/voice.wav" ]; then
    echo "  توليد الصوت..."
    TEXT="هذه الأدوات الخمس صنعت هذا الفيديو من هاتفي. تيرمكس بيئة تطوير حقيقية على الهاتف بدون روت. إف إف إمبيج محرك الفيديو الذي يدمج ويحول ويصدر. بايثون وأرابيك ريشيبر يعالجان النص العربي ويوصلان الحروف. إيدج تي تي إس يولد صوتا عربيا طبيعيا. كل هذا يعمل من هاتف واحد."
    
    if command -v edge-tts >/dev/null 2>&1; then
        edge-tts --voice ar-EG-ShakirNeural --text "$TEXT" --write-media "$TMP/voice_real.mp3" 2>/dev/null || true
    fi
    
    if [ -f "$HOME/AI_CONTENT_FACTORY/tmp/voice_real.mp3" ] && [ -s "$HOME/AI_CONTENT_FACTORY/tmp/voice_real.mp3" ]; then
        ffmpeg -y -i "$HOME/AI_CONTENT_FACTORY/tmp/voice_real.mp3" -ar 48000 -ac 1 voice/voice.wav 2>/dev/null
        echo "  ✅ الصوت جاهز (Edge-TTS)"
    elif command -v espeak >/dev/null 2>&1; then
        espeak -v ar -s 150 -w voice/voice.wav "$TEXT" 2>/dev/null || true
        echo "  ✅ الصوت جاهز (espeak)"
    else
        echo "  ⚠️  لا يوجد محرك صوت، الفيديو بدون صوت"
        touch voice/voice.wav
    fi
else
    echo "  ✅ الصوت موجود مسبقاً"
fi
echo ""

echo "المرحلة 3/4: تحويل اللقطات إلى فيديوهات..."
bash tools_capture/convert_to_video.sh
echo ""

echo "المرحلة 4/4: دمج كل شيء..."
bash tools_capture/merge_real_video.sh
echo ""

echo "=========================================="
echo "✅ اكتمل إنتاج الفيديو الحقيقي!"
echo "=========================================="
echo ""
echo "المخرجات:"
echo "  📁 اللقطات: real_demos/screenshots/"
echo "  🎬 المقاطع: real_demos/videos/"
echo "  📹 الفيديو النهائي: output/real_video_final.mp4"
echo ""
echo "لمشاهدة الفيديو:"
echo "  cp output/real_video_final.mp4 /sdcard/Movies/"
echo ""
