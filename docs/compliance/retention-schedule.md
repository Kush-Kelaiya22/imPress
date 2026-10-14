# Retention schedule

Decide how long each kind of data, **and each copy of it**, is kept; write it down; and make sure a person is responsible for each line. The "proposed" column is a starting point. Law, accreditation and your own academic rules decide the real periods.

| Data or copy | Proposed period | What imPress does | What you must do |
|---|---|---|---|
| Student records, enrolments | course plus [your rule] | nothing automatic | delete or erase after the period ([rights runbook](dsar-runbook.md)) |
| Attendance, quiz answers, poll votes | [your academic-records rule] | nothing automatic; erasing a student clears the link | decide anonymise-or-delete at the end of term |
| Staff accounts | while employed | permanent delete is available | remove leavers promptly |
| Sessions | days | expired and revoked sessions are purged every 5 minutes | nothing |
| Sign-in throttle counters | minutes | windows reset | nothing |
| **Activity log (in the database)** | at least 180 days where CERT-In applies; longer by your policy | deleted after `audit.purge_days` (365 in the hardened profile; **0 = never** in the standard profile) but never sooner than `audit.min_retention_days`; a clear or reset keeps entries younger than that | set the period in the signed policy; copy what you must keep to the external trail first |
| **External audit trail** | per your log-retention policy (at least 180 days where required) | never deletes it | rotate or archive the file or collector on your schedule; keep the chain verifiable (`audit-verify`) |
| Integrity backups: rolling and start-up | replaced continuously | 5-minute refresh | permissions only |
| Forensic copies (a failed database) | until the investigation closes | newest `integrity.forensic_copies` kept | delete when the incident is closed |
| Copies taken before a clear or reset | 14 to 30 days | deleted after `integrity.before_clear_days` (30 standard, 14 hardened) | nothing |
| Test-data copies (pending) | 24 hours to 7 days | deleted after `test_mode.pending_ttl_hours` | nothing |
| Saved test datasets | 30 days or less | deleted after `test_mode.dataset_ttl_days` (30 hardened; never in standard unless set) | prefer generated data |
| Test-data exports (CSV zips) | delete after use | each export is logged and signed | treat as personal data; delete from downloads |
| **Your off-host backups** | [your period, e.g. 35 days] | none | expire them on schedule; record that erased people may remain in backups until they expire |
| Firmware images | while in use | immutable registry | nothing personal |

## Erasure and backups

When someone's data is erased from the live system it stays in older backups until those expire. Say so in the privacy notice, keep the backup period short, and if a backup is ever restored, **re-apply erasures** made since (keep a log of erasure requests: the erase entry holds a keyed reference, not the name, so it can be replayed by an administrator who has the enrollment number).

## Legal holds

If an investigation or dispute needs data kept, record who ordered it, what is held and until when; pause deletion for those records (including the forensic copies and the audit trail).
