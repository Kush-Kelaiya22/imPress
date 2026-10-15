"""The error catalogue (impress.errors.json) and one shape for every error response.

Every HTTP error keeps its `detail` exactly as before and gains an `error` object, so a client (or a person reading a
log) always finds the same four things whatever raised it:

    {"detail": ..., "error": {"code": "STEP_UP_FAILED", "status": 403, "title": "...", "message": "...", "reference": "ab12cd34"}}

The same code is sent in the `X-Impress-Error` header. A code that routes use but the catalogue does not list fails the
build (backend/tests/test_errors.py), so the catalogue is the complete list. Unexpected faults answer 500 INTERNAL_ERROR
with a reference that matches the line in the server log; the trace is never sent.
"""

from __future__ import annotations

import json
import logging
import secrets
from functools import lru_cache

from .config import BACKEND_DIR

logger = logging.getLogger(__name__)
FILE = BACKEND_DIR / "impress.errors.json"

# What a status means when a route gives no code of its own.
DEFAULT_CODE = {400: "BAD_REQUEST", 401: "UNAUTHENTICATED", 403: "FORBIDDEN", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED",
                409: "CONFLICT", 410: "GONE", 413: "PAYLOAD_TOO_LARGE", 422: "VALIDATION_FAILED", 429: "RATE_LIMITED",
                500: "INTERNAL_ERROR", 501: "NOT_IMPLEMENTED", 503: "SERVICE_UNAVAILABLE"}


@lru_cache(maxsize=1)
def catalogue() -> dict:
    """{code: {category, http, title, description, fix}}"""
    try:
        doc = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        logger.error("the error catalogue %s is missing or unreadable", FILE)
        return {}
    return {e["code"]: {**e, "category": name} for name, c in doc["categories"].items() for e in c["errors"]}


def describe(code: str) -> dict | None:
    return catalogue().get(code)


def categories() -> dict:
    out: dict[str, list[str]] = {}
    for code, e in catalogue().items():
        out.setdefault(e["category"], []).append(code)
    return out


def _message(detail, status: int) -> tuple[str, str]:
    """(code, message) from whatever a route put in `detail`."""
    if isinstance(detail, dict):
        return str(detail.get("code") or DEFAULT_CODE.get(status, "BAD_REQUEST")), str(detail.get("message") or detail.get("detail") or "")
    if isinstance(detail, list):
        return "VALIDATION_FAILED", "; ".join(str(d.get("msg", d)) if isinstance(d, dict) else str(d) for d in detail)[:400]
    return DEFAULT_CODE.get(status, "BAD_REQUEST"), str(detail or "")


def envelope(status: int, detail, reference: str = "") -> dict:
    code, message = _message(detail, status)
    known = describe(code) or {}
    out = {"code": code, "status": status, "title": known.get("title", ""), "message": message or known.get("title", "")}
    if reference:
        out["reference"] = reference
    return out


def respond(status: int, detail, headers: dict | None = None, reference: str = ""):
    from fastapi.responses import JSONResponse
    err = envelope(status, detail, reference)
    return JSONResponse({"detail": detail, "error": err}, status_code=status,
                        headers={**(headers or {}), "X-Impress-Error": err["code"]})


def install(app) -> None:
    from fastapi.exceptions import RequestValidationError
    from fastapi.encoders import jsonable_encoder
    from starlette.exceptions import HTTPException as StarletteHTTPException

    @app.exception_handler(StarletteHTTPException)
    async def _http(request, exc):
        return respond(exc.status_code, exc.detail, getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def _validation(request, exc):
        return respond(422, jsonable_encoder(exc.errors()))

    @app.exception_handler(Exception)
    async def _unexpected(request, exc):
        ref = secrets.token_hex(4)
        logger.exception("unhandled error [%s] on %s %s", ref, request.method, request.url.path)
        return respond(500, "An unexpected error occurred. Quote the reference to whoever runs the server.", reference=ref)


def reference() -> str:
    """Markdown for docs/reference/errors.md, from the catalogue."""
    doc = json.loads(FILE.read_text(encoding="utf-8"))
    out = ["# Error reference", "",
           "Generated from `backend/impress.errors.json` by `python -m app.errors`; do not edit by hand. Every error response "
           "carries `error.code` and the `X-Impress-Error` header; the console explains one with `errors CODE`.", ""]
    for name, body in doc["categories"].items():
        out += [f"## {name.replace('_', ' ').capitalize()}", "", body["about"], "",
                "| Code | HTTP | Meaning | What to do |", "|---|---|---|---|"]
        for e in body["errors"]:
            http = e["http"] or "-"
            out.append(f"| `{e['code']}` | {http} | **{e['title']}.** {e['description']} | {e['fix']} |")
        out.append("")
    return "\n".join(out)


if __name__ == "__main__":
    import sys
    sys.stdout.write(reference())
