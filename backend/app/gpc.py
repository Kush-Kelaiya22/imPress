"""Global policy control (GPC, v2.2): the security and integrity switches that
only the root of an installation controls.

An application super admin can read the effective policy (System page,
GET /api/admin/system/policy) but nothing in the web app or the API can
change it. Where a value comes from, lowest to highest:

1. **built-in defaults** for the active profile
     standard   today's behaviour, plus protections that need no setup
     hardened   everything on: what a production classroom server should run
2. **a root-signed file**, global_policy_control.json (Ed25519). The server
   holds only the public key; the private key stays with root, off the
   application host (scripts/gpc.py keygen / set / sign / verify). A serial
   number only ever goes up, so an old signed file can't be put back.
3. **inline overrides** given on the command that starts the server:
     IMPRESS_GPC="dual_control.delay_minutes=30,test_mode.allowed=false" scripts/start.sh
   In the hardened profile an inline override may only make a flag *safer*;
   loosening one needs a signed file.

A signed file that fails verification is never half-applied. The hardened
profile refuses to start with it; the standard profile starts on defaults and
reports it (alert + audit event). The hardened profile also refuses to start
when the rest of the configuration is below its floor (hardened_problems()).
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field, replace
from pathlib import Path

from . import ed25519

log = logging.getLogger(__name__)

PROFILES = ("standard", "hardened")


class PolicyError(RuntimeError):
    """The policy could not be loaded as written: never half-applied."""


@dataclass(frozen=True)
class Conflict:
    flags: tuple
    why: str

    def text(self) -> str:
        return f"{' + '.join(self.flags)}: {self.why}"


class PolicyConflict(PolicyError):
    """Flags that cannot work together. Start-up stops here, before anything else is checked."""

    def __init__(self, conflicts: list):
        self.conflicts = conflicts
        super().__init__("flags that conflict:\n  - " + "\n  - ".join(c.text() for c in conflicts))


# (flags involved, does it hold, why it is a conflict, needs at least one of them set on purpose). A rule that needs an
# explicit flag does not fire on defaults alone, so `--no-test-mode` still works whatever the profile's defaults are.
RULES = [
    (("test_mode.forced", "test_mode.allowed"), lambda v, p: v["test_mode.forced"] and not v["test_mode.allowed"],
     "test mode is forced on, and also not allowed to exist (--test-mode with --no-test-mode)", False),
    (("test_mode.forced", "profile=hardened"), lambda v, p: v["test_mode.forced"] and p == "hardened",
     "the hardened profile cannot force test mode: it is for labs", False),
    (("iips.enabled", "profile=hardened"), lambda v, p: not v["iips.enabled"] and p == "hardened",
     "the hardened profile cannot run without integrity protection (--bypass-iips)", False),
    (("backups.restore_requires_approval", "dual_control.enabled"),
     lambda v, p: v["backups.restore_requires_approval"] and not v["dual_control.enabled"],
     "a restore needs a second super admin's approval, but dual control (approvals) is off, so no restore could ever run", True),
    (("dual_control.mfa_required", "dual_control.enabled"),
     lambda v, p: v["dual_control.mfa_required"] and not v["dual_control.enabled"],
     "a second factor is required for dual control, which is off", True),
    (("audit.purge_days", "audit.min_retention_days"),
     lambda v, p: 0 < v["audit.purge_days"] < v["audit.min_retention_days"],
     "audit entries would be deleted sooner than the minimum they must be kept", True),
    (("iips.device_binding", "iips.enabled"), lambda v, p: v["iips.device_binding"] == "enforce" and not v["iips.enabled"],
     "device binding is enforced, but integrity protection (which it belongs to) is off", True),
    (("firmware.signing_required", "ota.enabled"), lambda v, p: v["firmware.signing_required"] and not v["ota.enabled"],
     "images must be signed, but over-the-air updates are off, so there is nothing to sign", True),
]


def find_conflicts(values: dict, profile: str, explicit: set) -> list:
    """Every conflict among `values`. `explicit` names the flags somebody set on purpose (not left at the default)."""
    found = []
    for names, holds, why, needs_explicit in RULES:
        real = [n for n in names if n in values]
        if needs_explicit and not any(n in explicit for n in real):
            continue
        try:
            if holds(values, profile):
                found.append(Conflict(tuple(names), why))
        except KeyError:
            continue
    return found


@dataclass(frozen=True)
class Flag:
    name: str
    kind: str                      # bool | int | str | enum
    standard: object
    hardened: object
    safe: str                      # true | false | higher | lower | lower0 | order | set
    doc: str
    choices: tuple = ()
    scope: str = "policy"            # policy: sealed store, console/System page | feature: impress.flags.json, editable by hand
    editable_by: str = "root"        # root | super admin (the System page may change it, with step-up)


FLAGS: dict[str, Flag] = {f.name: f for f in [
    Flag("dual_control.enabled", "bool", True, True, "true",
         "Destructive or baseline-changing actions (accepting the current database state, clearing data) need a second super admin's approval."),
    Flag("dual_control.single_operator_ok", "bool", True, False, "false",
         "Allow the requester to approve their own action when they are the only active super admin."),
    Flag("dual_control.mfa_required", "bool", False, True, "true",
         "Every step of dual control (request, approve, restore a backup) also needs a code from the super admin's "
         "authenticator app (TOTP); a super admin who has not set one up cannot take part. A super admin who has set "
         "one up is always asked for the code, whatever this says."),
    Flag("dual_control.delay_minutes", "int", 0, 15, "higher",
         "Minutes between an approval and the earliest moment the action may run."),
    Flag("dual_control.expiry_minutes", "int", 240, 30, "lower",
         "Minutes an approval stays usable after its delay has passed."),
    Flag("system.reset_everything_allowed", "bool", True, False, "false",
         "Allow the 'reset everything' clear scope in the web app at all."),
    Flag("audit.sink_path", "str", "", "", "set",
         "Hash-chained, append-only audit file outside the database (put it on a WORM or remote-logged volume)."),
    Flag("audit.sink_url", "str", "", "", "set",
         "HTTP(S) endpoint that also receives every audit event, signed with an HMAC (off-host copy)."),
    Flag("audit.min_retention_days", "int", 0, 180, "higher",
         "A clear or reset never deletes activity-log entries younger than this many days."),
    Flag("audit.purge_days", "int", 0, 365, "locked",
         "Activity-log entries in the database older than this many days are deleted (0 = never; never sooner than audit.min_retention_days). The external audit sink is not touched. Only a signed policy can change it in the hardened profile."),
    Flag("integrity.forensic_copies", "int", 3, 10, "higher",
         "How many copies of a failed database are kept before an automatic restore replaces it."),
    Flag("integrity.before_clear_days", "int", 30, 14, "lower0",
         "Days the full copy taken before a clear or reset is kept (0 = never deleted). It is your way back, and a copy of the data."),
    Flag("test_mode.allowed", "bool", True, False, "false",
         "Debug mode and test data (copies of the database) may be used at all."),
    Flag("test_mode.forced", "bool", False, False, "false",
         "Test mode is forced on by root (launch flag --test-mode) and nobody can turn it off; the default super admin then signs in with a fixed lab password."),
    Flag("ota.require_emulation", "bool", False, True, "true",
         "TrustedInstaller qualification must boot the exact uploaded image in the pinned emulator (backend/emulator/manifest.json). "
         "Missing, unsupported, tampered, timed-out or failed emulation then blocks approval and every offer."),
    Flag("ota.enabled", "bool", True, True, "locked",
         "Over-the-air firmware updates exist at all (off with --no-ota): uploads, deployments and pushes are refused and devices are offered nothing."),
    Flag("features.disabled", "str", "", "", "set",
         "Comma-separated features switched off by root; administrators cannot switch them on (see the System page for the list)."),
    Flag("root.allow_access", "bool", True, True, "false",
         "Whether the separate root console may be opened (ssh, docker exec). TrustedInstaller switches it off inside a container: "
         "use the console attached to the container instead."),
    Flag("iips.enabled", "bool", True, True, "true",
         "imPress Integrity Protection Service: refuse to start when the program's own files changed since the last baseline."),
    Flag("iips.auto_accept_updates", "bool", True, False, "false",
         "When the program was updated (a different release or git commit than the one the baseline was made from), its "
         "new files become the reference by themselves instead of locking imPress. Files edited by hand under the same "
         "release still lock it. Off in the hardened profile: root accepts an update with --rehash."),
    Flag("iips.device_binding", "enum", "warn", "enforce", "order",
         "Bind the integrity reference to this machine (its hardware identity: not the address, system version or folder). "
         "Code or a reference copied to another machine is flagged: 'warn' alerts, 'enforce' locks imPress until root re-hashes "
         "there with root's password.", ("off", "warn", "enforce")),
    Flag("traffic.monitor", "bool", True, True, "true",
         "Watch request rates per endpoint, address and account and alert administrators to unusual traffic."),
    Flag("deadlock_prevention.enabled", "bool", True, True, "true",
         "If no active super admin exists, roll the database back and create a recovery account (global_deadlock_prevention)."),
    Flag("backups.restore_requires_approval", "bool", False, True, "true",
         "Restoring a backup needs a second super admin's approval (so only a super admin can request it)."),
    Flag("test_mode.export_allowed", "bool", True, False, "false",
         "Test-data copies may be exported as CSV files."),
    Flag("test_mode.pending_ttl_hours", "int", 168, 24, "lower0",
         "Hours a finished test database waits for a decision before it is deleted (0 = never)."),
    Flag("test_mode.dataset_ttl_days", "int", 0, 30, "lower0",
         "Days a saved test dataset is kept (0 = never)."),
    Flag("code.verify_manifest", "enum", "warn", "enforce", "order",
         "Check the server's own files against the root-signed MANIFEST.json at start-up.",
         ("off", "warn", "enforce")),
    Flag("device.https_required", "bool", False, True, "true",
         "Gateways and hubs must use HTTPS/WSS (same effect as IMPRESS_DEVICE_HTTPS_ONLY)."),
    Flag("device.keys_required", "bool", False, True, "true",
         "The shared device key may only enrol; every device must use its own key (same as IMPRESS_DEVICE_KEYS_REQUIRED)."),
    Flag("firmware.signing_required", "bool", False, True, "true",
         "A site firmware signing key must be configured and unsigned images are never accepted."),
]}


# Feature flags are launch choices a person may edit by hand (impress.flags.json) or change for a session (`flags set`).
# Everything else is policy: sealed, changed only through the console or the System page, and recorded.
FEATURE_SCOPE = ("test_mode.allowed", "test_mode.forced", "test_mode.export_allowed", "ota.enabled", "features.disabled",
                 "traffic.monitor")
SUPER_EDITABLE = ("integrity.forensic_copies", "integrity.before_clear_days", "test_mode.pending_ttl_hours",
                  "test_mode.dataset_ttl_days")
FLAGS = {n: (replace(f, scope="feature") if n in FEATURE_SCOPE else
             replace(f, editable_by="super admin") if n in SUPER_EDITABLE else f) for n, f in FLAGS.items()}


def _order(flag: Flag, value) -> float:
    if flag.kind == "enum":
        return flag.choices.index(value)
    if flag.safe == "lower0":                      # 0 means 'never expires': the least safe
        return float("-inf") if value == 0 else -value
    if flag.safe == "lower":
        return -value
    if flag.safe in ("true", "higher"):
        return int(value)
    if flag.safe == "false":
        return -int(value)
    raise KeyError(flag.name)


def at_least_as_safe(flag: Flag, new, base) -> bool:
    """May an unsigned override change `base` to `new` in the hardened profile?"""
    if flag.safe == "locked":                      # neither safer nor looser: only root's signed file may change it
        return new == base
    if flag.safe == "set":                         # text: fill in an empty value, never replace one
        return base == "" or new == base
    return _order(flag, new) >= _order(flag, base)


def coerce(flag: Flag, raw):
    """A typed value from JSON or from an inline 'name=value' string."""
    try:
        if flag.kind == "bool":
            if isinstance(raw, bool):
                return raw
            if str(raw).lower() in ("true", "1", "yes", "on"):
                return True
            if str(raw).lower() in ("false", "0", "no", "off"):
                return False
            raise ValueError
        if flag.kind == "int":
            if isinstance(raw, bool):
                raise ValueError
            value = int(raw)
            if value < 0:
                raise ValueError
            return value
        if flag.kind == "enum":
            if raw not in flag.choices:
                raise ValueError
            return raw
        if not isinstance(raw, str):
            raise ValueError
        return raw
    except (TypeError, ValueError):
        want = {"bool": "true or false", "int": "a whole number, 0 or more", "enum": " / ".join(flag.choices),
                "str": "text"}[flag.kind]
        raise PolicyError(f"{flag.name}: {raw!r} is not valid, expected {want}") from None


@dataclass
class Policy:
    profile: str = "standard"
    values: dict = field(default_factory=lambda: {f.name: f.standard for f in FLAGS.values()})
    sources: dict = field(default_factory=lambda: {f.name: "default" for f in FLAGS.values()})
    file: dict = field(default_factory=dict)       # serial, issued_at, key_id of the applied signed file
    problems: list = field(default_factory=list)   # a signed file that was refused (standard profile only)
    meta: dict = field(default_factory=dict)       # per flag: who set it, when, who enforces it since when
    notices: list = field(default_factory=list)    # events to record once the database is up (a reset store, ...)

    def sources_explicit(self) -> list:
        return [n for n, s in self.sources.items() if s != "default"]


_current = Policy()
_file_stamp: tuple | None = None


# ── Signed file ────────────────────────────────────────────────────────

def canonical(doc: dict) -> bytes:
    body = {k: v for k, v in doc.items() if k != "signature"}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode()


def load_public_key(path: Path) -> bytes:
    try:
        key = base64.b64decode(path.read_text().strip(), validate=True)
    except (OSError, ValueError):
        raise PolicyError(f"root public key {path} is missing or unreadable") from None
    if len(key) != 32:
        raise PolicyError(f"root public key {path} must be 32 bytes (base64)")
    return key


def check_signed_file(path: Path, public_path: Path, last_serial: int) -> dict:
    """The verified document, or PolicyError."""
    try:
        doc = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise PolicyError(f"{path.name} is unreadable: {exc}") from None
    if not isinstance(doc, dict) or doc.get("version") != 1:
        raise PolicyError(f"{path.name}: unsupported version")
    pub = load_public_key(public_path)
    if doc.get("key_id") != ed25519.key_id(pub):
        raise PolicyError(f"{path.name} was signed with a different key than {public_path.name}")
    try:
        sig = base64.b64decode(doc.get("signature", ""), validate=True)
    except ValueError:
        sig = b""
    if not ed25519.verify(pub, canonical(doc), sig):
        raise PolicyError(f"{path.name}: the signature does not verify (file edited, or signed with another key)")
    serial = doc.get("serial")
    if not isinstance(serial, int) or isinstance(serial, bool) or serial < 1:
        raise PolicyError(f"{path.name}: the serial must be a whole number, 1 or more")
    if serial < last_serial:
        raise PolicyError(f"{path.name}: serial {serial} is older than the last one applied ({last_serial}): rollback refused")
    if doc.get("profile") not in PROFILES:
        raise PolicyError(f"{path.name}: profile must be one of {', '.join(PROFILES)}")
    flags = doc.get("flags")
    if not isinstance(flags, dict):
        raise PolicyError(f"{path.name}: flags must be an object")
    for name, raw in flags.items():
        if name not in FLAGS:
            raise PolicyError(f"{path.name}: unknown flag {name}")
        coerce(FLAGS[name], raw)
    return doc


def sign_document(seed: bytes, profile: str, flags: dict, serial: int, issued_at: str) -> dict:
    """What `scripts/gpc.py sign` writes: the policy plus root's signature."""
    doc = {"version": 1, "profile": profile, "serial": serial, "issued_at": issued_at, "flags": flags,
           "key_id": ed25519.key_id(ed25519.public_key(seed))}
    doc["signature"] = base64.b64encode(ed25519.sign(seed, canonical(doc))).decode()
    return doc


