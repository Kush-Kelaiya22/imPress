#!/usr/bin/env python3
"""Build imPress's deterministic Graphify graph and enrich non-code coverage.

Graphify's AST extractor maps executable source locally.  This wrapper adds
tracked documentation/configuration file nodes and verified protocol nodes so
the keyless CI graph also covers the repository's non-code architecture.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

COMPONENTS = {
    "backend": ("Python/FastAPI backend", ("backend/",)),
    "frontend": ("Frontend", ("frontend/",)),
    "firmware": ("ESP32 firmware", ("firmware/",)),
    "automation": ("GitHub automation", (".github/", "scripts/")),
    "documentation": ("Documentation", ("docs/", "README.md", "CONTRIBUTING.md", "CHANGELOG.md")),
    "configuration": ("Configuration", ("pyproject.toml", "Dockerfile", ".env.example", ".gitignore")),
}
PROTOCOLS = {
    "rest-api": ("REST API", "backend/app/routers/", "backend"),
    "websocket": ("WebSocket live session protocol", "firmware/class_c6/main/ws_client", "firmware"),
    "spi": ("SPI framed batch protocol", "firmware/class_c6/main/spi_slave", "firmware"),
}


def run(*args: str, cwd: Path = ROOT) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def tracked_files() -> list[str]:
    return subprocess.check_output(["git", "ls-files"], cwd=ROOT, text=True).splitlines()


def node_id(prefix: str, path: str) -> str:
    return f"impress_{prefix}_" + "".join(c if c.isalnum() else "_" for c in path).strip("_").lower()


def component_for(path: str) -> str | None:
    for key, (_, prefixes) in COMPONENTS.items():
        if any(path == prefix or path.startswith(prefix) for prefix in prefixes):
            return key
    return None


def enrich() -> None:
    graph_path = OUT / "graph.json"
    graph = json.loads(graph_path.read_text())
    nodes, links = graph["nodes"], graph["links"]
    ids = {node["id"] for node in nodes}
    pairs = {(edge["source"], edge["target"], edge.get("relation")) for edge in links}

    def add_node(identifier: str, label: str, **fields: str) -> None:
        if identifier not in ids:
            nodes.append({"id": identifier, "label": label, "_origin": "repository_catalog", **fields})
            ids.add(identifier)

    def add_edge(source: str, target: str, relation: str) -> None:
        edge = (source, target, relation)
        if edge not in pairs:
            links.append({"source": source, "target": target, "relation": relation,
                          "confidence": "EXTRACTED", "_origin": "repository_catalog"})
            pairs.add(edge)

    for key, (label, _) in COMPONENTS.items():
        add_node(f"impress_component_{key}", label, type="component", source_file="repository catalog")

    for path in tracked_files():
        if path.startswith("graphify-out/"):
            continue
        kind = "documentation" if path.endswith(".md") else "configuration"
        if kind == "documentation" or path.endswith((".yml", ".yaml", ".toml", ".json")) or path in {"Dockerfile", ".env.example"}:
            identifier = node_id(kind, path)
            add_node(identifier, path, type=kind, source_file=path)
            owner = component_for(path) or kind
            add_edge(f"impress_component_{owner}", identifier, "contains")

    for key, (label, evidence, owner) in PROTOCOLS.items():
        if not any(path.startswith(evidence) for path in tracked_files()):
            raise RuntimeError(f"protocol evidence missing: {evidence}")
        identifier = f"impress_protocol_{key}"
        add_node(identifier, label, type="protocol", source_file=evidence)
        add_edge(f"impress_component_{owner}", identifier, "implements")
        if key == "rest-api":
            add_edge(identifier, "impress_component_frontend", "serves")
        elif key == "websocket":
            add_edge(identifier, "impress_component_backend", "connects_to")
        else:
            add_edge(identifier, "impress_component_backend", "transports_to")

    graph_path.write_text(json.dumps(graph, indent=2, sort_keys=True) + "\n")


def append_coverage() -> None:
    report = OUT / "GRAPH_REPORT.md"
    report.write_text(report.read_text().rstrip() + "\n\n## Repository Coverage\n"
                      "- Python/FastAPI backend, frontend, and ESP32 firmware are AST-extracted by Graphify.\n"
                      "- Tracked Markdown documentation and configuration files are cataloged deterministically.\n"
                      "- Verified protocol nodes cover REST, WebSocket live sessions, and SPI framed batches.\n"
                      "- This CI mode is keyless: semantic document summarization is intentionally disabled.\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--graphify", default=os.environ.get("GRAPHIFY_BIN") or shutil.which("graphify") or "graphify")
    args = parser.parse_args()
    run(args.graphify, "extract", ".", "--code-only", "--out", ".", "--max-workers", "4")
    run(args.graphify, "cluster-only", ".", "--no-label")
    enrich()
    # Re-export after enrichment so graph.html contains the catalog nodes too.
    run(args.graphify, "export", "html", "--graph", str(OUT / "graph.json"), "--output", str(OUT / "graph.html"))
    append_coverage()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
