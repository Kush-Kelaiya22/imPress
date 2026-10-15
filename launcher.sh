#!/usr/bin/env bash
# imPress launcher for macOS and Linux: everything from a fresh checkout to a
# running server, without Docker. Safe to run every time.
#
#   ./launcher.sh                       # listens on all interfaces at port 8000
#   ./launcher.sh --test-mode      test mode forced on, nobody can turn it off (a lab)
#   ./launcher.sh --no-test-mode   no test-data menu at all
#   ./launcher.sh --no-ota         over-the-air updates off
#   ./launcher.sh --feature dual_control.delay_minutes=30     any policy flag (docs/guides/launch-flags.md)
#
# 1. finds Python 3.12+ (installs it with Homebrew, apt or dnf when missing)
# 2. creates backend/.venv and installs the dependencies (pip skips what is there)
# 3. creates backend/.env with fresh secrets if it does not exist (keeps existing values)
# 4. checks port 8000 and asks before stopping its current owner
# 5. starts the server (scripts/start.sh)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$ROOT/backend"
HOST="0.0.0.0"
PORT=8000
export IMPRESS_HOST="$HOST" IMPRESS_PORT="$PORT"

say() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
die() { printf '\033[1;31mError:\033[0m %s\n' "$*" >&2; exit 1; }
sudo_if_needed() { if [ "$(id -u)" -eq 0 ]; then "$@"; else sudo "$@"; fi; }

# Check before installing packages or rewriting any setup state. Never signal a
# process until an operator has seen its PID/name and opted in at the terminal.
pids_on_port() {
  if command -v lsof >/dev/null 2>&1; then lsof -nP -t -iTCP:"$PORT" -sTCP:LISTEN 2>/dev/null || true
  elif command -v fuser >/dev/null 2>&1; then fuser -n tcp "$PORT" 2>/dev/null | tr -s ' ' '\n' | grep . || true
  elif command -v ss >/dev/null 2>&1; then ss -ltnpH "sport = :$PORT" 2>/dev/null | grep -o 'pid=[0-9]*' | cut -d= -f2 || true
  fi
}

if ! command -v lsof >/dev/null 2>&1 && ! command -v fuser >/dev/null 2>&1 && ! command -v ss >/dev/null 2>&1; then
  die "cannot check whether port $PORT is occupied (install lsof, fuser, or ss)."
fi

confirm() {
  local answer
  if ! read -r -p "$1 [y/N] " answer </dev/tty 2>/dev/null; then
    return 1
  fi
  case "$answer" in y|Y|yes|YES|Yes) return 0 ;; *) return 1 ;; esac
}

ensure_port_free() {
  local pids pid name remaining
  pids="$(pids_on_port | sort -nu | tr '\n' ' ')"
  [ -n "${pids// /}" ] || return 0

  say "Port $PORT is already in use"
  for pid in $pids; do
    name="$(ps -p "$pid" -o comm= 2>/dev/null | cut -c1-80)"
    [ -n "$name" ] || name="process details unavailable"
    printf '    PID %-7s %s\n' "$pid" "$name"
  done
  confirm "Stop these process(es) so imPress can use port $PORT?" \
    || die "no process was stopped; rerun in a terminal and confirm if you want to replace it."

  for pid in $pids; do
    if ! kill -TERM "$pid" 2>/dev/null; then
      [ -n "$(pids_on_port | grep -x "$pid" || true)" ] || continue
      sudo_if_needed kill -TERM "$pid" || die "could not stop PID $pid; port $PORT remains in use."
    fi
  done
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    [ -z "$(pids_on_port)" ] && return 0
    sleep 0.5
  done
  remaining="$(pids_on_port | sort -nu | tr '\n' ' ')"
  [ -n "${remaining// /}" ] || return 0

  say "The listener did not exit after a graceful stop"
  for pid in $remaining; do
    name="$(ps -p "$pid" -o comm= 2>/dev/null | cut -c1-80)"
    [ -n "$name" ] || name="process details unavailable"
    printf '    PID %-7s %s\n' "$pid" "$name"
  done
  confirm "Force-kill these remaining process(es)?" \
    || die "left the remaining process(es) untouched; port $PORT is still in use."
  for pid in $remaining; do
    if ! kill -KILL "$pid" 2>/dev/null; then
      [ -n "$(pids_on_port | grep -x "$pid" || true)" ] || continue
      sudo_if_needed kill -KILL "$pid" || die "could not force-kill PID $pid; port $PORT remains in use."
    fi
  done
  sleep 0.5
  [ -z "$(pids_on_port)" ] || die "port $PORT is still in use; stop its owner manually and retry."
}