def parse_inline(text: str) -> dict:
    out = {}
    for part in (text or "").split(","):
        part = part.strip()
        if not part:
            continue
        name, sep, raw = part.partition("=")
        name = name.strip()
        if not sep or name not in FLAGS:
            raise PolicyError(f"IMPRESS_GPC: unknown flag or missing '=' in {part!r} (flags: see docs/design/gpc.md)")
        out[name] = coerce(FLAGS[name], raw.strip())
    return out


# ── Loading ───────────────────────────────────────────────────────────────

def _meta(by: str, at, rank: str = "", via: str = "") -> dict:
    return {"set_by": by, "set_at": at, "enforced_by": by, "enforced_at": at, "authority": rank, "via": via}


def build(profile_env: str, inline: str, file_doc: dict | None, file_error: str | None,
          store: dict | None = None, session: dict | None = None, booted_at: str | None = None) -> Policy:
    if profile_env not in PROFILES:
        raise PolicyError(f"IMPRESS_PROFILE must be one of {', '.join(PROFILES)}, not {profile_env!r}")
    if file_error and profile_env == "hardened":
        raise PolicyError(f"the hardened profile will not start with an invalid policy file: {file_error}")
    pol = Policy(profile=(file_doc or {}).get("profile", profile_env))
    if file_error:
        pol.problems.append(file_error)
    use = "hardened" if pol.profile == "hardened" else "standard"
    for f in FLAGS.values():
        pol.values[f.name] = f.hardened if use == "hardened" else f.standard
        pol.sources[f.name] = "default"
    from .timeutil import istnow
    booted = booted_at or istnow().isoformat(timespec="seconds")
    for name in FLAGS:
        pol.meta[name] = _meta("built-in default (" + use + " profile)", None)
    for name, e in ((store or {}).get("flags") or {}).items():              # the sealed store: set from the console or the web
        flag = FLAGS.get(name)
        if flag is None or flag.scope != "policy":
            continue
        value = coerce(flag, e["value"])
        if pol.profile == "hardened" and not at_least_as_safe(flag, value, pol.values[name]):
            pol.problems.append(f"The stored value of {name} would loosen the hardened profile and was ignored.")
            continue
        pol.values[name], pol.sources[name] = value, "policy store"
        pol.meta[name] = {"set_by": e["set_by"], "set_at": e["set_at"], "authority": RANK_LABEL.get(e["set_rank"], ""),
                          "via": e.get("set_via", ""), "enforced_by": e.get("enforced_by", e["set_by"]),
                          "enforced_at": e.get("enforced_at", e["set_at"]), "note": e.get("note", "")}
    if file_doc:
        for name, raw in file_doc["flags"].items():
            pol.values[name] = coerce(FLAGS[name], raw)
            pol.sources[name] = "file"
            pol.meta[name] = _meta(f"root-signed policy file (serial {file_doc.get('serial')})", file_doc.get("issued_at"), "root", "signed file")
            pol.meta[name]["enforced_at"] = booted
        pol.file = {k: file_doc.get(k) for k in ("serial", "issued_at", "key_id")}
    for name, value in parse_inline(inline).items():
        if pol.profile == "hardened" and not at_least_as_safe(FLAGS[name], value, pol.values[name]):
            raise PolicyError(f"IMPRESS_GPC would loosen {name} in the hardened profile; "
                              "only a root-signed policy file may do that (scripts/gpc.py)")
        pol.values[name] = value
        pol.sources[name] = "inline"
        pol.meta[name] = _meta("launch flags (flags file, environment or command line)", booted, "root", "launch")
    for name, raw in (session or {}).items():                                # `flags set`: this run only
        flag = FLAGS.get(name)
        if flag is None or flag.scope != "feature":
            continue
        pol.values[name] = coerce(flag, raw)
        pol.sources[name] = "session"
        pol.meta[name] = _meta("root (`flags set`, this session only)", booted, "root", "console")
    conflicts = find_conflicts(pol.values, pol.profile, set(pol.sources_explicit()))
    if conflicts:
        raise PolicyConflict(conflicts)
    return pol


