"""v2.2: the page's Content-Security-Policy forbids inline script, and the app still works under it."""

import re

from playwright.sync_api import expect

from conftest import login

ROUTES_ADMIN = ["#/admin", "#/admin/classes", "#/sessions", "#/admin/students", "#/admin/courses", "#/admin/modules",
                "#/admin/firmware", "#/admin/users", "#/admin/activity", "#/admin/system", "#/admin/test-data", "#/settings"]


def _watch(page):
    page.add_init_script("""window.__csp = [];
      document.addEventListener('securitypolicyviolation', e => window.__csp.push(e.violatedDirective + ' ' + e.blockedURI));""")


def test_the_policy_has_no_unsafe_inline_for_scripts(server, page):
    base, _ = server
    r = page.request.get(base + "/")
    csp = r.headers["content-security-policy"]
    script = re.search(r"script-src ([^;]*)", csp).group(1)
    assert script == "'self'", csp
    assert "script-src-attr 'none'" in csp and "object-src 'none'" in csp and "base-uri 'none'" in csp
    assert "frame-ancestors 'none'" in csp and "report-uri /api/system/csp-report" in csp
    assert "unsafe-eval" not in csp
    html = r.text()
    assert not re.search(r"<script(?![^>]*\bsrc=)", html), "an inline <script> is back"
    assert not re.search(r"\son[a-z]+=", html)


def test_every_page_loads_and_its_buttons_work_under_the_policy(server, page):
    base, api = server
    api("/api/admin/classes", {"name": "Policy class", "code": "CSP101"})
    api("/api/admin/users", {"username": "csp_t", "email": "csp@example.edu", "password": "Passw0rd!x", "full_name": "Csp T", "role": "teacher"})
    _watch(page)
    login(page, base)
    page.wait_for_url("**/#/admin*")
    for route in ROUTES_ADMIN:
        page.goto(base + "/" + route)
        page.wait_for_timeout(500)
    # buttons that used to be inline handlers
    page.goto(base + "/#/admin/users")
    page.click("text=Add account")
    expect(page.locator("#create-user-modal")).not_to_have_class(re.compile("hidden"))
    page.click("#create-user-modal button:has-text('Cancel')")
    expect(page.locator("#create-user-modal")).to_have_class(re.compile("hidden"))
    page.click('[data-action="toggle-theme"] >> nth=0')
    theme = page.evaluate("document.documentElement.getAttribute('data-theme')")
    page.click('[data-action="toggle-theme"] >> nth=0')
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") != theme
    page.click('[data-action="toggle-notices"]')
    expect(page.locator("#notice-pop")).not_to_have_class(re.compile("hidden"))
    page.click('[data-action="toggle-notices"]')
    expect(page.locator("#notice-pop")).to_have_class(re.compile("hidden"))
    page.goto(base + "/#/admin/classes")
    page.once("dialog", lambda d: d.dismiss())
    page.click('button[title="Delete"] >> nth=0')               # data-call: deleteClass(id, name) with a confirm
    page.keyboard.press("ControlOrMeta+k")                      # the command palette (global search, data-input)
    page.fill("#palette-input", "Policy")
    expect(page.locator(".palette")).to_contain_text("Policy class")
    page.keyboard.press("Escape")

    assert page.evaluate("window.__csp") == [], page.evaluate("window.__csp")


def test_inline_script_is_blocked_and_reported(server, page):
    base, _ = server
    _watch(page)
    reports = []
    page.on("request", lambda r: reports.append(r.url) if r.url.endswith("/api/system/csp-report") else None)
    login(page, base)
    page.wait_for_url("**/#/admin*")
    page.evaluate("""() => { const b = document.createElement('button'); b.id = 'evil'; b.setAttribute('onclick', 'window.__owned = 1');
                              document.body.appendChild(b); b.click(); }""")
    page.evaluate("""() => { const s = document.createElement('script'); s.textContent = 'window.__owned = 2'; document.body.appendChild(s); }""")
    page.wait_for_timeout(800)
    assert page.evaluate("window.__owned") is None
    assert len(page.evaluate("window.__csp")) >= 2
    assert reports, "the browser did not report the violation"
