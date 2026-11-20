"""أدوات مشتركة: إعدادات، سجلات، أوامر، WAV، تشكيل عربي وRTL، خطوط."""
from __future__ import annotations
import array, datetime, json, math, os, re, shlex, shutil, subprocess, sys, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
IMG = ROOT / "assets" / "images"
BG = ROOT / "assets" / "backgrounds"
FONTS = ROOT / "assets" / "fonts"
MUSIC = ROOT / "assets" / "music"
OUT = ROOT / "output"
VOICE = ROOT / "voice"
_CFG = None


def cfg():
    global _CFG
    if _CFG is None:
        _CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    return _CFG


def log(msg, level="INFO"):
    LOGS.mkdir(parents=True, exist_ok=True)
    line = "[%s][%s] %s" % (datetime.datetime.now().strftime("%H:%M:%S"), level, msg)
    print(line, flush=True)
    with (LOGS / "engine.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def die(msg, code=1):
    log(msg, "ERROR")
    raise SystemExit(code)


def need(name):
    p = shutil.which(name)
    if not p:
        die("Executable مفقود: %s" % name)
    return p


def run(cmd, capture=True, check=True, timeout=None, input_text=None):
    cmd = [str(c) for c in cmd]
    log("EXEC " + " ".join(cmd)[:500])
    try:
        p = subprocess.run(cmd, input=input_text, stdin=(None if input_text is not None else subprocess.DEVNULL),
                           stdout=subprocess.PIPE if capture else None,
                           stderr=subprocess.PIPE if capture else None,
                           text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        die("Timeout (%ss): %s" % (timeout, cmd[0]))
    if capture and p.stderr:
        LOGS.mkdir(parents=True, exist_ok=True)
        with (LOGS / "ffmpeg.log").open("a", encoding="utf-8") as f:
            f.write("$ " + " ".join(cmd)[:500] + "\n" + p.stderr[-6000:] + "\n")
    if check and p.returncode != 0:
        if capture:
            log(((p.stderr or "") + (p.stdout or ""))[-2500:], "ERROR")
        die("Command failed (%d): %s" % (p.returncode, " ".join(cmd)[:220]))
    return p


def ffprobe_json(path):
    p = run(["ffprobe", "-v", "error", "-print_format", "json",
             "-show_format", "-show_streams", str(path)])
    return json.loads(p.stdout)


def duration(path):
    return float(ffprobe_json(path)["format"]["duration"])


def wav_read(path):
    with wave.open(str(path), "rb") as w:
        ch, sw, sr, n = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        die("WAV يجب أن يكون 16-bit: %s" % path)
    a = array.array("h"); a.frombytes(raw)
    if sys.byteorder != "little":
        a.byteswap()
    if ch > 1:
        m = len(a) // ch
        mono = array.array("h", bytes(2 * m))
        for i in range(m):
            s = 0
            for c in range(ch):
                s += a[i * ch + c]
            mono[i] = int(s / ch)
        a = mono
    return sr, a


def wav_write(path, sr, samples, channels=1):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    b = array.array("h", [max(-32767, min(32767, int(v))) for v in samples])
    if sys.byteorder != "little":
        b.byteswap()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(b.tobytes())


def wav_write_stereo(path, sr, left, right):
    n = min(len(left), len(right))
    inter = array.array("h", bytes(4 * n))
    for i in range(n):
        inter[2 * i] = max(-32767, min(32767, int(left[i])))
        inter[2 * i + 1] = max(-32767, min(32767, int(right[i])))
    if sys.byteorder != "little":
        inter.byteswap()
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(inter.tobytes())


def silence(sr, seconds):
    return array.array("h", bytes(2 * max(0, int(round(sr * seconds)))))


def peak(a):
    return max(abs(min(a)), abs(max(a))) if len(a) else 0


def rms(a):
    if not len(a):
        return 0.0
    step = max(1, len(a) // 150000)
    s = c = 0
    for v in a[::step]:
        s += v * v; c += 1
    return math.sqrt(s / max(1, c))


def trim(a, sr, thresh=320, pad=0.05):
    n = len(a)
    if n == 0:
        return a
    win = max(1, int(sr * 0.02))
    first, last = 0, n
    i = 0
    while i < n:
        seg = a[i:i + win]
        if len(seg) and max(abs(min(seg)), abs(max(seg))) > thresh:
            first = i; break
        i += win
    i = max(0, n - win)
    while i > 0:
        seg = a[i:i + win]
        if len(seg) and max(abs(min(seg)), abs(max(seg))) > thresh:
            last = min(n, i + win); break
        i -= win
    p = int(sr * pad)
    out = a[max(0, first - p):min(n, last + p)]
    return out if len(out) else a


TASHKEEL = re.compile("[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]")
AR_PUNCT = "،؛؟:!.,\"'()[]«»—-…"


def strip_tashkeel(t):
    return TASHKEEL.sub("", t)


def norm_word(t):
    return strip_tashkeel(t).strip(AR_PUNCT).strip().lower()


_FORMS_RAW = (
    "ء FE80 0 0 0|آ FE81 FE82 0 0|أ FE83 FE84 0 0|ؤ FE85 FE86 0 0|إ FE87 FE88 0 0|"
    "ئ FE89 FE8A FE8B FE8C|ا FE8D FE8E 0 0|ب FE8F FE90 FE91 FE92|ة FE93 FE94 0 0|"
    "ت FE95 FE96 FE97 FE98|ث FE99 FE9A FE9B FE9C|ج FE9D FE9E FE9F FEA0|ح FEA1 FEA2 FEA3 FEA4|"
    "خ FEA5 FEA6 FEA7 FEA8|د FEA9 FEAA 0 0|ذ FEAB FEAC 0 0|ر FEAD FEAE 0 0|ز FEAF FEB0 0 0|"
    "س FEB1 FEB2 FEB3 FEB4|ش FEB5 FEB6 FEB7 FEB8|ص FEB9 FEBA FEBB FEBC|ض FEBD FEBE FEBF FEC0|"
    "ط FEC1 FEC2 FEC3 FEC4|ظ FEC5 FEC6 FEC7 FEC8|ع FEC9 FECA FECB FECC|غ FECD FECE FECF FED0|"
    "ف FED1 FED2 FED3 FED4|ق FED5 FED6 FED7 FED8|ك FED9 FEDA FEDB FEDC|ل FEDD FEDE FEDF FEE0|"
    "م FEE1 FEE2 FEE3 FEE4|ن FEE5 FEE6 FEE7 FEE8|ه FEE9 FEEA FEEB FEEC|و FEED FEEE 0 0|"
    "ى FEEF FEF0 0 0|ي FEF1 FEF2 FEF3 FEF4"
)
FORMS = {}
for _p in _FORMS_RAW.split("|"):
    _f = _p.split()
    FORMS[_f[0]] = tuple(int(x, 16) if x != "0" else 0 for x in _f[1:])
_LAMALEF = {"ا": (0xFEFB, 0xFEFC), "أ": (0xFEF7, 0xFEF8),
            "إ": (0xFEF9, 0xFEFA), "آ": (0xFEF5, 0xFEF6)}

try:
    import arabic_reshaper as _reshaper
except Exception:
    _reshaper = None


def _reshape_fb(text):
    out = []; i = 0; n = len(text); prev_join = False
    while i < n:
        c = text[i]
        if c not in FORMS:
            out.append(c); prev_join = False; i += 1; continue
        right = prev_join
        if c == "ل" and i + 1 < n and text[i + 1] in _LAMALEF:
            iso, fin = _LAMALEF[text[i + 1]]
            out.append(chr(fin if right else iso))
            i += 2; prev_join = False; continue
        nxt = text[i + 1] if i + 1 < n else ""
        left = nxt in FORMS and (FORMS[nxt][1] or FORMS[nxt][3])
        iso, fin, ini, med = FORMS[c]
        if right and left:
            f = med or fin or iso
        elif right:
            f = fin or iso
        elif left:
            f = ini or iso
        else:
            f = iso
        out.append(chr(f)); prev_join = bool(ini); i += 1
    return "".join(out)


_RS_CACHE = {}


def reshape(t):
    if _reshaper is not None:
        try:
            lig = bool(cfg()["font"].get("ligatures", True))
        except Exception:
            lig = True
        if lig not in _RS_CACHE:
            try:
                _RS_CACHE[lig] = _reshaper.ArabicReshaper(
                    configuration={"support_ligatures": lig, "delete_harakat": False})
            except Exception:
                _RS_CACHE[lig] = None
        r = _RS_CACHE[lig]
        try:
            return r.reshape(t) if r is not None else _reshaper.reshape(t)
        except Exception:
            pass
    return _reshape_fb(t)


SYSTEM_FONTS = [
    "/system/fonts/NotoNaskhArabic-Regular.ttf",
    "/system/fonts/NotoSansArabic-Regular.ttf",
    "/system/fonts/NotoNaskhArabicUI-Regular.ttf",
    "/system/fonts/NotoSansArabicUI-Regular.ttf",
    "/system/fonts/NotoSansArabic-VF.ttf",
    "/system/fonts/DroidNaskh-Regular.ttf",
]
RANK = ["cairo", "notokufi", "notosansarabic", "notonaskh", "amiri", "droid"]


def _rank(p):
    n = p.name.lower()
    for i, k in enumerate(RANK):
        if k in n:
            return i
    return len(RANK)


def font_candidates(bold=False):
    c = cfg()
    ov = c["font"]["bold_override" if bold else "override"]
    out = []
    if ov and Path(ov).exists():
        out.append(Path(ov))
    local = sorted(FONTS.glob("*.ttf"), key=_rank) + sorted(FONTS.glob("*.otf"), key=_rank)
    if bold:
        local = [p for p in local if "bold" in p.name.lower()] + [p for p in local if "bold" not in p.name.lower()]
    out += local
    out += [Path(p) for p in SYSTEM_FONTS if Path(p).exists()]
    pref = Path(os.environ.get("PREFIX", "/data/data/com.termux/files/usr"))
    if (pref / "share" / "fonts").exists():
        out += sorted((pref / "share" / "fonts").rglob("*.ttf"))
    seen = set(); uniq = []
    for p in out:
        if str(p) not in seen:
            seen.add(str(p)); uniq.append(p)
    return uniq


def font_has_arabic_forms(path, size=44):
    from PIL import Image, ImageDraw, ImageFont
    try:
        f = ImageFont.truetype(str(path), size)
    except Exception:
        return False
    def render(ch):
        im = Image.new("L", (120, 120), 0)
        ImageDraw.Draw(im).text((5, 5), ch, font=f, fill=255)
        return im.tobytes(), im.getbbox()
    a, ba = render("\uFE91")
    b, bb = render("\uE123")
    return ba is not None and a != b


def resolve_font(bold=False, verbose=True):
    from PIL import features
    raqm = features.check("raqm")
    cands = font_candidates(bold)
    if not cands:
        die("لا يوجد أي خط. ضع ملف .ttf عربي في assets/fonts/")
    for p in cands:
        if raqm or font_has_arabic_forms(p):
            if verbose:
                log("FONT %s -> %s (raqm=%s)" % ("bold" if bold else "regular", p, raqm))
            return str(p)
    die("الخطوط تفتقد أشكال الوصل العربية. pkg install libraqm أو ضع Amiri-Regular.ttf")



_MIRROR = {"(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{",
           "<": ">", ">": "<", "\u00ab": "\u00bb", "\u00bb": "\u00ab"}
_AR_RE = re.compile("[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
_EDGE_PUNCT = ":!?.\u060c\u061b\u061f,"


def mirror_reverse(s):
    return "".join(_MIRROR.get(ch, ch) for ch in reversed(s))


def prep_visual(token, raqm, rtl=True):
    """ترتيب بصري صحيح عند غياب raqm: عكس الحروف العربية فقط."""
    t = strip_tashkeel(token)
    if not rtl:
        return t
    if not _AR_RE.search(t):
        core = t.rstrip(_EDGE_PUNCT)
        tail = t[len(core):]
        return (tail + core) if core else t
    if raqm:
        return t
    return mirror_reverse(reshape(t))


class ArabicPen:
    """رسم عربي صحيح: تشكيل + ترتيب RTL يدوي + تلوين كلمات مفتاحية."""

    def __init__(self, font_path, size, bold=False, stroke=0):
        from PIL import Image, ImageDraw, ImageFont, features
        self.Image, self.ImageDraw = Image, ImageDraw
        self.size = int(size); self.stroke = int(stroke)
        self.font = ImageFont.truetype(str(font_path), int(size))
        self.raqm = features.check("raqm")
        if bold:
            try:
                names = [n.decode() if isinstance(n, bytes) else str(n)
                         for n in (self.font.get_variation_names() or [])]
                for want in ("Bold", "SemiBold", "Medium"):
                    if want in names:
                        self.font.set_variation_by_name(want); break
            except Exception:
                pass
        self.ascent, self.descent = self.font.getmetrics()
        self.padv = int(size * 0.30); self.padh = int(size * 0.14)
        self.line_h = self.ascent + self.descent + 2 * self.padv
        self.space_w = max(4.0, self.font.getlength(" "))

    def _kw(self, rtl=True):
        if self.raqm:
            return {"direction": "rtl" if rtl else "ltr", "language": "ar"}
        return {}

    def _prep(self, token, rtl=True):
        return prep_visual(token, self.raqm, rtl)

    def token_width(self, token, rtl=True):
        s = self._prep(token, rtl)
        try:
            return self.font.getlength(s, **self._kw(rtl)) + 2 * self.padh + 2 * self.stroke
        except Exception:
            return self.font.getlength(s) + 2 * self.padh

    def token_img(self, token, fill, rtl=True):
        s = self._prep(token, rtl)
        w = int(math.ceil(self.token_width(token, rtl))) + 2
        im = self.Image.new("RGBA", (max(2, w), self.line_h), (0, 0, 0, 0))
        d = self.ImageDraw.Draw(im)
        d.text((self.padh, self.padv), s, font=self.font, fill=fill,
               stroke_width=self.stroke, stroke_fill=fill, **self._kw(rtl))
        return im

    def line_width(self, text, rtl=True):
        toks = text.split()
        if not toks:
            return 0.0
        return sum(self.token_width(t, rtl) for t in toks) + self.space_w * (len(toks) - 1)

    def wrap(self, text, max_w, rtl=True, max_lines=2):
        words = text.split(); lines = []; cur = []
        for w in words:
            trial = " ".join(cur + [w])
            if cur and self.line_width(trial, rtl) > max_w:
                lines.append(" ".join(cur)); cur = [w]
            else:
                cur.append(w)
        if cur:
            lines.append(" ".join(cur))
        if len(lines) > max_lines:
            head = lines[:max_lines - 1]
            head.append(" ".join(" ".join(lines[max_lines - 1:]).split()[:14]))
            lines = head
        return lines

    def line_img(self, text, fill, hl=(), hl_fill=None, rtl=True, max_w=None):
        toks = text.split()
        hlset = {norm_word(x) for x in hl}
        imgs = []
        for t in toks:
            is_hl = norm_word(t) in hlset and hl_fill is not None
            imgs.append(self.token_img(t, hl_fill if is_hl else fill, rtl))
        total = int(math.ceil(sum(i.width for i in imgs) + self.space_w * max(0, len(imgs) - 1)))
        im = self.Image.new("RGBA", (max(2, total), self.line_h), (0, 0, 0, 0))
        x = total
        for i in imgs:
            x -= i.width
            im.alpha_composite(i, (max(0, x), 0))
            x -= int(self.space_w)
        return im

    def latin_img(self, text, fill):
        return self.token_img(text, fill, rtl=False)


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def snap(x, fps):
    return round(float(x) * fps) / float(fps)


def dims(preview=False):
    c = cfg()
    if preview:
        p = c["preview"]
        return int(p["width"]), int(p["height"]), int(p["fps"])
    return int(c["width"]), int(c["height"]), int(c["fps"])


def scale(v, W):
    return int(round(v * (W / 1080.0)))
