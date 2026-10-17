# Pass13 UI / boot audit result

2026-10-16, Codex `/root/pass13_ui_boot`. Worktree `/root/dev/Beamo Wipe`,
branch `fix/safety-audit-20261015`, HEAD35107a8d1a701093eac876a58ab4efd50e291673.
Only this agent's allocated `src/beamo_wipe/ui/tk_wizard.py` and
`tests/test_tk_input_scroll_pass13.py` changed. Prior pass12 source fixes retained.
No staging, commit, push, external service or physical operation. All application
engine/discovery/audio/power effects were forbidden in new GUI cases/captures.

## Two proved defects and fixes

1. A bare-X11 windowed Tk preview with pointer outside its mapped1280x820
rectangle ignored first real Escape; no native/Tk focus was owned. Initial
screen focus requests occur before mapping and are ignored. `run()` now claims
input once after the root maps, then rerenders through the existing screen
renderer to restore its intended child. The mapping binding removes itself
before scheduling the one claim. Already-mapped run uses one idle claim. No
blocking visibility wait, repeated focus claim or key ledger reset added.
2. General Tk body wheel events targeted at descendant prose never reached
canvas/inner bindings. A root bindtag route now walks to the current body canvas;
footer/outside widgets are ignored. Text/Listbox/Treeview/scrollbars and nested
canvas scroll regions keep their own wheel behavior; old canvas/inner handlers
were removed to prevent duplicate movement. Picker handling remains separate.
Existing ±120 wheel-unit and tiny-delta behavior preserved.

No selection, discovery, nwipe flags, confirmation token, owner authorization,
method, countdown, product claims, pinned dependency or publication changes.

## Before-edit evidence and failed-check dispositions

- `tk_wizard-before.py`, SHA256
  892d9dc27082c84ca5bfa06dc09dc36c90b7b19e23ff402e22c89a861c855fee,
  exactly matches starting source. It was never restored over shared work.
- `original-proof.xml`:8cases,3intendedFAIL/5controls,2.48s.
- `original-native-proof.xml/txt`:10cases,5FAIL/5PASS,2.76s; four intended failures
  and one setup error assuming a blank canvas gutter. The hit-test showed the
  label covers the point; the original setup/test variant is retained as
  `test_body_wheel-initial-native.py`.
- Corrected `original-confirmed.xml/txt`:9cases,4intendedFAIL/5controls,2.71s.
  Native Escape and real XTest wheel are delivered to actual owned windows;
  the wheel case hit-tests the prose label. Same-canvas synthetic events are
  normal controls. No errors/skips. Root independently reviewed this proof.
- Initial fix `fixed-focused-initial.xml/txt`:53cases,42PASS/11FAIL,0ERROR/0SKIP,
  12.707s. Nine failures proved the first implementation claimed root focus
  before mapping resolved the intended child. `focus-ordering.txt` records
  constructor/firstidle/nestedidle mapped0/last'.', then root Map, root-onlyfocus.
  `focus-map-claim-redraw.txt` proves the corrected Map→idle→nativeclaim→renderer
  sequence leaves the intended primary focused at120ms. Initial source/test
  snapshots and private trace scripts are retained. Two failures were test-only
  geometry setup: packing a label into the gridded footer. Only its parent was
  changed to the existing packed footer column; assertions were preserved.
- `fixed-focused.xml/txt`:all53PASS/0SKIP/0ERROR,12.364s after correction.
- Expanded final module:all61PASS/0SKIP/0ERROR,17.195s,
  `fixed-focused-expanded.xml/txt`. Eight extra controls cover initial mapped/
  unmapped Keyboard Entry, owner checkbox, confirmation Entry and LastChance
  safe Back focus, preserving wizard state and the exact3sec remaining review.
- `fixed-adjacent.xml/txt`:630PASS/0SKIP/0ERROR across27existing Tk/curses/plain/
  startup/kiosk/refresh modules,120.512s. Exact selection and command retained.
  This is691disjoint focused cases including the new61, overlapping the later
  root full gate. No extra runtime campaign was active alongside these jobs.

## Native artifacts

Two unedited full-root ImageGrab PNGs were generated from private72DPI Xvfb,
viewed by this agent, with exact native hit target, geometry/focus/yview, source
hash, image hash, owner false/token empty/no wipe request and owned teardown
receipts in adjacent JSON files. Tk reports72.05673758865248pixels/inch, matching
its explicit scaling1.0 and integer-mm X server geometry.

- `tk-body-native-800x600.png`:actual800x600root,800x600window at0,0.
  SHA256135b0fe40a835fc72b8ce7e156e16fac3fc9d7fce0963131c17800f289bd2ba6.
- `tk-body-native-1600x1000.png`:actual1600x1000root,800x600window at400,200.
  SHA256503b94cf3a2ee398b8c4aee772b1bf5e781c6882a500c939c15861aa8cb78dc4.

Both show the scrolled owner preparation body while the footer remains visible;
the top title is partly above the viewport because the native wheel moved it.
Neither image is cropped, resized, annotated or otherwise edited. Each receipt
records button5 delivered over the hit-tested title label and body yview moving
from0 to0.06320907617504051. `capture.py` is the exact producer script.

## Final identity, review and handoff

- Runtime source SHA256:
  9d098c65fd501cceabbfa7277037bc3c4225b685e33d3a8b12eed19e3bc05910.
- New61-case module SHA256:
  726364bbe995765ce3e869fb8f48d8332b39fee831cef7691600b58406e02648.
- Independent source/test reviewer `/root/pass13_discovery` approved these exact
  final hashes, superseding its first source-only approval after runtime exposed
  the mapping-order defect. Review notes are in that agent's evidence directory:
  `/tmp/pass13-discovery/ui-independent-review-round2.md`. Root also reviewed
  before-edit proof, ordering trace, corrected source and expanded state controls.
- All owned GUI windows, tests, private Xvfb/D-Bus sessions and native input
  connections have exited; runtime slot explicitly released to root.
- Source-only review coverage and detailed before-edit history remain in
  `review-notes.md`. No further UI bug is proved or source edit pending.
- Root owns independent original-source reproduction, exact final freeze, full
  local gate, durable repository evidence and unresolved historical acceptance
  or ISO/nativeWindows/physical qualification. This report does not claim those
  unavailable acceptance checks or a deployed/committed state.
