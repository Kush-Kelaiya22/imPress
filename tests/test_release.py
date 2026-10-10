"""Releases (#96, #100, #104): owner-prefixed names, patch numbers per push,
the CHANGELOG, the release page, Beta/Stable status, the workflow's safety
settings, and the backend container image.
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


# ── Names ───────────────────────────────────────────────────────────────────

def test_integration_lines_and_tags_carry_the_owner():
    assert release.parse_branch("varun/v2.1") == ("varun", "2.1")
    assert release.parse_branch("kush/v2.1") == ("kush", "2.1")
    for not_a_line in ("fix/v2.1-quiz-timer", "main", "varun/v2.1-experimental", "stranger/v2.1", ""):
        assert release.parse_branch(not_a_line) is None, not_a_line
    assert release.parse_tag("varun/v2.1.4") == ("varun", "2.1.4")
    assert release.parse_tag("v2.1.0") == (None, "2.1.0")                     # before #104
    assert release.parse_tag("varun/v2.1") is None
    assert release.tag_for("aamna", "2.1.7") == "aamna/v2.1.7"
    assert release.asset_base("varun", "2.1.4") == "impress-varun-2.1.4"
    assert release.title_for("varun/v2.1.4", "beta") == "varun/v2.1.4 (Beta)"
    assert release.title_for("varun/v2.1.4", "stable") == "varun/v2.1.4"


# ── Version per owner ───────────────────────────────────────────────────────

def _repo(tmp_path, version="2.1.0"):
    def g(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)
    g("init", "-q", "-b", "main")
    g("config", "user.email", "t@example.edu")
    g("config", "user.name", "t")
    (tmp_path / "VERSION").write_text(version + "\n")
    (tmp_path / "docs" / "releases").mkdir(parents=True)
    (tmp_path / "docs" / "releases" / f"v{version.rsplit('.', 1)[0]}.md").write_text("{{tag}}\n")
    g("add", "-A")
    g("commit", "-qm", "base")
    return g


def test_first_release_of_a_line_is_patch_zero(tmp_path):
    _repo(tmp_path)
    assert release.release_version("varun", tmp_path) == "2.1.0"


def test_patch_counts_pushes_since_the_owners_line_tag(tmp_path):
    g = _repo(tmp_path)
    g("tag", "varun/v2.1.0")
    assert release.release_version("varun", tmp_path) == "2.1.0"
    for n in range(3):
        g("commit", "-q", "--allow-empty", "-m", f"push {n}")
    assert release.release_version("varun", tmp_path) == "2.1.3"
    g("switch", "-q", "-c", "feature")                 # a merged branch counts once
    g("commit", "-q", "--allow-empty", "-m", "a")
    g("commit", "-q", "--allow-empty", "-m", "b")
    g("switch", "-q", "main")
    g("merge", "-q", "--no-ff", "-m", "merge", "feature")
    assert release.release_version("varun", tmp_path) == "2.1.4"
    assert release.previous_tag("varun", "2.1.4", tmp_path) == "varun/v2.1.0"
    # another owner's line has its own numbering
    assert release.release_version("kush", tmp_path) == "2.1.0"
    assert release.previous_tag("kush", "2.1.0", tmp_path) is None


def test_plan_refuses_feature_branches(tmp_path):
    _repo(tmp_path)
    ok = release.plan("varun/v2.1", tmp_path)
    assert ok["releasable"] and ok["tag"] == "varun/v2.1.0" and ok["asset"] == "impress-varun-2.1.0"
    assert ok["line"] == "2.1" and ok["warning"] == ""
    assert not release.plan("fix/v2.1-x", tmp_path)["releasable"]


def test_the_branch_name_decides_the_line(tmp_path):
    """aamna/v2.4 branched from a 2.1 tree releases aamna/v2.4.0 right away (VERSION is only checked)."""
    _repo(tmp_path)
    p = release.plan("aamna/v2.4", tmp_path)
    assert p["releasable"] and p["tag"] == "aamna/v2.4.0" and p["version"] == "2.4.0"
    assert "VERSION says 2.1" in p["warning"]
    assert p["template"].endswith("v2.1.md")                     # the newest template is used


def test_template_falls_back_to_the_default_branch(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _repo(repo)
    (repo / "docs" / "releases" / "v2.1.md").unlink()             # an old branch without templates
    defaults = tmp_path / "defaults"
    defaults.mkdir()
    (defaults / "v2.1.md").write_text("old")
    (defaults / "v2.3.md").write_text("new")
    assert release.find_template("2.4.0", repo, defaults).name == "v2.3.md"
    assert release.find_template("2.4.0", repo, None) is None
    assert not release.plan("kush/v2.4", repo)["releasable"]


def test_version_file_is_semver_and_its_line_has_a_page_template():
    version = release.read_version()
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)
    assert release.notes_path(version).exists(), "add docs/releases/v<MAJOR.MINOR>.md for a new line"


# ── CHANGELOG ───────────────────────────────────────────────────────────────

CHANGELOG = """# Changelog

