"""Account lifecycle: shared by every route that changes a user (#116-#119).

Who may do what is decided by policy.account_refusal() (#122). The database
triggers from migration 9 are the real guard for "at least one active super
admin"; commit() turns their abort into a 409.
"""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import revoke_user_sessions
from ..models import User
from ..policy import account_refusal


def error(status: int, code: str, message: str) -> HTTPException:
    """An HTTP error with a machine-readable code: {"detail": {"code", "message"}}."""
    return HTTPException(status, {"code": code, "message": message})


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


# What happens to each reference when a user is deleted (#117). Every foreign
# key to users.id must appear here; test_user_delete.py checks that.
#   "delete":   the row only makes sense with the user (sessions, co-faculty links)
#   "null":     keep the record, forget who did it (provenance)
#   "audit":    keep the activity entry, record the deleted username in details
#   "refuse":   the user still owns something that needs an owner
DELETE_RULES = {
    ("user_sessions", "user_id"): "delete",
    ("class_faculty", "user_id"): "delete",
    ("class_sessions", "teacher_id"): "refuse",
    ("class_sessions", "created_by"): "null",
    ("users", "created_by"): "null",
    ("students", "registered_by"): "null",
    ("student_enrollments", "enrolled_by"): "null",
    ("firmware_artifacts", "uploaded_by"): "null",
    ("firmware_artifacts", "approved_by"): "null",
    ("firmware_deployments", "requested_by"): "null",
    ("activity_logs", "user_id"): "audit",
    ("class_occurrence_exceptions", "created_by"): "null",
}


async def delete_user(db: AsyncSession, target: User) -> None:
    """Permanently delete `target` and settle every reference to it, in the
    caller's transaction. The caller commits with commit(db, revoked=target)."""
    from sqlalchemy import select, text
    from ..models import ClassSession

    owned = (await db.execute(select(ClassSession.id, ClassSession.name)
                              .where(ClassSession.teacher_id == target.id))).all()
    if owned:
        raise error(409, "USER_OWNS_CLASSES",
                    "Assign another primary teacher first: " + ", ".join(f"{n} (#{i})" for i, n in owned))
    uid = {"u": target.id}
    for (table, column), rule in DELETE_RULES.items():
        if rule == "delete":
            await db.execute(text(f"DELETE FROM {table} WHERE {column} = :u"), uid)
        elif rule == "null":
            await db.execute(text(f"UPDATE {table} SET {column} = NULL WHERE {column} = :u"), uid)
        elif rule == "audit":
            await db.execute(text(
                f"UPDATE {table} SET details = json_set(COALESCE(details, '{{}}'), '$.deleted_user', :name), "
                f"{column} = NULL WHERE {column} = :u"), {**uid, "name": target.username})
    # SQL, not db.delete(): the ORM would also try to remove the class_faculty
    # rows through User.taught_classes, which are already gone.
    await db.execute(text("DELETE FROM users WHERE id = :u"), uid)
    db.expunge(target)


# ── Who may do what to an account (#119, #122) ───────────────────────────
# The rule itself is policy.account_refusal(); the routes enforce it and
# GET /api/admin/users returns allowed_actions from it, so the web app shows
# exactly the buttons the server will accept.

ACTIONS = ("edit", "deactivate", "reactivate", "change_role", "reset_password", "delete")


def check(actor: User, target: User, action: str) -> None:
    """Raise 403 unless `actor` may do `action` to `target`."""
    refusal = account_refusal(actor, target, action)
    if refusal is not None:
        raise refusal


def allowed_actions(actor: User, target: User) -> list[str]:
    """The actions `check` would allow, minus the ones that make no sense now."""
    return [a for a in ACTIONS
            if not (a == "deactivate" and not target.is_active) and not (a == "reactivate" and target.is_active)
            and account_refusal(actor, target, a) is None]
