"""The imPress mark and version, printed when the server and the root console start."""

from __future__ import annotations

import sys

MARK = (
    " ╻┏┳┓┏━┓┏━┓┏━╸┏━┓┏━┓",
    " ┃┃┃┃┣━┛┣┳┛┣╸ ┗━┓┗━┓",
    " ╹╹ ╹╹  ╹┗╸┗━╸┗━┛┗━┛",
)
TAGLINE = "classroom response system"


def utf8_output() -> None:
    """The mark and the root screen use box-drawing characters: a Windows console that defaults to a legacy code page
    must not stop imPress from starting over them."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def release() -> str:
    from .config import APP_RELEASE
    return APP_RELEASE


def lines(color: bool | None = None, detail: list[str] | None = None) -> list[str]:
    on = sys.stdout.isatty() if color is None else color
    c = (lambda code, s: f"\033[{code}m{s}\033[0m") if on else (lambda code, s: s)
    out = [c("38;5;75;1", row) for row in MARK]
    out[1] += "   " + c("1", f"v{release()}")
    out[2] += "   " + c("2", TAGLINE)
    return out + [c("2", x) for x in (detail or [])]


def show(detail: list[str] | None = None, file=None) -> None:
    print("\n".join(["", *lines(detail=detail), ""]), file=file or sys.stdout, flush=True)
