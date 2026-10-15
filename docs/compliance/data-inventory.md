# Data inventory

What personal data imPress holds, derived from its database models. Copy this table, fill in the right-hand columns for your institution, and keep it with your record of processing activities. "Proposed" retention is a suggestion to decide on, not something imPress enforces unless the last column says so.

| Data | Fields | Whose | Purpose | Where it lives | Who can see it | Proposed retention | Enforced by imPress |
|---|---|---|---|---|---|---|---|
| **Staff accounts** | username, name, e-mail, role, password (salted bcrypt over SHA-256, never reversible), active flag | teachers, administrators | sign-in, access control, accountability | `users` | administrators (list), the person (own profile) | while employed, then delete the account | deletion is available (permanent delete); nothing automatic |
| **Sessions** | account, time, **IP address**, browser/OS string, idle and expiry times | staff | session security, one-device rule | `user_sessions` | administrators indirectly (blocked-sign-in entries) | days | expired and revoked sessions are purged automatically |
| **Sign-in throttling** | counters keyed by username or **IP address** | staff or attackers | slow password guessing | `login_throttle` | nobody in the UI | minutes | the window resets; rows are kept until cleared |
| **Students** | enrollment number, name, e-mail, phone, programme, intake and graduation year, linked module | students | roster, results, attendance | `students` | staff with access to the student's classes; administrators | the course plus an agreed period | erase (see the [rights runbook](dsar-runbook.md)); nothing automatic |
| **Enrolments** | which student is in which class | students | roster | `student_enrollments` | staff of that class; administrators | with the student record | removed on erase |
| **Attendance** | student, class, time, present | students | attendance records | `attendance` | staff of that class | per your academic-records rules | removed on erase |
| **Quiz answers and poll votes** | student (or none), question, chosen option, time taken | students | grading, participation | `quiz_answers`, `poll_votes` | staff of that class | per your academic-records rules | on erase the student link is cleared, so completed results keep their totals but are anonymous |
| **Student modules** | module id, the enrollment number it is provisioned with, last seen, battery | students (indirectly) | route answers to the right student | `student_modules`, `esp_devices` | administrators | while the module is in use | the link is cleared on erase |
| **Activity log** | who did what to what, when; details (some include names, class names, addresses of a blocked sign-in) | staff, and students named in entries | accountability, security | `activity_logs` | administrators with audit access | **proposed 180 days minimum** for security logs where required, longer by policy | deleted after `audit.purge_days` (0 = never, the standard profile's default); a clear or reset keeps entries younger than `audit.min_retention_days` |
| **External audit trail** | the same entries, without any student personal data | staff | tamper-evident accountability | the file or collector you configure | whoever administers that volume | per your log-retention policy | append-only by design; imPress never deletes it |
| **Integrity backups** | whole-database copies: start-up, rolling, failed (forensic), before-a-clear | everyone above | repair after tampering, recovery | `IMPRESS_TEMP_BACKUP_DIR` | the server's user (0600/0700) | short | rolling is replaced every 5 minutes; forensic copies pruned by count; copies before a clear expire (`integrity.before_clear_days`) |
| **Test-data copies** | a copy of the real database (debug mode), pending test databases, saved datasets, CSV exports | everyone above | trying the system | `test-data/` next to the database | the server's user; super admins in the UI | hours to days | pending and saved copies expire by policy; exports are signed and logged |
| **Your own off-host backups and exports** | database, firmware, `.env` | everyone above | disaster recovery | your storage | you decide | you decide | **not managed by imPress**: include them in erasure and retention |

## Things to check

- **IP addresses** of staff are stored with sessions and in some audit entries. Say so in the staff notice.
- **Student phone and e-mail** are optional fields; if you don't need them, don't collect them (minimisation).
- **Children:** if students are minors where you operate, settle consent and any restrictions on monitoring before using attendance and participation tracking.
- **Transfers:** where does the server run, where do the backups and the audit collector run, and who administers them?
- **Free-text fields** (class names, course descriptions, question text) can contain personal data typed by staff. Train staff not to put it there.
