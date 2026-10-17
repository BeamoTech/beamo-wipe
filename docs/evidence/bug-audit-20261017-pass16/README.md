# Beamo Wipe bug audit — 2026-10-17, pass16

Four independently proved bugs are fixed locally, with 398 new regression cases.
All applicable local gates pass. Overall acceptance remains **BLOCKED** pending
review of the failed test-launch boundary incident and historical pass8
signal/pass9 failed-timing attribution; later passing checks
cannot explain those original events. Separate image/native/physical release
qualification remains NOT RUN/BLOCKED. No commit, push, PR, hosted job or release.

Repository: BeamoTech/beamo-wipe, `/root/dev/Beamo Wipe`.
Branch: `fix/safety-audit-20261015`.
HEAD: `35107a8d1a701093eac876a58ab4efd50e291673`.
Final runtime SHA-256: `008add544330133a4cf979d39327dae3ccfd341925cb897b8ca19c23f983d2ab`.
Freeze of 754 inputs: [source-freeze.json](primary/source-freeze.json).
744 of 751 starting inputs remain unchanged; only three runtime files and four
existing fixtures changed. The 27 prior local bug fixes, 22 prior modules / 1,365 cases
and earlier evidence are preserved; retained/new regressions total 1,763 cases in
25 untracked modules. The index remains empty. Eventual commit requires `safety:`.

## Verified defects and repairs

| ID/status | Original evidence and resulting repair |
| --- | --- |
| P16-1 / locally fixed | A malformed duplicate physical observation could be filtered away, leaving one apparently unique target despite contrary valid display/layout metadata. Track repeated canonical physical paths before filtering and refuse when exactly one selectable row survives. Complete identical target duplicates stay two; boot/RO duplicates and unrelated malformed rows retain their contracts. |
| P16-2 / locally fixed | Kernel-command-line optical boot identity bypassed competition with other physical media; disk hits also omitted competing ROMs. Both hit and competition checks now include whole disk/ROM observations. Authoritative live mounts still precede fallback; zero-size competitors stay noncompeting. |
| P16-3 / locally fixed | A modal Escape key-down was absent from parent hold tracking, so auto-repeat after dialog closure became a separate parent navigation/Stop action. Modal and parent presses share the original guard bookkeeping; modal presses never dispatch parent navigation. Release and same-timestamp repeat semantics remain conservative. |
| P16-4 / locally fixed | Redraw or teardown deleted widget-owned Tcl callback commands while their after/idle events stayed queued, producing invalid-command errors. Cancel only exact Python callback scripts owned by the retiring subtree, through the actual owner. Persistent container/root jobs survive redraw; full root jobs retire on teardown; peer interpreters remain untouched. |

Incremental repairs: [pass16-source.diff](primary/pass16-source.diff).
Accumulated source patch: [source.diff.gz](primary/source.diff.gz).
Exact archive of 25 test modules: [new-tests.tar.gz](primary/new-tests.tar.gz).
Four fixture corrections and preserved assertions:
[pass16-fixture.diff](primary/pass16-fixture.diff).
No method/argv/owner/token/countdown/engine pin/claims/launcher/build/publication
input changed this pass. No wipe engine was added or executed.

## Original proof and controlled corrections

Root independently replayed the final 398 tests against 58 exact starting
source/static files in a private copy; shared source was never reverted.
**203 intended AssertionError failures / 195 controls / 0 errors / 0 skips**:
159 discovery refusals, 18 modal key cases, 26 explicit Tcl-bgerror cases.
All 26 final Tk failures explicitly identify invalid Tcl callbacks, rather than
an unrelated focus assertion. See [original-summary.json](primary/original-summary.json),
[original.xml](primary/original.xml), [original.txt](primary/original.txt) and
[original-proof.py](primary/original-proof.py). The independent native replays cover six Escape cases and three callback cases. The default-bgerror trace maps
the exact callback registration, old Entry owner, pending after ID, redraw,
deleted command and eventual default Tcl error; no error-modal focus claim.

The fresh 49-module baseline ended with 1,676 passes, seven existing 140 ms startup focus failures and zero errors/skips.
The mapped-frame diagnostic reproduced two 140 ms races and settled by 300 ms;
it does not individually attribute all seven initial frames. Existing fixture
now starts the same 140 ms observation after the actual mapped startup redraw,
retains every focus/state/countdown assertion, and fails a missing-draw watchdog.
Two AST-only GTK fixtures bind the extracted actual shared guard; every prior
assertion is unchanged. No safety assertion or test was removed or skipped.

Retained failed/corrected history:

- Initial new Tk fixtures forced root focus after an update and later resized
  after preparing callbacks. These setup artifacts obscured 13 then 3 failures;
  native focus/geometry now precedes callback preparation, every assertion stays.
- First combined adjacency: 2,073 PASS / 8 FAIL. Five new fresh-key controls sent
  release/press in the same server millisecond. The new fixture keeps the
  conservative guard, adds a 20 ms release gap and asserts distinct observed
  timestamps. Synthetic equal-timestamp cases remain unchanged. Three remaining
  Tk navigate-idle fixtures now set final geometry before mapping. Final affected
  UI 119 cases PASS, 0 error/skip.
- One private replay setup selected default Xvfb :99; 47 new fixtures refused it
  before effects. Corrected to a new owned display starting 150. No shared X11
  display was changed. Initial setup receipts are retained, not counted as passes.
- Initial full lint stopped on two type errors in the new helper. Runtime Tk's
  private registry is obtained with `getattr` and an optional lookup uses its own
  variable. No type ignore or behavior relaxation; re-frozen full gate rerun.
- One full suite run used a space-bearing venv executable path. CI fake tools
  generated invalid Linux shebangs. Exact failures, harmless interpreter/shebang
  probe and final no-space alias receipts distinguish this environment issue
  from a product defect. The alias uses the same existing interpreter, packages
  and venv; no install, product change or assertion relaxation. The full failed
  run was 23 FAIL / 7,942 PASS / 14 skips, plus one Orca PASS. 22 cases were launch setup; the
  remaining Tcl-only picker fixture needed an accurate leaf winfo_children
  method. All 23 exact failed IDs pass with the corrected interpreter, fixture and
  rejecting fallback guards before the full rerun.
- A guard then blocked the legitimate local gcloud file-list test. Its exact
  failure is retained. Root intentionally stopped only owned pytest PID 36787:
  SIGINT 03:21:42.296955 UTC was ignored by the inherited background disposition;
  SIGTERM 03:22:25.187569 UTC ended it. Wrapper exit 1; no fresh main JUnit, and the
  stale older report is explicitly rejected. Tracked child and pytest both
  exited. This attributed interruption is distinct from historical pass8.
  The final guard permits only canonical owned private pytest upload trees with
  fresh matching configuration and disables credentials/telemetry/update checks.
  Installed SDK source and an independent peer confirm the command is local
  file listing. Twelve intercepted authority cases and the actual local test
  pass. Final gate starts with deleted old owned JUnit reports and verifies
  freshness; denied remote/privileged fallback attempts remain zero.

A derived receipt verifier initially assumed a JUnit failure type attribute;
Pytest 9 omits it. The corrected observer authenticates each traceback ending
with AssertionError. Source, tests and passing gate are unchanged. Prepared
diagnostic scripts without an execution receipt were not run.

All initial/intermediate scripts, logs, JUnit and freezes are retained with
explicit prefixes. Setup-observer corrections (Tcl empty interpreter path and
callit code-name registration) are distinct from product/gate passes. No 80 ms
deliberate product timer exists. No unexplained stop/kill/termination occurred
this pass. Historical pass8/pass9 blockers are separately preserved.

## Final verification and actual artifacts

All nine local phase exits 0 on the exact final freeze/config. Commands, UTC
times and logs: [local-gate-status.json](primary/local-gate-status.json),
[run-gates.py](primary/run-gates.py), [final-summary.json](primary/final-summary.json).

| Check | Result |
| --- | --- |
| Syntax, full lint, types, security and shell checks | PASS; 52 typed source files. Existing TODO scanner's regex-constant match and annotation-unchecked notes are informational, not missing tests or product warnings. |
| Fake preview and negative boot-exclusion mutant | PASS; generated HTML, all-language JavaScript, console/helper checks; required missing-exception mutant failure confirmed. |
| Go 1.26.8 uncached race, vet, 350,000 fuzz executions | PASS; fake firmware only. |
| Windows AMD64 test cross-build | PE32+ AMD64, 9,021,440 bytes, SHA-256 `d05ac4db6463aa6d7f51188f3bcfcfb4891aeab549ab481843538114904a76d9`. Cross-compilation only; native acceptance NOT RUN. Binary remains outside git at `/tmp/pass16-primary/desktop-windows.test.exe`. |
| Canonical separate main/Orca private 72 DPI sessions | **7,966 unique PASS / 14 same image-only skips**, 0 failure/error/xfail/duplicate IDs. All 398 new and 1,365 prior regression cases pass. Unchanged sound timing test passes. |
| Final fresh runner matrix | 153 short semantic/projection cases, 153 actual >1 MiB fake polls, 90 evidence/export-readiness/recovery roundtrips with authenticated suffix-tamper refusal; 0 mismatches/semantic errors/native acquisitions. 54 mixed-advisory traces are explicitly nonfindings. |
| Final cancellation/retry matrix | 144 cases across 3 paths / 3 methods / 2 completion states / 8 stop modes. Real ordinary-file flock/log FDs retained during uncertain stop; released only after confirmed terminal state. Fake process operations only; no OS PID signals. |
| Final native geometry | 270 Tk/GTK cases across 3 languages / 3 text sizes / 15 screens; all pass, 0 effects/callback errors. 27 critical Tk keyboard/owner/token controls fully visible. Five actual PNGs independently viewed. |
| Final reports/export/privacy | 90 cases across 3 methods / 3 languages / 5 count states / 2 log sizes. 70 actual bundle files/manifests authenticated; five owner/share/result/HTML bundles inspected. Preview 185,540 bytes, SHA-256 `5492d76fb06bee55066b55cc305c66bd6149514d3367456337f045032f752880`. |

