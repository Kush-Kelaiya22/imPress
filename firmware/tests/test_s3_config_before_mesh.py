"""#7: the S3 loads its config before the mesh uses g_cfg.mesh_channel, and a
failed esp_wifi_set_channel() is reported instead of silently ignored."""

import re

from c_source import FIRMWARE, calls, functions

S3 = FIRMWARE / "class_s3" / "main"


def test_config_loaded_before_mesh_init():
    body = functions(S3 / "main.c")["app_main"]
    assert body.index("init_nvs_config") < body.index("mesh_master_init")


def test_config_loader_initialises_nvs_itself():
    assert calls(functions(S3 / "config.c")["init_nvs_config"], "nvs_flash_init")


def test_mesh_init_reads_channel_from_config():
    assert "g_cfg.mesh_channel" in functions(S3 / "mesh_master.c")["mesh_master_init"]


def test_set_channel_result_checked_on_s3_and_student():
    for path, fn in ((S3 / "mesh_master.c", "mesh_master_init"),
                     (FIRMWARE / "student" / "main" / "mesh_espnow.c", "mesh_init")):
        body = functions(path)[fn]
        assert re.search(r"\bret\s*=\s*esp_wifi_set_channel\s*\(", body), path.name
        assert re.search(r"if\s*\(\s*ret\s*!=\s*ESP_OK\s*\)", body[body.index("esp_wifi_set_channel"):]), path.name
