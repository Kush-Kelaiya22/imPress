#!/usr/bin/env bash
# Container entrypoint (#96): make sure the secrets exist, then serve.
#
# Secrets come from the environment (-e IMPRESS_JWT_SECRET=... -e
# IMPRESS_DEVICE_API_KEY=...) or, when one is missing, are generated once into
# /data/.env (mode 600) and kept across restarts and upgrades. The device key
# that gateways need is printed on the first start.
set -eu
cd /app/backend

if [ -z "${IMPRESS_JWT_SECRET:-}" ] || [ -z "${IMPRESS_DEVICE_API_KEY:-}" ]; then
  python /app/scripts/init_env.py /app/backend
  if [ -z "${IMPRESS_DEVICE_API_KEY:-}" ]; then
    echo "Device API key (CONFIG_DEVICE_API_KEY on every gateway and hub):" \
      "$(sed -n 's/^IMPRESS_DEVICE_API_KEY=\([^ #]*\).*/\1/p' /data/.env)"
  fi
fi

set -- --host "${IMPRESS_HOST}" --port "${IMPRESS_PORT}" --workers 1 --proxy-headers
if [ -n "${IMPRESS_SSL_CERTFILE:-}" ] || [ -n "${IMPRESS_SSL_KEYFILE:-}" ]; then
  if [ ! -r "${IMPRESS_SSL_CERTFILE:-}" ] || [ ! -r "${IMPRESS_SSL_KEYFILE:-}" ]; then
    echo "Set both IMPRESS_SSL_CERTFILE and IMPRESS_SSL_KEYFILE to readable files" >&2
    exit 1
  fi
  set -- "$@" --ssl-certfile "$IMPRESS_SSL_CERTFILE" --ssl-keyfile "$IMPRESS_SSL_KEYFILE"
fi
# One worker: the presence sweep, the schedulers and the WebSocket rooms live in the process.
exec python -m uvicorn app.main:app "$@"
