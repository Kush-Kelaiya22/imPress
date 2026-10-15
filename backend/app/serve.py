"""Start the server with launch flags (v2.2):  python -m app.serve [options]

Launch flags are root's: they are decided where the server is started, and nothing in the web app can undo them.

  --test-mode        test mode is forced on and nobody can turn it off (a lab setting: the default super admin
                     then signs in with a fixed password; the hardened profile refuses it)
  --no-test-mode     the test-data menu and routes are gone and can't be switched on
  --no-ota           over-the-air updates are off: no uploads, deployments or pushes, and devices are offered nothing
  --rehash           accept the program's files as they are now as the reference for the integrity check (IIPS)
  --bypass-iips      start although the integrity check failed; every page shows a warning (not in the hardened profile)
  --feature N=V      any policy flag (see `python -m app.console`, `policy show`, or docs/design/gpc.md)
  --profile P        standard (default) or hardened
  --host H --port N  where to listen (IMPRESS_HOST / IMPRESS_PORT, default 127.0.0.1:8000)

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
    ap.add_argument("--host", default=os.environ.get("IMPRESS_HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("IMPRESS_PORT", "8000")))
    ap.add_argument("--test-mode", action="store_true", help="force test mode on; nobody can turn it off")
    ap.add_argument("--no-test-mode", action="store_true", help="remove test mode; nobody can turn it on")
    ap.add_argument("--no-ota", action="store_true", help="switch over-the-air updates off")
    ap.add_argument("--rehash", action="store_true", help="make the current files the integrity reference")
    ap.add_argument("--bypass-iips", action="store_true", help="start without the integrity check (a warning shows on every page)")
    ap.add_argument("--plain", action="store_true", help="no root screen: print the log only")
    ap.add_argument("--feature", action="append", default=[], metavar="NAME=VALUE", help="set any policy flag")
    ap.add_argument("--profile", choices=("standard", "hardened"))
    return ap


def overrides(args: argparse.Namespace) -> list[str]:
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


def main(argv: list[str] | None = None) -> int:
    from .banner import utf8_output
    utf8_output()
    argv = list(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    if not args.plain and not os.environ.get("IMPRESS_PLAIN") and sys.stdin.isatty() and sys.stdout.isatty():
        from . import rootscreen          # a terminal: the root screen (logo, live log, prompt); no terminal: plain log
        return rootscreen.run(argv)
    if args.test_mode and args.no_test_mode:
        print("error: --test-mode and --no-test-mode contradict each other", file=sys.stderr)
        return 2
    if args.rehash and args.bypass_iips:
        print("error: --rehash and --bypass-iips contradict each other", file=sys.stderr)
        return 2
    flags = overrides(args)
    # The environment must be set before the application (and its settings) is imported.
    existing = os.environ.get("IMPRESS_GPC", "")
    if flags:
        os.environ["IMPRESS_GPC"] = ",".join(x for x in [existing, *flags] if x)
    if args.profile:
        os.environ["IMPRESS_PROFILE"] = args.profile
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
    except gpc.PolicyError as exc:
        print(f"error: global policy: {exc}", file=sys.stderr)
        return 2
    if not os.environ.get("IMPRESS_ROOT_SCREEN"):
        banner.show()
    verdict = iips.check(enabled=bool(gpc.get("iips.enabled")), rehash=args.rehash)
    if iips.locked():
        print("  " + iips.violation_message() + "\n", file=sys.stderr)
        return 3
    note = {"baseline_created": "Integrity protection: first start, the program's files were recorded as the reference.",
            "rehashed": "Integrity protection: the current files are now the reference.",
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
