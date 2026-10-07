#!/usr/bin/env bash
# Build + run the C6 host tests (no ESP-IDF needed). Exits non-zero on failure.
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
SAN="-fsanitize=address,undefined -fno-omit-frame-pointer"
# Use-after-return detection makes a stale stack descriptor fail loudly.
if cc -fsanitize=address -fsanitize-address-use-after-return=always -x c -c /dev/null -o /dev/null 2>/dev/null; then
    SAN="$SAN -fsanitize-address-use-after-return=always"
fi
export ASAN_OPTIONS="detect_stack_use_after_return=1:abort_on_error=1"
cc -std=gnu11 -g -Wall -Wextra $SAN -Istubs -I../main -I../../protocol \
   test_spi_slave.c ../main/spi_slave.c ../../protocol/protocol.c -o "$OUT/test_spi_slave"
"$OUT/test_spi_slave"
