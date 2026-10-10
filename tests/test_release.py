"""#96: release status rules, the release workflow's safety settings, and the
backend container image.

A release is Beta while an open `testing` issue is in its milestone, Stable
otherwise; the workflow publishes only after CI passed on the default branch.
"""

import json
import re
import sys
import unicodedata

import pytest

from conftest import ROOT

import run_tests

sys.path.insert(0, str(ROOT / "scripts"))
import release  # noqa: E402

REPO = "Kush-Kelaiya22/imPress"
ISSUES = [{"number": 83, "title": "timed quizzes", "milestone": 1},
          {"number": 84, "title": "bench bring-up", "milestone": 1}]


# ── Status rules ────────────────────────────────────────────────────────────

def test_open_test_issues_make_a_release_beta():
    assert release.status_of(ISSUES) == "beta"
    assert release.status_of([]) == "stable"


def test_title_says_beta_only_while_beta():
    assert release.title_for("2.1.0", "beta") == "imPress 2.1.0 (Beta)"
    assert release.title_for("2.1.0", "stable") == "imPress 2.1.0"


def test_beta_block_has_badge_and_lists_open_issues():
    block = release.status_block("2.1.0", "beta", ISSUES, REPO)
    assert block.startswith(release.START) and block.endswith(release.END)
    assert release.BADGE["beta"] in block and 'alt="Status: Beta"' in block
    assert "2 test issues are open" in block
    for i in ISSUES:
        assert f"[#{i['number']}](https://github.com/{REPO}/issues/{i['number']}) {i['title']}" in block
    assert f"https://github.com/{REPO}/milestone/1" in block


def test_one_open_issue_reads_correctly():
    assert "1 test issue is open" in release.status_block("2.1.0", "beta", ISSUES[:1], REPO)


def test_stable_block_says_it_can_go_back_to_beta():
    block = release.status_block("2.1.0", "stable", [], REPO)
    assert release.BADGE["stable"] in block and "Status: Stable" in block
    assert "changes back to Beta" in block and "milestone%3Av2.1.0" in block


def test_status_block_is_replaced_in_place_and_idempotent():
    notes = "# imPress 2.1.0\n\nBody text.\n"
    beta = release.apply_status(notes, release.status_block("2.1.0", "beta", ISSUES, REPO))
    assert beta.startswith(release.START) and beta.endswith(notes)
    assert release.apply_status(beta, release.status_block("2.1.0", "beta", ISSUES, REPO)) == beta
    stable = release.apply_status(beta, release.status_block("2.1.0", "stable", [], REPO))
    assert stable.count(release.START) == 1 and "Status: Stable" in stable and "Status: Beta" not in stable
    assert stable.endswith(notes)


def test_newest_compares_numerically():
    assert release.newest(["2.9.0", "2.10.0", "2.1.0"]) == "2.10.0"
    assert release.newest(["2.1.0-rc1", "bad"]) is None and release.newest([]) is None


def test_version_file_is_semver_and_its_release_notes_exist():
    version = release.read_version()
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert release.notes_path(version).exists(), "add docs/releases/v<VERSION>.md before bumping VERSION"


# ── sync against a fake GitHub ──────────────────────────────────────────────

class FakeGitHub:
    def __init__(self, releases, milestones, issues, latest=None):
        self.releases, self.milestones, self.issues, self.latest = releases, milestones, issues, latest
        self.patches = []

    def gh(self, *args, input=None):
        if args[:3] == ("api", "-X", "PATCH"):
            self.patches.append((args[3], json.loads(input)))
            return "{}"
        if args[1].endswith("/releases/latest"):
            if not self.latest:
                raise release.subprocess.CalledProcessError(1, "gh")
            return json.dumps({"tag_name": self.latest})
        path = args[-1]
        if path.endswith("/releases"):
            return json.dumps([self.releases])
        if "/milestones" in path:
            return json.dumps([self.milestones])
        if "/issues?" in path:
            number = int(re.search(r"milestone=(\d+)", path).group(1))
            return json.dumps([[i for i in self.issues if i["milestone"] == number]])
        raise AssertionError(path)


def _release(tag, prerelease, body="Notes."):
    return {"id": 1, "tag_name": tag, "name": f"imPress {tag[1:]}", "body": body,
            "prerelease": prerelease, "draft": False}


def test_sync_marks_beta_while_test_issues_are_open(monkeypatch):
    fake = FakeGitHub([_release("v2.1.0", False)], [{"number": 1, "title": "v2.1.0"}],
                      [{"number": 83, "title": "t", "milestone": 1}])
    monkeypatch.setattr(release, "gh", fake.gh)
    assert release.sync(REPO) == [{"tag": "v2.1.0", "status": "beta"}]
    (_, update), = fake.patches
    assert update["prerelease"] is True and update["make_latest"] == "false"
    assert update["name"] == "imPress 2.1.0 (Beta)" and "Status: Beta" in update["body"]


def test_sync_promotes_to_stable_when_the_last_issue_closes(monkeypatch):
    beta_body = release.apply_status("Notes.", release.status_block("2.1.0", "beta", ISSUES, REPO))
    fake = FakeGitHub([_release("v2.1.0", True, beta_body)], [{"number": 1, "title": "v2.1.0"}], [])
    monkeypatch.setattr(release, "gh", fake.gh)
    assert release.sync(REPO) == [{"tag": "v2.1.0", "status": "stable"}]
    (_, update), = fake.patches
    assert update["prerelease"] is False and update["make_latest"] == "true"
    assert update["name"] == "imPress 2.1.0" and "Status: Stable" in update["body"]
    assert update["body"].endswith("Notes.")


