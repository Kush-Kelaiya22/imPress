"""Shared pytest fixtures for the imPress backend.

Every test gets a fresh SQLite database file and an in-process FastAPI
TestClient (no network, no running server). Environment is set BEFORE the
app is imported so pydantic-settings picks it up.
"""

import asyncio
import os
import shutil
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
    # A test site: unsigned test images, one administrator approving their own
    # uploads (#123). test_trusted_installer.py checks the strict defaults.
    "IMPRESS_FIRMWARE_ALLOW_UNSIGNED": "true",
    "IMPRESS_FIRMWARE_SINGLE_APPROVER": "true",
    # The in-process test client is neither HTTPS nor loopback; test_transport.py
    # checks the HTTPS rule itself (#152).
    "IMPRESS_REQUIRE_HTTPS": "false",
    "IMPRESS_TEMP_BACKUP_DIR": str(_TMP / "backups"),
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
    # uploaded firmware is state too: a file left by one test must not exist in the next
    shutil.rmtree(_TMP / "firmware_bins", ignore_errors=True)
    # v2.2 state next to the database: Degraded / debug-mode flags, test data, temporary backups
    (_TMP / "test.state.json").unlink(missing_ok=True)
    shutil.rmtree(_TMP / "test-data", ignore_errors=True)
    shutil.rmtree(_TMP / "backups", ignore_errors=True)


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
        _post = c.post

        def post(url, *args, **kwargs):
            """New accounts start with temporary credentials (v2.2); most tests are not about that, so the first
            sign-in's work is done for them. A test of the first-sign-in flow sends {"keep_pending": true}."""
            keep = bool((kwargs.get("json") or {}).pop("keep_pending", False)) if isinstance(kwargs.get("json"), dict) else False
            r = _post(url, *args, **kwargs)
            if url == "/api/admin/users" and r.status_code == 201 and not keep:
                finish_setup(c, r.json()["id"])
            return r
        c.post = post
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


def login(client, username="impress.default.superAdmin", password="admin123"):
    r = client.post("/api/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    client.cookies.clear()      # tests authenticate with the bearer token; the cookie path has its own tests
    return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def approved(client, headers, action, password="admin123", approver=None, approver_password=None):
    """Dual control (v2.2): request `action`, have it approved (by `approver` headers, or by the
    requester when they are the only super admin), return the approval id. The default
    profile has no delay."""
    r = client.post("/api/admin/approvals", headers=headers, json={"action": action, "params": {}, "password": password})
    assert r.status_code == 201, r.text
    aid = r.json()["id"]
    r = client.post(f"/api/admin/approvals/{aid}/approve", headers=approver or headers,
                    json={"password": approver_password or password})
    assert r.status_code == 200, r.text
    return aid


@pytest.fixture
def policy():
    """Change global-policy flags for one test: policy({"dual_control.delay_minutes": 10}). Root does this
    with a signed file or inline flags; a test sets the loaded values directly. Use after `client`."""
    from app import gpc
    saved = dict(gpc.current().values)

    def setter(flags: dict):
        for name, value in flags.items():
            assert name in gpc.FLAGS, name
            gpc.current().values[name] = value
    yield setter
    gpc.current().values.clear()
    gpc.current().values.update(saved)


def finish_setup(client, user_id):
    """New accounts start with temporary credentials (v2.2: 'pending setup'). Most tests are not about that:
    this is the first sign-in's work already done. Tests of the first-sign-in flow don't call it."""
    from sqlalchemy import update

    from app.database import async_session
    from app.dbgateway import SYSTEM, act_as
    from app.models import User
    from app.timeutil import istnow

    async def go():
        act_as(SYSTEM)
        async with async_session() as s:
            await s.execute(update(User).where(User.id == user_id).values(must_change_password=False, onboarded_at=istnow()))
            await s.commit()
    client.portal.call(go)


# ── Domain helpers (keep tests short and intention-revealing) ───────────────

PASSWORD = "Passw0rd!x"


def make_user(client, admin_headers, username, role="teacher", password=PASSWORD):
    """Create a user through the admin API; returns (user_id, auth headers). A super admin is created the way
    root creates one (the console's function): the API refuses to."""
    if role == "super_admin":
        from sqlalchemy import select

        from app.database import async_session
        from app.models import User
        from app.services import rootops
        client.portal.call(rootops.create_account, username, "super_admin", f"{username}@example.edu", username.title(), password)

        async def find():
            async with async_session() as s:
                return (await s.execute(select(User.id).where(User.username == username))).scalar_one()
        uid = client.portal.call(find)
        finish_setup(client, uid)
        return uid, auth(login(client, username, password))
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


def upload_firmware(client, headers, project="impress_class_s3", version="2.1.0", approve=True, **kw):
    """Register (and by default approve, so it can be pushed) a structurally
    valid image through the admin API; returns its bytes."""
    from firmware_images import make_image
    image = make_image(project, version, **kw)
    r = client.post("/api/admin/firmware", headers=headers,
                    files={"file": ("fw.bin", image, "application/octet-stream")})
    assert r.status_code == 200, r.text
    if approve:
        assert client.post(f"/api/admin/firmware/{r.json()['id']}/approve", headers=headers).status_code == 200
    return image
