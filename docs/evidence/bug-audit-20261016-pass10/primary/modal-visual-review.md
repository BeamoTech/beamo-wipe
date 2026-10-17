# Primary visual verification — 2026-10-16

The exact-source original modal proof independently checks 58 source/static
inputs against the initial three-fix freeze, then runs all14 final modal
regressions on those bytes:10 intended failures/four controls, no errors/skips.
The original primary and author traces show native parent-above-modal stacking
and parent input focus, root focus after modal close, and stale modal retention.

After repair, `capture-modal-visible.py` ran under private Xvfb1600x1000 at72DPI,
private D-Bus/runtime and fake-only device/engine/audio/power boundaries. The
actual100ms GTK timer applies the refused output job. The full-root screenshot
is unedited. Primary opened and inspected the PNG: the sound controls are
visible above the Owner wizard, failure text is readable, Speakers is selected,
Headphones unselected, volume/mute/play/outcome/Close controls fit the dialog.
The status owns GTK child focus; XQueryTree/XGetInputFocus prove modal stacking
above the parent and native modal keyboard focus. All retry/state assertions
pass, exactly one fake set_output was called, persisted output stays empty,
and owned window/worker teardown completes.

Final PNG SHA256:6ddcba140a650c46348017500382205c1de28c0b6c28836da868243edff2f400.
Receipt:`modal-visible-rollback-72dpi.json`; helper/run log/exit retained.

One earlier post-fix capture helper attempted GdkMonitor physical dimensions,
which report synthetic96DPI for this Xvfb monitor although the X server screen
is configured at72DPI. That helper stopped before capture; exact script/log/exit
preserved with `monitor-dpi-mismatch-` prefix. Corrected helper directly reads
X server screen dimensions via Xlib, reports72.0567/71.9547DPI, and passes. It
uses no deprecated GdkScreen measurement calls. This was instrumentation,
not a product source defect or a passing artifact. The pre-fix black native
capture and nonblank but occluded full-root capture remain unchanged under ui/.
