"""Browser UI checks: a real backend on a temp database, driven by Playwright.

Run: python run_tests.py --with-ui   (or: pytest ui_tests)
Needs `pip install -r ui_tests/requirements.txt` and a browser: the bundled
Chromium (`python -m playwright install chromium`) or a local Google Chrome.
Screenshots of every test land in ui_tests/screenshots/ (git-ignored).
"""

import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHOTS = Path(__file__).parent / "screenshots"
ADMIN_PASSWORD = "ui-admin-pw"


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Api:
    """Tiny JSON client for setting up data the test then checks in the UI."""

    def __init__(self, base, token=None):
        self.base, self.token = base, token

    def __call__(self, path, body=None, method=None):
        req = urllib.request.Request(self.base + path, method=method or ("POST" if body is not None else "GET"))
        req.add_header("content-type", "application/json")
        if self.token:
            req.add_header("authorization", f"Bearer {self.token}")
        with urllib.request.urlopen(req, json.dumps(body).encode() if body is not None else None) as r:
            return json.loads(r.read() or b"null")


@pytest.fixture
def server():
    """A fresh backend per test: (base_url, admin Api)."""
    tmp = Path(tempfile.mkdtemp(prefix="impress-ui-"))
    port = _free_port()
    env = {**os.environ, "IMPRESS_DATABASE_URL": f"sqlite+aiosqlite:///{tmp}/ui.db", "IMPRESS_DEBUG": "false",
           "IMPRESS_JWT_SECRET": "ui-secret-not-default", "IMPRESS_DEVICE_API_KEY": "ui-device-key",
           "IMPRESS_INITIAL_ADMIN_PASSWORD": ADMIN_PASSWORD, "IMPRESS_FIRMWARE_DIR": str(tmp / "fw")}
    log = open(tmp / "server.log", "w")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port),
                             "--log-level", "warning"], cwd=ROOT / "backend", env=env, stdout=log,
                            stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(120):
            try:
                urllib.request.urlopen(base + "/health")
                break
            except OSError:
                if proc.poll() is not None:
                    raise RuntimeError((tmp / "server.log").read_text())
                time.sleep(0.25)
        token = Api(base)("/api/auth/login", {"username": "admin", "password": ADMIN_PASSWORD})["access_token"]
        yield base, Api(base, token)
    finally:
        proc.terminate()
        proc.wait(10)
        log.close()


@pytest.fixture(scope="session")
def browser():
    from playwright.sync_api import Error, sync_playwright
    with sync_playwright() as p:
        try:
            b = p.chromium.launch(headless=True)              # bundled Chromium (CI)
        except Error:
            b = p.chromium.launch(channel="chrome", headless=True)   # local Google Chrome
        yield b
        b.close()


@pytest.fixture
def page(browser, request):
    """A page that fails the test on any uncaught JS error; screenshot at the end."""
    ctx = browser.new_context(viewport={"width": 1200, "height": 900}, accept_downloads=True)
    # hermetic: only the local test server. The SPA loads web fonts from the
    # internet; on a slow network the page's load event then times out.
    ctx.route("**/*", lambda route: route.continue_() if route.request.url.startswith("http://127.0.0.1")
              else route.abort())
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    yield pg
    SHOTS.mkdir(exist_ok=True)
    try:
        pg.screenshot(path=str(SHOTS / f"{request.node.name}.png"), full_page=True)
    finally:
        ctx.close()
    assert not errors, f"uncaught JavaScript errors: {errors}"


def login(page, base, username="admin", password=ADMIN_PASSWORD):
    page.goto(base + "/#/login")
    page.fill("#login-user", username)
    page.fill("#login-pass", password)
    page.click("button[type=submit]")
