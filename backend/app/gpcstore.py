"""The sealed policy store (v2.2): `backend/impress.gpc.json`, and the session overlay of feature flags.

Global policy control (docs/design/gpc.md) has three sources of values below a root-signed file: the built-in defaults, **this
store**, and the launch flags. The store is where a change made while the system runs is kept, so it survives a restart and
carries its own history. It works like the database: every write goes through this module, and the whole document is sealed
with an HMAC under a key only this server holds (derived from IMPRESS_JWT_SECRET). **Editing the file by hand breaks the
seal**: the next load sets the edited copy aside (`impress.gpc.json.tampered-<time>`), restores the defaults, raises an alert and
records the event in the new store's history. To change a flag use the console (`policy set`, root's password) or, for the few
operational flags, the System page (a super admin, with step-up). Nobody else can: administrators and faculty never.

Each flag changed from its default keeps: the value, **who** set it and at which authority, **how** (console, web, system),
**when**, a note, and **who enforces it since when** (`enforced_by`, `enforced_at`). The history is a hash chain: every entry
carries the hash of the one before it.

Feature flags (test mode, OTA, features.disabled, traffic monitor) are not policy: they live in `impress.flags.json`, which a
person may edit by hand. `session_*` below keep what `flags set` changed for this run only, in `impress.session.flags.json`; the
server removes that file when it starts.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
ADMIN, SUPER, ROOT, TRUSTED = 1, 2, 3, 4
RANK_NAME = {ADMIN: "administrator", SUPER: "super admin", ROOT: "root", TRUSTED: "TrustedInstaller"}
HISTORY_LIMIT = 500


class PolicyRefused(Exception):
    """A change the rules do not allow; carries the catalogue code and an HTTP status."""

    def __init__(self, code: str, message: str, status: int = 403):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status


def store_path() -> Path:
    return Path(os.environ.get("IMPRESS_GPC_STORE") or BACKEND_DIR / "impress.gpc.json")


def session_path() -> Path:
    return Path(os.environ.get("IMPRESS_SESSION_FLAGS") or BACKEND_DIR / "impress.session.flags.json")


def _now() -> str:
    from .timeutil import istnow
    return istnow().isoformat(timespec="seconds")


def _key() -> bytes:
    from .config import settings
    return hashlib.sha256(b"impress.gpc-store\0" + settings.JWT_SECRET.encode()).digest()


def _canon(doc: dict) -> bytes:
    return json.dumps({k: v for k, v in doc.items() if k != "seal"}, sort_keys=True, separators=(",", ":")).encode()


def _seal(doc: dict) -> str:
    return hmac.new(_key(), _canon(doc), hashlib.sha256).hexdigest()


def _link(prev: str, entry: dict) -> str:
    body = json.dumps({k: v for k, v in entry.items() if k != "hash"}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((prev + body).encode()).hexdigest()


def restrictions() -> dict:
    """Who may change what, in words (shown on the System page and in `policy show`)."""
    return {"administrator": "cannot change policy", "faculty": "cannot change policy",
            "super admin": "may change only the operational flags (editable_by = super admin), with their password and second factor",
            "root": "may change any policy flag in the console, with root's password",
            "TrustedInstaller": "turns protections on when the host needs them",
            "direct edits": "not allowed: an edited file fails its seal and is reset to the defaults"}


def _fresh(reason: str = "") -> dict:
    doc = {"version": 1, "created_at": _now(), "resets": 0, "flags": {}, "history": [], "restrictions": restrictions()}
    if reason:
        _append(doc, "*", "(edited file)", "defaults", "system", TRUSTED, "integrity check", reason)
        doc["resets"] = 1
    return doc


def _append(doc: dict, flag: str, old, new, by: str, rank: int, via: str, note: str) -> dict:
    prev = doc["history"][-1]["hash"] if doc["history"] else ""
    entry = {"seq": (doc["history"][-1]["seq"] + 1) if doc["history"] else 1, "at": _now(), "flag": flag,
             "old": old, "new": new, "by": by, "rank": RANK_NAME.get(rank, str(rank)), "via": via, "note": note, "prev": prev}
    entry["hash"] = _link(prev, entry)
    doc["history"].append(entry)
    del doc["history"][:-HISTORY_LIMIT]
    return entry


def _write(doc: dict) -> None:
    doc["seal"] = _seal(doc)
    path = store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{os.urandom(3).hex()}.tmp")       # two writers never share one
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)


def _chain_ok(doc: dict) -> bool:
    prev = None                                    # the oldest kept entry may point at one that was trimmed away
    for e in doc.get("history", []):
        if prev is not None and e.get("prev") != prev:
            return False
        if e.get("hash") != _link(e.get("prev", ""), e):
            return False
        prev = e["hash"]
    return True


def load() -> tuple[dict, str | None]:
    """(the verified store, a notice when it had to be reset). A missing file is created; an edited one is set aside."""
    path = store_path()
    if not path.exists():
        doc = _fresh()
        try:
            _write(doc)
        except OSError:
            pass                                   # a read-only install keeps the defaults in memory
        return doc, None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        ok = (isinstance(doc, dict) and isinstance(doc.get("flags"), dict) and isinstance(doc.get("history"), list)
              and hmac.compare_digest(str(doc.get("seal", "")), _seal(doc)) and _chain_ok(doc))
    except (OSError, ValueError):
        ok = False
    if ok:
        return doc, None
    aside = path.with_name(f"{path.name}.tampered-{time.strftime('%Y%m%d-%H%M%S')}")
    try:
        os.replace(path, aside)
        kept = f"The edited file was kept as {aside.name}."
    except OSError:
        kept = "The edited file could not be kept."
    reason = f"The policy store {path.name} did not verify: it was edited outside imPress. {kept} The defaults were restored."
    doc = _fresh(reason)
    try:
        _write(doc)
    except OSError:
        pass
    return doc, reason


def read() -> dict:
    return load()[0]


def history(flag: str | None = None, limit: int = 50) -> list[dict]:
    rows = [e for e in read()["history"] if flag in (None, e["flag"])]
    return list(reversed(rows))[:limit]


def set_flag(name: str, raw, actor: str, rank: int, via: str, note: str = "") -> dict:
    """Change one policy flag, with every rule applied. Returns the store entry. Raises PolicyRefused."""
    from . import gpc
    flag = gpc.FLAGS.get(name)
    if flag is None:
        raise PolicyRefused("POLICY_UNKNOWN_FLAG", f"There is no policy flag called {name}.", 422)
    if flag.scope != "policy":
        raise PolicyRefused("POLICY_UNKNOWN_FLAG", f"{name} is a feature flag: change it with `flags set` (this session) or in "
                            "impress.flags.json, not in the policy store.", 422)
    try:
        value = gpc.coerce(flag, raw)
    except gpc.PolicyError as exc:
        raise PolicyRefused("POLICY_BAD_VALUE", str(exc), 422) from None
    needed = SUPER if flag.editable_by == "super admin" else ROOT
    if rank < needed:
        who = "root, in the console" if needed == ROOT else "a super admin or root"
        raise PolicyRefused("POLICY_FORBIDDEN", f"{name} can be changed only by {who}. A {RANK_NAME.get(rank, 'person')} cannot.")
    doc = read()
    cur = doc["flags"].get(name)
    if cur and cur["set_rank"] > rank:
        raise PolicyRefused("POLICY_FORBIDDEN", f"{name} was set by {cur['set_by']} ({RANK_NAME.get(cur['set_rank'])}); "
                            "only someone with that authority or more can change it.")
    pol = gpc.current()
    if pol.profile == "hardened" and not gpc.at_least_as_safe(flag, value, flag.hardened):
        raise PolicyRefused("POLICY_LOOSENING", f"{name}={value!r} would loosen the hardened profile; only a root-signed policy "
                            "file may do that (scripts/gpc.py).")
    trial = dict(pol.values)
    trial[name] = value
    found = gpc.find_conflicts(trial, pol.profile, set(pol.sources_explicit()) | {name})
    if found:
        raise PolicyRefused("POLICY_CONFLICT", "That would make flags conflict: " + " | ".join(c.text() for c in found), 409)
    old = pol.values.get(name)
    entry = {"value": value, "set_by": actor, "set_rank": rank, "set_via": via, "set_at": _now(), "note": note,
             "enforced_by": f"{actor} ({via})", "enforced_at": _now(), "min_rank": needed}
    doc["flags"][name] = entry
    _append(doc, name, old, value, actor, rank, via, note)
    _write(doc)
    return entry


def reset_flags(names: list[str] | None, actor: str, rank: int, via: str, note: str = "") -> list[str]:
    """Return flags to their defaults (all of them when `names` is None). Same authority rules as setting."""
    from . import gpc
    doc = read()
    chosen = list(doc["flags"]) if names is None else names
    for n in chosen:
        if n not in gpc.FLAGS:
            raise PolicyRefused("POLICY_UNKNOWN_FLAG", f"There is no policy flag called {n}.", 422)
        cur = doc["flags"].get(n)
        needed = SUPER if gpc.FLAGS[n].editable_by == "super admin" else ROOT
        if cur and (rank < needed or cur["set_rank"] > rank):
            raise PolicyRefused("POLICY_FORBIDDEN", f"{n} can be reset only by {RANK_NAME[max(needed, cur['set_rank'])]} or more.")
    done = []
    for n in chosen:
        if n in doc["flags"]:
            old = doc["flags"].pop(n)["value"]
            _append(doc, n, old, "default", actor, rank, via, note)
            done.append(n)
    if done:
        _write(doc)
    return done


# ── feature flags for this session only ─────────────────────────────────

def session_read() -> dict:
    try:
        d = json.loads(session_path().read_text(encoding="utf-8"))
        return d.get("flags", {}) if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def session_write(flags: dict, actor: str) -> None:
    path = session_path()
    if not flags:
        path.unlink(missing_ok=True)
        return
    path.write_text(json.dumps({"flags": flags, "set_by": actor, "set_at": _now(),
                                "about": "Feature flags changed for this run only; removed when the server starts."}, indent=2),
                    encoding="utf-8")


def session_clear() -> None:
    session_path().unlink(missing_ok=True)


def stamp() -> tuple:
    """Changes on disk that need a reload: the store and the session overlay."""
    out = []
    for p in (store_path(), session_path()):
        try:
            st = p.stat()
            out.append((st.st_mtime_ns, st.st_size))
        except OSError:
            out.append(None)
    return tuple(out)
