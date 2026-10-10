#!/usr/bin/env python3
"""Release helper for .github/workflows/release.yml (#96, #100).

Version. VERSION holds the release line, MAJOR.MINOR (its PATCH digit is the
line's base, normally 0). A release's PATCH is the number of first-parent
commits on the default branch since the line's first release, tag
vMAJOR.MINOR.0; without that tag the release *is* vMAJOR.MINOR.0. Every push
that passes CI therefore becomes the next patch release, and the same commit
always gets the same number.

Status. A release is Beta while an open issue labelled `testing` is in the
line milestone vMAJOR.MINOR (or in an exact vMAJOR.MINOR.PATCH milestone), and
Stable otherwise. The release page starts with a status section: badges, a
short alert and a table of the test issues with their state, all redrawn by
the workflow on every issue change.

    scripts/release.py plan                 # JSON for the workflow: version, tag, previous tag, notes
    scripts/release.py notes 2.1.4 [changes.md]   # the release text for a version (stdout)
    scripts/release.py sync [--tag v2.1.4]  # set Beta/Stable on the releases (gh CLI, GH_TOKEN)
    scripts/release.py channels             # JSON: newest stable and newest beta version
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
GATE_LABEL = os.environ.get("RELEASE_GATE_LABEL", "testing")
START, END = "<!-- release-status:start -->", "<!-- release-status:end -->"
SHIELDS = "https://img.shields.io"
BADGE = {
    "beta": f"{SHIELDS}/badge/release-beta-d29922?style=for-the-badge",
    "stable": f"{SHIELDS}/badge/release-stable-2da44e?style=for-the-badge",
}
_SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
_TAG = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def _key(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version.split("."))


# ── Version ─────────────────────────────────────────────────────────────────

def read_version(root: Path = ROOT) -> str:
    version = (root / "VERSION").read_text().strip()
    if not _SEMVER.match(version):
        raise ValueError(f"VERSION must be MAJOR.MINOR.PATCH, got {version!r}")
    return version


def line_of(version: str) -> str:
    return ".".join(version.split(".")[:2])


def tag_for(version: str) -> str:
    return f"v{version}"


def git(*args: str, root: Path = ROOT) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def tags(root: Path = ROOT) -> list[str]:
    """Release versions that exist as tags, oldest first."""
    found = [t[1:] for t in git("tag", "--list", "v*", root=root).split() if _TAG.match(t)]
    return sorted(found, key=_key)


def release_version(root: Path = ROOT, rev: str = "HEAD") -> str:
    """MAJOR.MINOR from VERSION; PATCH = first-parent commits since vMAJOR.MINOR.0."""
    line = line_of(read_version(root))
    anchor = f"v{line}.0"
    if anchor not in {tag_for(v) for v in tags(root)}:
        return f"{line}.0"
    count = git("rev-list", "--count", "--first-parent", f"{anchor}..{rev}", root=root)
    return f"{line}.{int(count)}"


def previous_tag(version: str, root: Path = ROOT) -> str | None:
    older = [v for v in tags(root) if _key(v) < _key(version)]
    return tag_for(older[-1]) if older else None


# ── Release text ────────────────────────────────────────────────────────────

def notes_path(version: str, root: Path = ROOT) -> Path:
    """One release-notes template per line: docs/releases/vMAJOR.MINOR.md."""
    return root / "docs" / "releases" / f"v{line_of(version)}.md"


def render_notes(template: str, version: str, previous: str | None, changes: str = "") -> str:
    text = (template.replace("{{version}}", version).replace("{{tag}}", tag_for(version))
            .replace("{{line}}", line_of(version)).replace("{{previous}}", previous or "the previous release"))
    if "{{changes}}" in text:
        text = text.replace("{{changes}}", changes.strip() or "No pull requests were merged since the previous release.")
    leftover = re.findall(r"\{\{\w+\}\}", text)
    if leftover:
        raise ValueError(f"unknown placeholders in the release notes: {sorted(set(leftover))}")
    return text


def clean_changes(generated: str) -> str:
    """GitHub's generated notes, without their own heading."""
    return re.sub(r"^## What's Changed\s*\n", "", generated.strip()).strip()


