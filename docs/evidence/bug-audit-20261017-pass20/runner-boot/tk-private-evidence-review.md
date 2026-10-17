# Pass20 private Tk lifetime evidence review

2026-10-17 / Codex `/root/pass20_runner_boot`. Independent read-only parsing of
root's completed source snapshots, test bytes, logs, JUnit child properties and
status receipts. No product imports, GUI, tests, subprocess-backed product
actions, collectors, threads or native calls were run by this reviewer. No
shared product or test source was edited. Root owns any implementation decision
and full verification. Exact evidence hashes are in the companion JSON.

## Measured results and their scope

| Campaign | Independent readback |
| --- | --- |
| Initial ownership boundary | 24 parent assertion failures, zero errors/skips. Two peer/redraw cases contain an invalid fixture assumption: typing outside the keyboard screen should not mutate Wizard typing state. Do not count those two as product proof. Other cases record retained native assets, redraw callback assertions or partial-constructor cleanup failure. |
| Corrected ownership boundary on original shared Tk | 24 parent assertion failures, zero errors/skips. Fixture change preserves the screen-specific expected typing value and later checks against that value. It leaves asset, finalizer-thread, redraw-retirement, peer-trace and exception-preservation assertions intact. Constructor cases additionally expose original partial-teardown AttributeError; do not mistake their cleanup traceback for a clean disposal result. |
| Private graph candidate 1 | 28 cases: 24 pass / four fail, zero errors/skips. Two failures are the same invalid peer/redraw fixture assumption; two separate raise-route child failures are SIGABRT (`returncode=-6`) with `Tcl_AsyncDelete` diagnostics. Their scalar traceback properties name the private Tk source path. |
| Private pinned candidate 2 | 28 pass, zero failures/errors/skips. All 24 extended-boundary children report no remaining product-owned native wrappers; their observed native finalizers return on the creator thread. Four supported-run collector children also complete. Strongly retained peer variables and exception/root references remain explicitly outside a claim that all interpreters were reclaimed. |
| Initial broad candidate 3 driver | Exit 134, fatal abort, no JUnit. The traceback explicitly names shared `build_identity.py`, `evidence.py` and `wizard.py` during worker GC. Its command lacks the pytest pythonpath override. It is invalid acceptance evidence for the private candidate; do not label it a passing run, a completed case count or an isolated candidate regression. |
| Source provenance admission pair | Same one-case probe fails without override and records shared Tk/build-identity module paths. With only the explicit pytest pythonpath override, it passes and records both private module paths. No skips/errors. This causally establishes the import-precedence harness correction. |
| Corrected broad candidate 3 | Parsed only after its completion status appeared: exit 0, 466 actual JUnit cases pass, zero failures/errors/skips. Command includes `-o pythonpath=/tmp/pass20-primary/private-graph/src`. This is separate evidence from the invalid broad run. |

## Snapshot and fixture identity

The retained private Tk snapshots hash as follows:

- Candidate 1: `cff8bc2e1d9a801d44463be6b8b09b3afda5a87f0833ee2a91877ae6f20aa1bb`.
- Candidate 2: `928c88fc6f1fdffa1ee28cc6fe0441464e143a025b07688d0b292aa2a4b52289`.
- Candidate 3: `b3d66bdb83213000c9623a2a48c25cf39b089289a388aba67507f117b4a59546`.

Private tree Tk bytes equal candidate 3. Among its 58 frozen starting `src/`
inputs, exactly three differ: the already reviewed audio/discovery corrections
and private Tk candidate 3; the other 55 match the starting freeze. Shared Tk
still hashes to the original pass19
`23d280b0451d3e25d64387de62d4912a8867ffbdec934244efe6a7f7a7ee0615`
at this readback. Candidate 1's retained `private-graph-source.py` is an exact
copy of its named snapshot. Candidate 2 adds creator-thread interpreter pins
and retirement collection. Candidate 3 retains the root attribute for existing
callers and explicitly drops the outer UI local before final retirement scan.
The companion JSON authenticates the exact candidate-to-candidate diffs.

The new canonical boundary module exactly copies the corrected proof. Every
named helper, exception class, child function and supported collector test in
the canonical collector module has an identical AST to the original pass19
supported-child proof. Its structural test that expected unreleased original
fonts is not copied into the behavioral regression module. No destructor is
neutralized and no traceback is cleared in these proof sources. The probes'
temporary GC-mode changes and destructor observers are diagnostic fixture
instrumentation, not a shipped global-GC correction.

The original 28-case parent commands did not carry the explicit pytest path
override. Their measured behavior comes from direct child scripts, which
inherit private PYTHONPATH and do not invoke pytest themselves; raise and
constructor child traceback properties corroborate the private source path.
Those historical properties do not record a module hash in every child. Their
association with the retained candidate snapshots additionally relies on
root's staged sequence; this reviewer does not invent a cryptographic
per-child source receipt that was never captured.

## Remaining limits

This review authenticates recorded observations and guards their interpretation;
it does not approve private candidate 3 as the finished product correction.
The 466-case result is a bounded focused run, not unchanged full main/Orca
collection, final source review, complete artifact readback or platform/physical
acceptance. The private abort diagnostics identify the failure mechanism in
those two owned children only. They do not identify the exact object or complete
cause of either earlier full-run abort, earlier latency failures, or historical
unattributed SIGTERM. Preserve all failed/invalid histories and continue root's
source-bound final qualification before any commit or push.
