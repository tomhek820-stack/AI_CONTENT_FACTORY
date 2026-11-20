"""تعليق صوتي عربي + خط زمني مقاس فعليًا (piper / edge / espeak / manual)."""
from __future__ import annotations
import argparse, hashlib, json, os, shlex, shutil, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from engine import common as C
from engine import scenes as S

LINES = C.VOICE / "lines"
MANUAL = C.VOICE / "manual"
MODELS = C.ROOT / "assets" / "voices"
TEXT_TMP = LINES / "_text.txt"

def _signed(val, unit):
    """edge-tts يقبل فقط صيغة مثل +0Hz أو -6% — نُطبّع أي إدخال."""
    t = str(val).strip().replace(unit, "").replace("%", "").strip()
    try:
        n = int(float(t))
    except Exception:
        n = 0
    return "%+d%s" % (n, unit)



def http_get(url, dest=None, timeout=90):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AI-TECH-LAB)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if dest:
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        Path(dest).write_bytes(data)
        return Path(dest)
    return data


class Piper:
    name = "piper"; natural = True; offline = True

    def __init__(self):
        self.c = C.cfg()["tts"]["piper"]
        self.bin = shutil.which("piper"); self.module = False; self.proot = None; self._help = ""
        if self.bin:
            p = C.run([self.bin, "--help"], check=False); self._help = (p.stdout or "") + (p.stderr or "")
        else:
            p = C.run([sys.executable, "-c", "import piper"], check=False)
            self.module = p.returncode == 0
            if self.module:
                p = C.run([sys.executable, "-m", "piper", "--help"], check=False)
                self._help = (p.stdout or "") + (p.stderr or "")
            elif shutil.which("proot-distro"):
                dist = self.c.get("proot_distro", "debian")
                p = C.run(["proot-distro", "login", dist, "--", "bash", "-lc",
                           "command -v piper || python3 -c 'import piper'"], check=False)
                if p.returncode == 0:
                    self.proot = dist; self._help = "--output_file --config --length_scale"
        self.model = None

    def available(self):
        return bool(self.bin or self.module or self.proot)

    def _discover(self):
        idx = MODELS / "voices.json"
        if not idx.exists():
            try:
                http_get(self.c["voices_index"], idx)
            except Exception as e:
                C.log("piper: تعذّر تنزيل الفهرس (%s)" % e, "WARN"); return None
        try:
            data = json.loads(idx.read_text(encoding="utf-8"))
        except Exception:
            return None
        keys = [k for k in data if k.startswith("ar")]
        if not keys:
            C.log("piper: لا صوت عربي في الفهرس", "WARN"); return None
        hint = self.c.get("voice_hint", "ar"); q = self.c.get("quality_hint", "medium")
        keys.sort(key=lambda k: (0 if k.startswith(hint) else 1,
                                 0 if q in k else (1 if "medium" in k else 2), k))
        return keys[0], data[keys[0]]

    def ensure_model(self):
        if self.model:
            return self.model
        for f in sorted(MODELS.glob("ar_*.onnx")):
            j = f.with_suffix(".onnx.json")
            if f.stat().st_size > 3000000 and j.exists():
                self.model = (f, j); return self.model
        d = self._discover()
        if not d:
            return None
        key, entry = d
        files = list(entry.get("files", {}).keys())
        onnx_rel = next((f for f in files if f.endswith(".onnx")), None)
        json_rel = next((f for f in files if f.endswith(".onnx.json")), None)
        if not onnx_rel:
            return None
        if json_rel is None:
            json_rel = onnx_rel + ".json"
        try:
            op = http_get(self.c["base_url"] + onnx_rel, MODELS / Path(onnx_rel).name, timeout=240)
            jp = http_get(self.c["base_url"] + json_rel, MODELS / Path(json_rel).name, timeout=90)
        except Exception as e:
            C.log("piper: فشل تنزيل النموذج (%s)" % e, "WARN"); return None
        if op.stat().st_size < 3000000:
            C.log("piper: نموذج صغير جدًا — مرفوض", "WARN"); op.unlink(missing_ok=True); return None
        try:
            json.loads(jp.read_text(encoding="utf-8"))
        except Exception:
            C.log("piper: إعدادات تالفة", "WARN"); return None
        C.log("piper model: %s (%.1f MB)" % (op.name, op.stat().st_size / 1e6))
        self.model = (op, jp); return self.model

    def synth(self, text, out, rate):
        m = self.ensure_model()
        if not m:
            raise RuntimeError("no arabic piper model")
        onnx, js = m
        ls = float(self.c["length_scale"]) / max(0.5, rate)
        oflag = "--output-file" if "--output-file" in self._help else "--output_file"
        args = ["--model", str(onnx), oflag, str(out), "--length_scale", str(round(ls, 4))]
        if "--config" in self._help:
            args += ["--config", str(js)]
        TEXT_TMP.parent.mkdir(parents=True, exist_ok=True)
        TEXT_TMP.write_text(text, encoding="utf-8")
        if self.bin:
            p = C.run([self.bin] + args, input_text=text, check=False)
        elif self.module:
            p = C.run([sys.executable, "-m", "piper"] + args, input_text=text, check=False)
        else:
            inner = [a.replace(str(ROOT), "/host") for a in ["piper"] + args]
            cmd = "cd /host && " + " ".join(shlex.quote(a) for a in inner) + " < /host/voice/lines/_text.txt"
            p = C.run(["proot-distro", "login", self.proot, "--bind", "%s:/host" % ROOT,
                       "--", "bash", "-lc", cmd], check=False)
        if p.returncode != 0 or not Path(out).exists() or Path(out).stat().st_size < 2000:
            raise RuntimeError("piper failed: %s" % ((p.stderr or "")[-400:]))


