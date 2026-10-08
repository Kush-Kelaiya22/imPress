"""#31: import quiz questions from CSV (parse/preview, all-or-nothing import)."""

import pytest
from sqlalchemy import select

from conftest import auth, login, make_user

HEADER = "question_text,option_a,option_b,option_c,option_d,correct_option\n"


def _csv(*rows, header=HEADER):
    return (header + "".join(r + "\n" for r in rows)).encode()


def _files(raw, name="q.csv"):
    return {"file": (name, raw, "text/csv")}


@pytest.fixture
def ctx(client):
    h = auth(login(client))
    cid = client.post("/api/admin/classes", headers=h, json={"name": "Phys", "code": "PHY1"}).json()["id"]
    quiz = client.post("/api/quizzes/", headers=h, json={"class_session_id": cid, "title": "Q", "questions": [
        {"question_text": "Existing question?", "options": ["a", "b"], "correct_option": 0}]}).json()["id"]
    return {"h": h, "class": cid, "quiz": quiz}


def parse(client, h, raw):
    return client.post("/api/quizzes/questions/parse", headers=h, files=_files(raw))


def import_(client, ctx, raw, dry_run=False):
    return client.post(f"/api/quizzes/{ctx['quiz']}/questions/import?dry_run={str(dry_run).lower()}",
                       headers=ctx["h"], files=_files(raw))


def questions(db, quiz):
    from app.models import QuizQuestion

    async def q(s):
        rows = await s.execute(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz).order_by(QuizQuestion.order_num))
        return [(r.order_num, r.question_text, r.options, r.correct_option) for r in rows.scalars()]
    return db(q)


# ── Parsing and validation ──────────────────────────────────────────────────

def test_template_downloads_and_parses_cleanly(client, ctx):
    t = client.get("/api/quizzes/questions/template.csv")
    assert t.status_code == 200 and t.headers["content-type"].startswith("text/csv")
    assert "attachment" in t.headers["content-disposition"]
    rep = parse(client, ctx["h"], t.content).json()
    assert rep["valid"] == 2 and rep["invalid"] == 0
    assert rep["rows"][0]["correct_option"] == 1 and rep["rows"][1]["options"] == ["Mercury", "Venus"]


def test_valid_rows_letters_and_numbers(client, ctx):
    rep = parse(client, ctx["h"], _csv('"2+2?",3,4,5,6,B', '"Cap of France?",Paris,Rome,,,1', 'Two options,yes,no,,,b')).json()
    assert (rep["total"], rep["valid"], rep["invalid"], rep["duplicate"]) == (3, 3, 0, 0)
    assert [r["correct_option"] for r in rep["rows"]] == [1, 0, 1]
    assert [r["line"] for r in rep["rows"]] == [2, 3, 4]
    assert rep["committed"] is False and rep["imported"] == 0


@pytest.mark.parametrize("raw,needle", [
    (b"", "empty"),
    (b"   \n\n", "empty"),
    (HEADER.encode(), "no data rows"),
    (b"question_text,option_a,correct_option\nq,a,A\n", "Missing required column(s): option_b"),
    (_csv("q,a,b,,,A,5", header="question_text,option_a,option_b,option_c,option_d,correct_option,marks\n"),
     "Unknown column(s): marks"),
    (_csv("q,a,b,c,A", header="question_text,option_a,option_b,option_b,correct_option\n"), "Duplicate column"),
    ("question_text,option_a,option_b,correct_option\nCafé?,oui,non,A\n".encode("latin-1"), "not UTF-8"),
])
def test_unusable_files_rejected_with_the_reason(client, ctx, raw, needle):
    r = parse(client, ctx["h"], raw)
    assert r.status_code == 422 and needle in r.json()["detail"], r.text


def test_reordered_columns_and_aliases(client, ctx):
    raw = _csv("B,No,Is water wet?,Yes", header="Correct Answer,option_2,Question,option_1\n")
    rep = parse(client, ctx["h"], raw).json()
    assert rep["valid"] == 1
    row = rep["rows"][0]
    assert row["question_text"] == "Is water wet?" and row["options"] == ["Yes", "No"] and row["correct_option"] == 1


