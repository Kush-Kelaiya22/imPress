# Contributing to imPress

Thank you for helping improve imPress. This guide defines how to take work from
an issue through implementation, tests, review, integration, and release. Follow
the [Code of Conduct](CODE_OF_CONDUCT.md) in every project space.

## 1. Choose and scope the work

### Start with an issue

1. Search open and recently closed issues before starting. Check for an existing
   issue, pull request, or branch covering the same behavior.
2. For a defect, feature, documentation gap, or substantial maintenance task,
   create or use one GitHub issue. Describe the user-visible problem, expected
   behavior, affected components, acceptance criteria, and an appropriate test
   plan. Include hardware requirements and migration or compatibility concerns
   when they apply.
3. Comment that you intend to work on the issue and coordinate with its
   assignee or active contributor. Do not start a duplicate implementation
   without first agreeing how the work will be divided.
4. Keep one independently reviewable issue of work per issue branch. If an issue
   is too broad, split it into linked issues with separately testable outcomes.
5. If you discover an unrelated defect while working, record it in a separate
   issue instead of quietly expanding the pull request.

Do not publish credentials, private user data, signing keys, or exploitable
security details in an issue. For a security-sensitive report, contact a
repository maintainer privately through GitHub and share only the information
needed to investigate.

### Identify the affected surfaces

imPress combines a FastAPI backend, browser UI, ESP32 firmware, shared device
protocols, and documentation. A change that appears local can alter behavior
across those boundaries. Before editing:

- Trace the behavior across the browser, API, persistence layer, device
  protocol, and firmware as applicable.
- Read the existing architecture, API, design, and testing documentation in
  [`docs/`](docs/README.md).
- Check existing tests and related issues for established contracts and known
  limitations.
- Preserve compatibility with deployed devices unless the issue explicitly
  authorizes a breaking change. A UI-only restriction is not a substitute for
  backend validation.
- Never include real classroom data, secrets, access tokens, private keys, or
  generated database files in a commit.

## 2. Branch and version-line policy

### Work branches: one branch per issue

Create a new branch for each issue. Use a category prefix, the version line
being changed, and a short lowercase kebab-case description:

```text
feat/v2.1-{short-feature-name}
fix/v2.1-{short-bug-name}
docs/v2.1-{short-documentation-name}
test/v2.1-{short-test-name}
chore/v2.1-{short-maintenance-name}
```

Examples:

```text
feat/v2.1-timed-quizzes
fix/v2.1-quiz-option-validation
docs/v2.1-teacher-quiz-guide
```

Use `fix/` for correcting incorrect behavior, `feat/` for additive product
behavior, `docs/` for documentation-only work, `test/` for standalone test
infrastructure, and `chore/` for maintenance. Use other prefixes only when
they make the work category clearer and are agreed in the issue. The `v2.1`
segment identifies the target version line; it is not an issue number. Put the
issue reference in the branch description or pull request, not in place of the
version segment.

The repository also contains older numbered names such as `fix/10-role-escalation`
and `fix/25-fast-backend-tests`, and current version-scoped names such as
`feat/v2.1-device-tls` and `fix/v2.1-ota-root-causes`. New work should use the
version-scoped convention above rather than add more one-off naming styles.

### Create branches from the correct starting point

An issue branch must start from the integration branch into which its pull
request will be merged. The current v2.1 integration target observed in the
repository is `varun/v2.1`; recent feature, fix, and documentation pull requests
have targeted that branch. Do not assume that `main` is the right base for work
intended for v2.1.

When the issue is assigned to a different maintained product line, use that
line's designated integration branch and make the pull request target match it.
The owner/version branch pattern is:

```text
{owner}/v2.1
{owner}/v2.2
{owner}/v2.3
```

The owner namespace distinguishes independent lines of work; examples of the
requested naming pattern include `varun/v2.1`, `kush/v2.1`, `aamna/v2.1`, and
`encrypted/v2.1`. Use your own authorized namespace. Do not create, rewrite, or
push to another contributor's branch without their agreement.

The version suffix describes ancestry, not whichever branch happens to be
newest in the repository. A line created from the shared `v2` baseline is
`{owner}/v2.1`, even if some other line has since advanced further. Work based
on that line advances to `{owner}/v2.2`; work based on `v2.2` advances to
`{owner}/v2.3`, and so on. Select an agreed source `v2` branch (for example,
`varun/v2` or `encrypted/v2`) and record the exact base branch and commit in the
issue or pull request. Do not silently combine divergent lines or claim a
lineage that the branch does not have.

