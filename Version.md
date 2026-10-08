# Version policy and change history

This file records contributor-visible changes and explains how project
versions and versioned branches relate. It is not a replacement for the
machine-readable [`VERSION`](VERSION) file.

## Current state

- **Product version:** `2.1.0`, as recorded in `VERSION`.
- **Current integration line:** `varun/v2.1`, developed from the shared `v2`
  baseline.
- **Release status:** the README notes that no GitHub release or tag has been
  published yet.

The `VERSION` file is the canonical release value consumed by the backend and
reported by health endpoints. This Markdown file is the human-readable policy
and change log. Keep them consistent whenever a product release is made.

## Numbering policy

The application and firmware use three numeric components:

```text
MAJOR.MINOR.PATCH
```

- Keep ordinary compatible development within the current major series (`2.x`).
- For a new non-major product line, increment the middle component, such as
  `2.1` to `2.2`, then `2.2` to `2.3`. A major-version change is reserved for
  an explicitly agreed major product transition or compatibility break.
- Preserve the patch component required by the existing `X.Y.Z` format.
  Release owners decide whether a particular release needs a patch increment;
  contributors must not introduce a competing numbering rule.
- Do not bump `VERSION` once per commit or issue branch. A branch records work
  in progress; a product version is set for an agreed release.
- Record every merged change, however small, in **Unreleased changes** below.
  This includes code, documentation, tests, configuration, and maintenance
  changes. Update the relevant technical documentation in the same pull
  request.

The version-line branch suffix records its ancestry as well as its iteration.
A line made from `v2` uses `v2.1`; a subsequent line based on that `v2.1`
integration branch uses `v2.2`. Continue from the actual base (`v2.2` to
`v2.3`), rather than naming a branch after some unrelated line's newest
version. See [branch policy](CONTRIBUTING.md#2-branch-and-version-line-policy)
for owner namespaces and optional variant suffixes.

## Releasing

The release owner coordinates a release and its version across all artifacts.
Before a product release:

1. Confirm the release scope, compatibility expectations, and source
   integration branch.
2. Move the applicable entries in **Unreleased changes** into a dated or
   explicitly named release section below.
3. Update `VERSION` to the agreed `MAJOR.MINOR.PATCH`.
4. Update all three `firmware/<project>/version.txt` files to equal `VERSION`
   whenever `VERSION` changes, even if a particular firmware project's code
   did not change. The version consistency tests and
   [firmware versioning guide](docs/firmware/FIRMWARE_VERSIONING.md) define the
   repository's release constraints.
5. Update the README release history and relevant upgrade, API, deployment,
   and firmware documentation.
6. Run the required tests and builds, wait for the release branch's CI checks
   to pass, and only then mark the release ready.
7. Create GitHub release tags or published release records only through the
   agreed maintainer process. Do not claim a release exists until it has
   actually been published.

## Unreleased changes

- **Documentation:** moved contributor workflow guidance out of the README
  into `CONTRIBUTING.md`; added branch, testing, version-line, and CI
  requirements; added the community Code of Conduct. (2026-10)

## Published release history

| Version | Source/integration line | Notes |
|---|---|---|
| `2.1.0` | `v2` → `varun/v2.1` | Current repository version. See the [v2.1 changelog](docs/reference/changelog-v2.1.md). The README reports no published GitHub release or tag yet. |
| `2.0` | `v2` | Audit fixes, test suite, CI, and documentation. See the [v2 changelog](docs/reference/changelog-v2.md). |
| `1.x` | `main` | Original system. |
