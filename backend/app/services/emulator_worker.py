"""Boot the exact uploaded image in a pinned emulator (#176): the emulator stage of TrustedInstaller qualification.

The manifest (`backend/emulator/manifest.json`, IMPRESS_EMULATOR_MANIFEST) pins the runner (a path and its SHA-256) and, per
target, the bootloader and partition table of the build (each with a SHA-256). imPress never downloads anything: an operator
installs and pins them. The worker

 1. refuses unless the runner and the boot artifacts exist and match their pinned checksums;
 2. lays the uploaded app bytes into a flash image with that bootloader and partition table (never a different build);
 3. runs the runner **without a shell**, in a fresh temporary folder, with a clean environment, a wall-clock time-out,
    CPU and memory limits (POSIX), and its output capped;
 4. reads the output: any fail marker (abort, panic, Guru Meditation, no flash chip, reboot loop) fails; a pass marker is needed.

The result is a stage report like the other stages. Missing, unsupported, tampered, timed-out or failed emulation is `passed: False`
when policy `ota.require_emulation` is on (hardened), and `passed: None` ("not run") otherwise: never a pass.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from ..config import BACKEND_DIR

PARTITION_OFFSET, APP_OFFSET = 0x8000, 0x10000


def manifest_path() -> Path:
    return Path(os.environ.get("IMPRESS_EMULATOR_MANIFEST") or BACKEND_DIR / "emulator" / "manifest.json")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file(base: Path, rel: str | None, want: str | None, what: str) -> tuple[Path | None, str]:
    if not rel or not want:
        return None, f"{what} is not pinned in the manifest"
    p = Path(rel) if Path(rel).is_absolute() else base / rel
    if not p.is_file():
        return None, f"{what} {rel} does not exist"
    if _sha(p) != want.lower():
        return None, f"{what} {rel} does not match its pinned SHA-256 (replaced or corrupted)"
    return p, ""


def flash_image(app: bytes, bootloader: bytes, partitions: bytes, boot_offset: int, flash_mb: int) -> bytes:
    size = flash_mb * 1024 * 1024
    out = bytearray(b"\xff" * size)
    for offset, blob in ((boot_offset, bootloader), (PARTITION_OFFSET, partitions), (APP_OFFSET, app)):
        if offset + len(blob) > size:
            raise ValueError("the image does not fit the flash")
        out[offset:offset + len(blob)] = blob
    return bytes(out)


def judge(output: str, pass_markers: list, fail_markers: list, timed_out: bool, code: int | None) -> list[str]:
    problems = []
    if timed_out:
        problems.append("the emulator did not finish its run in time")
    low = output.lower()
    for marker in fail_markers:
        if marker.lower() in low:
            problems.append(f"the image failed to boot: its output contains {marker!r}")
    if not any(m.lower() in low for m in pass_markers):
        problems.append("the image never reached its first sign of life (no boot marker in the output)")
    if code not in (0, None) and not timed_out and not problems:
        problems.append(f"the emulator exited with code {code}")
    return problems


def _limits(cpu: int, memory_mb: int):
    def apply():                                           # POSIX only; Windows relies on the time-out
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
        resource.setrlimit(resource.RLIMIT_AS, (memory_mb * 2**20, memory_mb * 2**20))
    return apply if os.name == "posix" and sys.platform != "darwin" else None        # macOS does not honour RLIMIT_AS


def run(app: bytes, target: str, manifest: Path | None = None) -> dict:
    """{"ran": bool, "problems": [...], "note": str}. `ran` is False when nothing could be run (and `problems` says why)."""
    path = manifest or manifest_path()
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"ran": False, "problems": [f"the emulator manifest is unreadable ({exc})"], "note": ""}
    cfg = (doc.get("targets") or {}).get(target)
    if not cfg:
        return {"ran": False, "problems": [f"the manifest has no entry for {target}"], "note": ""}
    if not cfg.get("supported", False):
        return {"ran": False, "problems": [cfg.get("why") or f"the emulator does not support {target}"], "note": ""}
    base = path.parent
    runner_cfg = doc.get("runner") or {}
    runner, why = _file(base, runner_cfg.get("path"), runner_cfg.get("sha256"), "the emulator runner")
    if runner is None:
        return {"ran": False, "problems": [why], "note": runner_cfg.get("release", "")}
    boot, why = _file(base, cfg.get("bootloader"), cfg.get("bootloader_sha256"), "the bootloader")
    if boot is None:
        return {"ran": False, "problems": [why], "note": ""}
    parts, why = _file(base, cfg.get("partitions"), cfg.get("partitions_sha256"), "the partition table")
    if parts is None:
        return {"ran": False, "problems": [why], "note": ""}
    lim = doc.get("limits") or {}
    seconds, cap = int(lim.get("seconds", 30)), int(lim.get("output_kb", 512)) * 1024
    try:
        flash = flash_image(app, boot.read_bytes(), parts.read_bytes(), int(cfg.get("bootloader_offset", 0)), int(cfg.get("flash_mb", 4)))
    except ValueError as exc:
        return {"ran": True, "problems": [str(exc)], "note": ""}
    with tempfile.TemporaryDirectory(prefix="impress-emu-") as tmp:
        flash_path = Path(tmp) / "flash.bin"
        flash_path.write_bytes(flash)
        args = [a.replace("{chip}", cfg["chip"]).replace("{flash}", str(flash_path)) for a in runner_cfg.get("args", [])]
        env = {"PATH": os.defpath, "HOME": tmp, "TMPDIR": tmp, "LANG": "C"}                      # nothing of the server's environment
        timed_out, code, text = False, None, ""
        try:
            proc = subprocess.run([str(runner), *args], cwd=tmp, env=env, capture_output=True, timeout=seconds, stdin=subprocess.DEVNULL,
                                  preexec_fn=_limits(int(lim.get("cpu_seconds", 60)), int(lim.get("memory_mb", 1024))))
            code, text = proc.returncode, (proc.stdout + proc.stderr)[:cap].decode("utf-8", "replace")
        except subprocess.TimeoutExpired as exc:
            timed_out, text = True, ((exc.stdout or b"") + (exc.stderr or b""))[:cap].decode("utf-8", "replace")
        except OSError as exc:
            return {"ran": False, "problems": [f"the emulator could not start ({exc})"], "note": ""}
    return {"ran": True, "problems": judge(text, doc.get("pass_markers", []), doc.get("fail_markers", []), timed_out, code),
            "note": runner_cfg.get("release", "")}