RANK_LABEL = {1: "administrator", 2: "super admin", 3: "root", 4: "TrustedInstaller"}


def _paths(settings) -> tuple[Path, Path]:
    return (Path(settings.GPC_FILE or "global_policy_control.json"),
            Path(settings.ROOT_PUBLIC_KEY or "root_public.key"))


def _last_serial() -> int:
    from .services import integrity
    return int((integrity.read_state().get("gpc") or {}).get("serial", 0))


def _remember_serial(serial: int, key_id: str) -> None:
    from .services import integrity
    integrity.write_state(gpc={"serial": serial, "key_id": key_id})


def load(settings) -> Policy:
    """Compute the policy from the settings and the signed file, and make it
    the current one. Raises PolicyError if it can't be applied."""
    global _current, _file_stamp
    path, public = _paths(settings)
    doc = err = None
    if path.exists():
        try:
            doc = check_signed_file(path, public, _last_serial())
        except PolicyError as exc:
            err = str(exc)
    from . import gpcstore
    store, notice = gpcstore.load()
    _file_stamp = (_stamp(path), gpcstore.stamp())               # after load(): creating the store is not a change
    pol = build(settings.PROFILE, settings.GPC, doc, err, store=store, session=gpcstore.session_read(), booted_at=_booted_at())
    if notice:
        pol.notices.append({"action": "system.policy_store_reset", "message": notice})
    if doc and doc["serial"] > _last_serial():
        _remember_serial(doc["serial"], doc["key_id"])
    _current = pol
    return pol


