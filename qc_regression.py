import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

PCTS = (10, 30, 50, 70, 90)


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


def ffprobe(video):
    return json.loads(run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(video)
    ]))


def extract_frames(video, duration, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    frames = {}
    for pct in PCTS:
        t = duration * pct / 100.0
        out = outdir / f"frame_{pct:02d}.png"
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
            "-ss", f"{t:.3f}", "-i", str(video),
            "-frames:v", "1", "-vf", "scale=540:960:flags=bicubic",
            "-pix_fmt", "rgb24", str(out)
        ])
        frames[pct] = out
    return frames


def image_diff_percent(a_path, b_path):
    with Image.open(a_path) as a, Image.open(b_path) as b:
        a = a.convert("RGB")
        b = b.convert("RGB")
        if a.size != b.size:
            b = b.resize(a.size)
        diff = ImageChops.difference(a, b)
        stat = ImageStat.Stat(diff)
        mean = sum(stat.mean[:3]) / 3.0
        pct = mean / 255.0 * 100.0
        hist = diff.convert("L").histogram()
        changed = sum(hist[13:]) / float(a.width * a.height) * 100.0
        return pct, changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--golden", required=True)
    ap.add_argument("--threshold", type=float, default=5.0)
    ap.add_argument("--report", required=True)
    a = ap.parse_args()

    video = Path(a.video)
    golden = Path(a.golden)
    if not video.exists():
        raise SystemExit(f"missing video: {video}")
    if not golden.exists():
        raise SystemExit(f"missing golden dir: {golden}")

    gj = json.loads((golden / "ffprobe.json").read_text(encoding="utf-8"))
    cj = ffprobe(video)
    gd = float(gj["format"]["duration"])
    cd = float(cj["format"]["duration"])

    gv = next(s for s in gj["streams"] if s["codec_type"] == "video")
    cv = next(s for s in cj["streams"] if s["codec_type"] == "video")

    errors = []
    warnings = []

    if abs(cd - gd) > 0.5:
        errors.append(f"duration drift: golden={gd:.3f}s current={cd:.3f}s")
    if (gv["width"], gv["height"]) != (cv["width"], cv["height"]):
        errors.append("resolution changed")
    if gv.get("r_frame_rate") != cv.get("r_frame_rate"):
        warnings.append("fps changed")
    if gv.get("codec_name") != cv.get("codec_name"):
        errors.append("video codec changed")

    with tempfile.TemporaryDirectory() as td:
        cur = extract_frames(video, cd, Path(td) / "current")
        frames = []
        for pct in PCTS:
            gframe = golden / f"frame_{pct:02d}.png"
            if not gframe.exists():
                errors.append(f"missing golden frame {pct}%")
                continue
            pct_diff, changed = image_diff_percent(gframe, cur[pct])
            item = {
                "percent": pct,
                "mean_diff_percent": round(pct_diff, 4),
                "changed_pixels_percent": round(changed, 4),
                "pass": pct_diff <= a.threshold
            }
            frames.append(item)
            if pct_diff > a.threshold:
                errors.append(
                    f"visual regression at {pct}%: {pct_diff:.3f}% > {a.threshold}%"
                )

    report = {
        "video": str(video),
        "golden": str(golden),
        "threshold_percent": a.threshold,
        "golden_duration": gd,
        "current_duration": cd,
        "frames": frames,
        "errors": errors,
        "warnings": warnings,
        "pass": not errors
    }

    rp = Path(a.report)
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if errors:
        raise SystemExit("❌ REGRESSION FAIL → ارجع إلى Golden Master وأعد التفكير")
    print("✅ REGRESSION PASS")


if __name__ == "__main__":
    main()