## [Unreleased]

### Added

- New thing (#1)

### Changed

- Different thing,
  over two lines (#2)

### Removed

- Old thing (#3)

## [varun/v2.1.3] - 2026-10-10

### Fixed

- Released fix (#4)
"""


def test_unreleased_entries_are_read_by_category():
    entries = release.unreleased(CHANGELOG)
    assert entries["Added"] == ["New thing (#1)"]
    assert entries["Changed"] == ["Different thing, over two lines (#2)"]
    assert entries["Removed"] == ["Old thing (#3)"] and entries["Fixed"] == []        # not from a release section


def test_release_page_lists_only_entries_new_since_the_previous_release():
    later = CHANGELOG.replace("- Old thing (#3)", "- Old thing (#3)\n\n### Fixed\n\n- Crash fixed (#5)")
    new = release.new_entries(later, CHANGELOG)
    assert new == {"Added": [], "Changed": [], "Removed": [], "Fixed": ["Crash fixed (#5)"], "Security": []}
    assert release.new_entries(CHANGELOG, "")["Added"] == ["New thing (#1)"]      # no changelog before


def test_changes_render_as_added_changed_removed_fixed_with_prs_folded():
    text = release.render_changes(release.unreleased(CHANGELOG), "* feat: x by @a in #9")
    assert text.index("**Added**") < text.index("**Changed**") < text.index("**Removed**")
    assert "- New thing (#1)" in text and "**Fixed**" not in text
    assert "<details><summary>Pull requests in this release</summary>" in text and "* feat: x by @a in #9" in text
    assert "No changes for users" in release.render_changes({c: [] for c in release.CATEGORIES})


def test_changelog_structure_is_checked():
    assert release.check_changelog(CHANGELOG) == []
    assert release.check_changelog("# Changelog\n") == ["missing the '## [Unreleased]' section"]
    bad = CHANGELOG.replace("### Removed", "### Deleted").replace("- New thing", "* New thing")
    problems = release.check_changelog(bad)
    assert any("Deleted" in p for p in problems) and any("use '- '" in p for p in problems)


def test_the_repository_changelog_is_valid():
    text = (ROOT / "CHANGELOG.md").read_text()
    assert release.check_changelog(text) == []
    assert any(release.unreleased(text).values()), "the Unreleased section should not be empty after a change"


# ── Release page ────────────────────────────────────────────────────────────

PAGE_SECTIONS = ("What changed since", "Downloads", "Requirements", "Install and set up", "First use",
                 "Check the installation", "Setup problems", "Upgrade", "Verify the downloads",
                 "Help and documentation")


def test_page_template_follows_the_predefined_structure():
    template = release.notes_path(release.read_version()).read_text()
    headings = re.findall(r"^## (.+)$", template, re.M)
    assert [h.split(" {{")[0] for h in headings] == list(PAGE_SECTIONS)
    assert not [c for c in template if unicodedata.category(c) == "So" and ord(c) > 0x2600]
    assert release.START not in template                     # the workflow adds the status section
    assert "troubleshooting.md#setup-problems" in template


def test_page_renders_with_owner_names_and_no_placeholders_left():
    template = release.notes_path(release.read_version()).read_text()
    text = release.render_notes(template, "varun", "2.1.7", "varun/v2.1.6", "**Added**\n\n- x")
    assert "{{" not in text and "release **varun/v2.1.7**" in text and "`varun/v2.1`" in text
    assert "impress-varun-2.1.7.zip" in text and "impress-backend:varun-2.1.7" in text
    assert "## What changed since varun/v2.1.6" in text and "/blob/varun/v2.1.7/" in text
    assert '"version":"2.1.7"' in text


def test_unknown_placeholder_is_refused():
    with pytest.raises(ValueError):
        release.render_notes("{{version}} {{oops}}", "varun", "2.1.1", None, "")


def test_setup_problems_section_exists_in_the_troubleshooting_guide():
    guide = (ROOT / "docs/guides/troubleshooting.md").read_text()
    assert re.search(r"^## Setup problems$", guide, re.M)


# ── Status section ──────────────────────────────────────────────────────────

def test_beta_block_is_compact_with_the_renamed_columns():
    block = release.status_block("varun/v2.1.4", "beta", ISSUES, REPO)
    assert block.startswith(release.START) and block.endswith(release.END)
    assert "| No. | Issue | Assigned to | Status |" in block
    assert ("| [#83](https://github.com/Kush-Kelaiya22/imPress/issues/83) | Timed quizzes on real modules "
            "| @Kush-Kelaiya22 |") in block and "| nobody |" in block
    assert "for-the-badge" not in block and "style=flat-square" in block
    assert "badge/release-beta-d29922" in block and "badge/tests%20closed-0%20of%202-0969da" in block
    assert "> [!WARNING]" in block and "2 of 2 release test issues are open" in block
    assert "milestone%3A%22varun/v2.1%22" in block and "Test issues for varun/v2.1" in block
    assert "img.shields.io/github/" not in block


def test_stable_block_uses_a_note():
    block = release.status_block("varun/v2.1.4", "stable", CLOSED, REPO)
    assert "> [!NOTE]" in block and "[!TIP]" not in block and "All 2 release test issues are closed" in block
    assert 'alt="closed: completed"' in block and "badge/release-stable-2da44e" in block


def test_open_rows_come_first_and_one_issue_reads_correctly():
    block = release.status_block("varun/v2.1.4", "beta", [CLOSED[0], ISSUES[1]], REPO)
    assert "1 of 2 release test issue is open" in block
    assert block.index("issues/84)") < block.index("issues/83)")


def test_state_badges_distinguish_open_completed_and_not_planned():
    assert "badge/open-2da44e" in release.state_badge({"state": "open"})
    assert "closed:%20completed-8250df" in release.state_badge({"state": "closed", "state_reason": "completed"})
    assert "closed:%20not%20planned-6e7781" in release.state_badge({"state": "closed", "state_reason": "not_planned"})


def test_status_block_is_replaced_in_place_and_idempotent():
    notes = "## What changed since varun/v2.1.3\n\nBody.\n"
    beta = release.apply_status(notes, release.status_block("varun/v2.1.4", "beta", ISSUES, REPO))
    assert beta.endswith(notes)
    assert release.apply_status(beta, release.status_block("varun/v2.1.4", "beta", ISSUES, REPO)) == beta
    stable = release.apply_status(beta, release.status_block("varun/v2.1.4", "stable", CLOSED, REPO))
    assert stable.count(release.START) == 1 and "[!NOTE]" in stable and stable.endswith(notes)


def test_newest_compares_numerically():
    assert release.newest(["2.9.0", "2.10.0", "2.1.0"]) == "2.10.0"
    assert release.newest(["bad"]) is None and release.newest([]) is None


# ── Which milestones gate a release (#104) ──────────────────────────────────

def _ancestry(pairs):
    """A fake git: `older` is an ancestor of `newer` when (older, newer) is listed."""
    return lambda older, newer: (older, newer) in pairs


BUILT_ON = _ancestry({("varun/v2.1.0", "varun/v2.3.0"), ("varun/v2.1.0", "aamna/v2.4.2")})


@pytest.mark.parametrize("tag,milestone,expected", [
    ("varun/v2.1.4", "varun/v2.1", True),        # its own line
    ("varun/v2.3.0", "varun/v2.1", True),        # a later line of the same owner, built on 2.1.0
    ("aamna/v2.4.2", "varun/v2.1", True),        # another owner's line branched from varun/v2.1
    ("kush/v2.2.0", "varun/v2.1", False),        # not built on varun/v2.1.0
    ("varun/v2.1.4", "varun/v2.3", False),       # an older release is not gated by a newer line
    ("varun/v2.1.4", "varun/v2.1.4", True),      # exact milestone
    ("varun/v2.1.5", "varun/v2.1.4", False),
    ("varun/v2.1.0", "v2.1", True),              # legacy milestone without an owner
    ("varun/v2.1.0", "Sprint 3", False),         # not a release milestone
])
def test_milestone_gating_follows_the_git_ancestry(tag, milestone, expected):
    assert release.gates(tag, milestone, BUILT_ON) is expected


def test_ancestry_is_read_from_git(tmp_path):
    g = _repo(tmp_path)
    g("tag", "varun/v2.1.0")
    g("switch", "-q", "-c", "aamna/v2.4")                 # aamna branches from varun/v2.1
    g("commit", "-q", "--allow-empty", "-m", "aamna work")
    g("tag", "aamna/v2.4.0")
    g("switch", "-q", "--orphan", "kush/v2.2")            # unrelated history
    g("commit", "-q", "--allow-empty", "-m", "kush root")
    g("tag", "kush/v2.2.0")
    assert release.is_ancestor("varun/v2.1.0", "aamna/v2.4.0", tmp_path)
    assert not release.is_ancestor("varun/v2.1.0", "kush/v2.2.0", tmp_path)
    assert not release.is_ancestor("aamna/v2.4.0", "varun/v2.1.0", tmp_path)
    assert release.gates("aamna/v2.4.0", "varun/v2.1", lambda a, b: release.is_ancestor(a, b, tmp_path))


def test_inherited_issues_are_marked_with_their_line(monkeypatch):
    fake = FakeGitHub([], [{"number": 1, "title": "varun/v2.1"}, {"number": 2, "title": "varun/v2.3"}],
                      [dict(ISSUES[0]), dict(ISSUES[1], milestone=2)])
    monkeypatch.setattr(release, "gh", fake.gh)
    found = release.test_issues(REPO, "varun/v2.3.0", fake.milestones, ancestor=BUILT_ON)
    assert {i["number"]: i["from"] for i in found} == {83: "varun/v2.1", 84: ""}
    block = release.status_block("varun/v2.3.0", "beta", found, REPO)
    assert "Timed quizzes on real modules <sub>from varun/v2.1</sub>" in block


def test_a_new_release_is_published_with_its_status_section(monkeypatch, tmp_path):
    """#104: the first page already has the badges, the Beta/Stable box and the test issues."""
    fake = FakeGitHub([], LINE, ISSUES)
    monkeypatch.setattr(release, "gh", fake.gh)
    monkeypatch.setattr(release, "is_ancestor", lambda older, newer, root=None: True)
    status, body = release.initial_page(REPO, "varun/v2.1.5", "abc1234", "## Install and set up\n\nSteps.\n", tmp_path)
    assert status == "beta" and body.startswith(release.START) and body.endswith("Steps.\n")
    assert "| No. | Issue | Assigned to | Status |" in body and "> [!WARNING]" in body
    closed = FakeGitHub([], LINE, CLOSED)
    monkeypatch.setattr(release, "gh", closed.gh)
    assert release.initial_page(REPO, "varun/v2.1.5", "abc1234", "x", tmp_path)[0] == "stable"


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
                                 "state_reason": i.get("state_reason"),
                                 "assignees": [{"login": a} for a in i["assignees"]]}
                                for i in self.issues if i["milestone"] == number]])
        raise AssertionError(path)


