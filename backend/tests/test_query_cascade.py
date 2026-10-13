"""Loading a user or a class list must not pull in the teaching history (#133).

Measured before the fix: one select(User) for a teacher with 5 classes ×
10 quizzes × 60 answers ran 9 statements and loaded 3,000 answers.
"""

from contextlib import contextmanager

from sqlalchemy import event, select

from conftest import auth, login, make_class, make_user


@contextmanager
def statements():
    from app.database import engine
    seen = []

    def count(conn, cursor, statement, *args):
        seen.append(statement)
    event.listen(engine.sync_engine, "before_cursor_execute", count)
    try:
        yield seen
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", count)


def _history(client, db, teacher_id, classes=3, quizzes=4, answers=20):
    from app.models import Quiz, QuizAnswer, QuizQuestion
    su = auth(login(client))
    ids = [make_class(client, su, name=f"C{i}", code=f"C{i}X", teacher_id=teacher_id) for i in range(classes)]

    async def fill(s):
        for cid in ids:
            for _ in range(quizzes):
                q = Quiz(class_session_id=cid, title="q")
                s.add(q)
                await s.flush()
                s.add(QuizQuestion(quiz_id=q.id, order_num=0, question_text="?", options=["a", "b"], correct_option=0))
                for _ in range(answers):
                    s.add(QuizAnswer(quiz_id=q.id, question_order=0, selected_option=0))
    db(fill)
    return ids


def test_loading_a_user_is_one_statement(client, db):
    from app.database import async_session
    from app.models import User
    su = auth(login(client))
    uid, _ = make_user(client, su, "tch1")
    _history(client, db, uid)

    async def load():
        async with async_session() as s:
            with statements() as seen:
                await s.execute(select(User).where(User.id == uid))
            return len(seen)
    assert client.portal.call(load) == 1


def test_class_list_counts_without_loading_quizzes(client, db):
    su = auth(login(client))
    uid, teacher = make_user(client, su, "tch1")
    ids = _history(client, db, uid)
    with statements() as seen:
        classes = client.get("/api/classes/", headers=teacher).json()
    assert sorted(c["quiz_count"] for c in classes if c["id"] in ids) == [4, 4, 4]
    assert not [s for s in seen if "FROM quiz_answers" in s]
