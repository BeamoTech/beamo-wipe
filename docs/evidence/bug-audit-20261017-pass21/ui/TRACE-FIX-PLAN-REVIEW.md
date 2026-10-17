# Source review of proposed owned trace adoption

2026-10-17 / Codex `/root/pass21_ui_lifetime`; same repository/ref/worktree as
SOURCE-REVIEW.md. Source-only review requested by root after preparing the
actual-native trace adoption probe. No product imports, tests or runtime.

Inspected installed `/usr/lib/python3.12/tkinter/__init__.py` (SHA-256
`a2bd0d90e51582cf816f31914487397f1949f38b3c6b7aeeb5a2bfe4293a2973`), Variable._register,
trace_add and trace_remove. `_register` creates a Tcl command, records its exact
name in the Variable command registry and returns that name. `trace_add` then
installs the trace and returns the same name. `trace_remove` removes only the
given mode/name and deletes that command when no remaining trace refers to it.

Root proposes an owned-trace helper for CheckRow and the two persistent wizard
traces. For actual captured Variable instances, it temporarily shadows only that
instance's `_register`; delegates its original callable unchanged; immediately
adopts the returned name into the known owner's token field when the callback
is the exact callback object passed by this helper; and calls ordinary
trace_add('write',callback). Finally it restores the exact prior instance
override or removes only its own temporary shadow. Non-native test doubles
retain their ordinary trace_add API. No token-difference deletion is proposed.

This closes the inspected ownership gap: after `_register` returns, a later
trace_add failure no longer loses the exact command token. Constructor teardown
can retire that known command while an independent observer retains the
Variable. If native trace installation fails before adding the trace, the
library's trace_remove still removes the absent trace and deletes its known
command. Normal callback registration and library exception behavior remain.

Implementation conditions:

- Adopt only the first matching registration. A later reentrant independent
  peer registering that same callback object must not replace the owned token.
- Use callback identity, not equality. A bound method freshly accessed a second
  time is not necessarily the same object, so pass the helper's captured exact
  callback unchanged into trace_add.
- Preserve a preexisting instance `_register` override verbatim, distinguishing
  absence from an explicit value. Restore/delete only if this helper's shadow
  remains installed; preserve an independent replacement made during the call.
- Restore the shadow in finally without replacing the original trace_add
  exception or editing its identity/traceback. The normal returned token remains
  the library's result.
- No native destructor is suppressed. Retained helper exception frames can
  retain owner/Variable/original callable; pass20's creator-thread native pools
  cover this graph until owner-thread settlement. No traceback clearing or
  product GC mode/threshold change is needed.

No additional source objection to the plan under these conditions. This is a
plan review, not approval of uninspected implementation bytes or runtime
acceptance. Root must inspect and prove the exact implementation, peer
preservation, original exception, constructor, redraw and collection behavior.
Python3.11/live-bookworm execution is not established by the installed3.12
source review.
