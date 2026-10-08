#!/usr/bin/env bash
# Create the site's firmware signing key pair (#66), once per installation.
#
#   scripts/firmware_key.sh [dir]        # default: ~/.impress/firmware-signing
#
# Writes signing_key.pem (PRIVATE: keep it offline, back it up, never commit
# it) and signing_key.pub (public: give its path to the backend as
# IMPRESS_FIRMWARE_SIGNING_KEY). Refuses to overwrite an existing key: every
# device that trusts it would reject images signed with a new one.
set -euo pipefail

DIR="${1:-$HOME/.impress/firmware-signing}"
IDF_IMAGE="espressif/idf:v6.1@sha256:81893c71bb5e570088901f21def8684c25cd2a9020281bd01b843a7655edb18c"

if [ -e "$DIR/signing_key.pem" ]; then
  echo "A signing key already exists in $DIR; not replacing it." >&2
  echo "Devices that trust it refuse images signed with any other key." >&2
  exit 1
fi
mkdir -p "$DIR"
chmod 700 "$DIR"

run_espsecure() {                # native ESP-IDF if installed, else the pinned Docker image
  if type -P espsecure >/dev/null; then
    (cd "$DIR" && espsecure "$@")
  else
    docker run --rm -u "$(id -u):$(id -g)" -e HOME=/tmp -v "$DIR":/keys -w /keys "$IDF_IMAGE" espsecure "$@"
  fi
}

run_espsecure generate-signing-key --version 2 --scheme rsa3072 signing_key.pem
run_espsecure extract-public-key --version 2 --keyfile signing_key.pem signing_key.pub
chmod 600 "$DIR/signing_key.pem"
run_espsecure digest-sbv2-public-key --keyfile signing_key.pub --output key_digest.bin >/dev/null
DIGEST="$(od -An -tx1 -v "$DIR/key_digest.bin" | tr -d ' \n')"
rm -f "$DIR/key_digest.bin"

cat <<MSG

Signing key created in $DIR
  private  signing_key.pem   keep offline and backed up; losing it means devices
                             can only be updated over serial
  public   signing_key.pub   digest $DIGEST

Next:
  1. Backend: IMPRESS_FIRMWARE_SIGNING_KEY=$DIR/signing_key.pub in backend/.env, restart.
  2. Build:   IMPRESS_SIGNING_KEY=$DIR/signing_key.pem scripts/build_signed.sh class_c6   (and class_s3)
  3. Upload the signed image and deploy it as usual. Once a device runs it, it
     accepts only images signed with this key.
MSG
