# UI source review after proved fixes

2026-10-17, source-only child review. Runtime evidence is owned and retained
by the primary; this child ran no tests, GUI, engine, native inventory, build,
network or privileged action. No existing test was edited or weakened.

The primary reports the exact frozen curses module originally failed nine
intended assertions with 63 passing controls and no errors/skips. The minimal
console fix retains frame readiness immediately before footer construction.
The rejection occurs after Enter-hold bookkeeping and before `_handle`, which
retains the independent live authorization check. A blocked paint can no
longer become Erase merely because its output consumed the remaining wait.
Back, EOF and mapped/unmapped key behavior remain in the existing handlers.

The primary reports the exact frozen checkbox module originally failed 16
intended assertions with four live controls and no errors/skips. Its traces
showed `TclError: bad window path name` after a retained variable changed,
and destroyed local row/variable weakrefs remained live. Only after that
proof, the primary authorized this Tk patch:

- Retain the exact write-trace token created by each `_CheckRow`.
- Bind its own Destroy event and ignore events belonging to other widgets.
- Clear/remove only that token, once; preserve peer rows and independent
  variable observers. This also handles parent/native Tcl widget destruction.
- Allow interpreter teardown to have already removed the variable.

The Tk diff changes the registration and adds one small retirement method. It does not
change consent, disk selection, methods, countdown duration, engine arguments,
timers, callback exception handling, or the root's unrelated bindings. Normal
row updates still use `_on_variable`, `_sync` and `_paint` unchanged. The two
new test modules retain their exact pre-product-patch hashes. Actual fixed
tests and broader gate execution remain the primary's responsibility.

Exact reviewed bytes are in `final-source-hashes.json`; `tk-trace-fix.diff`
is the Tk-only patch against the pass18 starting archive and
`ui-source-incremental.diff` includes both authorized UI fixes. Starting Tk
SHA256 is bb64632df587965f41afc70efe2201d3b776579038d680c3a2405319764f170d;
reviewed Tk SHA256 is 612792b7c1328741cd8a194abd90cb297629b0f281cbf30538ca9bb9ae45f50d.
Reviewed console SHA256 is d9f78e2470823629b31c9e7b755a76efc61b03a06f03153834b27c47661e2fd8.
