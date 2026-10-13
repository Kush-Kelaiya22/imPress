# Authorization model

imPress decides every access question in one module, [`backend/app/policy.py`](../../backend/app/policy.py) (#122). Routes declare the permission they need; the policy answers whether the caller has it, whether the resource is in the caller's scope, and whether an integrity rule forbids the action anyway. Nothing else in the backend compares roles (a test fails if it does).

## Privilege rings

```{mermaid}
flowchart TB
    TI["Ring −2 · TrustedInstaller<br/>firmware verification service (#123)<br/>not a login"]
    ROOT["Ring −1 · Root<br/>integrity rules in policy.py<br/>not a login, grants nothing"]
    SA["Ring 0 · super_admin"]
    AD["Ring 1 · admin"]
    TE["Ring 2 · teacher (faculty)<br/>assigned classes"]
    ST["Ring 3 · student<br/>no account: identified by module and enrolment number"]
    UN["Ring 4+ · unauthenticated<br/>a state, never a role"]
    ROOT -. vetoes .-> SA & AD & TE
    TI -. checks every firmware offer .-> SA & AD
```

| Ring | Identity | Can log in | What it holds |
|---|---|---|---|
| −2 | **TrustedInstaller** (#123) | no | no user permissions; verifies firmware before any device is offered it |
| −1 | **Root** | no | no permissions; its rules veto actions (below) |
| 0 | `super_admin` | yes | every permission in the matrix |
| 1 | `admin` | yes | faculty and administration permissions |
| 2 | `teacher` | yes | faculty permissions, limited to assigned classes |
| 3 | student | no (decision #124) | answers and votes through an enrolled module while a quiz or poll is live |
| 4+ | unauthenticated | – | nothing but the public routes (login, health, CSV templates) |

A lower ring number does **not** inherit everything automatically: each role holds exactly the permissions listed for it, Root and TrustedInstaller hold none, and neither can be assigned to an account (the role field accepts only `teacher`, `admin`, `super_admin`).

## How a request is decided

1. **Authenticated**: a valid, unexpired, unrevoked session (`auth.get_current_user`), or a device key for device routes.
2. **Active**: a deactivated account holds no permission.
3. **Permission**: the route's `require("<permission>")` must be granted to the user's role (`GRANTS`). Default deny.
4. **Scope**: the resource must be the caller's: `class_access` (primary teacher, co-faculty, admin) for classes, quizzes, polls, results and the class WebSocket; `roster_access` for enrolment; `class_owner_or_admin` for deleting a class.
5. **Root rules**: checked last and override any grant (below).

## Permission matrix

| Permission | teacher | admin | super_admin | Allows |
|---|---|---|---|---|
| `assessments.manage` | ✓ | ✓ | ✓ | create, start, advance and stop quizzes and polls of assigned classes |
| `classes.create` | ✓ | ✓ | ✓ | create a class (the creator becomes its primary teacher) |
| `classes.join` | ✓ | ✓ | ✓ | join a class as co-faculty with its join code |
| `classes.manage` | ✓ | ✓ | ✓ | activate, deactivate and delete assigned classes (delete: primary teacher only) |
| `classes.read` | ✓ | ✓ | ✓ | open assigned classes, their live device tree and presence (scope: class access) |
| `courses.read` | ✓ | ✓ | ✓ | list active courses |
| `participation.read` | ✓ | ✓ | ✓ | quiz and poll details and results of assigned classes |
| `students.manage` | ✓ | ✓ | ✓ | register, edit, import and enrol students (roster: primary teacher, #146) |
| `students.read` | ✓ | ✓ | ✓ | look up students |
| `audit.read` | – | ✓ | ✓ | activity log |
| `classes.manage_all` | – | ✓ | ✓ | every class: create for others, assign faculty, import/export, delete |
| `courses.manage` | – | ✓ | ✓ | create, edit, delete courses; see inactive ones |
| `devices.manage` | – | ✓ | ✓ | device access, keys, links and verification |
| `devices.read` | – | ✓ | ✓ | every gateway, hub and student module |
| `firmware.approve` | – | ✓ | ✓ | approve or deprecate an image |
| `firmware.deploy` | – | ✓ | ✓ | start, pause, resume and cancel deployments; push one device |
| `firmware.manage` | – | ✓ | ✓ | upload, edit and delete firmware images |
| `firmware.read` | – | ✓ | ✓ | firmware registry and deployments |
| `students.delete` | – | ✓ | ✓ | permanently delete a student record |
| `users.manage` | – | ✓ | ✓ | create, edit, deactivate, reactivate, reset password, delete staff accounts |
| `users.read` | – | ✓ | ✓ | list staff accounts |
| `users.assign_role` | – | – | ✓ | grant or remove any role |
| `users.manage_privileged` | – | – | ✓ | manage super admin accounts |

A test (`test_policy.py`) fails if this table and `GRANTS` differ.

## Root: integrity rules

| Rule | Where | Result |
|---|---|---|
| At least one active super admin exists | SQLite triggers (migration 9, #116), checked inside the write | `409 LAST_SUPER_ADMIN`; concurrent requests cannot bypass it |
| Nobody deactivates, deletes or changes the role of their own account | `policy.account_refusal` | `403 SELF_LOCKOUT` |
| Only a super admin manages a super admin account | `policy.account_refusal` | `403 FORBIDDEN_TARGET` |
| Only a super admin grants or removes a role | `policy.account_refusal`, `policy.can_grant` | `403 FORBIDDEN_ROLE` |
| A deleted user's references are settled by documented rules | `accounts.DELETE_RULES` (#117) | `409 USER_OWNS_CLASSES` while they own a class |
| Account changes that end access revoke sessions and sockets | `accounts.revoke` (#118) | old tokens and sockets stop working |

Recovery when a database already has no usable super admin is an offline command on the server (`python -m app.manage restore-super-admin`, #120), never an HTTP route.

## Errors

Refusals carry a machine-readable code: `{"detail": {"code": "FORBIDDEN", "message": "Not allowed: users.manage"}}`. The web app shows `message`. Codes: `FORBIDDEN`, `FORBIDDEN_TARGET`, `FORBIDDEN_ROLE`, `SELF_LOCKOUT` (403), `LAST_SUPER_ADMIN`, `USER_OWNS_CLASSES` (409), `USE_LIFECYCLE_ENDPOINT` (422).

## Adding or changing a route

1. Give the route `user = Depends(require("<permission>"))`. Use an existing permission; add a new one to `policy.py` only with its row in this table.
2. If the route acts on a class or its contents, check the scope (`class_access`, `roster_access`).
3. Run `pytest backend/tests/test_policy.py backend/tests/test_route_matrix.py`. The matrix test records which status every route returns to five kinds of caller; an intended permission change is recorded with `IMPRESS_UPDATE_ROUTE_MATRIX=1` and explained in the PR.

The web app does not keep its own permission rules: user rows carry `allowed_actions` computed by the policy (#119), and navigation by role is only a convenience; the server refuses whatever it does not allow.
