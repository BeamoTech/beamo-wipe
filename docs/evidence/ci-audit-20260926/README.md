# CI audit — 2026-09-26

Status: **Windows and Linux source gates passed; image provenance fix awaiting hosted validation**. The operator
corrected the platform during this task: use **Blacksmith, not Google Cloud**.
This supersedes earlier instructions to renew gcloud authentication.

## Source and live baseline

- Checkout started on `main`, HEAD `438d996`, with the earlier `e60a3bf` and
  `438d996` reader fixes not yet pushed at the start of this audit.
- The operator approved a limited bootstrap push. Commit
  `dc32f589c28527c9a0140c80dbb52c07ebc906e0` is on GitHub branch
  `codex/ci-blacksmith`, including those earlier reader fixes. Main and the
  Cursor remote have not been changed by this rollout.
- [First Blacksmith run](https://github.com/BeamoTech/beamo-wipe/actions/runs/36266226513)
  started at 19:29:25 UTC. Linux was assigned an actual Blacksmith 8-vCPU
  Ubuntu 24.04 runner. Windows acquired its Blacksmith runner at 19:51:59 UTC,
  after about 22 minutes queued. Both jobs rejected failures; ISO/QEMU did not
  run. This is not a passing CI result. See [job timings](blacksmith-first-run.json)
  and [failure inventory and log hashes](blacksmith-first-failures.json).
- Corrections were pushed as `7e7ce981e20a03761fd5ef9e7007f7721fb5cf01`.
  [Second run](https://github.com/BeamoTech/beamo-wipe/actions/runs/36267895827)
  passed native Windows tests and vet: 161 passing test/subtest results and one
  case-sensitive-filesystem fixture skipped on Windows (still covered on Linux).
  Windows log SHA-256:
  `2f20c5a1c781150d7213cee215c33ade1115a042e7869a004d1b49b10b82063c`.
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
  gate and mypy: pass. The subsequent workspace instruction migration makes
  `AGENTS.md` the sole guide; duplicate instruction files must not be recreated.
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
- These initial proofs were local. Subsequent hosted source results are recorded
  below; full ISO/QEMU success and branch-protection enforcement remain required.

## Timings

[Before](before-timings.json) and [after](after-timings.json) measure local
command time only, excluding dependency installs and hosted execution. Exact
outputs are retained beside those files, with ephemeral host directory names
redacted. The original lint timing represented
an advisory check; the new one is blocking. No hosted speedup is claimed.
A new Blacksmith run is needed for comparable hosted timings and cache behavior.

## First hosted run findings

- Linux lint, preview, negative mutation and desktop launcher gates passed.
  Isolated Orca passed in 232.81 s. Main pytest: **5,397 passed, 20 failed,
  15 skipped in 696.52 s**. The source step took 1,004 s including setup.
- Linux artifact upload failed because the container created the parent `dist`
  directory privately for root. Ownership restoration now includes the parent.
- Browser readiness fixtures omitted the nonzero review revision supplied by
  the API. Platform-neutral fixtures now represent a published review. The
  product's incomplete-response rejection remains unchanged.
- Preview confirmation redraw scheduled a late input focus that could steal
  focus from Show more. Focus is now synchronous. URL fragment changes now
  apply preview navigation, with a regression waiting for the resulting screen.
- The unsure-disk browser test used an obsolete accessible region name. The
  metadata rendering test expected picker-only markings even when an unsafe
  token correctly kept the preview on the empty screen; it now checks both
  that rejection and the applicable display contract.
- Five rendering checks used Chromium's one-shot `--dump-dom` path, which
  hung without producing output. They now use the installed Playwright driver
  to await navigation and capture the same DOM, layout and screenshots.
- Native Windows found four fixture/platform-assumption failures. Read-only
  fixtures now create, then reopen files; the replacement fixture explicitly
  permits Windows delete sharing. Session tests verify Windows' manual-only
  policy and reject both missing and current-revision restart requests.
  Unix session and replacement checks remain in place.
- Local correction checks: all Go tests, Windows test-binary cross-compilation,
  Go vet, actionlint, Ruff and mypy passed. Focused CI/provenance tests passed
  (103 passed, two skipped). All 76 selected browser/adjacent tests passed.
  The expanded run also exposed 23 Node fixtures that sliced the newly added
  listener into their isolated function harness; keeping registration after
  initialization restored that boundary. All 52 gallery regressions then passed.
  Native Windows execution subsequently passed; a clean complete hosted Linux/ISO/QEMU run remains required.
- Final local full suite, with Playwright and isolated Chrome profiles enabled:
  **4,611 passed, 647 skipped, two failed in 350.64 s**. Both failures are the
  previously documented unavailable GTK/ATK imports on this Mac. The complete
  hosted Linux suite is required to cover them. The final six focused real-browser
  navigation, focus, help and metadata regressions passed in 15.87 s.

## Second hosted run findings

- Native Windows and all five Linux source gates passed. Main pytest:
  **5,417 passed, 15 skipped in 199.70 s**; isolated Orca: **one passed in
  234.59 s**. The source step completed in about 502 s including setup,
  compared with 1,004 s in the failed first run. Removing browser CLI hangs
  accounts for much of the difference; this is not a cache benchmark.
- Ownership restoration and the evidence upload passed. Artifact `10915021021`
  contains 14 files, 145,797 bytes; archive SHA-256:
  `d4b077a228a190a7a3520bf99f668b67d8f5e24044979e8f34a645af5e01f467`.
- The 538 MiB ISO built successfully, but manifest generation rejected the
  current `BeamoTech` origin because its exact allowlist retained only the old
  `BeamoINT` identity. QEMU correctly did not run after this failure.
- The manifest now accepts the exact current and redirected legacy repository
  URLs, normalizes provenance to `BeamoTech`, and rejects unrelated repositories,
  lookalike hosts and credential-bearing URLs without echoing their contents.
  Fourteen new cases cover this boundary. Focused manifest/CI tests and Ruff pass.
- [Complete second-run job and step timings](blacksmith-second-run.json).

## Remaining rollout requirements

1. Bootstrap completed with explicit operator approval, on the validation
   branch only. Follow-up fixes remain subject to hosted verification.
2. Verify enrollment/KVM and obtain a full clean hosted run; repair any actual
   Linux/Windows/browser failures without skipping or weakening tests.
3. Record hosted pass/failure proof, artifact identities and step timings.
4. Enable and read back main protection requiring the observed `CI gate` check,
   then deliver the verified commits according to operator authorization.
5. No production release is authorized by this task. Do not activate a new
   publication route or treat validation artifacts as a production release.
