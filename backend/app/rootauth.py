"""Root's password for sensitive actions (v2.2).

Root is not an application account, so the actions that can redefine or erase what the system trusts (re-hashing the program's
files, changing policy, resetting, flashing, creating a super admin, ...) ask for a password at the keyboard, in the console, on
the root screen, and for `--rehash` at start-up. Only its **SHA-512** is kept (`DEFAULT_SHA512`); a site sets its own with
`IMPRESS_ROOT_PASSWORD_SHA512` (the hex digest of the password it chose). The check is constant-time and failures slow down:
three wrong tries in a row wait 2, 4, 8 ... up to 30 seconds before the next one is looked at.

Honest limits: the shipped hash belongs to a password shared by every installation that has not set its own, so treat it as a
speed bump against the person who happens to be at an unlocked terminal, not as a secret. Set your own for any real server
(docs/guides/production-hardening.md). A fast hash is acceptable for a password that is long and random; it is not for a human-
chosen one, so choose a long random one.
"""

from __future__ import annotations

import getpass
import hashlib
import hmac
import os
import re
import sys
import time

DEFAULT_SHA512 = ("eb92829ebc50d1e1dfb8af978911f65b734aa2536f8c17133850fd69038be6ff"
                  "e5883e5338283a13a958c18a7c48646bef7c64c6f195f9fcfaff59bc2643d1c3")

# Console commands that need it: (first word, a test on the rest of the line). Reading is never sensitive.
_SENSITIVE = (
    ("policy", re.compile(r"^(set|reset)\b")),
    ("iips", re.compile(r"^rehash\b")),
    ("system", re.compile(r"^reset\b")),
    ("password", re.compile(r"^reset\b")),
    ("superadmin", re.compile(r"^create\b")),
    ("mfa", re.compile(r"^reset\b")),
    ("backup", re.compile(r"^restore\b")),
    ("flags", re.compile(r"^reset\b.*--file")),
    ("flash", re.compile(r".*")),
    ("sessions", re.compile(r"^end\s+--all\b")),
    ("users", re.compile(r"^set-password\b")),
    ("restart", re.compile(r".*--rehash")),
    ("api", re.compile(r"^(?!get\b)\w+", re.I)),
)
_failures = {"n": 0, "until": 0.0}


class RootAuthError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def expected() -> str:
    return (os.environ.get("IMPRESS_ROOT_PASSWORD_SHA512") or DEFAULT_SHA512).strip().lower()


def check(password: str | None) -> bool:
    """Is `password` root's? Constant-time; wrong tries slow the next one down."""
    wait = _failures["until"] - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    ok = bool(password) and hmac.compare_digest(hashlib.sha512(password.encode()).hexdigest(), expected())
    if ok:
        _failures.update(n=0, until=0.0)
    else:
        _failures["n"] += 1
        if _failures["n"] >= 3:
            _failures["until"] = time.monotonic() + min(30, 2 ** (_failures["n"] - 2))
    return ok


def is_sensitive(command: str) -> bool:
    parts = command.strip().split(None, 1)
    if not parts:
        return False
    rest = parts[1] if len(parts) > 1 else ""
    return any(parts[0] == name and rx.search(rest) for name, rx in _SENSITIVE)


def obtain(prompt: str = "Root's password: ", given: str | None = None) -> str | None:
    """The password from the caller, the environment (IMPRESS_ROOT_PASSWORD, for scripts) or the keyboard."""
    if given:
        return given
    if os.environ.get("IMPRESS_ROOT_PASSWORD"):
        return os.environ["IMPRESS_ROOT_PASSWORD"]
    if sys.stdin.isatty():
        try:
            return getpass.getpass(prompt)
        except (EOFError, KeyboardInterrupt):
            return None
    return None


def require(what: str, given: str | None = None) -> None:
    """Raise RootAuthError unless root's password is given (or typed) and right."""
    password = obtain(f"Root's password to {what}: ", given)
    if not password:
        raise RootAuthError("ROOT_PASSWORD_REQUIRED", f"Root's password is needed to {what}. "
                            "Type it when asked (or set IMPRESS_ROOT_PASSWORD for a script).")
    if not check(password):
        raise RootAuthError("ROOT_PASSWORD_WRONG", "Root's password is not correct.")
