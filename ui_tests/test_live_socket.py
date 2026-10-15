"""The live class page stops retrying when the server refuses it (#160)."""

from playwright.sync_api import expect

from conftest import login


def _teacher_with_class(api, name="teach1"):
    uid = api("/api/admin/users", {"username": name, "email": f"{name}@example.edu", "password": "Passw0rd!x",
                                   "full_name": name.title(), "role": "teacher"})["id"]
    cid = api("/api/admin/classes", {"name": "Physics A", "code": "PHY101", "teacher_id": uid})["id"]
    return uid, cid


def _count_sockets(page):
    seen = []
    page.on("websocket", lambda ws: seen.append(ws.url))
    return seen


def test_a_disabled_teacher_sees_a_notice_then_the_sign_in_page(server, page):
    base, api = server
    uid, cid = _teacher_with_class(api)
    login(page, base, "teach1", "Passw0rd!x")
    page.wait_for_url("**/#/dashboard*")
    sockets = _count_sockets(page)
    page.goto(f"{base}/#/class?id={cid}")
    expect(page.locator("#ws-status")).to_have_text("Connected")
    api(f"/api/admin/users/{uid}/deactivate", {})
    expect(page.locator("#notice-overlay")).to_contain_text("Your account has been disabled", timeout=15000)
    page.click("#ov-btn")
    page.wait_for_url("**/#/login*", timeout=10000)
    before = len(sockets)
    page.wait_for_timeout(4000)                       # longer than the first reconnect delays
    assert len(sockets) == before                     # no reconnect loop


def test_a_class_without_access_shows_why_and_stops(server, page):
    base, api = server
    _teacher_with_class(api)
    api("/api/admin/users", {"username": "other1", "email": "o@example.edu", "password": "Passw0rd!x",
                             "full_name": "Other", "role": "teacher"})
    login(page, base, "other1", "Passw0rd!x")
    page.wait_for_url("**/#/dashboard*")
    sockets = _count_sockets(page)
    page.goto(f"{base}/#/class?id=1")
    page.wait_for_timeout(6000)                       # the old page retried after 1, 1.5, 2.25 … s
    assert len(sockets) <= 1                          # one refused attempt, no retries