ensure_port_free

ok_python() { "$1" -c 'import sys, venv, ensurepip; sys.exit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; }

find_python() {
  for p in "${PYTHON:-}" python3.14 python3.13 python3.12 python3; do
    [ -n "$p" ] && command -v "$p" >/dev/null 2>&1 && ok_python "$p" && { command -v "$p"; return 0; }
  done
  return 1
}

# ── 1. Python ──────────────────────────────────────────────────────────
say "Python 3.12 or newer"
if ! PY="$(find_python)"; then
  case "$(uname -s)" in
    Darwin)
      command -v brew >/dev/null 2>&1 || die "Python 3.12+ is missing and Homebrew is not installed. Install Homebrew (https://brew.sh) or Python from https://www.python.org/downloads/, then run this again."
      say "Installing Python 3.12 with Homebrew"
      brew install python@3.12 ;;
    Linux)
      if command -v apt-get >/dev/null 2>&1; then
        say "Installing Python 3.12 with apt"
        sudo_if_needed apt-get update -qq
        sudo_if_needed apt-get install -y python3.12 python3.12-venv || die "apt has no python3.12 here; install Python 3.12+ yourself, then run this again (or set PYTHON=/path/to/python3)."
      elif command -v dnf >/dev/null 2>&1; then
        say "Installing Python 3.12 with dnf"
        sudo_if_needed dnf install -y python3.12
      else
        die "Python 3.12+ is missing; install it with your package manager, then run this again."
      fi ;;
    *) die "Unsupported system $(uname -s); on Windows use launcher.bat." ;;
  esac
  hash -r
  PY="$(find_python)" || die "Python 3.12+ still not found after installing; open a new terminal or set PYTHON=/path/to/python3."
fi
echo "    $("$PY" --version) at $PY"

# ── 2. virtualenv and dependencies ─────────────────────────────────────
VPY="$BACKEND/.venv/bin/python"
if [ -x "$VPY" ] && ! ok_python "$VPY"; then
  say "backend/.venv is broken or too old: recreating it"
  rm -rf "$BACKEND/.venv"
fi
if [ ! -x "$VPY" ]; then
  say "Creating backend/.venv"
  "$PY" -m venv "$BACKEND/.venv"
  "$VPY" -m pip install --quiet --upgrade pip
fi
say "Dependencies"
# The hash-locked set is what CI tests; it is resolved for Linux x86_64.
if [ "$(uname -s)-$(uname -m)" = "Linux-x86_64" ]; then
  "$VPY" -m pip install --quiet --disable-pip-version-check --require-hashes -r "$BACKEND/requirements-lock.txt"
else
  "$VPY" -m pip install --quiet --disable-pip-version-check -r "$BACKEND/requirements.txt"
fi

# ── 3. configuration ───────────────────────────────────────────────────
say "Configuration (backend/.env)"
"$VPY" "$ROOT/scripts/init_env.py" "$BACKEND"
(cd "$BACKEND" && "$VPY" -c 'from app.main import app; print(f"    imPress {app.version}")') \
  || die "the app does not import; see the error above."

# ── 5. start ───────────────────────────────────────────────────────────
say "Starting imPress on all network interfaces (0.0.0.0:$PORT)  (Ctrl+C stops it)"
exec "$ROOT/scripts/start.sh" "$@"
