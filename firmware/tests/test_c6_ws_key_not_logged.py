"""#11: the C6 must not put the device API key in the WS URL or the log."""

import re

from c_source import FIRMWARE, functions

WS_CLIENT = FIRMWARE / "class_c6" / "main" / "ws_client.c"


def test_api_key_sent_as_header_not_in_uri_or_log():
    raw = WS_CLIENT.read_text()
    body = raw[raw.index("int ws_client_start("):raw.index("bool ws_client_is_connected(")]
    assert "api_key=" not in body                       # not in the URI format string
    assert re.search(r'"X-API-Key: %s\\r\\n"', body)     # sent as a header
    assert ".headers = headers" in body
    for call in re.findall(r"ESP_LOG\w\([^;]*;", body, re.S):
        assert "api_key" not in call, call
    assert "ws_client_start" in functions(WS_CLIENT)
