"""Scene Graph v0.1 — layers + FFmpeg overlay.
   يتيح تركيب مشهد من طبقات PNG مستقلة مع حركات.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import subprocess


@dataclass
class Layer:
    """طبقة واحدة (PNG) مع حركة دخول."""
    path: Path
    x: int = 0
    y: int = 0
    t_in: float = 0.0
    entry: str = "static"  # static | right | left | fade_in | rise

    def overlay_expr(self, W: int, duration: float) -> str:
        """يعيد تعبير overlay x:y للـ FFmpeg."""
        if self.entry == "static":
            return f"x={self.x}:y={self.y}"

        if self.entry == "right":
            # يدخل من اليمين (RTL)
            end = self.t_in + 0.3
            return (
                f"x='if(lt(t,{self.t_in}),{W},"
                f"if(lt(t,{end}),"
                f"{W}-(t-{self.t_in})/0.3*({W}-{self.x}),"
                f"{self.x}))':y={self.y}"
            )

        if self.entry == "left":
            end = self.t_in + 0.3
            return (
                f"x='if(lt(t,{self.t_in}),-w,"
                f"if(lt(t,{end}),"
                f"-w+(t-{self.t_in})/0.3*({self.x}+w),"
                f"{self.x}))':y={self.y}"
            )

        if self.entry == "rise":
            # يصعد من الأسفل
            end = self.t_in + 0.3
            return (
                f"x={self.x}:y='if(lt(t,{self.t_in}),{self.y}+40,"
                f"if(lt(t,{end}),"
                f"{self.y}+40-(t-{self.t_in})/0.3*40,"
                f"{self.y}))'"
            )

        # fade_in → static + fade filter
        return f"x={self.x}:y={self.y}"

    def needs_fade(self) -> bool:
        return self.entry == "fade_in"

    def fade_filter(self) -> str:
        if self.entry == "fade_in":
            return f"fade=t=in:st={self.t_in}:d=0.3:alpha=1"
        return "null"


@dataclass
class Scene:
    """مشهد كامل: خلفية + طبقات + مدة."""
    duration: float
    background: Path
    layers: list[Layer] = field(default_factory=list)
    W: int = 1080
    H: int = 1920
    fps: int = 30

    def render(self, output: Path) -> Path:
        """يبني الفيديو عبر FFmpeg."""
        # inputs
        inputs = ["-loop", "1", "-t", str(self.duration), "-i", str(self.background)]
        for layer in self.layers:
            inputs += ["-loop", "1", "-t", str(self.duration), "-i", str(layer.path)]

        # filter_complex
        parts = ["[0:v]format=rgba[bg]"]
        prev = "bg"

        for i, layer in enumerate(self.layers, start=1):
            src_tag = f"v{i}"
            if layer.needs_fade():
                parts.append(
                    f"[{i}:v]format=rgba,setpts=PTS-STARTPTS,"
                    f"{layer.fade_filter()}[{src_tag}]"
                )
            else:
                parts.append(
                    f"[{i}:v]format=rgba,setpts=PTS-STARTPTS[{src_tag}]"
                )

            overlay = layer.overlay_expr(self.W, self.duration)
            next_tag = f"o{i}"
            parts.append(f"[{prev}][{src_tag}]overlay={overlay}:format=auto[{next_tag}]")
            prev = next_tag

        fc = ";".join(parts)

        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
            *inputs,
            "-filter_complex", fc,
            "-map", f"[{prev}]",
            "-c:v", "libx264", "-preset", "fast", "-crf", "17",
            "-pix_fmt", "yuv420p", "-r", str(self.fps),
            "-t", str(self.duration),
            str(output),
        ]

        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"FFmpeg failed:\n{r.stderr[-2000:]}")
        return output


def last_frame(video: Path, out: Path) -> Path:
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-nostdin",
        "-sseof", "-0.1", "-i", str(video),
        "-frames:v", "1", str(out)
    ], check=True)
    return out
