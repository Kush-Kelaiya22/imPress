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
import unicodedata
from collections import deque

ESC = "\033"
ACCENT, DIM, RED, YELLOW, GREEN, RESET, BOLD = "38;5;75", "2", "38;5;203", "38;5;221", "38;5;114", "0", "1"
ORANGE, TITLEBAR = "38;5;208", "48;5;53;38;5;255"        # the orange and aubergine of a familiar Linux terminal
LEVELS = (("CRITICAL", RED + ";1"), ("ERROR", RED), ("WARNING", YELLOW), ("WARN", YELLOW), ("INFO", ACCENT), ("DEBUG", DIM))


def c(code: str, text: str) -> str:
    return f"{ESC}[{code}m{text}{ESC}[0m"


def _cell_width(char: str) -> int:
    if unicodedata.combining(char) or unicodedata.category(char) in {"Cf", "Mn", "Me"}:
        return 0
    return 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1


def _fit_ansi(line: str, width: int) -> str:
    """Clip a line to terminal cells, not Python characters, without counting ANSI styles."""
    width = max(1, width)
    out, used = [], 0
    for token in _SGR.split(line):
        if _SGR.fullmatch(token):
            out.append(token)
            continue
        for char in token:
            cells = _cell_width(char)
            if used + cells > width:
                return "".join(out) + f"{ESC}[0m"
            out.append(char)
            used += cells
    return "".join(out) + f"{ESC}[0m"


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
    """Break a coloured line at `width` terminal cells; ANSI styles cost no width."""
    width = max(1, width)
    indent = min(max(0, indent), max(0, width - 1))
    out, cur, n = [], "", 0
    active_style = ""
    for tok in _SGR.split(line):
        if _SGR.fullmatch(tok):
            cur += tok
            active_style = "" if tok == f"{ESC}[0m" else active_style + tok
            continue
        for ch in tok.replace("\t", "    ").replace("\r", ""):
            cells = _cell_width(ch)
            if n + cells > width and n:
                out.append(cur + f"{ESC}[0m")
                cur, n = " " * indent + active_style, indent
            cur += ch
            n += cells
    return out + [cur] if cur or not out else out


class Screen:
    HEADER, FOOTER = 5, 3          # title bar, three logo lines, then a scrollable log pane
    HISTORY = 2000

    def __init__(self, title_lines: list[str]):
        self.lock = threading.Lock()
        self.title = title_lines
        self.messages: deque[str] = deque(maxlen=self.HISTORY)
        self.scrollback = 0
        self.rows = self.cols = 0
        self.top = self.bottom = 0
        self.compact = False
        self._measure()

    def _measure(self) -> None:
        size = shutil.get_terminal_size((80, 24))
        self.rows, self.cols = max(6, size.lines), max(1, size.columns)
        self.compact = self.rows < 12
        title_rows = 1 if self.compact else self.HEADER - 1
        self.top = title_rows + 2           # title followed by a rule
        self.bottom = max(self.top, self.rows - self.FOOTER)

    def _wrapped_logs(self) -> list[str]:
        width = max(1, self.cols - 1)
        indent = min(11, max(1, width // 5))
        wrapped: list[str] = []
        for message in self.messages:
            for line in message.split("\n"):
                wrapped.extend(wrap_ansi(line, width, indent=indent))
        return wrapped

    def _line(self, row: int, text: str = "") -> None:
        self._w(f"{ESC}[{row};1H{ESC}[2K" + _fit_ansi(text, self.cols - 1))

    def _render(self, clear: bool = False) -> None:
        self._w(f"{ESC}7")
        self._measure()
        if clear:
            self._w(f"{ESC}[2J{ESC}[H")
        self._w(f"{ESC}[r")
        title = [self.title[1] if len(self.title) > 1 else self.title[0]] if self.compact else self.title[:self.HEADER - 1]
        for row, line in enumerate(title, start=1):
            self._line(row, line)
        title_rows = 1 if self.compact else self.HEADER - 1
        rule_row = title_rows + 1
        self._line(rule_row, c(DIM, "─" * self.cols))

        available = self.bottom - self.top + 1
        logs = self._wrapped_logs()
        offset = min(self.scrollback, len(logs))
        end = len(logs) - offset
        if offset and available:
            note = c(YELLOW, "scrollback · use 'scroll down' or 'scroll live' to follow new logs")
            self._line(self.top, note)
            self.top += 1
            available -= 1
        start = max(0, end - available)
        visible = logs[start:end]
        first_row = self.top
        for index in range(available):
            self._line(first_row + index, visible[index] if index < len(visible) else "")
        # Recompute the non-mutating layout after reserving the scrollback hint row.
        self._measure()
        self._line(self.rows - 2, c(DIM, "─" * self.cols))
        hint = "help · scroll up/down/live · status · exit stops the server" if self.cols >= 72 else "help · scroll up/down/live · exit"
        self._line(self.rows - 1, c(DIM, hint))
        self._w(f"{ESC}8")

    def _w(self, text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()

    def draw(self) -> None:
        with self.lock:
            self._render(clear=True)

    def set_title(self, lines: list[str]) -> None:
        with self.lock:
            self.title = lines
            self._render()

    def log(self, text: str) -> None:
        with self.lock:
            if self.scrollback:
                self.scrollback += len(wrap_ansi(text, max(1, self.cols - 1)))
            self.messages.append(text)
            self._render()

    def scroll(self, action: str, amount: int = 8) -> None:
        with self.lock:
            logs = self._wrapped_logs()
            if action in {"live", "bottom", "down"}:
                self.scrollback = 0 if action in {"live", "bottom"} else max(0, self.scrollback - amount)
            elif action == "up":
                self.scrollback = min(len(logs), self.scrollback + amount)
            elif action == "top":
                page_size = max(1, self.bottom - self.top)
                self.scrollback = max(0, len(logs) - page_size)
            self._render()

    def clear(self) -> None:
        with self.lock:
            self.messages.clear()
            self.scrollback = 0
            self._render(clear=True)

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
    host = argv[argv.index("--host") + 1] if "--host" in argv else "0.0.0.0"
    port = argv[argv.index("--port") + 1] if "--port" in argv else "8000"
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
                screen.clear()
                continue
            if line.startswith("scroll"):
                parts = line.split()
                action = parts[1].lower() if len(parts) > 1 else ""
                try:
                    amount = max(1, min(500, int(parts[2]))) if len(parts) > 2 else 8
                except ValueError:
                    amount = 8
                if action not in {"up", "down", "top", "bottom", "live"}:
                    screen.log(c(YELLOW, "usage: scroll up [lines] | down [lines] | top | bottom | live"))
                else:
                    screen.scroll(action, amount)
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
