"""Dashboard input/rendering contracts and a real pseudoterminal/server session."""

import codecs
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

from app import rootscreen
from app.terminal import KeyDecoder


def test_fragmented_keys_unicode_and_bracketed_paste():
    decoder = KeyDecoder()
    assert decoder.feed("\x1b[") == []
    assert decoder.feed("A") == ["UP"]
    assert decoder.feed("\x1bOD") == ["LEFT"]
    assert decoder.feed("\x1b[200~users unlock someone\nexit\x1b[20") == []
    assert decoder.feed("1~") == ["PASTE:users unlock someone exit"]
    assert decoder.feed("\x1b") == []
    assert decoder.feed("", flush_escape=True) == ["ESCAPE"]
    assert decoder.feed("界é\r") == ["TEXT:界", "TEXT:é", "ENTER"]
    assert decoder.feed("\x1b[1;5A") == []       # unknown extended key, never command text


def test_windows_native_key_prefixes_and_shift_tab(monkeypatch):
    from types import SimpleNamespace
    from app import terminal
    chars = iter(["\xe0", "H", "\xe0", "P", "\xe0", "I", "\x00", "\x0f", "\r", "界"])
    monkeypatch.setitem(sys.modules, "msvcrt", SimpleNamespace(kbhit=lambda: True, getwch=lambda: next(chars)))
    monkeypatch.setattr(terminal, "os", SimpleNamespace(name="nt"))
    reader = terminal.Terminal()
    assert [reader.read() for _ in range(6)] == [["UP"], ["DOWN"], ["PAGEUP"], ["BACKTAB"], ["ENTER"], ["TEXT:界"]]


@pytest.mark.parametrize("width", [72, 48, 16, 6])
def test_command_tables_fit_the_log_pane_without_splitting_wide_characters(monkeypatch, width):
    from app.console import table
    monkeypatch.setenv("IMPRESS_CONSOLE_COLUMNS", str(width))
    result = table([{"id": 1, "username": "impress.default.superAdmin", "name": "界" * 20, "role": "super_admin",
                     "designation": "faculty", "status": "active"}])
    assert all(sum(rootscreen._cell_width(ch) for ch in row) <= width for row in result.splitlines())
    if width >= 72:
        assert "impress.default.superAdmin" in result


def test_actions_text_editing_history_and_clear(monkeypatch):
    monkeypatch.setattr(rootscreen.shutil, "get_terminal_size", lambda _fallback: os.terminal_size((100, 28)))
    screen = rootscreen.Screen(["imPress test", "running"])
    screen.key("DOWN")
    assert screen.key("ENTER") == "users list"
    screen.finish(True)
    assert screen.key("PASTE:versioz") is None
    screen.key("BACKSPACE")
    screen.key("TEXT:n")
    assert screen.key("ENTER") == "version"
    screen.finish(True)
    screen.key("UP")
    assert screen.buffer == "version"
    screen.key("DOWN")
    assert screen.buffer == ""
    screen.key("PASTE:status")
    screen.key("HOME")
    screen.key("RIGHT")
    screen.key("DELETE")
    assert screen.buffer == "satus" and screen.cursor == 1
    screen.key("KILL_START")
    assert screen.buffer == "atus" and screen.cursor == 0
    screen.key("KILL_END")
    screen.key("PASTE:clear")
    screen.key("ENTER")
    assert not screen.messages
    assert "ACTIONS" in rootscreen.plain("\n".join(screen.frame()))


def test_live_logs_never_write_or_destroy_a_partially_typed_command(monkeypatch, capsys):
    monkeypatch.setattr(rootscreen.shutil, "get_terminal_size", lambda _fallback: os.terminal_size((80, 24)))
    screen = rootscreen.Screen(["imPress", "running"])
    screen.key("PASTE:users show student")
    screen.key("LEFT")
    for i in range(40):
        screen.log(f"INFO: log {i}")
    assert capsys.readouterr().out == ""         # the log producer cannot paint over input
    assert screen.buffer == "users show student" and screen.cursor == 17
    screen.scroll("top")
    before = screen.scrollback
    screen.log("INFO: another message")
    assert screen.scrollback > before
    screen.key("END")                           # edit the command; log view is independent
    assert screen.scrollback > 0
    screen.key("ESCAPE")
    screen.key("TAB")                           # menu -> logs
    screen.key("END")
    assert screen.scrollback == 0


