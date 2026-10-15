"""imPress Integrity Protection Service (IIPS, v2.2): the program's own files are checked at every start.

The first start records a **baseline**: a hash of every file of the program, a hash for every folder (made from the
names and hashes inside it, so moving a folder or file to another place changes it) and a hash of the whole tree.
The baseline sits next to the database and is signed with a key derived from the server's secret, so editing it by
hand does not make a changed file pass. At every later start the files are hashed again; any difference (a file
changed, added, removed or moved) disables imPress until root decides: `--rehash` accepts the files as they are now,
`--bypass-iips` starts anyway and shows a warning on every page.

Not covered: things that are expected to change while the system runs (the database, which has its own seals and
backups; logs, state and test data; caches; uploaded firmware; the virtual environment and git's own folder).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path

from ..config import settings

ROOT = Path(__file__).resolve().parents[3]
COVERED = ("backend/app", "scripts", "VERSION", "launcher.sh", "launcher.bat", "console.bat", "backend/requirements.txt")
SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules", ".pytest_cache", ".ruff_cache", "backups", "test-data",
             "firmware_bins", "data", "logs", "graphify-out"}
SKIP_SUFFIX = (".pyc", ".pyo", ".db", ".sqlite", ".sqlite3", ".db-wal", ".db-shm", ".log")
SKIP_NAMES = {".env", "RELEASE", ".DS_Store", ".impress-write-test"}
SKIP_PATTERNS = (" 2.",)                    # duplicates a file-sync tool leaves behind are not the program

_state: dict = {"status": "unchecked", "changes": [], "enabled": True, "baseline_created": False}


def state() -> dict:
    return _state


def shipped_path(root: Path = ROOT) -> Path:
    """A baseline made when the program was built (the container image): read-only for the server's user, so it needs
    no seal and takes the place of the one next to the database."""
    return root / "IIPS-BASELINE.json"


def baseline_path() -> Path:
    url = settings.DATABASE_URL
    base = Path(url.split(":///", 1)[1]) if ":///" in url else Path.cwd() / "impress.db"
    return base.with_suffix(".iips.json")


def _key(device: str | None = None) -> bytes:
    """The sealing key: the site's secret and, when the reference is bound to a machine, that machine's fingerprint, so the
    reference verifies only on the machine it was made on (a copy elsewhere fails its seal, in a way we can recognise)."""
    base = hashlib.sha256(b"impress.iips\0" + settings.JWT_SECRET.encode()).digest()
    return hashlib.sha256(base + b"\0" + device.encode()).digest() if device else base


def _skip(p: Path) -> bool:
    return p.name in SKIP_NAMES or p.suffix in SKIP_SUFFIX or any(x in p.name for x in SKIP_PATTERNS)


def _files(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in COVERED:
        p = root / item
        if p.is_file():
            out[item] = hashlib.sha256(p.read_bytes()).hexdigest()
        elif p.is_dir():
            for dirpath, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for n in sorted(names):
                    f = Path(dirpath) / n
                    if f.is_file() and not _skip(f):
                        out[f.relative_to(root).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


def _tree(files: dict[str, str]) -> tuple[dict[str, str], str]:
    """Hash of every folder and of the whole tree, from names and hashes: a moved file or folder changes them."""
    parent = lambda d: d.rpartition("/")[0]                                  # noqa: E731
    items: dict[str, list[tuple[str, str]]] = {"": []}
    for rel, h in files.items():
        d = parent(rel)
        while d:
            items.setdefault(d, [])
            d = parent(d)
        items[parent(rel)].append((rel.rpartition("/")[2] + ":f", h))
    subdirs: dict[str, list[str]] = {}
    for d in items:
        if d:
            subdirs.setdefault(parent(d), []).append(d)
    folders: dict[str, str] = {}
    for d in sorted(items, key=lambda x: -(x.count("/") + 1 if x else 0)):   # deepest first
        entries = items[d] + [(c.rpartition("/")[2] + ":d", folders[c]) for c in subdirs.get(d, [])]
        folders[d] = hashlib.sha256("\n".join(f"{n}={h}" for n, h in sorted(entries)).encode()).hexdigest()
    return folders, folders[""]


def build_marker(root: Path = ROOT) -> str:
    """Which build of the program this is: the git commit of a checkout, else the release label. A change of marker is
    an update; files that differ under the SAME marker were edited by hand."""
    import subprocess
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=5)
        if out.returncode == 0 and out.stdout.strip():
            return "git:" + out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    from ..config import APP_RELEASE
    return "release:" + APP_RELEASE


def snapshot(root: Path = ROOT) -> dict:
    files = _files(root)
    folders, top = _tree(files)
    return {"version": 1, "files": files, "folders": folders, "root_hash": top,
            "structure_hash": hashlib.sha256("\n".join(sorted(files)).encode()).hexdigest()}


def _seal(doc: dict, device: str | None = None) -> str:
    return hmac.new(_key(device), json.dumps(doc, sort_keys=True).encode(), "sha256").hexdigest()


def write_baseline(root: Path = ROOT, binding: str = "off", previous: dict | None = None, by: str = "system",
                   reason: str = "") -> dict:
    """Record the program's files as the reference. With device binding the machine's fingerprint is part of the sealed
    document and of the key. `previous` (what was found before, from verify_baseline) goes into a hash-chained history, so
    the file says what was replaced, when, by whom and in what state it was."""
    from .. import fingerprint
    from ..timeutil import istnow
    doc = snapshot(root)
    doc["created_at"] = istnow().isoformat()
    doc["build"] = build_marker(root)
    fp, how = fingerprint.get() if binding != "off" else (None, "binding is off")
    doc["device"], doc["device_how"] = fp, how
    history = list((previous or {}).get("history", []))
    entry = {"at": doc["created_at"], "by": by, "reason": reason or "baseline written",
             "found": (previous or {}).get("found", "no reference before"),
             "replaced_tree": (previous or {}).get("root_hash", ""), "device": fingerprint.short(fp),
             "prev": history[-1]["hash"] if history else ""}
    entry["hash"] = hashlib.sha256((entry["prev"] + json.dumps(entry, sort_keys=True)).encode()).hexdigest()
    doc["history"] = (history + [entry])[-20:]
    path = baseline_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"baseline": doc, "seal": _seal(doc, fp)}, indent=1))
    return doc


def verify_baseline(binding: str = "off") -> dict:
    """What the reference file is, before anything is rewritten: {"found": missing | ok | edited | other_device | legacy,
    "baseline": the document when it can be trusted, "history", "root_hash"}. Never raises."""
    from .. import fingerprint
    path = baseline_path()
    if not path.exists():
        return {"found": "missing", "history": []}
    try:
        saved = json.loads(path.read_text())
        base, seal = saved["baseline"], saved["seal"]
    except (OSError, ValueError, KeyError):
        return {"found": "edited", "history": []}
    out = {"baseline": base, "history": base.get("history", []), "root_hash": base.get("root_hash", "")}
    fp, _ = fingerprint.get() if binding != "off" else (None, "")
    if binding != "off" and fp and hmac.compare_digest(seal, _seal(base, fp)) and base.get("device") == fp:
        return {**out, "found": "ok"}
    recorded = base.get("device")
    if recorded and hmac.compare_digest(seal, _seal(base, recorded)):
        # it is sealed for a device, and that is not this one (or binding is off now): copied, or moved to other hardware
        return {**out, "found": "other_device" if binding != "off" else "ok", "recorded_device": recorded}
    if hmac.compare_digest(seal, _seal(base)):
        return {**out, "found": "ok" if binding == "off" or not fp else "legacy"}          # made before device binding
    return {"found": "edited", "history": [], "root_hash": ""}


def compare(base: dict, now: dict) -> list[dict]:
    changes = []
    b, n = base["files"], now["files"]
    by_hash = {}
    for rel, h in b.items():
        by_hash.setdefault(h, []).append(rel)
    for rel in sorted(set(b) | set(n)):
        if rel in b and rel in n:
            if b[rel] != n[rel]:
                changes.append({"path": rel, "change": "changed"})
        elif rel in b:
            moved = [m for m in n if n[m] == b[rel] and m not in b]
            changes.append({"path": rel, "change": "moved" if moved else "removed", **({"to": moved[0]} if moved else {})})
        elif not any(c.get("to") == rel for c in changes) and n[rel] not in by_hash:
            changes.append({"path": rel, "change": "added"})
    if not changes and base["root_hash"] != now["root_hash"]:
        changes.append({"path": "(structure)", "change": "changed"})
    return changes


def check(enabled: bool = True, rehash: bool = False, root: Path = ROOT, auto_accept: bool = False,
          binding: str = "off") -> dict:
    """Run at start-up. Sets and returns the state: ok | baseline_created | violation | bypassed | rehashed | updated.
    `auto_accept` (policy iips.auto_accept_updates): a different build than the baseline's is an update, not tampering.
    `binding` (policy iips.device_binding: off | warn | enforce): the reference belongs to the machine it was made on.
    A rehash first looks at what is there (verify_baseline) and records it in the new reference's history."""
    from .. import fingerprint
    fp, how = fingerprint.get()
    _state.update(enabled=enabled, changes=[], baseline_created=False, device_warning="", device_mismatch=False,
                  device={"fingerprint": fingerprint.short(fp), "how": how, "binding": binding})
    if not enabled:
        _state["status"] = "bypassed"
        return _state
    path = baseline_path()
    if shipped_path(root).exists():
        base = json.loads(shipped_path(root).read_text())
        changes = compare(base, snapshot(root))
        _state.update(status="violation" if changes else "ok", changes=changes[:200], total_changes=len(changes),
                      note="This build carries its own reference (a container image): --rehash does not apply; rebuild the image." if rehash else "")
        return _state
    prior = verify_baseline(binding)
    found = prior["found"]
    if rehash or found == "missing":
        write_baseline(root, binding, prior if found != "missing" else None,
                       by="root (password verified)" if rehash else "system (first start)",
                       reason="rehash requested by root" if rehash else "first start")
        _state.update(status="rehashed" if rehash else "baseline_created", baseline_created=not rehash, replaced=found)
        return _state
    if found == "edited":
        _state.update(status="violation", changes=[{"path": path.name, "change": "edited: its seal does not verify"}])
        return _state
    base = prior["baseline"]
    if found == "other_device":
        msg = (f"{path.name} was made on another device ({fingerprint.short(prior.get('recorded_device'))}, this one is "
               f"{fingerprint.short(fp)}): the program or its reference was copied here")
        if binding == "enforce":
            _state.update(status="violation", device_mismatch=True, changes=[{"path": path.name, "change": "made on another device"}])
            return _state
        _state["device_warning"] = msg + " (policy iips.device_binding is 'warn': root's rehash makes this machine the owner)"
    changes = compare(base, snapshot(root))
    if changes and auto_accept and found != "other_device" and base.get("build") != build_marker(root):
        _state.update(status="updated", changes=changes[:200], total_changes=len(changes),
                      note=f"updated from {base.get('build', 'an older build')} to {build_marker(root)}")
        write_baseline(root, binding, prior, by="system (update)", reason="the program was updated")
        return _state
    if found == "legacy" and not changes:                         # made before device binding: bind it to this machine now
        write_baseline(root, binding, prior, by="system (binding)", reason="bound to this device")
    _state.update(status="violation" if changes else "ok", changes=changes[:200], total_changes=len(changes))
    return _state


def violation_message() -> str:
    if _state.get("device_mismatch"):
        return ("imPress has been disabled by Root: the program's reference was made on a different device, so this code or "
                "its reference was copied here (policy iips.device_binding is 'enforce'). Root accepts it on this machine with "
                "--rehash and root's password.")
    n = _state.get("total_changes") or len(_state["changes"])
    first = ", ".join(c["path"] for c in _state["changes"][:3])
    return (f"imPress has been disabled by Root: an integrity violation was detected in the source folder "
            f"({n} difference{'s' if n != 1 else ''}: {first}{'…' if n > 3 else ''}). "
            "Restore the original files, or start with --rehash to accept the current ones as the new reference "
            "(in the root screen: type  restart --rehash).")


def locked() -> bool:
    return _state["status"] == "violation"


if __name__ == "__main__":                 # python -m app.services.iips --write FILE   (the image build)
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--write":
        Path(sys.argv[2]).write_text(json.dumps(snapshot(), indent=1))
    else:
        sys.exit("usage: python -m app.services.iips --write FILE")
