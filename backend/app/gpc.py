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
from dataclasses import dataclass, field
from pathlib import Path

from . import ed25519

log = logging.getLogger(__name__)

PROFILES = ("standard", "hardened")


class PolicyError(RuntimeError):
    """The policy could not be loaded as written: never half-applied."""


@dataclass(frozen=True)
class Flag:
    name: str
    kind: str                      # bool | int | str | enum
    standard: object
    hardened: object
    safe: str                      # true | false | higher | lower | lower0 | order | set
    doc: str
    choices: tuple = ()


FLAGS: dict[str, Flag] = {f.name: f for f in [
    Flag("dual_control.enabled", "bool", True, True, "true",
         "Destructive or baseline-changing actions (accepting the current database state, clearing data) need a second super admin's approval."),
    Flag("dual_control.single_operator_ok", "bool", True, False, "false",
         "Allow the requester to approve their own action when they are the only active super admin."),
    Flag("dual_control.delay_minutes", "int", 0, 15, "higher",
         "Minutes between an approval and the earliest moment the action may run."),
    Flag("dual_control.expiry_minutes", "int", 60, 30, "lower",
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

def build(profile_env: str, inline: str, file_doc: dict | None, file_error: str | None) -> Policy:
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
    if file_doc:
        for name, raw in file_doc["flags"].items():
            pol.values[name] = coerce(FLAGS[name], raw)
            pol.sources[name] = "file"
        pol.file = {k: file_doc.get(k) for k in ("serial", "issued_at", "key_id")}
    for name, value in parse_inline(inline).items():
        if pol.profile == "hardened" and not at_least_as_safe(FLAGS[name], value, pol.values[name]):
            raise PolicyError(f"IMPRESS_GPC would loosen {name} in the hardened profile; "
                              "only a root-signed policy file may do that (scripts/gpc.py)")
        pol.values[name] = value
        pol.sources[name] = "inline"
    return pol


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
    _file_stamp = _stamp(path)
    pol = build(settings.PROFILE, settings.GPC, doc, err)
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


def changed_on_disk(settings) -> bool:
    return _stamp(_paths(settings)[0]) != _file_stamp


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
        _file_stamp = _stamp(_paths(settings)[0])
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


def current() -> Policy:
    return _current


def describe() -> dict:
    p = _current
    return {"profile": p.profile, "file": p.file or None, "problems": list(p.problems),
            "flags": [{"name": f.name, "value": p.values[f.name], "source": p.sources[f.name],
                       "standard": f.standard, "hardened": f.hardened, "description": f.doc}
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
