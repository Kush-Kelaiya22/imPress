"""#73: the class page offers Next for every timing mode, and a quiz the
server's timer ends switches to Results without a reload."""

from playwright.sync_api import expect

from conftest import SHOTS, login

QUESTIONS = [{"question_text": f"Q{i}?", "options": ["a", "b"], "correct_option": 0} for i in range(2)]


def test_timed_quiz_has_next_and_ends_on_the_timer(server, page):
    base, api = server
    cid = api("/api/admin/classes", {"name": "Physics A", "code": "PHY101"})["id"]
    per_q = api("/api/quizzes/", {"class_session_id": cid, "title": "Timed", "questions": QUESTIONS,
                                  "timing_mode": "per_question", "question_time_limit": 30})["id"]
    total = api("/api/quizzes/", {"class_session_id": cid, "title": "Sprint", "questions": QUESTIONS,
                                  "timing_mode": "total", "total_time_limit": 4})["id"]
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(f"{base}/#/class?id={cid}")
    api(f"/api/quizzes/{per_q}/start", {})
    page.reload()

    actions = page.locator(f"#quiz-actions-{per_q}")
    expect(actions.get_by_role("button", name="Next →")).to_be_visible()
    expect(page.get_by_text("per question · 30s/question")).to_be_visible()

    expect(page.locator("#ws-status")).to_have_text("Connected")
    api(f"/api/quizzes/{total}/start", {})                 # 4 s total: the server ends it
    page.reload()
    expect(page.locator("#ws-status")).to_have_text("Connected")
    sprint = page.locator(f"#quiz-actions-{total}")
    expect(sprint.get_by_role("link", name="Results")).to_be_visible(timeout=8000)
    page.screenshot(path=str(SHOTS / "quiz_timing.png"))
