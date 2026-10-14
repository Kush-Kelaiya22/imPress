"""v2.2: a simulated classroom feeds the real backend.

firmware/sim/classroom_sim.py runs the firmware's frame, de-duplication and
SPI code (host-compiled C) between 40 modules, a hub and a gateway, with
seeded radio faults; the gateway's batch goes to POST /api/device/batch.
Each student who got an answer through is counted exactly once, with the
option they pressed, however many copies arrived."""

import shutil
import sys
from pathlib import Path

import pytest
from sqlalchemy import select

from conftest import DEVICE, auth, login

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "firmware" / "sim"))
import classroom_sim as sim  # noqa: E402

pytestmark = pytest.mark.skipif(not shutil.which("cc"), reason="needs a C compiler for the firmware protocol code")

STUDENTS = 40


@pytest.fixture
def quiz(client, db):
    from app.models import Student
    h = auth(login(client))
    cid = client.post("/api/admin/classes", headers=h, json={"name": "Sim", "code": "SIM1"}).json()["id"]
    qid = client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "q1", "options": ["a", "b", "c", "d"], "correct_option": 0}]}).json()["id"]
    assert client.post(f"/api/quizzes/{qid}/start", headers=h).status_code == 200

    async def add(s):
        s.add_all([Student(roll_number=f"SIM{i:07d}", student_name=f"S{i}") for i in range(STUDENTS)])
    db(add)
    return qid


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_simulated_room_is_counted_once_per_student(client, db, quiz, seed):
    from app.models import QuizAnswer, Student
    r = sim.run_quiz(STUDENTS, seed=seed, quiz_id=quiz, loss=0.05, duplicate=0.3, corrupt=0.05, reorder=0.3)
    messages = r.delivered + r.delivered[: len(r.delivered) // 2]      # the gateway re-posts half after a timeout
    res = client.post("/api/device/batch", headers=DEVICE, json={"device_type": "c6", "messages": messages})
    assert res.status_code == 200, res.text
    assert res.json()["processed"] == len(r.delivered), f"seed={seed}"

    async def stored(s):
        rows = await s.execute(select(Student.roll_number, QuizAnswer.selected_option)
                               .join(QuizAnswer, QuizAnswer.student_id == Student.id))
        return dict(rows.all())
    want = {d["enrollment_number"]: d["selected_option"] for d in r.delivered}
    assert db(stored) == want, f"seed={seed}"
