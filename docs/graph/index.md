# Interactive knowledge graph

This is the hosted documentation graph page: on Read the Docs its stable URL is
`/graph/`. It is generated from the same source commit as the documentation
build and maps the FastAPI backend, frontend, ESP32 firmware, protocols,
configuration and documentation.

Select a node to inspect it, search for names in the graph's right-hand panel,
or filter a community to focus the view.

```{raw} html
<p class="graph-open-link"><a href="visualization.html" target="_blank" rel="noopener">Open the graph in a full page</a></p>
<iframe class="graph-frame" src="visualization.html" title="imPress interactive knowledge graph" loading="lazy"></iframe>
```

If the embedded view is constrained by a browser extension, use the full-page
link above. The deployed imPress service independently exposes this same
visualization at `/graph/visualization`, with searchable documentation at
`/graph`.

## Freshness and troubleshooting

Graphify updates `graphify-out/` automatically on the integration branch. The
Read the Docs build copies that committed `graph.html` and `graph.json` into
this page's output directory, so the documentation site never follows a
different source revision. For local generation, validation and CI behaviour,
see the [Graphify guide](../guides/graphify.md).
