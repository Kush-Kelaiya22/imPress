"""#31: importing questions from CSV on the create-quiz page."""

from pathlib import Path

from playwright.sync_api import expect

from conftest import SHOTS, login

HEADER = "question_text,option_a,option_b,option_c,option_d,correct_option\n"
WITH_ERRORS = HEADER + (
    '"What is 2 + 2?",3,4,5,6,B\n'
    '"Which planet is closest to the Sun?",Mercury,Venus,,,A\n'
    '"Boiling point of water?",90,100,,,E\n'
    '"what is 2 + 2?",1,2,,,A\n')
FIXED = HEADER + (
    '"What is 2 + 2?",3,4,5,6,B\n'
    '"Which planet is closest to the Sun?",Mercury,Venus,,,A\n'
    '"Boiling point of water (°C)?",90,100,110,,B\n')


def _open_create_quiz(server, page):
    base, api = server
    cid = api("/api/admin/classes", {"name": "Physics A", "code": "PHY101"})["id"]
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(f"{base}/#/quiz?class_id={cid}")
    expect(page.locator("#q-import")).to_be_visible()
    return base, api, cid


def test_template_link_downloads_the_example(server, page):
    _open_create_quiz(server, page)
    with page.expect_download() as dl:
        page.click("text=Download template")
    assert dl.value.suggested_filename == "impress-questions-template.csv"
    assert Path(dl.value.path()).read_text().startswith("question_text,option_a")


def test_invalid_rows_block_the_import_and_are_explained(server, page, tmp_path):
    _open_create_quiz(server, page)
    f = tmp_path / "questions.csv"
    f.write_text(WITH_ERRORS)
    page.set_input_files("#q-csv-file", str(f))
    result = page.locator("#q-csv-result")
    expect(result.locator("table")).to_be_visible()
    expect(result).to_contain_text("1 invalid")
    expect(result).to_contain_text("letter A–D or a number 1–4")
    expect(result).to_contain_text("duplicate of line 2")
    expect(page.locator("#q-csv-add")).to_be_disabled()
    expect(result).to_contain_text("nothing has been added")
    # the explanations must be readable without scrolling sideways (first version clipped them)
    assert page.evaluate("document.querySelector('.csv-preview').scrollWidth"
                         " <= document.querySelector('#q-csv-result').clientWidth + 1")
    # and a disabled button must look disabled (no style existed for it)
    assert float(page.eval_on_selector("#q-csv-add", "e => getComputedStyle(e).opacity")) < 1
    SHOTS.mkdir(exist_ok=True)
    page.locator("#q-import").screenshot(path=str(SHOTS / "csv-questions-invalid.png"))
    # nothing reached the form
    expect(page.locator("#questions-container [data-qi]")).to_have_count(1)


def test_valid_file_loads_into_the_form_and_creates_the_quiz(server, page, tmp_path):
    base, api, cid = _open_create_quiz(server, page)
    f = tmp_path / "questions.csv"
    f.write_text(FIXED)
    page.set_input_files("#q-csv-file", str(f))
    expect(page.locator("#q-csv-result")).to_contain_text("3 valid")
    SHOTS.mkdir(exist_ok=True)
    page.locator("#q-import").screenshot(path=str(SHOTS / "csv-questions-preview.png"))

    page.click("#q-csv-add")
    cards = page.locator("#questions-container [data-qi]")
    expect(cards).to_have_count(3)                       # the empty starter card was replaced
    expect(cards.nth(0).locator(".q-text")).to_have_value("What is 2 + 2?")
    expect(cards.nth(0).locator(".q-options")).to_have_value("3\n*4\n5\n6")
    expect(cards.nth(2).locator(".q-options")).to_have_value("90\n*100\n110")
    expect(cards.nth(2).locator("h2")).to_have_text("Question 3")

    page.fill("#quiz-title", "Imported quiz")
    page.click("button[type=submit]:has-text('Create Quiz')")
    page.wait_for_url(f"**/#/class?id={cid}")
    quizzes = api(f"/api/quizzes/class/{cid}")
    assert [(q["title"], q["question_count"]) for q in quizzes] == [("Imported quiz", 3)]


def test_unusable_file_shows_the_reason(server, page, tmp_path):
    _open_create_quiz(server, page)
    f = tmp_path / "questions.csv"
    f.write_text("question,answer\nq,a\n")
    page.set_input_files("#q-csv-file", str(f))
    expect(page.locator("#q-csv-result")).to_contain_text("Missing required column(s)")
