"""#66: the C6 and S3 use their own device key once issued, keep the shared
key for registering, and drop a key the backend no longer accepts (401)."""

from c_source import FIRMWARE, calls, functions

C6, S3 = FIRMWARE / "class_c6" / "main", FIRMWARE / "class_s3" / "main"


def test_register_stores_the_issued_key_on_both_boards():
    c6 = functions(C6 / "wifi_client.c")["http_register_device"]
    s3 = functions(S3 / "ota.c")["_register"]
    for body in (c6, s3):
        assert calls(body, "json_get_string") and calls(body, "cfg_set_device_key")
        assert body.index("json_get_string") < body.index("cfg_set_device_key")
    raw = (C6 / "wifi_client.c").read_text() + (S3 / "ota.c").read_text()
    assert raw.count('"device_key"') == 2                       # the field the backend returns


def test_only_401_drops_the_key():
    # 403 means disabled or the wrong device: dropping the key there would lock
    # the device out once it is re-enabled (its key is still active server-side)
    for path, fn in ((C6 / "wifi_client.c", "_check_auth"), (S3 / "ota.c", "_http_post_body")):
        body = functions(path)[fn]
        assert "status == 401" in body and calls(body, "cfg_clear_device_key") and "403" not in body


def test_every_request_sends_the_active_key():
    for path in (C6 / "wifi_client.c", C6 / "ota.c", C6 / "ws_client.c", S3 / "ota.c"):
        text = path.read_text()
        assert "g_cfg.api_key" in text and "prov_key" not in text, path   # prov_key only lives in config.c


def test_the_shared_key_is_kept_for_re_registration():
    for path in (C6 / "config.c", S3 / "config.c"):
        clear = functions(path)["cfg_clear_device_key"]
        assert "g_cfg.prov_key" in clear and calls(clear, "_store_dev_key"), path


def test_c6_re_registers_after_a_reset():
    task = functions(C6 / "main.c")["heartbeat_task"]
    assert "http_reregister_pending()" in task and calls(task, "http_register_device")
