#!/usr/bin/env python3
"""Create or complete backend/.env from backend/.env.example (#42).

The public default secrets are never written: an empty or missing
IMPRESS_JWT_SECRET / IMPRESS_DEVICE_API_KEY gets a random value; any value
already set is kept. The file is readable by its owner only.

Usage: scripts/init_env.py [backend_dir]
"""

import os
import secrets
import sys
from pathlib import Path

GENERATED = ("IMPRESS_JWT_SECRET", "IMPRESS_DEVICE_API_KEY")


def init_env(backend: Path) -> list[str]:
    """Returns the names of the secrets it generated."""
    env, example = backend / ".env", backend / ".env.example"
    lines = (env if env.exists() else example).read_text().splitlines()
    generated = []
    for i, line in enumerate(lines):
        key, sep, rest = line.partition("=")
        if sep and key.strip() in GENERATED:
            value, hash_, comment = rest.partition("#")
            if not value.strip():
                lines[i] = f"{key.strip()}={secrets.token_urlsafe(32)}" + (f"  #{comment}" if hash_ else "")
                generated.append(key.strip())
    for key in GENERATED:
        if not any(l.partition("=")[0].strip() == key for l in lines):
            lines.append(f"{key}={secrets.token_urlsafe(32)}")
            generated.append(key)
    fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(lines) + "\n")
    os.chmod(env, 0o600)                    # also when the file already existed
    return generated


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "backend"
    for name in init_env(root):
        print(f"generated {name}")
