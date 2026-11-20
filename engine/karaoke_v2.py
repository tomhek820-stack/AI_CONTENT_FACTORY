"""كاريوكي محسّن: مقاطع قصيرة 3-6 كلمات، سطرين، خط أكبر، تلوين الكلمة الحالية."""
from __future__ import annotations
import json, math
from pathlib import Path
from engine import common as C


def sub_frame_file(cue_idx, seg_idx, W):
    return C.IMG / ("sub_v2_%02d_%03d_%d.png" % (cue_idx, seg_idx, W))


def split_into_segments(text, max_words=6, min_words=3):
    """تقسيم النص إلى مقاطع من 3-6 كلمات."""
    words = text.split()
    segments = []
    i = 0
    while i < len(words):
        remaining = len(words) - i
        if remaining <= max_words:
            segments.append(" ".join(words[i:]))
            break
        seg_len = min(max_words, max(min_words, remaining // 2))
        segments.append(" ".join(words[i:i + seg_len]))
        i += seg_len
    return segments


def ts(t):
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def render_karaoke_v2(timeline, preview=False):
    from PIL import Image, ImageDraw
    W, H, fps = C.dims(preview)
    b = C.cfg()["brand"]
    L = C.cfg()["layout"]

    # ألوان
    col_done = C.hex2rgb(b["muted"]) + (200,)
    col_now = C.hex2rgb(b["electric"]) + (255,)
    col_next = C.hex2rgb(b["white"]) + (90,)
    col_hl = C.hex2rgb(b["electric"]) + (255,)

    # خط أكبر (من 60 إلى 72)
    f = C.resolve_font(verbose=False)
    font_size = C.scale(72, W)  # أكبر
    pen = C.ArabicPen(f, font_size, stroke=2)
    bottom = int(H * 0.78)  # أعلى قليلاً لتجنب واجهة المنصة

    meta = []
    all_cues = []
    for sc in timeline["scenes"]:
        for ln in sc["lines"]:
            all_cues.append({
                "start": ln["start"], "end": ln["end"],
                "text": ln["screen"], "hl": ln.get("hl", []),
            })

    for cue_i, cue in enumerate(all_cues):
        segments = split_into_segments(cue["text"], max_words=6, min_words=3)
        if not segments:
            continue

        hlset = {C.norm_word(x) for x in cue["hl"]}
        cue_dur = cue["end"] - cue["start"]
        seg_dur = cue_dur / len(segments)

        frames_for_cue = []

        for seg_i, seg_text in enumerate(segments):
            words = seg_text.split()
            word_dur = seg_dur / len(words) if words else seg_dur

            # إطار واحد لكل كلمة في المقطع
            for w_i, w in enumerate(words):
                is_hl = C.norm_word(w) in hlset

                # رسم المقطع الحالي مع تلوين الكلمة
                imgs = []
                for ww_i, ww in enumerate(words):
                    ww_is_hl = C.norm_word(ww) in hlset
                    if ww_i < w_i:
                        col = col_hl if ww_is_hl else col_done
                    elif ww_i == w_i:
                        col = col_now
                    else:
                        col = col_next
                    imgs.append(pen.token_img(ww, col))

                sp = int(pen.space_w * 1.2)
                line_w = sum(i.width for i in imgs) + sp * max(0, len(imgs) - 1)
                line_h = max(i.height for i in imgs) if imgs else pen.line_h

                # إذا كان المقطع أطول من العرض، نقسمه على سطرين
                max_line_w = W - 2 * C.scale(120, W)
                if line_w > max_line_w and len(words) > 3:
                    mid = len(words) // 2
                    line1_words = words[:mid]
                    line2_words = words[mid:]

                    def render_line(ws, active_idx, offset):
                        ls = []
                        for wi, ww in enumerate(ws):
                            idx = offset + wi
                            if idx < w_i:
                                col = col_hl if C.norm_word(ww) in hlset else col_done
                            elif idx == w_i:
                                col = col_now
                            else:
                                col = col_next
                            ls.append(pen.token_img(ww, col))
                        lw = sum(i.width for i in ls) + sp * max(0, len(ls) - 1)
                        lh = max(i.height for i in ls) if ls else pen.line_h
                        im = Image.new("RGBA", (max(2, lw), lh), (0, 0, 0, 0))
                        x = lw
                        for i in ls:
                            x -= i.width
                            im.alpha_composite(i, (max(0, x), (lh - i.height) // 2))
                            x -= sp
                        return im

                    img1 = render_line(line1_words, w_i, 0)
                    img2 = render_line(line2_words, w_i, mid)
                    line_h = img1.height + C.scale(10, W) + img2.height
                    line_w = max(img1.width, img2.width)

                    word_img = Image.new("RGBA", (line_w, line_h), (0, 0, 0, 0))
                    word_img.alpha_composite(img1, ((line_w - img1.width) // 2, 0))
                    word_img.alpha_composite(img2, ((line_w - img2.width) // 2, img1.height + C.scale(10, W)))
                else:
                    word_img = Image.new("RGBA", (max(2, line_w), line_h), (0, 0, 0, 0))
                    x = line_w
                    for i in imgs:
                        x -= i.width
                        word_img.alpha_composite(i, (max(0, x), (line_h - i.height) // 2))
                        x -= sp

                # صندوق
                padx, pady = C.scale(40, W), C.scale(28, W)
                bw = min(W - 2 * C.scale(60, W), word_img.width + 2 * padx)
                bh = word_img.height + 2 * pady
                box = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
                d = ImageDraw.Draw(box)
                d.rounded_rectangle([0, 0, bw - 1, bh - 1], radius=C.scale(30, W),
                                    fill=(5, 9, 16, 230),
                                    outline=C.hex2rgb(b["blue"]) + (140,),
                                    width=3)
                d.rectangle([bw - C.scale(10, W), C.scale(18, W),
                             bw - C.scale(4, W), bh - C.scale(18, W)],
                            fill=C.hex2rgb(b["electric"]) + (240,))

                # شريط تقدم
                progress = (seg_i * len(words) + w_i + 1) / (len(segments) * len(words))
                bar_y = bh - C.scale(10, W)
                d.rectangle([C.scale(24, W), bar_y, bw - C.scale(24, W), bar_y + C.scale(5, W)],
                            fill=(40, 60, 90, 180))
                pw = int((bw - 2 * C.scale(24, W)) * progress)
                if pw > 0:
                    d.rectangle([C.scale(24, W), bar_y,
                                 C.scale(24, W) + pw, bar_y + C.scale(5, W)],
                                fill=C.hex2rgb(b["electric"]) + (255,))

                box.alpha_composite(word_img, ((bw - word_img.width) // 2, pady))

                p = sub_frame_file(cue_i, seg_i * 20 + w_i, W)
                box.save(str(p), "PNG", compress_level=3)

                fr_start = cue["start"] + seg_i * seg_dur + w_i * word_dur
                fr_end = fr_start + word_dur

                frames_for_cue.append({
                    "file": str(p),
                    "w": bw, "h": bh,
                    "y": max(0, bottom - bh),
                    "start": fr_start,
                    "end": fr_end,
                })

        meta.append({"cue": cue_i, "text": cue["text"], "frames": frames_for_cue})

    (C.OUT / "karaoke_v2_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    total_frames = sum(len(m["frames"]) for m in meta)
    C.log("KARAOKE V2: %d cues -> %d frames" % (len(meta), total_frames))
    return meta


def build(preview=False):
    tl_path = C.VOICE / "timeline.json"
    if not tl_path.exists():
        C.die("timeline.json مفقود")
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    render_karaoke_v2(tl, preview)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    build(ap.parse_args().preview)
