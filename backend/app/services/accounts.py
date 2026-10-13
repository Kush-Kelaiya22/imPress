"""Account lifecycle rules shared by every route that changes a user (#116).

The database triggers from migration 9 are the real guard for "at least one
active super admin"; this module turns their abort into a 409 and refuses
changes an administrator makes to their own account that would lock them out.
"""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import revoke_user_sessions
from ..models import User


def error(status: int, code: str, message: str) -> HTTPException:
    """An HTTP error with a machine-readable code: {"detail": {"code", "message"}}."""
    return HTTPException(status, {"code": code, "message": message})


def refuse_self_lockout(actor: User, target: User, *, deactivate=False, delete=False, role=None) -> None:
    """No one can deactivate, delete or change the role of their own account."""
    if actor.id != target.id:
        return
    if deactivate or delete or (role is not None and role != target.role):
        action = "delete" if delete else "deactivate" if deactivate else "change the role of"
        raise error(403, "SELF_LOCKOUT", f"You cannot {action} your own account")


async def revoke(db: AsyncSession, target: User) -> None:
    """End the target's access: revoke their sessions in this transaction, and
    close their WebSockets once `commit(..., revoked=target)` succeeds (#118)."""
    await revoke_user_sessions(db, target.id)


async def commit(db: AsyncSession, revoked: User | None = None) -> None:
    """Commit; a write that would leave no active super admin becomes 409.
    After a successful commit, close the open sockets of `revoked`."""
    revoked_id = revoked.id if revoked is not None else None
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        if "LAST_SUPER_ADMIN" in str(e.orig):
            raise error(409, "LAST_SUPER_ADMIN",
                        "This is the last active super admin; promote or activate another one first") from e
        raise
    if revoked_id is not None:
        from ..ws.manager import manager
        await manager.close_user(revoked_id)
