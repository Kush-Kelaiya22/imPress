# The root console and the root screen

imPress has two sides. One is what the **system** does: it serves the web app, talks to the classroom hardware, repairs its database, verifies the host and refuses what is not allowed. The other is **root**: the person who runs the server, who has a shell on it (ssh, a terminal, `docker run -it`). Root is not an application account. Root cannot be reached from the web app or the API, and nothing a web user does can change what root decided.

Root has two tools: the **root screen**, which you see when imPress is started from a terminal, and the **root console**, a shell for commands.

## The root screen

```text
imPress 2.2.x | running | http://0.0.0.0:8000
root console · standard profile · type help for commands
ACTIONS                   | LOGS (live)
> Overview                | 10:41:02 INFO Application startup complete.
  Accounts                | > status
  Signed-in users         | version             : 2.2.0
  Show credentials        | profile             : standard
  Unlock account...       | active super admins : 1
  Classrooms              | ota                 : on
  Students                |
  Courses                 |
───────────────────────────────────────────────────────────────────────
root> users list
Tab: focus | arrows: move | Enter: select/run | PgUp/PgDn: logs
```

Start imPress in a terminal to open the dashboard. Actions are on the left, live logs and command results are on the right, and the command box stays at the bottom. The title shows the version, server state and fixed listener. The log is coloured by level; request lines are quiet.

| Key or action | Result |
| --- | --- |
| Up / Down, then Enter in Actions | Select and run an action. An action ending in `...` fills the command box for you to complete. |
| Start typing | Focus the command box. Enter runs the command. Commands run in order; up to eight may be pending. |
| Tab / Shift+Tab | Move focus between Actions, Logs and the command box. Escape returns to Actions. |
| Up / Down in the command box | Recall command history. Commands containing credential arguments are excluded. |
| Left / Right, Home / End, Backspace / Delete | Edit the command without interference from incoming logs. |
| Ctrl+A / Ctrl+E, Ctrl+U / Ctrl+K / Ctrl+W | Move to the start/end, delete before/after the cursor, or delete the previous word. |
| Page Up / Page Down | Scroll logs from any pane. With Logs focused, arrows scroll by one line and Home / End go to the oldest/newest output. |
| `clear`, `cls`, or Clear logs | Erase the in-memory log view and repaint both panes. |
| Ctrl+L | Redraw the complete screen. |
| `exit`, Ctrl+C, or Stop server | Stop the server and restore the previous terminal screen and input settings. |

The dashboard keeps the most recent 2,000 messages. New output does not move a scrolled log view until its oldest messages leave that buffer. The `scroll up [lines]`, `scroll down [lines]`, `scroll top` and `scroll live` commands also work. Pasted newlines become spaces; pasting alone never executes commands. Resize the terminal to change the layout. At least 24 columns and six rows are needed for both panes.

Each command runs in a separate console process with the same launch policy as the server. Command output and errors stay in the log pane; a failed command does not close the dashboard. The dashboard uses the terminal's alternate screen and restores normal input on exit, Ctrl+C, POSIX SIGTERM and SSH hangup.

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
| `users unlock USER [--ip ADDRESS]` | clear the account's sign-in throttle; optionally clear one explicitly named address's throttle |
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

## Recovering sign-in

The default account is `impress.default.superAdmin`. Choose **Show credentials**, or run `password show`, to inspect the password fixed by root in configuration. If none is fixed, the server generates one at each start and shows it in startup output. It cannot be recovered from its hash; use `password reset` to generate a replacement.

`password reset` revokes the default account's sessions and clears its old account-level guessing counter. When the fixed setting is present in the current working directory's `.env`, the command updates it. If the setting comes from an external environment, update that environment before the next restart. Run `users set-password USER` for another account; it receives a temporary password and chooses its own at sign-in.

The browser shows a countdown while guessing protection is active. During the wait, even the correct password is not checked. A password reset clears that account's counter but preserves the shared-address limit. After investigating address-wide failures, root can run `users unlock USER --ip ADDRESS` using the actual client address from the server log. This recovery is local to the server; it does not disable guessing protection.
