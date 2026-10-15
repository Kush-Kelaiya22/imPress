"""v2.2 accounts: display names, TA, the password rule, temporary credentials, the default super admin, the trash,
role changes, preferences and onboarding, session limits."""


import json

import pytest

from conftest import PASSWORD, auth, login, make_class, make_student, make_user
from app import passwords

DEFAULT = "impress.default.superAdmin"


def _new(client, su, username="newbie", role="teacher", **extra):
    body = {"username": username, "email": f"{username}@example.edu", "full_name": username.title(), "role": role,
            "keep_pending": True, **extra}
    return client.post("/api/admin/users", headers=su, json=body)


# ── the password rule ───────────────────────────────────────────────────

@pytest.mark.parametrize("pw,role,why", [
    ("Short1!", "teacher", "at least 8"), ("alllowercase1!", "teacher", "upper-case"), ("ALLUPPER1!", "admin", "lower-case"),
    ("NoNumbers!!", "teacher", "number"), ("NoSpecial123", "admin", "special"), ("password", "teacher", "common"),
    ("short", "super_admin", "at least 10"), ("onlylowercase", "super_admin", None),     # a super admin keeps the longer rule only
])
def test_the_password_rule_per_role(pw, role, why):
    got = passwords.problem(pw, "someone", role)
    assert (got is None) if why is None else (why in got), got


def test_generated_passwords_always_pass_and_differ():
    seen = {passwords.generate() for _ in range(50)}
    assert len(seen) == 50
    for pw in seen:
        assert len(pw) >= 12 and passwords.problem(pw, "x", "teacher") is None
        assert any(c.islower() for c in pw) and any(c.isupper() for c in pw) and any(c.isdigit() for c in pw) and any(not c.isalnum() for c in pw)


def test_the_strength_meter_scores():
    s = passwords.strength
    assert s("")["score"] == 0 and s("password")["score"] == 0 and s("abc")["score"] == 0
    assert s("Passw0rd!")["label"] == "Fair" and s("Tr0ub4dor&3xyz!")["label"] == "Good" and s("Tr0ub4dor&3-horse-staple")["label"] == "Strong"
    assert s("abcdefgh1")["missing"] == ["an upper-case letter", "a special character"]


# ── creating accounts, temporary credentials, first sign-in ─────────────

def test_a_new_account_gets_a_generated_password_that_must_be_changed(client):
    su = auth(login(client))
    r = _new(client, su, "gen1")
    assert r.status_code == 201
    body = r.json()
    temp = body["temporary_password"]
    assert passwords.problem(temp, "gen1", "teacher") is None
    assert body["status"] == "pending_setup" and body["must_change_password"] is True
    # it shown once: listing never carries it
    assert all("temporary_password" not in u or u["temporary_password"] is None for u in client.get("/api/admin/users", headers=su).json())
    token = client.post("/api/auth/login", json={"username": "gen1", "password": temp}).json()
    assert token["must_change_password"] is True
    h = auth(token["access_token"])
    # nothing but setting itself up
    r = client.get("/api/classes/", headers=h)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "PASSWORD_CHANGE_REQUIRED"
    assert client.get("/api/auth/me", headers=h).json()["status"] == "pending_setup"
    assert client.get("/api/events", headers=h).status_code == 403
    # weak and same-as-before are refused; a good new password finishes the setup
    assert client.post("/api/auth/change-password", headers=h, json={"current_password": temp, "new_password": "weak"}).status_code == 422
    assert client.post("/api/auth/change-password", headers=h, json={"current_password": temp, "new_password": temp}).status_code == 422
    assert client.post("/api/auth/change-password", headers=h, json={"current_password": temp, "new_password": "My-Own-Pass9"}).status_code == 200
    h2 = auth(client.post("/api/auth/login", json={"username": "gen1", "password": "My-Own-Pass9"}).json()["access_token"])
    assert client.get("/api/classes/", headers=h2).status_code == 200
    assert client.get("/api/auth/me", headers=h2).json()["status"] == "active"


