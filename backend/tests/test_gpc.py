"""Global policy control: defaults per profile, the root-signed file, inline overrides, the hardened floor."""

import base64
import json
from types import SimpleNamespace

import pytest

from app import ed25519, gpc

SEED = bytes(range(32))


def _files(tmp_path, doc=None, seed=SEED):
    pub = tmp_path / "root_public.key"
    pub.write_text(base64.b64encode(ed25519.public_key(seed)).decode())
    path = tmp_path / "global_policy_control.json"
    if doc is not None:
        path.write_text(json.dumps(doc))
    return path, pub


def _doc(profile="standard", flags=None, serial=1, seed=SEED):
    return gpc.sign_document(seed, profile, flags or {}, serial, "2026-10-15T10:00:00+05:30")


def _settings(tmp_path, **kw):
    base = dict(PROFILE="standard", GPC="", GPC_FILE=str(tmp_path / "global_policy_control.json"),
                ROOT_PUBLIC_KEY=str(tmp_path / "root_public.key"), DEBUG=False, REQUIRE_HTTPS=None,
                WS_REQUIRE_AUTH=True, SINGLE_SESSION=True, FIRMWARE_ALLOW_UNSIGNED=False,
                FIRMWARE_SINGLE_APPROVER=False, FIRMWARE_SIGNING_KEY="/k.pub",
                JWT_SECRET="s" * 32, DEVICE_API_KEY="k" * 32, DEVICE_HTTPS_ONLY=False, DEVICE_KEYS_REQUIRED=False)
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.fixture(autouse=True)
def _no_state(monkeypatch):
    serial = {"v": 0}
    monkeypatch.setattr(gpc, "_last_serial", lambda: serial["v"])
    monkeypatch.setattr(gpc, "_remember_serial", lambda n, k: serial.update(v=n))
    yield serial
    gpc.reset_for_tests()


def test_defaults_per_profile(tmp_path):
    _files(tmp_path)
    std = gpc.load(_settings(tmp_path))
    assert std.profile == "standard" and std.values["test_mode.allowed"] is True
    hard = gpc.load(_settings(tmp_path, PROFILE="hardened"))
    assert hard.profile == "hardened" and hard.values["test_mode.allowed"] is False
    assert hard.values["dual_control.single_operator_ok"] is False and hard.values["code.verify_manifest"] == "enforce"
    assert all(v == "default" for v in hard.sources.values())


def test_signed_file_applies_and_is_the_source(tmp_path):
    path, _ = _files(tmp_path, _doc(flags={"dual_control.delay_minutes": 45, "test_mode.allowed": False}))
    pol = gpc.load(_settings(tmp_path))
    assert pol.values["dual_control.delay_minutes"] == 45 and pol.sources["dual_control.delay_minutes"] == "file"
    assert pol.values["test_mode.allowed"] is False and pol.file["serial"] == 1
    assert gpc.get("dual_control.delay_minutes") == 45


@pytest.mark.parametrize("tamper", ["edit", "other_key", "unknown_flag", "bad_type", "no_public_key"])
def test_a_bad_signed_file_is_refused(tmp_path, tamper):
    doc = _doc(flags={"dual_control.delay_minutes": 5})
    if tamper == "edit":
        doc["flags"]["dual_control.delay_minutes"] = 0           # edited after signing
    elif tamper == "other_key":
        doc = _doc(flags={"dual_control.delay_minutes": 5}, seed=bytes(32))
    elif tamper == "unknown_flag":
        doc = _doc(flags={"made.up": True})
    elif tamper == "bad_type":
        doc = _doc(flags={"dual_control.delay_minutes": "soon"})
    path, pub = _files(tmp_path, doc)
    if tamper == "no_public_key":
        pub.unlink()
    pol = gpc.load(_settings(tmp_path))                          # standard: defaults + a recorded problem
    assert pol.problems and pol.values["dual_control.delay_minutes"] == 0 and pol.sources["dual_control.delay_minutes"] == "default"
    with pytest.raises(gpc.PolicyError):                         # hardened: refuses to start
        gpc.load(_settings(tmp_path, PROFILE="hardened"))


def test_an_older_signed_file_cannot_be_put_back(tmp_path, _no_state):
    _files(tmp_path, _doc(serial=7))
    gpc.load(_settings(tmp_path))
    assert _no_state["v"] == 7
    _files(tmp_path, _doc(serial=3, flags={"dual_control.enabled": False}))
    pol = gpc.load(_settings(tmp_path))
    assert any("rollback" in p for p in pol.problems) and pol.values["dual_control.enabled"] is True


def test_inline_overrides(tmp_path):
    _files(tmp_path)
    pol = gpc.load(_settings(tmp_path, GPC="dual_control.delay_minutes=30, test_mode.allowed=false"))
    assert pol.values["dual_control.delay_minutes"] == 30 and pol.sources["test_mode.allowed"] == "inline"
    for bad in ("nope=1", "dual_control.delay_minutes=-1", "dual_control.enabled=maybe", "code.verify_manifest=sometimes", "dual_control.delay_minutes"):
        with pytest.raises(gpc.PolicyError):
            gpc.load(_settings(tmp_path, GPC=bad))


