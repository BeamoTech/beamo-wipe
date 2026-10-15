# Unfinished work

## BW-BUG-AUDIT-20261015-PASS2 — DONE (local fixes verified and pushed)

- Date/author: 2026-10-15 / Codex.
- Request: another thorough, comprehensive bug audit and regression pass.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`. Baseline `8a5dced72b044f22b8dee168f76a2ea882083124`;
  implementation `57ead7e4304f7f373a0c862ff36335c949f4cf7a`, pushed to origin.
- Result/evidence: `docs/evidence/bug-audit-20261015-pass2/README.md` is the
  durable report, with original failures, fixed regressions, final transcripts,
  19-file source/test SHA-256 manifest, independent descriptor review and a Tk
  preview screenshot. Committed bytes match final tested bytes.
- Completed scope: three bounded reviewers revisited discovery/identity,
  runner/progress/log/evidence/cancel/retry, recovery/reporting and boot/build.
  Primary reviewed wizard state/confirmation/stop/retry/shutdown, language/UI,
  packaging boundaries, independently proved every finding and reviewed all
  changes. Fake devices/process boundaries/files/firmware only.
- Fixed seven finding groups: retired recovery-directory ownership, obsolete
  report preference snapshots/destinations, lock replacement before exec,
  substituted/reused log inode evidence, delayed-start overwriting ambiguous
  ownership, missing translated uncertainty warnings, English-only inventory
  counts. Added 71 regression/lifecycle cases; existing fixtures retain their
  assertions and now retire actual regular-log descriptors.
- Proof: baseline-compatible regressions on a private exact-original import
  tree produce 44 intended failures / 19 passing controls; all 71 new fixed
  tests pass. Original checkout was never reverted or mutated for proof.
- Review history: an intermediate dev/inode-only log fix was rejected after
  immediate inode reuse falsely completed. Retained-FD protection resisted
  1,000 unlink/recreates, refused replacement evidence and retired the handle.
  A draft transfer leak was proved and fixed. Independent approval: 76 tests
  with zero surviving temporary-file descriptors, plus 20 adjacent cases.
- Final applicable local gates PASSED: main pytest 5,787 pass / 14 image-only
  skips; private Orca 1 pass; combined 5,788 pass, no failures. Mandatory GTK
  result guard passes. Lint/types/security/shell/format, web/console/helper/JS
  preview, negative mutation, Go 1.26.8 race/vet and 350,000 firmware-parser fuzz
  executions pass. Native inventory override unset. Frozen hashes rechecked
  after the full gate and against the committed tree; all 19 match.
- Focused overlapping evidence: 56 baseline, 273 wizard, 108 inventory/language,
  222 discovery/safety, 812 recovery/report/boot, and 494 affected runner cases
  pass. The initial display-less recovery GTK failure is historical, not a pass;
  corrected runs use private 72-DPI D-Bus/Xvfb. Actual `./preview` welcome screen
  inspected at 72 DPI with no clipping. T3 web snapshot client is unavailable;
  existing browser regression tests passed separately, no interactive web
  inspection claimed. Owned preview HTTP server was positively identified/stopped.
- Current state/remaining criteria: local audit acceptance complete; no local
  blocker. No PR, hosted CI, ISO, guest, device operation, deployment or release.
  Exact next action for a public candidate is the separate qualification item
  below. Do not infer release authority from this record. Shared-guide absence
  remains resolved by the owner's earlier continue instruction.
- Conservative behavior retained: large-log recovery can become indeterminate
  if an early completion marker lies outside authenticated retained suffix
  evidence. Recorded in the report; no false success or schema expansion.

## BW-BUG-AUDIT-20261015 — DONE (local source fixes verified and pushed)

- Date/author: 2026-10-15 / Codex.
- Resolution: owner instructed Codex to address the issue and continue on
  2026-10-15. Proceed under current project AGENTS.md without the unavailable
  shared guide; do not invent its contents. Initial stop is retained below
  as history, not an active blocker. Three bounded audit subagents started.
- Baseline history: system `python3 -m pytest` exited 1 because pytest was
  absent. Resolved with the documented `.venv-linux` development environment.
- Request: systematic bug audit and minimal proven fixes across wizard,
  discovery/classification/exclusion, command construction, progress,
  cancellation, completion verification, logs, boot, hardware compatibility,
  build pipeline and recovery. Use bounded subagents; independently validate
  results. Prove each bug before changing code; add regression tests.
- Repository: BeamoTech/beamo-wipe; worktree `/root/dev/Beamo Wipe`;
  branch `fix/safety-audit-20261015` (started from `main`);
  baseline `cad8ed397818bca09634be57cd8a46e0195690c2`;
  implementation `ff0a3da08e56c3fb38941be20e42db9553269f32`, pushed to origin.
- Completed: read current `AGENTS.md`, memory index, `pyproject.toml` and
  `scripts/test-all.sh`; confirmed initially clean checkout. Searched tracked
  and hidden workspace paths for an existing unfinished-work/backlog record;
  none found, so this is the canonical record.
- Resolved initial blocker/evidence: `AGENTS.md` requires reading `~/dev/AGENTS.md`;
  `cat /root/dev/AGENTS.md` reports “No such file or directory” and
  `test -e /root/dev/AGENTS.md` exits 1. Shared checkout, cost, documentation
  and storage instructions are therefore unavailable. Current request says
  “Stop on any blocker.” At that initial stop, no implementation or delegated
  audit had started; the owner's subsequent continue instruction resolved it.
- Local acceptance completed: read applicable current instructions and relevant
  architecture/operations guidance; establish baseline; complete bounded
  reviews; reproduce suspected defects with failing tests or concrete traces;
  make minimal fixes; independently verify regressions and adjacent paths;
  run applicable full local gates and preview checks; inspect final diff.
  Commit/push occurred only after all applicable local gates passed and automatic
  CI trigger constraints were checked. No release is authorized.
- Current progress (2026-10-15): bounded reviews completed across discovery,
  safety/methods, runner/progress/evidence, wizard transitions and shutdown,
  recovery/report export, live boot/kiosk, compatibility and build scripts.
  Discovery/safety review found no new proven defect (439 focused tests passed).
- Proven fixes, committed and pushed:
  - `progress.py`, French/German tables: nwipe SIGUSR1 reports job-wide
    `round_percent`, incorrectly labeled as a within-step percentage; secondary
    text also showed 100% before completion evidence. Labels now say overall
    and clamp telemetry to 99% until completion. Pinned upstream signal handler
    checked at https://github.com/martijnvanbrummelen/nwipe/blob/6082bde060091e66365d852a1877f2ee80c67105/src/nwipe.c#L1350.
    Final review also proved headline/step percentages diverged during the
    five-second throttle or raw regressions. `wizard.py` now shares the displayed
    monotonic job percentage; two actual-runner fake-log regressions cover it.
  - `session_recovery.py`: lock pathname replacement left ownership/cached
    quiescence attached to obsolete inodes. Validate named inode after flock
    and before cached-quiescence/journal writes; fail closed on replacement.
  - `nwipe_runner.py`: same replacement race at wipe-lock acquisition; verify
    named inode after flock and release descriptor on refusal. Final review
    also proved an unpublished descriptor leak on KeyboardInterrupt during
    acquisition. Cleanup now catches BaseException; 66 adjacent tests passed.
  - `engine_checks.py`: incomplete final records falsely passed hidden-storage
    or I/O checks. Incomplete logs cannot produce passing parsed checks;
    explicit failures/warnings remain.
- Independent reproduction: private original-source snapshot from HEAD plus
  the four new regression modules produced **14 failures / 4 passing normal
  controls**, exit 1, in `/tmp/beamo-audit-original-repro.txt`. No mutation of
  shared source was needed to reprove the original defects. All **18** pass
  on the fixed source (`/tmp/beamo-audit-regressions-final.txt`). Independent
  progress review passed 135 tests and 36 en/fr/de boundary/staleness cases.
- Completed checks: 294 wizard confirmation/refresh/stop/retry/shutdown tests;
  177 independent changed/adjacent tests; source/tests Ruff and mypy (52 files)
  pass; web/console/helper previews generated; 3 embedded-JS syntax tests pass.
  Subagent recovery audit: 797 passed / 8 GTK dependency skips before exposing
  system GTK to the venv. Subagent runner audit: 182 runner/progress/completion
  tests and 65 security/cancellation tests passed.
- Environment diagnostics: original full-suite attempt interrupted after
  1102 passed / 18 failed / 13 skipped. Failures traced to fixture shebangs
  containing the spaced venv path and subprocess Python lacking pytest.
  Use `/tmp/beamo-wipe-audit-python` (symlink to `.venv-linux`) on PATH;
  venv now exposes installed system GTK. All 28 affected CI-fixture tests
  pass after environment correction. This interrupted run is not a gate pass.
- Intermediate direct test-all runs were interrupted after the final
  cancellation cleanup change and then an accessibility-bus failure. The
  AT-SPI quick-zero external-client test passes alone (1 passed); a combined
  run's registry tried the removed `/run/user/0/at-spi/bus` socket after speech
  testing. Do not count these interrupted runs as passes. Use the repository's
  existing private runtime/session separation rather than changing tests.
- Passed final gate: `PATH=/tmp/beamo-wipe-audit-python/bin:$PATH
  BEAMO_GATE_CHILD=1 BEAMO_GATE_JUNIT=/tmp/beamo-audit-final.xml
  ./scripts/ci-hosted.sh tests`; output `/tmp/beamo-audit-final.txt` and
  JUnit `/tmp/beamo-audit-final.xml{,.orca.xml}`. This runs locally, skips only
  dependency installation, uses existing dependencies, and does not dispatch CI.
  Local lint, preview and private safety-negative phases passed. Lint's
  existing TODO warning matches the literal placeholder-detection regex in
  unchanged `release_manifest.py:40`, not an untracked task or source warning.
- Complete-run diagnostic: pytest 9.1.1 produced 5668 passed / 58 skipped /
  2 failures in missing-GTK import simulation; its importlib-based importorskip
  bypasses that simulation's builtin-import hook. Installed repository-pinned
  pytest 9.0.3; all 15 GTK dependency-boundary tests then passed unchanged.
  Installed prescribed Playwright 1.63.0/Chromium and QR decoder for broader
  local coverage; dependency preflight passed 33 tests. The full gate passed
  with these dependencies. No source/test assertions weakened for setup errors.
- Final results: full pytest 5694 passed / 36 skipped, plus one passed Orca test;
  Go 1.26.8 launcher supplement 23 passed, resolving 22 skips (one overlapping
  bootstrap test). Combined **5717 unique passed / 14 image-dependent skipped**;
  no failures. Mandatory GTK guard, lint/types, preview, safety mutation,
  Linux Go race tests and vet all passed. Native inventory override stayed unset.
- Durable evidence retained under
  `docs/evidence/bug-audit-20261015/README.md` with original reproduction,
  fixed regressions, source/test SHA-256 manifest and local gate transcripts.
- Browser limit: T3 preview initialized, but navigation/snapshot automation
  failed repeatedly; no successful visual browser inspection claimed.
- Exact next action: review the pushed source commit and retained evidence.
  No further local implementation fix is pending. Selecting a public candidate
  requires the separate image/native qualification item below. No PR was
  opened; GitHub branch run query returned no runs after the source push.
- Safety: fake devices only for local work; ISO/QEMU requires an authorized
  isolated worker. Physical-device operations remain prohibited by current
  project instructions. Follow current Blacksmith guidance, not historical
  Cloud Build/publisher instructions in the task baseline.
- Source/publish state: implementation/tests committed and pushed on the stated
  branch. This documentation records the verification after that push. No PR,
  merge, deployment or release occurred.

## BW-BUG-AUDIT-20261015-QUALIFICATION — NOT RUN (future public candidate)

- Date/author: 2026-10-15 / Codex.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; latest implementation
  `57ead7e4304f7f373a0c862ff36335c949f4cf7a` (prior audit implementation
  `ff0a3da08e56c3fb38941be20e42db9553269f32` retained as history).
- Remaining acceptance: final-public-candidate exact-source Blacksmith ISO/QEMU
  and native Windows gates, plus applicable physical firmware/media acceptance.
  The 14 local skips need generated live-build config/manufacturing ISO bytes.
- Exact next action: when the owner selects a public candidate, qualify its
  exact final source through current Blacksmith guidance in `docs/ci.md` and
  retain all source/image receipts. Do not use legacy Cloud Build instructions.
- Blockers/approval: no public release authorized; no local guest authorized.
  Physical acceptance is blocked by unattended-host rules and needs the
  separately specified safe physical session. Local passing tests do not
  replace these gates. T3 interactive browser automation also remained unavailable;
  repository browser regressions passed, which is distinct evidence.
- Publication state: **NOT TESTED / NOT DEPLOYED** for ISO/QEMU/native Windows/
  physical acceptance. No hosted dispatch or publication performed.
