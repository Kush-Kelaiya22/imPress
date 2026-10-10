#!/usr/bin/env python3
"""Release helper for .github/workflows/release.yml (#96, #100, #104).

Names. Releases come from integration lines named <owner>/vMAJOR.MINOR (for
example varun/v2.1) and are named <owner>/vMAJOR.MINOR.PATCH (varun/v2.1.4).
Owners are listed in RELEASE_OWNERS.

Version. The branch name gives MAJOR.MINOR (VERSION should agree; the plan
warns when it doesn't). PATCH is the number of first-parent commits on the
line since the owner's first release of it, tag <owner>/vMAJOR.MINOR.0;
without that tag the release is <owner>/vMAJOR.MINOR.0. Every push that passes
CI is the next patch release, and the same commit always gets the same number.

Changes. CHANGELOG.md is kept by every pull request (CONTRIBUTING §14.4). A
release page lists the entries under "Unreleased" that are new since the
previous release of the same line, grouped as Added / Changed / Removed /
Fixed / Security.

Status. A release is Beta while an open issue labelled `testing` is in a
milestone that gates it, Stable otherwise. A line milestone <owner>/vX.Y gates
every release built on top of that line's first release <owner>/vX.Y.0 (git
ancestry), whoever owns the branch; an exact milestone <owner>/vX.Y.Z gates
that one release. The page starts with a status section the workflow redraws
on every issue change.

    scripts/release.py plan --branch varun/v2.1 [--root DIR]     # JSON for the workflow
    scripts/release.py notes varun/v2.1.4 [prs.md] [--root DIR] [--templates DIR]
    scripts/release.py sync [--tag varun/v2.1.4]     # Beta/Stable (gh CLI, GH_TOKEN)
    scripts/release.py channels                      # JSON: per owner, newest stable and beta
    scripts/release.py check-changelog               # CHANGELOG.md structure (exit 1 on problems)
    scripts/release.py page TAG notes.md --sha SHA --out body.md   # the complete first page (status + text)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OWNERS = tuple(os.environ.get("RELEASE_OWNERS", "varun kush aamna encrypted").split())
GATE_LABEL = os.environ.get("RELEASE_GATE_LABEL", "testing")
START, END = "<!-- release-status:start -->", "<!-- release-status:end -->"
SHIELDS = "https://img.shields.io"
CATEGORIES = ("Added", "Changed", "Removed", "Fixed", "Security")
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
_TAG = re.compile(r"^(?:(?P<owner>[a-z0-9-]+)/)?v(?P<version>\d+\.\d+\.\d+)$")
_BRANCH = re.compile(r"^(?P<owner>[a-z0-9-]+)/v(?P<line>\d+\.\d+)$")


def _key(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version.split("."))


# ── Names and versions ──────────────────────────────────────────────────────

def read_version(root: Path = ROOT) -> str:
    version = (root / "VERSION").read_text().strip()
    if not _SEMVER.match(version):
        raise ValueError(f"VERSION must be MAJOR.MINOR.PATCH, got {version!r}")
    return version


def line_of(version: str) -> str:
    return ".".join(version.split(".")[:2])


def parse_branch(branch: str) -> tuple[str, str] | None:
    """'varun/v2.1' -> ('varun', '2.1') for a listed owner's integration line, else None."""
    m = _BRANCH.match(branch or "")
    return (m["owner"], m["line"]) if m and m["owner"] in OWNERS else None


def parse_tag(tag: str) -> tuple[str | None, str] | None:
    """'varun/v2.1.4' -> ('varun', '2.1.4'); legacy 'v2.1.0' -> (None, '2.1.0')."""
    m = _TAG.match(tag or "")
    return (m["owner"], m["version"]) if m else None


def tag_for(owner: str, version: str) -> str:
    return f"{owner}/v{version}"


def asset_base(owner: str, version: str) -> str:
    return f"impress-{owner}-{version}"


