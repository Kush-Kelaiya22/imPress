"""#32: importing and exporting courses and sections on the Classrooms page."""

from pathlib import Path

from playwright.sync_api import expect

from conftest import SHOTS, login

HEADER = "course_code,course_name,section,class_code,teacher_username,classroom_code,term,year\n"
WITH_ERRORS = HEADER + ("CS101,Intro to Computing,A,CS101-A,teacher1,RM-201,Monsoon,2026\n"
                        "CS101,Intro to Computing,B,CS101-B,ghost,,Monsoon,2026\n"
                        "MA201,Linear Algebra,A,MA201-A,teacher1,,Spring,2026\n")
VALID = HEADER + ("CS101,Intro to Computing,A,CS101-A,teacher1,RM-201,Monsoon,2026\n"
                  "CS101,Intro to Computing,B,CS101-B,teacher1,,Monsoon,2026\n"
                  "MA201,Linear Algebra,A,MA201-A,teacher1,,Winter,2027\n")


def _open(server, page):
    base, api = server
    api("/api/admin/users", {"username": "teacher1", "email": "t1@example.edu", "password": "Passw0rd!x",
                             "full_name": "Teacher One", "role": "teacher"})
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/classes")
    page.click("#btn-classes-import")
    expect(page.locator("#classes-import")).to_be_visible()
    return base, api


def test_invalid_rows_block_the_import(server, page, tmp_path):
    _open(server, page)
    f = tmp_path / "classes.csv"
    f.write_text(WITH_ERRORS)
    page.set_input_files("#classes-csv-file", str(f))
    result = page.locator("#classes-csv-result")
    expect(result).to_contain_text("2 invalid")
    expect(result).to_contain_text("no active teacher with username 'ghost'")
    expect(result).to_contain_text("term 'Spring' must be one of")
    expect(page.locator("#classes-csv-run")).to_be_disabled()
    assert page.evaluate("document.querySelector('#classes-csv-result .csv-preview').scrollWidth"
                         " <= document.querySelector('#classes-csv-result').clientWidth + 1")
    SHOTS.mkdir(exist_ok=True)
    page.locator("#classes-import").screenshot(path=str(SHOTS / "csv-classes-invalid.png"))


def test_valid_file_creates_courses_and_sections(server, page, tmp_path):
    base, api = _open(server, page)
    f = tmp_path / "classes.csv"
    f.write_text(VALID)
    page.set_input_files("#classes-csv-file", str(f))
    expect(page.locator("#classes-csv-result")).to_contain_text("3 new")
    expect(page.locator("#classes-csv-result")).to_contain_text("2 new courses")
    SHOTS.mkdir(exist_ok=True)
    page.locator("#classes-import").screenshot(path=str(SHOTS / "csv-classes-preview.png"))
    page.click("#classes-csv-run")
    expect(page.locator("h2", has_text="3 Classrooms")).to_be_visible()     # the page re-rendered
    # the primary teacher shows up as faculty, like a classroom created in the form
    expect(page.locator("tr", has_text="Linear Algebra")).to_contain_text("Teacher One")
    codes = sorted(c["code"] for c in api("/api/admin/classes"))
    assert codes == ["CS101-A", "CS101-B", "MA201-A"]

    # update mode on the same file: nothing to change; switching the mode re-plans
    page.click("#btn-classes-import")
    page.set_input_files("#classes-csv-file", str(f))
    expect(page.locator("#classes-csv-result")).to_contain_text("3 already present")
    page.select_option("#classes-import-mode", "update")
    expect(page.locator("#classes-csv-result")).to_contain_text("0 to update")
    expect(page.locator("#classes-csv-run")).to_be_disabled()

    # export downloads the same sections
    with page.expect_download() as dl:
        page.click("#btn-classes-export")
    text = Path(dl.value.path()).read_text()
    assert dl.value.suggested_filename == "impress-classes.csv"
    assert all(code in text for code in codes)