def _stamp(path: Path):
    try:
        st = path.stat()
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return None


_booted: str | None = None


def _booted_at() -> str:
    """When this server run began: what `enforced_at` says for flags that came from the launch."""
    global _booted
    if _booted is None:
        from .timeutil import istnow
        _booted = istnow().isoformat(timespec="seconds")
    return _booted


def changed_on_disk(settings) -> bool:
    from . import gpcstore
    return (_stamp(_paths(settings)[0]), gpcstore.stamp()) != _file_stamp


def reload_if_changed(settings) -> tuple[bool, str | None]:
    """(reloaded, error). A new file that fails verification never replaces a
    policy that was applied cleanly: the defaults can be looser than what root
    signed before, so the last good policy stays in force."""
    global _file_stamp
    if not changed_on_disk(settings):
        return False, None
    previous = _current
    try:
        fresh = load(settings)
        error = fresh.problems[0] if fresh.problems and not previous.problems else None
    except PolicyError as exc:
        error = str(exc)
    if error:
        _set(previous)
        from . import gpcstore
        _file_stamp = (_stamp(_paths(settings)[0]), gpcstore.stamp())
        return False, error
    return True, None


def _set(pol: Policy) -> None:
    global _current
    _current = pol


def reset_for_tests() -> None:
    global _current, _file_stamp
    _current, _file_stamp = Policy(), None


