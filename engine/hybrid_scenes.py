"""مشاهد هجينة: لقطات حقيقية من real_demos + بطاقات نصية محسّنة."""
from __future__ import annotations
import json, os, random
from pathlib import Path
from engine import common as C


def build_hybrid_assets(timeline, preview=False):
    """دمج لقطات حقيقية من real_demos مع بطاقات نصية."""
    from PIL import Image, ImageDraw
    W, H, fps = C.dims(preview)
    b = C.cfg()["brand"]
    real_videos_dir = C.ROOT / "real_demos" / "videos"
    out_scenes = C.OUT / "scenes"
    out_scenes.mkdir(parents=True, exist_ok=True)

    # خريطة المشاهد إلى لقطات حقيقية
    real_map = {
        "real1": "01_termux_pro.mp4",
        "real2": "03_python_pro.mp4",
        "real3": "02_ffmpeg_pro.mp4",
    }

    C.log("HYBRID: فحص اللقطات الحقيقية في %s" % real_videos_dir)
    for scene_i, sc in enumerate(timeline["scenes"]):
        scene_id = sc.get("id", "")
        kind = sc.get("kind", "")

        if scene_id in real_map:
            real_file = real_videos_dir / real_map[scene_id]
            if real_file.exists():
                C.log("HYBRID: مشهد %d يستخدم لقطة حقيقية: %s" % (scene_i, real_file.name))
                # سنستخدم هذه اللقطة مباشرة في الرندر
                sc["real_video"] = str(real_file)
            else:
                C.log("HYBRID: لقطة غير موجودة، سأنشئ بطاقة نصية: %s" % real_map[scene_id], "WARN")

        # إنشاء بطاقة نصية محسّنة للمشهد
        title_ar = sc.get("title_ar", "")
        latin = sc.get("latin", "")
        lines = sc.get("lines", [])

        # بطاقة محسّنة
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        # خلفية متدرجة
        for y in range(H):
            t = y / H
            r = int(5 + t * 15)
            g = int(8 + t * 20)
            bl = int(15 + t * 40)
            d.line([(0, y), (W, y)], fill=(r, g, bl, 255))

        # شبكة نقاط خفيفة
        for yy in range(0, H, 60):
            for xx in range(0, W, 60):
                d.ellipse([xx, yy, xx + 2, yy + 2], fill=(60, 100, 180, 30))

        # عنوان المشهد (عربي فقط، بدون الإنجليزي)
        if title_ar:
            f = C.resolve_font(verbose=False)
            pen = C.ArabicPen(f, C.scale(80, W), bold=True, stroke=2)
            ti = pen.line_img(title_ar, C.hex2rgb(b["white"]) + (255,))
            y_pos = C.scale(400, W)
            img.alpha_composite(ti, ((W - ti.width) // 2, y_pos))

            # خط تحت العنوان
            line_y = y_pos + ti.height + C.scale(30, W)
            d.rectangle([(W // 2 - C.scale(100, W), line_y),
                         (W // 2 + C.scale(100, W), line_y + C.scale(6, W))],
                        fill=C.hex2rgb(b["electric"]) + (255,))

        # رقم المشهد (دائرة في الأعلى، ليست على الحافة)
        if kind == "tool":
            num = scene_i + 1
            cx = W // 2
            cy = C.scale(180, W)
            r = C.scale(60, W)
            d.ellipse([cx - r, cy - r, cx + r, cy + r],
                      fill=C.hex2rgb(b["blue"]) + (255,),
                      outline=C.hex2rgb(b["electric"]) + (255,),
                      width=4)
            num_pen = C.ArabicPen(f, C.scale(50, W), bold=True)
            ni = num_pen.latin_img("%d" % num, C.hex2rgb(b["white"]) + (255,))
            img.alpha_composite(ni, ((cx - ni.width // 2), (cy - ni.height // 2)))

        # اسم الأداة (أسفل العنوان)
        if latin and kind == "tool":
            small_pen = C.ArabicPen(f, C.scale(36, W))
            li = small_pen.line_img(latin, C.hex2rgb(b["muted"]) + (200,))
            img.alpha_composite(li, ((W - li.width) // 2, C.scale(700, W)))

        card_path = out_scenes / ("hybrid_card_%02d.png" % scene_i)
        img.convert("RGB").save(str(card_path), quality=95)
        sc["card_image"] = str(card_path)
        C.log("HYBRID: بطاقة مشهد %d -> %s" % (scene_i, card_path.name))

    # حفظ الـ timeline المحدث
    (C.ROOT / "voice" / "timeline_hybrid.json").write_text(
        json.dumps(timeline, ensure_ascii=False, indent=1), encoding="utf-8")
    C.log("HYBRID: اكتمل إنشاء %d مشهد" % len(timeline["scenes"]))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    tl_path = C.VOICE / "timeline.json"
    if not tl_path.exists():
        C.die("timeline.json مفقود")
    tl = json.loads(tl_path.read_text(encoding="utf-8"))
    build_hybrid_assets(tl, ap.parse_args().preview)
