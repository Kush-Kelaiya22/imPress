"""Public documentation portal and generated Graphify assets."""


def test_graph_portal_lists_docs_and_uses_the_embedded_visualisation(client):
    response = client.get("/graph")
    assert response.status_code == 200
    assert "Documentation that follows" in response.text
    assert "/graph/visualization" in response.text
    assert "Search documentation" in response.text


def test_graph_search_is_case_insensitive_and_returns_real_docs(client):
    response = client.get("/graph/search", params={"q": "spi"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] > 0
    assert any(item["path"].startswith("docs/") for item in payload["results"])


def test_graph_assets_are_served_from_the_committed_graph(client):
    visualisation = client.get("/graph/visualization")
    data = client.get("/graph/data")
    assert visualisation.status_code == 200 and "html" in visualisation.headers["content-type"]
    assert data.status_code == 200 and data.json()["nodes"]
