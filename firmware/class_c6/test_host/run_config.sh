#!/usr/bin/env bash
# Build + run the C6 runtime-config host test (no ESP-IDF needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
cc -std=gnu11 -g -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
   -include test_sdkconfig.h -Istubs -I../main -I../../test_support \
   test_c6_config.c ../main/config.c ../../test_support/nvs_fake.c -o "$OUT/test_c6_config"
"$OUT/test_c6_config"
