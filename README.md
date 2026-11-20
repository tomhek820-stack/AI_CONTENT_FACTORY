# AI Content Factory

محرك إنتاج فيديوهات عربية قصيرة (Reels/TikTok/Shorts) بهوية بصرية عربية أصيلة.

## الميزات

- **الهوية:** Amiri + IBM Plex Arabic + palette (حبر/فيروز/ورق/ذهب)
- **الأيقونات:** Iconify (200,000+ أيقونة) + كاش محلي
- **الترجمة:** ASS مزامن (Font 140)
- **الحركة:** Scene Graph + RTL
- **الصوت:** LUFS -16 + Ducking
- **الحماية:** Golden Master + Regression gate

## التثبيت

```bash
pkg install -y python ffmpeg librsvg git
pip install -r requirements.txt
```

## الاستخدام

```bash
bash produce_studio.sh 016 --fast
python3 qc_regression.py --video output/016/final_video.mp4 --golden golden/016 --threshold 2
```

## البنية

```
engine/    المحرك الأساسي
voice/     الصوت (edge-tts)
tools/     الأدوات
scripts/   السيناريوهات
config/    الإعدادات
assets/    الخطوط + المعقلي
```

## المتطلبات

- Python 3.11+
- FFmpeg 6.0+
- Pillow 10.0+
- librsvg (SVG -> PNG)

## الترخيص

MIT — انظر [LICENSE](LICENSE).

---

صُنع بـ ❤️ في اليمن
