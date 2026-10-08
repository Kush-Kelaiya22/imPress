#!/usr/bin/env bash
# Start the imPress backend (#42). One worker: the presence sweep, deployment
# scheduler and WebSocket rooms live in the process.
#
#   IMPRESS_HOST=0.0.0.0 IMPRESS_PORT=8000 scripts/start.sh
set -euo pipefail

BACKEND="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
[ -x "$BACKEND/.venv/bin/uvicorn" ] || { echo "Not installed: run scripts/install.sh first" >&2; exit 1; }
cd "$BACKEND"          # .env, the default SQLite path and firmware_bins/ are relative to backend/
exec .venv/bin/uvicorn app.main:app --host "${IMPRESS_HOST:-127.0.0.1}" --port "${IMPRESS_PORT:-8000}" \
  --workers 1 --proxy-headers