The exact 14 skip IDs/reasons match pass15: two generated live-build config checks
and 12 manufacturing-ISO checks. They remain skips, not image/native passes.
No auxiliary runtime campaign overlapped the canonical main/Orca gate.
Fresh final campaigns ran sequentially afterward; exact commands/exits:
[final-campaign-status.json](primary/final-campaign-status.json).
All 153 large logs and 90 evidence/sidecar pairs (333 files) are authenticated and
compressed in [runner-final-fixtures.tar.gz](primary/runner-final-fixtures.tar.gz).
Original pre-fix fixtures remain in a separate archive. Actual report bundles:
[report-artifacts.tar.gz](primary/report-artifacts.tar.gz).
Artifact checks: [campaign-verification.json](primary/campaign-verification.json),
[artifact-review.json](primary/artifact-review.json).

Three bounded source reviewers approved their exact final assignments. Root
independently reviewed the union, all original failures, full accumulated diff,
source/test/fixture preservation, actual artifacts, JUnit uniqueness/skips,
checksums and empty index. Reviews: [discovery](discovery/final-source-review.md),
[runner/evidence](runner/final-source-review.md), [UI/boot](ui/final-source-review.md).
These source reviews do not replace the runtime receipts or platform acceptance.

## Boundaries, remaining acceptance and next action

Final verification uses fake metadata/processes, ordinary temporary files and
owned private 72 DPI X11/DBus, plus rejecting child-PATH fallback guards with zero
attempts. The failed space-interpreter run escaped its fake executable stubs:
public metadata was downloaded (eight temporary fixtures), system xorriso ran on an ordinary temporary file, and three unmocked
loop probes reported successful regular-file attachments
and ownership-checked cleanup. Empty fake bookkeeping was initially misread as
zero attachments; that statement is corrected. Exact original loop IDs were not
retained. Follow-up read-only losetup inventory found no matching fixture
backings or remaining fixture-prefix directories; it did not detach anything. See
[failed-environment-boundary-audit.json](primary/failed-environment-boundary-audit.json).
No physical device was supplied as a wipe target and no erasure occurred. No
hosted job, login, external message, physical media/firmware/power
change, guest or passthrough operation was performed. No
Companion or USB Easy Use change. Current AGENTS/remote-host constraints apply;
the absent shared guide is recorded with the existing owner continuation.

Still required for audit acceptance: review the recorded failed-run boundary
incident and corrected guard evidence, plus attributable platform execution/signal
evidence for pass8's 06:29 UTC SIGTERM/exit 143, and the unavailable original pass9
failed timing trace. Obtain those records and reconcile them; later passes do
not supply their cause. Revalidate exact source/config after any further change,
then commit/push with `safety:` only when required acceptance is satisfied.
The canonical record is [BW-BUG-AUDIT-20261017-PASS16](../../../.ai/memory/unfinished-work.md).

ISO/QEMU, native Windows, actual hardware/firmware/boot media and physical
reconnect qualification remain **NOT RUN/BLOCKED** here. Use the separately
authorized disposable isolated worker and existing qualification records when
those prerequisites exist. No publication was requested or performed.

Every flat original/intermediate/final receipt has an exact copy in
`original-transcripts.tar.gz` and a checksum index. Final retained-file hashes
are in `artifacts-sha256.txt`; exact source/test/patch/archive readback and index
verification are in `primary/retention-verification.json`. These records prove
the stated local checks, not missing platform acceptance or deployment.