def test_a_typed_password_is_also_temporary_and_must_follow_the_rule(client):
    su = auth(login(client))
    assert _new(client, su, "typed1", password="weakpass").status_code == 422
    r = _new(client, su, "typed2", password="Typed-Pass1")
    assert r.status_code == 201 and r.json()["temporary_password"] is None and r.json()["must_change_password"] is True


def test_resetting_a_password_makes_it_temporary_again(client):
    su = auth(login(client))
    uid, th = make_user(client, su, "reset1")
    assert client.get("/api/classes/", headers=th).status_code == 200
    r = client.post(f"/api/admin/users/{uid}/reset-password", headers=su, json={})
    assert r.status_code == 200 and passwords.problem(r.json()["temporary_password"], "reset1", "teacher") is None
    assert client.get("/api/classes/", headers=th).status_code == 401                       # signed out everywhere
    token = client.post("/api/auth/login", json={"username": "reset1", "password": r.json()["temporary_password"]}).json()
    assert token["must_change_password"] is True


def test_super_admins_cannot_be_made_through_the_api(client):
    su = auth(login(client))
    r = _new(client, su, "sneaky", role="super_admin")
    assert r.status_code == 403 and r.json()["detail"]["code"] == "SUPER_ADMIN_VIA_CONSOLE"
    uid, _ = make_user(client, su, "tch1")
    r = client.post(f"/api/admin/users/{uid}/role", headers=su, json={"role": "super_admin"})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "SUPER_ADMIN_VIA_CONSOLE"


# ── names, designation, role changes ────────────────────────────────────

def test_display_names_and_the_ta_designation(client):
    su = auth(login(client))
    r = _new(client, su, "ta1", display_name="Anna the TA", designation="ta")
    assert r.json()["name"] == "Anna the TA" and r.json()["designation"] == "ta"
    uid = r.json()["id"]
    assert client.post(f"/api/admin/users/{uid}/designation", headers=su, json={"designation": "faculty"}).json()["designation"] == "faculty"
    admin_id, _ = make_user(client, su, "adm9", role="admin")
    assert client.post(f"/api/admin/users/{admin_id}/designation", headers=su, json={"designation": "ta"}).status_code == 422   # only faculty
    _, teacher = make_user(client, su, "tch2")
    assert client.post(f"/api/admin/users/{uid}/designation", headers=teacher, json={"designation": "ta"}).status_code == 403


def test_a_ta_has_exactly_a_teachers_permissions(client):
    su = auth(login(client))
    _, ta = make_user(client, su, "ta2")
    uid = next(u["id"] for u in client.get("/api/admin/users", headers=su).json() if u["username"] == "ta2")
    client.post(f"/api/admin/users/{uid}/designation", headers=su, json={"designation": "ta"})
    cid = make_class(client, su, name="TA class", code="TA101", teacher_id=uid)
    assert client.get(f"/api/classes/{cid}", headers=ta).status_code == 200
    assert client.get("/api/admin/users", headers=ta).status_code == 403
    assert client.get("/api/auth/me", headers=ta).json()["designation"] == "ta"


def test_faculty_and_admin_swap_by_a_super_admin_only(client):
    su = auth(login(client))
    uid, th = make_user(client, su, "swap1")
    _, adm = make_user(client, su, "adm2", role="admin")
    assert client.post(f"/api/admin/users/{uid}/role", headers=adm, json={"role": "admin"}).status_code == 403
    assert client.post(f"/api/admin/users/{uid}/role", headers=su, json={"role": "admin"}).json()["role"] == "admin"
    assert client.post(f"/api/admin/users/{uid}/role", headers=su, json={"role": "teacher"}).json()["role"] == "teacher"


# ── the default super admin ─────────────────────────────────────────────

