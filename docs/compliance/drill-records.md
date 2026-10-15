# Drill records

The drills the compliance runbooks ask for, **run as automated tests** so they can be repeated at every release, with what each one found. They prove the *product's* part. The institution's part (its own off-host storage, its legal review, its contacts and deadlines) is still to be done and recorded by the institution: copy the table at the end and fill it in.

Run them: `python run_tests.py -s backend` (file `backend/tests/test_compliance_drills.py`), or `pytest backend/tests/test_compliance_drills.py`.

## Data-rights (DSAR) drill: [#200](https://github.com/Kush-Kelaiya22/imPress/issues/200)

Test `test_data_rights_drill_finds_one_student_everywhere_and_erases_them`, against a generated student who is enrolled, has answered a quiz and has a linked module, following the [runbook](dsar-runbook.md).

| Runbook step | What the drill did | Result |
|---|---|---|
| 1. Student record | found by roll number on the Students list | found |
| 1. Enrolments and classes | `GET /api/students/{id}/classes` | found |
| 1. Participation | `GET /api/admin/students/{id}/participation` | found |
| 1. Module link | the student module is linked to the enrolment | found |
| 1. Activity log | the student's name appears in the log while the record exists | found |
| 1. External audit trail | the sink file holds neither the name nor the roll number | nothing to search (as the runbook says) |
| 1. Test-data copies | a pending test-data copy made from the real database holds the student | found: **delete it** (Test data page); the drill does |
| 4. Erase | `DELETE /api/students/{id}/hard-delete` | gone from every table and from the log (replaced by a one-way reference) |
| 4. Backups | the rolling integrity backup still holds the student | **remains until replaced**: record the expiry, re-apply the erasure if a backup is restored |

Finding: the places the runbook lists are the complete set in the product; the two that outlive an erasure are test-data copies (delete them) and backups (expire them).

## Restore and tamper drill: [#202](https://github.com/Kush-Kelaiya22/imPress/issues/202)

| Drill (test) | Result |
|---|---|
| `test_restore_drill_puts_the_data_back_and_measures_how_long_it_took`: save a backup, add a student, restore the backup with the password and the typed name | the data is exactly as at the backup (the student made afterwards is gone: **RPO = the moment of the backup**); the restore of a small database took well under a second and under 30 s is asserted (**RTO** grows with the database: measure yours); the database verifies afterwards; everyone is signed out |
| `test_the_external_trail_survives_a_reset_and_shows_tampering`: reset everything through dual control | the local activity log is cleared; the external hash-chained trail **keeps every earlier line**, records the reset, and still verifies; editing one line is found by `audit-verify` |

The off-host copy (`scripts/backup.sh`, tested in `test_backup_script.py`) is the institution's: restore it onto a spare machine once, time it, and record it below.

## The institution's record (copy and fill in)

| Drill | Date | Who | Environment | Result | Time taken | Follow-up |
|---|---|---|---|---|---|---|
| Rights request (access) | | | | | | |
| Rights request (erasure) | | | | | | |
| Restore from the off-host backup | | | | | | |
| Reset, then check the external trail | | | | | | |
