"""يحوّل SRT إلى ASS مع Style مضمون:
   - أسفل المركز (Alignment=2)
   - MarginV=140 (بعيد عن شريط التطبيقات)
   - FontSize=44، ظل خفيف
   - لا box (Outline فقط)
"""
import re
from pathlib import Path

SRT = Path("spike_tmp/voice_srt/merged.srt")  # الأصلي قبل التقسيم
OUT = Path("spike_tmp/voice_srt/merged.ass")

W, H = 1080, 1920

ASS_HEADER = f"""[Script Info]
Title: 017 subtitles
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Amiri,140,&H00F0E8DC,&H000000FF,&H00100A08,&H80000000,0,0,0,0,100,100,0,0,1,3,2,2,60,60,140,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def parse_srt(path):
    content = path.read_text(encoding="utf-8")
    blocks = content.strip().split("\n\n")
    cues = []
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) < 3:
            continue
        try:
            m = re.search(
                r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
                r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})",
                lines[1]
            )
            if not m:
                continue
            h1,mm1,s1,ms1,h2,mm2,s2,ms2 = map(int, m.groups())
            start = h1*3600+mm1*60+s1+ms1/1000
            end = h2*3600+mm2*60+s2+ms2/1000
            text = " ".join(lines[2:]).strip()
            # حذف أي override tags قديمة
            text = re.sub(r"\{[^}]*\}", "", text)
            cues.append((start, end, text))
        except Exception:
            continue
    return cues

def fmt_ass_time(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    cs = int((t - int(t)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

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

def escape_ass(text):
    """يهرب الأحرف الخاصة في ASS."""
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

cues = parse_srt(SRT)
print(f"Original SRT: {len(cues)} cues")

split = split_long(cues)
print(f"After split: {len(split)} cues (≤2.5s each)")

with OUT.open("w", encoding="utf-8") as f:
    f.write(ASS_HEADER)
    for (s, e, txt) in split:
        txt_esc = escape_ass(txt)
        f.write(f"Dialogue: 0,{fmt_ass_time(s)},{fmt_ass_time(e)},"
                f"Default,,0,0,0,,{txt_esc}\n")

print(f"✅ {OUT}")
print(f"   Style: Default, Amiri, 44, Alignment=2 (bottom-center), MarginV=140")
print(f"\nأول 3 Dialogue lines:")
for line in OUT.read_text(encoding="utf-8").split("\n"):
    if line.startswith("Dialogue:"):
        print(f"  {line[:100]}")
