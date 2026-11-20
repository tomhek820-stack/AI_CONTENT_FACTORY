"""يبني intro_scenegraph.mp4 من 5 طبقات + حركات FFmpeg."""
import sys, json, subprocess
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
LAYERS = ROOT / "spike_tmp" / "intro_layers"
OUT = ROOT / "spike_tmp" / "intro_scenegraph.mp4"
pos = json.loads((LAYERS / "positions.json").read_text(encoding="utf-8"))
tx, ty = pos["title"]; gx, gy = pos["gold"]
sx, sy = pos["subtitle"]; cx, cy = pos["channel"]
DUR = pos["duration"]

# filter_complex:
#   bg: static
#   title: enters from right (RTL), 0.0-0.3s
#   gold: slides from right, 0.3-0.6s
#   subtitle: fade in 0.6-0.9s
#   channel: fade in 1.5-2.0s
fc = (
    "[0:v]format=rgba[bg];"
    "[1:v]format=rgba,setpts=PTS-STARTPTS[t];"
    f"[bg][t]overlay=x='W-min(1,t/0.3)*(W-{tx})':y={ty}:format=auto[t1];"
    "[2:v]format=rgba,setpts=PTS-STARTPTS[g];"
    f"[t1][g]overlay=x='W-min(1,max(0,t-0.3)/0.3)*(W-{gx})':y={gy}:format=auto[t2];"
    "[3:v]format=rgba,setpts=PTS-STARTPTS,fade=t=in:st=0.6:d=0.3:alpha=1[s];"
    f"[t2][s]overlay=x={sx}:y={sy}:format=auto[t3];"
    "[4:v]format=rgba,setpts=PTS-STARTPTS,fade=t=in:st=1.5:d=0.5:alpha=1[c];"
    f"[t3][c]overlay=x={cx}:y={cy}:format=auto[final]"
)

cmd = [
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-loop", "1", "-t", str(DUR), "-i", str(LAYERS / "01_bg_motif.png"),
    "-loop", "1", "-t", str(DUR), "-i", str(LAYERS / "02_title.png"),
    "-loop", "1", "-t", str(DUR), "-i", str(LAYERS / "03_gold.png"),
    "-loop", "1", "-t", str(DUR), "-i", str(LAYERS / "04_subtitle.png"),
    "-loop", "1", "-t", str(DUR), "-i", str(LAYERS / "05_channel.png"),
    "-filter_complex", fc,
    "-map", "[final]",
    "-c:v", "libx264", "-preset", "fast", "-crf", "17",
    "-pix_fmt", "yuv420p", "-r", "30",
    "-t", str(DUR), str(OUT),
]

print("⏳ Rendering...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("❌ FFmpeg failed:")
    print(r.stderr[-2000:])
    sys.exit(1)

print(f"✅ {OUT} ({OUT.stat().st_size // 1024} KB)")

# استخراج آخر إطار للمقارنة
last_frame = ROOT / "spike_tmp" / "intro_scenegraph_last.png"
subprocess.run([
    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
    "-sseof", "-0.1", "-i", str(OUT),
    "-frames:v", "1", str(last_frame)
], check=True)
print(f"✅ last frame: {last_frame}")
