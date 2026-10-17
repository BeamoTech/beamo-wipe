# Tk native asset ownership: bounded source review

2026-10-17 / pass20_tk_lifetime. **Source review and proof preparation only.**
The author ran no Tk, product, pytest, collector, worker, or child process.
Product and canonical test files were not edited. Root owns serialized runtime.

## Established source facts

- `TkWizard.__init__` creates 17 `tkinter.font.Font` wrappers, three persistent
  variables, two logo images, and the `root._tk_wizard` backlink. `_support_qr`
  may subsequently own a third image. The persistent variables currently use
  the default root rather than an explicit master; do not silently widen this
  task into a multi-root behavior change without an independent proof.
- `_comparison` creates a BooleanVar captured by `toggle`; `_report_help`
  creates `choice` and `share` BooleanVars captured by command closures.
- `_CheckRow` stores `_font`, `_variable`, `_command`, `_label`, and `_icon`.
  Its Destroy observer retires its exact variable trace, but does not release
  those Python references. The local variable can therefore survive destruction
  in a row/label or command closure graph. This matters on redraw, before the
  outer `run_tk` boundary is reached.
- `_Button` stores its command closure, **not** the Font wrapper; its font is
  converted into a Tcl canvas option during construction. `_Scrollbar` stores
  a command that is commonly bound to a peer Text/Canvas. `_Box.inner` and
  normal widget `.master` links create additional Python widget cycles.
- `_teardown` retires the two owned variable trace tokens and owned callbacks,
  then destroys the root. It does not detach app resource/widget references or
  the root backlink. Tkinter widget destruction deletes Tcl commands and child
  dictionary entries, but leaves arbitrary Python fields and `.master` intact.
- `run_tk` constructs the UI then calls `ui.run()` with no cleanup boundary.
  `run` has no finally around its actual mainloop. A mainloop `quit()` or an
  exception can therefore return/propagate without `_teardown` at all.
- The refresh thread target closes over `self`; `_refresh_worker` also uses
  `self.w`. A daemon can retain the UI beyond close and release its last owner
  on the worker. Removing the root backlink alone does not address that path.
- Installed Python 3.12 Tkinter source: `Font.__del__` invokes `_call("font",
  "delete", ...)`; `Variable.__del__` invokes `_tk.call`/`globalunsetvar` and
  deletes registered commands; `Image.__del__` invokes `tk.call("image",
  "delete", ...)`. Font-only lifetime coverage is insufficient.

The pass19 supported-run proof already establishes late worker finalization of
owned fonts. The full-run first-failure snapshot locates a live audio worker
inside `Font.__del__`. Neither source review nor that snapshot identifies the
font in the original full run or proves the native abort's complete cause.

## Minimal complete product-owned release strategy

1. Add one idempotent deterministic retirement routine, used by ordinary close,
   a `run`/outer `run_tk` finally, and partial-constructor failure cleanup. Every
   native interaction and native wrapper release occurs on the creating UI
   thread. Keep the original returned code and original propagated exception.
2. **Pin the exact owned native wrappers and root in local variables before
   unlinking graph edges.** Use a finite reviewed resource list, plus variables
   owned by current `_CheckRow` instances. A worker can collect between ordinary
   Python statements; unlink-then-gc without these pins leaves a race.
3. Retire exact owned trace/timer tokens, preserving peer variable observers and
   other owners' timers. Destroy widget children through their normal destroy
   methods. Make `_CheckRow` destruction release its exact stored variable,
   font, and command references, including redraw destruction. Repeated destroy
   must remain harmless. Do not sweep all variable traces.
4. Detach the finite audited app-owned native fields and widget-container
   fields. Remove `root._tk_wizard` only if it still points to this owner.
   Existing `_draw` resets omit some resources (for example keyboard-card
   dictionaries and `_more_button`), so reusing that reset list alone is not a
   complete inventory. Do not clear unrelated Wizard/owner state.
5. Collect now-unreachable Python widget cycles on the UI thread while root and
   resource pins are strong. Then release the resource/root pins naturally on
   that same thread. No global GC mode/threshold change, Font delete flag
   mutation, patched destructor, traceback clearing, or arbitrary attribute
   sweep is needed to release the product-owned references.
6. Cover raw `root.destroy()` if it is a supported fixture/embedding path: a
   root-only Destroy observer can invoke retirement without recursively calling
   destroy. Descendant Destroy events must not retire a live wizard. The outer
   finally remains necessary for mainloop quit and exceptions. Do not depend on
   a callback after the root has already stopped processing events.
7. Either make refresh workers operate on a detached worker-safe state object
   rather than the UI, or prove that retirement leaves their retained `self`
   with no native assets. Joining a blocked discovery daemon indefinitely is
   not an acceptable disposal strategy.

This is a design proposal, **not an implemented or verified fix**. The finite
field inventory must be checked against the actual final implementation and
tested at the supported boundaries. Native resource pins also prevent GC from
moving finalization to an unrelated worker while the release graph changes.

## Required ownership boundary and objections

Retaining the application object or its Python exception frames must not retain
product-owned fonts/images/local variables after disposal. An exception frame
can also directly retain a Tkinter root, e.g. `Misc.mainloop(self=root)`, or an
embedding wrapper's bound `original_mainloop`. No app-field cleanup can make an
outside strong native-object reference disappear while preserving that frame.
Do not claim that all roots are reclaimed before returning in that situation.
Externally retained variable peers must remain usable and keep their exact
observer token; their subsequent lifetime belongs to that external owner.

The proof extension deliberately keeps an original exception object/traceback
and separately keeps the application object. It requires product-owned native
wrappers to be released on the UI thread and preserves externally retained
variable observers. The root itself may remain alive when a traceback or peer
holds it. A proposal that claims arbitrary external root release on a worker is
safe needs an additional thread-affine interpreter ownership design; it cannot
be established by `ui = None; gc.collect()`.

Construction is another boundary: if Font allocation or initial draw raises,
`run_tk` has no assigned `ui` to clean. Cleanup therefore needs either an
initialized partial-construction owner or an exception-safe resource factory.
Do not add only a finally after successful construction and call that complete.

## Root-run proof matrix

`ownership-boundary-probe.py` is a prepared evidence-local module, not executed
by this reviewer. It extends the retained pass19 proof with strong retention of
the original raised exception and optional retained UI, constructor failure,
mainloop quit, raw root destruction, and local-variable redraw. Native wrapper
weak references and unmodified-destructor entry/return observations identify
their natural finalization thread. The observations add allocation pressure;
successful instrumented cases cannot replace an unchanged canonical gate.

After the original-source failure is authenticated, root should add regressions
that assert the actual behavioral contract without observational monkeypatches,
then run unchanged full main/Orca collection. Preserve the pass19 failed gates,
original exact source receipt, historical timing failures, and platform limits.
