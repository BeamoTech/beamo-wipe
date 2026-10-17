# Pass 11 UI, boot and build review

2026-10-16, child `/root/pass11_ui_boot`, repository
`/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`,
HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
All preexisting pass8/pass10 dirty work is preserved.

## Proven defects, minimal repairs applied

1. Opening the GTK sound dialog with Return/KP Enter records that key as held
   on the parent. The real native key release is delivered to the modal,
   which has no key-release listener connected to the parent's repeat guard.
   Closing restores parent focus but retains the stale hold; the first new
   Enter action is discarded. Its release rearms the guard and the following
   press succeeds. Native XTest proof uses only an explicitly private Xvfb:
   `native_modal_release_trace.py`, `native-modal-release-trace.json/.txt/.exit`.
   The trace logs the actual modal release and parent state transitions.
   Source cause: `AccessibleWizard.open_sound_check` connects destroy only;
   parent `_key_release` owns held/timestamp bookkeeping.
   Minimal proposed repair: also connect the new modal's key-release-event to
   the existing parent handler. Do not forward presses or clear state on
   opening, redrawing or closing a dialog.

2. First GTK startup maps a window and gives its status label GTK focus, but
   never presents/focuses the native toplevel. On bare X11 native focus stays
   PointerRoot (XID 1). With the pointer outside the startup window, a native
   Escape is not delivered and cannot abandon slow startup. The live kiosk
   uses startx without a window manager. Native trace:
   `native_startup_focus_trace.py`, `native-startup-focus-trace.json/.txt/.exit`.
   It records mapped startup XID 2097155 and native focus 1 before/after Escape;
   an explicit owned delete-event ends the trace. Minimal proposed repair:
   present/focus the shown native startup window before focusing the label,
   matching the normal accessible wizard's bare-X11 discipline.

3. Both GTK fullscreen paths set the native fullscreen state flag but leave
   the actual X11 window at its windowed allocation when no window manager
   is running. `native_fullscreen_geometry_trace.py` records main wizard
   900x700 and startup 640x420 on a 1600x1000 monitor in both false/true
   fullscreen cases; the true cases report FULLSCREEN state despite the
   undersized native allocation. The shipped kiosk's bare X11 makes this a
   real path. The trace is in `native-fullscreen-geometry-trace.json/.txt/.exit`,
   with monitor geometry, native XIDs, allocations and owned teardown.
   This read-only trace was separately granted after the two-fix adjacency.
   A separate eight-case regression module proves four intended failures/four
   controls at 1600x1000 and three failures/five controls at 800x600, no errors
   or skips. The 800x600 main-window full-monitor case is already a passing
   boundary control because its windowed default is clamped to that size.
   Fake monitor geometry also covers nonzero origins and a smaller workarea.
   Approved repair: set requested monitor geometry explicitly before
   fullscreen on both surfaces, preserving existing windowed sizing/clamping.
   `accessible_wizard-before-geometry.py` and `original-geometry-source.sha256`
   preserve the exact two-fix pre-geometry source. The final test's cosmetic
   os-import cleanup has no assertion change; the exact original variant is
   retained as `test_accessible_fullscreen_geometry-original.py` with verified
   hash. The parent will independently reproduce all final tests on its exact
   initial source snapshot.

New `tests/test_accessible_focus_input_pass11.py` has 14 cases. The final
pre-fix run (`original-final-focus-input.xml/.txt/.exit`) produces exactly
6 intended failures and 8 passing controls, zero errors/skips. Four failures
are lost release/fresh activation for Return/KP Enter. Two failures are
startup Escape with the pointer outside, in windowed/fullscreen modes.
Controls cover Space, held keys across open/render/close without a release,
same-timestamp review repeat refusal, and pointer-inside startup cancellation.
Every audio/device/engine/power/subprocess boundary is fake or forbidden.
Native injection requires `BEAMO_ISOLATED_X11_TEST=1`; the canonical final
gate already provides that flag and libxtst6.

