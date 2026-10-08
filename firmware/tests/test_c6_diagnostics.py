"""#39: the C6 heartbeat carries the diagnostics the backend's health rules
read, under the same names."""

import ast
import re

from c_source import FIRMWARE, functions

ROOT = FIRMWARE.parent
WIFI = FIRMWARE / "class_c6" / "main" / "wifi_client.c"
MAIN = FIRMWARE / "class_c6" / "main" / "main.c"
DIAG = ("uptime_s", "reset_reason", "boot_count", "min_free_heap", "s3_link_ok", "s3_uptime_s")


def _raw(path, signature):
    """A function's text with its string literals (functions() blanks them)."""
    src = path.read_text()
    start = src.index(signature)
    return src[start:src.index("\n}\n", start)]


def _schema_fields(cls):
    tree = ast.parse((ROOT / "backend" / "app" / "schemas.py").read_text())
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    return {s.target.id for s in node.body if isinstance(s, ast.AnnAssign)}


def test_heartbeat_sends_every_diagnostic_the_schema_accepts():
    body = _raw(WIFI, "int http_send_heartbeat(")
    sent = set(re.findall(r'\\"(\w+)\\":', body))
    assert set(DIAG) <= sent
    assert sent <= _schema_fields("DeviceHeartbeat"), sent - _schema_fields("DeviceHeartbeat")


def test_reset_reason_names_cover_the_crash_rules():
    names = set(re.findall(r'return "(\w+)";', _raw(WIFI, "static const char *_reset_reason(")))
    health = (ROOT / "backend" / "app" / "services" / "health.py").read_text()
    crash = set(ast.literal_eval(re.search(r"CRASH_RESETS = (\{[^}]*\})", health).group(1)))
    assert crash <= names, crash - names
    assert all(len(n) <= 16 for n in names)          # reset_reason: max_length 16


def test_s3_link_tracks_only_the_s3s_own_heartbeat():
    conv = functions(MAIN)["msg_to_json"]
    hb = conv[conv.index("case MSG_HEARTBEAT"):conv.index("case MSG_STUDENT_JOIN")]
    seen = hb[hb.index("if (sender_device_id == 0) {"):]
    assert "s_s3_seen_tick = xTaskGetTickCount()" in seen.split("}")[0]
    task = functions(MAIN)["heartbeat_task"]
    assert "S3_LINK_TIMEOUT_MS" in task and "http_send_heartbeat(s_mac_str, s_student_count, s3_ok" in task


def test_boot_count_is_persisted():
    cfg = (FIRMWARE / "class_c6" / "main" / "config.c").read_text()
    assert "nvs_set_i32(h, NVS_KEY_BOOT_COUNT" in cfg and "nvs_commit(h)" in cfg
