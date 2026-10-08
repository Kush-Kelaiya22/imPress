"""A simulated C6 gateway for end-to-end tests (#43).

It talks to the backend exactly as firmware/class_c6 does:
- `register` / `heartbeat`: wifi_client.c.
- `relay` + `flush`: main.c's batch. Mesh messages are buffered and POSTed in
  one batch. On a 5xx or a network error the chunk is kept for a retry; on a
  4xx it is dropped.
- `ota_prompt` + `update`: ota.c. Check, download, verify the SHA-256 against
  the offer, report every step to /api/device/ota/status, "reboot" (register
  with the new version), then health_check → success.

What it can't simulate (radio, SPI, flash, real reboots) is listed in
docs/testing/HARDWARE_VALIDATION.md.
"""

import hashlib

from conftest import DEVICE

class Gateway:
    def __init__(self, client, mac, classroom_code="", version="2.1.0", name="sim gateway"):
        self.client, self.mac, self.code, self.version, self.name = client, mac, classroom_code, version, name
        self.pending: list[dict] = []          # the batch buffer
        self.reports: list[str] = []           # OTA states this gateway reported

    # ── wifi_client.c ────────────────────────────────────────────────────
    def register(self):
        r = self.client.post("/api/device/register", headers=DEVICE, json={
            "mac_address": self.mac, "device_type": "c6", "device_name": self.name,
            "classroom_code": self.code, "firmware_version": self.version})
        assert r.status_code == 200, r.text
        return r.json()

    def heartbeat(self, **diag):
        r = self.client.post("/api/device/heartbeat", headers=DEVICE, json={
            "mac_address": self.mac, "rssi": -55, "firmware_version": self.version,
            "uptime_s": 60, "reset_reason": "poweron", "s3_link_ok": True, **diag})
        assert r.status_code == 200, r.text

    # ── main.c batch ─────────────────────────────────────────────────────
    def relay(self, *messages):
        """Mesh messages arriving from the S3 (msg_to_json adds device_mac)."""
        self.pending += [{"device_mac": self.mac, **m} for m in messages]

    def flush(self):
        """POST the buffer; returns the HTTP status. Keeps it on a 5xx."""
        if not self.pending:
            return None
        r = self.client.post("/api/device/batch", headers=DEVICE,
                             json={"device_type": "c6", "messages": self.pending})
        if r.status_code < 500:
            self.pending = []                  # delivered (2xx) or dropped as malformed (4xx)
        self.last_batch = r.json() if r.headers.get("content-type", "").startswith("application/json") else None
        return r.status_code

    # ── ota.c ────────────────────────────────────────────────────────────
    def ota_prompt(self, frame):
        """ws_command.c → ota_prompt_target: only a prompt for this gateway."""
        p = frame.get("payload", {})
        return (frame.get("event") == "device_command" and frame.get("command") == "ota_update"
                and p.get("device_type") == "c6" and p.get("mac_address") == self.mac)

    def _status(self, state, version="", **kw):
        r = self.client.post("/api/device/ota/status", headers=DEVICE, json={
            "mac_address": self.mac, "state": state, "version": version, **kw})
        assert r.status_code == 200, (state, r.text)
        self.reports.append(state)

    def update(self, *, corrupt=False, stop_after=None, healthy=True):
        """One OTA attempt. `corrupt` flips a byte in transit, `stop_after` goes
        silent after that step (power loss), `healthy=False` fails the new
        image's health check so the bootloader reverts."""
        offer = self.client.post("/api/device/firmware/check", headers=DEVICE, json={
            "mac_address": self.mac, "current_version": self.version}).json()
        if not offer["update_available"] or len(offer.get("sha256", "")) != 64:
            return "no offer"                  # ota_parse_check refuses an unverifiable offer
        target = offer["version"]
        self._status("precheck", target)
        self._status("downloading", target)
        if stop_after == "downloading":
            return "silent"
        dl = self.client.get("/api/device/firmware/download", headers=DEVICE,
                             params={"mac_address": self.mac, "version": target})
        if dl.status_code != 200:              # nothing written to flash
            self._status("failed", target, error=f"http {dl.status_code}")
            return "failed"
        image = bytearray(dl.content)
        if corrupt:
            image[len(image) // 2] ^= 0xFF
        self._status("verifying", target)
        if hashlib.sha256(image).hexdigest() != offer["sha256"]:
            self._status("failed", target, error="sha256 mismatch", error_code=0x1503)
            return "failed"
        for step in ("installing", "rebooting"):
            self._status(step, target)
            if stop_after == step:
                return "silent"
        if not healthy:                        # bootloader reverts; the old image reports
            self.register()
            self._status("rolled_back", target)
            return "rolled_back"
        self.version = target                  # boot the new image
        self.register()
        self._status("health_check", target)
        self._status("success", target)
        return "success"


# ── Mesh messages, as msg_to_json builds them ────────────────────────────

def join(uid, roll):
    return {"type": "student_join", "enrollment_number": roll, "device_id": uid, "class_code": ""}


def leave(uid, roll, reason=0):
    return {"type": "student_leave", "enrollment_number": roll, "device_id": uid, "reason": reason}


def answer(quiz_id, order, roll, option, uid=0):
    return {"type": "quiz_answer", "quiz_id": quiz_id, "question_order": order, "enrollment_number": roll,
            "selected_option": option, "response_time_ms": 900, "device_id": uid}


def vote(poll_id, roll, option, uid=0):
    return {"type": "poll_vote", "poll_id": poll_id, "enrollment_number": roll, "selected_option": option,
            "device_id": uid}