def _release(tag, prerelease, body="Notes.", rid=1):
    return {"id": rid, "tag_name": tag, "name": tag, "body": body, "prerelease": prerelease, "draft": False}


LINE = [{"number": 1, "title": "varun/v2.1"}]


def test_closing_a_2_1_issue_updates_every_release_built_on_2_1(monkeypatch):
    """The cascade: one milestone, three lines from two owners."""
    rels = [_release("varun/v2.1.4", True, rid=1), _release("varun/v2.3.0", True, rid=2),
            _release("aamna/v2.4.2", True, rid=3), _release("kush/v2.2.0", False, rid=4)]
    fake = FakeGitHub(rels, LINE, CLOSED)
    monkeypatch.setattr(release, "gh", fake.gh)
    changed = {c["tag"]: c["status"] for c in release.sync(REPO, ancestor=BUILT_ON)}
    assert changed["varun/v2.1.4"] == changed["varun/v2.3.0"] == changed["aamna/v2.4.2"] == "stable"
    reopened = FakeGitHub(rels, LINE, ISSUES)
    monkeypatch.setattr(release, "gh", reopened.gh)
    release.sync(REPO, ancestor=BUILT_ON)
    beta = {path.rsplit("/", 1)[1]: u["prerelease"] for path, u in reopened.patches}
    assert beta["1"] and beta["2"] and beta["3"] and not beta.get("4", False)


