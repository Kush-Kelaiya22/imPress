#!/usr/bin/env bash
# Install the imPress backend on this machine (#42). Safe to re-run: it
# reuses the venv and keeps every value already in backend/.env.
#
#   scripts/install.sh            # then: scripts/start.sh
#
# PYTHON=python3.12 picks the interpreter (default: python3, >= 3.12).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND="$ROOT/backend"
PY="${PYTHON:-python3}"

"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' || {
  echo "imPress needs Python >= 3.12 (found: $("$PY" --version 2>&1)); set PYTHON=..." >&2; exit 1; }

echo "==> virtualenv: backend/.venv"
[ -x "$BACKEND/.venv/bin/python" ] || "$PY" -m venv "$BACKEND/.venv"
VPY="$BACKEND/.venv/bin/python"
"$VPY" -m pip install --quiet --upgrade pip

# The hash-locked set is what CI tests; it is resolved for Linux x86_64.
if [ "$(uname -s)-$(uname -m)" = "Linux-x86_64" ]; then
  echo "==> dependencies: requirements-lock.txt (hash-checked)"
  "$VPY" -m pip install --quiet --require-hashes -r "$BACKEND/requirements-lock.txt"
else
  echo "==> dependencies: requirements.txt (no lock for $(uname -s)-$(uname -m))"
  "$VPY" -m pip install --quiet -r "$BACKEND/requirements.txt"
fi

echo "==> configuration: backend/.env"
"$VPY" "$ROOT/scripts/init_env.py" "$BACKEND"

echo "==> check: the app imports and its migrations are known"
(cd "$BACKEND" && "$VPY" -c 'from app.main import app; from app.migrations import LATEST; print(f"imPress {app.version}, schema {LATEST}")')

cat <<MSG

Installed. Next:
  scripts/start.sh                     # serves http://127.0.0.1:8000
  Put IMPRESS_DEVICE_API_KEY from backend/.env into every gateway (CONFIG_DEVICE_API_KEY / NVS api_key).
  On first start the super admin 'admin' is created; its password is printed once in the log
  unless IMPRESS_INITIAL_ADMIN_PASSWORD is set in backend/.env.
MSG
