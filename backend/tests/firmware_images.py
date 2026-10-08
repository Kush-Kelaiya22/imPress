"""Build structurally valid ESP-IDF app images for tests (real header layout,
app descriptor and appended SHA-256), so validation is tested byte-exactly
without committing megabyte binaries."""

import hashlib
import struct

from app.services.firmware_image import APP_DESC_MAGIC, CHIP_IDS, IMAGE_MAGIC, PROJECTS


def make_image(project="impress_class_c6", version="2.1.0", *, chip_id=None, payload=b"\x00" * 64,
               hash_appended=True):
    if chip_id is None:
        chip_id = CHIP_IDS[PROJECTS[project][1]] if project in PROJECTS else 13
    header = bytearray(24)
    header[0], header[1] = IMAGE_MAGIC, 1
    struct.pack_into("<H", header, 12, chip_id)
    header[23] = 1 if hash_appended else 0
    desc = bytearray(256)                      # esp_app_desc_t, at file offset 32
    struct.pack_into("<I", desc, 0, APP_DESC_MAGIC)
    for off, text in ((16, version), (48, project), (80, "08:35:32"), (96, "Oct  8 2026"), (112, "v6.1")):
        desc[off:off + len(text)] = text.encode()
    desc[144:176] = hashlib.sha256((project + version).encode()).digest()
    body = bytes(header) + struct.pack("<II", 0x3C000020, len(desc) + len(payload)) + bytes(desc) + payload + b"\xaa"
    return body + (hashlib.sha256(body).digest() if hash_appended else b"\x00" * 32)
