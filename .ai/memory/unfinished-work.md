# Unfinished work

## BW-BUG-AUDIT-20261016-PASS7 — DONE (local acceptance and source push)

- Date/author: 2026-10-16 / Codex. Request: another fresh comprehensive pass.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; baseline
  `f102dfbe5a705fda10880fecc24626c7693c10f0`; implementation
  `de55b078514e2028a2a22633f1d7aa2941f9e0b6`, safety-prefixed commit pushed to origin.
- Outcome: fixed unchanged padded model/serial/WWN blocking report export, and
  verification receipts accepting mismatched skip/xfail kind counts. Only
  harmless hardware padding is normalized before existing strict validation;
  original safe Unicode model-to-generic-receipt behavior preserved. Paths,
  UUIDs, controls, protected identity and receipt schema/gates stay intact.
- Proof:75 new cases produce36 intended failures/39 passing controls, zero
  setup errors, on isolated exact baseline; corrected75 PASS. Original checkout
  never reverted; existing tests unchanged. All4 frozen hashes match committed
  source/test bytes. Runtime source digest
  `ff52fe2414436c9bec18cee235ee8a104fe16f567f7cd4237dabe62dcbdc0d42`.
- Final local gate: main6202PASS/14expected image-only skips (476.19s), private
  Orca1PASS =6203 unique passes; no failures/errors/duplicate IDs. Mandatory GTK
  result guardPASS. Corrected-source lint/types/security/shell/developer-format,
  preview, private negative mutation, pinned Go1.26.8 uncached race/vet/350000fuzz
  PASS. All skip reasons retained:2generated lb-config and12manufacturing ISO.
- Independent coverage: discovery648tests/454controlled sequence+retry/
  160concurrent observations; engine699tests/21600 completion projection cases/
  24readiness controls; corrected export731adjacent/1120helper-equivalence/
  240boundary cases, primary27controller roundtrips+27changed-scan refusals;
  receipt59adjacent/2268kind-count combinations. UI1359unique passes,
  build487PASS/2expectedskips; reviewer union1862PASS/2skips. Navigation54000
  events+54countdown detours;40concurrentfake sessions; primary5760malformed
  rendering/sharing calls with no unhandled exceptions. Overlaps not summed.
  Actual ./preview72DPI inspected by reviewer and primary; owned process retired.
- Draft history retained: first full integration2FAIL/6200PASS/14expected skips,
  private OrcaPASS. Discovery-parser reuse broke unchanged Unicode receipt
  contract. Focused2FAIL/3PASS proved it; narrow hardware-padding fix preserves
  original parser/display behavior. Existing tests unchanged; corrected80focused
  PASS and expanded independent sweep above. Earlier narrow reviewer approval
  superseded. Final replacement full frozen-source gate PASS as measured above.
- Setup history: initial reviewer DISPLAY/Chromium-PATH failures/skips resolved
  by private72DPI complete replacements/browser-case reruns; originals retained.
  Initial permission harness allowed predecessor read-only mount/cmdline probes;
  corrected fully fake harness reran PASS. Primary controller harness initially
  lacked preview mode; live tmpfs guard refused regular-file evidence directory
  before write; corrected explicit fake mode PASS, guard unchanged. No native
  lsblk inventory, actual nwipe, device/USB write, guest or host power action.
- Evidence: docs/evidence/bug-audit-20261016-pass7/README.md retains original and
  fixed proofs, failed draft gate, final raw logs/JUnit-derived skip list,
  independent matrices/scripts/reviews, screenshot, hashes and content manifest.
  A duplicate-skip suspicion was rejected with a real pytest call+teardown trace;
  duplicate outcome IDs are intentionally preserved, not silently deduplicated.
- State/remaining acceptance: no local audit blocker or further reproducible
  actionable finding remains in reviewed scope. Source pushed; no open PR,
  hosted run, merge/deployment/release. Documentation accompanies source; only
  docs changed after tested source freeze. Local acceptance is not a bug-free
  guarantee. No next action for this local pass; a selected public candidate
  needs separate exact-source ISO/QEMU/native/physical qualification below.
