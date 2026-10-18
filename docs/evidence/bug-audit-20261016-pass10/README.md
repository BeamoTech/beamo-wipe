# Comprehensive bug audit, pass 10 — 2026-10-16

Repository: BeamoTech/beamo-wipe. Branch: `fix/safety-audit-20261015`.
Worktree: `/root/dev/Beamo Wipe`.
HEAD: `35107a8d1a701093eac876a58ab4efd50e291673`.

This pass found and fixed four proven defects. It started with the two pass8
fixes, their tests, and pass8/pass9 evidence uncommitted; all are preserved.
Three bounded reviewers inspected discovery/authorization, runner/recovery,
and UI/boot/build. The primary reviewed every finding and the report/evidence
integration, reproduced failures independently, and measured sound-dialog timing.

Status: final four-fix applicable local gates PASS on 735 frozen application, test, build,
helper, desktop and workflow inputs in
[source-freeze.json](primary/source-freeze.json). The initial three-fix gate
passed; its receipts are preserved with `initial-threefix-` prefixes. Manual
visual verification exposed the fourth defect, now fixed and independently
reviewed with a visibly correct screenshot. Existing execution attribution
blockers remain separately recorded below.

## Proven fixes

### Preserve exact completion-record contents

Large-log scanning removed all trailing CR/LF characters from each binary
record. The regular small-log path preserves CR. Removing a CR from a malformed
Drive Status banner turned it into the exact banner required for completion
provenance. The same malformed evidence therefore failed below 1 MiB but could
be accepted as completed above that boundary, including a natural-exit-at-Stop
race. The scanner now removes only the single terminal LF. Other record
characters and the preexisting pass8 progress-order fix are preserved.

The proof uses deliberately malformed logs; it does not establish that pinned
nwipe naturally emits CRLF. Genuine LF completion controls still pass. The
[review](runner/README.md) records the boundary and scope. The 45 new cases span
three methods, polling and Stop, LF/CRLF/double-CRLF, CR inside model text and
exact 1 MiB−1/1 MiB/1 MiB+1 sizes. Original: 13 failures/32 passing controls.
Fixed new and adjacent runner/recovery checks: 412 passed, no skips or errors.
[Original proof](runner/record-ending-original.txt),
[fixed adjacent checks](runner/runner-fixed-adjacent.txt).

### Replace inventory overlays when opening console diagnostics

From an empty disk list, B/O opened read-only boot/other-device inventory.
D changed the controller screen to diagnostics while leaving that inventory
covering the body and footer. R could then prompt for report preparation before
the diagnostic instructions were visible. The existing diagnostic navigation
branch now clears its local inventory-overlay flag, as refresh already does.

The 22 new terminal cases include upper/lowercase B/O/D, prompt visibility,
ignored R/Q, Escape closing only inventory and F5 replacing it with refresh
confirmation. Original: 10 failures/12 passing controls. Corrected new and
adjacent console checks: 107 passed, no skips or errors.
[Original proof](ui/original-console-inventory.txt),
[fixed checks](ui/fixed-console-adjacent.txt), [review](ui/README.md).

### Keep sound selection consistent after failed changes

After a refused, errored, expired or cancelled output change, GTK still
highlighted the requested output while volume/mute commands targeted the
previous accepted output. The highlighted radio also could not be clicked
again to retry. The dialog now stores the accepted radio object and restores
it under a toggle guard before reenabling controls. Successful changes update
the accepted output/radio/preference together. Closing clears the reference
and discards late results. Rollback issues no extra audio request and does not
claim to change the operating system's output.

Actual GTK proof used real radio controls and a dedicated AudioWorker with
all audio calls fake: the original ten cases yielded eight failures/two passing
success/close controls. The final eleven cases also cover duplicate labels;
restoration uses widget identity. Corrected sound/GTK/audio/overlay adjacency:
86 passed, no skips or errors; the final eleven passed separately. An independent
reader approved callback guarding, restore ordering, success and close behavior.
[Original proof](ui/original-sound-selection.txt),
[fixed checks](ui/fixed-sound-adjacent.txt),
[independent integration review](discovery/integration-review.md).

### Keep the sound modal visible and return keyboard focus on bare X11

The generic GTK button callback redraws the parent after its action. Redraw
unconditionally presented and focused the parent, covering the sound dialog
immediately after opening it and again during sound/report updates. Without
a window manager, GTK's transient/modal flags do not enforce native stacking.
The live kiosk launches the application directly through startx, so this
bare-X11 behavior matters to the shipped path. Closing a correctly raised
dialog also left native focus at the X root and no live parent child focus.