def test_hardened_inline_overrides_can_only_tighten(tmp_path):
    _files(tmp_path)
    ok = gpc.load(_settings(tmp_path, PROFILE="hardened", GPC="dual_control.delay_minutes=60,integrity.forensic_copies=20,audit.sink_path=/var/log/impress-audit.jsonl"))
    assert ok.values["dual_control.delay_minutes"] == 60 and ok.values["audit.sink_path"] == "/var/log/impress-audit.jsonl"
    for loosen in ("dual_control.delay_minutes=1", "test_mode.allowed=true", "dual_control.single_operator_ok=true",
                   "code.verify_manifest=off", "test_mode.pending_ttl_hours=0", "test_mode.pending_ttl_hours=48",
                   "audit.min_retention_days=30"):
        with pytest.raises(gpc.PolicyError, match="loosen"):
            gpc.load(_settings(tmp_path, PROFILE="hardened", GPC=loosen))
    gpc.load(_settings(tmp_path, PROFILE="hardened", GPC="test_mode.pending_ttl_hours=12"))        # shorter is safer
    # but root can loosen with a signed file
    _files(tmp_path, _doc(profile="hardened", flags={"test_mode.allowed": True}))
    assert gpc.load(_settings(tmp_path, PROFILE="hardened")).values["test_mode.allowed"] is True


def test_the_signed_file_may_choose_the_profile(tmp_path):
    _files(tmp_path, _doc(profile="hardened"))
    assert gpc.load(_settings(tmp_path)).profile == "hardened"


def test_the_hardened_floor_names_what_is_missing(tmp_path):
    _files(tmp_path)
    gpc.load(_settings(tmp_path, PROFILE="hardened", GPC="audit.sink_path=/x"))
    assert gpc.hardened_problems(_settings(tmp_path, PROFILE="hardened")) == []
    gpc.enforce_startup(_settings(tmp_path, PROFILE="hardened"))
    bad = _settings(tmp_path, DEBUG=True, REQUIRE_HTTPS=False, WS_REQUIRE_AUTH=False, SINGLE_SESSION=False,
                    FIRMWARE_ALLOW_UNSIGNED=True, FIRMWARE_SINGLE_APPROVER=True, FIRMWARE_SIGNING_KEY="",
                    JWT_SECRET="CHANGE-ME-IN-PRODUCTION-use-a-real-secret")
    msgs = " | ".join(gpc.hardened_problems(bad))
    for needle in ("IMPRESS_DEBUG", "default secrets", "REQUIRE_HTTPS", "WS_REQUIRE_AUTH", "SINGLE_SESSION", "ALLOW_UNSIGNED",
                   "SINGLE_APPROVER", "SIGNING_KEY"):
        assert needle in msgs, needle
    with pytest.raises(RuntimeError, match="hardened"):
        gpc.enforce_startup(bad)
    gpc.load(_settings(tmp_path))                                  # standard: no floor
    assert gpc.hardened_problems(bad) == []


def test_the_hardened_floor_needs_an_audit_sink_and_the_root_key(tmp_path):
    path, pub = _files(tmp_path)
    gpc.load(_settings(tmp_path, PROFILE="hardened"))
    assert any("audit sink" in p for p in gpc.hardened_problems(_settings(tmp_path)))
    pub.unlink()
    assert any("root public key" in p for p in gpc.hardened_problems(_settings(tmp_path)))


def test_reload_keeps_the_last_good_policy_when_the_new_file_is_bad(tmp_path):
    path, _ = _files(tmp_path, _doc(serial=1, flags={"dual_control.delay_minutes": 20}))
    s = _settings(tmp_path)
    gpc.load(s)
    assert gpc.reload_if_changed(s) == (False, None)
    path.write_text(json.dumps(_doc(serial=2, flags={"dual_control.delay_minutes": 5}) | {"flags": {"dual_control.delay_minutes": 0}}))
    reloaded, err = gpc.reload_if_changed(s)
    assert not reloaded and "signature" in err     # refused ...
    assert gpc.get("dual_control.delay_minutes") == 20 and not gpc.current().problems   # ... and the last good policy stays
    path.write_text(json.dumps(_doc(serial=3, flags={"dual_control.delay_minutes": 90})))
    assert gpc.reload_if_changed(s) == (True, None) and gpc.get("dual_control.delay_minutes") == 90


def test_describe_lists_every_flag_with_its_source(tmp_path):
    _files(tmp_path)
    gpc.load(_settings(tmp_path, GPC="dual_control.delay_minutes=9"))
    d = gpc.describe()
    assert {f["name"] for f in d["flags"]} == set(gpc.FLAGS)
    one = next(f for f in d["flags"] if f["name"] == "dual_control.delay_minutes")
    assert one["value"] == 9 and one["source"] == "inline" and one["standard"] == 0 and one["hardened"] == 15


def test_every_flag_is_documented_with_its_defaults():
    from pathlib import Path
    doc = (Path(__file__).resolve().parents[2] / "docs/design/gpc.md").read_text()
    for f in gpc.FLAGS.values():
        row = next((l for l in doc.splitlines() if l.startswith(f"| `{f.name}` |")), None)
        assert row, f"{f.name} is not in docs/design/gpc.md"
        for want in (f.standard, f.hardened):
            assert (f"`{want}`" if want != "" else "empty") in row, (f.name, want)
