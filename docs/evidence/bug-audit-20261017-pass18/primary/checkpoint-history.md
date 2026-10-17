# Pass18 prior checkpoints

## BW-BUG-AUDIT-20261017-PASS18 — IN PROGRESS (fresh audit; previous acceptance blockers retained)

- Date/author: 2026-10-17 / Codex. Request: another comprehensive pass.
- Repo/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`; branch
  `fix/safety-audit-20261015`; HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
- Baseline: 762 source/test/build inputs exactly match final pass17 freeze;
  all previous uncommitted fixes/tests preserved; index empty.
- Work: three bounded source audits (discovery/safety, runner/recovery,
  UI/boot/build), primary harness isolation and reports/audio/power review.
- Checkpoint: all762 starting inputs match finalpass17; no-space interpreter
  and12 guard admission probes pass. Baseline3,190PASS/0skips.
  Original280-case proof: pathless physical alias208=96AssertionErrorFAIL/112
  controls; curses rendered-review72=9AssertionErrorFAIL/63controls;0errors/skips.
  Root reviewed raw frames/assertions; shared product remained unchanged for proof.
  Minimal fixes authorized in discover.py and console_wizard.py; exact regression
  bytes frozen. Native Tk variable-trace lifecycle hypothesis is being prepared,
  not yet a finding. No product change for that hypothesis before root proof.
- Further checkpoint: additional52-case original proof gives32AssertionErrorFAIL/
  20controls,0errors/skips: malformed pathless32=16FAIL/16controls; Tk trace20=
  16FAIL/4controls. Explicit TclError on variable updates after row destruction
  and retained row/variable weakrefs prove the lifetime bug. Initial evidence-local
  probe collection failed because harness replaced PYTHONPATH; rawerror retained,
  corrected src+tests import path before proof. No assertion changed.
- Three proved fixes now frozen: discovery safety-only pathless hardware facts
  plus candidate uncertainty; curses displayed-ready action gate; exact per-row
  Tk trace retirement. RuntimeSHA256
  `bebdb2425c6135dc79ad9dd37c89d4995173a8ffc8183edb4515cb1c726f89b7`;
  766inputs, exactly3runtimechanges/4newmodules332cases; prior759inputs unchanged.
  Focused/adjacent runtime active. Runner source review found no new proved bug;
  exact pinned nwipe/bookworm libparted source verifies relevant record origins.
- Final pre-gate checkpoint:1,062focused/adjacentPASS/0skips. Exact private replay
  of all332finalcanonical regression bytes on starting source gives137AssertionError
  FAIL/195controls,0errors/skips/deselections. Source never restored in shared tree.
  Independent seven-input peer review matches freeze. First8 final local phases
  pass; full canonical main/Orca running, not yet accepted. Final fake campaigns
  and artifact readback pending. Source frozen without further product/test edits.
- Full-gate checkpoint: one failure marker observed near existing GTK audio
  responsiveness cases; exact final traceback pending. Candidate must not be
  accepted/retried blindly. Main continues normally; Orca reports1PASS. Read-only
  resource sample records2CPU/load~4/highCPUpressure but does not attribute the
  failure. Source-only review found audio discovery asynchronous; timed GTK
  construction/event-drain and first-assertion fixture cleanup require exacttrace.
  No assertions weakened or auxiliary runtime overlapped canonical phase.
- Remaining acceptance: prove any new candidate before changing product code,
  regressions/adjacent cases, complete applicable local gate, final source and
  artifact review. Use no-space interpreter and rejecting child-PATH guards.
- Blockers retained: pass17 loop-test boundary incident review, pass8 original
  unexplained SIGTERM and pass9 original timing trace. ISO/QEMU/native Windows/
  physical/firmware acceptance remain NOT RUN/BLOCKED on this host.
- Next action: validate harmless interpreter/guard probes, then serialize fake
  runtime campaigns. No commit/push/hosted job/release authorized by evidence.
- Evidence/result in progress: `docs/evidence/bug-audit-20261017-pass18/`;
  `/tmp/pass18-primary/` is working staging, retained before handoff.


