"""Sphinx configuration for the public imPress documentation site."""

from __future__ import annotations

import shutil
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
REPOSITORY_ROOT = DOCS_DIR.parent

project = "imPress"
copyright = "2026, imPress contributors"
author = "imPress contributors"
release = "v2.1"

extensions = ["myst_parser", "sphinx_copybutton", "sphinxcontrib.mermaid"]
source_suffix = {".md": "markdown"}
master_doc = "index"
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
myst_enable_extensions = ["colon_fence", "deflist", "fieldlist", "tasklist"]
myst_fence_as_directive = ["mermaid"]
# Existing guides link to GitHub-compatible heading IDs down to H6.
myst_heading_anchors = 6
# Two historical documents use deliberate template/decision-record heading
# structures. Their content is valid; retain the source structure rather than
# flattening it solely for the renderer.
suppress_warnings = ["myst.header"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_title = "imPress documentation"
html_theme_options = {"collapse_navigation": False, "navigation_depth": 4, "sticky_navigation": True, "includehidden": True}
html_context = {
    "display_github": True,
    "github_user": "Kush-Kelaiya22",
    "github_repo": "imPress",
    "github_version": "varun/v2.1",
    "conf_py_path": "/docs/",
}


def _publish_graph_visualization(app) -> None:
    """Expose the generated graph beneath the hosted ``/graph/`` page."""
    graph_source = REPOSITORY_ROOT / "graphify-out" / "graph.html"
    graph_data = REPOSITORY_ROOT / "graphify-out" / "graph.json"
    if not graph_source.is_file() or not graph_data.is_file():
        raise RuntimeError("Graphify output is required: run `graphify update .`")
    output = Path(app.outdir)
    graph_output = output / "graph"
    graph_output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(graph_source, graph_output / "visualization.html")
    shutil.copy2(graph_data, graph_output / "graph.json")


def setup(app) -> dict[str, bool]:
    app.connect("builder-inited", _publish_graph_visualization)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
