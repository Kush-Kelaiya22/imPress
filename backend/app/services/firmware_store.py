"""Firmware artifact store (#35).

Uploads are validated as ESP-IDF app images (firmware_image.parse_image) and
registered in `firmware_artifacts`; the bytes are stored as
<FIRMWARE_DIR>/<sha256>.bin, a name derived from the content, never from user
input. A (target, version) pair can only ever name one set of bytes.
Files from the pre-v2.1 store (<type>-<version>.bin) are adopted at startup
when they are valid images, and ignored otherwise.
"""

import logging
import re
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..models import FirmwareArtifact
from .csv_import import read_upload
from .firmware_image import MAX_IMAGE_BYTES, ImageError, parse_image
from .firmware_signing import site_key_digest

log = logging.getLogger(__name__)

_VERSION_RE = re.compile(r"^v?\d+\.\d+\.\d+$")
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_LEGACY_RE = re.compile(r"^(c6|s3|student)-(\d+\.\d+\.\d+)\.bin$")


def normalize_version(version: str) -> str:
    v = (version or "").strip().lower()
    if not v:
        raise HTTPException(400, "version is required")
    if not _VERSION_RE.match(v):
        raise HTTPException(400, "version must be semver like 1.0.0")
    return v.removeprefix("v")


def store_dir() -> Path:
    d = Path(settings.FIRMWARE_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def artifact_path(sha256: str) -> Path:
    if not _SHA_RE.match(sha256 or ""):
        raise ValueError("artifact paths are built from a SHA-256 only")
    return Path(settings.FIRMWARE_DIR) / f"{sha256}.bin"


def artifact_file(artifact: FirmwareArtifact) -> Path:
    path = artifact_path(artifact.sha256)
    if not path.is_file():
        raise HTTPException(410, f"firmware {artifact.target} {artifact.version} is registered but its file is missing")
    return path


def _write(sha256: str, data: bytes) -> None:
    dest = artifact_path(sha256)
    if dest.is_file():
        return
    tmp = dest.with_suffix(".part")
    tmp.write_bytes(data)
    tmp.replace(dest)                    # atomic: a reader never sees half a file


async def resolve(db: AsyncSession, target: str, version: str, *, include_deprecated=False):
    q = select(FirmwareArtifact).where(FirmwareArtifact.target == target, FirmwareArtifact.version == version)
    if not include_deprecated:
        q = q.where(FirmwareArtifact.status != "deprecated")
    return (await db.execute(q)).scalar_one_or_none()


def _signer(info) -> str:
    """The site key if it signed the image, else its first signer, else ""."""
    site = site_key_digest()
    return site if site in info.signers else (info.signers[0] if info.signers else "")


async def store_upload(db: AsyncSession, file: UploadFile, user_id: int | None, *,
                       device_type: str | None = None, version: str | None = None,
                       channel: str = "stable", release_notes: str = "") -> tuple[FirmwareArtifact, bool]:
    """Validate and register an upload. Returns (artifact, created). Not committed."""
    data = await read_upload(file, MAX_IMAGE_BYTES)
    try:
        info = parse_image(data)
    except ImageError as e:
        raise HTTPException(422, str(e))
    if device_type and device_type.strip().lower() != info.target:
        raise HTTPException(422, f"this file is a {info.target} image ({info.project}), not {device_type}")
    if version and normalize_version(version) != info.version:
        raise HTTPException(422, f"this file is version {info.version}, not {normalize_version(version)}")
    if channel not in ("stable", "beta"):
        raise HTTPException(422, "channel must be stable or beta")
    site = site_key_digest()
    if site and site not in info.signers:
        raise HTTPException(422, ("the image is not signed" if not info.signers else
                                  "the image is not signed with this server's firmware key")
                            + f" (IMPRESS_FIRMWARE_SIGNING_KEY, key {site[:16]}…); build it with "
                              "scripts/build_signed.sh or sign it with espsecure.py sign_data --version 2")

    same = (await db.execute(select(FirmwareArtifact).where(FirmwareArtifact.sha256 == info.sha256))).scalar_one_or_none()
    if same is not None:
        return same, False                                   # identical bytes: idempotent
    clash = await resolve(db, info.target, info.version, include_deprecated=True)
    if clash is not None:
        raise HTTPException(409, f"{info.target} {info.version} already exists with different contents "
                                 f"(sha256 {clash.sha256[:12]}…); bump firmware/<project>/version.txt and rebuild")
    store_dir()
    _write(info.sha256, data)
    artifact = FirmwareArtifact(
        sha256=info.sha256, size=info.size, target=info.target, chip=info.chip, project=info.project,
        version=info.version, idf_version=info.idf_version, build_date=info.build_date,
        elf_sha256=info.elf_sha256, channel=channel, release_notes=release_notes[:5000], uploaded_by=user_id,
        signer=_signer(info))
    db.add(artifact)
    await db.flush()
    return artifact, True


async def adopt_legacy_files(db: AsyncSession) -> tuple[int, int]:
    """Register valid <type>-<version>.bin files from the old store (once)."""
    d = Path(settings.FIRMWARE_DIR)
    if not d.is_dir():
        return 0, 0
    adopted = rejected = 0
    for f in sorted(d.iterdir()):
        m = _LEGACY_RE.match(f.name)
        if not m:
            continue
        data = f.read_bytes()
        try:
            info = parse_image(data)
        except ImageError as e:
            rejected += 1
            log.warning("Not adopting %s: %s (it can no longer be downloaded)", f.name, e)
            continue
        if (info.target, info.version) != (m.group(1), m.group(2)):
            rejected += 1
            log.warning("Not adopting %s: the image is %s %s", f.name, info.target, info.version)
            continue
        known = await db.scalar(select(FirmwareArtifact.id).where(FirmwareArtifact.sha256 == info.sha256))
        if known or await resolve(db, info.target, info.version, include_deprecated=True):
            continue
        _write(info.sha256, data)
        db.add(FirmwareArtifact(sha256=info.sha256, size=info.size, target=info.target, chip=info.chip,
                                project=info.project, version=info.version, idf_version=info.idf_version,
                                build_date=info.build_date, elf_sha256=info.elf_sha256, legacy=True))
        adopted += 1
    if adopted:
        await db.flush()
        log.warning("Adopted %d firmware file(s) from the old store into the registry", adopted)
    return adopted, rejected
