# Follow-up focus attribution plan (not run)

Baseline exact source: seven failed original140ms focus assertions and old
lambda Tcl errors. First diagnostic's custom bgerror captures two CONFIRM
errors but all eight140ms focus checks match. The diagnostic deliberately
recorded and suppressed the default bgerror, so it cannot explain or clear the
baseline failures. Root identified a supported hypothesis: the native Tcl
default background-error dialog steals focus before subsequent measurements.

Next private diagnostic, only after root admission:

- Reuse the exact8case setup and140ms inspect deadline, no test/source edits.
- Wrap only Python callback registration and TkWizard _draw to record monotonic
  timestamps, callback command names, callback's original filename/line,
  owning widget path and afterID/script. Inspect pending scripts before and
  after each redraw plus info commands to prove a queued timer's command was
  deleted. No timer cancellation or callback behavior change during observation.
- Observe interpreter's existing `interp bgerror` command using a Tcl
  execution trace, preserving the default handler and its native error window.
  Capture error text, current/root XID focus, Tcl grab current and mapped
  toplevels at entry and140ms inspection. Log native map/focus events without
  replacing default error handling. Never click or close a peer's window.
- Preserve original140ms pass/fail outcome as measurement; later300/600ms frames
  only diagnose it. Owned cleanup at650ms cancels owned timers then destroys
  root; no outcome reclassification using a later frame.
- Need exact trace linking deleted callback to a source line, default error
  invocation and focus/grab transfer before proposing repair. If this proves
  cause of sevenbaseline failures, parent independently repeats exact source
  and traces rather than treating a later green run as attribution.

No new runtime admission is currently held. No test deadline, assertion or gate
will be relaxed. Historical pass8/pass9 attribution is separate and unchanged.
