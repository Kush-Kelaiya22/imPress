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
4. the stored file still has the registered size and SHA-256.
"""

from __future__ import annotations

import hashlib

from ..config import settings
from ..models import EspDevice, FirmwareArtifact
from .firmware_signing import site_key_digest
from .firmware_store import artifact_path

# The chip each device type runs (esp_app_desc / image header, #35).
CHIP = {"c6": "esp32c6", "s3": "esp32s3", "student": "esp32"}


def unsigned_accepted() -> bool:
    return bool(settings.FIRMWARE_ALLOW_UNSIGNED or settings.DEBUG)


def _file_intact(artifact: FirmwareArtifact) -> bool:
    path = artifact_path(artifact.sha256)
    if not path.is_file() or path.stat().st_size != artifact.size:
        return False
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest() == artifact.sha256


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
    if not _file_intact(artifact):
        return "stored image does not match its registered SHA-256 (file changed or missing)"
    return None
