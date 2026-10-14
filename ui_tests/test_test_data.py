"""v2.2: the Test data page: debug mode on, generate, paste, import, off and decide."""

from playwright.sync_api import expect

from conftest import SHOTS, login


def test_debug_mode_round_trip(server, page):
    base, api = server
    page.on("dialog", lambda d: d.accept())
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/test-data")
    page.click("#td-on")
    expect(page.locator(".sys-banner", has_text="Debug mode is on")).to_be_visible()

    for k, v in {"teachers": 2, "courses": 2, "students": 6, "classes": 2, "classes_per_student": 1,
                 "quizzes_per_class": 1, "questions_per_quiz": 2, "polls_per_class": 0}.items():
        page.fill(f'[data-count="{k}"]', str(v))
    page.fill("#td-seed", "42")
    page.click("#td-generate")
    expect(page.locator('#td-tabs [data-sheet="students"] .n')).to_have_text("6")

    # a pasted block with a quoted field lands cell by cell, below the generated rows
    page.click('#td-tabs [data-sheet="teachers"]')
    page.click('#td-sheet td[data-r="2"][data-c="0"]')
    page.evaluate("""tdPaste('pasted.one\\t"One, Pasted"\\tp1@example.edu\\tPhysics')""")
    assert page.locator('#td-sheet td[data-r="2"][data-c="1"]').inner_text() == "One, Pasted"
    expect(page.locator('#td-tabs [data-sheet="teachers"] .n')).to_have_text("3")

    # an invalid cell is flagged and blocks the import
    page.click('#td-sheet td[data-r="2"][data-c="2"]')
    page.keyboard.press("Enter")
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.type("not-an-email")
    page.keyboard.press("Enter")
    page.click("#td-validate")
    expect(page.locator("#td-sheet td.bad")).to_have_count(1)
    SHOTS.mkdir(exist_ok=True)
    page.screenshot(path=str(SHOTS / "test-data-sheet.png"), full_page=True)

    page.click('#td-sheet td[data-r="2"][data-c="2"]')
    page.keyboard.type("p1@example.edu")
    page.keyboard.press("Enter")
    page.click("#td-import")
    expect(page.locator(".toast", has_text="Imported")).to_be_visible()
    assert len(api("/api/students/")) >= 6

    page.click("#td-off")
    expect(page.locator("#td-pending-modal")).to_be_visible()
    page.click("#td-p-delete")
    expect(page.locator("#td-pending-modal")).to_be_hidden()
    expect(page.locator(".sys-banner", has_text="Debug mode is on")).to_have_count(0)
    assert api("/api/students/") == []      # the real data is back
