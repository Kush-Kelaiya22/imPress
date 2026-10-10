#!/usr/bin/env python3
"""Release helper for .github/workflows/release.yml (#96).

A release is identified by the root VERSION file: tag v<VERSION>, notes in
docs/releases/v<VERSION>.md. Its status follows the issues linked to it:

    Beta    while any open issue labelled `testing` is in milestone v<VERSION>
    Stable  otherwise

Beta is a GitHub pre-release; the release page starts with a status badge and
lists the open test issues. `sync` re-evaluates every release (or one tag) and
updates the title, the status block, the pre-release flag and "latest".

    scripts/release.py plan                  # JSON: version, tag, notes path, notes present
    scripts/release.py render v2.1.0 beta    # the release body as it would be published (stdin: issues JSON)
    scripts/release.py sync [--tag v2.1.0]   # needs GH_TOKEN and GITHUB_REPOSITORY; uses the gh CLI
    scripts/release.py channels              # JSON: newest stable and newest beta version (image tags)
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
BADGE = {
    "beta": "https://img.shields.io/badge/status-beta-d29922?style=flat-square",
    "stable": "https://img.shields.io/badge/status-stable-2da44e?style=flat-square",
}
_VERSION = re.compile(r"^\d+\.\d+\.\d+$")


# ── Pure rules (unit-tested in tests/test_release.py) ───────────────────────

def read_version(root: Path = ROOT) -> str:
    version = (root / "VERSION").read_text().strip()
    if not _VERSION.match(version):
        raise ValueError(f"VERSION must be MAJOR.MINOR.PATCH, got {version!r}")
    return version


def tag_for(version: str) -> str:
    return f"v{version}"


def notes_path(version: str, root: Path = ROOT) -> Path:
    return root / "docs" / "releases" / f"{tag_for(version)}.md"


def status_of(open_test_issues: list[dict]) -> str:
    return "beta" if open_test_issues else "stable"


def title_for(version: str, status: str) -> str:
    return f"imPress {version}" + (" (Beta)" if status == "beta" else "")


def status_block(version: str, status: str, issues: list[dict], repo: str) -> str:
    """The badge and one short paragraph, between the markers."""
    milestone = f"https://github.com/{repo}/milestone/{issues[0]['milestone']}" if issues and issues[0].get("milestone") else \
        f"https://github.com/{repo}/issues?q=milestone%3A{tag_for(version)}+label%3A{GATE_LABEL}"
    badge = f'<img alt="Status: {status.title()}" src="{BADGE[status]}">'
    if status == "beta":
        lines = [
            badge, "",
            f"**Status: Beta.** The software tests pass. The hardware tests for this release are not complete: "
            f"{len(issues)} test {'issue is' if len(issues) == 1 else 'issues are'} open. "
            f"Do a bench test before you use this release in a classroom.",
            "",
            *[f"- [#{i['number']}](https://github.com/{repo}/issues/{i['number']}) {i['title']}" for i in issues],
            "",
            f"This status changes to Stable automatically when all [test issues for {tag_for(version)}]({milestone}) are closed.",
        ]
    else:
        lines = [
            badge, "",
            f"**Status: Stable.** All [test issues for {tag_for(version)}]({milestone}) are closed. "
            f"If a new test issue is added to the milestone, the status changes back to Beta.",
        ]
    return "\n".join([START, *lines, END])


def apply_status(body: str, block: str) -> str:
    """Replace the status block, or put it at the top. Idempotent."""
    if START in body and END in body:
        head, rest = body.split(START, 1)
        return head + block + rest.split(END, 1)[1]
    return block + "\n\n" + body.lstrip()


def newest(versions: list[str]) -> str | None:
    valid = [v for v in versions if _VERSION.match(v)]
    return max(valid, key=lambda v: tuple(int(x) for x in v.split(".")), default=None)


# ── GitHub access (gh CLI; GH_TOKEN and GITHUB_REPOSITORY from the workflow) ─

def gh(*args: str, input: str | None = None) -> str:
    return subprocess.run(["gh", *args], input=input, capture_output=True, text=True, check=True).stdout


def gh_json(*args: str):
    out = gh("api", "--paginate", "--slurp", *args)
    pages = json.loads(out)
    return [item for page in pages for item in (page if isinstance(page, list) else [page])]


def releases(repo: str) -> list[dict]:
    return [r for r in gh_json(f"repos/{repo}/releases") if r["tag_name"].startswith("v") and not r["draft"]]


def open_test_issues(repo: str, tag: str) -> list[dict]:
    milestones = [m for m in gh_json(f"repos/{repo}/milestones?state=all") if m["title"] == tag]
    if not milestones:
        return []
    number = milestones[0]["number"]
    issues = gh_json(f"repos/{repo}/issues?milestone={number}&state=open&labels={GATE_LABEL}")
    return sorted(({"number": i["number"], "title": i["title"], "milestone": number}
                   for i in issues if "pull_request" not in i), key=lambda i: i["number"])


def current_latest(repo: str) -> str | None:
    """The tag GitHub shows as "Latest" (never a pre-release), or None."""
    try:
        return json.loads(gh("api", f"repos/{repo}/releases/latest"))["tag_name"]
    except subprocess.CalledProcessError:          # 404: no stable release yet
        return None


def sync(repo: str, only_tag: str | None = None) -> list[dict]:
    """Bring each release's status in line with its open test issues."""
    rels = releases(repo)
    issues = {r["tag_name"]: open_test_issues(repo, r["tag_name"]) for r in rels}
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
        print(f"{tag}: {status} ({len(issues[tag])} open test issue(s)){' - updated' if stale else ''}", file=sys.stderr)
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
    r = sub.add_parser("render")
    r.add_argument("tag")
    r.add_argument("status", choices=["beta", "stable"])
    s = sub.add_parser("sync")
    s.add_argument("--tag")
    sub.add_parser("channels")
    a = ap.parse_args(argv)
    repo = os.environ.get("GITHUB_REPOSITORY", "Kush-Kelaiya22/imPress")

    if a.cmd == "plan":
        version = read_version()
        notes = notes_path(version)
        print(json.dumps({"version": version, "tag": tag_for(version),
                          "notes": str(notes.relative_to(ROOT)), "notes_present": notes.exists()}))
    elif a.cmd == "render":
        version = a.tag.lstrip("v")
        issues = json.loads(sys.stdin.read() or "[]") if not sys.stdin.isatty() else []
        print(apply_status(notes_path(version).read_text(), status_block(version, a.status, issues, repo)))
    elif a.cmd == "sync":
        print(json.dumps(sync(repo, a.tag)))
    elif a.cmd == "channels":
        print(json.dumps(channels(repo)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