The initial pre-fix draft gives the same 6 failures/8 controls and is retained
separately. The final test cleanup synchronizes the GDK connection after native
input, removes unused test state and binds the erase spy before UI creation.
`accessible_wizard-before.py` is the exact pre-fix dirty source, with both test
versions' source hashes retained. No shared source was reverted.

## Read-only scope reviewed

- GTK render/button generations, modal screen epochs, focus, ticks, keyboard
  repeat, async refresh workers and runtime failure settlement.
- Tk navigation generations, responsive redraw/focus, key repeat/release,
  asynchronous refresh, reader handoff and callback failure settlement.
- Curses/plain input, review pagination/countdown overlay, diagnostic and
  inventory overlays, token entry, Stop, EOF, retry and report prompts.
- Shipped kiosk retry budget, recovery menu, process uncertainty/power refusal,
  entrypoint environment stripping and fallback ownership.
- ISO build/inside-docker copy binding, generated asset staging, prior bundle
  verification/rollback, source/artifact identity, launcher source snapshot and
  readiness boundaries, helper static links, workflow phase preservation.

No additional concrete defect has been proved in those paths. This is bounded
source review, not platform or image qualification.

## Checks and limits

- Two independent native trace helpers exit 0 and retire owned GTK/worker/X11
  resources; original behavior is explicitly defective as described.
- New final 14 cases: 6 intended FAIL /8 PASS, no setup errors or skips.
- Ruff on the new test and `git diff --check`: PASS.
- All GUI runs use private D-Bus/XDG and Xvfb 1600x1000 at 72 DPI. Test slot
  retired before the next agent's campaign.
- No actual nwipe, inventory, audio tool, power action, disk/USB operation,
  firmware, VM, network, hosted CI, staging, commit, push, PR or release.
- Parent independently parsed the original final JUnit/native traces and
  checked the source snapshot; a second reader approved both repairs.
- Approved repairs now applied only in `accessible_wizard.py`: one modal
  key-release connection and startup present/native focus before child focus.
  The held-key/timestamp logic and all pass10 changes are preserved exactly.
- Fixed two-fix adjacency: 114 PASS, no failures/errors/skips. Both corrected
  native helpers exit 0: modal release updates the parent ledger and the first
  fresh Return succeeds; startup native focus equals its window XID and Escape
  immediately abandons startup with the pointer outside.
  `ui-result-summary.json` records counts and exact source/test hashes.
- The two-fix source and new test pass Ruff and diff checks. The later geometry
  repair is now final and affects only explicit fullscreen size/origin.
- Final exact-source adjacency: 122 PASS at 1600x1000; geometry eight PASS again
  at 800x600. No failures/errors/skips. Files: `final-ui-adjacent.xml/.txt/.exit`,
  `final-geometry-800.xml/.txt/.exit`. Summary/source hashes are in
  `final-ui-result-summary.json` and `final-ui-source.sha256`.
- Four unedited full private-Xvfb root screenshots use the final source:
  `wizard-fullscreen-{1600x1000,800x600}-72dpi.png` and
  `startup-fullscreen-{1600x1000,800x600}-72dpi.png`.
  Receipts `fullscreen-capture-1600x1000.json` and
  `fullscreen-capture-800x600.json` record matching native allocation/root,
  zero origin, fullscreen state, child focus, nonblank PNG hash and actual
  X-server physical-screen DPI around 72. No GdkMonitor synthetic-DPI helper
  was used. The child reviewer opened/inspected all four: both surfaces fill
  the root; main action footers stay inside 800x600 and high resolution;
  the smaller Owner body uses its existing scroll area. Startup stages and
  status text are visible. Owned windows/builders and server/session wrappers
  retired normally. No screenshot was cropped or edited.
- No remaining source/test edits planned. Test slot retired so the parent can
  independently reproduce/review and run its exact-source final full gate.
  The parent owns canonical memory/evidence records.
