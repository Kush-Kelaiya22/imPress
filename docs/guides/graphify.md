# Graphify knowledge graph

imPress keeps a committed, queryable Graphify knowledge graph in `graphify-out/`:

- `graph.json` is the machine-readable graph.
- `graph.html` is the interactive local visualization; open it in a browser.
- `GRAPH_REPORT.md` is the architecture and coverage summary.

## Install and generate locally

Use the official PyPI package (the package name has two `y` characters):

```bash
uv tool install graphifyy
graphify install --project --platform codex
python scripts/graphify_generate.py
python scripts/validate_graphify.py
```

The project-scoped install adds the Codex skill under `.codex/` and appends
query-first guidance to `AGENTS.md`. After generating, prefer commands such as
`graphify query "how do live votes reach devices?"`, `graphify path "FastAPI"
"WebSocket live session protocol"`, and `graphify explain "SPI framed batch
protocol"` before broad source searches.

The generator is deliberately keyless and deterministic. Graphify AST-extracts
the Python/FastAPI backend, frontend, firmware, and supported configuration;
the wrapper catalogs tracked Markdown/configuration files and verified REST,
WebSocket, and SPI relationships. This keeps CI free of API keys and LLM cost.
It does not attempt LLM-authored summaries of documentation.

## GitHub synchronization

`.github/workflows/graphify.yml` runs on every source or documentation push to
`varun/v2.1` and on manual dispatch. It installs the pinned official CLI,
regenerates and validates the graph, then commits only changed published graph
files. Graph-only commits are ignored by the path filter and bot actor guard.

Runs queue per branch. Before pushing, a run verifies that its source SHA is
still the branch head; an older run therefore cannot publish a graph for an
older source revision. If direct writes are blocked by branch protection, it
pushes a dedicated automation branch and opens a pull request instead.

The workflow does not depend on local hooks: contributors may push without
Graphify installed and GitHub will update the graph. Its cache contains only
downloaded Graphify dependencies; source is always re-scanned against the
checked-out commit.

## Viewing the graph and documentation

The deployed backend exposes a public documentation portal at `/graph`. It has
client-side search backed by `/graph/search`, an interactive embedded graph at
`/graph/visualization`, and the raw graph at `/graph/data`. The portal indexes
the committed Markdown documentation and links to the exact `varun/v2.1`
source on GitHub. It does not use a GitHub iframe, so it also works from a
private or offline classroom deployment. Docker images copy both `docs/` and
the three published Graphify files to make these routes available.

## Hooks and troubleshooting

Each contributor must opt in on their own machine:

```bash
graphify hook install
graphify hook status
```

The hooks update the graph after commits and branch checkouts. They do not
replace CI. To remove them, run `graphify hook uninstall`.

If generation fails, confirm Python 3.12+, `graphify --version`, and that the
working tree has no ignored runtime files that should be modeled. Run the two
commands in the local-generation section and inspect the workflow log. A stale
graph fails validation when its `built_at_commit` is not the latest commit that
changed graph input; graph-only automation commits are therefore current and do
not create churn on a manual rerun.
