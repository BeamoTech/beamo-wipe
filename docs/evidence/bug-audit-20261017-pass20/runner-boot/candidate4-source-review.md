# Private Tk candidate 4 — independent source review

2026-10-17 / Codex `/root/pass20_runner_boot`. Read-only source review of
`/tmp/pass20-primary/private-candidate4-agent.py`, SHA256
`68b25648c658e5dc9de1e9f7edf3663c90f4dc52520852a8ea8458aa40f8327f`.
Compared the retained pass19 shared source (`23d280...`) and private candidate3
(`b3d66...`), exact supplied patch/metadata, constructor proof source and the
installed CPython 3.12 Tkinter implementation. No product imports, runtime,
tests, threads, GUI, native or device operation was performed. No product/test
source was edited. Root's constructor8 proof on candidate3 is existing evidence;
the additional source-supported cases below are NOT PROVED by this reviewer.

## Two unresolved objections

1. **Early root initialization can replace the original exception.**
   `_new_owned_root` manually allocates a genuine Tk wrapper, then invokes its
   initializer. If that initializer raises before `self.tk = None`, the except
   block immediately calls `_pin_retired_interpreter`, whose
   `getattr(root, "tk", None)` enters `Misc.__getattr__`. That method itself
   reads `self.tk`, so an uninitialized root recurses instead of returning the
   supplied default. The later getattr in `_new_owned_root` has the same issue.
   CPython's Tk initializer explicitly comments that assigning `self.tk = None`
   avoids this recursion. Current loadtk-before/loadtk-after proofs occur after
   the attribute exists. Root should prove an initializer-entry failure using
   the real class, require preservation of the exact exception and verify no
   unnecessary native operation. A nondelegating instance-dictionary lookup or
   guarded object attribute access can distinguish an absent interpreter.

2. **Asset removal invokes wrapper equality instead of exact ownership.**
   `_drain_retired_assets` uses `_RETIRED_NATIVE_ASSETS.remove(record)`. Searching
   for a later tuple can compare its native wrapper against earlier records.
   Tkinter Font and Variable implement value equality using `name`/`_name` and
   interpreter fields. Distinct aliases can compare equal, and a partially
   initialized wrapper can lack those fields and raise during comparison. A
   retained earlier peer plus an eligible later partial wrapper therefore needs
   a bounded proof before this removal strategy is accepted. Ownership removal
   must target the exact record identity/index; content equality is not the
   release condition. Raw interpreter records have no corresponding known
   Font/Variable equality overload, although consistent identity removal there
   is also straightforward.

These are source-supported counterexamples, not claims that either occurred in
the old full-run abort. Candidate4 is not approved until root proves/reconciles
the objections, corrects warranted defects and reviews the resulting exact bytes.

## Reviewed behavior with no additional source objection

- The CPython refcount release order is otherwise coherent. The pool list,
  slice and loop retain the same tuple; they do not each add a direct native
  asset reference. Refcount2 means the tuple element plus getrefcount's
  temporary argument. Removed tuples remain held by that helper's local loop/
  slice until its creating-thread return. Returning from asset draining before
  interpreter draining allows the raw interpreter references held by wrappers
  to disappear on the creator thread first.
- Creator ownership uses the stored Thread object and `is`, preventing a later
  thread with a recycled numeric ID from draining another owner's resources.
  Retained peers/tracebacks defer release rather than being neutralized. This
  source argument does not prove eventual pool draining or a memory bound over
  arbitrary externally retained owners; root still needs relevant controls.
- The genuine shipped Tk/Font/Variable/Image classes use ordinary allocation
  and return None from initialization. Explicit allocation retains a failed
  initialized wrapper before assignment and can protect its native state.
  Callable lightweight factories preserve their normal call/argument behavior
  through the fallback. The helpers are not general emulations of arbitrary
  custom metaclass calls, custom `__new__` argument handling or non-None
  initializer results; those are outside the inspected shipped-class contract.
- Every native factory call preserves its original root/master/value/font
  arguments. Persistent variables keep the original default-root behavior;
  no unproved multi-root semantic change was introduced. Partial native object
  failure coverage still needs the sibling's prepared post-allocation proofs.
- `_CheckRow.destroy` retires native references even if construction failed
  before its Destroy binding. Retirement uses getattr defaults, pins the row's
  exact variable/font, retires only the owned trace and clears retained command/
  label/icon fields. Repeated ordinary retirement does not delete peers' tokens.
  The early-root lookup objection also makes nondelegating interpreter access
  preferable when a partial widget has no tk attribute at all.
- `_teardown` resets `_retiring` in finally. Audio-cancel cleanup errors are
  retained while native cleanup continues, then reported. `_retire_tk_owner`
  preserves an original failure and reports a separate cleanup error rather
  than replacing the original exception. Resource pins survive exceptional
  partial cleanup, enabling retry where retirement did not finish. The pool
  lookup/removal objections must be resolved before claiming this complete.
- The actual app enters via `run_tk`, whose outer finally covers a failure in
  `run()`'s initial mapped/focus callback setup after construction. That setup
  remains before `run()`'s own try; a direct caller of `TkWizard.run` therefore
  still owns cleanup for setup failure. This is a bounded direct-call limit,
  not a newly established shipped-path blocker.
- Outside resource creation/retirement and the dead-UI navigation guard, the
  source preserves key handling, held-key release rules, displayed-frame
  actions, countdown restart, final Erase action, refresh worker ownership,
  disk selection and request construction. Wizard safety gates, method mapping,
  engine argv and authorization source are untouched by this private file.
  The added draw drain does not advance Wizard state or enable Erase.

The companion receipt authenticates exact source/patch inputs, changed AST
methods, native factory call count and installed Tkinter references. This is
bounded source reasoning, not a test pass or implementation qualification. The
shared Tk remains unchanged; root must keep all original/candidate/invalid
histories and independently verify the final selected correction.
