"""Flashing, building and testing from the console: safe commands, the same on every platform."""

import io
import sys

import pytest

from app.console import Console
from app.services import devtools
from firmware_images import make_image


def _console(*lines):
    out = io.StringIO()
    con = Console(out=out)
    try:
        for line in lines:
            con.root_password = "Test-Root-Password-1!"
            con.onecmd(line)
    finally:
        con.close()
    return out.getvalue()


@pytest.mark.parametrize("port,ok", [("COM5", True), ("COM12", True), ("/dev/ttyUSB0", True), ("/dev/cu.usbmodem1101", True),
                                     ("/dev/ttyACM0", True), ("-p", False), ("COM5; rm -rf /", False), ("/etc/passwd", False),
                                     ("../../dev/ttyUSB0", False), ("", False), ("--chip", False)])
def test_only_serial_ports_are_accepted(port, ok):
    if ok:
        assert devtools.check_port(port) == port
    else:
        with pytest.raises(devtools.ToolError):
            devtools.check_port(port)


@pytest.mark.parametrize("name,chip", [("c6", "esp32c6"), ("gateway", "esp32c6"), ("s3", "esp32s3"), ("hub", "esp32s3"), ("student", "esp32")])
def test_every_role_maps_to_its_chip(name, chip):
    assert devtools.role(name)[1] == chip


def test_an_unknown_role_is_refused():
    with pytest.raises(devtools.ToolError):
        devtools.role("teacher")


def test_an_image_is_written_with_esptool_after_it_is_checked(tmp_path):
    good = tmp_path / "c6.bin"
    good.write_bytes(make_image("impress_class_c6"))
    cmd = devtools.flash_command("c6", "COM5", str(good))
    assert cmd[:3] == [sys.executable, "-m", "esptool"] and "esp32c6" in cmd and "write_flash" in cmd and "COM5" in cmd
    assert not any(" " in part and part != str(good) for part in cmd[3:]) and "shell" not in " ".join(cmd)


def test_an_image_for_another_chip_is_refused_before_anything_is_written(tmp_path):
    wrong = tmp_path / "s3.bin"
    wrong.write_bytes(make_image("impress_class_s3"))
    with pytest.raises(devtools.ToolError, match="esp32s3.*esp32c6|nothing was written"):
        devtools.flash_command("c6", "COM5", str(wrong))


def test_a_file_that_is_not_firmware_is_refused(tmp_path):
    junk = tmp_path / "x.bin"
    junk.write_bytes(b"not firmware")
    with pytest.raises(devtools.ToolError, match="not an imPress firmware image"):
        devtools.flash_command("student", "/dev/ttyUSB0", str(junk))
    with pytest.raises(devtools.ToolError):
        devtools.flash_command("student", "/dev/ttyUSB0", str(junk.with_name("missing.bin")))


def test_without_an_image_the_projects_own_flash_is_used(monkeypatch):
    monkeypatch.setattr(devtools.shutil, "which", lambda n: "/opt/idf/idf.py")
    cmd = devtools.flash_command("s3", "/dev/ttyACM0")
    assert cmd[0] == "idf.py" and cmd[-1] == "flash" and cmd[cmd.index("-C") + 1].endswith("firmware/class_s3") and "-p" in cmd


def test_missing_idf_is_explained_not_a_stack_trace(monkeypatch):
    monkeypatch.setattr(devtools.shutil, "which", lambda n: None)
    with pytest.raises(devtools.ToolError, match="--image FILE"):
        devtools.flash_command("c6", "COM5")
    with pytest.raises(devtools.ToolError):
        devtools.build_command("c6")


def test_test_suites_are_validated():
    assert devtools.test_command(["backend", "repo"])[-4:] == ["-s", "backend", "-s", "repo"]
    assert devtools.test_command([])[-1].endswith("run_tests.py")
    with pytest.raises(devtools.ToolError):
        devtools.test_command(["backend; rm -rf /"])


def test_ports_lists_what_the_platform_has(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(devtools.glob, "glob", lambda p: {"/dev/ttyUSB*": ["/dev/ttyUSB1"], "/dev/ttyACM*": ["/dev/ttyACM0"]}.get(p, []))
    assert "/dev/ttyUSB1" in devtools.ports() and "/dev/ttyACM0" in devtools.ports()
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(devtools.glob, "glob", lambda p: ["/dev/cu.usbmodem1101"] if p == "/dev/cu.usb*" else [])
    assert devtools.ports() == ["/dev/cu.usbmodem1101"]


def test_stream_passes_output_line_by_line_and_returns_the_exit_code():
    lines = []
    assert devtools.stream([sys.executable, "-c", "print('a'); print('b'); raise SystemExit(3)"], lines.append) == 3
    assert lines == ["a", "b"]


def test_the_console_dry_runs_flash_build_and_test(tmp_path, monkeypatch):
    monkeypatch.setattr(devtools.shutil, "which", lambda n: "/opt/idf/idf.py")
    image = tmp_path / "hub.bin"
    image.write_bytes(make_image("impress_class_s3"))
    text = _console("flash s3 /dev/ttyUSB0 --image %s --dry-run" % image, "flash student COM3 --dry-run", "build c6 --dry-run",
                    "test backend --dry-run", "flash s3 nonsense --dry-run", "flash teacher COM3", "test nope --dry-run", "ports")
    assert text.count("(dry run: nothing was started)") == 4
    assert "esptool" in text and "idf.py" in text and "run_tests.py" in text
    assert "does not look like a serial port" in text and "Unknown role" in text and "Unknown suite" in text and "HW_FLASH_FAILED" in text


def test_flashing_needs_root_s_password(monkeypatch):
    monkeypatch.delenv("IMPRESS_ROOT_PASSWORD")
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    out = io.StringIO()
    con = Console(out=out)
    try:
        con.onecmd("flash c6 COM5 --dry-run")
    finally:
        con.close()
    assert "ROOT_PASSWORD_REQUIRED" in out.getvalue() and "dry run" not in out.getvalue()
