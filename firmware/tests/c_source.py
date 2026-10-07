"""Tiny C source helpers for structural firmware tests (no compiler needed).

Good enough for this code base's style: top-level functions start at column 0
and their body closes with a "}" at column 0. Comments and string literals are
blanked first so identifiers inside them don't count as uses.
"""

import re
from pathlib import Path

FIRMWARE = Path(__file__).resolve().parents[1]

_FUNC_RE = re.compile(r"^(?:static\s+)?[\w\s\*]+?\b(\w+)\s*\([^;{]*\)\s*\{", re.M)


def strip_comments_and_strings(src: str) -> str:
    def blank(m):
        return re.sub(r"[^\n]", " ", m.group(0))
    pattern = r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\''
    return re.sub(pattern, blank, src, flags=re.S)


def functions(path) -> dict:
    """{name: body_text} for every top-level function definition in a C file."""
    src = strip_comments_and_strings(Path(path).read_text())
    out = {}
    for m in _FUNC_RE.finditer(src):
        name = m.group(1)
        if name in ("if", "for", "while", "switch", "return", "sizeof"):
            continue
        end = src.find("\n}", m.end())
        assert end != -1, f"unterminated function {name}"
        out[name] = src[m.end():end]
    return out


def calls(body: str, name: str) -> bool:
    return re.search(rf"\b{re.escape(name)}\s*\(", body) is not None


def mentions(body: str, ident: str) -> bool:
    return re.search(rf"\b{re.escape(ident)}\b", body) is not None
