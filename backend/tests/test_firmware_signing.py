"""#66 (2/3): signed firmware. The verifier is checked against images signed
by the real espsecure.py (tests/fixtures/signing), then the upload and
deployment rules that use it."""

import struct
import zlib
from pathlib import Path

import pytest

from conftest import DEVICE, auth, login, upload_firmware
from firmware_images import make_image

FX = Path(__file__).parent / "fixtures" / "signing"
SIGNED_A = (FX / "c6_2.2.0_signed_a.img").read_bytes()
SIGNED_AB = (FX / "c6_2.2.0_signed_ab.img").read_bytes()
DIGEST_A = "e72c5da6eaa50b238e276e9ab76d78ba3f17051f9bbf3090c2cc884f6e9ead4c"   # espsecure digest_sbv2_public_key


def _digest(name):
    from app.services.firmware_signing import key_digest, load_public_key
    return key_digest(*load_public_key((FX / name).read_text()))


def _upload(client, h, data, name="fw.bin"):
    return client.post("/api/admin/firmware", headers=h, files={"file": (name, data, "application/octet-stream")})


@pytest.fixture
def h(client):
    return auth(login(client))


@pytest.fixture
def site_key(monkeypatch):
    from app.config import settings

    def use(name):
        monkeypatch.setattr(settings, "FIRMWARE_SIGNING_KEY", str(FX / name) if name else "")
    return use


# ── The verifier, against espsecure.py's own output ─────────────────────────

def test_real_signatures_verify_and_the_key_digest_matches_espsecure():
    from app.services.firmware_image import parse_image
    assert _digest("key_a.pub") == DIGEST_A
    assert parse_image(SIGNED_A).signers == (DIGEST_A,)
    assert parse_image(SIGNED_AB).signers == (DIGEST_A, _digest("key_b.pub"))
    assert parse_image(make_image()).signers == ()                       # unsigned


def _corrupt(offset, value=None, fix_crc=False):
    data = bytearray(SIGNED_A)
    data[offset] = value if value is not None else data[offset] ^ 0x01
    if fix_crc:                                    # forge a consistent-looking block
        block = 4096
        struct.pack_into("<I", data, block + 1196, zlib.crc32(bytes(data[block:block + 1196])) & 0xFFFFFFFF)
    return bytes(data)


@pytest.mark.parametrize("data,reason", [
    (_corrupt(1000), "unexpected data after the image"),                  # inside the 0xFF padding
    (_corrupt(4096 + 900), "corrupt (CRC mismatch)"),                     # signature byte, CRC left alone
    (_corrupt(4096 + 900, fix_crc=True), "signature block 0 is invalid"),  # forged signature
    (_corrupt(4096 + 40, fix_crc=True), "signature block 0 is invalid"),   # someone else's key in the block
    (_corrupt(4096 + 10, fix_crc=True), "modified after signing"),        # digest no longer matches
    (_corrupt(4096 + 1, 0x01, fix_crc=True), "expected Secure Boot V2"),
    (_corrupt(4096 + 1216 + 100), "after the signature blocks"),
    (SIGNED_A[:-1], "unexpected data after the image"),                   # truncated sector
    (make_image() + b"junk", "unexpected data after the image"),
])
def test_tampered_or_malformed_signatures_are_refused(data, reason):
    from app.services.firmware_image import ImageError, parse_image
    with pytest.raises(ImageError) as e:
        parse_image(data)
    assert reason in str(e.value)


def test_an_image_changed_after_signing_is_refused():
    from app.services.firmware_image import ImageError, parse_image
    data = bytearray(SIGNED_A)
    data[100] ^= 0x01                              # inside the image: its own SHA-256 catches it first
    with pytest.raises(ImageError, match="corrupt or truncated"):
        parse_image(bytes(data))


@pytest.mark.parametrize("pem,reason", [
    ("not a key", "unreadable public key"),
    ("-----BEGIN PUBLIC KEY-----\nMAA=\n-----END PUBLIC KEY-----", "unreadable public key"),
])
def test_bad_public_keys_are_refused(pem, reason):
    from app.services.firmware_signing import SignatureError, load_public_key
    with pytest.raises(SignatureError, match=reason):
        load_public_key(pem)


# ── Upload and deployment rules ──────────────────────────────────────────────

def test_without_a_site_key_signatures_are_recorded_not_required(client, h, site_key):
    site_key(None)
    a = _upload(client, h, SIGNED_A).json()
    assert (a["signer"], a["signed_by_site_key"]) == (DIGEST_A, None)
    assert _upload(client, h, make_image("impress_class_s3")).status_code == 200


def test_with_a_site_key_only_images_it_signed_are_accepted(client, h, site_key):
    site_key("key_a.pub")
    r = _upload(client, h, make_image("impress_class_c6", "2.3.0"))
    assert r.status_code == 422 and "not signed" in r.json()["detail"] and DIGEST_A[:16] in r.json()["detail"]
    a = _upload(client, h, SIGNED_A).json()
    assert (a["signer"], a["signed_by_site_key"]) == (DIGEST_A, True)


def test_a_foreign_key_is_refused_but_a_second_signature_by_the_site_key_counts(client, h, site_key):
    site_key("key_b.pub")
    r = _upload(client, h, SIGNED_A)
    assert r.status_code == 422 and "not signed with this server's firmware key" in r.json()["detail"]
    a = _upload(client, h, SIGNED_AB).json()                               # signed by A and B
    assert (a["signer"], a["signed_by_site_key"]) == (_digest("key_b.pub"), True)


def test_unsigned_images_from_before_are_not_deployed_once_signing_is_required(client, h, site_key):
    site_key(None)
    upload_firmware(client, h, "impress_class_c6", "2.2.0")               # unsigned, approved
    client.post("/api/device/register", headers=DEVICE, json={"mac_address": "48:F6:EE:00:00:01",
                                                               "device_type": "c6", "firmware_version": "2.1.0"})
    art = client.get("/api/admin/firmware", headers=h).json()[0]
    site_key("key_a.pub")
    assert client.get("/api/admin/firmware", headers=h).json()[0]["signed_by_site_key"] is False
    r = client.post("/api/admin/deployments?dry_run=true", headers=h, json={"artifact_id": art["id"], "device_ids": [1]})
    assert r.json()["excluded"][0]["reason"] == "image is not signed with the site firmware key (#66)"


def test_an_unreadable_site_key_is_reported(site_key):
    from app.services.firmware_signing import SignatureError, site_key_digest
    site_key("missing.pub")
    with pytest.raises(SignatureError, match="can't read IMPRESS_FIRMWARE_SIGNING_KEY"):
        site_key_digest()
