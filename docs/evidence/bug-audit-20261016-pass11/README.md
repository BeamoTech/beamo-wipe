# Comprehensive bug audit, pass 11 — 2026-10-16

Repository: BeamoTech/beamo-wipe. Branch: `fix/safety-audit-20261015`.
Worktree: `/root/dev/Beamo Wipe`.
HEAD: `35107a8d1a701093eac876a58ab4efd50e291673`.

Four new defects were proved and fixed. The six earlier local pass8/pass10
fixes, six regression modules and existing evidence are preserved. Three
bounded reviewers covered discovery/authorization, runner/recovery and
UI/boot/build; the primary reviewed report/export/privacy/diagnostics and
independently validated findings. Substantial test campaigns ran sequentially.

Status: final applicable local gates PASS on 738 frozen inputs. Acceptance
and commit/push remain pending on the separately recorded historical SIGTERM
and timing attribution. No publication or real-device operation is authorized
by this evidence.

## Proven fixes

### Observe key releases delivered to the sound modal

Opening the sound dialog with Return or keypad Enter records the press in the
parent's held-key ledger. Native keyboard focus then moves to the modal, whose
release event was never observed by the parent. After closing the modal, the
first fresh press was swallowed as a held-key repeat; only its release rearmed
the parent. Native XTest traces show the actual event routing and lost action.

Each new modal now forwards only key-release events to the existing release
handler. No parent key-press navigation is connected to the modal. Opening,
redraw and close do not clear held state; real release timestamps still guard
equal-time X11 repeat pairs. No token, countdown or Erase-action rule changed.
[Original native trace](ui/native-modal-release-trace.json),
[fixed native trace](ui/fixed-native-modal-release-trace.json).

### Give the startup window native keyboard focus

The startup window set GTK child focus but never presented/focused its native
top-level window. On bare X11 with the pointer outside the window, native focus
remained PointerRoot and real Escape input did nothing. A controlled delete
event was required to close the fake stalled startup. The window now presents
and takes native focus before its accessible status label receives child focus.
[Original native trace](ui/native-startup-focus-trace.json),
[fixed native trace](ui/fixed-native-startup-focus-trace.json).

The fourteen new input/focus cases yielded six intended failures/eight passing
controls on original source, no errors/skips. They cover Return/keypad Enter,
space controls, held keys without release over open/redraw/close, equal-time
review repeat refusal, and pointer-inside/outside startup in both window modes.
Fixed adjacency initially 114 passed; final geometry-inclusive adjacency 122
passed, no skips. All device/engine/audio/power effects are fake or forbidden.
[Original proof](ui/original-final-focus-input.xml),
[final fixed checks](ui/final-ui-adjacent.xml), [UI review](ui/README.md).

### Fill the requested monitor without relying on a window manager

GTK marked both windows fullscreen while their actual allocations remained
900×700 for the wizard and 640×420 for startup on a 1600×1000 display. The live
kiosk starts the application directly through startx without a window manager
to honor that request. Both paths now explicitly size and position the window
to the selected monitor's full geometry before requesting fullscreen. Windowed
wizard workarea clamping and the windowed startup default remain unchanged.

Eight native geometry cases test both surfaces/modes, actual monitor geometry,
and an explicitly injected nonzero origin with a distinct workarea. Original
1600×1000: four failures/four controls; original 800×600: three failures/five
controls, no setup errors/skips. Fixed geometry cases pass at both resolutions.
The origin/workarea variant is an injected fixture, not physical multi-monitor
acceptance. [Original geometry](ui/original-geometry-1600.xml),
[fixed800 geometry](ui/final-geometry-800.xml),
[independent geometry review](discovery/geometry-integration-review.md).

Four unedited full-root captures at 72 DPI were opened and inspected by primary
and independent reviewer. Both surfaces fill the root; Owner footer controls
and startup stages/status fit. At 800×600 the Owner body uses its intended scroll
area. Receipts verify native allocation/origin/fullscreen state, child focus,
X server DPI, image hash, nonblank pixels and owned teardown.
[Wizard800](ui/wizard-fullscreen-800x600-72dpi.png),
[startup800](ui/startup-fullscreen-800x600-72dpi.png),
[wizard1600](ui/wizard-fullscreen-1600x1000-72dpi.png),
[startup1600](ui/startup-fullscreen-1600x1000-72dpi.png).

### Preserve prefixed summary records in large-log assessment

The media parser accepts logger-prefixed Erasure Summary rows and closing
delimiters. The large-log projection retained the header but dropped those
rows/delimiters. A prefixed shortfall changed hidden-capacity warning→pass;
a malformed target row changed unavailable→pass; a dropped closing marker
could move a later row inside the table and change pass→unavailable. Identical
small logs remained consistent. These are advisory defects; completion outcomes
were unchanged. The proof does not claim pinned nwipe naturally emits every
supported prefix variant.

The scanner now uses its existing normalized engine body only to classify
relevant rows and summary-closing markers. It retains exact original records.
Terminal provenance, CR preservation, progress ordering, scan/line/evidence
bounds, log-tail bytes and engine methods/arguments remain unchanged.

Original 81 regressions: 25 intended failures/56 controls, zero errors/skips.
Cases cover all three methods, plain/info/timestamped rows, shortfall/malformed/
complete summaries, prefixed closing boundaries, polling/Stop and exact 1 MiB
boundary±1. Fixed new plus adjacent runner checks: 268 passed, no skips/errors,
including prior progress-order and CR-record-preservation regressions.
[Actual-poll trace](runner/projection-summary-original.json),
[original proof](runner/original-summary-context.xml),
[fixed checks](runner/fixed-adjacent.xml), [review](runner/README.md).

