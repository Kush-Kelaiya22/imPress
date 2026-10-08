"""#29: guards for the S3 <-> C6 link as ported from v3 (docs/engineering/V2_V3_COMPARISON.md).

Behaviour is covered by host tests (protocol slot/FIFO, C6 slave, student set);
these check the wiring that only the real ESP-IDF build sees.
"""

import re

from c_source import FIRMWARE, calls, functions, mentions, strip_comments_and_strings

C6 = FIRMWARE / "class_c6"
S3 = FIRMWARE / "class_s3"
SLAVE = C6 / "main" / "spi_slave.c"
MASTER = S3 / "main" / "spi_master.c"


def _src(path):
    return strip_comments_and_strings(path.read_text())


def test_both_ends_use_standard_full_duplex_spi():
    # v2: the master was quad half-duplex while the GPSPI slave only does
    # standard full-duplex, so slots never lined up (row 1).
    for path in (SLAVE, MASTER):
        src = _src(path)
        assert "SPICOMMON_BUSFLAG_QUAD" not in src, path
        assert "SPI_DEVICE_HALFDUPLEX" not in src, path
        assert re.search(r"\.quadwp_io_num\s*=\s*-1", src) and re.search(r"\.quadhd_io_num\s*=\s*-1", src), path


def test_slot_framing_and_crc_come_from_the_shared_protocol():
    # one implementation per wire format (D4); v3 had a CRC copy in each driver
    for path in (SLAVE, MASTER):
        src = _src(path)
        assert "crc16_local" not in src and "0x1021" not in src, path
        assert calls(src, "spi_slot_fifo_push") and calls(src, "spi_slot_decode"), path


def test_c6_validates_received_slots():
    # v3 dropped the RX CRC check on the C6 (row 4)
    read = functions(SLAVE)["spi_slave_read"]
    assert calls(read, "spi_slot_decode")


def test_master_drops_a_payload_only_after_a_successful_transfer():
    poll = functions(MASTER)["spi_master_poll"]
    transmit = poll.index("spi_device_polling_transmit")
    assert poll.index("spi_slot_fifo_peek") < transmit < poll.index("spi_slot_fifo_drop")


def test_clock_is_configurable_and_defaults_to_10_mhz():
    kconfig = (S3 / "main" / "Kconfig.projbuild").read_text()
    block = kconfig[kconfig.index("config SPI_CLOCK_MHZ"):]
    assert re.search(r"default\s+10\b", block.split("config ", 2)[1])
    assert "CONFIG_SPI_CLOCK_MHZ" in (S3 / "main" / "config.h").read_text()
    assert "CONFIG_SPI_CLOCK_MHZ=10" in (S3 / "sdkconfig").read_text()


def test_s3_link_task_always_clocks_a_slot():
    # v2 only transferred when TX was pending or the C6 ready-line ISR fired
    task = functions(S3 / "main" / "main.c")["spi_link_task"]
    assert calls(task, "xSemaphoreTake")                     # immediate wake on send
    assert re.search(r"^\s*if\s*\(\s*spi_master_poll\s*\(\s*\)\s*\)", task, re.M), \
        "spi_master_poll() must run every iteration, not behind a pending/ready condition"
    assert not calls(task, "spi_master_tx_pending") and not calls(task, "spi_master_c6_has_data")


def test_s3_mesh_heartbeat_is_encoded_once():
    fns = functions(S3 / "main" / "mesh_master.c")
    recv = fns["on_espnow_recv"]
    hb = recv[recv.index("payload_heartbeat_t"):]   # the heartbeat reply block
    assert calls(hb, "mesh_master_broadcast") and not calls(hb, "msg_encode")
    assert calls(fns["mesh_master_broadcast"], "msg_encode")   # broadcast encodes itself


def test_s3_heartbeat_record_is_not_copied_onto_itself():
    # v3 encoded into slot+header and then spi_record_write()'d slot+header onto
    # slot: overlapping memcpy, undefined behaviour (row 10, rejected)
    hb = functions(S3 / "main" / "main.c")["heartbeat_task"]
    m = re.search(r"spi_record_write\s*\(\s*(\w+)\s*,[^;]*?,\s*(\w+)\s*\+", hb, re.S)
    assert m is None or m.group(1) != m.group(2)


def test_c6_services_spi_while_wifi_is_down_with_a_bounded_batch():
    fns = functions(C6 / "main" / "main.c")
    task = fns["spi_to_http_task"]
    read_at = task.index("spi_slave_read")
    assert not re.search(r"wifi_client_is_connected\s*\(\s*\)\s*\)\s*\{?\s*continue", task[:read_at]), \
        "spi2http must not skip the SPI read while Wi-Fi is down"
    assert re.search(r"pdMS_TO_TICKS\(\s*2\s*\)", task)
    for name in ("spi_to_http_task", "process_spi_payload"):
        for m in re.finditer(r"batch_flush\s*\(\s*\)\s*;", fns[name]):
            before = fns[name][:m.start()].rsplit("\n", 2)[-2]
            assert "wifi_client_is_connected" in before, f"{name}: flush must wait for Wi-Fi"
    assert mentions(fns["batch_add"], "BATCH_MAX_BUFFERED")
    src = (C6 / "main" / "main.c").read_text()
    assert re.search(r"#if CONFIG_FREERTOS_HZ < 500\s*\n#error", src)


def test_c6_flushes_bounded_chunks_and_keeps_them_on_transport_errors():
    flush = functions(C6 / "main" / "main.c")["batch_flush"]
    assert mentions(flush, "batch_max") and calls(flush, "cJSON_DetachItemFromArray")
    assert calls(flush, "cJSON_InsertItemInArray")            # retry on network/5xx
    # batch JSON (enrollment numbers) is debug-only
    assert not re.search(r'ESP_LOGI\([^;]*"Batch data', (C6 / "main" / "main.c").read_text())


def test_c6_student_count_comes_from_join_and_leave_only():
    to_json = functions(C6 / "main" / "main.c")["msg_to_json"]
    assert "s_student_count++" not in to_json.replace(" ", "")
    assert calls(to_json, "student_set_join") and calls(to_json, "student_set_leave")
    assert calls(to_json, "student_set_root_uptime")


def test_c6_flash_mode_is_dio():
    assert "CONFIG_ESPTOOLPY_FLASHMODE_DIO=y" in (C6 / "sdkconfig").read_text()
    assert "CONFIG_ESPTOOLPY_FLASHMODE_DIO=y" in (C6 / "sdkconfig.defaults").read_text()
    assert "\nCONFIG_ESPTOOLPY_FLASHMODE_QIO=y" not in (C6 / "sdkconfig").read_text()


def test_student_placeholder_enrollment_is_the_unprovisioned_sentinel():
    # v3 set it to a real-looking student id (row 14, rejected)
    cfg = (FIRMWARE / "student" / "main" / "config.h").read_text()
    assert re.search(r'#define\s+DEFAULT_ENROLLMENT\s+"0000000000"', cfg)
