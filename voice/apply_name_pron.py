import json, re, sys
from pathlib import Path

VARIANTS = {
    "A": "الْمَساوى", "B": "الْمَساوَ", "C": "الْمَساوي",
    "D": "الْمَساوِ", "E": "الْمُساوى", "F": "الْمَساوْ",
}
if len(sys.argv) < 2 or sys.argv[1].upper() not in VARIANTS:
    print("الاستخدام: python3 voice/apply_name_pron.py B")
    print("الخيارات: " + " | ".join(f"{k}={v}" for k, v in VARIANTS.items()))
    raise SystemExit(2)

key = sys.argv[1].upper()
new = VARIANTS[key]
pat = re.compile("|".join(re.escape(x) for x in
                 ["الْمَساوى", "الْمَساوَ", "الْمَساوي", "الْمَساوِ", "الْمُساوى", "الْمَساوْ",
                  "المساوى", "المساوَ", "المساوي", "المساوِ"]))

changed = []
for p in sorted(Path("scripts").glob("video_*.txt")):
    out, hit = [], 0
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s and not s.startswith("#"):
            f = [x.strip() for x in s.split("|")]
            if f[0] == "LINE" and len(f) > 1:
                f[1], n = pat.subn(new, f[1])   # حقل النطق فقط
                hit += n
                out.append("|".join(f)); continue
        out.append(line)
    if hit:
        p.write_text("\n".join(out) + "\n", encoding="utf-8")
        changed.append((p.name, hit))

cfgp = Path("config.json")
c = json.loads(cfgp.read_text(encoding="utf-8"))
c.setdefault("brand", {})["name_tts"] = new
cfgp.write_text(json.dumps(c, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"✅ النطق المختار: {key} = {new}")
for n, h in changed:
    print(f"   {n}: {h} موضع")
print("ℹ️ نص الشاشة والشارة والغلاف لم يتغيّر.")