class Edge:
    name = "edge"; natural = True; offline = False

    def __init__(self):
        self.c = C.cfg()["tts"]["edge"]
        self.ok = C.run([sys.executable, "-c", "import edge_tts"], check=False).returncode == 0

    def available(self):
        return self.ok

    def synth(self, text, out, rate):
        pct = max(-40, min(60, int(round(self.c["rate_pct"] + (rate - 1.0) * 100))))
        mp3 = Path(str(out) + ".mp3"); last = ""
        _pitch = _signed(self.c.get("pitch", "0Hz"), "Hz")
        pargs = [] if _pitch == "+0Hz" else ["--pitch=%s" % _pitch]
        for voice in [self.c["voice"]] + list(self.c.get("alternates", [])):
            p = C.run([sys.executable, "-m", "edge_tts", "--voice", voice,
                       "--rate=%+d%%" % pct, *pargs,
                       "--text", text, "--write-media", str(mp3)], check=False, timeout=120)
            if p.returncode == 0 and mp3.exists() and mp3.stat().st_size > 1500:
                C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(mp3),
                       "-ar", str(C.cfg()["audio"]["voice_sr"]), "-ac", "1", "-c:a", "pcm_s16le", str(out)])
                mp3.unlink(missing_ok=True); C.log("edge voice: %s" % voice); return
            last = (p.stderr or "")[-300:]
        raise RuntimeError("edge-tts failed: %s" % last)


class Espeak:
    name = "espeak"; natural = False; offline = True

    def __init__(self):
        self.c = C.cfg()["tts"]["espeak"]
        self.bin = shutil.which("espeak-ng") or shutil.which("espeak")

    def available(self):
        return bool(self.bin)

    def synth(self, text, out, rate):
        TEXT_TMP.parent.mkdir(parents=True, exist_ok=True)
        TEXT_TMP.write_text(text, encoding="utf-8")
        speed = max(80, min(320, int(self.c["speed"] * rate)))
        p = C.run([self.bin, "-v", self.c["voice"], "-s", str(speed), "-p", str(self.c["pitch"]),
                   "-a", str(self.c["amplitude"]), "-f", str(TEXT_TMP), "-w", str(out)], check=False)
        if p.returncode != 0 or not Path(out).exists() or Path(out).stat().st_size < 2000:
            raise RuntimeError("espeak failed: %s" % ((p.stderr or "")[-300:]))


