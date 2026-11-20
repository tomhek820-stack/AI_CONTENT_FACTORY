# AI TECH LAB — مصنع الفيديو (Termux بدون Root)

## التشغيل
    bash generate.sh --preview     # اختبار سريع
    bash generate.sh --export      # الإنتاج الكامل + نسخ للهاتف

## المخرجات
output/final_video.mp4 · thumbnail.jpg · thumbnail_yt.jpg · publish_description.txt
scripts/subtitles.srt · voice/voice.wav · logs/

## محركات الصوت
piper (أفضل offline، يحتاج proot Debian على Termux) → edge (طبيعي، متصل، مجاني بلا مفتاح)
→ espeak (offline مضمون لكن آلي) → manual (تسجيلك: voice/manual/chatgpt_00.wav ...)

تحسين الصوت:  pip install edge-tts  ثم  bash generate.sh --force-voice

## ملاحظات
- الترجمة تُرسم PNG مشكولة RTL لأن FFmpeg drawtext لا يصل الحروف العربية.
- الموسيقى والأيقونات أصلية مولّدة (CC0)؛ لا شعارات رسمية.
- كل الأدوات لها خطة مجانية محدودة، وبعض الميزات مدفوعة.
- الفحص: python -m engine.selftest
