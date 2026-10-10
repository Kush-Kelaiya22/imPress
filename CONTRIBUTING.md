# Contributing to imPress

> **Project contribution and maintenance policy**
> This guide describes how to propose, implement, test, review, merge, document, and release changes to imPress. It also defines how to create, label, maintain, and close GitHub issues. Read the [Code of Conduct](CODE_OF_CONDUCT.md) before participating.

imPress is an open-source classroom response system. Its parts include a FastAPI backend, a browser interface, ESP32-based devices, the communication protocol between them, and deployment and testing tools. A change in one part can affect the others. This guide helps contributors make changes that are clear, safe, traceable, and easy to review.

The process is designed primarily for the project's maintainers, but **contributions are welcome from everyone**. The same quality, security, review, and conduct expectations apply to every contribution, regardless of a person's role or previous involvement. People who clone, modify, or distribute the software are encouraged to follow this guide. Repository maintainers can enforce this workflow for contributions to project-controlled branches and spaces, but this document does not replace the project license or impose control over independent forks.

## Contents

1. [Maintainers, access, and decisions](#1-maintainers-access-and-decisions)
2. [Contribution workflow at a glance](#2-contribution-workflow-at-a-glance)
3. [Before proposing a change](#3-before-proposing-a-change)
4. [Creating high-quality issues](#4-creating-high-quality-issues)
5. [Issue types and required content](#5-issue-types-and-required-content)
6. [Labels: definitions and selection rules](#6-labels-definitions-and-selection-rules)
7. [Triage, assignment, dependencies, and issue maintenance](#7-triage-assignment-dependencies-and-issue-maintenance)
8. [Branch ownership and naming](#8-branch-ownership-and-naming)
9. [Implementation and engineering standards](#9-implementation-and-engineering-standards)
10. [Tests and evidence](#10-tests-and-evidence)
11. [Commits and pull requests](#11-commits-and-pull-requests)
12. [Review, CI, and merge policy](#12-review-ci-and-merge-policy)
13. [Issue closure and reopening](#13-issue-closure-and-reopening)
14. [Version policy and change history](#14-version-policy-and-change-history)
15. [Release process](#15-release-process)
16. [Security, privacy, and responsible disclosure](#16-security-privacy-and-responsible-disclosure)
17. [Documentation and communication](#17-documentation-and-communication)
18. [Maintainer checklists](#18-maintainer-checklists)
19. [Issue and pull request templates](#19-issue-and-pull-request-templates)
20. [Questions and changes to this guide](#20-questions-and-changes-to-this-guide)

---

## 1. Maintainers, access, and decisions

The project maintainers identified for the current development process are:

| Maintainer | GitHub profile |
| --- | --- |
| **Varun Karthic** | [@varunkarthic](https://github.com/varunkarthic) |
| **Kush Kelaiya** | [@Kush-Kelaiya22](https://github.com/Kush-Kelaiya22) |
| **Aamna** | [@aamna-builds](https://github.com/aamna-builds) |
| **encrypted-official** | [@encrypted-official](https://github.com/encrypted-official) |

This list identifies the maintainers for this guide. It does **not** imply that every person has identical repository permissions or must approve every change. GitHub permissions and current branch protection rules determine which actions a person can perform.

Maintainers organize the backlog, review code, safeguard project data, resolve conflicts, and coordinate releases. They should explain decisions, apply rules consistently, and provide clear feedback. Contributors without write access can work through forks and pull requests. Contributors with write access should still use issue branches and pull requests rather than bypassing review.

**Decision principles**

- Prefer evidence over seniority or the number of comments on a thread.
- Give the person responsible for a component a chance to review changes that affect it.
- Use the issue and pull request as the public record of technical decisions. Keep secrets and personal reports private.
- Declare conflicts of interest. When possible, obtain review from someone other than the author.
- A maintainer can reject or defer a change when it creates unacceptable safety, maintenance, security, or compatibility risk. Explain the reason.
- For urgent risks, a maintainer may restrict access, halt a rollout, or revert a change. Record the follow-up once it is safe to do so.

An author must not treat their own approval as independent review. Where a separate reviewer is unavailable, record the limitation and seek another maintainer's review when practicable. Never bypass a configured protection rule.

## 2. Contribution workflow at a glance

A normal contribution follows this sequence:

1. **Find or open an issue.** Describe the problem and define an outcome that can be verified.
2. **Triage the issue.** Choose a type, priority, affected area, and other relevant labels. Confirm scope, owner, and integration target.
3. **Create an issue branch.** Branch from the actual destination integration line, not from an unrelated or stale branch.
4. **Implement and document the change.** Keep the work focused and preserve cross-component contracts.
5. **Test locally.** Run the standard test suite and any additional checks required for the affected components.
6. **Open a pull request.** Link the issue, provide results, and target the correct integration branch.
7. **Review and repair.** Address comments, resolve conflicts, and wait for required CI checks.
8. **Merge after approval.** Confirm the exact target and passing checks before using the agreed GitHub merge method.
9. **Close or update the issue.** Record the merged PR, outcome, limitations, and any follow-up work.
10. **Release separately.** A merge into an integration branch does not, by itself, publish a release.

For a small typo or broken link, a maintainer may accept a simpler issue or PR description. This exception does not remove the need for review, passing applicable checks, or an accurate change-history entry.

## 3. Before proposing a change

Search [open and closed issues](https://github.com/Kush-Kelaiya22/imPress/issues), [pull requests](https://github.com/Kush-Kelaiya22/imPress/pulls), branches, and the relevant pages in [`docs/`](docs/README.md). Look for work that already solves the same problem. A completed or closed issue may also explain why a certain design was chosen.

Before changing code, identify:

- **The problem:** What is wrong, missing, confusing, or difficult to maintain?
- **The user or operator impact:** Who is affected, and under what conditions?
- **The source of truth:** Which component owns the behavior or constraint?
- **Affected interfaces:** Does the change affect REST endpoints, database schema, browser state, WebSockets, firmware messages, hardware, packaging, or deployment?
- **Compatibility:** Must older devices, stored records, existing operators, or older deployments continue to work?
- **Dependencies:** Does another issue have to land first?
- **Verification:** How will reviewers know the change works, including failure cases?

A proposal is easier to review when it separates confirmed facts from assumptions, proposed solutions, and open questions. A requested feature is not an approved design merely because it has an issue number. Discuss high-risk architectural or device changes before implementation.

Do not create a public issue with passwords, live credentials, personal classroom records, firmware signing keys, private messages, or exploit details. Follow [Section 16](#16-security-privacy-and-responsible-disclosure).

## 4. Creating high-quality issues

### 4.1 When an issue is expected

Open an issue for defects, features, security hardening, documentation gaps, refactors, test infrastructure, deployment changes, hardware work, and tasks that need coordination. Prefer one issue for one independently testable outcome. Large initiatives may use a tracking issue with linked child issues.

An issue is a **record of a problem and the definition of done**, not only a task title. The proposed implementation may change after investigation, but the expected result should remain clear. Do not copy a long generated diagnosis into an issue without checking its claims against code or tests.

### 4.2 Recommended title format

Use a concise, searchable title:

```text
<type>(<optional-area>): <specific problem or desired outcome>
```

Examples:

```text
fix(quiz): timed quizzes remain on the first question
feat(ota): add staged firmware deployment with rollback
security(device): require per-device authentication
refactor(database): isolate migration responsibilities
test(ui): cover navigation races in the browser
docs(firmware): document device recovery steps
chore(ci): repair failing firmware host tests
```

Use the title to say **what** needs attention. Avoid vague titles such as `Bug`, `Improve code`, `Not working`, or `Urgent`. The title prefix helps readers, but **labels are the authoritative issue classification**.

### 4.3 Standard issue body

For nontrivial work, use these headings. Mark fields `Not applicable` and briefly say why when they do not apply. Do not invent a root cause, severity, or test result.

1. **Summary / type:** A short statement of the issue.
2. **Impact and severity:** The real or likely effect, not an unsupported claim.
3. **Priority and reason:** Why this belongs at P0, P1, P2, or P3.
4. **Affected components:** Relevant paths, modules, devices, versions, or environments.
5. **Current behavior:** Observed state, with evidence when available.
6. **Expected behavior:** The specific correct or desired state.
7. **Steps to reproduce:** Required for reproducible bug reports; see below.
8. **Technical context / investigation:** Relevant logs, code references, limitations, and unknowns.
9. **Proposed approach:** Optional for initial reports; distinguish proposals from decisions.
10. **Dependencies and blockers:** Link issues or PRs and state what is blocked.
11. **Compatibility and risks:** Security, privacy, data migration, API, UI, and device effects.
12. **Test plan:** Checks needed to establish correctness, including regressions.
13. **Acceptance criteria:** Observable, testable completion conditions.
14. **Rollback or recovery:** Required when the change can affect data, deployments, firmware, or core flows.
15. **Documentation requirements:** The pages or examples that must change.
16. **Integration target / owner:** The intended branch and the responsible contributor, if assigned.

Screenshots, logs, traces, sample requests, and device output can help. Remove or replace private data before posting them.

### 4.4 Reproduction rule for bugs

**A bug report must include steps to reproduce the problem.** Supply the environment, setup, input or event sequence, observed result, and expected result. When the problem is intermittent, also give the observed frequency and the last known occurrence. Add a minimal example or a failing test when possible.

An effective report allows another contributor to follow the same steps without asking for essential missing information:

```text
Environment: branch/commit, OS/browser, backend version, hardware/firmware
Preconditions: user role, test database, connected board, sample quiz
1. Start the service using the documented test setup.
2. Create a quiz with two questions and a 10-second per-question timer.
3. Start the quiz and wait more than 10 seconds.
Observed: question 1 remains active; no automatic advance occurs.
Expected: the next question becomes active when the timer expires.
Evidence: safe log excerpt, screenshot, or failing test (if available).
```

**If a report lacks usable reproduction steps**, a maintainer may request them and label or comment that more information is needed. If the reporter cannot provide the necessary information, and maintainers cannot reproduce or independently verify the defect after reasonable investigation, the issue **may be closed as not reproducible / not actionable** with an explanation. It can be reopened when new evidence is available.

Do **not** label a report invalid merely because it reproduces only on hardware that maintainers do not currently have. Ask for logs or arrange a device test. Also distinguish a traditional runtime bug from a security design gap, accessibility barrier, or destructive intermittent failure. When reproducing it would be unsafe, damaging, privacy-invasive, or would disclose an exploit, document a safe verification plan instead and keep sensitive details out of public issues. The exception must be explained; `N/A` alone is insufficient.

### 4.5 Acceptance criteria

Write acceptance criteria as observable results, not vague tasks. Examples:

- The API refuses a fifth answer choice, and a contract test verifies device limits.
- A stale page request cannot overwrite the most recent browser navigation.
- An interrupted firmware transfer leaves the device able to start or recover.
- A documented command succeeds on a clean supported environment.

Avoid criteria such as `works properly`, `fix everything`, `tested`, or `no bugs`.

## 5. Issue types and required content

### 5.1 Bug or regression

Use **`type:bug`** (and the relevant area, priority, and severity labels). Describe the failing behavior before suggesting a fix. Include:

- Preconditions, exact reproduction steps, actual versus expected behavior, version/commit, and evidence.
- Whether the failure is consistent, intermittent, environment-specific, or a regression.
- Impact on users, classes, devices, data, or deployments.
- A root-cause hypothesis clearly marked as such, or `Not yet established`.
- A regression test plan that fails before the fix and passes after it, where feasible.
- Rollback and migration notes when the fix changes persisted state or device behavior.

A fix is complete when the cause or failure mode is addressed, acceptance criteria pass, and appropriate regression coverage is present. Hiding an error message, disabling the affected feature, or adjusting only a UI control may not fix the underlying problem.

### 5.2 Feature or enhancement

Use **`type:feature`**. Define the user need, expected workflow, inputs, outputs, permissions, failure states, and scope limits. Explain why the current system is insufficient. Include API/firmware/database impacts, backwards compatibility, documentation updates, and measurable acceptance criteria. Split large features into reviewable subtasks and establish dependency order.

`enhancement` is a legacy/default GitHub label; prefer `type:feature` for new feature proposals. Do not apply both unless maintainers are intentionally maintaining legacy compatibility.

### 5.3 Documentation

Use **`type:documentation`**. Link the inaccurate or missing page; quote or summarize the specific problem, explain the intended reader, and define what must be added, corrected, or removed. Check that commands, paths, API names, screenshots, links, and examples match the real repository. Documentation-only PRs still need checks and a change-history entry.

`documentation` is a default/legacy label. Prefer `type:documentation` for new issues rather than duplicating the classification.

### 5.4 Security

Use **`type:security`** for public, non-exploitable hardening tasks. Explain the affected trust boundary, impact, desired security property, rollout constraints, and safe verification plan. Separate confirmed vulnerabilities from possible risks and design improvements. If the report contains a practical exploit, secret, sensitive configuration, or information that increases risk, **do not publish it as a public issue**. Contact a maintainer privately or use GitHub's private vulnerability reporting where enabled.

`security` is a default/legacy label; prefer `type:security` for ordinary public security work. A sensitive report may not receive a public label until coordinated disclosure is appropriate.

### 5.5 Refactor and maintenance

Use **`type:refactor`** when restructuring internals without intending to change behavior. State the code health problem, preserved contracts, affected modules, and test strategy. Any intended user-visible change should be separated or called out explicitly. For packaging, dependency updates, build tools, or configuration maintenance, describe the task as `chore(...)` in the title; use relevant area and priority labels. No `type:chore` label is assumed to exist.

### 5.6 Testing and CI

Use **`testing`** when the main purpose is tests, coverage, fixtures, or test infrastructure. Add **`area:devops`** for CI/CD or test tooling. Describe the gap, the test level, required dependencies, expected failure signal, and the evidence that the new test actually exercises the intended behavior. A test-only change may be titled `test(...)`; do not invent an unavailable `type:test` label.

### 5.7 Hardware and firmware

Use **`hardware`** for physical-device, electrical, module, or hardware-communication work; **`area:firmware`** for ESP32 software changes; use both when both are central. State the board variant, toolchain, wiring or power assumptions, protocol versions, expected resource limits, and physical safety or recovery risks. Distinguish simulations and host tests from direct board tests.

Add **`needs:hardware`** only when final verification needs physical devices that have not yet been tested. State exactly which board and scenario are outstanding. Remove the label after verification is recorded or keep it with a linked follow-up if integration is permitted before hardware validation.

### 5.8 Accessibility and questions

Use **`accessibility`** for barriers affecting people with disabilities. Describe the task, impact, input method, environment, and expected accessible behavior; do not require a person to disclose private medical information.

Use **`question`** for information requests that do not yet define actionable work. Convert or link the discussion to a properly scoped issue if it reveals a confirmed defect or approved change.

## 6. Labels: definitions and selection rules

The repository currently contains both structured labels and standard GitHub labels. **For new actionable issues, structured `type:*`, `area:*`, `priority:*`, and `severity:*` labels are preferred wherever an exact match exists.** Default labels remain valid for older issues and special cases. Do not relabel old closed issues only for appearance unless there is a practical need.

### 6.1 Classification rules

1. Choose **one primary type** where a suitable `type:*` label exists. An issue can touch many parts but should have one main purpose.
2. Choose **one priority** for actionable work. Priority controls scheduling; it does not measure severity.
3. Choose **zero or one severity** label for a confirmed defect or security impact. It is usually unnecessary for documentation, features, or questions.
4. Choose **all affected areas that materially require changes or review**, not every directory that the reporter mentions.
5. Add workflow and special labels only when their conditions are true. Remove stale labels as work advances.
6. Do not add conflicting priorities, multiple severities, or both structured and default labels for the same classification without a specific reason.
7. Never use label color as the source of meaning. Use the text definition.

### 6.2 Primary type and default labels

| Label | When to use it | Notes |
| --- | --- | --- |
| `type:bug` | Confirmed or credible incorrect behavior | Preferred over `bug` for new issues. |
| `type:feature` | New user- or operator-facing capability | Preferred over `enhancement`. |
| `type:documentation` | Missing, inaccurate, or unclear guidance | Preferred over `documentation`. |
| `type:refactor` | Internal structure change with no intended behavior change | Verify preserved behavior. |
| `type:security` | Public security hardening or safely disclosed fix | Never expose exploit details to satisfy a template. |
| `bug` | Existing legacy bug reports | Avoid pairing with `type:bug` on new issues. |
| `enhancement` | Existing feature requests | Prefer `type:feature` for new issues. |
| `documentation` | Existing docs issues | Prefer `type:documentation` for new issues. |
| `security` | Existing security issues or broad security classification | Prefer `type:security` for new issues. |
| `question` | Clarification or information request | May not need a `type:*` label. |

`hardware` and `testing` are **topic labels**, not automatic substitutes for a type. When no matching `type:*` label exists (for example, a standalone hardware specification task or test-infrastructure task), use the relevant topic, area, priority, and a clear title such as `hardware:` or `test:`. Maintainers may expand the taxonomy later through an agreed issue.

### 6.3 Area labels

| Label | Scope |
| --- | --- |
| `area:backend` | FastAPI routes, authentication, services, backend logic, server-side contracts. |
| `area:frontend` | Browser pages, JavaScript, layout, navigation, UI behavior, accessibility implementation. |
| `area:firmware` | ESP32 application code, OTA clients, device state machines, board-specific firmware behavior. |
| `area:database` | Schema, migrations, constraints, persistence, data integrity, stored-state compatibility. |
| `area:devops` | CI/CD, packaging, automation, build/release tooling, install scripts, deployment pipelines. |

Multiple area labels are justified when the implementation crosses boundaries. A device-protocol issue may need `area:backend` **and** `area:firmware`. A migration defect may need `area:database` **and** `area:backend`. A docs-only issue does not need an area label unless it concerns a specific component and that classification helps triage.

### 6.4 Priority versus severity

**Priority** answers: *When should the project act?* **Severity** answers: *How harmful is the actual defect or vulnerability?* A severe issue may have a lower immediate priority if the vulnerable configuration is not deployed; a moderate issue may have high priority if it blocks planned classroom use. Document the reason rather than assuming the values must match.

| Label | Meaning | Typical action |
| --- | --- | --- |
| `priority:P0` | Critical; blocks safe operation | Stop affected rollout, evaluate immediate mitigation, assign promptly. |
| `priority:P1` | Major defect in important functionality | Schedule near-term investigation and repair. |
| `priority:P2` | Standard planned work | Triage and deliver in the agreed iteration. |
| `priority:P3` | Low-risk or lower-impact improvement | Maintain in the backlog; bundle when appropriate. |

| Label | Meaning | Example |
| --- | --- | --- |
| `severity:critical` | Crash, data loss, broken core flow, or comparable severe impact | System unusable for an active class or unrecoverable records. |
| `severity:high` | Major functional or security impact | Critical device function fails under a supported workflow. |
| `severity:medium` | Real defect with limited or conditional impact | A navigation race affects a subset of actions. |
| `severity:low` | Minor defect | Cosmetic or limited non-critical behavior error. |

Consider scope, frequency, reachability, affected roles, data sensitivity, available mitigation, and recovery cost. Do not rate severity solely by frustration or by the number of lines changed. If impact is unknown, say `Impact under investigation` in the issue body and add a severity label after triage.

### 6.5 Workflow and special labels

| Label | Apply when | Remove or update when |
| --- | --- | --- |
| `status:blocked` | Progress is stopped by a stated external dependency or prerequisite | The dependency is resolved; explain what changed. |
| `needs:hardware` | Physical board testing is necessary and not yet complete | Verified on the documented hardware, or transfer the outstanding work to a linked issue. |
| `hardware` | Hardware design, board behavior, electrical or module interface is central | Keep while the issue remains about hardware. |
| `testing` | Tests, quality coverage, or test infrastructure are central | Keep for that workstream. |
| `accessibility` | The task relates to an accessibility barrier or improvement | Keep as a topic label. |
| `good first issue` | Scope is bounded, instructions are clear, and project context is manageable | Remove if the task becomes complex or high-risk. |
| `help wanted` | Maintainers welcome additional contributors | Remove when the work is assigned and no further help is needed. |
| `duplicate` | Another existing issue covers the same problem | Close with a link to the canonical issue. |
| `invalid` | The report is out of scope, incoherent, or cannot be actioned after clarification | Close with a clear reason; not a judgment about the reporter. |
| `wontfix` | A valid request is deliberately not planned or accepted | Close with a design, maintenance, safety, or scope reason. |
| `question` | Additional information or explanation is the primary purpose | Close after a satisfactory answer or convert to actionable work. |

`invalid` is not the default for an intermittent or hardware-only bug. `wontfix` does not mean `not yet scheduled`. `duplicate` should point to an actual canonical issue, not a vaguely related report.

### 6.6 Examples of consistent labeling

| Issue | Recommended labels | Why |
| --- | --- | --- |
| Quiz timer fails to advance | `type:bug`, `area:backend`, `area:frontend`, `priority:P1`, `severity:high` (if confirmed) | Defect crossing application layers. Add `area:firmware` only when that device behavior is in scope. |
| Add CSV question import | `type:feature`, `area:backend`, `area:frontend`, `priority:P2` | New user workflow. |
| Add firmware rollback | `type:feature`, `area:firmware`, `area:backend`, `priority:P1`, `needs:hardware` if pending | Cross-system capability with physical verification. |
| Correct recovery guide | `type:documentation`, `priority:P3` | Docs-only change. |
| Repair CI environment | `area:devops`, `testing`, `priority:P1` | Tooling/test-infrastructure task without an invented type label. |
| Database migration drops data | `type:bug`, `area:database`, `area:backend`, `severity:critical`, `priority:P0` | Serious data integrity failure. |
| Improve keyboard navigation | `type:feature` or `type:bug`, `area:frontend`, `accessibility`, priority based on impact | Choose type from existing expected behavior. |

These are **examples**, not automatic assignments. Triage must use the evidence from the actual issue.

## 7. Triage, assignment, dependencies, and issue maintenance

### 7.1 Initial triage

A maintainer or designated issue owner should:

1. Check for duplicates and existing PRs.
2. Confirm that the problem belongs to imPress and that the report has enough detail.
3. Ask for missing reproduction steps on bug reports.
4. Check that no personal information or unsafe security detail is exposed.
5. Choose the primary type, relevant areas, priority, and severity if applicable.
6. Identify a likely owner, target branch, dependencies, and blocked state.
7. Record questions or decisions in an issue comment so the next contributor can understand them.

Do not assign another contributor without considering availability and agreement. An unassigned issue is acceptable. The reporter and implementer need not be the same person.

### 7.2 Parent issues, subtasks, and dependencies

Use a parent tracking issue when a feature is too large for one reviewable PR. Define the overall goal and link separate tasks with independent acceptance criteria. A task is **blocked by** another only when it cannot safely proceed without it. Use GitHub's issue relationships where available and repeat important dependencies in the body.

A parent issue does not become complete merely because one subtask merges. Update progress after each merged PR. Close the parent only when the agreed overall acceptance criteria are met, or formally revise its scope and link deferred work.

### 7.3 Keeping issues useful

Update an issue when investigation changes the root-cause hypothesis, scope, priority, dependencies, test plan, or acceptance criteria. Add short dated comments for major decisions, failed approaches, or test findings. Avoid dozens of comments that repeat the same status. Use links to commits, PRs, CI runs, and follow-up issues rather than copying large logs.

When a contributor stops work, leave a handoff comment that identifies the branch, current state, known failures, and next steps. Remove an incorrect assignment or blocked label when circumstances change. A closed issue remains useful as part of the project history; do not erase evidence to make the issue appear simpler.

### 7.4 Handling inactivity

A maintainer may ask for an update on a dormant issue or PR. If it is no longer actionable, is superseded, or lacks required information after a reasonable opportunity to respond, close it with a factual explanation and a clear path to reopening. **Do not impose an arbitrary closure deadline on high-risk security, intermittent, or hardware-dependent reports.**

## 8. Branch ownership and naming

### 8.1 One issue branch per independently reviewable change

Create a fresh branch from the destination integration branch. Use lowercase kebab-case:

```text
feat/v2.1-short-name
fix/v2.1-short-name
docs/v2.1-short-name
test/v2.1-short-name
chore/v2.1-short-name
refactor/v2.1-short-name
security/v2.1-short-name
```

For example:

```text
fix/v2.1-quiz-timer
feat/v2.1-firmware-rollout
test/v2.1-navigation-race
docs/v2.1-hardware-recovery
```

Use `fix/` for defects, `feat/` for features, `docs/` for documentation, `test/` for test-only work, and `chore/` for maintenance. The version segment identifies the **target development line**, not the issue number or final published product version. Reference the issue in the PR and, if useful, branch description.

Older branches may use formats such as `fix/10-role-escalation`. Preserve relevant history, but use the current convention for new work.

### 8.2 Integration lines and ancestry

The current v2.1 integration target is **`varun/v2.1`**. The v2.1 changelog
records that line as developed from the shared `v2` baseline, and recent
feature, fix, and documentation PRs target it. Do not assume `main` is the
target for v2.1 changes. Confirm the current target and any branch protection
requirements on GitHub before branching or merging.

Owner-scoped integration lines may include:

```text
varun/v2.1
kush/v2.1
aamna/v2.1
encrypted/v2.1
```

These are naming examples, not a claim that all four branches exist. Choose only an authorized owner namespace. Do not create, rename, force-push, or merge into another person's integration line without agreement.

A version-line suffix indicates **branch ancestry**. A line created from the shared `v2` baseline can be `{owner}/v2.1`; a successor deliberately based on that `v2.1` line can be `{owner}/v2.2`, then `{owner}/v2.3`. Do not name a branch for another contributor's newest line if that is not its actual ancestor. Record the source branch and commit when a new line is created. Optional variant suffixes, such as `{owner}/v2.1-experimental`, are for clearly documented variants and do not grant release status.

**Branch iteration and product release version are separate concepts.** See [Section 14](#14-version-policy-and-change-history).

### 8.3 Safe Git workflow

From a checked-out repository, replace `<target-branch>` with the agreed integration branch:

```sh
git fetch origin
git switch <target-branch>
git pull --ff-only origin <target-branch>
git switch -c fix/v2.1-short-name
```

If you contribute through a fork, fetch the canonical repository from an `upstream` remote and push the issue branch to your own fork. Check your actual remote configuration before running commands. Do not copy and paste a command with a placeholder unchanged.

- Never commit directly to a shared integration branch as the normal workflow.
- Never force-push a shared integration or release branch.
- Keep unrelated issues in separate branches and PRs.
- Before resolving conflicts, fetch the latest target and check which commits belong to each side.
- Use merge or rebase for a private issue branch as appropriate. Coordinate before rewriting commits others depend on.
- Do not move a branch's target after review without explaining the change and rerunning the relevant checks.

## 9. Implementation and engineering standards

Make the **smallest complete change** that satisfies the issue. Small does not mean incomplete: update every component needed to preserve the system's contracts.

### 9.1 Backend and authorization

Keep permission checks, input validation, deadlines, state transitions, and data protection at the authoritative backend layer. A hidden button or a client-side check cannot enforce security. Use consistent error responses and explicit failure handling. Test permitted and denied actions, not only successful requests.

### 9.2 Frontend and user experience

Follow established UI patterns and avoid parallel designs for the same control. Verify loading, error, empty, delayed, and repeated-action states. Prevent stale responses from overwriting more recent user actions. Consider keyboard access, focus, contrast, readable messages, and responsive layouts when they apply.

### 9.3 Database and persisted state

For schema changes, use a versioned migration; preserve existing data and verify upgrade behavior. Document changes in uniqueness, foreign keys, defaults, and deletion policy. Do not silently reset a real database to make tests pass. Test from a clean database and from a representative earlier supported schema when applicable.

### 9.4 Device protocol and firmware

Review the backend, gateway, hub, and student-device behavior together. Keep producers and consumers consistent with [`firmware/protocol`](firmware/protocol) and the committed contract fixture, as explained in [design decision D5](docs/design/decisions.md#d5-the-backend--firmware-json-contract-is-a-committed-fixture).

Check message sizes, option counts, text encoding, timing, resets, watchdogs, reconnects, memory limits, and older firmware compatibility. For OTA changes, test interrupted downloads, incorrect images, failed boots, rollback, and power loss where safe. Never claim a physical hardware test when only a host test, emulator, or CI build ran.

### 9.5 Dependencies and build reproducibility

Use existing libraries and project conventions when suitable. Explain why a new dependency is needed. Update manifest and lock files together. Do not introduce unnecessary tooling, committed binaries, generated databases, test secrets, personal environment files, or machine-specific paths. A clean setup should behave like the documented setup.

### 9.6 Security impact

Use least-privilege access and safe default configurations. Protect signing material, credentials, device identifiers, and classroom records. Preserve secure failure behavior. Treat signing, transport security, credential revocation, and device enrollment as distinct controls; passing an integrity hash alone does not prove image authenticity.

## 10. Tests and evidence

Testing is part of implementation, not a final optional step. Add focused tests for new behavior and regression tests for repaired behavior. Test error paths, boundary inputs, authorization, concurrency, disconnections, and restart recovery as appropriate.

### 10.1 Required local checks

The supplied contributor guide identifies this root-level runner as the required standard pre-push test:

```sh
python run_tests.py
```

Run the complete default suite and read its report. A **skipped** suite is not a passing suite. If the current branch changes the runner or its requirements, follow the verified instructions from `python run_tests.py --help` and [`docs/guides/testing.md`](docs/guides/testing.md).

Additional suites identified by the existing documentation are:

```sh
python run_tests.py --with-frontend
python run_tests.py --with-ui
python run_tests.py --with-idf
```

```sh
python run_tests.py --list
python run_tests.py --help
```

Run the additional suites that apply to the change and that your environment supports. In the PR, state which were not run and why. If the repository's current CI requires more checks, those are required as well.

### 10.2 Minimum evidence by change type

| Change | Expected evidence |
| --- | --- |
| Backend/API | Unit and integration tests for routes, validation, auth, errors, and persisted behavior. |
| Frontend | Browser test or documented manual steps for the changed workflow and key edge states. |
| Database | Migration tests and verification that representative existing data is preserved. |
| Protocol | Contract test for frame fields, serialization, parsing, and compatible consumers. |
| Firmware | Host/structural tests, builds for affected targets, and hardware verification where needed. |
| Security | Negative tests, safe verification of the claimed property, and controlled release notes. |
| Docs | Correct links, paths, command examples, anchors, and docs checks. |
| CI/deployment | Clean-environment run and evidence that the intended job or deployment path succeeds. |

When practical, demonstrate that a regression test fails on the old behavior and passes after the fix. This strengthens the link between the report and the implementation.

### 10.3 Hardware verification status

Use one of these explicit phrases in the PR and issue:

- **Hardware verified:** State the board, firmware revision, procedure, result, and date.
- **Hardware not run:** State the reason, the required hardware, and the outstanding checks.
- **Hardware not applicable:** Explain why software-only verification covers the change.

A green CI build proves that the configured CI checks completed. It does **not** prove that a device has booted, connected, deployed an update, or recovered on real hardware. If hardware validation is a required acceptance criterion, do not close the issue as fully verified until it is completed. If maintainers accept a narrower software milestone, document that decision and open a linked issue for the remaining hardware verification.

### 10.4 Test failures and CI evidence

**Do not knowingly push failing code as ready for review.** If a failure is known, investigate and correct it before marking the PR ready. When a failing branch must be pushed to collaborate on diagnosis, mark the PR as a **draft**, explain the failure, and do not request a merge.

Do not make a failing suite green by deleting assertions, reducing coverage, hiding exit codes, or skipping tests without technical justification and approval. Link the final CI run for the reviewed commit, not a previous run that passed on different code.

## 11. Commits and pull requests

### 11.1 Commit subjects

Use a concise Conventional Commit-style message:

```text
feat(quizzes): support automatic question advancement
fix(auth): enforce answer deadlines on the server
test(ui): cover stale navigation responses
docs(ota): explain failed-update recovery
chore(ci): pin the firmware build toolchain
refactor(db): simplify migration execution
```

Each commit should have a coherent purpose. Avoid unrelated formatting churn or generated files. Use a detailed body for complex work and reference the issue in the PR.

### 11.2 Opening a PR

Open the PR **into the agreed integration branch**. Use a descriptive title and link the issue, usually with `Refs #123` while work is in progress. Use `Fixes #123` or `Closes #123` only when the PR fully satisfies that issue and GitHub's automatic closure behavior is appropriate for the actual target branch; otherwise close it manually after confirming the merge.

A PR description should include:

- Linked issue, objective, and approach.
- Important files and system behavior changed.
- What remains unchanged, limitations, and out-of-scope work.
- Compatibility, migrations, deployment, security, and rollback concerns.
- Tests **actually run**, exact commands, results, and final CI link.
- UI screenshots or hardware evidence where useful.
- Documentation and change-history updates.
- Outstanding verification or linked follow-up issues.

Open a **draft PR** for early design feedback or incomplete work. Do not call a draft ready merely because some tests pass.

### 11.3 Documentation within the PR

Update the relevant files in `docs/`, API specifications, hardware guides,
firmware guides, deployment guides, README, or repository policy pages in the
same PR as the behavior they describe. Add a concise entry to
[Unreleased changes](#unreleased-changes) in this file for **every merged PR**,
including documentation, tests, configuration, and maintenance.

## 12. Review, CI, and merge policy

### 12.1 Review standards

Reviewers examine correctness, security, maintainability, test quality, scope, compatibility, documentation, and change-history accuracy. Ask specific questions and explain requested changes. Authors should reply with evidence or a reasoned alternative, not silently dismiss concerns.

Prefer review from a maintainer other than the author. Ask a relevant component owner for review when firmware, authentication, database migrations, or release infrastructure are affected. Comply with whichever branch protection, CODEOWNERS, required checks, and review thresholds are actually configured on GitHub. This guide does not claim settings that have not been verified.

### 12.2 Conditions before merge

A PR is ready to merge only when:

1. The issue is linked and the agreed acceptance criteria are met or explicitly scoped down.
2. The target integration branch is correct.
3. The diff contains no unrelated changes, secret data, or accidental generated files.
4. The latest reviewed commit has passed all required CI checks; no required job is pending, cancelled, or failing.
5. Required local and component-specific tests have run, or approved exceptions are documented.
6. Relevant documentation and this document's Unreleased entry are updated.
7. Required reviewer approvals have been obtained; unresolved substantive requests are addressed.
8. Conflicts are resolved and checks have been rerun against the final code.
9. Migration, deployment, device compatibility, and rollback concerns are documented where relevant.
10. No unresolved safety or security concern makes the merge inappropriate.

A passing test suite does not override a valid security concern. Likewise, a review approval does not override failing required CI.

### 12.3 Merge method

Use the normal GitHub pull request merge interface and the method agreed for the target line. A **squash merge** is usually suitable for a single focused issue, while a **merge commit** may preserve useful history for a coordinated series. A rebase merge may be used when repository policy allows it. Do not rewrite protected history to make a PR appear merged.

Before pressing Merge, confirm the **base and head branches** in the PR. After merging, verify that the merge or squash commit appears on the intended integration branch. Delete the issue branch when it is no longer needed and safe to remove. Do not delete an independently maintained integration line or another contributor's branch without agreement.

### 12.4 Failed CI and merge conflicts

When CI fails, find the earliest meaningful error and determine whether it comes from the change, existing baseline, flaky test, or external tooling. Do not assume `flake` without evidence. Fix the problem, rerun local tests, push to the same issue branch, and wait for **new** CI results.

When the target branch has changed, merge or rebase it into the issue branch according to the branch's collaboration needs. Resolve conflicts deliberately, especially in migrations and Unreleased changes. Verify that entries from **both** PRs remain. A clean conflict resolution is not proven safe until tests pass.

### 12.5 Emergency fixes and reverts

For a confirmed P0 or urgent security risk, a maintainer may coordinate an accelerated fix or revert. Use a traceable issue/PR where safe, keep checks and independent review to the greatest feasible extent, and document any exception. A bypass is not justified solely by a deadline. After an emergency action, record the cause, decision, affected releases, and prevention work.

## 13. Issue closure and reopening

**An issue should not be closed as completed solely because code was written, pushed, or a PR was opened.** Completion normally requires that the accepted change has merged into the intended integration branch, or that the issue's deliverable has otherwise been explicitly verified.

### 13.1 Completed

Before closing as completed:

1. Verify that the PR is **merged**, not just approved or green.
2. Confirm the merge landed in the stated target line.
3. Compare the final implementation with the issue's acceptance criteria.
4. Check linked dependencies and remaining subtasks.
5. Record tests, CI evidence, documentation changes, and important limitations.
6. If hardware acceptance is incomplete, do not claim physical verification. Keep the issue open or formally split out a linked follow-up and explain the reduced completion scope.
7. Add a closing comment that links the merged PR and identifies any follow-up work.
8. Select GitHub's appropriate closure reason, such as **Completed**, when available.

**Recommended completed comment:**

```text
Implemented and merged in PR #<number> into <integration-branch>.

Delivered:
- <verified outcome 1>
- <verified outcome 2>

Verification:
- Local: <commands and results>
- CI: <link to final successful run>
- Hardware: <verified / not run / not applicable, with details>

Documentation: <updated files>
Remaining work: <none or linked follow-up issues>
```

### 13.2 Duplicate, not planned, and invalid

Use these distinctions:

| Decision | When appropriate | Required closure note |
| --- | --- | --- |
| **Duplicate** | Another issue tracks the same root problem or outcome. | Link the canonical issue and explain the overlap. |
| **Not planned / `wontfix`** | Valid request, but the project deliberately declines it. | State the technical, scope, maintenance, security, or design reason. |
| **Invalid / not actionable** | Out of scope or essential facts remain unavailable after reasonable clarification. | Say what is missing and how to submit a useful new report. |
| **Resolved without a code change** | Configuration, documentation, or an already deployed fix explains the outcome. | State the resolution and evidence. |
| **Superseded** | A newer design or tracking issue replaces the work. | Link the replacement and identify transferred acceptance criteria. |

Use GitHub's available state-reason options, which may be broader than the local label names. A closed issue can be valid and well reported even if the maintainers choose not to implement it.

### 13.3 Reopen when warranted

Reopen an issue when the linked PR failed to merge, the failure persists in the claimed target, acceptance criteria were not satisfied, new reproduction evidence is available, or a regression reappears with the same root cause. If the new problem is materially different, create a new issue and cross-link it instead. Add a short comment explaining **what changed** since closure.

Repository issue history illustrates an important case: a UI fix issue was
reopened while its pull request was still blocked by merge conflicts, then
closed after the merge landed. This is the correct distinction between
**implemented on a branch** and **integrated into the project**.

## 14. Version policy and change history

This section is the source of truth for the contributor-facing version policy
and change history. The root [`VERSION`](VERSION) file remains the
machine-readable product version used by the application.

### 14.1 Version format and source of truth

The application and firmware use three numeric components:

```text
MAJOR.MINOR.PATCH
```

Examples: `2.1.0`, `2.2.0`, `2.2.1`.

- **MAJOR:** An agreed major transition or compatibility break.
- **MINOR:** A new non-major product line or agreed feature release.
- **PATCH:** A maintenance release or correction on an existing product line, when approved by the release owner.

The release owner determines the actual next version based on compatibility and the planned release. Do not increment versions once per commit, branch, or issue. A version-line branch is a **development lineage**, not an automatically published product release.

### 14.2 Verified repository state

| Item | Documented state |
| --- | --- |
| Product version | `2.1.0` in root `VERSION`, checked 2026-10-09 |
| Current v2.1 integration line | `varun/v2.1`, fetched and checked 2026-10-09 |
| Version-line ancestry | The v2.1 changelog records `varun/v2.1` as developed from `v2` |
| Firmware versions | `firmware/class_c6/version.txt`, `firmware/class_s3/version.txt`, and `firmware/student/version.txt` each contain `2.1.0`, checked 2026-10-09 |
| Published GitHub releases and tags | None were listed by GitHub when checked 2026-10-09 |

This is a dated repository snapshot, not a promise that these values remain
current. Verify the root version, target branch, firmware version files, tags,
and GitHub Releases again before preparing a release. A recorded version or
integration branch is not proof of a published release.

### 14.3 Firmware version consistency

When `VERSION` changes, update **all three** `firmware/<project>/version.txt` files to the same version, even if one firmware project's code did not change. Follow [`docs/firmware/FIRMWARE_VERSIONING.md`](docs/firmware/FIRMWARE_VERSIONING.md) and the repository's consistency checks. A version bump should be performed by the coordinated release change, not each feature PR.

### 14.4 Recording changes

**Every merged PR needs a concise entry in Unreleased changes.** This includes fixes, features, test-only changes, documentation, refactors, configuration, build changes, and maintenance tasks. Add the entry in the PR before merge and preserve concurrent entries while resolving conflicts.

Write changes in past tense or as clear completed outcomes. Describe the effect and link the PR or issue. Do not record speculative features as delivered. A changelog entry does not prove that hardware verification occurred or that a release was published.

#### Unreleased changes

Keep this section accurate as changes merge. Record a concise completed outcome
and link to its issue or pull request. Do not describe a proposal as delivered.
This section is a change history; it does not assert that a GitHub release or
tag exists.

- **Documentation ([PR #74](https://github.com/Kush-Kelaiya22/imPress/pull/74)):** Added the GitHub wiki link to the README and integrated the initial contribution guidance, version policy, and Code of Conduct.
- **Governance ([PR #75](https://github.com/Kush-Kelaiya22/imPress/pull/75)):** Expanded the contributor handbook with issue triage, labels, branch ownership, review, testing, and release guidance; strengthened the Code of Conduct; consolidated version history and removed the separate version-policy document.
- **Documentation ([#79](https://github.com/Kush-Kelaiya22/imPress/issues/79)):** Rewrote the README architecture diagram and two other flowcharts in portable mermaid syntax so they render on GitHub; fixed two state diagrams that failed on mermaid 10; listed migration steps 4–7 in the database migration guide; linked the governance entry to PR #75.

#### Recorded product version and development history

This table records repository history. It is **not** a list of published GitHub
Releases. GitHub had no published releases or tags when checked on 2026-10-09.

| Recorded version or line | Source / integration line | Notes |
| --- | --- | --- |
| `2.1.0` | `v2` → `varun/v2.1` | Current value in `VERSION` at the 2026-10-09 check. The [v2.1 changelog](docs/reference/changelog-v2.1.md) records the integration lineage. No published release or tag was found at that check. |
| `2.0` | `v2` | Prior development line described in the [v2 changelog](docs/reference/changelog-v2.md) and README release history. No published release or tag was found at the check above. |
| `1.x` | `main` | Historical line described in the README. This records project history, not a published release. |

When a GitHub release is published, add its verified version, exact tag, date,
compatibility notes, and link to the real release. Do not invent release dates
or convert a development line into a release claim.

### 14.5 Branch-line numbering versus product numbering

A branch such as `varun/v2.2` may be the next iteration derived from `varun/v2.1`. It does not automatically mean that product version `2.2.0` has been approved, built, tagged, or published. Likewise, an independent line created from `v2` may still carry a `v2.1` ancestry suffix even if another maintainer's line has advanced. State the actual source and target explicitly to prevent accidental cross-line merges.

## 15. Release process

Releases require an identified release owner and an agreed source integration branch. The release owner is responsible for coordinating version and firmware consistency, verification, documentation, and publication.

### 15.1 Release preparation

1. Agree on the release scope, compatibility expectations, supported board variants, source commit, and target users.
2. Verify that required issues and PRs are complete and merged into the release source.
3. Review unresolved P0/P1 defects, security risks, migration risks, and outstanding device verification.
4. Choose the approved `MAJOR.MINOR.PATCH` value; confirm it is not already used by a published release.
5. Move relevant Unreleased entries into a dated release section, while leaving unfinished work in Unreleased.
6. Update root `VERSION` and **all three** firmware version files together.
7. Update the README, release notes, upgrade and rollback steps, API,
   deployment, and firmware documentation. Verify and document database
   migration steps and backend/device compatibility for supported upgrade
   paths.
8. Run the full required tests and builds, including release-signing and hardware checks where required.
9. Verify the exact release candidate and wait for all required CI to pass.
10. Obtain maintainer sign-off under current repository approval rules.
11. Create the agreed version tag on the exact approved release commit through
    the authorized repository process. Verify the tag points to that commit.
12. Publish the GitHub Release as a separate step after the tag exists. Include
    only release notes and artifacts that match the tagged source.
13. Verify the published release page, tag, artifacts, documentation links,
    and installation instructions against the approved commit.

Do not mark a release as published before its tag or release record actually exists. An integration PR, passing CI run, or updated `VERSION` file is not a release by itself.

### 15.2 Rollback and recovery

For server releases, document backup, migration, compatibility, and recovery steps. For device releases, document image approval, signing keys, target-board checks, canary deployment, rollback prerequisites, and recovery from an interrupted update. Some firmware or bootloader/security changes may not be reversible over the air; explain that **before** deployment. Never promise OTA rollback without verifying the supported recovery path.

### 15.3 Post-release follow-up

Check deployment health, known issues, device enrollment, OTA status, and reported regressions. Link new regressions to the published release and earlier related issues. A patch release should use the approved version process rather than editing an existing published artifact without traceability.

## 16. Security, privacy, and responsible disclosure

imPress can handle classroom activity, user roles, device identities, and firmware delivery. Treat this as a trust-sensitive system.

- Do not commit or post student records, credentials, secrets, signing keys, tokens, private certificates, private communications, or production databases.
- Use synthetic data and test-only credentials in documentation, issues, and test fixtures.
- Do not post working exploit instructions or sensitive vulnerability details in a public issue before an agreed disclosure decision.
- Report sensitive vulnerabilities privately to an uninvolved maintainer or through GitHub's private vulnerability-reporting facility if it is enabled.
- Preserve server-side authorization, input checks, secure transport, and device-image authenticity as separate requirements.
- Review logs, screenshots, CI artifacts, firmware dumps, and stack traces for secrets before sharing.
- Coordinate security changes with deployment operators; a safe source-code default and a safe deployed configuration are not always the same.

For misconduct and interpersonal safety, see the [Code of Conduct](CODE_OF_CONDUCT.md). For technical vulnerabilities, follow the repository's security reporting guidance if one is published. These reporting paths address different kinds of concerns.

## 17. Documentation and communication

Keep instructions simple, factual, and easy to follow. Explain acronyms on first use when a document is intended for new contributors. Prefer commands that a reader can verify, explicit preconditions, and links to the source of truth. Avoid claims such as `fully secure`, `hardware tested`, `production ready`, or `100% coverage` unless evidence supports the exact statement.

Keep design decisions, architecture diagrams, API documentation, device protocols, test strategy, and deployment guides consistent. If a change makes an existing document false, the PR is not complete until it corrects the document or identifies and tracks the remaining documentation work with an approved exception.

Use GitHub issues and PRs for implementation decisions. Be respectful and direct in review. Credit earlier work. For significant changes, document why an approach was selected and which alternatives were considered; this helps future maintainers avoid repeating the same investigation.

## 18. Maintainer checklists

### Issue ready for work

- [ ] Search for duplicate or related work completed.
- [ ] Scope and desired outcome are clear.
- [ ] Bug reproduction steps are present or a justified safe-verification exception is recorded.
- [ ] Acceptance criteria are testable.
- [ ] Type, areas, priority, and severity (when appropriate) are consistent.
- [ ] Dependency and integration target are recorded.
- [ ] Security/privacy review of public content completed.
- [ ] Ownership is agreed or the issue is openly available.

### Pull request ready for review

- [ ] PR points to the correct integration line and links the issue.
- [ ] Implementation is focused and contracts are preserved.
- [ ] Regression and failure-path tests are included where relevant.
- [ ] Full standard pre-push test was run; outcomes recorded.
- [ ] Required additional suites and hardware status are stated.
- [ ] Documentation and Unreleased changes are updated.
- [ ] No secrets, private data, or accidental build artifacts appear in the diff.

### Pull request ready to merge

- [ ] Required independent review and all branch protections satisfied.
- [ ] Latest reviewed commit has passing required CI.
- [ ] No unresolved requested changes or conflicts remain.
- [ ] Acceptance criteria and deployment risks have been checked.
- [ ] Target branch, source branch, and merge method are correct.
- [ ] Any verification exception has explicit approval and a linked follow-up.

### Issue ready to close as completed

- [ ] Merged PR (or other verified deliverable) is linked.
- [ ] Intended target branch contains the result.
- [ ] Test and CI evidence are linked or summarized.
- [ ] Hardware verification is described without exaggeration.
- [ ] Documentation and release implications are addressed.
- [ ] Remaining work has its own linked issue.
- [ ] Final closing comment explains the outcome.

## 19. Issue and pull request templates

The following templates are copyable starting points. They are **recommended formats**, not a requirement to fill in irrelevant fields. Maintain accuracy and remove placeholders before publishing.

### 19.1 Bug report template

````markdown
## Summary
[One or two sentences describing the failure.]

## Severity and priority
- Severity: [critical / high / medium / low, with reason]
- Priority: [P0 / P1 / P2 / P3, with reason]

## Affected components and environment
- Components / paths:
- Branch / commit / app version:
- OS / browser / device / firmware:
- Preconditions:

## Current behavior
[Observed behavior, not an inferred cause.]

## Expected behavior
[What should happen.]

## Steps to reproduce (required)
1. [Exact setup and input]
2. [Action]
3. [Action]
4. [Observed outcome]

## Evidence
[Sanitized logs, screenshot, request, trace, or failing test.]

## Investigation / possible cause
[Known findings, hypotheses, and unknowns.]

## Impact, compatibility, and risk
[Who is affected; database / firmware / security impact.]

## Proposed approach
[Optional; not yet an approved implementation.]

## Dependencies / blocked by
[Linked issues or None.]

## Test plan
- [ ] Regression test for the reported failure
- [ ] Relevant negative and boundary tests
- [ ] Cross-component or hardware checks, where required

## Acceptance criteria
- [ ] [Observable result]
- [ ] [Observable result]

## Rollback / recovery
[Plan or reason not applicable.]

## Documentation
[Pages to update.]

## Integration target
[Agreed branch or To be decided.]
````

### 19.2 Feature request template

````markdown
## Problem and user need
[Who needs this and why the current workflow is insufficient.]

## Proposed capability
[Expected workflow and intended result.]

## Scope
- Included:
- Not included:

## Users, inputs, outputs, and permissions
[Roles, UI/API/device actions, validation, failure states.]

## Affected components
[Backend, frontend, firmware, database, tooling, documentation.]

## Design options / proposed implementation
[Options and trade-offs; mark unapproved decisions.]

## Dependencies and risks
[Issue links, compatibility, security, migration, rollout.]

## Acceptance criteria
- [ ] [Testable capability]
- [ ] [Testable failure or boundary case]

## Test plan
[Unit, integration, browser, protocol, and hardware checks.]

## Deployment / rollback
[Requirements or reason not applicable.]

## Documentation
[Files or guides to update.]

## Target integration line
[Agreed branch.]
````

### 19.3 Documentation or maintenance template

````markdown
## Summary
[Specific content, process, or internal code problem.]

## Current state
[Link to existing file, behavior, command, or workflow.]

## Intended result
[Clear definition of improvement.]

## Scope and affected files
[Paths and boundaries.]

## Implementation notes
[Key constraints, supported environments, preserved behavior.]

## Dependencies and risk
[Links or None.]

## Acceptance criteria
- [ ] [Verifiable result]

## Verification
[Documentation checks, tests, clean-install checks, and/or review.]

## Version history
[Proposed Unreleased entry.]
````

### 19.4 Pull request template

````markdown
## Linked issue
Refs #<number>

## Summary
[What changed and why.]

## Implementation
[Relevant components, decisions, behavior preserved, and scope limits.]

## Compatibility, security, and deployment
[API / database / protocol / firmware / migration / rollback impacts.]

## Verification
| Check | Result | Evidence |
| --- | --- | --- |
| `python run_tests.py` | [Pass / Fail / Not run] | [summary] |
| Relevant optional suites | [result] | [commands] |
| Required CI | [result] | [link to final run] |
| Physical hardware | [Verified / Not run / N/A] | [board, steps, date, result] |

## Documentation and version history
[Updated documents and Unreleased entry.]

## Outstanding work
[None or linked follow-up issues.]

## Pre-merge checklist
- [ ] Correct base branch
- [ ] Focused diff; no secrets or accidental artifacts
- [ ] Required tests and CI passed
- [ ] Review comments addressed
- [ ] Acceptance criteria met or exception approved
- [ ] Relevant documentation and change history updated
````

### 19.5 Suggested GitHub issue setup

Maintainers may later place these templates in `.github/ISSUE_TEMPLATE/` and a PR template in `.github/PULL_REQUEST_TEMPLATE.md`. If implemented, keep template fields aligned with this policy. Do not create redundant required fields that prevent users from submitting valid early reports. For bugs, make reproduction steps clearly required and provide a safe exception path for security-sensitive or destructive cases.

## 20. Questions and changes to this guide

Ask questions in a relevant GitHub issue or discussion, or contact a maintainer through the repository. Propose substantive policy changes through a PR so they can be reviewed and linked to the reason for change. Maintainers should update this guide when the branching model, required tests, label taxonomy, release process, or enforcement workflow changes.

This guide is intended to make contributions predictable, not to create unnecessary barriers. The central standard is simple: **describe the work clearly, verify what can be verified, disclose what has not been tested, review before integration, and leave a useful record for the next contributor.**