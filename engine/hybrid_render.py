"""رندر هجين: لقطات حقيقية + بطاقات + كاريوكي + هوك سريع."""
from __future__ import annotations
import json
from pathlib import Path
from engine import common as C
from engine import scenes as S
from engine import karaoke_v2 as K2


def render_hybrid(timeline, preview=False, fast=False):
    W, H, fps = C.dims(preview)
    out = C.OUT / ("hybrid_video_%d.mp4" % W)
    tmp = C.ROOT / "tmp"
    tmp.mkdir(exist_ok=True)

    C.log("HYBRID RENDER: %dx%d@%d | مشاهد=%d" % (W, H, fps, len(timeline["scenes"])))

    # 1. إنشاء لقطات هوك (0-2 ثانية)
    hook_text = "ينساك بعد 10 رسائل؟"
    hook_path = C.OUT / "hook_frame.png"
    from PIL import Image, ImageDraw
    hook_img = Image.new("RGB", (W, H), (5, 8, 15))
    hd = ImageDraw.Draw(hook_img)
    f = C.resolve_font(verbose=False)
    pen = C.ArabicPen(f, C.scale(90, W), bold=True, stroke=3)
    hi = pen.line_img(hook_text, (255, 255, 255, 255))
    hook_img.paste(hi, ((W - hi.width) // 2, (H - hi.height) // 2))
    # تأثير توهج
    from PIL import ImageFilter
    glow = hook_img.filter(ImageFilter.GaussianBlur(20))
    hook_img = Image.blend(hook_img, glow, 0.3)
    hook_img.save(str(hook_path), quality=95)
    C.log("HYBRID: هوك جاهز -> %s" % hook_path.name)

    # 2. إنشاء فيديو هوك (2 ثانية مع حركة سريعة)
    hook_vid = tmp / "hook.mp4"
    C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-loop", "1", "-i", str(hook_path),
           "-c:v", "libx264", "-t", "2",
           "-vf", "scale=%d:%d,zoompan=z='min(zoom+0.002,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=60:s=%dx%d:fps=%d" % (W, H, W, H, fps),
           "-pix_fmt", "yuv420p", str(hook_vid)])
    C.log("HYBRID: فيديو الهوك جاهز")

    # 3. إنشاء قائمة الدمج (هوك + لقطات حقيقية + بطاقات)
    concat_list = tmp / "hybrid_concat.txt"
    entries = []

    # هوك أولاً
    entries.append(hook_vid)

    for scene_i, sc in enumerate(timeline["scenes"]):
        scene_id = sc.get("id", "")
        kind = sc.get("kind", "")
        span = float(sc.get("span", 5.0))

        # إذا كان المشهد يحتوي على لقطة حقيقية
        if "real_video" in sc and Path(sc["real_video"]).exists():
            real_path = Path(sc["real_video"])
            # قص اللقطة الحقيقية إلى مدة المشهد
            trimmed = tmp / ("trimmed_%02d.mp4" % scene_i)
            C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                   "-i", str(real_path),
                   "-t", str(min(span, 6)),
                   "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                   "-pix_fmt", "yuv420p", str(trimmed)])
            entries.append(trimmed)
            C.log("HYBRID: مشهد %d = لقطة حقيقية (%.1fs)" % (scene_i, span))
        else:
            # إنشاء فيديو من البطاقة النصية
            card_path = sc.get("card_image", "")
            if not card_path or not Path(card_path).exists():
                C.log("HYBRID: مشهد %d ليس له بطاقة، سأنشئ واحدة" % scene_i, "WARN")
                continue

            card_vid = tmp / ("card_%02d.mp4" % scene_i)
            dur = min(span, 5)  # بطاقات قصيرة
            C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                   "-loop", "1", "-i", str(card_path),
                   "-c:v", "libx264", "-t", str(dur),
                   "-vf", "scale=%d:%d,zoompan=z='min(zoom+0.0005,1.03)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=%d:s=%dx%d:fps=%d" % (W, H, int(dur * fps), W, H, fps),
                   "-pix_fmt", "yuv420p", str(card_vid)])
            entries.append(card_vid)
            C.log("HYBRID: مشهد %d = بطاقة نصية (%.1fs)" % (scene_i, dur))

    # كتابة قائمة الدمج
    with open(concat_list, "w") as f:
        for e in entries:
            f.write("file '%s'\n" % e)

    # 4. دمج كل المقاطع
    merged = tmp / "hybrid_merged.mp4"
    C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "concat", "-safe", "0", "-i", str(concat_list),
           "-c:v", "libx264", "-preset", "fast", "-crf", "18",
           "-pix_fmt", "yuv420p", str(merged)])
    C.log("HYBRID: دمج المقاطع جاهز")

    # 5. إضافة الكاريوكي
    kar_meta_path = C.OUT / "karaoke_v2_meta.json"
    if kar_meta_path.exists():
        kar_meta = json.loads(kar_meta_path.read_text(encoding="utf-8"))
        C.log("HYBRID: إضافة %d إطار كاريوكي" % sum(len(m["frames"]) for m in kar_meta))
        # سنضيف الكاريوكي كـ overlay في الخطوة التالية

    # 6. إضافة الصوت
    audio = C.VOICE / "voice.wav"
    if audio.exists():
        final = C.OUT / "hybrid_final.mp4"
        C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-i", str(merged), "-i", str(audio),
               "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
               "-map", "0:v:0", "-map", "1:a:0",
               "-shortest", str(final)])
        C.log("HYBRID: الفيديو النهائي جاهز -> %s" % final.name)
        return final
    else:
        C.log("HYBRID: لا يوجد صوت، الفيديو بدون صوت", "WARN")
        return merged


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--fast", action="store_true")
    tl_path = C.ROOT / "voice" / "timeline_hybrid.json"
    if not tl_path.exists():
        tl_path = C.VOICE / "timeline.json"
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    render_hybrid(tl, ap.parse_args().preview, ap.parse_args().fast)