# ── Reading ───────────────────────────────────────────────────────────────

def get(name: str):
    return _current.values[name]


def profile() -> str:
    return _current.profile


def take_notices() -> list:
    """Events waiting to be written to the activity log and shown as alerts (a reset policy store, ...)."""
    out, _current.notices[:] = list(_current.notices), []
    return out


def current() -> Policy:
    return _current


def _restrictions() -> dict:
    from . import gpcstore
    return gpcstore.restrictions()


def describe() -> dict:
    p = _current
    return {"profile": p.profile, "file": p.file or None, "problems": list(p.problems),
            "restrictions": _restrictions(),
            "flags": [{"name": f.name, "value": p.values[f.name], "source": p.sources[f.name],
                       "standard": f.standard, "hardened": f.hardened, "description": f.doc, "scope": f.scope,
                       "editable_by": f.editable_by if f.scope == "policy" else "flags file or `flags set`",
                       **{k: v for k, v in p.meta.get(f.name, {}).items()}}
                      for f in FLAGS.values()]}


def device_https_only(settings) -> bool:
    return bool(settings.DEVICE_HTTPS_ONLY or get("device.https_required"))


def device_keys_required(settings) -> bool:
    return bool(settings.DEVICE_KEYS_REQUIRED or get("device.keys_required"))


