"""TrustedInstaller qualification of a firmware image (#154).

Before an image can be approved, and again before it is offered to a device,
the TrustedInstaller needs a passing report. Each stage says what it proves:

1. analysis      what the bootloader checks before it runs an image: magic,
                 chip, segment count, every segment inside a real memory
                 region of that chip, entry point in executable memory,
                 checksum byte, appended SHA-256, chip-revision range, and
                 the imPress rules (project, version, slot size, signature).
2. ota_client    the device's OTA client (firmware/class_c6/main/ota.c and
                 ota_logic.c, class_s3/main/ota.c), simulated in Python
                 against this image: offer, download with an interruption,
                 digest check, esp_ota_end checks, reboot into the version.
                 It must accept this image and refuse every corrupted variant.
3. emulator      not run on the uploaded binary: QEMU cannot emulate the
                 production flash configuration (octal flash on the hub, QIO
                 on the module) and there is no ESP32-C6 emulator. The CI job
                 "Emulator boot test" boots the hub and module firmware of
                 every source revision instead (scripts/qemu_boot.py).
4. canary        the first real device of every deployment (existing).

A report is plain data: {"status": "qualified"|"failed", "stages": [...]}.
The TrustedInstaller stores it attested (attest() below): bound to the image's
digest and build identity and sealed with a server key, so a report edited
in the database, or copied from another image, is not trusted.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import struct

from .firmware_image import CHIP_IDS, CHIPS, IMAGE_MAGIC, PROJECTS, SLOT_BYTES, ImageError, image_end, parse_image

# Address ranges each chip can load a segment into (from the ESP-IDF memory
# maps, as esptool lists them). A segment outside them cannot be loaded.
MEMORY = {
    "esp32": {
        "flash": [(0x3F400000, 0x3F800000), (0x400D0000, 0x40400000)],          # DROM, IROM
        "ram": [(0x3FFAE000, 0x40000000), (0x40070000, 0x400A0000),             # DRAM, IRAM
                (0x3FF80000, 0x3FF82000), (0x400C0000, 0x400C2000), (0x50000000, 0x50002000)],  # RTC
        "exec": [(0x40070000, 0x400A0000), (0x400C0000, 0x400C2000), (0x400D0000, 0x40400000)],
    },
    "esp32s3": {
        "flash": [(0x3C000000, 0x3E000000), (0x42000000, 0x44000000)],
        "ram": [(0x3FC88000, 0x3FD00000), (0x40370000, 0x403E0000),
                (0x600FE000, 0x60100000), (0x50000000, 0x50002000)],
        "exec": [(0x40370000, 0x403E0000), (0x600FE000, 0x60100000), (0x42000000, 0x44000000)],
    },
    "esp32c6": {
        "flash": [(0x42000000, 0x43000000)],                                   # IROM and DROM share the cache
        "ram": [(0x40800000, 0x40880000), (0x50000000, 0x50004000)],          # HP SRAM, LP SRAM
        "exec": [(0x40800000, 0x40880000), (0x50000000, 0x50004000), (0x42000000, 0x43000000)],
    },
}
OTA_FLOW = ("queued", "precheck", "downloading", "verifying", "installing", "rebooting", "health_check", "success")


def _inside(addr: int, length: int, ranges) -> bool:
    return any(lo <= addr and addr + length <= hi for lo, hi in ranges)


def _segments(data: bytes):
    pos = 24
    for _ in range(data[1]):
        addr, length = struct.unpack_from("<II", data, pos)
        yield addr, length, data[pos + 8:pos + 8 + length]
        pos += 8 + length


def bootloader_checks(data: bytes, chip: str) -> list[str]:
    """What the second-stage bootloader would refuse; [] if it would load it."""
    problems = []
    if len(data) < 24 or data[0] != IMAGE_MAGIC:
        return ["not an ESP-IDF image (magic byte)"]
    if CHIPS.get(struct.unpack_from("<H", data, 12)[0]) != chip:
        problems.append(f"header chip is not {chip}")
    try:
        end = image_end(data)
    except ImageError as e:
        return problems + [str(e)]
    if end > len(data):
        return problems + ["image is truncated"]
    mem, checksum = MEMORY[chip], 0xEF
    for i, (addr, length, body) in enumerate(_segments(data)):
        if not _inside(addr, length, mem["flash"] + mem["ram"]):
            problems.append(f"segment {i} at 0x{addr:08x} (+{length}) is outside {chip} memory")
        for b in body:
            checksum ^= b
    entry = struct.unpack_from("<I", data, 4)[0]
    if not _inside(entry, 1, mem["exec"]):
        problems.append(f"entry point 0x{entry:08x} is not executable memory on {chip}")
    cs_at = end - (33 if data[23] == 1 else 1)
    if data[cs_at] != checksum:
        problems.append("segment checksum byte does not match")
    if data[23] == 1 and hashlib.sha256(data[:end - 32]).digest() != data[end - 32:end]:
        problems.append("appended SHA-256 does not match")
    min_rev, max_rev = struct.unpack_from("<HH", data, 15)
    if max_rev and min_rev > max_rev:
        problems.append(f"chip revision range is empty ({min_rev} > {max_rev})")
    return problems


def _stage(name: str, problems: list[str], proves: str) -> dict:
    return {"stage": name, "passed": not problems, "problems": problems, "proves": proves}


def analysis(data: bytes, target: str) -> dict:
    problems = []
    try:
        info = parse_image(data)                     # imPress rules: project, version, hash, signature, slot
        if info.target != target:
            problems.append(f"image is for {info.target}, registered as {target}")
    except ImageError as e:
        problems.append(str(e))
    problems += bootloader_checks(data, PROJECTS_BY_TARGET[target][1])
    return _stage("analysis", problems, "the bootloader of this chip would load it, and it is a valid imPress image")


PROJECTS_BY_TARGET = {target: (project, chip) for project, (target, chip) in PROJECTS.items()}


class _Device:
    """The OTA client of a gateway or hub, as the firmware implements it."""

    def __init__(self, target: str, running: str):
        self.target, self.chip = target, PROJECTS_BY_TARGET[target][1]
        self.running, self.states = running, []

    def update(self, offer: dict, fetch) -> tuple[bool, str]:
        """offer: what /firmware/check returns; fetch(): the downloaded bytes."""
        o = offer
        if not (o.get("version", "").count(".") == 2 and len(o.get("sha256", "")) == 64 and o.get("size", 0) > 0):
            return False, "offer unusable (ota_parse_check)"
        self.states += ["queued", "precheck"]
        if o["size"] > SLOT_BYTES[self.target]:
            return False, "esp_ota_begin: image larger than the OTA slot"
        self.states.append("downloading")
        data = fetch()
        if data is None:
            return False, "download interrupted: boot partition not changed"
        if len(data) != o["size"]:
            return False, "downloaded size differs from the offer"
        self.states.append("verifying")
        if hashlib.sha256(data).hexdigest() != o["sha256"]:
            return False, "SHA-256 differs from the offer (ota_digest_matches)"
        problems = bootloader_checks(data, self.chip)          # esp_ota_end validates the same things
        if problems:
            return False, "esp_ota_end: " + problems[0]
        self.states += ["installing", "rebooting"]
        self.running = data[48:80].split(b"\0", 1)[0].decode(errors="replace")
        self.states.append("health_check")
        if self.running != o["version"]:
            return False, f"rebooted into {self.running}, expected {o['version']}"
        self.states.append("success")
        return True, ""


def ota_client(data: bytes, target: str, version: str) -> dict:
    """The image must go through the simulated client, and each corruption
    must be refused before the boot partition changes."""
    problems = []
    offer = {"version": version, "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
    interrupted = [True]

    def flaky():                                    # the first download breaks off; the retry completes
        if interrupted[0]:
            interrupted[0] = False
            return None
        return data

    dev = _Device(target, "0.0.0")
    ok, why = dev.update(offer, flaky)
    if ok or "interrupted" not in why or dev.running != "0.0.0":
        problems.append("an interrupted download was not refused before installing")
    dev = _Device(target, "0.0.0")
    ok, why = dev.update(offer, flaky)
    if not ok:
        problems.append(f"the device would not install it: {why}")
    elif tuple(dev.states) != OTA_FLOW:
        problems.append(f"state sequence {dev.states} is not the deployment flow")

    other = next(t for t in PROJECTS_BY_TARGET if t != target)
    flipped = bytearray(data)
    struct.pack_into("<H", flipped, 12, CHIP_IDS[PROJECTS_BY_TARGET[other][1]])
    for label, variant in (("one flipped byte", data[:len(data) // 2] + bytes([data[len(data) // 2] ^ 0xFF])
                            + data[len(data) // 2 + 1:]),
                           ("a truncated download", data[:-100]),
                           ("another chip's header", bytes(flipped))):
        dev = _Device(target, "0.0.0")
        ok, _ = dev.update(offer, lambda v=variant: v)
        if ok or dev.running != "0.0.0":
            problems.append(f"the device would have installed {label}")
    return _stage("ota_client", problems, "the device's OTA client installs it and refuses corrupted or "
                  "interrupted transfers without switching its boot partition")


def emulator(data: bytes, target: str) -> dict:
    """Boot the exact uploaded bytes in the pinned emulator (services/emulator_worker.py, #176). When nothing could be run the stage
    is "not run" (passed None) in the standard profile and a FAILURE when policy ota.require_emulation is on: never a pass."""
    from .. import gpc
    from . import emulator_worker
    proves = "the exact uploaded image boots in the pinned emulator with the build's own bootloader and partition table"
    result = emulator_worker.run(data, target)
    if result["ran"]:
        return _stage("emulator", result["problems"], proves)
    if gpc.get("ota.require_emulation"):
        return {"stage": "emulator", "passed": False, "problems": ["emulation is required (policy ota.require_emulation) and could "
                "not be run: " + "; ".join(result["problems"])], "proves": proves}
    return {"stage": "emulator", "passed": None, "problems": [],
            "proves": "not run: " + "; ".join(result["problems"]) + ". CI boots the hub and module source in QEMU for every change"}


def qualify(data: bytes, target: str, version: str) -> dict:
    stages = [analysis(data, target), ota_client(data, target, version), emulator(data, target)]
    passed = all(s["passed"] is not False for s in stages)
    return {"status": "qualified" if passed else "failed", "stages": stages}


# ── Attestation (v2.2) ───────────────────────────────────────────────────
# Bump QUALIFIER when the stages change: older reports are then recomputed.
QUALIFIER = "impress-ti/3"
SUBJECT_FIELDS = ("sha256", "size", "target", "chip", "project", "version", "idf_version", "elf_sha256", "signer")


def _key() -> bytes:
    """A key only the server holds, derived from IMPRESS_JWT_SECRET (kept out
    of the database and the repository). Rotating that secret makes every
    stored report untrusted, so each is recomputed from its image."""
    from ..config import settings
    return hashlib.sha256(b"impress.trusted-installer.report\0" + settings.JWT_SECRET.encode()).digest()


def subject(artifact) -> dict:
    """What the report is about: the exact bytes and the build that made them."""
    return {f: getattr(artifact, f) for f in SUBJECT_FIELDS}


def _seal(body: dict) -> str:
    canonical = json.dumps({k: v for k, v in body.items() if k != "attestation"},
                           sort_keys=True, separators=(",", ":"), default=str)
    return hmac.new(_key(), canonical.encode(), hashlib.sha256).hexdigest()


def attest(report: dict, artifact) -> dict:
    body = {**report, "subject": subject(artifact), "qualifier": QUALIFIER}
    body["attestation"] = _seal(body)
    return body


def attested(report, artifact) -> bool:
    """Made by this server's TrustedInstaller, by the current stages, for
    exactly this image."""
    return (isinstance(report, dict) and isinstance(report.get("attestation"), str)
            and report.get("qualifier") == QUALIFIER and report.get("subject") == subject(artifact)
            and hmac.compare_digest(report["attestation"], _seal(report)))
