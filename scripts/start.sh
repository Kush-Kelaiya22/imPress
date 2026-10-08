#!/usr/bin/env bash
# Start the imPress backend (#42). One worker: the presence sweep, deployment
# scheduler and WebSocket rooms live in the process.
#
#   IMPRESS_HOST=0.0.0.0 IMPRESS_PORT=8000 scripts/start.sh
#
# TLS without a reverse proxy (#66): set both, and devices use BACKEND_TLS.
#   IMPRESS_SSL_CERTFILE=/etc/impress/server.crt IMPRESS_SSL_KEYFILE=/etc/impress/server.key scripts/start.sh
set -euo pipefail

BACKEND="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
[ -x "$BACKEND/.venv/bin/uvicorn" ] || { echo "Not installed: run scripts/install.sh first" >&2; exit 1; }
TLS=()
if [ -n "${IMPRESS_SSL_CERTFILE:-}" ] || [ -n "${IMPRESS_SSL_KEYFILE:-}" ]; then
  [ -r "${IMPRESS_SSL_CERTFILE:-}" ] && [ -r "${IMPRESS_SSL_KEYFILE:-}" ] || {
    echo "Set both IMPRESS_SSL_CERTFILE and IMPRESS_SSL_KEYFILE to readable files" >&2; exit 1; }
  TLS=(--ssl-certfile "$IMPRESS_SSL_CERTFILE" --ssl-keyfile "$IMPRESS_SSL_KEYFILE")
fi
cd "$BACKEND"          # .env, the default SQLite path and firmware_bins/ are relative to backend/
exec .venv/bin/uvicorn app.main:app --host "${IMPRESS_HOST:-127.0.0.1}" --port "${IMPRESS_PORT:-8000}" \
  --workers 1 --proxy-headers ${TLS[@]+"${TLS[@]}"}
