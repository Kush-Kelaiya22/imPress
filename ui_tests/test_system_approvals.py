"""v2.2: dangerous actions on the System page need a second super admin (dual control)."""

from playwright.sync_api import expect

from conftest import login


def test_clear_data_needs_a_second_super_admin(server, page):
    base, api = server
    api.make_super_admin("boss2", "Passw0rd!x")
    api("/api/admin/classes", {"name": "Doomed class", "code": "DOOM101"})

    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/system")
    expect(page.locator("h1", has_text="System")).to_be_visible()

    # the policy is shown, and there is nothing to edit
    expect(page.locator("code", has_text="dual_control.enabled")).to_be_visible()
    assert page.locator("input[name*=flag]").count() == 0

    # request: step-up with the password
    page.click('[data-action="sys-request"][data-kind="system.clear.class_data"]')
    page.fill('input[name="password"]', "wrong")
    page.click('.modal button[type="submit"]')
    expect(page.locator(".toast", has_text="password is not correct")).to_be_visible()
    page.click('[data-action="sys-request"][data-kind="system.clear.class_data"]')
    page.fill('input[name="password"]', "ui-admin-pw")
    page.click('.modal button[type="submit"]')
    expect(page.locator(".feed-item", has_text="Clear class data")).to_contain_text("pending")
    assert page.locator('[data-action="sys-run"]').count() == 0                 # nothing to run yet

    # the other super admin approves (their own session, their own password)
    other = login_api(api, base, "boss2", "Passw0rd!x")
    rid = other("/api/admin/approvals")["requests"][0]["id"]
    other(f"/api/admin/approvals/{rid}/approve", {"password": "Passw0rd!x"})

    page.goto(base + "/#/admin/system")
    page.click('[data-action="sys-run"]')
    expect(page.locator(".modal button[type=submit]")).to_be_disabled()           # needs the typed phrase
    page.fill('input[name="phrase"]', "DELETE CLASS DATA")
    page.click('.modal button[type="submit"]')
    expect(page.locator(".toast-success", has_text="Done. A copy was saved first")).to_be_visible()
    assert api("/api/admin/classes") == []
    expect(page.locator(".feed-item", has_text="Clear class data")).to_contain_text("executed")


def login_api(api, base, username, password):
    import json
    import urllib.request

    req = urllib.request.Request(base + "/api/auth/login", data=json.dumps({"username": username, "password": password}).encode(),
                                 headers={"content-type": "application/json"}, method="POST")
    token = json.load(urllib.request.urlopen(req))["access_token"]
    return type(api)(base, token)