def test_the_default_super_admin_is_new_every_start_unless_root_fixes_it(client, monkeypatch):
    import asyncio

    from app.config import settings
    from app.services import bootstrap
    monkeypatch.setattr(settings, "DEFAULT_SUPERADMIN_PASSWORD", "")
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "")
    first = client.portal.call(bootstrap.ensure_default_superadmin, True)
    second = client.portal.call(bootstrap.ensure_default_superadmin, True)
    assert first != second and len(first) >= 20 and passwords.problem(first, DEFAULT, "super_admin") is None
    assert client.post("/api/auth/login", json={"username": DEFAULT, "password": first}).status_code == 401
    token = client.post("/api/auth/login", json={"username": DEFAULT, "password": second}).json()
    assert token["must_change_password"] is False                                            # never forced through a change
    monkeypatch.setattr(settings, "DEFAULT_SUPERADMIN_PASSWORD", "Fixed-By-Root-1")
    assert client.portal.call(bootstrap.ensure_default_superadmin, True) == "Fixed-By-Root-1"
    assert client.post("/api/auth/login", json={"username": DEFAULT, "password": "Fixed-By-Root-1"}).status_code in (200, 409)
    assert asyncio.get_event_loop_policy() is not None


def test_the_new_password_signs_out_the_old_sessions(client, monkeypatch):
    from app.config import settings
    from app.services import bootstrap
    monkeypatch.setattr(settings, "INITIAL_ADMIN_PASSWORD", "")
    monkeypatch.setattr(settings, "DEFAULT_SUPERADMIN_PASSWORD", "")
    su = auth(login(client))
    assert client.get("/api/auth/me", headers=su).status_code == 200
    client.portal.call(bootstrap.ensure_default_superadmin, True)
    assert client.get("/api/auth/me", headers=su).status_code == 401


def test_forced_test_mode_gives_the_default_super_admin_the_lab_password(client, policy):
    from app.services import bootstrap
    policy({"test_mode.forced": True})
    pw = client.portal.call(bootstrap.ensure_default_superadmin, True)
    assert pw == "imPress@2026" == bootstrap.FORCED_TEST_PASSWORD


def test_the_default_super_admin_cannot_be_removed_by_anyone(client):
    su = auth(login(client))
    _, other = make_user(client, su, "root9", role="super_admin")
    me = client.get("/api/auth/me", headers=su).json()["id"]
    for r in (client.post(f"/api/admin/users/{me}/deactivate", headers=other), client.delete(f"/api/admin/users/{me}", headers=other),
              client.post(f"/api/admin/users/{me}/role", headers=other, json={"role": "teacher"}),
              client.post(f"/api/admin/users/{me}/reset-password", headers=other, json={})):
        assert r.status_code == 403


# ── session limits ──────────────────────────────────────────────────────

def test_only_faculty_get_the_longer_limit_during_class(client, monkeypatch):
    from app import auth as authmod
    from app.config import settings

    async def in_class(db, user, now):
        return True
    monkeypatch.setattr(authmod, "in_class_now", in_class)
    su = auth(login(client))
    _, adm = make_user(client, su, "adm3", role="admin")
    _, teacher = make_user(client, su, "tch3")
    me = lambda h: client.get("/api/auth/session", headers=h).json()["idle_timeout_s"]            # noqa: E731
    assert me(adm) == settings.SESSION_IDLE_MINUTES * 60 and me(su) == settings.SESSION_IDLE_MINUTES * 60
    assert me(teacher) == settings.SESSION_CLASS_IDLE_MINUTES * 60


# ── the trash ───────────────────────────────────────────────────────────

def test_a_deleted_account_goes_to_the_trash_and_comes_back(client):
    su = auth(login(client))
    uid, th = make_user(client, su, "gone1")
    assert client.delete(f"/api/admin/users/{uid}", headers=su).status_code == 204
    assert not any(u["username"] == "gone1" for u in client.get("/api/admin/users", headers=su).json())
    trash = client.get("/api/admin/users/deleted", headers=su).json()
    assert trash["retention_days"] == 30 and [a["username"] for a in trash["accounts"]] == ["gone1"]
    assert trash["accounts"][0]["days_left"] in (29, 30)
    again = client.post(f"/api/admin/users/deleted/{trash['accounts'][0]['id']}/restore", headers=su)
    assert again.status_code == 200 and again.json()["username"] == "gone1"
    assert client.get("/api/admin/users/deleted", headers=su).json()["accounts"] == []
    assert client.post("/api/auth/login", json={"username": "gone1", "password": PASSWORD}).status_code == 200      # same password


