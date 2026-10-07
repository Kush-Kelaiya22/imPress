#!/usr/bin/env bash
# Build + run the shared protocol host tests (no ESP-IDF needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
cc -std=gnu11 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
   -I.. test_protocol.c ../protocol.c -o "$OUT/test_protocol"
"$OUT/test_protocol"
