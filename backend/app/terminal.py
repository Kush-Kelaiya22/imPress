"""Terminal ownership and key decoding for the root screen (no third-party UI dependency)."""

from __future__ import annotations

import codecs
import os
import signal
import sys
import time

ESC = "\033"
KEYS = {
    "\x1b[A": "UP", "\x1b[B": "DOWN", "\x1b[C": "RIGHT", "\x1b[D": "LEFT",
    "\x1bOA": "UP", "\x1bOB": "DOWN", "\x1bOC": "RIGHT", "\x1bOD": "LEFT",
    "\x1b[H": "HOME", "\x1b[F": "END", "\x1bOH": "HOME", "\x1bOF": "END",
    "\x1b[1~": "HOME", "\x1b[4~": "END", "\x1b[7~": "HOME", "\x1b[8~": "END",
    "\x1b[3~": "DELETE", "\x1b[5~": "PAGEUP", "\x1b[6~": "PAGEDOWN", "\x1b[Z": "BACKTAB",
}
# Scroll the log pane whichever pane has the focus: Shift, Alt or Ctrl with Up/Down, Ctrl+Home/End, and Option+Up/Down
# on terminals that send Escape first. (xterm sends 2 = Shift, 3 = Alt, 5 = Ctrl, 4/6/7/8 = combinations.)
for _mod in "2345678":
    KEYS[f"\x1b[1;{_mod}A"], KEYS[f"\x1b[1;{_mod}B"] = "SCROLL_UP", "SCROLL_DOWN"
    KEYS[f"\x1b[1;{_mod}H"], KEYS[f"\x1b[1;{_mod}F"] = "LOG_TOP", "LOG_LIVE"
    KEYS[f"\x1b[5;{_mod}~"], KEYS[f"\x1b[6;{_mod}~"] = "SCROLL_UP", "SCROLL_DOWN"
KEYS["\x1b\x1b[A"], KEYS["\x1b\x1b[B"] = "SCROLL_UP", "SCROLL_DOWN"
CONTROLS = {"\r": "ENTER", "\n": "ENTER", "\t": "TAB", "\x7f": "BACKSPACE", "\b": "BACKSPACE",
            "\x03": "INTERRUPT", "\x04": "EOF", "\x01": "HOME", "\x05": "END", "\x0c": "REDRAW",
            "\x15": "KILL_START", "\x0b": "KILL_END", "\x17": "KILL_WORD"}


class KeyDecoder:
    """Decode fragmented escape sequences; pasted newlines never execute commands."""

    def __init__(self):
        self.pending = ""
        self.pasting = False
        self.paste = ""

    def feed(self, text: str, flush_escape: bool = False) -> list[str]:
        self.pending += text
        out = []
        while self.pending:
            if self.pasting:
                end = self.pending.find(ESC + "[201~")
                if end < 0:
                    # Keep a possible split end marker for the next read.
                    keep = min(len(self.pending), len(ESC + "[201~") - 1)
                    self.paste += self.pending[:-keep] if keep else self.pending
                    self.pending = self.pending[-keep:] if keep else ""
                    break
                self.paste += self.pending[:end]
                clean = "".join(ch if ch.isprintable() else " " for ch in self.paste)
                out.append("PASTE:" + clean)
                self.pending = self.pending[end + len(ESC + "[201~"):]
                self.pasting, self.paste = False, ""
                continue
            if self.pending.startswith(ESC + "[200~"):
                self.pasting = True
                self.pending = self.pending[len(ESC + "[200~"):]
                continue
            if self.pending.startswith(ESC):
                match = next((seq for seq in KEYS if self.pending.startswith(seq)), None)
                if match:
                    out.append(KEYS[match])
                    self.pending = self.pending[len(match):]
                    continue
                candidates = [*KEYS, ESC + "[200~"]
                if any(seq.startswith(self.pending) for seq in candidates) and not flush_escape:
                    break
                if self.pending == ESC:
                    out.append("ESCAPE")
                    self.pending = ""
                    continue
                # Swallow unsupported terminal key sequences instead of putting
                # their bytes into the command field (or executing a newline).
                if self.pending.startswith((ESC + "[", ESC + "O")):
                    end = next((i for i in range(2, len(self.pending)) if "@" <= self.pending[i] <= "~"), None)
                    if end is None and not flush_escape:
                        break
                    self.pending = self.pending[end + 1:] if end is not None else ""
                else:
                    self.pending = self.pending[1:]
                continue
            ch, self.pending = self.pending[0], self.pending[1:]
            if ch in CONTROLS:
                out.append(CONTROLS[ch])
            elif ch.isprintable():
                out.append("TEXT:" + ch)
        return out