def git(*args: str, root: Path = ROOT) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def owner_versions(owner: str, root: Path = ROOT) -> list[str]:
    """This owner's release versions that exist as tags, oldest first."""
    found = []
    for t in git("tag", "--list", f"{owner}/v*", root=root).split():
        parsed = parse_tag(t)
        if parsed and parsed[0] == owner:
            found.append(parsed[1])
    return sorted(found, key=_key)


def release_version(owner: str, root: Path = ROOT, rev: str = "HEAD", line: str | None = None) -> str:
    line = line or line_of(read_version(root))
    anchor = tag_for(owner, f"{line}.0")
    if f"{line}.0" not in owner_versions(owner, root):
        return f"{line}.0"
    count = git("rev-list", "--count", "--first-parent", f"{anchor}..{rev}", root=root)
    return f"{line}.{int(count)}"


def previous_tag(owner: str, version: str, root: Path = ROOT) -> str | None:
    older = [v for v in owner_versions(owner, root) if _key(v) < _key(version)]
    return tag_for(owner, older[-1]) if older else None


def plan(branch: str, root: Path = ROOT, templates: Path | None = None) -> dict:
    """What a push to `branch` publishes. The branch name decides the line."""
    parsed = parse_branch(branch)
    if not parsed:
        return {"releasable": False, "reason": f"{branch!r} is not an integration line <owner>/vX.Y of {', '.join(OWNERS)}"}
    owner, line = parsed
    version = release_version(owner, root, line=line)
    template = find_template(version, root, templates)
    file_line = line_of(read_version(root))
    warning = "" if file_line == line else f"VERSION says {file_line}; the branch name {line} is used"
    return {"releasable": template is not None,
            "reason": "" if template else f"no page template docs/releases/v{line}.md (and no fallback)",
            "warning": warning, "owner": owner, "line": line, "version": version, "tag": tag_for(owner, version),
            "previous": previous_tag(owner, version, root) or "", "asset": asset_base(owner, version),
            "template": str(template) if template else ""}


# ── Changelog ───────────────────────────────────────────────────────────────

def unreleased(changelog: str) -> dict[str, list[str]]:
    """Entries under '## [Unreleased]', by category; each entry is one '- ' bullet."""
    m = re.search(r"^## \[Unreleased\][^\n]*\n(.*?)(?=^## |\Z)", changelog, re.S | re.M)
    out: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    if not m:
        return out
    current = None
    for line in m.group(1).splitlines():
        head = re.match(r"^### (\w+)", line)
        if head:
            current = head.group(1) if head.group(1) in CATEGORIES else None
        elif current and line.startswith("- "):
            out[current].append(line[2:].strip())
        elif current and line.startswith("  ") and out[current]:
            out[current][-1] += " " + line.strip()
    return out


def check_changelog(text: str) -> list[str]:
    """Structure problems in CHANGELOG.md (empty list = valid)."""
    problems = []
    if not re.search(r"^## \[Unreleased\]", text, re.M):
        problems.append("missing the '## [Unreleased]' section")
    for n, line in enumerate(text.splitlines(), 1):
        head = re.match(r"^### (.+)$", line)
        if head and head.group(1).strip() not in CATEGORIES:
            problems.append(f"line {n}: '### {head.group(1)}' is not one of {', '.join(CATEGORIES)}")
        if re.match(r"^\s*[*+] ", line):
            problems.append(f"line {n}: use '- ' for entries")
    for m in re.finditer(r"^## \[([^\]]+)\]", text, re.M):
        name = m.group(1)
        if name != "Unreleased" and not parse_tag(name) and not re.match(r"^v?\d+\.\d+(\.\d+)?$", name):
            problems.append(f"'## [{name}]' is not 'Unreleased', a release tag or a version")
    return problems


def changelog_at(rev: str | None, root: Path = ROOT) -> str:
    if rev is None:
        return ""
    try:
        return git("show", f"{rev}:CHANGELOG.md", root=root)
    except subprocess.CalledProcessError:
        return ""


