"""Transport security: HTTPS for people, security headers for browsers (#152).

Encrypting what the web app sends (passwords, session tokens, student
records) is TLS's job: an extra cipher on top of plain HTTP would need a key
that reached the browser over that same unprotected channel. So the backend
refuses staff traffic that did not arrive over HTTPS, instead of encrypting
it twice.

Not affected:
- the computer the server runs on (loopback): traffic never leaves it;
- devices authenticating with a device key: gateway and hub TLS is a
  firmware option (#66); IMPRESS_DEVICE_HTTPS_ONLY makes it mandatory too;
- health checks and the public documentation portal.

Behind a reverse proxy the scheme comes from X-Forwarded-Proto, which
uvicorn trusts only from IMPRESS_FORWARDED_ALLOW_IPS (scripts/start.sh).
"""

from __future__ import annotations

import ipaddress
import re

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

from . import gpc
from .config import settings

# Routes a device calls with its key (device_caller): the device API and the
# direct answer/vote routes of older firmware.
_DEVICE_PATHS = re.compile(r"^/api/device/|^/api/quizzes/\d+/answer$|^/api/polls/\d+/vote$")
_ALWAYS_OPEN = re.compile(r"^/health$|^/api/health$|^/graph(/|$)")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
}
# The web app uses inline event handlers and Google Fonts; everything else is same-origin.
APP_CSP = ("default-src 'self'; script-src 'self' 'unsafe-inline'; "
           "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; "
           "img-src 'self' data:; connect-src 'self' ws: wss:; frame-ancestors 'none'; base-uri 'self'; "
           "form-action 'self'; object-src 'none'")
HSTS = "max-age=31536000"


def https_required() -> bool:
    return settings.REQUIRE_HTTPS if settings.REQUIRE_HTTPS is not None else not settings.DEBUG


def is_loopback(host: str | None) -> bool:
    try:
        return ipaddress.ip_address(host or "").is_loopback
    except ValueError:
        return host == "localhost"


def needs_https(path: str, scheme: str, client_host: str | None) -> bool:
    """Should this request be refused for arriving without TLS?"""
    if scheme in ("https", "wss") or not https_required() or is_loopback(client_host):
        return False
    if _ALWAYS_OPEN.search(path):
        return False
    if _DEVICE_PATHS.search(path):
        return gpc.device_https_only(settings)
    return True


_MESSAGE = ("This connection is not encrypted. Open imPress with https:// "
            "(ask your administrator for the address), so that passwords and class data are protected.")


async def enforce_https(request: Request, call_next):
    if needs_https(request.url.path, request.url.scheme, request.client.host if request.client else None):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": {"code": "HTTPS_REQUIRED", "message": _MESSAGE}}, status_code=403)
        return HTMLResponse(f"<!doctype html><meta charset=utf-8><title>HTTPS required</title>"
                            f"<p style='font:16px system-ui;margin:2rem'>{_MESSAGE}</p>", status_code=403)
    response = await call_next(request)
    for k, v in SECURITY_HEADERS.items():
        response.headers.setdefault(k, v)
    path = request.url.path
    if not path.startswith(("/graph", "/api/", "/static/")):
        response.headers.setdefault("Content-Security-Policy", APP_CSP)
    if path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    if request.url.scheme == "https":
        response.headers.setdefault("Strict-Transport-Security", HSTS)
    return response