## Independent reproduction and integration

All 735 starting input hashes match the pass10 final receipt. The primary copied
the application/tests to a private import root, restored only the two pass11
changed modules to their exact starting dirty bytes, and checked all 58
application/static hashes. All 103 final new regression cases produce 35 intended
failures/68 passing controls, zero errors/skips, in 14.15 seconds. Shared source
was never reverted. Earlier 95-case proof is separately retained under
`pre-fullscreen-` names. [Script](primary/original-proof.py),
[result](primary/original-summary.json), [JUnit](primary/original.xml).

A 72-case actual fake-process→runner→evidence→owner HTML/text/sharing-copy matrix
covers three methods, three languages, four summary variants and both log sizes.
Full advisory payloads match the direct full-log parser; completion/verification
policy stays consistent; exact tail hashes and unchanged log bytes are checked.
[Script](primary/report-checks-matrix.py),
[result](primary/report-checks-matrix.txt).

Fresh discovery review passed 461 focused cases across 51 modules and 588 bounded
fake inventory cases: ownership/schema, boot sources, hardware aliases and
duplicates. No additional discovery defect was proved. Native acquisition was
guarded. [Discovery review](discovery/README.md), [counts](discovery/summary.json).
The primary report/export/diagnostic baseline passed 173 cases in 3.50 seconds.
[Primary review](primary/primary-review.md), [baseline](primary/baseline.xml).
Focused counts overlap the full gate and must not be added as unique cases.

An initial discovery run included one actual GTK case without DISPLAY:
458 passed, one setup failure, two skips. It is retained; the identical selection
passed 461 with no skips under private 72 DPI Xvfb/D-Bus. Early UI fixture-only
cleanup and cosmetic import variants are retained and hash-disambiguated in
the UI review. No assertion, threshold or safety gate was weakened. Independent
read-only reviews cover the exact fixes and boundary controls:
[initial integration review](discovery/final-integration-review.md),
[geometry review](discovery/geometry-integration-review.md).

## Final local verification and source state

The final local gate exited zero: **6,417 main pytest passes /14 expected
image-only skips** in 530.31 seconds, plus the separate private Orca **one pass**
in 60.086 seconds. The mandatory GTK result guard passed. All eight local phases
exited zero: lint/types/security/shell/developer-format, preview, negative safety,
pinned Go1.26.8 uncached race/vet/350,000 fuzz executions, and full tests.
[Phase status](primary/local-gate-status.json).

[JUnit-derived summary](primary/final-summary.json) confirms **6,418 unique
passes**, zero failures/errors/xfails/duplicate IDs, all 103 new and 112 retained
regressions passed, and the unchanged GTK sound timing case passed. All 738
frozen input hashes match. Direct independent XML counts and source/test
archive byte checks agree. [Independent review](primary/final-independent-review.json),
[frozen inputs](primary/source-freeze.json), [exact delta](primary/delta-review.json).

The fourteen skips are exactly the same two generated live-build configuration
and twelve manufacturing-ISO cases as the previous gate, with IDs/reasons
compared. They remain unrun image checks. The existing literal TODO regex warning
and mypy untyped-body notes are informational. The negative phase intentionally
requires the isolated unsafe mutant to fail and unmodified safety to pass.

The final complete source diff, new regressions and actual artifacts were
reread. Only two existing runtime files changed in this pass and three test
modules were added; no starting input disappeared or earlier test changed.
All owned jobs are retired, and no source changed after the final gate.
Readable transcripts trim trailing whitespace; exact originals, including the
synthetic fixture logs, are preserved in
[original-transcripts.tar.gz](original-transcripts.tar.gz) with
[raw hashes](original-transcripts-sha256.txt). Large synthetic logs stay only
in that compressed archive. The [artifact manifest](artifacts-sha256.txt) and
[verification script](primary/verify-retained.py) cover retained byte identity.
Final retention verification passed: 158 exact original artifacts, 151 retained
artifacts hashed, all 738 frozen files and nine test-module contents match.

Runtime application SHA-256:
`70382edd3f47fba150187014901200bb35c1f76f46a74b4fc35f4fd327a8fb01`.
HEAD remains the baseline above. Application changes and nine new regression
modules (including earlier pass8/pass10 work) remain LOCAL UNCOMMITTED; index
empty. [Exact source patch](primary/source.diff.gz),
[test modules](primary/new-tests.tar.gz). No version pin, claims, discovery,
boot exclusion, token, countdown, method or nwipe argv rule changed.

No actual nwipe, native inventory, physical disk/USB operation, host power or
firmware change, guest, hosted CI, PR, merge, deployment or release occurred.
Native Windows/ISO/QEMU/firmware/physical reconnect qualification remain separate
NOT TESTED work. Source inspections and cross-builds cannot qualify them.

Historical pass8 SIGTERM sender/cause and pass9 timing variation remain
unattributed. This pass's evidence cannot establish their causes. Acceptance
and commit/push remain pending; publication is separately authorized. The exact
next external action is platform execution/signal audit evidence for the original
06:29UTC termination and an attributable failed timing trace. The canonical
[unfinished-work record](../../../.ai/memory/unfinished-work.md) preserves these
limits and local/pushed/deployed state. This bounded review is no bug-free proof.
