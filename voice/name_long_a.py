import json, re, shutil, subprocess
from pathlib import Path

CHOSEN = "الْمَساوَا"          # واو + ألف صريحة = مدّ طويل مضمون
FORMS  = {
    "G": ("الْمَساوَا",  "واو + ألف صريحة — مدّ طويل مضمون (المختار)"),
    "H": ("الْمَساوىٰٓ", "ألف خنجرية + مدّة — كتابتك الأصلية"),
    "I": ("الْمَسَاوَى",  "فتحة على الواو + ألف مقصورة"),
}

OLD = ["الْمَساوىٰٓ","الْمَساوَا","الْمَسَاوَى","الْمَساوى","الْمَساوَ","الْمَساوي",
       "الْمَساوِ","الْمُساوى","الْمَساوْ","المساوىٰٓ","المساوا","المساوى",
       "المساوَ","المساوي","المساوِ"]
OLD.sort(key=len, reverse=True)
pat = re.compile("|".join(re.escape(x) for x in OLD))

changed = []
for p in sorted(Path("scripts").glob("video_*.txt")):
    out, hit = [], 0
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            f = [x.strip() for x in s.split("|")]
            if f[0] == "LINE" and len(f) > 1:
                f[1], n = pat.subn(CHOSEN, f[1])   # حقل النطق فقط
                hit += n
                out.append("|".join(f)); continue
        out.append(line)
    if hit:
        p.write_text("\n".join(out) + "\n", encoding="utf-8")
        changed.append((p.name, hit))

cfgp = Path("config.json")
c = json.loads(cfgp.read_text(encoding="utf-8"))
c.setdefault("brand", {})["name_tts"] = CHOSEN
c["project"] = "أبو محمد المساوى"
cfgp.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"✅ النطق المطبَّق: {CHOSEN}  (مدّ طويل)")
for n, h in changed:
    print(f"   {n}: {h} موضع")
print("ℹ️ الشاشة والشارة والغلاف: المساوى (لم تتغيّر)")

OUT = Path("output/name_test"); OUT.mkdir(parents=True, exist_ok=True)
edge = shutil.which("edge-tts")
espeak = shutil.which("espeak-ng") or shutil.which("espeak")
for key, (name, desc) in FORMS.items():
    text = f"احْفَظِ الْفيدْيو وَتابِعْ أَبو مُحَمَّد {name}، وَغَدًا نَنْتَقِلُ لِلْمَهارَة."
    mp3, wav = OUT / f"{key}.mp3", OUT / f"{key}.wav"
    ok = False
    if edge:
        r = subprocess.run([edge, "--voice", "ar-EG-ShakirNeural", "--text", text,
                            "--write-media", str(mp3)], capture_output=True,
                           text=True, stdin=subprocess.DEVNULL)
        ok = r.returncode == 0 and mp3.exists() and mp3.stat().st_size > 1500
    if not ok and espeak:
        r = subprocess.run([espeak, "-v", "ar", "-s", "145", "-w", str(wav), text],
                           capture_output=True, text=True, stdin=subprocess.DEVNULL)
        ok = r.returncode == 0 and wav.exists()
    print(f"{'✅' if ok else '❌'} عينة {key}: {desc}")