def test_restore_refuses_a_taken_name_and_purge_removes_for_good(client):
    su = auth(login(client))
    uid, _ = make_user(client, su, "dup1")
    client.delete(f"/api/admin/users/{uid}", headers=su)
    make_user(client, su, "dup1")                                                                  # the name is used again
    tid = client.get("/api/admin/users/deleted", headers=su).json()["accounts"][0]["id"]
    assert client.post(f"/api/admin/users/deleted/{tid}/restore", headers=su).status_code == 409
    assert client.delete(f"/api/admin/users/deleted/{tid}", headers=su).status_code == 204
    assert client.get("/api/admin/users/deleted", headers=su).json()["accounts"] == []


def test_the_trash_is_emptied_after_thirty_days(client):
    from datetime import timedelta

    from sqlalchemy import update

    from app.database import async_session
    from app.models import DeletedUser
    from app.services import housekeeping
    from app.timeutil import istnow
    su = auth(login(client))
    uid, _ = make_user(client, su, "old1")
    client.delete(f"/api/admin/users/{uid}", headers=su)
    assert client.portal.call(housekeeping.purge_deleted_accounts) == 0

    async def age():
        async with async_session() as s:
            await s.execute(update(DeletedUser).values(purge_after=istnow() - timedelta(days=1)))
            await s.commit()
    client.portal.call(age)
    assert client.portal.call(housekeeping.purge_deleted_accounts) == 1
    assert client.get("/api/admin/users/deleted", headers=su).json()["accounts"] == []


def test_only_admins_see_the_trash_and_only_super_admins_restore_admins(client):
    su = auth(login(client))
    _, teacher = make_user(client, su, "tch4")
    _, adm = make_user(client, su, "adm4", role="admin")
    aid, _ = make_user(client, su, "adm5", role="admin")
    client.delete(f"/api/admin/users/{aid}", headers=su)
    assert client.get("/api/admin/users/deleted", headers=teacher).status_code == 403
    tid = client.get("/api/admin/users/deleted", headers=adm).json()["accounts"][0]["id"]
    assert client.post(f"/api/admin/users/deleted/{tid}/restore", headers=adm).status_code == 403
    assert client.post(f"/api/admin/users/deleted/{tid}/restore", headers=su).status_code == 200


# ── preferences and onboarding ──────────────────────────────────────────

def test_preferences_are_validated_and_saved_per_account(client):
    su = auth(login(client))
    _, th = make_user(client, su, "pref1")
    p = client.get("/api/auth/preferences", headers=th).json()
    assert p["theme"] == "system" and p["advanced"] is False and p["scale"] == "default"
    r = client.put("/api/auth/preferences", headers=th, json={"theme": "dark", "accent": "teal", "scale": "large", "vision": "deuteranopia",
                                                              "motion": "reduce", "contrast": "high", "sidebar_collapsed": True})
    assert r.status_code == 200 and r.json()["theme"] == "dark" and r.json()["vision"] == "deuteranopia"
    assert client.get("/api/auth/preferences", headers=su).json()["theme"] == "system"             # someone else's are separate
    for bad in ({"theme": "neon"}, {"scale": "2x"}, {"unknown": 1}, {"accent_custom": "red"}, {"sidebar_collapsed": "yes"},
                {"dashboard": [{"id": "a", "kind": "x", "size": "huge"}]}, {"dashboard": "nope"}):
        assert client.put("/api/auth/preferences", headers=th, json=bad).status_code == 422, bad


def test_advanced_mode_is_for_administrators(client):
    su = auth(login(client))
    _, th = make_user(client, su, "pref2")
    assert client.put("/api/auth/preferences", headers=th, json={"advanced": True}).json()["advanced"] is False
    assert client.put("/api/auth/preferences", headers=su, json={"advanced": True}).json()["advanced"] is True
    assert client.get("/api/auth/me", headers=su).json()["preferences"]["advanced"] is True


