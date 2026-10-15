"""Root's terminal dashboard: actions on the left, logs on the right, commands below.

Only the main thread paints the terminal. Server logs and command output update a
bounded model; raw keyboard input edits that model, never a competing readline
prompt. A separate console process runs each command with the server's policy.
"""

from __future__ import annotations

import os
import queue
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


MENU = (
    ("Overview", "status"), ("Accounts", "users list"), ("Signed-in users", "sessions list"),
    ("Show credentials", "password show"), ("Unlock account...", "users unlock "),
    ("Classrooms", "classes list"), ("Students", "students list"), ("Courses", "courses list"),
    ("Devices", "devices list"), ("Firmware", "firmware list"), ("Deployments", "firmware deployments"),
    ("Quizzes", "quizzes list"), ("Polls", "polls list"), ("Feature switches", "features"),
    ("Backups", "backup list"), ("Command help", "help"), ("Clear logs", "clear"), ("Stop server", "exit"),
)


def plain(text: str) -> str:
    return _SGR.sub("", text)


def safe_text(text: str) -> str:
    """Keep colour, but never let output move the cursor or change terminal modes."""
    parts = []
    for token in _SGR.split(text):
        if _SGR.fullmatch(token):
            parts.append(token)
        else:
            # Discard OSC and non-SGR CSI sequences, then other control bytes.
            token = re.sub(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)", "", token)
            token = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", token)
            parts.append("".join(ch for ch in token if ch.isprintable() or ch in "\n\t"))
    return "".join(parts)


def pad(text: str, width: int) -> str:
    clipped = _fit_ansi(text, max(1, width)) if width else ""
    return clipped + " " * max(0, width - sum(_cell_width(ch) for ch in plain(clipped)))