# ── The hardened floor ───────────────────────────────────────────────────

def hardened_problems(settings) -> list[str]:
    """What is below the hardened floor. Empty in the standard profile."""
    if profile() != "hardened":
        return []
    from .config import insecure_settings
    out = []
    if settings.DEBUG:
        out.append("IMPRESS_DEBUG must be off")
    if insecure_settings(settings):
        out.append("the default secrets must be replaced: " + ", ".join(insecure_settings(settings)))
    if settings.REQUIRE_HTTPS is False:
        out.append("IMPRESS_REQUIRE_HTTPS must not be false")
    if not settings.WS_REQUIRE_AUTH:
        out.append("IMPRESS_WS_REQUIRE_AUTH must be true")
    if not settings.SINGLE_SESSION:
        out.append("IMPRESS_SINGLE_SESSION must be true")
    if settings.FIRMWARE_ALLOW_UNSIGNED:
        out.append("IMPRESS_FIRMWARE_ALLOW_UNSIGNED must be off")
    if settings.FIRMWARE_SINGLE_APPROVER:
        out.append("IMPRESS_FIRMWARE_SINGLE_APPROVER must be off (upload and approval by different administrators)")
    if get("firmware.signing_required") and not settings.FIRMWARE_SIGNING_KEY:
        out.append("IMPRESS_FIRMWARE_SIGNING_KEY must name the site's firmware signing public key")
    if not (get("audit.sink_path") or get("audit.sink_url")):
        out.append("an external audit sink must be set (flag audit.sink_path or audit.sink_url)")
    if get("code.verify_manifest") != "off" and not _paths(settings)[1].exists():
        out.append(f"the root public key {_paths(settings)[1]} is needed to verify the code manifest")
    return out


def enforce_startup(settings) -> None:
    problems = hardened_problems(settings)
    if problems:
        raise RuntimeError("Refusing to start in the hardened profile:\n  - " + "\n  - ".join(problems)
                           + "\nFix these, or run the standard profile (IMPRESS_PROFILE=standard).")
