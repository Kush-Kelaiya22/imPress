"""The CI workflow is well-formed and actually runs every suite the repo has.

These tests fail when someone adds a firmware project, a test suite or a
setting without wiring it into CI, or weakens the pipeline's safety settings.
"""

import re

from conftest import ROOT

import run_tests


def _steps_text(job) -> str:
    return "\n".join(str(s.get("run", "")) + " " + str(s.get("uses", "")) for s in job["steps"])


def _on(workflow):
    return workflow.get("on", workflow.get(True))      # PyYAML parses bare `on:` as True


def test_triggers_include_push_pr_and_manual(workflow):
    assert {"push", "pull_request", "workflow_dispatch"} <= set(_on(workflow))


def test_push_runs_only_on_long_lived_branches(workflow):
    # PR branches are built by `pull_request`; an unfiltered push trigger ran
    # every pipeline twice per PR push.
    on = _on(workflow)
    branches = set(on["push"]["branches"])
    assert {"main", "v2", "varun/**"} <= branches
    assert not (on["pull_request"] or {}).get("branches"), "PRs into any base must be checked"


def test_least_privilege_and_concurrency(workflow):
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] is True
    assert "github.ref" in workflow["concurrency"]["group"]


def test_every_job_has_runner_and_timeout(workflow):
    for name, job in workflow["jobs"].items():
        assert "runs-on" in job, name
        assert 0 < job.get("timeout-minutes", 0) <= 60, f"{name} needs a timeout"


WORKFLOW_FILE = ROOT / ".github/workflows/ci.yml"


def test_actions_are_pinned_to_commit_shas():
    # A tag can be moved to new code; a commit SHA can't. The comment names the release.
    uses = re.findall(r"^\s*-?\s*uses:\s*(\S+)(.*)$", WORKFLOW_FILE.read_text(), re.M)
    assert uses
    for ref, comment in uses:
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", ref), f"not pinned to a commit: {ref}"
        assert re.search(r"#\s*v\d+\.\d+\.\d+", comment), f"{ref}: add '# vX.Y.Z' after the SHA"


def test_container_images_are_pinned_to_digests(workflow):
    text = WORKFLOW_FILE.read_text()
    for image in re.findall(r"(?:docker run [^\n]*?|container:\s*)((?:espressif|rhysd)/[\w./-]+:[\w.-]+(?:@sha256:[0-9a-f]{64})?)", text):
        assert re.search(r"@sha256:[0-9a-f]{64}$", image), f"image not pinned by digest: {image}"
    assert run_tests.IDF_IMAGE == workflow["jobs"]["firmware-build"]["container"]


def test_every_default_runner_suite_runs_in_ci(workflow):
    ci = "\n".join(_steps_text(j) for j in workflow["jobs"].values())
    groups = {s.name.split(":")[0] for s in run_tests.discover() if not s.optional}
    for group in groups:
        assert re.search(rf"run_tests\.py --suite {re.escape(group)}\b", ci), f"suite '{group}' not run in CI"


def test_browser_ui_checks_run_in_ci(workflow):
    job = workflow["jobs"]["ui"]
    text = _steps_text(job)
    assert "run_tests.py --suite ui" in text and "playwright install --with-deps chromium" in text
    assert "ui_tests/requirements.txt" in text          # the pinned Playwright version comes from there
    upload = next(s for s in job["steps"] if "upload-artifact" in str(s.get("uses")))
    assert "ui_tests/screenshots/" in upload["with"]["path"] and upload["if"] == "always()"


def test_every_firmware_project_is_built(workflow):
    projects = sorted(p.parent.parent.name for p in (ROOT / "firmware").glob("*/main/CMakeLists.txt"))
    matrix = workflow["jobs"]["firmware-build"]["strategy"]["matrix"]["project"]
    assert sorted(matrix) == projects
    assert sorted(run_tests.IDF_PROJECTS) == projects


def test_idf_version_is_consistent(workflow):
    image = workflow["jobs"]["firmware-build"]["container"]
    assert image == run_tests.IDF_IMAGE
    version = image.split("@")[0].split(":")[1]        # v6.1
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


def _norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def test_ci_installs_the_hash_locked_dependency_set(workflow):
    lock = (ROOT / "backend/requirements-lock.txt").read_text()
    locked = {_norm(m) for m in re.findall(r"^([A-Za-z0-9_.-]+)==", lock, re.M)}
    # every direct runtime and dev requirement is in the lock, pinned and hashed
    for name in run_tests._requirements(ROOT / run_tests.DEV_REQUIREMENTS):
        assert _norm(name) in locked, f"{name} missing from requirements-lock.txt (re-run pip-compile)"
    assert lock.count("--hash=sha256:") >= len(locked)
    for job in ("repo", "backend"):
        text = _steps_text(workflow["jobs"][job])
        assert "pip install --require-hashes -r backend/requirements-lock.txt" in text, job


def test_frontend_is_installed_from_its_lockfile(workflow):
    assert (ROOT / "frontend/package-lock.json").exists()
    frontend = {s.name: s for s in run_tests.discover()}["frontend"]
    assert "npm ci" in " ".join(frontend.cmd)
    setup = next(s for s in workflow["jobs"]["frontend"]["steps"] if "setup-node" in str(s.get("uses")))
    assert setup["with"]["cache-dependency-path"] == "frontend/package-lock.json"


def test_python_is_linted(workflow):
    assert "ruff check" in _steps_text(workflow["jobs"]["repo"])
    cfg = (ROOT / "pyproject.toml").read_text()
    assert re.search(r'select\s*=\s*\[[^\]]*"F"', cfg), "ruff must run the pyflakes rules"


def test_dependencies_are_audited(workflow):
    sec = _steps_text(workflow["jobs"]["security"])
    assert "pip-audit" in sec and "requirements-lock.txt" in sec
    assert "npm audit --audit-level=high" in sec


def test_backend_coverage_is_reported(workflow):
    text = _steps_text(workflow["jobs"]["backend"])
    assert re.search(r"run_tests\.py --suite backend .*--coverage reports", text)
    assert "pytest-cov" in (ROOT / "backend/requirements-dev.txt").read_text()
    # async SQLAlchemy (greenlets) + TestClient (thread): otherwise under-reported on 3.12
    assert re.search(r'concurrency\s*=\s*\[[^\]]*"greenlet"[^\]]*"thread"', (ROOT / "pyproject.toml").read_text())


def test_firmware_artifacts_carry_checksums(workflow):
    job = workflow["jobs"]["firmware-build"]
    assert "sha256sum" in _steps_text(job)
    upload = next(s for s in job["steps"] if "upload-artifact" in str(s.get("uses")))
    assert "SHA256SUMS" in upload["with"]["path"]


def test_test_reports_are_uploaded(workflow):
    for job in ("repo", "backend"):
        text = _steps_text(workflow["jobs"][job])
        assert "--junit-dir reports" in text and "actions/upload-artifact" in text


def test_workflow_is_linted_in_ci(workflow):
    text = _steps_text(workflow["jobs"]["repo"])
    assert re.search(r"rhysd/actionlint:\d+\.\d+\.\d+", text), "actionlint must run, pinned to a release"
