"""Read and validate an ESP-IDF application image (#35). Pure: bytes in, facts out.

An uploaded file is trusted for nothing: the target, chip and version come
from the image itself, not from the filename or form fields.

Layout (ESP-IDF v5/v6, esp_app_format):
    0   esp_image_header_t (24 B): magic 0xE9, segment_count, ..., chip_id
        u16 at offset 12, ..., hash_appended u8 at offset 23
    24  first segment header (8 B): load_addr, data_len
    32  esp_app_desc_t (256 B): magic 0xABCD5432, secure_version, reserv1[2],
        version[32] @48, project_name[32] @80, time[16] @112, date[16] @128,
        idf_ver[32] @144, app_elf_sha256[32] @176
    ... segments (8-byte header + data each), zero padding, checksum byte
        ending a 16-byte block ...
    SHA-256 of everything before it (when hash_appended == 1)
    optional: 0xFF padding + a 4096-byte signature sector (#66, firmware_signing.py)
"""

from __future__ import annotations

import hashlib
import re
import struct
from dataclasses import dataclass

from .firmware_signing import SignatureError, verify_signature

IMAGE_MAGIC = 0xE9
APP_DESC_MAGIC = 0xABCD5432
CHIPS = {0: "esp32", 9: "esp32s3", 13: "esp32c6"}
CHIP_IDS = {name: chip_id for chip_id, name in CHIPS.items()}

# project_name (from each firmware/<project>/CMakeLists.txt) → (device type, chip)
PROJECTS = {
    "impress_class_c6": ("c6", "esp32c6"),
    "impress_class_s3": ("s3", "esp32s3"),
    "impress_student": ("student", "esp32"),
}
# OTA app slot size per device type (firmware/<project>/partitions.csv);
# test_firmware_registry.py checks these against the partition tables.
SLOT_BYTES = {"c6": 0x3E0000, "s3": 0x400000, "student": 0x1C0000}
MAX_IMAGE_BYTES = max(SLOT_BYTES.values())

_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
_MIN_SIZE = 24 + 8 + 256 + 32


class ImageError(ValueError):
    """The bytes are not a usable imPress firmware image; the message says why."""


@dataclass(frozen=True)
class ImageInfo:
    target: str          # c6 | s3 | student
    chip: str            # esp32c6 | esp32s3 | esp32
    project: str
    version: str
    idf_version: str
    build_date: str      # "Oct  8 2026 08:35:32"
    elf_sha256: str      # hex of the ELF hash the build embedded
    sha256: str          # hex of the whole file
    size: int
    signers: tuple[str, ...] = ()   # Secure Boot V2 key digests of its signatures; () if unsigned (#66)


def _cstr(b: bytes) -> str:
    return b.split(b"\0", 1)[0].decode("utf-8", errors="replace").strip()


def parse_image(data: bytes) -> ImageInfo:
    if len(data) < _MIN_SIZE:
        raise ImageError(f"file is too small to be a firmware image ({len(data)} bytes)")
    if data[0] != IMAGE_MAGIC:
        raise ImageError("not an ESP-IDF firmware image (wrong magic byte); upload the app .bin from build/")
    segments = data[1]
    if not 1 <= segments <= 16:
        raise ImageError(f"implausible segment count {segments}")
    chip_id = struct.unpack_from("<H", data, 12)[0]
    chip = CHIPS.get(chip_id)
    if chip is None:
        raise ImageError(f"image is built for chip id {chip_id}, which no imPress device uses")
    if struct.unpack_from("<I", data, 32)[0] != APP_DESC_MAGIC:
        raise ImageError("no application descriptor: this is not an app image (bootloader or partition table?)")

    project = _cstr(data[80:112])
    if project not in PROJECTS:
        raise ImageError(f"project '{project}' is not an imPress firmware ({', '.join(PROJECTS)})")
    target, expected_chip = PROJECTS[project]
    if chip != expected_chip:
        raise ImageError(f"{project} must be built for {expected_chip}, but the image is for {chip}")
    version = _cstr(data[48:80])
    if not _SEMVER.match(version):
        raise ImageError(f"image version '{version}' is not X.Y.Z; set it in firmware/<project>/version.txt")

    if data[23] != 1:
        raise ImageError("image has no appended SHA-256, so its integrity can't be checked")
    end = image_end(data)
    if end > len(data) or hashlib.sha256(data[:end - 32]).digest() != data[end - 32:end]:
        raise ImageError("image is corrupt or truncated (appended SHA-256 does not match)")
    try:
        signers = verify_signature(data, end)
    except SignatureError as exc:
        raise ImageError(f"bad signature: {exc}") from None
    if len(data) > SLOT_BYTES[target]:
        raise ImageError(f"image is {len(data)} bytes; the {target} OTA slot holds {SLOT_BYTES[target]}")

    return ImageInfo(
        target=target, chip=chip, project=project, version=version,
        idf_version=_cstr(data[144:176]),
        build_date=f"{_cstr(data[128:144])} {_cstr(data[112:128])}".strip(),
        elf_sha256=data[176:208].hex(), sha256=hashlib.sha256(data).hexdigest(), size=len(data), signers=signers)


def image_end(data: bytes) -> int:
    """Length of the app image itself (segments, checksum, appended SHA-256),
    without any signature sector after it."""
    pos = 24
    for _ in range(data[1]):
        if pos + 8 > len(data):
            raise ImageError("image is truncated (segment header past the end)")
        pos += 8 + struct.unpack_from("<I", data, pos + 4)[0]
    pos = (pos // 16 + 1) * 16                 # the checksum byte ends a 16-byte block
    return pos + (32 if data[23] == 1 else 0)

