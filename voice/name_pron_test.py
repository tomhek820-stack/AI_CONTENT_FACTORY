import shutil, subprocess, sys
from pathlib import Path

OUT = Path("output/name_test"); OUT.mkdir(parents=True, exist_ok=True)
VOICE = "ar-EG-ShakirNeural"

VARIANTS = {
    "A": ("الْمَساوى", "ألف مقصورة ممدودة — al-Masawaa (النطق الحالي)"),
    "B": ("الْمَساوَ", "فتحة قصيرة على الواو — al-Masawa"),
    "C": ("الْمَساوي", "ياء ممدودة — al-Masawee"),
    "D": ("الْمَساوِ", "كسرة قصيرة — al-Masawi"),
    "E": ("الْمُساوى", "ميم مضمومة — al-Musawaa"),
    "F": ("الْمَساوْ", "سكون بلا حركة أخيرة — al-Masaw"),
}

has_edge = shutil.which("edge-tts") is not None
has_espeak = shutil.which("espeak-ng") or shutil.which("espeak")

for key, (name, desc) in VARIANTS.items():
    text = f"أَبو مُحَمَّد {name}. وَتابِعْ أَبو مُحَمَّد {name}."
    mp3 = OUT / f"{key}.mp3"
    wav = OUT / f"{key}.wav"
    ok = False
    if has_edge:
        r = subprocess.run(["edge-tts", "--voice", VOICE, "--text", text,
                            "--write-media", str(mp3)],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL)
        ok = r.returncode == 0 and mp3.exists() and mp3.stat().st_size > 1500
    if not ok and has_espeak:
        b = shutil.which("espeak-ng") or shutil.which("espeak")
        r = subprocess.run([b, "-v", "ar", "-s", "145", "-w", str(wav), text],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL)
        ok = r.returncode == 0 and wav.exists()
    print(f"{'✅' if ok else '❌'} {key}: {desc}")

(OUT / "README.txt").write_text(
    "\n".join(f"{k} = {v[0]}  |  {v[1]}" for k, v in VARIANTS.items()), encoding="utf-8")
print("\nاستمع للملفات A→F ثم اختر حرفًا واحدًا.")
