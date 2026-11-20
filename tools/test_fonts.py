from __future__ import annotations
import sys
from pathlib import Path as _P
_ROOT = _P(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from engine import common as C

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = ROOT / "assets" / "fonts"
OUT = ROOT / "spike_tmp" / "fonts"
OUT.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    "Amiri-Bold.ttf",
    "ReemKufi-Bold.ttf",
    "IBMPlexSansArabic-Medium.ttf",
    "Cairo-Bold.ttf",
    "Tajawal-Bold.ttf",
]

SENTENCES = [
    ("plain", "بسم الله الرحمن الرحيم"),
    ("digits", "٣ إعدادات خفية تبطئ هاتفك"),
    ("tashkeel", "هَذِهِ جُمْلَةٌ مُشَكَّلَةٌ لِلْاِخْتِبَارِ"),
]


def components(alpha: Image.Image):
    w, h = alpha.size
    data = alpha.tobytes()
    seen = bytearray(w * h)
    comps = []
    for y in range(h):
        row = y * w
        for x in range(w):
            idx = row + x
            if not data[idx] or seen[idx]:
                continue
            stack = [idx]
            seen[idx] = 1
            area = 0
            minx = maxx = x
            miny = maxy = y
            sumx = sumy = 0
            while stack:
                cur = stack.pop()
                cy, cx = divmod(cur, w)
                area += 1
                sumx += cx
                sumy += cy
                if cx < minx: minx = cx
                if cx > maxx: maxx = cx
                if cy < miny: miny = cy
                if cy > maxy: maxy = cy
                if cx > 0:
                    n = cur - 1
                    if data[n] and not seen[n]:
                        seen[n] = 1; stack.append(n)
                if cx < w - 1:
                    n = cur + 1
                    if data[n] and not seen[n]:
                        seen[n] = 1; stack.append(n)
                if cy > 0:
                    n = cur - w
                    if data[n] and not seen[n]:
                        seen[n] = 1; stack.append(n)
                if cy < h - 1:
                    n = cur + w
                    if data[n] and not seen[n]:
                        seen[n] = 1; stack.append(n)
            if area >= 5:
                comps.append({
                    "area": area,
                    "bbox": [minx, miny, maxx, maxy],
                    "cx": sumx / area,
                    "cy": sumy / area,
                })
    return comps


def median(vals):
    if not vals:
        return 0
    s = sorted(vals)
    return s[len(s) // 2]


def missing_glyphs(fp: Path, chars: set[str]) -> list[str]:
    font = ImageFont.truetype(str(fp), 64)

    def bitmap(ch: str) -> bytes:
        im = Image.new("L", (160, 160), 0)
        ImageDraw.Draw(im).text((20, 20), ch, font=font, fill=255)
        return im.tobytes()

    notdef = bitmap("\uE123")
    missing = []
    for ch in sorted(chars):
        if ch.isspace():
            continue
        if bitmap(ch) == notdef:
            missing.append(ch)
    return missing


def analyze_line(fp: Path, text: str, size: int = 52):
    pen = C.ArabicPen(str(fp), size, stroke=1)
    li = pen.line_img(text, (255, 255, 255, 255))
    alpha = li.getchannel("A").point(lambda v: 255 if v > 40 else 0)
    comps = components(alpha)
    total_ink = sum(1 for v in alpha.tobytes() if v)
    large_thr = max(40, int(total_ink * 0.002))
    large = [c for c in comps if c["area"] >= large_thr]
    small = [c for c in comps if c["area"] < large_thr]
    expected = max(1, len(text.split()))
    # العربية: كلمة = جسم + نقاط. عتبة 6× آمنة للعربية، صارمة على اللاتيني
    connected_ok = len(large) <= max(6, expected * 6)

    base_top = median([c["bbox"][1] for c in large])
    base_bottom = median([c["bbox"][3] for c in large])
    marks = 0
    for c in small:
        if c["cy"] < base_top - 4 or c["cy"] > base_bottom + 4:
            marks += 1

    chars = set()
    for tok in text.split():
        try:
            chars.update(ch for ch in pen._prep(tok, True) if not ch.isspace())
        except Exception:
            chars.update(ch for ch in tok if not ch.isspace())
    miss = missing_glyphs(fp, chars)
    coverage_ok = len(miss) == 0

    return li, {
        "expected_words": expected,
        "large_components": len(large),
        "small_components": len(small),
        "connected_ok": bool(connected_ok),
        "tashkeel_marks_detected": int(marks),
        "missing_glyphs": miss,
        "coverage_ok": bool(coverage_ok),
        "pass": bool(connected_ok and coverage_ok),
    }


def main():
    report = {"fonts": [], "recommend": {}}
    for name in CANDIDATES:
        fp = FONT_DIR / name
        item = {"file": name, "exists": fp.exists(), "lines": {}}
        if not fp.exists():
            item["decision"] = "SKIP_MISSING"
            report["fonts"].append(item)
            print(f"⚠️ SKIP missing: {name}")
            continue

        canvas = Image.new("RGBA", (1080, 400), (0, 0, 0, 0))
        y = 24
        all_pass = True
        for key, text in SENTENCES:
            try:
                li, metrics = analyze_line(fp, text)
            except Exception as e:
                metrics = {"error": str(e), "pass": False}
                li = None
                all_pass = False
            item["lines"][key] = metrics
            if not metrics.get("pass", False):
                all_pass = False
            if li is not None:
                x = max(16, 1080 - 96 - li.width)
                canvas.alpha_composite(li, (x, y))
            y += 120

        item["decision"] = "PASS" if all_pass else "REJECT"
        canvas.convert("RGB").save(str(OUT / f"{fp.stem}.png"), "PNG")
        report["fonts"].append(item)
        print(f"{'✅' if all_pass else '❌'} {name}: {item['decision']}")
        for key, m in item["lines"].items():
            if "error" in m:
                print(f"   {key}: ERROR {m['error']}")
            else:
                print(f"   {key}: connected={m['connected_ok']} coverage={m['coverage_ok']} large={m['large_components']} marks={m['tashkeel_marks_detected']} missing={len(m['missing_glyphs'])}")

    passed = {i["file"] for i in report["fonts"] if i.get("decision") == "PASS"}
    for role, prefs in {
        "title": ["ReemKufi-Bold.ttf", "Cairo-Bold.ttf", "Tajawal-Bold.ttf", "Amiri-Bold.ttf"],
        "body": ["IBMPlexSansArabic-Medium.ttf", "Cairo-Bold.ttf", "Tajawal-Bold.ttf", "Amiri-Bold.ttf"],
        "wisdom": ["Amiri-Bold.ttf"],
    }.items():
        report["recommend"][role] = next((p for p in prefs if p in passed), None)

    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== RECOMMEND ===")
    print(json.dumps(report["recommend"], ensure_ascii=False, indent=2))
    print(f"📄 report: {OUT / 'report.json'}")


if __name__ == "__main__":
    main()
