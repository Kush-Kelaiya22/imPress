"""Two-step verification for super admins (#211): set up, turn off, recovery codes. See services/mfa.py."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from .. import gpc
from ..database import get_db
from ..models import User
from ..policy import require
from ..services import approvals, mfa

router = APIRouter(prefix="/api/auth/mfa", tags=["auth"])
SUPER = require("users.assign_role")            # the dual-control accounts


class Password(BaseModel):
    password: str


class Code(BaseModel):
    code: str


class PasswordCode(BaseModel):
    password: str
    code: str


@router.get("")
async def mfa_status(user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    return await mfa.status(db, user)


@router.post("/setup")
async def setup(body: Password, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    """Start the set-up: a new secret, shown once as text and as an otpauth:// link for a QR code."""
    await approvals.check_password(db, user, body.password)
    return await mfa.start_enrolment(db, user)


@router.post("/enable")
async def enable(body: Code, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    """Prove the app works with its first code. Returns the recovery codes: this is the only time they are shown."""
    return {"recovery_codes": await mfa.finish_enrolment(db, user, body.code)}


@router.post("/disable")
async def disable(body: PasswordCode, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    if gpc.get("dual_control.mfa_required"):
        raise HTTPException(403, {"code": "MFA_REQUIRED_BY_POLICY",
                                  "message": "Two-step verification is required by policy (dual_control.mfa_required) and cannot be turned off here."})
    await approvals.step_up(db, user, body.password, body.code)
    await mfa.disable(db, user)
    return {"enrolled": False}


@router.post("/recovery-codes")
async def new_recovery_codes(body: PasswordCode, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    """Replace the recovery codes (the old ones stop working)."""
    await approvals.step_up(db, user, body.password, body.code)
    row = await mfa.get(db, user)
    codes = mfa.new_recovery_codes()
    row.recovery = [mfa._recovery_hash(c) for c in codes]
    await db.commit()
    return {"recovery_codes": [f"{c[:5]}-{c[5:]}" for c in codes]}
