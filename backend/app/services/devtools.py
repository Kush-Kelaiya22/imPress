"""Flash the boards, build the firmware and run the test suites from the root console (v2.2).

Everything a person would do in a terminal to bring a classroom up, with the same commands on Windows, macOS and Linux:

    ports                                    which serial ports exist
    flash ROLE PORT [--image FILE]           write the firmware (ROLE: c6 gateway | s3 hub | student module)
    build ROLE                               build a role's firmware with ESP-IDF (idf.py)
    test [SUITE ...]                         run_tests.py: backend, repo, firmware-static, host, ...

`flash` with `--image` writes a finished image with esptool, after checking that the file is an imPress image for that role's
chip (parse_image); without it, it runs `idf.py flash` in the role's project, which installs the matching bootloader,
partition table and app together (the first flash of a board must be that one). Every command is built as an argument list (never
through a shell), the port must look like a serial port, and `--dry-run` shows what would run. Output streams line by line.
Flashing asks for root's password (rootauth).
"""

from __future__ import annotations

import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .firmware_image import ImageError, parse_image

ROOT = Path(__file__).resolve().parents[3]
ROLES = {"c6": ("class_c6", "esp32c6", "gateway"), "gateway": ("class_c6", "esp32c6", "gateway"),
         "s3": ("class_s3", "esp32s3", "hub"), "hub": ("class_s3", "esp32s3", "hub"),
         "student": ("student", "esp32", "student module")}
PORT_RE = re.compile(r"^(COM\d{1,3}|/dev/(tty|cu)\.?[A-Za-z0-9_.\-]+)$")
SUITES = ("backend", "repo", "firmware-static", "host", "frontend", "ui", "idf")


class ToolError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code, self.message = code, message


def ports() -> list[str]:
    """Serial ports that look like boards, whatever the platform."""
    found: list[str] = []
    try:
        from serial.tools import list_ports                        # when pyserial is installed (it comes with esptool)
        found = [p.device for p in list_ports.comports()]
    except ImportError:
        pass
    if sys.platform == "darwin":
        found += glob.glob("/dev/cu.usb*") + glob.glob("/dev/cu.wchusbserial*") + glob.glob("/dev/cu.SLAB*")
    elif sys.platform.startswith("linux"):
        found += glob.glob("/dev/ttyUSB*") + glob.glob("/dev/ttyACM*")
    elif sys.platform == "win32" and not found:
        out = subprocess.run(["powershell", "-NoProfile", "-Command", "[System.IO.Ports.SerialPort]::GetPortNames()"],
                             capture_output=True, text=True, timeout=10).stdout
        found = re.findall(r"COM\d+", out)
    return sorted(set(found))


def role(name: str) -> tuple[str, str, str]:
    if name.lower() not in ROLES:
        raise ToolError("HW_FLASH_FAILED", f"Unknown role {name!r}: use c6 (gateway), s3 (hub) or student.")
    return ROLES[name.lower()]


def check_port(port: str) -> str:
    if not PORT_RE.match(port):
        raise ToolError("HW_FLASH_FAILED", f"{port!r} does not look like a serial port (COM5, /dev/ttyUSB0, /dev/cu.usbmodem...).")
    return port


def flash_command(name: str, port: str, image: str | None = None) -> list[str]:
    project, chip, _ = role(name)
    check_port(port)
    if image:
        path = Path(image)
        try:
            info = parse_image(path.read_bytes())
        except (OSError, ImageError) as exc:
            raise ToolError("HW_FLASH_FAILED", f"{image}: not an imPress firmware image ({exc})") from None
        if info.chip != chip:
            raise ToolError("HW_FLASH_FAILED", f"{image} is for {info.chip}, but a {name} board is {chip}: nothing was written.")
        return [sys.executable, "-m", "esptool", "--chip", chip, "--port", port, "write_flash", "0x10000", str(path)]
    if not shutil.which("idf.py"):
        raise ToolError("HW_FLASH_FAILED", "idf.py was not found: install ESP-IDF v6.1 and open its environment (firmware/activate_idf.ps1 on "
                        "Windows), or give a finished image with --image FILE (needs: pip install esptool).")
    return ["idf.py", "-C", str(ROOT / "firmware" / project), "-p", port, "flash"]


def build_command(name: str) -> list[str]:
    project, _, _ = role(name)
    if not shutil.which("idf.py"):
        raise ToolError("HW_FLASH_FAILED", "idf.py was not found: install ESP-IDF v6.1 and open its environment.")
    return ["idf.py", "-C", str(ROOT / "firmware" / project), "build"]


def test_command(suites: list[str]) -> list[str]:
    bad = [s for s in suites if not any(x.startswith(s) for x in SUITES)]
    if bad:
        raise ToolError("ROOT_COMMAND_FAILED", f"Unknown suite {bad[0]!r}: {', '.join(SUITES)}.")
    cmd = [sys.executable, str(ROOT / "run_tests.py")]
    for s in suites:
        cmd += ["-s", s]
    return cmd


def stream(cmd: list[str], emit, cwd: Path | None = None) -> int:
    """Run `cmd` (never through a shell), pass its output to `emit` line by line, return its exit code."""
    try:
        proc = subprocess.Popen(cmd, cwd=cwd or ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, bufsize=1, env={**os.environ, "PYTHONUNBUFFERED": "1", "NO_COLOR": "1"})
    except OSError as exc:
        raise ToolError("ROOT_COMMAND_FAILED", f"could not start {cmd[0]}: {exc}") from None
    for line in proc.stdout:
        emit(line.rstrip("\n"))
    return proc.wait()