@pytest.mark.parametrize("row,needle", [
    ("q,a,b,c,d,E", "letter A–D or a number 1–4"),
    ("q,a,b,c,d,0", "letter A–D or a number 1–4"),
    ("q,a,b,c,d,x", "letter A–D or a number 1–4"),
    ("q,a,b,,,C", "points at an empty option"),
    ("q,a,b,c,d,", "correct_option is empty"),
    ("q,a,,c,,A", "option B is empty but a later option is filled"),
    ("q,a,,,,A", "options"),                              # only one option
    (",a,b,,,A", "question_text"),                        # empty question
    ('"' + "x" * 1001 + '",a,b,,,A', "longer than 1000"),
    ("q," + "o" * 201 + ",b,,,A", "option A is longer than 200"),
    ("q,a,b,,,A,surplus", "more cell(s) than columns"),
])
def test_invalid_rows_are_explained(client, ctx, row, needle):
    rep = parse(client, ctx["h"], _csv(row)).json()
    assert rep["invalid"] == 1 and rep["rows"][0]["status"] == "invalid"
    assert any(needle in e for e in rep["rows"][0]["errors"]), rep["rows"][0]["errors"]


def test_quoted_commas_line_breaks_and_quotes(client, ctx):
    raw = _csv('"Which is larger, 3 or 4?","3, the first","4",,,B',
               '"Line one\nline two?","say ""hi""",bye,,,A')
    rep = parse(client, ctx["h"], raw).json()
    assert rep["valid"] == 2
    assert rep["rows"][0]["question_text"] == "Which is larger, 3 or 4?" and rep["rows"][0]["options"][0] == "3, the first"
    assert rep["rows"][1]["question_text"] == "Line one\nline two?" and rep["rows"][1]["options"][0] == 'say "hi"'
    assert rep["rows"][1]["line"] == 4      # the quoted row spans lines 3-4


def test_unicode_bom_crlf_and_display_warnings(client, ctx):
    raw = "﻿" + HEADER.replace("\n", "\r\n") + "पानी का सूत्र क्या है?,H₂O,CO₂,,,A\r\n" + \
          '"Emoji 🙂 ok?",yes 👍,no,,,A\r\n' + "Long options?,abcdefghijklmnopq,b,,,A\r\n"
    rep = parse(client, ctx["h"], raw.encode("utf-8")).json()
    assert rep["valid"] == 3 and rep["rows"][0]["options"] == ["H₂O", "CO₂"]
    assert rep["rows"][0]["question_text"].startswith("पानी")
    assert rep["rows"][0]["warnings"] == []                # 52 bytes fits 139
    assert any("option A is 17 bytes" in w for w in rep["rows"][2]["warnings"])


def test_duplicates_within_the_file_are_flagged(client, ctx):
    rep = parse(client, ctx["h"], _csv("Same?,a,b,,,A", "  same?  ,c,d,,,B", "Other?,a,b,,,A")).json()
    assert (rep["valid"], rep["duplicate"]) == (2, 1)
    assert rep["rows"][1]["status"] == "duplicate" and rep["rows"][1]["duplicate_of"] == "line 2"


def test_size_and_row_limits(client, ctx):
    big = HEADER.encode() + b"q,a,b,,,A\n" + b"x" * 1_000_001
    assert parse(client, ctx["h"], big).status_code == 413
    many = _csv(*[f"Question {i}?,a,b,,,A" for i in range(501)])
    r = parse(client, ctx["h"], many)
    assert r.status_code == 422 and "Too many rows" in r.json()["detail"]
    assert parse(client, ctx["h"], _csv(*[f"Question {i}?,a,b,,,A" for i in range(500)])).json()["valid"] == 500


# ── Importing into a draft quiz ─────────────────────────────────────────────

def test_dry_run_is_the_default_and_stores_nothing(client, db, ctx):
    r = client.post(f"/api/quizzes/{ctx['quiz']}/questions/import", headers=ctx["h"],
                    files=_files(_csv("New?,a,b,,,A")))
    assert r.status_code == 200 and r.json()["committed"] is False
    assert len(questions(db, ctx["quiz"])) == 1