# ── Status ──────────────────────────────────────────────────────────────────

def status_of(issues: list[dict]) -> str:
    return "beta" if any(i.get("state", "open") == "open" for i in issues) else "stable"


def title_for(version: str, status: str) -> str:
    return f"imPress {version}" + (" (Beta)" if status == "beta" else "")


def test_area(title: str) -> str:
    """'test(hardware): bench bring-up: …' → 'Bench bring-up: …'."""
    text = re.sub(r"^\w+(\([^)]*\))?:\s*", "", title).strip()
    return text[:1].upper() + text[1:]


def _badge_text(text: str) -> str:
    """Escape text for a shields.io static badge path segment."""
    return text.replace("-", "--").replace("_", "__").replace(" ", "%20")


def state_badge(issue: dict) -> str:
    """A static badge for the issue's state, drawn by the workflow (never fails to load)."""
    if issue.get("state", "open") == "open":
        text, color = "open", "2da44e"
    elif issue.get("state_reason") == "not_planned":
        text, color = "closed: not planned", "6e7781"
    else:
        text, color = "closed: completed", "8250df"
    return (f'<img alt="{text}" src="{SHIELDS}/badge/{_badge_text(text)}-{color}?style=flat-square">')


def status_block(version: str, status: str, issues: list[dict], repo: str) -> str:
    """Badges, a short alert and the test-issue table, between the markers."""
    open_n = sum(1 for i in issues if i.get("state", "open") == "open")
    total = len(issues)
    query = f"https://github.com/{repo}/issues?q=label%3A{GATE_LABEL}+milestone%3Av{line_of(version)}"
    progress = _badge_text(f"{total - open_n} of {total}")
    badges = [f'<img alt="Release status: {status.title()}" src="{BADGE[status]}">']
    if total:
        badges.append(f'<a href="{query}"><img alt="Test issues closed: {total - open_n} of {total}" '
                      f'src="{SHIELDS}/badge/tests%20closed-{progress}-0969da?style=for-the-badge"></a>')
    if status == "beta":
        alert = ["> [!WARNING]",
                 f"> **Beta.** The software tests pass. {open_n} of {total} release test "
                 f"{'issue is' if open_n == 1 else 'issues are'} still open. Do a bench test before you use "
                 "this release in a classroom. This release becomes Stable automatically when all of them are closed."]
    else:
        alert = ["> [!TIP]",
                 f"> **Stable.** All {total} release test {'issue is' if total == 1 else 'issues are'} closed. "
                 "If a new test issue is added, this release changes back to Beta automatically." if total else
                 "> **Stable.** No release test issues are linked to this release."]
    lines = [START, "", "<p>", *badges, "</p>", "", *alert, ""]
    if issues:
        lines += ["### Release tests", "",
                  "| Issue | Test area | Owner | Status |",
                  "|:--|:--|:--|:--|"]
        for i in sorted(issues, key=lambda i: (i.get("state", "open") != "open", i["number"])):
            owners = ", ".join(f"@{a}" for a in i.get("assignees", [])) or "unassigned"
            lines.append(f"| [#{i['number']}](https://github.com/{repo}/issues/{i['number']}) "
                         f"| {test_area(i['title'])} | {owners} | {state_badge(i)} |")
        lines += ["",
                  "<sub>The status of each issue, the badges and the release status are updated automatically "
                  "within about a minute of any change to a test issue, and checked again every day. "
                  f"<a href=\"{query}\">All test issues for v{line_of(version)}</a></sub>", ""]
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
    return [r for r in gh_json(f"repos/{repo}/releases") if _TAG.match(r["tag_name"]) and not r["draft"]]


