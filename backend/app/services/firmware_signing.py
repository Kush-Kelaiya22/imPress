"""Signed firmware images (#66): ESP-IDF Secure Boot V2 RSA-3072 signatures,
verified with the standard library only.

A signed app (espsecure.py sign_data --version 2, or a build with
CONFIG_SECURE_BOOT_BUILD_SIGNED_BINARIES) is laid out as:

    image          the app as built (ends with its appended SHA-256)
    0xFF padding   up to the next 4096-byte boundary
    sector         4096 bytes: 1-3 signature blocks of 1216 bytes, then 0xFF

Signature block (esp_secure_boot.h, ets_secure_boot_sig_block_t):
    0     magic 0xE7, version 0x02, 2 reserved bytes
    4     SHA-256 of everything before the sector (image + padding)
    36    RSA public key: modulus n (384 B, little-endian), exponent e (u32 LE)
    424   rinv (384 B) and mdash (u32): Montgomery constants for the ROM
    812   RSA-PSS signature (384 B, little-endian) of that SHA-256:
          SHA-256, MGF1-SHA-256, 32-byte salt
    1196  CRC32 of bytes 0..1195
    1200  16 bytes padding

The devices verify the same signature in esp_ota_end() when built with
CONFIG_SECURE_SIGNED_APPS_NO_SECURE_BOOT; the backend checks it at upload so
an unsigned or foreign image is refused before any device downloads it.
"""

from __future__ import annotations

import base64
import hashlib
import struct
import zlib
from functools import lru_cache
from pathlib import Path

SECTOR = 4096
BLOCK = 1216
MAGIC, VERSION = 0xE7, 0x02
KEY_BYTES = 384                   # RSA-3072
SALT = 32


class SignatureError(ValueError):
    pass


# ── Public keys ─────────────────────────────────────────────────────────

def _der(data: bytes, pos: int) -> tuple[int, int, int]:
    """(tag, start of content, end of content) of the DER element at pos."""
    tag, length = data[pos], data[pos + 1]
    pos += 2
    if length & 0x80:
        n = length & 0x7F
        length = int.from_bytes(data[pos:pos + n], "big")
        pos += n
    return tag, pos, pos + length


def load_public_key(pem: str) -> tuple[int, int]:
    """(n, e) from a PEM RSA public key (SubjectPublicKeyInfo, as written by
    espsecure.py extract_public_key or openssl rsa -pubout)."""
    body = "".join(l for l in pem.strip().splitlines() if not l.startswith("-----"))
    try:
        der = base64.b64decode(body, validate=True)
        _, start, _ = _der(der, 0)                 # SEQUENCE SubjectPublicKeyInfo
        _, alg, alg_end = _der(der, start)         # SEQUENCE AlgorithmIdentifier
        if b"\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01" not in der[alg:alg_end]:
            raise SignatureError("not an RSA public key")
        tag, bits, _ = _der(der, alg_end)          # BIT STRING
        if tag != 0x03:
            raise SignatureError("malformed public key")
        _, seq, _ = _der(der, bits + 1)            # skip the unused-bits byte; SEQUENCE RSAPublicKey
        _, n0, n1 = _der(der, seq)
        _, e0, e1 = _der(der, n1)
        n, e = int.from_bytes(der[n0:n1], "big"), int.from_bytes(der[e0:e1], "big")
    except (ValueError, IndexError) as exc:
        raise SignatureError(f"unreadable public key: {exc}") from None
    if n.bit_length() != KEY_BYTES * 8:
        raise SignatureError(f"expected an RSA-3072 key, got {n.bit_length()} bits")
    return n, e


def key_digest(n: int, e: int) -> str:
    """The key's Secure Boot V2 digest: SHA-256 over n, e, rinv, mdash as they
    sit in a signature block. The same value espsecure.py
    digest_sbv2_public_key prints, so an operator can compare the two."""
    rinv = (1 << (KEY_BYTES * 16)) % n
    mdash = (-pow(n, -1, 1 << 32)) % (1 << 32)
    blob = n.to_bytes(KEY_BYTES, "little") + struct.pack("<I", e) + rinv.to_bytes(KEY_BYTES, "little") \
        + struct.pack("<I", mdash)
    return hashlib.sha256(blob).hexdigest()


