#!/data/data/com.termux/files/usr/bin/bash
set -e
VIDEOS="$HOME/AI_CONTENT_FACTORY/real_demos/videos"
OUT="$HOME/AI_CONTENT_FACTORY/output"
AUDIO="$HOME/AI_CONTENT_FACTORY/voice/voice.wav"
TMP="$HOME/AI_CONTENT_FACTORY/tmp"
mkdir -p "$OUT" "$TMP"

echo "🎞️ دمج الفيديوهات الحقيقية..."

# إنشاء قائمة الدمج فقط للملفات الموجودة
> "$TMP/real_concat.txt"
for v in "$VIDEOS"/0*.mp4; do
    [ -f "$v" ] && echo "file '$v'" >> "$TMP/real_concat.txt"
done

if [ ! -s "$TMP/real_concat.txt" ]; then
    echo "❌ لا توجد مقاطع فيديو للدمج"
    exit 1
fi

echo "  دمج المقاطع..."
ffmpeg -y -f concat -safe 0 -i "$TMP/real_concat.txt" \
    -c:v libx264 \
    -preset fast \
    -crf 23 \
    -pix_fmt yuv420p \
    "$TMP/real_merged.mp4" 2>/dev/null

echo "  ✅ تم دمج المقاطع"

if [ -f "$AUDIO" ] && [ -s "$AUDIO" ]; then
    echo "  إضافة الصوت..."
    ffmpeg -y -i "$TMP/real_merged.mp4" -i "$AUDIO" \
        -c:v copy \
        -c:a aac \
        -b:a 128k \
        -map 0:v:0 -map 1:a:0 \
        -shortest \
        "$OUT/real_video_final.mp4" 2>/dev/null
    echo "  ✅ تم إضافة الصوت"
else
    echo "  ⚠️  لا يوجد ملف صوت، الفيديو بدون صوت"
    cp "$TMP/real_merged.mp4" "$OUT/real_video_final.mp4"
fi

echo ""
echo "✅ الفيديو الحقيقي النهائي جاهز:"
ls -lh "$OUT/real_video_final.mp4"

echo ""
echo "📊 فحص الفيديو:"
ffprobe -v error -show_entries format=duration,size -show_entries stream=codec_name,width,height,r_frame_rate -of default=noprint_wrappers=1 "$OUT/real_video_final.mp4" 2>/dev/null || echo "فحص غير متاح"
