# Control mapping

How the software's controls support three common frameworks. "Supports" means the control helps you meet the requirement; it is **not** a claim that imPress, or your deployment, meets it. Mapping is at chapter or function level: checking individual requirements is a separate exercise ([#207](https://github.com/Kush-Kelaiya22/imPress/issues/207)) and needs evidence from your deployment (configuration, logs, test runs). Not legal advice, not a certification.

## OWASP ASVS 5.0 (chapters)

| ASVS chapter | Supported by | Evidence | Gaps / your part |
|---|---|---|---|
| Encoding and sanitization; Web frontend security | strict CSP (`script-src 'self'`, no inline handlers), quote-escaping of every shown name, `X-Frame-Options`, `nosniff`, referrer policy, `HttpOnly` + `SameSite=Strict` cookie, CSRF header | `ui_tests/test_xss.py`, `ui_tests/test_csp.py`, [security model](../design/security-model.md) | style attributes still need `style-src 'unsafe-inline'` |
| Validation and business logic | typed request models, all-or-nothing imports with row errors, quiz and roster rules | `backend/tests` | |
| API and web service | one permission per route, matrix snapshot reviewed by hand, public routes listed | `test_route_matrix.py`, `test_route_guards.py` | |
| Authentication | salted bcrypt over SHA-256, throttling, one device per account, step-up password for dangerous actions | `test_sessions_v22.py`, `test_hardening.py` | no multi-factor authentication yet (tracked) |
| Session management | opaque server-side sessions (hash stored), idle 5 / 30 min, 6 h hard limit, revocation on account change | [security model](../design/security-model.md) | |
| Authorization | central policy with class-scoped rules, database gateway checking each write per table | [authorization](../design/authorization.md), `test_db_gateway.py` | |
| Cryptography | HMAC-SHA256 row seals, Ed25519 for policy, manifest and exports, RSA-3072 firmware signatures | `test_ed25519.py` (RFC 8032 vectors), `test_gpc.py` | pure-Python Ed25519 is not constant-time: private keys stay in root's tooling |
| Secure communication | HTTPS required for staff; device TLS required in the hardened profile | [production hardening](../guides/production-hardening.md) | device TLS is a board build option; hardware tests open |
| Configuration | two profiles, a hardened floor that refuses insecure start, signed policy and code manifest | `test_gpc.py`, `test_hardening.py` | |
| Data protection | erasure that scrubs the log, retention flags, private permissions on copies, expiry of test data | [retention](retention-schedule.md) | no encryption at rest of copies and backups (tracked) |
| Secure coding and architecture | gateway as a single write checkpoint, dual control for baseline changes | [data integrity](../design/data-integrity.md) | |
| Security logging and error handling | flagged activity entries, external hash-chained trail, alerts to administrators | `test_hardening.py` | log forwarding to your SIEM is yours |

## NIST CSF 2.0 (functions)

| Function | Supported by | Your part |
|---|---|---|
| **Govern** | root-owned policy, roles that must be different people, this toolkit | name owners; approve residual risks ([risk register](risk-register.md)) |
| **Identify** | [data inventory](data-inventory.md), asset list in the security model | keep it current |
| **Protect** | access control, session limits, gateway, signed firmware and policy, TLS, dual control | deploy the hardened profile; protect root's key |
| **Detect** | row seals and 5-minute verification, Degraded alerts, flagged log, code manifest, audit-chain verification | watch the alerts; run `audit-verify` |
| **Respond** | [incident response](incident-response.md), forensic copy before restore, approvals trail | contacts, drills |
| **Recover** | rolling and start-up backups, before-clear copy, restore | off-host backups and restore drills |

## GDPR Article 32 (security of processing), examples

| Measure listed in the Article | Where |
|---|---|
| Pseudonymisation and encryption of personal data | passwords hashed; student identifiers removed from the audit sink and erase entries replaced by a keyed reference; TLS in transit. **Encryption at rest is not provided by the application**: use disk or volume encryption |
| Ongoing confidentiality, integrity, availability and resilience | access control, gateway and seals, automatic repair, dual control |
| Restore availability and access after an incident | backups and the before-a-clear copy; **you** provide off-host backups |
| Regular testing and evaluation | the test suites; your restore, DSAR and incident drills |

## Other articles the software helps with

Rights (Arts. 12 to 22): [rights runbook](dsar-runbook.md). Records of processing (Art. 30): [data inventory](data-inventory.md). Privacy by default (Art. 25): standard profile minimises session data, hardened profile switches off test-data copies. Breach (Arts. 33, 34): [incident response](incident-response.md). DPIA (Art. 35): start from the inventory and the [risk register](risk-register.md); the decision is yours.