def new_entries(current: str, previous: str) -> dict[str, list[str]]:
    """Unreleased entries in `current` that are not in `previous`."""
    before = {e for entries in unreleased(previous).values() for e in entries}
    return {c: [e for e in entries if e not in before] for c, entries in unreleased(current).items()}


def render_changes(entries: dict[str, list[str]], prs: str = "") -> str:
    blocks = [f"**{c}**\n\n" + "\n".join(f"- {e}" for e in items) for c, items in entries.items() if items]
    text = "\n\n".join(blocks) if blocks else "No changes for users in this release. See the pull requests below."
    prs = prs.strip()
    if prs:
        text += f"\n\n<details><summary>Pull requests in this release</summary>\n\n{prs}\n\n</details>"
    return text


def clean_prs(generated: str) -> str:
    """GitHub's generated notes, without their own heading."""
    return re.sub(r"^## What's Changed\s*\n", "", generated.strip()).strip()


# ── Release text ────────────────────────────────────────────────────────────

def notes_path(version: str, root: Path = ROOT) -> Path:
    """One release-page template per line: docs/releases/vMAJOR.MINOR.md."""
    return root / "docs" / "releases" / f"v{line_of(version)}.md"


def find_template(version: str, root: Path = ROOT, fallback: Path | None = None) -> Path | None:
    """The line's own template; else the newest template in `fallback` (the default branch's docs/releases)."""
    own = notes_path(version, root)
    if own.exists():
        return own
    candidates = []
    for d in (root / "docs" / "releases", fallback):
        if d and d.is_dir():
            candidates += [f for f in d.glob("v*.md") if re.fullmatch(r"v\d+\.\d+\.md", f.name)]
    return max(candidates, key=lambda f: _key(f.stem[1:]), default=None)


def render_notes(template: str, owner: str, version: str, previous: str | None, changes: str) -> str:
    values = {"version": version, "owner": owner, "line": line_of(version), "tag": tag_for(owner, version),
              "branch": f"{owner}/v{line_of(version)}", "asset": asset_base(owner, version),
              "previous": previous or "the previous release", "changes": changes.strip()}
    text = re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), template)
    leftover = re.findall(r"\{\{\w+\}\}", text)
    if leftover:
        raise ValueError(f"unknown placeholders in the release notes: {sorted(set(leftover))}")
    return text


# ── Status ──────────────────────────────────────────────────────────────────

def status_of(issues: list[dict]) -> str:
    return "beta" if any(i.get("state", "open") == "open" for i in issues) else "stable"


def title_for(tag: str, status: str) -> str:
    return tag + (" (Beta)" if status == "beta" else "")


def issue_title(title: str) -> str:
    """'test(hardware): bench bring-up: …' -> 'Bench bring-up: …'."""
    text = re.sub(r"^\w+(\([^)]*\))?:\s*", "", title).strip()
    return text[:1].upper() + text[1:]


def _badge_text(text: str) -> str:
    return text.replace("-", "--").replace("_", "__").replace(" ", "%20")


def badge(label: str, message: str, color: str) -> str:
    path = f"{_badge_text(label)}-{_badge_text(message)}" if label else _badge_text(message)
    return f'<img alt="{(label + ": ") if label else ""}{message}" src="{SHIELDS}/badge/{path}-{color}?style=flat-square">'


def state_badge(issue: dict) -> str:
    if issue.get("state", "open") == "open":
        return badge("", "open", "2da44e")
    if issue.get("state_reason") == "not_planned":
        return badge("", "closed: not planned", "6e7781")
    return badge("", "closed: completed", "8250df")