@pytest.mark.parametrize("cols,rows", [(120, 32), (80, 24), (48, 10), (24, 6), (12, 3), (1, 1)])
def test_frames_fit_after_resize_and_keep_commands_on_screen(monkeypatch, cols, rows):
    monkeypatch.setattr(rootscreen.shutil, "get_terminal_size", lambda _fallback: os.terminal_size((cols, rows)))
    screen = rootscreen.Screen(["imPress test", "running"])
    screen.key("PASTE:" + "界" * 30 + " status")
    screen.log("a long log " + "界" * 100)
    frame = screen.frame()
    assert len(frame) == rows
    for line in frame:
        fitted = rootscreen._fit_ansi(line, cols)
        assert sum(rootscreen._cell_width(ch) for ch in rootscreen.plain(fitted)) <= cols


def test_logs_cannot_clear_the_screen_and_password_arguments_are_not_echoed_or_recalled():
    screen = rootscreen.Screen(["imPress", "running"])
    screen.log("name\x1b[2J\x1b]0;changed-title\x07 ok")
    assert "\x1b[2J" not in screen.messages[-1] and "\x07" not in screen.messages[-1]
    screen.key("PASTE:password reset --password Only-In-The-Input-19!")
    screen.key("ENTER")
    assert "Only-In-The-Input" not in "\n".join(screen.messages)
    assert not screen.history


class VT:
    """Small terminal emulator for observing the actual painted PTY, not source strings."""

    def __init__(self, cols, rows):
        self.resize(cols, rows)
        self.pending = ""
        self.decoder = codecs.getincrementaldecoder("utf-8")("replace")

    def resize(self, cols, rows):
        self.cols, self.rows, self.x, self.y = cols, rows, 0, 0
        self.cells = [[" "] * cols for _ in range(rows)]

    @property
    def text(self):
        return "\n".join("".join(row) for row in self.cells)

    def feed(self, data):
        self.pending += self.decoder.decode(data)
        while self.pending:
            if self.pending.startswith("\x1b["):
                m = re.match(r"\x1b\[([0-?]*)([ -/]*)([@-~])", self.pending)
                if not m:
                    break
                args, _, op = m.groups()
                self.pending = self.pending[m.end():]
                nums = [int(n or 0) for n in args.split(";")] if not args.startswith("?") else []
                if op == "H":
                    self.y, self.x = (nums[0] or 1) - 1, ((nums[1] if len(nums) > 1 else 1) or 1) - 1
                elif op == "J" and nums == [2]:
                    self.cells = [[" "] * self.cols for _ in range(self.rows)]
                elif op == "K" and nums == [2] and 0 <= self.y < self.rows:
                    self.cells[self.y] = [" "] * self.cols
                continue
            if self.pending == "\x1b":
                break
            ch, self.pending = self.pending[0], self.pending[1:]
            if ch == "\r":
                self.x = 0
            elif ch == "\n":
                self.y += 1
            elif ch.isprintable() and 0 <= self.y < self.rows:
                if self.x < self.cols:
                    self.cells[self.y][self.x] = ch
                self.x += 1