- Authorization: fake targets/process boundaries and ordinary temporary files
  only. No hosted/ISO/QEMU/native-platform/physical acceptance or publication
  authorized here. Current Blacksmith guidance applies, not legacy Cloud Build.
  Missing shared guide remains resolved by prior owner continue direction.

## BW-BUG-AUDIT-20261016-PASS6 — DONE (local acceptance and source push)

- Date/author: 2026-10-16 / Codex.
- Request: another fresh thorough comprehensive audit; prior evidence was
  baseline history, not proof for this pass. Three bounded reviewers rotated
  discovery/safety, persistence/report/privacy, UI/boot/build ownership; primary
  independently reviewed runner/progress/evidence and all fixes/original proofs.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; baseline
  `6bf8c54ce6b25dd21f8be730f705a54c2c8c3ff8`; implementation
  `ac6ed67c496090c26a9520d0244100ca371ce192`, committed with safety prefix and pushed to origin.
- Fixed: model-LF spoofed readiness could trigger premature SIGUSR1; sharing
  identifier/control collisions and UI-language restarts could corrupt valid
  results; malformed nested dictionary keys leaked private identifiers; later
  identifiers could re-redact inserted placeholders. Full timestamped readiness,
  validated machine controls/canonical presentation, scalar-only sharing leaves
  and single-pass escaped substitution fix these without touching original data.
  Method and verification prose keep intended redactions; outcomes parser strict.
- Proof/evidence: docs/evidence/bug-audit-20261016-pass6/README.md retains exact
  original/fixed cases, final logs/JUnit-derived skip list, reviews, matrices and
  scripts, preview screenshot, hashes and unsuccessful draft history. New180
  cases yield120 intended failures/60 controls on exact baseline; fixed180 PASS.
- Final local gate: main6127 PASS/14 expected image-only skips plus private
  Orca1 PASS =6128 unique passes; no errors/failures/duplicates. Mandatory GTK
  guard PASS. Lint/types/security/shell/preview/negative and pinned Go1.26.8
  uncached race/vet/350000 fuzz PASS. All9 tested hashes match committed bytes.
- Independent coverage: discovery415 +364 controlled cases; runner213/1176
  matrix plus189 primary; privacy482 adjacent/305 independent and1408 malformed
  core/118 nested-container/330 multisecret cases; UI955+358adjacent/242build
  and20000 navigation events, with2 generated lb-config skips classified.
  Overlapping counts are not summed as unique passes. Actual ./preview at72DPI
  inspected by reviewer and primary, owned subprocesses retired.
- Draft history: first complete integration FAILED1/6089pass/14skips because
  approved draft restored too much method prose. Existing pass37 test stayed
  unchanged. Method/scope redaction restored; collision tests check semantic
  controls and valid redacted prose. Cross-review then proved pre-existing
  placeholder re-scrubbing (24fail/12controls), fixed single-pass. Early
  replacement intentionally stopped on owned PID269626; missing-JUnit failure
  superseded, not a pass. Final replacement full frozen-source gate PASS above.
- Result/state: no further reproducible actionable local defect or blocker
  remains in reviewed scope. Source branch pushed; no open PR, hosted run,
  merge/deployment/release. Only evidence/handoff documentation changed after
  implementation; these artifacts accompany source. This is not proof of no bugs.
- Remaining acceptance/next action: none for local audit. A selected public
  candidate needs the separate exact-source ISO/QEMU/native/physical
  qualification item below; no guest/hosted/physical/publication authority here.
- Safety: fake targets/process boundaries, ordinary temporary files and private
  72-DPI sessions only. No real nwipe/device operation/guest/native inventory;
  current Blacksmith guidance applies, not legacy Cloud Build. Shared-guide
  absence remains resolved by prior owner continue direction. Logs /tmp/beamo-pass6-*.

## BW-BUG-AUDIT-20261015-PASS5 — DONE (local acceptance and source push)

- Date/author: 2026-10-15–16 / Codex.
- Request: another thorough and comprehensive pass after the completed
  continuous audit; prior passing evidence is baseline history, not new proof.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; clean baseline
  `604e72b3ae1fe1a2abdda08200b8f271cb5c675d` (implementation `af2b6e9`).
