#!/usr/bin/env bash
# Run every host-side firmware test suite (no ESP-IDF needed):
#   firmware/*/test_host/run*.sh  — each builds its tests with cc + sanitizers.
set -uo pipefail
cd "$(dirname "$0")"
shopt -s nullglob
suites=(*/test_host/run*.sh)
if [ ${#suites[@]} -eq 0 ]; then
    echo "no host test suites found"; exit 0
fi
fail=0
for s in "${suites[@]}"; do
    echo "=== $s"
    if bash "$s"; then echo "--- PASS $s"; else echo "--- FAIL $s"; fail=1; fi
done
exit $fail