# ── RSA-PSS (RFC 8017 §9.1.2) ───────────────────────────────────────────

def _mgf1(seed: bytes, length: int) -> bytes:
    out = b""
    for counter in range((length + 31) // 32):
        out += hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
    return out[:length]


def pss_verify(n: int, e: int, digest: bytes, signature: int) -> bool:
    em_bits = n.bit_length() - 1
    em_len = (em_bits + 7) // 8
    if signature >= n:
        return False
    em = pow(signature, e, n).to_bytes(em_len, "big")
    if em[-1] != 0xBC:
        return False
    masked_db, h = em[:em_len - 33], em[em_len - 33:-1]
    if masked_db[0] >> (8 - (8 * em_len - em_bits)):
        return False
    db = bytearray(a ^ b for a, b in zip(masked_db, _mgf1(h, len(masked_db))))
    db[0] &= 0xFF >> (8 * em_len - em_bits)
    ps_len = len(db) - SALT - 1
    if any(db[:ps_len]) or db[ps_len] != 0x01:
        return False
    salt = bytes(db[-SALT:])
    return hashlib.sha256(b"\x00" * 8 + digest + salt).digest() == h


# ── Signature sectors ───────────────────────────────────────────────────

def verify_signature(data: bytes, image_end: int) -> tuple[str, ...]:
    """() if nothing follows the image (unsigned). Otherwise check the padding
    and every signature block, and return the digests of the keys that signed
    it; raise SignatureError if anything is off."""
    tail = data[image_end:]
    if not tail:
        return ()
    sector_at = -(-image_end // SECTOR) * SECTOR
    if any(b != 0xFF for b in data[image_end:sector_at]) or len(data) - sector_at != SECTOR:
        raise SignatureError("unexpected data after the image (not an ESP-IDF signature sector)")
    digest = hashlib.sha256(data[:sector_at]).digest()
    sector = data[sector_at:]
    signers = []
    for i in range(3):
        block = sector[i * BLOCK:(i + 1) * BLOCK]
        if block[0] != MAGIC:
            break
        if block[1] != VERSION:
            raise SignatureError(f"signature block {i} is version {block[1]}, expected Secure Boot V2")
        if struct.unpack_from("<I", block, 1196)[0] != zlib.crc32(block[:1196]) & 0xFFFFFFFF:
            raise SignatureError(f"signature block {i} is corrupt (CRC mismatch)")
        if block[4:36] != digest:
            raise SignatureError("the image does not match its signature (modified after signing)")
        n = int.from_bytes(block[36:36 + KEY_BYTES], "little")
        e = struct.unpack_from("<I", block, 36 + KEY_BYTES)[0]
        sig = int.from_bytes(block[812:812 + KEY_BYTES], "little")
        if not pss_verify(n, e, digest, sig):
            raise SignatureError(f"signature block {i} is invalid")
        signers.append(key_digest(n, e))
    if not signers:
        raise SignatureError("signature sector has no signature block")
    if any(b != 0xFF for b in sector[len(signers) * BLOCK:]):
        raise SignatureError("unexpected data after the signature blocks")
    return tuple(signers)


@lru_cache(maxsize=1)
def _site_key(path: str) -> str:
    try:
        n, e = load_public_key(Path(path).read_text())
    except OSError as exc:
        raise SignatureError(f"can't read IMPRESS_FIRMWARE_SIGNING_KEY {path}: {exc.strerror}") from None
    return key_digest(n, e)


def site_key_digest() -> str | None:
    """Digest of the public key every image must be signed with
    (IMPRESS_FIRMWARE_SIGNING_KEY), or None when signing isn't required."""
    from ..config import settings
    path = settings.FIRMWARE_SIGNING_KEY.strip()
    return _site_key(path) if path else None
