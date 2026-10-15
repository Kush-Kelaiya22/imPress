"""The launch flags file (v2.2): `backend/impress.flags.json`.

Root decides how imPress starts. The flags used to be typed on the start command (`--test-mode`, `--feature NAME=VALUE`);
they live in this file now, each one with its own explanation next to its value, so a start is the same every time and
nothing has to be remembered. Command-line flags still work and win over the file for that start.

This file holds the **feature flags**: launch choices (test mode, over-the-air updates, the traffic monitor, which web-app
features exist) that a person may edit by hand. The security and integrity switches are **policy**, not feature flags: they live
in the sealed policy store (gpcstore.py) and change only through the console or the System page, so that every change is
recorded with who and when.

Layers, lowest first (a later one overrides an earlier one):

    built-in defaults  <  policy store  <  root-signed global_policy_control.json  <  this file  <  IMPRESS_GPC  <  command
    line  <  `flags set` (this session only)

The file is plain JSON. Every flag is an object; **only `value` is read**, the other keys are there for the person
editing it (what the flag does, what the standard and hardened profiles default to, what is allowed):

    "test_mode.forced": { "value": false, "about": "...", "standard": false, "hardened": false, "type": "bool" }

A flag whose value is the one the file shipped with is **not an override**: the profile's own default applies, so one file
serves both profiles (the hardened profile is never loosened by a file that was never edited). Edit a value and it is
applied; in the hardened profile an edit may only make a flag safer (the same rule as the command line).

`python -m app.flagsfile write [--force]` writes the file (it is also written on first start when missing),
`check` validates it, `docs` prints the reference for docs/reference/flags.md.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

FILE_NAME = "impress.flags.json"
BACKEND_DIR = Path(__file__).resolve().parents[1]

# Launch choices that are not policy flags, with what to say about them.
PROFILE_ABOUT = ("Which set of defaults the policy starts from: 'standard' (a classroom or lab: protections that need no "
                 "set-up) or 'hardened' (a production server: everything on, and it REFUSES to start when the rest of the "
                 "configuration is below its floor: debug off, real secrets, HTTPS, an external audit sink, ...). "
                 "The command line's --profile wins.")

README = [
    "imPress launch flags. Root edits this file; nothing in the web app or the API can change it.",
    "Change a flag's \"value\" and restart imPress. Every flag explains itself in \"about\"; only \"value\" is read.",
    "A value left as shipped is not an override, so the profile's own default applies (hardened stays hardened).",
    "In the hardened profile an edit may only make a flag safer; to loosen one, sign a policy file with scripts/gpc.py.",
    "Command-line flags (--test-mode, --feature NAME=VALUE, ...) still work and win over this file for that start.",
    "A mistake here is reported when imPress starts, with the flag's name; it never half-applies.",
    "Reference: docs/guides/launch-flags.md and docs/reference/flags.md.",
]


class FlagsFileError(ValueError):
    """The file could not be applied as written."""


def path() -> Path:
    return Path(os.environ.get("IMPRESS_FLAGS_FILE") or BACKEND_DIR / FILE_NAME)


def template() -> dict:
    """The complete file, from the flag catalogue (so it cannot drift from the code)."""
    from . import gpc
    from .services.features import FEATURES
    flags = {}
    for f in (x for x in gpc.FLAGS.values() if x.scope == "feature"):
        entry = {"value": f.standard, "about": f.doc, "type": f.kind, "standard": f.standard, "hardened": f.hardened}
        if f.choices:
            entry["choices"] = list(f.choices)
        if f.kind == "int":
            entry["note"] = "a whole number, 0 or more"
        flags[f.name] = entry
        if f.name in _HOW:
            entry["how"] = _HOW[f.name]
    features = {n: {"value": True, "about": f"{x.title}. {x.doc}", "group": x.group} for n, x in FEATURES.items()}
    return {"_readme": README,
            "profile": {"value": "standard", "choices": list(gpc.PROFILES), "about": PROFILE_ABOUT},
            "flags": flags,
            "features": {"_about": "Web-app features. `false` switches one off for everybody and administrators cannot "
                                   "switch it back on (the same as the flag features.disabled). They are listed, with who "
                                   "changed them, under System > Features.", **features}}


# Extra guidance for the flags people reach for first.
_HOW = {
    "test_mode.forced": "Lab use. Same as the command line's --test-mode. Not allowed in the hardened profile. "
                        "Cannot be true while test_mode.allowed is false.",
    "test_mode.allowed": "false = the test-data menu and routes do not exist (the command line's --no-test-mode).",
    "ota.enabled": "false = no firmware uploads, deployments or pushes, and devices are offered nothing (--no-ota).",
    "iips.enabled": "false = start although the program's files changed; every page shows a warning (--bypass-iips). "
                    "Not allowed to be loosened in the hardened profile.",
    "iips.auto_accept_updates": "true: when the program was updated (a different release or git commit), its new files "
                                "become the reference by themselves. Files edited by hand under the SAME release still "
                                "lock imPress until root runs with --rehash.",
    "features.disabled": "Prefer the \"features\" section below: it lists every feature by name.",
}


def write(force: bool = False, target: Path | None = None) -> Path | None:
    """Write the template. Without `force`, an existing file is never touched. Returns the path written."""
    target = target or path()
    if target.exists() and not force:
        return None
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(template(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    return target


def _value(entry, where: str):
    if isinstance(entry, dict):
        if "value" not in entry:
            raise FlagsFileError(f"{where}: needs a \"value\"")
        return entry["value"]
    return entry                                 # a bare value is accepted too: "ota.enabled": false


def _text(value) -> str:
    return str(value).lower() if isinstance(value, bool) else str(value)


def load(file: Path | None = None) -> tuple[str | None, list[str]]:
    """(profile or None, overrides as 'name=value' strings). Raises FlagsFileError naming the flag at fault.
    A missing file is not an error: there is nothing to apply."""
    from . import gpc
    from .services.features import FEATURES
    file = file or path()
    if not file.exists():
        return None, []
    try:
        doc = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise FlagsFileError(f"{file.name} is not valid JSON ({exc})") from None
    if not isinstance(doc, dict):
        raise FlagsFileError(f"{file.name} must be a JSON object")
    profile = None
    if "profile" in doc:
        profile = _value(doc["profile"], "profile")
        if profile not in gpc.PROFILES:
            raise FlagsFileError(f"profile: {profile!r} is not valid, expected {' or '.join(gpc.PROFILES)}")
        if profile == "standard":
            profile = None                       # shipped value: the environment or the command line may choose
    overrides: list[str] = []
    for name, entry in (doc.get("flags") or {}).items():
        if name not in gpc.FLAGS:
            raise FlagsFileError(f"flags: unknown flag {name!r} (see docs/reference/flags.md)")
        flag = gpc.FLAGS[name]
        if flag.scope != "feature":
            raise FlagsFileError(f"flags: {name} is a policy flag (FLAG_IS_POLICY): it is sealed and recorded, so it is changed "
                                 "with `policy set` in the console (root's password), not in this file")
        try:
            value = gpc.coerce(flag, _value(entry, f"flags.{name}"))
        except gpc.PolicyError as exc:
            raise FlagsFileError(f"flags: {exc}") from None
        if value != flag.standard:
            overrides.append(f"{name}={_text(value)}")
    off = []
    for name, entry in (doc.get("features") or {}).items():
        if name.startswith("_"):
            continue
        if name not in FEATURES:
            raise FlagsFileError(f"features: unknown feature {name!r} (see System > Features)")
        on = _value(entry, f"features.{name}")
        if not isinstance(on, bool):
            raise FlagsFileError(f"features.{name}: {on!r} is not valid, expected true or false")
        if not on:
            off.append(name)
    if off:
        listed = [x for x in dict(o.split("=", 1) for o in overrides).get("features.disabled", "").split(",") if x]
        overrides = [o for o in overrides if not o.startswith("features.disabled=")]
        overrides.append("features.disabled=" + ",".join(sorted({*listed, *off})))
    return profile, overrides


def save(changes: dict, target: Path | None = None) -> Path:
    """Write feature-flag values (and, under the key "profile", the profile) into the file, keeping every explanation.
    This is `--save` and `flags save`: the next start uses them. Raises FlagsFileError for a policy or unknown flag."""
    from . import gpc
    target = target or path()
    write(target=target)                                    # creates it with the explanations when missing
    doc = json.loads(target.read_text(encoding="utf-8"))
    for name, raw in changes.items():
        if name == "profile":
            if raw not in gpc.PROFILES:
                raise FlagsFileError(f"profile: {raw!r} is not valid")
            doc["profile"]["value"] = raw
            continue
        flag = gpc.FLAGS.get(name)
        if flag is None:
            raise FlagsFileError(f"unknown flag {name!r}")
        if flag.scope != "feature":
            raise FlagsFileError(f"{name} is a policy flag (FLAG_IS_POLICY): it cannot be saved here; use `policy set` in the console")
        try:
            doc["flags"][name]["value"] = gpc.coerce(flag, raw)
        except gpc.PolicyError as exc:
            raise FlagsFileError(str(exc)) from None
    tmp = target.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, target)
    return target


def reference() -> str:
    """Markdown for docs/reference/flags.md, from the same catalogue."""
    t = template()
    out = ["# Launch flags reference", "",
           "Generated from the flag catalogue by `python -m app.flagsfile docs`; do not edit by hand. "
           "How to use the file: [launch flags](../guides/launch-flags.md).", "",
           "## Feature flags (`impress.flags.json`, editable by hand)", "",
           "| Flag | Type | Standard | Hardened | What it does |", "|---|---|---|---|---|"]
    for name, e in t["flags"].items():
        std, hard = json.dumps(e["standard"]), json.dumps(e["hardened"])
        choices = f" ({' / '.join(e['choices'])})" if "choices" in e else ""
        extra = f" **{e['how']}**" if "how" in e else ""
        out.append(f"| `{name}` | {e['type']}{choices} | `{std}` | `{hard}` | {e['about']}{extra} |")
    from . import gpc
    out += ["", "## Policy flags (the sealed store: `policy set` in the console, or the System page)", "",
            "Sealed, recorded with who and when; administrators and faculty can never change them. *Changed by* says who may.", "",
            "| Flag | Type | Standard | Hardened | Changed by | What it does |", "|---|---|---|---|---|---|"]
    for f in (x for x in gpc.FLAGS.values() if x.scope == "policy"):
        choices = f" ({' / '.join(f.choices)})" if f.choices else ""
        out.append(f"| `{f.name}` | {f.kind}{choices} | `{json.dumps(f.standard)}` | `{json.dumps(f.hardened)}` | "
                   f"{f.editable_by} | {f.doc} |")
    out += ["", "## Web-app features", "",
            "Set `false` under `\"features\"` to switch one off for everybody (root outranks administrators).", "",
            "| Feature | Group | What it is |", "|---|---|---|"]
    for name, e in t["features"].items():
        if not name.startswith("_"):
            out.append(f"| `{name}` | {e['group']} | {e['about']} |")
    return "\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else ""
    if cmd == "write":
        done = write(force="--force" in argv)
        print(f"wrote {done}" if done else f"{path()} exists (use --force to replace it with the shipped template)")
        return 0
    if cmd == "check":
        try:
            profile, overrides = load()
        except FlagsFileError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"{path()}: ok (profile {profile or 'unchanged'}; {len(overrides)} override(s))")
        for o in overrides:
            print("  " + o)
        return 0
    if cmd == "docs":
        sys.stdout.write(reference())
        return 0
    print("usage: python -m app.flagsfile write [--force] | check | docs", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
