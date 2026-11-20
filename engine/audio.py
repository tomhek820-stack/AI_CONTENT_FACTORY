"""موسيقى ومؤثرات أصلية مولّدة رياضيًا (CC0) — Python خالص بلا numpy."""
from __future__ import annotations
import argparse, array, json, math, random
from engine import common as C


def synth(timeline, out_path):
    sr = int(C.cfg()["audio"]["bed_sr"])
    T = float(timeline["total"]); n = int(T * sr) + 1
    buf = array.array("d", bytes(8 * n))
    rnd = random.Random(7); sin, exp, pi = math.sin, math.exp, math.pi

    def add(start, samples, gain=1.0):
        i0 = int(start * sr)
        for k, v in enumerate(samples):
            j = i0 + k
            if 0 <= j < n:
                buf[j] += v * gain

    def pad(freqs, dur, amp=0.17):
        m = int(dur * sr); o = [0.0] * m
        for f in freqs:
            for det in (0.9975, 1.0035):
                w = 2 * pi * f * det / sr
                for i in range(m):
                    o[i] += sin(w * i)
        a = int(0.9 * sr); r = int(1.3 * sr); k = amp / (len(freqs) * 2)
        for i in range(m):
            e = 1.0
            if i < a:
                e = i / a
            if i > m - r:
                e = min(e, max(0.0, (m - i) / r))
            e *= 0.86 + 0.14 * sin(2 * pi * 0.17 * i / sr)
            o[i] *= e * k
        return o

    def thump(dur=0.55, f0=95, f1=44, amp=0.55):
        m = int(dur * sr); o = [0.0] * m; ph = 0.0
        for i in range(m):
            t = i / m; ph += 2 * pi * (f0 + (f1 - f0) * min(1.0, t * 3)) / sr
            o[i] = sin(ph) * exp(-6.0 * t) * amp
        return o

    def pluck(f, dur=0.30, amp=0.055):
        m = int(dur * sr); o = [0.0] * m; w = 2 * pi * f / sr
        for i in range(m):
            t = i / sr
            o[i] = (sin(w * i) + 0.34 * sin(2 * w * i) + 0.14 * sin(3 * w * i)) * exp(-9 * t) * amp
        return o

    def blip(f=1500, dur=0.085, amp=0.13):
        m = int(dur * sr); o = [0.0] * m; w = 2 * pi * f / sr
        for i in range(m):
            t = i / sr
            o[i] = (sin(w * i) + 0.3 * sin(1.5 * w * i)) * exp(-26 * t) * amp
        return o

    def whoosh(dur=0.75, amp=0.20, up=False):
        m = int(dur * sr); o = [0.0] * m; lp = 0.0
        for i in range(m):
            t = i / m
            lp += (0.02 + 0.34 * (t if up else (1.0 - t))) * (rnd.uniform(-1, 1) - lp)
            o[i] = lp * (sin(pi * t) ** 2) * amp * 3.2
        return o

    starts = [float(s["visual_start"]) for s in timeline["scenes"]]
    prog = [[110.0, 164.81, 220.0], [87.31, 130.81, 174.61],
            [130.81, 196.0, 261.63], [98.0, 146.83, 196.0]]
    part = T / 4.0
    for k, ch in enumerate(prog):
        add(k * part, pad(ch, part + 0.7))
    t = 0.55
    while t < T - 1.2:
        add(t, thump(0.5, 92, 46, 0.22)); t += 0.6667
    notes = [440.0, 523.25, 587.33, 659.25, 783.99, 659.25, 587.33, 523.25]
    t = 1.6; k = 0
    while t < T - 1.5:
        if k % 8 not in (3, 7):
            add(t, pluck(notes[k % len(notes)]))
        t += 0.3333; k += 1
    add(0.02, thump(0.7, 110, 40, 0.5))
    for i, st in enumerate(starts):
        if i > 0:
            add(max(0.0, st - 0.34), whoosh(0.72, 0.19))
        add(st + (0.42 if i else 0.30), blip(1500 if i % 2 else 1850))
    if starts:
        add(max(0.0, starts[-1] - 1.0), whoosh(1.0, 0.16, up=True))
        add(starts[-1], thump(0.8, 120, 38, 0.45))
    fi, fo = int(0.30 * sr), int(1.0 * sr)
    for i in range(n):
        if i < fi:
            buf[i] *= i / fi
        if i > n - fo:
            buf[i] *= max(0.0, (n - i) / fo)
    pk = max(1e-9, max(abs(min(buf)), abs(max(buf))))
    g = 0.72 / pk
    left = [v * g * 32767 for v in buf]
    d = int(0.006 * sr); right = [0.0] * n
    for i in range(n):
        right[i] = (left[i - d] if i >= d else 0.0) * 0.92
    C.wav_write_stereo(out_path, sr, left, right)
    C.log("BED: %.2fs stereo %dHz" % (T, sr))


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args()
    tl = json.loads((C.VOICE / "timeline.json").read_text(encoding="utf-8"))
    synth(tl, C.MUSIC / "bed.wav")
