"""Docs stay in sync with the code: links resolve, every route and setting is
documented, diagrams are well-formed."""

import re
import unicodedata

import pytest

from conftest import ROOT

DOCS = [ROOT / "README.md"] + sorted((ROOT / "docs").rglob("*.md"))


def _strip_code(text):
    return re.sub(r"```.*?```", "", text, flags=re.S)


def _slug(heading):
    out = [c for c in heading.strip().lower()
           if c.isalnum() or c in "-_ " or unicodedata.category(c).startswith(("L", "N"))]
    return "".join(out).replace(" ", "-")


def _anchors(path):
    seen, res = {}, set()
    for m in re.finditer(r"^#{1,6}\s+(.+?)\s*$", _strip_code(path.read_text()), re.M):
        s = _slug(m.group(1))
        n = seen.get(s, 0)
        seen[s] = n + 1
        res.add(s if n == 0 else f"{s}-{n}")
    return res


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_internal_links_and_anchors_resolve(doc):
    for target in re.findall(r"\]\(([^)\s]+)\)", _strip_code(doc.read_text())):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        path, _, anchor = target.partition("#")
        dest = (doc.parent / path).resolve() if path else doc.resolve()
        assert dest.exists(), f"{doc.name}: broken link {target}"
        if anchor and dest.suffix == ".md":
            assert anchor in _anchors(dest), f"{doc.name}: missing anchor {target}"


@pytest.mark.parametrize("doc", DOCS, ids=lambda p: str(p.relative_to(ROOT)))
def test_code_fences_are_balanced_and_mermaid_typed(doc):
    text = doc.read_text()
    assert text.count("```") % 2 == 0, f"{doc.name}: unbalanced code fence"
    for block in re.findall(r"```mermaid\n(.*?)```", text, re.S):
        first = block.strip().splitlines()[0].split()[0]
        assert first in {"flowchart", "sequenceDiagram", "stateDiagram-v2", "erDiagram", "graph", "classDiagram"}, first


def _route_paths():
    import importlib
    from fastapi.routing import APIRoute
    paths = set()
    for name in ("auth", "admin", "classes", "quizzes", "polls", "device", "courses", "students", "firmware"):
        mod = importlib.import_module(f"app.routers.{name}")
        for router in (mod.router, getattr(mod, "live_router", None)):
            for r in getattr(router, "routes", []):
                if isinstance(r, APIRoute):
                    paths.add(re.sub(r"\{[^}]+\}", "{}", r.path).rstrip("/") or "/")
    return paths


def test_every_api_route_is_documented(monkeypatch):
    monkeypatch.setenv("IMPRESS_DEBUG", "true")
    docs = " ".join((ROOT / f"docs/api/{f}").read_text() for f in ("rest-api.md", "device-api.md"))
    # paths may contain dots (template.csv); a sentence-ending period is not part of one
    documented = {re.sub(r"\{[^}]+\}", "{}", p).rstrip(".").rstrip("/")
                  for p in re.findall(r"(/api/[A-Za-z0-9_/{}.\-]+)", docs)}
    missing = sorted(p for p in _route_paths() if p not in documented)
    assert missing == [], f"undocumented routes: {missing}"


def test_every_setting_is_documented():
    from app.config import Settings
    config_doc = (ROOT / "docs/guides/configuration.md").read_text()
    env_example = (ROOT / "backend/.env.example").read_text()
    for field in Settings.model_fields:
        assert f"IMPRESS_{field}" in config_doc, f"IMPRESS_{field} missing from docs/guides/configuration.md"
    for key in ("IMPRESS_JWT_SECRET", "IMPRESS_DEVICE_API_KEY", "IMPRESS_DEBUG", "IMPRESS_INITIAL_ADMIN_PASSWORD"):
        assert key in env_example


def test_readme_is_professional_plain_text():
    text = (ROOT / "README.md").read_text()
    emoji = [c for c in text if unicodedata.category(c) == "So" and ord(c) > 0x2600]
    assert emoji == [], f"README contains emoji: {set(emoji)}"
    for section in ("Quick start", "Architecture", "Testing", "Documentation"):
        assert re.search(rf"^##\s+.*{section}", text, re.M | re.I), section
