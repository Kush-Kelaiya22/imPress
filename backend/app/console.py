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
import json
import os
import shlex
import sys


PROMPT = "impress# "
INTRO = """imPress root console. You are root: nothing here asks the web app's permission.
Type 'help' for the commands, 'status' for the state of the system, 'exit' to leave."""


def table(rows: list[dict], columns: list[str] | None = None) -> str:
    if not rows:
        return "(none)"
    cols = columns or list(rows[0])
    from .rootscreen import _cell_width, _fit_ansi, plain, safe_text, wrap_ansi
    clean = lambda value: plain(safe_text(str(value))).replace("\n", " ").replace("\t", " ")  # noqa: E731
    cells = lambda value: sum(_cell_width(ch) for ch in value)  # noqa: E731
    headings = [clean(c).upper() for c in cols]
    values = [[clean(r.get(c, "")) for c in cols] for r in rows]
    widths = [max(cells(headings[i]), *(cells(r[i]) for r in values)) for i in range(len(cols))]
    try:
        limit = max(0, int(os.environ.get("IMPRESS_CONSOLE_COLUMNS", "0")))
    except ValueError:
        limit = 0
    if limit:
        if limit < len(cols) * 4 + 2 * (len(cols) - 1):
            # In a very narrow pane, labelled records retain their full values.
            return "\n".join(plain(part) for row in values for i, value in enumerate(row)
                             for part in wrap_ansi(f"{headings[i]}: {value}", limit, indent=min(2, limit // 4)))
        widths = [min(w, limit) for w in widths]
        identifiers = {"id", "username", "roll_number", "code", "mac_address"}
        while sum(widths) + 2 * (len(cols) - 1) > limit:
            candidates = [i for i, w in enumerate(widths) if w > 4 and cols[i] not in identifiers]
            candidates = candidates or [i for i, w in enumerate(widths) if w > 4]
            if not candidates:
                break
            widths[max(candidates, key=lambda i: widths[i])] -= 1

    def fit(value, width):
        if cells(value) > width:
            value = plain(_fit_ansi(value, max(1, width - 1))) + "…"
        return value + " " * max(0, width - cells(value))

    line = "  ".join(fit(value, w) for value, w in zip(headings, widths))
    body = ["  ".join(fit(value, w) for value, w in zip(row, widths)) for row in values]
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
        self.root_password: str | None = None       # given out of band by the root screen, for one command
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
        from fastapi import HTTPException
        from sqlalchemy.exc import SQLAlchemyError
        from . import rootauth
        from .services.rootops import RootError
        try:
            if rootauth.is_sensitive(line):
                what = " ".join(line.split()[:2])
                try:
                    rootauth.require(f"run '{what}'", self.root_password)
                finally:
                    self.root_password = None                 # asked again for the next sensitive command
            return super().onecmd(line)
        except rootauth.RootAuthError as exc:
            self.fail(f"{exc.message} [{exc.code}]")
        except RootError as exc:
            self.fail(str(exc))
        except ValueError as exc:
            self.fail(str(exc))
        except HTTPException as exc:
            detail = exc.detail
            self.fail(detail.get("message", str(detail)) if isinstance(detail, dict) else str(detail))
        except SQLAlchemyError:
            self.fail("The database operation failed; nothing was committed. Check the server log and retry.")
        except Exception as exc:                                  # noqa: BLE001  a command never ends the console
            # Domain errors (BackupError, TestModeError, ...) carry a message fit to show; anything else is a bug,
            # reported by name with a way to see the details rather than a traceback in the middle of the log.
            message = getattr(exc, "message", "")
            if os.environ.get("IMPRESS_CONSOLE_TRACE"):
                import traceback
                traceback.print_exc(file=self.out)
            self.fail(message or f"{type(exc).__name__}: {exc}" + ("" if os.environ.get("IMPRESS_CONSOLE_TRACE") else
                                                                  "  (set IMPRESS_CONSOLE_TRACE=1 for the details)"))
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
            from .services import rootapi
            self.run(rootapi.close())
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
        | restore USER|ID | unlock USER [--ip ADDRESS]
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
            pos, o = _opts(rest, values={"ip"})
            if len(pos) != 1:
                return self.fail("users unlock USER [--ip ADDRESS]")
            self.say(f"cleared {self.run(rootops.unlock(pos[0], o.get('ip')))} throttle record(s)")
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

    def do_mfa(self, line):
        """mfa status USER | reset USER: a super admin's two-step verification. 'reset' removes it (a lost phone and no
        recovery codes); they set it up again in Settings > Security, and the policy may require it before they can approve."""
        from .services import rootops
        a = self._args(line)
        if len(a) != 2 or a[0] not in ("status", "reset"):
            return self.fail("mfa status USER | reset USER")
        self.say(self.run(rootops.mfa(a[1], a[0] == "reset")))

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

    def _reload_policy(self) -> None:
        from . import gpc
        from .config import settings
        gpc.load(settings)

    def do_policy(self, line):
        """policy show | history [FLAG] | restrictions | set NAME VALUE [--note TEXT] | reset [NAME ...]
        The global policy: every flag, its value, who set it and who enforces it since when. `set` and `reset` change the
        sealed policy store and ask for root's password; a super admin may change only the operational flags, from the
        System page. Editing impress.gpc.json by hand does not work: it fails its seal and is reset to the defaults."""
        from . import gpc, gpcstore
        a = self._args(line)
        sub, rest = (a[0] if a else "show"), a[1:]
        if sub == "show":
            d = gpc.describe()
            self.say(f"profile: {d['profile']}")
            rows = [{"name": f["name"], "value": f["value"], "source": f["source"], "set by": f.get("set_by", ""),
                     "enforced since": str(f.get("enforced_at") or "-")[:19], "editable by": f["editable_by"]} for f in d["flags"]]
            self.say(table(rows, ["name", "value", "source", "set by", "enforced since", "editable by"]))
            for problem in d["problems"]:
                self.say(f"! {problem}")
        elif sub == "history":
            rows = [{"#": e["seq"], "when": e["at"], "flag": e["flag"], "old": e["old"], "new": e["new"], "by": e["by"],
                     "authority": e["rank"], "via": e["via"], "note": e["note"]} for e in gpcstore.history(rest[0] if rest else None, 40)]
            self.say(table(rows))
        elif sub == "restrictions":
            self.say(kv(gpcstore.restrictions()))
        elif sub == "set":
            pos, o = _opts(rest, values={"note"})
            if len(pos) != 2:
                return self.fail("policy set NAME VALUE [--note TEXT]")
            self._policy_change(lambda: gpcstore.set_flag(pos[0], pos[1], "root (console)", gpcstore.ROOT, "console", o.get("note", "")),
                                "policy_set", {"flag": pos[0], "value": pos[1]})
            self.say(f"{pos[0]} = {gpc.get(pos[0])!r}  (recorded; the running server picks it up within seconds)")
        elif sub == "reset":
            names = rest or None
            done = []
            self._policy_change(lambda: done.extend(gpcstore.reset_flags(names, "root (console)", gpcstore.ROOT, "console")),
                                "policy_reset", {"flags": names or "all"})
            self.say("back to the defaults: " + (", ".join(done) if done else "nothing was changed"))
        else:
            self.fail("policy show | history [FLAG] | restrictions | set NAME VALUE [--note TEXT] | reset [NAME ...]")

    def _policy_change(self, change, action: str, details: dict) -> None:
        from . import gpcstore
        try:
            change()
        except gpcstore.PolicyRefused as exc:
            raise ValueError(f"{exc.message} [{exc.code}]") from None
        self.run(self._audit(action, details))
        self._reload_policy()

    def do_flags(self, line):
        """flags show | set NAME VALUE | unset NAME | save | reset [--file]
        The feature flags (test mode, OTA, the traffic monitor, features.disabled). `set` changes one for THIS RUN only
        (the server forgets it when it restarts); `save` writes the run's changes into impress.flags.json for every later
        start; `reset` drops them (with --file also restores the shipped file: root's password). Unlike policy, the file
        may also be edited by hand. A change that makes flags conflict is refused."""
        from . import flagsfile, gpc, gpcstore
        a = self._args(line)
        sub, rest = (a[0] if a else "show"), a[1:]
        overlay = gpcstore.session_read()
        if sub == "show":
            d = {f["name"]: f for f in gpc.describe()["flags"]}
            rows = [{"name": n, "value": d[n]["value"], "source": ("session" if n in overlay else d[n]["source"]),
                     "default": d[n]["standard"]} for n, f in gpc.FLAGS.items() if f.scope == "feature"]
            self.say(table(rows))
            if overlay:
                self.say("changed for this session only: " + ", ".join(overlay) + "   ('flags save' keeps them)")
        elif sub == "set":
            if len(rest) != 2:
                return self.fail("flags set NAME VALUE")
            name, raw = rest
            flag = gpc.FLAGS.get(name)
            if flag is None or flag.scope != "feature":
                return self.fail(f"{name} is " + ("a policy flag: use `policy set`" if flag else "not a flag") + " [FLAG_IS_POLICY]")
            value = gpc.coerce(flag, raw)
            pol = gpc.current()
            trial = {**pol.values, name: value}
            found = gpc.find_conflicts(trial, pol.profile, {*pol.sources_explicit(), name})
            if found:
                return self.fail("that would make flags conflict [POLICY_CONFLICT]: " + " | ".join(c.text() for c in found))
            overlay[name] = value
            gpcstore.session_write(overlay, "root (console)")
            self.run(self._audit("flags_set", {"flag": name, "value": value, "session": True}))
            self._reload_policy()
            self.say(f"{name} = {value!r} for this session only. 'flags save' keeps it for later starts.")
        elif sub == "unset" and len(rest) == 1:
            overlay.pop(rest[0], None)
            gpcstore.session_write(overlay, "root (console)")
            self._reload_policy()
            self.say(f"{rest[0]}: back to what the file says")
        elif sub == "save":
            if not overlay:
                return self.say("nothing to save: no flag was changed in this session")
            try:
                where = flagsfile.save(overlay)
            except flagsfile.FlagsFileError as exc:
                return self.fail(str(exc))
            names = list(overlay)
            gpcstore.session_write({}, "root (console)")
            self.run(self._audit("flags_save", {"flags": names}))
            self._reload_policy()
            self.say(f"saved to {where}: {', '.join(names)}. Every later start uses them.")
        elif sub == "reset":
            gpcstore.session_write({}, "root (console)")
            if "--file" in rest:
                flagsfile.write(force=True)
                self.run(self._audit("flags_reset", {"file": True}))
                self.say("this session's changes dropped, and impress.flags.json is the shipped file again")
            else:
                self.say("this session's changes dropped")
            self._reload_policy()
        else:
            self.fail("flags show | set NAME VALUE | unset NAME | save | reset [--file]")

    def do_errors(self, line):
        """errors [CODE | CATEGORY]: the error catalogue (impress.errors.json): what each code means and what to do."""
        from . import errors
        a = self._args(line)
        if not a:
            self.say(table([{"category": c, "codes": len(v), "examples": ", ".join(v[:3])} for c, v in errors.categories().items()]))
            return self.say("errors CATEGORY lists its codes; errors CODE explains one.")
        key = a[0]
        if key in errors.categories():
            self.say(table([{"code": c, "http": errors.describe(c)["http"] or "-", "title": errors.describe(c)["title"]}
                            for c in errors.categories()[key]]))
        elif (e := errors.describe(key.upper())):
            self.say(kv({"code": e["code"], "category": e["category"], "http": e["http"] or "(not an HTTP response)",
                         "title": e["title"], "what it means": e["description"], "what to do": e["fix"]}))
        else:
            self.fail(f"no such error code or category: {key}")

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
        self.say(f"the system was reset. A copy of what was there: {backup}" if backup
                 else "the system was reset (test mode makes no backups, so no copy was kept)")

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
        """iips status | rehash | history: imPress Integrity Protection. 'rehash' makes the program's files, as they are now, the
        reference, for this machine (root's password). It first checks what is there and records it in the reference's history."""
        from . import fingerprint, gpc
        from .services import iips
        a = self._args(line)
        binding = gpc.get("iips.device_binding")
        if a[:1] == ["rehash"]:
            prior = iips.verify_baseline(binding)
            doc = iips.write_baseline(binding=binding, previous=prior if prior["found"] != "missing" else None,
                                      by="root (console, password verified)", reason="rehash requested by root")
            self.say(f"the reference found was: {prior['found']}")
            self.say(f"the current files are the new reference ({len(doc['files'])} files, tree {doc['root_hash'][:16]}, "
                     f"device {fingerprint.short(doc['device'])})")
        elif a[:1] in ([], ["status"]):
            st = iips.check(enabled=True, binding=binding)
            fp, how = fingerprint.get()
            self.say(kv({"status": st["status"], "differences": len(st["changes"]), "baseline": iips.baseline_path().name,
                         "device binding": binding, "this device": f"{fingerprint.short(fp)} ({how})",
                         "device warning": st.get("device_warning") or "-"}))
            for c in st["changes"][:20]:
                self.say(f"  {c['change']:8} {c['path']}")
        elif a[:1] == ["history"]:
            base = iips.verify_baseline(binding)
            self.say(table([{"when": h["at"], "by": h["by"], "reason": h["reason"], "found": h["found"], "device": h["device"]}
                            for h in reversed(base.get("history", []))]))
        else:
            self.fail("iips status | rehash | history")

    # ── the default super admin's password ──────────────────────────────
    def do_password(self, line):
        """password show | reset [--password P]: the default super admin's password. 'show' prints the one fixed in the
        environment (backend/.env); otherwise it is random and shown only when the server starts. 'reset' sets a new
        one (random unless given), signs the account out, and updates backend/.env when the password is fixed there."""
        from .services import bootstrap
        a = self._args(line)
        if not a or a[0] == "show":
            fixed = bootstrap.fixed_password()
            if self._forced_test():
                return self.say(f"test mode is forced: the password is {bootstrap.FORCED_TEST_PASSWORD}")
            if fixed:
                self.say(f"impress.default.superAdmin\n{fixed[0]} = {fixed[1]}")
            else:
                self.say("The password is random: new at every start and shown once on the root screen when it starts.\n"
                         "Use 'password reset' to set one now.")
        elif a[0] == "reset":
            _, o = _opts(a[1:], values={"password"})
            pw, note = self.run(bootstrap.reset_default_password(o.get("password", "")))
            self.run(self._audit("password_reset"))
            self.say(f"impress.default.superAdmin\npassword: {pw}\n{note}")
        else:
            self.fail("password show | reset [--password P]")

    def _forced_test(self) -> bool:
        from . import gpc
        return bool(gpc.get("test_mode.forced"))

    async def _audit(self, action, details=None):
        from .services import rootops
        await rootops.audit(action, details)

    # ── everything a super admin can do: the application's own API, as root ──
    def _api(self, method, path, body=None):
        from .services import rootapi
        status, data = self.run(rootapi.call(method, path, body))
        if method.upper() != "GET":
            self.run(self._audit("api", {"method": method.upper(), "path": path, "status": status}))
        if status >= 400:
            detail = data.get("detail") if isinstance(data, dict) else data
            msg = detail.get("message") if isinstance(detail, dict) else detail
            self.fail(f"{status}: {msg if isinstance(msg, str) else json.dumps(detail)}")
            return None
        return data

    def _show(self, data, columns=None):
        if isinstance(data, list) and data and isinstance(data[0], dict):
            self.say(table([{k: ("" if r.get(k) is None else r.get(k)) for k in (columns or list(r))[:9]} for r in data], columns))
        elif isinstance(data, (dict, list)):
            self.say(json.dumps(data, indent=2, default=str))
        elif data is not None:
            self.say(str(data))

    def do_api(self, line):
        """api METHOD PATH [JSON]: call any of the application's routes as a super admin, for example
        api GET /api/admin/users | api POST /api/admin/classes '{"name":"Demo","code":"demo1"}' | api routes [FILTER].
        Same validation, permissions, approvals and activity log as the web app."""
        from .services import rootapi
        a = self._args(line)
        if a and a[0] == "routes":
            flt = a[1] if len(a) > 1 else ""
            return self.say(table([{"method": m, "path": p} for m, p in rootapi.routes() if flt in p]) )
        if len(a) < 2:
            return self.fail("api METHOD PATH [JSON]   (api routes lists them)")
        body = json.loads(a[2]) if len(a) > 2 else None
        self._show(self._api(a[0], a[1], body))

    def do_classes(self, line):
        """classes list | show ID | create NAME CODE [--teacher USER] [--room R] [--icon I] [--color #RRGGBB] | activate ID | deactivate ID | delete ID | faculty ID USER[,USER]"""
        a = self._args(line)
        sub, rest = (a[0] if a else "list"), a[1:]
        if sub == "list":
            rows = self._api("GET", "/api/admin/classes") or []
            self._show([{k: c.get(k) for k in ("id", "name", "code", "classroom_code", "is_active", "student_count", "teacher_name")} for c in rows])
        elif sub == "show" and rest:
            rows = self._api("GET", "/api/admin/classes")
            if rows is not None:
                self._show(next((c for c in rows if str(c["id"]) == rest[0]), "no such class"))
        elif sub == "create" and len(rest) >= 2:
            pos, o = _opts(rest, values={"teacher", "room", "icon", "color"})
            if len(pos) != 2:
                return self.fail("classes create NAME CODE [--teacher USER] [--room R]")
            body = {"name": pos[0], "code": pos[1], **({"classroom_code": o["room"]} if "room" in o else {}),
                    **({"icon": o["icon"]} if "icon" in o else {}), **({"color": o["color"]} if "color" in o else {})}
            if "teacher" in o:
                body["teacher_id"] = self._user_id(o["teacher"])
            self._show(self._api("POST", "/api/admin/classes", body))
        elif sub in ("activate", "deactivate") and rest:
            self._show(self._api("POST", f"/api/classes/{rest[0]}/{sub}"))
        elif sub == "delete" and rest:
            self._show(self._api("DELETE", f"/api/admin/classes/{rest[0]}"))
        elif sub == "faculty" and len(rest) == 2:
            self._show(self._api("PUT", f"/api/admin/classes/{rest[0]}/faculty", {"teacher_ids": [self._user_id(u) for u in rest[1].split(",")]}))
        else:
            self.fail("classes list | show ID | create NAME CODE [--teacher USER] [--room R] | activate ID | deactivate ID | delete ID | faculty ID USER,USER")

    def _user_id(self, ref):
        from .services import rootops
        rows = self.run(rootops.list_users())
        row = next((r for r in rows if ref in (r["username"], str(r["id"]))), None)
        if row is None:
            raise ValueError(f"no such account: {ref}")
        return row["id"]

    def do_students(self, line):
        """students list [TEXT] | add ROLL NAME [--email E] | delete ID | enroll ID CLASS_ID | unenroll ID CLASS_ID"""
        a = self._args(line)
        sub, rest = (a[0] if a else "list"), a[1:]
        if sub == "list":
            rows = self._api("GET", "/api/students/") or []
            q = (rest[0].lower() if rest else "")
            self._show([{k: r.get(k) for k in ("id", "roll_number", "student_name", "program", "is_active")} for r in rows
                        if q in f"{r.get('student_name', '')} {r.get('roll_number', '')}".lower()])
        elif sub == "add" and len(rest) >= 2:
            pos, o = _opts(rest, values={"email"})
            if len(pos) < 2:
                return self.fail("students add ROLL NAME [--email E]")
            self._show(self._api("POST", "/api/students/", {"roll_number": pos[0], "student_name": " ".join(pos[1:]), **({"email": o["email"]} if "email" in o else {})}))
        elif sub == "delete" and rest:
            self._show(self._api("DELETE", f"/api/students/{rest[0]}/hard-delete"))
        elif sub == "enroll" and len(rest) == 2:
            self._show(self._api("POST", f"/api/admin/classes/{rest[1]}/enroll", {"student_id": int(rest[0])}))
        elif sub == "unenroll" and len(rest) == 2:
            self._show(self._api("DELETE", f"/api/classes/{rest[1]}/students/{rest[0]}"))
        else:
            self.fail("students list [TEXT] | add ROLL NAME [--email E] | delete ID | enroll ID CLASS | unenroll ID CLASS")

    def do_courses(self, line):
        """courses list | add CODE NAME | delete ID"""
        a = self._args(line)
        sub, rest = (a[0] if a else "list"), a[1:]
        if sub == "list":
            self._show([{k: r.get(k) for k in ("id", "code", "name", "credits", "is_active")} for r in self._api("GET", "/api/courses/") or []])
        elif sub == "add" and len(rest) >= 2:
            self._show(self._api("POST", "/api/courses/", {"code": rest[0], "name": " ".join(rest[1:])}))
        elif sub == "delete" and rest:
            self._show(self._api("DELETE", f"/api/courses/{rest[0]}"))
        else:
            self.fail("courses list | add CODE NAME | delete ID")

    def do_devices(self, line):
        """devices list | show ID: gateways, hubs and student modules"""
        rows = self._api("GET", "/api/admin/modules") or []
        a = self._args(line)
        if a[:1] == ["show"] and len(a) > 1:
            return self._show(next((r for r in rows if str(r.get("id")) == a[1]), "no such device"))
        self._show([{k: r.get(k) for k in ("id", "mac_address", "device_type", "device_name", "health", "is_connected", "firmware_version")} for r in rows])

    def do_firmware(self, line):
        """firmware list | approve ID | deprecate ID | delete ID, and: firmware deployments | pause ID | resume ID | cancel ID"""
        a = self._args(line)
        sub, rest = (a[0] if a else "list"), a[1:]
        if sub == "list":
            self._show([{k: r.get(k) for k in ("id", "target", "version", "status", "size", "signed")} for r in self._api("GET", "/api/admin/firmware") or []])
        elif sub in ("approve", "deprecate") and rest:
            self._show(self._api("POST", f"/api/admin/firmware/{rest[0]}/{sub}"))
        elif sub == "delete" and rest:
            self._show(self._api("DELETE", f"/api/admin/firmware/{rest[0]}"))
        elif sub == "deployments":
            self._show([{k: r.get(k) for k in ("id", "state", "kind", "note", "created_at")} for r in self._api("GET", "/api/admin/deployments") or []])
        elif sub in ("pause", "resume", "cancel") and rest:
            self._show(self._api("POST", f"/api/admin/deployments/{rest[0]}/{sub}"))
        else:
            self.fail("firmware list | approve ID | deprecate ID | delete ID | deployments | pause|resume|cancel ID")

    def do_quizzes(self, line):
        """quizzes list | start ID | stop ID, and: polls list | start ID | end ID"""
        self._qp("quizzes", "quizzes", line)

    def do_polls(self, line):
        self._qp("polls", "polls", line)

    def _qp(self, kind, key, line):
        a = self._args(line)
        sub, rest = (a[0] if a else "list"), a[1:]
        if sub == "list":
            data = self._api("GET", "/api/quizzes/overview") or {}
            self._show([{k: r.get(k) for k in ("id", "title", "class_name", "status")} for r in data.get(key, [])])
        elif sub in ("start", "stop", "end") and rest:
            self._show(self._api("POST", f"/api/{kind}/{rest[0]}/{sub}"))
        else:
            self.fail(f"{kind} list | start ID | {'stop' if kind == 'quizzes' else 'end'} ID")

    def do_activity(self, line):
        """activity [N] [--flagged]: the latest entries of the activity log"""
        pos, o = _opts(self._args(line), flags={"flagged"})
        rows = self._api("GET", f"/api/admin/activity?limit={int(pos[0]) if pos else 30}") or []
        if o.get("flagged"):
            rows = [r for r in rows if (r.get("details") or {}).get("flag")]
        self._show([{"time": str(r.get("timestamp", ""))[:19], "who": r.get("username") or "system", "action": r.get("action"),
                     "what": f"{r.get('entity_type', '')} {r.get('entity_id') or ''}".strip()} for r in rows])

    def do_approvals(self, line):
        """approvals list | deny ID: requests that need a second super admin (approving needs a person's password in the web app)"""
        a = self._args(line)
        if a[:1] == ["deny"] and len(a) > 1:
            return self._show(self._api("POST", f"/api/admin/approvals/{a[1]}/deny"))
        data = self._api("GET", "/api/admin/approvals") or {}
        self._show([{k: r.get(k) for k in ("id", "action", "status", "requested_by", "approved_by")} for r in data.get("requests", [])])

    def do_verify(self, line):
        """verify: check the database's integrity now (the same as System, Verify now)"""
        data = self._api("POST", "/api/admin/system/integrity/verify")
        if isinstance(data, dict) and "last_verification" in data:
            last = data["last_verification"]
            self.say(f"database: {data.get('db')}  ({last.get('summary')}, checked {str(last.get('verified_at', ''))[:19]})")
            if data.get("degraded"):
                self.say(f"degraded since {data['degraded'].get('since')}: {data['degraded'].get('message')}")
        else:
            self._show(data)

    # ── familiar names ──────────────────────────────────────────────────
    def do_whoami(self, line):
        """whoami: you are root"""
        self.say("root")

    def do_date(self, line):
        """date: the server's time (Indian Standard Time)"""
        from .timeutil import istnow
        self.say(istnow().strftime("%a %d %b %Y %H:%M:%S IST"))

    def do_uptime(self, line):
        """uptime: how long the server has been running, and how many sessions are open"""
        import time

        from .services import rootops
        st = self.run(rootops.status())
        self.say(f"{time.strftime('%H:%M:%S')}  sessions: {st.get('open sessions', 0)}  version: {st.get('version', '')}")

    def do_ls(self, line):
        """ls [users|classes|students|courses|devices]: list things (users by default)"""
        what = (self._args(line) or ["users"])[0]
        if what not in {"users", "classes", "students", "courses", "devices"}:
            return self.fail("ls [users|classes|students|courses|devices]")
        getattr(self, f"do_{what}")("list")

    def do_ps(self, line):
        """ps: who is signed in (the same as 'sessions list')"""
        self.do_sessions("list")

    def do_env(self, line):
        """env: the settings imPress runs with (secrets are hidden)"""
        from .config import settings
        rows = []
        for k, v in settings.model_dump().items():
            rows.append({"setting": f"IMPRESS_{k}", "value": "********" if any(x in k for x in ("SECRET", "KEY", "PASSWORD")) and v else v})
        self.say(table(rows))

    def do_help(self, arg):
        """help [COMMAND]: the commands, or how to use one"""
        if arg:
            return super().do_help(arg)
        groups = [
            ("System", "status version uptime date env verify system policy flags errors policylog requirements iips features feature testmode deadlock"),
            ("Accounts", "users superadmin password mfa sessions ps ls whoami activity"),
            ("Classroom", "classes students courses quizzes polls"),
            ("Devices", "devices firmware"),
            ("Data", "backup approvals audit api"),
            ("Shell", "help clear exit"),
        ]
        doc = lambda n: (getattr(self, f"do_{n}").__doc__ or "").strip().split("\n")[0].split(":", 1)[-1].strip()   # noqa: E731
        for title, names in groups:
            self.say(f"\n{title}")
            for n in names.split():
                if hasattr(self, f"do_{n}"):
                    self.say(f"  {n.ljust(13)} {doc(n)}"[:118])
        self.say("\nType help COMMAND for the details. 'api routes' lists every route you can call with 'api'.")

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
    ap.add_argument("--serve", action="store_true", help=argparse.SUPPRESS)      # the root screen's long-lived worker
    args = ap.parse_args(argv)
    from .banner import utf8_output
    utf8_output()
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
        elif args.serve:
            for line in sys.stdin:                           # one command per line; END + OK/FAIL after each answer
                con.failed = False
                line, _, con.root_password = line.rstrip("\n").partition("\x1f")      # the root screen's masked prompt
                con.root_password = con.root_password or None
                con.onecmd(line.strip())
                print(f"\x1e{'FAIL' if con.failed else 'OK'}", flush=True)
            con.failed = False
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
