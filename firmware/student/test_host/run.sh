#!/usr/bin/env bash
# Build + run the student firmware host tests (no ESP-IDF needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
cc -std=gnu11 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
   -Istubs -I../main -I../../test_support \
   test_student_config.c ../main/config.c ../../test_support/nvs_fake.c -o "$OUT/test_student_config"
"$OUT/test_student_config"
