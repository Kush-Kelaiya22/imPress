#!/usr/bin/env bash
# Build + run the delivery acknowledgement host tests (#181) (no ESP-IDF needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
cc -std=gnu11 -g -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
   -I.. test_answer_ack.c ../protocol.c -o "$OUT/test_answer_ack"
"$OUT/test_answer_ack"