def test_sync_marks_every_release_of_the_owners_line_beta(monkeypatch):
    fake = FakeGitHub([_release("varun/v2.1.0", False), _release("varun/v2.1.3", False, rid=2),
                       _release("kush/v2.1.0", False, rid=3)], LINE, ISSUES)
    monkeypatch.setattr(release, "gh", fake.gh)
    changed = {c["tag"]: c["status"] for c in release.sync(REPO)}
    assert changed["varun/v2.1.0"] == changed["varun/v2.1.3"] == "beta"
    assert changed["kush/v2.1.0"] == "stable"               # another owner's line: its own (empty) milestone
    updates = {path.rsplit("/", 1)[1]: u for path, u in fake.patches}
    assert updates["1"]["name"] == "varun/v2.1.0 (Beta)" and updates["1"]["prerelease"] is True
    assert updates["3"]["name"] == "kush/v2.1.0" and updates["3"]["prerelease"] is False


def test_sync_promotes_to_stable_and_the_newest_becomes_latest(monkeypatch):
    fake = FakeGitHub([_release("varun/v2.1.0", True, rid=1), _release("varun/v2.1.3", True, rid=2)], LINE, CLOSED)
    monkeypatch.setattr(release, "gh", fake.gh)
    release.sync(REPO)
    updates = {path.rsplit("/", 1)[1]: u for path, u in fake.patches}
    assert updates["2"]["make_latest"] == "true" and updates["1"]["make_latest"] == "false"
    assert updates["2"]["name"] == "varun/v2.1.3" and "[!NOTE]" in updates["2"]["body"]


