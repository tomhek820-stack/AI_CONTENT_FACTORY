"""Level 3 identity loader. stdlib only: json/pathlib/typing/copy."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "config" / "identity.json"
FONT_DIR = ROOT / "assets" / "fonts"

DEFAULTS: Dict[str, Any] = {
    "version": 1,
    "enabled": False,
    "fonts": {
        "title": {"family": "ReemKufi", "file": "ReemKufi-Bold.ttf", "verified": False},
        "body": {"family": "IBMPlexSansArabic", "file": "IBMPlexSansArabic-Medium.ttf", "verified": False},
        "wisdom": {"family": "Amiri", "file": "Amiri-Bold.ttf", "verified": True},
        "fallback": {"family": "Amiri", "file": "Amiri-Bold.ttf"},
    },
    "palette": {
        "ink": "#0B0A08",
        "turquoise": "#0FB5A8",
        "paper": "#E8DCC8",
        "gold": "#C9A227",
        "agate": "#B33A3A",
    },
    "layout": {
        "margin_side": 96,
        "safe_top": 220,
        "safe_bottom": 420,
        "align": "right",
        "grid": {
            "motif_corner": {"x": 984, "y": 180, "size": 48},
            "hero_word_y": 760,
            "gold_rule_y": 820,
            "karaoke_top": 1380,
            "karaoke_bottom": 1560,
            "progress_y": 1620,
        },
    },
    "rhythm": {
        "comma_ms": 180,
        "period_ms": 320,
        "wisdom_ms": 500,
        "sentence_gap_ms": 100,
    },
    "motion": {
        "entry_direction": "right",
        "entry_offset_px": 24,
        "connection_reveal_steps": 6,
        "connection_reveal_ms": 300,
    },
    "audio": {
        "lufs_target": -16.0,
        "true_peak": -1.5,
        "lra": 7.0,
        "rate_min": 0.92,
        "rate_max": 1.06,
    },
    "level3": {
        "enabled": False,
        "scene_graph": False,
        "rtl_motion": False,
        "waqf_rhythm": False,
        "connection_reveal": False,
        "kufic_motif": False,
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _is_hex(s: Any) -> bool:
    if not isinstance(s, str):
        return False
    if len(s) != 7 or s[0] != "#":
        return False
    try:
        int(s[1:], 16)
        return True
    except Exception:
        return False


def _need_type(path: str, value: Any, types: tuple) -> None:
    if not isinstance(value, types):
        names = "/".join(t.__name__ for t in types)
        raise ValueError(f"identity.json: {path} must be {names}, got {type(value).__name__}")


def _validate(d: Dict[str, Any]) -> None:
    _need_type("version", d.get("version"), (int,))
    _need_type("enabled", d.get("enabled"), (bool,))

    fonts = d.get("fonts")
    _need_type("fonts", fonts, (dict,))
    for role, info in fonts.items():
        _need_type(f"fonts.{role}", info, (dict,))
        _need_type(f"fonts.{role}.family", info.get("family"), (str,))
        _need_type(f"fonts.{role}.file", info.get("file"), (str,))
        if "verified" in info:
            _need_type(f"fonts.{role}.verified", info["verified"], (bool,))

    pal = d.get("palette")
    _need_type("palette", pal, (dict,))
    for name, hexv in pal.items():
        if not _is_hex(hexv):
            raise ValueError(f"identity.json: palette.{name} must be #RRGGBB, got {hexv!r}")

    layout = d.get("layout")
    _need_type("layout", layout, (dict,))
    for k in ("margin_side", "safe_top", "safe_bottom"):
        _need_type(f"layout.{k}", layout.get(k), (int,))
    _need_type("layout.align", layout.get("align"), (str,))
    grid = layout.get("grid")
    _need_type("layout.grid", grid, (dict,))
    for k, v in grid.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                _need_type(f"layout.grid.{k}.{kk}", vv, (int,))
        else:
            _need_type(f"layout.grid.{k}", v, (int,))

    rhythm = d.get("rhythm")
    _need_type("rhythm", rhythm, (dict,))
    for k, v in rhythm.items():
        _need_type(f"rhythm.{k}", v, (int,))

    motion = d.get("motion")
    _need_type("motion", motion, (dict,))
    _need_type("motion.entry_direction", motion.get("entry_direction"), (str,))
    for k in ("entry_offset_px", "connection_reveal_steps", "connection_reveal_ms"):
        _need_type(f"motion.{k}", motion.get(k), (int,))

    audio = d.get("audio")
    _need_type("audio", audio, (dict,))
    for k, v in audio.items():
        _need_type(f"audio.{k}", v, (int, float))

    level3 = d.get("level3")
    _need_type("level3", level3, (dict,))
    for k, v in level3.items():
        _need_type(f"level3.{k}", v, (bool,))


def load_identity(path: str | Path = DEFAULT_PATH) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return copy.deepcopy(DEFAULTS)
    try:
        user = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"identity.json invalid JSON: {e}") from e
    if not isinstance(user, dict):
        raise ValueError("identity.json root must be object")
    merged = _deep_merge(DEFAULTS, user)
    _validate(merged)
    return merged


def get(path: str, default: Any = None, identity: Optional[Dict[str, Any]] = None) -> Any:
    d = identity if identity is not None else load_identity()
    cur: Any = d
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur


def is_enabled(feature: str, identity: Optional[Dict[str, Any]] = None) -> bool:
    d = identity if identity is not None else load_identity()
    return bool(d.get("enabled", False) and d.get("level3", {}).get(feature, False))


def palette_rgb(name: str, identity: Optional[Dict[str, Any]] = None) -> tuple:
    hexv = get(f"palette.{name}", None, identity)
    if not _is_hex(hexv):
        raise ValueError(f"unknown palette color: {name}")
    r = int(hexv[1:3], 16)
    g = int(hexv[3:5], 16)
    b = int(hexv[5:7], 16)
    return (r, g, b, 255)


def font_path(role: str, identity: Optional[Dict[str, Any]] = None) -> Path:
    d = identity if identity is not None else load_identity()
    info = d.get("fonts", {}).get(role) or d.get("fonts", {}).get("fallback")
    if not info:
        raise FileNotFoundError("no font role and no fallback")
    p = FONT_DIR / info["file"]
    if p.exists():
        return p
    fb = d.get("fonts", {}).get("fallback", {})
    fp = FONT_DIR / fb.get("file", "Amiri-Bold.ttf")
    if fp.exists():
        return fp
    raise FileNotFoundError(f"font missing for role={role}: {p}")


def verified_fonts(identity: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    d = identity if identity is not None else load_identity()
    out = {}
    for role, info in d.get("fonts", {}).items():
        if info.get("verified") is True:
            out[role] = copy.deepcopy(info)
    return out


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        missing = Path(td) / "missing.json"
        d = load_identity(missing)
        assert d["enabled"] is False
        assert d["palette"]["turquoise"] == "#0FB5A8"
        print("✅ unit 1: missing file -> defaults")

        partial = Path(td) / "partial.json"
        partial.write_text(json.dumps({"palette": {"ink": "#000000"}}), encoding="utf-8")
        d = load_identity(partial)
        assert d["palette"]["ink"] == "#000000"
        assert d["palette"]["turquoise"] == "#0FB5A8"
        assert d["layout"]["margin_side"] == 96
        print("✅ unit 2: partial file -> deep-merge")

        bad = Path(td) / "bad.json"
        bad.write_text(json.dumps({"layout": {"margin_side": "96"}}), encoding="utf-8")
        try:
            load_identity(bad)
        except ValueError as e:
            assert "layout.margin_side" in str(e)
            print("✅ unit 3: wrong type -> clear ValueError")
        else:
            raise AssertionError("wrong type was not rejected")

    print("✅ identity.py unit tests PASS")