def test_the_dashboard_layout_is_saved(client):
    su = auth(login(client))
    layout = [{"id": "w1", "kind": "students-ring", "size": "md"}, {"id": "w2", "kind": "classes-list", "size": "lg"}]
    assert client.put("/api/auth/preferences", headers=su, json={"dashboard": layout}).json()["dashboard"] == layout
    assert client.put("/api/auth/preferences", headers=su, json={"dashboard": layout + layout}).status_code == 422     # duplicate ids


def test_onboarding_needs_the_password_first_and_then_marks_the_welcome_done(client):
    su = auth(login(client))
    r = _new(client, su, "onb1")
    temp = r.json()["temporary_password"]
    h = auth(client.post("/api/auth/login", json={"username": "onb1", "password": temp}).json()["access_token"])
    assert client.get("/api/auth/me", headers=h).json()["onboarded"] is False
    assert client.post("/api/auth/onboarding", headers=h, json={"display_name": "Oni", "theme": "dark"}).status_code == 409
    client.post("/api/auth/change-password", headers=h, json={"current_password": temp, "new_password": "My-Own-Pass9"})
    h = auth(client.post("/api/auth/login", json={"username": "onb1", "password": "My-Own-Pass9"}).json()["access_token"])
    me = client.post("/api/auth/onboarding", headers=h, json={"display_name": "Oni", "theme": "dark"}).json()
    assert me["onboarded"] is True and me["name"] == "Oni" and me["preferences"]["theme"] == "dark"
    assert client.put("/api/auth/me", headers=h, json={"display_name": "Oni-san"}).json()["name"] == "Oni-san"


# ── classes: icon and colour ────────────────────────────────────────────

def test_a_class_has_an_icon_and_a_colour(client):
    su = auth(login(client))
    cid = make_class(client, su, name="Pretty", code="PRT101", icon="rocket", color="#ff8800")
    c = client.get(f"/api/classes/{cid}", headers=su).json()
    assert c["icon"] == "rocket" and c["color"] == "#ff8800"
    assert client.put(f"/api/admin/classes/{cid}", headers=su, json={"icon": "leaf", "color": "#00aa55"}).json()["icon"] == "leaf"
    for bad in ({"icon": "skull"}, {"color": "orange"}, {"color": "#12"}):
        assert client.put(f"/api/admin/classes/{cid}", headers=su, json=bad).status_code == 422, bad
    r = client.post("/api/admin/classes", headers=su, json={"name": "X", "code": "X1", "icon": "nope"})
    assert r.status_code == 422


# ── search ──────────────────────────────────────────────────────────────

def test_search_finds_only_what_the_caller_may_see(client):
    su = auth(login(client))
    ida, a = make_user(client, su, "srcha")
    _, b = make_user(client, su, "srchb")
    mine = make_class(client, su, name="Quantum Physics", code="QP101", teacher_id=ida)
    make_class(client, su, name="Quantum Chemistry", code="QC101")
    own = make_student(client, a, roll="SEARCH0001", name="Quentin Quark")
    make_student(client, su, roll="SEARCH0002", name="Quincy Quark")
    groups = lambda h, q: {g["type"]: g["items"] for g in client.get(f"/api/search?q={q}", headers=h).json()["groups"]}      # noqa: E731
    assert [i["title"] for i in groups(su, "quantum")["class"]] == ["Quantum Physics", "Quantum Chemistry"] or len(groups(su, "quantum")["class"]) == 2
    assert [i["title"] for i in groups(a, "quantum")["class"]] == ["Quantum Physics"]                # not the other class
    assert "class" not in groups(b, "quantum")
    assert [i["title"] for i in groups(a, "quark")["student"]] == ["Quentin Quark"]                  # only the student A registered
    assert len(groups(su, "quark")["student"]) == 2
    assert "user" not in groups(a, "srch") and "user" in groups(su, "srch")                          # accounts are for admins
    assert client.get("/api/search?q=q", headers=su).json()["groups"] == []                         # too short
    assert client.get("/api/search?q=quantum").status_code == 401
    assert mine and own


