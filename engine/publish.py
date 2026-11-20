"""مولّد نسخ النشر لأي منشور — يقرأ scripts/publish_<id>.json."""
from __future__ import annotations
import argparse, json
from engine import common as C


def build():
    c = C.cfg(); vid = str(c.get("video_id", "001"))
    mp = C.ROOT / "scripts" / ("publish_%s.json" % vid)
    if mp.exists():
        m = json.loads(mp.read_text(encoding="utf-8"))
    else:
        m = {"title": c["title"], "hook": "", "bullets": [], "note": "",
             "cta": "احفظ الفيديو وعلّق بسؤالك.",
             "tags_ar": ["#الذكاء_الاصطناعي", "#تقنية"], "tags_en": ["#AI", "#Tech"]}
    ta = " ".join(m.get("tags_ar", [])); te = " ".join(m.get("tags_en", []))
    bul = "\n".join("• " + b for b in m.get("bullets", []))
    yt = m.get("youtube_title") or m["title"]
    note = m.get("note", "")
    cta = m.get("cta", "احفظ الفيديو وعلّق بسؤالك.")
    txt = f"""=== {c['project']} — VIDEO {vid} ===
{m['title']}
45–60 ثانية | 1080×1920 | 30fps | H.264 + AAC

--- YOUTUBE SHORTS ---
{yt}

{m.get('hook','')}

{bul}

{note}

{cta}
تابع {c['project']}.

{ta}
{te}

--- TIKTOK ---
{m.get('hook','')}
{bul}
{cta}
{ta} #fyp #AI

--- INSTAGRAM REELS ---
{m.get('hook','')}
{bul}
احفظ البوست 🔖 وشاركه.
{cta}
{ta} #reels #AI

--- FACEBOOK REELS ---
{m.get('hook','')}
{bul}
{note}
{cta}
{ta} {te}

--- إفصاحات ---
• الصوت مُولّد آليًا أو بتسجيل بشري حسب المحرك المستخدم.
• الموسيقى والمؤثرات مولّدة داخل المشروع (CC0).
• الخلفيات والأيقونات أصلية؛ لا شعارات رسمية ولا واجهات مزيفة.
• لا يُدّعى أن أي أداة مجانية بالكامل؛ الخطط محدودة وقابلة للتغيير.
"""
    out = C.OUT / "publish_description.txt"
    out.write_text(txt, encoding="utf-8")
    C.log("PUBLISH video %s -> %s" % (vid, out))
    return out


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    build()