An optional suffix may identify a deliberate variant or experiment:

```text
{owner}/v2.1-aamna
{owner}/v2.1-experimental
```

Use a suffix only when it clarifies the source or purpose, document that
meaning, and obtain agreement before treating an experimental branch as a
release candidate. It does not replace the ordinary issue branch or issue
reference.

### Keep branches safe to collaborate on

- Push your issue branch to your fork or authorized namespace; open a pull
  request into its matching integration branch.
- Keep your changes on your own issue branch. Do not commit directly to another
  contributor's integration or feature branch.
- Never force-push a shared branch or rewrite commits after another person has
  based work on them. If the branch is private to you and rewriting is
  necessary, coordinate first.
- Rebase or merge the target integration branch into your issue branch only
  when useful; resolve conflicts without discarding other contributors'
  changes. Explain non-obvious conflict resolutions in the pull request.
- Keep an issue branch focused. Avoid mixing unrelated issues into one branch
  or pull request.

## 3. Make the change

### Implementation quality

- Make the smallest complete change that solves the issue, and follow existing
  naming, formatting, error-handling, and architecture patterns.
- Keep validation at the authoritative layer. Enforce permissions, input
  validation, deadlines, and state transitions on the server even if the UI or
  firmware also constrains them.
- Preserve existing API and device contracts unless the issue explicitly
  requires a change. If a contract must change, update every producer and
  consumer together and explain rollout compatibility.
- For database changes, add a versioned migration, preserve existing data,
  enforce appropriate constraints, and cover upgrade behavior in tests.
- For firmware changes, consider memory, task timing, watchdog behavior,
  network loss, reset and power-loss behavior, OTA rollback, and supported
  board variants. Do not claim physical-hardware validation unless it was
  actually performed.
- Do not add dependencies without a clear need. Keep lockfiles and dependency
  manifests in sync when dependencies do change.
- Do not commit generated output, build artifacts, databases, personal
  configuration, or machine-specific files.

### Tests are part of the change

Add or update tests that demonstrate the issue is fixed and that relevant
existing behavior remains intact. Prefer focused tests for boundary conditions,
failure paths, authorization, and regressions, not only a happy path.

Depending on the affected code, include:

- backend route, service, authorization, persistence, and migration tests;
- browser/UI tests for visible behavior and navigation or timing races;
- firmware structural and host C tests for protocol and state-machine changes;
- contract tests when changing JSON, binary framing, or device messages;
- build or hardware validation evidence for board-specific changes.

