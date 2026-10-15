"""A user's saved preferences (v2.2): personalization, accessibility, advanced mode, dashboard layout.

Stored as one small JSON object per account (`users.preferences`) and validated here: only known keys, only
known values, and a size limit, so a preferences write can never carry anything else.
"""

from __future__ import annotations

import re

THEMES = ("system", "light", "dark")
ACCENTS = ("indigo", "blue", "teal", "green", "amber", "rose", "violet", "slate")
MOTION = ("system", "reduce", "full")
CONTRAST = ("normal", "high")
SCALES = ("small", "default", "large", "xlarge")
VISION = ("none", "protanopia", "deuteranopia", "tritanopia", "monochrome")
DENSITY = ("comfortable", "compact")
DATE_FORMATS = ("dmy", "mdy", "ymd", "long", "iso")          # 31/12/2026, 12/31/2026, 2026/12/31, 31 Dec 2026, 2026-12-31
TIME_FORMATS = ("24h", "12h")
WEEK_STARTS = ("monday", "sunday", "saturday")
NUMBER_FORMATS = ("1,234.5", "1.234,5", "1 234,5")
LANDING = ("overview", "classrooms", "students")
WIDGET_SIZES = ("sm", "md", "lg", "xl")
MAX_WIDGETS = 24
_ID = re.compile(r"^[A-Za-z0-9_-]{1,32}$")
_HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")

DEFAULTS = {
    "theme": "system", "accent": "indigo", "accent_custom": "", "motion": "system", "contrast": "normal",
    "scale": "default", "vision": "none", "density": "comfortable", "sidebar_collapsed": False,
    "advanced": False, "tutorial_done": False, "dashboard": [],
    "date_format": "dmy", "time_format": "24h", "show_seconds": False, "week_start": "monday", "number_format": "1,234.5",
    "relative_times": True, "landing": "overview",
}


class PreferenceError(ValueError):
    pass


def _choice(key: str, value, allowed: tuple):
    if value not in allowed:
        raise PreferenceError(f"{key} must be one of: {', '.join(allowed)}")
    return value


def _widgets(value) -> list[dict]:
    if not isinstance(value, list) or len(value) > MAX_WIDGETS:
        raise PreferenceError(f"dashboard must be a list of at most {MAX_WIDGETS} widgets")
    out, seen = [], set()
    for w in value:
        if not isinstance(w, dict) or not _ID.match(str(w.get("id", ""))) or not _ID.match(str(w.get("kind", ""))):
            raise PreferenceError("each widget needs an id and a kind (letters, digits, - and _)")
        if w["id"] in seen:
            raise PreferenceError("widget ids must be unique")
        seen.add(w["id"])
        size = w.get("size", "md")
        out.append({"id": w["id"], "kind": w["kind"], "size": _choice("widget size", size, WIDGET_SIZES)})
    return out


def validate(changes: dict, role: str) -> dict:
    """The cleaned subset of `changes` (unknown keys are an error). Advanced mode is for administrators."""
    clean = {}
    for key, value in changes.items():
        if key == "theme":
            clean[key] = _choice(key, value, THEMES)
        elif key == "accent":
            clean[key] = _choice(key, value, ACCENTS)
        elif key == "accent_custom":
            if value != "" and not (isinstance(value, str) and _HEX.match(value)):
                raise PreferenceError("accent_custom must be empty or a colour like #5b4ee5")
            clean[key] = value
        elif key == "motion":
            clean[key] = _choice(key, value, MOTION)
        elif key == "contrast":
            clean[key] = _choice(key, value, CONTRAST)
        elif key == "scale":
            clean[key] = _choice(key, value, SCALES)
        elif key == "vision":
            clean[key] = _choice(key, value, VISION)
        elif key == "density":
            clean[key] = _choice(key, value, DENSITY)
        elif key == "date_format":
            clean[key] = _choice(key, value, DATE_FORMATS)
        elif key == "time_format":
            clean[key] = _choice(key, value, TIME_FORMATS)
        elif key == "week_start":
            clean[key] = _choice(key, value, WEEK_STARTS)
        elif key == "number_format":
            clean[key] = _choice(key, value, NUMBER_FORMATS)
        elif key == "landing":
            clean[key] = _choice(key, value, LANDING)
        elif key in ("sidebar_collapsed", "tutorial_done", "show_seconds", "relative_times"):
            if not isinstance(value, bool):
                raise PreferenceError(f"{key} must be true or false")
            clean[key] = value
        elif key == "advanced":
            if not isinstance(value, bool):
                raise PreferenceError("advanced must be true or false")
            clean[key] = bool(value) and role in ("admin", "super_admin")
        elif key == "dashboard":
            clean[key] = _widgets(value)
        else:
            raise PreferenceError(f"unknown preference: {key}")
    return clean


def merged(stored: dict | None, role: str) -> dict:
    out = {**DEFAULTS, **{k: v for k, v in (stored or {}).items() if k in DEFAULTS}}
    if role not in ("admin", "super_admin"):
        out["advanced"] = False
    return out
