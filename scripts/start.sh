#!/usr/bin/env bash
# Start the imPress backend (#42). One worker: the presence sweep, deployment
# scheduler and WebSocket rooms live in the process.
#
#   IMPRESS_HOST=0.0.0.0 IMPRESS_PORT=8000 scripts/start.sh
#
# Launch flags (v2.2), after the command: scripts/start.sh --no-ota   |  --test-mode  |  --no-test-mode
#   (docs/guides/launch-flags.md)
#
# TLS without a reverse proxy (#66): set both, and devices use BACKEND_TLS.
#   IMPRESS_SSL_CERTFILE=/etc/impress/server.crt IMPRESS_SSL_KEYFILE=/etc/impress/server.key scripts/start.sh
set -euo pipefail

BACKEND="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
[ -x "$BACKEND/.venv/bin/uvicorn" ] || { echo "Not installed: run scripts/install.sh first" >&2; exit 1; }
if [ -n "${IMPRESS_SSL_CERTFILE:-}" ] || [ -n "${IMPRESS_SSL_KEYFILE:-}" ]; then
  [ -r "${IMPRESS_SSL_CERTFILE:-}" ] && [ -r "${IMPRESS_SSL_KEYFILE:-}" ] || {
    echo "Set both IMPRESS_SSL_CERTFILE and IMPRESS_SSL_KEYFILE to readable files" >&2; exit 1; }
  :   # app.serve reads the same two variables
fi
HOST="${IMPRESS_HOST:-127.0.0.1}" PORT="${IMPRESS_PORT:-8000}"
if [ "$HOST" = 127.0.0.1 ] || [ "$HOST" = localhost ]; then
  # Gateways connect over the network; this address only accepts this computer (#132).
  echo "Listening on $HOST:$PORT: only this computer can connect. For classroom gateways run" \
       "IMPRESS_HOST=0.0.0.0 scripts/start.sh and allow TCP $PORT in the firewall." >&2
fi
cd "$BACKEND"          # .env, the default SQLite path and firmware_bins/ are relative to backend/
# One worker. Launch flags (--test-mode, --no-test-mode, --no-ota, --feature name=value, --profile) go to
# app.serve, which turns them into root-owned policy overrides; TLS comes from IMPRESS_SSL_* as above.
exec .venv/bin/python -m app.serve --host "$HOST" --port "$PORT" "$@"
