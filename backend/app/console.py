"""The root console (v2.2): an interactive shell for operating imPress as root, like a terminal.

    cd backend && python -m app.console                     # interactive: a prompt, history, tab completion
    python -m app.console -c "users list" -c "status"       # one command per -c, then exit
    echo "status" | python -m app.console                   # commands from a pipe

It runs on the server's host with the database file's own access: nothing about it is reachable over the network.
Operations run as the system through the database gateway, and every command that changes something is a flagged
entry in the activity log and in the external audit trail, as root's. This is the only place a super admin account
can be created.
"""

from __future__ import annotations

import asyncio
import cmd
import shlex
import sys


PROMPT = "impress# "
INTRO = """imPress root console. You are root: nothing here asks the web app's permission.
Type 'help' for the commands, 'status' for the state of the system, 'exit' to leave."""


def table(rows: list[dict], columns: list[str] | None = None) -> str:
    if not rows:
        return "(none)"
    cols = columns or list(rows[0])
    widths = [max(len(str(c)), *(len(str(r.get(c, ""))) for r in rows)) for c in cols]
    line = "  ".join(str(c).upper().ljust(w) for c, w in zip(cols, widths))
    body = ["  ".join(str(r.get(c, "")).ljust(w) for c, w in zip(cols, widths)) for r in rows]
    return "\n".join([line, "  ".join("-" * w for w in widths), *body])


def kv(d: dict) -> str:
    w = max(len(k) for k in d)
    return "\n".join(f"{k.ljust(w)} : {v}" for k, v in d.items())


def _opts(argv: list[str], flags: set[str] = frozenset(), values: set[str] = frozenset()):
    """(positional, {name: value}) from a simple --name value / --flag command line."""
    pos, opts, i = [], {}, 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--"):
            name = a[2:]
            if name in flags:
                opts[name] = True
            elif name in values and i + 1 < len(argv):
                opts[name] = argv[i + 1]
                i += 1
            else:
                raise ValueError(f"unknown or incomplete option {a}")
        else:
            pos.append(a)
        i += 1
    return pos, opts


