"""#51: only the latest navigation renders."""

from playwright.sync_api import expect

from conftest import login


def test_quick_navigation_is_not_overwritten_by_a_slower_page(server, page):
    base, api = server
    cid = api("/api/admin/classes", {"name": "Physics A", "code": "PHY101"})["id"]
    login(page, base)
    page.wait_for_url("**/#/admin*")             # the admin dashboard is still loading its data
    page.goto(f"{base}/#/quiz?class_id={cid}")   # ...and the user moves on at once
    page.wait_for_timeout(2000)                  # long after the dashboard's requests finished
    assert page.evaluate("location.hash") == f"#/quiz?class_id={cid}"
    expect(page.locator("#quiz-form")).to_be_visible()
    expect(page.locator("h1").first).to_have_text("Create Quiz")


def test_normal_navigation_and_in_page_rerender_still_work(server, page):
    base, api = server
    api("/api/admin/users", {"username": "teach1", "email": "t1@example.edu", "password": "Passw0rd!x",
                             "full_name": "Teach One", "role": "teacher"})
    login(page, base)
    page.wait_for_url("**/#/admin*")
    expect(page.locator("text=Good day")).to_be_visible()
    page.goto(base + "/#/admin/users")
    row = page.locator("tr", has_text="teach1")
    expect(row).to_be_visible()
    page.on("dialog", lambda d: d.accept())
    row.locator("button", has_text="Disable").click()   # re-renders the same page
    expect(page.locator("tr", has_text="teach1").locator("button", has_text="Enable")).to_be_visible()
