"""#4: the C6 batch accumulator (cJSON, not thread-safe) has exactly one owner.

spi_to_http_task and heartbeat_task run at different priorities on a
preemptive single-core RTOS; if both mutate s_batch the heap can be corrupted
(use-after-free / double free) and items are lost. Structural guard: every
function that touches the batch must be reachable only from spi_to_http_task.
"""

from c_source import FIRMWARE, calls, functions, mentions

MAIN = FIRMWARE / "class_c6" / "main" / "main.c"
BATCH_API = ("batch_init", "batch_add", "batch_flush", "batch_flush_needed")


def _users_of_batch(fns):
    return {name for name, body in fns.items()
            if name not in BATCH_API and (mentions(body, "s_batch") or any(calls(body, f) for f in BATCH_API))}


def test_only_spi2http_path_touches_the_batch():
    fns = functions(MAIN)
    assert "spi_to_http_task" in fns and "heartbeat_task" in fns
    users = _users_of_batch(fns)
    # Each batch user must itself be spi_to_http_task or called only from it.
    for name in users - {"spi_to_http_task"}:
        callers = {n for n, b in fns.items() if n != name and calls(b, name)}
        assert callers == {"spi_to_http_task"}, f"{name} touches s_batch and is called from {callers}"
    assert "heartbeat_task" not in users
    assert not mentions(fns["heartbeat_task"], "cJSON_AddItemToArray")


def test_heartbeat_hands_off_via_flag():
    fns = functions(MAIN)
    assert mentions(fns["heartbeat_task"], "s_hb_item_pending")
    assert mentions(fns["spi_to_http_task"], "s_hb_item_pending")


def test_stack_watermark_reports_spi2http_not_app_main():
    body = functions(MAIN)["app_main"]
    assert "uxTaskGetStackHighWaterMark(NULL)" not in body.replace(" ", "")
    assert mentions(body, "s_spi2http_task")
