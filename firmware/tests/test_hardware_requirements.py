"""#30: hardware requirements stay true to the build configuration."""

import re

from c_source import FIRMWARE

DOC = FIRMWARE.parent / "docs" / "hardware" / "CLASSROOM_NODE_REQUIREMENTS.md"
PROJECTS = ("class_c6", "class_s3", "student")


def _cfg(project, key):
    m = re.search(rf"^{key}=(.*)$", (FIRMWARE / project / "sdkconfig").read_text(), re.M)
    return m.group(1).strip('"') if m else None


def _partitions_end(project):
    rows = [[c.strip() for c in l.split(",")] for l in (FIRMWARE / project / "partitions.csv").read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    return max(int(r[3], 16) + int(r[4], 16) for r in rows)


def test_psram_is_optional_on_the_hub():
    # a module without PSRAM must still boot: no code allocates from it
    assert _cfg("class_s3", "CONFIG_SPIRAM_IGNORE_NOTFOUND") == "y"
    assert "CONFIG_SPIRAM_IGNORE_NOTFOUND=y" in (FIRMWARE / "class_s3" / "sdkconfig.defaults").read_text()
    src = "".join(p.read_text() for p in (FIRMWARE / "class_s3" / "main").glob("*.c"))
    assert "MALLOC_CAP_SPIRAM" not in src and "EXT_RAM_BSS_ATTR" not in src


def test_flash_table_matches_partitions_and_headers():
    doc = DOC.read_text()
    for project in PROJECTS:
        end = _partitions_end(project)
        minimum = 1 << (end - 1).bit_length()               # next power of two
        header = _cfg(project, "CONFIG_ESPTOOLPY_FLASHSIZE")
        row = re.search(rf"^\| `{project}` \| (0x[0-9A-F]+) \| (\d+) MB \| (\d+) MB \|", doc, re.M)
        assert row, project
        assert (int(row.group(1), 16), int(row.group(2)) << 20, row.group(3) + "MB") == (end, minimum, header), project


def test_student_capacity_matches_on_hub_and_gateway():
    hub = re.search(r"#define MESH_MAX_STUDENTS\s+(\d+)", (FIRMWARE / "class_s3/main/config.h").read_text()).group(1)
    gw = re.search(r"#define STUDENT_SET_MAX\s+(\d+)", (FIRMWARE / "class_c6/main/student_set.h").read_text()).group(1)
    assert hub == gw and f"≤ {hub}" in DOC.read_text()
