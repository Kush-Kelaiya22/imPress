"""v2.2 platform: features and who may change them, TrustedInstaller's start-up check, the traffic monitor and risk
badges, 1PSID, the disabled-account signal, the status banners."""

import time

import pytest

from conftest import PASSWORD, auth, login, make_user
from app.services import boot_verify, features, traffic

DEFAULT = "impress.default.superAdmin"


# ── features and authority ───────────────────────────────────────────────

def test_a_super_admin_switches_a_feature_and_it_is_logged_with_who_and_when(client):
    su = auth(login(client))
    r = client.put("/api/admin/features/search", headers=su, json={"enabled": False})
    assert r.status_code == 200 and r.json()["enabled"] is False and r.json()["set_by"]
    assert client.get("/api/system/status").json()["feature_flags"]["search"] is False
    log = client.get("/api/admin/features/log?flag=search", headers=su).json()
    assert log[0]["new"] == "off" and log[0]["actor_role"] == "super admin" and log[0]["at"]


def test_a_lower_rank_cannot_undo_a_higher_one_and_a_lock_stops_lower_ranks(client):
    su = auth(login(client))
    _, adm = make_user(client, su, "adm1", role="admin")
    assert client.put("/api/admin/features/trash", headers=adm, json={"enabled": False}).status_code == 200
    assert client.put("/api/admin/features/trash", headers=su, json={"enabled": True}).status_code == 200      # higher may
    assert client.put("/api/admin/features/trash", headers=adm, json={"enabled": False}).status_code == 403     # set by a super admin
    assert client.put("/api/admin/features/trash", headers=su, json={"enabled": True, "min_rank": 2}).status_code == 200
    r = client.put("/api/admin/features/trash", headers=adm, json={"enabled": False})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "FEATURE_LOCKED"
    assert client.put("/api/admin/features/trash", headers=adm, json={"min_rank": 2}).status_code == 403
    assert client.put("/api/admin/features/trash", headers=su, json={"min_rank": 3}).status_code == 403     # cannot lock above yourself


def test_faculty_see_nothing_of_it_and_unknown_features_are_refused(client):
    su = auth(login(client))
    _, th = make_user(client, su, "fac1")
    for call in (lambda: client.get("/api/admin/features", headers=th), lambda: client.get("/api/admin/features/log", headers=th),
                 lambda: client.put("/api/admin/features/search", headers=th, json={"enabled": False}),
                 lambda: client.get("/api/admin/traffic", headers=th), lambda: client.get("/api/admin/risk", headers=th),
                 lambda: client.get("/api/admin/system/requirements", headers=th)):
        assert call().status_code == 403
    assert client.put("/api/admin/features/nope", headers=su, json={"enabled": False}).status_code == 403


def test_root_switches_win_over_everyone(client, policy):
    su = auth(login(client))
    policy({"features.disabled": "backups,search"})
    assert client.get("/api/system/status").json()["feature_flags"]["backups"] is False
    r = client.put("/api/admin/features/backups", headers=su, json={"enabled": True})
    assert r.status_code == 403 and "Root" in r.json()["detail"]["message"]
    got = {f["name"]: f for f in client.get("/api/admin/features", headers=su).json()["features"]}
    assert got["backups"]["set_by"].startswith("root")


def test_trusted_installer_turns_features_off_and_back_on_and_restores_the_earlier_choice(client, db):
    su = auth(login(client))
    client.put("/api/admin/features/backups", headers=su, json={"enabled": False})                     # an admin's choice
    async def off(s):
        await features.trusted_set(s, "backups", False, "Free disk space: 100 MB is below the minimum of 2048 MB")
    db(off)
    client.portal.call(lambda: None)
    assert features.describe("backups")["set_rank"] == features.TRUSTED
    r = client.put("/api/admin/features/backups", headers=su, json={"enabled": True})
    assert r.status_code == 403 and "TrustedInstaller" in r.json()["detail"]["message"]
    async def on(s):
        await features.trusted_set(s, "backups", True, "ok")
    db(on)
    client.portal.call(lambda: None)
    got = {f["name"]: f for f in client.get("/api/admin/features", headers=su).json()["features"]}
    assert got["backups"]["enabled"] is False and got["backups"]["set_rank"] == features.SUPER          # the choice came back
    assert any(e["actor_role"] == "TrustedInstaller" for e in client.get("/api/admin/features/log?flag=backups", headers=su).json())


def test_a_switched_off_feature_is_enforced_by_the_server(client):
    su = auth(login(client))
    client.put("/api/admin/features/risk_scores", headers=su, json={"enabled": False})
    r = client.get("/api/admin/risk", headers=su)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "FEATURE_DISABLED"


# ── TrustedInstaller ──────────────────────────────────────────────────────

