# Comprehensive source audit — 2026-10-25

**Source fixes saved; final qualification BLOCKED.** This pass found and corrected
a stale-success parser defect and adjacent ownership, discovery and recovery
issues. The two final narrow reviews report no remaining concrete objection.
The latest source has no final Linux or full-platform pass. Nothing was staged,
committed, pushed, published, or written to a physical device.

Base `9764d93ac21273aa79ae4618629b0a30e3eda271`, branch `codex/wipe-audit-20261024`, worktree
`C:/Users/Jack/beamo-release-work/20261024-wipe-audit-pass2`.
Final census: **922** functional/configuration inputs at
`1016e41e61b2f78a4cf84841c8657b5cc55a4ae09a2553668ffb5635a909df51`.
Four production modules and nine regression modules differ from this pass's
entry. Earlier integrated fixes are preserved. The peer source/status and empty
index were rechecked. Exact hashes are in [verification.json](verification.json).

Raw evidence: `C:/Users/Jack/beamo-release-evidence/wipe-comprehensive-repass-20261025-r3`.
`final-source-overlay.zip` contains 63 uncommitted functional paths over the
named base, with every member read back and hashed. ZIP SHA-256:
`f5deda9e5ffa882cefd8fd02faa4e652980b82d1f94b0f7b0a73954d46317a9e`. This is source evidence, not a released artifact.

## Findings and corrections

| Finding | Result and evidence boundary |
| --- | --- |
| P1: malformed later target progress reused an earlier 100% sample | Invalidates stale progress completion; independent Erased-table rules retained. Root causal replay: nine failures/nine controls before, 18 passes after. |
| P2: runner and wizard log-reader acquisition/close failures lost handles or primary errors | Acquisition is protected, wrappers borrow the descriptor, one raw owner closes once. Explicit operation-local primary errors preserve interruptions and prevent unrelated caller exceptions from hiding a new close failure. |
| P2: malformed/latest projected progress lost the only erase-activity witness | Activity survives independently of the latest completion sample. Damaged progress cannot support an untouched-media claim. Root replay: three failures/three controls before, six passes after. |
| P2: confirmed safe shutdown rejected an invalid journal afterward | Shutdown quiescence/ownership is separate from eligibility for another erase. Invalid journals still block erasure; process, lock, report and finalization guards remain. |
| P2: unexpected raw-disk and reverse boot ancestry bypassed refusal | Contradictory raw ancestry refuses selection; malformed boot ancestry invalidates authorization while retaining protected boot/physical observations. Final module has 64 fixture cases. |
| P2: surviving local NVMe head/private namespace was hidden after original-controller removal | Fallback verifies the actual namespace parent, matching subsystem/member/class links, stable identities and all surviving PCIe transports. Readable direct decisions are preserved. Root independent private replay: two causal failures/10 controls before, 12 passes after; final reviewer 43/43. |
| Runner-API terminal snapshot race; shipped-flow reachability unproved | Pending progress refresh cannot replace a terminal assessment snapshot. Wizard serialization was found to prevent the demonstrated overlap; no shipped-flow P2 is claimed. |
| P3: deferred/synthetic projection insertion and invalid UTF-8 exceeded the intended retained budget | Every retained/deferred record and collision witness is charged in normalized UTF-8 bytes. Root normalized-budget replay: six failures/23 controls before, 29 passes after; final reviewer 2,306 fake-I/O checks. |

The general whole-log assessment versus authenticated retained suffix limitation
is **withdrawn as a new finding**: the October 15 evidence already documents
conservative recovery/export refusal when proof falls outside the retained
window. Separate assessment, exact suffix, privacy and authentication remain.
The unrelated-controller-number reuse bypass hypothesis also remains withdrawn.
NVMe topology observations are not an atomic lock. No fake reproduction proves
an incomplete real wipe, a real hardware topology or physical acceptance.

## Recorded verification

