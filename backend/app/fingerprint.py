"""A device fingerprint (v2.2): what stays the same on this machine however imPress is moved, renamed or updated.

Used by integrity protection (services/iips.py) to bind the program's reference hashes to the machine they were made on, so
code and reference copied (or pasted) onto another machine are flagged. It must not change when things that change often
change, so it uses **none** of: IP address, host name, operating-system version, Python version, user name, the folder the
program is in. It takes the first of these that exists, strongest first:

    1. the platform's hardware UUID     macOS IOPlatformUUID, Windows SMBIOS UUID, Linux /sys/class/dmi/id/product_uuid
    2. the machine id of the installation   /etc/machine-id, Windows MachineGuid
    3. the lowest MAC address of a physical network adapter   (virtual, bridge, docker and veth adapters are skipped)

and hashes it with a fixed label, so the id itself is never stored. `IMPRESS_DEVICE_ID` replaces all of this (a cloned virtual
machine that must keep working, or a test). In a container there is no machine to bind to: the fingerprint is None and binding
is not applied (the image carries its own read-only reference).
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path

_BAD = {"", "00000000-0000-0000-0000-000000000000", "ffffffff-ffff-ffff-ffff-ffffffffffff", "03000200-0400-0500-0006-000700080009",
        "to be filled by o.e.m.", "none", "default string", "0"}
_cache: dict = {}


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=8).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def _usable(value: str | None) -> str | None:
    v = (value or "").strip().strip('"').lower()
    return v if v and v not in _BAD and set(v) - set("0-:") else None


def _hardware_uuid() -> str | None:
    if sys.platform == "darwin":
        m = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', _run(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]))
        return _usable(m.group(1) if m else None)
    if sys.platform.startswith("linux"):
        try:
            return _usable(Path("/sys/class/dmi/id/product_uuid").read_text())
        except OSError:
            return None
    if sys.platform == "win32":
        out = _run(["wmic", "csproduct", "get", "uuid"]) or _run(
            ["powershell", "-NoProfile", "-Command", "(Get-CimInstance Win32_ComputerSystemProduct).UUID"])
        m = re.search(r"[0-9A-Fa-f]{8}(?:-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}", out)
        return _usable(m.group(0) if m else None)
    return None


def _machine_id() -> str | None:
    if sys.platform.startswith("linux"):
        for p in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                if (v := _usable(Path(p).read_text())):
                    return v
            except OSError:
                continue
    if sys.platform == "win32":
        m = re.search(r"MachineGuid\s+REG_SZ\s+(\S+)", _run(["reg", "query", r"HKLM\SOFTWARE\Microsoft\Cryptography", "/v", "MachineGuid"]))
        return _usable(m.group(1) if m else None)
    return None


def _physical_macs() -> list[str]:
    macs: list[str] = []
    if sys.platform.startswith("linux"):
        base = Path("/sys/class/net")
        for nic in sorted(base.iterdir()) if base.exists() else []:
            if (nic / "device").exists() and not (nic / "bridge").exists() and nic.name != "lo":     # a real adapter
                try:
                    macs.append(_usable((nic / "address").read_text()) or "")
                except OSError:
                    pass
    elif sys.platform == "darwin":
        for name in re.findall(r"^(en\d+):", _run(["ifconfig", "-l", "-u"]).replace(" ", ":\n") + ":", re.M)[:6]:
            m = re.search(r"ether\s+([0-9a-f:]{17})", _run(["ifconfig", name]))
            if m:
                macs.append(m.group(1))
    elif sys.platform == "win32":
        macs = re.findall(r"([0-9A-F]{2}(?:-[0-9A-F]{2}){5})", _run(["getmac", "/fo", "csv", "/nh"]))
    node = uuid.getnode()
    if not (node >> 40) & 1 and not macs:                       # a real MAC (the multicast bit is set on invented ones)
        macs.append(":".join(f"{(node >> s) & 255:02x}" for s in range(40, -1, -8)))
    return sorted(m.lower().replace("-", ":") for m in macs if m)


def compute() -> tuple[str | None, str]:
    """(fingerprint hex or None, how it was made)."""
    if (forced := os.environ.get("IMPRESS_DEVICE_ID", "").strip()):
        kind, value = "configured", forced
    else:
        from .services.boot_verify import in_container
        if in_container():
            return None, "container: nothing to bind to"
        for kind, getter in (("hardware", _hardware_uuid), ("installation", _machine_id),
                             ("network adapter", lambda: (_physical_macs() or [None])[0])):
            if (value := getter()):
                break
        else:
            return None, "no stable hardware identity could be read"
    digest = hashlib.sha256(f"impress.device\0{kind}\0{value}".encode()).hexdigest()
    return digest, kind


def get() -> tuple[str | None, str]:
    if "fp" not in _cache or _cache.get("env") != os.environ.get("IMPRESS_DEVICE_ID"):
        _cache.update(fp=compute(), env=os.environ.get("IMPRESS_DEVICE_ID"))
    return _cache["fp"]


def short(fp: str | None) -> str:
    return fp[:12] if fp else "-"