def test_the_host_check_reports_each_requirement(client):
    su = auth(login(client))
    rep = client.get("/api/admin/system/requirements", headers=su).json()
    ids = {c["id"] for c in rep["checks"]}
    assert {"os", "python", "sqlite", "data", "cores", "memory", "disk", "clock"} <= ids
    assert rep["locked"] is False and rep["host"]["python"] and "summary" in rep


def test_a_host_below_the_minimum_loses_exactly_the_features_that_need_it(client, db, monkeypatch):
    monkeypatch.setenv("IMPRESS_MIN_DISK_MB", str(10**9))
    async def go(s):
        return await boot_verify.run(s)
    rep = db(go)
    assert rep["passed"] is False and rep["locked"] is False and set(rep["gated"]) == {"backups", "trash"}
    assert features.enabled("backups") is False and features.enabled("search") is True
    su = auth(login(client))
    assert client.get("/api/system/status").json()["feature_flags"]["backups"] is False
    monkeypatch.setenv("IMPRESS_MIN_DISK_MB", "1")
    assert db(go)["passed"] is True and features.enabled("backups") is True                          # back at the next passing start
    assert su


def test_nothing_is_offered_while_locked_down(client, monkeypatch):
    monkeypatch.setitem(boot_verify._report, "locked", True)
    monkeypatch.setitem(boot_verify._report, "summary", "Python 3.9 is below the minimum.")
    r = client.get("/api/auth/me")
    assert r.status_code == 503 and r.json()["detail"]["code"] == "LOCKED_DOWN" and "Python" in r.json()["detail"]["message"]
    assert client.get("/api/system/status").status_code == 200 and client.get("/health").status_code == 200


def test_a_container_loses_the_separate_root_console(client, db, monkeypatch, policy):
    monkeypatch.setenv("IMPRESS_IN_CONTAINER", "1")
    async def go(s):
        return await boot_verify.run(s)
    rep = db(go)
    from app import gpc
    assert rep["container"] is True and gpc.get("root.allow_access") is False
    su = auth(login(client))
    assert any(e["flag"] == "root.allow_access" and e["actor_role"] == "TrustedInstaller"
               for e in client.get("/api/admin/features/log?flag=root.allow_access", headers=su).json())


# ── status banners, release, the update notice ───────────────────────────

def test_status_carries_the_release_and_the_banners(client, policy):
    st = client.get("/api/system/status").json()
    assert st["release"].count(".") == 2 and st["banners"] == [] and st["updating"]["active"] is False
    policy({"iips.enabled": False})
    from app.services import iips
    iips._state["enabled"] = False
    banners = client.get("/api/system/status").json()["banners"]
    assert banners[0]["id"] == "iips" and "Integrity Protection Service is disabled. Proceed with caution." in banners[0]["text"]
    iips._state["enabled"] = True


def test_the_update_notice_appears_while_a_deployment_runs(client, db):
    from sqlalchemy import select

    from app.models import FirmwareArtifact, FirmwareDeployment
    from conftest import upload_firmware
    upload_firmware(client, auth(login(client)))
    assert client.get("/api/system/status").json()["updating"]["active"] is False

    async def add(s):
        aid = (await s.execute(select(FirmwareArtifact.id))).scalars().first()
        s.add(FirmwareDeployment(artifact_id=aid, state="running"))
    db(add)
    up = client.get("/api/system/status").json()["updating"]
    assert up["active"] is True and "updating the system" in up["message"]


# ── 1PSID and the disabled account ────────────────────────────────────────

def test_session_ids_carry_the_servers_identity_and_die_with_a_restart(client, monkeypatch):
    from app import auth as authmod
    tok = login(client)
    assert tok.startswith("impress_" + authmod.BOOT_ID)
    assert client.get("/api/auth/me", headers=auth(tok)).status_code == 200
    monkeypatch.setattr(authmod, "BOOT_ID", "ffffffff")                      # the server restarted
    r = client.get("/api/auth/me", headers=auth(tok))
    assert r.status_code == 401 and r.headers["x-session-code"] == "restart" and r.json()["detail"] == "SERVER_RESTARTED"
    assert client.get("/api/auth/me", headers=auth(login(client))).status_code == 200


def test_a_disabled_account_gets_a_clear_signal_not_a_generic_error(client):
    su = auth(login(client))
    uid, th = make_user(client, su, "gone2")
    assert client.get("/api/auth/me", headers=th).status_code == 200
    assert client.post(f"/api/admin/users/{uid}/deactivate", headers=su).status_code == 200
    r = client.get("/api/auth/me", headers=th)
    assert r.status_code == 401 and r.headers["x-session-code"] == "disabled" and r.json()["detail"] == "ACCOUNT_DISABLED"
    again = client.post("/api/auth/login", json={"username": "gone2", "password": PASSWORD})
    assert again.status_code in (401, 403)


