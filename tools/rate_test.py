"""يقيس TOTAL_DURATION لسيناريو 016 عند rates مختلفة.
   يستخدم edge-tts مباشرة (بدون إعادة بناء كامل)."""
import sys, subprocess, json, asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "rate_test"
OUT.mkdir(parents=True, exist_ok=True)

# نص 016 (5 سطور)
LINES = [
    "هَاتِفُكَ بَطِيءٌ؟ الْمُشْكِلَةُ لَيْسَتْ فِي الْجِهَازِ، بَلْ فِي هَذِهِ الْإِعْدَادَاتِ الثَّلَاثَةِ الْخَفِيَّةِ.",
    "أَوَّلًا: رُسُومُ الِانْتِقَالِ. اِذْهَبْ إِلَى خِيَارَاتِ الْمُطَوِّرِ، وَأَوْقِفْهَا أَوْ خَفِّفْهَا لِتَسْرِيعِ الِاسْتِجَابَةِ فَوْرًا.",
    "ثَانِيًا: تَحْدِيثُ التَّطْبِيقَاتِ فِي الْخَلْفِيَّةِ. أَغْلِقْ هَذَا الْخِيَارَ لِلتَّطْبِيقَاتِ الَّتِي لَا تَسْتَخْدِمُهَا يَوْمِيًّا.",
    "ثَالِثًا: مَسَاحَةُ التَّخْزِينِ الْمُمْتَلِئَةُ. اِتْرُكْ عِشْرِينَ بِالْمِئَةِ فَارِغَةً عَلَى الْأَقَلِّ، لِيَعْمَلَ النِّظَامُ بِسَلَاسَةٍ.",
    "جَرِّبْ هَذِهِ الْخُطُوَاتِ الْيَوْمَ، وَلَاحِظِ الْفَرْقَ بِنَفْسِكَ. اِحْفَظِ الْفِيدْيُو، وَتَابِعْ أَبُو مُحَمَّدْ الْمَساوَا.",
]

VOICE = "ar-EG-ShakirNeural"
RATES = [0.795, 0.85, 0.88, 0.92, 1.00]

async def synth_one(text, rate, out_path):
    import edge_tts
    communicate = edge_tts.Communicate(
        text=text, voice=VOICE,
        rate=f"{int((rate - 1.0) * 100)}%"
    )
    await communicate.save(str(out_path))

def probe_duration(path):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True
    )
    return float(r.stdout.strip())

async def main():
    results = []
    for rate in RATES:
        print(f"\n=== rate = {rate} ===")
        total = 0.0
        lines = []
        for i, text in enumerate(LINES):
            mp3 = OUT / f"line_{i}_{rate}.mp3"
            wav = OUT / f"line_{i}_{rate}.wav"
            try:
                await synth_one(text, rate, mp3)
                subprocess.run(
                    ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                     "-i", str(mp3), "-ar", "48000", "-ac", "1",
                     "-c:a", "pcm_s16le", str(wav)],
                    check=True
                )
                dur = probe_duration(wav)
                lines.append({"i": i, "dur": round(dur, 3)})
                total += dur
                print(f"  line {i}: {dur:.2f}s")
            except Exception as e:
                print(f"  ❌ line {i}: {e}")
                lines.append({"i": i, "error": str(e)})

        # + 100ms بين كل مشهدين (4 فرواصل)
        with_silence = total + (len(LINES) - 1) * 0.1
        result = {
            "rate": rate,
            "voice_duration": round(total, 3),
            "with_silence": round(with_silence, 3),
            "in_range_45_58": 45.0 <= with_silence <= 58.0,
            "lines": lines,
        }
        results.append(result)
        status = "✓" if result["in_range_45_58"] else "✗"
        print(f"  → TOTAL: {total:.2f}s | +silence: {with_silence:.2f}s {status}")

    # حفظ
    (OUT / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\n" + "=" * 55)
    print("ملخص:")
    print(f"{'rate':>6} | {'voice':>8} | {'+silence':>9} | النطاق")
    print("-" * 55)
    for r in results:
        s = "✓" if r["in_range_45_58"] else "✗"
        print(f"{r['rate']:>6.3f} | {r['voice_duration']:>7.2f}s | {r['with_silence']:>8.2f}s | {s}")

    # التوصية: أعلى rate داخل النطاق (أسرع = أكثر طبيعية)
    valid = [r for r in results if r["in_range_45_58"]]
    if valid:
        best = max(valid, key=lambda r: r["rate"])
        print(f"\n🎯 التوصية: rate = {best['rate']} ({best['with_silence']:.2f}s)")
    else:
        # أعلى rate أقل من 45s + أعلى rate أكبر من 45s
        too_fast = [r for r in results if r["with_silence"] < 45.0]
        too_slow = [r for r in results if r["with_silence"] > 58.0]
        if too_fast:
            print(f"\n⚠️  أقرب rate سريع: {max(too_fast, key=lambda r: r['rate'])['rate']}")

asyncio.run(main())
print(f"\n📄 {OUT / 'results.json'}")
