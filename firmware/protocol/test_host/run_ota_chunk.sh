#!/usr/bin/env bash
# Build + run the student-OTA chunking host tests (#130; no ESP-IDF needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
cc -std=gnu11 -g -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
   -I.. test_ota_chunk.c ../ota_chunk.c -o "$OUT/test_ota_chunk"
"$OUT/test_ota_chunk"
