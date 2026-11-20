"""مشاهد متحركة -> xfade -> مزج/Ducking -> ترجمة محروقة -> H.264/AAC."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from engine import common as C
from engine import scenes as S


def clip_frames(span, fps, xfade, last):
    L = span + (0.0 if last else xfade)
    return int(round(L * fps)), L


def render_scene(i, sc, W, H, fps, preview, fast, xfade, last):
    L = C.cfg()["layout"]; V = C.cfg()["video"]
    nf, dur = clip_frames(sc["span"], fps, xfade, last)
    nfm1 = max(1, nf - 1); z = float(V["zoom"]) - 1.0
    panx = 0.28 if i % 2 == 0 else -0.28
    pany = -0.16 if i % 3 == 0 else 0.12
    card_y = C.scale(L["intro_card_y"] if sc["kind"] == "intro" else L["card_y"], W)
    cin = 0.35 if i == 0 else xfade + 0.05
    cout = max(cin + 0.4, sc["span"] - 0.10)
    bg = S.bg_file(i, W, H); card = S.card_file(i, W)
    for p in (bg, card, S.glow_file(W), S.part_file(W, H), S.scan_file(W)):
        if not p.exists():
            C.die("أصل مفقود: %s — شغّل python -m engine.scenes" % p)
    fc = []
    fc.append("[0:v]zoompan=z='1+%.4f*on/%d':x='(iw-iw/zoom)*(0.5%+.2f*on/%d)'"
              ":y='(ih-ih/zoom)*(0.5%+.2f*on/%d)':d=%d:s=%dx%d:fps=%d,setsar=1,"
              "eq=saturation=1.06:contrast=1.03[bgv]" % (z, nfm1, panx, nfm1, pany, nfm1, nf, W, H, fps))
    fc.append("[bgv][1:v]overlay=x='(W-w)/2+%.1f*sin(t/3.1)':y='H*0.20+%.1f*cos(t/4.3)'[l1]" % (W * 0.11, H * 0.05))
    fc.append("[l1][2:v]overlay=x='%.1f*sin(t/6)':y='-%d+%d*sin(t/8)'[l2]" % (W * 0.017, int(H * 0.062), int(H * 0.021)))
    fc.append("[3:v]loop=loop=%d:size=1:start=0,setpts=N/(%d*TB),format=rgba,"
              "fade=t=in:st=%.3f:d=0.45:alpha=1,fade=t=out:st=%.3f:d=0.45:alpha=1[card]" % (nf - 1, fps, cin, cout))
    fc.append("[l2][card]overlay=x=0:y='%d+%.1f*(1-min(1,max(0,(t-%.3f)/0.5)))'[l3]" % (card_y, H * 0.016, cin))
    fc.append("[l3][4:v]overlay=x=0:y='mod(t*%.1f,%d)-100'[l4]" % (H * 0.078, H + 200))
    tail = ""
    if i == 0:
        tail += ",fade=t=in:st=0:d=0.35"
    if last:
        tail += ",fade=t=out:st=%.3f:d=0.50" % max(0.0, dur - 0.55)
    fc.append("[l4]format=yuv420p%s[vout]" % tail)
    out = C.OUT / "scenes" / ("scene_%02d_%d.mp4" % (i, W))
    out.parent.mkdir(parents=True, exist_ok=True)
    preset = V["preview_preset" if (preview or fast) else "preset"]
    crf = V["preview_crf" if (preview or fast) else "crf"]
    C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats",
           "-i", bg, "-i", S.glow_file(W), "-i", S.part_file(W, H), "-i", card, "-i", S.scan_file(W),
           "-filter_complex", ";".join(fc), "-map", "[vout]", "-frames:v", nf, "-r", fps,
           "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", "-an", out])
    got = C.duration(out)
    if abs(got - dur) > 0.12:
        C.die("مشهد %02d مدة %.3f بدل %.3f" % (i, got, dur))
    C.log("scene %02d ok %d frames" % (i, nf))
    return out


def xfade_master(clips, tl, W, H, fps, preview, fast, xfade):
    kinds = ["fade", "slideleft", "circleopen", "smoothright", "wipeleft", "slideright", "fade"]
    fc = ["[%d:v]settb=AVTB,fps=%d[v%d]" % (i, fps, i) for i in range(len(clips))]
    prev = "v0"; off = 0.0
    for i in range(1, len(clips)):
        off += float(tl["scenes"][i - 1]["span"]); lab = "x%d" % i
        fc.append("[%s][v%d]xfade=transition=%s:duration=%.3f:offset=%.3f[%s]"
                  % (prev, i, kinds[(i - 1) % len(kinds)], xfade, off, lab))
        prev = lab
    fc.append("[%s]format=yuv420p[vout]" % prev)
    out = C.OUT / ("master_%d.mp4" % W)
    V = C.cfg()["video"]
    preset = V["preview_preset" if (preview or fast) else "preset"]
    crf = V["preview_crf" if (preview or fast) else "crf"]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats"]
    for c in clips:
        cmd += ["-i", c]
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-r", fps, "-c:v", "libx264",
            "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p", "-an", out]
    p = C.run(cmd, check=False)
    if p.returncode != 0 or not out.exists():
        C.log("xfade فشل — التحويل إلى concat", "WARN")
        lst = C.OUT / "concat.txt"
        lst.write_text("".join("file '%s'\n" % c.resolve() for c in clips), encoding="utf-8")
        C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
               "-i", lst, "-c", "copy", out])
    got = C.duration(out)
    if abs(got - tl["total"]) > 0.20:
        C.die("الماستر %.3fs لا يطابق الصوت %.3fs" % (got, tl["total"]))
    C.log("MASTER ok %.3fs" % got)
    return out


def mix_audio(tl):
    A = C.cfg()["audio"]
    total = float(tl["total"])
    voice = C.VOICE / "voice.wav"; bed = C.MUSIC / "bed.wav"
    if not voice.exists():
        C.die("voice.wav مفقود")
    if not bed.exists():
        C.die("bed.wav مفقود")
    mix = C.OUT / "mix.wav"
    fc = ("[1:a]aresample=%d,volume=%.3f[bed];"
          "[0:a]aresample=%d,highpass=f=85,acompressor=threshold=-18dB:ratio=3:attack=8:release=180,"
          "volume=%.3f[v];[v]asplit=2[v1][vsc];"
          "[bed][vsc]sidechaincompress=threshold=%.3f:ratio=%d:attack=20:release=320:makeup=1:knee=6:detection=rms[duck];"
          "[duck][v1]amix=inputs=2:duration=first:dropout_transition=0,volume=2.0,apad[mix]"
          % (int(A["voice_sr"]), float(A["bed_gain"]), int(A["voice_sr"]), float(A["voice_gain"]),
             float(A["duck_threshold"]), int(A["duck_ratio"])))
    C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", voice, "-i", bed,
           "-filter_complex", fc, "-map", "[mix]", "-ar", str(A["voice_sr"]), "-ac", "2",
           "-c:a", "pcm_s16le", "-t", "%.6f" % total, mix])
    C.log("mix.wav = %.3fs (target %.3fs)" % (C.duration(mix), total))
    target = "loudnorm=I=%.1f:TP=%.1f:LRA=%.1f" % (A["loudnorm_I"], A["loudnorm_TP"], A["loudnorm_LRA"])
    p = C.run(["ffmpeg", "-hide_banner", "-nostats", "-i", mix, "-af",
               target + ":print_format=json", "-f", "null", "-"], check=False)
    measured = None
    if p.stderr:
        blocks = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", p.stderr, re.S)
        if blocks:
            try:
                measured = json.loads(blocks[-1])
            except Exception:
                measured = None
    if measured:
        try:
            gain = float(A["loudnorm_I"]) - float(measured["input_i"])
        except Exception:
            gain = 6.0
        gain = max(-12.0, min(18.0, gain))
        C.log("loudness measured I=%s TP=%s -> linear gain %+.2f dB"
              % (measured["input_i"], measured["input_tp"], gain))
    else:
        gain = 6.0
        C.log("loudness measurement failed -> fallback +6 dB", "WARN")
    lim = 10.0 ** (float(A["loudnorm_TP"]) / 20.0)
    af = "volume=%.3fdB,alimiter=limit=%.4f:attack=5:release=60:level=false,apad" % (gain, lim)
    norm = C.OUT / "mix_norm.wav"
    C.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", mix, "-af", af,
           "-ar", str(A["voice_sr"]), "-ac", "2", "-c:a", "pcm_s16le",
           "-t", "%.6f" % total, norm])
    d = C.duration(norm)
    if abs(d - total) > 0.10:
        C.die("المزيج %.3fs لا يطابق %.3fs" % (d, total))
    q = C.run(["ffmpeg", "-hide_banner", "-nostats", "-i", norm, "-af",
               target + ":print_format=json", "-f", "null", "-"], check=False)
    if q.stderr:
        b = re.findall(r"\{[^{}]*\"input_i\"[^{}]*\}", q.stderr, re.S)
        if b:
            try:
                m = json.loads(b[-1])
                C.log("FINAL loudness I=%s LUFS | TP=%s dBTP" % (m["input_i"], m["input_tp"]))
            except Exception:
                pass
    C.log("MIX ok %.3fs (sample-exact)" % d)
    return norm


def final_pass(master, audio, tl, W, H, fps, preview, fast, visual_only=False):
    kar_path = C.OUT / "karaoke_meta.json"
    use_karaoke = (not visual_only) and kar_path.exists()
    if use_karaoke:
        kar_meta = json.loads(kar_path.read_text(encoding="utf-8"))
        meta = []
    else:
        kar_meta = None
        meta = [] if visual_only else json.loads((C.OUT / "subtitles_meta.json").read_text(encoding="utf-8"))
    V = C.cfg()["video"]; L = C.cfg()["layout"]
    inputs = ["-i", master]
    if audio is not None:
        inputs += ["-i", audio]
    ai = 2 if audio is not None else 1
    inputs += ["-i", S.bug_file(W), "-i", S.bar_file(W)]
    bug_i, bar_i = ai, ai + 1; sub_start = ai + 2
    if visual_only:
        inputs += ["-i", S.label_file(W)]; label_i = sub_start
    else:
        if use_karaoke:
            for cm in kar_meta:
                for fr in cm["frames"]:
                    inputs += ["-i", fr["file"]]
        else:
            for m in meta:
                inputs += ["-i", m["file"]]
    fc = ["[0:v][%d:v]overlay=x=W-w-%d:y=%d:enable='gte(t,0.2)'[b1]"
          % (bug_i, C.scale(L["bug_x"], W), C.scale(L["bug_y"], W)),
          "[b1][%d:v]overlay=x='-w+w*t/%.6f':y=H-%d[b2]" % (bar_i, tl["total"], max(6, C.scale(10, W)))]
    prev = "b2"
    if visual_only:
        fc.append("[%s][%d:v]overlay=x='(W-w)/2':y=%d[vout]" % (prev, label_i, C.scale(300, W)))
    else:
        k_input = sub_start
        if use_karaoke:
            for cm in kar_meta:
                for fr in cm["frames"]:
                    lab = "k%d_%d" % (cm["cue"], fr["frame"])
                    fc.append("[%s][%d:v]overlay=x='(W-w)/2':y=%d:enable='between(t,%.3f,%.3f)'[%s]"
                              % (prev, k_input, fr["y"], fr["start"], fr["end"], lab))
                    prev = lab
                    k_input += 1
        else:
            for k, m in enumerate(meta):
                lab = "s%d" % k
                fc.append("[%s][%d:v]overlay=x='(W-w)/2':y=%d:enable='between(t,%.3f,%.3f)'[%s]"
                          % (prev, k_input, m["y"], m["start"], m["end"], lab))
                prev = lab
                k_input += 1
        fc.append("[%s]format=yuv420p[vout]" % prev)
    out = C.OUT / ("preview_visual_only.mp4" if visual_only else "final_video.mp4")
    preset = V["preview_preset" if (preview or fast) else "preset"]
    crf = V["preview_crf" if (preview or fast) else "crf"]
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats"] + inputs
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]"]
    if audio is not None:
        cmd += ["-map", "1:a", "-c:a", "aac", "-b:a", V["audio_bitrate"],
                "-ar", str(C.cfg()["audio"]["voice_sr"]), "-ac", "2"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-profile:v", V["profile"],
            "-level", V["level"], "-pix_fmt", "yuv420p", "-r", str(fps),
            "-t", "%.6f" % tl["total"], "-movflags", "+faststart", out]
    C.run(cmd)
    C.log("FINAL: %s" % out)
    return out


def verify(path, tl, W, H, fps, visual_only):
    j = C.ffprobe_json(path)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in j["streams"] if s["codec_type"] == "audio"), None)
    d = float(j["format"]["duration"]); ok = True

    def chk(name, cond, got):
        nonlocal ok
        C.log("  [%s] %s = %s" % ("PASS" if cond else "FAIL", name, got))
        ok = ok and bool(cond)

    chk("h264", v and v["codec_name"] == "h264", v and v["codec_name"])
    chk("size", v and v["width"] == W and v["height"] == H, v and "%sx%s" % (v["width"], v["height"]))
    chk("yuv420p", v and v["pix_fmt"] == "yuv420p", v and v["pix_fmt"])
    num, den = (v["r_frame_rate"].split("/") + ["1"])[:2] if v else ("0", "1")
    chk("fps", abs(float(num) / max(1.0, float(den)) - fps) < 0.6, v and v["r_frame_rate"])
    chk("duration", abs(d - tl["total"]) < 0.30, "%.3f" % d)
    if not visual_only:
        D = C.cfg()["duration"]
        chk("45-60s", D["min"] <= d <= D["max"], "%.3f" % d)
        chk("aac", a and a["codec_name"] == "aac", a and a["codec_name"])
        chk("48k stereo", a and int(a["sample_rate"]) == 48000 and a["channels"] == 2,
            a and "%s/%s" % (a["sample_rate"], a["channels"]))
    (C.OUT / "report.json").write_text(json.dumps({"file": str(path), "duration": d, "ok": ok},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")
    if not ok:
        C.die("فشل التحقق من الفيديو")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true"); ap.add_argument("--fast", action="store_true")
    ap.add_argument("--visual-only", action="store_true")
    a = ap.parse_args()
    C.need("ffmpeg"); C.need("ffprobe")
    W, H, fps = C.dims(a.preview)
    tlp = C.VOICE / ("timeline.dry.json" if a.visual_only else "timeline.json")
    if not tlp.exists():
        C.die("مفقود: %s" % tlp)
    tl = json.loads(tlp.read_text(encoding="utf-8"))
    xfade = C.snap(C.cfg()["video"]["xfade"], fps)
    scenes = tl["scenes"]
    C.log("RENDER %dx%d@%d total=%.3fs" % (W, H, fps, tl["total"]))
    clips = [render_scene(i, sc, W, H, fps, a.preview, a.fast, xfade, i == len(scenes) - 1)
             for i, sc in enumerate(scenes)]
    master = xfade_master(clips, tl, W, H, fps, a.preview, a.fast, xfade)
    audio = None if a.visual_only else mix_audio(tl)
    out = final_pass(master, audio, tl, W, H, fps, a.preview, a.fast, a.visual_only)
    verify(out, tl, W, H, fps, a.visual_only)
    if not a.visual_only:
        from engine import publish
        publish.build()
        C.log("✅ الإنتاج مكتمل: %s" % out)
    else:
        C.log("⚠ معاينة بصرية بلا صوت: %s" % out)


if __name__ == "__main__":
    main()
