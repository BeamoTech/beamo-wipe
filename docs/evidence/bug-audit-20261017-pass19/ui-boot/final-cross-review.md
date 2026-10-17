# Pass19 final independent cross-review

2026-10-17, Codex `/root/pass19_runner`. Source-only review. No application or
test runtime, device/inventory/engine probe, network request, product/test edit,
commit or push was performed by this reviewer. Standard-library byte hashing,
archive reads, AST inspection and diff reconstruction were used to authenticate
the inspected source. Exact identities are in `final-cross-review.json`.

Independently authenticated every one of the 766 starting archive streams and
771 final frozen inputs, reconstructed the full four-file incremental diff
exactly, read all five new modules and their imported fake-device guard fixture,
and recomputed runtime framing from source bytes without importing the app.
The runtime SHA256 is
`a69d8d2d8199b71a28f5f5280bad6d4bb13f46211d0f5e68a6f1d13d99c9460b`.
Exactly two runtime files, two existing fixtures and five new test modules
changed or were added; the other 762 starting inputs remain unchanged.

No source objection remains to these exact nine inputs:

- Discovery reuses its established stacked-holder predicates. A bcache device
  reported as TYPE=disk no longer terminates physical ownership resolution at
  itself. Missing, unknown or cyclic holder ancestry cannot silently discard an
  opened filesystem. A filesystem below an otherwise blank holder receives the
  same check through `_has_stacked_holder`; the filesystem evidence belongs to
  the descendant, so this preserves blank unmounted subtree controls.
- Repeated TYPE=disk bcache records now enter the shared-device ancestry guard
  before display construction. Identical filesystem copies can no longer claim
  different raw parents merely because their eventual Disk records compare
  equal. Malformed display metadata cannot remove one copy before this guard.
  Ordinary physical disks remain outside this mapper grouping. Repeated copies
  on one owner, distinct holders and blank unmounted mappings retain controls.
- Ownership resolution checks tree versus PKNAME at both the starting node and
  every traversed ancestor. A blank holder with a contradictory parent cannot
  redirect a descendant filesystem to another raw disk. The resolver returns
  unknown/ambiguous rather than guessing; existing callers' fail-closed checks
  remain in force. Consistent nested and flat chains continue to resolve.
- Tk records the exact two confirmation/typing variable trace tokens during
  construction and retires those tokens before destroying its root. Clearing
  ownership before removal makes repeated teardown harmless; Tcl already-removed
  trace/interpreter state is tolerated. Independent observers, actual callback
  bodies and live input behavior are preserved. This does not turn callback
  suppression into a substitute for removing a retained reference.
- The GTK slow-audio fixture now owns a private AudioWorker and enters its
  release-finally before the first timed click. Releasing the controlled barrier
  precedes closing/joining that worker; a new assertion requires the owned
  thread to have settled while its mocks still exist. Both original 60 ms
  assertions and all closed-dialog checks remain. This improves failure cleanup
  and isolation; it does not establish the cause of the prior 74.932779 ms click.
- The prior checkbox fixture's independent peer observer remains active through
  every original assertion and recorded trace/callback evidence. Its finally
  removes only `peer_token`, including failing old-source paths. It neither
  removes product-owned traces before assertions nor sweeps peer callbacks.

Independent AST comparison confirms all 301 original accessible-runtime
assertions remain, with one added worker-settlement assertion (302 total), and
all 24 original checkbox-module assertions remain exactly. No bound, expected
outcome, state assertion or effect guard was weakened. Literal parameterization
counts independently total 214 new cases: 74 descendant-holder, 30 duplicate
bcache, 72 ancestor-contradiction, eight Tk-owner lifetime and 30 unbound bcache.
The new source includes refusal cases and valid flat/tree/blank/peer controls.

The discovery fixture supplies all inventory and stubs production metadata
acquisition while rejecting native process calls and native-path opens. Tk
proofs require explicit private X11 and reject engine, power, discovery and
audio process effects. Their cleanup follows assertions and retires exact
fixture-owned resources, including failures against old source.

Earlier review observations were refined, not treated as proof: normal mixed
bcache copies can be rejected by final Disk/layout reconciliation, while equal
copies and a display-skipped copy evade that later comparison. The new earlier
shared-device guard covers those root-proved cases. The separate transitive
ancestry proof motivated both resolver-edge checks; no speculative extra policy
change is included in the final patch.

Root owns the retained original/fixed proofs, full applicable gate and fresh
artifact campaigns. This review is source evidence only. The historical GTK
delay remains unexplained; a later passing run cannot explain that event.
Historical incidents and ISO/QEMU, native Windows, physical reconnect/firmware
and real-hardware acceptance remain distinct limits. This receipt grants no
commit, push, hosted job or release authority.

After candidate1 source review, the root focused gate exposed one existing
error-classification assertion: earlier resolver refusal reported filesystem
ancestry for a mounted mapper whose intermediate parent contradicted the tree.
The correction retains the safe refusal and restores the existing mounted
ancestry category when `mounts` is nonempty; unmounted filesystem errors retain
their category. No test changed. This peer read that exact two-line correction
and authenticated all771 final bytes and all766 original archive streams again.
The earlier candidate1 receipt/report remain separate historical evidence.
Affected runtime acceptance remains root-owned; no passing retry is presumed.
