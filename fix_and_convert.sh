#!/data/data/com.termux/files/usr/bin/bash
set -e
cd ~/AI_CONTENT_FACTORY

echo "🎬 تحويل اللقطات الاحترافية إلى فيديوهات..."

convert_shot() {
    local input="$1"
    local output="$2"
    local duration="$3"
    
    if [ ! -f "$input" ]; then
        echo "  ⚠️  ملف غير موجود: $input"
        return 0
    fi
    
    echo "  معالجة: $(basename "$input") -> $(basename "$output")"
    
    ffmpeg -y -loop 1 -i "$input" \
        -c:v libx264 \
        -t "$duration" \
        -pix_fmt yuv420p \
        -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0004,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$((duration * 30)):s=1080x1920:fps=30,format=yuv420p" \
        "$output" 2>/dev/null
    
    echo "  ✅ تم: $(basename "$output")"
}

mkdir -p real_demos/videos

convert_shot real_demos/screenshots/01_termux_pro.png real_demos/videos/01_termux_pro.mp4 8
convert_shot real_demos/screenshots/02_ffmpeg_pro.png real_demos/videos/02_ffmpeg_pro.mp4 8
convert_shot real_demos/screenshots/03_python_pro.png real_demos/videos/03_python_pro.mp4 8
convert_shot real_demos/screenshots/04_reshaper_pro.png real_demos/videos/04_reshaper_pro.mp4 8
convert_shot real_demos/screenshots/05_edge_pro.png real_demos/videos/05_edge_pro.mp4 8
convert_shot real_demos/screenshots/06_outro_pro.png real_demos/videos/06_outro_pro.mp4 6

echo ""
echo "=========================================="
echo "✅ اكتمل التحويل"
echo "=========================================="
ls -lh real_demos/videos/*_pro.mp4

echo ""
echo "📂 نسخ اللقطات للمشاهدة..."
mkdir -p /sdcard/Pictures/PRO_SCREENSHOTS 2>/dev/null || mkdir -p ~/storage/downloads/PRO_SCREENSHOTS
cp real_demos/screenshots/*_pro.png /sdcard/Pictures/PRO_SCREENSHOTS/ 2>/dev/null || cp real_demos/screenshots/*_pro.png ~/storage/downloads/PRO_SCREENSHOTS/
echo "✅ اللقطات في: /sdcard/Pictures/PRO_SCREENSHOTS/"
