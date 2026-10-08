"""#43 fault injection on the answer path: what the gateway's retry rules
(keep a batch on 5xx, drop it on 4xx) meet when the database fails, a
response is lost, the gateway drops off, or two copies race."""

import threading

import pytest
from sqlalchemy import func, select

from conftest import auth, login, make_class, make_student
from gateway_sim import Gateway, answer

GW = "48:F6:EE:00:00:C6"
ROLLS = ["ABCDE12340", "ABCDE12341", "ABCDE12342"]


@pytest.fixture
def live(client):
    h = auth(login(client))
    cid = make_class(client, h, classroom_code="RM-1")
    for roll in ROLLS:
        make_student(client, h, roll=roll)
    gw = Gateway(client, GW, "RM-1")
    gw.register()
    qid = client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "q", "options": ["a", "b", "c", "d"], "correct_option": 0}]}).json()["id"]
    assert client.post(f"/api/quizzes/{qid}/start", headers=h).status_code == 200
    return h, gw, qid


def _stored(db):
    from app.models import QuizAnswer

    async def q(s):
        return await s.scalar(select(func.count()).select_from(QuizAnswer))
    return db(q)


def test_a_failed_commit_stores_nothing_and_the_retry_stores_once(client, db, live, monkeypatch):
    from sqlalchemy.exc import OperationalError
    from sqlalchemy.ext.asyncio import AsyncSession
    _, gw, qid = live
    real_commit, failures = AsyncSession.commit, [1]

    async def flaky(self):
        if failures:
            failures.pop()
            raise OperationalError("COMMIT", {}, Exception("database is locked"))
        return await real_commit(self)
    monkeypatch.setattr(AsyncSession, "commit", flaky)

    gw.relay(*[answer(qid, 0, r, 1) for r in ROLLS])
    assert gw.flush() == 503                       # was an unhandled 500 before #43
    assert _stored(db) == 0 and len(gw.pending) == 3                 # kept for the retry
    assert gw.flush() == 200 and gw.last_batch["processed"] == 3
    assert _stored(db) == 3


def test_a_lost_response_makes_the_gateway_resend_harmlessly(client, db, live):
    _, gw, qid = live
    batch = [answer(qid, 0, r, 2) for r in ROLLS]
    gw.relay(*batch)
    assert gw.flush() == 200                       # stored, but say the 200 never reached the gateway…
    gw.relay(*batch)                               # …so it sends the same chunk again
    assert gw.flush() == 200 and gw.last_batch == {"status": "ok", "processed": 0, "skipped": 3}
    assert _stored(db) == 3


def test_answers_buffered_while_offline_count_only_if_the_quiz_is_still_open(client, db, live):
    from app.services.presence import _sweep_once
    from app.models import EspDevice
    from app.timeutil import istnow
    from datetime import timedelta
    from sqlalchemy import update
    h, gw, qid = live

    async def silent(s):
        await s.execute(update(EspDevice).values(last_seen=istnow() - timedelta(seconds=60)))
    db(silent)
    client.portal.call(_sweep_once)
    assert client.get("/api/admin/modules", headers=h).json()[0]["health"] == "OFFLINE"

    gw.relay(answer(qid, 0, ROLLS[0], 1))          # pressed while the Wi-Fi was down
    gw.register()                                  # back online
    assert gw.flush() == 200 and _stored(db) == 1
    assert client.get("/api/admin/modules", headers=h).json()[0]["health"] == "ONLINE"

    gw.relay(answer(qid, 0, ROLLS[1], 1))          # buffered across the end of the quiz
    assert client.post(f"/api/quizzes/{qid}/stop", headers=h).status_code == 200
    assert gw.flush() == 200 and gw.last_batch["skipped"] == 1 and _stored(db) == 1


def test_two_copies_racing_store_one_answer(client, db, live):
    _, _, qid = live
    copies = [Gateway(client, GW) for _ in range(2)]   # the same chunk, sent twice at once
    for g in copies:
        g.relay(answer(qid, 0, ROLLS[0], 3))
    barrier, codes = threading.Barrier(2), []

    def send(g):
        barrier.wait()
        codes.append(g.flush())
    threads = [threading.Thread(target=send, args=(g,)) for g in copies]
    [t.start() for t in threads]
    [t.join(30) for t in threads]
    assert sorted(codes) in ([200, 200], [200, 503])   # the loser either saw the winner's row or hit the index
    for g in copies:                                   # a 503 copy is retried, and skipped
        if g.pending:
            assert g.flush() == 200 and g.last_batch["skipped"] == 1
    assert _stored(db) == 1


def test_a_malformed_chunk_is_dropped_not_retried_forever(client, live):
    _, gw, _ = live
    r = client.post("/api/device/batch", headers={"X-API-Key": "test-device-key"}, json={"messages": "nope"})
    assert 400 <= r.status_code < 500                  # 4xx: the gateway drops it (main.c)