def test_an_exact_patch_milestone_also_gates(monkeypatch):
    issue = dict(ISSUES[0], milestone=7)
    fake = FakeGitHub([_release("varun/v2.1.3", False)], [{"number": 7, "title": "varun/v2.1.3"}], [issue])
    monkeypatch.setattr(release, "gh", fake.gh)
    release.sync(REPO)
    assert fake.patches[0][1]["prerelease"] is True


def test_sync_changes_nothing_when_already_correct(monkeypatch):
    body = release.apply_status("Notes.", release.status_block("varun/v2.1.0", "stable", CLOSED, REPO))
    fake = FakeGitHub([_release("varun/v2.1.0", False, body)], LINE, CLOSED, latest="varun/v2.1.0")
    monkeypatch.setattr(release, "gh", fake.gh)
    assert release.sync(REPO) == [] and fake.patches == []


def test_image_tags_per_owner_and_line():
    rels = [_release("varun/v2.1.2", False), _release("varun/v2.1.3", True, rid=2),
            _release("varun/v2.2.0", True, rid=3), _release("aamna/v2.4.1", False, rid=4)]
    assert release.image_aliases(rels) == {
        "aamna-2.4": "aamna-2.4.1", "aamna-latest": "aamna-2.4.1",
        "varun-2.1": "varun-2.1.3", "varun-2.2": "varun-2.2.0",
        "varun-beta": "varun-2.2.0", "varun-latest": "varun-2.1.2"}
    assert release.legacy_images(rels)["varun-2.1.2"] == "2.1.2"


# ── The workflows ───────────────────────────────────────────────────────────

WORKFLOW = ROOT / ".github/workflows/release.yml"


@pytest.fixture(scope="module")
def wf():
    yaml = pytest.importorskip("yaml")
    return yaml.safe_load(WORKFLOW.read_text())


