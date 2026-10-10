"""#96: release status rules, the release workflow's safety settings, and the
backend container image.

A release is Beta while an open `testing` issue is in its milestone, Stable
otherwise; the workflow publishes only after CI passed on the default branch.
"""

import json
import re
import subprocess
import sys
import unicodedata

import pytest

from conftest import ROOT

import run_tests

sys.path.insert(0, str(ROOT / "scripts"))
import release  # noqa: E402

REPO = "Kush-Kelaiya22/imPress"
ISSUES = [{"number": 83, "title": "test(hardware): timed quizzes on real modules", "state": "open",
           "milestone": 1, "assignees": ["Kush-Kelaiya22"]},
          {"number": 84, "title": "test(hardware): bench bring-up", "state": "open", "milestone": 1, "assignees": []}]
CLOSED = [dict(i, state="closed", state_reason="completed") for i in ISSUES]


# ── Version (#100) ──────────────────────────────────────────────────────────

def _repo(tmp_path, version="2.1.0"):
    def g(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@example.edu")
    g("config", "user.name", "t")
    (tmp_path / "VERSION").write_text(version + "\n")
    g("add", "VERSION")
    g("commit", "-qm", "base")
    return g


def test_first_release_of_a_line_is_patch_zero(tmp_path):
    _repo(tmp_path)
    assert release.release_version(tmp_path) == "2.1.0"


def test_patch_counts_first_parent_commits_since_the_line_tag(tmp_path):
    g = _repo(tmp_path)
    g("tag", "v2.1.0")
    assert release.release_version(tmp_path) == "2.1.0"           # the tagged commit keeps its number
    for n in range(3):
        g("commit", "-q", "--allow-empty", "-m", f"push {n}")
    assert release.release_version(tmp_path) == "2.1.3"
    # a merged feature branch with two commits counts once (one push to the default branch)
    g("switch", "-q", "-c", "feature")
    g("commit", "-q", "--allow-empty", "-m", "a")
    g("commit", "-q", "--allow-empty", "-m", "b")
    g("switch", "-q", "main")
    g("merge", "-q", "--no-ff", "-m", "merge", "feature")
    assert release.release_version(tmp_path) == "2.1.4"
    assert release.previous_tag("2.1.4", tmp_path) == "v2.1.0"


def test_a_new_line_starts_again_at_zero(tmp_path):
    g = _repo(tmp_path)
    g("tag", "v2.1.0")
    g("commit", "-q", "--allow-empty", "-m", "more")
    (tmp_path / "VERSION").write_text("2.2.0\n")
    g("commit", "-qam", "2.2")
    assert release.release_version(tmp_path) == "2.2.0"
    assert release.previous_tag("2.2.0", tmp_path) == "v2.1.0"


def test_version_file_is_semver_and_its_line_has_release_notes():
    version = release.read_version()
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert release.notes_path(version).exists(), "add docs/releases/v<MAJOR.MINOR>.md for a new line"


# ── Release notes template ──────────────────────────────────────────────────

def test_notes_template_renders_every_placeholder():
    template = release.notes_path(release.read_version()).read_text()
    text = release.render_notes(template, "2.1.7", "v2.1.6", "* fix(x): y by @a in #1")
    assert "{{" not in text and "imPress 2.1.7" in text and "impress-2.1.7.zip" in text
    assert "## Changes since v2.1.6" in text and "* fix(x): y by @a in #1" in text
    assert "impress-backend:2.1.7" in text and "/blob/v2.1.7/" in text
    assert "2.1.0" not in text.replace("v2.1.0", "")          # no version left hard-coded
    assert "No pull requests were merged" in release.render_notes(template, "2.1.7", "v2.1.6")


def test_unknown_placeholder_is_refused():
    with pytest.raises(ValueError):
        release.render_notes("{{version}} {{oops}}", "2.1.1", None)


def test_generated_heading_is_removed():
    assert release.clean_changes("## What's Changed\n* a in #1\n\n**Full Changelog**: x") == \
        "* a in #1\n\n**Full Changelog**: x"


# ── Status rules ────────────────────────────────────────────────────────────

def test_open_test_issues_make_a_release_beta():
    assert release.status_of(ISSUES) == "beta"
    assert release.status_of(CLOSED) == "stable" and release.status_of([]) == "stable"


def test_title_says_beta_only_while_beta():
    assert release.title_for("2.1.0", "beta") == "imPress 2.1.0 (Beta)"
    assert release.title_for("2.1.0", "stable") == "imPress 2.1.0"


def test_test_area_drops_the_conventional_prefix():
    assert release.test_area("test(hardware): bench bring-up: flash") == "Bench bring-up: flash"
    assert release.test_area("timed quizzes") == "Timed quizzes"


def test_beta_block_has_badges_alert_and_a_table_with_status():
    block = release.status_block("2.1.0", "beta", ISSUES, REPO)
    assert block.startswith(release.START) and block.endswith(release.END)
    assert release.BADGE["beta"] in block and "badge/tests%20closed-0%20of%202-0969da" in block
    assert "> [!WARNING]" in block and "2 of 2 release test issues are still open" in block
    assert "| Issue | Test area | Owner | Status |" in block
    assert ("| [#83](https://github.com/Kush-Kelaiya22/imPress/issues/83) | Timed quizzes on real modules "
            "| @Kush-Kelaiya22 |") in block
    assert "| unassigned |" in block
    assert block.count('alt="open" src="https://img.shields.io/badge/open-2da44e') == 2
    assert "img.shields.io/github/" not in block          # static badges only: they never fail to load


def test_one_open_issue_reads_correctly_and_open_rows_come_first():
    issues = [CLOSED[0], ISSUES[1]]
    block = release.status_block("2.1.0", "beta", issues, REPO)
    assert "1 of 2 release test issue is still open" in block
    assert block.index("issues/84)") < block.index("issues/83)")


def test_stable_block_lists_closed_issues_and_says_it_can_go_back():
    block = release.status_block("2.1.0", "stable", CLOSED, REPO)
    assert release.BADGE["stable"] in block and "> [!TIP]" in block
    assert "All 2 release test issues are closed" in block and "changes back to Beta" in block
    assert 'alt="closed: completed"' in block and "badge/tests%20closed-2%20of%202-0969da" in block


def test_status_block_is_replaced_in_place_and_idempotent():
    notes = "## Changes since v2.1.0\n\nBody text.\n"
    beta = release.apply_status(notes, release.status_block("2.1.1", "beta", ISSUES, REPO))
    assert beta.startswith(release.START) and beta.endswith(notes)
    assert release.apply_status(beta, release.status_block("2.1.1", "beta", ISSUES, REPO)) == beta
    stable = release.apply_status(beta, release.status_block("2.1.1", "stable", CLOSED, REPO))
    assert stable.count(release.START) == 1 and "[!TIP]" in stable and "[!WARNING]" not in stable
    assert stable.endswith(notes)


def test_state_badges_distinguish_open_completed_and_not_planned():
    assert "badge/open-2da44e" in release.state_badge({"state": "open"})
    assert "badge/closed:%20completed-8250df" in release.state_badge({"state": "closed", "state_reason": "completed"})
    assert "badge/closed:%20not%20planned-6e7781" in release.state_badge({"state": "closed",
                                                                       "state_reason": "not_planned"})
    assert release._badge_text("a-b c_d") == "a--b%20c__d"


def test_newest_compares_numerically():
    assert release.newest(["2.9.0", "2.10.0", "2.1.0"]) == "2.10.0"
    assert release.newest(["2.1.0-rc1", "bad"]) is None and release.newest([]) is None


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
            assert "state=all" in path and "labels=testing" in path
            number = int(re.search(r"milestone=(\d+)", path).group(1))
            return json.dumps([[{"number": i["number"], "title": i["title"], "state": i["state"],
                                 "state_reason": i.get("state_reason"), "assignees": [{"login": a} for a in i["assignees"]]}
                                for i in self.issues if i["milestone"] == number]])
        raise AssertionError(path)


def _release(tag, prerelease, body="Notes.", rid=1):
    return {"id": rid, "tag_name": tag, "name": f"imPress {tag[1:]}", "body": body,
            "prerelease": prerelease, "draft": False}


LINE = [{"number": 1, "title": "v2.1"}]


def test_sync_marks_every_release_of_the_line_beta_while_issues_are_open(monkeypatch):
    fake = FakeGitHub([_release("v2.1.0", False), _release("v2.1.3", False, rid=2)], LINE, ISSUES)
    monkeypatch.setattr(release, "gh", fake.gh)
    assert {c["tag"] for c in release.sync(REPO)} == {"v2.1.0", "v2.1.3"}
    for _, update in fake.patches:
        assert update["prerelease"] is True and update["make_latest"] == "false"
        assert "(Beta)" in update["name"] and "[!WARNING]" in update["body"]


def test_sync_promotes_to_stable_when_the_last_issue_closes(monkeypatch):
    beta_body = release.apply_status("Notes.", release.status_block("2.1.3", "beta", ISSUES, REPO))
    fake = FakeGitHub([_release("v2.1.0", True, rid=1), _release("v2.1.3", True, beta_body, rid=2)], LINE, CLOSED)
    monkeypatch.setattr(release, "gh", fake.gh)
    release.sync(REPO)
    updates = {path.rsplit("/", 1)[1]: u for path, u in fake.patches}
    assert updates["2"]["prerelease"] is False and updates["2"]["make_latest"] == "true"      # newest stable
    assert updates["1"]["prerelease"] is False and updates["1"]["make_latest"] == "false"
    assert updates["2"]["name"] == "imPress 2.1.3" and "[!TIP]" in updates["2"]["body"]
    assert updates["2"]["body"].endswith("Notes.")


def test_an_exact_patch_milestone_also_gates(monkeypatch):
    issue = dict(ISSUES[0], milestone=7)
    fake = FakeGitHub([_release("v2.1.3", False)], [{"number": 7, "title": "v2.1.3"}], [issue])
    monkeypatch.setattr(release, "gh", fake.gh)
    release.sync(REPO)
    assert fake.patches[0][1]["prerelease"] is True


def test_sync_without_a_milestone_is_stable(monkeypatch):
    fake = FakeGitHub([_release("v2.1.0", True)], [], [])
    monkeypatch.setattr(release, "gh", fake.gh)
    release.sync(REPO)
    assert fake.patches[0][1]["prerelease"] is False


def test_sync_changes_nothing_when_already_correct(monkeypatch):
    body = release.apply_status("Notes.", release.status_block("2.1.0", "stable", CLOSED, REPO))
    rel = _release("v2.1.0", False, body) | {"name": "imPress 2.1.0"}
    fake = FakeGitHub([rel], LINE, CLOSED, latest="v2.1.0")
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
    assert wf["jobs"]["plan"]["steps"][0]["with"]["fetch-depth"] == 0      # the patch counts commits


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
    assert "generate-notes" in publish and "release.py notes" in publish and "--notes-file notes.md" in publish
    assert 'printf \'%s\\n\' "$VERSION"' in publish                       # the bundle reports the release version
    firmware = "\n".join(s.get("run", "") for s in wf["jobs"]["firmware"]["steps"])
    assert "version.txt" in firmware.split("idf.py build")[0]               # stamped before the build
    image = "\n".join(s.get("run", "") for s in wf["jobs"]["image"]["steps"])
    assert image.index("> VERSION") < image.index("docker build")
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
    for heading in ("Changes since", "Downloads", "Set up the server", "Test the installation", "Deploy to a classroom",
                    "Upgrade from an earlier 2.1 release", "Upgrade from 2.0", "Verify the downloads"):
        assert re.search(rf"^##\s+{heading}", notes, re.M), heading
    assert not [c for c in notes if unicodedata.category(c) == "So" and ord(c) > 0x2600]
    assert release.START not in notes            # the workflow adds the status block
