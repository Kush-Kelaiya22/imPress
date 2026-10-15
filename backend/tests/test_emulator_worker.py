"""#176: the emulator stage boots the exact uploaded image in a pinned, verified emulator, and never passes by default."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

from app import gpc
from app.services import emulator_worker as ew
from app.services import qualification
from firmware_images import make_image


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


@pytest.fixture
def kit(tmp_path):
    """A manifest with a fake runner (a Python script run by the current interpreter) and boot artifacts."""
    script = tmp_path / "fake_emulator.py"
    script.write_text(
        "import sys, pathlib\n"
        "flash = pathlib.Path(sys.argv[sys.argv.index('--flash-image') + 1]).read_bytes()\n"
        "mode = pathlib.Path(sys.argv[0]).with_name('mode.txt').read_text().strip()\n"
        "assert flash[0x10000:0x10000 + 4] == pathlib.Path(sys.argv[0]).with_name('app.head').read_bytes()\n"
        "if mode == 'ok': print('I (123) impress boot ok'); print('app_main started')\n"
        "elif mode == 'abort': print('E Octal Flash: No detected Flash chip'); print('abort() was called')\n"
        "elif mode == 'silent': print('nothing useful')\n"
        "elif mode == 'hang':\n    import time; time.sleep(60)\n"
        "elif mode == 'env': print('app_main', __import__('os').environ.get('IMPRESS_JWT_SECRET', 'clean'))\n")
    (tmp_path / "boot.bin").write_bytes(b"BOOT" * 8)
    (tmp_path / "parts.bin").write_bytes(b"PART" * 8)
    manifest = {"runner": {"path": sys.executable, "sha256": _sha(Path(sys.executable).read_bytes()), "release": "fake 1.0",
                           "args": [str(script), "--chip", "{chip}", "--flash-image", "{flash}"]},
                "limits": {"seconds": 5, "memory_mb": 1024, "output_kb": 64, "cpu_seconds": 30},
                "pass_markers": ["impress boot ok", "app_main"], "fail_markers": ["abort() was called", "No detected Flash chip"],
                "targets": {"c6": {"supported": True, "chip": "esp32c6", "flash_mb": 1, "bootloader": "boot.bin", "partitions": "parts.bin",
                                   "bootloader_sha256": _sha(b"BOOT" * 8), "partitions_sha256": _sha(b"PART" * 8), "bootloader_offset": 0},
                            "s3": {"supported": False, "chip": "esp32s3", "why": "octal flash is not emulated"}}}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    image = make_image("impress_class_c6")
    (tmp_path / "app.head").write_bytes(image[:4])
    (tmp_path / "mode.txt").write_text("ok")

    def set_mode(m):
        (tmp_path / "mode.txt").write_text(m)
    return {"path": path, "image": image, "mode": set_mode, "dir": tmp_path, "manifest": manifest}


def test_the_exact_uploaded_bytes_are_booted_with_the_builds_bootloader(kit):
    r = ew.run(kit["image"], "c6", kit["path"])                 # the fake runner asserts the app is at 0x10000 of the flash image
    assert r == {"ran": True, "problems": [], "note": "fake 1.0"}


def test_the_flash_image_layout():
    flash = ew.flash_image(b"APP", b"BOOT", b"PART", 0x1000, 1)
    assert len(flash) == 2**20 and flash[0x1000:0x1004] == b"BOOT" and flash[0x8000:0x8004] == b"PART" and flash[0x10000:0x10003] == b"APP"
    assert flash[:0x1000] == b"\xff" * 0x1000
    with pytest.raises(ValueError):
        ew.flash_image(b"x" * 2**20, b"B", b"P", 0, 1)


@pytest.mark.parametrize("mode,needle", [("abort", "No detected Flash chip"), ("silent", "first sign of life"), ("hang", "in time")])
def test_a_failed_silent_or_hanging_boot_fails(kit, mode, needle):
    kit["mode"](mode)
    r = ew.run(kit["image"], "c6", kit["path"])
    assert r["ran"] and any(needle in p for p in r["problems"]), r


def test_the_runner_gets_none_of_the_servers_environment(kit, monkeypatch):
    monkeypatch.setenv("IMPRESS_JWT_SECRET", "super-secret")
    kit["mode"]("env")
    assert ew.run(kit["image"], "c6", kit["path"])["problems"] == []


@pytest.mark.parametrize("tamper,needle", [
    (lambda m, d: m["runner"].update(sha256="0" * 64), "pinned SHA-256"),
    (lambda m, d: m["runner"].update(path=None), "not pinned"),
    (lambda m, d: m["targets"]["c6"].update(bootloader_sha256="0" * 64), "bootloader"),
    (lambda m, d: m["targets"]["c6"].update(partitions="missing.bin"), "does not exist"),
    (lambda m, d: m["targets"]["c6"].update(supported=False, why="nope"), "nope"),
    (lambda m, d: m["targets"].pop("c6"), "no entry"),
])
def test_anything_unpinned_missing_or_tampered_means_nothing_ran(kit, tamper, needle):
    tamper(kit["manifest"], kit["dir"])
    kit["path"].write_text(json.dumps(kit["manifest"]))
    r = ew.run(kit["image"], "c6", kit["path"])
    assert r["ran"] is False and needle in " ".join(r["problems"])


def test_an_unreadable_manifest_runs_nothing(tmp_path):
    bad = tmp_path / "m.json"
    bad.write_text("{ nope")
    assert ew.run(b"x", "c6", bad)["ran"] is False and ew.run(b"x", "c6", tmp_path / "none.json")["ran"] is False


def test_the_shipped_manifest_pins_nothing_and_marks_the_hub_unsupported():
    doc = json.loads((Path(__file__).resolve().parents[1] / "emulator/manifest.json").read_text())
    assert doc["runner"]["path"] is None and doc["targets"]["s3"]["supported"] is False and "Octal" in doc["targets"]["s3"]["why"]
    assert ew.run(b"x", "c6")["ran"] is False


# ── the stage and the policy ───────────────────────────────────────────

def test_without_a_runner_the_stage_is_not_run_never_a_pass(client):
    stage = qualification.emulator(make_image("impress_class_c6"), "c6")
    assert stage["passed"] is None and "not run" in stage["proves"]


def test_with_the_policy_on_a_missing_emulator_blocks_qualification(client, policy):
    policy({"ota.require_emulation": True})
    data = make_image("impress_class_c6")
    report = qualification.qualify(data, "c6", "2.1.0")
    assert report["status"] == "failed" and report["stages"][2]["passed"] is False
    assert "ota.require_emulation" in report["stages"][2]["problems"][0]


def test_the_policy_is_on_in_the_hardened_profile_only():
    f = gpc.FLAGS["ota.require_emulation"]
    assert f.standard is False and f.hardened is True and f.safe == "true"


def test_a_real_run_decides_the_stage(kit, monkeypatch, client):
    monkeypatch.setenv("IMPRESS_EMULATOR_MANIFEST", str(kit["path"]))
    assert qualification.emulator(kit["image"], "c6")["passed"] is True
    kit["mode"]("abort")
    stage = qualification.emulator(kit["image"], "c6")
    assert stage["passed"] is False and "No detected Flash chip" in " ".join(stage["problems"])
    assert qualification.qualify(kit["image"], "c6", "2.1.0")["status"] == "failed"
