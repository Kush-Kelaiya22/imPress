"""Contract test: frames the C6 gateway receives on its device WebSocket (#3).

The firmware (firmware/class_c6/main/ws_command.c) dispatches on "event" and
reads the keys listed in FIRMWARE_KEYS. This test drives the real quiz/poll
endpoints, captures what a role=device socket receives, projects each frame
onto those keys and compares with firmware/contract/device_ws_frames.json,
which the C host test (firmware/class_c6/test_host) feeds to ws_command.c.

Regenerate the fixture after an intentional contract change with:
    IMPRESS_UPDATE_CONTRACT=1 pytest backend/tests/test_device_ws_contract.py
"""

import json
import os
from pathlib import Path

from conftest import DEVICE_KEY, auth, login

FIXTURE = Path(__file__).resolve().parents[2] / "firmware" / "contract" / "device_ws_frames.json"

FIRMWARE_KEYS = {
    "quiz_question": ["event", "quiz_id", "question_order", "question_text", "options", "time_limit_s"],
    "quiz_end": ["event", "quiz_id"],
    "poll_start": ["event", "poll_id", "title", "options"],
    "poll_end": ["event", "poll_id"],
}


def _next_device_frame(ws):
    """The single frame an action broadcasts; it must carry a firmware event.

    Reads exactly one frame so a missing/renamed "event" fails the test
    instead of blocking forever on receive.
    """
    frame = ws.receive_json()
    assert frame.get("event") in FIRMWARE_KEYS, f"frame has no firmware event: {frame}"
    return frame


def _project(frame):
    keys = FIRMWARE_KEYS[frame["event"]]
    missing = [k for k in keys if k not in frame]
    assert not missing, f"{frame['event']} frame lacks firmware keys {missing}: {frame}"
    return {k: frame[k] for k in keys}


def test_device_socket_receives_firmware_contract(client):
    h = auth(login(client))
    cls = client.post("/api/admin/classes", headers=h, json={"name": "Physics", "code": "PHY101"})
    assert cls.status_code == 201, cls.text
    cid = cls.json()["id"]

    frames = []
    with client.websocket_connect(f"/ws/class/{cid}?role=device&api_key={DEVICE_KEY}") as ws:
        assert ws.receive_json()["event"] == "connected"

        quiz = client.post("/api/quizzes/", headers=h, json={
            "class_session_id": cid, "title": "Q", "timing_mode": "per_question",
            "question_time_limit": 30,
            "questions": [
                {"question_text": "2+2?", "options": ["3", "4", "5", "6"], "correct_option": 1},
                {"question_text": "Capital of France?", "options": ["Paris", "Rome"], "correct_option": 0},
            ],
        })
        assert quiz.status_code == 201, quiz.text
        qid = quiz.json()["id"]
        assert client.post(f"/api/quizzes/{qid}/start", headers=h).status_code == 200
        frames.append(_next_device_frame(ws))
        assert client.post(f"/api/quizzes/{qid}/next", headers=h).status_code == 200
        frames.append(_next_device_frame(ws))
        assert client.post(f"/api/quizzes/{qid}/stop", headers=h).status_code == 200
        frames.append(_next_device_frame(ws))

        poll = client.post("/api/polls/", headers=h, json={
            "class_session_id": cid, "title": "Lab on Friday?", "options": ["Yes", "No", "Maybe"],
            "poll_mode": "planned",
        })
        assert poll.status_code == 201, poll.text
        pid = poll.json()["id"]
        assert client.post(f"/api/polls/{pid}/start", headers=h).status_code == 200
        frames.append(_next_device_frame(ws))
        assert client.post(f"/api/polls/{pid}/end", headers=h).status_code == 200
        frames.append(_next_device_frame(ws))

    got = [_project(f) for f in frames]
    assert [f["event"] for f in got] == ["quiz_question", "quiz_question", "quiz_end", "poll_start", "poll_end"]
    assert [f["question_order"] for f in got[:2]] == [0, 1]
    assert got[0]["time_limit_s"] == 30

    if os.environ.get("IMPRESS_UPDATE_CONTRACT"):
        FIXTURE.write_text(json.dumps(got, indent=2) + "\n")
    assert json.loads(FIXTURE.read_text()) == got, (
        "device WS contract changed — update firmware/class_c6/main/ws_command.c "
        "and regenerate the fixture (see module docstring)"
    )
