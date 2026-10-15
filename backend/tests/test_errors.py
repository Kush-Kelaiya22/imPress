"""The error catalogue is complete, well formed, and every error response has one shape."""

import json
import re
from pathlib import Path

import pytest

from fastapi.routing import APIRoute

from app import errors
from conftest import auth, login

APP = Path(__file__).resolve().parents[1] / "app"
CATALOGUE = Path(__file__).resolve().parents[1] / "impress.errors.json"


def _codes_in_source() -> set[str]:
    found = set()
    for path in APP.rglob("*.py"):
        text = path.read_text()
        found |= set(re.findall(r'"code":\s*"([A-Z][A-Z0-9_]+)"', text))
        found |= set(re.findall(r'(?:_err|forbidden|BackupError|TestModeError|PolicyRefused|RootAuthError)\(\s*(?:\d+,\s*)?"([A-Z][A-Z0-9_]+)"', text))
    return found


def test_every_code_the_server_can_raise_is_in_the_catalogue():
    missing = sorted(_codes_in_source() - set(errors.catalogue()))
    assert not missing, f"add these to impress.errors.json: {missing}"


def test_the_catalogue_is_well_formed():
    doc = json.loads(CATALOGUE.read_text())
    assert doc["_readme"] and len(doc["categories"]) >= 12
    seen = set()
    for category, body in doc["categories"].items():
        assert body["about"] and body["errors"], category
        for e in body["errors"]:
            assert set(e) == {"code", "http", "title", "description", "fix"}, e
            assert re.fullmatch(r"[A-Z][A-Z0-9_]+", e["code"]) and e["code"] not in seen, e["code"]
            seen.add(e["code"])
            assert e["http"] == 0 or 200 <= e["http"] <= 599, e
            assert len(e["title"]) > 3 and len(e["description"]) > 15 and e["fix"], e["code"]
    assert len(seen) >= 120


def test_every_generic_http_status_has_a_default_code():
    for status, code in errors.DEFAULT_CODE.items():
        assert errors.describe(code)["http"] == status, code


def test_the_error_reference_page_is_current():
    from app import errors as e
    page = Path(__file__).resolve().parents[2] / "docs/reference/errors.md"
    assert page.read_text() == e.reference(), "run  python -m app.errors > docs/reference/errors.md"


def test_an_error_keeps_its_detail_and_gains_a_uniform_error_object(client):
    r = client.post("/api/auth/login", json={"username": "nobody", "password": "x"})
    assert r.status_code == 401 and r.headers["x-impress-error"] == "UNAUTHENTICATED"
    assert r.json()["detail"] == "Invalid username or password"                                  # unchanged for old clients
    err = r.json()["error"]
    assert err["status"] == 401 and err["code"] == "UNAUTHENTICATED" and err["message"] and err["title"]


def test_a_coded_detail_is_carried_over(client):
    h = auth(login(client))
    r = client.post("/api/admin/approvals", headers=h, json={"action": "nope", "params": {}, "password": "admin123"})
    assert r.status_code == 422 and r.headers["x-impress-error"] == "UNKNOWN_ACTION"
    assert r.json()["error"]["code"] == "UNKNOWN_ACTION" and r.json()["detail"]["code"] == "UNKNOWN_ACTION"


@pytest.mark.parametrize("method,path,status,code", [
    ("get", "/api/no/such/route", 404, "NOT_FOUND"),
    ("delete", "/api/auth/login", 405, "METHOD_NOT_ALLOWED"),
    ("get", "/api/admin/users", 401, "UNAUTHENTICATED"),
])
def test_http_failures_use_the_generic_codes(client, method, path, status, code):
    r = getattr(client, method)(path)
    assert r.status_code == status and r.json()["error"]["code"] == code and r.headers["x-impress-error"] == code


def test_a_validation_failure_lists_the_fields(client):
    r = client.post("/api/auth/login", json={"username": 5})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_FAILED"
    assert isinstance(r.json()["detail"], list) and r.json()["detail"]


def test_a_crash_is_a_500_with_a_reference_and_no_trace(client):
    from app.main import app

    async def boom():
        raise RuntimeError("secret internal detail")
    app.router.routes.insert(0, APIRoute("/api/_boom_for_tests", boom, methods=["GET"]))     # before the page fallback
    quiet = type(client)(app, raise_server_exceptions=False)
    r = quiet.get("/api/_boom_for_tests")
    assert r.status_code == 500 and r.json()["error"]["code"] == "INTERNAL_ERROR"
    assert re.fullmatch(r"[0-9a-f]{8}", r.json()["error"]["reference"])
    assert "secret internal detail" not in r.text and "Traceback" not in r.text


def test_the_console_and_the_api_can_look_codes_up(client):
    h = auth(login(client))
    data = client.get("/api/system/errors", headers=h).json()
    assert "STEP_UP_FAILED" in data["errors"] and "authentication" in data["categories"]
    assert client.get("/api/system/errors").status_code == 401


def test_the_console_explains_a_code():
    import io

    from app.console import Console
    out = io.StringIO()
    con = Console(out=out)
    try:
        con.onecmd("errors step_up_failed")
        con.onecmd("errors dual_control")
        con.onecmd("errors NOPE")
    finally:
        con.close()
    text = out.getvalue()
    assert "what to do" in text and "STEP_UP_LOCKED" in text and "no such error code or category" in text