- Scope/acceptance: fresh source review of discovery/identity/authorization,
  runner/argv/progress/log/completion/cancel/retry, wizard/Tk/GTK/console/app,
  recovery/report/export/diagnostics and boot/build/compatibility. Prove any
  suspected defect before a minimal regression-backed fix; independent review;
  final frozen-source full local gates and artifact/diff inspection.
- Progress: read current guide/record and verified clean source. Three bounded
  reviewers resumed with rotated scopes; primary owns persistence/export/
  diagnostic integration and final independent verification.
- Proven findings this pass: falsey malformed `children` values accepted as
  empty topology (original regression fails; minimal fix now frozen);
  malformed findmnt bracket suffix trusted as a different source; embedded
  model newlines forging positive hidden-capacity/error-summary checks; stale
  import-time startup translations and hardcoded GTK status. Each reviewer
  saved a failing fake/isolated-label proof before authorized source edits.
- Additional proven fix: report mount cleanup skipped owned directory removal/
  descriptor close after lock-close or unmount I/O errors, and worker child
  close EIO skipped parent close. Original fake-only proofs fail3 cases;4
  regressions/controls now pass with independently reviewed nested-finally fixes.
- Final local acceptance PASS:59 new cases, exact-original38 intended failures/
 21 controls and fixed59 passes. Main5947 pass/14 expected image skips plus
  private Orca1 pass =5948 unique passes, no errors/failures or duplicate case
  IDs. Lint/types/security/shell/preview/negative and refreshed Go1.26.8
  uncached race/vet/350000 fuzz executions PASS. All20 frozen hashes match.
- Integration history:2 preliminary runs deliberately interrupted on exact
  owned pytest PIDs for final proven source variants; later integration run
  completed3 failed/5944 passed/14 skips from1 remaining short positive-header
  fixture and2 GTK tests selecting an unrelated global window. Original
  assertions retained; fixture corrections pass12 parser/60 ordered UI cases;
  replacement full frozen-source gate PASS above. Superseded runs are not passes.
- Evidence checkpoint: docs/evidence/bug-audit-20261015-pass5/README.md contains
  original proof, fixed cases, reviews, complete final logs, hashes and exact
  image skip reasons. Independent sweeps394 discovery,499 runner,1176 matrix,
 1203 UI plus31 resolved setup skips,380 parent persistence; overlapping counts.
- Source state: implementation `cdfe9fac6238c8fd3d867c9ef48c4ca3248facce` committed with safety prefix and
  pushed to origin after all applicable local gates passed. All20 frozen
  source/test hashes match committed bytes. No open PR or branch hosted run;
  no merge/deployment/release. Evidence/handoff are the only subsequent edits.
- Result: fresh bounded reviews and final complete local gate found no further
  reproducible actionable defect in authorized local scope. Local acceptance
  criteria passed; this is not an absolute proof of no bugs or image/hardware
  qualification. No unresolved local implementation blocker remains.
- Exact next action: no further local implementation fix required. Review the
  source/evidence if desired; any selected public candidate must follow the
  separate qualification item below. No PR/hosted run/release is part of this task.
- Constraints: fake fixtures only, isolated72-DPI Xvfb, no host/physical device
  operation, guest, hosted CI, PR, production publication or release. Current
  Blacksmith/project guidance applies; shared-guide absence remains resolved
  by prior owner continue direction. Image/native/physical qualification stays
  in the separate existing item below. Logs use `/tmp/beamo-pass5-*`; retain
  final evidence in repository before completion.

## BW-BUG-AUDIT-20261015-CONTINUOUS — DONE (local acceptance and source push)

