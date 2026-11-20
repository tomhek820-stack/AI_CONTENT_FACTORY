"""ترجمة عربية: SRT + شرائح PNG مشكولة RTL (بديل drawtext)."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from engine import common as C


def sub_file(i, W):
    return C.IMG / ("sub_%02d_%d.png" % (i, W))


def ts(t):
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def cues(tl):
    return [{"start": ln["start"], "end": ln["end"], "text": ln["screen"], "hl": ln.get("hl", [])}
            for sc in tl["scenes"] for ln in sc["lines"]]


def write_srt(tl, path):
    cs = cues(tl)
    body = ["%d\n%s --> %s\n%s\n" % (i, ts(c["start"]), ts(c["end"]), c["text"])
            for i, c in enumerate(cs, 1)]
    Path(path).write_text("\n".join(body), encoding="utf-8")
    C.log("SRT: %d cues" % len(cs))
    return cs


def render_pngs(tl, preview=False):
    from PIL import Image, ImageDraw
    W, H, fps = C.dims(preview)
    b = C.cfg()["brand"]; L = C.cfg()["layout"]
    maxw = W - 2 * C.scale(L["safe_margin"], W)
    pen = C.ArabicPen(C.resolve_font(verbose=False), C.scale(L["sub_font"], W), stroke=1)
    bottom = int(H * (L["sub_bottom"] / 1920.0))
    meta = []
    for i, c in enumerate(cues(tl)):
        lines = pen.wrap(c["text"], maxw - C.scale(72, W), max_lines=2)
        imgs = [pen.line_img(l, C.hex2rgb(b["white"]) + (255,), c["hl"],
                             C.hex2rgb(b["electric"]) + (255,)) for l in lines]
        padx, pady, gap = C.scale(34, W), C.scale(22, W), C.scale(6, W)
        bw = min(W - 2 * C.scale(30, W), max(im.width for im in imgs) + 2 * padx)
        bh = sum(im.height for im in imgs) + gap * (len(imgs) - 1) + 2 * pady
        box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); d = ImageDraw.Draw(box)
        d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=C.scale(26, W),
                            fill=(5, 9, 16, 205), outline=C.hex2rgb(b["blue"]) + (120,), width=2)
        d.rectangle([bw - C.scale(9, W), C.scale(16, W), bw - C.scale(4, W), bh - C.scale(16, W)],
                    fill=C.hex2rgb(b["electric"]) + (230,))
        y = pady
        for im in imgs:
            box.alpha_composite(im, ((bw - im.width) // 2, y)); y += im.height + gap
        p = sub_file(i, W); box.save(str(p), "PNG", compress_level=3)
        meta.append({"index": i, "file": str(p), "w": bw, "h": bh,
                     "y": max(0, bottom - bh), "start": c["start"], "end": c["end"]})
    (C.OUT / "subtitles_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    C.log("SUB PNG: %d strips" % len(meta))
    return meta


def build(preview=False, srt_only=False):
    p = C.VOICE / ("timeline.dry.json" if srt_only else "timeline.json")
    if not p.exists():
        C.die("غير موجود: %s" % p)
    tl = json.loads(p.read_text(encoding="utf-8"))
    write_srt(tl, C.ROOT / "scripts" / "subtitles.srt")
    if not srt_only:
        render_pngs(tl, preview)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true"); ap.add_argument("--srt-only", action="store_true")
    a = ap.parse_args(); build(a.preview, a.srt_only)
