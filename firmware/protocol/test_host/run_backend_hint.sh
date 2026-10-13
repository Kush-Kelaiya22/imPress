#!/usr/bin/env bash
# Build + run the backend connection-hint host tests (#132; no ESP-IDF needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
cc -std=gnu11 -g -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
   -I.. test_backend_hint.c -o "$OUT/test_backend_hint"
"$OUT/test_backend_hint"
