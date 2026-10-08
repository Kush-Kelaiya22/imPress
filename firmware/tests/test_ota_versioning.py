"""#33: OTA root causes stay fixed (version source, premature success,
unchecked HTTP status, an S3 result that never reached the backend)."""

import re

from c_source import FIRMWARE, calls, functions, strip_comments_and_strings

PROJECTS = ("class_c6", "class_s3", "student")
S3 = FIRMWARE / "class_s3" / "main"


def test_version_comes_from_the_image():
    for p in PROJECTS:
        ver = (FIRMWARE / p / "version.txt").read_text().strip()
        assert re.fullmatch(r"\d+\.\d+\.\d+", ver), f"{p}/version.txt must be semver, got {ver!r}"
        cfg = strip_comments_and_strings((FIRMWARE / p / "main" / "config.h").read_text())
        assert re.search(r"#define\s+FIRMWARE_VERSION\s+\(esp_app_get_description\(\)->version\)", cfg), p
        assert "esp_app_format" in (FIRMWARE / p / "main" / "CMakeLists.txt").read_text(), p


def test_all_projects_share_one_release_version():
    assert len({(FIRMWARE / p / "version.txt").read_text().strip() for p in PROJECTS}) == 1


def test_download_checks_http_status_before_touching_flash():
    fn = functions(S3 / "ota.c")["_download_and_apply"]
    assert fn.index("esp_http_client_get_status_code") < fn.index("esp_ota_begin")
    assert "!= 200" in fn
    assert calls(fn, "esp_http_client_is_complete_data_received")


def test_success_is_reported_after_the_reboot_not_before():
    fns = functions(S3 / "ota.c")
    task = fns["_ota_task"]
    restart = task.index("esp_restart")
    assert calls(task[:restart], "_remember_target")
    assert "OTA_RESULT_APPLIED" not in task and "MSG_OTA_APPLIED" not in task
    assert "OTA_RESULT_FAILED" in task                     # failures are reported
    boot = fns["ota_report_boot_result"]
    assert "OTA_RESULT_APPLIED" in boot and "OTA_RESULT_ROLLED_BACK" in boot
    main = functions(S3 / "main.c")["app_main"]
    assert main.index("esp_ota_mark_app_valid_cancel_rollback") < main.index("ota_report_boot_result")


def test_s3_result_is_an_spi_record_and_the_c6_relays_it():
    rep = functions(S3 / "ota.c")["_report_result"]
    assert calls(rep, "spi_record_write") and calls(rep, "spi_master_send")
    to_json = functions(FIRMWARE / "class_c6" / "main" / "main.c")["msg_to_json"]
    case = to_json[to_json.index("MSG_OTA_APPLIED"):]
    assert '"ota_result"' in (FIRMWARE / "class_c6" / "main" / "main.c").read_text()
    case = case[:case.index("case MSG_", 1)]                  # up to the next case label
    assert calls(case, "cJSON_AddStringToObject") and "mac_address" in (FIRMWARE / "class_c6" / "main" / "main.c").read_text()
