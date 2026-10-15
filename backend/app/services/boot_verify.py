"""TrustedInstaller's start-up check (v2.2): the server is locked down until the host has been verified.

At every start TrustedInstaller looks at where imPress is running (operating system, Python and SQLite versions,
processor, memory, free disk, the data folder, the clock, whether it is inside a container) and compares it with
the minimum a classroom server needs. Until it has finished, every request is refused (`locked()`).

* everything passes: the features are as the administrators left them last session (nothing is changed);
* something fails that only some features need (memory, disk, processor): those features are switched off by
  TrustedInstaller, with the reason, and come back on their own at the first start that passes;
* something fails that nothing can run without (Python, SQLite, a writable data folder): imPress stays locked
  and says why.

Inside a container the separate root console is switched off (policy flag root.allow_access): the console
attached to the container is root's there.
"""

from __future__ import annotations

import ctypes
import os
import platform
import shutil
import sqlite3
import ssl
import subprocess
import sys
import time
from pathlib import Path

from .. import gpc
from ..config import settings

MINIMUM = {"python": (3, 12), "sqlite": (3, 35, 0), "cores": 2, "memory_mb": 1024, "disk_mb": 2048, "year": 2024}

# what each soft requirement protects: features that are switched off when it fails
GATES = {
    "memory": ["advanced_mode", "activity_charts", "presence", "backups", "search"],
    "cores": ["traffic_monitor", "activity_charts"],
    "disk": ["backups", "trash"],
}

_report: dict = {"at": None, "passed": False, "locked": True, "checks": [], "container": False, "host": {}}


def locked() -> bool:
    return bool(_report["locked"])


def report() -> dict:
    return _report


def in_container() -> bool:
    if os.environ.get("IMPRESS_IN_CONTAINER"):
        return os.environ["IMPRESS_IN_CONTAINER"].lower() in ("1", "true", "yes")
    if Path("/.dockerenv").exists() or Path("/run/.containerenv").exists():
        return True
    try:
        return any(w in Path("/proc/1/cgroup").read_text() for w in ("docker", "kubepods", "containerd"))
    except OSError:
        return False


def memory_mb() -> int | None:
    try:
        if sys.platform.startswith("linux"):
            for line in Path("/proc/meminfo").read_text().splitlines():
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) // 1024
        if sys.platform == "darwin":
            return int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5).stdout) // 2**20
        if sys.platform == "win32":
            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("m", ctypes.c_ulong), ("total", ctypes.c_ulonglong)] + \
                           [(f"x{i}", ctypes.c_ulonglong) for i in range(5)]
            ms = MS()
            ms.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(ms))
            return int(ms.total) // 2**20
    except Exception:                                    # noqa: BLE001
        pass
    return None


def volume_encrypted(path: Path | None = None) -> bool | None:
    """Is the volume that holds the data folder encrypted? True / False when it can be seen, None when it cannot
    (containers, Windows, network volumes): decision D16, #212. Best effort and read-only."""
    path = path or _data_dir()
    try:
        if sys.platform == "darwin":
            out = subprocess.run(["fdesetup", "status"], capture_output=True, text=True, timeout=5).stdout
            return "On" in out if "FileVault" in out else None
        if sys.platform.startswith("linux") and not in_container():
            source = subprocess.run(["findmnt", "-no", "SOURCE", "--target", str(path)], capture_output=True, text=True,
                                    timeout=5).stdout.strip()
            if not source.startswith("/dev/"):
                return None
            types = subprocess.run(["lsblk", "-s", "-no", "TYPE", source], capture_output=True, text=True, timeout=5).stdout.split()
            return "crypt" in types if types else None
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _minimum(name: str):
    env = os.environ.get(f"IMPRESS_MIN_{name.upper()}")
    return int(env) if env and env.isdigit() else MINIMUM[name]


def _data_dir() -> Path:
    url = settings.DATABASE_URL
    if ":///" in url:
        p = Path(url.split(":///", 1)[1]).resolve().parent
        return p if p.exists() else Path.cwd()
    return Path.cwd()


