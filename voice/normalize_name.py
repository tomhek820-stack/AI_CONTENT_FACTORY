"""يُوحّد نطق اسم القناة في حقل النطق فقط، حسب config.brand.name_tts."""
import json, re, sys
from pathlib import Path

cfg = json.loads(Path("config.json").read_text(encoding="utf-8"))
CHOSEN = cfg.get("brand", {}).get("name_tts", "الْمَساوَا")

OLD = ["الْمَساوىٰٓ","الْمَساوَاا","الْمَساوَا","الْمَسَاوَى","الْمَساوى","الْمَساوَ",
       "الْمَساوي","الْمَساوِ","الْمُساوى","الْمَساوْ","المساوىٰٓ","المساوا",
       "المساوى","المساوَ","المساوي","المساوِ"]
OLD = sorted(set(OLD) - {CHOSEN}, key=len, reverse=True)
pat = re.compile("|".join(re.escape(x) for x in OLD)) if OLD else None

targets = [Path(a) for a in sys.argv[1:]] or sorted(Path("scripts").glob("video_*.txt"))
total = 0
for p in targets:
    if not p.exists():
        print(f"⚠️ غير موجود: {p.name}"); continue
    out, hit = [], 0
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            f = [x.strip() for x in s.split("|")]
            if f[0] == "LINE" and len(f) > 1 and pat:
                f[1], n = pat.subn(CHOSEN, f[1])
                hit += n
                out.append("|".join(f)); continue
        out.append(line)
    if hit:
        p.write_text("\n".join(out) + "\n", encoding="utf-8")
    total += hit
    print(f"{'🔧' if hit else '✅'} {p.name}: {hit} تعديل")
print(f"\nالنطق المعتمد: {CHOSEN} | إجمالي التعديلات: {total}")
