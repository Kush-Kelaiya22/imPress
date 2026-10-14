"""Route × caller matrix (#122): which status every route returns to each kind
of caller, against the same seeded data. The snapshot in
fixtures/route_matrix.json was recorded before the authorization refactor; a
change in who may call what shows up here as a diff, never silently.

Regenerate only for an intended permission change, and say so in the PR:
    IMPRESS_UPDATE_ROUTE_MATRIX=1 pytest backend/tests/test_route_matrix.py
"""

import json
import os
import re
from pathlib import Path

import pytest

from conftest import PASSWORD, auth, login, make_class, make_student, make_user
from test_route_guards import _routes

SNAPSHOT = Path(__file__).parent / "fixtures" / "route_matrix.json"
CALLERS = ("anonymous", "teacher_owner", "teacher_other", "admin", "super_admin")


def _seed(client):
    su = auth(login(client))
    owner, owner_h = make_user(client, su, "owner1")
    _, other_h = make_user(client, su, "other1")
    _, admin_h = make_user(client, su, "admin1", role="admin")
    cid = make_class(client, su, name="Owned", code="OWN101", teacher_id=owner)       # id 1
    make_class(client, su, name="Elsewhere", code="ELS101", teacher_id=owner + 1)      # id 2, other1's
    assert client.post("/api/quizzes/", headers=owner_h, json={
        "class_session_id": cid, "title": "Q", "questions": [
            {"question_text": "2+2?", "options": ["3", "4"], "correct_option": 1}]}).status_code == 201
    assert client.post("/api/polls/", headers=owner_h, json={
        "class_session_id": cid, "title": "P", "options": ["a", "b"], "poll_mode": "planned"}).status_code == 201
    sid = make_student(client, owner_h, roll="ROLL000001")
    client.post(f"/api/admin/classes/{cid}/enroll", headers=owner_h, json={"student_id": sid})
    users = {"teacher_owner": "owner1", "teacher_other": "other1", "admin": "admin1"}
    # A fresh login for every request: a route that ends the session (logout)
    # must not turn every later route into a 401.
    return lambda caller: {} if caller == "anonymous" else auth(
        login(client) if caller == "super_admin" else login(client, users[caller], PASSWORD))


def _matrix(client, headers_for):
    out = {}
    order = {"GET": 0, "POST": 1, "PUT": 1, "PATCH": 1, "DELETE": 2}   # reads see the seeded data
    for method, path in sorted(set(_routes()), key=lambda r: (order[r[0]], r[1], r[0])):
        if path == "/api/events":          # an endless stream; test_system.py covers it
            continue
        url = re.sub(r"\{[^}]+\}", "1", path)
        kw = {"json": {}} if method in ("POST", "PUT", "PATCH") else {}
        out[f"{method} {path}"] = client.request(method, url, headers=headers_for(), **kw).status_code
    return out


@pytest.mark.parametrize("caller", CALLERS)
def test_route_matrix_matches_snapshot(client, caller):
    headers = _seed(client)
    got = _matrix(client, lambda: headers(caller))
    data = json.loads(SNAPSHOT.read_text()) if SNAPSHOT.exists() else {}
    if os.environ.get("IMPRESS_UPDATE_ROUTE_MATRIX"):
        data[caller] = got
        SNAPSHOT.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
        pytest.skip("snapshot updated")
    want = data[caller]
    diff = {k: (want.get(k), v) for k, v in got.items() if want.get(k) != v}
    diff.update({k: (v, None) for k, v in want.items() if k not in got})
    assert not diff, f"{caller}: route → (snapshot, now)\n" + "\n".join(f"  {k}: {v}" for k, v in sorted(diff.items()))
