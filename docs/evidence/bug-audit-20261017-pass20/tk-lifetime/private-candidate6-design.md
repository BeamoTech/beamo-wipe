# Private candidate6 owner-thread collection hook

2026-10-17 / pass20_tk_lifetime. **AST-parsed source only; not run by author.**
The active private tree, shared product files, and existing tests are unchanged
by this author. No original weakref/collection assertion is relaxed.

Base: `/tmp/pass20-primary/private-candidate5-agent.py`, SHA256
`6b5be8d70416318a83b24e3ce6bc9dc212ab63293d2498889810401ecccbfdbe`.
Candidate: `/tmp/pass20-primary/private-candidate6-agent.py`, SHA256
`d639822ca03fccc2f9be78c476fc4b594118ac2b9195d2a2979b3c8f9a6e7cf8`.
The exact ten-line patch, AST receipt, and preparation script are alongside it.

Candidate5's strong pools intentionally defer resources while outside locals or
peers hold them. Existing callers later drop those references and invoke ordinary
`gc.collect()` on the UI thread. They should not have to know a private product
drain helper to finish owner-thread collection. The original collectibility
assertions therefore remain meaningful acceptance requirements.

Candidate6 registers one `gc.callbacks` function. It does work only in phase
`stop` and only when at least one pool is nonempty. It invokes the existing
lightweight drain, not `gc.collect()`. Each drain first compares its recorded
creator Thread by identity; a foreign worker cannot release another thread's
resources. Assets and raw interpreters still drain in separate helper calls so
temporary asset-record references are gone before testing the raw interpreter.
An empty-pool callback is a phase check and two dictionary truth checks.

This changes neither GC mode nor thresholds. It does not patch or neutralize
native destructors, detach handles, clear traceback frames, or sweep unrelated
callbacks. The hook adds its own callback and leaves existing GC callbacks
intact. The full canonical local gate is still required to assess responsiveness
and cross-surface behavior; no latency result is inferred from source inspection.

Root reported 52 boundary passes and a passing equality counterexample on
candidate5. Its broader run had visible collectibility failures at assignment
time, but exact IDs/JUnit were still pending. Those are root-owned results, not
executions by this author, and do not qualify candidate6. Root must authenticate
the original failures and independently run this exact candidate afterward.

Ordinary Python module import registers the callback once. Arbitrary repeated
module reloading, non-main external Tk owner threads exiting before settlement,
and outside mutation of the private pools/callback list are not qualified by
this candidate's source review. Current source/test search found no Tk module
reload or GC callback mutation.