def test_triggers_cover_every_owners_line(wf):
    on = wf.get("on", wf.get(True))
    assert on["workflow_run"]["workflows"] == ["CI"]
    owners = set(wf["env"]["RELEASE_OWNERS"].split())
    assert set(on["workflow_run"]["branches"]) == {f"{o}/**" for o in owners}
    assert owners == set(release.OWNERS)
    ci = pytest.importorskip("yaml").safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    assert {f"{o}/**" for o in owners} <= set(ci.get("on", ci.get(True))["push"]["branches"])
    assert {"closed", "reopened", "milestoned", "demilestoned", "labeled", "unlabeled"} <= set(on["issues"]["types"])


def test_publishing_needs_a_green_ci_push_on_an_integration_line(wf):
    cond = " ".join(wf["jobs"]["plan"]["if"].split())
    assert "workflow_run.conclusion == 'success'" in cond and "workflow_run.event == 'push'" in cond
    decide = wf["jobs"]["plan"]["steps"][-1]["run"]
    assert '"$RUNNER_TEMP/release.py" plan --branch "$BRANCH" --root .' in decide and "releasable" in decide
    assert 'git show "origin/$DEFAULT_BRANCH:scripts/release.py"' in decide       # current rules on old branches
    assert "gh release view" in decide                                  # never re-creates a release
    assert wf["jobs"]["plan"]["steps"][0]["with"]["fetch-depth"] == 0


def test_least_privilege_and_no_cancelled_releases(wf):
    assert wf["permissions"] == {"contents": "read"}
    assert wf["concurrency"]["cancel-in-progress"] is False
    assert wf["jobs"]["release"]["permissions"] == {"contents": "write", "issues": "write"}
    assert wf["jobs"]["status"]["steps"][0]["with"]["fetch-depth"] == 0              # ancestry needs every tag
    assert wf["jobs"]["image"]["permissions"] == {"contents": "read", "packages": "write"}
    for name, job in wf["jobs"].items():
        assert 0 < job.get("timeout-minutes", 0) <= 60, name


def test_release_is_built_from_a_tested_image_and_firmware(wf):
    rel = wf["jobs"]["release"]
    assert set(rel["needs"]) == {"plan", "image", "firmware"}
    image = "\n".join(s.get("run", "") for s in wf["jobs"]["image"]["steps"])
    assert image.index("> VERSION") < image.index("docker build") < image.index("smoke_test.py") < image.index("docker push")
    assert '"$OWNER-$LINE"' in image and '"$OWNER-$VERSION"' in image
    assert sorted(wf["jobs"]["firmware"]["strategy"]["matrix"]["project"]) == sorted(run_tests.IDF_PROJECTS)
    assert wf["jobs"]["firmware"]["container"] == run_tests.IDF_IMAGE
    firmware = "\n".join(s.get("run", "") for s in wf["jobs"]["firmware"]["steps"])
    assert "version.txt" in firmware.split("idf.py build")[0]
    publish = "\n".join(s.get("run", "") for s in rel["steps"])
    assert '"$RUNNER_TEMP/release.py" notes "$TAG" prs.md --root . --templates' in publish and "CHANGELOG.md" in publish
    assert 'title="$OWNER/v$LINE"' in publish                                     # the line's milestone
    assert "--verify-tag" in publish and 'page "$TAG" notes.md --sha "$SHA" --out body.md --root .' in publish
    assert "--notes-file body.md" in publish and "--prerelease" in publish
    assert 'git/ref/tags/$TAG" -q .object.sha)" = "$SHA"' in publish


def test_ci_requires_a_changelog_entry_on_pull_requests():
    yaml = pytest.importorskip("yaml")
    ci = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    job = ci["jobs"]["changelog"]
    run = job["steps"][-1]["run"]
    assert "no-changelog" in run and "grep -qx CHANGELOG.md" in run and "check-changelog" in run
    assert job["steps"][0]["with"]["fetch-depth"] == 0 and "changelog" in ci["jobs"]["result"]["needs"]


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


def test_build_context_is_an_allow_list():
    lines = [l for l in (ROOT / ".dockerignore").read_text().splitlines() if l and not l.startswith("#")]
    assert lines[0] == "*"
    copied = set(re.findall(r"^COPY (.+) \S+$", (ROOT / "Dockerfile").read_text(), re.M))
    allowed = {l[1:] for l in lines if l.startswith("!")}
    for group in copied:
        for path in group.split():
            assert path in allowed, f"{path} is copied but excluded from the build context"
