#!/usr/bin/env python3
"""Fail clearly if committed Graphify output is incomplete, stale, or unsafe."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"
SENSITIVE = re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|sk-[A-Za-z0-9]{20,}|BEGIN (?:RSA |EC )?PRIVATE KEY)")


def source_commit() -> str:
    return subprocess.check_output(
        ["git", "log", "-1", "--format=%H", "--", ".", ":(exclude)graphify-out/**"],
        cwd=ROOT, text=True,
    ).strip()


def main() -> int:
    required = [OUT / "graph.json", OUT / "graph.html", OUT / "GRAPH_REPORT.md"]
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    if missing:
        raise SystemExit(f"missing or empty Graphify output: {', '.join(missing)}")
    graph = json.loads((OUT / "graph.json").read_text())
    nodes, links = graph.get("nodes", []), graph.get("links", [])
    if len(nodes) < 100 or len(links) < 100:
        raise SystemExit(f"graph is not meaningful: {len(nodes)} nodes, {len(links)} links")
    labels = {node.get("label") for node in nodes}
    needed = {"Python/FastAPI backend", "Frontend", "ESP32 firmware", "REST API", "WebSocket live session protocol", "SPI framed batch protocol"}
    if not needed <= labels:
        raise SystemExit(f"missing component coverage: {sorted(needed - labels)}")
    built = graph.get("built_at_commit")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    expected = source_commit()
    if built and not expected.startswith(built):
        raise SystemExit(f"stale graph: built from {built}, latest source commit is {expected}")
    text = "\n".join(path.read_text(errors="replace") for path in required)
    if str(ROOT) in text or SENSITIVE.search(text):
        raise SystemExit("generated graph contains a sensitive value or local absolute path")
    print(f"Graphify validation passed: {len(nodes)} nodes, {len(links)} links, commit {head[:12]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
