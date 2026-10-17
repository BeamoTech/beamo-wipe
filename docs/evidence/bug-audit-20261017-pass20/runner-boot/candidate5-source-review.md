# Private Tk candidate 5 — independent source review

2026-10-17 / Codex `/root/pass20_runner_boot`. Source-only review of standalone
candidate SHA256
`6b5be8d70416318a83b24e3ce6bc9dc212ab63293d2498889810401ecccbfdbe`,
its exact candidate4-to5 patch and metadata. Compared frozen candidate4,
original shared pass19 Tk, installed CPython Tkinter, actual StartupRun and
app startup dispatch. No product imports, runtime, tests, GUI, threads, native
or device action was run; no shared product/test source was edited.

No additional source objection remains for the reviewed candidate5 bytes.
This is bounded source approval, conditional on root proving the selected
candidate and passing its required focused/full/artifact checks. It is not an
implementation qualification or an explanation of earlier full-run aborts.

Both candidate4 objections are now grounded in root evidence and corrected:

- The v3 constructor campaign on frozen4 has 19 cases, five failures and
  fourteen controls, zero errors/skips. `tk-init-before` exposes the original
  exception being masked. The other four failures are owned startup windows
  left open at load-before/load-after/Frame/Label boundaries. Candidate5 reads
  the actual wrapper instance dictionary for `tk`, bypassing Misc's recursive
  fallback when the genuine initializer has not assigned that attribute.
- Root's separate exact-source counterexample records installed Font.__eq__ at
  `tkinter/font.py:110`, called by list.remove, raising AttributeError for the
  earlier partial Font's missing name. Candidate5 keys both pools by object id
  and deletes only when the stored record `is` the inspected record. No wrapper
  equality participates. A strong record prevents object-id reuse while it is
  present. Snapshot/loop references still retain the same tuple, so the accepted
  CPython refcount2 release argument and asset-before-interpreter helper return
  ordering continue to apply.

Direct `TkWizard.run` now encloses its mapped/focus setup in the same cleanup
boundary as mainloop. Setup failure therefore reaches exact-owner retirement
even outside the shipped `run_tk` wrapper. Return/exception semantics, mainloop
control and dead-UI navigation guards are otherwise unchanged from candidate4.

The startup refactor extends owned-root cleanup across title/geometry/configure,
Frame/Label construction, protocol/bind setup, rendering, worker launch, timers
and mainloop. Root creation uses the guarded real-class factory. TclError from
that creation retains StartupDisplayUnavailable with its original cause, so
app's synchronous no-display fallback remains intact. Other setup exceptions
still reach app's blocked-startup explanation; propagated control exceptions
retain their identity. Normal output remains wizard/failed/abandoned.

The inner startup window keeps the actual stage queue and StartupRun instance.
Its render, close and poll_once callback ASTs are identical to original shared
Tk. Stage strings, geometry, labels, the single worker start, poll cadence,
result-paint-before-close and Escape/window-close behavior are unchanged. Exact
owned timer cancellation remains inside the inner finally. Unexpected timer
cleanup failures are recorded while remaining cleanup continues; the outer
finally still closes the owned window and preserves a prior failure. This
changes failure cleanup, not discovery, erasure authorization or startup-stage
claims. Callable lightweight factories retain their prior invocation contract.

The original shared Tk source is still unchanged at review time. Candidate5
does not alter Wizard safety/method/argv source or introduce a new countdown,
key, navigation, launch or engine path. Current root runtime campaigns were
not counted as complete without their completion status, and no candidate5
runtime pass is claimed here. Existing source review limits remain: ordinary
shipped native classes are the supported factory scope; externally retained
peers/frames deliberately defer pool draining; eventual draining and broader
platform behavior need actual evidence. Preserve every original/candidate/
invalid run and bind final verification to the exact selected bytes.