| Source/stage | Actual result | Scope |
| --- | --- | --- |
| Final v2 | Four native Windows Ruff code/security/developer-format commands pass; input hashes unchanged | Static checks only; no Linux types/shell/runtime acceptance |
| Final v2 | Normalized-budget and private-NVMe independent reviews: no concrete objection | Exact-AST/in-memory fakes; 20 budget and 76 NVMe cases inspected statically, not executed as pytest at v2 |
| Final v2 | `r3-v2-lint` refused admission before WSL startup; controller exit2, gate exit null | C:8,464,756,736 bytes free versus 8,589,934,592 required. All subsequent v2 batches blocked/unrun |
| Earlier c4 candidate | 332 new/GTK-adjacent tests pass; 694 adjacent tests pass; zero failures/errors/skips | Actual exit0, source stable, private namespaces and owned cleanup valid; both precede the last UTF-8/private-NVMe edits |
| Intermediate 915 inputs | 134 runner/evidence tests pass | Superseded source |
| Entry 913 inputs | Canonical lint/type/shell and preview pass; corrected selected run470 passes | Initial selection retained three Git-fixture failures/seven opt-in skips; corrected exact Git/private-X11 run has none |
| Four unchanged output-helper inputs | Eight native Windows regular-file tests pass, rechecked bound hashes | Fake compiler/Git; not Go, real launcher or native inventory acceptance |
| Expanded intermediate selection | 1,106 collected; runtime exceeded300s, queried test exit null, no final JUnit | INCOMPLETE; observed dots are not passes. Source/namespace/owned cleanup valid |
| Older full gate | No final main JUnit/queried test exit/cleanup receipt | INCOMPLETE; no qualification reused |
| Pinned native Go startup | `go version` timed out45s without output; owned cleanup retained | BLOCKED; no blind retry |

See [verification.json](verification.json) for stage receipts and
[reviews.json](reviews.json) for all 14 bounded delegated implementation/review
tasks. These counts overlap and are not summed into a full-suite result.
The original failure, timeout, skip and refusal receipts remain intact.

Storage recovery compressed only 15 explicitly named older owned JSON receipts.
All byte hashes, file identities and mtimes remained unchanged; no deletion,
directory compression, peer cleanup or host setting change occurred. The two
Linux-source retirement candidates were inspected but never removed. Capacity
later fell below the unchanged 8 GiB floor, so final Linux execution stopped at
admission. The native static checks do not bypass or qualify that Linux gate.

Current Lab doctor/sync/plan and final preparation report are integrity-verified
preparation evidence only. Report run `20261025T214341Z-b627490ee204` is PASS,
verified VALID (six files/three events), with candidate_acceptance=false.
The collaborative browser rejected its local-file URL (`unsupported-protocol:
file:`); visual report QA remains unavailable. No server or browser dependency
was installed to work around the restriction.

## Remaining acceptance and exact next work

1. Obtain adequate resources on a safely authorized environment. Preserve the
   immutable refused `r3-v2-lint` receipt; prepare a **new**, uniquely named
   source-bound phase chain. Recheck all 922 inputs and run the new regressions
   (including all 76 NVMe and 20 budget cases), adjacent selection, both large-log
   batches, and canonical lint/types/shell, preview and negative phases. Retain
   assertions/timeouts/namespace/cleanup checks and fix every failure/material
   warning. The reviewed `candidate-checks-v2.py` records the pending selection;
   do not rerun it over an existing phase receipt.
2. Complete the full applicable source/GUI gate with reviewed process/service
   ownership. Selected/fake passes cannot replace full GTK/Orca acceptance.
   Diagnose the pinned native Go startup blocker safely, then retain required
   Windows/macOS launcher/platform evidence; a cross-build is not acceptance.
3. Retain separately required isolated ISO/QEMU, native, release and approvals
   for a final public candidate. No hosted job or guest is authorized or needed
   merely to maintain these source fixes. Real USB reconnect/readback, valuable
   disk disconnection, firmware/Secure Boot and real-device cases remain
   **NOT TESTED / BLOCKED** under the remote-only host rules.
4. Review/integrate and commit explicit owned paths only after applicable gates;
   disk-selection changes require a `safety:` commit and their completed tests.
   Push, publication and historical artifact changes were not performed.

The durable continuation is `BW-COMPREHENSIVE-REPASS-20261025-R3` in
`.ai/memory/unfinished-work.md`. This report is a source-audit handoff, not a
release or physical Secure Boot qualification.