def test_issues(repo: str, version: str, milestones: list[dict] | None = None) -> list[dict]:
    """Every `testing` issue (open and closed) in milestone vMAJOR.MINOR or vVERSION."""
    milestones = milestones if milestones is not None else gh_json(f"repos/{repo}/milestones?state=all")
    wanted = {f"v{line_of(version)}", tag_for(version)}
    found = {}
    for m in milestones:
        if m["title"] in wanted:
            for i in gh_json(f"repos/{repo}/issues?milestone={m['number']}&state=all&labels={GATE_LABEL}"):
                if "pull_request" not in i:
                    found[i["number"]] = {"number": i["number"], "title": i["title"], "state": i["state"],
                                          "state_reason": i.get("state_reason"), "milestone": m["number"],
                                          "assignees": [a["login"] for a in i.get("assignees", [])]}
    return [found[n] for n in sorted(found)]


def current_latest(repo: str) -> str | None:
    try:
        return json.loads(gh("api", f"repos/{repo}/releases/latest"))["tag_name"]
    except subprocess.CalledProcessError:          # 404: no stable release yet
        return None


def sync(repo: str, only_tag: str | None = None) -> list[dict]:
    """Bring each release's title, text, pre-release flag and "latest" in line with its test issues."""
    rels = releases(repo)
    milestones = gh_json(f"repos/{repo}/milestones?state=all")
    issues = {r["tag_name"]: test_issues(repo, r["tag_name"][1:], milestones) for r in rels}
    statuses = {tag: status_of(found) for tag, found in issues.items()}
    latest = newest([tag[1:] for tag, status in statuses.items() if status == "stable"])
    shown_latest = current_latest(repo)
    changed = []
    for r in rels:
        tag, version = r["tag_name"], r["tag_name"][1:]
        if only_tag and tag != only_tag:
            continue
        status = statuses[tag]
        update = {"name": title_for(version, status),
                  "body": apply_status(r.get("body") or "", status_block(version, status, issues[tag], repo)),
                  "prerelease": status == "beta",
                  "make_latest": "true" if version == latest else "false"}
        stale = (r["name"] != update["name"] or (r.get("body") or "") != update["body"]
                 or r["prerelease"] != update["prerelease"] or (version == latest and shown_latest != tag))
        if stale:
            gh("api", "-X", "PATCH", f"repos/{repo}/releases/{r['id']}", "--input", "-", input=json.dumps(update))
            changed.append({"tag": tag, "status": status})
        opened = sum(1 for i in issues[tag] if i["state"] == "open")
        print(f"{tag}: {status} ({opened}/{len(issues[tag])} test issues open){' - updated' if stale else ''}",
              file=sys.stderr)
    return changed


def channels(repo: str) -> dict:
    statuses = {r["tag_name"][1:]: ("beta" if r["prerelease"] else "stable") for r in releases(repo)}
    return {"latest": newest([v for v, s in statuses.items() if s == "stable"]),
            "beta": newest([v for v, s in statuses.items() if s == "beta"])}


# ── CLI ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    n = sub.add_parser("notes")
    n.add_argument("version")
    n.add_argument("changes", nargs="?")
    s = sub.add_parser("sync")
    s.add_argument("--tag")
    sub.add_parser("channels")
    a = ap.parse_args(argv)
    repo = os.environ.get("GITHUB_REPOSITORY", "Kush-Kelaiya22/imPress")

    if a.cmd == "plan":
        version = release_version()
        notes = notes_path(version)
        print(json.dumps({"version": version, "tag": tag_for(version), "line": line_of(version),
                          "previous": previous_tag(version) or "", "notes": str(notes.relative_to(ROOT)),
                          "notes_present": notes.exists()}))
    elif a.cmd == "notes":
        changes = Path(a.changes).read_text() if a.changes else ""
        print(render_notes(notes_path(a.version).read_text(), a.version, previous_tag(a.version), changes))
    elif a.cmd == "sync":
        print(json.dumps(sync(repo, a.tag)))
    elif a.cmd == "channels":
        print(json.dumps(channels(repo)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
