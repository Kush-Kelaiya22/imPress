"""v2.2: the motion is there, plays when the route changes, never replays on a refresh, and is off with reduced motion."""

import pytest
from playwright.sync_api import expect

from conftest import login

MOTION = pytest.mark.parametrize("page", ["no-preference"], indirect=True)


def _settled(page):
    """The route's entry has played and ended (it is set when the page has rendered, and ends by itself)."""
    expect(page.locator("#app[data-enter]")).to_be_attached(timeout=5000)
    expect(page.locator("#app[data-enter]")).to_have_count(0, timeout=4000)


def _anim(page, selector):
    return page.evaluate("(s) => getComputedStyle(document.querySelector(s)).animationName", selector)


@MOTION
def test_a_route_change_plays_the_entry_and_then_settles(server, page):
    base, api = server
    for i in range(3):
        api("/api/students/", {"roll_number": f"MOTION000{i}", "student_name": f"Motion {i}"})
    page.add_init_script("window.__csp = []; document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.violatedDirective));")
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/students")
    expect(page.locator("#app[data-enter]")).to_be_attached()
    assert _anim(page, ".stat-card") == "m3-rise"
    expect(page.locator("#app[data-enter]")).to_have_count(0, timeout=4000)                          # it ends by itself
    for sel in (".stat-card", ".page-header", ".table tbody tr"):
        assert page.evaluate("(s) => { const c = getComputedStyle(document.querySelector(s)); return [c.opacity, c.transform]; }", sel) == ["1", "none"], sel
    # the figure counted up and ended on the real number
    assert page.locator(".stat-value").first.inner_text().strip() == "3"
    assert page.evaluate("window.__csp") == []


@MOTION
def test_a_background_refresh_never_replays_it(server, page):
    base, api = server
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/students")
    _settled(page)
    api("/api/students/", {"roll_number": "MOTION9999", "student_name": "Late Arrival"})
    page.evaluate("quietRefresh()")                              # what live refresh does when data changes
    expect(page.locator("tr", has_text="Late Arrival")).to_be_visible()
    assert page.evaluate("document.querySelector('#app').hasAttribute('data-enter')") is False
    assert _anim(page, ".stat-card") == "none" and _anim(page, ".table tbody tr") == "none"


@MOTION
def test_dialogs_spring_in_and_land(server, page):
    base, _ = server
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    page.click("text=Add account")
    assert _anim(page, "#create-user-modal .modal-content") == "m3-dialog"
    page.wait_for_timeout(700)
    assert page.evaluate("getComputedStyle(document.querySelector('#create-user-modal .modal-content')).opacity") == "1"


@MOTION
def test_buttons_press_and_morph(server, page):
    base, _ = server
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/users")
    _settled(page)
    btn = page.locator('button[data-action="show"][data-target="#create-user-modal"]')
    box = btn.bounding_box()
    page.mouse.move(box["x"] + 5, box["y"] + 5)
    page.mouse.down()
    page.wait_for_timeout(450)
    pressed = page.evaluate("(el) => { const c = getComputedStyle(el); return [c.transform, c.borderRadius]; }", btn.element_handle())
    page.mouse.up()
    assert pressed[0].startswith("matrix(0.96") and pressed[1] == "7px", pressed


@MOTION
def test_the_keyboard_ring_is_visible(server, page):
    base, _ = server
    login(page, base)
    page.wait_for_url("**/#/admin*")
    for _ in range(12):                                          # the first stops may be fields with their own ring
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.tagName") in ("BUTTON", "A"):
            break
    outline = page.evaluate("(() => { const c = getComputedStyle(document.activeElement); return [c.outlineStyle, c.outlineWidth]; })()")
    assert outline == ["solid", "3px"], outline


def test_reduced_motion_turns_it_all_off(server, page):          # the suite's default context
    base, api = server
    api("/api/students/", {"roll_number": "REDUCED001", "student_name": "Calm"})
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.goto(base + "/#/admin/students")
    expect(page.locator(".stat-card").first).to_be_visible()
    assert page.evaluate("document.querySelector('#app').hasAttribute('data-enter')") is False
    assert _anim(page, ".stat-card") == "none"
    page.goto(base + "/#/admin/users")
    page.click("text=Add account")
    assert _anim(page, "#create-user-modal .modal-content") == "none"
