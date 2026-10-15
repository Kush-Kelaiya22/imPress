"""Two-step verification for dual control (#211): RFC 6238 vectors, replay, recovery codes, enrolment, the hardened rule."""

import time

import pytest

from conftest import auth, login, make_user
from app.services import mfa

# RFC 6238 appendix B, SHA-1, secret "12345678901234567890" (8 digits there; ours are the last 6)
RFC_SECRET = "GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ"
RFC_VECTORS = {59: "287082", 1111111109: "081804", 1111111111: "050471", 1234567890: "005924", 2000000000: "279037"}


@pytest.mark.parametrize("at,expected", RFC_VECTORS.items())
def test_rfc6238_vectors(at, expected):
    assert mfa.totp(RFC_SECRET, at) == expected


def test_a_code_is_accepted_once_and_a_skewed_clock_is_tolerated():
    secret, now = mfa.new_secret(), 1_700_000_000.0
    code = mfa.totp(secret, now)
    counter = mfa.match(secret, code, -1, now)
    assert counter == int(now // 30)
    assert mfa.match(secret, code, counter, now) is None                      # replay
    assert mfa.match(secret, mfa.totp(secret, now - 30), -1, now) == counter - 1       # a step behind
    assert mfa.match(secret, mfa.totp(secret, now + 30), -1, now) == counter + 1
    assert mfa.match(secret, mfa.totp(secret, now - 90), -1, now) is None              # expired
    assert mfa.match(secret, "12345", -1, now) is None and mfa.match(secret, "abcdef", -1, now) is None
    assert mfa.match(secret, " ".join([code[:3], code[3:]]), -1, now) == counter       # spaces as typed from the app


def test_the_otpauth_link_names_the_account_and_the_app():
    uri = mfa.otpauth_uri("a b", "SECRET")
    assert uri.startswith("otpauth://totp/imPress:a%20b?secret=SECRET&issuer=imPress") and "digits=6&period=30" in uri


def _super(client, name="boss2"):
    _, h = make_user(client, auth(login(client)), name, role="super_admin")
    return h


def _enrol(client, h, password="Passw0rd!x"):
    r = client.post("/api/auth/mfa/setup", headers=h, json={"password": password})
    assert r.status_code == 200, r.text
    secret = r.json()["secret"]
    r = client.post("/api/auth/mfa/enable", headers=h, json={"code": mfa.totp(secret)})
    assert r.status_code == 200, r.text
    return secret, r.json()["recovery_codes"]


def test_only_super_admins_can_set_it_up(client):
    su = auth(login(client))
    _, admin = make_user(client, su, "adm1", role="admin")
    assert client.get("/api/auth/mfa", headers=admin).status_code == 403
    assert client.get("/api/auth/mfa", headers=su).json() == {"enrolled": False, "pending": False, "required": False,
                                                              "recovery_codes_left": 0}


def test_enrolment_needs_the_password_and_a_working_code(client):
    h = _super(client)
    assert client.post("/api/auth/mfa/setup", headers=h, json={"password": "wrong"}).status_code == 403
    secret = client.post("/api/auth/mfa/setup", headers=h, json={"password": "Passw0rd!x"}).json()["secret"]
    assert client.get("/api/auth/mfa", headers=h).json()["pending"] is True
    assert client.post("/api/auth/mfa/enable", headers=h, json={"code": "000000"}).status_code == 403
    r = client.post("/api/auth/mfa/enable", headers=h, json={"code": mfa.totp(secret)})
    codes = r.json()["recovery_codes"]
    assert len(codes) == 10 and all(len(c) == 11 and c[5] == "-" for c in codes)
    assert client.get("/api/auth/mfa", headers=h).json()["enrolled"] is True
    assert client.post("/api/auth/mfa/setup", headers=h, json={"password": "Passw0rd!x"}).status_code == 409


def test_step_up_asks_for_the_code_once_enrolled(client):
    h = _super(client)
    secret, codes = _enrol(client, h)
    body = {"action": "integrity.accept_current", "params": {}, "password": "Passw0rd!x"}
    r = client.post("/api/admin/approvals", headers=h, json=body)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "MFA_CODE_REQUIRED"
    r = client.post("/api/admin/approvals", headers=h, json={**body, "code": "000000"})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "STEP_UP_FAILED"


def test_a_used_code_cannot_be_used_again_and_a_recovery_code_works_once(client, monkeypatch):
    h = _super(client)
    secret, codes = _enrol(client, h)                       # enrolment used this step's code
    body = {"action": "integrity.accept_current", "params": {}, "password": "Passw0rd!x"}
    r = client.post("/api/admin/approvals", headers=h, json={**body, "code": mfa.totp(secret)})
    assert r.status_code == 403, "the code that enrolled the account is spent"
    later = time.time() + 30                                # the next step's code
    monkeypatch.setattr(mfa.time, "time", lambda: later)
    code = mfa.totp(secret, later)
    assert client.post("/api/admin/approvals", headers=h, json={**body, "code": code}).status_code == 201
    assert client.post("/api/admin/approvals", headers=h, json={**body, "code": code}).status_code == 403    # replay
    assert client.post("/api/admin/approvals", headers=h, json={**body, "code": codes[0].lower()}).status_code == 201
    assert client.post("/api/admin/approvals", headers=h, json={**body, "code": codes[0]}).status_code == 403   # single use
    assert client.get("/api/auth/mfa", headers=h).json()["recovery_codes_left"] == 9


def test_wrong_codes_count_towards_the_step_up_lockout(client):
    h = _super(client)
    _enrol(client, h)
    body = {"action": "integrity.accept_current", "params": {}, "password": "Passw0rd!x", "code": "000000"}
    for _ in range(5):
        assert client.post("/api/admin/approvals", headers=h, json=body).status_code == 403
    r = client.post("/api/admin/approvals", headers=h, json=body)
    assert r.status_code == 429 and r.json()["detail"]["code"] == "STEP_UP_LOCKED"


def test_the_policy_makes_it_mandatory_and_unremovable(client, policy):
    h = _super(client)
    policy({"dual_control.mfa_required": True})
    body = {"action": "integrity.accept_current", "params": {}, "password": "Passw0rd!x"}
    r = client.post("/api/admin/approvals", headers=h, json=body)
    assert r.status_code == 403 and r.json()["detail"]["code"] == "MFA_ENROLMENT_REQUIRED"
    secret, _ = _enrol(client, h)                            # enrolling is still possible: it is how you comply
    assert client.get("/api/auth/mfa", headers=h).json()["required"] is True
    r = client.post("/api/auth/mfa/disable", headers=h, json={"password": "Passw0rd!x", "code": mfa.totp(secret)})
    assert r.status_code == 403 and r.json()["detail"]["code"] == "MFA_REQUIRED_BY_POLICY"


def test_it_can_be_turned_off_when_policy_does_not_require_it(client, monkeypatch):
    h = _super(client)
    secret, _ = _enrol(client, h)
    later = time.time() + 30
    monkeypatch.setattr(mfa.time, "time", lambda: later)
    assert client.post("/api/auth/mfa/disable", headers=h, json={"password": "Passw0rd!x", "code": "000000"}).status_code == 403
    assert client.post("/api/auth/mfa/disable", headers=h, json={"password": "Passw0rd!x", "code": mfa.totp(secret, later)}).status_code == 200
    assert client.get("/api/auth/mfa", headers=h).json()["enrolled"] is False


def test_new_recovery_codes_replace_the_old(client, monkeypatch):
    h = _super(client)
    secret, old = _enrol(client, h)
    later = time.time() + 30
    monkeypatch.setattr(mfa.time, "time", lambda: later)
    r = client.post("/api/auth/mfa/recovery-codes", headers=h, json={"password": "Passw0rd!x", "code": mfa.totp(secret, later)})
    new = r.json()["recovery_codes"]
    assert len(new) == 10 and not set(new) & set(old)
    body = {"action": "integrity.accept_current", "params": {}, "password": "Passw0rd!x"}
    assert client.post("/api/admin/approvals", headers=h, json={**body, "code": old[0]}).status_code == 403
    assert client.post("/api/admin/approvals", headers=h, json={**body, "code": new[0]}).status_code == 201


def test_a_restore_also_asks_for_the_code(client):
    h = _super(client)
    _enrol(client, h)
    r = client.post("/api/admin/backups/startup/startup.db/restore", headers=h,
                    json={"password": "Passw0rd!x", "confirm": "startup.db"})
    assert r.status_code in (403, 404) and (r.status_code == 404 or r.json()["detail"]["code"] == "MFA_CODE_REQUIRED")


def test_hardened_defaults_require_it_and_the_flag_cannot_be_loosened_by_an_override():
    from app import gpc
    assert gpc.FLAGS["dual_control.mfa_required"].hardened is True and gpc.FLAGS["dual_control.mfa_required"].standard is False
    with pytest.raises(gpc.PolicyError, match="loosen"):
        gpc.build("hardened", "dual_control.mfa_required=false", None, None)


def test_root_can_remove_a_lost_second_factor(client):
    from app.services import rootops
    h = _super(client)
    _enrol(client, h)
    assert "on" in client.portal.call(rootops.mfa, "boss2", False)
    assert "removed" in client.portal.call(rootops.mfa, "boss2", True)
    assert "off" in client.portal.call(rootops.mfa, "boss2", False)
    assert client.get("/api/auth/mfa", headers=h).status_code == 401           # signed out
