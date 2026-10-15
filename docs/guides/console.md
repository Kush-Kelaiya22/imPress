# The root console and the root screen

imPress has two sides. One is what the **system** does: it serves the web app, talks to the classroom hardware, repairs its database, verifies the host and refuses what is not allowed. The other is **root**: the person who runs the server, who has a shell on it (ssh, a terminal, `docker run -it`). Root is not an application account. Root cannot be reached from the web app or the API, and nothing a web user does can change what root decided.

Root has two tools: the **root screen**, which you see when imPress is started from a terminal, and the **root console**, a shell for commands.

## The root screen

```text
  root@impress: ~                                   imPress 2.2.24 · root screen
 ╻┏┳┓┏━┓┏━┓┏━╸┏━┓┏━┓   v2.2.24   ● running    http://0.0.0.0:8000
 ┃┃┃┃┣━┛┣┳┛┣╸ ┗━┓┗━┓   standard profile
 ╹╹ ╹╹  ╹┗╸┗━╸┗━┛┗━┛   type help for the commands
────────────────────────────────────────────────────────────────────────
 10:41:02  INFO      Application startup complete.
 10:41:09  WARNING   Possible DoS: 1210 requests a minute to read pages from 203.0.113.9
 …                                                  (the live log scrolls here)
────────────────────────────────────────────────────────────────────────
 help · status · users list · features · backup save NAME · iips status · exit stops the server
root@impress:~>
```

Start imPress in a terminal and you get it: the logo and version (with the patch number), the state of the server, the **live log** scrolling above, and a **command line** at the bottom. The log is coloured by level; request lines are quiet. The screen keeps a bounded in-memory log history: enter `scroll up [lines]`, `scroll down [lines]`, `scroll top`, or `scroll live` to review startup errors and return to new output. `clear` clears that view. The server runs as a child process: closing the screen (`exit`, Ctrl+C) stops it.

Without a terminal (a service, a pipe, a container started with `-d`) there is no screen: the logo and version are printed once, then the log is plain lines. Force that with `--plain` or `IMPRESS_PLAIN=1`.

### In a container

- `docker run -it … IMAGE` attaches your terminal: you get the root screen, and its command line is root's console.
- `docker run -d …` runs in the background: no screen, plain log (`docker logs -f`).
- A **separate** console (`docker exec -it … python -m app.console`, or ssh into the host and open one) is **refused inside a container**. TrustedInstaller turns the policy flag `root.allow_access` off when it finds it is running in a container, and the console checks it. The screen attached to the container is root's there. The change is recorded in the [change log](../design/trusted-boot.md#who-changed-what) as made by TrustedInstaller.

## The console

```bash
scripts/console.sh                      # macOS and Linux: an interactive prompt with history and tab completion
console.bat                             # Windows
cd backend && python -m app.console -c "users list" -c "status"     # one command per -c, then exit
echo "status" | python -m app.console   # commands from a pipe
```

It runs on the server's own host with the database file's own access. Every command that changes something is a **flagged** entry in the activity log and in the external audit trail, recorded as made by root. It is the only place a super admin account can be created.

| Command | What it does |
|---|---|
| `status`, `version` | version, profile, database state, super admins, sessions, test mode, OTA |
| `users list [--role R]`, `users show USER` | the accounts |
| `users create USER --role admin\|teacher [--name N] [--email E] [--password P] [--ta]` | add an account; a temporary password is generated unless you give one |
| `superadmin create USER [--name N] [--email E] [--password P]` | the only way to create a super admin; it starts *pending setup* |
| `users set-password USER [--password P]` | a new temporary password; signs the account out everywhere |
| `password show`, `password reset [--password P]` | root-only access to the protected default super admin's configured password, or set a new one and sign it out everywhere |
| `users finish-setup USER` | treat the welcome set-up as done (labs and tests) |
| `users activate\|deactivate USER`, `users delete USER` | enable, disable, move to the trash |
| `users trash`, `users restore USER` | the 30-day trash |
| `users unlock USER` | clear the sign-in throttle for an account |
| `sessions list [USER]`, `sessions end USER`, `sessions end --all` | who is signed in; sign someone (or everyone) out |
| `features`, `feature NAME on\|off [--lock]` | features and who set them; root outranks administrators and super admins, `--lock` stops everyone below root changing it |
| `policy show`, `policylog [FLAG]` | the effective global policy, and who changed what, when |
| `requirements` | what TrustedInstaller checks on this host and the minimum for each |
| `iips status`, `iips rehash` | integrity protection: compare, or accept the current files as the reference |
| `backup list`, `backup save NAME`, `backup restore ID --yes` | backups of the database and system state |
| `api routes [FILTER]`, `api METHOD PATH [JSON]` | call the application's own routes as the default super admin, in-process and through the same authorization and validation as the web app |
| `testmode status`, `deadlock check` | test mode; run deadlock prevention now |
| `system reset --confirm "RESET EVERYTHING"` | clear everything and start over (a full copy is saved first); the default super admin comes back with a new password, shown here |
| `audit verify FILE` | check an external audit trail's hash chain |
| `help [COMMAND]`, `clear`, `scroll`, `exit` | |

Exit codes: `0` success, `1` a command failed, `4` the separate console is closed here.
