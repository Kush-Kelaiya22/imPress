"""#12: raw bearer tokens are never persisted; legacy raw rows are revoked."""

import shutil
import subprocess
from datetime import timedelta
from pathlib import Path

import pytest
from sqlalchemy import select, text

from conftest import auth, login

REPO = Path(__file__).resolve().parents[2]


def _all_session_values(db):
    async def q(s):
        rows = (await s.execute(text("SELECT * FROM user_sessions"))).all()
        return [str(v) for row in rows for v in row]
    return db(q)


def test_raw_token_not_stored_anywhere(client, db):
    tok = login(client)
    assert client.get("/api/auth/me", headers=auth(tok)).status_code == 200
    values = _all_session_values(db)
    assert values, "session row expected"
    assert tok not in values
    assert not any(tok in v for v in values)


def test_legacy_raw_token_rows_revoked_and_scrubbed(client, db):
    from app.auth import _sha256_hex
    from app.database import _scrub_raw_session_tokens
    from app.models import User, UserSession
    from app.timeutil import istnow

    raw = "impress_legacy-token-from-an-old-db"

    async def insert_legacy(s):
        admin = (await s.execute(select(User).where(User.username == "admin"))).scalar_one()
        now = istnow()
        s.add(UserSession(user_id=admin.id, token_hash=_sha256_hex(raw), session_token=raw,
                          created_at=now, last_activity_at=now,
                          expires_at=now + timedelta(hours=6), revoked=False))
    db(insert_legacy)
    # Before the scrub the leaked token works — that's the exposure.
    assert client.get("/api/auth/me", headers=auth(raw)).status_code == 200

    assert client.portal.call(_scrub_raw_session_tokens) == 1
    assert client.get("/api/auth/me", headers=auth(raw)).status_code == 401
    assert raw not in _all_session_values(db)
    assert client.portal.call(_scrub_raw_session_tokens) == 0      # idempotent

    # Sessions created by current code are untouched by the scrub.
    tok = login(client)
    client.portal.call(_scrub_raw_session_tokens)
    assert client.get("/api/auth/me", headers=auth(tok)).status_code == 200


@pytest.mark.skipif(not (REPO / ".git").exists() or not shutil.which("git"), reason="needs a git checkout")
def test_no_databases_tracked_in_git():
    tracked = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split()
    bad = [f for f in tracked if f.endswith((".db", ".sqlite")) or ".db.bak" in f or f.endswith("sdkconfig.old")]
    assert bad == []
    ignored = subprocess.run(["git", "check-ignore", "-q", "backend/impress.db"], cwd=REPO)
    assert ignored.returncode == 0, "*.db must be gitignored"