The renderer now closes a modal whose wizard screen/epoch is obsolete, routes
presentation/focus to a valid active dialog, preserves its child focus through
parent redraws and returns focus to the current wizard heading after close.
Application close prevents parent refocus. Stop and the model's existing
review-overlay/countdown behavior remain unchanged.

The original eleven native XQueryTree/XGetInputFocus cases yielded nine intended
failures/two controls. Strengthening close checks on the initial draft exposed
two missing live-parent-focus assertions, with app-close control passing; the
repair restores the current arrival widget. The final fourteen new cases cover open,
reopen, redraw on Owner/Working/Review, real tick revision, preserved child
focus, close, epoch revisit, countdown, Stop and app close. Corrected affected
adjacency: 87 passed, no skips/errors. The explanatory bare-X11 comment was
added after adjacency; removing exactly that comment reproduces its tested
source hash. The final gate freezes the actual final bytes.
[Original proof](ui/original-modal-stacking.txt),
[draft close-focus proof](ui/modal-live-parent-focus.txt),
[fixed adjacency](ui/final-modal-adjacent.txt),
[independent lifecycle review](discovery/modal-lifecycle-review.md).

## Independent reproduction and integration

The primary copied the application into a private import root and restored the
three changed modules to the exact starting dirty source, preserving pass8.
All 52 starting application-module hashes match the pass9 baseline manifest.
The final **78 new cases produce 32 intended failures /46 passing controls**,
zero setup errors or skips. The shared checkout was never reverted.
[Reproduction script](primary/original-proof.py),
[original log](primary/original.txt), [counts](primary/original-summary.json).

All **98 new and existing uncommitted regression cases pass** on the corrected
source. [Fixed log](primary/fixed-regressions.txt),
[JUnit](primary/fixed-regressions.xml). Existing tests were not weakened.

A separate 54-case fake-process → runner → evidence → result check covers all
three methods, three languages, both log-size paths and LF/CRLF/double-CRLF.
It confirms consistent success/refusal, verification policy, exact tail hashes
and unchanged log bytes. [Script](primary/report-provenance-matrix.py),
[result](primary/report-provenance-matrix.txt).

The primary independently runs all fourteen final modal regressions against the exact
initial three-fix source, checking all 58 source/static hashes before running:
10 intended failures/four passing controls, zero errors/skips.
[Script](primary/original-modal-proof.py),
[result](primary/original-modal-summary.json). No shared source was reverted.
The final full gate executed and passed all 92 pass10 regression cases.

Fresh discovery/safety review passed 425 cases across 49 modules, no skips or
errors. Fake guards intercepted inventory/mount/cmdline probes and prohibited
native acquisition. Source review covered malformed ancestry, boot provenance,
aliases, metadata, tokens, consent snapshots, rediscovery and argv/method bounds.
[Review](discovery/README.md), [result](discovery/focused-summary.json).
Counts in these focused runs overlap the final gate; do not add them as unique.

## Timing investigation and retained setup history

The existing five sound regressions passed with measured wrapper calls before
and after the fix. Constructor wall times were about 4.1–6.4 ms before and
5.0–8.1 ms after; worker submission remained below 0.5 ms in the initial profile.
The trace records wall/thread CPU time, context switches and worker-thread
activity. Tests retain their original 60 ms limits. These measurements do not
attribute the earlier pass9 timing misses or the pass8 SIGTERM.
[Initial measurements](primary/sound-profile.json),
[final measurements](primary/sound-profile-after.json).

All substantial suites in this pass run sequentially. The final canonical
script retains its prescribed separate private Orca and main sessions, with no
auxiliary GUI/Go/generated campaign alongside them. Private D-Bus/XDG runtimes
and Xvfb at 72 DPI are used. No performance assertion or gate was relaxed.

A discovery harness initially used system Python without pytest; it ran no
tests. The corrected run used the existing pinned audit venv. The primary's
first fixed console trace had an incorrect case-sensitive footer literal;
that harness failure is retained and corrected against the actual displayed
copy. New GTK test lint initially flagged an imported fixture name; helper
naming and the repository's existing fixture-noqa convention corrected it,
with no assertion removed. All final original proofs have zero setup errors.

