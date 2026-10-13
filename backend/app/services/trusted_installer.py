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
   simulation (services/qualification.py).
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
    r = report(artifact, data)
    if not r or r.get("status") != "qualified":
        failed = next((s for s in (r or {}).get("stages", []) if s.get("passed") is False), None)
        return "not qualified" + (f" ({failed['stage']}: {failed['problems'][0]})" if failed else "")
    return None
