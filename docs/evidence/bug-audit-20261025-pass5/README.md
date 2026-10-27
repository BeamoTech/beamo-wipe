# Comprehensive audit pass 5 — 2026-10-25

Status: **BLOCKED / SOURCE FIXES SAVED**. The established findings are corrected,
the final independent review has bounded no objection, and the available checks
pass. Required actual-Linux, full, native application, artifact and physical
qualification remain incomplete.
Nothing is staged, committed, pushed, merged or released.

Worktree `C:/Users/Jack/beamo-release-work/20261024-wipe-audit-pass2`, branch `codex/wipe-audit-20261024`, base
`9764d93ac21273aa79ae4618629b0a30e3eda271` plus dirty changes. Default/peer checkouts were not edited;
captured peer hashes, guide hashes and the empty index were rechecked.

Final reviewed source: **931 functional inputs**,
`2a6260d711af5f78442d8a2728fbfe663859ee5d94cea778f196ba6a95b31333`. Readback-verified source overlay:
`2d86f20f4c784ff7373df4883efaa09886f24719d8bced2895e64dcd122930f9`. Raw evidence:
`C:/Users/Jack/beamo-release-evidence/wipe-comprehensive-repass-20261025-r5`. The census excludes documentation and `.ai`, as before.

## Changes and findings

The comprehensive pass covers disk/launch safety, completion/recovery/report
claims, build/finalizer transactions and their cleanup. Saved corrections cover
preference acquisition and primary-error preservation, matching-stage ETA,
accepted finalizer manifest/ISO bytes, initial checksum-list snapshot ownership,
atomic-writer cleanup and the proved reader/immediate-caller ownership chain.
No new unsafe erase target, terminal false success or publisher bypass was
established in this pass. Foreign checksum bytes were retained; accepted
snapshots do not promise an atomic multi-file visible bundle. Downstream
verification remains required.

The prior reader review requested two more corrections:

- **P3 regression:** named-leaf disappearance after double-read followed by a
  close failure became optional `None`, hiding cleanup. The parent independently
  reproduced it. A private operation-level absence marker now reaches optional
  callers only after successful cleanup. Required/fatal primaries keep their
  original identity or existing wrapper cause.
- **P3 fault-model contract:** cleanup-origin `FileNotFoundError` became optional
  absence. The marker distinguishes it from approved input absence. Several
  paths predate the diff; native close-ENOENT feasibility remains **UNPROVEN**.

R6 changed only four CI reader functions, their new private marker and the reader
test module. Entire finalizer/close-helper AST, RM bytes, all other CI definitions
and statements, safety predicates and all twenty old test bodies remain unchanged.
Six new groups add 168 ownership assertions; all 26 groups/655 assertions pass
in direct fake-only replay. Parent independent 46 leaf/provenance controls and
retained 11 helper/20 caller/12 retained/16 build/six optional controls pass at
the recorded final hashes. Counts overlap and are not unique product-test totals.

Implementation evidence: `optional-leaf-implementation-r6/HANDOFF.md`, retained
before/after bytes, original failures, exact diff and readback seal. Parent
evidence: `parent-r6-preservation.json`, `parent-optional-leaf-implementation-r6.json`
and the `after-r6` receipts. Earlier requested changes remain in their historical
reports; completed task status alone is not an approving review.

## Available checks at this source

| Check | Actual result and scope |
| --- | --- |
| Portable pytest | **254 passed plus 37 subtests**, zero failures/errors/skips across three disjoint bounded batches. JUnit has 291 outcomes in 254 testcase elements. Exact AST/fake OS; progress modules are explicitly synthetic. No product runtime or native application acceptance. |
| Ruff | Four existing lint/security/format commands exit 0; 809 input hashes remain stable and match the frozen source. |
| Type analysis | Windows-hosted mypy 2.1.0 with Linux/Python 3.11 stubs: exit 0, 52 source files. Five existing unchecked-untyped-body notes remain explicit. This is not the canonical actual-Linux gate. |
| Source | 742 Python files plus generator embedded Python parse; overlay readback, current source, captured peer/guide hashes, empty index and whitespace checks pass. |

`r6-check-reconciliation.json` binds these scopes and hashes. The initial expanded
reader batch hit the unchanged 45-second deadline, outer exit 124, test exit
unknown; it remains **INCOMPLETE** at `native-r6-readers/timeout.json`. Its 26 groups
were split into two 13-group batches, with all assertions and the deadline
unchanged. All prior setup/style/oracle failures and timeouts are retained.
Historical b310/248-test and R4 Linux receipts retain their original identities.

