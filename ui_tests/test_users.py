"""Account lifecycle in the admin UI (#117, #119): buttons follow the server's allowed_actions."""

from playwright.sync_api import expect

from conftest import login


def _teacher(api, name="teach1"):
    return api("/api/admin/users", {"username": name, "email": f"{name}@example.edu", "password": "Passw0rd!x",
                                    "full_name": name.title(), "role": "teacher"})["id"]


def test_own_row_offers_no_lockout_actions(server, page):
    base, api = server
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    me = page.locator("tr", has_text="admin@impress.local")
    expect(me.locator("text=You")).to_be_visible()
    for label in ("Deactivate", "Delete permanently"):
        expect(me.locator("button", has_text=label)).to_have_count(0)


def test_delete_needs_the_username(server, page):
    base, api = server
    _teacher(api)
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    row = page.locator("tr", has_text="teach1")
    page.once("dialog", lambda d: d.accept("wrong-name"))
    row.locator("button", has_text="Delete permanently").click()
    expect(page.locator("text=Username did not match")).to_be_visible()
    expect(page.locator("tr", has_text="teach1")).to_be_visible()
    page.once("dialog", lambda d: d.accept("teach1"))
    page.locator("tr", has_text="teach1").locator("button", has_text="Delete permanently").click()
    expect(page.locator("tr", has_text="teach1")).to_have_count(0)