class Console(cmd.Cmd):
    prompt = PROMPT
    intro = INTRO

    def __init__(self, out=None):
        super().__init__()
        self.out = out or sys.stdout
        self.stdout = self.out
        self.loop = asyncio.new_event_loop()
        self.failed = False
        self._start()

    # ── plumbing ────────────────────────────────────────────────────────
    def _start(self) -> None:
        from . import gpc
        from .config import settings
        from .database import init_db
        from .dbgateway import SYSTEM, act_as
        try:
            gpc.load(settings)
        except gpc.PolicyError as exc:
            self.say(f"warning: the policy could not be loaded ({exc}); using the defaults")
        self.run(init_db())
        act_as(SYSTEM)

    def run(self, coro):
        return self.loop.run_until_complete(coro)

    def say(self, text: str = "") -> None:
        print(text, file=self.out, flush=True)

    def fail(self, text: str) -> None:
        self.failed = True
        print(f"error: {text}", file=self.out, flush=True)

    def onecmd(self, line: str):
        from .services.rootops import RootError
        try:
            return super().onecmd(line)
        except RootError as exc:
            self.fail(str(exc))
        except ValueError as exc:
            self.fail(str(exc))
        return False

    def emptyline(self):
        return False

    def default(self, line):
        self.fail(f"unknown command: {line.split()[0]} (try 'help')")

    def _args(self, line: str) -> list[str]:
        return shlex.split(line)

    def close(self) -> None:
        try:
            from .database import engine
            self.run(engine.dispose())
        finally:
            self.loop.close()

    # ── commands ────────────────────────────────────────────────────────
    def do_status(self, line):
        """status: the state of the system: version, profile, database, super admins, sessions, test mode, OTA."""
        from .services import rootops
        self.say(kv(self.run(rootops.status())))

    def do_version(self, line):
        """version: the imPress version."""
        from .config import APP_VERSION
        self.say(APP_VERSION)

    def do_users(self, line):
        """users list [--role R] | show USER | create USER --role admin|teacher [--name N] [--email E] [--password P] [--ta]
        | set-password USER [--password P] | finish-setup USER | activate USER | deactivate USER | delete USER | trash
        | restore USER|ID | unlock USER
        A new account (or a reset) gets a generated temporary password unless you give one; the person chooses their own
        at first sign-in. Super admins are created with 'superadmin create', not here."""
        from .services import rootops
        a = self._args(line)
        if not a:
            return self.fail("users: list | show | create | set-password | activate | deactivate | delete | trash | restore | unlock")
        sub, rest = a[0], a[1:]
        if sub == "list":
            pos, o = _opts(rest, values={"role"})
            self.say(table(self.run(rootops.list_users(o.get("role"))), ["id", "username", "name", "role", "designation", "status"]))
        elif sub == "show":
            rows = [r for r in self.run(rootops.list_users()) if rest and rest[0] in (r["username"], str(r["id"]))]
            self.say(kv(rows[0]) if rows else "no such account")
        elif sub == "create":
            pos, o = _opts(rest, flags={"ta"}, values={"role", "name", "email", "password"})
            if not pos or o.get("role") not in ("admin", "teacher"):
                return self.fail("users create USER --role admin|teacher [--name N] [--email E] [--password P] [--ta]")
            user, pw = self.run(rootops.create_account(pos[0], o["role"], o.get("email", ""), o.get("name", ""),
                                                       o.get("password", ""), "ta" if o.get("ta") else "faculty"))
            self.say(f"created {user}\ntemporary password: {pw}\n(they must choose their own at first sign-in)")
        elif sub == "set-password":
            pos, o = _opts(rest, values={"password"})
            if not pos:
                return self.fail("users set-password USER [--password P]")
            user, pw = self.run(rootops.set_password(pos[0], o.get("password", "")))
            self.say(f"{user}: temporary password: {pw}\n(signed out everywhere; they choose their own at next sign-in)")
        elif sub == "finish-setup":
            if not rest:
                return self.fail("users finish-setup USER")
            self.say(f"{self.run(rootops.finish_setup(rest[0]))}: setup treated as done (the password is unchanged)")
        elif sub in ("activate", "deactivate"):
            if not rest:
                return self.fail(f"users {sub} USER")
            self.say(f"{self.run(rootops.set_active(rest[0], sub == 'activate'))}: {sub}d")
        elif sub == "delete":
            if not rest:
                return self.fail("users delete USER")
            self.say(f"{self.run(rootops.delete_account(rest[0]))} moved to the trash (restorable for 30 days)")
        elif sub == "trash":
            self.say(table(self.run(rootops.trash())))
        elif sub == "restore":
            if not rest:
                return self.fail("users restore USER|ID")
            self.say(f"{self.run(rootops.restore_account(rest[0]))} restored")
        elif sub == "unlock":
            if not rest:
                return self.fail("users unlock USER")
            self.say(f"cleared {self.run(rootops.unlock(rest[0]))} throttle record(s)")
        else:
            self.fail(f"users: unknown subcommand {sub}")

    def do_superadmin(self, line):
        """superadmin create USER [--name N] [--email E] [--password P]
        The only way to create a super admin. The account starts as 'pending setup': the temporary password only opens
        onboarding, where its owner sets their own."""
        from .services import rootops
        a = self._args(line)
        if not a or a[0] != "create":
            return self.fail("superadmin create USER [--name N] [--email E] [--password P]")
        pos, o = _opts(a[1:], values={"name", "email", "password"})
        if not pos:
            return self.fail("superadmin create USER [--name N] [--email E] [--password P]")
        user, pw = self.run(rootops.create_account(pos[0], "super_admin", o.get("email", ""), o.get("name", ""), o.get("password", "")))
        self.say(f"created super admin {user}\ntemporary password: {pw}\n(they must choose their own at first sign-in)")

    def do_sessions(self, line):
        """sessions list [USER] | end USER | end --all: who is signed in; sign someone out (or everyone)."""
        from .services import rootops
        a = self._args(line)
        if not a or a[0] == "list":
            self.say(table(self.run(rootops.sessions(a[1] if len(a) > 1 else None))))
        elif a[0] == "end" and len(a) > 1:
            n = self.run(rootops.end_sessions(None if a[1] == "--all" else a[1]))
            self.say(f"ended {n} session(s)")
        else:
            self.fail("sessions list [USER] | end USER | end --all")

    def do_backup(self, line):
        """backup list | save NAME | restore ID --yes: the backups (see 'list' for ids like saved/NAME or rolling/rolling.db)."""
        from .services import backups
        a = self._args(line)
        if not a or a[0] == "list":
            self.say(table(backups.listing(), ["id", "label", "modified", "size"]))
        elif a[0] == "save" and len(a) > 1:
            e = self.run(backups.save(a[1], "root (console)"))
            self.say(f"saved: {e['id']}")
        elif a[0] == "restore" and len(a) > 1:
            if "--yes" not in a:
                return self.fail("restore replaces the live database and signs everyone out: add --yes to go ahead")
            try:
                r = self.run(backups.restore(a[1], "root (console)"))
            except backups.BackupError as exc:
                return self.fail(exc.message)
            self.say(f"restored {r['restored']} (what was there is kept as {r['kept']})")
        else:
            self.fail("backup list | save NAME | restore ID --yes")

    def do_policy(self, line):
        """policy show: the effective global policy (flags, values and where each came from). Root changes it with
        a signed file or launch flags (scripts/gpc.py, python -m app.serve --help); it is not changed here."""
        from . import gpc
        if self._args(line)[:1] not in ([], ["show"]):
            return self.fail("policy show")
        d = gpc.describe()
        self.say(f"profile: {d['profile']}")
        self.say(table(d["flags"], ["name", "value", "source"]))

    def do_audit(self, line):
        """audit verify FILE: check an external audit trail's hash chain."""
        from pathlib import Path

        from .services import auditsink
        a = self._args(line)
        if len(a) != 2 or a[0] != "verify":
            return self.fail("audit verify FILE")
        problems = auditsink.verify_file(Path(a[1]))
        self.say("the audit chain is intact" if not problems else "\n".join(problems))
        self.failed = self.failed or bool(problems)

    def do_testmode(self, line):
        """testmode status: whether test mode is on, forced by root, or not allowed."""
        from . import gpc
        from .services import test_mode
        st = test_mode.state()
        self.say(kv({"on": st["on"], "forced by root": gpc.get("test_mode.forced"), "allowed": gpc.get("test_mode.allowed"),
                     "since": st["since"] or "-"}))

    def do_deadlock(self, line):
        """deadlock check: run global_deadlock_prevention now (rolls back and creates a recovery account if there is no active super admin)."""
        from .services import deadlock
        done = self.run(deadlock.check("console"))
        self.say("an active super admin exists: nothing to do" if done is None else f"acted: {done}")

    def do_system(self, line):
        """system reset --confirm "RESET EVERYTHING": clear everything and start over (a full copy is saved first).
        The default super admin comes back with a new password, shown here."""
        from .services import bootstrap, rootops
        a = self._args(line)
        pos, o = _opts(a[1:], values={"confirm"}) if a[:1] == ["reset"] else ([], {})
        if a[:1] != ["reset"] or o.get("confirm") != "RESET EVERYTHING":
            return self.fail('system reset --confirm "RESET EVERYTHING"')
        backup = self.run(rootops.clear_data("everything", entry="console.system_reset"))
        self.run(bootstrap.after_reset("root (console)"))
        self.say(f"the system was reset. A copy of what was there: {backup}")

    def do_features(self, line):
        """features: every feature, whether it is on, and who set it last (administrators, super admins, root, TrustedInstaller)."""
        from .services import features

        async def go():
            from .database import async_session
            async with async_session() as db:
                await features.load(db)
            return [{k: (d[k] if d[k] is not None else "-") for k in ("name", "enabled", "set_by", "set_at")} | {"changeable_by": features.RANK_SHORT.get(d["min_rank"])}
                    for d in (features.describe(n) for n in features.FEATURES)]
        self.say(table(self.run(go())))

    def do_feature(self, line):
        """feature NAME on|off [--lock]: switch a feature as root. Root outranks administrators and super admins; --lock stops
        everyone below root changing it again. (To set it at launch instead: --feature features.disabled=NAME,NAME.)"""
        from .database import async_session
        from .services import features
        a = self._args(line)
        pos, o = _opts(a, flags={"lock"})
        if len(pos) != 2 or pos[1] not in ("on", "off"):
            return self.fail("feature NAME on|off [--lock]")

        async def go():
            async with async_session() as db:
                await features.load(db)
                try:
                    out = await features.set_feature(db, pos[0], pos[1] == "on", "root (console)", features.ROOT,
                                                     min_rank=features.ROOT if o.get("lock") else None)
                except features.Refused as exc:
                    raise ValueError(str(exc)) from None
                await db.commit()
                return out
        d = self.run(go())
        self.say(f"{d['name']}: {'on' if d['enabled'] else 'off'}" + (" (locked: only root can change it)" if o.get("lock") else ""))

    def do_policylog(self, line):
        """policylog [FLAG]: who changed which policy or feature, and when."""
        from .database import async_session
        from .services import features
        a = self._args(line)

        async def go():
            async with async_session() as db:
                return await features.history(db, a[0] if a else None, 40)
        self.say(table(self.run(go()), ["at", "flag", "old", "new", "actor", "actor_role"]))

    def do_requirements(self, line):
        """requirements: what TrustedInstaller checks on this host (system, memory, disk, ...) and the minimum for each."""
        from .services import boot_verify
        checks, host = boot_verify.inspect()
        self.say(table([{"check": c["title"], "found": c["detail"], "needs": c["minimum"], "ok": "yes" if c["ok"] else "NO"} for c in checks]))
        self.say(f"\ncontainer: {'yes' if host['container'] else 'no'}")

    def do_iips(self, line):
        """iips status | rehash: imPress Integrity Protection. 'rehash' makes the program's files, as they are now, the reference."""
        from .services import iips
        a = self._args(line)
        if a[:1] == ["rehash"]:
            doc = iips.write_baseline()
            self.say(f"the current files are the new reference ({len(doc['files'])} files, tree {doc['root_hash'][:16]})")
        elif a[:1] in ([], ["status"]):
            st = iips.check(enabled=True)
            self.say(kv({"status": st["status"], "differences": len(st["changes"]), "baseline": iips.baseline_path().name}))
            for c in st["changes"][:20]:
                self.say(f"  {c['change']:8} {c['path']}")
        else:
            self.fail("iips status | rehash")

    def do_clear(self, line):
        """clear: clear the screen."""
        print("\033[2J\033[H", end="", file=self.out)

    def do_exit(self, line):
        """exit: leave the console."""
        return True

    do_quit = do_exit
    do_EOF = do_exit

    def completenames(self, text, *ignored):
        return [n[3:] + " " for n in self.get_names() if n.startswith("do_" + text) and n not in ("do_EOF", "do_quit")]


