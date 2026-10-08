"""Shared pytest fixtures for the imPress backend.

Every test gets a fresh SQLite database file and an in-process FastAPI
TestClient (no network, no running server). Environment is set BEFORE the
app is imported so pydantic-settings picks it up.
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="impress-test-"))
os.environ.update({
    "IMPRESS_DATABASE_URL": f"sqlite+aiosqlite:///{_TMP / 'test.db'}",
    "IMPRESS_DEBUG": "false",
    "IMPRESS_JWT_SECRET": "test-jwt-secret-not-the-default",
    "IMPRESS_DEVICE_API_KEY": "test-device-key",
    "IMPRESS_INITIAL_ADMIN_PASSWORD": "admin123",
    "IMPRESS_FIRMWARE_DIR": str(_TMP / "firmware_bins"),
})
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bcrypt  # noqa: E402
import pytest  # noqa: E402

# Production hashes use bcrypt's default cost (12, ~0.25 s each). Every test
# seeds an admin and logs users in, so that cost dominated the suite's runtime.
# Cost 4 is the minimum; checkpw reads the cost from the hash, so nothing else changes.
_gensalt = bcrypt.gensalt
bcrypt.gensalt = lambda rounds=4, prefix=b"2b": _gensalt(rounds, prefix)
from fastapi.testclient import TestClient  # noqa: E402

DEVICE_KEY = "test-device-key"
DEVICE = {"X-API-Key": DEVICE_KEY}


async def _reset_db():
    # Delete the file rather than drop_all(): the schema has a foreign-key cycle
    # (class_sessions / esp_devices / student_enrollments) that SQLite can't
    # sort. The app's own startup (init_db → migrations) then builds the schema
    # exactly as on a fresh install.
    from app.database import engine
    await engine.dispose()
    (_TMP / "test.db").unlink(missing_ok=True)


# Fire-and-forget DB tasks the app spawns (presence pushes, WS presence
# refresh). If one outlives a test, its open SQLite connection makes the next
# test's _reset_db() fail with "database is locked".
_BACKGROUND_TASKS = {"_push_after_commit", "_touch_device_on_message"}


async def _drain_background_tasks(timeout=5.0):
    pending = [t for t in asyncio.all_tasks()
               if not t.done() and t.get_coro().__name__ in _BACKGROUND_TASKS]
    if pending:
        await asyncio.wait(pending, timeout=timeout)


@pytest.fixture
def client():
    """TestClient on an empty database (the app seeds the super admin)."""
    from app.main import app
    asyncio.run(_reset_db())
    with TestClient(app) as c:
        yield c
        c.portal.call(_drain_background_tasks)


@pytest.fixture
def db(client):
    """Run an async callable against a DB session: db(lambda s: ...)."""
    from app.database import async_session

    def run(fn):
        async def go():
            async with async_session() as s:
                result = await fn(s)
                await s.commit()
                return result
        return client.portal.call(go)
    return run


def login(client, username="admin", password="admin123"):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── Domain helpers (keep tests short and intention-revealing) ───────────────

PASSWORD = "Passw0rd!x"


def make_user(client, admin_headers, username, role="teacher", password=PASSWORD):
    """Create a user through the admin API; returns (user_id, auth headers)."""
    r = client.post("/api/admin/users", headers=admin_headers, json={
        "username": username, "email": f"{username}@example.edu", "password": password,
        "full_name": username.title(), "role": role})
    assert r.status_code == 201, r.text
    return r.json()["id"], auth(login(client, username, password))


def make_class(client, admin_headers, name="Physics", code="PHY101", activate=False, **extra):
    """Create a class via /api/admin/classes; optionally activate it."""
    r = client.post("/api/admin/classes", headers=admin_headers, json={"name": name, "code": code, **extra})
    assert r.status_code == 201, r.text
    cid = r.json()["id"]
    if activate:
        assert client.post(f"/api/classes/{cid}/activate", headers=admin_headers).status_code == 200
    return cid


def make_student(client, headers, roll="ABCDE12345", name="Asha Rao", **extra):
    r = client.post("/api/students/", headers=headers, json={"roll_number": roll, "student_name": name, **extra})
    assert r.status_code == 201, r.text
    return r.json()["id"]
