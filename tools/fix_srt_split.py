"""يقسم cues طويلة ويضيف \\pos لضمان الموضع أسفل الشاشة."""
import re
from pathlib import Path

SRT = Path("spike_tmp/voice_srt/merged.srt")
OUT = Path("spike_tmp/voice_srt/merged_split.srt")

# موضع الترجمة: أسفل المركز، أعلى شريط التطبيقات
# \an2 = alignment قاع-وسط
# \pos(540, 1650) = x=منتصف، y=قاع النص عند 1650 (من أصل 1920)
POS_TAG = r"{\an2\pos(540,1650)}"

def parse_srt(path):
    content = path.read_text(encoding="utf-8")
    blocks = content.strip().split("\n\n")
    cues = []
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) < 3:
            continue
        try:
            m1 = re.search(
                r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
                r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
                lines[1]
            )
            if not m1:
                continue
            h1,mm1,s1,ms1,h2,mm2,s2,ms2 = map(int, m1.groups())
            start = h1*3600+mm1*60+s1+ms1/1000
            end = h2*3600+mm2*60+s2+ms2/1000
            text = " ".join(lines[2:]).strip()
            # حذف أي override tags قديمة
            text = re.sub(r"^\{[^}]*\}", "", text)
            cues.append((start, end, text))
        except Exception:
            continue
    return cues

def split_long(cues, max_dur=2.5):
    out = []
    for start, end, text in cues:
        dur = end - start
        if dur <= max_dur:
            out.append((start, end, text))
            continue
        words = text.split()
        if not words:
            continue
        n_parts = max(2, int(dur / max_dur) + (1 if dur % max_dur > 0.3 else 0))
        wpp = max(1, len(words) // n_parts)
        parts = []
        for i in range(0, len(words), wpp):
            chunk = words[i:i+wpp]
            if chunk:
                parts.append(" ".join(chunk))
        if not parts:
            out.append((start, end, text))
            continue
        part_dur = dur / len(parts)
        for i, part in enumerate(parts):
            ps = start + i * part_dur
            pe = ps + part_dur
            out.append((ps, pe, part))
    return out

def fmt(t):
    h = int(t // 3600); m = int((t % 3600) // 60)
    s = int(t % 60); ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

cues = parse_srt(SRT)
print(f"Original: {len(cues)} cues")

split = split_long(cues)
print(f"Split: {len(split)} cues")

with OUT.open("w", encoding="utf-8") as f:
    for i, (s, e, txt) in enumerate(split, 1):
        # إضافة \pos مطلق قبل كل نص
        tagged = POS_TAG + txt
        f.write(f"{i}\n{fmt(s)} --> {fmt(e)}\n{tagged}\n\n")

print(f"✅ {OUT}")
print(f"   كل cue يبدأ بـ {POS_TAG}")
print(f"\nأول 3 cues:")
for line in OUT.read_text(encoding="utf-8").split("\n\n")[:3]:
    print(f"  ---")
    for ln in line.strip().split("\n"):
        print(f"  {ln}")