def test_sync_without_a_milestone_is_stable(monkeypatch):
    fake = FakeGitHub([_release("v2.1.0", True)], [], [])
    monkeypatch.setattr(release, "gh", fake.gh)
    release.sync(REPO)
    assert fake.patches[0][1]["prerelease"] is False


def test_sync_changes_nothing_when_already_correct(monkeypatch):
    body = release.apply_status("Notes.", release.status_block("2.1.0", "stable", [], REPO))
    rel = _release("v2.1.0", False, body) | {"name": "imPress 2.1.0"}
    fake = FakeGitHub([rel], [{"number": 1, "title": "v2.1.0"}], [], latest="v2.1.0")
    monkeypatch.setattr(release, "gh", fake.gh)
    assert release.sync(REPO) == [] and fake.patches == []


# ── The workflow ────────────────────────────────────────────────────────────

WORKFLOW = ROOT / ".github/workflows/release.yml"


@pytest.fixture(scope="module")
def wf():
    yaml = pytest.importorskip("yaml")
    return yaml.safe_load(WORKFLOW.read_text())


def test_triggers(wf):
    on = wf.get("on", wf.get(True))
    assert on["workflow_run"]["workflows"] == ["CI"] and on["workflow_run"]["types"] == ["completed"]
    assert {"closed", "reopened", "milestoned", "demilestoned", "labeled", "unlabeled"} <= set(on["issues"]["types"])
    assert "schedule" in on and "workflow_dispatch" in on


def test_publishing_needs_a_green_ci_push_on_the_default_branch(wf):
    cond = " ".join(wf["jobs"]["plan"]["if"].split())
    for part in ("workflow_run.conclusion == 'success'", "workflow_run.event == 'push'",
                 "workflow_run.head_branch == github.event.repository.default_branch"):
        assert part in cond
    decide = wf["jobs"]["plan"]["steps"][-1]["run"]
    assert '"$GITHUB_REF_NAME" = "$DEFAULT_BRANCH"' in decide          # manual runs too
    assert "notes_present" in decide and "gh release view" in decide   # never re-creates a release


def test_least_privilege_and_no_cancelled_releases(wf):
    assert wf["permissions"] == {"contents": "read"}
    assert wf["concurrency"]["cancel-in-progress"] is False
    assert wf["jobs"]["release"]["permissions"] == {"contents": "write"}
    assert wf["jobs"]["image"]["permissions"] == {"contents": "read", "packages": "write"}
    for name, job in wf["jobs"].items():
        assert 0 < job.get("timeout-minutes", 0) <= 60, name


def test_release_waits_for_a_tested_image_and_firmware(wf):
    rel = wf["jobs"]["release"]
    assert set(rel["needs"]) == {"plan", "image", "firmware"}
    steps = "\n".join(s.get("run", "") for s in wf["jobs"]["image"]["steps"])
    assert steps.index("smoke_test.py") < steps.index("docker push")
    assert sorted(wf["jobs"]["firmware"]["strategy"]["matrix"]["project"]) == sorted(run_tests.IDF_PROJECTS)
    assert wf["jobs"]["firmware"]["container"] == run_tests.IDF_IMAGE
    publish = "\n".join(s.get("run", "") for s in rel["steps"])
    assert "--verify-tag" in publish and 'git/ref/tags/$TAG" -q .object.sha)" = "$SHA"' in publish


def test_actions_are_pinned_to_commit_shas():
    uses = re.findall(r"^\s*-?\s*uses:\s*(\S+)(.*)$", WORKFLOW.read_text(), re.M)
    assert uses
    for ref, comment in uses:
        assert re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", ref), ref
        assert re.search(r"#\s*v\d+\.\d+\.\d+", comment), ref


# ── The container image ─────────────────────────────────────────────────────

def test_dockerfile_is_pinned_unprivileged_and_health_checked():
    text = (ROOT / "Dockerfile").read_text()
    assert re.search(r"^FROM python:3\.12-slim@sha256:[0-9a-f]{64}$", text, re.M)
    assert "pip install --require-hashes -r backend/requirements-lock.txt" in text
    user = re.findall(r"^USER\s+(\S+)", text, re.M)
    assert user and user[-1] not in ("root", "0")
    assert re.search(r"^HEALTHCHECK ", text, re.M) and 'VOLUME ["/data"]' in text
    assert "sqlite+aiosqlite:////data/impress.db" in text


def test_build_context_is_an_allow_list():
    lines = [l for l in (ROOT / ".dockerignore").read_text().splitlines() if l and not l.startswith("#")]
    assert lines[0] == "*"
    copied = set(re.findall(r"^COPY (.+) \S+$", (ROOT / "Dockerfile").read_text(), re.M))
    allowed = {l[1:] for l in lines if l.startswith("!")}
    for group in copied:
        for path in group.split():
            assert path in allowed, f"{path} is copied but excluded from the build context"


# ── Release notes ───────────────────────────────────────────────────────────

def test_release_notes_cover_setup_test_and_deploy_without_emoji():
    notes = release.notes_path(release.read_version()).read_text()
    for heading in ("Downloads", "Set up the server", "Test the installation", "Deploy to a classroom",
                    "Upgrade from 2.0", "Verify the downloads"):
        assert re.search(rf"^##\s+{heading}", notes, re.M), heading
    assert not [c for c in notes if unicodedata.category(c) == "So" and ord(c) > 0x2600]
    assert release.START not in notes            # the workflow adds the status block
