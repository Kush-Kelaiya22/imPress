"""The served v2.2 sign-in page reports errors, waits visibly, and recovers with valid credentials."""

import json
import subprocess
import sys

from playwright.sync_api import expect

from conftest import ADMIN_PASSWORD, Api, ROOT, login


def test_wrong_password_has_a_useful_error_and_can_be_corrected(server, page):
    base, _ = server
    login(page, base, password="incorrect-password")
    expect(page.locator("#login-error")).to_have_text("Invalid username or password")
    expect(page.locator("#login-go")).to_be_enabled()
    page.fill("#login-pass", ADMIN_PASSWORD)
    page.click("#login-go")
    page.wait_for_url("**/#/admin*", timeout=15000)


def test_retry_countdown_blocks_repeated_submits_and_survives_reload(server, page):
    base, _ = server
    attempts = []

    def throttle_once(route):
        attempts.append(route.request.post_data_json)
        route.fulfill(status=429, headers={"Content-Type": "application/json", "Retry-After": "2"},
                      body=json.dumps({"detail": {"code": "TOO_MANY_ATTEMPTS", "message": "Try again in 2 s."}}))
    page.route("**/api/auth/login", throttle_once)
    login(page, base)
    expect(page.locator("#login-wait")).to_contain_text("password is not checked")
    expect(page.locator("#login-go")).to_be_disabled()
    page.locator("#login-form").evaluate("form => { form.requestSubmit(); form.requestSubmit(); }")
    assert len(attempts) == 1
    page.reload()
    expect(page.locator("#login-go")).to_be_disabled()
    expect(page.locator("#login-go")).to_be_enabled(timeout=6000)
    expect(page.locator("#login-wait")).to_be_hidden()
    page.unroute("**/api/auth/login", throttle_once)
    page.fill("#login-user", "impress.default.superAdmin")
    page.fill("#login-pass", ADMIN_PASSWORD)
    page.click("#login-go")
    page.wait_for_url("**/#/admin*", timeout=15000)


def test_root_recovers_the_throttled_account_then_browser_sign_in_works(server, page):
    base, _ = server
    page.goto(base + "/#/login")
    # Hit the real throttle; root's separate process resets credentials and counters.
    for _ in range(5):
        response = page.request.post(base + "/api/auth/login", data={"username": "impress.default.superAdmin", "password": "wrong"})
        assert response.status == 401
    recovered = "Recovered-From-Root-19!"
    result = subprocess.run([sys.executable, "-m", "app.console"], cwd=ROOT / "backend", env=Api.console_env,
                            input=f"users set-password impress.default.superAdmin --password {recovered}\n",
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0
    page.fill("#login-user", "impress.default.superAdmin")
    page.fill("#login-pass", recovered)
    page.click("#login-go")
    page.wait_for_url("**/#/admin*", timeout=15000)
