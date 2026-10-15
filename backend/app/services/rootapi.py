"""Root's own way into the application's API (v2.2): the console calls the same routes the web app calls, in this
process, as the default super admin, so anything a super admin can do can be done from the root shell, with the same
validation, permissions, approvals and activity log. No network is involved.

The session it signs in with is made here and ended when the console closes. Writes are also recorded as made by
root in the activity log (console.api)."""

from __future__ import annotations

import json
from urllib.parse import urlsplit

from ..config import DEFAULT_SUPERADMIN
from ..database import async_session
from ..dbgateway import SYSTEM, act_as

_token: str | None = None
_session_id: int | None = None


async def _login() -> str:
    global _token, _session_id
    if _token:
        from ..auth import validate_session
        async with async_session() as db:
            _session, user, error = await validate_session(db, _token, refresh_activity=False)
        if user is not None and not error:
            return _token
        await close()
    from sqlalchemy import select

    from ..auth import create_session
    from ..models import User
    from . import boot_verify, bootstrap
    boot_verify._report["locked"] = False         # the host check belongs to the server process, not to this shell
    act_as(SYSTEM)
    async with async_session() as db:
        user = (await db.execute(select(User).where(User.username == DEFAULT_SUPERADMIN))).scalar_one_or_none()
        if user is None or not user.is_active:
            await bootstrap.ensure_default_superadmin(quiet=True)
            user = (await db.execute(select(User).where(User.username == DEFAULT_SUPERADMIN))).scalar_one()
        session, _token = await create_session(db, user)
        _session_id = session.id
    return _token


async def close() -> None:
    """End root's session."""
    global _token, _session_id
    if _session_id is not None:
        from sqlalchemy import update

        from ..models import UserSession
        act_as(SYSTEM)
        async with async_session() as db:
            await db.execute(update(UserSession).where(UserSession.id == _session_id).values(revoked=True, end_reason="signed_out"))
            await db.commit()
    _token = _session_id = None


async def call(method: str, path: str, body=None, files: dict | None = None) -> tuple[int, object]:
    """One request to the application. Returns (status, parsed JSON or text)."""
    from ..main import app
    token = await _login()
    url = urlsplit(path)
    raw = b"" if body is None else json.dumps(body).encode()
    headers = [(b"authorization", f"Bearer {token}".encode()), (b"host", b"root.local"), (b"x-impress-request", b"1"),
               (b"x-impress-background", b"1"), (b"user-agent", b"impress-root-console")]
    if raw:
        headers += [(b"content-type", b"application/json"), (b"content-length", str(len(raw)).encode())]
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": method.upper(), "scheme": "http",
             "path": url.path, "raw_path": url.path.encode(), "query_string": url.query.encode(), "headers": headers,
             "client": ("127.0.0.1", 1), "server": ("root.local", 80), "root_path": "", "state": {}}
    sent = {"done": False}
    out = {"status": 500, "body": b""}

    async def receive():
        if not sent["done"]:
            sent["done"] = True
            return {"type": "http.request", "body": raw, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(msg):
        if msg["type"] == "http.response.start":
            out["status"] = msg["status"]
        elif msg["type"] == "http.response.body":
            out["body"] += msg.get("body", b"")

    try:
        await app(scope, receive, send)
    finally:
        act_as(SYSTEM)                                   # the request raised the principal; the console is the system again
    text = out["body"].decode(errors="replace")
    if out["status"] == 200 and text.lstrip().lower().startswith("<!doctype"):      # the web app's catch-all page
        return 404, {"detail": {"message": f"No such route: {path}"}}
    try:
        return out["status"], json.loads(text) if text else None
    except ValueError:
        return out["status"], text


def routes() -> list[tuple[str, str]]:
    from ..main import app
    rows = []
    for path, ops in app.openapi().get("paths", {}).items():
        if path.startswith("/api"):
            rows += [(m.upper(), path) for m in ops if m.upper() not in ("HEAD", "OPTIONS")]
    return sorted(set(rows), key=lambda x: (x[1], x[0]))
