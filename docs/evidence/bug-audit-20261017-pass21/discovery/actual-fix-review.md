# Pass21 actual discovery fix review

`pass21_discovery` independently reviewed shared discover.py SHA256
`504315316ded12cf11502614d067139be25908418851895053339fde7bc38067`.
The original source was read from root's immutable starting-inputs archive and
authenticated against starting-freeze.json SHA entry
`9f5a5a36ddf9dad77c7195920ed6290ed745d4684d63beeac103882fb6198f65`.

PASS for these bounded edits. Exact text reconstruction and AST comparison show
only `_as_int` and `node_to_disk` changed from pass21 starting discover.py. The
separate diff is `pass21-discovery-only.diff`; all other top-level definitions
are unchanged. Root owns final frozen source, canonical regression review and
full applicable gates; this source review does not replace them.

The name guard follows the old path guard, preserving its diagnostic contract.
It rejects missing and slash-containing type=disk kernel names before display
target creation. It does not infer or repair an identity from PATH. The
independent physical observation pass remains unchanged and retains unmounted
excluded rows as hardware alias evidence. Mounted malformed physical metadata
continues to refuse the inventory; malformed boot disk names cannot produce a
confirmed boot Disk. The change does not loosen rom or non-disk eligibility.

The float branch converts only OverflowError into a closed ValueError while
preserving its cause. Finite float, integer, large integer, NaN and string paths
retain their previous operations. The direct parser now follows its established
malformed metadata error convention; public discover was already failclosed
through its generic exception handler. No public uncaught OverflowError is
claimed.

Independently read actual root JUnit files, filtering the exact three prepared
discovery probes: original missing-name 16 failures/44 controls; original
noncanonical-name 24 failures/6 controls; original nonfinite-size 9 failures/63
controls. In root's focused fixed run all 162 discovery probe cases passed,
without failures, errors or skips. This child did not execute the tests. Detailed
testcase identities, file hashes and source checks are in `actual-fix-review.json`
(SHA256 `a753f6d451cc9e1b2bac9842cc46d098f4434444ac0ed04a68699ae321a16393`).

No source/test changes, product imports, test/native runtime, device, network,
guest, staging, commit, push or publication action was performed by this child.
