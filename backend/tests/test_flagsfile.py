"""The launch flags file: every flag explained, edits applied, mistakes named, the hardened profile never loosened."""

import json
from pathlib import Path

import pytest

from app import flagsfile, gpc
from app.services.features import FEATURES

SHIPPED = Path(__file__).resolve().parents[1] / flagsfile.FILE_NAME


@pytest.fixture
def file(tmp_path):
    path = tmp_path / "flags.json"
    path.write_text(json.dumps(flagsfile.template()))
    return path


def _edit(path, **changes):
    doc = json.loads(path.read_text())
    for name, value in changes.items():
        section = "features" if name in FEATURES else "flags"
        doc[section][name]["value"] = value
    path.write_text(json.dumps(doc))


def test_the_template_explains_every_flag_and_feature():
    t = flagsfile.template()
    assert set(t["flags"]) == {n for n, f in gpc.FLAGS.items() if f.scope == "feature"}
    assert {n for n in t["features"] if not n.startswith("_")} == set(FEATURES)
    for name, entry in t["flags"].items():
        assert entry["about"] and entry["value"] == entry["standard"] == gpc.FLAGS[name].standard
        assert entry["hardened"] == gpc.FLAGS[name].hardened


def test_the_file_in_the_repository_matches_the_catalogue():
    """It must list the same flags with the same explanations; the values are the owner's to edit."""
    shipped, fresh = json.loads(SHIPPED.read_text()), flagsfile.template()
    for name, entry in fresh["flags"].items():
        mine = shipped["flags"][name]
        assert {k: v for k, v in mine.items() if k != "value"} == {k: v for k, v in entry.items() if k != "value"}, \
            f"{name} drifted: run  python -m app.flagsfile write --force"
    assert set(shipped["flags"]) == set(fresh["flags"]) and set(shipped["features"]) == set(fresh["features"])


def test_an_untouched_file_changes_nothing(file):
    assert flagsfile.load(file) == (None, [])


def test_a_missing_file_is_not_an_error(tmp_path):
    assert flagsfile.load(tmp_path / "none.json") == (None, [])


def test_edited_values_become_overrides(file):
    _edit(file, **{"test_mode.forced": True, "ota.enabled": False, "traffic.monitor": False})
    profile, overrides = flagsfile.load(file)
    assert profile is None
    assert set(overrides) == {"test_mode.forced=true", "ota.enabled=false", "traffic.monitor=false"}
    parsed = gpc.parse_inline(",".join(overrides))
    assert parsed == {"test_mode.forced": True, "ota.enabled": False, "traffic.monitor": False}


def test_features_switched_off_become_features_disabled(file):
    _edit(file, search=False, backups=False)
    _, overrides = flagsfile.load(file)
    assert overrides == ["features.disabled=backups,search"]


def test_the_profile_is_read(file):
    doc = json.loads(file.read_text())
    doc["profile"]["value"] = "hardened"
    file.write_text(json.dumps(doc))
    assert flagsfile.load(file)[0] == "hardened"


@pytest.mark.parametrize("edit,needle", [
    (lambda d: d["flags"].update({"no.such.flag": {"value": 1}}), "no.such.flag"),
    (lambda d: d["flags"]["ota.enabled"].update(value="maybe"), "ota.enabled"),
    (lambda d: d["flags"].update({"dual_control.delay_minutes": {"value": 4}}), "FLAG_IS_POLICY"),
    (lambda d: d["features"].update({"nothing": {"value": False}}), "nothing"),
    (lambda d: d["features"]["search"].update(value="off"), "features.search"),
    (lambda d: d["profile"].update(value="paranoid"), "paranoid"),
    (lambda d: d["flags"]["ota.enabled"].pop("value"), "needs a \"value\""),
])
def test_a_mistake_is_named(file, edit, needle):
    doc = json.loads(file.read_text())
    edit(doc)
    file.write_text(json.dumps(doc))
    with pytest.raises(flagsfile.FlagsFileError, match=needle.replace('"', '.')):
        flagsfile.load(file)


def test_invalid_json_is_an_error_not_a_stack_trace(file):
    file.write_text("{ not json")
    with pytest.raises(flagsfile.FlagsFileError, match="not valid JSON"):
        flagsfile.load(file)


def test_a_bare_value_is_accepted(file):
    doc = json.loads(file.read_text())
    doc["flags"]["ota.enabled"] = False
    file.write_text(json.dumps(doc))
    assert flagsfile.load(file)[1] == ["ota.enabled=false"]


def test_an_untouched_file_does_not_loosen_the_hardened_profile(file):
    _, overrides = flagsfile.load(file)
    pol = gpc.build("hardened", ",".join(overrides), None, None)
    assert pol.values["dual_control.delay_minutes"] == 15 and pol.values["test_mode.allowed"] is False and pol.values["ota.enabled"]


def test_an_edit_that_loosens_the_hardened_profile_is_refused(file):
    _edit(file, **{"ota.enabled": False})
    _, overrides = flagsfile.load(file)
    with pytest.raises(gpc.PolicyError, match="loosen"):
        gpc.build("hardened", ",".join(overrides), None, None)


def test_it_is_written_once_and_never_overwritten(tmp_path):
    target = tmp_path / "f.json"
    assert flagsfile.write(target=target) == target
    target.write_text('{"flags": {}}')
    assert flagsfile.write(target=target) is None and target.read_text() == '{"flags": {}}'
    assert flagsfile.write(force=True, target=target) == target and "_readme" in json.loads(target.read_text())


def test_the_reference_page_lists_everything():
    text = flagsfile.reference()
    assert all(f"`{n}`" in text for n in gpc.FLAGS) and all(f"`{n}`" in text for n in FEATURES)


def test_the_reference_page_in_the_docs_is_current():
    doc = Path(__file__).resolve().parents[2] / "docs/reference/flags.md"
    assert doc.read_text() == flagsfile.reference(), "run  python -m app.flagsfile docs > docs/reference/flags.md"


def test_the_command_line_wins_over_the_environment_and_the_file(file, monkeypatch):
    from app import serve
    _edit(file, **{"test_mode.export_allowed": False})
    monkeypatch.setenv("IMPRESS_FLAGS_FILE", str(file))
    monkeypatch.setenv("IMPRESS_GPC", "test_mode.export_allowed=true")
    _, flags = serve.effective(["--feature", "test_mode.export_allowed=false"])
    assert gpc.parse_inline(",".join(flags))["test_mode.export_allowed"] is False         # the command line
    _, flags = serve.effective([])
    assert gpc.parse_inline(",".join(flags))["test_mode.export_allowed"] is True           # then the environment, over the file
    monkeypatch.delenv("IMPRESS_GPC")
    _, flags = serve.effective([])
    assert gpc.parse_inline(",".join(flags))["test_mode.export_allowed"] is False          # the file alone
