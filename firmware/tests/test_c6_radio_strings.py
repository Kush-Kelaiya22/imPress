"""v2.2: strings from a radio frame are not trusted to be NUL-terminated.

The gateway turns mesh frames into JSON. A spoofed or malformed frame whose
10-character enrollment field has no terminator would make cJSON read past
the field, so every enrollment goes through enrollment_of() first."""

import re
from pathlib import Path

MAIN = Path(__file__).resolve().parents[1] / "class_c6" / "main" / "main.c"


def test_every_enrollment_is_terminated_before_json():
    src = MAIN.read_text()
    adds = re.findall(r'cJSON_AddStringToObject\(j, "enrollment_number", ([^;]+)\);', src)
    assert len(adds) >= 5
    assert all(a.startswith("enrollment_of(") for a in adds), adds


def test_enrollment_of_copies_ten_bytes_and_terminates():
    body = re.search(r"static const char \*enrollment_of\([^)]*\)\s*\{(.*?)\n\}", MAIN.read_text(), re.S)
    assert body and "memcpy(out, field, 10)" in body.group(1) and "out[10] = '\\0'" in body.group(1)
