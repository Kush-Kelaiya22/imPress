"""Authorization policy: the one place that decides who may do what (#122).

Every REST route and the WebSocket gate ask this module; no other module
compares roles. The model (docs/design/authorization.md):

    Ring −2  TrustedInstaller  firmware verification service, not a login (#123)
    Ring −1  Root              the integrity rules below; vetoes, grants nothing
    Ring  0  super_admin
    Ring  1  admin
    Ring  2  teacher (faculty) assigned classes only
    Ring  3  student           no accounts: device-mediated identity (#124)
    Ring 4+  unauthenticated   a state, never a stored role

A role holds exactly the permissions listed for it in GRANTS. Rings describe
authority, they do not make a lower ring number inherit everything: Root and
TrustedInstaller hold no user-facing permission at all.

Decision order: authenticated → active → permission granted to the role →
resource scope (ownership, assignment) → Root integrity rules. Anything not
granted is denied.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException

from .auth import get_current_user
from .models import ClassSession, User

RING = {"super_admin": 0, "admin": 1, "teacher": 2}

# ── Permission catalogue ─────────────────────────────────────────────────
FACULTY = frozenset({
    "classes.read",          # classes they are assigned to (scope: class_access)
    "classes.manage",        # activate, deactivate, delete assigned classes (scope rules per route)
    "classes.create",        # create a class they then own
    "classes.join",          # join a class as co-faculty with its code
    "assessments.manage",    # quizzes and polls of their classes
    "participation.read",    # results and participation of their classes
    "students.read",
    "students.manage",       # register, edit and enrol students (roster scope: roster_access)
    "courses.read",
})
ADMINISTRATION = frozenset({
    "classes.manage_all",    # every class: create for others, assign faculty, import, delete
    "courses.manage",
    "students.delete",
    "users.read",
    "users.manage",          # create, edit, deactivate, reactivate, reset password, delete
    "devices.read",          # every device and module (teachers see their classes' live tree via classes.read)
    "devices.manage",        # access, keys, links, verification
    "firmware.read",
    "firmware.manage",       # upload, edit, deprecate, delete images
    "firmware.approve",
    "firmware.deploy",       # start, pause, resume, cancel deployments and single pushes
    "audit.read",
})
SUPER = frozenset({
    "users.assign_role",     # grant or remove any role
    "users.manage_privileged",  # manage admin and super admin accounts' credentials
})

GRANTS: dict[str, frozenset[str]] = {
    "teacher": FACULTY,
    "admin": FACULTY | ADMINISTRATION,
    "super_admin": FACULTY | ADMINISTRATION | SUPER,
}
PERMISSIONS = FACULTY | ADMINISTRATION | SUPER
ASSIGNABLE_ROLES = tuple(GRANTS)          # Root and TrustedInstaller are never roles


def forbidden(code: str, message: str) -> HTTPException:
    return HTTPException(403, {"code": code, "message": message})


def allowed(user: User | None, permission: str) -> bool:
    """Does `user`'s role grant `permission`? Default deny, inactive denied."""
    assert permission in PERMISSIONS, f"unknown permission {permission!r}"
    return bool(user is not None and user.is_active and permission in GRANTS.get(user.role, ()))


def require(permission: str):
    """Route dependency: the authenticated user must hold `permission`."""
    assert permission in PERMISSIONS, f"unknown permission {permission!r}"

    async def dependency(user: User = Depends(get_current_user)) -> User:
        if not allowed(user, permission):
            raise forbidden("FORBIDDEN", f"Not allowed: {permission}")
        return user
    dependency.permission = permission            # read by test_policy.py
    return dependency


# ── Resource scope ───────────────────────────────────────────────────────

def class_access(user: User, cls: ClassSession) -> bool:
    """Work with a class: its primary teacher, any co-faculty member, or an
    administrator. One rule for classes, quizzes, polls, results and the
    class WebSocket (#20, #21, #121)."""
    if allowed(user, "classes.manage_all"):
        return True
    return allowed(user, "classes.read") and (
        cls.teacher_id == user.id or any(f.id == user.id for f in (cls.faculty or [])))


def roster_access(user: User, cls: ClassSession) -> bool:
    """Enrol or remove students, list a class roster: the primary teacher or
    an administrator. (Co-faculty are not included today; see #146.)"""
    return allowed(user, "classes.manage_all") or (allowed(user, "students.manage") and cls.teacher_id == user.id)


def class_owner_or_admin(user: User, cls: ClassSession) -> bool:
    """Delete a class: its primary teacher or an administrator."""
    return allowed(user, "classes.manage_all") or cls.teacher_id == user.id


def sees_all_classes(user: User) -> bool:
    return allowed(user, "classes.manage_all")


# ── Root: integrity rules that override every grant ──────────────────────

def can_grant(actor: User, role: str) -> bool:
    """Granting or taking away an administrative role needs users.assign_role."""
    return RING.get(role, 99) > RING["admin"] or allowed(actor, "users.assign_role")


def account_refusal(actor: User, target: User, action: str) -> HTTPException | None:
    """Why `actor` may not do `action` to `target`'s account, or None.

    Actions: edit, deactivate, reactivate, change_role, reset_password, delete.
    The last-active-super-admin rule is enforced by the database itself
    (migration 9, #116) so that concurrent requests cannot bypass it."""
    if not allowed(actor, "users.manage"):
        return forbidden("FORBIDDEN", "Not allowed: users.manage")
    if RING.get(target.role, 99) == 0 and not allowed(actor, "users.manage_privileged"):
        return forbidden("FORBIDDEN_TARGET", "Only a super admin can manage a super admin")
    if actor.id == target.id and action in ("deactivate", "delete", "change_role"):
        verb = {"deactivate": "deactivate", "delete": "delete", "change_role": "change the role of"}[action]
        return forbidden("SELF_LOCKOUT", f"You cannot {verb} your own account")
    if action == "change_role" and not allowed(actor, "users.assign_role"):
        return forbidden("FORBIDDEN_ROLE", "Only a super admin can change roles")
    return None


def is_staff(user: User | None) -> bool:
    """A logged-in, active member of staff (any assignable role)."""
    return bool(user is not None and user.is_active and user.role in GRANTS)
