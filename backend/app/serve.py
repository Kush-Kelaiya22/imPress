"""Start the server with launch flags (v2.2):  python -m app.serve [options]

Launch flags are root's: they are decided where the server is started, and nothing in the web app can undo them.
They live in backend/impress.flags.json, each with its own explanation (docs/guides/launch-flags.md); the options below
still work and win over the file for that start.

  --test-mode        test mode is forced on and nobody can turn it off (a lab setting: the default super admin
                     then signs in with a fixed password; the hardened profile refuses it)
  --no-test-mode     the test-data menu and routes are gone and can't be switched on
  --no-ota           over-the-air updates are off: no uploads, deployments or pushes, and devices are offered nothing
  --rehash           accept the program's files as they are now as the reference for the integrity check (IIPS)
  --bypass-iips      start although the integrity check failed; every page shows a warning (not in the hardened profile)
  --feature N=V      any policy flag (see `python -m app.console`, `policy show`, or docs/design/gpc.md)
  --profile P        standard (default) or hardened
  --save             keep the feature flags given here (--test-mode, --no-ota, --feature ..., --profile) in impress.flags.json
                     for every later start; command-line only
  --host H --port N  fixed listener: 0.0.0.0:8000 (other values are refused)

They become inline policy overrides (IMPRESS_GPC); in the hardened profile an override may only tighten.
TLS comes from IMPRESS_SSL_CERTFILE / IMPRESS_SSL_KEYFILE, as with scripts/start.sh.
"""

from __future__ import annotations

import argparse
import os
import sys


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="python -m app.serve", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("--host", choices=("0.0.0.0",), default="0.0.0.0")
    ap.add_argument("--port", type=int, choices=(8000,), default=8000)
    ap.add_argument("--test-mode", action="store_true", help="force test mode on; nobody can turn it off")
    ap.add_argument("--no-test-mode", action="store_true", help="remove test mode; nobody can turn it on")
    ap.add_argument("--no-ota", action="store_true", help="switch over-the-air updates off")
    ap.add_argument("--rehash", action="store_true", help="make the current files the integrity reference")
    ap.add_argument("--bypass-iips", action="store_true", help="start without the integrity check (a warning shows on every page)")
    ap.add_argument("--plain", action="store_true", help="no root screen: print the log only")
    ap.add_argument("--feature", action="append", default=[], metavar="NAME=VALUE", help="set any policy flag")
    ap.add_argument("--profile", choices=("standard", "hardened"))
    ap.add_argument("--save", action="store_true",
                    help="write the feature flags given on this command line into impress.flags.json, so the next start "
                         "uses them without being told (policy flags cannot be saved here: use `policy set`)")
    return ap


def overrides(args: argparse.Namespace) -> list[str]:
    """The command line's overrides only; the flags file is read in main() (see effective())."""
    out = []
    if args.test_mode:
        out.append("test_mode.forced=true")
    if args.no_test_mode:
        out.append("test_mode.allowed=false")
    if args.no_ota:
        out.append("ota.enabled=false")
    if args.bypass_iips:
        out.append("iips.enabled=false")
    out.extend(args.feature)
    return out


def effective(argv: list[str]) -> tuple[str | None, list[str]]:
    """(profile, policy overrides) this start will use, lowest first: the flags file, IMPRESS_GPC, the command line.
    Raises flagsfile.FlagsFileError for a file that cannot be applied."""
    from . import flagsfile
    args = build_parser().parse_args(argv)
    profile, from_file = flagsfile.load()
    env = [x for x in os.environ.get("IMPRESS_GPC", "").split(",") if x.strip()]
    return args.profile or profile, [*from_file, *env, *overrides(args)]


def command_line_conflicts(args: argparse.Namespace) -> list[str]:
    out = []
    if args.test_mode and args.no_test_mode:
        out.append("--test-mode + --no-test-mode: test mode cannot be both forced on and removed")
    if args.rehash and args.bypass_iips:
        out.append("--rehash + --bypass-iips: you cannot accept the files as the reference and also skip checking them")
    return out


def conflict_exit(lines: list[str]) -> int:
    """Flags that cannot work together end the program here, before anything else is checked or started."""
    print("error: flags that conflict (FLAG_CONFLICT): imPress will not start.\n  - " + "\n  - ".join(lines)
          + "\nChange one of them (docs/reference/errors.md#startup).", file=sys.stderr)
    return 2


def saveable(args: argparse.Namespace) -> dict:
    """The feature flags on this command line, as {name: value}, for --save."""
    out: dict = {}
    if args.test_mode:
        out["test_mode.forced"] = True
    if args.no_test_mode:
        out["test_mode.allowed"] = False
    if args.no_ota:
        out["ota.enabled"] = False
    if args.profile:
        out["profile"] = args.profile
    for item in args.feature:
        name, _, raw = item.partition("=")
        out[name.strip()] = raw.strip()
    return out


