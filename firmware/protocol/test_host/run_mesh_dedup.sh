#!/usr/bin/env bash
# Build + run the mesh de-dup host tests (no ESP-IDF needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
cc -std=gnu11 -g -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
   -I.. test_mesh_dedup.c ../protocol.c -o "$OUT/test_mesh_dedup"
"$OUT/test_mesh_dedup"