class Manual:
    name = "manual"; natural = True; offline = True

    def available(self):
        return MANUAL.exists() and any(MANUAL.glob("*.wav"))

    def synth(self, text, out, rate):
        raise RuntimeError("manual needs per-line files")


def pick_engine(name, offline_only):
    order = ["manual"] if name == "manual" else (C.cfg()["tts"]["engine_order"] if name == "auto" else [name])
    tried = []
    for n in order:
        cls = {"piper": Piper, "edge": Edge, "espeak": Espeak, "manual": Manual}.get(n)
        if cls is None:
            continue
        e = cls()
        if not e.available():
            tried.append("%s:غير متوفر" % n); continue
        if offline_only and not e.offline:
            tried.append("%s:offline مستبعد" % n); continue
        if not C.cfg()["tts"]["allow_online"] and not e.offline:
            tried.append("%s:allow_online=false" % n); continue
        C.log("TTS engine = %s (natural=%s offline=%s)" % (e.name, e.natural, e.offline))
        return e
    C.die("لا يوجد محرك صوت. جرّب: pkg install espeak  أو  pip install edge-tts")


def normalize(raw, out, sr):
    C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw),
           "-ar", str(sr), "-ac", "1", "-c:a", "pcm_s16le", str(out)])
    sr2, a = C.wav_read(out)
    a = C.trim(a, sr2)
    pk = C.peak(a)
    if pk < 900:
        raise RuntimeError("مقطع صامت (peak=%d)" % pk)
    g = min(3.0, 26000.0 / pk)
    C.wav_write(out, sr2, [v * g for v in a])
    return len(a) / float(sr2)


def synth_lines(scenes, engine, rate, sr):
    LINES.mkdir(parents=True, exist_ok=True)
    for sc in scenes:
        for li, ln in enumerate(sc["lines"]):
            key = hashlib.sha1(("%s|%s|%.3f|%s|%s" % (engine.name, ln["tts"], rate, sc["id"], json.dumps(C.cfg()["tts"], sort_keys=True, ensure_ascii=False))).encode()).hexdigest()[:10]
            final = LINES / ("%s_%02d_%s.wav" % (sc["id"], li, key))
            if final.exists() and final.stat().st_size > 2000:
                ln["dur"] = C.duration(final); ln["file"] = str(final); continue
            man = MANUAL / ("%s_%02d.wav" % (sc["id"], li))
            raw = LINES / ("raw_%s_%02d.wav" % (sc["id"], li))
            if man.exists():
                shutil.copyfile(str(man), str(raw)); C.log("manual: %s" % man.name)
            elif isinstance(engine, Manual):
                C.die("محرك manual: مفقود %s" % man)
            else:
                engine.synth(ln["tts"], raw, rate)
            ln["dur"] = normalize(raw, final, sr)
            ln["file"] = str(final); raw.unlink(missing_ok=True)
            C.log("  line %s/%02d = %.2fs" % (sc["id"], li, ln["dur"]))


