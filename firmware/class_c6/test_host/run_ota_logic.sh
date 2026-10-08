#!/usr/bin/env bash
# Build + run the C6 OTA client logic host test (no ESP-IDF; uses the vendored cJSON).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
CJSON=../managed_components/espressif__cjson/cJSON
SAN="-fsanitize=address,undefined -fno-omit-frame-pointer"
cc -std=gnu11 -g -w $SAN -c "$CJSON/cJSON.c" -o "$OUT/cJSON.o"   # vendored: not our warnings
cc -std=gnu11 -g -Wall -Wextra -Werror $SAN -I../main -I"$CJSON" \
   test_ota_logic.c ../main/ota_logic.c "$OUT/cJSON.o" -o "$OUT/test_ota_logic"
"$OUT/test_ota_logic"
