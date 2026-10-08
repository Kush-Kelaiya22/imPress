"""#34: the C6 OTA client keeps its safety ordering (behaviour of the pure
parts is host-tested in class_c6/test_host/test_ota_logic.c)."""

import re

from c_source import FIRMWARE, calls, functions

C6 = FIRMWARE / "class_c6"
OTA = C6 / "main" / "ota.c"


def _order(body, *names):
    pos = [body.index(n) for n in names]
    assert pos == sorted(pos), f"expected order {names}"


def test_image_is_verified_before_it_can_boot():
    task = functions(OTA)["ota_task"]
    _order(task, "ota_digest_matches", "esp_ota_end", "esp_ota_set_boot_partition", "remember_target", "esp_restart")
    mismatch = task[task.index("ota_digest_matches"):task.index("esp_ota_end")]
    assert calls(mismatch, "esp_ota_abort") and "ESP_ERR_INVALID_CRC" in mismatch


def test_download_checks_status_size_and_completeness_and_hashes_while_streaming():
    dl = functions(OTA)["download"]
    assert "!= 200" in dl and "o->size" in dl
    assert calls(dl, "psa_hash_update") and calls(dl, "esp_ota_write")
    assert calls(dl, "esp_http_client_is_complete_data_received")
    _order(dl, "esp_http_client_get_status_code", "esp_ota_begin")      # no flash erase for an error


def test_every_step_is_reported():
    text = OTA.read_text()
    for state in ("verifying", "installing", "rebooting", "health_check", "success", "rolled_back", "failed"):
        assert f'"{state}"' in text, state
    assert '"/api/device/ota/status"' in text


def test_new_image_is_confirmed_only_when_healthy_or_reverted():
    fns = functions(OTA)
    boot = fns["ota_c6_boot_check"]
    healthy_branch = boot[boot.index("if (!healthy)"):]
    assert calls(healthy_branch, "esp_ota_mark_app_valid_cancel_rollback")
    assert boot.index("if (!healthy)") < boot.index("esp_ota_mark_app_valid_cancel_rollback")
    watchdog = fns["health_watchdog"]
    assert "ESP_OTA_IMG_PENDING_VERIFY" in watchdog and calls(watchdog, "esp_restart")


def test_rollback_is_enabled_on_the_c6():
    assert "CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y" in (C6 / "sdkconfig").read_text()
    assert "CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y" in (C6 / "sdkconfig.defaults").read_text()


def test_prompts_are_routed_by_target():
    main = (C6 / "main" / "main.c").read_text()
    on_ws = functions(C6 / "main" / "main.c")["on_ws_command"]
    assert re.search(r"ota_prompt_target\(pld, s_mac_str\) == OTA_PROMPT_SELF", on_ws)
    assert re.search(r"ota_prompt_target\(pld, s_mac_str\) == OTA_PROMPT_S3", on_ws)
    app = functions(C6 / "main" / "main.c")["app_main"]
    assert app.index("ota_c6_set_mac") < app.index("ota_c6_boot_check") < app.index("ota_c6_start")
    assert "ota_c6_boot_check(true)" in main                     # confirmation after a reconnect
