# Pass 10 UI, terminal, boot/build review

2026-10-16 / Codex child `pass10_ui_boot`; worktree `/root/dev/Beamo Wipe`,
branch `fix/safety-audit-20261015`, starting HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`.

Reviewed current AGENTS.md, memory index, canonical unfinished-work record,
wizard authorization/countdown/overlay/stop/shutdown/report/refresh lifecycle,
Tk and GTK event/worker teardown, plain and curses fallback, sound dialog,
startup stages, live kiosk supervisor/entrypoint/service, build bootstrap and
claims. Shared `/root/dev/AGENTS.md` is absent; existing record states the
owner previously authorized continuation without it. Preserve pass8 source
changes and pass8/pass9 evidence.

## Proven and fixed: stale curses inventory overlay hides diagnostics

On fake empty discovery with protected boot and other-device inventory, B/O
opens a read-only inventory overlay. D transitions Wizard to DIAGNOSTIC but
the inventory body/footer stay visible. R then can ask to prepare a report
over that inventory instead of displaying the diagnostic instructions.

Original fully stubbed proof: `console_overlay_trace.py` fails its diagnostic
notice assertion; exact rendered frames and assertion retained in
`original-console-overlay-trace.{json,txt}`. Original regression proof:
`original-console-inventory.{txt,xml}` = 22 unique cases, 10 intended failures,
12 controls pass, zero errors/skips. Parent independently reproduced and
approved the narrow fix. One source line clears `inventory_open` in the
existing D navigation branch. No model/authorization/countdown changes.

Corrected new plus adjacent console/review/fallback/terminal-loss/held-key/
report-save regressions: `fixed-console-adjacent.{txt,xml}` = 107 unique PASS,
zero failures/errors/skips. `console-summary.json` records XML-derived counts.
New regression file: `tests/test_console_inventory_diagnostic_pass10.py`.
R/Q remain ignored in inventory, Escape closes only the overlay, F5 replaces
it with the refresh confirmation; all controls passed.

## Proven and fixed: failed sound output selection disagrees with controls

The requested GTK radio stays active after set_output refuses, raises,
expires, or is cancelled. Internal chosen remains the prior output; Louder
and Mute affect that prior output despite the newly highlighted radio.
Selecting the same highlighted radio also cannot retry because GTK sees no
state change. Failure text alone does not reconcile the selected output.

Fully stubbed proof: `sound_failed_selection_trace.py` exits 1;
`original-sound-selection-trace.{json,txt}` shows visible headphones while
volume targets speakers. Parent independently reproduced. Actual GTK proof
with real radios and dedicated AudioWorker, all sound calls fake, private
XDG runtime/D-Bus/Xvfb at 72 DPI: `original-sound-selection.{txt,xml}` =
10 cases, 8 intended assertion failures, 2 success/close controls pass, no
setup errors or skips. New file `tests/test_sound_output_selection_pass10.py`.

After parent independently reproduced and reviewed the actual GTK red proof,
implemented the approved narrow fix: retain the last accepted radio object,
restore it under a toggle guard after explicit/generic failure, update the
reference only on accepted success and clear it on close. Failure restoration
or successful choice update precedes controls reenable. No labels, extra
audio calls, or retry loops. Original `sound_dialog.py` SHA-256
`e847d67c57c078021db32822e95992fd14aa1be6721874b1d520f01b72e0a1cf`;
corrected SHA-256
`dec869b260dfc13b9b93d19f1face4d2c5fa870e8f9b0bf1fc07fa8f82186ed5`.

Actual GTK corrected 11 cases (original ten plus duplicate-label control) and
adjacent sound/audio worker/GTK review/countdown/overlay cases: 86 unique PASS,
no failures/errors/skips in 5.88 seconds; raw logs and JUnit in
`fixed-sound-adjacent.{txt,xml}`. An initial focused Ruff check identified five
F811 imported-fixture name collisions in the new test; corrected to the
project's existing fixture-noqa convention and renamed the local helper's
parameter. Source behavior and test assertions unchanged. Corrected focused
Ruff check passes (`lint.txt`); final eleven actual GTK cases rerun PASS in
`fixed-sound-final11.{txt,xml}`. Parent independently reviewed accepted-radio
identity, toggle guard, failure ordering and close behavior and approved the
implementation. `source-final-summary.json` records the final four file
hashes and final eleven-case counts. No further source/test edit planned.

## Boundaries

No actual devices/inventory, audio tools, nwipe, power calls, VM/ISO/hosted CI,
commit/push/PR/release. No GUI or pytest launched until parent granted the
single test slot; all test runs sequential. No other source files changed.
Independent broad source review is bounded, not proof of absence of bugs.

## Final frozen-source GTK artifact check

After the parent reported the final full local gate retired (6300 main PASS,
14 expected image skips, separate Orca 1 PASS), it authorized exactly one
additional fake-only GTK capture. Prepared helper
`capture_sound_rollback.py` ran once under private XDG runtime, D-Bus and
Xvfb at 72 DPI, exit 0. The application's real GTK timer applied the refused
second-output job; assertions verified accepted Speakers restored,
Headphones inactive, both radios enabled for retry, exact failure copy,
unchanged persisted choice, exactly one fake set_output call, and owned
window/worker teardown. JSON records measured X11 DPI 72.0567 / 71.9547.

Artifacts: `sound-output-refusal-restored-72dpi.{png,json,log,exit}`. PNG SHA-256
`88977b72c8f75578b4fede3f4e6fc49bcf86f213dc412294d81a17cfaaf1377f`.
**Image inspection found the PNG entirely black** (RGB extrema all 0, one
unique color); this artifact is unusable for visual acceptance despite the
state/teardown assertions passing. Parent notified. No successful visual
review is claimed, and no retry executed. The helper log also retains four
Gdk.Screen deprecation warnings from DPI measurement; they are helper
instrumentation warnings, not product failures. Source/tests untouched.

The parent then authorized one corrected artifact-only capture. Preserved
the original helper, PNG, JSON, log and exit file with `original-black-`
prefixes. New helper `capture_sound_rollback_corrected.py` retains all fake
boundaries and state/teardown assertions, adds GDK display synchronization,
uses Pillow ImageGrab on the full private 1600x1000 Xvfb root without cropping
or editing, and asserts nonblank pixels. It ran once, exit 0, all state and
teardown assertions passed. New artifacts:
`sound-output-refusal-restored-full-root-72dpi.{png,json,log,exit}`; PNG SHA-256
`7db4689dc340cd3604d88290384f0393377a7bf094f857ca736fc968c1d9682a`.
RGB extrema are all 0..255; measured DPI matches the original run. The same
four helper DPI deprecation warnings remain in its log.

**Changed-control visual acceptance remains incomplete:** the corrected
nonblank root screenshot shows only the underlying Owner wizard, without
the mapped SoundDialog. This is a new visibility suspicion requiring
independent controlled proof; the accepted radio/state assertions alone do
not establish visible modal controls. Parent notified immediately. One
plausible source cause is the generic GTK button wrapper rerendering and
presenting the parent after opening SoundDialog on bare X11, which could
occlude it. Root cause is not yet proved. No additional capture attempt or
source/test edit was made. Exact next action belongs to parent: inspect the
full-root artifact and establish actual modal stacking/visibility before
claiming visual acceptance or deciding a minimal regression-backed fix.

## Proved and fixed: bare-X11 sound modal stacking and focus

The parent authorized a bounded fourth-finding investigation after viewing
the nonblank root artifact. Source review confirmed that the shipped
accessible kiosk uses bare startx without a window manager; the generic GTK
button callback rerenders and explicitly presents/focuses the parent after
opening the sound dialog. A mapped modal property does not keep it above its
parent in that environment.

New `tests/test_accessible_sound_modal_pass10.py` queries actual private X11
top-level stacking and native keyboard focus through read-only libX11 calls.
Original proof `original-modal-stacking.{txt,xml}`: 11 unique cases, 9 intended
failures and 2 controls passed, zero errors/skips. It proved the sound button
and same-dialog reopen leave the modal below the parent and native focus on
the parent; parent rerender does the same after explicitly correct setup;
close leaves native focus on the X root; direct render does not close an
obsolete screen/epoch modal. Ordinary parent focus and visible-review
countdown controls passed. This converts the earlier visual suspicion into
a reproducible product defect; the image was not merely a capture failure.

Narrow `accessible_wizard.py` fix: close obsolete modal controllers before
render; route native presentation/focus to the current live modal and retain
its current child focus; reconnect explicit dialog destruction to the live
parent; suppress that focus restoration after application close. No sound,
authorization, timer, countdown or boot changes. Parent independently reviewed
the patch and approved it. The existing headless `object.__new__` first-review
render fixture remains supported through getattr-based controller/closed checks.

An intermediate draft restored native parent focus but left its GTK focus
widget None after modal close. Strengthened real GTK assertions proved that
with 2 intended failures and 1 application-close control pass, retained in
`modal-live-parent-focus.{txt,xml}`. The narrow final close callback now focuses
the current rendered arrival widget only after the live parent is selected.
Current tests require the current arrival object to be mapped and owned by
the live parent. The app-close test records any parent presentation rather
than raising inside a GTK signal callback where exceptions could be swallowed.

Final new regression module has 14 cases, including WORKING sound-revision
tick rerenders with stable child focus, Stop-from-sound confirmation, app-close
guard, same-screen epoch revisit and normal full review countdown. It skips
explicitly unsupported non-Linux/non-X11 displays; all cases executed with
zero skips on the prescribed private 72-DPI Xvfb. Corrected focused draft plus
selection/review controls passed 27 tests; final corrected adjacent sound,
focus, refresh, runtime-failure, held-key, stop, close and review check passed
87 unique tests with zero failures/errors/skips in
`final-modal-adjacent.{txt,xml}`. Focused Ruff check passed. Counts overlap.
`modal-summary.json` records the original/draft/final JUnit counts and hashes.

Remaining parent acceptance: independent final modal rerun, a new distinct
full-root visual artifact with the repaired visible controls, final source
freeze and all applicable local gates. Prior three-fix full-gate success
predates this fourth source change and cannot qualify it. Original black and
occluded-root artifacts remain preserved. No additional capture was executed
during this fourth-finding investigation. No source changes outside
`accessible_wizard.py` and its new regression module.
