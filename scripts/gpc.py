#!/usr/bin/env python3
"""Root's tool for the global policy and the code manifest (v2.2).

Run it as root, on a machine that is NOT the application host in production:
the private key it makes must never sit next to the server it controls.

    scripts/gpc.py keygen  --dir ~/impress-root          # root.key (private, 0600) + root_public.key
    scripts/gpc.py sign    --key root.key --profile hardened --set dual_control.delay_minutes=30 \\
                           --set audit.sink_path=/var/log/impress/audit.jsonl --out global_policy_control.json
    scripts/gpc.py sign    --key root.key --from global_policy_control.json --set test_mode.allowed=true --out ...
    scripts/gpc.py show    global_policy_control.json    [--public root_public.key]
    scripts/gpc.py verify  global_policy_control.json    --public root_public.key
    scripts/gpc.py flags                                  # every flag, its type and defaults
    scripts/gpc.py manifest --key root.key               # sign backend/app (MANIFEST.json + MANIFEST.sig)
    scripts/gpc.py manifest --verify --public root_public.key

Copy global_policy_control.json, root_public.key (and MANIFEST.*) to the server read-only for the
service user. The server never writes them. Each `sign` raises the serial by one, so an older
signed file can't be put back. Docs: docs/design/gpc.md
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app import ed25519, gpc, signing  # noqa: E402


def _read_key(path: str) -> bytes:
    return base64.b64decode(Path(path).expanduser().read_text().strip(), validate=True)


def _public(path: str) -> bytes:
    return gpc.load_public_key(Path(path).expanduser())


def cmd_keygen(a):
    out = Path(a.dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    priv, pub = out / "root.key", out / "root_public.key"
    if priv.exists() and not a.force:
        sys.exit(f"{priv} exists: refusing to overwrite (use --force if you mean it)")
    seed = ed25519.generate_seed()
    fd = os.open(priv, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(base64.b64encode(seed).decode() + "\n")
    pub.write_text(base64.b64encode(ed25519.public_key(seed)).decode() + "\n")
    print(f"private key  {priv}   (keep it off the server; 0600)")
    print(f"public key   {pub}   (copy to the server)")
    print(f"key id       {ed25519.key_id(ed25519.public_key(seed))}")


def cmd_sign(a):
    seed = _read_key(a.key)
    flags, serial, profile = {}, 1, a.profile
    if a.from_file:
        old = json.loads(Path(a.from_file).read_text())
        flags, serial, profile = dict(old.get("flags", {})), int(old.get("serial", 0)) + 1, profile or old.get("profile")
    elif Path(a.out).exists():
        serial = int(json.loads(Path(a.out).read_text()).get("serial", 0)) + 1
    for item in a.set or []:
        name, sep, raw = item.partition("=")
        if not sep or name not in gpc.FLAGS:
            sys.exit(f"unknown flag or missing '=': {item!r} (run: scripts/gpc.py flags)")
        flags[name] = gpc.coerce(gpc.FLAGS[name], raw)
    for name in a.unset or []:
        flags.pop(name, None)
    profile = profile or "standard"
    if profile not in gpc.PROFILES:
        sys.exit("profile must be standard or hardened")
    ist = timezone(timedelta(hours=5, minutes=30))
    doc = gpc.sign_document(seed, profile, flags, serial, datetime.now(ist).isoformat(timespec="seconds"))
    Path(a.out).write_text(json.dumps(doc, indent=2) + "\n")
    print(f"wrote {a.out}: profile {profile}, serial {serial}, {len(flags)} flag(s) set, key {doc['key_id']}")


def cmd_show(a):
    doc = json.loads(Path(a.file).read_text())
    print(f"profile {doc.get('profile')}  serial {doc.get('serial')}  issued {doc.get('issued_at')}  key {doc.get('key_id')}")
    for name in sorted(doc.get("flags", {})):
        print(f"  {name} = {doc['flags'][name]!r}")
    if a.public:
        cmd_verify(a)


def cmd_verify(a):
    try:
        doc = gpc.check_signed_file(Path(a.file), Path(a.public).expanduser(), 0)
    except gpc.PolicyError as exc:
        sys.exit(f"NOT VALID: {exc}")
    print(f"valid: serial {doc['serial']}, profile {doc['profile']}, signed with key {doc['key_id']}")


def cmd_flags(a):
    for f in gpc.FLAGS.values():
        print(f"{f.name:34} {f.kind:5} standard={f.standard!r:8} hardened={f.hardened!r:10} {f.doc}")


def cmd_manifest(a):
    if a.verify:
        problems = signing.verify_manifest(_public(a.public))
        print("\n".join(problems) or "the code matches the signed manifest")
        sys.exit(1 if problems else 0)
    manifest = signing.write_manifest(_read_key(a.key), version=(Path(__file__).resolve().parents[1] / "VERSION").read_text().strip())
    print(f"signed {len(manifest['files'])} files under backend/app (MANIFEST.json, MANIFEST.sig)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("keygen"); p.add_argument("--dir", default="."); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_keygen)
    p = sub.add_parser("sign"); p.add_argument("--key", required=True); p.add_argument("--out", default="global_policy_control.json")
    p.add_argument("--profile"); p.add_argument("--from", dest="from_file"); p.add_argument("--set", action="append"); p.add_argument("--unset", action="append"); p.set_defaults(fn=cmd_sign)
    p = sub.add_parser("show"); p.add_argument("file"); p.add_argument("--public"); p.set_defaults(fn=cmd_show)
    p = sub.add_parser("verify"); p.add_argument("file"); p.add_argument("--public", required=True); p.set_defaults(fn=cmd_verify)
    sub.add_parser("flags").set_defaults(fn=cmd_flags)
    p = sub.add_parser("manifest"); p.add_argument("--key"); p.add_argument("--public"); p.add_argument("--verify", action="store_true"); p.set_defaults(fn=cmd_manifest)
    a = ap.parse_args()
    if a.cmd == "manifest" and not (a.key or a.verify):
        ap.error("manifest needs --key (to sign) or --verify --public")
    a.fn(a)


if __name__ == "__main__":
    main()