Keep [decision D5](docs/design/decisions.md#d5-the-backend--firmware-json-contract-is-a-committed-fixture)
in mind: keep on-wire formats in `firmware/protocol` and the committed device
contract fixture in sync with their producers, consumers, tests, and
documentation.

### Documentation and version history are required

Every pull request that changes code, behavior, tests, configuration, build or
release processes must update the relevant documentation. Documentation-only
changes must update the document being corrected and the version history. At
minimum:

1. Update the applicable page in `docs/` or the relevant repository policy
   file. Document new API routes and settings; repository tests check that
   routes and settings are documented.
2. Add a concise entry under **Unreleased changes** in [`Version.md`](Version.md)
   for every pull request, including documentation-only and test-only changes.
   Include the issue or PR reference when available and describe the user- or
   maintainer-visible result.
3. At a product release, move the accumulated entries into the corresponding
   release section in `Version.md` and update the canonical [`VERSION`](VERSION)
   file as described in the version policy. The repository requires every
   firmware `version.txt` to equal `VERSION`, so update all three firmware
   version files whenever `VERSION` changes, even if a particular firmware
   project's code did not change.

Do not bump the product version for every individual commit or use a branch
name as a substitute for the recorded product version. The exact rules for
which release number to bump are in [`Version.md`](Version.md).

## 4. Test locally before pushing

Before pushing a commit or updating a pull request, run the repository's test
runner from the repository root:

```sh
python run_tests.py
```

This is the required pre-push check. The default run covers backend tests,
firmware structural tests, repository/documentation checks, and discovered
firmware host test suites. Read the consolidated report: skipped suites are
not passing suites, and a failed or errored suite must be investigated.

Run extra suites when the change touches them or the required hardware/tooling
is available:

```sh
python run_tests.py --with-frontend
python run_tests.py --with-ui
python run_tests.py --with-idf
```

Use `python run_tests.py --list` to inspect suite names and
`python run_tests.py --help` for supported options. The focused selectors
documented in [`docs/guides/testing.md`](docs/guides/testing.md) can shorten
iteration while editing, but do not replace the full required pre-push run.
Record the exact commands and results in the pull request, including any
optional suite that could not be run and why.

**Do not push known-failing code.** If a test fails, investigate and fix it,
then rerun the appropriate tests and the full required pre-push run before
pushing. Do not hide failures by removing assertions, weakening checks, or
marking tests as skipped without an agreed, documented reason.

## 5. Commit and open a pull request

### Commit messages

Use a concise Conventional Commit-style subject that says what changed:

```text
feat(quizzes): advance timed quizzes automatically
fix(auth): reject answers after the quiz deadline
docs(teacher-guide): explain timed quiz behavior
test(firmware): cover gateway retry after reconnect
```

Use the imperative where natural, keep unrelated edits out of a commit, and
include issue references in the pull request description. Do not include
secrets, generated artifacts, or unrelated formatting churn.

### Pull request checklist

Open a pull request from the issue branch into the correct owner/version
integration branch. A useful pull request description includes:

- the issue number and a short problem statement;
- what changed and why, including behavior intentionally left unchanged;
- the relevant API, database, protocol, firmware, or configuration impact;
- tests run and their actual outcomes;
- documentation and `Version.md` updates;
- hardware or optional validation still outstanding;
- migration, deployment, rollback, or compatibility notes.

Before requesting review, verify that:

- the pull request is focused on one issue and its target branch is correct;
- the diff does not contain secrets, user data, generated files, or accidental
  changes from another branch;
- the relevant tests and documentation are included;
- the full `python run_tests.py` pre-push check passes;
- the GitHub Actions checks for the pull request are complete and green.

### CI is a required integration gate

The GitHub Actions workflow runs for pull requests and checks repository
quality, dependencies, backend tests, firmware structure and host tests,
firmware builds, and other configured validation. Allow the workflow to finish;
do not mark a pull request complete while checks are pending or failing.

If CI fails:

1. Stop treating the branch as ready to merge and identify the failing job and
   first relevant error.
2. Determine whether the failure is caused by the change, a flaky test, or an
   external runner/tooling problem. Do not dismiss a failure without evidence.
3. Fix the issue on the same issue branch, rerun tests locally, push a new
   commit, and wait for the new CI run to pass.
4. Update the pull request with the diagnosis and the new test results.

Until the branch is green, **do not ask other stakeholders to pull or build on
it unless they are intentionally helping diagnose or fix the failure**. A
failing branch can create wasted effort, conflicting changes, or unintended
behavior. If a shared branch becomes unhealthy, tell its collaborators
promptly and coordinate a repair.

Merge only after review is complete and all required CI checks pass. Prefer the
repository's standard GitHub pull-request merge process so issue and review
context remain visible. After merge, verify that the pull request landed on the
intended integration branch.

## 6. Versioning and release boundaries

The source code release version is the three-part semantic version in the
repository-root `VERSION` file. Version-specific integration branch names
(`v2.1`, `v2.2`, and so on) describe lines of development; they do not by
themselves publish a release. The [version policy and history](Version.md)
explains the current release and how to record changes.

The project remains in the v2 series for ordinary compatible work. For
successive non-major product lines, advance the middle number (`2.1` to `2.2`,
then `2.3`). Reserve a major-version change for an explicitly agreed major
product or compatibility break. Preserve the patch component required by the
repository's `MAJOR.MINOR.PATCH` version format; do not independently invent a
new numbering scheme. A release owner decides and records the actual release
version. Firmware releases must also follow
[`docs/firmware/FIRMWARE_VERSIONING.md`](docs/firmware/FIRMWARE_VERSIONING.md).

## 7. Collaboration expectations

- Be transparent about ownership, intended base branch, test status, and
  unverified hardware assumptions.
- Ask for review early when the design or compatibility approach is uncertain;
  do not use a review request as a substitute for a passing pre-push test run.
- Respond to review comments by discussing the technical concern and either
  changing the code or explaining, with evidence, why a different approach is
  safer.
- Keep contributions on your own branches and coordinate before rebasing onto
  or integrating another person's work.
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md). Report security issues
  privately rather than posting exploit details publicly.

Thank you for contributing carefully and helping keep imPress reliable for
classrooms, operators, and device owners.
