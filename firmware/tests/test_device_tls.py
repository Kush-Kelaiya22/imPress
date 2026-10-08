"""#66 (3/3): the hub and gateway can reach the backend over HTTPS/WSS, and
every client that talks to it gets the same TLS settings."""

import re

from c_source import FIRMWARE, strip_comments_and_strings

SOURCES = [FIRMWARE / "class_c6/main" / f for f in ("wifi_client.c", "ota.c", "ws_client.c")] + \
          [FIRMWARE / "class_s3/main/ota.c"]


def test_every_backend_client_gets_the_tls_settings():
    for path in SOURCES:
        code = strip_comments_and_strings(path.read_text())
        inits = re.findall(r"esp_(?:http|websocket)_client_init\(&(\w+)\)", code)
        applied = re.findall(r"BACKEND_TLS_APPLY\((\w+)\)", code)
        assert inits and sorted(inits) == sorted(applied), path
        for var in inits:   # applied before the client copies the config
            assert code.index(f"BACKEND_TLS_APPLY({var})") < code.index(f"_client_init(&{var})"), path


def test_no_hard_coded_plaintext_scheme():
    for path in SOURCES:
        text = path.read_text()
        assert '"http://' not in text and '"ws://' not in text, path
        assert "backend_tls.h" in text, path
    assert 'BACKEND_HTTP_SCHEME "://' in (FIRMWARE / "class_c6/main/wifi_client.c").read_text()
    assert 'BACKEND_WS_SCHEME "://' in (FIRMWARE / "class_c6/main/ws_client.c").read_text()


def test_both_boards_offer_the_same_choice_and_embed_the_site_ca():
    for project in ("class_c6", "class_s3"):
        kconfig = (FIRMWARE / project / "main/Kconfig.projbuild").read_text()
        for sym in ("config BACKEND_TLS\n", "config BACKEND_TLS_CRT_BUNDLE", "config BACKEND_TLS_CA_FILE"):
            assert sym in kconfig, (project, sym)
        cmake = (FIRMWARE / project / "main/CMakeLists.txt").read_text()
        assert 'if(CONFIG_BACKEND_TLS_CA_FILE)' in cmake and 'certs/backend_ca.pem" TEXT' in cmake, project
    header = (FIRMWARE / "protocol/backend_tls.h").read_text()
    assert '"_binary_backend_ca_pem_start"' in header      # the symbol target_add_binary_data makes for that file


def test_tls_is_off_in_the_default_builds():
    # turning it on needs a server certificate and the TLS port: a site decision
    for project in ("class_c6", "class_s3"):
        assert "CONFIG_BACKEND_TLS=y" not in (FIRMWARE / project / "sdkconfig").read_text(), project
