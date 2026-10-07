"""The CI workflow is well-formed and actually runs every suite the repo has.

These tests fail when someone adds a firmware project, a test suite or a
setting without wiring it into CI, or weakens the pipeline's safety settings.
"""

import re

from conftest import ROOT

import run_tests


def _steps_text(job) -> str:
    return "\n".join(str(s.get("run", "")) + " " + str(s.get("uses", "")) for s in job["steps"])


def test_triggers_include_push_pr_and_manual(workflow):
    on = workflow.get("on", workflow.get(True))        # PyYAML parses bare `on:` as True
    assert {"push", "pull_request", "workflow_dispatch"} <= set(on)


def test_least_privilege_and_concurrency(workflow):
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] is True
    assert "github.ref" in workflow["concurrency"]["group"]


def test_every_job_has_runner_and_timeout(workflow):
    for name, job in workflow["jobs"].items():
        assert "runs-on" in job, name
        assert 0 < job.get("timeout-minutes", 0) <= 60, f"{name} needs a timeout"


def test_actions_are_pinned_to_major_versions(workflow):
    for name, job in workflow["jobs"].items():
        for step in job["steps"]:
            uses = step.get("uses")
            if uses:
                assert re.search(r"@v\d+$", uses), f"{name}: unpinned or floating action {uses}"


def test_every_default_runner_suite_runs_in_ci(workflow):
    ci = "\n".join(_steps_text(j) for j in workflow["jobs"].values())
    groups = {s.name.split(":")[0] for s in run_tests.discover() if not s.optional}
    for group in groups:
        assert re.search(rf"run_tests\.py --suite {re.escape(group)}\b", ci), f"suite '{group}' not run in CI"


def test_every_firmware_project_is_built(workflow):
    projects = sorted(p.parent.parent.name for p in (ROOT / "firmware").glob("*/main/CMakeLists.txt"))
    matrix = workflow["jobs"]["firmware-build"]["strategy"]["matrix"]["project"]
    assert sorted(matrix) == projects
    assert sorted(run_tests.IDF_PROJECTS) == projects


def test_idf_version_is_consistent(workflow):
    image = workflow["jobs"]["firmware-build"]["container"]
    assert image == run_tests.IDF_IMAGE
    version = image.split(":")[1]                      # v6.1
    assert f"ESP--IDF-{version}" in (ROOT / "README.md").read_text()      # README badge
    assert version in (ROOT / "docs/guides/development-setup.md").read_text()


def test_result_gate_needs_every_other_job(workflow):
    jobs = set(workflow["jobs"]) - {"result"}
    gate = workflow["jobs"]["result"]
    assert set(gate["needs"]) == jobs and gate["if"] == "always()"


def test_python_and_dependency_files_exist(workflow):
    assert float(workflow["env"]["PYTHON_VERSION"]) >= 3.12
    dev = (ROOT / "backend/requirements-dev.txt").read_text()
    assert "-r requirements.txt" in dev and "pytest" in dev and "pyyaml" in dev
    assert (ROOT / "frontend/package.json").exists()


def test_test_reports_are_uploaded(workflow):
    for job in ("repo", "backend"):
        text = _steps_text(workflow["jobs"][job])
        assert "--junit-dir reports" in text and "actions/upload-artifact" in text


def test_workflow_is_linted_in_ci(workflow):
    text = _steps_text(workflow["jobs"]["repo"])
    assert re.search(r"rhysd/actionlint:\d+\.\d+\.\d+", text), "actionlint must run, pinned to a release"
