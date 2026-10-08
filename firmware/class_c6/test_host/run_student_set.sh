#!/usr/bin/env bash
# Build + run the C6 online-student set host test (no ESP-IDF needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
cc -std=gnu11 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
   -I../main test_student_set.c ../main/student_set.c -o "$OUT/test_student_set"
"$OUT/test_student_set"
