#!/usr/bin/env bash
# Build + run the mesh frame authentication host tests (#187; no ESP-IDF needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
cc -std=gnu11 -g -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
   -I.. test_mesh_auth.c ../mesh_auth.c -o "$OUT/test_mesh_auth"
"$OUT/test_mesh_auth"
