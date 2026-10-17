# Source assessment: cancellation by retired widget ownership

Date/author:2026-10-17 / delegated Codex pass16_ui_boot. Root requested this
review before implementing. No product edit or runtime by this delegate.

Proposed design is appropriate: inspect only the current Tcl interpreter's
pending after IDs, map exact Python callback command names to their owner
widget's _tclCommands registry in the retiring subtree, and cancel matched
IDs through that exact owner before destroying the widgets. This covers
Entry idle/retry, _CheckRow flow idle, hover timers and body canvas focus idle
at their common lifetime boundary instead of repairing one callback at a time.

Python3.12 Misc.after_cancel source independently checked: it retrieves the
pending script, calls self.deletecommand(script), handles TclError, then
cancels the after ID. Correct self ownership removes the callback command
from its actual owner's _tclCommands list. This avoids deleting commands via
an unrelated owner while leaving dangling entries for subsequent destroy.
Pending after IDs and owner command names should be snapshotted before any
cancellation mutates their registries. Cancellation does not pump events;
already running callbacks are absent from pending after info. Existing Tk
callit cleanup tolerates an already deleted command if destruction occurs
inside the current callback.

Important scope detail: _clear(frame) preserves frame itself, so collect only
its children and their subtrees (or equivalent include_self=False) there.
Do not cancel an after callback registered on the persistent container merely
because its children are retired. _teardown(root) should include root because
the full application is retired. Existing explicit tick/hold/restore cleanup
can safely run first; the final owner sweep catches only remaining work.

Use exact full script-command equality for Python after callbacks. Avoid
substring or broad first-word matching that might capture an unrelated Tcl
script invoking the same name with extra semantics. Interpreter-local scan
plus subtree registry ensures separate Tk roots and persistent root timers
remain untouched on redraw. Retiring full root can include its owned
toplevel children as normal Tk destruction already does.

The approved24case new module tests idle/retry plus redraw/navigation/destroy
and current-focus controls across3textsizes, preserving exact authority and
zero Tcl/Python errors. It has not been run. Add a focused ownership control
for a persistent container/root callback and another independent interpreter
before freeze; these checks distinguish this generic repair's scope and are
more useful than merely counting canceled callbacks. Root owns any additional
test authorization, implementation, independent verification and final gate.
