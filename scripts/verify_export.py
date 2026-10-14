#!/usr/bin/env python3
"""Check that an imPress export zip is exactly what the server signed (v2.2).

    scripts/verify_export.py impress-test-data-test-20261015-101500.zip --public-key <base64>
    scripts/verify_export.py export.zip --server https://impress.example.edu     # fetches /api/system/signing-key

Get the key over a channel you trust (the System page shows its id): a key fetched from the
same place as the zip proves integrity but not who made it. Exit status 0 only when valid.
"""

import argparse
import base64
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app import ed25519, signing  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zip")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--public-key", help="base64 Ed25519 public key")
    g.add_argument("--server", help="base URL of the imPress server to ask for its key")
    a = ap.parse_args()
    key_b64 = a.public_key
    if a.server:
        with urllib.request.urlopen(a.server.rstrip("/") + "/api/system/signing-key", timeout=10) as r:
            key_b64 = json.load(r)["public_key"]
    public = base64.b64decode(key_b64, validate=True)
    with zipfile.ZipFile(a.zip) as z:
        if "SIGNATURE.json" not in z.namelist():
            sys.exit("NOT SIGNED: the zip has no SIGNATURE.json")
        files = {n: z.read(n) for n in z.namelist() if n != "SIGNATURE.json"}
        problems = signing.verify_files(z.read("SIGNATURE.json"), files, public)
    if problems:
        sys.exit("NOT VALID:\n  " + "\n  ".join(problems))
    print(f"valid: {len(files)} files, signed by key {ed25519.key_id(public)}")


if __name__ == "__main__":
    main()
