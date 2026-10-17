# Font lifetime review after the first confirmed failure

2026-10-17, Codex child `/root/pass19_ui_boot`. Source/existing-evidence review
only. No application/test runtime or product/test edits performed by this child.

Root's full-list `--maxfail=1` diagnostic confirms the first failure as
`test_start_error_after_spawn_never_leaves_a_competing_worker[False-False-True]`:
477 earlier cases pass, `next_entered.wait(1)` is false, and the finally block
still observes a live owned thread after its joins. Its immediate scalar thread
snapshot shows that audio worker inside `active()` → `Event.wait()` → condition
entry → `/usr/lib/python3.12/tkinter/font.py:121`, `Font.__del__`.
This identifies a wrong-thread Font finalization path during this failed case.
It does not identify which Tk app created the font or prove the precise native
abort cause of either earlier full run.

## Pre-pass14 fixtures and production ownership

- `test_accessibility_lowres.py`'s native matrix and two later direct app tests
  all call the actual `app._teardown()` in finally. The raw `root.destroy()` at
  line 364 belongs to `_needs_display()`'s temporary root probe and creates no
  explicit `tkfont.Font` object.
- `test_adaptive_layout.py:28` imports the real `ui` fixture from
  `test_tk_runtime.py`. That fixture retains created apps through the test and
  invokes each actual `app._teardown()` after yield (`:70–88`). Its direct
  support-block test also tears down in finally (`test_adaptive_layout.py:429`).
  Raw root destruction in `test_tk_runtime._needs_display()` is another
  temporary root probe without an explicit font.
- Thus a font's origin in these tests would not by itself indicate that a
  fixture bypassed product teardown. Parent's creation/destruction provenance
  must determine the actual instance and lifecycle before a correction.
- Production `TkWizard.__init__` allocates 17 named `tkfont.Font` objects at
  `tk_wizard.py:1149–1165`. `Font.__init__` retains the tkapp in `_tk` and bound
  tkapp methods in `_split` / `_call`; `Font.__del__` calls the interpreter's
  `font delete` command. Destroying a Tk window does not remove those ordinary
  Python references from the app's attributes.
- There are explicit Python ownership cycles after Tcl widget destruction:
  `app.root._tk_wizard = app` (`:1111`) gives app → root → app. The app also keeps
  `_primary` (`:2408`); the destroyed `_Button` keeps its `_command` (`:677`),
  assigned from `_nav(command)` (`:2400`), and `_nav`'s closure captures the app
  (`:1611–1621`). This gives app → primary → command → app. Tk's destruction
  removes Tcl command registrations; it does not clear those custom Python
  attributes or ordinary closure cells.
- `_teardown` cancels owned jobs and traces and destroys the root but does not
  deterministically release these app-owned font references or all such Python
  cycles. `run_tk` simply constructs `ui` and returns `ui.run()` (`:4644–4646`).
  The ownership shape therefore exists in production too. This is a source
  observation, not yet an attribution of the captured font's origin.
- Adjacent interpreter-owning objects need consideration in any eventual
  correction: `tkinter.Variable.__del__` invokes its `_tk` and
  `tkinter.Image.__del__` invokes `image delete`. Deleting only a font name or
  suppressing one destructor would not prove that interpreter ownership is
  released safely. Clearing one root backlink would not by itself remove the
  independent primary-button closure cycle.

## What current regressions do and do not verify

The eight new owner-trace cases explicitly call `gc.collect()` on the UI thread
when checking collectability. That proves the old bound trace leak was removed;
it does not prove that deferred collection of remaining app cycles cannot take
place on a later worker thread. The pass18 local-row collection tests similarly
exercise main-thread collection. Their six failure IDs are still estimates
unless an actual report confirms them; do not infer their cause from glyphs.

Root's next parent-only Font provenance observer should keep only scalar font
ID/name, creation node ID/stack/thread, destruction node ID/stack/thread, and
entry/return timestamps. It must call original initialization/destruction
unchanged and must not retain font, frame, exception or interpreter objects.
Preserve the full active item list and stop at the first actual failure. Use
that evidence to select a bounded fake-only lifecycle reproduction before
editing any product or fixture. No proposed fix is approved by this note.
