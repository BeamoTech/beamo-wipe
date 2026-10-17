# Pass18 UI and boot source review

2026-10-17; `/root/dev/Beamo Wipe`; branch `fix/safety-audit-20261015`;
HEAD `35107a8d1a701093eac876a58ab4efd50e291673`. The primary owns the
762-input starting freeze and all runtime verification. This child ran no
tests, GUI, native inventory, engine, network, build, or privileged commands.
No existing fixture changed during this review. After the primary proved the
curses candidate, its explicitly authorized minimal console patch was applied.

## Curses candidate proved by primary

`ui/console_wizard.py` computes the final-review footer before painting the
body and calling `stdscr.refresh()`. Once the initial full review is visible,
the overlay releases and starts five seconds. A later repaint can begin while
the gate is blocked and finish after that deadline. The next Enter reaches
`_handle`, which checks the current live `wizard.erase_enabled`, even though
the painted footer still says to wait. Thus a queued Enter can be accepted
without a frame visibly offering the enabled Erase action. The primary reports
an authenticated original-source run: nine intended assertion failures and
63 controls, zero errors/skips. Root retains the actual command/JUnit receipt.

The new fake-only module `tests/test_curses_rendered_erase_gate_pass18.py`
has 72 prospective cases: three methods, three recognized Enter encodings,
and eight timing/lifecycle paths. The failing hypothesis is a later paint
that begins at t=2 while blocked, finishes at t=6, then consumes an Enter
queued before expiry. Adjacent controls cover a ready frame before input,
fresh input after a ready repaint, early input, an initial slow frame whose
overlay must restart the countdown, a slow frame still before expiry, Back,
and input disappearance. All actual engine, discovery, shutdown and sound
entry points are forbidden. Only a fake clock and fake Terminal are used.
Space and E have no Erase mapping on LAST_CHANCE and do not need a separate
mapped-action probe. The primary inspected and ran the tests before authorizing
the product change. `console_wizard.py` now snapshots readiness immediately
before constructing the footer and rejects Enter belonging to a blocked frame.
This rejection is after existing Enter-hold bookkeeping, and `_handle` retains
its independent live model-gate check. New test assertions were not changed for
this patch. Fixed verification remains the primary's next action.

## Tk variable trace candidate proved by primary

`_CheckRow` registers a variable write trace to its bound `_on_variable`
method, but does not retain/remove its token on destruction. Tcl can retain
the destroyed row and its local variable; a separately retained variable can
also invoke a stale row after its widgets are gone. The shared owner IntVar
is not a `_CheckRow` variable, so this review does not claim that normal owner
consent triggers this path. Local comparison/report preference controls are
rebuilt through screen redraws and are the resource-retention concern.

The primary authorized source-only preparation of
`tests/test_checkrow_trace_lifetime_pass18.py`: 20 native Tk cases for its
private 72-DPI X11 runtime. Six hold a variable across row/parent/redraw-clear
destruction and assert no stale callback; six require weakrefs to a destroyed
local row and variable to release; eight preserve live/shared-peer traces,
including four controls with no destruction. The fixture independently
retires pending row after callbacks before destroying widgets so this probe
isolates variable traces. The primary authenticated 16 intended assertion
failures and four passing live controls, zero errors/skips, on unchanged
starting Tk source. It then authorized retaining the exact row trace token
and retiring that token from the row's own Destroy event. That minimal patch
is applied; `final-source-review.md` and `final-source-hashes.json` identify
its bytes. Fixed verification remains the primary's responsibility. No child
runtime was performed.

## Inspected source and rejected hypotheses

- `wizard.py`: owner/token/method binding, layout change invalidation,
  keyboard/report/refresh detours, fresh countdown on return, overlay depth,
  refresh claims, launch claims, Back, stop confirmation, shutdown recheck,
  report-discard generation. State guards preserve fail-closed transitions.
- `ui/tk_wizard.py`: key press/release repeat timestamps, generation-bound
  navigation, startup and widget callback retirement, asynchronous refresh
  admission, teardown, stop/shutdown handlers. Disabled rendered buttons
  already prevent the equivalent slow-paint Erase activation.
- `ui/accessible_wizard.py`: generation-bound GTK actions, token/owner
  signals, held-key tracking shared with the sound modal, refresh result
  handoff, runtime settlement, startup. GTK's sensitive-state check prevents
  the equivalent activation through a disabled rendered control.
- `ui/sound_dialog.py`: overlay ownership, screen epoch retirement, ticket
  cancellation, output restore and stop action. No supported new defect.
- `ui/console_wizard.py`: plain TTY typeahead flush, curses Enter/Escape/Space
  repeat suppression, paged review visibility, report/diagnostic explicit
  prompts, Back and terminal failure. The two issues above were proved by the
  primary; no other supported new issue was found in this assigned source scope.
- GTK startup retains a timeout after manual close, but its first line
  observes the already recorded outcome and returns False before touching
  destroyed widgets. This is bounded cleanup latency, not demonstrated
  invalid-widget execution; no product change proposed.
- `packaging/live/inside-docker.sh`, pinned engine build hook, live entrypoint,
  kiosk supervisor, systemd service, package list, GRUB and ISOLINUX menus:
  reviewed source pin, immutable engine placement, clean live overrides,
  private tmpfs, no network, finite retry budget, non-erasing recovery and
  fail-closed power check. No new proved defect. Boot/hardware qualification
  remains unrun; reading these files is not acceptance.
- `scripts/build-iso.sh`, `scripts/ci-blacksmith.sh` and
  `.github/workflows/ci.yml`: reviewed staged-input copy verification,
  candidate bundle protection, secret-free container phases and required
  Linux/Windows result aggregation. No automation or publication change is
  proposed, and no hosted job was started.

Current project AGENTS.md and relevant remote-development/product-constraint
notes were read. `/root/dev/AGENTS.md` remains absent, matching the existing
primary record. Historical incident/trace/platform acceptance blockers remain
the primary's responsibility and are not resolved by this source review.