Initial native-window capture was black; a corrected full-root capture showed
the actual occlusion and led to the fourth fix. Both pre-fix artifacts are
preserved. The repaired full-root 72 DPI capture now visibly shows the restored
accepted output, exact failure message and retry/Close controls above the
wizard. Native stacking/input focus and GTK status child focus also pass;
owned window/worker teardown completes. Primary opened and inspected the image.
[PNG](primary/modal-visible-rollback-72dpi.png),
[state receipt](primary/modal-visible-rollback-72dpi.json),
[visual review](primary/modal-visual-review.md).

One post-fix helper tried GdkMonitor dimensions, which report synthetic 96 DPI
for the Xvfb monitor. Its failed assertion/script/log/exit are retained; it
did not produce an accepted capture. The corrected helper reads the X server
screen dimensions directly through Xlib, verifies 72.0567/71.9547 DPI, and passes
without the older GdkScreen deprecation warnings. No product source changed
for this instrumentation correction.

## Final local gates and publication state

The final four-fix local gate exited zero: **6,314 main pytest passes /14
expected image-only skips** in 518.00 seconds, plus the separate private Orca
**one pass** in 66.067 seconds. The mandatory GTK result guard passed.
[JUnit-derived summary](primary/final-summary.json) confirms **6,315 unique
passes**, no failures/errors/duplicate IDs, all 92 new cases and 20 retained
pass8 cases passed, and the unchanged sound timing case passed. All 735 frozen
input hashes match. A separate direct XML/source review confirms the counts,
source patch hash and empty index:
[independent final review](primary/final-independent-review.json).

The fourteen skips are the exact same two generated live-build configuration
cases and twelve manufacturing-ISO cases as the initial gate; every ID/reason
was compared. They remain unrun image checks, not passing checks.

Before manual visual verification exposed the fourth defect, the initial
three-fix gate passed 6,300 main cases plus one private Orca case. It cannot
qualify the later source change; its exact receipts remain separately
preserved under `initial-threefix-` names, including
[its summary](primary/initial-threefix-final-summary.json).

[Local phase status](primary/local-gate-status.json) records zero exit codes
for lint/types/security/shell/developer-format, preview, the negative safety
phase, pinned Go1.26.8 uncached race/vet and 350,000 fuzz executions. Native
inventory override stayed unset. No dependency installation or upgrade was
needed. Runtime application SHA-256:
`c0196a53381b5d3235b5f7cdd764d47b5ee074c2f684d18a26bb7c8183e8efcd`.

HEAD remains the baseline. The five changed application files (including the
preexisting pass8 diagnostic fix) and six new regression modules remain LOCAL
UNCOMMITTED; index empty. Exact [source patch](primary/source.diff.gz) and
[test-module archive](primary/new-tests.tar.gz) preserve the reviewable work.
No existing test was edited. Final source diff and all new test modules were
reread; normal, malformed, boundary, failure, Stop, retry and close paths are
covered by the retained proofs and full gate.

Readable transcripts trim trailing whitespace; the exact original bytes of
all collected artifacts are preserved in
[original-transcripts.tar.gz](original-transcripts.tar.gz) with
[their hashes](original-transcripts-sha256.txt). Source/test archive contents
were compared byte-for-byte with the frozen working files.
[Artifact manifest](artifacts-sha256.txt) covers every retained artifact;
[verification script](primary/verify-retained.py) checks the archives, source
freeze, empty index and diff whitespace. No source changed after the final gate.
Final retention verification passed: 149 exact original artifacts, 152 retained
artifacts hashed, all 735 frozen inputs and six test-module contents match.

The literal TODO detection-regex warning and mypy untyped-body notes are existing
informational output. The negative phase intentionally requires the private
unsafe mutant to fail, then confirms that unmodified safety passes. That mutant
failure is the expected successful gate behavior.

No actual nwipe, native disk inventory, physical disk/USB operation, power or
firmware change, guest, hosted CI, PR, merge, deployment or release occurred.
Native Windows, ISO/QEMU, firmware and physical media/reconnect qualification
remain separate NOT TESTED work. No version pin, claims, method, token,
countdown, boot exclusion or argv boundary was changed.

Acceptance and commit/push remain pending on the prior unexplained execution
results: original pass8 SIGTERM attribution and pass9 timing variation. This
pass's measured normal behavior cannot establish their causes. Do not infer
permission to publish from tests or saved notes. The canonical
[unfinished-work record](../../../.ai/memory/unfinished-work.md) tracks the exact
next actions and local/pushed/deployed state. This bounded audit is no proof
that the product is bug-free.
