"""#42: the documented install path: scripts, secrets, version, CI job."""

import importlib.util
import json
import re
import stat

from conftest import ROOT

spec = importlib.util.spec_from_file_location("init_env", ROOT / "scripts" / "init_env.py")
init_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(init_env)

DEFAULTS = ("CHANGE-ME-IN-PRODUCTION-use-a-real-secret", "impress-device-key-2024")


def _backend(tmp_path, env=None):
    (tmp_path / ".env.example").write_text((ROOT / "backend" / ".env.example").read_text())
    if env is not None:
        (tmp_path / ".env").write_text(env)
    return tmp_path


def _values(path):
    return {k.strip(): v.partition("#")[0].strip() for k, _, v in
            (l.partition("=") for l in path.read_text().splitlines() if "=" in l and not l.startswith("#"))}


def test_fresh_env_gets_random_secrets_never_the_defaults(tmp_path):
    b = _backend(tmp_path)
    assert init_env.init_env(b) == ["IMPRESS_JWT_SECRET", "IMPRESS_DEVICE_API_KEY"]
    v = _values(b / ".env")
    for name in init_env.GENERATED:
        assert len(v[name]) >= 40 and v[name] not in DEFAULTS
    assert stat.S_IMODE((b / ".env").stat().st_mode) == 0o600


def test_two_installs_get_different_secrets(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    init_env.init_env(_backend(a))
    init_env.init_env(_backend(b))
    assert _values(a / ".env")["IMPRESS_JWT_SECRET"] != _values(b / ".env")["IMPRESS_JWT_SECRET"]


def test_existing_values_are_kept_and_missing_ones_added(tmp_path):
    b = _backend(tmp_path, "IMPRESS_JWT_SECRET=mine\nIMPRESS_DEBUG=false\n")
    (b / ".env").chmod(0o644)
    assert init_env.init_env(b) == ["IMPRESS_DEVICE_API_KEY"]
    v = _values(b / ".env")
    assert v["IMPRESS_JWT_SECRET"] == "mine" and v["IMPRESS_DEBUG"] == "false" and v["IMPRESS_DEVICE_API_KEY"]
    assert stat.S_IMODE((b / ".env").stat().st_mode) == 0o600            # tightened
    assert init_env.init_env(b) == []                                     # idempotent


def test_generated_env_is_accepted_by_the_backend_settings(tmp_path, monkeypatch):
    b = _backend(tmp_path)
    init_env.init_env(b)
    monkeypatch.chdir(b)
    for name in ("IMPRESS_JWT_SECRET", "IMPRESS_DEVICE_API_KEY", "IMPRESS_DEBUG"):
        monkeypatch.delenv(name, raising=False)
    import sys
    sys.path.insert(0, str(ROOT / "backend"))
    from app.config import Settings, insecure_settings
    s = Settings()                                   # reads ./.env, inline comments included
    assert insecure_settings(s) == [] and s.DEVICE_API_KEY == _values(b / ".env")["IMPRESS_DEVICE_API_KEY"]


def test_version_file_is_semver_and_matches_the_firmware():
    version = (ROOT / "VERSION").read_text().strip()
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    for project in ("class_c6", "class_s3", "student"):
        assert (ROOT / "firmware" / project / "version.txt").read_text().strip() == version, project


def test_ci_runs_the_install_path(workflow):
    job = workflow["jobs"]["install-smoke"]
    text = json.dumps(job["steps"])
    for needle in ("scripts/install.sh", "scripts/start.sh", "scripts/smoke_test.py"):
        assert needle in text, needle
    assert "pip install" not in text            # the script installs, not the workflow