def status_block(tag: str, status: str, issues: list[dict], repo: str) -> str:
    owner, version = parse_tag(tag)
    milestone = f"{owner}/v{line_of(version)}" if owner else f"v{line_of(version)}"
    open_n = sum(1 for i in issues if i.get("state", "open") == "open")
    total = len(issues)
    query = f"https://github.com/{repo}/issues?q=label%3A{GATE_LABEL}+milestone%3A%22{milestone}%22"
    badges = [badge("release", "beta", "d29922") if status == "beta" else badge("release", "stable", "2da44e")]
    if total:
        badges.append(f'<a href="{query}">{badge("tests closed", f"{total - open_n} of {total}", "0969da")}</a>')
    if status == "beta":
        alert = ["> [!WARNING]",
                 f"> **Beta.** {open_n} of {total} release test {'issue is' if open_n == 1 else 'issues are'} open. "
                 "Test on a bench before you use this release in a classroom. "
                 "The release becomes Stable automatically when all are closed."]
    elif total:
        alert = ["> [!NOTE]",
                 f"> **Stable.** All {total} release test {'issue is' if total == 1 else 'issues are'} closed. "
                 "If a test issue is added later, the release becomes Beta again."]
    else:
        alert = ["> [!NOTE]", "> **Stable.** No release test issues are linked to this release."]
    lines = [START, " ".join(badges), "", *alert, ""]
    if issues:
        lines += ["| No. | Issue | Assigned to | Status |", "|:--|:--|:--|:--|"]
        for i in sorted(issues, key=lambda i: (i.get("state", "open") != "open", i["number"])):
            who = ", ".join(f"@{a}" for a in i.get("assignees", [])) or "nobody"
            inherited = f" <sub>from {i['from']}</sub>" if i.get("from") else ""
            lines.append(f"| [#{i['number']}](https://github.com/{repo}/issues/{i['number']}) "
                         f"| {issue_title(i['title'])}{inherited} | {who} | {state_badge(i)} |")
        lines += ["", f"<sub>Updated automatically within a minute of any change to a test issue. Issues marked "
                      f"<i>from</i> belong to a line this release is built on. "
                      f'<a href="{query}">Test issues for {milestone}</a></sub>', ""]
    lines.append(END)
    return "\n".join(lines)


def apply_status(body: str, block: str) -> str:
    """Replace the status block, or put it at the top. Idempotent."""
    if START in body and END in body:
        head, rest = body.split(START, 1)
        return head + block + rest.split(END, 1)[1]
    return block + "\n\n" + body.lstrip()


def newest(versions: list[str]) -> str | None:
    valid = [v for v in versions if _SEMVER.match(v)]
    return max(valid, key=_key, default=None)


# ── GitHub access (gh CLI; GH_TOKEN and GITHUB_REPOSITORY from the workflow) ─

def gh(*args: str, input: str | None = None) -> str:
    return subprocess.run(["gh", *args], input=input, capture_output=True, text=True, check=True).stdout


def gh_json(*args: str):
    pages = json.loads(gh("api", "--paginate", "--slurp", *args))
    return [item for page in pages for item in (page if isinstance(page, list) else [page])]


def releases(repo: str) -> list[dict]:
    return [r for r in gh_json(f"repos/{repo}/releases") if parse_tag(r["tag_name"]) and not r["draft"]]


_MILESTONE = re.compile(r"^(?:(?P<owner>[a-z0-9-]+)/)?v(?P<line>\d+\.\d+)(?:\.(?P<patch>\d+))?$")


def _rev(ref: str) -> str:
    return ref if re.fullmatch(r"[0-9a-f]{7,40}", ref) else f"refs/tags/{ref}"


