# Independent source review of pass 11 runner and GTK findings

2026-10-16, Codex discovery reviewer. Read-only review; no tests or source edits
performed for this round. Own completed discovery evidence remains unchanged.

## GTK release ledger across a sound modal

Reviewed `/tmp/pass11-ui/native-modal-release-trace.json` and the native-X11
trace helper, plus `AccessibleWizard.open_sound_check`, `_key_press`,
`_key_release`, and `SoundDialog` lifetime/event setup.

The trace demonstrates a concrete state leak: Return keydown is delivered to
the parent and adds Return to `held`; activating the sound button transfers
native focus to the sound modal; the physical keyup goes to that modal. The
parent ledger never observes keyup. Closing the modal leaves Return held, so
the next fresh keydown is rejected as repeat. Its keyup finally releases the
ledger, allowing the third press. The control press and native modal keyup
recipient distinguish this from a toolkit synthetic-event assumption.

Connecting the modal's `key-release-event` to the existing parent `_key_release`
is an appropriate narrow repair. The handler uses event key/time and no
parent-widget identity, so sharing it preserves existing timestamp handling and
return False lets GTK retain its local release/default behavior. Connect it
synchronously after constructing the live modal, before returning to the GTK
loop. Avoid clearing all `held`/release timestamps or forwarding modal keypress
into the parent's navigation handler: either would weaken the explicit repeat
safety guard or make modal Escape/Enter operate the underlying review.

Required adjacent coverage: Return, keypad Enter and space release routing;
equal-time X11 release/press repeat pair still suppressed; later fresh press
accepted; modal Escape stays local; review remains gated while modal exists,
and closes to a fresh five-second review; close/reopen and stale-dialog epoch
behavior remain intact. A real native-X11 press/open/release/close/fresh-press
recheck should supplement signal/unit cases, using the private display only.

## Large-log Erasure Summary projection

Reviewed `projection-summary-trace.py`, `_scan_completion_log`,
`_engine_log_body`, `_status_column_has_name`, `engine_checks._body`,
`_erasure_summary_state`, and `_parse_hidden_capacity`.

There is a source-supported semantic mismatch: the direct advisory parser
removes a recognized nwipe logger prefix before reading Erasure Summary rows
and table-closing star lines. The scanner currently tests raw lines for target
columns and leading stars, while retaining the header through a substring.
A prefixed target shortfall/invalid row can vanish from projected evidence,
leaving the positive hidden-sector sentence and no summary row; direct warning
or unavailable can therefore become an apparent pass. A prefixed closing line
can also vanish and incorrectly keep following rows inside the summary.
The prepared fake-log trace is suitable concrete proof once executed.

Use normalization only to decide relevance/table boundaries. Preserve each
retained raw record unchanged, including CR and exact terminal-banner bytes;
then existing direct parsers determine their own provenance and verdict.
Recognized body target-column lines and closing delimiters must both survive.
The current progress-position bookkeeping and retained-evidence/line/file
identity bounds must stay intact. A retention superset is conservative; do not
broaden completion success parsing or replace raw logs with normalized text.

Required checks: direct/projected equality for prefixed/plain shortfall,
malformed, complete and closing-delimiter cases; duplicate/contradictory rows;
logger levels/timestamps accepted by the current parser; unknown/malformed
prefix and CR controls; small/cap-minus-one/cap/cap-plus-one and large logs;
all three methods and natural poll/stop completion paths. Confirm exact tail
and raw logfile bytes unchanged, then report/evidence integration uses the
preserved assessment. Evidence bound overflow remains indeterminate.

## GTK startup keyboard focus

Additionally read the native startup trace and `run_accessible_startup`.
The mapped startup window has a GTK child focus widget but native X11 focus
stays on root (XID 1), with the pointer outside the new window. Native Escape
therefore does not reach the app; the helper must send a direct delete signal.
Source calls `show_all` and child `grab_focus` without presenting/focusing its
native toplevel, unlike the wizard's established bare-X11 handling.

A one-time presentation/native-focus after mapping is consistent with the
shipped startx session without a window manager. Keep the stage label focused
for Orca and preserve startup worker close/abandon semantics. Prove actual
private-X11 native focus and Escape abandonment with pointer outside, check
fullscreen and ordinary modes, completed/failed/abandoned worker cases, and
owned timer/window/worker cleanup. No need to alter discovery or cancel the
worker's read-only acquisition from the Escape handler.

Disposition: the reviewed narrow repair directions are sound, subject to
executed original failing regressions, corrected regressions and final diff/
artifact review. This is not implementation approval for unseen source changes.
