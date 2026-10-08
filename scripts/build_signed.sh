#!/usr/bin/env bash
# Build a signed firmware image (#66) for the hub or the gateway.
#
#   IMPRESS_SIGNING_KEY=~/.impress/firmware-signing/signing_key.pem scripts/build_signed.sh class_c6
#
# Output: firmware/<project>/build/signed/impress_<project>.bin, signed with
# the key, and an app that verifies every later OTA image against it. Upload
# that file on the Firmware page. The normal build (firmware/<project>/build)
# is not touched.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="${1:-}"
KEY="${IMPRESS_SIGNING_KEY:-}"
IDF_IMAGE="espressif/idf:v6.1@sha256:81893c71bb5e570088901f21def8684c25cd2a9020281bd01b843a7655edb18c"

case "$PROJECT" in
  class_c6|class_s3) ;;
  student) echo "Student modules have no over-the-air updates, so there is nothing to sign." >&2; exit 2 ;;
  *) echo "usage: IMPRESS_SIGNING_KEY=<private key> $0 class_c6|class_s3" >&2; exit 2 ;;
esac
[ -n "$KEY" ] && [ -r "$KEY" ] || { echo "Set IMPRESS_SIGNING_KEY to the private key from scripts/firmware_key.sh" >&2; exit 2; }
KEY="$(cd "$(dirname "$KEY")" && pwd)/$(basename "$KEY")"

if command -v idf.py >/dev/null 2>&1; then
  FW="$ROOT/firmware"; KEY_IN="$KEY"
  run() { (cd "$FW/$PROJECT" && "$@"); }
else
  FW="/project"; KEY_IN="/keys/$(basename "$KEY")"
  run() { docker run --rm --init -v "$ROOT/firmware":/project -v "$(dirname "$KEY")":/keys:ro \
            -w "/project/$PROJECT" "$IDF_IMAGE" "$@"; }
fi

# Start from the project's committed sdkconfig, so the signed image keeps its
# flash mode and size, partition table, rollback and every other setting;
# only the signing options below change.
OUT="build/signed"
DIR="$ROOT/firmware/$PROJECT/$OUT"
mkdir -p "$DIR"
SIGNED_OPTS='SECURE_SIGNED_APPS_NO_SECURE_BOOT|SECURE_SIGNED_APPS_[A-Z0-9_]*SCHEME|SECURE_SIGNED_ON_UPDATE_NO_SECURE_BOOT|SECURE_BOOT_BUILD_SIGNED_BINARIES|SECURE_BOOT_SIGNING_KEY'
grep -Ev "^(# )?CONFIG_($SIGNED_OPTS)[= ]" "$ROOT/firmware/$PROJECT/sdkconfig" > "$DIR/sdkconfig"
grep '^CONFIG_' "$ROOT/firmware/sdkconfig.defaults.signed" >> "$DIR/sdkconfig"
printf 'CONFIG_SECURE_BOOT_SIGNING_KEY="%s"\n' "$KEY_IN" >> "$DIR/sdkconfig"
run idf.py -B "$OUT" -D SDKCONFIG="$OUT/sdkconfig" build

BIN="$ROOT/firmware/$PROJECT/$OUT/impress_$PROJECT.bin"
[ -f "$BIN" ] || { echo "build produced no image" >&2; exit 1; }
echo
echo "Signed image: $BIN"
echo "Upload it on the Firmware page; the backend checks the signature against IMPRESS_FIRMWARE_SIGNING_KEY."
