# Proposed modal Escape regression design

Root owns repair authorization and independent proof. No source/test edit is
authorized or performed by this delegate at this checkpoint.

Observed native defect: parent Escape hold state stays empty when GTK sound
dialog receives physical Escape and closes. Its server auto-repeat reaches the
parent as a new press and performs a second navigation. Native source trace has
three violations (OWNER, METHOD, LAST_CHANCE) and three genuine fresh-press
controls. All effects/state guards remain intact.

Minimal repair shape: a dedicated modal key-press bookkeeping handler claims
guarded physical keys using the same held/release timestamp semantics as the
parent, but never dispatches parent navigation. It should return False for the
first modal press so native Escape close, Return/Space button activation and
other standard dialog behavior remain available. Guarded repeats should return
True to stop reactivation. Key releases already route to parent release state.
The first modal Escape must be recorded before native close/destroy; after
close, the same hold and equal-timestamp release/press pair remain suppressed
on the parent. A later actual release plus fresh press re-enables normal
navigation. Do not call parent _key_press directly from modal; that would
navigate the covered review/working screen while the dialog is still active.

Suggested focused regression module:

1. Native private XTest Escape hold closes current SoundDialog once while
   retaining exact parent screen/epoch/authorization/request. Exercise OWNER,
   METHOD, LAST_CHANCE; use actual X server auto-repeat, no direct handler calls.
   Verify modal has native keyboard focus first and old controller is destroyed.
2. Release then genuinely fresh native Escape acts once on parent for each
   screen. Holding that fresh Escape does not perform a third navigation.
3. Valid fake WORKING context includes an immutable fake WipeRequest, a fake
   poll that remains nonterminal and a fake active observation. Modal-close
   hold must not open Stop; fresh Escape opens a separate confirmation, never
   invokes cancel. Existing8probe WORKING rows have no request and must not be
   misrepresented as this acceptance.
4. Unit/exact-handler controls for direct repeated press and same-timestamp
   X11 release/press for Escape/Return/KPEnter/Space/F5. A normal first modal
   press returns False, guarded repeat returns True, plain unguarded key
   remains unconsumed. Stale screen/epoch closure remains normal.
5. Preexisting held Return/Space that opened the modal: releases still reach
   parent guard, first later fresh activation is not lost. Existing native
   test_accessible_focus_input_pass11 controls already cover this; repeat them
   adjacent to the new module and include the new modal press handler where
   necessary. Sound overlays preserve fresh five-second review after closing.

Every GUI test must require BEAMO_ISOLATED_X11_TEST=1 and a private display
other than :1/:99 at72DPI; guard application subprocess/inventory/engine/power/
sound calls; fake tickets never invoke audio callbacks. Capture Python/GTK
callback exceptions and Tcl bgerror when present; zero errors is an assertion.
No actual erase, process signals, disk inventory or file export. Preserve exact
owner/selected/token/method/authorized operation/request except the intended
screen/review countdown transitions. Destroy only owned windows and cancel
owned fixture timers safely.
