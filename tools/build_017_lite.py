"""017: scenes + fade + ASS subs + music + LUFS -16."""
import sys, json, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import scene_graph as SG
from engine import scene_graph_bridge as BR
from engine import identity as ID

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "spike_tmp" / "017_lite"
OUT.mkdir(parents=True, exist_ok=True)
VOICE_DIR = ROOT / "spike_tmp" / "voice_srt"
INFO = json.loads((VOICE_DIR / "info.json").read_text(encoding="utf-8"))

W, H, FPS = 1080, 1920, 30
SILENCE = 0.1         # بين المشاهد (للتزامن مع الصوت)
FADE = 0.2            # مدة fade in/out
MUSIC_VOL = 0.26
TARGET_LUFS = -16

def probe(p):
    r = subprocess.run(
        ["ffprobe","-v","error","-show_entries","format=duration",
         "-of","default=noprint_wrappers=1:nokey=1", str(p)],
        capture_output=True, text=True, check=True
    )
    return float(r.stdout.strip())

def probe_frames(p):
    r = subprocess.run(
        ["ffprobe","-v","error","-count_frames","-select_streams","v:0",
         "-show_entries","stream=nb_read_frames","-of","csv=p=0", str(p)],
        capture_output=True, text=True, check=True
    )
    return int(r.stdout.strip())

def parse_script(path):
    scenes = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        if line.startswith("SCENE|"):
            p = line.split("|")
            scenes.append({
                "kind": p[1] if len(p)>1 else "tool",
                "scene_id": p[2] if len(p)>2 else "sc",
                "title_ar": p[3] if len(p)>3 else "",
                "subtitle": p[4] if len(p)>4 else "",
                "icon": p[5] if len(p)>5 else "",
            })
    return scenes

scenes = parse_script(ROOT / "scripts" / "video_016.txt")
lines_info = INFO["lines"]
print(f"📄 {len(scenes)} scenes | voice {INFO['total_dur']:.2f}s")

# ═══ 1. Render each scene with fade in/out + extended duration
scene_videos = []
for i, (sc, info) in enumerate(zip(scenes, lines_info)):
    dur = info["dur"]
    # كل مشهد يمتد بـ SILENCE (عدا الأخير) لضمان التزامن مع الصوت
    extend = SILENCE if i < len(scenes) - 1 else 0
    scene_dur = dur + extend
    print(f"\n🎬 Scene {i}: {sc['kind']} | {dur:.2f}s + {extend:.2f}s = {scene_dur:.2f}s")

    BR.render_card(sc, i, len(scenes), W, H, OUT)
    manifest = json.loads((OUT / f"l3_{i:02d}_manifest.json").read_text(encoding="utf-8"))
    layers = [SG.Layer(Path(l["path"]), l["x"], l["y"], l["t_in"], l["entry"])
              for l in manifest["layers"]]

    raw = OUT / f"scene_{i:02d}_raw.mp4"
    SG.Scene(duration=scene_dur, background=Path(manifest["background"]),
             layers=layers, W=W, H=H, fps=FPS).render(raw)

    # fade in/out
    faded = OUT / f"scene_{i:02d}.mp4"
    fade_out_start = max(0, scene_dur - FADE)
    subprocess.run([
        "ffmpeg","-y","-hide_banner","-loglevel","error","-nostdin",
        "-i", str(raw),
        "-vf", f"fade=t=in:st=0:d={FADE},fade=t=out:st={fade_out_start:.2f}:d={FADE}",
        "-c:v","libx264","-preset","fast","-crf","18",
        "-pix_fmt","yuv420p","-r",str(FPS),
        str(faded)
    ], check=True)

    frames = probe_frames(faded)
    print(f"   ✅ {faded.name} ({frames} frames, {probe(faded):.2f}s)")
    scene_videos.append(faded)

# ═══ 2. Concat
print(f"\n🔗 Concat {len(scene_videos)} scenes")
inputs = []
for v in scene_videos: inputs += ["-i", str(v)]
n = len(scene_videos)
concat_in = "".join(f"[{i}:v]" for i in range(n))
video_concat = OUT / "video_concat.mp4"
subprocess.run([
    "ffmpeg","-y","-hide_banner","-loglevel","error","-nostdin",
    *inputs, "-filter_complex", f"{concat_in}concat=n={n}:v=1:a=0[out]",
    "-map","[out]","-c:v","libx264","-preset","fast","-crf","18",
    "-pix_fmt","yuv420p","-r",str(FPS), str(video_concat)
], check=True)
print(f"✅ video_concat: {probe(video_concat):.2f}s")

# ═══ 3. Music mix + ducking + LUFS -16
print(f"\n🎵 Music + ducking + LUFS -16")
voice = INFO["voice"]
music = ROOT / "assets" / "music" / "studio_bed.wav"
voice_dur = probe(voice)

# pre-normalize voice to -16
print("   → normalize voice to -16 LUFS...")
voice_norm = OUT / "voice_norm.wav"
subprocess.run([
    "ffmpeg","-y","-hide_banner","-loglevel","error","-nostdin",
    "-i", voice,
    "-af", f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=7",
    "-c:a","pcm_s16le","-ar","48000","-ac","1", str(voice_norm)
], check=True)

if music.exists():
    print(f"   → mix with music (ducking 6dB)")
    mix_out = OUT / "audio_mixed.wav"
    fc = (
        f"[1:a]atrim=0:{voice_dur:.3f},volume={MUSIC_VOL},"
        f"afade=t=in:st=0:d=1.5,afade=t=out:st={voice_dur-2:.3f}:d=2[bed];"
        f"[0:a]asplit=2[voice][sc];"
        f"[bed][sc]sidechaincompress=threshold=0.04:ratio=8:attack=15:release=250[ducked];"
        f"[voice][ducked]amix=inputs=2:weights='1 0.35':duration=first:dropout_transition=2[mixed]"
    )
    subprocess.run([
        "ffmpeg","-y","-hide_banner","-loglevel","error","-nostdin",
        "-i", str(voice_norm),
        "-stream_loop","-1","-i", str(music),
        "-filter_complex", fc,
        "-map","[mixed]",
        "-c:a","pcm_s16le","-ar","48000","-ac","1", str(mix_out)
    ], check=True)
else:
    print("   ⚠️  no music — using voice only")
    mix_out = voice_norm

print(f"✅ audio: {probe(mix_out):.2f}s")

# ═══ 4. Final mux: video + audio + ASS subs
print(f"\n📝 Final mux with ASS")
ass = str(VOICE_DIR / "merged.ass")
final = OUT / "017_lite.mp4"
subprocess.run([
    "ffmpeg","-y","-hide_banner","-loglevel","error","-nostdin",
    "-i", str(video_concat),
    "-i", str(mix_out),
    "-vf", f"ass={ass}:fontsdir=assets/fonts",
    "-c:v","libx264","-preset","fast","-crf","18",
    "-c:a","aac","-b:a","192k",
    "-pix_fmt","yuv420p",
    str(final)
], check=True)
print(f"✅ FINAL: {final} ({probe(final):.2f}s)")

SG.last_frame(final, OUT / "017_lite_last.png")