def test_import_appends_in_order_and_is_logged(client, db, ctx):
    r = import_(client, ctx, _csv("First new?,a,b,,,B", "Second new?,x,y,z,,C"))
    rep = r.json()
    assert r.status_code == 200 and rep["committed"] and (rep["imported"], rep["skipped"]) == (2, 0)
    assert questions(db, ctx["quiz"]) == [
        (0, "Existing question?", ["a", "b"], 0),
        (1, "First new?", ["a", "b"], 1),
        (2, "Second new?", ["x", "y", "z"], 2)]
    from app.models import ActivityLog

    async def log(s):
        return await s.scalar(select(ActivityLog).where(ActivityLog.action == "quiz.import_questions"))
    entry = db(log)
    assert entry.details["imported"] == 2 and len(entry.details["file_sha256"]) == 64


def test_any_invalid_row_means_nothing_is_imported(client, db, ctx):
    r = import_(client, ctx, _csv("Good?,a,b,,,A", "Bad?,a,b,,,Z"))
    assert r.status_code == 422
    detail = r.json()["detail"]
    assert "nothing was imported" in detail["message"] and detail["report"]["invalid"] == 1
    assert len(questions(db, ctx["quiz"])) == 1


def test_existing_questions_and_repeated_uploads_are_not_duplicated(client, db, ctx):
    raw = _csv("existing QUESTION?,a,b,,,A", "Fresh?,a,b,,,A")
    first = import_(client, ctx, raw).json()
    assert (first["imported"], first["duplicate"]) == (1, 1)
    assert first["rows"][0]["duplicate_of"] == "already in this quiz"
    again = import_(client, ctx, raw).json()             # a retry / double click
    assert again["imported"] == 0 and again["duplicate"] == 2
    assert len(questions(db, ctx["quiz"])) == 2


def test_only_draft_quizzes_accept_imports(client, ctx):
    assert client.post(f"/api/quizzes/{ctx['quiz']}/start", headers=ctx["h"]).status_code == 200
    r = import_(client, ctx, _csv("Late?,a,b,,,A"))
    assert r.status_code == 409


def test_database_failure_leaves_nothing_behind(client, db, ctx, monkeypatch):
    from sqlalchemy.exc import OperationalError

    from app.routers import quizzes

    async def broken(session, detail, status=409):
        raise OperationalError("COMMIT", {}, Exception("disk I/O error"))
    monkeypatch.setattr(quizzes, "commit_or_conflict", broken)
    r = import_(client, ctx, _csv("Will fail?,a,b,,,A"))
    assert r.status_code == 503 and "nothing was imported" in r.json()["detail"]
    assert len(questions(db, ctx["quiz"])) == 1


def test_positions_are_unique_per_quiz(client, db, ctx):
    # two concurrent imports would claim the same positions; the index makes
    # the slower one fail cleanly instead of interleaving
    from sqlalchemy.exc import IntegrityError

    from app.models import QuizQuestion

    async def clash(s):
        s.add(QuizQuestion(quiz_id=ctx["quiz"], order_num=0, question_text="dup", options=["a", "b"], correct_option=0))
        await s.flush()
    with pytest.raises(IntegrityError):
        db(clash)


# ── Access control ──────────────────────────────────────────────────────────

def test_requires_a_session_and_class_access(client, ctx):
    raw = _csv("New?,a,b,,,A")
    assert client.post("/api/quizzes/questions/parse", files=_files(raw)).status_code == 401
    assert client.post(f"/api/quizzes/{ctx['quiz']}/questions/import", files=_files(raw)).status_code == 401
    _, outsider = make_user(client, ctx["h"], "outsider")
    assert parse(client, outsider, raw).status_code == 200       # parsing touches no class data
    r = client.post(f"/api/quizzes/{ctx['quiz']}/questions/import?dry_run=false", headers=outsider, files=_files(raw))
    assert r.status_code == 403
    assert client.post("/api/quizzes/999/questions/import", headers=ctx["h"], files=_files(raw)).status_code == 404
