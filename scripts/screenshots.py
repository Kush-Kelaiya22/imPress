#!/usr/bin/env python3
"""Regenerate the pictures in docs/images from a throw-away demo server.

    pip install -r ui_tests/requirements.txt pyte      # pyte only for the root screen picture
    python -m playwright install chromium
    python scripts/screenshots.py [--out docs/images] [--only name,name]

It starts imPress on a temporary database with made-up data (no real names, no addresses), drives the web app with
Playwright and saves PNGs; the root screen is captured from a pseudo-terminal and drawn as an SVG. Everything it shows
is fictional.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
PASSWORD = "Demo-Pass-2026!"
DEVICE_KEY = "demo-device-key"
FIRST = ["Aarav", "Diya", "Ishaan", "Meera", "Rohan", "Saanvi", "Vihaan", "Anaya", "Kabir", "Tara", "Arjun", "Nisha", "Rhea", "Yash", "Zara",
         "Dev", "Isha", "Karan", "Leela", "Neel", "Pooja", "Sameer", "Tanvi", "Uday", "Veda"]
LAST = ["Rao", "Patel", "Iyer", "Shah", "Nair", "Menon", "Gupta", "Singh", "Kapoor", "Das", "Reddy", "Joshi", "Bose", "Khan", "Verma"]


class Api:
    def __init__(self, base, token=None):
        self.base, self.token = base, token

    def __call__(self, path, body=None, method=None):
        req = urllib.request.Request(self.base + path, method=method or ("POST" if body is not None else "GET"))
        req.add_header("content-type", "application/json")
        if self.token:
            req.add_header("authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, json.dumps(body).encode() if body is not None else None) as r:
                return json.loads(r.read() or b"null")
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                return None
            raise SystemExit(f"{method or 'POST'} {path} -> {exc.code}: {exc.read().decode()[:300]}") from None


def free_port() -> int:
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def console(env, *cmds):
    out = subprocess.run([sys.executable, "-m", "app.console", *[x for c in cmds for x in ("-c", c)]], cwd=BACKEND, env=env, capture_output=True, text=True)
    if out.returncode:
        raise SystemExit(out.stdout + out.stderr)
    return out.stdout


def seed(base, env):
    console(env, "users finish-setup impress.default.superAdmin", "superadmin create seeder --password Seed-Pass-2026!")
    temp = Api(base)("/api/auth/login", {"username": "seeder", "password": "Seed-Pass-2026!"})["access_token"]
    Api(base, temp)("/api/auth/change-password", {"current_password": "Seed-Pass-2026!", "new_password": "Seeder-Final-2026!"})
    api = Api(base, Api(base)("/api/auth/login", {"username": "seeder", "password": "Seeder-Final-2026!"})["access_token"])
    rnd = random.Random(7)
    people = [("anita.rao", "Dr. Anita Rao", "teacher", "faculty"), ("dev.patel", "Dev Patel", "teacher", "faculty"), ("meera.iyer", "Meera Iyer", "teacher", "ta"),
              ("rohan.shah", "Rohan Shah", "admin", "faculty")]
    ids = {}
    for username, name, role, desig in people:
        r = api("/api/admin/users", {"username": username, "email": f"{username}@example.edu", "full_name": name, "role": role, "designation": desig, "password": PASSWORD})
        ids[username] = r["id"]
        console(env, f"users finish-setup {username}")
    courses = [("CS101", "Introduction to Programming"), ("PHY101", "Mechanics"), ("MA101", "Calculus"), ("CH101", "Chemistry"), ("BI101", "Biology")]
    cid = {c: api("/api/courses/", {"code": c, "name": n})["id"] for c, n in courses}
    day = time.strftime("%A")
    plan = [("CS101", "A", "rocket", "#5b4ee5", "anita.rao", "RM-201"), ("CS101", "B", "code", "#2563eb", "anita.rao", "RM-202"),
            ("PHY101", "A", "zap", "#d97706", "dev.patel", "RM-110"), ("MA101", "A", "calculator", "#0d9488", "dev.patel", "RM-111"),
            ("CH101", "A", "flask", "#16a34a", "meera.iyer", "RM-301"), ("BI101", "A", "leaf", "#e11d48", "meera.iyer", "RM-302")]
    classes = []
    for i, (course, sec, icon, color, teacher, room) in enumerate(plan):
        name = next(n for c, n in courses if c == course)
        c = api("/api/admin/classes", {"name": f"{course} Sec {sec}", "code": f"{course}-{sec}", "course_id": cid[course], "course_section": sec, "icon": icon, "color": color,
                                       "teacher_id": ids[teacher], "classroom_code": room, "term": "Monsoon", "year": 2026,
                                       "meeting_schedule": [{"day": day, "start": f"{9 + i}:00".rjust(5, "0"), "end": f"{10 + i}:00".rjust(5, "0")}]})
        classes.append(c["id"])
    students = []
    for n in range(36):
        name = f"{rnd.choice(FIRST)} {rnd.choice(LAST)}"
        sid = api("/api/students/", {"roll_number": f"S{2026000 + n:09d}"[:10], "student_name": name, "email": f"s{n}@example.edu", "program": "B.Tech"})["id"]
        students.append(sid)
        for c in rnd.sample(classes, 2):
            try:
                api(f"/api/admin/classes/{c}/enroll", {"student_id": sid})
            except Exception:
                pass
    try:
        api(f"/api/classes/{classes[0]}/activate", {})
    except Exception:
        pass
    for c in classes[:3]:
        try:
            q = api("/api/quizzes/", {"class_session_id": c, "title": "Week 3 check", "questions": [
                {"question_text": "Which is a loop?", "options": ["for", "if", "def", "class"], "correct_option": 0}]})
            api(f"/api/quizzes/{q['id']}/start", {})
        except Exception:
            pass
    return api


def run_server(tmp, port, extra_env=None):
    env = {**os.environ, "IMPRESS_DATABASE_URL": f"sqlite+aiosqlite:///{tmp}/demo.db", "IMPRESS_DEBUG": "false", "IMPRESS_JWT_SECRET": "demo-secret-not-default",
           "IMPRESS_DEVICE_API_KEY": DEVICE_KEY, "IMPRESS_INITIAL_ADMIN_PASSWORD": PASSWORD, "IMPRESS_FIRMWARE_DIR": str(tmp / "fw"),
           "IMPRESS_REQUIRE_HTTPS": "false", "IMPRESS_TEMP_BACKUP_DIR": str(tmp / "bk"), **(extra_env or {})}
    log = open(tmp / "server.log", "w")
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"], cwd=BACKEND, env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    base = f"http://127.0.0.1:{port}"
    for _ in range(160):
        try:
            urllib.request.urlopen(base + "/health")
            return proc, base, env
        except OSError:
            time.sleep(0.25)
    raise SystemExit("the demo server did not start: " + (tmp / "server.log").read_text())


def ansi_to_svg(raw: bytes, out: Path, cols=100, rows=26) -> None:
    import pyte
    screen = pyte.Screen(cols, rows)
    stream = pyte.ByteStream(screen)
    stream.feed(raw)
    palette = {"default": "#d8dae5", "black": "#1b1d2b", "red": "#ff6b8a", "green": "#6ee7a8", "brown": "#f2c14e", "blue": "#7aa7ff", "magenta": "#c4a6ff", "cyan": "#6bd6e8", "white": "#eceef6"}
    def colour(c, default):
        if c == "default":
            return default
        if re.fullmatch(r"[0-9a-f]{6}", c):
            return "#" + c
        return palette.get(c, default)
    cw, ch, pad = 8.4, 18, 14
    w, h = cols * cw + pad * 2, rows * ch + pad * 2 + 30
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace" font-size="13.5">',
             f'<rect width="{w:.0f}" height="{h:.0f}" rx="10" fill="#1d1722"/><rect width="{w:.0f}" height="30" rx="10" fill="#4a1d3d"/><rect y="20" width="{w:.0f}" height="10" fill="#4a1d3d"/>',
             '<circle cx="18" cy="15" r="5" fill="#e95420"/><circle cx="36" cy="15" r="5" fill="#77216f"/><circle cx="54" cy="15" r="5" fill="#5e2750"/>',
             f'<text x="{w / 2:.0f}" y="19" text-anchor="middle" fill="#f4e9f0" font-size="12">root@impress: ~</text>']
    for y in range(rows):
        line = screen.buffer[y]
        x = 0
        while x < cols:
            c = line[x]
            run = [c]
            while x + len(run) < cols and (line[x + len(run)].fg, line[x + len(run)].bg, line[x + len(run)].bold) == (c.fg, c.bg, c.bold):
                run.append(line[x + len(run)])
            text = "".join(r.data for r in run)
            if c.bg != "default":
                parts.append(f'<rect x="{pad + x * cw:.1f}" y="{30 + pad + y * ch - 13:.1f}" width="{len(run) * cw:.1f}" height="{ch}" fill="{colour(c.bg, "#1d1722")}"/>')
            if text.strip():
                esc = text.replace("&", "&amp;").replace("<", "&lt;").replace(" ", "&#160;")
                parts.append(f'<text x="{pad + x * cw:.1f}" y="{30 + pad + y * ch:.1f}" fill="{colour(c.fg, palette["default"])}"{" font-weight=\"700\"" if c.bold else ""} xml:space="preserve">{esc}</text>')
            x += len(run)
    parts.append("</svg>")
    out.write_text("".join(parts))


def root_screen(tmp, out: Path) -> None:
    import pty
    import select
    import socket
    with socket.socket() as probe:
        try:
            probe.bind(("0.0.0.0", 8000))
        except OSError:
            raise SystemExit("Root-screen capture needs port 8000 free; no existing listener was stopped.") from None
    env = {**os.environ, "IMPRESS_DATABASE_URL": f"sqlite+aiosqlite:///{tmp}/screen.db", "IMPRESS_GPC": "", "IMPRESS_TEMP_BACKUP_DIR": str(tmp / "sbk"),
           "IMPRESS_FIRMWARE_DIR": str(tmp / "sfw"), "IMPRESS_DEFAULT_SUPERADMIN_PASSWORD": PASSWORD,
           "IMPRESS_JWT_SECRET": "screen-demo-secret", "IMPRESS_DEVICE_API_KEY": DEVICE_KEY, "IMPRESS_REQUIRE_HTTPS": "false",
           "IMPRESS_MIN_CORES": "1", "IMPRESS_MIN_MEMORY_MB": "1", "IMPRESS_MIN_DISK_MB": "1",
           "PYTHONPATH": str(BACKEND), "COLUMNS": "100", "LINES": "26", "TERM": "xterm-256color"}
    env.pop("IMPRESS_PLAIN", None)
    env.pop("IMPRESS_ROOT_SCREEN", None)
    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(tmp)
        os.execvpe(sys.executable, [sys.executable, "-m", "app.serve"], env)
    import fcntl
    import struct
    import termios
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 26, 100, 0, 0))
    buf = b""

    def pump(t):
        nonlocal buf
        end = time.time() + t
        while time.time() < end:
            r, _, _ = select.select([fd], [], [], 0.2)
            if r:
                try:
                    buf += os.read(fd, 65536)
                except OSError:
                    return
    try:
        deadline = time.monotonic() + 30
        while b"Application startup complete" not in buf and time.monotonic() < deadline:
            pump(0.25)
        if b"Application startup complete" not in buf:
            raise RuntimeError("The disposable root-screen server did not start")
        os.write(fd, b"\x1b[B\r"); pump(2.5)      # select Accounts using the actual menu
        os.write(fd, b"status\r"); pump(2.5)
        os.write(fd, b"users "); pump(0.3)         # a partially typed command survives live output
        ansi_to_svg(buf, out)
    finally:
        os.write(fd, b"\x03"); pump(3)
        os.close(fd)
        os.waitpid(pid, 0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--out", default=str(ROOT / "docs/images"))
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    only = {x for x in args.only.split(",") if x}
    want = lambda n: not only or n in only                                        # noqa: E731
    tmp = Path(tempfile.mkdtemp(prefix="impress-shots-"))
    if only == {"root-screen"}:
        root_screen(tmp, out / "root-screen.svg")
        print("pictures are in", out)
        return 0
    from playwright.sync_api import sync_playwright
    port = free_port()
    proc, base, env = run_server(tmp, port)
    try:
        seed(base, env)
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception:
                browser = p.chromium.launch(channel="chrome", headless=True)
            ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1, reduced_motion="reduce", color_scheme="light")
            page = ctx.new_page()
            route = lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1") else r.abort()   # noqa: E731
            ctx.route("**/*", route)

            def shot(name, full=False, clip=None):
                if want(name):
                    page.wait_for_timeout(900)
                    page.screenshot(path=str(out / f"{name}.png"), full_page=full)

            page.goto(base + "/#/login"); page.wait_for_selector("#login-user")
            shot("login")
            page.fill("#login-user", "impress.default.superAdmin"); page.fill("#login-pass", PASSWORD); page.click("button[type=submit]")
            page.wait_for_url("**/#/admin*"); page.wait_for_selector(".widgets .widget")
            shot("overview")
            for i in range(75):                                                         # an unusual burst of sign-in attempts: a traffic alert
                try:
                    Api(base)("/api/auth/login", {"username": f"nobody{i}", "password": "x"})
                except (Exception, SystemExit):                                         # noqa: BLE001 (they are meant to fail)
                    pass

            page.click("#dash-customise"); shot("dashboard-customise"); page.click("#dash-customise")
            page.goto(base + "/#/admin/classes"); page.wait_for_selector(".class-card"); shot("classrooms")
            page.goto(base + "/#/admin/classes/new"); page.wait_for_selector("#cls-icons button"); page.click('#cls-icons [data-ic="rocket"]'); page.click('#cls-colors [data-co="#2563eb"]'); shot("class-form")
            page.goto(base + "/#/admin/users"); page.wait_for_selector("#usr-table tr"); shot("accounts")
            page.click("text=Add account"); page.click('[data-pwmode="manual"]'); page.fill("#new-password", "Tr0ub4dor&3-horse"); shot("add-account")
            page.keyboard.press("Escape"); page.click('#create-user-modal [data-action="hide"]')
            page.click('[data-sub="active"]'); page.wait_for_selector(".pres-dot"); shot("active-now")
            page.click('[data-sub="people"]'); page.click('tr:has-text("anita.rao") [data-action="toggle-menu"]'); page.click('tr:has-text("anita.rao") [data-action="usr-activity"]'); page.wait_for_selector(".drawer .act-chart"); shot("activity-history")
            page.keyboard.press("Escape"); page.click("[data-close] >> nth=0")
            page.goto(base + "/#/admin/system"); page.wait_for_selector(".stats-grid"); shot("system")
            for tab in ("features", "requirements", "backups", "security"):
                page.click(f'[data-tab="{tab}"]'); page.wait_for_selector(".card"); shot(f"system-{tab}")
            page.goto(base + "/#/settings"); page.wait_for_selector("#sec-appearance"); shot("settings")
            page.click('[data-action="settings-jump"][data-id="accessibility"]'); shot("settings-accessibility")
            page.keyboard.press("ControlOrMeta+k"); page.wait_for_selector(".palette"); page.fill("#palette-input", "dark"); shot("search"); page.keyboard.press("Escape")
            page.click('[data-action="toggle-notices"]'); shot("notifications"); page.click('[data-action="toggle-notices"]')
            page.click('[data-action="toggle-menu"][data-menu="help-menu"]'); page.click('#help-menu [data-action="start-tour"]'); page.wait_for_selector(".tour-pop"); page.click('[data-tour="next"]'); shot("tour"); page.keyboard.press("Escape")
            page.click('[data-action="toggle-theme"] >> nth=0'); page.goto(base + "/#/admin"); page.wait_for_selector(".widgets .widget"); shot("overview-dark")
            page.click('[data-action="sidebar-toggle"]'); shot("sidebar-collapsed"); page.click('[data-action="sidebar-toggle"]'); page.click('[data-action="toggle-theme"] >> nth=0')
            # overlays
            page.evaluate("Overlays.show('update', { iconName: 'refresh', tone: 'info', spin: true, progress: true, title: 'Updating imPress', text: 'We are sorry for the interruption. imPress is applying a system update and will be available again in a moment. This page returns by itself as soon as the update has finished.' })")
            shot("update-notice"); page.evaluate("Overlays.hide()")
            page.evaluate("Overlays.show('disabled', { iconName: 'userX', title: 'Your account has been disabled', text: 'An administrator has disabled this account, so your session has ended. If you think this is a mistake, please contact your administrator.', button: 'Return to sign in', onButton() {} })")
            shot("disabled-notice"); page.evaluate("Overlays.hide()")
            m = ctx.new_page(); m.set_viewport_size({"width": 390, "height": 800}); ctx.route("**/*", route)
            m.goto(base + "/#/admin/classes"); m.wait_for_selector(".class-card"); m.wait_for_timeout(900)
            if want("phone"):
                m.screenshot(path=str(out / "phone.png"))
            browser.close()
        if want("root-screen"):
            root_screen(tmp, out / "root-screen.svg")
    finally:
        proc.terminate()
        proc.wait(10)
    print("pictures are in", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
