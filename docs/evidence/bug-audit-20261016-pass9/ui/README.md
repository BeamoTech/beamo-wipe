# Pass 9 UI / boot bounded audit — 2026-10-16

Repository: BeamoTech/beamo-wipe; branch fix/safety-audit-20261015;
HEAD 35107a8d1a701093eac876a58ab4efd50e291673; shared worktree
/root/dev/Beamo Wipe. Existing pass8 edits preserved. No source edits by this audit.

Read AGENTS.md, relevant memory/unfinished record, wizard launch/stop/tick/refresh/
shutdown state transitions, Tk keyboard guards/close/teardown and countdown,
GTK keyboard/timer/failure paths, plain-console terminal-loss recovery, curses
paging/modal/held-key dispatch, shipped kiosk supervisor power and retry guards,
boot menus and ISO wrapper provenance/output-preservation gates.
/root/dev/AGENTS.md does not exist in this environment.

No new source defect proved. Fake-only focused tests completed 215 cases with
100% dots/no failure indicators (focused-tests.txt; double quiet removes summary).
Toolkit tests initially ran without the repository's private suite runtime and
exposed the known AT-SPI stale /run/user/0/at-spi/bus warning; preserve original
failure output toolkit-tests.txt. Corrected private runtime run is recorded in
toolkit-private.txt and toolkit-private.xml, exit in toolkit-private.exit.

Fake Tk preview capture script capture_preview.py completed exit 0 using private
Xvfb 1600x1000 at 72 DPI; window 1000x760. Nine screenshots show splash, owner,
picker, token confirmation, methods, final review, working, stop consent, and
interrupted preview result. Visually inspected picker, final review, interrupted
result; protected boot card and fake-mode banner visible, explicit disabled
Erase button during fresh five-second review, scrolling preserves footer actions.
preview.txt records model state and expected fake /dev missing rdev diagnostics.
No engine subprocess or actual disk operation ran.

No physical/device, local guest, native Windows, ISO/QEMU, hosted build,
commit/push or publication action. Such platform acceptance remains unrun here.

Checkpoint: corrected private run also has one unresolved failure around
case 167, corresponding (from toolkit-collected.txt) to
`tests/test_accessible_runtime.py::test_slow_sound_discovery_does_not_block_gtk_or_update_closed_dialog`.
Do not classify the private run as passing or attribute this failure to AT-SPI.
Await final traceback. The test has <60ms timing bounds and a 1s thread event
bound; multiple pytest/Go jobs were concurrently active, but load is only an
unproved hypothesis pending the failure trace. No assertion/test/source change.

Original toolkit run finished exit 1. Exact failures:
- external AT-SPI quick-zero client aborted -5; its trace explicitly reports
  missing `/run/user/0/at-spi/bus` (shared-runtime setup issue).
- slow sound discovery dialog click took 0.076446527 seconds against <0.06s
  at `tests/test_accessible_runtime.py:1620`; this is a measured timing failure,
  not proof of blocking I/O/root cause. Private run trace still pending.

Corrected private runtime suite finished: **1 failed, 623 passed, 7 skipped**,
308.94s; pytest exit 1 (toolkit-private.exit, toolkit-private.xml). The sole
failure is the same dialog-click <60ms assertion with measured 137.614432ms.
The external AT-SPI quick-zero case passed under private runtime. The seven
skips are Tk isolated-X11 checks requiring BEAMO_ISOLATED_X11_TEST=1.
Parent owns the complete local gate, which has progressed beyond this same
sound test without a failure; final JUnit receipt must confirm that pass.
Pending next action after parent full gate retires: run one isolated focused
sound-dialog adjacent group under private runtime, 72 DPI and
BEAMO_ISOLATED_X11_TEST=1. No test/source assertions changed. CPU/scheduling
causality is not established merely by contemporaneous other jobs.

Final focused adjacency check after the parent full gate retired: private runtime
and 72-DPI Xvfb, BEAMO_ISOLATED_X11_TEST=1, no concurrent primary-owned test/Go
jobs. Existing sound-dialog tests (three dialog behavior cases, the slow-discovery
responsiveness/closed-dialog case, and automatic done-sound case): **5 passed,
164 deselected, 0.70s**, exit 0. Evidence sound-isolated.txt/xml/exit. No tests,
thresholds, production code or assertions changed. Source review confirms slow
`list_outputs` executes through AudioWorker._run; SoundDialog construction submits
it and never joins that worker. This and the passing focused check do not prove
the cause of the earlier 76.45ms/137.61ms threshold misses. Timing variability
in those parallel auxiliary batches remains observed but unexplained.

Parent reports its complete prescribed local gate retired exit 0: 6222 passed /
14 image-dependent skipped plus separate Orca passed. Its JUnit confirms the
specific timing case exactly once passed and final source/test hashes unchanged.
The private toolkit failures remain retained diagnostic evidence, not passing
runs. No new proven source defect was changed in this bounded audit.
