# Pass15 UI / startup / boot review

- Date/author:2026-10-16 / delegated Codex pass15_ui_boot.
- Repository `/root/dev/Beamo Wipe`; root coordinates final source identity.
- Current AGENTS.md and latest unfinished work entry read. Shared guide absent;
  prior owner continuation supplied by root. Notes grant no authority.
- Source-only review initially. No product/test edits, staging, commit, push,
  hosted CI, physical media, native inventory/engine/power, guests or loops.

## Reviewed paths and disposition

- `ui/tk_wizard.py`: current mapped startup input claim, hold/release repeat
  guards, generation-scoped actions, body wheel/focus reveal, picker scroll
  restoration, nested inventory/comparison keyboard controls, close/teardown,
  countdown restart and progress/report redraws.
- `ui/accessible_wizard.py`: generation and screen guards, held keys and exact
  repeat timestamps, focused last-chance Enter dispatch, async refresh launch
  decision gate, callback failure settlement and modal focus/release handling.
- `ui/console_wizard.py`: startup/fallback failure handling, terminal loss,
  owner/token/method action dispatch, paging/review exposure, held key quiet
  intervals, Stop/report/shutdown confirmations and read-only inventories.
- `startup_stages.py` and both graphical startup presenters: report queue then
  final drain, stage markers, persistent graphical stall note, abandonment,
  display checks and owned widget lifetime. No supported new defect found.
- Shipped kiosk supervisor/service/entrypoint: finite retry budget, no shell,
  independent recovery text, exact pgrep failure semantics, typed power action,
  tmpfs logs, isolation and unset test environment variables. Safety boundaries
  hold in reviewed source. Native qualification remains unrun.
- `scripts/build-iso.sh` reviewed output/prior-bundle ownership and failure
  cleanup portion; current dedicated regressions cover displaced/symlinked and
  concurrent output preservation. No new evidenced build defect found.
- Desktop Go launcher main/firmware/inventory boundaries source reviewed;
  readiness and optional guided restart only, no erase path. No operation run.
- `docs/claims.md` is unchanged and still limits overwrite/SSD/certification,
  platform and Secure Boot claims. No new conflicting product copy established.
- `app.py` reviewed session replacement, staged display abandonment, accessible
  handoff, exception settlement and final shutdown recheck; a new session keeps
  language/keyboard/text preferences while rebuilding authority-bearing objects.
- Current `ci.yml`/`ci-blacksmith.sh` source retains lint/types/tests/preview/
  launcher/negative, ISO, QEMU and native Windows phases; required gate insists
  both platforms report success. No hosted action dispatched.

## Candidates and controlled probes

1. Tk empty screen recursively binds its outer `_wheel` to inventory Text
   descendants after `_other_devices`, replacing widget wheel semantics and
   returning `break` before native Text class handling. Existing pass13 wheel
   isolation tests use OWNER, and existing inventory keyboard tests use PICK.
   Prepared `empty-wheel-probe.py` with empty vs picker controls, four wheel
   forms, independent inner/outer views, focused geometry and unchanged wizard
   state. All native application effects forbidden. `run-empty-wheel.py` owns
   private72DPI display170+ and DBus. Actual hit testing verifies the reader is
   visible before dispatch. All callback exceptions are collected and printed;
   Tcl-only after cancellation precedes normal teardown. Root admitted one
   runtime campaign after discovery lane release; it exited normally0.
2. Generic body PageUp/PageDown would also intercept native Text class binding
   if a reader were present there; canonical report/disk/limits readers exclude
   the general body canvas, picker comparison/inventory return `break` before
   root. No supported current production trigger established; no fix proposed.
3. Curses ASCII input was checked against token construction: safe confirmation
   tokens use explicit ASCII letters/digits/punctuation, so no supported Unicode
   confirmation-token dead end exists. No fix proposed.

## Limits

Source review is bounded and is not full local gate or native ISO/Windows/
hardware acceptance. Root independently validates any concrete trace before
editing, owns full final gates and retains durable evidence.

## Concrete wheel proof

- Current Tk source SHA256:
  `9abb3cf1800a04d8f094c030b2b7a2052d8da3b608389dc95bbfb07b0454a8ea`.
- Eight cases: four empty-screen failures and four picker controls, across
  Button4/5 and MouseWheel±120. Every dispatch was hit-tested against the
  actual visible disabled Text at a real root coordinate,800x600/private72DPI.
- Empty reader yview starts `.3006802721088435` and never changes, while its
  nearest outer canvas moves in the requested direction. Widget wheel binding
  names `_wheel` and returns `break`. Picker reader changes in all four cases,
  outer canvas remains exactly unchanged, and no widget wheel override exists.
- All8 retain focus and wizard screen/owner/disk/token/method/authorization/
  request; engine not started. Zero forbidden effects and callback errors.
- Original artifacts: `empty-wheel-probe.json`, `.txt`, `empty-wheel-exit.json`,
  prepared scripts and two unedited PNGs `empty-wheel-empty.png` and
  `empty-wheel-happy.png`; both PNGs visually inspected. Exit0 means harness
  completed, **not** that the four measured empty-screen behaviors passed.
- Directly focusing an offscreen inventory remains offscreen on both empty
  and picker controls before manual fixture reveal. This is not a separate
  proven regression or new defect claim; no change proposed from that field.
- Runtime lane released to root. No shared source/test changed.

Minimal candidate repair is to stop recursive empty-screen wheel binding when
reaching independent native/custom scroll surfaces, preserving their class/
widget handlers and outer empty prose scrolling. Root owns independent proof,
any implementation, regression tests and final checks.

## Approved regression module

Root independently reproduced the4/4 result using native XTest Button4/5 and
then authorized writing only `tests/test_empty_inventory_wheel_pass15.py`.
The module now contains64 cases:48 empty/picker reader cases across3 profiles,
4 wheel forms and redraw/current;8 ordinary empty prose controls;8 actual
nested custom scrollbar cases. Profiles include800x600standard/extra and
1280x720large, requiring a private1600x1000 or larger display at72DPI.
Button4/5 use actual private XTest; MouseWheel remains Tk synthetic. Every
target is visibly hit-tested. Read-only text, inner direction, outer stability,
focus, authorization/request/state and no-effects invariants are checked.
Callback errors fail; fixture-owned Tcl timers are canceled before teardown.
Tests have not been run by this delegate. Primary independently ran all64 on
exact original source:32intendedFAIL/32controls,0errors/skips. Per root request,
the test file is frozen at SHA256
`9e1dd204f39e96c7a6943783687481056caff0dffff3b0b520d206666c069138`;
no further writes without coordination. Product repair/focused validation and
requested exact-source peer review remain pending at this checkpoint.
Only this approved test file was added in the repository; product unchanged
by this delegate. Root owns any implementation and all acceptance gates.
