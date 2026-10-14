#!/usr/bin/env bash
# The imPress root console (v2.2): an interactive shell for operating the system as root.
#   scripts/console.sh                     interactive
#   scripts/console.sh -c "users list"     one command, then exit
# Run it on the server's host: it uses the database file directly (docs/guides/console.md).
set -euo pipefail
BACKEND="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backend" && pwd)"
[ -x "$BACKEND/.venv/bin/python" ] || { echo "Not installed: run ./launcher.sh or scripts/install.sh first" >&2; exit 1; }
cd "$BACKEND"
exec .venv/bin/python -m app.console "$@"
