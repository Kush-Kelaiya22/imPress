"""The authorization policy is the one place that decides access (#122)."""

import importlib
import re
from pathlib import Path

from fastapi.routing import APIRoute

from conftest import auth, login, make_user
from test_route_guards import PUBLIC, ROUTERS

APP = Path(__file__).resolve().parents[1] / "app"

# Routes a logged-in user calls about their own session; any staff role may.
SELF_SERVICE = {"/api/auth/me", "/api/auth/change-password", "/api/auth/logout",
                "/api/auth/session", "/api/auth/session-status", "/api/auth/activity",
                "/api/events",          # the signed-in user's own live-update stream (v2.2)
                "/api/auth/preferences", "/api/auth/onboarding"}    # their own settings and welcome (v2.2)


def _routes():
    for name in ROUTERS:
        mod = importlib.import_module(f"app.routers.{name}")
        for router in (mod.router, getattr(mod, "live_router", None)):
            for r in getattr(router, "routes", []):
                if isinstance(r, APIRoute):
                    yield r


def _calls(dependant):
    for d in dependant.dependencies:
        yield d.call
        yield from _calls(d)


def test_every_route_is_governed_by_the_policy_or_listed():
    """A staff route without a policy permission is a new hole; device routes
    authenticate the device key; the rest are explicitly listed."""
    unexplained = []
    for r in _routes():
        calls = list(_calls(r.dependant))
        if any(getattr(c, "permission", None) for c in calls):
            continue
        if any(getattr(c, "__name__", "") == "device_caller" for c in calls):
            continue
        if r.path in SELF_SERVICE or any((m, r.path) in PUBLIC for m in r.methods):
            continue
        unexplained.append(f"{sorted(r.methods)} {r.path}")
    assert unexplained == []


def test_no_role_comparisons_outside_the_policy():
    """Role checks scattered across routers drifted before (#19-#21, #116, #121)."""
    pattern = re.compile(r"\.role\s*(==|!=|\bin\b|\bnot in\b)")
    offenders = []
    for path in APP.rglob("*.py"):
        if path.name == "policy.py":
            continue
        for n, line in enumerate(path.read_text().splitlines(), 1):
            code = line.split("#")[0]
            if pattern.search(code) and "User.role ==" not in code and "body.role == target.role" not in code:
                offenders.append(f"{path.relative_to(APP)}:{n}: {line.strip()}")
    assert offenders == []


def test_grants_are_explicit_and_bounded():
    from app.policy import ADMINISTRATION, FACULTY, GRANTS, PERMISSIONS, SUPER
    assert set(GRANTS) == {"teacher", "admin", "super_admin"}
    assert all(g <= PERMISSIONS for g in GRANTS.values())
    assert not (GRANTS["teacher"] & (ADMINISTRATION | SUPER))       # faculty get no administration
    assert not (GRANTS["admin"] & SUPER)                             # admins can't grant roles
    assert GRANTS["super_admin"] == FACULTY | ADMINISTRATION | SUPER


def test_root_and_trusted_installer_are_not_roles(client):
    su = auth(login(client))
    uid, _ = make_user(client, su, "tch1")
    for role in ("root", "Root", "trusted_installer", "TrustedInstaller", "ti", "system"):
        assert client.post(f"/api/admin/users/{uid}/role", headers=su, json={"role": role}).status_code == 422
        assert client.post("/api/admin/users", headers=su, json={
            "username": f"x{abs(hash(role)) % 10**6}", "email": "x@x.io", "password": "Passw0rd!x",
            "full_name": "x", "role": role}).status_code == 422


def test_inactive_or_unknown_roles_hold_nothing():
    from app.models import User
    from app.policy import PERMISSIONS, allowed
    assert not any(allowed(User(role="super_admin", is_active=False), p) for p in PERMISSIONS)
    assert not any(allowed(User(role="root", is_active=True), p) for p in PERMISSIONS)
    assert not any(allowed(None, p) for p in PERMISSIONS)


def test_published_permission_matrix_matches_the_code():
    """docs/design/authorization.md shows GRANTS; it must not drift."""
    from app.policy import GRANTS, PERMISSIONS
    doc = (APP.parents[1] / "docs/design/authorization.md").read_text()
    for perm in sorted(PERMISSIONS):
        row = next((l for l in doc.splitlines() if l.startswith(f"| `{perm}` |")), None)
        assert row, f"{perm} missing from the matrix"
        cells = [c.strip() for c in row.strip("|").split("|")][1:4]
        assert cells == ["✓" if perm in GRANTS[r] else "–" for r in ("teacher", "admin", "super_admin")], perm
