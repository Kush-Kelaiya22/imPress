# Backups, restore and resetting the system

Administrators and super admins can save, view and restore **backups of the database and the system state** from *System → Backups* (feature `backups`). Root has the same in the [console](console.md) (`backup list`, `backup save NAME`, `backup restore ID --yes`).

## What a backup is

| Kind | Made | Kept |
|---|---|---|
| **Saved** | when you press *Save a backup now* | until you delete it |
| **Start-up** and **Rolling** | automatically (the database must verify first) | replaced as the system runs |
| **Failed database** | when the integrity check repairs a database | for investigation |
| **Before a clear** and **before a restore** | automatically, before either action | for 14 to 30 days (policy) |

A saved backup is the database **plus a description of the system state** at that moment: the imPress version, the profile, the effective policy, and what the tables held (accounts, classrooms, students, quizzes, polls, devices, activity entries, the schema version, the number of active super admins). *View* shows it, so you know what you would be going back to.

**Not while test mode is on:** no backup is made or restored then (see [test mode](test-mode.md#notes)); the automatic ones are refreshed from the real data when it ends.

A backup is saved only when the database **verifies**: you never save a damaged copy by accident. The automatic copies live on the same machine and repair tampering; for a copy that survives the machine, use `scripts/backup.sh` ([off-host backup](production-hardening.md)).

## Restoring

1. *System → Backups → Restore* on the copy you want.
2. Type the backup's name and **your password** (a step-up check).
3. imPress checks that the copy itself verifies, keeps what is there now as a *before restore* copy, replaces the live database, and **signs everyone out**, including you.

In the hardened profile (`backups.restore_requires_approval`), a restore also needs a second super admin's approval (dual control).

## Resetting the system

A super admin can **clear class data** or **reset everything** from *System → Approvals*: the request needs a second super admin's approval, a delay in the hardened profile, your password and a typed phrase (`DELETE CLASS DATA` or `RESET EVERYTHING`). A backup is taken first. After a full reset the default super admin comes back with a new password, printed on the root screen. Root can reset from the console with `system reset --confirm "RESET EVERYTHING"`.
