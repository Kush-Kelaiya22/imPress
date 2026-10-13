"""TrustedInstaller (Ring −2): the last check before firmware reaches a device (#123).

It is a service, not an account: no HTTP route calls it directly, no user
holds its authority, and it decides nothing about users. Administrators
request deployments (policy.py); the deployment engine asks this module
before it offers an image to a device, and the download route asks again
before it serves the bytes. Its own checks, re-run every time rather than
trusted from the request:

1. the image is approved (or, for an update already offered, deprecated);
2. it was built for this device: the device type and its chip;
3. it is signed with the site key, or the site has explicitly accepted
   unsigned images (IMPRESS_FIRMWARE_ALLOW_UNSIGNED, or DEBUG);
4. the stored file still has the registered size and SHA-256;
5. it passed qualification (#154): image analysis and the OTA client
   simulation (services/qualification.py);
6. it fits the board, where the board reported its flash and slot (#129).
"""

from __future__ import annotations

import hashlib

from ..config import settings
from ..models import EspDevice, FirmwareArtifact
from .firmware_signing import site_key_digest
from .firmware_store import artifact_path
from .qualification import qualify

# The chip each device type runs (esp_app_desc / image header, #35).
CHIP = {"c6": "esp32c6", "s3": "esp32s3", "student": "esp32"}


def unsigned_accepted() -> bool:
    return bool(settings.FIRMWARE_ALLOW_UNSIGNED or settings.DEBUG)


def _intact_bytes(artifact: FirmwareArtifact) -> bytes | None:
    """The stored image, if it still has its registered size and SHA-256."""
    path = artifact_path(artifact.sha256)
    if not path.is_file() or path.stat().st_size != artifact.size:
        return None
    data = path.read_bytes()
    return data if hashlib.sha256(data).hexdigest() == artifact.sha256 else None


def report(artifact: FirmwareArtifact, data: bytes | None = None) -> dict | None:
    """The qualification report (#154); computed from the stored bytes for an
    image registered before qualification existed."""
    if artifact.qualification:
        return artifact.qualification
    data = data if data is not None else _intact_bytes(artifact)
    return None if data is None else qualify(data, artifact.target, artifact.version)


# esp_image_header_t byte 3, high nibble: the flash size the image was built for.
_HEADER_FLASH_MB = {0: 1, 1: 2, 2: 4, 3: 8, 4: 16, 5: 32, 6: 64, 7: 128}


def board_refusal(data: bytes, device: EspDevice) -> str | None:
    """Does the image fit this board (#129)? Only checked where the board
    reported its capabilities; older firmware keeps the type/chip checks."""
    built_for = _HEADER_FLASH_MB.get(data[3] >> 4) if len(data) > 3 else None
    if device.flash_mb and built_for and built_for > device.flash_mb:
        return (f"incompatible: image built for {built_for} MB flash, this board has {device.flash_mb} MB "
                "(a different hub profile; see the classroom node requirements)")
    if device.ota_slot_kb and len(data) > device.ota_slot_kb * 1024:
        return f"incompatible: image is {len(data) // 1024} KB, this board's OTA slot holds {device.ota_slot_kb} KB"
    return None


def refusal(artifact: FirmwareArtifact, device: EspDevice, *, continuing: bool = False) -> str | None:
    """Why this image must not go to this device, or None.

    continuing=True: the device is fetching an update it was already offered,
    so a since-deprecated image is still served (deprecating must not strand
    a device mid-update)."""
    statuses = ("approved", "deprecated") if continuing else ("approved",)
    if artifact.status not in statuses or artifact.approved_by is None and not artifact.legacy:
        return f"image is {artifact.status}, not approved"
    dtype = (device.device_type or "").lower()
    if dtype != artifact.target or CHIP.get(dtype) != artifact.chip:
        return f"incompatible: a {device.device_type} device can't run a {artifact.target} ({artifact.chip}) image"
    site = site_key_digest()
    if site is not None:
        if artifact.signer != site:
            return "image is not signed with the site firmware key"
    elif not unsigned_accepted():
        return ("no site firmware key: set IMPRESS_FIRMWARE_SIGNING_KEY, or accept unsigned images "
                "explicitly with IMPRESS_FIRMWARE_ALLOW_UNSIGNED=true")
    data = _intact_bytes(artifact)
    if data is None:
        return "stored image does not match its registered SHA-256 (file changed or missing)"
    fits = board_refusal(data, device)
    if fits:
        return fits
    r = report(artifact, data)
    if not r or r.get("status") != "qualified":
        failed = next((s for s in (r or {}).get("stages", []) if s.get("passed") is False), None)
        return "not qualified" + (f" ({failed['stage']}: {failed['problems'][0]})" if failed else "")
    return None
