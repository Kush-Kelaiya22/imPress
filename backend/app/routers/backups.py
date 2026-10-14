"""Backups of the database and the system state (v2.2): see, save and restore (administrators and above)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .. import gpc
from ..activity import log_activity
from ..database import get_db
from ..models import User
from ..policy import require
from ..services import approvals, backups

router = APIRouter(prefix="/api/admin/backups", tags=["backups"])
ADMIN = require("users.manage")


def _err(e: backups.BackupError) -> HTTPException:
    return HTTPException(e.status, {"code": e.code, "message": e.message})


class Save(BaseModel):
    name: str = Field(min_length=1, max_length=48)
    note: str = Field(default="", max_length=200)


class Restore(BaseModel):
    password: str
    confirm: str                       # the backup's name, typed
    approval_id: int | None = None


@router.get("")
async def list_backups(user: User = Depends(ADMIN)):
    return {"restore_needs_approval": gpc.get("backups.restore_requires_approval"), "state": backups.system_state(),
            "backups": backups.listing()}


@router.post("", status_code=201)
async def save_backup(body: Save, user: User = Depends(ADMIN), db: AsyncSession = Depends(get_db)):
    try:
        entry = await backups.save(body.name, user.username, body.note)
    except backups.BackupError as e:
        raise _err(e) from None
    await log_activity(db, "backup.save", user.id, "system", None, {"flag": True, "name": entry["name"]})
    await db.commit()
    return entry


@router.get("/{kind}/{name}")
async def describe_backup(kind: str, name: str, user: User = Depends(ADMIN)):
    try:
        return backups.describe(f"{kind}/{name}")
    except backups.BackupError as e:
        raise _err(e) from None


@router.post("/{kind}/{name}/restore")
async def restore_backup(kind: str, name: str, body: Restore, user: User = Depends(ADMIN), db: AsyncSession = Depends(get_db)):
    try:
        entry = backups.describe(f"{kind}/{name}")
    except backups.BackupError as e:
        raise _err(e) from None
    if body.confirm.strip() != entry["name"]:
        raise HTTPException(422, {"code": "CONFIRM", "message": f"Type {entry['name']} to confirm"})
    await approvals.step_up(db, user, body.password)
    if gpc.get("backups.restore_requires_approval"):
        await approvals.require(db, user, "backups.restore", {"backup": entry["id"]}, body.approval_id)
    await log_activity(db, "backup.restore", user.id, "system", None, {"flag": True, "backup": entry["id"]})
    await db.commit()
    try:
        return await backups.restore(entry["id"], user.username)
    except backups.BackupError as e:
        raise _err(e) from None


@router.delete("/{kind}/{name}", status_code=204)
async def delete_backup(kind: str, name: str, user: User = Depends(ADMIN), db: AsyncSession = Depends(get_db)):
    try:
        backups.delete(f"{kind}/{name}")
    except backups.BackupError as e:
        raise _err(e) from None
    await log_activity(db, "backup.delete", user.id, "system", None, {"flag": True, "backup": f"{kind}/{name}"})
    await db.commit()