def assemble(scenes, fps):
    A = C.cfg()["audio"]; sr = int(A["voice_sr"])
    cursor = 0.0
    for i, sc in enumerate(scenes):
        vis = cursor
        cursor = C.snap(cursor + (A["head"] if i == 0 else A["scene_gap"]), fps)
        for j, ln in enumerate(sc["lines"]):
            if j:
                cursor = C.snap(cursor + A["line_gap"], fps)
            ln["start"] = round(cursor, 6); cursor += ln["dur"]; ln["end"] = round(cursor, 6)
        if i == len(scenes) - 1:
            cursor = C.snap(cursor + A["tail"], fps)
        span = C.snap(cursor - vis, fps); cursor = round(vis + span, 6)
        sc["visual_start"] = round(vis, 6); sc["span"] = round(span, 6)
        sc["frames"] = int(round(span * fps))
    total = round(cursor, 6)
    buf = C.silence(sr, total + 0.05)
    for sc in scenes:
        for ln in sc["lines"]:
            _, a = C.wav_read(ln["file"])
            i0 = int(ln["start"] * sr)
            for k, v in enumerate(a):
                j = i0 + k
                if j < len(buf):
                    buf[j] = v
    C.wav_write(C.VOICE / "voice.wav", sr, buf[:int(total * sr)])
    tl = {"total": total, "fps": fps, "sample_rate": sr, "synthetic": False, "scenes": scenes}
    (C.VOICE / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    return total


def dry_timeline(scenes, fps):
    A = C.cfg()["audio"]; cursor = 0.0
    for i, sc in enumerate(scenes):
        vis = cursor
        cursor = C.snap(cursor + (A["head"] if i == 0 else A["scene_gap"]), fps)
        for j, ln in enumerate(sc["lines"]):
            if j:
                cursor = C.snap(cursor + A["line_gap"], fps)
            ln["dur"] = round(0.42 * len(ln["tts"].split()) + 0.30, 3)
            ln["start"] = round(cursor, 6); cursor += ln["dur"]; ln["end"] = round(cursor, 6)
        if i == len(scenes) - 1:
            cursor = C.snap(cursor + A["tail"], fps)
        span = C.snap(cursor - vis, fps); cursor = round(vis + span, 6)
        sc["visual_start"] = round(vis, 6); sc["span"] = round(span, 6)
        sc["frames"] = int(round(span * fps))
    tl = {"total": round(cursor, 6), "fps": fps, "sample_rate": int(A["voice_sr"]),
          "synthetic": True, "scenes": scenes}
    (C.VOICE / "timeline.dry.json").write_text(json.dumps(tl, ensure_ascii=False, indent=1), encoding="utf-8")
    return tl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", default="auto", choices=["auto", "piper", "edge", "espeak", "manual"])
    ap.add_argument("--offline", action="store_true"); ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-timeline", action="store_true"); ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()
    C.need("ffmpeg"); C.need("ffprobe")
    scenes = S.parse_script(); W, H, fps = C.dims(a.preview)
    if a.dry_timeline:
        tl = dry_timeline(scenes, fps); C.log("DRY timeline %.2fs (تقدير)" % tl["total"]); return
    D = C.cfg()["duration"]; sr = int(C.cfg()["audio"]["voice_sr"])
    tlp = C.VOICE / "timeline.json"; vp = C.VOICE / "voice.wav"
    if tlp.exists() and vp.exists() and not a.force:
        tl = json.loads(tlp.read_text(encoding="utf-8"))
        if D["min"] <= tl["total"] <= D["max"] and tl.get("fps") == fps:
            C.log("VOICE موجود (%.2fs) — تخطي" % tl["total"]); return
    engine = pick_engine(a.engine, a.offline)
    rate = 1.0; total = None
    for attempt in range(1, 5):
        C.log("TTS attempt %d rate=%.3f" % (attempt, rate))
        synth_lines(scenes, engine, rate, sr)
        total = assemble(scenes, fps)
        C.log("TOTAL = %.2fs" % total)
        if D["min"] <= total <= D["max"]:
            break
        speech = sum(ln["dur"] for sc in scenes for ln in sc["lines"])
        fixed = max(0.5, total - speech)
        want = max(10.0, D["target"] - fixed)
        rate = max(0.72, min(1.45, rate * (speech / want)))
        if attempt == 4:
            C.die("تعذّر ضبط المدة 45–60s (الناتج %.2fs)" % total)
    if not engine.natural:
        C.log("تحذير: الصوت آلي النبرة. للطبيعي: pip install edge-tts ثم --force-voice", "WARN")
    if C.peak(C.wav_read(vp)[1]) < 1500:
        C.die("voice.wav شبه صامت — فشل TTS")
    C.log("VOICE OK %.2fs engine=%s" % (total, engine.name))


if __name__ == "__main__":
    main()
