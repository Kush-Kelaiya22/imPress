"""Firmware artifact store for ESP OTA.

Filenames: <device_type>-<version>.bin  (e.g. c6-1.0.0.bin, s3-1.0.0.bin)
- Admin uploads a .bin; the version + device_type is parsed from the payload it
  provides in the multipart form (version field) and the model name.
- Devices download the .bin by their device_type + the pending version the
  server has set on their EspDevice row.
"""

import re
import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile

from ..config import settings

_VERSION_RE = re.compile(r"^v?\d+\.\d+\.\d+$")


def firmware_path(device_type: str, version: str) -> Path:
    """Where a firmware binary for a device_type+version is stored."""
    return Path(settings.FIRMWARE_DIR) / f"{device_type}-{version}.bin"


def ensure_dir() -> Path:
    d = Path(settings.FIRMWARE_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def normalize_version(version: str) -> str:
    v = (version or "").strip()
    if not v:
        raise HTTPException(400, "version is required")
    v = v.lower()
    if v.startswith("v"):
        v = v[1:]
    if not _VERSION_RE.match(v):
        raise HTTPException(400, "version must be semver like 1.0.0")
    return v


async def save_firmware(file: UploadFile, device_type: str, version: str) -> Path:
    """Persist an uploaded firmware binary. Returns the stored path."""
    dt = (device_type or "").strip().lower()
    if dt not in ("c6", "s3", "student"):
        raise HTTPException(400, f"unsupported device_type '{device_type}'")
    ver = normalize_version(version)

    ensure_dir()
    dest = firmware_path(dt, ver)
    tmp = dest.with_suffix(".bin.part")
    try:
        with tmp.open("wb") as out:
            while chunk := await file.read(1024 * 256):
                out.write(chunk)
    except OSError as e:
        raise HTTPException(500, f"failed to store firmware: {e}")
    shutil.move(str(tmp), str(dest))
    return dest


def get_firmware_path(device_type: str, version: str) -> Path:
    """Resolve a stored firmware file for download (404 if absent)."""
    dt = (device_type or "").strip().lower()
    ver = normalize_version(version)
    p = firmware_path(dt, ver)
    if not p.is_file():
        raise HTTPException(404, f"firmware {dt}-{ver}.bin not found")
    return p