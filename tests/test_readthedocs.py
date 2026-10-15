"""Read the Docs configuration is complete and keeps the graph deployable."""

import ast
import re

from conftest import ROOT


def test_readthedocs_configuration_uses_reproducible_sphinx_build():
    config = (ROOT / ".readthedocs.yaml").read_text()
    assert re.search(r"^version:\s*2\s*$", config, re.M)
    assert "os: ubuntu-24.04" in config
    assert 'python: "3.12"' in config
    assert "configuration: docs/conf.py" in config
    assert "fail_on_warning: true" in config
    assert "requirements: docs/requirements.txt" in config


def test_sphinx_site_has_searchable_navigation_and_graph_page():
    index = (ROOT / "docs" / "index.md").read_text()
    graph = (ROOT / "docs" / "graph" / "index.md").read_text()
    assert "{toctree}" in index
    for document in ("README", "graph/index", "architecture/overview", "api/rest-api", "guides/deployment"):
        assert document in index
    assert 'src="visualization.html"' in graph
    assert "/graph/visualization" in graph


def test_docs_build_inputs_are_pinned_and_valid_python():
    requirements = (ROOT / "docs" / "requirements.txt").read_text().splitlines()
    required = {"Sphinx", "myst-parser", "sphinx-rtd-theme", "sphinx-copybutton", "sphinxcontrib-mermaid"}
    installed = {line.split("==", 1)[0] for line in requirements if line and not line.startswith("#")}
    assert required <= installed
    assert all("==" in line for line in requirements if line and not line.startswith("#"))
    ast.parse((ROOT / "docs" / "conf.py").read_text())
    assert (ROOT / "docs" / "_static" / "custom.css").is_file()


def test_sphinx_copies_the_committed_graph_at_build_time():
    config = (ROOT / "docs" / "conf.py").read_text()
    assert "graphify-out" in config
    assert "visualization.html" in config and "graph.json" in config
    assert 'output / "graph"' in config
    assert "builder-inited" in config


def test_every_documentation_page_is_listed_in_the_index():
    """A page the index does not list is unreachable on the published site (and -W fails the build)."""
    listed = set(re.findall(r"^([\w\-./]+)$", (ROOT / "docs" / "index.md").read_text(), re.M))
    pages = {p.relative_to(ROOT / "docs").with_suffix("").as_posix() for p in (ROOT / "docs").rglob("*.md")}
    pages = {p for p in pages if " 2" not in p and not p.startswith("_build") and p != "index"}   # " 2": sync-tool duplicates
    assert pages <= listed, sorted(pages - listed)


def test_the_published_site_says_which_release_it_describes():
    """#209: the site's 'latest' once showed v2.1 for a v2.2 release; the release comes from VERSION and a banner shows it."""
    conf = (ROOT / "docs" / "conf.py").read_text()
    assert 'release = "v2.1"' not in conf and "VERSION" in conf and '"github_version": line' in conf
    layout = (ROOT / "docs" / "_templates" / "layout.html").read_text()
    assert "impress_release" in layout and "impress-banner" in layout
