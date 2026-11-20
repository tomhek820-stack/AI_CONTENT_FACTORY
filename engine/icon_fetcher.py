"""يجلب أيقونات من Iconify (SVG) + يحوّلها PNG + كاش.
   Iconify يدعم SVG فقط: /{prefix}/{name}.svg
   التحويل عبر rsvg-convert (librsvg)."""
from __future__ import annotations
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "assets" / "icons" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36"
)

CDN_HOSTS = [
    "https://api.iconify.design",
    "https://api.simplesvg.com",
    "https://api.unisvg.com",
]

ICON_MAP = {
    # Brand icons (ألوان أصلية من simple-icons)
    "android":   {"icon": "simple-icons:android", "brand": True},
    "python":    {"icon": "simple-icons:python",  "brand": True},
    "git":       {"icon": "simple-icons:git",     "brand": True},
    "github":    {"icon": "simple-icons:github",  "brand": True},
    "chatgpt":   {"icon": "simple-icons:openai",  "brand": True},
    "whatsapp":  {"icon": "simple-icons:whatsapp","brand": True},
    "youtube":   {"icon": "simple-icons:youtube", "brand": True},
    "instagram": {"icon": "simple-icons:instagram","brand": True},

    # Concept icons (monochrome، تلوّن turquoise)
    "settings":  {"icon": "mdi:cog",              "brand": False},
    "battery":   {"icon": "mdi:battery-high",     "brand": False},
    "storage":   {"icon": "mdi:harddisk",         "brand": False},
    "rocket":    {"icon": "mdi:rocket-launch",    "brand": False},
    "search":    {"icon": "mdi:magnify",          "brand": False},
    "terminal":  {"icon": "mdi:console",          "brand": False},
    "design":    {"icon": "mdi:palette",          "brand": False},
    "video":     {"icon": "mdi:video",            "brand": False},
    "chat":      {"icon": "mdi:chat",             "brand": False},
    "speed":     {"icon": "mdi:speedometer",      "brand": False},
    "update":    {"icon": "mdi:refresh",          "brand": False},
    "lock":      {"icon": "mdi:lock",             "brand": False},
    "shield":    {"icon": "mdi:shield-check",     "brand": False},
    "wifi":      {"icon": "mdi:wifi",             "brand": False},
    "bluetooth": {"icon": "mdi:bluetooth",        "brand": False},
    "bell":      {"icon": "mdi:bell",             "brand": False},
    "camera":    {"icon": "mdi:camera",           "brand": False},
    "music":     {"icon": "mdi:music",            "brand": False},
    "folder":    {"icon": "mdi:folder",           "brand": False},
    "file":      {"icon": "mdi:file",             "brand": False},
    "alert":     {"icon": "mdi:alert",            "brand": False},
    "check":     {"icon": "mdi:check-circle",     "brand": False},
    "close":     {"icon": "mdi:close-circle",     "brand": False},
    "key":       {"icon": "mdi:key",              "brand": False},
    "account":   {"icon": "mdi:account",          "brand": False},
}


def _cache_key(icon_id: str, color: str | None, size: int) -> str:
    safe = icon_id.replace(":", "_").replace("/", "_")
    c = color.replace("#", "") if color else "orig"
    return f"{safe}_{c}_{size}.png"


def _http_get(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "image/svg+xml,image/*;q=0.9,*/*;q=0.5",
    })
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _svg_to_png(svg_bytes: bytes, size: int, color: str | None) -> bytes:
    """يحول SVG إلى PNG عبر rsvg-convert."""
    # نعدّل لون SVG إن طُلب (Iconify يدعم color parameter، لكن للأمان)
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
        f.write(svg_bytes)
        tmp_svg = f.name

    tmp_png = tmp_svg.replace(".svg", ".png")
    try:
        cmd = [
            "rsvg-convert",
            "-w", str(size), "-h", str(size),
            "-o", tmp_png,
            tmp_svg,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            raise RuntimeError(f"rsvg-convert failed: {r.stderr[:500]}")

        with open(tmp_png, "rb") as f:
            png_bytes = f.read()

        # تحقق PNG
        if png_bytes[:8] != b"\x89PNG\r\n\x1a\n":
            raise RuntimeError("rsvg-convert output is not PNG")

        return png_bytes
    finally:
        for p in (tmp_svg, tmp_png):
            try:
                os.unlink(p)
            except OSError:
                pass


def _try_fetch_svg(icon_id: str, color: str | None) -> bytes:
    prefix, _, name = icon_id.partition(":")
    if not name:
        prefix, name = "mdi", icon_id

    # الصيغة الصحيحة: /{prefix}/{name}.svg  (وليس .png)
    path = f"/{prefix}/{name}.svg"
    if color:
        path += f"?color={color.replace('#', '%23')}"

    last_error = None
    for host in CDN_HOSTS:
        url = host + path
        try:
            data = _http_get(url)
            if b"<svg" in data[:500] or b"<?xml" in data[:500]:
                return data
            last_error = f"non-SVG response from {url}"
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code} from {url}"
        except Exception as e:
            last_error = f"{type(e).__name__}: {e} from {url}"

    raise RuntimeError(f"all CDNs failed for {icon_id}. Last: {last_error}")


def fetch(name: str, size: int = 256, color: str | None = None) -> Image.Image:
    entry = ICON_MAP.get(name.lower())
    if entry is None:
        icon_id = f"mdi:{name}"
        is_brand = False
    else:
        icon_id = entry["icon"]
        is_brand = entry.get("brand", False)

    if not is_brand and color is None:
        color = "#0FB5A8"  # turquoise

    cache_name = _cache_key(icon_id, color, size)
    cache_path = CACHE / cache_name

    if not cache_path.exists():
        svg_bytes = _try_fetch_svg(icon_id, color)
        png_bytes = _svg_to_png(svg_bytes, size, color)
        cache_path.write_bytes(png_bytes)

    return Image.open(str(cache_path)).convert("RGBA")


def fetch_to_file(name: str, size: int = 256, color: str | None = None,
                  out_path: Path | None = None) -> Path:
    img = fetch(name, size=size, color=color)
    if out_path is None:
        entry = ICON_MAP.get(name.lower())
        icon_id = entry["icon"] if entry else f"mdi:{name}"
        if not (entry and entry.get("brand")) and color is None:
            color = "#0FB5A8"
        out_path = CACHE / _cache_key(icon_id, color, size)
    img.save(str(out_path), "PNG", optimize=True)
    return out_path


if __name__ == "__main__":
    names = ("settings", "battery", "storage", "rocket", "android")
    ok, fail = 0, 0
    for name in names:
        try:
            p = fetch_to_file(name, size=256)
            print(f"✅ {name}: {p.name} ({p.stat().st_size // 1024} KB)")
            ok += 1
        except Exception as e:
            print(f"❌ {name}: {e}")
            fail += 1
    print(f"\n{ok}/{len(names)} نجحت")
