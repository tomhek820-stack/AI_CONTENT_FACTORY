"""كاريوكي عربي: كل كلمة تضيء بلحظة نطقها مع تلوين تدرجي وشريط تقدم."""
from __future__ import annotations
import json, math
from pathlib import Path
from engine import common as C


def sub_frame_file(cue_idx, frame_idx, W):
    return C.IMG / ("sub_k_%02d_%03d_%d.png" % (cue_idx, frame_idx, W))


def ts(t):
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def word_timings(cue, total_words):
    """تقسيم مدة الجملة على الكلمات (طريقة بسيطة وموثوقة)."""
    dur = cue["end"] - cue["start"]
    if total_words <= 1:
        return [(cue["start"], cue["end"])]
    per = dur / total_words
    return [(cue["start"] + i * per, cue["start"] + (i + 1) * per) for i in range(total_words)]


def render_karaoke_frames(timeline, preview=False):
    from PIL import Image, ImageDraw
    W, H, fps = C.dims(preview)
    b = C.cfg()["brand"]
    L = C.cfg()["layout"]
    maxw = W - 2 * C.scale(L["safe_margin"], W)

    col_done = C.hex2rgb(b["muted"]) + (220,)      # كلمات منطوقة
    col_now = C.hex2rgb(b["electric"]) + (255,)    # الكلمة الحالية
    col_next = C.hex2rgb(b["white"]) + (95,)       # كلمات قادمة
    col_hl = C.hex2rgb(b["electric"]) + (255,)     # كلمات مفتاحية (دائمًا ساطعة)

    f = C.resolve_font(verbose=False)
    pen = C.ArabicPen(f, C.scale(L["sub_font"], W), stroke=1)
    bottom = int(H * (L["sub_bottom"] / 1920.0))

    meta = []
    all_cues = []
    for sc in timeline["scenes"]:
        for ln in sc["lines"]:
            all_cues.append({
                "start": ln["start"], "end": ln["end"],
                "text": ln["screen"], "hl": ln.get("hl", []),
                "scene_kind": sc.get("kind", ""),
            })

    for cue_i, cue in enumerate(all_cues):
        words = cue["text"].split()
        if not words:
            continue
        hlset = {C.norm_word(x) for x in cue["hl"]}
        timings = word_timings(cue, len(words))
        frames_for_cue = []

        # إطار واحد لكل كلمة + إطار نهائي
        for frame_i in range(len(words) + 1):
            imgs = []
            for w_i, w in enumerate(words):
                is_hl = C.norm_word(w) in hlset
                if w_i < frame_i:
                    col = col_hl if is_hl else col_done
                elif w_i == frame_i:
                    col = col_now
                else:
                    col = col_next
                imgs.append(pen.token_img(w, col))

            sp = int(pen.space_w)
            total_w = sum(i.width for i in imgs) + sp * max(0, len(imgs) - 1)
            line_h = max(i.height for i in imgs) if imgs else pen.line_h
            word_img = Image.new("RGBA", (max(2, total_w), line_h), (0, 0, 0, 0))
            x = total_w
            for i in imgs:
                x -= i.width
                word_img.alpha_composite(i, (max(0, x), (line_h - i.height) // 2))
                x -= sp

            # صندوق كامل مع شريط تقدم
            padx, pady = C.scale(34, W), C.scale(22, W)
            bw = min(W - 2 * C.scale(30, W), word_img.width + 2 * padx)
            bh = word_img.height + 2 * pady + C.scale(14, W)
            box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
            d = ImageDraw.Draw(box)
            d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=C.scale(26, W),
                                fill=(5, 9, 16, 215),
                                outline=C.hex2rgb(b["blue"]) + (130,),
                                width=2)
            d.rectangle([bw - C.scale(9, W), C.scale(16, W),
                         bw - C.scale(4, W), bh - C.scale(16, W)],
                        fill=C.hex2rgb(b["electric"]) + (230,))

            # شريط تقدم
            progress = frame_i / len(words) if words else 0
            bar_y = bh - C.scale(9, W)
            d.rectangle([C.scale(20, W), bar_y, bw - C.scale(20, W), bar_y + C.scale(4, W)],
                        fill=(40, 60, 90, 180))
            pw = int((bw - 2 * C.scale(20, W)) * progress)
            if pw > 0:
                d.rectangle([C.scale(20, W), bar_y,
                             C.scale(20, W) + pw, bar_y + C.scale(4, W)],
                            fill=C.hex2rgb(b["electric"]) + (255,))

            # موضع النص (يمين إلى يسار)
            box.alpha_composite(word_img,
                                ((bw - word_img.width) // 2, pady))

            # حفظ الإطار
            p = sub_frame_file(cue_i, frame_i, W)
            box.save(str(p), "PNG", compress_level=3)

            # توقيت الإطار
            if frame_i < len(words):
                fr_start = timings[frame_i][0]
                fr_end = timings[frame_i][1]
            else:
                fr_start = cue["end"]
                fr_end = cue["end"] + 0.05

            frames_for_cue.append({
                "frame": frame_i,
                "file": str(p),
                "w": bw, "h": bh,
                "y": max(0, bottom - bh),
                "start": fr_start,
                "end": fr_end,
            })

        meta.append({
            "cue": cue_i,
            "text": cue["text"],
            "kind": cue.get("scene_kind", ""),
            "frames": frames_for_cue,
        })

    (C.OUT / "karaoke_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    total_frames = sum(len(m["frames"]) for m in meta)
    C.log("KARAOKE: %d cues -> %d frames (كلمة كلمة)" % (len(meta), total_frames))
    return meta


def build(preview=False):
    tl_path = C.VOICE / "timeline.json"
    if not tl_path.exists():
        C.die("timeline.json مفقود — شغّل توليد الصوت أولاً")
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    render_karaoke_frames(tl, preview)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    build(ap.parse_args().preview)
