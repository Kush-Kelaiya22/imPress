"""Signatures the server produces and checks (v2.2), all Ed25519.

* **Code manifest** (root signs, the server verifies at start-up): MANIFEST.json
  lists the SHA-256 of every file under backend/app; MANIFEST.sig is root's
  signature over it. A changed, added or removed file is found before the
  server serves a request. See scripts/gpc.py manifest.
* **Signed exports** (the server signs, the receiver verifies): an export zip
  carries SIGNATURE.json with the hash of every file in it and a signature by
  the install's export key (generated on first use, 0600, public half at
  GET /api/system/signing-key). scripts/verify_export.py checks a zip offline.

Device messages are not signed or changed here: the firmware and its wire
protocols are out of scope for this module.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

from . import ed25519
from .timeutil import istnow

MANIFEST = "MANIFEST.json"
MANIFEST_SIG = "MANIFEST.sig"
_SKIP_DIRS = {"__pycache__"}
_SKIP_FILES = {MANIFEST, MANIFEST_SIG, ".DS_Store"}


def app_dir() -> Path:
    return Path(__file__).resolve().parent


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(root: Path) -> dict[str, str]:
    files = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name in _SKIP_FILES or p.suffix == ".pyc" or _SKIP_DIRS & set(p.relative_to(root).parts):
            continue
        files[p.relative_to(root).as_posix()] = _sha(p)
    return files


def _canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def build_manifest(root: Path | None = None, version: str = "") -> dict:
    root = root or app_dir()
    return {"version": 1, "app_version": version, "created": istnow().isoformat(), "files": collect(root)}


def write_manifest(seed: bytes, root: Path | None = None, version: str = "") -> dict:
    """Root's command: write MANIFEST.json and MANIFEST.sig next to the code."""
    root = root or app_dir()
    manifest = build_manifest(root, version)
    body = _canonical(manifest)
    (root / MANIFEST).write_bytes(body)
    sig = ed25519.sign(seed, body)
    (root / MANIFEST_SIG).write_text(base64.b64encode(sig).decode() + "\n")
    return manifest


def verify_manifest(public: bytes, root: Path | None = None) -> list[str]:
    """Problems found, empty when the files are exactly what root signed."""
    root = root or app_dir()
    try:
        body = (root / MANIFEST).read_bytes()
        sig = base64.b64decode((root / MANIFEST_SIG).read_text().strip(), validate=True)
    except (OSError, ValueError):
        return ["the code manifest or its signature is missing or unreadable"]
    if not ed25519.verify(public, body, sig):
        return ["the manifest's signature does not verify (edited, or signed with another key)"]
    try:
        want = json.loads(body)["files"]
    except (ValueError, KeyError, TypeError):
        return ["the manifest is not valid"]
    have = collect(root)
    problems = [f"changed: {p}" for p in sorted(want) if p in have and have[p] != want[p]]
    problems += [f"missing: {p}" for p in sorted(want) if p not in have]
    problems += [f"not in the manifest: {p}" for p in sorted(have) if p not in want]
    return problems


def verify_manifest_if_present() -> dict:
    """For the System page: {"present": bool, "problems": [...]} against root's public key."""
    from . import gpc
    from .config import settings
    root = app_dir()
    if not (root / MANIFEST).exists():
        return {"present": False, "problems": []}
    try:
        public = gpc.load_public_key(gpc._paths(settings)[1])
    except gpc.PolicyError as exc:
        return {"present": True, "problems": [str(exc)]}
    return {"present": True, "problems": verify_manifest(public, root)}


# ── Signed exports ───────────────────────────────────────────────────────

def _key_path() -> Path:
    from .services import integrity
    return integrity.state_file().parent / "export_signing.key"


def _export_seed() -> bytes:
    path = _key_path()
    try:
        return base64.b64decode(path.read_text().strip(), validate=True)
    except (OSError, ValueError):
        seed = ed25519.generate_seed()
        tmp = path.with_suffix(".tmp")
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(base64.b64encode(seed).decode() + "\n")
        os.replace(tmp, path)
        return seed


def export_public_key() -> dict:
    pub = ed25519.public_key(_export_seed())
    return {"alg": "ed25519", "public_key": base64.b64encode(pub).decode(), "key_id": ed25519.key_id(pub)}


def sign_files(files: dict[str, bytes]) -> bytes:
    """SIGNATURE.json for a set of files (name -> content)."""
    seed = _export_seed()
    doc = {"version": 1, "alg": "ed25519", "key_id": ed25519.key_id(ed25519.public_key(seed)),
           "created": istnow().isoformat(),
           "files": {n: hashlib.sha256(b).hexdigest() for n, b in sorted(files.items())}}
    doc["signature"] = base64.b64encode(ed25519.sign(seed, _canonical(doc))).decode()
    return json.dumps(doc, indent=2).encode()


def verify_files(signature_json: bytes, files: dict[str, bytes], public: bytes) -> list[str]:
    """Problems with an export (empty = it is exactly what the key's owner signed)."""
    try:
        doc = json.loads(signature_json)
        sig = base64.b64decode(doc.pop("signature"), validate=True)
    except (ValueError, KeyError, TypeError):
        return ["SIGNATURE.json is missing or not valid"]
    if not ed25519.verify(public, _canonical(doc), sig):
        return ["the signature does not verify (edited, or another key)"]
    want = doc.get("files", {})
    problems = [f"changed: {n}" for n, b in files.items() if n in want and hashlib.sha256(b).hexdigest() != want[n]]
    problems += [f"missing: {n}" for n in want if n not in files]
    problems += [f"not signed: {n}" for n in files if n not in want]
    return problems
