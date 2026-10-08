"""#35: uploaded firmware is validated as a real imPress image and registered
immutably; the old file store is adopted or ignored."""

import hashlib
import os
import re
from pathlib import Path

import pytest
from sqlalchemy import func, select

from conftest import DEVICE, auth, login, upload_firmware
from firmware_images import make_image

FIRMWARE_SRC = Path(__file__).resolve().parents[2] / "firmware"


def _upload(client, h, data, **form):
    return client.post("/api/admin/firmware/upload" if form else "/api/admin/firmware", headers=h,
                       data=form or None, files={"file": ("fw.bin", data, "application/octet-stream")})


def _count(db):
    from app.models import FirmwareArtifact

    async def q(s):
        return await s.scalar(select(func.count()).select_from(FirmwareArtifact))
    return db(q)


@pytest.fixture
def h(client):
    return auth(login(client))


# ── The parser's constants match the firmware sources ───────────────────────

def test_project_names_match_the_cmake_projects():
    from app.services.firmware_image import PROJECTS
    names = {re.search(r"project\((\w+)\)", (FIRMWARE_SRC / p / "CMakeLists.txt").read_text()).group(1)
             for p in ("class_c6", "class_s3", "student")}
    assert names == set(PROJECTS)


def test_slot_sizes_match_the_partition_tables():
    from app.services.firmware_image import SLOT_BYTES
    for project, target in (("class_c6", "c6"), ("class_s3", "s3"), ("student", "student")):
        rows = [l.split(",") for l in (FIRMWARE_SRC / project / "partitions.csv").read_text().splitlines()
                if l.strip() and not l.startswith("#")]
        sizes = {int(r[4].strip(), 16) for r in rows if r[0].strip() in ("ota_0", "ota_1")}
        assert sizes == {SLOT_BYTES[target]}, project


# ── Validation ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("make,needle", [
    (lambda: os.urandom(4096), "not an ESP-IDF firmware image"),
    (lambda: b"\xe9" + b"\x00" * 100, "too small"),
    (lambda: make_image()[:200], "too small"),
    (lambda: make_image(chip_id=5), "chip id 5"),
    (lambda: make_image(project="some_other_app"), "not an imPress firmware"),
    (lambda: make_image("impress_class_c6", chip_id=9), "must be built for esp32c6"),
    (lambda: make_image(version="1"), "not X.Y.Z"),
    (lambda: make_image(hash_appended=False), "no appended SHA-256"),
])
def test_invalid_images_are_rejected_with_the_reason(client, db, h, make, needle):
    r = _upload(client, h, make())
    assert r.status_code == 422 and needle in r.json()["detail"], r.text
    assert _count(db) == 0
    store = Path(os.environ["IMPRESS_FIRMWARE_DIR"])
    assert not store.exists() or not list(store.glob("*.bin"))      # nothing written


def test_corrupted_image_is_detected_by_its_hash(client, h):
    image = bytearray(make_image())
    image[100] ^= 0x01
    r = _upload(client, h, bytes(image))
    assert r.status_code == 422 and "corrupt or truncated" in r.json()["detail"]


def test_oversized_image_is_rejected(client, h):
    from app.services.firmware_image import SLOT_BYTES
    r = _upload(client, h, make_image("impress_student", payload=b"\x00" * SLOT_BYTES["student"]))
    assert r.status_code == 422 and "slot holds" in r.json()["detail"]
    too_big = _upload(client, h, b"\xe9" + b"\x00" * (max(SLOT_BYTES.values()) + 1))
    assert too_big.status_code == 413


def test_facts_come_from_the_image_not_the_form(client, h):
    image = make_image("impress_student", "3.0.1")
    a = _upload(client, h, image).json()
    assert (a["target"], a["chip"], a["project"], a["version"]) == ("student", "esp32", "impress_student", "3.0.1")
    assert a["sha256"] == hashlib.sha256(image).hexdigest() and a["size"] == len(image)
    assert a["idf_version"] == "v6.1" and a["build_date"] == "Oct  8 2026 08:35:32"
    # the legacy form endpoint must agree with the image
    wrong_type = _upload(client, h, make_image("impress_class_c6", "1.0.0"), device_type="s3", version="1.0.0")
    assert wrong_type.status_code == 422 and "is a c6 image" in wrong_type.json()["detail"]
    wrong_ver = _upload(client, h, make_image("impress_class_c6", "1.0.0"), device_type="c6", version="1.0.1")
    assert wrong_ver.status_code == 422 and "is version 1.0.0" in wrong_ver.json()["detail"]


# ── Immutability ────────────────────────────────────────────────────────────

def test_identical_reupload_is_idempotent_and_different_bytes_conflict(client, db, h):
    image = make_image("impress_class_s3", "2.1.0")
    first, again = _upload(client, h, image).json(), _upload(client, h, image).json()
    assert first["created"] is True and again["created"] is False and again["id"] == first["id"]
    other = _upload(client, h, make_image("impress_class_s3", "2.1.0", payload=b"\x01" * 64))
    assert other.status_code == 409 and "already exists with different contents" in other.json()["detail"]
    assert _count(db) == 1
    stored = Path(os.environ["IMPRESS_FIRMWARE_DIR"]) / f"{first['sha256']}.bin"
    assert stored.read_bytes() == image            # the original bytes were not replaced


