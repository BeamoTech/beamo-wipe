# Private candidate4 protocol and limits

2026-10-17 / pass20_tk_lifetime. **Private source only, not runtime qualified.**
No product imports, Tk, tests, threads, collectors, or child processes executed
by this author. The active private tree and shared product/tests were not edited.

Input: `/tmp/pass20-primary/private-graph-candidate3.py`, SHA256
`b3d66bdb83213000c9623a2a48c25cf39b089289a388aba67507f117b4a59546`.
Output: `/tmp/pass20-primary/private-candidate4-agent.py`, SHA256
`68b25648c658e5dc9de1e9f7edf3663c90f4dc52520852a8ea8458aa40f8327f`.
Exact patch, AST-only receipt, and preparation script are alongside that output.
Root must freeze/review any subsequent correction separately.

## Implemented private protocol

- Store the creating Thread object before native initialization. Pool entries
  compare Thread identity, avoiding reused integer thread IDs.
- Retain exact Font/Variable/Image wrappers separately from raw Tcl interpreters.
  Pin before unlinking graph edges; preserve original native destructor behavior.
  On CPython the sole-owner test is refcount2: the record plus getrefcount's
  temporary argument. Tuple list/snapshot/loop references do not add another
  direct reference to the contained native object.
- Drain assets in a helper that returns before raw interpreter draining. Its
  snapshot and loop variable otherwise temporarily retain the final asset and
  therefore that asset's interpreter. A lightweight drain after row destruction
  and successful draw performs no full collection. Full collection remains at
  constructor/teardown/outer run boundaries.
- Retire `_CheckRow` exact fields/tokens in an idempotent helper used by both its
  Destroy observer and destroy-finally. This covers partial construction before
  the event binding exists, while preserving independent variable traces.
- Continue native teardown if audio cancellation fails. Reset `_retiring` in a
  finally. Propagate a standalone cleanup failure; when already handling an
  original constructor/mainloop error, retain that exact exception and traceback
  and add a typed secondary note/diagnostic rather than replacing it.
- Allocate real Tk/owned native wrappers before invoking their initializer, so
  an initialization exception has an exact object to pin. Callable lightweight
  test factories retain their ordinary calling convention. There are 25 explicit
  owned native factory call sites: 17 fonts, three persistent variables, three
  local BooleanVars, and two image creation sites. Existing constructor arguments
  are preserved, including the current default-root variable convention.
- Keep the closed root wrapper on the UI to preserve existing references and
  fixture contracts. Other finite native/widget fields detach. The raw pool
  protects a retained root/traceback if its final Python owner later disappears
  on a worker. External variable owners retain their native handles and tokens.

This adds more lifecycle code than font-only graph collection. The additional
machinery addresses concrete separate ownership boundaries: partial root
allocation, partial row construction, and wrapper arguments held by retained
exception frames. The after-native wrapper-initializer cases are prepared in
the next proof revision and still require root-run original/fixed evidence.

## Known source objections awaiting root proof/correction

1. **Uninitialized Tk lookup recursion:** private candidate4's generic
   `getattr(root, "tk", None)` can enter Tk.__getattr__ before Tk.__init__ has
   assigned `tk`. A controlled initializer failure before its first statement
   can therefore mask the original error with RecursionError. Inspect an actual
   partial root's `__dict__` rather than invoking dynamic Tk attribute lookup.
   The new no-native proof case exercises this explicitly; this frozen candidate
   is intentionally not silently corrected before original proof.
2. **Direct run setup:** the product `run_tk` outer cleanup covers failures in
   `run` setup, but direct `TkWizard.run()` callers still execute focus/map setup
   outside its local error-retirement block. Wrapping setup and mainloop in one
   block is a small correction if that direct contract is retained. Prove the
   setup fault before calling the contract complete.
3. **Startup scope:** `run_tk_startup` still uses a raw Tk constructor and its own
   cleanup. Its partial-native-construction/error-chain behavior has not been
   proved or covered by this private candidate. Reuse only after a focused proof.

No destructor is skipped, made inert, or replaced by this candidate. No GC mode,
threshold, native handle, traceback frame, real disk, firmware, or host setting
is changed. Observational proof wrappers invoke original destructors but do
change allocation pressure; they cannot replace an unchanged full gate.

Pool entries may remain while external peers/tracebacks hold resources, until a
later creating-thread sweep or process exit. This is deliberate safe deferred
ownership, not an immediate-reclamation claim. Product Tk is owned by its main
UI thread. Arbitrary outside Tk creation in a thread that exits before ownership
settlement is not qualified by these proofs or by the process-global pool.
