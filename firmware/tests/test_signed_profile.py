"""#66: the signed-app profile and the scripts that build with it."""

import re

from c_source import FIRMWARE

ROOT = FIRMWARE.parent
PROFILE = (FIRMWARE / "sdkconfig.defaults.signed").read_text()
BUILD = (ROOT / "scripts" / "build_signed.sh").read_text()


def test_profile_verifies_updates_without_hardware_secure_boot():
    opts = dict(re.findall(r"^(CONFIG_\w+)=(\S+)$", PROFILE, re.M))
    assert opts == {"CONFIG_SECURE_SIGNED_APPS_NO_SECURE_BOOT": "y", "CONFIG_SECURE_SIGNED_APPS_RSA_SCHEME": "y",
                    "CONFIG_SECURE_SIGNED_ON_UPDATE_NO_SECURE_BOOT": "y", "CONFIG_SECURE_BOOT_BUILD_SIGNED_BINARIES": "y"}
    # nothing that burns eFuses or changes what the bootloader accepts
    assert "CONFIG_SECURE_BOOT=y" not in PROFILE and "FLASH_ENC" not in PROFILE
    assert "SIGNING_KEY" not in "".join(l for l in PROFILE.splitlines() if not l.startswith("#"))   # key never in the repo


def test_signed_build_starts_from_the_committed_sdkconfig():
    # building from sdkconfig.defaults alone loses the partition table, flash
    # mode and size: the first version of this script produced an image for a
    # 1 MB factory partition
    assert 'grep -Ev "^(# )?CONFIG_($SIGNED_OPTS)[= ]" "$ROOT/firmware/$PROJECT/sdkconfig"' in BUILD
    assert "SDKCONFIG_DEFAULTS" not in BUILD
    assert 'build/signed' in BUILD                      # inside the git-ignored build directory


def test_only_boards_with_ota_are_signed():
    assert "class_c6|class_s3) ;;" in BUILD and "student)" in BUILD


def test_default_builds_are_unchanged():
    for project in ("class_c6", "class_s3", "student"):
        cfg = (FIRMWARE / project / "sdkconfig").read_text()
        assert "CONFIG_SECURE_SIGNED_APPS_NO_SECURE_BOOT=y" not in cfg, project