class Screen:
    HISTORY = 2000

    def __init__(self, title_lines: list[str]):
        self.lock = threading.RLock()
        self.dirty = threading.Event()
        self.title = title_lines
        self.messages: deque[str] = deque(maxlen=self.HISTORY)
        self._wrapped_cache: deque[list[str]] = deque(maxlen=self.HISTORY)
        self._cache_width = 0
        self.scrollback = 0
        self.focus, self.selected = "menu", 0
        self.buffer, self.cursor = "", 0
        self.history: list[str] = []
        self.history_index, self.draft = 0, ""
        self.busy, self.quit, self.pending = False, False, 0
        self.notice = "Choose an action, or type a command."
        self._measure()
        self.dirty.set()

    def _measure(self) -> None:
        size = shutil.get_terminal_size((100, 30))
        self.rows, self.cols = max(1, size.lines), max(1, size.columns)
        self.header = 2 if self.rows >= 12 else 1
        self.left = min(25, max(8, self.cols // 3)) if self.cols >= 24 else 0
        self.log_width = max(1, self.cols - self.left - (3 if self.left else 0))
        self.top = self.header + 2
        self.bottom = max(self.top, self.rows - 3)
        self.page = max(1, self.bottom - self.top + 1)

    def _wrapped_logs(self) -> list[str]:
        if self._cache_width != self.log_width or len(self._wrapped_cache) != len(self.messages):
            self._wrapped_cache = deque((self._wrap_message(msg) for msg in self.messages), maxlen=self.HISTORY)
            self._cache_width = self.log_width
        return [line for chunk in self._wrapped_cache for line in chunk]

    def _wrap_message(self, message: str) -> list[str]:
        return [part for line in message.split("\n")
                for part in wrap_ansi(line, self.log_width, indent=min(3, self.log_width // 5))]

    def frame(self) -> list[str]:
        """Build a complete frame, including blank rows, for drawing and terminal tests."""
        with self.lock:
            self._measure()
            if self.rows < 6 or self.cols < 24:
                return ([c(ACCENT, "imPress root"), "Resize terminal: 24 columns, 6 rows minimum."] +
                        [""] * self.rows)[:max(0, self.rows - 1)] + ["> " + self.buffer]
            log_title = "LOGS (scrollback)" if self.scrollback else "LOGS (live)"
            if self.busy:
                log_title += " | running command"
                if self.pending > 1:
                    log_title += f" (+{self.pending - 1} queued)"
            lines = [self.title[0]]
            if self.header == 2:
                lines.append(self.title[1] if len(self.title) > 1 else "")
            lines.append(pad(c(ACCENT if self.focus == "menu" else DIM, "ACTIONS"), self.left) + " | " +
                         c(ACCENT if self.focus == "logs" else DIM, log_title))
            logs = self._wrapped_logs()
            self.scrollback = min(self.scrollback, max(0, len(logs) - self.page))
            end = len(logs) - self.scrollback
            visible = logs[max(0, end - self.page):end]
            start = max(0, min(self.selected - self.page + 1, len(MENU) - self.page))
            for i in range(self.page):
                idx = start + i
                label = ("> " if idx == self.selected else "  ") + MENU[idx][0] if idx < len(MENU) else ""
                if idx == self.selected:
                    label = c("48;5;24;38;5;255" if self.focus == "menu" else ACCENT, label)
                log = visible[i] if i < len(visible) else ""
                if not logs and i == 0:
                    log = c(DIM, "Waiting for server output...")
                lines.append(pad(label, self.left) + c(DIM, " | ") + log)
            lines.append(c(DIM, "─" * self.cols))
            prompt, self.input_col = self._input_line()
            lines.append(prompt)
            hint = "Tab: focus | arrows: move | Enter: select/run | PgUp/PgDn: logs | Ctrl+L: redraw"
            lines.append(c(DIM, self.notice if self.busy else hint))
            return lines[:self.rows]

    def _input_line(self) -> tuple[str, int]:
        prefix = "root> " if self.cols >= 40 else "> "
        width = max(1, self.cols - len(prefix) - 1)
        before = self.buffer[:self.cursor]
        offset, used = 0, sum(_cell_width(ch) for ch in before)
        while used >= width and offset < len(before):
            used -= _cell_width(before[offset])
            offset += 1
        text = self.buffer[offset:]
        col = len(prefix) + sum(_cell_width(ch) for ch in before[offset:]) + 1
        return c(ACCENT if self.focus == "command" else DIM, prefix) + text, min(self.cols, col)

    def draw(self, clear: bool = False) -> None:
        with self.lock:
            self.dirty.clear()
            lines = self.frame()
            out = f"{ESC}[?25l" + (f"{ESC}[2J{ESC}[H" if clear else "")
            for row, line in enumerate(lines, start=1):
                out += f"{ESC}[{row};1H{ESC}[2K" + _fit_ansi(line, self.cols)
            if self.focus == "command" and self.rows >= 6 and self.cols >= 24:
                out += f"{ESC}[{self.rows - 1};{self.input_col}H{ESC}[?25h"
            sys.stdout.write(out)
            sys.stdout.flush()

    def set_title(self, lines: list[str]) -> None:
        with self.lock:
            self.title = lines
            self.dirty.set()

    def log(self, text: str) -> None:
        with self.lock:
            text = safe_text(text)
            wrapped = self._wrap_message(text)
            if self.scrollback:
                self.scrollback += len(wrapped)
            self.messages.append(text)
            if self._cache_width == self.log_width:
                self._wrapped_cache.append(wrapped)
            self.dirty.set()

    def scroll(self, action: str, amount: int = 8) -> None:
        with self.lock:
            maximum = max(0, len(self._wrapped_logs()) - self.page)
            if action in {"live", "bottom"}:
                self.scrollback = 0
            elif action == "down":
                self.scrollback = max(0, self.scrollback - amount)
            elif action == "up":
                self.scrollback = min(maximum, self.scrollback + amount)
            elif action == "top":
                self.scrollback = maximum
            self.dirty.set()

    def clear(self) -> None:
        with self.lock:
            self.messages.clear()
            self._wrapped_cache.clear()
            self.scrollback = 0
            self.dirty.set()

    def finish(self, ok: bool) -> None:
        with self.lock:
            self.pending = max(0, self.pending - 1)
            self.busy = self.pending > 0
            self.notice = "Command completed." if ok else "Command failed; see the log for details."
            self.dirty.set()

    def _submit(self, command: str) -> str | None:
        if not command.strip():
            return None
        if command.strip() in {"clear", "cls"}:
            self.clear()
            return None
        if command.strip().split()[0] == "scroll":
            parts = command.split()
            if len(parts) not in (2, 3) or parts[1] not in {"up", "down", "top", "bottom", "live"}:
                self.log("usage: scroll up/down [lines] | top | bottom | live")
            else:
                try:
                    self.scroll(parts[1], max(1, min(500, int(parts[2]))) if len(parts) == 3 else self.page)
                except ValueError:
                    self.log("scroll: the line count must be a number")
            return None
        if command.strip() in {"exit", "quit", "stop"}:
            self.quit = True
            return None
        if self.pending >= 8:
            self.log("Eight commands are already queued. Wait for one to finish.")
            return None
        # Credentials typed into a command are not echoed or kept in history.
        sensitive = bool(re.search(r"password|secret|token|authorization", command, re.I))
        if not sensitive:
            if not self.history or self.history[-1] != command:
                self.history.append(command)
                self.history = self.history[-100:]
        self.history_index = len(self.history)
        self.log(c(ORANGE, "> ") + (command.split()[0] + " [private arguments]" if sensitive else command))
        self.pending += 1
        self.busy, self.notice = True, "Commands run in order; logs continue to update."
        return command

    def key(self, key: str) -> str | None:
        with self.lock:
            self.dirty.set()
            if key in {"INTERRUPT", "EOF"}:
                self.quit = True
            elif key == "ESCAPE":
                self.focus = "menu"
            elif key in {"TAB", "BACKTAB"}:
                panes = ["menu", "logs", "command"]
                self.focus = panes[(panes.index(self.focus) + (-1 if key == "BACKTAB" else 1)) % 3]
            elif key in {"PAGEUP", "PAGEDOWN"}:
                self.scroll("up" if key == "PAGEUP" else "down", self.page)
            elif key == "REDRAW":
                pass                         # next full frame erases stale terminal content
            elif key.startswith(("TEXT:", "PASTE:")):
                text = key.split(":", 1)[1]
                self.focus = "command"
                text = "".join(ch if ch.isprintable() else " " for ch in text)[:4096 - len(self.buffer)]
                self.buffer = self.buffer[:self.cursor] + text + self.buffer[self.cursor:]
                self.cursor += len(text)
            elif self.focus == "menu":
                if key in {"UP", "DOWN"}:
                    self.selected = (self.selected + (-1 if key == "UP" else 1)) % len(MENU)
                elif key in {"HOME", "END"}:
                    self.selected = 0 if key == "HOME" else len(MENU) - 1
                elif key == "RIGHT":
                    self.focus = "logs"
                elif key == "ENTER":
                    command = MENU[self.selected][1]
                    if command.endswith(" "):
                        self.focus, self.buffer, self.cursor = "command", command, len(command)
                    else:
                        return self._submit(command)
            elif self.focus == "logs":
                if key == "LEFT":
                    self.focus = "menu"
                elif key in {"UP", "DOWN", "HOME", "END", "ENTER"}:
                    self.scroll({"UP": "up", "DOWN": "down", "HOME": "top", "END": "live", "ENTER": "live"}[key], 1)
            elif self.focus == "command":
                if key == "ENTER":
                    if self.pending >= 8:
                        self.notice = "Command queue is full. Your text is kept; retry when a command finishes."
                        return None
                    command, self.buffer, self.cursor = self.buffer.strip(), "", 0
                    return self._submit(command)
                if key in {"UP", "DOWN"}:
                    if self.history_index == len(self.history):
                        self.draft = self.buffer
                    self.history_index = min(len(self.history), max(0, self.history_index + (-1 if key == "UP" else 1)))
                    self.buffer = self.history[self.history_index] if self.history_index < len(self.history) else self.draft
                    self.cursor = len(self.buffer)
                elif key in {"LEFT", "RIGHT"}:
                    self.cursor = max(0, min(len(self.buffer), self.cursor + (-1 if key == "LEFT" else 1)))
                elif key in {"HOME", "END"}:
                    self.cursor = 0 if key == "HOME" else len(self.buffer)
                elif key == "BACKSPACE" and self.cursor:
                    self.buffer = self.buffer[:self.cursor - 1] + self.buffer[self.cursor:]
                    self.cursor -= 1
                elif key == "DELETE":
                    self.buffer = self.buffer[:self.cursor] + self.buffer[self.cursor + 1:]
                elif key == "KILL_START":
                    self.buffer, self.cursor = self.buffer[self.cursor:], 0
                elif key == "KILL_END":
                    self.buffer = self.buffer[:self.cursor]
                elif key == "KILL_WORD":
                    before = self.buffer[:self.cursor].rstrip()
                    at = before.rfind(" ") + 1
                    self.buffer, self.cursor = self.buffer[:at] + self.buffer[self.cursor:], at
        return None


def _title(version: str, state: str, args: list[str], url: str) -> list[str]:
    dot = {"running": c(GREEN, "● running"), "starting": c(YELLOW, "● starting"), "stopped": c(RED, "● stopped")}[state]
    tags = []
    if "--test-mode" in args:
        tags.append(c(YELLOW, "TEST MODE (forced)"))
    if "--bypass-iips" in args:
        tags.append(c(RED + ";1", "INTEGRITY PROTECTION OFF"))
    if "--no-ota" in args:
        tags.append(c(DIM, "OTA off"))
    profile = (args[args.index("--profile") + 1] if "--profile" in args else os.environ.get("IMPRESS_PROFILE", "standard"))
    return [c(BOLD + ";" + ACCENT, f"imPress {version}") + "  |  " + dot + "  |  " + c(DIM, url),
            c(DIM, f"root console · {profile} profile · type help for commands") + ("  " + "  ".join(tags) if tags else "")]


def run(argv: list[str]) -> int:
    from .config import APP_RELEASE
    from .terminal import Terminal
    host = argv[argv.index("--host") + 1] if "--host" in argv else "0.0.0.0"
    port = argv[argv.index("--port") + 1] if "--port" in argv else "8000"
    scheme = "https" if os.environ.get("IMPRESS_SSL_CERTFILE") else "http"
    url = f"{scheme}://{host}:{port}"
    screen = Screen(_title(APP_RELEASE, "starting", argv, url))
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "IMPRESS_ROOT_SCREEN": "1", "NO_COLOR": "1"}
    ready = threading.Event()
    stopping = threading.Event()
    commands: queue.Queue[str | None] = queue.Queue()
    active: list[subprocess.Popen] = []
    active_lock = threading.Lock()
    child = None

    def pump() -> None:
        assert child.stdout is not None
        for line in child.stdout:
            line = line.rstrip("\n")
            if line.strip():
                screen.log(style_line(line))
            if "Application startup complete" in line:
                ready.set()
                screen.set_title(_title(APP_RELEASE, "running", argv, url))
        screen.set_title(_title(APP_RELEASE, "stopped", argv, url))
        screen.log(c(RED, f"the server stopped (exit code {child.wait()})"))

    def command_worker() -> None:
        while not stopping.is_set():
            command = commands.get()
            if command is None:
                break
            while not ready.wait(0.1) and child.poll() is None and not stopping.is_set():
                pass
            if stopping.is_set():
                break
            try:
                # Isolate every print, warning and event-loop lifetime from the
                # drawing thread. Send commands over stdin, never process args.
                proc = subprocess.Popen([sys.executable, "-m", "app.console"],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        text=True, env={**env, "IMPRESS_CONSOLE_COLUMNS": str(screen.log_width)}, bufsize=1)
                with active_lock:
                    active.append(proc)
                try:
                    proc.stdin.write(command + "\n")
                    proc.stdin.close()
                    for line in proc.stdout:
                        screen.log(line.rstrip("\n"))
                    screen.finish(proc.wait() == 0)
                finally:
                    if proc.poll() is None:
                        proc.terminate()
                        proc.wait(timeout=15)
                    with active_lock:
                        active.remove(proc)
            except Exception as exc:                       # one failed command must not end the dashboard
                screen.log(c(RED, f"Command could not finish ({type(exc).__name__}). Check the server log and retry."))
                screen.finish(False)

    with Terminal() as terminal:
        try:
            screen.draw(clear=True)
            child = subprocess.Popen([sys.executable, "-m", "app.serve", "--plain", *argv], stdin=subprocess.DEVNULL,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, bufsize=1)
            threading.Thread(target=pump, daemon=True).start()
            worker = threading.Thread(target=command_worker, daemon=True)
            worker.start()
            while not screen.quit:
                for key in terminal.read():
                    command = screen.key(key)
                    if command is not None:
                        commands.put(command)
                size = shutil.get_terminal_size((100, 30))
                if screen.dirty.is_set() or (size.lines, size.columns) != (screen.rows, screen.cols):
                    screen.draw()
        except KeyboardInterrupt:
            pass
        finally:
            stopping.set()
            commands.put(None)
            with active_lock:
                for proc in active:
                    if proc.poll() is None:
                        proc.terminate()
            if child is not None and child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()
            if "worker" in locals():
                worker.join(timeout=3)
    return 0
