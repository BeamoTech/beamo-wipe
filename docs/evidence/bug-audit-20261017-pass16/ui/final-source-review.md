# Pass16 UI exact-source review

2026-10-17 / delegated Codex pass16_ui_boot. Source-only review; no runtime or
edits. Compared both actual runtime files to exact starting-source.tar.gz;
compared existing focus fixture to fixture-before-focus-anchor.py; read both
new modules and relevant real/fake controllers. Hashes in final-source-review.json.

## Resolved source dependency objection

The GTK shared _remember_key_press extraction introduces a dependency from
_key_press. Two existing no-GTK fixtures compile only _key_press/_key_release
and bind them to SimpleNamespace controllers: test_accessible_key_repeat.py
and test_accessible_last_chance_actions_pass12_ui.py. Those fake controllers
provide no _remember_key_press, so all such calls will raise AttributeError.
Include/bind the exact real shared helper in their source-only extraction,
preserving every original key/action assertion; do not replace it with a stub.
Root corrected both fixtures to compile the exact real _remember_key_press,
return it alongside the handlers, and bind it using MethodType on every fake
controller. This reviewer independently reread those final bytes and compared
the ASTs of all assertions to the saved originals: every original assertion is
unchanged. The direct source dependency objection is resolved; no stub replaces
product logic. Exact before/current hashes and assertion counts are recorded.

## Tk product assessment

- New helper maps exact full pending script strings to _tclCommands owners in
  the retiring subtree, scans only that interpreter's after IDs and invokes
  owner.after_cancel. Python3.12 implementation removes the matching command
  from the correct owner's registry before canceling its timer. Other callback
  command names/bindings are untouched. Pending scans do not pump events;
  currently executing callbacks are already absent from pending after IDs.
- _clear excludes the persistent frame itself, retaining container/root jobs
  while retiring child jobs. _teardown includes root after existing targeted
  timer cleanup, capturing remaining root/descendant work before destruction.
  Separate Tk interpreters are unreachable from either owner's widget tree
  or Tcl pending-event inventory. TclError tolerance supports repeated teardown.
- Non-Tk lightweight roots skip the helper; existing __new__ controllers retain
  normal fake teardown semantics. No engine, gate, timer interval, token,
  countdown, selection, authorization or disk behavior changed.
- Initial Entry focus, retries, _CheckRow flow, hover and body focus idle jobs
  all share the corrected widget destruction boundary. The helper does not
  rewrite their individual focus/geometry policies.

## GTK product assessment

Original parent held-key/release-timestamp behavior is factored unchanged into
_remember_key_press. Parent delegates before its existing action dispatch.
Modal connects a dedicated press handler that only records/suppresses repeats,
never dispatches parent navigation. First press remains available to native
dialog behavior; held and equal-timestamp repeats remain blocked after close.
Existing modal key-release connection clears held state so fresh actions work.
Normal screen epochs, review overlay release/fresh countdown and focus-return
logic remain unchanged. Product shape is correct conditional on original
source-only fixture compatibility and parent runtime gates.

## Existing and new tests

Existing startup focus test preserves all140ms/focus/state/countdown assertions,
adds a missing-mapped-draw watchdog and schedules only after its first observed
post-run mapped production redraw. No focus forcing/event pumping is introduced
by the observer. Missing frame or missing inspect cannot pass because both
mapped_draws and seen are required. Under this fixed viewport/standard fixture,
the observed mapped startup draw is run's claim_input redraw. Earlier120ms
native first-key and one-time-focus/no-reclaim tests retain early input coverage.
The anchor change addresses readiness vs native child-focus delivery; there is
no deliberate80ms source timer. Baseline failures remain failed history.

New modal21cases assert physical native hold/fresh behavior across owner,
method, final review and valid fake working request, optional rerender, all
five guarded event keys, split timestamp pairs and release/open controls.
New Tk26cases retain original state/focus/error/wait assertions with mapped
fixture priming; include idle/retry redraw/navigation/destruction, current
owner controls and actual persistent-container/root/peer callback outcomes.
Strict fake-only effects and Tcl/Python callback errors are checked. Fixture
native focus occurs before production child focus, avoiding the corrected
initial fixture artifact. No assertion/timeout weakening or new method import.

Final readiness corrections independently reviewed against exact
pre-readiness module copies: Tk fixes800×600geometry before its initial
mapping/prime, preserving all34assertion ASTs and all26cases. Geometry is no
longer changed after old callback preparation and immediately before the
lifecycle renderer; the intended current picker focus assertion remains.
Modal adds20ms between the observed native Escape release and genuinely new
press, then asserts their native timestamps differ. All29prior assertion ASTs
remain in order and two stronger timestamp assertions are added. The explicit
synthetic equal-timestamp repeat cases are unchanged, preserving conservative
product behavior rather than weakening its guard. Product bytes are unchanged
since prior review. Exact new module hashes are in the updated JSON.

Final source approval is granted for the exact hashes in the revised JSON,
conditional on root's independent applicable gates. No runtime was performed
by this reviewer during this final review. Parent reports119focused UI cases
passing with zero errors/skips after these fixture-only readiness corrections;
this is parent evidence, not a reviewer runtime result. Earlier failed native
timestamp/geometry fixtures remain failed history. Exact original-source replay
and final applicable gates remain parent-owned. Any subsequent test/source
change requires an updated exact-byte review.
ISO/native/hardware qualification and historical acceptance blockers are
outside this review.

## Final typing-only Tk delta

Independently checked the initial failed type-gate source patch/log and the
current Tk helper. Misc stubs omit the runtime _tclCommands attribute, and
reusing the traversal owner's nonoptional local for dict.get's optional result
caused two configured mypy failures. Final code uses
getattr(owner,"_tclCommands",None) and a distinct callback_owner lookup local.
For actual Tk widgets this preserves the same registry, exact command matching,
ownership scope and cancellation behavior. No ignore, assertion, guard, timer
policy or gate relaxation. Initial failed gate remains failed history; parent
has re-frozen and restarted the required local phases.

Approved Tk SHA256 now
9764924b29c3c491a6acde0ca0853135e1e9eccf71bd77cbeb7c90b35534b29f.
All six other approved source/test hashes are unchanged. JSON includes the
prior hash snapshot and this delta's review. Source approval remains conditional
on parent's final applicable gates. This reviewer performed no runtime or repo
edit in this recheck.

## Tcl-only picker leaf fixture

Reviewed the exact fourth existing-fixture adjustment against its saved
original: test_pick_scroll_restore.py adds only winfo_children returning[].
Its Canvas intentionally subclasses tk.Misc to provide real Tcl timers plus
simulated geometry, not an actual Tk widget path/hierarchy. The new generic
owned-callback sweep correctly reaches that Misc subclass during teardown;
the inherited Tk winfo_children requires _w, which this Tcl-only fake has
never modeled. Explicit empty children accurately supplies its leaf contract.
Actual Tk hierarchy ownership remains exercised by the new native26case module,
including independent peer-interpreter/container/root jobs.

All11original assertion ASTs are independently confirmed unchanged. Product
bytes and all seven previously approved hashes are unchanged. Newly approved
fixture SHA256c7b22e9446ca7cb10463661654fcd3e0382be07021c8bf54dbfd1c7385c4242e.
Updated JSON records exact before/current hashes. First full-run failures,
space-bearing interpreter/PATH fallback diagnosis and corrected rejecting
guards remain parent-owned evidence; this source review neither reruns them
nor reclassifies a failed phase. Approval remains conditional on final gates.