## Independent review disposition

The fresh R7 review has **bounded no objection; no new findings**. Its new
in-memory OS independently reproduced both prior defects and checked the
correction through 410 observations: 224 current and 186 historical. Historical
observations assert the old defects; these are not 410 product passes. Exact
required/optional causes, standalone fatal cleanup identity, parent cleanup,
borrowed ownership and sorted source listing all retain their reviewed behavior.

All 931 final inputs and 79 overlay entries were reread by the reviewer and
again by the parent. Finalizer logic, regular-file/binding predicates and all
twenty existing test bodies remain unchanged. All thirteen delegated tasks are
terminal, with no pending child runs. The earlier changes-requested review and
all failed intermediate evidence are retained; its two objections were corrected
and independently rereviewed at R7. Completion status alone was not approval.

`verification.json` binds final source, check receipts, packet readback hashes,
actual scopes and remaining gates; `reviews.json` retains all thirteen task
results. Raw final review: `optional-leaf-review-r7/RESULT.md`.

The parent's first final-report inventory assertion failed before canonical
writes because it assumed the review seal included its own post-termination
command receipt. The sealed closing record explicitly excludes that receipt.
The parent verified the declared exclusion, actual exit 0, source/overlay counts
and seal hash, then separately hashed the receipt. The original failed driver
and inspection remain retained; no product check or source assertion changed.

## Remaining work and acceptance

1. **R5-G1 / BLOCKED:** actual-Linux adjacent/build/shell/completion/preview/
   negative/type batches and new modules/checksum fixtures. R5 admission refused
   before WSL/test startup. Latest free disk is 2,790,412,288
   bytes, below the unchanged 8 GiB floor; available RAM is
   8,449,486,848 bytes. Cause of capacity loss
   remains unknown. No peer/cache cleanup, floor relaxation or R5 WSL test run.
   Next: adequate capacity/current peer admission and a new reviewed controller
   bound to the final identity, unique phase chain from `r4v2-new-regressions`;
   retain 1 GiB RAM, 8 GiB disk, 300s phase and 420s transport limits.
2. **R5-G2 / BLOCKED:** full main/Orca gate. Full mode stays disabled until the
   R4 containment checklist and ten finite selftests qualify PID-init/reaping,
   lifelines/private proc, service/interop exclusion, aggregate CPU/memory/task
   and bounded storage/log controls. Prior timeouts remain incomplete.
3. **R5-G3 / INCOMPLETE:** actual native Go/startup/Windows/macOS/platform/artifact
   acceptance and separately authorized final-public isolated ISO/QEMU/hosted
   verification. No blind retry, cross-build relabeling, guest or hosted run.
4. **R5-G4 / NOT TESTED/BLOCKED:** physical task119 reconnect/cold readback,
   valuable-disk disconnection, firmware/Secure Boot trust/revocation/SBAT and
   enforcement matrix. Requires an explicit owner physical-session update and
   original equipment/recovery prerequisites. No host/device/firmware/nwipe action.
5. **R5-G5 / PENDING:** commit/push/merge/publication after all required gates and
   authorization. Lab remains at d3d0959bb26b17531464dbd1ba233d4d842ad581 with its
   pre-existing notes; preparation PASS/VALID is not candidate acceptance.

App initial-reader SIGINT reachability, QEMU fdopen MemoryError ownership, native
close errno and arbitrary-bytecode/signal timing remain qualified **UNPROVEN**
candidates. No production/native/hardware acceptance is inferred from fakes.


## Final scoped identities

| Path | SHA-256 |
| --- | --- |
| `src/beamo_wipe/report_intent.py` | `d8b3c0154f813074971b9c015f447d691615e92e8f10a6ff6dc3d3aa4725e56c` |
| `src/beamo_wipe/wizard.py` | `3c017228651a17de21ead30270d70bbbca34f8a7403551f97080113f0e0c130d` |
| `src/beamo_wipe/ci_evidence.py` | `6eea55bfa18bd217402bdcb3ea258223ad206d65aa76143c3cb7c5d541ed0ec1` |
| `src/beamo_wipe/release_manifest.py` | `5c81a0a2a259c27481c5944c5431eded9718a42fea7c5f2e8b45f6b7502757a0` |
| `tests/test_build_reader_cleanup.py` | `3ddbb65e1814680eaaef7bd7da1fd8a944a22e98700e97e9dac2fbc80e4327a1` |

Updated 2026-10-26T00:48:00.685234+00:00 / Codex.
