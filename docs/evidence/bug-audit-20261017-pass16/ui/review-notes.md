# Pass16 UI / boot audit checkpoint

Date/author: 2026-10-17 / delegated Codex pass16_ui_boot. Repository
`/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`, starting HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`.

Read current AGENTS, memory index, unfinished pass15 record and pass15 evidence.
Root supplied continued-owner authority for the absent shared guide. Preserve
all dirty prior fixes/tests/fixtures; no product or test edits. Exact reviewed
source hashes are in review-inputs.json. No native inventory, engine, power,
firmware, physical media, guest/loop/passthrough, network, credential, hosted CI,
external message, commit or publication operation.

Source paths reviewed include Tk draw generations, body/reader scrolling,
keyboard hold/release and startup input; GTK rendering, stale widget/epoch
guards, review utilities and sound modal focus/release; curses typed-token
branch, paging/review exposure and quiet-interval repeat gates; Wizard consent,
token/method authorization and keyboard-layout invalidation; app UI fallback,
session replacement and reader ownership; startup stages/final queue drain;
bounded optional audio/power workers; shipped kiosk, service isolation and
entrypoint; ISO output/backups and manifest finalization; Go launcher server
and platform boundary; local/hosted CI phase and separate publisher definitions;
canonical claims.

Nonfindings/rejected speculation:

- Empty inventory's explicit Up/Down/PageUp/PageDown/Return/Space handler
  returns break before the generic root body paging path; no keyboard analogue
  to the pass15 wheel bug is established.
- Native reader pages outside generic body canvas keep class scrolling;
  custom scrollbar key handlers return break. Nested comparison reader
  generation is retired on redraw and its key/focus handlers retain ownership.
- Curses safe tokens remain ASCII. Typed Confirm has its own bounded read and
  Escape hold; other shortcuts do not consume token characters. Generic Enter
  quiet intervals suppress interleaved auto-repeat. Review coverage accumulates
  painted lines and fresh countdown follows complete coverage/detours.
- Audio output radios ignore deactivation and restore prior choice on failure;
  stale modal epochs close and release their review overlay. No new optional
  worker ownership defect established by source inspection.
- Launcher state polling deliberately does not refresh explicit activity; its
  five-minute idle exit is specified by a focused existing test, not a bug.
- Kiosk recovery is outside Python, finite automatic retries, no shell or disk
  identification, and pgrep failure/uncertainty blocks power. Entrypoint clears
  preview/test override variables. No erase engine in preview/helper/launcher.
- Workflow source retains every Linux image/QEMU and native Windows phase;
  required gate insists both succeed; release publisher is separately protected
  and authorized. No hosted or image/native acceptance was run here.

Proved modal Escape defect:

AccessibleWizard connects sound modal key-release to parent hold tracking but
not key-press. A physical Escape may close SoundDialog then its hold-repeat may
reach the parent as a fresh Escape, navigating back or opening Stop. Existing
modal tests call response/close without native held Escape. Prepared
modal-escape-probe.py / run-modal-escape.py use real private XTest press and X
server auto-repeat, exact modal focus, OWNER/METHOD/LAST_CHANCE/WORKING, fresh
press controls, fake pending audio tickets, all native application effects
forbidden, and callback error/state checks. Root admitted the serial runtime
lane. All8cases completed normally0, zero effects/callback errors, no engine
start/cancel or shutdown/session request. Three hold-repeat violations:
OWNER→KEYBOARD, METHOD→CONFIRM, LAST_CHANCE→METHOD after one physical Escape
closed the modal. Three genuine fresh-press controls navigate separately as
expected. Both WORKING rows have no request and remain unchanged; they are
controls, not valid working-Stop qualification. Exact JSON/log/command receipt
retained. Root independently reproduced the modal defect. Regression design
is in modal-regression-design.md; no product/test edits by this delegate.

Focus baseline and concrete stale Tcl callback:

- Root's fresh baseline has7failed unchanged140ms focus assertions and
  invalid old lambda Tcl commands. Its original logs/JUnit own those failures.
- First8case standalone diagnostic preserves the140ms measurements and records
  later300/600ms frames only for attribution. All8focus checks match but two
  CONFIRM Tcl bgerrors are captured, causing strict diagnostic exit1. That
  custom bgerror capture suppresses default handler behavior, so root requested
  exact default-handler/timer tracing; no earlier baseline failure was cleared.
- Prepared follow-up traces original Python callback source/owner/Tcl command,
  pending timer/script/existence before/after redraw and actual interpreter
  ::tcl::Bgerror, native XID/Tcl focus/grab/toplevels. It preserves default
  behavior and original140ms deadline. Initial query setup omitted the empty
  Tcl interpreter path (exit1, no campaign); corrected query only. First
  observer used function.__name__ to identify Tk callit, but Tk rewrites it;
  retained intermediate output and corrected to __code__.co_name. These are
  observer/setup corrections, not product/test changes or gate passes.
- Final registration trace independently proves one stale timer: original
  CONFIRM/unmapped registers after#89/130389123747200<lambda> at87.25ms from
  tk_wizard.py:3460, owned by old Entry. claim_input redraw finishes174.07ms
  with timer still pending but its command deleted. Default ::tcl::Bgerror
  reports that exact command at179.56ms. No error toplevel/grab appears, so
  a default error modal stealing focus is not established here.
- Final8case diagnostic exits0 as a completed observer, not a passing product
  gate. It reproduces2of8original140ms focus mismatches (KEYBOARD/unmapped,
  LAST_CHANCE/unmapped), focus still on root after mapped claim redraw. Both
  focus correctly at300ms;6other140ms checks match. State/requests/engine
  unchanged, zero native effects. This supports asynchronous focus delivery
  as a candidate timing cause but does not independently attribute all7initial
  baseline failures. Root must validate actual readiness/required original
  assertions; no deadline/assertion relaxation.
- Scripts/JSON/logs/command receipts are focus-frame-diagnostic.* and
  focus-default-bgerror-diagnostic.*, including initial/intermediate outputs.
  All displays and timers are owned/private72DPI; final observation cleanup
  at650ms cancels fixture-owned Tcl timers then normal teardown. Native
  :1/:99 untouched. Runtime lane released to root.

Script preparation used two source-read commands naming nonexistent standalone
desktop firmware.go / transaction.go; each failed before those reads. Actual
platform implementation and idle polling specification were located with rg.
These were read setup issues, not product test failures.

Historical pass8 SIGTERM and pass9 timing attribution remain unavailable; no
later passing check can supply that attribution. Parent owns final durable
evidence, applicable gates, and any eventual repair authorization.

## Approved regression work and original-proof fixture correction

Root authorized only two new regression modules. Modal has21cases; Tk has26
including two further authorized actual ownership controls. This delegate has
not run the modules. Root's original398case run produced203failures/195controls,
zero errors/skips. Modal18failures/3controls are intended. The26Tk failures
were inspected individually:13stopped at Tcl-background-error assertions and
13at focus assertions. The initial fixture called root.focus_force after an
update could already have established correct child focus; this deliberately
replaced it with root focus and obscured the actual callback-lifetime proof.
This fixture artifact is not a product bug.

Root archived initial bytes/receipts before authorizing correction. Corrected
only new Tk test sequencing: configure/deiconify and establish native root focus
before lifecycle production redraw, then mapping/update/pump; current-owner
controls likewise focus root before update. Every26case assertion and120ms
observation pump is retained. Selected picker renderer focuses current primary,
so its assertion remains. Destroy and ownership tests unchanged. Frozen Tk
SHA256c6cabf08c9f1762daaea4c460b0e04231cb742b62d35e4cd791d138424a8fe6a;
modalSHA25643ae904e9436724706b60fd6221c6d265abb4bdfa8cd8382cefa3b54631045c5.
No other repo files or product source changed by this delegate.

Parent's baseline fixture proposal is an observation-anchor correction: after
the actual mapped claim_input redraw, retain the same140ms interval and all
focus/state/countdown checks. Watchdog detects missing mapped redraw and cannot
count as success. Existing120ms native-first-key and one-time-focus/no-reclaim
tests retain earlier input coverage. There is no deliberate80ms product focus
timer; delayed native child FocusIn delivery was observed, not a scheduled
source callback with that delay.
