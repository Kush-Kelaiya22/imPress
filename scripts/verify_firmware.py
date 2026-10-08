#!/usr/bin/env python3
"""Check a firmware image the way the backend will at upload (#35, #66),
before uploading it. Standard library only.

  scripts/verify_firmware.py firmware/class_c6/build/signed/impress_class_c6.bin \\
      --key ~/.impress/firmware-signing/signing_key.pub

Prints the image's facts and signers; with --key, exits 1 unless that key
signed it. Exits 1 on any invalid image.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.services.firmware_image import ImageError, parse_image  # noqa: E402
from app.services.firmware_signing import SignatureError, key_digest, load_public_key  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("image")
    ap.add_argument("--key", help="public key (PEM) that must have signed it")
    a = ap.parse_args()
    try:
        info = parse_image(Path(a.image).read_bytes())
    except (ImageError, OSError) as e:
        print(f"INVALID: {e}")
        return 1
    print(f"{info.project} {info.version} for {info.chip} ({info.target}), {info.size} bytes, IDF {info.idf_version}")
    print(f"sha256 {info.sha256}")
    print("signers: " + (", ".join(info.signers) if info.signers else "none (unsigned)"))
    if a.key:
        try:
            want = key_digest(*load_public_key(Path(a.key).read_text()))
        except (SignatureError, OSError) as e:
            print(f"bad key: {e}")
            return 1
        if want not in info.signers:
            print(f"NOT signed with {a.key} (digest {want})")
            return 1
        print(f"OK: signed with {a.key}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