- Date/author: 2026-10-15 / Codex.
- Request/goal: repeat comprehensive audit/fix passes until a fresh whole pass
  finds no further reproducible actionable defect in authorized safe local
  scope. Acceptance achieved after fixes, independent reviews, fresh source/
  fixture/matrix/actual-Tk checks and the final complete local gates. This is
  not an absolute proof of no bugs or image/hardware acceptance.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`. Baseline `20ae39a556ab961baf204e3108e6ebc93b695ac5`;
  implementation `af2b6e9c3d053b65e666d807a87207db14521cb2`, pushed to origin.
- Result/evidence: `docs/evidence/bug-audit-20261015-continuous/README.md` with
  exact-original failures, fixed regression transcript, final full gate logs,
  source/test hashes, independent review summaries, reproducible mutation/
  exploration scripts, and actual picker before/after screenshots. Evidence
  and this complete local handoff are retained alongside the implementation;
  final remote HEAD verification confirms their subsequent documentation push.
- Seven verified finding groups fixed: mounted aliases lost through malformed/
  hidden/type/flat-ancestry filtering; unrelated empty readers blocking recovery
  journals; diagnostic-directory substitution; completion overriding method
  counter contradictions; float-rounded malformed percentages falsely completing;
  stale concurrent runner telemetry publication; Tk comparison title mid-word
  wrapping. No method/argv/confirmation/claim/version/surface-boundary relaxation.
- Proof before fixes: private exact-baseline import tree yields67 intended
  failures /34 normal controls across101 new cases; fixed101 pass. Original
  checkout was never reverted or mutated. Every source change has a regression.
- Draft history retained: mounted-root draft missed hidden/flat observations and
  false loop/ram types; extra failing proofs drove effective mount reconciliation.
  Counter draft omitted syncing/retrying/blanking and was corrected after9
  failures against pinned engine semantics. An actual72-DPI fullscreen preview
  exposed the title bug after an early full run started;9 original layout cases
  failed, then passed after the one-line fill-X fix. That obsolete full run was
  deliberately interrupted on its exact owned pytest PID; its missing-JUnit
  failure is not a passing gate. Replacement final run passed after all changes.
- Final local gates: main pytest5,888 pass /14 image-only skips, private Orca1
  pass; combined5,889 unique passes, zero failures/errors. Mandatory GTK result
  guard passes. Lint/types/security/shell/developer-format, preview web/console/
  helper/JS, negative mutation, pinned Go1.26.8 uncached race/vet and350,000 parser
  fuzz executions pass. All12 changed source/test hashes match frozen and
  committed bytes. No source/tests changed after final freeze.
- Fresh no-new-findings evidence: discovery132-case graph matrix; runner1,176-
  case completion matrix and595-test sweep; recovery/report/diagnostics/export
 331-test sweep; primary100 fake wizard sessions/30,000 public actions/10 explicit
  fake starts preserved safety invariants;185 boot/build/compatibility cases.
  All4 isolated Tk startup cases passed. These overlap full tests; do not sum.
- Independent approvals: discovery/recovery216 cases; recovery/diagnostics88;
  final runner242 plus27 cancel/retry cases on hash2979312e...; final Tk UI524
  unique cases across main and supplementary runs (all11 initial dependency/
  isolated-X11 skips resolved). Reviewer summaries are labeled as summaries,
  not fabricated raw terminal transcripts. All temporary fixtures were fake.
- Resolved exploratory setup history: initial wizard harness keyword typo was
  corrected; two baseline fullscreen cases initially lacked isolated-X11 opt-in
  and later ran/passed. Expected missing-fake-device rdev notices are not live
  identity evidence. Existing TODO-regex warning/mypy notes are informational.
- Limits/current publication state: source branch pushed, unmerged, unreleased.
  No hosted CI/PR/ISO/guest/physical-device operation performed. T3 status/open
  worked but snapshot client errored again; no manual web inspection claimed.
  Repository browser regressions and actual Tk navigation passed separately.
  Owned preview HTTP server and Tk/Xvfb sessions were retired. Go native
  inventory override unset; this is not native Windows/hardware qualification.
- Remaining local acceptance/blockers: none. Exact next action, only for a
  selected public candidate, is the existing separate qualification item below.
  Report export can conservatively refuse unidentified/zero-capacity optional
  inventory; large-log recovery can remain indeterminate without retained
  completion evidence. These fail-closed limits are documented, not relaxed.
  Missing shared guide remains resolved by prior owner continue direction.

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
  `de55b078514e2028a2a22633f1d7aa2941f9e0b6` (prior audit implementations
  `ac6ed67c496090c26a9520d0244100ca371ce192`,
  `cdfe9fac6238c8fd3d867c9ef48c4ca3248facce`,
  `af2b6e9c3d053b65e666d807a87207db14521cb2`,
  `57ead7e4304f7f373a0c862ff36335c949f4cf7a` and
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