class Terminal:
    """Own raw input and the alternate screen, restoring both even after an exception."""

    def __init__(self):
        self.decoder = KeyDecoder()
        self.utf8 = codecs.getincrementaldecoder("utf-8")("replace")
        self.saved = None
        self.saved_signals = {}

    def __enter__(self):
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes
            self.kernel = ctypes.windll.kernel32
            self.kernel.GetStdHandle.restype = wintypes.HANDLE
            self.kernel.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
            self.kernel.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            self.handles = [self.kernel.GetStdHandle(-10), self.kernel.GetStdHandle(-11)]
            self.saved = []
            for handle in self.handles:
                mode = ctypes.c_ulong()
                if not self.kernel.GetConsoleMode(handle, ctypes.byref(mode)):
                    raise OSError("Use a Windows Terminal or a console with interactive input")
                self.saved.append(mode.value)
            if not self.kernel.SetConsoleMode(self.handles[1], self.saved[1] | 0x0004):
                raise OSError("This terminal does not support ANSI screen rendering")
            self.kernel.SetConsoleMode(self.handles[0], (self.saved[0] | 0x0080) & ~(0x0001 | 0x0002 | 0x0004 | 0x0040))
        else:
            import termios
            import tty
            self.fd = sys.stdin.fileno()
            self.saved = termios.tcgetattr(self.fd)
            tty.setraw(self.fd)
        try:
            sys.stdout.write(ESC + "[?1049h" + ESC + "[?7l" + ESC + "[?2004h" + ESC + "[?25l" + ESC + "[2J" + ESC + "[H")
            sys.stdout.flush()
        except BaseException:
            self.__exit__(None, None, None)
            raise
        def interrupt(_signum, _frame):
            raise KeyboardInterrupt
        for name in ("SIGTERM", "SIGHUP"):
            if hasattr(signal, name):
                sig = getattr(signal, name)
                self.saved_signals[sig] = signal.getsignal(sig)
                signal.signal(sig, interrupt)
        return self

    def read(self, timeout: float = 0.05) -> list[str]:
        if os.name == "nt":
            import msvcrt
            until = time.monotonic() + timeout
            while not msvcrt.kbhit():
                if time.monotonic() >= until:
                    return self.decoder.feed("", flush_escape=True)
                time.sleep(0.01)
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):
                return [{"H": "UP", "P": "DOWN", "M": "RIGHT", "K": "LEFT", "G": "HOME", "O": "END",
                         "S": "DELETE", "I": "PAGEUP", "Q": "PAGEDOWN", "\x0f": "BACKTAB",
                         "\x8d": "SCROLL_UP", "\x91": "SCROLL_DOWN", "w": "LOG_TOP", "u": "LOG_LIVE"}.get(msvcrt.getwch(), "IGNORE")]
            return self.decoder.feed(ch)
        import select
        ready, _, _ = select.select([self.fd], [], [], timeout)
        if not ready:
            return self.decoder.feed("", flush_escape=True)
        raw = os.read(self.fd, 4096)
        if not raw:
            return ["EOF"]
        return self.decoder.feed(self.utf8.decode(raw))

    def __exit__(self, *_exc):
        try:
            sys.stdout.write(ESC + "[0m" + ESC + "[r" + ESC + "[?2004l" + ESC + "[?7h" + ESC + "[?25h" + ESC + "[?1049l")
            sys.stdout.flush()
        finally:
            for sig, handler in self.saved_signals.items():
                signal.signal(sig, handler)
            if self.saved is not None:
                if os.name == "nt":
                    for handle, mode in zip(self.handles, self.saved):
                        self.kernel.SetConsoleMode(handle, mode)
                else:
                    import termios
                    termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)