def _check(id_: str, title: str, ok: bool, detail: str, need: str, critical: bool = False, gates: list[str] | None = None) -> dict:
    return {"id": id_, "title": title, "ok": bool(ok), "detail": detail, "minimum": need, "critical": critical, "gates": gates or []}


def inspect() -> tuple[list[dict], dict]:
    mem, cores = memory_mb(), os.cpu_count() or 1
    disk = shutil.disk_usage(_data_dir()).free // 2**20
    try:
        probe = _data_dir() / ".impress-write-test"
        probe.write_text("x")
        probe.unlink()
        writable = True
    except OSError:
        writable = False
    py, sq = sys.version_info[:3], tuple(int(x) for x in sqlite3.sqlite_version.split("."))
    fmt = lambda t: ".".join(str(x) for x in t)           # noqa: E731
    host = {"os": f"{platform.system()} {platform.release()}", "machine": platform.machine(),
            "python": fmt(py), "sqlite": sqlite3.sqlite_version, "openssl": ssl.OPENSSL_VERSION, "cores": cores,
            "memory_mb": mem, "disk_free_mb": disk, "container": in_container()}
    checks = [
        _check("os", "Operating system", platform.system() in ("Linux", "Darwin", "Windows"), host["os"],
               "Linux, macOS or Windows", critical=True),
        _check("arch", "64-bit platform", sys.maxsize > 2**32, platform.machine(), "64-bit", critical=True),
        _check("python", "Python", py >= MINIMUM["python"], fmt(py), fmt(MINIMUM["python"]) + " or newer", critical=True),
        _check("sqlite", "SQLite", sq >= MINIMUM["sqlite"], sqlite3.sqlite_version, fmt(MINIMUM["sqlite"]) + " or newer", critical=True),
        _check("data", "Data folder is writable", writable, str(_data_dir().name) + (" (writable)" if writable else " (read-only)"),
               "writable", critical=True),
        _check("clock", "System clock", time.gmtime().tm_year >= MINIMUM["year"], time.strftime("%Y-%m-%d", time.gmtime()),
               f"year {MINIMUM['year']} or later"),
        _check("cores", "Processor cores", cores >= _minimum("cores"), str(cores), f"{_minimum('cores')} or more", gates=GATES["cores"]),
        _check("memory", "Memory", mem is None or mem >= _minimum("memory_mb"),
               "unknown" if mem is None else f"{mem} MB", f"{_minimum('memory_mb')} MB", gates=GATES["memory"]),
        _check("disk", "Free disk space", disk >= _minimum("disk_mb"), f"{disk} MB", f"{_minimum('disk_mb')} MB", gates=GATES["disk"]),
    ]
    return checks, host


async def run(db) -> dict:
    """Verify the host, apply what that means for the features, and open the server (or keep it locked)."""
    from . import features
    _report.update(locked=True)
    checks, host = inspect()
    failed = [c for c in checks if not c["ok"]]
    critical = [c for c in failed if c["critical"]]
    gated: dict[str, str] = {}
    for c in failed:
        for name in c["gates"]:
            gated.setdefault(name, f"{c['title']}: {c['detail']} is below the minimum of {c['minimum']}")
    for name in features.FEATURES:
        if name in gated:
            await features.trusted_set(db, name, False, gated[name])
        else:
            await features.trusted_set(db, name, True, "The host meets the minimum requirements")
    if host["container"] and gpc.get("root.allow_access"):
        gpc.current().values["root.allow_access"] = False
        await features.log(db, "root.allow_access", "on", "off", "TrustedInstaller", features.TRUSTED,
                           "Running in a container: use the console attached to it")
    await features.load(db)
    _report.update(at=time.time(), passed=not failed, locked=bool(critical), checks=checks, host=host,
                   container=host["container"], gated=sorted(gated),
                   summary=("The host meets the minimum requirements." if not failed else
                            "Below the minimum: " + "; ".join(f"{c['title']} ({c['detail']}, needs {c['minimum']})" for c in failed)))
    await features.log(db, "boot.verification", "", "passed" if not failed else "failed", "TrustedInstaller", features.TRUSTED,
                       _report["summary"][:240])
    return _report
