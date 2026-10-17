# Private Tk candidate 6 — GC-stop retirement source review

2026-10-17 / Codex `/root/pass20_runner_boot`. Exact candidate SHA256
`d639822ca03fccc2f9be78c476fc4b594118ac2b9195d2a2979b3c8f9a6e7cf8`;
ten-line delta from candidate5 `6b5be8...`. Source/evidence parsing only: no
imports, callback, collector, test, GUI, thread or native operation was executed
by this reviewer. Shared source and canonical assertions were not edited.

The completed unchanged candidate5 broad campaign has 486 cases, 478 passes,
eight assertion failures, zero errors/skips. The exact failed IDs are the two
Wizard owner/variable collectibility cases and six checkbox local-variable
collectibility cases. Their caller retains assets during teardown, drops its
locals and performs creator-thread GC without another private drain helper.
The source-only correction targets that evidenced lifetime gap; the old
assertions and immediate-GC contract remain intact.

Candidate6 appends exactly one GC callback during normal module import. It
ignores start phase and empty pools, then calls the existing lightweight drain
only at stop phase. Neither callback nor either drain calls gc.collect, changes
GC enablement/thresholds, modifies a destructor/handle/traceback, or constructs
UI state. The separate explicit ownership-boundary collection helper is
unchanged. Duplicate module reload behavior is not promised by this one normal
import registration.

Source review supports these bounded arguments:

- A foreign worker's stop callback cannot remove the creator's records:
  Thread-object identity is tested before the refcount condition and exact
  record deletion. Snapshot references do not replace the global strong pin,
  so skipping another owner's entry cannot make that worker its final owner.
- Creator-thread retirement preserves original Font/Variable/Image destructors.
  Eligible assets leave their helper before raw interpreters are considered;
  external peer/traceback references continue to defer retirement. Active/live
  peer wrappers remain strongly referenced and cannot satisfy the sole-record
  refcount condition.
- After a complete snapshot exists, same-thread destructor reentry or new pins
  are guarded by exact dictionary record identity and defer unvisited records.
  No collection is explicitly initiated by the callback. Native destructor
  callbacks retain their normal behavior; the source does not claim control
  over arbitrary externally supplied callbacks.
- Normal owned-child process exit and callback/unraisable stderr still require
  root readback. A source argument alone cannot qualify interpreter shutdown,
  eventual release on a dead creator thread, or unrelated external native
  objects. The shipped UI creator is the main application thread.

One source-supported verification question remains open at this handoff:
`list(pool.items())` allocates while building a snapshot. An automatic same-
thread GC at that explicit-drain allocation boundary could call the new stop
hook and mutate that same pool before the outer snapshot is complete. The
earlier statement that snapshot processing tolerates reentry applies after
snapshot construction, not automatically to construction itself. No failure
has been proved by this reviewer. Root has agreed to a bounded real-native/
real-dict low-threshold fixture with restored settings, preserving callback/
exception traces before deciding whether any guard correction is warranted.
Do not label this a product defect or add a speculative guard without proof.

Source approval is conditional on that reentry admission plus root's unchanged
486-case, constructor/collector, registration/foreign-worker and child-shutdown
checks. The current candidate6 campaigns were not treated as completed by this
review. No attribution of earlier full-run abort, latency or SIGTERM follows
from candidate5's collectibility failures or this proposed callback. Final
source/full main-Orca/artifact/platform qualification remains root-owned.
