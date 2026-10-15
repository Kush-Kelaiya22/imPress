# Incident response

The first hours of a security incident: something altered the database, a device or an account looks compromised, data may have left the system. Fill in the contact table now, not during the incident. This is a checklist, not legal advice; confirm which notification duties apply to you.

## What will tell you

| Signal | Meaning |
|---|---|
| **Degraded** badge, banner and toast to administrators | the database changed outside imPress and was restored from a backup |
| Flagged entries in the activity log | `system.db_degraded`, `db.write_refused`, `auth.second_sign_in_blocked`, `approval.*`, `system.policy_alert`, `system.clear_*` |
| *A policy file was refused* on the System page | someone changed the signed policy file, or signed it with another key |
| *The server's code differs from the signed manifest* | a file under `backend/app` changed |
| Refused sign-in from a second device | an account is being used from somewhere else |
| An approval request you did not expect | another super admin's account may be misused |

## First hour

1. **Do not reset, clear or acknowledge anything yet.** Resets and acknowledgements destroy evidence and some need approval anyway.
2. **Note the time** you noticed and who noticed. Start a written timeline.
3. **Contain:** end the suspect account's sessions (User access → *End sessions*), deactivate it, change shared secrets if exposed. For a compromised device, disable it on the Devices page (and revoke its key).
4. **Preserve evidence:** copy the forensic database (`forensic-<time>.db` in the backup folder), the external audit file, the server's logs and the policy and manifest files to a read-only location. Run `python -m app.manage audit-verify <file>`: a broken chain tells you where tampering begins.
5. **Assess:** what changed (the alert names the tables), which accounts acted, whether personal data was read or copied (exports, downloads, a stolen backup), and the time window.

## Notify (decide with your privacy lead and counsel)

| If this applies to you | Typical duty | Clock | Who |
|---|---|---|---|
| CERT-In directions (India) | report specified cyber incidents | **6 hours** from noticing | CERT-In, through your designated point of contact |
| GDPR (EU/UK data) | notify the supervisory authority of a personal-data breach unless unlikely to risk people's rights; tell affected people if high risk | **72 hours** from becoming aware | your DPO or lead supervisory authority |
| India DPDP Act and Rules | intimate the Data Protection Board and each affected person of a personal-data breach, in the form and time the Rules prescribe | per the Rules in force for you | the Board; affected people |
| Contracts | processor must tell controller, customers, insurers | per contract | named contacts |

Write what you decided, when, and why, even if the decision is "not reportable".

## Recover

1. Confirm the cause is closed (credentials rotated, vulnerable path fixed, host rebuilt if root was exposed).
2. Restore from the **off-host** backup if the local backups can't be trusted; re-apply erasures made since.
3. Rotate: `IMPRESS_JWT_SECRET` (this reseals the database and signs everyone out), device keys, the audit-sink and webhook secrets, and, if root's key or host was exposed, **root's signing key** (generate a new one and re-sign the policy and the code manifest).
4. Re-run the [production hardening](../guides/production-hardening.md) checks.

## After

Write up what happened, what worked, what was slow; open issues for the fixes; update this page and the [risk register](risk-register.md).

## Contacts (fill in)

| Role | Name | Reachable 24/7 | Phone | E-mail |
|---|---|---|---|---|
| Incident lead | | | | |
| System owner (root) | | | | |
| Privacy lead / DPO | | | | |
| CERT-In point of contact (if applicable) | | | | |
| Hosting or support vendor | | | | |
| Legal counsel | | | | |