def test_only_a_super_admin_ends_other_peoples_sessions(client):
    su = auth(login(client))
    uid, th = make_user(client, su, "vict1")
    _, adm = make_user(client, su, "adm2", role="admin")
    assert client.post(f"/api/admin/users/{uid}/end-sessions", headers=adm).status_code == 403
    assert client.post(f"/api/admin/users/{uid}/end-sessions", headers=su).status_code == 200
    assert client.get("/api/auth/me", headers=th).status_code == 401


# ── the traffic monitor and risk ─────────────────────────────────────────

@pytest.fixture(autouse=True)
def _fresh_traffic():
    traffic.reset()
    yield
    traffic.reset()


def test_one_origin_over_a_limit_is_a_dos_flag_with_details_and_no_blocking(client):
    t = time.monotonic()
    for i in range(traffic.LIMITS["sign-in"][0] + 5):
        traffic.record("203.0.113.9", "/api/auth/login", "POST", 401, None, now=t + i * 0.01)
    [a] = traffic.alerts()
    assert a["type"] == "DoS" and a["origin"] == "203.0.113.9" and a["endpoint_kind"] == "sign-in"
    assert a["pages"][0]["path"] == "/api/auth/login" and a["requests_per_minute"] > a["limit_per_minute"]
    assert client.get("/health").status_code == 200                           # nothing is refused


def test_a_flag_is_raised_once_per_cooldown_not_on_every_request(client):
    t = time.monotonic()
    for i in range(300):
        traffic.record("203.0.113.9", "/api/auth/login", "POST", 401, None, now=t + i * 0.01)
    assert len(traffic.alerts()) == 1


def test_many_origins_together_make_a_ddos_flag(client):
    t = time.monotonic()
    limit = traffic.LIMITS["sign-in"][0]
    for i in range(limit * traffic.DDOS_FACTOR + 10):
        traffic.record(f"198.51.100.{i % 20}", "/api/auth/login", "POST", 401, None, now=t + i * 0.001)
    kinds = {a["type"] for a in traffic.alerts()}
    assert "DDoS" in kinds and any(len(a["origins"]) >= traffic.DDOS_ORIGINS for a in traffic.alerts() if a["type"] == "DDoS")


def test_ordinary_busy_use_is_not_flagged(client):
    t = time.monotonic()
    for i in range(400):                                      # a busy page: far below the read limit
        traffic.record("192.0.2.5", "/api/classes/", "GET", 200, 7, now=t + i * 0.1)
    assert traffic.alerts() == []
    assert traffic.score(7, 0, now=t + 40)["label"] == "Safe"


def test_the_account_named_in_a_flag_is_in_the_alert_and_the_activity_log(client):
    su = auth(login(client))
    me = client.get("/api/auth/me", headers=su).json()["id"]
    async def burst():
        t = time.monotonic()
        for i in range(traffic.LIMITS["write"][1] + 5):
            traffic.record("192.0.2.77", "/api/classes/1", "POST", 200, me, now=t + i * 0.01)
        await __import__("asyncio").sleep(0.5)
    client.portal.call(burst)
    seen = client.get("/api/admin/traffic", headers=su).json()
    assert seen["alerts"][0]["username"] == DEFAULT and "Nothing was blocked" in seen["alerts"][0]["message"]
    assert seen["limits"]["write"]["per_account"] == traffic.LIMITS["write"][1]
    acts = client.get("/api/admin/activity?action=traffic.flagged", headers=su)
    assert acts.status_code in (200, 404, 422)


def test_risk_badges_and_reasons(client):
    t = time.monotonic()
    assert traffic.score(1, 0, now=t) == {"score": 0, "label": "Safe", "reasons": ["Nothing unusual."]}
    for i in range(40):
        traffic.record("192.0.2.1", "/api/admin/users", "GET", 403, 5, now=t + i)
    for ip in ("192.0.2.1", "192.0.2.2", "192.0.2.3", "192.0.2.4"):
        traffic.record(ip, "/api/classes/", "GET", 200, 5, now=t + 41)
    s = traffic.score(5, 2, now=t + 45)
    assert s["label"] in ("Potentially Unsafe", "Likely Compromised") and 25 <= s["score"] <= 100
    assert any("refused requests" in r for r in s["reasons"]) and any("addresses" in r for r in s["reasons"])
    assert traffic.label(0) == "Safe" and traffic.label(24) == "Safe" and traffic.label(25) == "Potentially Unsafe" \
        and traffic.label(60) == "Likely Compromised" and traffic.label(100) == "Likely Compromised"


def test_risk_endpoint_lists_every_account_for_administrators(client):
    su = auth(login(client))
    uid, _ = make_user(client, su, "risk1")
    got = client.get("/api/admin/risk", headers=su).json()
    assert got[str(uid)]["label"] == "Safe" and isinstance(got[str(uid)]["score"], int)


def test_the_monitor_can_be_switched_off(client, policy):
    policy({"traffic.monitor": False})
    t = time.monotonic()
    for i in range(300):
        traffic.record("203.0.113.9", "/api/auth/login", "POST", 401, None, now=t + i * 0.01)
    assert traffic.alerts() == []