def test_same_version_for_different_targets_is_fine(client, db, h):
    for project in ("impress_class_c6", "impress_class_s3", "impress_student"):
        upload_firmware(client, h, project, "2.1.0")
    listed = client.get("/api/admin/firmware", headers=h).json()
    assert sorted(a["target"] for a in listed) == ["c6", "s3", "student"]
    assert [a["target"] for a in client.get("/api/admin/firmware?target=c6", headers=h).json()] == ["c6"]


# ── Download and push use the registry ─────────────────────────────────────

def test_device_downloads_its_registered_image_with_its_hash(client, h):
    image = upload_firmware(client, h, "impress_class_s3", "2.2.0")
    dev = client.post("/api/device/register", headers=DEVICE,
                      json={"mac_address": "a1b2c3d4e5f6", "device_type": "s3", "device_name": "hub"}).json()
    assert client.post(f"/api/admin/modules/{dev['device_id']}/ota", headers=h, json={"version": "2.2.0"}).status_code == 200
    r = client.get("/api/device/firmware/download", headers=DEVICE,
                   params={"mac_address": "a1b2c3d4e5f6", "version": "2.2.0"})
    assert r.status_code == 200 and r.content == image
    assert r.headers["x-firmware-sha256"] == hashlib.sha256(image).hexdigest()


def test_a_c6_image_is_never_pushed_to_an_s3(client, h):
    upload_firmware(client, h, "impress_class_c6", "2.2.0")
    dev = client.post("/api/device/register", headers=DEVICE,
                      json={"mac_address": "a1b2c3d4e5f6", "device_type": "s3", "device_name": "hub"}).json()
    r = client.post(f"/api/admin/modules/{dev['device_id']}/ota", headers=h, json={"version": "2.2.0"})
    assert r.status_code == 404 and "No uploaded s3 firmware 2.2.0" in r.json()["detail"]


# ── Pre-v2.1 file store ─────────────────────────────────────────────────────

def test_legacy_files_are_adopted_only_when_valid(client, db):
    from app.services.firmware_store import adopt_legacy_files
    d = Path(os.environ["IMPRESS_FIRMWARE_DIR"])
    d.mkdir(parents=True, exist_ok=True)
    good = make_image("impress_class_s3", "1.5.0")
    (d / "s3-1.5.0.bin").write_bytes(good)                        # valid
    (d / "s3-9.9.9.bin").write_bytes(b"\xe9random bytes")          # what v2 accepted
    (d / "c6-1.0.0.bin").write_bytes(make_image("impress_class_s3", "1.0.0"))   # name lies

    async def run(s):
        return await adopt_legacy_files(s)
    assert db(run) == (1, 2)
    assert db(run) == (0, 2)                                       # idempotent
    listed = client.get("/api/admin/firmware", headers=auth(login(client))).json()
    assert [(a["target"], a["version"], a["legacy"]) for a in listed] == [("s3", "1.5.0", True)]
    assert (d / f"{hashlib.sha256(good).hexdigest()}.bin").read_bytes() == good


def test_admin_only(client, h):
    from conftest import make_user
    _, teacher = make_user(client, h, "teach1")
    assert _upload(client, teacher, make_image()).status_code == 403
    assert client.get("/api/admin/firmware", headers=teacher).status_code == 403
    assert client.post("/api/admin/firmware", files={"file": ("f", b"x", "x")}).status_code == 401


@pytest.mark.parametrize("project,target,chip", [
    ("class_c6", "c6", "esp32c6"), ("class_s3", "s3", "esp32s3"), ("student", "student", "esp32")])
def test_real_build_output_parses(project, target, chip):
    """Against genuine ESP-IDF output when a local build exists (the synthetic
    images above cover CI, which doesn't build firmware in this job)."""
    from app.services.firmware_image import parse_image
    path = FIRMWARE_SRC / project / "build" / f"impress_{project}.bin"
    if not path.exists():
        pytest.skip(f"no local build of {project}")
    info = parse_image(path.read_bytes())
    version = (FIRMWARE_SRC / project / "version.txt").read_text().strip()
    assert (info.target, info.chip, info.version) == (target, chip, version)


@pytest.mark.parametrize("project", ["class_c6", "class_s3"])
def test_real_signed_build_output_parses(project):
    """A scripts/build_signed.sh build (#66), when one exists locally."""
    from app.services.firmware_image import SLOT_BYTES, parse_image
    path = FIRMWARE_SRC / project / "build" / "signed" / f"impress_{project}.bin"
    if not path.exists():
        pytest.skip(f"no local signed build of {project}")
    info = parse_image(path.read_bytes())
    assert len(info.signers) == 1 and info.size <= SLOT_BYTES[info.target]

