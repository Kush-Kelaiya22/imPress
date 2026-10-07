"""#13: S3 OTA — rollback protection and no reboot when nothing is installed."""

import re

from c_source import FIRMWARE, calls, functions, strip_comments_and_strings

S3 = FIRMWARE / "class_s3"
OTA = S3 / "main" / "ota.c"


def test_app_rollback_enabled():
    for cfg in ("sdkconfig", "sdkconfig.defaults"):
        assert re.search(r"^CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE=y$", (S3 / cfg).read_text(), re.M), cfg


def test_new_image_marked_valid_only_after_mesh_and_spi_init():
    body = functions(S3 / "main" / "main.c")["app_main"]
    mark = body.index("esp_ota_mark_app_valid_cancel_rollback")
    assert body.index("mesh_master_init") < mark and body.index("spi_master_init") < mark
    assert "ESP_OTA_IMG_PENDING_VERIFY" in body


def test_only_a_successful_install_reboots():
    task = functions(OTA)["_ota_task"]
    assert len(re.findall(r"\besp_restart\s*\(", task)) == 1
    # ...and that single restart comes after the image was applied.
    assert task.index("_download_and_apply") < task.index("esp_restart")
    # Every early exit (no WiFi / nothing pending / failed apply) detaches instead.
    assert len(re.findall(r"\b_ota_finish_without_update\s*\(", task)) == 3


def test_detach_unregisters_reconnect_handler_before_disconnecting():
    body = functions(OTA)["_wifi_detach"]
    assert body.index("esp_event_handler_instance_unregister") < body.index("esp_wifi_disconnect")
    assert calls(body, "esp_wifi_set_channel")          # back to the mesh channel
    src = strip_comments_and_strings(OTA.read_text())
    assert "&s_wifi_evt_inst" in src and "&s_ip_evt_inst" in src
