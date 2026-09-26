# CI audit — 2026-09-26

Status: **local implementation checked; hosted rollout pending**. The operator
corrected the platform during this task: use **Blacksmith, not Google Cloud**.
This supersedes earlier instructions to renew gcloud authentication.

## Source and live baseline

- Checkout started on `main`, HEAD `438d996`, with the earlier `e60a3bf` and
  `438d996` reader fixes not yet pushed. No commits or pushes were made for this
  CI audit at the time of this record.
- GitHub redirects `BeamoINT/beamo-wipe` to `BeamoTech/beamo-wipe`.
- Remote main was `4feb25a6996268fd0890e7570e8cd3548b53c993`.
- GitHub APIs reported no `.github/workflows` directory, no classic protection
  on main (404), and no effective ruleset (`[]`). Actions is enabled, default
  token permissions are read, and workflow PR approval is disabled.
- Blacksmith is installed in the organization with selected repository access.
  The current token cannot list its selected repositories or organization
  runner groups (403); actual execution is still required to prove enrollment.
- [Recent run snapshot](github-runs-before.json) records automatic CodeQL and
  dependency jobs, not a current Beamo Wipe ISO gate. Latest successful CodeQL
  run `36188328103` lasted approximately 127 seconds on September 25; this is
  **not** an ISO/QEMU baseline. Older removed custom workflows ran September 3.
- GitHub's automatically managed CodeQL configuration remains a separate
  provider-managed security check; this task does not claim it ran on Blacksmith.

## Changes and review

- New Blacksmith workflow covers PRs/main and validation branches. Five source
  gates run concurrently in separate pinned Debian containers, followed by ISO
  and full QEMU on the same worker. Native Windows launcher tests run separately.
  `CI gate` fails unless both platform jobs succeed, including on skipped or
  cancelled dependencies. Actions are pinned to resolved immutable commits.
- Full Ruff and mypy are now blocking. Baseline lint exited zero despite 19 Ruff
  and 36 mypy errors. Type annotations, ambiguous variable reuse and explicit
  pytest fixture registration were corrected without changing disk eligibility,
  authorization, erase methods or nwipe argv. The Tk comparison focus callback
  now also tolerates no next focus target.
- Added missing Node, browser/Playwright, Go, QR decoder and rsync prerequisites
  so existing hosted tests can execute. The approved Go 1.26.8 download/checksum
  is shared by desktop and Python rendering checks; the version is unchanged.
- Dedicated Orca JUnit is aggregated with the main suite, including a failed
  early Orca run. Stale secondary reports are rejected. Receipts identify
  Blacksmith, source commit, GitHub run and attempt; all phases share a UUID.
- Negative checks run against a private copy, can run in parallel, and install
  only their necessary dependencies. The `all` entrypoint now installs preview
  dependencies before invoking preview validation.
- Pip downloads alone are cached; only successful main pushes save the trusted
  cache. Results, launchers and image outputs are never reused from cache.
- QEMU has no host disk arguments or host `/dev` bind. Existing loop ownership
  checks are retained. Privileged image/QEMU work is limited to disposable
  hosted workers. No QEMU or image build was run on this Mac.
- Publication is absent from the workflow, with read-only token permissions and
  no signing/production secrets. Legacy Cloud tooling remains labeled as such.
  Existing signature/hash/no-overwrite/completion-marker checks and the pinned
  prior-stable 0.2.9 rollback artifact are preserved.
- Current Debian package repositories remain mutable: the pipeline records
  package inventory but does not establish bit-for-bit reproducible ISO bytes.
- Agent guides, durable memory, README and operating docs now identify Blacksmith.

## Verification actually performed

- `actionlint`, `git diff --check`, ShellCheck, compile, Ruff, existing formatter
  gate and mypy: pass. Five agent instruction copies match.
- Full local pytest: **4,546 passed, 696 skipped, five failed in 380.02 s**.
  Two failures require unavailable GTK/ATK. The other three were sandbox-only
  headless Chrome / Unix socket failures and **all passed** when rerun with
  the required local permissions and disposable profiles/socket.
- Subsequent focused CI/provenance/live-image run: **103 passed, two skipped
  in 14.97 s**. Preview validation passes. Also passing are the relevant
  discovery/inventory/boot-exclusion regressions. New orchestration tests use
  fake Docker and verify parallel startup, waiting for every gate, and failure
  propagation for each source gate.
- A temporary safe pytest fixture deliberately fails, creates a failing CI
  receipt, is repaired, then produces a passing receipt. `-B` prevents same-size
  rapid edits from reusing the failing fixture's cached bytecode. The repository
  never contains the failing fixture. The private boot-safety negative gate
  also rejects its mutant and passes again against the original source.
- These are **local** proofs. They do not establish successful Blacksmith Linux,
  Windows, ISO or QEMU execution, or live branch-protection enforcement.

## Timings

[Before](before-timings.json) and [after](after-timings.json) measure local
command time only, excluding dependency installs and hosted execution. Exact
outputs are retained beside those files, with ephemeral host directory names
redacted. The original lint timing represented
an advisory check; the new one is blocking. No hosted speedup is claimed.
A new Blacksmith run is needed for comparable hosted timings and cache behavior.

## Remaining rollout requirements

1. Bootstrap the new workflow on a GitHub validation branch. The request says
   to commit/push only after trustworthy pipeline proof, but GitHub cannot run
   an absent workflow from an uncommitted local checkout. Resolve permission
   for this limited bootstrap push before proceeding.
2. Verify enrollment/KVM and obtain a full clean hosted run; repair any actual
   Linux/Windows/browser failures without skipping or weakening tests.
3. Record hosted pass/failure proof, artifact identities and step timings.
4. Enable and read back main protection requiring the observed `CI gate` check,
   then deliver the verified commits according to operator authorization.
5. No production release is authorized by this task. Do not activate a new
   publication route or treat validation artifacts as a production release.
