"""فحص ذاتي صارم — لا نجاح معلن مع فشل أي مكوّن حرج."""
from __future__ import annotations
import argparse, json, os, py_compile, re, subprocess
from pathlib import Path
from engine import common as C

RESULTS = []


def chk(name, cond, detail="", critical=True):
    RESULTS.append({"name": name, "ok": bool(cond), "detail": str(detail), "critical": critical})
    print("[%s] %-32s %s" % ("PASS" if cond else ("FAIL" if critical else "WARN"), name, detail), flush=True)
    return bool(cond)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true"); ap.add_argument("--structure-only", action="store_true")
    a = ap.parse_args(); R = C.ROOT; W, H, fps = C.dims(a.preview)
    core = ["requirements.txt", "generate.sh", "config.json",
            "voice/generate_voice.py", "engine/common.py", "engine/scenes.py", "engine/subtitles.py",
            "engine/audio.py", "engine/render.py", "engine/publish.py", "engine/selftest.py",
            "output/publish_description.txt"]
    for f in core:
        p = R / f
        chk("file:" + f, p.exists() and p.stat().st_size > 40, p.stat().st_size if p.exists() else 0)
    import os as _os
    act = _os.environ.get("AILAB_SCRIPT") or str(R / "scripts" / "video_001.txt")
    chk("active script", Path(act).exists() and Path(act).stat().st_size > 40, Path(act).name)
    r = subprocess.run(["bash", "-n", str(R / "generate.sh")], capture_output=True, text=True)
    chk("bash -n generate.sh", r.returncode == 0, r.stderr.strip()[:120])
    chk("exec bit generate.sh", os.access(str(R / "generate.sh"), os.X_OK), "")
    bad = []
    for p in list((R / "engine").glob("*.py")) + [R / "voice" / "generate_voice.py"]:
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as e:
            bad.append("%s:%s" % (p.name, e))
    chk("python syntax", not bad, "; ".join(bad)[:200])
    try:
        from PIL import features
        chk("Pillow", True, "raqm=%s" % features.check("raqm"))
    except Exception as e:
        chk("Pillow", False, str(e)[:100])
    try:
        from PIL import features
        f = C.resolve_font(verbose=False)
        chk("Arabic font", C.font_has_arabic_forms(f) or features.check("raqm"), Path(f).name)
    except Exception as e:
        chk("Arabic font", False, str(e)[:100])
    chk("reshaper", any(0xFE70 <= ord(c) <= 0xFEFF for c in C.reshape("مرحبا بالعقل")), "")
    if a.structure_only:
        finish(); return
    vw = C.VOICE / "voice.wav"; tlp = C.VOICE / "timeline.json"; tl = None
    if chk("voice.wav", vw.exists() and vw.stat().st_size > 100000, ""):
        sr, arr = C.wav_read(vw); dur = len(arr) / float(sr); D = C.cfg()["duration"]
        chk("voice 48k", sr == 48000, sr)
        chk("voice 45-60s", D["min"] <= dur <= D["max"], "%.2f" % dur)
        chk("voice not silent", C.rms(arr) > 250, "rms=%.0f" % C.rms(arr))
    if chk("timeline.json", tlp.exists(), ""):
        tl = json.loads(tlp.read_text(encoding="utf-8"))
        chk("not synthetic", tl.get("synthetic") is False, "")
        last = -1; mono = True
        for sc in tl["scenes"]:
            for ln in sc["lines"]:
                if ln["start"] < last - 1e-6 or ln["end"] <= ln["start"]:
                    mono = False
                last = ln["end"]
        chk("timeline monotonic", mono, "")
    srt = R / "scripts" / "subtitles.srt"
    if chk("subtitles.srt", srt.exists() and srt.stat().st_size > 200, ""):
        body = srt.read_text(encoding="utf-8")
        blocks = [b for b in body.strip().split("\n\n") if "-->" in b]
        chk("srt cues>=8", len(blocks) >= 8, len(blocks))
        chk("srt arabic", bool(re.search(r"[\u0600-\u06FF]", body)), "")
        over = sum(1 for b in blocks if len(b.split("\n")[2:]) > 2)
        chk("srt <=2 lines", over == 0, over)
        if tl:
            t = re.search(r"(\d\d):(\d\d):(\d\d),(\d\d\d)", body)
            if t:
                g = t.groups(); first = int(g[0]) * 3600 + int(g[1]) * 60 + int(g[2]) + int(g[3]) / 1000
                chk("srt synced", abs(first - tl["scenes"][0]["lines"][0]["start"]) < 0.02, "%.3f" % first)
    meta = C.OUT / "subtitles_meta.json"
    if chk("subtitle meta", meta.exists(), ""):
        m = json.loads(meta.read_text(encoding="utf-8"))
        chk("sub PNGs", all(Path(x["file"]).exists() for x in m) and len(m) >= 8, len(m))
        chk("sub safe width", all(x["w"] <= W - 2 * C.scale(30, W) for x in m), "")
        chk("sub above UI", all(x["y"] + x["h"] <= H * 0.86 for x in m), "")
    bed = C.MUSIC / "bed.wav"
    if chk("bed.wav", bed.exists() and bed.stat().st_size > 100000, ""):
        chk("bed not silent", C.rms(C.wav_read(bed)[1]) > 100, "")
    fv = C.OUT / "final_video.mp4"
    if chk("final_video.mp4", fv.exists() and fv.stat().st_size > 300000,
           "%.2fMB" % (fv.stat().st_size / 1e6 if fv.exists() else 0)):
        j = C.ffprobe_json(fv)
        v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
        au = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
        d = float(j["format"]["duration"]); D = C.cfg()["duration"]
        chk("h264", v and v["codec_name"] == "h264", "")
        chk("dimensions", v and v["width"] == W and v["height"] == H, "%sx%s" % (v["width"], v["height"]))
        chk("45-60s", D["min"] <= d <= D["max"], "%.3f" % d)
        chk("aac audio", au and au["codec_name"] == "aac", "")
    for t in ("thumbnail.jpg", "thumbnail_yt.jpg"):
        p = C.OUT / t
        chk("thumb " + t, p.exists() and p.stat().st_size > 20000, "")
    finish()


def finish():
    fails = [r for r in RESULTS if not r["ok"] and r["critical"]]
    C.LOGS.mkdir(parents=True, exist_ok=True)
    (C.LOGS / "selftest.json").write_text(json.dumps(RESULTS, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n===== SELFTEST: %d checks | %d FAIL =====" % (len(RESULTS), len(fails)))
    for f in fails:
        print("  FAIL: %s -> %s" % (f["name"], f["detail"]))
    if fails:
        raise SystemExit(2)
    print("✅ كل الفحوص الحرجة نجحت.")


if __name__ == "__main__":
    main()
