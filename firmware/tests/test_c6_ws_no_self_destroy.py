"""#5: nothing running on the websocket client's own task may stop/destroy it.

esp_websocket_client refuses to stop itself from its task ("Client cannot be
stopped from websocket task") but esp_websocket_client_destroy() then frees
the client, event loop and locks under the still-running task → crash.
The WS event handler runs on that task and calls on_ws_command(), so every
function reachable from ws_event_handler must stay clear of stop/destroy.
"""

from c_source import FIRMWARE, calls, functions

MAIN = FIRMWARE / "class_c6" / "main"
FORBIDDEN = ("ws_client_stop", "ws_client_start", "ws_client_reconnect",
             "esp_websocket_client_stop", "esp_websocket_client_destroy")


def _graph():
    fns = {}
    for f in ("main.c", "ws_client.c"):
        fns.update(functions(MAIN / f))
    return fns


def _reachable(fns, roots):
    seen, todo = set(), list(roots)
    while todo:
        name = todo.pop()
        if name in seen or name not in fns:
            continue
        seen.add(name)
        todo += [callee for callee in fns if callee != name and calls(fns[name], callee)]
    return seen


def test_ws_task_never_stops_or_destroys_its_client():
    fns = _graph()
    # ws_event_handler invokes the registered callback (s_callback) = on_ws_command.
    reach = _reachable(fns, ["ws_event_handler", "on_ws_command"])
    assert {"on_ws_command", "handle_class_assignment"} <= reach
    offenders = {(fn, bad) for fn in reach for bad in FORBIDDEN if calls(fns[fn], bad)}
    assert offenders == set(), offenders


def test_reassignment_is_applied_from_app_main():
    fns = _graph()
    assert "s_ws_restart_pending" in fns["handle_class_assignment"]
    loop = fns["app_main"]
    assert "s_ws_restart_pending" in loop and calls(loop, "ws_client_stop")