@pytest.mark.skipif(os.name == "nt", reason="Windows native key decoding is covered separately; this test needs POSIX PTY")
@pytest.mark.parametrize("stop", ["ctrl-c", "sigterm", "exit"])
def test_real_terminal_menu_commands_logs_clear_resize_and_shutdown(tmp_path, stop):
    import fcntl
    import pty
    import select
    import struct
    import termios

    # Never replace a real service to run a test.
    with socket.socket() as probe:
        try:
            probe.bind(("0.0.0.0", 8000))
        except OSError:
            pytest.skip("port 8000 is already in use; leave that listener untouched")
    master, slave = pty.openpty()
    old_mode = termios.tcgetattr(slave)
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 30, 110, 0, 0))
    vt = VT(110, 30)
    env = {**os.environ, "PYTHONUNBUFFERED": "1", "IMPRESS_DATABASE_URL": f"sqlite+aiosqlite:///{tmp_path}/ui.db",
           "IMPRESS_DEFAULT_SUPERADMIN_PASSWORD": "Terminal-Test-Root-19!", "IMPRESS_JWT_SECRET": "terminal-test-secret",
           "IMPRESS_DEVICE_API_KEY": "terminal-device-key", "IMPRESS_TEMP_BACKUP_DIR": str(tmp_path / "backups"),
           "IMPRESS_FIRMWARE_DIR": str(tmp_path / "fw"), "IMPRESS_MIN_CORES": "1", "IMPRESS_MIN_MEMORY_MB": "1",
           "IMPRESS_MIN_DISK_MB": "1", "IMPRESS_GPC": "", "IMPRESS_REQUIRE_HTTPS": "false"}
    for name in ("IMPRESS_PLAIN", "IMPRESS_ROOT_SCREEN"):
        env.pop(name, None)
    proc = subprocess.Popen([sys.executable, "-m", "app.serve", "--rehash", "--no-ota", "--no-test-mode"],
                            cwd=Path(__file__).resolve().parents[1], env=env, stdin=slave, stdout=slave, stderr=slave,
                            start_new_session=True)

    def until(expected, timeout=25):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if expected(vt.text):
                return vt.text
            if select.select([master], [], [], 0.1)[0]:
                vt.feed(os.read(master, 65536))
            if proc.poll() is not None:
                break
        pytest.fail("Terminal state did not arrive:\n" + vt.text)

    def send(text):
        os.write(master, text.encode())

    try:
        until(lambda s: "● running" in s and "ACTIONS" in s)
        send("\x1b[B\r")                       # menu: Accounts
        until(lambda s: "USERNAME" in s and "impress.default.superAdmin" in s)
        assert "Accounts" in vt.text.splitlines()[4][:25]
        send("versioz\x7fn\r")               # edit in command box while logs are live
        until(lambda s: "> version" in s and "2.2.0" in s)
        send("status\r")
        until(lambda s: "ota" in s and "off" in s and "active super admins" in s)
        send("frobnicate\r")
        until(lambda s: "unknown command: frobnicate" in s)
        send("clear\r")
        until(lambda s: "Waiting for server output..." in s and "frobnicate" not in s)
        send("help\r")
        until(lambda s: "api routes" in s)
        send("\x1b[5~")                        # actual Page Up key
        until(lambda s: "scrollback" in s)
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 12, 48, 0, 0))
        vt.resize(48, 12)
        until(lambda s: "root>" in s and "ACTIONS" in s)
        if stop == "sigterm":
            proc.terminate()
        else:
            send("\x03" if stop == "ctrl-c" else "exit\r")
        deadline = time.monotonic() + 20
        while proc.poll() is None and time.monotonic() < deadline:
            # A terminal keeps consuming output during shutdown. Waiting on the
            # process without reading the PTY can itself fill its output buffer.
            if select.select([master], [], [], 0.1)[0]:
                vt.feed(os.read(master, 65536))
        assert proc.poll() == 0
        while select.select([master], [], [], 0.1)[0]:
            data = os.read(master, 65536)
            if not data:
                break
            vt.feed(data)
        restored = termios.tcgetattr(slave)
        # macOS sets PENDIN while restoring canonical input; this is a kernel
        # request to retype pending input, not an unrestored raw-mode setting.
        pendin = getattr(termios, "PENDIN", 0)
        assert restored[3] & ~pendin == old_mode[3] & ~pendin
        restored[3] = old_mode[3]
        assert restored == old_mode
    finally:
        if proc.poll() is None:
            os.killpg(proc.pid, signal.SIGTERM)
            try:
                proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
        os.close(master)
        os.close(slave)
