"""Device health states (#39), computed from the latest heartbeat. Rules, in
order (the first that matches wins):

| State    | When |
|----------|------|
| UNKNOWN  | never seen |
| OFFLINE  | silent for more than 30 s (presence.OFFLINE_AFTER_S) |
| UPDATING | an OTA update is in progress (the deployment target is active) |
| ERROR    | the last OTA update failed, or the device reset from a panic, watchdog or brown-out in the last 10 minutes |
| DEGRADED | S3 link down, Wi-Fi RSSI below -80 dBm, or minimum free heap below 20 KB |
| ONLINE   | otherwise |

Firmware that predates #39 omits the diagnostics; those rules then don't apply.
"""

from datetime import datetime

from ..models import EspDevice
from .deployments import ACTIVE, FAILURES
from .presence import OFFLINE_AFTER_S

CRASH_RESETS = {"panic", "int_wdt", "task_wdt", "wdt", "brownout"}
CRASH_WINDOW_S = 600
WEAK_RSSI_DBM = -80
LOW_HEAP_BYTES = 20 * 1024


def health(d: EspDevice, now: datetime) -> tuple[str, list[str]]:
    """(state, reasons) for one device."""
    if d.last_seen is None:
        return "UNKNOWN", ["never seen"]
    silent = (now - d.last_seen).total_seconds()
    if not d.is_connected or silent > OFFLINE_AFTER_S:
        return "OFFLINE", [f"silent for {int(silent)} s"]
    if d.ota_status in ACTIVE:
        return "UPDATING", [f"OTA {d.ota_status}"]

    errors = []
    if d.ota_status in FAILURES:
        errors.append(f"last OTA update {d.ota_status.replace('_', ' ')}")
    if d.reset_reason in CRASH_RESETS and d.uptime_s is not None and d.diag_at is not None:
        up = d.uptime_s + (now - d.diag_at).total_seconds()
        if up < CRASH_WINDOW_S:
            errors.append(f"reset by {d.reset_reason} {int(up // 60)} min ago")
    if errors:
        return "ERROR", errors

    degraded = []
    if d.s3_link_ok is False:
        degraded.append("S3 link down")
    if d.rssi is not None and WEAK_RSSI_DBM > d.rssi:
        degraded.append(f"weak Wi-Fi ({d.rssi} dBm)")
    if d.min_free_heap is not None and d.min_free_heap < LOW_HEAP_BYTES:
        degraded.append(f"low memory (min free heap {d.min_free_heap} B)")
    if degraded:
        return "DEGRADED", degraded
    return "ONLINE", []
