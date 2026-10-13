#!/usr/bin/env python3
"""Boot a firmware image in Espressif's QEMU and judge the serial log (#154).

    scripts/qemu_boot.py --machine esp32s3 --image full.bin --flash-mb 16 \
        --expect "imPress S3 Class Module" --expect "EMULATOR: alive 6 s"

The image is a merged flash image (`idf.py merge-bin`) of an emulator build
(CONFIG_IMPRESS_EMULATOR, firmware/<project>/sdkconfig.qemu). It passes when
every --expect line appears, in order, before --seconds, and no line shows a
panic, abort, failed assert, watchdog, brownout or reset. Exit 0 = pass,
1 = fail, 2 = could not run. The log is written to --log.

QEMU emulates the CPU, flash, RAM and timers. It does not emulate the radio
or the SPI link to the gateway, and there is no emulator for the ESP32-C6.
"""

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time

FATAL = re.compile(r"Guru Meditation|abort\(\) was called|assert failed|Rebooting\.\.\.|"
                   r"Brownout detector|Task watchdog got triggered|Interrupt wdt timeout|stack overflow|"
                   r"rst:0x(?!1 )[0-9a-f]+ ")   # any reset reason other than power-on (0x1)
BINARIES = {"esp32": "qemu-system-xtensa", "esp32s3": "qemu-system-xtensa", "esp32c3": "qemu-system-riscv32"}


def find_qemu(machine: str) -> str | None:
    name = BINARIES[machine]
    return shutil.which(name) or next(iter(sorted(glob.glob(f"/opt/esp/tools/qemu-*/*/qemu/bin/{name}"))), None)


def judge(lines: list[str], expect: list[str]) -> tuple[bool, str]:
    """(passed, reason) for a captured log."""
    pending = list(expect)
    for line in lines:
        if FATAL.search(line):
            return False, f"fatal: {line.strip()}"
        if pending and pending[0] in line:
            pending.pop(0)
    return (not pending), ("all expected lines seen" if not pending else f"missing: {pending[0]!r}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--machine", required=True, choices=sorted(BINARIES))
    ap.add_argument("--image", required=True)
    ap.add_argument("--flash-mb", type=int, default=4, help="emulated flash size (2, 4, 8 or 16)")
    ap.add_argument("--expect", action="append", default=[], help="a log fragment that must appear (in order)")
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--log", default="qemu-boot.log")
    a = ap.parse_args(argv)

    qemu = find_qemu(a.machine)
    if not qemu:
        print(f"no {BINARIES[a.machine]} found (ESP-IDF: idf_tools.py install qemu-xtensa qemu-riscv32)")
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        flash = os.path.join(tmp, "flash.bin")
        data = open(a.image, "rb").read()
        size = a.flash_mb * 1024 * 1024
        if len(data) > size:
            print(f"image ({len(data)} bytes) larger than the {a.flash_mb} MB flash")
            return 1
        with open(flash, "wb") as f:
            f.write(data + b"\xff" * (size - len(data)))
        cmd = [qemu, "-nographic", "-machine", a.machine,
               "-drive", f"file={flash},if=mtd,format=raw", "-serial", "mon:stdio"]
        lines, deadline = [], time.monotonic() + a.seconds
        proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, errors="replace")
        reader = threading.Thread(target=lambda: lines.extend(iter(proc.stdout.readline, "")), daemon=True)
        reader.start()
        try:
            while time.monotonic() < deadline and proc.poll() is None:
                ok, why = judge(list(lines), a.expect)
                if ok or why.startswith("fatal"):
                    break
                time.sleep(0.2)
        finally:
            proc.kill()
            proc.wait()
            reader.join(timeout=2)
    open(a.log, "w").write("\n".join(lines))
    ok, why = judge(lines, a.expect)
    if proc.returncode not in (None, -9, 0) and not ok:
        why += f" (qemu exited {proc.returncode})"
    print(f"{'PASS' if ok else 'FAIL'} {a.machine} {os.path.basename(a.image)}: {why} ({len(lines)} log lines)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
