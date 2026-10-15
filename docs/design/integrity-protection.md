# imPress Integrity Protection Service (IIPS)

IIPS checks that **imPress's own files** are the files it started with. It complements the [database gateway and seals](data-integrity.md) (which protect the data) and the [signed code manifest](gpc.md) (which proves the files came from root).

## What it records

At the **first start**, it hashes every file of the program, hashes every folder from the names and hashes inside it, and hashes the whole tree. Because a folder's hash is made from its children's names and hashes, **moving a file or a folder to another place changes it too**, even if no byte changed. The result is the **baseline**, stored next to the database, signed with a key derived from the server's secret so that editing it by hand does not make a changed file pass.

| Covered | Not covered (it is expected to change) |
|---|---|
| `backend/app` (the program and its web files), `scripts`, `VERSION`, the launchers, the requirements | the database and its sidecar files (it has its own seals and backups), logs, state files, caches and `__pycache__`, uploaded firmware, test data, backups, `.env`, the virtual environment, `.git` |

A container image carries its own baseline (`IIPS-BASELINE.json`, made when the image is built and read-only for the server's user), which takes the place of the one next to the database.

## At every start

```mermaid
flowchart TD
    A[Start] --> B{iips.enabled?}
    B -- no --> W[Warning banner on every page]
    B -- yes --> C{Baseline exists?}
    C -- no --> D[Record it: first start]
    C -- yes --> E{Files match?}
    E -- yes --> F[Start]
    E -- no --> X[imPress is disabled]
    D --> F
```

When something differs, imPress **does not start**. The message is:

> imPress has been disabled by Root: an integrity violation was detected in the source folder (3 differences: backend/app/main.py, …). Restore the original files, or start with --rehash to accept the current ones as the new reference.

The start command exits with code 3. If imPress was started in another way (for example `uvicorn app.main:app`), it starts but answers every request with `503 INTEGRITY_VIOLATION` and the same message.

Each difference is classified: **changed**, **added**, **removed** or **moved** (the same content at another path).

## Root's choices

| To… | Do |
|---|---|
| accept the files as they are now (after an upgrade, or after you changed something on purpose) | start with `--rehash`, or `iips rehash` in the console |
| start although the check failed | start with `--bypass-iips`. **Every page, including the sign-in page and super admins' pages, shows a red banner**: *imPress Integrity Protection Service is disabled. Proceed with caution.* It cannot be dismissed. Not allowed in the hardened profile |
| see the differences | `iips status` in the console |
| turn it off for good | policy flag `iips.enabled=false`; the banner stays |

If test mode is also on, the two banners stack: the integrity warning first, then the test mode notice.

## Limits

IIPS finds changes made while imPress was stopped. A change to a running process's memory, or to files by someone who also has the server's secret, is outside its reach: the hardened profile adds the root-signed manifest (`code.verify_manifest=enforce`), whose signing key stays off the host.
