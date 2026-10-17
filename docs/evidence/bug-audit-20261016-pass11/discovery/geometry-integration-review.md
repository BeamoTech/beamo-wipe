# Independent review: GTK fullscreen geometry repair

2026-10-16, Codex discovery reviewer. Result: **approve the exact additional
geometry implementation and regression scope**. No tests executed in this
round; source/diff, original/native traces, regression source, corrected capture
receipts and all four full-root PNGs inspected read-only.

Exact reviewed bytes and screenshot receipts are recorded in
`geometry-review-hashes.json`, with narrow delta `geometry-reviewed.diff`.
The pre-geometry snapshot hash matches the UI source approved in the earlier
`final-integration-review-hashes.json`; the runner source still matches that
prior approved hash. This establishes that the earlier reviewed release-ledger,
startup focus and projection repairs were not changed by the extra geometry work.

## Root cause and implementation

The original private-X11 trace demonstrates that fullscreen requests mark both
GTK windows fullscreen but leave the main window at 900x700 and startup at
640x420 on a 1600x1000 monitor. A fullscreen flag alone does not prove geometry.
The shipped live kiosk starts the app under startx without a window manager, so
there is no window manager to consume the fullscreen hint and expand the window.

The new code only runs when fullscreen was requested. For the current primary
monitor (or first monitor fallback), it sets the default size to the complete
monitor rectangle and moves the window to that monitor's x/y origin before the
existing fullscreen request. Main-window monitor lookup already existed;
startup adds the equivalent lookup. If no monitor is available, the old GTK
fullscreen request remains the fallback. No geometry, content, screen,
countdown, action, worker, focus or closure logic changes in windowed mode.

Using monitor geometry instead of workarea is appropriate for fullscreen:
workarea can exclude panels/docks, while fullscreen should occupy the complete
monitor. Windowed main keeps its existing 900x700 upper bound clamped to workarea;
windowed startup keeps its 640x420 default. GDK monitor geometry and GTK default
size/move coordinates use the toolkit's matching logical coordinate system.
The explicit nonzero origin handles a primary monitor placed away from root 0,0.

## Regression and artifact review

Read all eight cases in `test_accessible_fullscreen_geometry_pass11.py`:
main/startup, windowed/fullscreen and actual/injected monitor geometry. The
injected monitor has a nonzero x/y origin and a workarea smaller than full
geometry, so it distinguishes geometry from both root origin and workarea.
Assertions use actual mapped native origin, allocated size, reported size and
fullscreen state; they do not infer success from the fullscreen property alone.
The fixtures prohibit application process, inventory, engine, audio-tool and
power effects; native tests require the explicit isolated-X11 gate. Each owned
main window is closed, and startup's controlled blocked worker is released and
confirmed retired after its inspection/abandon path.

Independently viewed the unedited full-root screenshots at 1600x1000 and 800x600:
main Owner and startup stages fill the root surface with visible controls/text,
and startup retains focused status text. The 800x600 main screenshot uses its
existing scrolling content area with persistent footer controls; this change
does not alter that layout. All four PNG hashes match their capture receipts.
Receipts also show matching native allocations/root sizes, origin 0,0, fullscreen
state true, child focus and measured X server DPI approximately 72.

No blocking implementation or regression concern found. The parent's independent
original-source proof, fixed-source matrices and complete final gate still own
acceptance. No source edits, device actions, tests or platform qualification were
performed by this reviewer for this review. Historical unexplained termination
and timing observations remain separate.
