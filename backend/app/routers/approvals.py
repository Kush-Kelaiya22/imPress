"""Dual-control requests (super admins only): see services/approvals.py."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..policy import require
from ..services import approvals

router = APIRouter(prefix="/api/admin/approvals", tags=["approvals"])
SUPER = require("users.assign_role")


class NewRequest(BaseModel):
    action: str
    params: dict = {}
    password: str


class Password(BaseModel):
    password: str


@router.get("")
async def list_requests(user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    return {"actions": approvals.ACTIONS, "requests": await approvals.listing(db)}


@router.post("", status_code=201)
async def request_action(body: NewRequest, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    a = await approvals.create(db, user, body.action, body.params, body.password)
    return {"id": a.id, "status": a.status}


@router.post("/{approval_id}/approve")
async def approve(approval_id: int, body: Password, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    a = await approvals.approve(db, user, approval_id, body.password)
    return {"id": a.id, "status": a.status, "not_before": a.not_before, "expires_at": a.expires_at}


@router.post("/{approval_id}/deny")
async def deny(approval_id: int, user: User = Depends(SUPER), db: AsyncSession = Depends(get_db)):
    a = await approvals.deny(db, user, approval_id)
    return {"id": a.id, "status": a.status}