def _root_screen_allowed() -> bool:
    """The separate console (ssh, docker exec) is closed when root.allow_access is off or the host is a container.
    The console on the container's own screen (the root screen) sets IMPRESS_ROOT_SCREEN and is always allowed."""
    import os
    if os.environ.get("IMPRESS_ROOT_SCREEN"):
        return True
    from . import gpc
    from .config import settings
    from .services import boot_verify
    try:
        gpc.load(settings)
    except Exception:                                    # noqa: BLE001
        pass
    return bool(gpc.get("root.allow_access")) and not boot_verify.in_container()


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="python -m app.console", description=__doc__.split("\n\n")[0])
    ap.add_argument("-c", "--command", action="append", default=[], help="run this command (repeatable), then exit")
    args = ap.parse_args(argv)
    if not _root_screen_allowed():
        print("The separate root console is switched off here (policy root.allow_access): TrustedInstaller closes it inside a "
              "container. Use the console on the container's own screen (docker run -it, docker attach).", file=sys.stderr)
        return 4
    try:
        import readline  # noqa: F401  (line editing and history)
    except ImportError:
        pass
    con = Console()
    try:
        if args.command:
            for line in args.command:
                con.onecmd(line)
        elif not sys.stdin.isatty():
            for line in sys.stdin:
                if con.onecmd(line.strip()):
                    break
        else:
            con.cmdloop()
    finally:
        con.close()
    return 1 if con.failed else 0


if __name__ == "__main__":
    sys.exit(main())
