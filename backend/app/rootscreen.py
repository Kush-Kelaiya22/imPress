"""The root screen (v2.2): what root sees when imPress is started from a terminal (a shell, or `docker run -it`).

    ╻┏┳┓┏━┓┏━┓┏━╸┏━┓┏━┓   v2.2.24   ● running    http://0.0.0.0:8000
    ┃┃┃┃┣━┛┣┳┛┣╸ ┗━┓┗━┓   standard profile · integrity protection on
    ╹╹ ╹╹  ╹┗╸┗━╸┗━┛┗━┛   root screen: type help
    ────────────────────────────────────────────────────────────────────────
    10:41:02  INFO     application startup complete
    10:41:09  WARNING  ...                                      (the live log scrolls here)
    ────────────────────────────────────────────────────────────────────────
    help · users list · features · backup save NAME · iips status · exit stops the server
    ❯

The server runs as a child process and its log is shown live above; the prompt at the bottom takes the same commands as
the root console (python -m app.console). Without a terminal (a background container, a pipe, a service) none of this
is used: the log is printed as plain lines. Nothing here is reachable over the network.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import threading
import time

ESC = "\033"
ACCENT, DIM, RED, YELLOW, GREEN, RESET, BOLD = "38;5;75", "2", "38;5;203", "38;5;221", "38;5;114", "0", "1"
ORANGE, TITLEBAR = "38;5;208", "48;5;53;38;5;255"        # the orange and aubergine of a familiar Linux terminal
LEVELS = (("CRITICAL", RED + ";1"), ("ERROR", RED), ("WARNING", YELLOW), ("WARN", YELLOW), ("INFO", ACCENT), ("DEBUG", DIM))


def c(code: str, text: str) -> str:
    return f"{ESC}[{code}m{text}{ESC}[0m"


def style_line(raw: str) -> str:
    """Colour a log line by its level; access-log lines are quiet."""
    stamp = time.strftime("%H:%M:%S")
    for name, code in LEVELS:
        m = re.search(rf"\b{name}\b:?\s*", raw)
        if m:
            body = raw[m.end():].strip()
            quiet = DIM if re.search(r'"(GET|POST|PUT|DELETE|HEAD)\s', body) else None
            return f"{c(DIM, stamp)}  {c(code, name.ljust(8))} {c(quiet, body) if quiet else body}"
    return f"{c(DIM, stamp)}  {' ' * 8} {raw}"


_SGR = re.compile(r"(\x1b\[[0-9;]*m)")


def wrap_ansi(line: str, width: int, indent: int = 11) -> list[str]:
    """Break a coloured line at `width` visible characters; the colour codes cost no width."""
    out, cur, n = [], "", 0
    for tok in _SGR.split(line):
        if _SGR.fullmatch(tok):
            cur += tok
            continue
        for ch in tok:
            if n >= width:
                out.append(cur + f"{ESC}[0m")
                cur, n = " " * indent, indent
            cur += ch
            n += 1
    return out + [cur] if cur or not out else out


class Screen:
    HEADER, FOOTER = 5, 3          # title bar, three lines of logo (the rule is row HEADER), then the log

    def __init__(self, title_lines: list[str]):
        self.lock = threading.Lock()
        self.title = title_lines
        size = shutil.get_terminal_size((100, 30))
        self.rows, self.cols = (size.lines if size.lines >= 12 else 30), (size.columns if size.columns >= 40 else 100)
        self.top, self.bottom = self.HEADER + 1, self.rows - self.FOOTER

    def _w(self, text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()

    def draw(self) -> None:
        rule = c(DIM, "─" * self.cols)
        with self.lock:
            self._w(f"{ESC}[2J{ESC}[H")
            for i, line in enumerate(self.title[:self.HEADER - 1]):
                self._w(f"{ESC}[{i + 1};1H{line}")
            self._w(f"{ESC}[{self.HEADER};1H{rule}")
            self._w(f"{ESC}[{self.rows - 2};1H{rule}")
            self._w(f"{ESC}[{self.rows - 1};1H" + c(DIM, " help · status · users list · features · backup save NAME · policylog · exit stops the server"))
            self._w(f"{ESC}[{self.top};{self.bottom}r{ESC}[{self.bottom};1H")

    def set_title(self, lines: list[str]) -> None:
        self.title = lines
        with self.lock:
            self._w(f"{ESC}7")
            for i, line in enumerate(lines[:self.HEADER - 1]):
                self._w(f"{ESC}[{i + 1};1H{ESC}[2K{line}")
            self._w(f"{ESC}8")

    def log(self, text: str) -> None:
        width = max(20, self.cols - 1)
        parts: list[str] = []
        for line in text.split("\n"):
            parts += wrap_ansi(line, width)
        with self.lock:
            self._w(f"{ESC}7{ESC}[{self.bottom};1H")
            for p in parts:
                self._w(f"\n{p}{ESC}[0m")
            self._w(f"{ESC}8")

    def prompt(self) -> str:
        with self.lock:
            self._w(f"{ESC}[{self.rows};1H{ESC}[2K")
        return input(f"\001{ESC}[1;32m\002root@impress\001{ESC}[0m\002:\001{ESC}[1;34m\002~\001{ESC}[0m\002\001{ESC}[{ORANGE};1m\002>\001{ESC}[0m\002 ")

    def close(self) -> None:
        self._w(f"{ESC}[r{ESC}[{self.rows};1H\n")


def _title(version: str, state: str, args: list[str], url: str) -> list[str]:
    from .banner import MARK
    dot = {"running": c(GREEN, "● running"), "starting": c(YELLOW, "● starting"), "stopped": c(RED, "● stopped")}[state]
    tags = []
    if "--test-mode" in args:
        tags.append(c(YELLOW, "TEST MODE (forced)"))
    if "--bypass-iips" in args:
        tags.append(c(RED + ";1", "INTEGRITY PROTECTION OFF"))
    if "--no-ota" in args:
        tags.append(c(DIM, "OTA off"))
    profile = (args[args.index("--profile") + 1] if "--profile" in args else os.environ.get("IMPRESS_PROFILE", "standard"))
    cols = shutil.get_terminal_size((100, 30)).columns
    cols = cols if cols >= 40 else 100
    left, right = "  root@impress: ~", f"imPress {version} · root screen  "
    bar = c(TITLEBAR, (left + " " * max(1, cols - len(left) - len(right)) + right)[:cols])
    return [bar,
            c(ORANGE + ";1", MARK[0]) + f"   {c(BOLD, 'v' + version)}   {dot}    {c(DIM, url)}",
            c(ORANGE + ";1", MARK[1]) + f"   {c(DIM, profile + ' profile')}" + ("  " + "  ".join(tags) if tags else ""),
            c(ORANGE + ";1", MARK[2]) + f"   {c(DIM, 'type help for the commands')}"]


def run(argv: list[str]) -> int:
    from .config import APP_RELEASE
    if os.name == "nt":
        os.system("")                                    # turns on ANSI colours in the Windows console
    else:
        try:
            import readline  # noqa: F401
        except ImportError:
            pass
    host = argv[argv.index("--host") + 1] if "--host" in argv else os.environ.get("IMPRESS_HOST", "127.0.0.1")
    port = argv[argv.index("--port") + 1] if "--port" in argv else os.environ.get("IMPRESS_PORT", "8000")
    scheme = "https" if os.environ.get("IMPRESS_SSL_CERTFILE") else "http"
    url = f"{scheme}://{host}:{port}"
    screen = Screen(_title(APP_RELEASE, "starting", argv, url))
    screen.draw()
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "IMPRESS_ROOT_SCREEN": "1", "NO_COLOR": "1"}
    child = subprocess.Popen([sys.executable, "-m", "app.serve", "--plain", *argv], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, env=env, bufsize=1)

    def pump() -> None:
        assert child.stdout is not None
        for line in child.stdout:
            line = line.rstrip("\n")
            if line.strip():
                screen.log(style_line(line))
            if "Application startup complete" in line:
                screen.set_title(_title(APP_RELEASE, "running", argv, url))
        screen.set_title(_title(APP_RELEASE, "stopped", argv, url))
        screen.log(c(RED, f"the server stopped (exit code {child.wait()})"))

    threading.Thread(target=pump, daemon=True).start()
    console = None

    class Out:
        """What a root command prints goes into the log area, line by line."""
        def write(self, text: str) -> int:
            for line in text.rstrip("\n").split("\n") if text.strip() else []:
                screen.log(c(ORANGE, "›") + " " + line)
            return len(text)

        def flush(self) -> None:
            pass

    try:
        while True:
            try:
                line = screen.prompt().strip()
            except EOFError:
                break
            if not line:
                continue
            if line in ("exit", "quit", "stop"):
                break
            if line == "clear":
                screen.draw()
                continue
            if child.poll() is not None and line == "start":
                screen.log(c(YELLOW, "restart imPress from the shell: the screen closes when the server has stopped"))
                continue
            if console is None:
                from .console import Console
                console = Console(out=Out())
            screen.log(c(DIM, "> " + line))
            console.onecmd(line)
    except KeyboardInterrupt:
        pass
    finally:
        if child.poll() is None:
            screen.log(c(YELLOW, "stopping the server…"))
            child.terminate()
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
        if console is not None:
            console.close()
        screen.close()
    return 0
