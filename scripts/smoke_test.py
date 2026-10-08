#!/usr/bin/env python3
"""HTTP smoke test of a running imPress backend (#42): the system audit's
workflow, end to end, with the standard library only.

  scripts/smoke_test.py --base http://127.0.0.1:8000 --password <admin password>

The device key is read from backend/.env unless --device-key is given.
Exits non-zero at the first failed step.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def call(base, path, body=None, token=None, key=None, raw=None, ctype="application/json"):
    data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
    req = urllib.request.Request(base + path, data=data, method="POST" if data is not None else "GET")
    req.add_header("content-type", ctype)
    if token:
        req.add_header("authorization", f"Bearer {token}")
    if key:
        req.add_header("x-api-key", key)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            text = r.read().decode()
            return r.status, (json.loads(text) if r.headers.get_content_type() == "application/json" else text)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def env_value(name):
    for line in (ROOT / "backend" / ".env").read_text().splitlines():
        key, _, rest = line.partition("=")
        if key.strip() == name:
            return rest.partition("#")[0].strip()
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--username", default="admin")
    ap.add_argument("--password", required=True)
    ap.add_argument("--device-key")
    a = ap.parse_args()
    base, key = a.base.rstrip("/"), a.device_key or env_value("IMPRESS_DEVICE_API_KEY")
    tag = uuid.uuid4().hex[:6].upper()          # re-runnable against the same database
    gw = "48:F6:EE:" + ":".join(tag[i:i + 2] for i in (0, 2, 4))

    def step(name, ok, detail=""):
        print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {detail}" if detail and not ok else ""))
        if not ok:
            sys.exit(1)

    status, h = call(base, "/health")
    expected = (ROOT / "VERSION").read_text().strip()
    step("health reports version and schema", status == 200 and h.get("version") == expected
         and h.get("schema_version", 0) >= 1, h)

    status, r = call(base, "/api/auth/login", {"username": a.username, "password": a.password})
    step("admin login", status == 200, r)
    tok = r["access_token"]

    status, course = call(base, "/api/courses/", {"code": f"SM{tag}", "name": "Smoke course"}, tok)
    step("create course", status in (200, 201), course)
    status, cls = call(base, "/api/admin/classes", {"name": "Smoke section", "code": f"S{tag}",
                                                    "course_id": course["id"], "course_section": "A",
                                                    "classroom_code": f"RM-{tag}"}, tok)
    step("create section with a room code", status == 201, cls)

    status, reg = call(base, "/api/device/register", {"mac_address": gw, "device_type": "c6",
                                                      "device_name": "smoke gateway", "classroom_code": f"RM-{tag}",
                                                      "firmware_version": expected}, key=key)
    step("gateway registers and links to the room", status == 200 and reg.get("class_id") == cls["id"], reg)
    status, hb = call(base, "/api/device/heartbeat", {"mac_address": gw, "rssi": -60, "uptime_s": 5,
                                                      "reset_reason": "poweron", "s3_link_ok": True}, key=key)
    step("gateway heartbeat with diagnostics", status == 200, hb)
    status, b = call(base, "/api/device/batch", {"device_type": "c6", "messages": [
        {"type": "student_join", "device_mac": gw, "device_id": int(tag, 16), "enrollment_number": f"SMOKE{tag}"[:10]}]},
        key=key)
    step("student join through the gateway", status == 200, b)
    status, view = call(base, f"/api/admin/classes/{cls['id']}/devices", token=tok)
    step("class devices list the gateway and the module", status == 200 and view["node"]
         and len(view["student_modules"]) == 1, view)
    status, mods = call(base, "/api/admin/modules", token=tok)
    step("gateway health is online", status == 200 and any(m["mac_address"] == gw and m["health"] == "ONLINE"
                                                             for m in mods), mods)

    status, fw = call(base, "/api/admin/firmware", token=tok)
    step("firmware registry lists", status == 200 and isinstance(fw, list), fw)
    boundary = "smoke" + tag
    junk = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"x.bin\"\r\n"
            f"Content-Type: application/octet-stream\r\n\r\n").encode() + b"\xe9" + bytes(2047) + f"\r\n--{boundary}--\r\n".encode()
    status, r = call(base, "/api/admin/firmware", raw=junk, token=tok, ctype=f"multipart/form-data; boundary={boundary}")
    step("random bytes are refused as firmware", status == 422, f"{status} {r}")

    status, page = call(base, "/")
    step("web app served", status == 200 and "<html" in str(page).lower(), status)
    print("smoke test passed")


if __name__ == "__main__":
    main()
