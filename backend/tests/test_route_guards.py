"""Security review (#16 of the v2.1 brief): every route refuses a caller
without credentials, except an explicit public list. A new route that
forgets its guard fails here."""

import importlib
import re

from fastapi.routing import APIRoute

ROUTERS = ("auth", "admin", "classes", "quizzes", "polls", "device", "courses", "students", "firmware", "deployments")

# Deliberately public: signing in, liveness, and static CSV templates.
PUBLIC = {
    ("POST", "/api/auth/login"),
    ("GET", "/api/quizzes/questions/template.csv"),
    ("GET", "/api/admin/classes/import-template.csv"),
}


def _refused(r):
    """401/403, or 422 for the missing device-key header (a required
    `X-API-Key` is checked before the body, so the request never runs)."""
    if r.status_code in (401, 403):
        return True
    return r.status_code == 422 and any(e.get("loc", [None])[0] == "header" for e in r.json().get("detail", []))


def _routes():
    for name in ROUTERS:
        mod = importlib.import_module(f"app.routers.{name}")
        for router in (mod.router, getattr(mod, "live_router", None)):
            for r in getattr(router, "routes", []):
                if isinstance(r, APIRoute):
                    for method in r.methods - {"HEAD", "OPTIONS"}:
                        yield method, r.path


def test_every_route_needs_credentials(client):
    open_routes = []
    for method, path in sorted(set(_routes())):
        if (method, path) in PUBLIC:
            continue
        url = re.sub(r"\{[^}]+\}", "1", path)
        r = client.request(method, url, json={}) if method in ("POST", "PUT", "PATCH") else client.request(method, url)
        if not _refused(r):
            open_routes.append(f"{method} {path} -> {r.status_code}")
    assert open_routes == [], "\n".join(open_routes)


def test_device_routes_reject_a_wrong_key(client):
    bad = {"X-API-Key": "not-the-key"}
    for method, path in sorted(set(_routes())):
        if path.startswith("/api/device/"):
            url = re.sub(r"\{[^}]+\}", "1", path)
            r = client.request(method, url, headers=bad, **({"json": {}} if method == "POST" else {}))
            assert r.status_code in (401, 403), f"{method} {path} -> {r.status_code}"


def test_public_routes_are_still_reachable(client):
    for method, path in PUBLIC:
        r = client.request(method, path, **({"json": {"username": "x", "password": "y"}} if method == "POST" else {}))
        assert r.status_code in (200, 401), (method, path, r.status_code)     # 401 = wrong password, still public
