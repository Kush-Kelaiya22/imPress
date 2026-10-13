"""Build structurally valid ESP-IDF app images for tests (real header layout,
app descriptor and appended SHA-256), so validation is tested byte-exactly
without committing megabyte binaries."""

import hashlib
import struct

from app.services.firmware_image import APP_DESC_MAGIC, CHIP_IDS, IMAGE_MAGIC, PROJECTS


# Where a real build of each chip puts its first (flash data) segment and its
# entry point, so the TrustedInstaller's analysis (#154) sees a loadable image.
LAYOUT = {"esp32c6": (0x42000020, 0x4086B91A), "esp32s3": (0x3C0B0020, 0x40375B37), "esp32": (0x3F400020, 0x40081815)}


def make_image(project="impress_class_c6", version="2.1.0", *, chip_id=None, payload=b"\x00" * 64,
               hash_appended=True):
    if chip_id is None:
        chip_id = CHIP_IDS[PROJECTS[project][1]] if project in PROJECTS else 13
    header = bytearray(24)
    header[0], header[1] = IMAGE_MAGIC, 1
    load, entry = LAYOUT.get(PROJECTS[project][1] if project in PROJECTS else "esp32c6")
    struct.pack_into("<I", header, 4, entry)
    struct.pack_into("<H", header, 12, chip_id)
    header[23] = 1 if hash_appended else 0
    desc = bytearray(256)                      # esp_app_desc_t, at file offset 32
    struct.pack_into("<I", desc, 0, APP_DESC_MAGIC)
    for off, text in ((16, version), (48, project), (80, "08:35:32"), (96, "Oct  8 2026"), (112, "v6.1")):
        desc[off:off + len(text)] = text.encode()
    desc[144:176] = hashlib.sha256((project + version).encode()).digest()
    segment = bytes(desc) + payload
    body = bytes(header) + struct.pack("<II", load, len(segment)) + segment
    checksum = 0xEF
    for b in segment:
        checksum ^= b
    body += b"\x00" * (15 - len(body) % 16) + bytes([checksum])   # checksum ends a 16-byte block, as ESP-IDF pads it
    return body + (hashlib.sha256(body).digest() if hash_appended else b"\x00" * 32)