# ── presence and activity ───────────────────────────────────────────────

def test_presence_and_the_activity_summary(client):
    su = auth(login(client))
    uid, th = make_user(client, su, "pres1")
    client.get("/api/classes/", headers=th)
    p = client.get("/api/admin/presence", headers=su).json()
    names = {u["username"] for u in p["active"]}
    assert {DEFAULT, "pres1"} <= names and p["total_accounts"] >= 2
    assert client.get("/api/admin/presence", headers=th).status_code == 403
    s = client.get(f"/api/admin/users/{uid}/activity-summary?days=7", headers=su).json()
    assert s["days"] == 7 and len(s["daily"]) == 7 and len(s["heatmap"]) == 7 and len(s["heatmap"][0]) == 24
    assert s["logins"] >= 1 and s["total"] >= 1 and s["by_kind"][0]["kind"] == "auth"
    assert client.get(f"/api/admin/users/{uid}/activity-summary?days=7", headers=th).status_code == 403
    assert client.get(f"/api/admin/users/{uid}/activity-summary?days=999", headers=su).status_code == 422


def test_date_and_time_formats_are_preferences(client):
    su = auth(login(client))
    r = client.put("/api/auth/preferences", headers=su, json={"date_format": "long", "time_format": "12h", "show_seconds": True,
                                                              "week_start": "sunday", "number_format": "1.234,5",
                                                              "relative_times": False, "landing": "classrooms"})
    assert r.status_code == 200 and r.json()["date_format"] == "long" and r.json()["time_format"] == "12h"
    p = client.get("/api/auth/preferences", headers=su).json()
    assert p["week_start"] == "sunday" and p["relative_times"] is False and p["landing"] == "classrooms"
    for bad in ({"date_format": "yy"}, {"time_format": "36h"}, {"week_start": "friday"}, {"show_seconds": "yes"}, {"landing": "admin"}):
        assert client.put("/api/auth/preferences", headers=su, json=bad).status_code == 422, bad


def test_the_web_apps_meter_agrees_with_the_servers():
    """ui.js passwordStrength / passwordProblem must score and judge exactly as passwords.py does."""
    import shutil
    import subprocess
    from pathlib import Path
    node = shutil.which("node")
    if not node:
        pytest.skip("node is not installed")
    cases = ["", "abc", "password", "Passw0rd!", "abcdefgh1", "Tr0ub4dor&3xyz!", "Tr0ub4dor&3-horse-staple", "ALLUPPER1!", "aA1!aA1!aA1!aA1!x",
             "impress.default.superAdmin", "short1A!", "NoSpecial123", "alllower12345", "aaaaaaaaaa"]
    src = (Path(__file__).resolve().parents[1] / "app/static/js/ui.js").read_text()
    start, end = src.index("const COMMON_PASSWORDS"), src.index("/** The meter under")
    js = (src[start:end] + f"const cases = {json.dumps(cases)};"
          "process.stdout.write(JSON.stringify(cases.map(p => [passwordStrength(p, 'impress.default.superAdmin').score, "
          "passwordProblem(p, 'impress.default.superAdmin', 'teacher'), passwordProblem(p, 'impress.default.superAdmin', 'super_admin')])));")
    out = json.loads(subprocess.run([node, "-e", js], capture_output=True, text=True, check=True).stdout)
    want = [[passwords.strength(c, "impress.default.superAdmin")["score"], passwords.problem(c, "impress.default.superAdmin", "teacher"),
             passwords.problem(c, "impress.default.superAdmin", "super_admin")] for c in cases]
    norm = lambda rows: [[r[0], (r[1] or "").replace("(for example ! @ # $ %)", "").strip(), (r[2] or "").strip()] for r in rows]     # noqa: E731
    assert norm(out) == norm(want)
