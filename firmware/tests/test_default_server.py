"""The hub fetches its own updates from BACKEND_HOST (class_s3), so its
default must name the same server as the gateway's (class_c6): with
different defaults an unconfigured hub looked for its update elsewhere."""

import re
from pathlib import Path

FW = Path(__file__).resolve().parents[1]


def _kconfig_default(project):
    text = (FW / project / "main" / "Kconfig.projbuild").read_text()
    return re.search(r'config BACKEND_HOST\b.*?default "([^"]*)"', text, re.S).group(1)


def _sdkconfig(project):
    return re.search(r'^CONFIG_BACKEND_HOST="([^"]*)"', (FW / project / "sdkconfig").read_text(), re.M).group(1)


def test_hub_and_gateway_default_to_the_same_server():
    assert _kconfig_default("class_s3") == _kconfig_default("class_c6")
    assert _sdkconfig("class_s3") == _sdkconfig("class_c6") == _kconfig_default("class_c6")
