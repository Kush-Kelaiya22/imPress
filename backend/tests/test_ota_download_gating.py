"""#13: firmware can only be downloaded for an OTA an admin actually pushed."""

import os
from pathlib import Path

import pytest
from sqlalchemy import update

from conftest import DEVICE

MAC = "AA:BB:CC:DD:EE:13"


@pytest.fixture
def device(client, db):
    r = client.post("/api/device/register", headers=DEVICE,
                    json={"mac_address": MAC, "device_type": "s3", "device_name": "hub"})
    assert r.status_code == 200, r.text
    fw_dir = Path(os.environ["IMPRESS_FIRMWARE_DIR"])
    fw_dir.mkdir(parents=True, exist_ok=True)
    for v in ("1.1.0", "9.9.9"):
        (fw_dir / f"s3-{v}.bin").write_bytes(b"\xe9" + v.encode())

    def set_pending(version):
        from app.models import EspDevice

        async def go(s):
            await s.execute(update(EspDevice).where(EspDevice.mac_address == MAC).values(pending_version=version))
        db(go)
    return set_pending


def dl(client, version, headers=DEVICE):
    return client.get("/api/device/firmware/download", headers=headers,
                      params={"mac_address": MAC, "version": version})


def test_no_pending_ota_means_no_download(client, device):
    assert dl(client, "9.9.9").status_code == 403         # was 200: any stored image
    assert dl(client, "1.1.0").status_code == 403


def test_only_the_pushed_version_downloads(client, device):
    device("1.1.0")
    ok = dl(client, "1.1.0")
    assert ok.status_code == 200 and ok.content == b"\xe91.1.0"
    assert dl(client, "9.9.9").status_code == 403


def test_download_requires_device_key(client, device):
    device("1.1.0")
    assert dl(client, "1.1.0", headers={"X-API-Key": "wrong"}).status_code == 403
    assert dl(client, "1.1.0", headers={}).status_code in (401, 403, 422)
