"""An audit trail the database can't rewrite (v2.2).

Every activity-log entry is also appended, as one JSON line, to a file outside
the database (policy flag audit.sink_path) and, if audit.sink_url is set, sent
to that endpoint. The file is **hash-chained**: each line holds the SHA-256 of
the previous line's hash plus its own content, so an edited, removed, reordered
or truncated line is found by `python -m app.manage audit-verify FILE`.

A chain makes tampering *evident*; it does not make it impossible. For that the
file belongs on an append-only or write-once volume, or the URL on another
host that the application's administrators don't control (docs/design/data-integrity.md).
The webhook body carries an HMAC (key derived from the server secret) so the
receiver can check who sent it; delivery is best effort, in the background,
and never blocks or fails a request.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import threading
import urllib.request
from pathlib import Path

from .. import gpc
from ..config import settings
from ..timeutil import istnow

log = logging.getLogger(__name__)

GENESIS = "0" * 64
_STUDENT_SAFE = {"flag", "class_id", "count", "student_ref", "erased"}
_lock = threading.Lock()
_head: dict[str, tuple[int, str]] = {}          # path -> (last seq, last hash)
_failures = {"url": 0}


def _line_hash(prev: str, body: dict) -> str:
    return hashlib.sha256((prev + json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)).encode()).hexdigest()


def _read_head(path: Path) -> tuple[int, str]:
    if not path.exists() or path.stat().st_size == 0:
        return 0, GENESIS
    with open(path, "rb") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(max(0, size - 8192))
        last = f.read().splitlines()[-1]
    rec = json.loads(last)
    return rec["seq"], rec["hash"]


def emit(action: str, user_id=None, entity_type: str = "", entity_id=None, details=None) -> None:
    """Append one event. Never raises: the audit trail must not break the action it records."""
    try:
        path_s = gpc.get("audit.sink_path")
        url = gpc.get("audit.sink_url")
        if not path_s and not url:
            return
        if entity_type == "student":                      # students' names and numbers never leave the database:
            details = {k: v for k, v in (details or {}).items() if k in _STUDENT_SAFE}    # the sink can't be erased
        body = {"ts": istnow().isoformat(), "action": action, "user_id": user_id, "entity_type": entity_type,
                "entity_id": entity_id, "details": details or {}}
        if path_s:
            _append(Path(path_s), body)
        if url:
            threading.Thread(target=_post, args=(url, body), daemon=True).start()
    except Exception:                                # pragma: no cover - best effort by design
        log.exception("audit sink failed for %s", action)


def _append(path: Path, body: dict) -> None:
    with _lock:
        key = str(path)
        if key not in _head:
            path.parent.mkdir(parents=True, exist_ok=True)
            _head[key] = _read_head(path)
        seq, prev = _head[key]
        rec = {"seq": seq + 1, "prev": prev, **body}
        rec["hash"] = _line_hash(prev, {k: v for k, v in rec.items() if k != "hash"})
        fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
        try:
            os.write(fd, (json.dumps(rec, sort_keys=True, default=str) + "\n").encode())
            os.fsync(fd)
        finally:
            os.close(fd)
        _head[key] = (rec["seq"], rec["hash"])


def _hmac_key() -> bytes:
    return hashlib.sha256(b"impress-audit-webhook\0" + settings.JWT_SECRET.encode()).digest()


def _post(url: str, body: dict) -> None:
    try:
        payload = json.dumps(body, sort_keys=True, default=str).encode()
        req = urllib.request.Request(url, data=payload, method="POST", headers={
            "Content-Type": "application/json",
            "X-Impress-Signature": "sha256=" + hmac.new(_hmac_key(), payload, hashlib.sha256).hexdigest()})
        urllib.request.urlopen(req, timeout=5).close()
    except Exception as exc:
        _failures["url"] += 1
        log.warning("audit webhook failed (%d so far): %s", _failures["url"], exc)


def status() -> dict:
    return {"file": gpc.get("audit.sink_path") or None, "url": bool(gpc.get("audit.sink_url")),
            "webhook_failures": _failures["url"]}


def verify_file(path: Path) -> list[str]:
    """Problems in a chain file; empty when it is intact from the first line."""
    problems, prev, seq = [], GENESIS, 0
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        return [f"cannot read {path}: {exc}"]
    for n, line in enumerate(lines, 1):
        try:
            rec = json.loads(line)
        except ValueError:
            problems.append(f"line {n}: not valid JSON")
            break
        if rec.get("seq") != seq + 1:
            problems.append(f"line {n}: expected sequence {seq + 1}, found {rec.get('seq')} (a line was removed, added or reordered)")
        if rec.get("prev") != prev:
            problems.append(f"line {n}: does not continue the previous line")
        if rec.get("hash") != _line_hash(rec.get("prev", ""), {k: v for k, v in rec.items() if k != "hash"}):
            problems.append(f"line {n}: content does not match its hash (edited)")
        prev, seq = rec.get("hash", ""), rec.get("seq", seq + 1)
        if problems:
            break
    return problems
