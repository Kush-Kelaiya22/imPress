"""Second factor for dual control (#211): TOTP (RFC 6238) with single-use recovery codes, standard library only.

A super admin enrols an authenticator app (a secret shown once, as text and as an otpauth:// link), proves it works with
one code, and receives recovery codes (shown once, stored only as hashes). From then on every step of dual control asks
for the password **and** a code. Policy `dual_control.mfa_required` (on in the hardened profile) makes the code mandatory
for everybody: a super admin who has not enrolled cannot request or approve.

A code is accepted once: the newest time step already used is remembered, so a code that was seen cannot be replayed.
A window of one step either side tolerates a clock a few seconds out. Wrong codes count with wrong passwords towards the
step-up lockout (services/approvals.py). Root can remove a lost second factor in the console (`mfa reset USER`).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .. import gpc
from ..activity import log_activity
from ..models import User, UserMfa
from ..timeutil import istnow

STEP, DIGITS, WINDOW, RECOVERY_CODES = 30, 6, 1, 10
ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"            # no 0/O/1/I: recovery codes are read aloud and copied by hand


def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _code(secret: str, counter: int) -> str:
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    mac = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = mac[-1] & 0x0F
    return f"{(struct.unpack('>I', mac[offset:offset + 4])[0] & 0x7FFFFFFF) % 10 ** DIGITS:0{DIGITS}d}"


def totp(secret: str, at: float | None = None) -> str:
    return _code(secret, int((time.time() if at is None else at) // STEP))


def match(secret: str, code: str, last_counter: int, at: float | None = None) -> int | None:
    """The time step `code` belongs to, or None. Only a step newer than `last_counter` counts (no replay)."""
    code = "".join(code.split())
    if len(code) != DIGITS or not code.isdigit():
        return None
    now = int((time.time() if at is None else at) // STEP)
    for counter in range(now - WINDOW, now + WINDOW + 1):
        if counter > last_counter and hmac.compare_digest(_code(secret, counter), code):
            return counter
    return None


def otpauth_uri(username: str, secret: str) -> str:
    return (f"otpauth://totp/imPress:{quote(username)}?secret={secret}&issuer=imPress&algorithm=SHA1"
            f"&digits={DIGITS}&period={STEP}")


def _recovery_hash(code: str) -> str:
    return hashlib.sha256("".join(c for c in code.upper() if c.isalnum()).encode()).hexdigest()


def new_recovery_codes() -> list[str]:
    return ["".join(secrets.choice(ALPHABET) for _ in range(10)) for _ in range(RECOVERY_CODES)]


def _err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status, {"code": code, "message": message})


async def get(db: AsyncSession, user: User) -> UserMfa | None:
    return await db.get(UserMfa, user.id)


async def status(db: AsyncSession, user: User) -> dict:
    row = await get(db, user)
    return {"enrolled": bool(row and row.enabled), "pending": bool(row and not row.enabled),
            "required": bool(gpc.get("dual_control.mfa_required")),
            "recovery_codes_left": len(row.recovery or []) if row and row.enabled else 0}


async def start_enrolment(db: AsyncSession, user: User) -> dict:
    row = await get(db, user)
    if row and row.enabled:
        raise _err(409, "MFA_ENROLLED", "Two-step verification is already on. Turn it off first to set it up again.")
    secret = new_secret()
    if row is None:
        db.add(UserMfa(user_id=user.id, secret=secret, enabled=False, last_counter=-1, recovery=[]))
    else:
        row.secret, row.last_counter = secret, -1
    await db.commit()
    return {"secret": secret, "uri": otpauth_uri(user.username, secret), "digits": DIGITS, "period": STEP}


async def finish_enrolment(db: AsyncSession, user: User, code: str) -> list[str]:
    row = await get(db, user)
    if row is None or row.enabled:
        raise _err(409, "MFA_NOT_PENDING", "Start the set-up first.")
    counter = match(row.secret, code, -1)
    if counter is None:
        raise _err(403, "MFA_CODE_WRONG", "That code is not right. Check the app's clock and try the newest code.")
    codes = new_recovery_codes()
    row.enabled, row.enabled_at, row.last_counter = True, istnow(), counter
    row.recovery = [_recovery_hash(c) for c in codes]
    await log_activity(db, "mfa.enrol", user.id, "user", user.id, {"flag": True})
    await db.commit()
    return [f"{c[:5]}-{c[5:]}" for c in codes]


async def verify(db: AsyncSession, user: User, code: str) -> bool:
    """Check a code from the app, or a recovery code (used up). The caller decides what a False costs."""
    row = await get(db, user)
    if row is None or not row.enabled or not code:
        return False
    counter = match(row.secret, code, row.last_counter)
    if counter is not None:
        row.last_counter = counter
        await db.commit()
        return True
    cleaned = "".join(c for c in code.upper() if c.isalnum())
    wanted = _recovery_hash(cleaned)
    if len(cleaned) == 10 and wanted in (row.recovery or []):
        row.recovery = [h for h in row.recovery if h != wanted]
        await log_activity(db, "mfa.recovery_used", user.id, "user", user.id,
                           {"flag": True, "left": len(row.recovery)})
        await db.commit()
        return True
    return False


async def second_factor_needed(db: AsyncSession, user: User) -> bool:
    """Will a step-up need a code? Yes once enrolled; and enrolment is mandatory when the policy says so."""
    row = await get(db, user)
    return bool(row and row.enabled) or bool(gpc.get("dual_control.mfa_required"))


async def disable(db: AsyncSession, user: User) -> None:
    row = await get(db, user)
    if row is not None:
        await db.delete(row)
        await log_activity(db, "mfa.disable", user.id, "user", user.id, {"flag": True})
        await db.commit()
