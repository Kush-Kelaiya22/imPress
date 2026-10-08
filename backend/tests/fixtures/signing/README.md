# Firmware signing test fixtures (#66)

Made with the real `espsecure.py` from the pinned ESP-IDF v6.1 image, so the
backend's verifier (`app/services/firmware_signing.py`) is tested against the
tool that devices and release builds use. **Test keys only**: the private keys
were thrown away and never committed.

| File | What |
|---|---|
| `key_a.pub`, `key_b.pub` | RSA-3072 public keys (PEM), `espsecure.py extract_public_key --version 2` |
| `c6_2.2.0_signed_a.img` | `make_image("impress_class_c6", "2.2.0")` signed with key A: `espsecure.py sign_data --version 2` |
| `c6_2.2.0_signed_ab.img` | the same image signed with keys A and B (two signature blocks) |

Key A's digest (`espsecure.py digest_sbv2_public_key`):
`e72c5da6eaa50b238e276e9ab76d78ba3f17051f9bbf3090c2cc884f6e9ead4c`

The extensions avoid `.bin` and `.pem`, which `.gitignore` excludes so that
real images and keys are never committed.
