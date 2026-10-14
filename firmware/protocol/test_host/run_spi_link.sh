#!/usr/bin/env bash
# Build + run the acknowledged SPI slot host tests (#182) (no ESP-IDF needed).
set -euo pipefail
cd "$(dirname "$0")"
OUT="$(mktemp -d)"
cc -std=gnu11 -g -O1 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-omit-frame-pointer \
   -I.. test_spi_link.c ../protocol.c ../spi_link.c -o "$OUT/test_spi_link"
"$OUT/test_spi_link"
