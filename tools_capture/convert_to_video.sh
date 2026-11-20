#!/data/data/com.termux/files/usr/bin/bash
set -e
IN="$HOME/AI_CONTENT_FACTORY/real_demos/screenshots"
OUT="$HOME/AI_CONTENT_FACTORY/real_demos/videos"
TMP="$HOME/AI_CONTENT_FACTORY/tmp"
mkdir -p "$OUT" "$TMP"

echo "🎬 تحويل اللقطات إلى فيديوهات حقيقية..."

convert_shot() {
    local input="$1"
    local output="$2"
    local duration="$3"
    local zoom_speed="$4"
    
    if [ ! -f "$input" ]; then
        echo "  ⚠️  ملف غير موجود: $input"
        return 0
    fi
    
    echo "  معالجة: $(basename "$input")"
    
    ffmpeg -y -loop 1 -i "$input" \
        -c:v libx264 \
        -t "$duration" \
        -pix_fmt yuv420p \
        -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+$zoom_speed,1.12)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=$((duration * 30)):s=1080x1920:fps=30,format=yuv420p" \
        "$output" 2>/dev/null
    
    echo "  ✅ تم: $(basename "$output")"
}

convert_shot "$IN/termux_real.png" "$OUT/01_termux.mp4" 8 0.0008
convert_shot "$IN/ffmpeg_real.png" "$OUT/02_ffmpeg.mp4" 8 0.0008
convert_shot "$IN/python_real.png" "$OUT/03_python.mp4" 8 0.0008
convert_shot "$IN/edge_real.png" "$OUT/04_edge.mp4" 8 0.0008

if [ -f "$IN/termux_live.png" ]; then
    convert_shot "$IN/termux_live.png" "$OUT/00_intro.mp4" 5 0.001
fi

echo ""
echo "✅ اكتمل تحويل اللقطات إلى فيديوهات:"
ls -lh "$OUT"/*.mp4 2>/dev/null || echo "لا توجد فيديوهات بعد"
