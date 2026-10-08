"""#43 end to end: a teacher runs a quiz in a room, and the answers arrive
through a simulated gateway, as on the real hardware path:
class → CSV questions → gateway → modules join → start → device WS frames →
answers relayed in batches → live counts on the teacher's socket → results."""

from conftest import DEVICE_KEY, login, auth, make_class, make_student, make_user
from gateway_sim import Gateway, answer, join

GW = "48:F6:EE:00:00:C6"
ROLLS = [f"ABCDE1234{i}" for i in range(5)]
CSV = (b"question_text,option_a,option_b,option_c,option_d,correct_option\n"
       b"\"Capital of France, the city?\",Paris,Rome,Berlin,,A\n"
       b"2 + 2?,3,4,5,6,B\n")


def _marker(client, cid, ws, ignore=("presence",)):
    """Frames the socket got before a marker broadcast now (so a missing
    frame fails instead of blocking). Presence pushes are timing-dependent."""
    from app.ws.manager import manager
    client.portal.call(manager.broadcast_to_class, cid, {"event": "marker"})
    frames = []
    while True:
        f = ws.receive_json()
        if f.get("event") == "marker":
            return frames
        if f.get("type") not in ignore and f.get("event") not in ignore:
            frames.append(f)


def _next_command(ws):
    """The next frame ws_command.c acts on: it dispatches on "event" and
    ignores the rest (live counts are for teachers)."""
    while True:
        f = ws.receive_json()
        if f.get("event") in ("quiz_question", "quiz_end", "poll_start", "poll_end", "device_command"):
            return f


def test_a_quiz_runs_end_to_end_through_a_gateway(client):
    admin = auth(login(client))
    teacher_id, th = make_user(client, admin, "teach1")
    _, other_teacher = make_user(client, admin, "teach2")
    cid = make_class(client, admin, "Physics", "PHY101", classroom_code="RM-201", teacher_id=teacher_id)
    for i, roll in enumerate(ROLLS):
        make_student(client, admin, roll=roll, name=f"Student {i}")

    # the room's gateway comes up and links itself to the class by its room code
    gw = Gateway(client, GW, "RM-201")
    assert gw.register()["class_id"] == cid
    gw.heartbeat()

    # the teacher writes one question and imports two from a spreadsheet
    quiz = client.post("/api/quizzes/", headers=th, json={
        "class_session_id": cid, "title": "Warm-up", "timing_mode": "manual",
        "questions": [{"question_text": "Water boils at?", "options": ["90", "100"], "correct_option": 1}]})
    assert quiz.status_code == 201, quiz.text
    qid = quiz.json()["id"]
    files = {"file": ("q.csv", CSV, "text/csv")}
    dry = client.post(f"/api/quizzes/{qid}/questions/import", headers=th, files=files).json()
    assert (dry["valid"], dry["committed"]) == (2, False)
    real = client.post(f"/api/quizzes/{qid}/questions/import?dry_run=false", headers=th, files=files).json()
    assert (real["imported"], real["committed"]) == (2, True)

    # five modules join over the mesh; the gateway relays them in one batch
    gw.relay(*[join(0x1A000 + i, roll) for i, roll in enumerate(ROLLS)])
    assert gw.flush() == 200
    snap = client.get(f"/api/classes/{cid}/presence", headers=th).json()
    assert [m["state"] for m in snap["student_modules"]] == ["connected"] * 5

    token = th["Authorization"].split()[1]
    with client.websocket_connect(f"/ws/class/{cid}?role=teacher&token={token}") as teacher, \
         client.websocket_connect(f"/ws/class/{cid}?role=device&api_key={DEVICE_KEY}") as device:
        teacher.receive_json(), device.receive_json()                     # "connected"

        # question 0 reaches the gateway in the shape ws_command.c reads
        assert client.post(f"/api/quizzes/{qid}/start", headers=th).status_code == 200
        q0 = _next_command(device)
        assert (q0["event"], q0["question_order"], q0["options"]) == ("quiz_question", 0, ["90", "100"])

        # four students press; one press reaches the hub over two relay paths
        presses = [answer(qid, 0, ROLLS[i], opt) for i, opt in enumerate([1, 1, 0, 1])]
        gw.relay(*presses, presses[0])
        assert gw.flush() == 200 and gw.last_batch == {"status": "ok", "processed": 4, "skipped": 1}
        live = [f["total_answers"] for f in _marker(client, cid, teacher) if f.get("type") == "quiz_answer"]
        assert live == [4, 4, 4, 4]      # one update per stored answer, each with the total after the batch committed

        for order, picks in ((1, [0, 0, 1, 0, 0]), (2, [1, 1, 1, 1, 2])):
            assert client.post(f"/api/quizzes/{qid}/next", headers=th).status_code == 200
            frame = _next_command(device)
            assert (frame["event"], frame["question_order"]) == ("quiz_question", order)
            gw.relay(*[answer(qid, order, roll, opt) for roll, opt in zip(ROLLS, picks)])
            assert gw.flush() == 200

        assert client.post(f"/api/quizzes/{qid}/stop", headers=th).status_code == 200
        end = _next_command(device)
        assert (end["event"], end["quiz_id"]) == ("quiz_end", qid)        # the keys ws_command.c reads

    # a press that was still on the mesh when the quiz ended is not counted
    gw.relay(answer(qid, 2, ROLLS[0], 0))
    assert gw.flush() == 200 and gw.last_batch["skipped"] == 1

    res = client.get(f"/api/quizzes/{qid}/results", headers=th).json()
    assert res["status"] == "completed"
    assert [(r["question_text"], r["total_answers"], r["option_counts"]) for r in res["results"]] == [
        ("Water boils at?", 4, [1, 3]),
        ("Capital of France, the city?", 5, [4, 1, 0]),
        ("2 + 2?", 5, [0, 4, 1, 0]),
    ]
    assert client.get(f"/api/quizzes/{qid}/results", headers=other_teacher).status_code == 403
