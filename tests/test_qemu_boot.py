"""The emulator boot test's verdict on a serial log (#154)."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("qemu_boot", ROOT / "scripts/qemu_boot.py")
qb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qb)

EXPECT = ["imPress S3 Class Module", "EMULATOR:", "EMULATOR: alive 6 s"]
GOOD = ["rst:0x1 (POWERON_RESET),boot:0x8 (SPI_FAST_FLASH_BOOT)", "I (100) s3_main: === imPress S3 Class Module v2.1.0 ===",
        "W (112) s3_main: EMULATOR: ESP-NOW mesh and SPI link skipped (not emulated)",
        "I (114) s3_main: EMULATOR: alive 2 s", "I (4116) s3_main: EMULATOR: alive 6 s, free heap 393200"]


def test_a_clean_boot_passes():
    assert qb.judge(GOOD, EXPECT) == (True, "all expected lines seen")


def test_lines_must_appear_in_order():
    ok, why = qb.judge(list(reversed(GOOD)), EXPECT)
    assert not ok and "missing" in why


def test_any_panic_or_reset_fails():
    for bad in ("Guru Meditation Error: Core  0 panic'ed (Interrupt wdt timeout on CPU0).",
                "abort() was called at PC 0x42003a4c on core 0",
                "assert failed: __esp_sys_init_fn_init_flash esp_flash_spi_init.c:650 (flash_ret == ESP_OK)",
                "Rebooting...", "rst:0xc (RTC_SW_CPU_RST),boot:0x4 (SPI_FLASH_BOOT)",
                "E (305) task_wdt: Task watchdog got triggered.", "Brownout detector was triggered"):
        ok, why = qb.judge(GOOD[:3] + [bad] + GOOD[3:], EXPECT)
        assert not ok and why.startswith("fatal"), bad


def test_power_on_reset_is_fine():
    assert qb.FATAL.search("rst:0x1 (POWERON_RESET),boot:0x12 (SPI_FAST_FLASH_BOOT)") is None


def test_emulator_profiles_skip_only_what_qemu_lacks():
    for p in ("class_s3", "student"):
        cfg = (ROOT / f"firmware/{p}/sdkconfig.qemu").read_text()
        assert "CONFIG_IMPRESS_EMULATOR=y" in cfg and "CONFIG_ESPTOOLPY_FLASHMODE_DIO=y" in cfg
        assert "CONFIG_PM_ENABLE=n" in cfg
        main = (ROOT / f"firmware/{p}/main/main.c").read_text()
        assert "#if CONFIG_IMPRESS_EMULATOR" in main and "EMULATOR: alive" in main
