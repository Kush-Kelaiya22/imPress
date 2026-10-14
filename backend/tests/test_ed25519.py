"""Ed25519 (stdlib) against the RFC 8032 section 7.1 test vectors."""

import pytest

from app import ed25519

VECTORS = [   # secret, public, message, signature
    ("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
     "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a", "",
     "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"),
    ("4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
     "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c", "72",
     "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da085ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"),
]


@pytest.mark.parametrize("secret,public,message,signature", VECTORS)
def test_rfc8032_vectors(secret, public, message, signature):
    seed, msg = bytes.fromhex(secret), bytes.fromhex(message)
    assert ed25519.public_key(seed).hex() == public
    assert ed25519.sign(seed, msg).hex() == signature
    assert ed25519.verify(bytes.fromhex(public), msg, bytes.fromhex(signature))


def test_round_trip_and_tampering():
    seed = ed25519.generate_seed()
    pub = ed25519.public_key(seed)
    sig = ed25519.sign(seed, b"policy v1")
    assert ed25519.verify(pub, b"policy v1", sig)
    assert not ed25519.verify(pub, b"policy v2", sig)                       # message changed
    assert not ed25519.verify(pub, b"policy v1", sig[:-1] + bytes([sig[-1] ^ 1]))   # signature changed
    assert not ed25519.verify(ed25519.public_key(ed25519.generate_seed()), b"policy v1", sig)   # another key
    assert not ed25519.verify(pub, b"policy v1", sig[:63])                 # short
    assert not ed25519.verify(pub[:31], b"policy v1", sig)
    assert not ed25519.verify(b"\xff" * 32, b"x", b"\xff" * 64)            # not a curve point: no exception


def test_key_id_is_stable_and_short():
    pub = ed25519.public_key(bytes(32))
    assert ed25519.key_id(pub) == ed25519.key_id(pub) and len(ed25519.key_id(pub)) == 16
