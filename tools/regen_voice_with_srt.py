"""يعيد توليد TTS مع SRT تلقائي من edge-tts.
   يدعم --write-subtitles (word-level boundaries)."""
import sys, subprocess, asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "voice_srt"
OUT.mkdir(parents=True, exist_ok=True)

LINES = [
    "هَاتِفُكَ بَطِيءٌ؟ الْمُشْكِلَةُ لَيْسَتْ فِي الْجِهَازِ، بَلْ فِي هَذِهِ الْإِعْدَادَاتِ الثَّلَاثَةِ الْخَفِيَّةِ.",
    "أَوَّلًا: رُسُومُ الِانْتِقَالِ. اِذْهَبْ إِلَى خِيَارَاتِ الْمُطَوِّرِ، وَأَوْقِفْهَا أَوْ خَفِّفْهَا لِتَسْرِيعِ الِاسْتِجَابَةِ فَوْرًا.",
    "ثَانِيًا: تَحْدِيثُ التَّطْبِيقَاتِ فِي الْخَلْفِيَّةِ. أَغْلِقْ هَذَا الْخِيَارَ لِلتَّطْبِيقَاتِ الَّتِي لَا تَسْتَخْدِمُهَا يَوْمِيًّا.",
    "ثَالِثًا: مَسَاحَةُ التَّخْزِينِ الْمُمْتَلِئَةُ. اِتْرُكْ عِشْرِينَ بِالْمِئَةِ فَارِغَةً عَلَى الْأَقَلِّ، لِيَعْمَلَ النِّظَامُ بِسَلَاسَةٍ.",
    "جَرِّبْ هَذِهِ الْخُطُوَاتِ الْيَوْمَ، وَلَاحِظِ الْفَرْقَ بِنَفْسِكَ. اِحْفَظِ الْفِيدْيُو، وَتَابِعْ أَبُو مُحَمَّدْ الْمَساوَا.",
]

VOICE = "ar-EG-ShakirNeural"
RATE = -12  # 0.88 → -12%

def probe(p):
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True
    )
    return float(r.stdout.strip())

async def synth(text, mp3_path, srt_path):
    import edge_tts
    comm = edge_tts.Communicate(text=text, voice=VOICE, rate=f"{RATE}%")
    # الطريقة الرسمية: stream() + SubMaker (لا save(subtitle=...))
    submaker = edge_tts.SubMaker()
    with open(str(mp3_path), "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)
    # SRT
    Path(srt_path).write_text(submaker.get_srt(), encoding="utf-8")

async def main():
    lines_info = []
    for i, text in enumerate(LINES):
        mp3 = OUT / f"line_{i}.mp3"
        wav = OUT / f"line_{i}.wav"
        srt = OUT / f"line_{i}.srt"
        print(f"🎤 line {i}...")
        await synth(text, mp3, srt)
        subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(mp3), "-ar", "48000", "-ac", "1",
             "-c:a", "pcm_s16le", str(wav)],
            check=True
        )
        dur = probe(wav)
        lines_info.append({"i": i, "dur": round(dur, 3),
                            "wav": str(wav), "srt": str(srt)})
        print(f"   {dur:.2f}s")

    # دمج SRT مع إزاحة زمنية
    def parse_srt(path):
        """يعيد list of (start, end, text)."""
        import re
        content = Path(path).read_text(encoding="utf-8")
        blocks = content.strip().split("\n\n")
        out = []
        for b in blocks:
            lines = b.strip().split("\n")
            if len(lines) < 3:
                continue
            m = re.match(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})", lines[1])
            if not m:
                continue
            h, mm, s, ms = map(int, m.groups())
            start = h*3600 + mm*60 + s + ms/1000
            m2 = re.match(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
                          lines[1].split(" --> ")[1])
            h, mm, s, ms = map(int, m2.groups())
            end = h*3600 + mm*60 + s + ms/1000
            text = " ".join(lines[2:])
            out.append((start, end, text))
        return out

    def fmt_srt(t):
        h = int(t // 3600); m = int((t % 3600) // 60)
        s = int(t % 60); ms = int((t - int(t)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    all_cues = []
    offset = 0.0
    SILENCE = 0.1
    for info in lines_info:
        cues = parse_srt(info["srt"])
        for (s, e, txt) in cues:
            all_cues.append((s + offset, e + offset, txt))
        offset += info["dur"] + SILENCE

    # SRT merged
    merged_srt = OUT / "merged.srt"
    with merged_srt.open("w", encoding="utf-8") as f:
        for idx, (s, e, txt) in enumerate(all_cues, 1):
            f.write(f"{idx}\n{fmt_srt(s)} --> {fmt_srt(e)}\n{txt}\n\n")
    print(f"\n✅ merged.srt: {len(all_cues)} cues, offset total={offset:.2f}s")

    # WAV concat
    silence_wav = OUT / "silence.wav"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=mono",
        "-t", str(SILENCE), "-c:a", "pcm_s16le", str(silence_wav)
    ], check=True)

    concat_list = OUT / "concat.txt"
    with concat_list.open("w") as f:
        for i, info in enumerate(lines_info):
            f.write(f"file '{info['wav']}'\n")
            if i < len(lines_info) - 1:
                f.write(f"file '{silence_wav}'\n")

    voice_full = OUT / "voice_full.wav"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "1",
        str(voice_full)
    ], check=True)
    print(f"✅ voice_full.wav: {probe(voice_full):.2f}s")

    import json
    (OUT / "info.json").write_text(json.dumps({
        "lines": lines_info, "offset": offset,
        "voice": str(voice_full), "srt": str(merged_srt),
        "total_dur": probe(voice_full)
    }, ensure_ascii=False, indent=2), encoding="utf-8")

asyncio.run(main())
print(f"📁 {OUT}")
