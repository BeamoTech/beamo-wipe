# Independent final source review: pass 11 GTK and runner repairs

2026-10-16, Codex discovery reviewer. Result: **approve the reviewed implementation
and regression scope**, subject to the primary's independent original-source
proof and fixed-source integration gates. No tests were executed by this reviewer
in this review round; the parent coordinates the single test slot.

Exact reviewed starting/final source and new test SHA-256 values are recorded in
`final-integration-review-hashes.json`; separate `ui-reviewed.diff` and
`runner-reviewed.diff` preserve the narrow pass 11 deltas, rather than folding
prior uncommitted pass 8/pass 10 work into this review.

## GTK input and startup

Compared `accessible_wizard.py` with the exact dirty pre-fix snapshot
`/tmp/pass11-ui/accessible_wizard-before.py`. Its only changes are:

1. Connect each newly created sound modal's key-release-event to the existing
   parent `_key_release` handler.
2. Present and natively focus the startup window after `show_all`, before
   focusing its accessible status label.

The existing release handler uses only key/time from the event, returns False,
removes the corresponding held key, and records real guarded-key release times.
Sharing it with the modal adds no parent navigation or action dispatch. Held
state is not cleared on modal opening, re-render or closing. Equal-time X11
release/press pairs still go through the unchanged repeat guard. Signal
connections are installed synchronously before returning to GTK's event loop
and are destroyed with the modal. Prior modal lifetime/epoch/stacking fixes,
review overlay countdown suspension/reset, default Erase protections and close
focus restoration are preserved.

Startup follows the normal accessible wizard's established bare-X11 behavior.
Its shown native toplevel is focused once, then its selectable status label
gets GTK focus for Orca. No worker, poll, abandonment, failure or success logic
changes. The live kiosk's startx environment has no window manager to do this
focus transfer itself. The original native trace concretely shows PointerRoot
focus and ignored native Escape with the pointer outside, distinguishing native
focus from merely having a GTK child focus widget.

Read all 14 new regression cases. Native input requires the existing explicit
isolated-X11 opt-in. Audio, process, disk discovery, engine and power boundaries
are fake or forbidden; the test creates and closes its own audio worker and X11
connection and releases injected down keys. Cases cover Return/keypad Enter
lost-release and first-fresh-activation failures, space controls, holds without
release over opening/render/close, same-time review repeat refusal, and all four
startup fullscreen/pointer-inside combinations. Startup tests have a bounded
fallback close, verify that successful Escape did not need it, release their
fake worker, await completion and retire the owned rescue callback.

The same-time review test binds its erase spy before UI creation, advances the
fake clock to the post-overlay deadline, focuses Erase, and checks no launch
occurs; it therefore exercises the relevant enabled-control repeat gate.
The existing pass 10 modal and review suites supply adjacent stacking, stale
screen, stop, app-close and five-second restart checks for the final gate.

## Runner projection

Compared `nwipe_runner.py` with exact pass 11 starting snapshot
`/tmp/pass11-runner/nwipe_runner-start.py`. The new body value is used only for
line-retention and error-table closing classification. Original raw record text
is still appended unchanged. The status success parser is untouched; terminal
banner CR bytes remain preserved by the prior pass 10 delimiter-only fix.

The full direct advisory parser already accepts prefixed summary rows and
closing star delimiters. The scanner previously discarded these while keeping
the Erasure Summary header. The parent's actual-poll proof records large-only
warning/unavailable-to-pass upgrades and a table-boundary mismatch. The patch
keeps normalized target-column rows and normalized closing star delimiters,
without normalizing retained data or rewriting provenance. Thus direct parsers
still apply their own exact prefix/provenance and invalid-record rules.

No changes to device selection, nwipe argv/methods, launch/stop ownership,
progress positions, raw tail storage/export, file identity/stability checks,
scan/line/evidence caps, or malformed/incomplete read refusal. The error table
state still keeps relevant table contents, now recognizing the same ordinary
logger-prefixed closing markers. Extra preserved records are conservative;
unknown/malformed prefix lines are not rewritten into valid evidence.

Read all 81 new regression cases. They compare full check payloads, including
provenance, from the full log and actual poll/cancel assessment. They cover all
three methods, plain/info/timestamp-info row forms, shortfall/malformed/complete
rows, prefixed closing boundaries, stop outcome/assessment and exact completion
cap-minus-one/cap/cap-plus-one behavior. Fixtures use regular temporary files
and controlled fake processes, verify unchanged exact log bytes, and require
process retirement. Prior progress-order and CR-record-ending regressions must
remain in the fixed-source adjacent/full gate.

## Verification disposition

Original failing UI results and runner actual-poll traces were reviewed as
provided; no claim here substitutes for the primary's independent reproduction.
The fixed-source tests, final frozen-source full gate, provenance/report
integration and raw-artifact checks remain parent-owned. This reviewer found no
blocking source or test concern in the exact hashes recorded alongside this
report. Re-review is necessary if those implementation bytes change.

Historical unexplained termination/timing evidence remains separate and
unattributed. No physical/platform acceptance or release is asserted.