def is_ancestor(older: str, newer: str, root: Path = ROOT) -> bool:
    """Is tag `older` an ancestor of `newer` (a tag or a commit SHA), or the same commit?"""
    try:
        subprocess.run(["git", "merge-base", "--is-ancestor", _rev(older), _rev(newer)],
                       cwd=root, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False


def gates(tag: str, milestone: str, ancestor=is_ancestor) -> bool:
    """Does `milestone` gate release `tag`?

    - exact <owner>/vX.Y.Z: that release only;
    - line <owner>/vX.Y: every release built on top of <owner>/vX.Y.0 (same line, a later line of the
      same owner, or another owner's line branched from it); before vX.Y.0 exists, the same line only;
    - legacy vX.Y (no owner): releases of line X.Y.
    """
    m, (owner, version) = _MILESTONE.match(milestone), parse_tag(tag)
    if not m:
        return False
    if m["patch"] is not None:
        return milestone == tag or (not m["owner"] and f"v{version}" == milestone)
    if not m["owner"]:
        return line_of(version) == m["line"]
    if m["owner"] == owner and m["line"] == line_of(version):
        return True
    return ancestor(f"{m['owner']}/v{m['line']}.0", tag)


def test_issues(repo: str, tag: str, milestones: list[dict], cache: dict | None = None,
                ancestor=is_ancestor) -> list[dict]:
    """Every `testing` issue (open and closed) in a milestone that gates release `tag`."""
    cache = {} if cache is None else cache
    owner, version = parse_tag(tag)
    own_line = f"{owner}/v{line_of(version)}" if owner else f"v{line_of(version)}"
    found = {}
    for m in milestones:
        if not gates(tag, m["title"], ancestor):
            continue
        if m["number"] not in cache:
            cache[m["number"]] = [i for i in gh_json(
                f"repos/{repo}/issues?milestone={m['number']}&state=all&labels={GATE_LABEL}") if "pull_request" not in i]
        for i in cache[m["number"]]:
            found[i["number"]] = {"number": i["number"], "title": i["title"], "state": i["state"],
                                  "state_reason": i.get("state_reason"), "milestone": m["number"],
                                  "from": "" if m["title"] in (own_line, tag) else m["title"],
                                  "assignees": [a["login"] for a in i.get("assignees", [])]}
    return [found[n] for n in sorted(found)]


def current_latest(repo: str) -> str | None:
    try:
        return json.loads(gh("api", f"repos/{repo}/releases/latest"))["tag_name"]
    except subprocess.CalledProcessError:
        return None


def sync(repo: str, only_tag: str | None = None, ancestor=None) -> list[dict]:
    rels = releases(repo)
    milestones = gh_json(f"repos/{repo}/milestones?state=all")
    cache: dict = {}
    issues = {r["tag_name"]: test_issues(repo, r["tag_name"], milestones, cache, ancestor or is_ancestor)
              for r in rels}
    statuses = {tag: status_of(found) for tag, found in issues.items()}
    stable = [t for t, s in statuses.items() if s == "stable"]
    latest_version = newest([parse_tag(t)[1] for t in stable])
    latest = max((t for t in stable if parse_tag(t)[1] == latest_version), default=None,
                 key=lambda t: (parse_tag(t)[0] is not None, t))
    shown_latest = current_latest(repo)
    changed = []
    for r in rels:
        tag = r["tag_name"]
        if only_tag and tag != only_tag:
            continue
        status = statuses[tag]
        update = {"name": title_for(tag, status),
                  "body": apply_status(r.get("body") or "", status_block(tag, status, issues[tag], repo)),
                  "prerelease": status == "beta", "make_latest": "true" if tag == latest else "false"}
        stale = (r["name"] != update["name"] or (r.get("body") or "") != update["body"]
                 or r["prerelease"] != update["prerelease"] or (tag == latest and shown_latest != tag))
        if stale:
            gh("api", "-X", "PATCH", f"repos/{repo}/releases/{r['id']}", "--input", "-", input=json.dumps(update))
            changed.append({"tag": tag, "status": status})
        opened = sum(1 for i in issues[tag] if i["state"] == "open")
        print(f"{tag}: {status} ({opened}/{len(issues[tag])} test issues open){' - updated' if stale else ''}",
              file=sys.stderr)
    return changed


def image_aliases(rels: list[dict]) -> dict[str, str]:
    """Moving image tags -> the release image tag each should point at.

    <owner>-<X.Y>      newest release of that line (any status)
    <owner>-latest     the owner's newest Stable release
    <owner>-beta       the owner's newest Beta release
    """
    by_owner: dict[str, list[tuple[str, bool]]] = {}
    for r in rels:
        owner, version = parse_tag(r["tag_name"])
        if owner:
            by_owner.setdefault(owner, []).append((version, r["prerelease"]))
    out = {}
    for owner, items in by_owner.items():
        for line in {line_of(v) for v, _ in items}:
            out[f"{owner}-{line}"] = f"{owner}-{newest([v for v, _ in items if line_of(v) == line])}"
        stable = newest([v for v, beta in items if not beta])
        beta = newest([v for v, b in items if b])
        if stable:
            out[f"{owner}-latest"] = f"{owner}-{stable}"
        if beta:
            out[f"{owner}-beta"] = f"{owner}-{beta}"
    return dict(sorted(out.items()))


def legacy_images(rels: list[dict]) -> dict[str, str]:
    """Owner-prefixed copies of images published before #104 under plain version tags."""
    return {f"{parse_tag(r['tag_name'])[0]}-{parse_tag(r['tag_name'])[1]}": parse_tag(r["tag_name"])[1]
            for r in rels if parse_tag(r["tag_name"])[0]}


def channels(repo: str) -> dict:
    rels = releases(repo)
    return {"aliases": image_aliases(rels), "legacy": legacy_images(rels)}


def initial_page(repo: str, tag: str, sha: str, notes: str, root: Path = ROOT) -> tuple[str, str]:
    """The complete page of a release about to be published: its status section (computed against the
    release commit, since the tag does not exist yet) on top of `notes`. Returns (status, body)."""
    milestones = gh_json(f"repos/{repo}/milestones?state=all")
    issues = test_issues(repo, tag, milestones, ancestor=lambda older, _new: is_ancestor(older, sha, root))
    status = status_of(issues)
    return status, apply_status(notes, status_block(tag, status, issues, repo))


# ── CLI ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("--branch", required=True)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--templates", type=Path)
    n = sub.add_parser("notes")
    n.add_argument("tag")
    n.add_argument("prs", nargs="?")
    n.add_argument("--root", type=Path, default=ROOT)
    n.add_argument("--templates", type=Path)
    s = sub.add_parser("sync")
    s.add_argument("--tag")
    sub.add_parser("channels")
    sub.add_parser("check-changelog")
    i = sub.add_parser("page")
    i.add_argument("tag")
    i.add_argument("notes", type=Path)
    i.add_argument("--sha", required=True)
    i.add_argument("--out", type=Path, required=True)
    i.add_argument("--root", type=Path, default=ROOT)
    a = ap.parse_args(argv)
    repo = os.environ.get("GITHUB_REPOSITORY", "Kush-Kelaiya22/imPress")

    if a.cmd == "plan":
        print(json.dumps(plan(a.branch, a.root, a.templates)))
    elif a.cmd == "notes":
        owner, version = parse_tag(a.tag)
        previous = previous_tag(owner, version, a.root)
        log = a.root / "CHANGELOG.md"
        changes = new_entries(log.read_text() if log.exists() else "", changelog_at(previous, a.root))
        prs = clean_prs(Path(a.prs).read_text()) if a.prs else ""
        template = find_template(version, a.root, a.templates)
        print(render_notes(template.read_text(), owner, version, previous, render_changes(changes, prs)))
    elif a.cmd == "sync":
        print(json.dumps(sync(repo, a.tag)))
    elif a.cmd == "channels":
        print(json.dumps(channels(repo)))
    elif a.cmd == "page":
        status, body = initial_page(repo, a.tag, a.sha, a.notes.read_text(), a.root)
        a.out.write_text(body)
        print(json.dumps({"status": status, "title": title_for(a.tag, status), "prerelease": status == "beta"}))
    elif a.cmd == "check-changelog":
        problems = check_changelog((ROOT / "CHANGELOG.md").read_text())
        for problem in problems:
            print(f"CHANGELOG.md: {problem}", file=sys.stderr)
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
