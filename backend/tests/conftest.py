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

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

DEVICE_KEY = "test-device-key"
DEVICE = {"X-API-Key": DEVICE_KEY}


async def _reset_db():
    from app.database import Base, engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


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

