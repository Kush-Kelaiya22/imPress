#!/usr/bin/env bash
# Off-host backup of an imPress installation (v2.2): a consistent copy of the database,
# the firmware folder and .env, checksummed, optionally encrypted, copied somewhere the
# application's administrators can't alter.
#
#   scripts/backup.sh --dest /mnt/backup/impress                      # a folder (a mounted, append-only or versioned volume)
#   scripts/backup.sh --dest backup@vault.example.edu:/srv/impress    # rsync over ssh
#   scripts/backup.sh --dest /mnt/backup/impress --encrypt-to ops@example.edu --keep 35
#
# Options (defaults are the layout scripts/install.sh makes):
#   --db PATH            the SQLite file               (backend/impress.db)
#   --firmware DIR       uploaded firmware images      (backend/firmware_bins)
#   --env FILE           the secrets file              (backend/.env)
#   --encrypt-to ID      gpg recipient: the archive is encrypted and only that key can read it.
#                        .env holds secrets: do not send it anywhere unencrypted.
#   --keep N             in a local --dest, delete archives older than N days (default: keep all)
#
# Restore: decrypt (gpg -d), check the .sha256, untar, put impress.db back (stop the server first),
# then re-apply any erasures made since the backup (docs/compliance/retention-schedule.md).
# Schedule it (cron or a systemd timer) and rehearse a restore: an untested backup is a hope.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="$ROOT/backend/impress.db"; FW="$ROOT/backend/firmware_bins"; ENVF="$ROOT/backend/.env"
DEST=""; GPG_TO=""; KEEP=""
while [ $# -gt 0 ]; do
  case "$1" in
    --db) DB="$2"; shift 2 ;; --firmware) FW="$2"; shift 2 ;; --env) ENVF="$2"; shift 2 ;;
    --dest) DEST="$2"; shift 2 ;; --encrypt-to) GPG_TO="$2"; shift 2 ;; --keep) KEEP="$2"; shift 2 ;;
    -h|--help) sed -n '2,24p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done
[ -n "$DEST" ] || { echo "--dest is required" >&2; exit 2; }
[ -f "$DB" ] || { echo "database not found: $DB" >&2; exit 1; }

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
STAMP="$(date +%Y%m%d-%H%M%S)"; NAME="impress-backup-$STAMP"
mkdir -p "$WORK/$NAME"

# A consistent copy while the server runs (SQLite's online backup), then verify it opens.
PY="$ROOT/backend/.venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
"$PY" - "$DB" "$WORK/$NAME/impress.db" <<'PYEOF'
import sqlite3, sys
from contextlib import closing
with closing(sqlite3.connect(sys.argv[1])) as s, closing(sqlite3.connect(sys.argv[2])) as d:
    s.backup(d)
with closing(sqlite3.connect(sys.argv[2])) as d:
    assert d.execute("PRAGMA integrity_check").fetchone()[0] == "ok", "the copy does not pass SQLite's integrity check"
PYEOF
[ -d "$FW" ] && cp -R "$FW" "$WORK/$NAME/firmware_bins"
[ -f "$ENVF" ] && cp "$ENVF" "$WORK/$NAME/dot-env"
( cd "$WORK/$NAME" && find . -type f -print0 | sort -z | xargs -0 shasum -a 256 > MANIFEST.sha256 )
COPYFILE_DISABLE=1 tar -C "$WORK" -czf "$WORK/$NAME.tar.gz" "$NAME"
OUT="$NAME.tar.gz"
if [ -n "$GPG_TO" ]; then
  gpg --batch --yes --trust-model always --encrypt --recipient "$GPG_TO" --output "$WORK/$NAME.tar.gz.gpg" "$WORK/$NAME.tar.gz"
  rm "$WORK/$NAME.tar.gz"; OUT="$NAME.tar.gz.gpg"
fi
( cd "$WORK" && shasum -a 256 "$OUT" > "$OUT.sha256" )

case "$DEST" in
  *:*) rsync -a "$WORK/$OUT" "$WORK/$OUT.sha256" "$DEST/" ;;
  *)   mkdir -p "$DEST"; cp "$WORK/$OUT" "$WORK/$OUT.sha256" "$DEST/"; chmod 600 "$DEST/$OUT" ;;
esac
if [ -n "$KEEP" ] && [[ "$DEST" != *:* ]]; then
  find "$DEST" -maxdepth 1 -name 'impress-backup-*' -mtime "+$KEEP" -delete
fi
[ -z "$GPG_TO" ] && echo "note: this archive contains .env (secrets) and is NOT encrypted: use --encrypt-to" >&2
echo "backup written: $DEST/$OUT"
