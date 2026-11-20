import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd):
    p = subprocess.run(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    if p.returncode != 0:
        raise SystemExit((p.stderr or p.stdout or "command failed").strip())
    return p.stdout


def main():
    vid = sys.argv[1] if len(sys.argv) > 1 else "016"
    src = Path("output") / vid / "final_video.mp4"
    if not src.exists():
        raise SystemExit(f"missing video: {src}")

    g = Path("golden") / vid
    if g.exists():
        shutil.rmtree(g)
    g.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(str(src), str(g / f"{vid}.mp4"))

    probe = run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(src)
    ])
    (g / "ffprobe.json").write_text(probe, encoding="utf-8")
    j = json.loads(probe)
    duration = float(j["format"]["duration"])

    for pct in (10, 30, 50, 70, 90):
        t = duration * pct / 100.0
        out = g / f"frame_{pct:02d}.png"
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-ss", f"{t:.3f}", "-i", str(src),
            "-frames:v", "1", "-vf", "scale=540:960:flags=bicubic",
            "-pix_fmt", "rgb24", str(out)
        ])

    rep = Path("output") / vid / "report.json"
    if rep.exists():
        shutil.copyfile(str(rep), str(g / "report.json"))

    manifest = {
        "video_id": vid,
        "source": str(src),
        "duration": duration,
        "frames_percent": [10, 30, 50, 70, 90],
        "frame_size": "540x960",
        "purpose": "Golden Master for numeric regression",
        "stdin_safe": True
    }
    (g / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print("✅ GOLDEN:", g)


if __name__ == "__main__":
    main()