def main(argv: list[str] | None = None) -> int:
    from .banner import utf8_output
    utf8_output()
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    if (found := command_line_conflicts(args)):                      # first of all: nothing else matters if these fail
        return conflict_exit(found)
    from . import rootauth
    if args.rehash:                                                 # accepting the files as the reference is root's alone
        password = rootauth.obtain("Root's password to accept the current files as the reference: ")
        if not rootauth.check(password):
            print("error: re-hashing needs root's password" + (" (ROOT_PASSWORD_WRONG)" if password else " (ROOT_PASSWORD_REQUIRED)"),
                  file=sys.stderr)
            return 2
        os.environ["IMPRESS_ROOT_PASSWORD"] = password               # the server process inherits the proof, not the screen
    if args.save:
        from . import flagsfile
        try:
            where = flagsfile.save(saveable(args))
        except flagsfile.FlagsFileError as exc:
            print(f"error: --save: {exc}", file=sys.stderr)
            return 2
        print(f"  Saved to {where}: the next start uses these without being told.", flush=True)
        argv = [a for a in argv if a != "--save"]                    # saved once, here; the server it starts is not asked again
    from . import flagsfile
    try:
        try:
            flagsfile.write()                                      # first start: the documented file, with every default
        except OSError:
            pass                                                   # a read-only install: there is nothing to edit
        profile, flags = effective(argv)
    except flagsfile.FlagsFileError as exc:
        print(f"error: {flagsfile.path()}: {exc}", file=sys.stderr)
        return 2
    from . import gpc
    try:                                                            # contradictory flags end the program here, before anything else
        gpc.build(profile or os.environ.get("IMPRESS_PROFILE", "standard"), ",".join(flags), None, None)
    except gpc.PolicyConflict as exc:
        return conflict_exit([c.text() for c in exc.conflicts])
    except gpc.PolicyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not args.plain and not os.environ.get("IMPRESS_PLAIN") and sys.stdin.isatty() and sys.stdout.isatty():
        from . import rootscreen          # the screen starts (and restarts) the server and the console itself, and reads
        return rootscreen.run(argv)       # the flags file again each time, so an edit takes effect on 'restart'
    # The environment must be set before the application (and its settings) is imported.
    if flags:
        os.environ["IMPRESS_GPC"] = ",".join(flags)
    if profile:
        os.environ["IMPRESS_PROFILE"] = profile
    try:
        from . import gpc
        gpc.parse_inline(os.environ.get("IMPRESS_GPC", ""))          # a typo is an error here, not a stack trace later
    except Exception as exc:                                         # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        return 2
    from . import banner, gpc
    from .config import settings
    from .services import iips
    try:
        gpc.load(settings)
    except gpc.PolicyConflict as exc:
        return conflict_exit([c.text() for c in exc.conflicts])
    except gpc.PolicyError as exc:
        print(f"error: global policy: {exc}", file=sys.stderr)
        return 2
    if not os.environ.get("IMPRESS_ROOT_SCREEN"):
        banner.show()
    verdict = iips.check(enabled=bool(gpc.get("iips.enabled")), rehash=args.rehash,
                         auto_accept=bool(gpc.get("iips.auto_accept_updates")), binding=gpc.get("iips.device_binding"))
    if iips.locked():
        print("  " + iips.violation_message() + "\n", file=sys.stderr)
        return 3
    note = {"baseline_created": "Integrity protection: first start, the program's files were recorded as the reference.",
            "rehashed": "Integrity protection: the current files are now the reference.",
            "updated": "Integrity protection: imPress was updated (" + str(verdict.get("note", "")) + "): the new files are now the reference.",
            "bypassed": "Integrity protection is DISABLED (--bypass-iips): every page shows a warning."}.get(verdict["status"])
    if note:
        print("  " + note + "\n", flush=True)
    import uvicorn
    kwargs = dict(host=args.host, port=args.port, workers=1, proxy_headers=True,
                  forwarded_allow_ips=os.environ.get("IMPRESS_FORWARDED_ALLOW_IPS", "127.0.0.1"))
    cert, key = os.environ.get("IMPRESS_SSL_CERTFILE"), os.environ.get("IMPRESS_SSL_KEYFILE")
    if cert or key:
        if not (cert and key and os.access(cert, os.R_OK) and os.access(key, os.R_OK)):
            print("error: set both IMPRESS_SSL_CERTFILE and IMPRESS_SSL_KEYFILE to readable files", file=sys.stderr)
            return 2
        kwargs.update(ssl_certfile=cert, ssl_keyfile=key)
    if args.test_mode:
        print("\n  TEST MODE IS FORCED BY ROOT: it cannot be turned off from the web app. Lab use only.\n", flush=True)
    uvicorn.run("app.main:app", **kwargs)
    return 0


if __name__ == "__main__":
    sys.exit(main())
